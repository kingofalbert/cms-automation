/**
 * Authentication Context
 *
 * Provides authentication state and methods throughout the application.
 * Integrates with Supabase Auth for session management.
 */

import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from 'react'
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

  // Fetch user profile from profiles table
  // Note: We pass userEmail as a parameter to avoid dependency on state.user
  // which would cause an infinite re-render loop (fetchProfile -> setState ->
  // state.user changes -> fetchProfile recreated -> useEffect runs again)
  const fetchProfile = useCallback(async (userId: string, userEmail?: string): Promise<UserProfile | null> => {
    try {
      const { data, error } = await supabase
        .from('profiles')
        .select('id, display_name, role')
        .eq('id', userId)
        .single()

      if (error) {
        console.error('Error fetching profile:', error)
        return null
      }

      return {
        id: data.id,
        email: userEmail || '',
        displayName: data.display_name || userEmail || 'User',
        role: data.role as UserRole,
      }
    } catch (err) {
      console.error('Error in fetchProfile:', err)
      return null
    }
  }, [])  // No dependencies - stable function reference

  // Initialize auth state
  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(async ({ data: { session }, error }) => {
      if (error) {
        setState(prev => ({ ...prev, loading: false, error }))
        return
      }

      if (session?.user) {
        const profile = await fetchProfile(session.user.id, session.user.email)
        setState({
          user: session.user,
          profile,
          session,
          loading: false,
          error: null,
        })
      } else {
        setState(prev => ({ ...prev, loading: false }))
      }
    })

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('Auth state changed:', event)

        if (event === 'SIGNED_IN' && session?.user) {
          const profile = await fetchProfile(session.user.id, session.user.email)
          setState({
            user: session.user,
            profile,
            session,
            loading: false,
            error: null,
          })
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
        }
      }
    )

    return () => {
      subscription.unsubscribe()
    }
  }, [fetchProfile])

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
