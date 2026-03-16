# Chinese → English Smart Translation Web App

A mobile-friendly translation web app that accepts **Chinese text or voice input**, detects the language automatically, translates it into **English**, and lets the user **tap to hear the English pronunciation**.

This repository is structured as a **frontend-first starter project** with:
- a React + Vite frontend
- Netlify deployment config
- project documentation
- a lightweight backend plan for Lingua / Whisper / Argos integration

## Core Features

- **Chinese text input** for direct translation
- **Chinese voice input** using microphone capture
- **Automatic language detection** with Lingua
- **Chinese → English translation**
- **English pronunciation playback** using the browser's Speech Synthesis API
- **Mobile-friendly responsive UI**
- **Netlify-ready frontend deployment**

## Planned Flow

### Text input flow
1. User enters Chinese text
2. Backend detects the language with Lingua
3. Backend translates Chinese to English
4. Frontend displays the translated English text
5. User taps the speaker button to hear pronunciation

### Voice input flow
1. User taps the microphone button
2. Audio is captured from the browser
3. Backend transcribes speech to text
4. Backend detects the text language with Lingua
5. Backend translates Chinese to English
6. Frontend displays the translated English text
7. User taps the speaker button to hear pronunciation

## Proposed Tech Stack

### Frontend
- **React**
- **Vite**
- **CSS**
- **Web Speech API** for English pronunciation
- **Netlify** for hosting

### Backend
- **Python FastAPI**
- **Lingua** for language detection
- **Whisper** for speech-to-text
- **Argos Translate** for Chinese → English translation

## Repository Structure

```text
chinese-english-smart-translator/
├── backend/
│   ├── README.md
│   ├── requirements.txt
│   └── app/
│       └── main.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API_CONTRACT.md
│   └── ROADMAP.md
├── public/
│   └── manifest.webmanifest
├── src/
│   ├── components/
│   │   └── TranslatorCard.jsx
│   ├── hooks/
│   │   ├── useSpeechRecognition.js
│   │   └── useSpeechSynthesis.js
│   ├── services/
│   │   └── api.js
│   ├── App.jsx
│   ├── index.css
│   └── main.jsx
├── .env.example
├── .gitignore
├── index.html
├── netlify.toml
├── package.json
├── vite.config.js
└── README.md
```

## Getting Started

### 1. Install frontend dependencies
```bash
npm install
```

### 2. Start the frontend locally
```bash
npm run dev
```

### 3. Build the frontend
```bash
npm run build
```

### 4. Preview the production build
```bash
npm run preview
```

## Backend Setup

The backend is included as a starter scaffold only.

See:
- [`backend/README.md`](backend/README.md)
- [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md)

## Netlify Deployment

This project includes a `netlify.toml` file.

Deploy flow:
1. Push this repository to GitHub
2. Connect the repo to Netlify
3. Use the default build command:
   - `npm run build`
4. Publish directory:
   - `dist`

## Environment Variables

Copy `.env.example` into `.env` and update values when needed.

Example:
```bash
cp .env.example .env
```

## Current Status

This repository is a **starter template** and planning scaffold.
It includes:
- a clean frontend structure
- deployment config
- documentation
- backend placeholders

It does **not yet include full production translation logic**.
That part will be connected in the next implementation phase.

## Suggested Next Steps

1. Build the frontend UI flow
2. Connect frontend to a FastAPI backend
3. Add Lingua detection endpoint
4. Add Whisper transcription endpoint
5. Add Argos translation endpoint
6. Test on mobile browsers
7. Deploy frontend to Netlify

## Portfolio Description

Built a mobile-friendly Chinese-to-English translation web application that automatically detects input language, converts Chinese speech or text into English, and allows users to hear the pronunciation of the translated English text.
