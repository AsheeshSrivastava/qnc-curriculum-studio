"""Workspace page with dual-mode interface: Chat (Quick Q&A) and Generate Content."""

import json
import time

import streamlit as st

from auth import require_authentication
from components.sidebar import render_sidebar
from utils.api_client import get_api_client
from utils.session import add_message, clear_chat_history, get_chat_history, init_session_state

# Page config
st.set_page_config(
    page_title="AXIS AI Chat - Curriculum Studio",
    page_icon="🤖",
    layout="wide",
)

# Require authentication
require_authentication()

# Initialize
init_session_state()
render_sidebar()

# Header with branding
st.markdown(
    """
    <div style='text-align: center; padding: 10px 0;'>
        <h1 style='color: #2E5266; margin: 0;'>🎯 Curriculum Workspace</h1>
        <p style='color: #6E8898; margin: 5px 0;'>Quest and Crossfire™ | Aethelgard Academy™</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# Create tabs for dual-mode interface
tab1, tab2 = st.tabs(["🤖 AXIS AI Chat", "📝 Generate Content"])

# =============================================================================
# TAB 1: CHAT MODE (Quick Q&A)
# =============================================================================
with tab1:
    st.markdown("### 🤖 AXIS AI Chat")
    st.markdown(
        """
        **Augmented eXpert Intelligent System** - Your AI teaching assistant.
        Fast, conversational answers powered by your knowledge base with **RAG-first** strategy.
        """
    )
    
    # Initialize chat-specific session state
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "teaching_mode" not in st.session_state:
        st.session_state.teaching_mode = "coach"
    
    # Teaching Mode Selector
    st.markdown("#### 🎓 Teaching Mode")
    mode_col1, mode_col2, mode_col3, mode_col4 = st.columns([1, 1, 1, 2])
    
    with mode_col1:
        if st.button("🎯 Coach", key="mode_coach", use_container_width=True, 
                     type="primary" if st.session_state.teaching_mode == "coach" else "secondary"):
            st.session_state.teaching_mode = "coach"
            st.rerun()
    
    with mode_col2:
        if st.button("⚖️ Hybrid", key="mode_hybrid", use_container_width=True,
                     type="primary" if st.session_state.teaching_mode == "hybrid" else "secondary"):
            st.session_state.teaching_mode = "hybrid"
            st.rerun()
    
    with mode_col3:
        if st.button("🤔 Socratic", key="mode_socratic", use_container_width=True,
                     type="primary" if st.session_state.teaching_mode == "socratic" else "secondary"):
            st.session_state.teaching_mode = "socratic"
            st.rerun()
    
    with mode_col4:
        # Mode description
        mode_descriptions = {
            "coach": "📖 Direct explanations with examples",
            "hybrid": "🔄 Balanced: Questions + Explanations",
            "socratic": "💭 Guided discovery through questions"
        }
        st.caption(mode_descriptions.get(st.session_state.teaching_mode, ""))
    
    st.divider()
    
    # Chat controls
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("⚡ Fast responses (5-15s) | 💾 Maintains last 10 messages | 🎯 RAG-first (20 docs)")
    with col2:
        if st.button("🗑️ Clear Chat", key="clear_chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()
    
    st.divider()
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Show source info for assistant messages
                if message["role"] == "assistant" and "metadata" in message:
                    metadata = message["metadata"]
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption(f"📚 Sources: {metadata.get('sources_used', 0)}")
                    with col2:
                        rag_only = metadata.get('rag_only', False)
                        st.caption(f"🔍 {'RAG Only' if rag_only else 'RAG + Tavily'}")
                    with col3:
                        st.caption(f"⏱️ {metadata.get('time', 0)}s")
    
    # Chat input
    if chat_prompt := st.chat_input("Ask a quick question about Python...", key="chat_input"):
        # Get selected provider and model
        provider = st.session_state.provider
        selected_model = st.session_state.get("selected_model", "gpt-4o")
        
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": chat_prompt})
        
        # Display user message
        with chat_container:
            with st.chat_message("user"):
                st.markdown(chat_prompt)
        
        # Get AI response
        with chat_container:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                metadata_placeholder = st.empty()
                
                try:
                    api_client = get_api_client()
                    start_time = time.time()
                    
                    # Quick Q&A query
                    with st.spinner("⏳ Searching knowledge base... (5-15s)"):
                        # Build history for API
                        history = [
                            {"role": msg["role"], "content": msg["content"]}
                            for msg in st.session_state.chat_messages[-11:-1]  # Last 10 messages (excluding current)
                        ]
                        
                        response = api_client.quick_qa(
                            question=chat_prompt,
                            provider=provider,
                            model=selected_model,
                            secret_token=st.session_state.secret_tokens.get(provider),
                            history=history,
                            teaching_mode=st.session_state.teaching_mode,
                        )
                    
                    answer = response.get("answer", "")
                    sources_used = response.get("sources_used", 0)
                    rag_only = response.get("rag_only", False)
                    generation_time = int(time.time() - start_time)
                    
                    # Display answer
                    message_placeholder.markdown(answer)
                    
                    # Display metadata
                    with metadata_placeholder.container():
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.caption(f"📚 Sources: {sources_used}")
                        with col2:
                            st.caption(f"🔍 {'RAG Only' if rag_only else 'RAG + Tavily'}")
                        with col3:
                            st.caption(f"⏱️ {generation_time}s")
                    
                    # Add to history
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": answer,
                        "metadata": {
                            "sources_used": sources_used,
                            "rag_only": rag_only,
                            "time": generation_time,
                        }
                    })
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.caption("Please try again or check the backend connection.")
    
    # Tips
    st.markdown("---")
    with st.expander("💡 Tips for Chat Mode"):
        st.markdown("""
        **Best For:**
        - Quick clarifications on Python concepts
        - Code snippet explanations
        - Syntax questions
        - Troubleshooting help
        
        **Features:**
        - ⚡ Fast responses (5-15 seconds)
        - 💾 Remembers last 10 messages
        - 🎯 RAG-first (20 documents)
        - 🌐 Tavily fallback when needed
        - 🤖 Configurable model selection
        
        **Example Questions:**
        - "What's the difference between list and tuple?"
        - "How do I use enumerate()?"
        - "Explain lambda functions briefly"
        - "What does the * operator do in function arguments?"
        """)

# =============================================================================
# TAB 2: GENERATE CONTENT MODE (Full Pipeline)
# =============================================================================
with tab2:
    st.markdown("### 📝 Generate Curriculum Content")
    st.markdown(
        """
        High-quality, curriculum-ready content with the PSW structure,
        real-world examples, and comprehensive citations. **95+ quality threshold**.
        """
    )
    
    # Initialize generate-specific session state
    if "generate_messages" not in st.session_state:
        st.session_state.generate_messages = []
    
    # Get quality display preference from sidebar
    show_eval = st.session_state.get("show_quality_sidebar", True)
    
    # Generate controls
    if st.button("🗑️ Clear History", key="clear_generate", use_container_width=True):
        st.session_state.generate_messages = []
        st.session_state.quality_scores = []
        st.session_state.total_generation_time = 0
        st.rerun()
    
    st.divider()
    
    # Display generate history
    generate_container = st.container()
    with generate_container:
        for message in st.session_state.generate_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Generate input
    if generate_prompt := st.chat_input("Ask about Python concepts for curriculum generation...", key="generate_input"):
        # Get selected provider and model
        provider = st.session_state.provider
        selected_model = st.session_state.get("selected_model", "gpt-4o")
        
        # Add user message
        st.session_state.generate_messages.append({"role": "user", "content": generate_prompt})
        
        # Display user message
        with generate_container:
            with st.chat_message("user"):
                st.markdown(generate_prompt)
        
        # Get AI response
        with generate_container:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                status_placeholder = st.empty()
                citations_placeholder = st.empty()
                evaluation_placeholder = st.empty()
                actions_placeholder = st.empty()
                
                try:
                    api_client = get_api_client()
                    start_time = time.time()
                    
                    # Generate curriculum content
                    with st.spinner("⏳ Generating curriculum content (60-120s)... Quality-first pipeline with 95+ threshold"):
                        # Build history for API
                        history = [
                            {"role": msg["role"], "content": msg["content"]}
                            for msg in st.session_state.generate_messages[:-1]
                        ]
                        
                        response = api_client.chat_query(
                            question=generate_prompt,
                            provider=provider,
                            model=selected_model,
                            secret_token=st.session_state.secret_tokens.get(provider),
                            history=history,
                            stream=False,
                        )
                    
                    answer = response.get("answer", "")
                    message_placeholder.markdown(answer)
                    st.session_state.generate_messages.append({"role": "assistant", "content": answer})
                    
                    st.session_state.current_citations = response.get("citations", [])
                    st.session_state.current_evaluation = response.get("evaluation")
                    
                    # Track generation time and quality
                    generation_time = int(time.time() - start_time)
                    st.session_state.total_generation_time = st.session_state.get("total_generation_time", 0) + generation_time
                    
                    if st.session_state.current_evaluation:
                        quality_score = st.session_state.current_evaluation.get("total_score", 0)
                        if quality_score > 0:
                            st.session_state.quality_scores.append(quality_score)
                    
                    # Display quality metrics card
                    if show_eval and st.session_state.current_evaluation:
                        try:
                            eval_data = st.session_state.current_evaluation
                            
                            with evaluation_placeholder.container():
                                st.markdown("---")
                                st.markdown("### 📊 Quality Metrics")
                                
                                # Overall metrics
                                total_score = eval_data.get("total_score") or 0
                                passed = eval_data.get("passed", False)
                                
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Overall Score", f"{float(total_score):.1f}/100")
                                with col2:
                                    status_emoji = "✅" if passed else "⚠️"
                                    st.metric("Status", f"{status_emoji} {'Passed' if passed else 'Review'}")
                                with col3:
                                    st.metric("Generation Time", f"{generation_time}s")
                                with col4:
                                    citation_count = len(st.session_state.current_citations)
                                    st.metric("Citations", citation_count)
                                
                                # Expandable detailed metrics
                                with st.expander("📈 Detailed Quality Breakdown", expanded=False):
                                    criteria = eval_data.get("criteria", {})
                                    if criteria:
                                        for key, criterion_data in criteria.items():
                                            if isinstance(criterion_data, dict):
                                                score = criterion_data.get("score") or 0
                                                max_points = criterion_data.get("max_points") or 20
                                                rationale = criterion_data.get("rationale", "")
                                                
                                                progress_value = float(score) / float(max_points) if max_points > 0 else 0
                                                st.progress(
                                                    progress_value,
                                                    text=f"{key.replace('_', ' ').title()}: {float(score):.1f}/{max_points}"
                                                )
                                                if rationale:
                                                    st.caption(rationale)
                                    
                                    # Feedback
                                    feedback = eval_data.get("feedback", [])
                                    if feedback:
                                        st.markdown("**Improvement Suggestions:**")
                                        for item in feedback:
                                            st.markdown(f"- {item}")
                        except Exception as eval_error:
                            st.caption(f"Note: Quality metrics partially available ({str(eval_error)})")
                    
                    # Display citations
                    if st.session_state.current_citations:
                        with citations_placeholder.expander("📚 Sources & Citations", expanded=False):
                            for i, citation in enumerate(st.session_state.current_citations, 1):
                                citation_id = citation.get('id', f'citation-{i}')
                                source = citation.get('source', 'Unknown')
                                citation_type = citation.get('type', 'N/A')
                                score = citation.get('score')
                                
                                st.markdown(f"**[{citation_id}] {source}**")
                                
                                if score is not None:
                                    st.caption(f"Type: {citation_type} | Relevance: {float(score):.2f}")
                                else:
                                    st.caption(f"Type: {citation_type}")
                                
                                metadata = citation.get("metadata", {})
                                if metadata:
                                    st.caption(f"Metadata: {metadata}")
                                
                                if i < len(st.session_state.current_citations):
                                    st.divider()
                    
                    # Action buttons
                    with actions_placeholder.container():
                        st.markdown("---")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            # Download as Markdown
                            try:
                                if len(st.session_state.generate_messages) >= 2:
                                    question = st.session_state.generate_messages[-2]["content"]
                                    answer = st.session_state.generate_messages[-1]["content"]
                                    
                                    content = api_client.export_chat(
                                        question=question,
                                        answer=answer,
                                        citations=st.session_state.current_citations or [],
                                        evaluation=st.session_state.current_evaluation or {},
                                        format="markdown",
                                    )
                                    
                                    st.download_button(
                                        "📥 Download as Markdown",
                                        data=content,
                                        file_name="curriculum_content.md",
                                        mime="text/markdown",
                                        use_container_width=True,
                                        type="primary",
                                    )
                            except Exception as e:
                                st.error(f"Export failed: {e}")
                        
                        with col2:
                            # Regenerate button
                            if st.button("🔄 Regenerate Content", use_container_width=True):
                                st.rerun()
                        
                        with col3:
                            # Copy to clipboard hint
                            st.caption("💡 You can also select and copy the text directly")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.caption("Please try again or check the backend connection.")
    
    # Tips section
    st.markdown("---")
    with st.expander("💡 Tips for Generate Content Mode"):
        st.markdown("""
        **Best For:**
        - Comprehensive curriculum content
        - Lesson plans and learning materials
        - In-depth explanations with examples
        - Production-ready educational content
        
        **Features:**
        - 📝 PSW structure (Problem-Solution-Win)
        - 🎯 95+ quality threshold
        - 📚 Comprehensive citations
        - 🔄 Up to 5 rewrites for quality
        - 📊 Detailed quality metrics
        - 📥 Markdown export
        
        **Quality-First Pipeline:**
        - ✓ RAG retrieval (15 documents)
        - ✓ Tavily web research (8 sources)
        - ✓ Multi-agent sequential pipeline
        - ✓ Technical compilation
        - ✓ Citation preservation
        
        **Example Questions:**
        - "Explain Python decorators with real-world examples for beginners"
        - "What are context managers and when should developers use them?"
        - "Compare list comprehensions vs generator expressions for intermediate learners"
        """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 10px;'>
        <p><strong>Quest and Crossfire™ | Aethelgard Academy™</strong></p>
        <p style='font-style: italic; color: #D3A625;'>"Small Fixes, Big Clarity"</p>
    </div>
    """,
    unsafe_allow_html=True,
)

