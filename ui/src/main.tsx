import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./Layout";
import { AboutPage } from "./pages/AboutPage";
import { ComparePage } from "./pages/ComparePage";
import { JobPage } from "./pages/JobPage";
import { NewRunPage } from "./pages/NewRunPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { RunPage } from "./pages/RunPage";
import { RunsPage } from "./pages/RunsPage";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<RunsPage />} />
          <Route path="new" element={<NewRunPage />} />
          <Route path="jobs/:jobId" element={<JobPage />} />
          <Route path="runs/:runId" element={<RunPage />} />
          <Route path="compare" element={<ComparePage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
