# Architecture Overview

## Objective
Create a mobile-friendly Chinese → English translation web app with:
- automatic language detection
- optional voice input
- English pronunciation playback

## System Components

### Frontend
The frontend handles:
- user input
- microphone interactions
- displaying detection results
- displaying translation results
- triggering English text-to-speech

### Backend
The backend handles:
- text language detection with Lingua
- voice transcription with Whisper
- Chinese → English translation with Argos Translate

## Main User Flow

```text
Text or voice input
        ↓
If voice: speech-to-text
        ↓
Text is passed to Lingua
        ↓
Language is identified
        ↓
Text is translated from Chinese to English
        ↓
English output is shown on screen
        ↓
User taps speaker button to hear English pronunciation
```

## Why this split is used

### Frontend responsibilities
- lightweight UI rendering
- browser text-to-speech
- browser microphone access
- mobile responsiveness

### Backend responsibilities
- Python-based AI/NLP libraries
- handling audio transcription
- handling translation logic
- keeping integration modular

## Hosting plan

### Frontend
- Host on Netlify
- Static frontend build from Vite

### Backend
- Host separately later if needed
- Example options: Render, Railway, Fly.io, local deployment, or a school server

## Notes
Netlify is excellent for the frontend, but the Python translation stack is not meant to run directly as a static frontend build.
