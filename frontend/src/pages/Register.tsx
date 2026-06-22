/**
 * Register page — missing from repo, now created.
 * App.tsx imports this as RegisterPage from pages/Register.
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Zap, Loader2 } from 'lucide-react';
import { useAuth } from '../store/AuthContext';

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({ username: '', email: '', password: '', confirm: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function set(field: string, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
    setError('');
  }

  async function handleSubmit() {
    if (!form.username || !form.email || !form.password) {
      setError('All fields are required.');
      return;
    }
    if (form.password !== form.confirm) {
      setError('Passwords do not match.');
      return;
    }
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }

    setLoading(true);
    try {
      await register(form.username, form.email, form.password);
      navigate('/dashboard', { replace: true });
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Registration failed. Please try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0f1117] flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <Zap size={20} className="text-[#C9A84C]" />
          <span className="text-xl font-semibold tracking-wide text-white">Vestora</span>
        </div>

        <div className="bg-[#161b27] border border-white/5 rounded-2xl p-8">
          <h1 className="text-lg font-semibold text-white mb-1">Create account</h1>
          <p className="text-sm text-gray-400 mb-6">
            Start with professional-grade market intelligence.
          </p>

          {error && (
            <div className="mb-4 px-3 py-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <Field
              label="Username"
              type="text"
              value={form.username}
              onChange={(v) => set('username', v)}
              placeholder="e.g. keith"
            />
            <Field
              label="Email"
              type="email"
              value={form.email}
              onChange={(v) => set('email', v)}
              placeholder="you@example.com"
            />
            <Field
              label="Password"
              type="password"
              value={form.password}
              onChange={(v) => set('password', v)}
              placeholder="Min. 8 characters"
            />
            <Field
              label="Confirm password"
              type="password"
              value={form.confirm}
              onChange={(v) => set('confirm', v)}
              placeholder="Repeat password"
              onEnter={handleSubmit}
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={loading}
            className="mt-6 w-full flex items-center justify-center gap-2 bg-[#C9A84C] hover:bg-[#b8943d]
                       disabled:opacity-60 disabled:cursor-not-allowed text-black font-semibold
                       py-2.5 rounded-xl transition-colors text-sm"
          >
            {loading && <Loader2 size={15} className="animate-spin" />}
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </div>

        <p className="text-center text-sm text-gray-500 mt-5">
          Already have an account?{' '}
          <Link to="/login" className="text-[#C9A84C] hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}

// ── Minimal field component ──────────────────────────────────────────────────

function Field({
  label,
  type,
  value,
  onChange,
  placeholder,
  onEnter,
}: {
  label: string;
  type: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  onEnter?: () => void;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-400 mb-1.5">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && onEnter?.()}
        placeholder={placeholder}
        className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm
                   text-white placeholder:text-gray-600 focus:outline-none focus:border-[#C9A84C]/50
                   focus:ring-1 focus:ring-[#C9A84C]/20 transition-colors"
      />
    </div>
  );
}
