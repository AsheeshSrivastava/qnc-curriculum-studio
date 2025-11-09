"""Admin Panel - User Management for Curriculum Studio."""

import streamlit as st
from auth import (
    require_authentication,
    is_admin,
    load_users,
    add_user,
    remove_user,
    ROLE_ADMIN,
    ROLE_USER,
)
from components.sidebar import render_sidebar

# Page configuration
st.set_page_config(
    page_title="Admin Panel - Curriculum Studio",
    page_icon="👤",
    layout="wide",
)

# Require authentication
require_authentication()

# Check if user is admin
if not is_admin(st.session_state.username):
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
    
    users = load_users()
    
    if not users:
        st.warning("No users found in the database.")
    else:
        # Display users in a table
        st.markdown(f"**Total Users:** {len(users)}")
        st.markdown("---")
        
        for username, user_data in users.items():
            col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
            
            with col1:
                role_emoji = "👑" if user_data["role"] == ROLE_ADMIN else "👤"
                st.markdown(f"### {role_emoji} {username}")
            
            with col2:
                role_badge = "🔴 Admin" if user_data["role"] == ROLE_ADMIN else "🟢 User"
                st.markdown(f"**{role_badge}**")
            
            with col3:
                last_login = user_data.get("last_login", "Never")
                if last_login and last_login != "Never":
                    last_login = last_login.split("T")[0]  # Show only date
                st.markdown(f"**Last Login:** {last_login}")
                st.markdown(f"**Usage Count:** {user_data.get('usage_count', 0)}")
            
            with col4:
                # Delete button (disabled for admin)
                if username == "admin":
                    st.button("🔒 Protected", key=f"del_{username}", disabled=True)
                else:
                    if st.button("🗑️ Remove", key=f"del_{username}", type="secondary"):
                        success, message = remove_user(username)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            
            st.markdown("---")

# Tab 2: Add User
with tab2:
    st.markdown("## ➕ Add New User")
    st.markdown("Create a new user account with specified role and credentials.")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input(
                "Username",
                placeholder="Enter username (min 3 characters)",
                help="Username must be at least 3 characters long"
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
            if not new_username or not new_password:
                st.error("❌ Username and password are required")
            else:
                success, message = add_user(new_username, new_password, new_role)
                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                    
                    # Show credentials
                    st.info(f"""
                    **New User Created:**
                    - Username: `{new_username}`
                    - Password: `{new_password}`
                    - Role: {new_role}
                    
                    ⚠️ **Important:** Share these credentials securely with the user.
                    The password will not be shown again.
                    """)
                else:
                    st.error(f"❌ {message}")

# Tab 3: Usage Statistics
with tab3:
    st.markdown("## 📊 Usage Statistics")
    
    users = load_users()
    
    if not users:
        st.warning("No usage data available.")
    else:
        # Overall stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("👥 Total Users", len(users))
        
        with col2:
            admin_count = sum(1 for u in users.values() if u["role"] == ROLE_ADMIN)
            st.metric("👑 Admins", admin_count)
        
        with col3:
            user_count = sum(1 for u in users.values() if u["role"] == ROLE_USER)
            st.metric("👤 Regular Users", user_count)
        
        st.markdown("---")
        
        # Usage by user
        st.markdown("### 📈 Usage by User")
        
        # Sort users by usage count
        sorted_users = sorted(
            users.items(),
            key=lambda x: x[1].get("usage_count", 0),
            reverse=True
        )
        
        for username, user_data in sorted_users:
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                role_emoji = "👑" if user_data["role"] == ROLE_ADMIN else "👤"
                st.markdown(f"**{role_emoji} {username}**")
            
            with col2:
                st.metric("Usage Count", user_data.get("usage_count", 0))
            
            with col3:
                last_login = user_data.get("last_login", "Never")
                if last_login and last_login != "Never":
                    last_login = last_login.split("T")[0]
                st.markdown(f"**Last Login:**\n{last_login}")
            
            st.markdown("---")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>Admin Panel</strong> - Quest and Crossfire™ | Aethelgard Academy™</p>
    <p style='font-size: 0.9em;'>Manage users and monitor system usage</p>
</div>
""", unsafe_allow_html=True)

