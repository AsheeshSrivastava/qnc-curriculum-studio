"""Authentication module for Curriculum Studio - Supabase Auth Integration."""

import streamlit as st
from typing import Optional
from utils.supabase_client import get_supabase_client, get_supabase_admin_client

try:
    DEBUG_AUTH = int(st.secrets.get("DEBUG_AUTH", 0))
except Exception:
    DEBUG_AUTH = 1 if st.secrets.get("DEBUG_AUTH", False) else 0


def _mask_token(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    token = str(token)
    if len(token) <= 8:
        return token
    return f"{token[:4]}…{token[-4:]}"


# User roles
ROLE_ADMIN = "admin"
ROLE_USER = "user"


def check_authentication() -> bool:
    """
    Check if user is authenticated via Supabase tokens we keep in session state.
    Returns True if authenticated, False otherwise.
    """
    # Ensure auth-related keys exist
    for key in ("sb_access_token", "sb_refresh_token", "sb_session_expires_at", "user_id", "user_email", "user_role"):
        st.session_state.setdefault(key, None)

    try:
        supabase = get_supabase_client()
        debug_state = {
            "attempted_with_access": bool(st.session_state.sb_access_token),
            "attempted_with_refresh": bool(st.session_state.sb_refresh_token),
        }

        # 1) Try current access token
        if st.session_state.sb_access_token:
            try:
                user_response = supabase.auth.get_user(st.session_state.sb_access_token)
                if user_response and getattr(user_response, "user", None):
                    user = user_response.user
                    st.session_state.user_id = user.id
                    st.session_state.user_email = user.email
                    if st.session_state.user_role is None:
                        st.session_state.user_role = get_user_role(user.id)

                    debug_state.update({
                        "auth_via": "access_token",
                        "user_id": user.id,
                        "user_email": user.email,
                    })
                    if DEBUG_AUTH:
                        st.session_state._debug_latest_session_response = debug_state
                    return True
            except Exception as exc:
                debug_state["access_token_error"] = str(exc)

        # 2) Attempt refresh using refresh token
        if st.session_state.sb_refresh_token:
            try:
                refresh_response = supabase.auth.refresh_session(st.session_state.sb_refresh_token)
                session = getattr(refresh_response, "session", None) if refresh_response else None
                user = getattr(refresh_response, "user", None) if refresh_response else None

                if session and user:
                    st.session_state.sb_access_token = session.access_token
                    st.session_state.sb_refresh_token = session.refresh_token
                    st.session_state.sb_session_expires_at = session.expires_at
                    st.session_state.user_id = user.id
                    st.session_state.user_email = user.email
                    st.session_state.user_role = get_user_role(user.id)

                    debug_state.update({
                        "auth_via": "refresh_token",
                        "user_id": user.id,
                        "user_email": user.email,
                        "access_token_preview": _mask_token(session.access_token),
                        "refresh_token_preview": _mask_token(session.refresh_token),
                        "expires_at": session.expires_at,
                    })
                    if DEBUG_AUTH:
                        st.session_state._debug_latest_session_response = debug_state
                    return True
            except Exception as exc:
                debug_state["refresh_token_error"] = str(exc)

        # 3) No valid session
        st.session_state.sb_access_token = None
        st.session_state.sb_refresh_token = None
        st.session_state.sb_session_expires_at = None
        st.session_state.user_id = None
        st.session_state.user_email = None
        st.session_state.user_role = None

        debug_state.update({
            "session_present": False,
            "reason": "No valid access or refresh token",
        })
        if DEBUG_AUTH:
            st.session_state._debug_latest_session_response = debug_state
        return False

    except Exception as exc:
        # Hard failure -> clear session
        st.session_state.sb_access_token = None
        st.session_state.sb_refresh_token = None
        st.session_state.sb_session_expires_at = None
        st.session_state.user_id = None
        st.session_state.user_email = None
        st.session_state.user_role = None

        if DEBUG_AUTH:
            st.session_state._debug_latest_session_response = {
                "session_present": False,
                "reason": f"Exception: {exc}",
            }
        return False


def get_user_role(user_id: Optional[str] = None) -> str:
    """Get user's role from curriculum_studio_users table."""
    if user_id is None:
        user_id = st.session_state.get("user_id")

    if not user_id:
        return ROLE_USER

    try:
        supabase_admin = get_supabase_admin_client()
        response = supabase_admin.table("curriculum_studio_users").select("role").eq("id", user_id).execute()

        if response.data and len(response.data) > 0:
            role = response.data[0].get("role", ROLE_USER)
            if DEBUG_AUTH:
                st.session_state["_debug_last_role_lookup"] = {"user_id": user_id, "role": role}
            return role

        if DEBUG_AUTH:
            st.session_state["_debug_last_role_lookup"] = {"user_id": user_id, "role": ROLE_USER, "reason": "no data"}
        return ROLE_USER
    except Exception as exc:
        if DEBUG_AUTH:
            st.session_state["_debug_last_role_lookup"] = {"user_id": user_id, "role": ROLE_USER, "error": str(exc)}
        return ROLE_USER


def is_admin(user_id: Optional[str] = None) -> bool:
    """Check if user is admin."""
    if user_id is None:
        user_id = st.session_state.get("user_id")
    
    return get_user_role(user_id) == ROLE_ADMIN


def login_page():
    """Display login page with Supabase Auth - includes Sign In and Sign Up tabs."""
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
        
        # Tabs for Sign In and Sign Up
        tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Sign Up"])
        
        # Tab 1: Sign In
        with tab1:
            st.markdown("### 🔐 Sign In")
            
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="Enter your email", type="default")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit = st.form_submit_button("Sign In", use_container_width=True, type="primary")
                
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
                                session = response.session

                                # Persist session tokens in Streamlit state
                                st.session_state.sb_access_token = session.access_token
                                st.session_state.sb_refresh_token = session.refresh_token
                                st.session_state.sb_session_expires_at = session.expires_at

                                st.session_state.user_id = user.id
                                st.session_state.user_email = user.email
                                st.session_state.user_role = get_user_role(user.id)

                                if DEBUG_AUTH:
                                    st.session_state._debug_last_login_result = {
                                        "user_id": user.id,
                                        "user_email": user.email,
                                        "access_token_preview": _mask_token(session.access_token),
                                        "refresh_token_preview": _mask_token(session.refresh_token),
                                        "expires_at": session.expires_at,
                                    }

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
        
        # Tab 2: Sign Up
        with tab2:
            st.markdown("### 📝 Create Account")
            st.markdown("Register for a new account. You'll be assigned **User** role by default.")
            
            with st.form("signup_form"):
                signup_email = st.text_input("Email", placeholder="Enter your email", key="signup_email")
                signup_password = st.text_input(
                    "Password", 
                    type="password", 
                    placeholder="Enter password (min 6 characters)",
                    key="signup_password",
                    help="Password must be at least 6 characters long"
                )
                signup_confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Confirm your password",
                    key="signup_confirm_password"
                )
                
                st.markdown("""
                <div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin: 10px 0;'>
                    <p style='margin: 0; font-size: 0.9em; color: #666;'>
                        <strong>Note:</strong> New accounts are created with <strong>User</strong> role by default.
                        Contact an administrator if you need <strong>Admin</strong> access.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                submit_signup = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                
                if submit_signup:
                    if not signup_email or not signup_password or not signup_confirm_password:
                        st.error("❌ Please fill in all fields")
                    elif signup_password != signup_confirm_password:
                        st.error("❌ Passwords do not match")
                    elif len(signup_password) < 6:
                        st.error("❌ Password must be at least 6 characters long")
                    else:
                        try:
                            supabase = get_supabase_client()
                            response = supabase.auth.sign_up({
                                "email": signup_email,
                                "password": signup_password
                            })
                            
                            if response.user:
                                # User created successfully
                                user = response.user
                                session = response.session
                                
                                # The database trigger will automatically create entry in curriculum_studio_users
                                # with default role 'user'
                                
                                # If session exists (auto-login), store it
                                if session:
                                    st.session_state.sb_access_token = session.access_token
                                    st.session_state.sb_refresh_token = session.refresh_token
                                    st.session_state.sb_session_expires_at = session.expires_at
                                    st.session_state.user_id = user.id
                                    st.session_state.user_email = user.email
                                    st.session_state.user_role = get_user_role(user.id)

                                    if DEBUG_AUTH:
                                        st.session_state._debug_last_signup_result = {
                                            "user_id": user.id,
                                            "user_email": user.email,
                                            "access_token_preview": _mask_token(session.access_token),
                                            "refresh_token_preview": _mask_token(session.refresh_token),
                                            "expires_at": session.expires_at,
                                        }

                                # Log signup event
                                log_security_event(user.id, "signup", {"email": user.email})
                                
                                st.success(f"✅ Account created successfully for {signup_email}!")
                                
                                if session:
                                    st.info("✅ You are now logged in!")
                                else:
                                    st.info("""
                                    **Next Steps:**
                                    1. Check your email for confirmation (if email confirmation is enabled)
                                    2. Sign in with your credentials
                                    3. Contact an administrator if you need Admin access
                                    """)
                                
                                st.rerun()
                            else:
                                st.error("❌ Failed to create account")
                        except Exception as e:
                            error_msg = str(e)
                            if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
                                st.error("❌ An account with this email already exists. Please sign in instead.")
                            elif "password" in error_msg.lower():
                                st.error("❌ Password does not meet requirements")
                            else:
                                st.error(f"❌ Sign up failed: {error_msg}")
        
        st.markdown("---")
        
        # Help text
        with st.expander("ℹ️ Need Help?"):
            st.markdown("""
            **For New Users:**
            - Use the **Sign Up** tab to create a new account
            - New accounts are created with **User** role by default
            - Contact an administrator if you need **Admin** access
            
            **For Existing Users:**
            - Use the **Sign In** tab to access your account
            
            **Security Note:**
            All passwords are securely hashed and stored by Supabase Auth.
            Never share your password.
            """)

    if DEBUG_AUTH:
        with st.expander("🔍 Auth Debug", expanded=DEBUG_AUTH >= 2):
            st.markdown("**Stored tokens (Session State):**")
            st.json({
                "access_token": _mask_token(st.session_state.get("sb_access_token")),
                "refresh_token": _mask_token(st.session_state.get("sb_refresh_token")),
                "expires_at": st.session_state.get("sb_session_expires_at"),
                "user_id": st.session_state.get("user_id"),
                "user_email": st.session_state.get("user_email"),
                "user_role": st.session_state.get("user_role"),
            })

            st.markdown("**Latest Supabase get_session():**")
            st.json(st.session_state.get("_debug_latest_session_response", {}))

            if st.session_state.get("_debug_last_login_result"):
                st.markdown("**Last login response:**")
                st.json(st.session_state.get("_debug_last_login_result"))

            if st.session_state.get("_debug_last_signup_result"):
                st.markdown("**Last signup response:**")
                st.json(st.session_state.get("_debug_last_signup_result"))

            if st.session_state.get("_debug_last_role_lookup"):
                st.markdown("**Last role lookup:**")
                st.json(st.session_state.get("_debug_last_role_lookup"))


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
    st.session_state.sb_access_token = None
    st.session_state.sb_refresh_token = None
    st.session_state.sb_session_expires_at = None
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
