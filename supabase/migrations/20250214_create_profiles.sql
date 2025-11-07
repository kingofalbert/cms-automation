-- 2025-02-14: Supabase Auth Profiles + RLS
-- Applies the foundational schema required for Supabase-based user management.

-- 1) Role enum ----------------------------------------------------------------
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
    CREATE TYPE public.user_role AS ENUM ('admin', 'editor', 'viewer');
  END IF;
END$$;

-- 2) Profiles table -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
  id uuid PRIMARY KEY REFERENCES auth.users (id) ON DELETE CASCADE,
  display_name text,
  role public.user_role NOT NULL DEFAULT 'editor',
  created_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
  updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
);

CREATE UNIQUE INDEX IF NOT EXISTS profiles_id_key ON public.profiles (id);

-- 3) Timestamp trigger --------------------------------------------------------
CREATE OR REPLACE FUNCTION public.set_profiles_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = timezone('utc', now());
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_profiles_updated_at ON public.profiles;
CREATE TRIGGER trg_profiles_updated_at
BEFORE UPDATE ON public.profiles
FOR EACH ROW
EXECUTE PROCEDURE public.set_profiles_updated_at();

-- 4) Auto-provision profile after signup -------------------------------------
CREATE OR REPLACE FUNCTION public.handle_new_user_profile()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  default_role public.user_role := 'editor';
  requested_role text;
BEGIN
  -- Optional: honor metadata role if provided and valid
  requested_role := (new.raw_user_meta_data->>'role');
  IF requested_role IS NOT NULL AND requested_role = ANY (ARRAY['admin','editor','viewer']) THEN
    default_role := requested_role::public.user_role;
  END IF;

  INSERT INTO public.profiles (id, display_name, role)
  VALUES (
    new.id,
    COALESCE(new.raw_user_meta_data->>'display_name', new.email, 'New User'),
    default_role
  )
  ON CONFLICT (id) DO NOTHING;

  RETURN new;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW
EXECUTE PROCEDURE public.handle_new_user_profile();

-- 5) Helper to detect admins --------------------------------------------------
CREATE OR REPLACE FUNCTION public.is_admin(uid uuid)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  result boolean;
BEGIN
  IF uid IS NULL THEN
    RETURN FALSE;
  END IF;

  SELECT EXISTS (
    SELECT 1 FROM public.profiles p
    WHERE p.id = uid AND p.role = 'admin'
  )
  INTO result;

  RETURN COALESCE(result, FALSE);
END;
$$;

GRANT EXECUTE ON FUNCTION public.is_admin(uuid) TO anon, authenticated, service_role;

-- 6) Row Level Security policies ---------------------------------------------
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Profiles are selectable by self or admins" ON public.profiles;
CREATE POLICY "Profiles are selectable by self or admins"
ON public.profiles
FOR SELECT
USING (
  auth.uid() = id
  OR public.is_admin(auth.uid())
);

DROP POLICY IF EXISTS "Admins insert profiles" ON public.profiles;
CREATE POLICY "Admins insert profiles"
ON public.profiles
FOR INSERT
WITH CHECK (public.is_admin(auth.uid()));

DROP POLICY IF EXISTS "Admins update profiles" ON public.profiles;
CREATE POLICY "Admins update profiles"
ON public.profiles
FOR UPDATE
USING (public.is_admin(auth.uid()))
WITH CHECK (public.is_admin(auth.uid()));

DROP POLICY IF EXISTS "Admins delete profiles" ON public.profiles;
CREATE POLICY "Admins delete profiles"
ON public.profiles
FOR DELETE
USING (public.is_admin(auth.uid()));

-- Optional: allow users to read their own role without admin check via RPC.
COMMENT ON TABLE public.profiles IS 'User profile & role metadata mirrored from Supabase auth.users';
COMMENT ON COLUMN public.profiles.role IS 'Authorization role (admin/editor/viewer)';
