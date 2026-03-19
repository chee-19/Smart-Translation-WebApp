import argostranslate.package
import argostranslate.translate

SOURCE_CODE = "zh"
TARGET_CODE = "en"


def is_translation_installed(from_code: str, to_code: str) -> bool:
    installed_languages = argostranslate.translate.get_installed_languages()

    source_language = next(
        (lang for lang in installed_languages if lang.code == from_code),
        None,
    )
    target_language = next(
        (lang for lang in installed_languages if lang.code == to_code),
        None,
    )

    if source_language is None or target_language is None:
        return False

    try:
        translation = source_language.get_translation(target_language)
        return translation is not None
    except Exception:
        return False


def main():
    if is_translation_installed(SOURCE_CODE, TARGET_CODE):
        print(f"Argos model {SOURCE_CODE}_{TARGET_CODE} already installed.")
        return

    print(f"Installing Argos model {SOURCE_CODE}_{TARGET_CODE}...")
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()

    package_to_install = next(
        (
            pkg
            for pkg in available_packages
            if pkg.from_code == SOURCE_CODE and pkg.to_code == TARGET_CODE
        ),
        None,
    )

    if package_to_install is None:
        raise RuntimeError(f"Could not find Argos package {SOURCE_CODE}_{TARGET_CODE}")

    download_path = package_to_install.download()
    argostranslate.package.install_from_path(download_path)
    print(f"Installed Argos model {SOURCE_CODE}_{TARGET_CODE}.")


if __name__ == "__main__":
    main()