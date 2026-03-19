from contextlib import asynccontextmanager

import argostranslate.translate
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from lingua import Language, LanguageDetectorBuilder
from pydantic import BaseModel


SUPPORTED_SOURCE_LANGUAGE = Language.CHINESE
SUPPORTED_SOURCE_LANGUAGE_CODE = "zh"
SUPPORTED_TARGET_LANGUAGE_CODE = "en"

LANGUAGE_NAME_MAP = {
    Language.CHINESE: "Chinese",
    Language.ENGLISH: "English",
}

detector = (
    LanguageDetectorBuilder.from_languages(Language.CHINESE, Language.ENGLISH)
    .build()
)
argos_translation = None


def get_language_name(language: Language | None) -> str:
    if language is None:
        return "Unknown"

    return LANGUAGE_NAME_MAP.get(language, language.name.title())


def get_language_code(language: Language | None) -> str:
    if language is None or language.iso_code_639_1 is None:
        return "unknown"

    return language.iso_code_639_1.name.lower()


def load_argos_translation():
    installed_languages = argostranslate.translate.get_installed_languages()

    source_language = next(
        (
            language
            for language in installed_languages
            if language.code == SUPPORTED_SOURCE_LANGUAGE_CODE
        ),
        None,
    )
    target_language = next(
        (
            language
            for language in installed_languages
            if language.code == SUPPORTED_TARGET_LANGUAGE_CODE
        ),
        None,
    )

    if source_language is None or target_language is None:
        raise RuntimeError(
            "Argos Translate packages for Chinese to English are not installed."
        )

    translation = source_language.get_translation(target_language)

    if translation is None:
        raise RuntimeError(
            "Chinese to English Argos Translate package is not available."
        )

    return translation


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global argos_translation
    argos_translation = load_argos_translation()
    yield


app = FastAPI(
    title="Chinese to English Smart Translator API",
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

    return {
        "language": get_language_name(detected_language),
        "language_code": get_language_code(detected_language),
        "confidence": 1.0,
    }


@app.post("/translate")
def translate(payload: TranslateRequest):
    text = payload.text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="Text is required.")

    detected_language = detector.detect_language_of(text)
    detected_language_name = get_language_name(detected_language)

    if detected_language != SUPPORTED_SOURCE_LANGUAGE:
        raise HTTPException(
            status_code=400,
            detail="Only Chinese input is supported for translation.",
        )

    if argos_translation is None:
        raise HTTPException(
            status_code=500,
            detail="Chinese to English translation package is not loaded.",
        )

    translated_text = argos_translation.translate(text)

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
