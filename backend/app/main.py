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

SOURCE_LANGUAGE_CODE = "zh"
TARGET_LANGUAGE_CODE = "en"

detector = LanguageDetectorBuilder.from_languages(
    Language.CHINESE,
    Language.ENGLISH,
).build()

argos_translations = {}
translator = None


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


def get_lingua_aliases_for_argos_code(argos_code: str) -> set[str]:
    normalized_code = normalize_code(argos_code)

    argos_lingua_aliases = {
        "zh": {"zh", "zho", "chinese"},
        "en": {"en", "eng", "english"},
    }

    if not normalized_code:
        return set()

    return argos_lingua_aliases.get(normalized_code, {normalized_code})


def get_installed_language_by_code(code: str):
    normalized_code = normalize_code(code)

    for language in list_installed_languages():
        if normalize_code(language.code) == normalized_code:
            return language

    return None


def load_required_translation():
    source_language = get_installed_language_by_code(SOURCE_LANGUAGE_CODE)
    target_language = get_installed_language_by_code(TARGET_LANGUAGE_CODE)

    installed_codes = list_installed_language_codes()

    if source_language is None:
        raise RuntimeError(
            f"Argos source language '{SOURCE_LANGUAGE_CODE}' is not installed. "
            f"Installed languages: {installed_codes}"
        )

    if target_language is None:
        raise RuntimeError(
            f"Argos target language '{TARGET_LANGUAGE_CODE}' is not installed. "
            f"Installed languages: {installed_codes}"
        )

    try:
        translation = source_language.get_translation(target_language)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load Argos translation {SOURCE_LANGUAGE_CODE} -> "
            f"{TARGET_LANGUAGE_CODE}: {exc}"
        ) from exc

    if translation is None:
        raise RuntimeError(
            f"Argos translation {SOURCE_LANGUAGE_CODE} -> {TARGET_LANGUAGE_CODE} "
            "is not installed."
        )

    return source_language, translation


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


def load_argos_translations() -> None:
    configure_argos_environment()
    log_argos_environment()
    argos_translations.clear()

    installed_codes = list_installed_language_codes()
    logger.info("Installed Argos language codes at startup: %s", installed_codes)
    logger.info("Startup has '%s': %s", SOURCE_LANGUAGE_CODE, SOURCE_LANGUAGE_CODE in installed_codes)
    logger.info("Startup has '%s': %s", TARGET_LANGUAGE_CODE, TARGET_LANGUAGE_CODE in installed_codes)

    source_language, translation = load_required_translation()
    logger.info("Startup zh -> en translation loads: %s", translation is not None)

    index_translation(translation, source_language)

    if not argos_translations:
        raise RuntimeError(
            f"Argos translation {SOURCE_LANGUAGE_CODE} -> {TARGET_LANGUAGE_CODE} "
            "was found but could not be indexed."
        )

    logger.info("Loaded Argos translation keys: %s", sorted(argos_translations))


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
    global translator

    load_argos_translations()

    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = next(lang for lang in installed_languages if lang.code == SOURCE_LANGUAGE_CODE)
    to_lang = next(lang for lang in installed_languages if lang.code == TARGET_LANGUAGE_CODE)
    translator = from_lang.get_translation(to_lang)

    if translator is None:
        raise RuntimeError("Translator failed to load during startup.")

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


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/detect-language")
def detect_language(payload: DetectLanguageRequest):
    return detect_language_from_text(payload.text)


@app.post("/translate")
async def translate_text(request: TranslateRequest):
    if translator is None:
        raise HTTPException(status_code=500, detail="Translator not loaded.")

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
    }


@app.post("/transcribe-audio")
async def transcribe_audio(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "transcript": "你好",
        "language": "zh",
    }