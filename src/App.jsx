import TranslatorCard from './components/TranslatorCard';

export default function App() {
  return (
    <div className="app-shell">
      <main className="page-container">
        <header className="hero">
          <p className="eyebrow">Portfolio Project</p>
          <h1>Chinese → English Smart Translator</h1>
          <p className="hero-copy">
            Mobile-friendly translation app with automatic language detection,
            speech input support, and English pronunciation playback.
          </p>
        </header>

        <TranslatorCard />
      </main>
    </div>
  );
}
