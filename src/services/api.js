const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function detectLanguage(text) {
  const response = await fetch(`${API_BASE_URL}/detect-language`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error('Failed to detect language.');
  }

  return response.json();
}

export async function translateChineseToEnglish(text) {
  const response = await fetch(`${API_BASE_URL}/translate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text,
      source_language: 'zh',
      target_language: 'en',
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to translate text.');
  }

  return response.json();
}
