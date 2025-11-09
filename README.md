# Quest and Crossfire™ Curriculum Studio

> AI-Powered Curriculum Generation Engine for Aethelgard Academy™

[![License: BSL](https://img.shields.io/badge/License-BSL-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)

---

## Overview

Curriculum Studio is an enterprise-grade AI-powered system for generating high-quality, pedagogically sound Python curriculum content. Built as the engine powering Aethelgard Academy™, it combines multi-agent AI pipelines, adaptive teaching modes, and self-improving RAG to deliver curriculum-ready content with 95+ quality standards.

**Status**: Beta (Production-Ready for Testing)

---

## Key Features

### 🤖 Multi-Agent Content Generation
- **5-Agent Sequential Pipeline**: Research → Synthesis → Structure → Compilation → Narrative Enrichment
- **Quality Gates**: Automated validation at each stage (citations, code quality, structure)
- **Retry Logic**: Intelligent fallback mechanisms for quality assurance
- **GPT-5/O3 Integration**: Leverages cutting-edge LLMs for superior content quality

### 💬 AXIS AI Chat (Augmented Expert Intelligent System)
- **3 Teaching Modes**:
  - **Coach Mode**: Direct, practical teaching with code examples
  - **Hybrid Mode**: Balanced approach with guided exploration
  - **Socratic Mode**: Question-driven learning for deep understanding
- **RAG-First Strategy**: Retrieves from curated knowledge base before web search
- **Tavily Fallback**: Web search integration for out-of-scope queries
- **Conversation History**: Maintains context across sessions

### 🧠 Self-Improving RAG
- **Q&A Vectorization**: Stores high-quality Q&A pairs back into the knowledge base
- **Dual-Mode Learning**: Captures insights from both chat and content generation
- **PostgreSQL + pgvector**: Scalable vector database for semantic search
- **Quality Filtering**: Only stores Q&A pairs meeting quality thresholds

### 🔐 Multi-User Authentication
- **Role-Based Access Control**: Admin and User roles
- **Admin Panel**: User management, usage statistics, and system monitoring
- **Secure Storage**: Hashed passwords with secure session management

---

## Architecture

### Backend (FastAPI)
```
research-portal/backend/
├── app/
│   ├── agents/              # 5-agent pipeline (Research, Synthesis, Structure, Compiler, Narrative)
│   ├── api/routes/          # REST endpoints (chat, generate, health)
│   ├── clients/             # OpenAI, Tavily integrations
│   ├── core/                # Configuration, logging, LangSmith tracing
│   ├── db/                  # PostgreSQL + pgvector setup
│   ├── schemas/             # Pydantic models
│   ├── services/            # RAG, Q&A storage, research graph
│   └── vectorstore/         # Vector database operations
├── pyproject.toml           # Poetry dependencies
└── main.py                  # FastAPI app entry point
```

**Key Technologies**:
- FastAPI 0.104+ (async REST API)
- LangGraph (agent orchestration)
- LangChain (LLM abstractions)
- PostgreSQL + pgvector (vector database)
- OpenAI GPT-5/O3 (LLM)
- Tavily API (web search)
- LangSmith (tracing & monitoring)

### Frontend (Streamlit)
```
frontend/
├── pages/
│   ├── 2_🎯_Workspace.py   # AXIS AI Chat interface
│   └── 3_👤_Admin_Panel.py # User management (admin-only)
├── components/
│   └── sidebar.py           # Navigation with user role display
├── utils/
│   └── api_client.py        # Backend API communication
├── auth.py                  # Multi-user authentication
└── app.py                   # Main entry point (Home page)
```

**Key Technologies**:
- Streamlit 1.28+ (Python web framework)
- Requests (HTTP client)
- JSON-based user database (with migration path to Supabase)

---

## Business Value

### For Educational Institutions
- **Rapid Curriculum Development**: Generate weeks of content in hours
- **Pedagogical Consistency**: Enforced PSW (Problem-System-Win) framework
- **Adaptive Learning**: 3 teaching modes for diverse learning styles
- **Quality Assurance**: Automated validation against 10-criterion rubric

### For Learners
- **Personalized Support**: AXIS AI adapts to individual learning preferences
- **Real-World Context**: Narrative enrichment connects theory to practice
- **Self-Paced Learning**: Coach mode for beginners, Socratic for advanced learners
- **Always Available**: 24/7 AI-powered tutoring

### For Instructors
- **Time Savings**: Automates content creation and Q&A support
- **Curated Knowledge Base**: Ensures accuracy with vetted sources
- **Usage Analytics**: Admin panel tracks engagement and usage patterns
- **Scalable**: Supports multiple users with role-based access

### Market Differentiators
1. **Multi-Agent Pipeline**: Unlike single-LLM solutions, our 5-agent system ensures comprehensive, well-structured content
2. **Self-Improving RAG**: Learns from every interaction, continuously improving response quality
3. **3 Teaching Modes**: Unique pedagogical flexibility not found in generic chatbots
4. **Quality Gates**: Automated validation ensures 95+ quality standards (vs. industry 70-80%)
5. **Narrative Enrichment**: Agent 4 adds real-world context, making technical content engaging

---

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 14+ with pgvector extension
- OpenAI API key (GPT-5/O3 access)
- Tavily API key (web search)
- LangSmith API key (optional, for tracing)

### Installation

#### 1. Clone Repository
```bash
git clone https://github.com/AsheeshSrivastava/qnc-curriculum-studio.git
cd qnc-curriculum-studio
```

#### 2. Backend Setup
```bash
cd research-portal/backend

# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
# - OPENAI_API_KEY
# - TAVILY_API_KEY
# - LANGSMITH_API_KEY (optional)
# - DATABASE_URL (PostgreSQL connection string)

# Run database migrations
poetry run alembic upgrade head

# Start backend server
poetry run uvicorn app.main:app --reload --port 8000
```

#### 3. Frontend Setup
```bash
cd ../../frontend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up Streamlit secrets
mkdir -p .streamlit
cat > .streamlit/secrets.toml << EOF
BACKEND_URL = "http://localhost:8000"
EOF

# Start frontend
streamlit run app.py
```

#### 4. Access Application
- **Frontend**: http://localhost:8501
- **Backend API Docs**: http://localhost:8000/docs

---

## Deployment

### Backend (Render.com)
- **Service Type**: Web Service
- **Build Command**: `cd research-portal/backend && pip install poetry && poetry install`
- **Start Command**: `cd research-portal/backend && poetry run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**: Set `OPENAI_API_KEY`, `TAVILY_API_KEY`, `LANGSMITH_API_KEY`, `DATABASE_URL`, `ENABLE_NARRATIVE_ENRICHMENT=true`

### Frontend (Streamlit Cloud)
- **Main File**: `frontend/app.py`
- **Python Version**: 3.11
- **Secrets**: Add `BACKEND_URL` in Streamlit Cloud dashboard

### Database (Render.com PostgreSQL)
- **Plan**: Starter or higher (for pgvector support)
- **Extensions**: Enable `vector` extension after creation
- **Connection String**: Add to backend's `DATABASE_URL` environment variable

---

## Usage

### Generate Content Mode
1. Navigate to **Home** page
2. Enter a Python concept (e.g., "list comprehensions")
3. Select difficulty level (Beginner/Intermediate/Advanced)
4. Click **Generate Content**
5. Review the 5-agent pipeline output:
   - Research findings with citations
   - Synthesized explanations
   - Structured PSW framework
   - Compiled content with code examples
   - Narrative-enriched final output

### AXIS AI Chat Mode
1. Navigate to **AXIS AI Chat** page
2. Select teaching mode:
   - **Coach**: Direct answers with code examples
   - **Hybrid**: Balanced guidance and exploration
   - **Socratic**: Question-driven deep learning
3. Ask questions about Python concepts
4. Chat maintains conversation history for context
5. High-quality Q&A pairs are automatically stored for future RAG

### Admin Panel (Admin-Only)
1. Navigate to **Admin Panel** page
2. **Add User**: Create new user accounts with roles
3. **Remove User**: Delete user accounts (cannot remove admin)
4. **Usage Statistics**: View user activity and system metrics

---

## Roadmap

### Phase 1: Foundation (Completed ✅)
- [x] Multi-agent content generation pipeline
- [x] AXIS AI chat with 3 teaching modes
- [x] Self-improving RAG with Q&A vectorization
- [x] Multi-user authentication with admin panel
- [x] PostgreSQL + pgvector integration
- [x] LangSmith tracing and monitoring

### Phase 2: Enhancements (Planned)
- [ ] **Multimodal AI**:
  - Voice input (Whisper API)
  - Text-to-speech (TTS for narration)
  - Image analysis (GPT-4 Vision for code screenshots)
  - Diagram generation (Mermaid for flowcharts)
- [ ] **Advanced Teaching Modes**:
  - Dedicated agent pipelines for each mode
  - Adaptive difficulty adjustment
  - Learning path recommendations
- [ ] **Content Management**:
  - Curriculum versioning
  - Content review workflow
  - Export to LMS formats (SCORM, xAPI)

### Phase 3: Aethelgard Academy Integration (Q1 2026)
- [ ] **LMS Integration**:
  - API-first architecture for frontend consumption
  - Supabase database for user progress tracking
  - Next.js frontend with embedded AXIS AI widget
  - Python playground integration
- [ ] **Analytics Dashboard**:
  - Learning analytics and progress tracking
  - Content effectiveness metrics
  - User engagement insights

---

## Technical Highlights

### Multi-Agent Pipeline
- **Agent 1 (Research)**: Retrieves relevant documents from vector database + web search
- **Agent 2 (Synthesis)**: Combines sources into coherent explanations
- **Agent 3 (Structure)**: Applies PSW framework and difficulty scaffolding
- **Agent 4 (Compiler)**: Generates executable code examples with output
- **Agent 5 (Narrative)**: Adds real-world context and engaging storytelling

### Quality Gates
- **Gate 1**: Minimum 6 citations from research
- **Gate 2**: Code examples must execute successfully
- **Gate 3**: Structured PSW framework validation
- **Gate 4**: Compiler score ≥85/100

### RAG Strategy
1. **Query Embedding**: Convert user query to vector (OpenAI embeddings)
2. **Similarity Search**: Retrieve top-k documents from pgvector
3. **Reranking**: Score documents by relevance
4. **Context Injection**: Provide retrieved docs to LLM
5. **Fallback**: Use Tavily web search if RAG returns insufficient results
6. **Storage**: Vectorize high-quality Q&A pairs for future retrieval

### Teaching Mode Prompts
- **Coach Mode**: "Start EVERY response with a clear, direct answer (2-3 sentences max). ALWAYS include a working code example with inline comments. End with a 💡 Pro Tip."
- **Hybrid Mode**: "Balance direct explanation (40%) with guided discovery (60%). Use analogies and questions to build understanding."
- **Socratic Mode**: "NEVER give direct answers. Ask 3-5 progressively deeper questions. Guide learners to discover solutions themselves."

---

## License

**Business Source License 1.1**

- **Licensor**: Quest and Crossfire™ (Asheesh Srivastava)
- **Licensed Work**: Quest and Crossfire™ Curriculum Studio
- **Additional Use Grant**: Non-commercial educational use permitted
- **Change Date**: 2027-11-09
- **Change License**: Apache License 2.0

For commercial licensing inquiries, contact: asheesh.srivastava@questandcrossfire.com

See [LICENSE](LICENSE) for full terms.

---

## Trademarks

- **QUEST AND CROSSFIRE™** - Registered Trademark
- **AETHELGARD ACADEMY™** - Registered Trademark

---

## Contributing

This is a proprietary project under the Business Source License. Contributions are welcome under the following terms:
1. All contributions must align with the BSL 1.1 license
2. Contributors grant Quest and Crossfire™ perpetual rights to their contributions
3. No contributions may be used for commercial purposes until the Change Date (2027-11-09)

For collaboration inquiries, contact: asheesh.srivastava@questandcrossfire.com

---

## Acknowledgments

**AI Assistance**: This project was developed with assistance from:
- **Claude Code** (Anthropic) - Architecture, contracts, quality framework
- **ChatGPT** (OpenAI) - Content generation, backend API, frontend development

**Technologies**: Built with FastAPI, Streamlit, LangChain, LangGraph, PostgreSQL, OpenAI GPT-5/O3, Tavily API, and LangSmith.

---

## Contact

**Asheesh Ranjan Srivastava**
- **Email**: asheesh.srivastava@questandcrossfire.com
- **GitHub**: [@AsheeshSrivastava](https://github.com/AsheeshSrivastava)
- **LinkedIn**: [asheesh-ranjan-srivastava](https://www.linkedin.com/in/asheesh-ranjan-srivastava/)

---

## Project Statistics

- **Backend**: 15,000+ lines of Python code
- **Frontend**: 3,000+ lines of Python/Streamlit code
- **Agents**: 5 specialized AI agents
- **Quality Criteria**: 10-criterion rubric (100-point scale)
- **Teaching Modes**: 3 adaptive pedagogical styles
- **Vector Database**: PostgreSQL + pgvector with 1,536-dimensional embeddings
- **API Endpoints**: 8 REST endpoints (chat, generate, health, admin)
- **Development Time**: 6 weeks (Oct-Nov 2025)

---

**Last Updated**: November 9, 2025  
**Version**: 1.0.0-beta  
**Status**: Production-Ready for Beta Testing

---

**◇ Where chaos becomes clarity. Small fixes, big clarity.**

---

**For questions, collaboration, or commercial licensing inquiries, please contact Asheesh Ranjan Srivastava.**
