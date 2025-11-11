"""Admin Panel - User Management for Curriculum Studio."""

import streamlit as st
from auth import (
    require_authentication,
    is_admin,
    log_security_event,
    ROLE_ADMIN,
    ROLE_USER,
)
from components.sidebar import render_sidebar
from utils.supabase_client import get_supabase_admin_client

# Page configuration
st.set_page_config(
    page_title="Admin Panel - Curriculum Studio",
    page_icon="👤",
    layout="wide",
)

# Require authentication
require_authentication()

# Check if user is admin
if not is_admin():
    st.error("🚫 Access Denied: Admin privileges required")
    st.info("This page is only accessible to administrators.")
    st.stop()

# Render sidebar
render_sidebar()

# Header
st.markdown("# 👤 Admin Panel")
st.markdown("### User Management & System Administration")
st.markdown("---")

# Tabs for different admin functions
tab1, tab2, tab3 = st.tabs(["👥 Manage Users", "➕ Add User", "📊 Usage Statistics"])

# Tab 1: Manage Users
with tab1:
    st.markdown("## 👥 Current Users")
    
    try:
        supabase_admin = get_supabase_admin_client()
        
        # Get all users from curriculum_studio_users table
        response = supabase_admin.table("curriculum_studio_users").select("*").order("created_at", desc=True).execute()
        users = response.data if response.data else []
        
        # Get auth users for additional info
        auth_users_response = supabase_admin.auth.admin.list_users()
        auth_users = {user.id: user for user in auth_users_response.users} if auth_users_response.users else {}
        
        if not users:
            st.warning("No users found in the database.")
        else:
            # Display users in a table
            st.markdown(f"**Total Users:** {len(users)}")
            st.markdown("---")
            
            for user_data in users:
                user_id = user_data["id"]
                email = user_data["email"]
                role = user_data.get("role", ROLE_USER)
                created_at = user_data.get("created_at", "")
                
                # Get last login from auth.users
                auth_user = auth_users.get(user_id)
                last_login = auth_user.last_sign_in_at if auth_user and auth_user.last_sign_in_at else None
                
                col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
                
                with col1:
                    role_emoji = "👑" if role == ROLE_ADMIN else "👤"
                    st.markdown(f"### {role_emoji} {email}")
                
                with col2:
                    role_badge = "🔴 Admin" if role == ROLE_ADMIN else "🟢 User"
                    st.markdown(f"**{role_badge}**")
                
                with col3:
                    if last_login:
                        last_login_str = last_login.split("T")[0] if "T" in str(last_login) else str(last_login)
                    else:
                        last_login_str = "Never"
                    st.markdown(f"**Last Login:** {last_login_str}")
                    
                    if created_at:
                        created_str = created_at.split("T")[0] if "T" in created_at else created_at
                        st.markdown(f"**Created:** {created_str}")
                
                with col4:
                    # Delete button (disabled for current user and if only one admin)
                    admin_count = sum(1 for u in users if u.get("role") == ROLE_ADMIN)
                    is_current_user = user_id == st.session_state.get("user_id")
                    is_only_admin = role == ROLE_ADMIN and admin_count == 1
                    
                    if is_current_user:
                        st.button("🔒 Current User", key=f"del_{user_id}", disabled=True)
                    elif is_only_admin:
                        st.button("🔒 Last Admin", key=f"del_{user_id}", disabled=True, help="Cannot delete the last admin")
                    else:
                        if st.button("🗑️ Remove", key=f"del_{user_id}", type="secondary"):
                            try:
                                # Delete from auth.users (this will cascade delete from curriculum_studio_users)
                                supabase_admin.auth.admin.delete_user(user_id)
                                
                                # Log deletion
                                log_security_event(
                                    st.session_state.get("user_id"),
                                    "user_deleted",
                                    {"deleted_user_id": user_id, "deleted_email": email}
                                )
                                
                                st.success(f"✅ User {email} deleted successfully")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Failed to delete user: {str(e)}")
                
                st.markdown("---")
    
    except Exception as e:
        st.error(f"❌ Error loading users: {str(e)}")

