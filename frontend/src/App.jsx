import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './store/ThemeContext';
import { AuthProvider, useAuth } from './store/AuthContext';
import AppLayout from './layouts/AppLayout/AppLayout';
import { healthApi } from './lib/api';
import { useEffect } from 'react';

/* ── Lazy-loaded pages ─────────────────────────────────────── */
const Landing = lazy(() => import('./pages/Landing/Landing'));
const Login = lazy(() => import('./pages/Auth/Login'));
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

/* ── Protected Route Wrapper ───────────────────────────────── */
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  
  if (loading) return <PageLoader />;
  if (!user) return <Navigate to="/login" replace />;
  
  return children;
}

/* ── App ───────────────────────────────────────────────────── */
export default function App() {
  // Warm up the Render backend to mitigate cold starts
  useEffect(() => {
    healthApi.check().catch(() => {
      // ignore errors, this is just to wake up the server
    });
  }, []);

  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              {/* Public routes */}
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />

              {/* App shell with sidebar (Protected) */}
              <Route path="/app" element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }>
                <Route index element={<Dashboard />} />
                <Route path="resume" element={<ResumeAnalyzer />} />
                <Route path="interview" element={<Interview />} />
                <Route path="voice" element={<VoiceStudio />} />
                <Route path="settings" element={<Settings />} />
              </Route>
            </Routes>
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}
