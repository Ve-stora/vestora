import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./store/AuthContext";
import ProtectedRoute from "./components/shared/ProtectedRoute";

import Dashboard   from "./pages/Dashboard";
import Market      from "./pages/Market";
import Portfolio   from "./pages/Portfolio";
import Analytics   from "./pages/Analytics";
import Login       from "./pages/Login";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/"           element={<Dashboard />} />
            <Route path="/market"     element={<Market />} />
            <Route path="/portfolio"  element={<Portfolio />} />
            <Route path="/analytics"  element={<Analytics />} />
          </Route>
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}