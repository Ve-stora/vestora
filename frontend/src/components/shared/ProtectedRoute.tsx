import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../lib/authStore'

interface ProtectedRouteProps {
  /** Fallback redirect path. Defaults to /login */
  redirectTo?: string
  /** Render children directly instead of <Outlet /> */
  children?: React.ReactNode
}

/**
 * Wraps routes that require authentication.
 * If the user is not authenticated, redirects to `redirectTo` and preserves
 * the attempted path in location.state so LoginPage can redirect back after login.
 */
export default function ProtectedRoute({
  redirectTo = '/login',
  children,
}: ProtectedRouteProps) {
  const token = useAuthStore((s) => s.token)
  const location = useLocation()

  if (!token) {
    return (
      <Navigate
        to={redirectTo}
        state={{ from: location }}
        replace
      />
    )
  }

  return children ? <>{children}</> : <Outlet />
}