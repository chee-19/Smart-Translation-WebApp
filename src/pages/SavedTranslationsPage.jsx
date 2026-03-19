import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchSavedTranslations } from '../services/supabase';

function ArrowIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M5 12h14m0 0-5-5m5 5-5 5"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

export default function SavedTranslationsPage() {
  const navigate = useNavigate();
  const itemTouchRef = useRef({
    id: null,
    x: null,
    y: null,
  });
  const [savedTranslations, setSavedTranslations] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isMounted = true;

    async function loadSavedTranslations() {
      try {
        setIsLoading(true);
        setError('');
        const data = await fetchSavedTranslations();

        if (isMounted) {
          setSavedTranslations(data);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Could not load saved translations.');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadSavedTranslations();

    return () => {
      isMounted = false;
    };
  }, []);

  const filteredTranslations = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();

    if (!query) {
      return savedTranslations;
    }

    return savedTranslations.filter((item) => {
      const sourceText = item.source_text?.toLowerCase() || '';
      const translatedText = item.translated_text?.toLowerCase() || '';

      return sourceText.includes(query) || translatedText.includes(query);
    });
  }, [savedTranslations, searchQuery]);

  function openSavedTranslation(item) {
    navigate('/', {
      state: {
        selectedTranslation: item,
      },
    });
  }

  function handleItemTouchStart(item, event) {
    const touch = event.changedTouches[0];
    itemTouchRef.current = {
      id: item.id,
      x: touch.clientX,
      y: touch.clientY,
    };
  }

  function handleItemTouchEnd(item, event) {
    if (itemTouchRef.current.id !== item.id) {
      return;
    }

    const touch = event.changedTouches[0];
    const deltaX = touch.clientX - itemTouchRef.current.x;
    const deltaY = touch.clientY - itemTouchRef.current.y;

    itemTouchRef.current = { id: null, x: null, y: null };

    if (deltaX > 70 && Math.abs(deltaY) < 40) {
      openSavedTranslation(item);
    }
  }

  return (
    <section className="saved-page">
      <header className="saved-page-header">
        <h1 className="saved-page-title">Saved Translations</h1>
      </header>

      <label className="sr-only" htmlFor="saved-search">
        Search saved translations
      </label>
      <input
        id="saved-search"
        className="saved-search-input"
        type="search"
        value={searchQuery}
        onChange={(event) => setSearchQuery(event.target.value)}
        placeholder="Search saved translations"
      />

      {isLoading ? <p className="status-message">Loading saved translations...</p> : null}
      {!isLoading && error ? <p className="status-message error-text">{error}</p> : null}

      {!isLoading && !error ? (
        <div className="saved-list" aria-label="Saved translations list">
          {filteredTranslations.length > 0 ? (
            filteredTranslations.map((item) => (
              <button
                key={item.id}
                type="button"
                className="saved-pill"
                onClick={() => openSavedTranslation(item)}
                onTouchStart={(event) => handleItemTouchStart(item, event)}
                onTouchEnd={(event) => handleItemTouchEnd(item, event)}
                aria-label={`Open saved translation ${item.source_text} to ${item.translated_text}`}
              >
                <span className="saved-pill-layer saved-pill-layer-left" aria-hidden="true" />
                <span className="saved-pill-layer saved-pill-layer-middle" aria-hidden="true" />

                <span className="saved-pill-content">
                  <span className="saved-pill-text saved-pill-text-left">
                    {item.source_text}
                  </span>
                  <span className="saved-pill-arrow" aria-hidden="true">
                    <ArrowIcon />
                  </span>
                  <span className="saved-pill-text saved-pill-text-right">
                    {item.translated_text}
                  </span>
                </span>
              </button>
            ))
          ) : (
            <p className="status-message">
              {searchQuery.trim()
                ? 'No saved translations match your search.'
                : 'No saved translations yet.'}
            </p>
          )}
        </div>
      ) : null}

      <button type="button" className="back-button" onClick={() => navigate('/')}>
        Back
      </button>
    </section>
  );
}
