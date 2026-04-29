import { useMemo, useRef, useState } from 'react';

export function useSpeechRecognition() {
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition || null;

  const recognitionRef = useRef(null);
  const [transcript, setTranscript] = useState('');
  const [isListening, setIsListening] = useState(false);

  const isSupported = useMemo(() => Boolean(SpeechRecognition), [SpeechRecognition]);

  function createRecognition(language = 'zh-CN') {
    if (!SpeechRecognition) return null;

    const recognition = new SpeechRecognition();
    recognition.lang = language;
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);
    recognition.onresult = (event) => {
      const value = Array.from(event.results)
        .map((result) => result[0]?.transcript || '')
        .join(' ')
        .trim();

      setTranscript(value);
    };

    return recognition;
  }

  function startListening(language = 'zh-CN') {
    if (!SpeechRecognition) return;

    if (!recognitionRef.current || recognitionRef.current.lang !== language) {
      recognitionRef.current?.stop();
      recognitionRef.current = createRecognition(language);
    }

    recognitionRef.current.lang = language;
    recognitionRef.current?.start();
  }

  function stopListening() {
    recognitionRef.current?.stop();
  }

  function clearTranscript() {
    setTranscript('');
  }

  return {
    isSupported,
    isListening,
    transcript,
    startListening,
    stopListening,
    clearTranscript,
  };
}
