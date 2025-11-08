"""Session state management utilities."""

import streamlit as st


def init_session_state():
    """Initialize session state variables."""
    # Chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Current conversation
    if "current_answer" not in st.session_state:
        st.session_state.current_answer = None

    if "current_citations" not in st.session_state:
        st.session_state.current_citations = []

    if "current_evaluation" not in st.session_state:
        st.session_state.current_evaluation = None

    # Provider settings
    if "provider" not in st.session_state:
        st.session_state.provider = "openai"

    if "api_keys" not in st.session_state:
        st.session_state.api_keys = {
            "openai": None,
            "gemini": None,
            "openrouter": None,
        }

    if "secret_tokens" not in st.session_state:
        st.session_state.secret_tokens = {
            "openai": None,
            "gemini": None,
            "openrouter": None,
        }

    # Document library
    if "documents" not in st.session_state:
        st.session_state.documents = []

    if "selected_document" not in st.session_state:
        st.session_state.selected_document = None

    # Quality tracking
    if "quality_scores" not in st.session_state:
        st.session_state.quality_scores = []

    if "total_generation_time" not in st.session_state:
        st.session_state.total_generation_time = 0

    # UI preferences
    if "stream_mode" not in st.session_state:
        st.session_state.stream_mode = False

    if "show_quality" not in st.session_state:
        st.session_state.show_quality = True


def clear_chat_history():
    """Clear chat history."""
    st.session_state.messages = []
    st.session_state.current_answer = None
    st.session_state.current_citations = []
    st.session_state.current_evaluation = None


def add_message(role: str, content: str):
    """Add a message to chat history."""
    st.session_state.messages.append({"role": role, "content": content})


def get_chat_history() -> list[dict[str, str]]:
    """Get chat history in API format."""
    return st.session_state.messages


