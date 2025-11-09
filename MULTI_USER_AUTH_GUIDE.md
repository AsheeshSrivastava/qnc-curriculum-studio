# Multi-User Authentication System

## Overview

The Curriculum Studio now supports **multi-user authentication** with role-based access control (RBAC).

## Features

✅ **Multi-User Support**: Multiple users can have separate accounts  
✅ **Role-Based Access**: Admin and User roles with different permissions  
✅ **Secure Authentication**: SHA-256 password hashing  
✅ **Usage Tracking**: Track login times and usage counts  
✅ **Admin Panel**: Manage users through a web interface  

---

## User Roles

### 👑 Admin
- Full access to all features
- Can add/remove users
- Can view usage statistics
- Access to Admin Panel

### 👤 User
- Can upload documents
- Can generate content
- Can use AXIS AI Chat
- **Cannot** manage other users

---

## Default Credentials

**Admin Account:**
- Username: `admin`
- Password: `aethelgard2024`

⚠️ **Change this password in production!**

---

## How to Add Users

### Method 1: Admin Panel (Recommended)

1. Login as `admin`
2. Navigate to **Admin Panel** (sidebar)
3. Go to **"Add User"** tab
4. Fill in:
   - Username (min 3 characters)
   - Password (min 6 characters)
   - Role (Admin or User)
5. Click **"Create User"**
6. Share credentials securely with the new user

### Method 2: Programmatically (Python)

```python
from auth import add_user, ROLE_USER

# Add a test user
success, message = add_user("testuser", "password123", ROLE_USER)
print(message)
```

---

## User Database

### Location
`frontend/users.json`

### Structure
```json
{
  "username": {
    "password_hash": "sha256_hash_here",
    "role": "admin" or "user",
    "created_at": "2025-01-01T00:00:00",
    "last_login": "2025-01-01T00:00:00",
    "usage_count": 0
  }
}
```

### Security
- ✅ Passwords are **hashed** using SHA-256
- ✅ `users.json` is in `.gitignore` (not committed to Git)
- ✅ Admin user cannot be deleted
- ✅ No plaintext passwords stored

---

## Deployment to Streamlit Cloud

### Step 1: Create User Database Locally

1. Run the app locally:
   ```bash
   cd frontend
   streamlit run app.py
   ```

2. Login as `admin` (password: `aethelgard2024`)

3. Go to **Admin Panel** → **Add User**

4. Create test users

5. The `users.json` file will be created automatically

### Step 2: Deploy to Streamlit Cloud

1. **Option A: Upload via Streamlit Secrets** (Recommended)
   
   - Copy the contents of `users.json`
   - In Streamlit Cloud dashboard, go to **App Settings** → **Secrets**
   - Add:
     ```toml
     [users]
     database = '''
     {
       "admin": {
         "password_hash": "...",
         "role": "admin",
         ...
       }
     }
     '''
     ```
   - Update `auth.py` to read from `st.secrets.users.database` if available

2. **Option B: Manual Upload** (Simpler for MVP)
   
   - After deploying, the app will create a default `admin` user
   - Login and use Admin Panel to add users
   - **Note**: Users will be lost if app restarts (Streamlit Cloud ephemeral storage)

### Step 3: Persistent Storage (Production)

For production, use one of these:

1. **Supabase** (Recommended)
   - Free PostgreSQL database
   - Built-in auth
   - Persistent storage

2. **Streamlit Secrets** (Simple)
   - Store user database in secrets
   - Load on startup

3. **External Database**
   - PostgreSQL, MySQL, etc.
   - Most robust option

---

## Usage Examples

### Example Test Users

Here are some example users you can create for testing:

| Username | Password | Role | Purpose |
|----------|----------|------|---------|
| `admin` | `aethelgard2024` | Admin | Administrator |
| `tester1` | `test123` | User | Test user 1 |
| `tester2` | `test456` | User | Test user 2 |
| `demo` | `demo123` | User | Demo account |

### Testing Workflow

1. **Login as admin**
   - Create 2-3 test users
   - Verify they appear in Admin Panel

2. **Logout and login as test user**
   - Verify they can access Upload and Chat
   - Verify they **cannot** access Admin Panel

3. **Check usage tracking**
   - Login as admin
   - Go to Admin Panel → Usage Statistics
   - Verify login times and usage counts

---

## Security Best Practices

1. ✅ **Change default admin password** immediately
2. ✅ **Use strong passwords** (min 8 characters, mix of letters/numbers/symbols)
3. ✅ **Don't commit `users.json`** to Git (already in `.gitignore`)
4. ✅ **Share credentials securely** (use encrypted channels)
5. ✅ **Regularly review users** in Admin Panel
6. ✅ **Remove inactive users** to prevent unauthorized access

---

## Troubleshooting

### Issue: "users.json not found"
**Solution**: The app will create it automatically on first run with default admin user.

### Issue: "Cannot access Admin Panel"
**Solution**: Only users with `role: "admin"` can access. Login as `admin` first.

### Issue: "Invalid username or password"
**Solution**: 
- Check username spelling (case-sensitive)
- Verify password
- If locked out, delete `users.json` to reset to default admin

### Issue: "Users lost after app restart on Streamlit Cloud"
**Solution**: Streamlit Cloud uses ephemeral storage. Use Streamlit Secrets or external database for persistence.

---

## Future Enhancements

- 🔄 Password reset functionality
- 🔄 Email verification
- 🔄 Session timeout
- 🔄 Rate limiting per user
- 🔄 Audit logs
- 🔄 Two-factor authentication (2FA)

---

## Questions?

Contact the administrator or refer to the main README.md for more information.

