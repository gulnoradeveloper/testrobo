import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ServerOffline } from "./components/ServerOffline";
import { Spinner } from "./components/ui/spinner";
import AboutPage from "./pages/AboutPage";
import AnalyzePage from "./pages/AnalyzePage";
import HistoryPage from "./pages/HistoryPage";
import HomePage from "./pages/HomePage";
import NotFoundPage from "./pages/NotFoundPage";

/** Diagrammali sahifalar (Recharts) alohida yuklanadi. Server javob bermay qolsa, bo‘sh sahifa o‘rniga
 * “server bilan bog‘lanib bo‘lmadi” xabari ko‘rsatiladi. */
function lazyPage(loader: () => Promise<{ default: React.ComponentType }>) {
  return lazy(() =>
    loader().catch(() => ({
      default: () => (
        <div className="container py-10"><ServerOffline onRetry={() => window.location.reload()} /></div>
      ),
    })),
  );
}
const ResultPage = lazyPage(() => import("./pages/ResultPage"));
const ModelPage = lazyPage(() => import("./pages/ModelPage"));

const page = (el: React.ReactNode) => <Suspense fallback={<div className="container py-16"><Spinner /></div>}>{el}</Suspense>;

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="tahlil" element={<AnalyzePage />} />
        <Route path="natija/:id" element={page(<ResultPage />)} />
        <Route path="tarix" element={<HistoryPage />} />
        <Route path="model" element={page(<ModelPage />)} />
        <Route path="haqida" element={<AboutPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
