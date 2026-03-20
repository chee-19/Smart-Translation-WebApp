import os
import sys
import logging

os.environ["ARGOS_PACKAGE_DIR"] = os.getenv(
    "ARGOS_PACKAGE_DIR",
    "/opt/render/project/src/backend/.argos-packages"
)

import argostranslate.package
import argostranslate.translate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("install-models")

SOURCE_LANGUAGE_CODE = "zh"
TARGET_LANGUAGE_CODE = "en"


def normalize_code(code: str | None) -> str | None:
    if not code:
        return None
    return code.strip().lower().replace("_", "-")


def get_installed_language_by_code(code: str):
    normalized_code = normalize_code(code)

    for language in argostranslate.translate.get_installed_languages():
        if normalize_code(language.code) == normalized_code:
            return language

    return None


def get_installed_translation(source_code: str, target_code: str):
    source_language = get_installed_language_by_code(source_code)
    target_language = get_installed_language_by_code(target_code)

    if source_language is None or target_language is None:
        return None

    try:
        return source_language.get_translation(target_language)
    except Exception as exc:
        logger.warning(
            "Could not load installed Argos translation %s -> %s: %s",
            source_code,
            target_code,
            exc,
        )
        return None


def ensure_argos_translation_installed():
    installed_languages = argostranslate.translate.get_installed_languages()
    installed_codes_before = sorted(
        normalize_code(language.code) for language in installed_languages if language.code
    )

    logger.info("ARGOS_PACKAGE_DIR = %s", os.getenv("ARGOS_PACKAGE_DIR"))
    logger.info("Installed Argos language codes before ensure: %s", installed_codes_before)

    existing_translation = get_installed_translation(
        SOURCE_LANGUAGE_CODE,
        TARGET_LANGUAGE_CODE,
    )

    if existing_translation is not None:
        logger.info(
            "Argos package %s_%s already installed; skipping download/install.",
            SOURCE_LANGUAGE_CODE,
            TARGET_LANGUAGE_CODE,
        )
        return

    logger.info(
        "Argos package %s_%s missing; downloading/installing now.",
        SOURCE_LANGUAGE_CODE,
        TARGET_LANGUAGE_CODE,
    )

    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()

    package_to_install = next(
        (
            pkg
            for pkg in available_packages
            if normalize_code(pkg.from_code) == SOURCE_LANGUAGE_CODE
            and normalize_code(pkg.to_code) == TARGET_LANGUAGE_CODE
        ),
        None,
    )

    if package_to_install is None:
        raise RuntimeError(
            f"Argos package {SOURCE_LANGUAGE_CODE}_{TARGET_LANGUAGE_CODE} is not available."
        )

    download_path = package_to_install.download()
    logger.info("Downloaded Argos package to: %s", download_path)

    argostranslate.package.install_from_path(download_path)
    logger.info("Installed Argos model successfully.")

    installed_languages_after = argostranslate.translate.get_installed_languages()
    installed_codes_after = sorted(
        normalize_code(language.code) for language in installed_languages_after if language.code
    )
    logger.info("Installed Argos language codes after ensure: %s", installed_codes_after)

    installed_translation = get_installed_translation(
        SOURCE_LANGUAGE_CODE,
        TARGET_LANGUAGE_CODE,
    )
    if installed_translation is None:
        raise RuntimeError(
            f"Argos package {SOURCE_LANGUAGE_CODE}_{TARGET_LANGUAGE_CODE} was installed, "
            "but the translation could still not be loaded."
        )

    logger.info("Argos translation zh -> en is ready.")


if __name__ == "__main__":
    try:
        ensure_argos_translation_installed()
        logger.info("Model installation script completed successfully.")
    except Exception as exc:
        logger.exception("Model installation failed: %s", exc)
        sys.exit(1)