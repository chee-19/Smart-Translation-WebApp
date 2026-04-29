const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function parseApiError(response, fallbackMessage) {
  try {
    const data = await response.json();
    return data.detail || data.error || fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

export async function translateText(text, { sourceLanguage, targetLanguage }) {
  const response = await fetch(`${API_BASE_URL}/translate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text,
      source_language: sourceLanguage,
      target_language: targetLanguage,
    }),
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to translate text.'));
  }

  const data = await response.json();

  return {
    translated_text: data.translated || '',
    detected_language: data.detected_language || 'Input',
    source_language: data.source_language || sourceLanguage,
    target_language: data.target_language || targetLanguage,
  };
}
