"""Authentication module for Curriculum Studio - Multi-User with Roles."""

import streamlit as st
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


# User roles
ROLE_ADMIN = "admin"
ROLE_USER = "user"

# User database file
USER_DB_FILE = Path("users.json")


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == hashed_password


def load_users() -> Dict:
    """
    Load user database from JSON file.
    
    Structure:
    {
        "username": {
            "password_hash": "...",
            "role": "admin" or "user",
            "created_at": "2025-01-01T00:00:00",
            "last_login": "2025-01-01T00:00:00",
            "usage_count": 0
        }
    }
    """
    # Create default admin user if file doesn't exist
    if not USER_DB_FILE.exists():
        default_users = {
            "admin": {
                "password_hash": hash_password("aethelgard2024"),
                "role": ROLE_ADMIN,
                "created_at": datetime.now().isoformat(),
                "last_login": None,
                "usage_count": 0,
            }
        }
        save_users(default_users)
        return default_users
    
    try:
        with open(USER_DB_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading user database: {e}")
        return {}


def save_users(users: Dict) -> bool:
    """Save user database to JSON file."""
    try:
        with open(USER_DB_FILE, "w") as f:
            json.dump(users, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving user database: {e}")
        return False


def add_user(username: str, password: str, role: str = ROLE_USER) -> tuple[bool, str]:
    """
    Add a new user to the database.
    
    Returns:
        (success: bool, message: str)
    """
    users = load_users()
    
    # Check if user already exists
    if username in users:
        return False, "Username already exists"
    
    # Validate username
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    # Validate password
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    # Add user
    users[username] = {
        "password_hash": hash_password(password),
        "role": role,
        "created_at": datetime.now().isoformat(),
        "last_login": None,
        "usage_count": 0,
    }
    
    if save_users(users):
        return True, f"User '{username}' created successfully"
    else:
        return False, "Failed to save user database"


def remove_user(username: str) -> tuple[bool, str]:
    """
    Remove a user from the database.
    
    Returns:
        (success: bool, message: str)
    """
    users = load_users()
    
    # Prevent removing admin
    if username == "admin":
        return False, "Cannot remove admin user"
    
    # Check if user exists
    if username not in users:
        return False, "User not found"
    
    # Remove user
    del users[username]
    
    if save_users(users):
        return True, f"User '{username}' removed successfully"
    else:
        return False, "Failed to save user database"


def update_user_login(username: str):
    """Update user's last login time and usage count."""
    users = load_users()
    
    if username in users:
        users[username]["last_login"] = datetime.now().isoformat()
        users[username]["usage_count"] = users[username].get("usage_count", 0) + 1
        save_users(users)


def get_user_role(username: str) -> Optional[str]:
    """Get user's role."""
    users = load_users()
    return users.get(username, {}).get("role")


def is_admin(username: str) -> bool:
    """Check if user is admin."""
    return get_user_role(username) == ROLE_ADMIN


def load_credentials() -> dict:
    """
    Legacy function for backward compatibility.
    Now loads from multi-user database.
    """
    users = load_users()
    admin_user = users.get("admin", {})
    
    return {
        "username": "admin",
        "password_hash": admin_user.get("password_hash", hash_password("aethelgard2024")),
    }


def check_authentication() -> bool:
    """
    Check if user is authenticated.
    Returns True if authenticated, False otherwise.
    """
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
    
    return st.session_state.authenticated


def login_page():
    """Display login page with multi-user support."""
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Logo and branding
        try:
            st.image("assets/Logo_Primary.png", use_container_width=True)
        except Exception:
            st.markdown("# 🎓")
        
        st.markdown(
            """
            <div style='text-align: center; margin: 20px 0;'>
                <h2 style='color: #2E5266; margin: 0;'>Quest and Crossfire™</h2>
                <p style='color: #6E8898; font-size: 1.1em; margin: 5px 0;'>Aethelgard Academy™</p>
                <h3 style='color: #D3A625; margin: 10px 0;'>Curriculum Studio</h3>
                <p style='color: #6E8898; font-style: italic; margin: 5px 0;'>"Small Fixes, Big Clarity"</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        st.markdown("---")
        
        # Login form
        st.markdown("### 🔐 Login")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if submit:
                users = load_users()
                
                # Check if user exists
                if username in users:
                    user_data = users[username]
                    
                    # Verify password
                    if verify_password(password, user_data["password_hash"]):
                        # Successful login
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.user_role = user_data["role"]
                        
                        # Update login stats
                        update_user_login(username)
                        
                        st.success(f"✅ Welcome back, {username}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.error("❌ Invalid username or password")
        
        st.markdown("---")
        
        # Help text
        with st.expander("ℹ️ Need Help?"):
            st.markdown("""
            **Default Admin Credentials:**
            - Username: `admin`
            - Password: `aethelgard2024`
            
            **For Test Users:**
            Contact the administrator to create an account for you.
            
            **Security Note:**
            All passwords are hashed using SHA-256. Never share your password.
            """)


def logout():
    """Logout the current user."""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.rerun()


def require_authentication():
    """
    Decorator/wrapper to require authentication for a page.
    Call this at the top of each page that requires authentication.
    """
    if not check_authentication():
        login_page()
        st.stop()



