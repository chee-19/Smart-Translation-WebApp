const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function parseApiError(response, fallbackMessage) {
  try {
    const data = await response.json();
    return data.detail || data.error || fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

export async function detectLanguage(text) {
  const response = await fetch(`${API_BASE_URL}/detect-language`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to detect language.'));
  }

  return response.json();
}

export async function translateToEnglish(text) {
  const response = await fetch(`${API_BASE_URL}/translate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error(await parseApiError(response, 'Failed to translate text.'));
  }

  return response.json();
}
