# Curriculum Studio

## Quest and Crossfire™ | Aethelgard Academy™

**"Small Fixes, Big Clarity"**

---

## 🎓 Overview

Curriculum Studio is a quality-first AI-powered content generation platform for creating Python curriculum materials. Built specifically for Aethelgard Academy, it combines RAG (Retrieval-Augmented Generation) with web search to produce high-quality, curriculum-ready content.

---

## ✨ Features

- 🔐 **Secure Authentication** - Login/password protection
- 📚 **RAG System** - Retrieves from 67+ Python learning materials
- 🌐 **Web Search** - Tavily integration for additional context
- 🎯 **Quality-First** - Dual quality gates (95+ threshold)
- 📝 **PSW Structure** - Problem-Solution-Win format
- 💡 **Real-World Examples** - Industry-relevant content
- 🤔 **Reflection Questions** - Pedagogical depth
- 📥 **Markdown Export** - Curriculum-ready output
- 📊 **Quality Metrics** - Detailed evaluation tracking

---

## 🏗️ Architecture

### Backend (FastAPI)
- Python 3.11+
- LangChain & LangGraph
- PostgreSQL + pgvector (Supabase)
- Redis caching
- OpenAI GPT-4o
- Tavily search

### Frontend (Streamlit)
- Python 3.11+
- Quest and Crossfire™ branding
- Responsive UI
- Session management

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Poetry
- PostgreSQL with pgvector
- Redis

### Backend Setup

```bash
cd research-portal/backend
poetry install
poetry run python run_server.py
```

Backend runs on: `http://127.0.0.1:8000`

### Frontend Setup

```bash
cd research-portal/frontend
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

Frontend runs on: `http://localhost:8501`

### Default Login
- **Username**: `admin`
- **Password**: `aethelgard2024`

⚠️ **Change these before production deployment!**

---

## 📦 Deployment

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed instructions.

**Recommended**: Streamlit Cloud (frontend) + Render.com (backend)

---

## 🔑 Environment Variables

### Backend
```bash
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
LANGSMITH_API_KEY=ls__...
LANGSMITH_PROJECT=python-research-portal
```

### Frontend
```bash
API_BASE_URL=http://127.0.0.1:8000
AUTH_USERNAME=admin
AUTH_PASSWORD_HASH=<sha256_hash>
```

---

## 📚 Documentation

- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Production deployment
- [QUICK_START.md](./QUICK_START.md) - Local development
- [FINAL_SUMMARY.md](./FINAL_SUMMARY.md) - Project overview

---

## 🎯 Quality Pipeline

1. **Research Phase**
   - RAG retrieval (15 documents)
   - Tavily web search (8 sources)

2. **Quality Gate 1: Technical Generation**
   - GPT-4o (temperature=0.3)
   - Target: 95+ score
   - Max retries: 5

3. **Quality Gate 2: Technical Compilation**
   - GPT-4o (temperature=0.4)
   - PSW structure
   - Real-world examples
   - Reflection questions
   - Target: 95+ score
   - Max retries: 5

4. **Output**
   - Curriculum-ready Markdown
   - 11+ citations
   - 95+ quality score

---

## 🔒 Security

- SHA-256 password hashing
- Session-based authentication
- Environment variable secrets
- CORS protection
- API key encryption (Redis)

---

## 📊 Tech Stack

**Backend:**
- FastAPI
- LangChain & LangGraph
- OpenAI GPT-4o
- PostgreSQL + pgvector
- Redis
- Tavily
- LangSmith
- Honeycomb

**Frontend:**
- Streamlit
- Python 3.11+

---

## 📝 License

Proprietary - Quest and Crossfire™

---

## 🙏 Acknowledgments

Built for **Aethelgard Academy™** by **Quest and Crossfire™**

---

**Version**: 2.0  
**Status**: Production Ready  
**Last Updated**: November 8, 2025



