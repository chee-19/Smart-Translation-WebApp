import asyncio
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter

# Set Argos directories BEFORE importing argostranslate
BACKEND_DIR = Path(__file__).resolve().parents[1]
ARGOS_ROOT_DIR = BACKEND_DIR / ".argos"
XDG_DATA_HOME = ARGOS_ROOT_DIR / "data"
XDG_CACHE_HOME = ARGOS_ROOT_DIR / "cache"
XDG_CONFIG_HOME = ARGOS_ROOT_DIR / "config"

os.environ["XDG_DATA_HOME"] = str(XDG_DATA_HOME)
os.environ["XDG_CACHE_HOME"] = str(XDG_CACHE_HOME)
os.environ["XDG_CONFIG_HOME"] = str(XDG_CONFIG_HOME)

import argostranslate.settings
import argostranslate.translate
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from lingua import Language, LanguageDetectorBuilder
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("smart-translator")

SUPPORTED_TRANSLATION_PAIRS = [
    ("zh", "en"),
    ("en", "zh"),
]

detector = LanguageDetectorBuilder.from_languages(
    Language.CHINESE,
    Language.ENGLISH,
).build()

argos_translations = {}


def normalize_code(code: str | None) -> str | None:
    if not code:
        return None
    return code.strip().lower().replace("_", "-")


def configure_argos_environment() -> None:
    ARGOS_ROOT_DIR.mkdir(parents=True, exist_ok=True)
    XDG_DATA_HOME.mkdir(parents=True, exist_ok=True)
    XDG_CACHE_HOME.mkdir(parents=True, exist_ok=True)
    XDG_CONFIG_HOME.mkdir(parents=True, exist_ok=True)

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


def log_argos_environment() -> None:
    logger.info("Python executable: %s", sys.executable)
    logger.info("XDG_DATA_HOME: %s", os.environ["XDG_DATA_HOME"])
    logger.info("XDG_CACHE_HOME: %s", os.environ["XDG_CACHE_HOME"])
    logger.info("XDG_CONFIG_HOME: %s", os.environ["XDG_CONFIG_HOME"])
    logger.info("Argos settings.data_dir: %s", argostranslate.settings.data_dir)
    logger.info("Argos settings.package_data_dir: %s", argostranslate.settings.package_data_dir)
    logger.info("Argos settings.package_dirs: %s", argostranslate.settings.package_dirs)
    logger.info("Argos settings.local_package_index: %s", argostranslate.settings.local_package_index)
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


def get_installed_language_by_code(code: str):
    normalized_code = normalize_code(code)

    for language in list_installed_languages():
        if normalize_code(language.code) == normalized_code:
            return language

    return None


def load_required_translation(source_code: str, target_code: str):
    source_language = get_installed_language_by_code(source_code)
    target_language = get_installed_language_by_code(target_code)

    installed_codes = list_installed_language_codes()

    if source_language is None:
        raise RuntimeError(
            f"Argos source language '{source_code}' is not installed. "
            f"Installed languages: {installed_codes}"
        )

    if target_language is None:
        raise RuntimeError(
            f"Argos target language '{target_code}' is not installed. "
            f"Installed languages: {installed_codes}"
        )

    try:
        translation = source_language.get_translation(target_language)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load Argos translation {source_code} -> "
            f"{target_code}: {exc}"
        ) from exc

    if translation is None:
        raise RuntimeError(
            f"Argos translation {source_code} -> {target_code} is not installed."
        )

    return source_language, translation


def index_translation(source_code: str, target_code: str, translation) -> None:
    pair_key = (normalize_code(source_code), normalize_code(target_code))
    argos_translations[pair_key] = translation

    logger.info(
        "Loaded Argos translation: %s -> %s",
        source_code,
        target_code,
    )


def load_argos_translations() -> None:
    configure_argos_environment()
    log_argos_environment()
    argos_translations.clear()

    installed_codes = list_installed_language_codes()
    logger.info("Installed Argos language codes at startup: %s", installed_codes)
    for source_code, target_code in SUPPORTED_TRANSLATION_PAIRS:
        logger.info("Startup has '%s': %s", source_code, source_code in installed_codes)
        logger.info("Startup has '%s': %s", target_code, target_code in installed_codes)

        _, translation = load_required_translation(source_code, target_code)
        logger.info(
            "Startup %s -> %s translation loads: %s",
            source_code,
            target_code,
            translation is not None,
        )
        index_translation(source_code, target_code, translation)

    if not argos_translations:
        raise RuntimeError("No Argos translations were loaded.")

    logger.info(
        "Loaded Argos translation keys: %s",
        [f"{source}->{target}" for source, target in sorted(argos_translations)],
    )


def detect_language_from_text(text: str) -> dict:
    text = text.strip()

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_argos_translations()
    logger.info("Application startup completed")
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
    source_language: str
    target_language: str


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/detect-language")
def detect_language(payload: DetectLanguageRequest):
    return detect_language_from_text(payload.text)


@app.post("/translate")
async def translate_text(request: TranslateRequest):
    source_code = normalize_code(request.source_language)
    target_code = normalize_code(request.target_language)
    translator = argos_translations.get((source_code, target_code))

    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text is required.")

    if source_code == target_code:
        raise HTTPException(status_code=400, detail="Source and target languages must differ.")

    if translator is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported translation direction: {request.source_language} -> "
                f"{request.target_language}"
            ),
        )

    start = time.time()
    logger.info("STEP 1: Received translate request")

    detected_lang = detect_language_from_text(request.text)
    logger.info("STEP 2: Detected language: %s", detected_lang)

    mid1 = time.time()

    translated = await asyncio.to_thread(translator.translate, request.text)

    mid2 = time.time()

    logger.info("STEP 3: Translation done")
    logger.info("DETECT TIME: %.2fs", mid1 - start)
    logger.info("TRANSLATE TIME: %.2fs", mid2 - mid1)
    logger.info("TOTAL TIME: %.2fs", mid2 - start)

    return {
        "translated": translated,
        "detected_language": detected_lang.get("language", "Input"),
        "source_language": source_code,
        "target_language": target_code,
    }


@app.post("/transcribe-audio")
async def transcribe_audio(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "transcript": "你好",
        "language": "zh",
    }
