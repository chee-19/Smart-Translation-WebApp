import logging
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
ARGOS_ROOT_DIR = BACKEND_DIR / ".argos"
XDG_DATA_HOME = ARGOS_ROOT_DIR / "data"
XDG_CACHE_HOME = ARGOS_ROOT_DIR / "cache"
XDG_CONFIG_HOME = ARGOS_ROOT_DIR / "config"
ARGOS_PACKAGES_DIR = XDG_DATA_HOME / "argos-translate" / "packages"

os.environ["XDG_DATA_HOME"] = str(XDG_DATA_HOME)
os.environ["XDG_CACHE_HOME"] = str(XDG_CACHE_HOME)
os.environ["XDG_CONFIG_HOME"] = str(XDG_CONFIG_HOME)


import argostranslate.package
import argostranslate.settings
import argostranslate.translate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("install-models")

SUPPORTED_TRANSLATION_PAIRS = [
    ("zh", "en"),
    ("en", "zh"),
]


def normalize_code(code: str | None) -> str | None:
    if not code:
        return None
    return code.strip().lower().replace("_", "-")


def configure_argos_environment() -> None:
    ARGOS_ROOT_DIR.mkdir(parents=True, exist_ok=True)
    XDG_DATA_HOME.mkdir(parents=True, exist_ok=True)
    XDG_CACHE_HOME.mkdir(parents=True, exist_ok=True)
    XDG_CONFIG_HOME.mkdir(parents=True, exist_ok=True)
    ARGOS_PACKAGES_DIR.mkdir(parents=True, exist_ok=True)

    Path(argostranslate.settings.data_dir).mkdir(parents=True, exist_ok=True)
    Path(argostranslate.settings.package_data_dir).mkdir(parents=True, exist_ok=True)
    Path(argostranslate.settings.downloads_dir).mkdir(parents=True, exist_ok=True)
    Path(argostranslate.settings.local_package_index).parent.mkdir(parents=True, exist_ok=True)


def reset_argos_runtime_state() -> None:
    cache_clear = getattr(
        argostranslate.translate.get_installed_languages,
        "cache_clear",
        None,
    )
    if callable(cache_clear):
        cache_clear()

    if hasattr(argostranslate.package, "get_installed_packages"):
        package_cache_clear = getattr(
            argostranslate.package.get_installed_packages,
            "cache_clear",
            None,
        )
        if callable(package_cache_clear):
            package_cache_clear()


def log_argos_directories() -> None:
    logger.info("Python executable: %s", sys.executable)
    logger.info("XDG_DATA_HOME: %s", os.environ["XDG_DATA_HOME"])
    logger.info("XDG_CACHE_HOME: %s", os.environ["XDG_CACHE_HOME"])
    logger.info("XDG_CONFIG_HOME: %s", os.environ["XDG_CONFIG_HOME"])
    
    logger.info("Argos settings.data_dir: %s", argostranslate.settings.data_dir)
    logger.info(
        "Argos settings.package_data_dir: %s",
        argostranslate.settings.package_data_dir,
    )
    logger.info("Argos settings.package_dirs: %s", argostranslate.settings.package_dirs)
    logger.info(
        "Argos settings.local_package_index: %s",
        argostranslate.settings.local_package_index,
    )
    logger.info("Argos settings.downloads_dir: %s", argostranslate.settings.downloads_dir)


def list_installed_languages():
    reset_argos_runtime_state()
    return argostranslate.translate.get_installed_languages()


def list_installed_language_codes() -> list[str]:
    return sorted(
        {
            normalize_code(language.code)
            for language in list_installed_languages()
            if language.code
        }
    )


def get_installed_language_by_code(code: str):
    normalized_code = normalize_code(code)

    for language in list_installed_languages():
        if normalize_code(language.code) == normalized_code:
            return language

    return None


def load_installed_translation(source_code: str, target_code: str):
    source_language = get_installed_language_by_code(source_code)
    target_language = get_installed_language_by_code(target_code)

    if source_language is None or target_language is None:
        return None

    return source_language.get_translation(target_language)


def log_installation_status(prefix: str) -> None:
    installed_codes = list_installed_language_codes()
    logger.info("%s installed languages: %s", prefix, installed_codes)

    for source_code, target_code in SUPPORTED_TRANSLATION_PAIRS:
        has_source = source_code in installed_codes
        has_target = target_code in installed_codes
        translation = None

        try:
            translation = load_installed_translation(source_code, target_code)
        except Exception as exc:
            logger.warning(
                "%s %s -> %s translation load raised an exception: %s",
                prefix,
                source_code,
                target_code,
                exc,
            )

        logger.info("%s has '%s': %s", prefix, source_code, has_source)
        logger.info("%s has '%s': %s", prefix, target_code, has_target)
        logger.info(
            "%s %s -> %s translation loads: %s",
            prefix,
            source_code,
            target_code,
            translation is not None,
        )


def verify_installation() -> None:
    installed_codes = list_installed_language_codes()
    for source_code, target_code in SUPPORTED_TRANSLATION_PAIRS:
        if source_code not in installed_codes:
            raise RuntimeError(
                f"Argos source language '{source_code}' is not installed. "
                f"Installed languages: {installed_codes}"
            )

        if target_code not in installed_codes:
            raise RuntimeError(
                f"Argos target language '{target_code}' is not installed. "
                f"Installed languages: {installed_codes}"
            )

        try:
            translation = load_installed_translation(source_code, target_code)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load Argos translation {source_code} -> "
                f"{target_code}: {exc}"
            ) from exc

        if translation is None:
            raise RuntimeError(
                f"Argos translation {source_code} -> {target_code} "
                "is not installed or could not be loaded."
            )


def ensure_argos_translation_installed() -> None:
    configure_argos_environment()
    log_argos_directories()
    log_installation_status("BEFORE install")

    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()

    for source_code, target_code in SUPPORTED_TRANSLATION_PAIRS:
        existing_translation = load_installed_translation(source_code, target_code)

        if existing_translation is None:
            logger.info(
                "Argos translation %s -> %s is missing. Downloading package.",
                source_code,
                target_code,
            )

            package_to_install = next(
                (
                    package
                    for package in available_packages
                    if normalize_code(package.from_code) == source_code
                    and normalize_code(package.to_code) == target_code
                ),
                None,
            )

            if package_to_install is None:
                raise RuntimeError(
                    f"Argos package {source_code}_{target_code} "
                    "is not available from the package index."
                )

            download_path = package_to_install.download()
            logger.info("Downloaded Argos package to: %s", download_path)
            argostranslate.package.install_from_path(download_path)
            logger.info(
                "Installed Argos package: %s -> %s",
                source_code,
                target_code,
            )
        else:
            logger.info(
                "Argos translation %s -> %s already installed. Skipping download.",
                source_code,
                target_code,
            )

    reset_argos_runtime_state()
    log_installation_status("AFTER install")
    verify_installation()
    logger.info("Argos installation verified successfully.")


if __name__ == "__main__":
    try:
        ensure_argos_translation_installed()
        logger.info("Model installation completed successfully.")
    except Exception as exc:
        logger.exception("Model installation failed: %s", exc)
        sys.exit(1)
