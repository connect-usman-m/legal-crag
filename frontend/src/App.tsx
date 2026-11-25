import { useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";

import { useHealth } from "./api/queries";
import Footer from "./components/layout/Footer";
import TopBar from "./components/layout/TopBar";
import AskPage from "./pages/AskPage";
import ComparePage from "./pages/ComparePage";
import HowItWorksPage from "./pages/HowItWorksPage";
import ResultsPage from "./pages/ResultsPage";

function OfflineBanner() {
  const [offline, setOffline] = useState(!navigator.onLine);
  useEffect(() => {
    const update = () => setOffline(!navigator.onLine);
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);
  if (!offline) return null;
  return (
    <div role="status" className="border-b border-hairline bg-decision-ambiguous-bg px-4 py-2 text-center text-sm text-decision-ambiguous-fg">
      You&apos;re offline. Reconnect to ask a question.
    </div>
  );
}

export default function App() {
  const health = useHealth();
  return (
    <div className="min-h-screen bg-page text-ink">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:bg-surface focus:p-3">
        Skip to main content
      </a>
      <OfflineBanner />
      <TopBar />
      {health.data && !health.data.ready && (
        <div role="alert" className="border-b border-hairline bg-decision-ambiguous-bg px-4 py-3 text-sm text-decision-ambiguous-fg">
          Index not ready. Run <code>make ingest</code> and reload. Checks: {Object.entries(health.data.checks).filter(([, ok]) => !ok).map(([name]) => name).join(", ")}.
        </div>
      )}
      <main id="main" className="scroll-mt-20">
        <Routes>
          <Route path="/" element={<AskPage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/eval" element={<ResultsPage />} />
          <Route path="/how-it-works" element={<HowItWorksPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
