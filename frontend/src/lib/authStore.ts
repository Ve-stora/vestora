import { create } from 'zustand'

interface AuthState {
  token: string | null
  setToken: (token: string) => void
  logout: () => void
}

// Simple in-memory store — token lives for the session only.
// For persistence across page refreshes, wire this to sessionStorage in your own environment.
export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  setToken: (token) => set({ token }),
  logout: () => set({ token: null }),
}))
