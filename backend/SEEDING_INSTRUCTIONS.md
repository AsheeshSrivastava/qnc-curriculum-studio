# 🌱 Database Seeding Instructions

## Overview
This script will download Python official documentation from python.org and seed your Render PostgreSQL database with ~40 high-quality learning documents.

## Prerequisites
- Python 3.11+ with Poetry installed
- OpenAI API key
- Render PostgreSQL connection URL

## Step-by-Step Instructions

### 1. Get Your Database URL

Go to your Render dashboard:
1. Navigate to: https://dashboard.render.com/d/dpg-d47gd53ipnbc73crsan0-a
2. Scroll down to **"Connections"** section
3. Copy the **"Internal Database URL"** (it looks like: `postgresql://curriculum_user:...@...`)

### 2. Set Environment Variables

**On Windows (PowerShell):**
```powershell
$env:DATABASE_URL="postgresql://curriculum_user:YOUR_PASSWORD@dpg-d47gd53ipnbc73crsan0-a.singapore-postgres.render.com/curriculum_db_wdtc"
$env:OPENAI_API_KEY="sk-YOUR_OPENAI_KEY"
```

**On macOS/Linux (Bash):**
```bash
export DATABASE_URL="postgresql://curriculum_user:YOUR_PASSWORD@dpg-d47gd53ipnbc73crsan0-a.singapore-postgres.render.com/curriculum_db_wdtc"
export OPENAI_API_KEY="sk-YOUR_OPENAI_KEY"
```

### 3. Navigate to Backend Directory

```bash
cd D:\claude-projects\portfolio\projects\research-portal\backend
```

### 4. Run the Seeding Script

```bash
poetry run python seed_python_docs.py
```

## What to Expect

The script will:
1. ✅ Download 40 Python documentation pages from python.org
2. ✅ Process each page (extract text, chunk into 800-char pieces)
3. ✅ Generate embeddings using OpenAI API
4. ✅ Upload to your Render PostgreSQL database

**Estimated time:** 5-10 minutes (depends on network speed)

**Output example:**
```
============================================================
🌱 SEEDING PYTHON DOCUMENTATION
============================================================

[1/40] Processing: Python Tutorial: Introduction
  📥 Downloading: Python Tutorial: Introduction
  ✂️  Chunking...
  🧮 Generating embeddings for 12 chunks...
  ✅ Stored: 12 chunks

[2/40] Processing: Python Tutorial: Control Flow
  📥 Downloading: Python Tutorial: Control Flow
  ✂️  Chunking...
  🧮 Generating embeddings for 15 chunks...
  ✅ Stored: 15 chunks

...

============================================================
✅ SEEDING COMPLETE
============================================================
📊 Documents uploaded: 38
📦 Total chunks created: 487
❌ Failed documents: 2
⏱️  Time elapsed: 342.5s
📈 Average: 9.0s per document
============================================================

🔍 VERIFYING DATABASE...
✅ Documents in database: 38
✅ Chunks in database: 487
✅ Sample document: Python Tutorial: Introduction
   URL: https://docs.python.org/3/tutorial/introduction.html

🎉 SUCCESS! Your database is now seeded with Python documentation.
```

## Troubleshooting

### Error: "DATABASE_URL environment variable not set"
- Make sure you ran the `export` or `$env:` command in the same terminal window
- Check that you copied the full URL including the password

### Error: "OPENAI_API_KEY environment variable not set"
- Make sure you set your OpenAI API key
- Get it from: https://platform.openai.com/api-keys

### Error: "Failed to download..."
- Check your internet connection
- Some pages might be temporarily unavailable (the script will skip them)

### Error: "Connection refused" or "Database error"
- Verify your DATABASE_URL is correct
- Check that your Render PostgreSQL is running (status: "available")
- Ensure your IP is allowed (currently set to 0.0.0.0/0 - everywhere)

## After Seeding

Once complete, you can:

1. **Test RAG retrieval** - Ask a Python question in your frontend
2. **Check Render logs** - Look for `rag_docs > 0` instead of `rag_docs=0`
3. **Verify quality** - Answers should now include citations like `[doc-1]`, `[doc-2]`

## Cost Estimate

**OpenAI API costs:**
- ~40 documents × ~500 tokens each = ~20,000 tokens
- Embedding cost: ~$0.002 per 1K tokens
- **Total: ~$0.04** (4 cents)

Very affordable! 💰

## Need Help?

If you encounter any issues, share the error message and I'll help debug!

