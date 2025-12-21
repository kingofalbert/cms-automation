/**
 * Authentication Context
 *
 * Provides authentication state and methods throughout the application.
 * Integrates with Supabase Auth for session management.
 */

import React, { createContext, useContext, useEffect, useState, useCallback, useMemo, useRef } from 'react'
import { User, Session, AuthError } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'

// User role type matching database enum
export type UserRole = 'admin' | 'editor' | 'viewer'

// Extended user profile with role
export interface UserProfile {
  id: string
  email: string
  displayName: string
  role: UserRole
}

// Auth context state
interface AuthState {
  user: User | null
  profile: UserProfile | null
  session: Session | null
  loading: boolean
  error: AuthError | null
}

// Auth context methods
interface AuthContextType extends AuthState {
  signIn: (email: string, password: string) => Promise<{ error: AuthError | null }>
  signOut: () => Promise<void>
  sendMagicLink: (email: string) => Promise<{ error: AuthError | null }>
  resetPassword: (email: string) => Promise<{ error: AuthError | null }>
  isAuthenticated: boolean
  isAdmin: boolean
  isEditor: boolean
  hasRole: (roles: UserRole[]) => boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    profile: null,
    session: null,
    loading: true,
    error: null,
  })

  // Track if component is mounted to prevent state updates after unmount
  const isMountedRef = useRef(true)

  // Initialize auth state using onAuthStateChange only (avoids lock issues with getSession)
  // Using direct REST calls for profile fetching to avoid Supabase client lock issues
  // that can occur with React StrictMode double-mounting
  useEffect(() => {
    isMountedRef.current = true

    // Listen for auth changes - this handles INITIAL_SESSION on first load
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        // Check if component is still mounted before updating state
        if (!isMountedRef.current) {
          return
        }

        if ((event === 'INITIAL_SESSION' || event === 'SIGNED_IN') && session?.user) {
          // Fetch profile using direct REST call to avoid Supabase client lock issues
          try {
            const response = await fetch(
              `${import.meta.env.VITE_SUPABASE_URL}/rest/v1/profiles?id=eq.${session.user.id}&select=id,display_name,role`,
              {
                headers: {
                  'apikey': import.meta.env.VITE_SUPABASE_ANON_KEY,
                  'Authorization': `Bearer ${session.access_token}`,
                },
              }
            )

            if (!isMountedRef.current) return

            if (response.ok) {
              const data = await response.json()
              const profileData = data[0]

              if (!isMountedRef.current) return

              const profile = profileData ? {
                id: profileData.id,
                email: session.user.email || '',
                displayName: profileData.display_name || session.user.email || 'User',
                role: profileData.role as UserRole,
              } : null

              setState({
                user: session.user,
                profile,
                session,
                loading: false,
                error: null,
              })
            } else {
              console.error('Failed to fetch profile:', response.status)
              setState({
                user: session.user,
                profile: null,
                session,
                loading: false,
                error: null,
              })
            }
          } catch (err) {
            console.error('Error fetching profile:', err)
            if (isMountedRef.current) {
              setState({
                user: session.user,
                profile: null,
                session,
                loading: false,
                error: null,
              })
            }
          }
        } else if (event === 'SIGNED_OUT') {
          setState({
            user: null,
            profile: null,
            session: null,
            loading: false,
            error: null,
          })
        } else if (event === 'TOKEN_REFRESHED' && session) {
          setState(prev => ({ ...prev, session }))
        } else if (event === 'INITIAL_SESSION' && !session) {
          // No session on initial load
          setState(prev => ({ ...prev, loading: false }))
        }
      }
    )

    return () => {
      isMountedRef.current = false
      subscription.unsubscribe()
    }
  }, [])

  // Sign in with email and password
  const signIn = useCallback(async (email: string, password: string) => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) {
      setState(prev => ({ ...prev, loading: false, error }))
    }

    return { error }
  }, [])

  // Sign out
  const signOut = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true }))
    await supabase.auth.signOut()
    setState({
      user: null,
      profile: null,
      session: null,
      loading: false,
      error: null,
    })
  }, [])

  // Send magic link
  const sendMagicLink = useCallback(async (email: string) => {
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    })
    return { error }
  }, [])

  // Reset password
  const resetPassword = useCallback(async (email: string) => {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/auth/reset-password`,
    })
    return { error }
  }, [])

  // Computed properties
  const isAuthenticated = !!state.user && !!state.session
  const isAdmin = state.profile?.role === 'admin'
  const isEditor = state.profile?.role === 'editor' || isAdmin

  const hasRole = useCallback((roles: UserRole[]) => {
    if (!state.profile) return false
    return roles.includes(state.profile.role)
  }, [state.profile])

  const value = useMemo(() => ({
    ...state,
    signIn,
    signOut,
    sendMagicLink,
    resetPassword,
    isAuthenticated,
    isAdmin,
    isEditor,
    hasRole,
  }), [state, signIn, signOut, sendMagicLink, resetPassword, isAuthenticated, isAdmin, isEditor, hasRole])

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

// Hook to use auth context
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export default AuthContext
