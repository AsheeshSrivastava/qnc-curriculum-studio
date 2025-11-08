"""Authentication module for Curriculum Studio."""

import streamlit as st
import hashlib
import os
from pathlib import Path


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == hashed_password


def load_credentials() -> dict:
    """
    Load credentials from environment variables or use defaults.
    
    For production, set these environment variables:
    - AUTH_USERNAME: The username
    - AUTH_PASSWORD_HASH: The SHA-256 hash of the password
    
    Default credentials (for development):
    - Username: admin
    - Password: aethelgard2024
    """
    # Default credentials (hashed password for "aethelgard2024")
    default_username = "admin"
    default_password_hash = hash_password("aethelgard2024")
    
    # Try to load from environment
    username = os.getenv("AUTH_USERNAME", default_username)
    password_hash = os.getenv("AUTH_PASSWORD_HASH", default_password_hash)
    
    return {
        "username": username,
        "password_hash": password_hash,
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
    """Display login page."""
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
                credentials = load_credentials()
                
                if username == credentials["username"] and verify_password(password, credentials["password_hash"]):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
        
        st.markdown("---")
        
        # Help text
        with st.expander("ℹ️ Need Help?"):
            st.markdown("""
            **Default Credentials (Development):**
            - Username: `admin`
            - Password: `aethelgard2024`
            
            **For Production:**
            Set environment variables:
            - `AUTH_USERNAME`: Your username
            - `AUTH_PASSWORD_HASH`: SHA-256 hash of your password
            
            **Generate Password Hash:**
            ```python
            import hashlib
            password = "your_password"
            hash = hashlib.sha256(password.encode()).hexdigest()
            print(hash)
            ```
            """)


def logout():
    """Logout the current user."""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.rerun()


def require_authentication():
    """
    Decorator/wrapper to require authentication for a page.
    Call this at the top of each page that requires authentication.
    """
    if not check_authentication():
        login_page()
        st.stop()



