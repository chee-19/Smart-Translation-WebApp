from contextlib import asynccontextmanager
import logging
from time import perf_counter
import sys

import argostranslate.translate
import argostranslate.package
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from lingua import Language, LanguageDetectorBuilder
from pydantic import BaseModel


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart-translator")

SOURCE_LANGUAGE_CODE = "zh"
TARGET_LANGUAGE_CODE = "en"
detector = LanguageDetectorBuilder.from_languages(
    Language.CHINESE,
    Language.ENGLISH,
).build()
argos_translations = {}

def normalize_code(code: str | None) -> str | None:
    if not code:
        return None

    return code.strip().lower().replace("_", "-")


def get_language_name(language) -> str:
    if language is None:
        return "Unknown"

    return language.name.replace("_", " ").title()


def get_language_code_candidates(language) -> list[str]:
    if language is None:
        return []

    candidates = []

    if language.iso_code_639_1 is not None:
        candidates.append(normalize_code(language.iso_code_639_1.name))

    if language.iso_code_639_3 is not None:
        candidates.append(normalize_code(language.iso_code_639_3.name))

    return [code for code in dict.fromkeys(candidates) if code]


def get_lingua_aliases_for_argos_code(argos_code: str) -> set[str]:
    normalized_code = normalize_code(argos_code)

    # ARGOS_LINGUA_ALIASES = {
    #     "zh": {"zh", "zho", "chinese"},
    #     "ja": {"ja", "jpn", "japanese"},
    #     "ko": {"ko", "kor", "korean"},
    #     "de": {"de", "deu", "ger", "german"},
    #     "en": {"en", "eng", "english"},
    # }
    ARGOS_LINGUA_ALIASES = {
        "zh": {"zh", "zho", "chinese"},
        "en": {"en", "eng", "english"},
    }

    if not normalized_code:
        return set()

    return ARGOS_LINGUA_ALIASES.get(normalized_code, {normalized_code})


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

    install_started_at = perf_counter()
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
    argostranslate.package.install_from_path(download_path)
    logger.info(
        "Installed Argos package %s_%s in %.3fs",
        SOURCE_LANGUAGE_CODE,
        TARGET_LANGUAGE_CODE,
        perf_counter() - install_started_at,
    )


def index_translation(translation, source_language) -> None:
    aliases = get_lingua_aliases_for_argos_code(source_language.code)

    if not aliases:
        logger.warning(
            "Skipping Argos translation with no usable aliases: %s -> %s",
            getattr(source_language, "code", "unknown"),
            TARGET_LANGUAGE_CODE,
        )
        return

    for alias in aliases:
        argos_translations[alias] = {
            "translation": translation,
            "source_code": normalize_code(source_language.code),
            "source_name": getattr(source_language, "name", source_language.code),
            "aliases": sorted(aliases),
        }

    logger.info(
        "Loaded Argos translation: %s -> %s (aliases=%s)",
        source_language.code,
        TARGET_LANGUAGE_CODE,
        sorted(aliases),
    )


def load_argos_translations():
    argos_translations.clear()
    installed_languages = argostranslate.translate.get_installed_languages()
    installed_codes = sorted(
        normalize_code(language.code) for language in installed_languages if language.code
    )
    logger.info("Python executable: %s", sys.executable)
    logger.info("Installed Argos language codes: %s", installed_codes)

    target_language = next(
        (
            language
            for language in installed_languages
            if normalize_code(language.code) == TARGET_LANGUAGE_CODE
        ),
        None,
    )

    if target_language is None:
        raise RuntimeError("Argos Translate English package is not installed.")

    for source_language in installed_languages:
        source_code = normalize_code(source_language.code)

        if source_code == TARGET_LANGUAGE_CODE or source_code != SOURCE_LANGUAGE_CODE:
            continue

        try:
            translation = source_language.get_translation(target_language)
        except Exception as exc:
            logger.warning(
                "Skipping Argos pair %s -> %s due to get_translation error: %s",
                source_language.code,
                target_language.code,
                exc,
            )
            continue

        if translation is None:
            logger.warning(
                "Skipping Argos pair %s -> %s because no translation object was returned.",
                source_language.code,
                target_language.code,
            )
            continue

        index_translation(translation, source_language)

    if not argos_translations:
        raise RuntimeError("No Argos Translate source-to-English packages are installed.")

    logger.info("Loaded source-to-English translation keys: %s", sorted(argos_translations))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    startup_started_at = perf_counter()
    logger.info("Application startup started.")
    ensure_argos_translation_installed()
    load_argos_translations()
    logger.info(
        "Application startup completed in %.3fs",
        perf_counter() - startup_started_at,
    )
    yield


app = FastAPI(
    title="Smart Translator API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://cheetranslator.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DetectLanguageRequest(BaseModel):
    text: str


class TranslateRequest(BaseModel):
    text: str


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/detect-language")
def detect_language(payload: DetectLanguageRequest):
    text = payload.text.strip()

    if not text:
        return {"language": "Unknown", "language_code": "unknown", "confidence": 0.0}

    detection_started_at = perf_counter()
    detected_language = detector.detect_language_of(text)
    detected_codes = get_language_code_candidates(detected_language)
    detection_duration = perf_counter() - detection_started_at
    logger.info(
        "Language detection completed in %.3fs: name=%s codes=%s",
        detection_duration,
        get_language_name(detected_language),
        detected_codes,
    )

    return {
        "language": get_language_name(detected_language),
        "language_code": detected_codes[0] if detected_codes else "unknown",
        "confidence": 1.0,
    }


@app.post("/translate")
def translate(payload: TranslateRequest):
    request_started_at = perf_counter()
    text = payload.text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="Text is required.")

    detection_started_at = perf_counter()
    detected_language = detector.detect_language_of(text)
    detection_duration = perf_counter() - detection_started_at
    detected_language_name = get_language_name(detected_language)
    detected_codes = get_language_code_candidates(detected_language)

    logger.info(
        "Translate request detected language in %.3fs: name=%s codes=%s",
        detection_duration,
        detected_language_name,
        detected_codes,
    )

    if not detected_codes:
        raise HTTPException(status_code=400, detail="Could not detect the input language.")

    if TARGET_LANGUAGE_CODE in detected_codes:
        total_duration = perf_counter() - request_started_at
        logger.info("Detected English input; returning text without Argos translation.")
        logger.info("Total translate request duration: %.3fs", total_duration)
        return {
            "detected_language": detected_language_name,
            "translated_text": text,
        }

    translation_entry = None

    for code in detected_codes:
        translation_entry = argos_translations.get(code)

        if translation_entry:
            break

    logger.info(
        "Translation lookup result: found=%s matched_code=%s available_keys=%s",
        bool(translation_entry),
        code if translation_entry else None,
        sorted(argos_translations),
    )

    if translation_entry is None:
        raise HTTPException(
            status_code=400,
            detail=f"Translation from {detected_language_name} to English is not available.",
        )

    translation_started_at = perf_counter()
    translated_text = translation_entry["translation"].translate(text)
    translation_duration = perf_counter() - translation_started_at
    total_duration = perf_counter() - request_started_at
    logger.info("Translation completed in %.3fs", translation_duration)
    logger.info("Total translate request duration: %.3fs", total_duration)

    return {
        "detected_language": detected_language_name,
        "translated_text": translated_text,
    }


@app.post("/transcribe-audio")
async def transcribe_audio(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "transcript": "你好",
        "language": "zh",
    }
