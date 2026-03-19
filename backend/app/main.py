from contextlib import asynccontextmanager
import logging
import sys

import argostranslate.translate
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from lingua import LanguageDetectorBuilder
from pydantic import BaseModel


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart-translator")

TARGET_LANGUAGE_CODE = "en"
detector = LanguageDetectorBuilder.from_all_languages().build()
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

    ARGOS_LINGUA_ALIASES = {
        "zh": {"zh", "zho", "chinese"},
        "ja": {"ja", "jpn", "japanese"},
        "ko": {"ko", "kor", "korean"},
        "de": {"de", "deu", "ger", "german"},
        "en": {"en", "eng", "english"},
    }

    if not normalized_code:
        return set()

    return ARGOS_LINGUA_ALIASES.get(normalized_code, {normalized_code})


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

        if source_code == TARGET_LANGUAGE_CODE:
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
    load_argos_translations()
    yield


app = FastAPI(
    title="Smart Translator API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

    detected_language = detector.detect_language_of(text)
    detected_codes = get_language_code_candidates(detected_language)

    return {
        "language": get_language_name(detected_language),
        "language_code": detected_codes[0] if detected_codes else "unknown",
        "confidence": 1.0,
    }


@app.post("/translate")
def translate(payload: TranslateRequest):
    text = payload.text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="Text is required.")

    detected_language = detector.detect_language_of(text)
    detected_language_name = get_language_name(detected_language)
    detected_codes = get_language_code_candidates(detected_language)

    logger.info(
        "Translate request detected language: name=%s codes=%s",
        detected_language_name,
        detected_codes,
    )

    if not detected_codes:
        raise HTTPException(status_code=400, detail="Could not detect the input language.")

    if TARGET_LANGUAGE_CODE in detected_codes:
        logger.info("Detected English input; returning text without Argos translation.")
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

    return {
        "detected_language": detected_language_name,
        "translated_text": translation_entry["translation"].translate(text),
    }


@app.post("/transcribe-audio")
async def transcribe_audio(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "transcript": "你好",
        "language": "zh",
    }
