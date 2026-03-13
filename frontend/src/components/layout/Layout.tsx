/**
 * Layout — shell wrapper for authenticated pages.
 *
 * Provides the sidebar nav, top bar, and main content area.
 * App.tsx imports this from components/layout/Layout.
 */

import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  TrendingUp,
  Briefcase,
  BarChart2,
  LogOut,
  Menu,
  X,
  Zap,
  AlertTriangle,
  type LucideIcon,
} from 'lucide-react';
import { useAuth } from '../../store/AuthContext';

interface NavItem {
  to: string;
  label: string;
  Icon: LucideIcon;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard', Icon: LayoutDashboard },
  { to: '/market', label: 'Market', Icon: TrendingUp },
  { to: '/portfolio', label: 'Portfolio', Icon: Briefcase },
  { to: '/analytics', label: 'Analytics', Icon: BarChart2 },
];

// ── Error boundary ──────────────────────────────────────────────────────────
// Catches render errors thrown by whatever page is mounted inside the
// layout (Dashboard, Market, etc.) so a bug in one page shows a recoverable
// message instead of a blank white screen with the sidebar gone too.

interface BoundaryState {
  error: Error | null;
}

class PageErrorBoundary extends React.Component<{ children: React.ReactNode }, BoundaryState> {
  state: BoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): BoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error('Vestora page crashed:', error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex flex-1 items-center justify-center p-6">
          <div className="max-w-md text-center">
            <AlertTriangle size={28} className="text-amber-400 mx-auto mb-3" />
            <h2 className="text-white font-semibold mb-1">Something went wrong loading this page</h2>
            <p className="text-gray-500 text-sm mb-4">
              {this.state.error.message || 'An unexpected error occurred.'}
            </p>
            <button
              onClick={() => this.setState({ error: null })}
              className="bg-[#C9A84C] hover:bg-[#b8943d] text-black text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
            >
              Try again
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  return (
    <div className="flex h-screen bg-[#0f1117] text-gray-100 overflow-hidden">
      {/* ── Mobile overlay ─────────────────────────────────────────────── */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Sidebar ────────────────────────────────────────────────────── */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-30
          w-60 flex flex-col bg-[#161b27] border-r border-white/5
          transform transition-transform duration-200
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-5 py-5 border-b border-white/5">
          <Zap size={18} className="text-[#C9A84C]" />
          <span className="font-semibold tracking-wide text-white text-sm">Vestora</span>
          <span className="relative ml-1 flex h-2 w-2" title="Live market data">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          <button
            className="ml-auto lg:hidden text-gray-400 hover:text-white"
            onClick={() => setSidebarOpen(false)}
          >
            <X size={16} />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {NAV_ITEMS.map(({ to, label, Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
                 ${
                   isActive
                     ? 'bg-[#C9A84C]/10 text-[#C9A84C]'
                     : 'text-gray-400 hover:text-white hover:bg-white/5'
                 }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* User + logout */}
        <div className="px-3 py-4 border-t border-white/5">
          <div className="px-3 py-2 mb-1">
            <p className="text-xs text-gray-500">Signed in as</p>
            <p className="text-sm text-gray-200 truncate">{user?.email ?? '—'}</p>
          </div>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-400
                       hover:text-red-400 hover:bg-white/5 transition-colors"
          >
            <LogOut size={16} />
            Sign out
          </button>
        </div>
      </aside>
/**
 * Layout — shell wrapper for authenticated pages.
 *
 * Provides the sidebar nav, top bar, and main content area.
 * App.tsx imports this from components/layout/Layout.
 */

import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  TrendingUp,
  Briefcase,
  BarChart2,
  LogOut,
  Menu,
  X,
  Zap,
  type LucideIcon,
} from 'lucide-react';
import { useAuth } from '../../store/AuthContext';

interface NavItem {
  to: string;
  label: string;
  Icon: LucideIcon;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard', Icon: LayoutDashboard },
  { to: '/market', label: 'Market', Icon: TrendingUp },
  { to: '/portfolio', label: 'Portfolio', Icon: Briefcase },
  { to: '/analytics', label: 'Analytics', Icon: BarChart2 },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  return (
    <div className="flex h-screen bg-[#0f1117] text-gray-100 overflow-hidden">
      {/* ── Mobile overlay ─────────────────────────────────────────────── */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Sidebar ────────────────────────────────────────────────────── */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-30
          w-60 flex flex-col bg-[#161b27] border-r border-white/5
          transform transition-transform duration-200
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-5 py-5 border-b border-white/5">
          <Zap size={18} className="text-[#C9A84C]" />
          <span className="font-semibold tracking-wide text-white text-sm">Vestora</span>
          <button
            className="ml-auto lg:hidden text-gray-400 hover:text-white"
            onClick={() => setSidebarOpen(false)}
          >
            <X size={16} />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {NAV_ITEMS.map(({ to, label, Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
                 ${
                   isActive
                     ? 'bg-[#C9A84C]/10 text-[#C9A84C]'
                     : 'text-gray-400 hover:text-white hover:bg-white/5'
                 }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* User + logout */}
        <div className="px-3 py-4 border-t border-white/5">
          <div className="px-3 py-2 mb-1">
            <p className="text-xs text-gray-500">Signed in as</p>
            <p className="text-sm text-gray-200 truncate">{user?.email ?? '—'}</p>
          </div>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-400
                       hover:text-red-400 hover:bg-white/5 transition-colors"
          >
            <LogOut size={16} />
            Sign out
          </button>
        </div>
      </aside>

      {/* ── Main ───────────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top bar (mobile only) */}
        <header className="lg:hidden flex items-center gap-3 px-4 py-3 bg-[#161b27] border-b border-white/5">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-gray-400 hover:text-white"
          >
            <Menu size={20} />
          </button>
          <Zap size={16} className="text-[#C9A84C]" />
          <span className="font-semibold text-sm text-white">Vestora</span>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
      {/* ── Main ───────────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top bar (mobile only) */}
        <header className="lg:hidden flex items-center gap-3 px-4 py-3 bg-[#161b27] border-b border-white/5">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-gray-400 hover:text-white"
          >
            <Menu size={20} />
          </button>
          <Zap size={16} className="text-[#C9A84C]" />
          <span className="font-semibold text-sm text-white">Vestora</span>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto flex flex-col">
          <PageErrorBoundary>{children}</PageErrorBoundary>
        </main>
      </div>
    </div>
  );
}