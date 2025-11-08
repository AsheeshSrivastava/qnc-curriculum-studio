"""Document upload page."""

import streamlit as st

from auth import require_authentication
from components.sidebar import render_sidebar
from utils.api_client import get_api_client
from utils.session import init_session_state

# Page config
st.set_page_config(
    page_title="Upload Materials - Curriculum Studio",
    page_icon="📄",
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
        <h1 style='color: #2E5266; margin: 0;'>📄 Upload Learning Materials</h1>
        <p style='color: #6E8898; margin: 5px 0;'>Quest and Crossfire™ | Aethelgard Academy™</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")
st.markdown("Build your knowledge base by uploading Python learning materials for curriculum generation.")

# Instructions
with st.expander("📖 Upload Instructions", expanded=False):
    st.markdown("""
    ### Supported Formats
    - **PDF** (.pdf) - Python books, tutorials, documentation
    - **Markdown** (.md, .markdown) - README files, guides, notes
    - **JSON** (.json) - Structured Python knowledge

    ### Requirements
    - Documents must contain Python-related content
    - Maximum file size: 50MB
    - Content will be chunked and vectorized automatically

    ### What Happens After Upload?
    1. Document is parsed and extracted
    2. Content is filtered for Python relevance
    3. Text is chunked into manageable pieces
    4. Each chunk is embedded using OpenAI
    5. Vectors are stored in the database
    6. Document becomes searchable via chat
    """)

st.divider()

# Upload form
st.markdown("### 📤 Upload New Document")

with st.form("upload_form", clear_on_submit=True):
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "md", "markdown", "json"],
        help="Upload a Python-related document (PDF, Markdown, or JSON)",
    )

    # Metadata inputs
    col1, col2 = st.columns(2)

    with col1:
        title = st.text_input(
            "Document Title",
            placeholder="e.g., Python Best Practices Guide",
            help="Optional: Override the filename with a custom title",
        )

    with col2:
        source_uri = st.text_input(
            "Source URL (Optional)",
            placeholder="https://...",
            help="Optional: Link to the original source",
        )

    description = st.text_area(
        "Description (Optional)",
        placeholder="Brief description of the document content...",
        help="Optional: Add a description to help identify this document later",
        height=100,
    )

    # Submit button
    submitted = st.form_submit_button(
        "🚀 Upload & Process",
        use_container_width=True,
        type="primary",
    )

# Handle submission
if submitted and uploaded_file is not None:
    with st.spinner("🔄 Processing document... This may take a minute."):
        try:
            api_client = get_api_client()

            # Read file content
            file_content = uploaded_file.read()
            filename = uploaded_file.name

            # Upload to backend
            result = api_client.upload_document(
                file_content=file_content,
                filename=filename,
                title=title if title else None,
                description=description if description else None,
            )

            # Success message
            st.success("✅ Document uploaded successfully!")

            # Show results
            st.markdown("### 📊 Processing Results")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Document ID", result["document_id"][:8] + "...")
            with col2:
                st.metric("Chunks Created", result["chunk_count"])
            with col3:
                st.metric("Status", "✅ Indexed")

            st.info("💡 Your document is now searchable! Go to the Chat page to ask questions.")

            # Refresh documents list
            if st.button("📚 View in Library"):
                st.switch_page("pages/3_📚_Library.py")

        except Exception as e:
            st.error(f"❌ Upload failed: {str(e)}")
            st.caption("Please check your document and try again.")

elif submitted and uploaded_file is None:
    st.warning("⚠️ Please select a file to upload.")

st.divider()

# Recent uploads
st.markdown("### 📋 Recent Uploads")

try:
    api_client = get_api_client()
    documents = api_client.list_documents(limit=5)

    if documents:
        for doc in documents:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:
                    st.markdown(f"**{doc['title']}**")
                    if doc.get("description"):
                        st.caption(doc["description"])

                with col2:
                    st.caption(f"Type: {doc['source_type']}")
                    st.caption(f"Uploaded: {doc['created_at'][:10]}")

                with col3:
                    if st.button("View", key=f"view_{doc['id']}", use_container_width=True):
                        st.session_state.selected_document = doc
                        st.switch_page("pages/3_📚_Library.py")

                st.divider()
    else:
        st.info("📭 No documents uploaded yet. Upload your first document above!")

except Exception as e:
    st.error(f"Failed to load recent uploads: {str(e)}")

# Tips
st.markdown("---")
with st.expander("💡 Tips for Better Results"):
    st.markdown("""
    - **Quality over Quantity**: Upload well-structured, accurate Python content
    - **Clear Titles**: Use descriptive titles to easily find documents later
    - **Add Descriptions**: Help identify documents quickly in the library
    - **Source URLs**: Link to original sources for reference
    - **Organize Content**: Upload related documents together for better context
    """)


