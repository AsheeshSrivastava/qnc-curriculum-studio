# Quick Start Guide - Curriculum Studio

## Quest and Crossfire™ | Aethelgard Academy™

---

## 🚀 Local Development

### 1. **Start Backend**:

```powershell
cd research-portal\backend
poetry run python run_server.py
```

Backend will run on: **http://127.0.0.1:8000**

### 2. **Start Frontend**:

```powershell
cd research-portal\frontend
streamlit run app.py --server.port 8501
```

Frontend will run on: **http://localhost:8501**

### 3. **Login**:

**Default Credentials**:
- Username: `admin`
- Password: `aethelgard2024`

---

## 🔐 Change Default Password

### Generate New Password Hash:

```python
import hashlib
password = "your_new_password"
hash = hashlib.sha256(password.encode()).hexdigest()
print(f"Set this as AUTH_PASSWORD_HASH: {hash}")
```

### Set Environment Variables:

```bash
# Windows PowerShell
$env:AUTH_USERNAME="your_username"
$env:AUTH_PASSWORD_HASH="your_generated_hash"

# Linux/Mac
export AUTH_USERNAME="your_username"
export AUTH_PASSWORD_HASH="your_generated_hash"
```

---

## 📦 What's Included

✅ **Authentication** - Login/logout system  
✅ **Upload** - Add Python learning materials  
✅ **Chat** - Generate curriculum content  
✅ **Quality Gates** - 95+ threshold enforcement  
✅ **Markdown Export** - Download curriculum-ready content  
✅ **Vector Database** - 67 Python materials indexed  
✅ **RAG + Web Search** - Hybrid retrieval system  

---

## 🎯 Quick Test

1. **Login** with default credentials
2. **Go to Chat** page
3. **Ask**: "What is a Python variable?"
4. **Wait** 60-120 seconds for quality-first generation
5. **Review** quality metrics (should be 95+)
6. **Download** as Markdown

---

## 📚 Next Steps

- Read [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for production deployment
- Read [UI_OVERHAUL_SUMMARY.md](./frontend/UI_OVERHAUL_SUMMARY.md) for features
- Change default credentials before deploying!

---

**Quest and Crossfire™ | Aethelgard Academy™**  
**"Small Fixes, Big Clarity"**



