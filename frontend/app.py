"""Main Streamlit application for Quest and Crossfire Curriculum Studio."""

import streamlit as st

from auth import require_authentication
from components.sidebar import render_sidebar
from utils.session import init_session_state

# Page configuration
st.set_page_config(
    page_title="Quest and Crossfire™ - Curriculum Studio",
    page_icon="🎓",
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

# Create 2-tab interface
tab1, tab2 = st.tabs(["📄 Upload Materials", "💬 Generate Content"])

with tab1:
    st.markdown("### 📤 Upload Learning Materials")
    st.markdown(
        """
        Build your knowledge base by uploading Python learning materials.
        The system will process and index them for curriculum generation.
        """
    )
    
    # Quick navigation to upload page
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info("📚 Upload PDF, Markdown, or JSON files to expand your knowledge base")
    with col2:
        if st.button("Go to Upload Page →", use_container_width=True, type="primary"):
            st.switch_page("pages/1_📄_Upload.py")
    
    st.markdown("---")
    
    # Knowledge base status
    st.markdown("#### 📊 Knowledge Base Status")
    doc_count = len(st.session_state.get("documents", []))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📚 Total Documents", doc_count)
    with col2:
        st.metric("📝 Ready for Use", doc_count)
    with col3:
        st.metric("🔍 Searchable", "Yes" if doc_count > 0 else "No")
    
    st.markdown("---")
    
    # Features
    st.markdown("#### ✨ What Happens After Upload")
    feat_col1, feat_col2 = st.columns(2)
    
    with feat_col1:
        st.markdown("""
        **🔍 Intelligent Processing**
        - Automatic text extraction
        - Smart chunking for optimal retrieval
        - Vector embedding generation
        - Metadata preservation
        """)
    
    with feat_col2:
        st.markdown("""
        **🎯 Quality-First Retrieval**
        - Semantic similarity search
        - Top 15 most relevant chunks
        - Automatic web search fallback
        - Citation tracking
        """)

with tab2:
    st.markdown("### 💬 Generate Curriculum Content")
    st.markdown(
        """
        Ask questions about Python concepts and get high-quality, curriculum-ready content
        with the PSW structure, real-world examples, and reflection questions.
        """
    )
    
    # Quick navigation to chat page
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info("💡 Generate content with 95+ quality threshold and automatic compilation")
    with col2:
        if st.button("Go to Chat Page →", use_container_width=True, type="primary"):
            st.switch_page("pages/2_💬_Chat.py")
    
    st.markdown("---")
    
    # Session stats
    st.markdown("#### 📊 Current Session")
    msg_count = len(st.session_state.get("messages", []))
    quality_scores = st.session_state.get("quality_scores", [])
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    total_time = st.session_state.get("total_generation_time", 0)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💬 Questions Asked", msg_count // 2)
    with col2:
        st.metric("⭐ Average Quality", f"{avg_quality:.1f}/100" if avg_quality > 0 else "—")
    with col3:
        st.metric("⏱️ Total Time", f"{total_time // 60}m {total_time % 60}s" if total_time > 0 else "—")
    
    st.markdown("---")
    
    # Quality pipeline
    st.markdown("#### 🎯 Quality-First Pipeline")
    pipeline_col1, pipeline_col2 = st.columns(2)
    
    with pipeline_col1:
        st.markdown("""
        **📝 Content Generation**
        - RAG retrieval (15 documents)
        - Tavily web research (8 sources)
        - Technical generation (95+ threshold)
        - Up to 5 rewrites for quality
        """)
    
    with pipeline_col2:
        st.markdown("""
        **✨ Technical Compilation**
        - PSW structure (Problem-Solution-Win)
        - Real-world examples integration
        - Reflection questions
        - Citation preservation (95+ threshold)
        """)

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


