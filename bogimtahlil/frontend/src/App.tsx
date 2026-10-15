import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Spinner } from "./components/ui/spinner";
import AboutPage from "./pages/AboutPage";
import AnalyzePage from "./pages/AnalyzePage";
import HistoryPage from "./pages/HistoryPage";
import HomePage from "./pages/HomePage";
import NotFoundPage from "./pages/NotFoundPage";

// Diagrammali sahifalar (Recharts) alohida yuklanadi
const ResultPage = lazy(() => import("./pages/ResultPage"));
const ModelPage = lazy(() => import("./pages/ModelPage"));

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
