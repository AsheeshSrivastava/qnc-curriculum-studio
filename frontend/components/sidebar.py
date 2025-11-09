"""Sidebar components for navigation and settings."""

import streamlit as st

from utils.api_client import get_api_client
from auth import logout


def render_sidebar():
    """Render the sidebar with branding, stats, and quick settings."""
    with st.sidebar:
        # Logo and Branding
        try:
            st.image("assets/Logo_Primary.png", use_container_width=True)
        except Exception:
            st.markdown("# 🎓")
        
        st.markdown(
            """
            <div style='text-align: center; margin-top: -10px;'>
                <h3 style='margin: 0; color: #2E5266;'>Quest and Crossfire™</h3>
                <p style='margin: 0; color: #6E8898; font-size: 0.9em;'>Aethelgard Academy™</p>
                <p style='margin: 5px 0; color: #D3A625; font-size: 0.85em; font-style: italic;'>"Small Fixes, Big Clarity"</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        # Backend status (compact)
        api_client = get_api_client()
        health = api_client.health_check()
        
        if health.get("status") == "ok":
            st.markdown("🟢 **Backend Online**")
        else:
            st.markdown("🔴 **Backend Offline**")

        st.divider()

        # Session Stats
        st.markdown("### 📊 Session Stats")
        
        doc_count = len(st.session_state.get("documents", []))
        msg_count = len(st.session_state.get("messages", []))
        
        # Calculate average quality if available
        avg_quality = 0
        quality_scores = st.session_state.get("quality_scores", [])
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📚 Docs", doc_count)
            st.metric("💬 Chats", msg_count // 2)  # Divide by 2 for Q&A pairs
        with col2:
            st.metric("⭐ Quality", f"{avg_quality:.1f}" if avg_quality > 0 else "—")
            total_time = st.session_state.get("total_generation_time", 0)
            st.metric("⏱️ Time", f"{total_time // 60}m" if total_time > 0 else "—")

        st.divider()

        # Quick Settings
        st.markdown("### ⚙️ Quick Settings")
        
        # Model Selection
        st.markdown("#### 🤖 Model Selection")
        
        # Organized model options with categories
        model_options = {
            # GPT-5 Series (Latest)
            "gpt-5": "🌟 GPT-5 (Latest Flagship)",
            "gpt-5-mini": "GPT-5 Mini (Fast & Efficient)",
            "gpt-5-nano": "GPT-5 Nano (Lightweight)",
            "gpt-5-codex": "GPT-5 Codex (Coding Specialist)",
            # O3 Series
            "o3-deep-research": "🔬 O3 Deep Research (Advanced)",
            # GPT-4 Series
            "gpt-4o": "GPT-4o (Balanced)",
            "gpt-4o-mini": "GPT-4o Mini (Fast & Cheap)",
            "gpt-4-turbo": "GPT-4 Turbo (Advanced)",
            # O1 Series
            "o1-preview": "O1 Preview (Reasoning)",
            "o1-mini": "O1 Mini (Fast Reasoning)",
        }
        
        selected_model = st.selectbox(
            "Choose Model",
            options=list(model_options.keys()),
            index=0,  # Default to gpt-5
            format_func=lambda x: model_options[x],
            key="selected_model",
            help="🌟 GPT-5 series recommended for best performance. O3 for deep research. GPT-4 for legacy compatibility."
        )
        
        # Show quality toggle
        show_quality = st.toggle(
            "📊 Show Quality Metrics",
            value=st.session_state.get("show_quality", True),
            key="show_quality_sidebar",
            help="Display detailed quality metrics with responses"
        )

        st.divider()

        # Quality Gates Info
        st.markdown("### 🎯 Quality Gates")
        st.markdown(
            """
            <div style='font-size: 0.85em; color: #6E8898;'>
                <p style='margin: 5px 0;'>✓ Gate 1: Technical (95+)</p>
                <p style='margin: 5px 0;'>✓ Gate 2: Compiler (95+)</p>
                <p style='margin: 5px 0;'>✓ PSW Structure</p>
                <p style='margin: 5px 0;'>✓ Real-World Examples</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # Logout button
        st.markdown("### 👤 Account")
        username = st.session_state.get("username", "User")
        user_role = st.session_state.get("user_role", "user")
        
        role_emoji = "👑" if user_role == "admin" else "👤"
        role_label = "Admin" if user_role == "admin" else "User"
        
        st.markdown(f"**{role_emoji} {username}**")
        st.markdown(f"*Role: {role_label}*")
        
        if st.button("🚪 Logout", use_container_width=True):
            logout()

        # Footer
        st.markdown("---")
        st.markdown(
            """
            <div style='text-align: center; font-size: 0.75em; color: #999;'>
                <p style='margin: 2px 0;'>Curriculum Studio v2.0</p>
                <p style='margin: 2px 0;'>Quest and Crossfire™</p>
                <p style='margin: 2px 0;'>Aethelgard Academy™</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

