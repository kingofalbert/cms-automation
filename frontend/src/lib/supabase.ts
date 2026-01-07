/**
 * Supabase client configuration
 *
 * Provides a singleton Supabase client for authentication and database operations.
 * Uses lazy initialization to prevent crashes when environment variables are missing.
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://twsbhjmlmspjwfystpti.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

let _supabase: SupabaseClient | null = null;

/**
 * Get or create the Supabase client instance.
 * Returns null if the anon key is not configured.
 */
function getSupabaseClient(): SupabaseClient | null {
  if (!supabaseAnonKey) {
    console.warn('Supabase anon key is not set. Authentication will not work.');
    return null;
  }

  if (!_supabase) {
    _supabase = createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
      },
    });
  }

  return _supabase;
}

// Export as a getter to allow lazy initialization
// This prevents the app from crashing if env vars are missing
export const supabase = getSupabaseClient();
