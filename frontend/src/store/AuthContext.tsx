/**
 * Vestora Auth — single source of truth.
 *
 * Strategy: React Context + localStorage persistence.
 * Replaces BOTH store/AuthContext.tsx (sessionStorage) and lib/authStore.ts (Zustand, no persistence).
 *
 * Token survives page refresh. All imports across the app should point here:
 *   import { useAuth, AuthProvider } from '@/store/AuthContext'
 *
 * lib/authStore.ts is kept as a re-export shim for backward compat (see that file).
 */

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from 'react';
import { authApi, type RegisterResponse } from '../lib/api';

// ─── Types ───────────────────────────────────────────────────────────────────

interface User {
  id: number;
  email: string;
  username: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

// ─── Storage helpers ─────────────────────────────────────────────────────────

const TOKEN_KEY = 'vestora_token';
const USER_KEY = 'vestora_user';

function readStorage(): { token: string | null; user: User | null } {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    const raw = localStorage.getItem(USER_KEY);
    const user: User | null = raw ? JSON.parse(raw) : null;
    return { token, user };
  } catch {
    return { token: null, user: null };
  }
}

function writeStorage(token: string, user: User) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearStorage() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

// ─── Context ─────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const stored = readStorage();

  const [state, setState] = useState<AuthState>({
    user: stored.user,
    token: stored.token,
    isAuthenticated: Boolean(stored.token && stored.user),
    isLoading: Boolean(stored.token && !stored.user), // token exists but user not yet verified
  });

  // Rehydrate user from /me on mount if we have a token but want to verify it's still valid
  useEffect(() => {
    if (state.token && state.user) {
      // Already hydrated from localStorage — mark done
      setState((s) => ({ ...s, isLoading: false }));
      return;
    }
    if (state.token && !state.user) {
      authApi
        .me()
        .then((user) => {
          setState({
            user,
            token: state.token,
            isAuthenticated: true,
            isLoading: false,
          });
        })
        .catch(() => {
          clearStorage();
          setState({ user: null, token: null, isAuthenticated: false, isLoading: false });
        });
    } else {
      setState((s) => ({ ...s, isLoading: false }));
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await authApi.login(email, password);
    const user = await authApi.me();          // fetch full user after token acquired
    writeStorage(access_token, user);
    setState({ user, token: access_token, isAuthenticated: true, isLoading: false });
  }, []);

  const register = useCallback(
    async (username: string, email: string, password: string) => {
      await authApi.register(username, email, password);
      // Auto-login after register
      await login(email, password);
    },
    [login],
  );

  const logout = useCallback(() => {
    clearStorage();
    setState({ user: null, token: null, isAuthenticated: false, isLoading: false });
  }, []);

  const value: AuthContextValue = { ...state, login, register, logout };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}