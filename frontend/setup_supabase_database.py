"""Script to set up Supabase database trigger for Curriculum Studio.
This script creates the trigger that auto-creates curriculum_studio_users entries
when a new user signs up via Supabase Auth.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Get service role key from environment
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://rqhpxwlsrgbxsqgpmolc.supabase.co")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ ERROR: SUPABASE_SERVICE_ROLE_KEY not found in environment variables")
    print("Please set SUPABASE_SERVICE_ROLE_KEY in your .env file or environment")
    exit(1)

# Create admin client
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# SQL to create the trigger function and trigger
TRIGGER_SQL = """
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
"""

def setup_database_trigger():
    """Set up the database trigger for auto-creating curriculum_studio_users entries."""
    print("🔧 Setting up database trigger...")
    print("=" * 50)
    
    try:
        # Execute SQL using Supabase RPC or direct SQL execution
        # Note: Supabase Python client doesn't support direct SQL execution
        # You'll need to run this SQL in Supabase Dashboard → SQL Editor
        
        print("⚠️  Note: Supabase Python client doesn't support direct SQL execution.")
        print("Please run the following SQL in Supabase Dashboard → SQL Editor:")
        print("=" * 50)
        print(TRIGGER_SQL)
        print("=" * 50)
        
        # Alternative: Check if trigger exists by querying information_schema
        print("\n✅ SQL script ready!")
        print("\n📋 Next Steps:")
        print("1. Go to Supabase Dashboard → SQL Editor")
        print("2. Copy and paste the SQL above")
        print("3. Click 'Run' to execute")
        print("4. Verify trigger is created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    setup_database_trigger()

