# Backend Starter

This folder contains the backend for the Smart Translation Web App.

## Purpose
The backend is responsible for:
- detecting language with Lingua
- transcribing speech with Whisper
- translating Chinese to English and English to Chinese with Argos Translate

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
python install_models.py
uvicorn app.main:app --reload
```

## Notes
`install_models.py` installs both required Argos packages:
- `zh -> en`
- `en -> zh`

The `/translate` endpoint expects `text`, `source_language`, and `target_language` in the request body.
