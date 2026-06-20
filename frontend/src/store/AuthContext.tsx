import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { authApi } from '../services/api'

interface User {
  id: string
  email: string
  full_name: string | null
  tier: 'free' | 'premium' | 'b2b'
}

interface AuthContextValue {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, full_name: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(
    () => sessionStorage.getItem('vestora_token')
  )
  const [user, setUser] = useState<User | null>(null)

  const login = useCallback(async (email: string, password: string) => {
    const data = await authApi.login(email, password) as { access_token: string }
    const t = data.access_token
    sessionStorage.setItem('vestora_token', t)
    setToken(t)
    // Decode basic user info from JWT payload
    try {
      const payload = JSON.parse(atob(t.split('.')[1]))
      setUser({ id: payload.sub, email, full_name: null, tier: 'free' })
    } catch {
      setUser({ id: '', email, full_name: null, tier: 'free' })
    }
  }, [])

  const register = useCallback(async (email: string, password: string, full_name: string) => {
    await authApi.register(email, password, full_name)
    await login(email, password)
  }, [login])

  const logout = useCallback(() => {
    sessionStorage.removeItem('vestora_token')
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
