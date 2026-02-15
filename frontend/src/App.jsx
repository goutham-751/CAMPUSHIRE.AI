import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './store/ThemeContext';
import AppLayout from './layouts/AppLayout/AppLayout';

/* ── Lazy-loaded pages ─────────────────────────────────────── */
const Landing = lazy(() => import('./pages/Landing/Landing'));
const Dashboard = lazy(() => import('./pages/Dashboard/Dashboard'));
const ResumeAnalyzer = lazy(() => import('./pages/ResumeAnalyzer/ResumeAnalyzer'));
const Interview = lazy(() => import('./pages/Interview/Interview'));
const VoiceStudio = lazy(() => import('./pages/VoiceStudio/VoiceStudio'));
const Settings = lazy(() => import('./pages/Settings/Settings'));

/* ── Fallback spinner ──────────────────────────────────────── */
function PageLoader() {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      height: '100vh', width: '100%',
    }}>
      <div className="skeleton" style={{ width: 48, height: 48, borderRadius: '50%' }} />
    </div>
  );
}

/* ── App ───────────────────────────────────────────────────── */
export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            {/* Landing page */}
            <Route path="/" element={<Landing />} />

            {/* App shell with sidebar */}
            <Route path="/app" element={<AppLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="resume" element={<ResumeAnalyzer />} />
              <Route path="interview" element={<Interview />} />
              <Route path="voice" element={<VoiceStudio />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ThemeProvider>
  );
}
