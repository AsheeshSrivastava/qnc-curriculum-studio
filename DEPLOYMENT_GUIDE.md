# Deployment Guide - Curriculum Studio

## Quest and Crossfire™ | Aethelgard Academy™

**Version**: 2.0  
**Date**: November 8, 2025

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Authentication Setup](#authentication-setup)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Deployment Options](#deployment-options)
7. [Environment Variables](#environment-variables)
8. [Post-Deployment](#post-deployment)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The Curriculum Studio consists of two components:
- **Backend**: FastAPI application (Python)
- **Frontend**: Streamlit application (Python)

Both need to be deployed and configured to work together.

---

## ✅ Prerequisites

### Required Services:
- ✅ **PostgreSQL with pgvector** (Supabase recommended)
- ✅ **Redis** (for caching and secrets)
- ✅ **OpenAI API** (for embeddings and GPT-4o)
- ✅ **Tavily API** (for web search)
- ✅ **LangSmith** (optional, for tracing)
- ✅ **Honeycomb** (optional, for observability)

### Required Tools:
- Python 3.11+
- Poetry (for dependency management)
- Git

---

## 🔐 Authentication Setup

### Default Credentials (Development):
- **Username**: `admin`
- **Password**: `aethelgard2024`

### Production Credentials:

1. **Generate a secure password hash**:
```python
import hashlib

password = "your_secure_password"
password_hash = hashlib.sha256(password.encode()).hexdigest()
print(f"Password hash: {password_hash}")
```

2. **Set environment variables**:
```bash
export AUTH_USERNAME="your_username"
export AUTH_PASSWORD_HASH="your_generated_hash"
```

**⚠️ IMPORTANT**: Change the default credentials before deploying to production!

---

## 🔧 Backend Deployment

### Option 1: Deploy to Render.com (Recommended)

1. **Create a new Web Service** on Render.com

2. **Connect your GitHub repository**

3. **Configure Build Settings**:
   - **Build Command**:
     ```bash
     cd research-portal/backend && pip install poetry && poetry install --no-dev
     ```
   - **Start Command**:
     ```bash
     cd research-portal/backend && poetry run python run_server.py
     ```

4. **Set Environment Variables** (see [Environment Variables](#environment-variables))

5. **Deploy**: Render will automatically build and deploy

### Option 2: Deploy to Railway.app

1. **Create a new project** on Railway.app

2. **Connect your GitHub repository**

3. **Configure**:
   - Root Directory: `research-portal/backend`
   - Start Command: `poetry run python run_server.py`

4. **Set Environment Variables**

5. **Deploy**

### Option 3: Deploy to Heroku

1. **Create a new app**:
   ```bash
   heroku create your-app-name
   ```

2. **Add buildpack**:
   ```bash
   heroku buildpacks:set heroku/python
   ```

3. **Set environment variables**:
   ```bash
   heroku config:set OPENAI_API_KEY=your_key
   # ... set all other variables
   ```

4. **Deploy**:
   ```bash
   git push heroku main
   ```

### Option 4: Deploy to VPS (DigitalOcean, AWS EC2, etc.)

1. **SSH into your server**

2. **Install dependencies**:
   ```bash
   sudo apt update
   sudo apt install python3.11 python3-pip postgresql redis-server
   pip install poetry
   ```

3. **Clone repository**:
   ```bash
   git clone your-repo-url
   cd research-portal/backend
   ```

4. **Install Python dependencies**:
   ```bash
   poetry install --no-dev
   ```

5. **Set environment variables** in `.env` file or system

6. **Run with systemd** (create `/etc/systemd/system/curriculum-backend.service`):
   ```ini
   [Unit]
   Description=Curriculum Studio Backend
   After=network.target

   [Service]
   Type=simple
   User=your-user
   WorkingDirectory=/path/to/research-portal/backend
   Environment="PATH=/path/to/poetry/bin:$PATH"
   ExecStart=/path/to/poetry run python run_server.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

7. **Start service**:
   ```bash
   sudo systemctl enable curriculum-backend
   sudo systemctl start curriculum-backend
   ```

8. **Setup Nginx reverse proxy** (optional but recommended):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

---

## 🎨 Frontend Deployment

### Option 1: Deploy to Streamlit Cloud (Easiest)

1. **Go to** [share.streamlit.io](https://share.streamlit.io)

2. **Sign in with GitHub**

3. **New app**:
   - Repository: Your repo
   - Branch: `main`
   - Main file path: `research-portal/frontend/app.py`

4. **Advanced settings** → Set environment variables:
   ```
   API_BASE_URL=https://your-backend-url.com
   AUTH_USERNAME=your_username
   AUTH_PASSWORD_HASH=your_password_hash
   ```

5. **Deploy**: Streamlit Cloud handles everything

### Option 2: Deploy to Render.com

1. **Create a new Web Service**

2. **Configure**:
   - **Build Command**:
     ```bash
     cd research-portal/frontend && pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     cd research-portal/frontend && streamlit run app.py --server.port $PORT --server.address 0.0.0.0
     ```

3. **Set Environment Variables**

4. **Deploy**

### Option 3: Deploy to VPS

1. **SSH into server**

2. **Install dependencies**:
   ```bash
   cd research-portal/frontend
   pip install -r requirements.txt
   ```

3. **Create systemd service** (`/etc/systemd/system/curriculum-frontend.service`):
   ```ini
   [Unit]
   Description=Curriculum Studio Frontend
   After=network.target

   [Service]
   Type=simple
   User=your-user
   WorkingDirectory=/path/to/research-portal/frontend
   ExecStart=/usr/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

4. **Start service**:
   ```bash
   sudo systemctl enable curriculum-frontend
   sudo systemctl start curriculum-frontend
   ```

5. **Setup Nginx** (if needed)

---

## 🌐 Deployment Options Comparison

| Platform | Backend | Frontend | Difficulty | Cost | Notes |
|----------|---------|----------|------------|------|-------|
| **Streamlit Cloud + Render** | Render | Streamlit Cloud | ⭐ Easy | Free tier available | Recommended for quick deployment |
| **Railway** | Railway | Railway | ⭐⭐ Medium | Pay-as-you-go | Good for scaling |
| **Heroku** | Heroku | Heroku | ⭐⭐ Medium | Paid (no free tier) | Reliable but expensive |
| **VPS (DigitalOcean, AWS)** | VPS | VPS | ⭐⭐⭐ Hard | $5-20/month | Full control, best for production |
| **Docker + Cloud Run** | Cloud Run | Cloud Run | ⭐⭐⭐ Hard | Pay-per-use | Serverless, scalable |

---

## 🔑 Environment Variables

### Backend Environment Variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://host:6379/0

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Tavily
TAVILY_API_KEY=tvly-...

# LangSmith (Optional)
LANGSMITH_API_KEY=ls__...
LANGSMITH_PROJECT=python-research-portal

# Honeycomb (Optional)
HONEYCOMB_API_KEY=...

# Application
APP_ENV=production
LOG_LEVEL=INFO
CORS_ORIGINS=["https://your-frontend-url.com"]

# Quality Settings
ENABLE_TECHNICAL_COMPILER=true
COMPILER_QUALITY_THRESHOLD=95.0
QUALITY_THRESHOLD=95.0
```

### Frontend Environment Variables:

```bash
# Backend API
API_BASE_URL=https://your-backend-url.com

# Authentication
AUTH_USERNAME=your_username
AUTH_PASSWORD_HASH=your_generated_hash
```

---

## 📦 Docker Deployment (Advanced)

### Backend Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "run_server.py"]
```

### Frontend Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8501

# Run application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Docker Compose:

```yaml
version: '3.8'

services:
  backend:
    build: ./research-portal/backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - TAVILY_API_KEY=${TAVILY_API_KEY}
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./research-portal/frontend
    ports:
      - "8501:8501"
    environment:
      - API_BASE_URL=http://backend:8000
      - AUTH_USERNAME=${AUTH_USERNAME}
      - AUTH_PASSWORD_HASH=${AUTH_PASSWORD_HASH}
    depends_on:
      - backend

  postgres:
    image: ankane/pgvector:latest
    environment:
      - POSTGRES_DB=curriculum_studio
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## ✅ Post-Deployment Checklist

### 1. **Test Backend**:
```bash
curl https://your-backend-url.com/api/health
```
Expected: `{"status":"ok"}`

### 2. **Test Frontend**:
- Visit `https://your-frontend-url.com`
- Login with credentials
- Try uploading a document
- Try generating content

### 3. **Security**:
- ✅ Changed default credentials
- ✅ HTTPS enabled
- ✅ CORS configured correctly
- ✅ API keys secured in environment variables
- ✅ Database has strong password
- ✅ Redis password set (if exposed)

### 4. **Monitoring**:
- ✅ Check LangSmith traces
- ✅ Check Honeycomb metrics
- ✅ Set up uptime monitoring (UptimeRobot, Pingdom)
- ✅ Configure error alerts

### 5. **Backup**:
- ✅ Database backups enabled
- ✅ Document storage backed up
- ✅ Environment variables documented

---

## 🐛 Troubleshooting

### Backend Issues:

**Problem**: "Database connection failed"
- **Solution**: Check `DATABASE_URL` format and credentials
- Ensure pgvector extension is installed

**Problem**: "Redis connection failed"
- **Solution**: Check `REDIS_URL` and Redis server status

**Problem**: "OpenAI API error"
- **Solution**: Verify API key and check billing

### Frontend Issues:

**Problem**: "Cannot connect to backend"
- **Solution**: Check `API_BASE_URL` environment variable
- Ensure backend is running and accessible

**Problem**: "Login not working"
- **Solution**: Verify `AUTH_USERNAME` and `AUTH_PASSWORD_HASH`
- Check password hash was generated correctly

**Problem**: "Page not loading"
- **Solution**: Check Streamlit logs
- Ensure all dependencies are installed

### General Issues:

**Problem**: "Slow performance"
- **Solution**: 
  - Increase server resources
  - Enable Redis caching
  - Optimize database queries
  - Use CDN for assets

**Problem**: "Out of memory"
- **Solution**:
  - Increase RAM allocation
  - Reduce `chunk_size` in settings
  - Limit concurrent requests

---

## 📞 Support

For deployment support:
- Check logs first
- Review environment variables
- Test each component separately
- Contact: support@questandcrossfire.com

---

## 🎓 Recommended Production Setup

**For Quest and Crossfire™ / Aethelgard Academy™:**

1. **Backend**: Render.com or Railway (for simplicity)
2. **Frontend**: Streamlit Cloud (easiest) or Render
3. **Database**: Supabase (managed PostgreSQL + pgvector)
4. **Redis**: Upstash (managed Redis)
5. **Monitoring**: LangSmith + Honeycomb
6. **Domain**: Custom domain with HTTPS
7. **Backup**: Daily database backups

**Estimated Cost**: $20-50/month

---

**Quest and Crossfire™ | Aethelgard Academy™**  
**Curriculum Studio v2.0**  
**"Small Fixes, Big Clarity"**



