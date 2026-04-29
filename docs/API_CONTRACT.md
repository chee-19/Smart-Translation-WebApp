# API Contract

This document defines the expected backend endpoints for the frontend.

## Base URL

```text
http://localhost:8000
```

## 1. Detect Language

### Endpoint
```text
POST /detect-language
```

### Request body
```json
{
  "text": "你好"
}
```

### Response body
```json
{
  "language": "Chinese",
  "language_code": "zh",
  "confidence": 0.98
}
```

## 2. Translate Text

### Endpoint
```text
POST /translate
```

### Request body
```json
{
  "text": "你好",
  "source_language": "zh",
  "target_language": "en"
}
```

### Response body
```json
{
  "translated": "Hello",
  "detected_language": "Chinese",
  "source_language": "zh",
  "target_language": "en"
}
```

## 3. Transcribe Audio

### Endpoint
```text
POST /transcribe-audio
```

### Request body
Multipart form-data containing an audio file.

### Response body
```json
{
  "transcript": "你好",
  "language": "zh"
}
```

## Expected Error Shape

```json
{
  "error": "Readable error message"
}
```
