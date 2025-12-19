/**
 * Login Page
 *
 * Provides email/password and magic link authentication.
 * Redirects to original destination after successful login.
 */

import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '@/contexts/AuthContext'
import { Card, Input, Button } from '@/components/ui'
import { Mail, Lock, Loader2, AlertCircle, CheckCircle } from 'lucide-react'

type AuthMode = 'password' | 'magic-link'

export default function LoginPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const { signIn, sendMagicLink, isAuthenticated, loading: authLoading } = useAuth()

  const [mode, setMode] = useState<AuthMode>('password')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [magicLinkSent, setMagicLinkSent] = useState(false)

  // Get redirect path from query params
  const searchParams = new URLSearchParams(location.search)
  const redirectTo = searchParams.get('redirect') || '/'

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      navigate(redirectTo, { replace: true })
    }
  }, [isAuthenticated, authLoading, navigate, redirectTo])

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const { error } = await signIn(email, password)
      if (error) {
        setError(getErrorMessage(error.message))
      }
      // Navigation handled by useEffect
    } catch (err) {
      setError(t('login.error.unexpected', 'An unexpected error occurred'))
    } finally {
      setLoading(false)
    }
  }

  const handleMagicLink = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const { error } = await sendMagicLink(email)
      if (error) {
        setError(getErrorMessage(error.message))
      } else {
        setMagicLinkSent(true)
      }
    } catch (err) {
      setError(t('login.error.unexpected', 'An unexpected error occurred'))
    } finally {
      setLoading(false)
    }
  }

  const getErrorMessage = (message: string): string => {
    if (message.includes('Invalid login credentials')) {
      return t('login.error.invalidCredentials', 'Invalid email or password')
    }
    if (message.includes('Email not confirmed')) {
      return t('login.error.emailNotConfirmed', 'Please confirm your email first')
    }
    if (message.includes('Too many requests')) {
      return t('login.error.tooManyRequests', 'Too many attempts. Please try again later.')
    }
    return message
  }

  // Show loading spinner while checking auth state
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">
            CMS Automation
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            {t('login.subtitle', 'Sign in to your account')}
          </p>
        </div>

        {/* Login Card */}
        <Card className="p-8">
          {/* Mode Toggle */}
          <div className="flex rounded-lg bg-gray-100 p-1 mb-6">
            <button
              type="button"
              onClick={() => { setMode('password'); setMagicLinkSent(false); setError(null) }}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                mode === 'password'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {t('login.mode.password', 'Password')}
            </button>
            <button
              type="button"
              onClick={() => { setMode('magic-link'); setError(null) }}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                mode === 'magic-link'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {t('login.mode.magicLink', 'Magic Link')}
            </button>
          </div>

          {/* Magic Link Success Message */}
          {magicLinkSent && mode === 'magic-link' ? (
            <div className="text-center py-8">
              <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {t('login.magicLink.sent', 'Check your email')}
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                {t('login.magicLink.description', 'We sent a login link to')} <strong>{email}</strong>
              </p>
              <button
                type="button"
                onClick={() => setMagicLinkSent(false)}
                className="text-sm text-blue-600 hover:text-blue-500"
              >
                {t('login.magicLink.tryAgain', 'Send another link')}
              </button>
            </div>
          ) : (
            <form onSubmit={mode === 'password' ? handlePasswordLogin : handleMagicLink}>
              {/* Error Message */}
              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                  <span className="text-sm text-red-700">{error}</span>
                </div>
              )}

              {/* Email Field */}
              <div className="mb-4">
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                  {t('login.email', 'Email')}
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="pl-10"
                    required
                    autoComplete="email"
                  />
                </div>
              </div>

              {/* Password Field (only for password mode) */}
              {mode === 'password' && (
                <div className="mb-6">
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                    {t('login.password', 'Password')}
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <Input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="********"
                      className="pl-10"
                      required
                      autoComplete="current-password"
                    />
                  </div>
                </div>
              )}

              {/* Submit Button */}
              <Button
                type="submit"
                className="w-full"
                disabled={loading || !email || (mode === 'password' && !password)}
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : mode === 'password' ? (
                  t('login.submit.password', 'Sign In')
                ) : (
                  t('login.submit.magicLink', 'Send Magic Link')
                )}
              </Button>

              {/* Forgot Password Link */}
              {mode === 'password' && (
                <div className="mt-4 text-center">
                  <button
                    type="button"
                    onClick={() => setMode('magic-link')}
                    className="text-sm text-blue-600 hover:text-blue-500"
                  >
                    {t('login.forgotPassword', 'Forgot your password?')}
                  </button>
                </div>
              )}
            </form>
          )}
        </Card>

        {/* Footer */}
        <p className="text-center text-sm text-gray-500">
          {t('login.footer', 'Contact your administrator if you need access.')}
        </p>
      </div>
    </div>
  )
}
