import { Navigate, Route, Routes } from 'react-router-dom';
import SavedTranslationsPage from './pages/SavedTranslationsPage';
import TranslatePage from './pages/TranslatePage';

export default function App() {
  return (
    <div className="app-shell">
      <main className="app-frame">
        <Routes>
          <Route path="/" element={<TranslatePage />} />
          <Route path="/saved" element={<SavedTranslationsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
