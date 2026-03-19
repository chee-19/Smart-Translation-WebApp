import { useEffect, useMemo, useState } from 'react';
import { detectLanguage, translateChineseToEnglish } from '../services/api';
import { useSpeechSynthesis } from '../hooks/useSpeechSynthesis';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';

function SwapIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M7 7h10m0 0-3-3m3 3-3 3M17 17H7m0 0 3-3m-3 3 3 3"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

function BookmarkIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M7 4.75h10a1 1 0 0 1 1 1V20l-6-3.4L6 20V5.75a1 1 0 0 1 1-1Z"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M4 7h16M10 11v5m4-5v5M9 4h6l1 2H8l1-2Zm1 16h4a2 2 0 0 0 2-2V7H8v11a2 2 0 0 0 2 2Z"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

function MicIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M12 15a3 3 0 0 0 3-3V8a3 3 0 0 0-6 0v4a3 3 0 0 0 3 3Zm0 0v3m-4-6a4 4 0 1 0 8 0m-7 6h6"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

function SpeakerIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M5 14h4l5 4V6l-5 4H5v4Zm12.5-4a4.5 4.5 0 0 1 0 4m1.5-7a8 8 0 0 1 0 10"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

export default function TranslatorCard() {
  const [inputText, setInputText] = useState('你好');
  const [detectedLanguage, setDetectedLanguage] = useState('');
  const [confidence, setConfidence] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isSlowMode, setIsSlowMode] = useState(false);

  const { speak } = useSpeechSynthesis();
  const {
    isSupported: micSupported,
    isListening,
    transcript,
    startListening,
    stopListening,
    clearTranscript,
  } = useSpeechRecognition();

  const activeTranscript = useMemo(() => transcript?.trim(), [transcript]);

  useEffect(() => {
    if (activeTranscript) {
      setInputText(activeTranscript);
      setError('');
    }
  }, [activeTranscript]);

  async function handleTranslate(textToUse = inputText) {
    const cleanText = textToUse.trim();

    if (!cleanText) {
      setError('Please enter or record some Chinese text first.');
      return;
    }

    try {
      setLoading(true);
      setError('');

      const detection = await detectLanguage(cleanText);
      const translation = await translateChineseToEnglish(cleanText);

      setDetectedLanguage(detection.language);
      setConfidence(String(detection.confidence));
      setTranslatedText(translation.translated_text);
    } catch (err) {
      setError(err.message || 'Something went wrong while translating.');
    } finally {
      setLoading(false);
    }
  }

  function handleMicPress() {
    if (!micSupported) {
      setError('Speech recognition is not supported in this browser.');
      return;
    }

    setError('');

    if (isListening) {
      stopListening();
      return;
    }

    startListening();
  }

  function handleClearInput() {
    setInputText('');
    setTranslatedText('');
    setDetectedLanguage('');
    setConfidence('');
    setError('');
    clearTranscript();
  }

  const translationPlaceholder = loading
    ? 'Translating...'
    : translatedText || 'Translation will appear here';

  const detectionSummary =
    detectedLanguage && confidence
      ? `Detected ${detectedLanguage} with ${confidence} confidence.`
      : '';

  return (
    <section className="translator-app">
      <header className="language-bar" aria-label="Language selection">
        <div className="language-pair">
          <span className="language-name">Chinese</span>
          <button
            type="button"
            className="swap-button"
            aria-label="Swap languages"
            disabled
            title="Language swapping is not available in this version."
          >
            <SwapIcon />
          </button>
          <span className="language-name">English</span>
        </div>

        <div className="bookmark-icon" aria-hidden="true">
          <BookmarkIcon />
        </div>
      </header>

      <div className="translator-stack">
        <section className="translator-panel translator-panel-input">
          <div className="panel-header">
            <p className="panel-label">Chinese</p>
          </div>

          <label className="sr-only" htmlFor="translator-input">
            Chinese input
          </label>
          <textarea
            id="translator-input"
            className="panel-textarea"
            value={inputText}
            onChange={(event) => setInputText(event.target.value)}
            placeholder="Type Chinese text here"
            rows={6}
          />

          <div className="panel-footer">
            <button
              type="button"
              className="icon-button"
              onClick={handleClearInput}
              aria-label="Clear text"
            >
              <TrashIcon />
            </button>

            <button
              type="button"
              className={`icon-button ${isListening ? 'is-active' : ''}`}
              onClick={handleMicPress}
              aria-label={isListening ? 'Stop microphone' : 'Start microphone'}
            >
              <MicIcon />
            </button>
          </div>
        </section>

        <section className="translator-panel translator-panel-output">
          <div className="panel-header">
            <p className="panel-label">English</p>
          </div>

          <div className="panel-output-text" aria-live="polite">
            {translationPlaceholder}
          </div>

          <div className="panel-footer panel-footer-output">
            <button
              type="button"
              className="icon-button"
              onClick={() => speak(translatedText, { rate: isSlowMode ? 0.75 : 1 })}
              disabled={!translatedText}
              aria-label="Play translation audio"
            >
              <SpeakerIcon />
            </button>

            <label className="slow-toggle">
              <input
                type="checkbox"
                checked={isSlowMode}
                onChange={(event) => setIsSlowMode(event.target.checked)}
              />
              <span className="slow-toggle-track" aria-hidden="true">
                <span className="slow-toggle-thumb" />
              </span>
              <span className="slow-toggle-label">Slow</span>
            </label>
          </div>
        </section>
      </div>

      <button
        type="button"
        className="translate-button"
        onClick={() => handleTranslate()}
        disabled={loading}
      >
        {loading ? 'Translating...' : 'Translate'}
      </button>

      {error ? <p className="status-message error-text">{error}</p> : null}
      {!error && activeTranscript ? (
        <p className="status-message">Transcript captured: {activeTranscript}</p>
      ) : null}
      {!error && !activeTranscript && detectionSummary ? (
        <p className="status-message">{detectionSummary}</p>
      ) : null}
    </section>
  );
}
