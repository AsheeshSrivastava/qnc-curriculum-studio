# 🗄️ Database Setup Guide - Curriculum Studio

## Overview

This guide explains how to set up the database trigger that automatically creates `curriculum_studio_users` entries when new users sign up via Supabase Auth.

## Access Levels

### 👑 Admin Role
- **Full access** to all features
- Can manage users (add/remove)
- Can access Admin Panel
- Can view usage statistics
- Can create users directly via Admin Panel

### 👤 User Role (Regular)
- **Standard access** to curriculum tools
- Can upload documents
- Can generate content
- Can use AXIS AI Chat
- **Cannot** manage users
- **Cannot** access Admin Panel

## Database Trigger Setup

### Why This Trigger is Needed

When a user signs up via the **Sign Up** tab or is created via **Admin Panel**, Supabase Auth creates an entry in `auth.users`. However, we also need an entry in `curriculum_studio_users` table to store the user's role and other metadata.

The trigger automatically creates this entry with default role `'user'`.

### Step 1: Run the SQL Script

1. Go to: https://supabase.com/dashboard
2. Select **Curriculum Studio** project
3. Navigate to: **SQL Editor**
4. Click **"New Query"**
5. Copy and paste the SQL from `setup_database_trigger.sql`:

```sql
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
```

6. Click **"Run"** to execute the SQL
7. You should see: ✅ Success. No rows returned

### Step 2: Verify Trigger is Working

1. Go to: **Authentication → Users**
2. Create a test user (or use Sign Up tab in the app)
3. Go to: **Table Editor → curriculum_studio_users**
4. Verify that a new entry was created with:
   - `id` matching the auth user ID
   - `email` matching the auth user email
   - `role` set to `'user'`

## User Registration Flow

### Option 1: Self-Registration (Sign Up Tab)

1. User goes to login page
2. Clicks **"Sign Up"** tab
3. Enters email and password
4. Clicks **"Create Account"**
5. **Trigger automatically creates** `curriculum_studio_users` entry with role `'user'`
6. User can sign in immediately (if email confirmation is disabled) or after email confirmation

### Option 2: Admin Creates User (Admin Panel)

1. Admin logs in and goes to **Admin Panel**
2. Clicks **"➕ Add User"** tab
3. Enters email, password, and selects role (Admin or User)
4. Clicks **"➕ Create User"**
5. **Trigger automatically creates** `curriculum_studio_users` entry
6. Admin Panel then **updates the role** to the selected role (Admin or User)
7. User can sign in immediately

## Creating Your First Admin

### Method 1: Via Supabase Dashboard (Recommended)

1. Go to: **Authentication → Users**
2. Click **"Add User"**
3. Enter:
   - Email: `admin@example.com`
   - Password: `YourSecurePassword123!`
   - ✅ Check **"Auto Confirm User"**
4. Click **"Create User"**
5. Go to: **SQL Editor**
6. Run this SQL to set admin role:

```sql
UPDATE curriculum_studio_users 
SET role = 'admin' 
WHERE email = 'admin@example.com';
```

### Method 2: Via Admin Panel (After First Admin Exists)

1. Log in as an existing admin
2. Go to **Admin Panel → ➕ Add User**
3. Enter email, password
4. Select **"👑 Admin (Full Access)"** from role dropdown
5. Click **"➕ Create User"**

## Access Control Verification

### Admin Access
- ✅ Can access Admin Panel (`pages/3_👤_Admin_Panel.py`)
- ✅ Can see all users
- ✅ Can create/delete users
- ✅ Can view usage statistics

### User Access
- ✅ Can access Workspace (`pages/2_🎯_Workspace.py`)
- ✅ Can use AXIS AI Chat
- ✅ Can generate content
- ❌ Cannot access Admin Panel (shows "Access Denied")
- ❌ Cannot manage users

## Troubleshooting

### Trigger Not Creating Entries

**Check if trigger exists:**
```sql
SELECT * FROM pg_trigger WHERE tgname = 'on_auth_user_created_curriculum';
```

**Check trigger function:**
```sql
SELECT * FROM pg_proc WHERE proname = 'handle_new_curriculum_user';
```

**Re-run the trigger setup SQL** if trigger doesn't exist.

### User Created But No Entry in curriculum_studio_users

1. Check Supabase logs: **Logs → Postgres Logs**
2. Look for errors in `handle_new_curriculum_user` function
3. Manually create entry:

```sql
INSERT INTO curriculum_studio_users (id, email, role)
SELECT id, email, 'user'
FROM auth.users
WHERE id NOT IN (SELECT id FROM curriculum_studio_users);
```

### Admin Can't Access Admin Panel

1. Verify role in database:
```sql
SELECT id, email, role FROM curriculum_studio_users WHERE email = 'your-email@example.com';
```

2. If role is `'user'`, update it:
```sql
UPDATE curriculum_studio_users 
SET role = 'admin' 
WHERE email = 'your-email@example.com';
```

3. Sign out and sign back in to refresh session

## Security Notes

- ✅ **Default Role**: All new signups get `'user'` role by default
- ✅ **Admin Creation**: Only existing admins can create new admins via Admin Panel
- ✅ **Direct Database Access**: Admins can also be created directly in Supabase Dashboard + SQL Editor
- ✅ **Password Security**: All passwords are hashed by Supabase Auth
- ✅ **Session Management**: Roles are checked on each page load

---

**Next Step:** After setting up the trigger, test the sign-up flow and admin creation! 🚀

