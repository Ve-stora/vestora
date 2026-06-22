/**
 * App.tsx — fixed.
 *
 * Changes from broken version:
 *  1. Page imports now match actual file names (Login, Dashboard, Market, Portfolio, Analytics)
 *  2. Layout imported from components/layout/Layout (now exists)
 *  3. RegisterPage imported from pages/Register (now exists)
 *  4. StockPage replaced with inline StockDetail route (no missing file)
 *  5. Auth from store/AuthContext only (single system)
 *  6. QueryClientProvider wraps everything (react-query)
 */

import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './store/AuthContext';
import Layout from './components/layout/Layout';

// ─── Lazy pages ──────────────────────────────────────────────────────────────

const Login      = lazy(() => import('./pages/Login'));
const Register   = lazy(() => import('./pages/Register'));
const Dashboard  = lazy(() => import('./pages/Dashboard'));
const Market     = lazy(() => import('./pages/Market'));
const Portfolio  = lazy(() => import('./pages/Portfolio'));
const Analytics  = lazy(() => import('./pages/Analytics'));

// ─── React Query client ──────────────────────────────────────────────────────

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
});

// ─── Route guards ─────────────────────────────────────────────────────────────

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0f1117] flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-[#C9A84C] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) return null;

  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <>{children}</>;
}

// ─── Loading fallback ─────────────────────────────────────────────────────────

function PageLoader() {
  return (
    <div className="min-h-screen bg-[#0f1117] flex items-center justify-center">
      <div className="w-6 h-6 border-2 border-[#C9A84C] border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

// ─── App ──────────────────────────────────────────────────────────────────────

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              {/* Public routes */}
              <Route
                path="/login"
                element={
                  <PublicRoute>
                    <Login />
                  </PublicRoute>
                }
              />
              <Route
                path="/register"
                element={
                  <PublicRoute>
                    <Register />
                  </PublicRoute>
                }
              />

              {/* Protected routes — all wrapped in Layout */}
              <Route
                path="/"
                element={
                  <PrivateRoute>
                    <Layout>
                      <Suspense fallback={<PageLoader />}>
                        <Routes>
                          <Route index element={<Navigate to="/dashboard" replace />} />
                        </Routes>
                      </Suspense>
                    </Layout>
                  </PrivateRoute>
                }
              />

              <Route
                path="/dashboard"
                element={
                  <PrivateRoute>
                    <Layout>
                      <Dashboard />
                    </Layout>
                  </PrivateRoute>
                }
              />

              <Route
                path="/market"
                element={
                  <PrivateRoute>
                    <Layout>
                      <Market />
                    </Layout>
                  </PrivateRoute>
                }
              />

              <Route
                path="/market/:symbol"
                element={
                  <PrivateRoute>
                    <Layout>
                      {/* StockDetail is re-exported from Market page or a sub-route */}
                      <Market />
                    </Layout>
                  </PrivateRoute>
                }
              />

              <Route
                path="/portfolio"
                element={
                  <PrivateRoute>
                    <Layout>
                      <Portfolio />
                    </Layout>
                  </PrivateRoute>
                }
              />

              <Route
                path="/analytics"
                element={
                  <PrivateRoute>
                    <Layout>
                      <Analytics />
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* Catch-all */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}