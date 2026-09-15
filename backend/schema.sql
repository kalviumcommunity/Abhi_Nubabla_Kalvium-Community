-- ===================================================
-- Supabase PostgreSQL Schema for Backend User Credentials Storage
-- ===================================================

-- 1. Create a custom ENUM for roles if not existing
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('user', 'admin');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Create the public.users table for storing user credentials and profiles
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role user_role NOT NULL DEFAULT 'user',
    history JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure history column exists on existing public.users tables
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS history JSONB DEFAULT '[]'::jsonb;

-- 3. Enable Row Level Security (RLS) on public.users
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- 4. RLS Policy: Allow service role / backend API full access to public.users
DROP POLICY IF EXISTS "Backend API full access" ON public.users;
CREATE POLICY "Backend API full access" ON public.users
    FOR ALL
    USING (true)
    WITH CHECK (true);
