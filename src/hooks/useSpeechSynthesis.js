export function useSpeechSynthesis() {
  function speak(text, options = {}) {
    if (!text || !('speechSynthesis' in window)) return;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = options.rate || 1;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }

  return { speak };
}
