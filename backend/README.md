# Backend Starter

This folder contains the starter backend scaffold for the Chinese → English Smart Translation Web App.

## Purpose
The backend is responsible for:
- detecting language with Lingua
- transcribing speech with Whisper
- translating Chinese to English with Argos Translate

## Planned Stack
- Python 3.11+
- FastAPI
- Uvicorn
- Lingua
- Whisper
- Argos Translate

## Local Setup

### 1. Create a virtual environment
```bash
python -m venv .venv
```

### 2. Activate it
#### Windows
```bash
.venv\Scripts\activate
```

#### macOS / Linux
```bash
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the backend
```bash
uvicorn app.main:app --reload
```

## Notes
This scaffold currently returns mock data so the frontend can be wired up early.
Replace the placeholder logic with:
- Lingua detection
- Whisper transcription
- Argos translation
