"""Chat interface page for curriculum content generation."""

import json
import time

import streamlit as st

from auth import require_authentication
from components.sidebar import render_sidebar
from utils.api_client import get_api_client
from utils.session import add_message, clear_chat_history, get_chat_history, init_session_state

# Page config
st.set_page_config(
    page_title="Chat - Curriculum Studio",
    page_icon="💬",
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
        <h1 style='color: #2E5266; margin: 0;'>💬 Generate Curriculum Content</h1>
        <p style='color: #6E8898; margin: 5px 0;'>Quest and Crossfire™ | Aethelgard Academy™</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# Chat controls
if st.button("🗑️ Clear Chat History", use_container_width=True):
    clear_chat_history()
    st.session_state.quality_scores = []
    st.session_state.total_generation_time = 0
    st.rerun()

# Get quality display preference from sidebar
show_eval = st.session_state.get("show_quality_sidebar", True)

st.divider()

# Main chat interface
chat_container = st.container()

# Display chat history
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about Python concepts for curriculum generation..."):
    # Get selected provider
    provider = st.session_state.provider

    # Add user message to chat
    add_message("user", prompt)

    # Display user message
    with chat_container:
        with st.chat_message("user"):
            st.markdown(prompt)

    # Get AI response
    with chat_container:
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
                    response = api_client.chat_query(
                        question=prompt,
                        provider=provider,
                        secret_token=st.session_state.secret_tokens.get(provider),
                        history=get_chat_history()[:-1],
                        stream=False,
                    )

                answer = response.get("answer", "")
                message_placeholder.markdown(answer)
                add_message("assistant", answer)

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
                        # Download as Markdown - direct download button
                        try:
                            if len(st.session_state.messages) >= 2:
                                question = st.session_state.messages[-2]["content"]
                                answer = st.session_state.messages[-1]["content"]

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
with st.expander("💡 Tips for Better Curriculum Content"):
    st.markdown("""
    **For Best Results:**
    - **Be Specific**: Ask clear questions about specific Python concepts
    - **Provide Context**: Mention the target audience (beginners, intermediate, advanced)
    - **Check Quality**: Ensure the score is 95+ for curriculum use
    - **Review Citations**: Verify sources are authoritative and relevant
    - **Download Markdown**: Save content for integration into your curriculum
    - **Use Regenerate**: Try again if the content doesn't meet your needs
    
    **Quality-First Pipeline:**
    - ✓ RAG retrieval from your knowledge base (15 documents)
    - ✓ Tavily web research for additional context (8 sources)
    - ✓ Technical generation with 95+ threshold (up to 5 rewrites)
    - ✓ PSW structure compilation (Problem-Solution-Win)
    - ✓ Real-world examples and reflection questions
    - ✓ Citation preservation and verification
    
    **Example Questions:**
    - "Explain Python decorators with real-world examples for beginners"
    - "What are context managers and when should developers use them?"
    - "Compare list comprehensions vs generator expressions for intermediate learners"
    """)
