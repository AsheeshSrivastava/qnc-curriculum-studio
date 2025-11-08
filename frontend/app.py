"""Main Streamlit application for Quest and Crossfire Curriculum Studio."""

import streamlit as st

from auth import require_authentication
from components.sidebar import render_sidebar
from utils.session import init_session_state

# Page configuration
st.set_page_config(
    page_title="Home - Quest and Crossfire™",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "# Quest and Crossfire™\nAethelgard Academy™\n\nCurriculum Studio - Quality-First Content Generation",
    },
)

# Require authentication
require_authentication()

# Initialize session state
init_session_state()

# Render sidebar
render_sidebar()

# Header with branding
st.markdown(
    """
    <div style='text-align: center; padding: 20px 0;'>
        <h1 style='color: #2E5266; margin: 0;'>🎓 Curriculum Studio</h1>
        <p style='color: #6E8898; font-size: 1.2em; margin: 5px 0;'>Quest and Crossfire™ | Aethelgard Academy™</p>
        <p style='color: #D3A625; font-style: italic; margin: 5px 0;'>"Small Fixes, Big Clarity"</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# Welcome message
st.markdown("### 🎯 Welcome to Curriculum Studio")
st.markdown(
    """
    Your AI-powered assistant for creating high-quality Python curriculum content.
    Choose your workflow below:
    """
)

st.markdown("---")

# Dual-mode interface overview
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🤖 AXIS AI Chat")
    st.markdown(
        """
        **Augmented eXpert Intelligent System**
        
        Perfect for:
        - Quick clarifications
        - Code snippet explanations
        - Syntax questions
        - Troubleshooting help
        
        Features:
        - ⚡ Fast responses (5-15s)
        - 💾 Conversation history
        - 🎯 RAG-first (20 docs)
        - 🌐 Tavily fallback
        """
    )
    
    if st.button("🤖 Start AXIS AI →", use_container_width=True, type="secondary"):
        st.switch_page("pages/2_🎯_Workspace.py")

with col2:
    st.markdown("### 📝 Generate Content")
    st.markdown(
        """
        **High-quality curriculum content**
        
        Perfect for:
        - Lesson plans
        - Learning materials
        - In-depth explanations
        - Production content
        
        Features:
        - 📝 PSW structure
        - 🎯 95+ quality threshold
        - 📚 Comprehensive citations
        - 📥 Markdown export
        """
    )
    
    if st.button("📝 Generate Content →", use_container_width=True, type="primary"):
        st.switch_page("pages/2_🎯_Workspace.py")

st.markdown("---")

# Tips
with st.expander("💡 Tips for Best Results"):
    st.markdown("""
    **For Uploading:**
    - Upload high-quality Python learning materials
    - Include diverse sources (official docs, tutorials, guides)
    - Markdown files work best for text content
    - PDFs are processed automatically
    
    **For Content Generation:**
    - Be specific in your questions
    - Reference specific Python concepts or libraries
    - Review quality scores to ensure 95+ threshold
    - Download as Markdown for curriculum integration
    - Use Regenerate button if needed
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p><strong>Quest and Crossfire™ | Aethelgard Academy™</strong></p>
        <p>Curriculum Studio v2.0 - Built with FastAPI, LangChain, LangGraph, and Streamlit</p>
        <p style='font-style: italic; color: #D3A625;'>"Small Fixes, Big Clarity"</p>
    </div>
    """,
    unsafe_allow_html=True,
)


