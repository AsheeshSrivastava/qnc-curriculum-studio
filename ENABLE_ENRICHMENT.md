# Quick Start: Enable Narrative Enrichment

## What This Does

Transforms technical Python answers into engaging learning experiences with:
- Industry context and practical urgency
- Realistic variable names (`countries`, `users`, not `x`, `y`)
- Common pitfalls as cautionary tales
- Reflection questions for deeper learning

## Prerequisites

✅ Backend running  
✅ Google Gemini API key  
✅ 51 Python documents ingested (already done)

## Step 1: Update Settings

Edit `backend/config/settings.env`:

```bash
# Enable narrative enrichment (Aethelgard Academy)
ENABLE_NARRATIVE_ENRICHMENT=true
ENRICHMENT_QUALITY_THRESHOLD=90.0
ENRICHMENT_CACHE_ENABLED=true

# Ensure Gemini API key is set (already configured)
GOOGLE_API_KEY=your_existing_key_here
```

## Step 2: Restart Backend

```powershell
# Stop existing backend
Get-Process | Where-Object {$_.ProcessName -like "*uvicorn*"} | Stop-Process -Force

# Start with enrichment enabled
cd D:\claude-projects\portfolio\projects\research-portal\backend
poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Step 3: Test with Anaconda Question

Open frontend (http://localhost:8501) or use curl:

```bash
curl -X POST http://127.0.0.1:8000/api/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is Anaconda?",
    "provider": "openai",
    "history": []
  }'
```

## What to Look For

### ✅ Good Enrichment
- Opens with WHY it matters ("When your Flask app works locally but crashes in production...")
- Flows like a story (no section headers like "## Common Pitfalls")
- Uses realistic examples (`project_env`, not `myenv`)
- Includes ONE pitfall as a story
- Ends with a reflection question
- ALL citations preserved [doc-1], [doc-2]

### ❌ Bad Enrichment (shouldn't happen)
- Section headers visible
- Bullet points instead of narrative
- Generic examples (`x = 1`)
- Citations missing
- No industry context

## Troubleshooting

### Enrichment Not Happening?

Check logs for:
```
graph.enrich.start
```

If not present:
1. Verify `ENABLE_NARRATIVE_ENRICHMENT=true` in settings.env
2. Check `GOOGLE_API_KEY` is set
3. Restart backend completely

### Getting Original Answer?

This is normal for:
- BASIC questions with quality score >= 90 (e.g., "What is a variable?")
- Enrichment failures (graceful fallback)

Check logs for:
```
graph.enrich.failed
narrative_enricher.enrich.validation_failed
```

### Enrichment Too Slow?

Expected latency:
- BASIC + high quality: 8-12s (no enrichment)
- STANDARD/COMPLEX: 14-20s (with enrichment)

If slower:
- Check Gemini API latency
- Consider enabling caching (already enabled by default)

## Disable Enrichment

If you want to go back:

```bash
# In backend/config/settings.env
ENABLE_NARRATIVE_ENRICHMENT=false
```

Restart backend → System reverts to original behavior (no code changes needed)

## Next: Test These Questions

1. **BASIC** (should skip enrichment if quality >= 90):
   - "What is a variable?"
   - "Define a list"

2. **STANDARD** (should always enrich):
   - "How do I create a virtual environment?"
   - "How do I use list comprehensions?"

3. **COMPLEX** (should always enrich):
   - "Why is dependency management important in production?"
   - "When should I use async/await vs threading?"

Compare enriched vs original to see the difference!

---

**Ready?** Update settings.env, restart backend, and test! 🚀

