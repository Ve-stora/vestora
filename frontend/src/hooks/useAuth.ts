import { useState, useCallback } from 'react'
import { useAuthStore } from '../lib/authStore'
import { authApi } from '../lib/api'

interface AuthError {
  message: string
  field?: string
}

export function useAuth() {
  const { token, setToken, logout } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<AuthError | null>(null)

  const isAuthenticated = Boolean(token)

  const login = useCallback(
    async (email: string, password: string): Promise<boolean> => {
      setLoading(true)
      setError(null)
      try {
        const data = await authApi.login(email, password)
        setToken(data.access_token)
        return true
      } catch (err: any) {
        const msg =
          err?.response?.data?.detail ?? 'Invalid credentials. Please try again.'
        setError({ message: msg })
        return false
      } finally {
        setLoading(false)
      }
    },
    [setToken],
  )

  const register = useCallback(
    async (
      email: string,
      password: string,
      fullName?: string,
    ): Promise<boolean> => {
      setLoading(true)
      setError(null)
      try {
        await authApi.register(email, password, fullName)
        const data = await authApi.login(email, password)
        setToken(data.access_token)
        return true
      } catch (err: any) {
        const detail = err?.response?.data?.detail
        const msg =
          typeof detail === 'string'
            ? detail
            : Array.isArray(detail)
            ? detail[0]?.msg ?? 'Registration failed.'
            : 'Registration failed. Please try again.'
        setError({ message: msg })
        return false
      } finally {
        setLoading(false)
      }
    },
    [setToken],
  )

  const clearError = useCallback(() => setError(null), [])

  return {
    isAuthenticated,
    token,
    loading,
    error,
    login,
    register,
    logout,
    clearError,
  }
}