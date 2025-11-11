-- ============================================
-- Curriculum Studio - Database Trigger Setup
-- Auto-create curriculum_studio_users entry when auth user is created
-- ============================================

-- Function to automatically create curriculum_studio_users entry when user signs up
CREATE OR REPLACE FUNCTION public.handle_new_curriculum_user()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql
AS $$
BEGIN
  INSERT INTO public.curriculum_studio_users (id, email, role)
  VALUES (
    NEW.id,
    NEW.email,
    'user' -- Default role for new signups
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
EXCEPTION
  WHEN others THEN
    RAISE LOG 'Error in handle_new_curriculum_user: %', SQLERRM;
    RETURN NEW;
END;
$$;

-- Grant execute permission to auth admin
GRANT EXECUTE ON FUNCTION public.handle_new_curriculum_user() TO supabase_auth_admin;

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS on_auth_user_created_curriculum ON auth.users;

-- Create trigger to auto-create curriculum_studio_users entry
CREATE TRIGGER on_auth_user_created_curriculum
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_curriculum_user();

-- ============================================
-- Verify the trigger is set up correctly
-- ============================================
-- You can test by creating a user in Supabase Auth Dashboard
-- and checking if an entry appears in curriculum_studio_users table

