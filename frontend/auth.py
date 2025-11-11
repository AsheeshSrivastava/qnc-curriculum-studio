"""Authentication module for Curriculum Studio - Supabase Auth Integration."""

import streamlit as st
from typing import Optional
from utils.supabase_client import get_supabase_client, get_supabase_admin_client


# User roles
ROLE_ADMIN = "admin"
ROLE_USER = "user"


def check_authentication() -> bool:
    """
    Check if user is authenticated via Supabase session.
    Returns True if authenticated, False otherwise.
    """
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "user_role" not in st.session_state:
        st.session_state.user_role = None
    
    # Check Supabase session
    try:
        supabase = get_supabase_client()
        session = supabase.auth.get_session()
        
        if session and session.session:
            # Session exists, update session state
            user = session.user
            st.session_state.authenticated = True
            st.session_state.user_id = user.id
            st.session_state.user_email = user.email
            
            # Get user role from curriculum_studio_users table
            if st.session_state.user_role is None:
                st.session_state.user_role = get_user_role(user.id)
            
            return True
        else:
            # No session, clear state
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.user_email = None
            st.session_state.user_role = None
            return False
    except Exception as e:
        # Error checking session, assume not authenticated
        st.session_state.authenticated = False
        return False


def get_user_role(user_id: Optional[str] = None) -> str:
    """Get user's role from curriculum_studio_users table."""
    if user_id is None:
        user_id = st.session_state.get("user_id")
    
    if not user_id:
        return ROLE_USER
    
    try:
        supabase = get_supabase_client()
        response = supabase.table("curriculum_studio_users").select("role").eq("id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0].get("role", ROLE_USER)
        return ROLE_USER
    except Exception:
        return ROLE_USER


def is_admin(user_id: Optional[str] = None) -> bool:
    """Check if user is admin."""
    if user_id is None:
        user_id = st.session_state.get("user_id")
    
    return get_user_role(user_id) == ROLE_ADMIN


def login_page():
    """Display login page with Supabase Auth."""
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
            email = st.text_input("Email", placeholder="Enter your email", type="default")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if submit:
                if not email or not password:
                    st.error("❌ Please enter both email and password")
                else:
                    try:
                        supabase = get_supabase_client()
                        response = supabase.auth.sign_in_with_password({
                            "email": email,
                            "password": password
                        })
                        
                        if response.user and response.session:
                            # Successful login
                            user = response.user
                            st.session_state.authenticated = True
                            st.session_state.user_id = user.id
                            st.session_state.user_email = user.email
                            st.session_state.user_role = get_user_role(user.id)
                            
                            # Log login event
                            log_security_event(user.id, "login", {"email": user.email})
                            
                            st.success(f"✅ Welcome back, {user.email}!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid email or password")
                    except Exception as e:
                        error_msg = str(e)
                        if "Invalid login credentials" in error_msg or "Email not confirmed" in error_msg:
                            st.error("❌ Invalid email or password")
                        else:
                            st.error(f"❌ Login failed: {error_msg}")
        
        st.markdown("---")
        
        # Help text
        with st.expander("ℹ️ Need Help?"):
            st.markdown("""
            **For New Users:**
            Contact the administrator to create an account for you.
            
            **Security Note:**
            All passwords are securely hashed and stored by Supabase Auth.
            Never share your password.
            """)


def logout():
    """Logout the current user."""
    try:
        # Log logout event before clearing session
        user_id = st.session_state.get("user_id")
        if user_id:
            log_security_event(user_id, "logout", {})
        
        # Sign out from Supabase
        supabase = get_supabase_client()
        supabase.auth.sign_out()
    except Exception:
        pass
    
    # Clear session state
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.user_email = None
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


def log_security_event(user_id: Optional[str], action_type: str, details: dict, ip_address: Optional[str] = None):
    """Log a security event to audit_logs table."""
    try:
        supabase = get_supabase_client()
        supabase.table("audit_logs").insert({
            "user_id": user_id,
            "action_type": action_type,
            "details": details,
            "ip_address": ip_address
        }).execute()
    except Exception:
        # Silently fail - don't break the app if logging fails
        pass