# Tab 2: Add User
with tab2:
    st.markdown("## ➕ Add New User")
    st.markdown("Create a new user account with specified role and credentials.")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_email = st.text_input(
                "Email",
                placeholder="Enter email address",
                help="Email address will be used as username"
            )
            
            new_password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter password (min 6 characters)",
                help="Password must be at least 6 characters long"
            )
        
        with col2:
            new_role = st.selectbox(
                "Role",
                options=[ROLE_USER, ROLE_ADMIN],
                format_func=lambda x: "👑 Admin (Full Access)" if x == ROLE_ADMIN else "👤 User (Standard Access)",
                help="Admin: Full access including user management\nUser: Standard access to curriculum tools"
            )
            
            st.markdown("### Role Permissions")
            if new_role == ROLE_ADMIN:
                st.markdown("""
                **Admin can:**
                - ✅ Access all features
                - ✅ Manage users (add/remove)
                - ✅ View usage statistics
                - ✅ Access admin panel
                """)
            else:
                st.markdown("""
                **User can:**
                - ✅ Upload documents
                - ✅ Generate content
                - ✅ Use AXIS AI Chat
                - ❌ Cannot manage users
                """)
        
        submit = st.form_submit_button("➕ Create User", use_container_width=True, type="primary")
        
        if submit:
            if not new_email or not new_password:
                st.error("❌ Email and password are required")
            elif len(new_password) < 6:
                st.error("❌ Password must be at least 6 characters long")
            else:
                try:
                    supabase_admin = get_supabase_admin_client()
                    
                    # Create user in Supabase Auth
                    user_response = supabase_admin.auth.admin.create_user({
                        "email": new_email,
                        "password": new_password,
                        "email_confirm": True  # Auto-confirm email
                    })
                    
                    if user_response.user:
                        user_id = user_response.user.id
                        
                        # Update role in curriculum_studio_users table
                        supabase_admin.table("curriculum_studio_users").update({
                            "role": new_role
                        }).eq("id", user_id).execute()
                        
                        # Log user creation
                        log_security_event(
                            st.session_state.get("user_id"),
                            "user_created",
                            {"created_user_id": user_id, "created_email": new_email, "role": new_role}
                        )
                        
                        st.success(f"✅ User {new_email} created successfully!")
                        st.balloons()
                        
                        # Show credentials
                        st.info(f"""
                        **New User Created:**
                        - Email: `{new_email}`
                        - Password: `{new_password}`
                        - Role: {new_role}
                        
                        ⚠️ **Important:** Share these credentials securely with the user.
                        The password will not be shown again.
                        """)
                    else:
                        st.error("❌ Failed to create user")
                
                except Exception as e:
                    error_msg = str(e)
                    if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
                        st.error("❌ User with this email already exists")
                    else:
                        st.error(f"❌ Failed to create user: {error_msg}")

# Tab 3: Usage Statistics
with tab3:
    st.markdown("## 📊 Usage Statistics")
    
    try:
        supabase_admin = get_supabase_admin_client()
        
        # Get all users
        users_response = supabase_admin.table("curriculum_studio_users").select("*").execute()
        users = users_response.data if users_response.data else []
        
        # Get audit logs for statistics
        logs_response = supabase_admin.table("audit_logs").select("*").order("created_at", desc=True).limit(1000).execute()
        logs = logs_response.data if logs_response.data else []
        
        if not users:
            st.warning("No usage data available.")
        else:
            # Overall stats
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("👥 Total Users", len(users))
            
            with col2:
                admin_count = sum(1 for u in users if u.get("role") == ROLE_ADMIN)
                st.metric("👑 Admins", admin_count)
            
            with col3:
                user_count = sum(1 for u in users if u.get("role") == ROLE_USER)
                st.metric("👤 Regular Users", user_count)
            
            st.markdown("---")
            
            # Login statistics
            login_logs = [log for log in logs if log.get("action_type") == "login"]
            if login_logs:
                st.markdown("### 📈 Recent Activity")
                st.metric("Total Logins", len(login_logs))
                
                # Show recent logins
                with st.expander("View Recent Logins"):
                    for log in login_logs[:10]:
                        user_email = log.get("details", {}).get("email", "Unknown")
                        log_time = log.get("created_at", "")
                        if log_time:
                            log_time = log_time.split("T")[0] + " " + log_time.split("T")[1].split(".")[0]
                        st.caption(f"{user_email} - {log_time}")
            
            st.markdown("---")
            
            # Usage by user
            st.markdown("### 📈 Users List")
            
            for user_data in users:
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    role_emoji = "👑" if user_data.get("role") == ROLE_ADMIN else "👤"
                    st.markdown(f"**{role_emoji} {user_data.get('email', 'Unknown')}**")
                
                with col2:
                    # Count logins for this user
                    user_logins = sum(1 for log in login_logs if log.get("user_id") == user_data.get("id"))
                    st.metric("Logins", user_logins)
                
                with col3:
                    created_at = user_data.get("created_at", "")
                    if created_at:
                        created_str = created_at.split("T")[0] if "T" in created_at else created_at
                        st.markdown(f"**Created:**\n{created_str}")
                    else:
                        st.markdown("**Created:**\nUnknown")
                
                st.markdown("---")
    
    except Exception as e:
        st.error(f"❌ Error loading statistics: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>Admin Panel</strong> - Quest and Crossfire™ | Aethelgard Academy™</p>
    <p style='font-size: 0.9em;'>Manage users and monitor system usage</p>
</div>
""", unsafe_allow_html=True)
