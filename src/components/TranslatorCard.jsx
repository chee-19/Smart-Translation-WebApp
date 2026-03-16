import { useMemo, useState } from 'react';
import { detectLanguage, translateChineseToEnglish } from '../services/api';
import { useSpeechSynthesis } from '../hooks/useSpeechSynthesis';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';

export default function TranslatorCard() {
  const [inputText, setInputText] = useState('你好');
  const [detectedLanguage, setDetectedLanguage] = useState('');
  const [confidence, setConfidence] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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
      setTranslatedText(translation.translation);
    } catch (err) {
      setError(err.message || 'Something went wrong while translating.');
    } finally {
      setLoading(false);
    }
  }

  function handleUseTranscript() {
    if (!activeTranscript) return;
    setInputText(activeTranscript);
  }

  return (
    <section className="card">
      <div className="field-group">
        <label htmlFor="inputText">Chinese input</label>
        <textarea
          id="inputText"
          value={inputText}
          onChange={(event) => setInputText(event.target.value)}
          placeholder="Type Chinese text here"
          rows={5}
        />
      </div>

      <div className="actions-row">
        <button type="button" onClick={() => handleTranslate()} disabled={loading}>
          {loading ? 'Translating...' : 'Translate to English'}
        </button>

        <button
          type="button"
          className="secondary"
          onClick={() => speak(translatedText)}
          disabled={!translatedText}
        >
          Pronounce English
        </button>
      </div>

      <div className="voice-panel">
        <h2>Voice input</h2>
        <p>
          Record Chinese speech, convert it to text, then send the text for language
          detection and translation.
        </p>

        {micSupported ? (
          <div className="actions-row">
            <button type="button" className="secondary" onClick={startListening}>
              {isListening ? 'Listening...' : 'Start microphone'}
            </button>
            <button type="button" className="secondary" onClick={stopListening}>
              Stop
            </button>
            <button type="button" className="secondary" onClick={clearTranscript}>
              Clear transcript
            </button>
            <button type="button" className="secondary" onClick={handleUseTranscript}>
              Use transcript
            </button>
          </div>
        ) : (
          <p className="muted">Speech recognition is not supported in this browser.</p>
        )}

        <div className="result-box muted-box">
          <strong>Transcript:</strong>
          <p>{activeTranscript || 'No speech captured yet.'}</p>
        </div>
      </div>

      <div className="results-grid">
        <div className="result-box">
          <h3>Detected language</h3>
          <p>{detectedLanguage || 'Waiting for input'}</p>
          <small>{confidence ? `Confidence: ${confidence}` : ''}</small>
        </div>

        <div className="result-box">
          <h3>English output</h3>
          <p>{translatedText || 'Translation will appear here'}</p>
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}
    </section>
  );
}
