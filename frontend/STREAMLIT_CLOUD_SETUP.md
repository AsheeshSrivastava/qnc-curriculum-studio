# 🚀 Streamlit Cloud Setup Guide

## Adding Secrets to Streamlit Cloud Dashboard

Since your app is **already deployed** on Streamlit Cloud, you need to add secrets through the **Streamlit Cloud Dashboard** (not a local file).

### Step 1: Go to Streamlit Cloud Dashboard

1. Visit: https://share.streamlit.io
2. Sign in with your GitHub account
3. Find your **Curriculum Studio** app
4. Click on your app to open it

### Step 2: Add Secrets

1. Click **"☰" (Menu)** → **"Settings"**
2. Scroll down to **"Secrets"** section
3. Click **"Edit secrets"** or **"Add secrets"**

### Step 3: Add These Secrets

Copy and paste this into the secrets editor:

```toml
# Supabase Configuration
SUPABASE_URL = "https://rqhpxwlsrgbxsqgpmolc.supabase.co"
SUPABASE_ANON_KEY = "paste_your_anon_key_here"
SUPABASE_SERVICE_ROLE_KEY = "paste_your_service_role_key_here"

# Backend API Configuration (Your Render URL)
BACKEND_URL = "https://your-backend-service.onrender.com"
```

### Step 4: Get Your Keys

**Supabase Keys:**
1. Go to: https://supabase.com/dashboard
2. Select **Curriculum Studio** project
3. Go to: **Settings → API**
4. Copy:
   - **anon** `public` key → Replace `paste_your_anon_key_here`
   - **service_role** `secret` key → Replace `paste_your_service_role_key_here`

**Render Backend URL:**
1. Go to: https://dashboard.render.com
2. Find your backend service
3. Copy the URL (e.g., `https://curriculum-studio-backend.onrender.com`)
4. Replace `https://your-backend-service.onrender.com`

### Step 5: Configure Supabase Auth URLs ⚠️ IMPORTANT

**Before testing, you MUST configure Site URL and Redirect URLs in Supabase:**

1. Go to Supabase Dashboard → **Authentication → URL Configuration**
2. Set **Site URL** to your Streamlit Cloud URL:
   ```
   https://your-app-name.streamlit.app
   ```
3. Add **Redirect URLs**:
   ```
   https://your-app-name.streamlit.app
   https://your-app-name.streamlit.app/*
   ```
4. Click **"Save"**

📖 **See `SUPABASE_AUTH_CONFIG.md` for detailed instructions.**

### Step 6: Save and Redeploy

1. Click **"Save"** in the Streamlit secrets editor
2. Streamlit will automatically **redeploy** your app
3. Wait for deployment to complete (usually 1-2 minutes)

### Step 7: Test

1. Open your Streamlit app URL
2. You should see the **login page**
3. If you haven't created a user yet, use the **Sign Up** tab
4. Or create an admin user via Supabase Dashboard (see below)

## ✅ Creating Your First Admin User

### Option 1: Via Supabase Dashboard (Recommended)

1. Go to Supabase Dashboard → **Authentication → Users**
2. Click **"Add User"**
3. Enter:
   - Email: `your-email@example.com`
   - Password: `YourSecurePassword123!`
   - ✅ Check **"Auto Confirm User"**
4. Click **"Create User"**

### Option 2: Via Streamlit App

1. Use the **Sign Up** tab on the login page
2. Enter email and password
3. Check your email for confirmation (or auto-confirm in Supabase)

### Set Admin Role

After creating the user, set admin role:

1. Go to Supabase Dashboard → **SQL Editor**
2. Run this SQL:
   ```sql
   UPDATE curriculum_studio_users 
   SET role = 'admin' 
   WHERE email = 'your-email@example.com';
   ```
   (Replace with your actual email)

## 🎯 What Gets Deployed

- ✅ **No local `secrets.toml` needed** - Secrets are stored securely in Streamlit Cloud
- ✅ **Automatic redeploy** - App restarts when you save secrets
- ✅ **Secure storage** - Secrets are encrypted and never exposed in code

## 🐛 Troubleshooting

**"SUPABASE_ANON_KEY is required"**
- Check that secrets are saved correctly in Streamlit Cloud
- Make sure there are no extra spaces or quotes
- Try redeploying the app

**"Backend connection failed"**
- Verify `BACKEND_URL` is your correct Render URL
- Make sure your Render backend is running
- Check that Render URL doesn't have trailing slash

**"Invalid login credentials"**
- Verify user exists in Supabase Dashboard → Authentication → Users
- Make sure user is confirmed (check "Auto Confirm User" when creating)
- Check email spelling

## 📝 Example Secrets Format

Your secrets should look exactly like this (with your actual values):

```toml
SUPABASE_URL = "https://rqhpxwlsrgbxsqgpmolc.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJxaHB4d2xzcmdieHNxZ3Btb2xjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI4NzQ2MzMsImV4cCI6MjA3ODQ1MDYzM30.example"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJxaHB4d2xzcmdieHNxZ3Btb2xjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2Mjg3NDYzMywiZXhwIjoyMDc4NDUwNjMzfQ.example"
BACKEND_URL = "https://curriculum-studio-backend.onrender.com"
```

**Important:** 
- Use **double quotes** around values
- No spaces around the `=` sign
- Each secret on its own line

---

**That's it!** Once secrets are added, your app will automatically use Supabase for authentication. 🎉

