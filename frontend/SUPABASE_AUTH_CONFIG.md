# 🔐 Supabase Auth Configuration for Streamlit Cloud

## Required Supabase Settings

Before testing your Streamlit Cloud deployment, you need to configure **Site URL** and **Redirect URLs** in Supabase Dashboard.

### Step 1: Get Your Streamlit Cloud URL

1. Go to: https://share.streamlit.io
2. Find your **Curriculum Studio** app
3. Copy your app URL (e.g., `https://your-app-name.streamlit.app`)

### Step 2: Configure Supabase Auth Settings

1. Go to: https://supabase.com/dashboard
2. Select **Curriculum Studio** project
3. Navigate to: **Authentication → URL Configuration**

### Step 3: Set Site URL

**Site URL** should be your Streamlit Cloud app URL:

```
https://your-app-name.streamlit.app
```

**Example:**
```
https://curriculum-studio.streamlit.app
```

### Step 4: Set Redirect URLs

Add your Streamlit Cloud URL to **Redirect URLs** (one per line):

```
https://your-app-name.streamlit.app
https://your-app-name.streamlit.app/*
```

**Example:**
```
https://curriculum-studio.streamlit.app
https://curriculum-studio.streamlit.app/*
```

**Note:** The `/*` wildcard allows redirects to any path within your app.

### Step 5: Optional - Add Local Development URL

If you want to test locally, also add:

```
http://localhost:8501
http://localhost:8501/*
```

### Complete Configuration Example

**Site URL:**
```
https://curriculum-studio.streamlit.app
```

**Redirect URLs:**
```
https://curriculum-studio.streamlit.app
https://curriculum-studio.streamlit.app/*
http://localhost:8501
http://localhost:8501/*
```

## Why These Settings Matter

- **Site URL**: Used by Supabase Auth for email confirmation links and OAuth redirects
- **Redirect URLs**: Whitelist of allowed redirect destinations after authentication
- **Security**: Prevents unauthorized redirects to malicious sites

## Important Notes

1. ✅ **Email/Password Auth**: Since we're using email/password authentication (not OAuth), redirect URLs are less critical, but still recommended for security
2. ✅ **Email Confirmation**: If you enable email confirmation, the confirmation link will use the Site URL
3. ✅ **OAuth (Future)**: If you add OAuth providers later (Google, GitHub, etc.), redirect URLs become essential

## Verification Checklist

- [ ] Site URL set to your Streamlit Cloud URL
- [ ] Redirect URLs include your Streamlit Cloud URL (with and without `/*`)
- [ ] Optional: Local development URLs added for testing
- [ ] Click **"Save"** in Supabase Dashboard

## After Configuration

1. Your Streamlit app should be able to authenticate users
2. Email confirmation links (if enabled) will work correctly
3. Future OAuth integrations will work seamlessly

---

**Next Step:** Test your Streamlit Cloud deployment! 🚀




