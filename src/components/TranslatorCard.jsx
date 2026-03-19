import { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { translateToEnglish } from '../services/api';
import {
  checkTranslationSaved,
  deleteSavedTranslation,
  saveTranslation,
} from '../services/supabase';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { useSpeechSynthesis } from '../hooks/useSpeechSynthesis';

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

function LibraryIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M5 19h14M7 6h3v10H7zM12 4h3v12h-3zM17 8h3v8h-3z"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

function CopyIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M9 9h10v11H9zM5 15V5h10"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

function getPairKey(sourceText, translatedText) {
  return `${sourceText.trim()}:::${translatedText.trim()}`;
}

export default function TranslatorCard() {
  const location = useLocation();
  const navigate = useNavigate();
  const savedStatusCacheRef = useRef(new Map());
  const [inputText, setInputText] = useState('');
  const [detectedLanguage, setDetectedLanguage] = useState('');
  const [confidence, setConfidence] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isSlowMode, setIsSlowMode] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  const [copyMessage, setCopyMessage] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isCurrentSaved, setIsCurrentSaved] = useState(false);

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
  const trimmedInputText = inputText.trim();
  const trimmedTranslatedText = translatedText.trim();
  const currentPairKey = getPairKey(trimmedInputText, trimmedTranslatedText);
  const canSave = Boolean(trimmedInputText && trimmedTranslatedText) && !isSaving;
  const sourceLabel = detectedLanguage || 'Input';

  useEffect(() => {
    if (activeTranscript) {
      setInputText(activeTranscript);
      setError('');
      setSaveMessage('');
      setCopyMessage('');
    }
  }, [activeTranscript]);

  useEffect(() => {
    const preload = location.state?.selectedTranslation;

    if (!preload) {
      return;
    }

    const sourceText = preload.source_text ?? '';
    const translatedValue = preload.translated_text ?? '';
    const sourceLanguage = preload.source_language ?? 'Input';
    const preloadKey = getPairKey(sourceText, translatedValue);

    setInputText(sourceText);
    setTranslatedText(translatedValue);
    setDetectedLanguage(sourceLanguage);
    setConfidence('');
    setError('');
    setSaveMessage('');
    setCopyMessage('');
    setIsCurrentSaved(true);
    savedStatusCacheRef.current.set(preloadKey, true);
  }, [location.key, location.state]);

  useEffect(() => {
    setSaveMessage('');
    setCopyMessage('');
  }, [currentPairKey]);

  useEffect(() => {
    if (!trimmedInputText || !trimmedTranslatedText) {
      setIsCurrentSaved(false);
      return;
    }

    if (savedStatusCacheRef.current.has(currentPairKey)) {
      setIsCurrentSaved(savedStatusCacheRef.current.get(currentPairKey));
      return;
    }

    let isActive = true;
    const timeoutId = window.setTimeout(async () => {
      try {
        const isSaved = await checkTranslationSaved(trimmedInputText, trimmedTranslatedText);

        if (!isActive) {
          return;
        }

        savedStatusCacheRef.current.set(currentPairKey, isSaved);
        setIsCurrentSaved(isSaved);
      } catch {
        if (isActive) {
          setIsCurrentSaved(false);
        }
      }
    }, 200);

    return () => {
      isActive = false;
      window.clearTimeout(timeoutId);
    };
  }, [currentPairKey, trimmedInputText, trimmedTranslatedText]);

  async function handleTranslate(textToUse = inputText) {
    const cleanText = textToUse.trim();

    if (!cleanText) {
      setError('Please enter some text first.');
      return;
    }

    try {
      setLoading(true);
      setError('');
      setSaveMessage('');
      setCopyMessage('');

      const translation = await translateToEnglish(cleanText);

      setDetectedLanguage(translation.detected_language || 'Input');
      setConfidence('');
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
    setSaveMessage('');
    setCopyMessage('');

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
    setSaveMessage('');
    setCopyMessage('');
    setIsCurrentSaved(false);
    clearTranscript();
  }

  async function handleSaveTranslation() {
    if (!canSave) {
      setSaveMessage('Translate something first before saving.');
      return;
    }

    if (isCurrentSaved) {
      const shouldRemove = window.confirm(
        'Remove this saved translation?'
      );

      if (!shouldRemove) {
        return;
      }

      try {
        setIsSaving(true);
        setError('');
        setSaveMessage('');

        const result = await deleteSavedTranslation(
          trimmedInputText,
          trimmedTranslatedText
        );

        if (result.status === 'missing') {
          savedStatusCacheRef.current.set(currentPairKey, false);
          setIsCurrentSaved(false);
          setSaveMessage('Translation was already removed.');
          return;
        }

        savedStatusCacheRef.current.set(currentPairKey, false);
        setIsCurrentSaved(false);
        setSaveMessage('Saved translation removed.');
      } catch (err) {
        setError(err.message || 'Could not remove saved translation.');
      } finally {
        setIsSaving(false);
      }

      return;
    }

    try {
      setIsSaving(true);
      setError('');
      setSaveMessage('');

      const result = await saveTranslation({
        sourceText: trimmedInputText,
        translatedText: trimmedTranslatedText,
        sourceLanguage: detectedLanguage || 'Input',
        targetLanguage: 'English',
      });

      if (result.status === 'duplicate') {
        savedStatusCacheRef.current.set(currentPairKey, true);
        setIsCurrentSaved(true);
        setSaveMessage('Translation already saved.');
        return;
      }

      savedStatusCacheRef.current.set(currentPairKey, true);
      setIsCurrentSaved(true);
      setSaveMessage('Translation saved.');
    } catch (err) {
      setError(err.message || 'Could not save translation.');
    } finally {
      setIsSaving(false);
    }
  }

  async function handleCopyTranslation() {
    if (!trimmedTranslatedText) {
      setCopyMessage('Nothing to copy yet.');
      return;
    }

    try {
      await navigator.clipboard.writeText(trimmedTranslatedText);
      setError('');
      setCopyMessage('Copied.');
    } catch {
      setError('Could not copy translation.');
    }
  }

  const translationPlaceholder = loading
    ? 'Translating...'
    : translatedText || 'Translation will appear here';

  const detectionSummary =
    detectedLanguage && confidence
      ? `Detected ${detectedLanguage} with ${confidence} confidence.`
      : detectedLanguage || '';

  return (
    <section className="translator-app">
      <header className="language-bar" aria-label="Language selection">
        <div className="language-pair">
          <span className="language-name">{sourceLabel}</span>
          <button
            type="button"
            className="swap-button"
            aria-label="Auto-detect input language"
            disabled
            title="Input language is detected automatically."
          >
            <SwapIcon />
          </button>
          <span className="language-name">English</span>
        </div>

        <button
          type="button"
          className={`bookmark-button ${isCurrentSaved ? 'is-saved' : ''}`}
          onClick={handleSaveTranslation}
          disabled={!canSave}
          aria-label={
            isCurrentSaved ? 'Remove saved translation' : 'Save current translation'
          }
          title={isCurrentSaved ? 'Remove saved translation' : 'Save current translation'}
        >
          <BookmarkIcon />
        </button>
      </header>

      <div className="translator-stack">
        <section className="translator-panel translator-panel-input">
          <div className="panel-header">
            <p className="panel-label">{sourceLabel}</p>
          </div>

          <label className="sr-only" htmlFor="translator-input">
            Source input
          </label>
          <textarea
            id="translator-input"
            className="panel-textarea"
            value={inputText}
            onChange={(event) => setInputText(event.target.value)}
            placeholder="Type text here"
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

            <button
              type="button"
              className="icon-button"
              onClick={handleCopyTranslation}
              disabled={!translatedText}
              aria-label="Copy English translation"
            >
              <CopyIcon />
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

      <div className="translate-actions">
        <button
          type="button"
          className="translate-button"
          onClick={() => handleTranslate()}
          disabled={loading}
        >
          {loading ? 'Translating...' : 'Translate'}
        </button>

        <button
          type="button"
          className="saved-nav-button"
          onClick={() => navigate('/saved')}
        >
          <LibraryIcon />
          <span>Saved Translations</span>
        </button>
      </div>

      {error ? <p className="status-message error-text">{error}</p> : null}
      {!error && saveMessage ? <p className="status-message">{saveMessage}</p> : null}
      {!error && !saveMessage && copyMessage ? (
        <p className="status-message">{copyMessage}</p>
      ) : null}
      {!error && !saveMessage && !copyMessage && activeTranscript ? (
        <p className="status-message">Transcript captured: {activeTranscript}</p>
      ) : null}
      {!error && !saveMessage && !copyMessage && !activeTranscript && detectionSummary ? (
        <p className="status-message">{detectionSummary}</p>
      ) : null}
    </section>
  );
}
