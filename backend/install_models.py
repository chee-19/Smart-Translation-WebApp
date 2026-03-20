import logging
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
DEFAULT_ARGOS_PACKAGE_DIR = BACKEND_DIR / ".argos-packages"
ARGOS_PACKAGE_DIR = Path(
    os.getenv("ARGOS_PACKAGE_DIR", str(DEFAULT_ARGOS_PACKAGE_DIR))
).resolve()
ARGOS_DATA_DIR = ARGOS_PACKAGE_DIR.parent / ".argos-data"

os.environ["ARGOS_PACKAGE_DIR"] = str(ARGOS_PACKAGE_DIR)
os.environ["ARGOS_TRANSLATE_DATA_DIR"] = str(ARGOS_DATA_DIR)

import argostranslate.package
import argostranslate.settings
import argostranslate.translate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("install-models")

SOURCE_LANGUAGE_CODE = "zh"
TARGET_LANGUAGE_CODE = "en"


def normalize_code(code: str | None) -> str | None:
    if not code:
        return None
    return code.strip().lower().replace("_", "-")


def configure_argos_directories() -> None:
    ARGOS_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    ARGOS_DATA_DIR.mkdir(parents=True, exist_ok=True)

    argostranslate.settings.data_dir = str(ARGOS_DATA_DIR)
    argostranslate.settings.package_data_dir = str(ARGOS_PACKAGE_DIR)

    logger.info("Python executable: %s", sys.executable)
    logger.info("ARGOS_PACKAGE_DIR: %s", ARGOS_PACKAGE_DIR)
    logger.info("ARGOS_TRANSLATE_DATA_DIR: %s", ARGOS_DATA_DIR)


def list_installed_language_codes() -> list[str]:
    return sorted(
        {
            normalize_code(language.code)
            for language in argostranslate.translate.get_installed_languages()
            if language.code
        }
    )


def get_installed_language_by_code(code: str):
    normalized_code = normalize_code(code)

    for language in argostranslate.translate.get_installed_languages():
        if normalize_code(language.code) == normalized_code:
            return language

    return None


def load_installed_translation(source_code: str, target_code: str):
    source_language = get_installed_language_by_code(source_code)
    target_language = get_installed_language_by_code(target_code)

    if source_language is None or target_language is None:
        return None

    return source_language.get_translation(target_language)


def verify_languages_installed() -> None:
    installed_codes = list_installed_language_codes()

    if SOURCE_LANGUAGE_CODE not in installed_codes:
        raise RuntimeError(
            f"Argos source language '{SOURCE_LANGUAGE_CODE}' is not installed. "
            f"Installed languages: {installed_codes}"
        )

    if TARGET_LANGUAGE_CODE not in installed_codes:
        raise RuntimeError(
            f"Argos target language '{TARGET_LANGUAGE_CODE}' is not installed. "
            f"Installed languages: {installed_codes}"
        )


def verify_translation_loadable() -> None:
    try:
        translation = load_installed_translation(
            SOURCE_LANGUAGE_CODE,
            TARGET_LANGUAGE_CODE,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load Argos translation {SOURCE_LANGUAGE_CODE} -> "
            f"{TARGET_LANGUAGE_CODE}: {exc}"
        ) from exc

    if translation is None:
        raise RuntimeError(
            f"Argos translation {SOURCE_LANGUAGE_CODE} -> {TARGET_LANGUAGE_CODE} "
            "is not installed or could not be loaded."
        )

    logger.info(
        "Verified Argos translation load: %s -> %s",
        SOURCE_LANGUAGE_CODE,
        TARGET_LANGUAGE_CODE,
    )


def ensure_argos_translation_installed() -> None:
    configure_argos_directories()

    installed_codes_before = list_installed_language_codes()
    logger.info(
        "Installed Argos language codes BEFORE installation: %s",
        installed_codes_before,
    )

    translation = None
    try:
        translation = load_installed_translation(
            SOURCE_LANGUAGE_CODE,
            TARGET_LANGUAGE_CODE,
        )
    except Exception as exc:
        logger.warning(
            "Existing Argos translation %s -> %s could not be loaded yet: %s",
            SOURCE_LANGUAGE_CODE,
            TARGET_LANGUAGE_CODE,
            exc,
        )

    if translation is None:
        logger.info(
            "Argos translation %s -> %s is missing. Downloading package.",
            SOURCE_LANGUAGE_CODE,
            TARGET_LANGUAGE_CODE,
        )
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()

        package_to_install = next(
            (
                package
                for package in available_packages
                if normalize_code(package.from_code) == SOURCE_LANGUAGE_CODE
                and normalize_code(package.to_code) == TARGET_LANGUAGE_CODE
            ),
            None,
        )

        if package_to_install is None:
            raise RuntimeError(
                f"Argos package {SOURCE_LANGUAGE_CODE}_{TARGET_LANGUAGE_CODE} is "
                "not available from the package index."
            )

        download_path = package_to_install.download()
        logger.info("Downloaded Argos package to: %s", download_path)
        argostranslate.package.install_from_path(download_path)
        logger.info(
            "Installed Argos package: %s -> %s",
            SOURCE_LANGUAGE_CODE,
            TARGET_LANGUAGE_CODE,
        )
    else:
        logger.info(
            "Argos translation %s -> %s already installed. Skipping download.",
            SOURCE_LANGUAGE_CODE,
            TARGET_LANGUAGE_CODE,
        )

    installed_codes_after = list_installed_language_codes()
    logger.info(
        "Installed Argos language codes AFTER installation: %s",
        installed_codes_after,
    )

    verify_languages_installed()
    verify_translation_loadable()


if __name__ == "__main__":
    try:
        ensure_argos_translation_installed()
        logger.info("Model installation completed successfully.")
    except Exception as exc:
        logger.exception("Model installation failed: %s", exc)
        sys.exit(1)
