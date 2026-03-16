from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Chinese to English Smart Translator API")

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
    source_language: str
    target_language: str


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/detect-language")
def detect_language(payload: DetectLanguageRequest):
    text = payload.text.strip()

    if not text:
        return {"language": "Unknown", "language_code": "unknown", "confidence": 0.0}

    return {
        "language": "Chinese",
        "language_code": "zh",
        "confidence": 0.98,
    }


@app.post("/translate")
def translate(payload: TranslateRequest):
    mock_dictionary = {
        "你好": "Hello",
        "谢谢": "Thank you",
        "早上好": "Good morning",
    }

    translation = mock_dictionary.get(payload.text.strip(), "Translation placeholder")

    return {"translation": translation}


@app.post("/transcribe-audio")
async def transcribe_audio(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "transcript": "你好",
        "language": "zh",
    }
