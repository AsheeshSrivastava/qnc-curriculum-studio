# 🧪 Full Stack Integration Test Guide

**Date:** November 8, 2025  
**Purpose:** Comprehensive testing of Python Research Portal

---

## ✅ Pre-Test Checklist

### Services Running:
- [ ] Backend: `http://127.0.0.1:8000` ✅ **RUNNING**
- [ ] Frontend: `http://localhost:8501` ✅ **STARTING**
- [ ] Database: Supabase (cloud) ✅
- [ ] Redis: Upstash (cloud) ✅

### API Keys Available:
- [ ] OpenAI API key
- [ ] Tavily API key (for web search)
- [ ] LangSmith API key (for tracing)

---

## 🧪 Test Plan

### Phase 1: Frontend Connectivity (5 minutes)
### Phase 2: API Key Configuration (2 minutes)
### Phase 3: Document Upload (5 minutes)
### Phase 4: Chat & RAG (10 minutes)
### Phase 5: Quality Evaluation (5 minutes)
### Phase 6: Export Functionality (5 minutes)
### Phase 7: Library Management (3 minutes)

**Total Time:** ~35 minutes

---

## 📋 Phase 1: Frontend Connectivity

### Test 1.1: Access Frontend
1. Open browser to: `http://localhost:8501`
2. **Expected:** Home page loads with "🔬 Python Research Portal"
3. **Verify:** 
   - Navigation sidebar visible
   - "Backend Connected" status shows ✅
   - Quick start guide displayed

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 1.2: Navigation
1. Click through all pages:
   - 📄 Upload
   - 💬 Chat
   - 📚 Library
   - ⚙️ Settings
2. **Expected:** All pages load without errors
3. **Verify:** Each page has proper header and content

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 1.3: Backend Connection Status
1. Check sidebar for "🔌 Connection Status"
2. **Expected:** Shows "✅ Backend Connected"
3. **If fails:** Check backend is running at port 8000

**Status:** ⬜ Pass / ⬜ Fail

---

## 📋 Phase 2: API Key Configuration

### Test 2.1: Navigate to Settings
1. Go to **⚙️ Settings** page
2. Click on **🔑 API Keys** tab
3. **Expected:** Three provider sections visible

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 2.2: Configure OpenAI Key
1. Expand **🟢 OpenAI** section
2. Enter your OpenAI API key
3. Click **💾 Save OpenAI Key**
4. **Expected:** 
   - Success message: "✅ OpenAI API key saved!"
   - Status shows: "✅ OpenAI key is configured"
5. **Verify:** Sidebar shows "✅ OpenAI key configured"

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 2.3: Select Default Provider
1. Go to **🤖 Provider Settings** tab
2. Select **🟢 OpenAI**
3. **Expected:** Provider status shows "✅ Ready"

**Status:** ⬜ Pass / ⬜ Fail

---

## 📋 Phase 3: Document Upload

### Test 3.1: Navigate to Upload Page
1. Go to **📄 Upload** page
2. **Expected:** Upload form displayed with file uploader

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 3.2: Create Test Document
**Create a simple Python guide:**

1. Create file: `python_functions_test.md`
2. Content:
```markdown
# Python Functions Guide

## Introduction
Functions are reusable blocks of code in Python.

## Defining Functions
```python
def greet(name):
    return f"Hello, {name}!"
```

## Function Parameters
- Positional parameters
- Keyword parameters
- Default parameters
- *args and **kwargs

## Return Values
Functions can return single or multiple values.

## Best Practices
1. Use descriptive names
2. Keep functions small
3. Document with docstrings
4. Follow PEP 8
```

**Status:** ⬜ Created

---

### Test 3.3: Upload Document
1. Click **"Choose a file"** or drag & drop
2. Select `python_functions_test.md`
3. Enter:
   - **Title:** "Python Functions Guide"
   - **Description:** "Comprehensive guide to Python functions"
4. Click **🚀 Upload & Process**
5. **Expected:**
   - Processing spinner appears
   - Success message after 10-30 seconds
   - Shows document ID and chunk count
6. **Verify:** Chunk count should be 1-3 chunks

**Status:** ⬜ Pass / ⬜ Fail  
**Chunks Created:** _____

---

### Test 3.4: Verify in Recent Uploads
1. Scroll down to "📋 Recent Uploads"
2. **Expected:** Your document appears in the list
3. **Verify:** Title, type, and date are correct

**Status:** ⬜ Pass / ⬜ Fail

---

## 📋 Phase 4: Chat & RAG

### Test 4.1: Navigate to Chat
1. Go to **💬 Chat** page
2. **Expected:** Clean chat interface with input box

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 4.2: Simple Question (RAG Retrieval)
1. Type: **"What are Python functions?"**
2. Press Enter
3. **Expected:**
   - "🤔 Thinking..." spinner appears
   - Answer appears within 5-10 seconds
   - Answer mentions functions are reusable blocks of code
4. **Verify:**
   - Answer is coherent
   - Citations section appears (📚 Sources & Citations)
   - Quality evaluation section appears (📊 Quality Evaluation)

**Status:** ⬜ Pass / ⬜ Fail  
**Response Time:** _____ seconds

---

### Test 4.3: Check Citations
1. Expand **📚 Sources & Citations**
2. **Expected:**
   - At least 1 citation listed
   - Shows document title: "Python Functions Guide"
   - Shows source type: markdown
   - Shows relevance score
3. **Verify:** Content preview matches uploaded document

**Status:** ⬜ Pass / ⬜ Fail  
**Citations Found:** _____

---

### Test 4.4: Check Quality Evaluation
1. Expand **📊 Quality Evaluation**
2. **Expected:**
   - Overall score displayed (out of 100)
   - Status: ✅ Passed or ❌ Failed
   - Gates Passed: X/4
   - Criteria scores with progress bars
3. **Verify:** Score should be ≥ 85 for passing

**Status:** ⬜ Pass / ⬜ Fail  
**Overall Score:** _____ / 100  
**Passed:** ⬜ Yes / ⬜ No

---

### Test 4.5: Follow-up Question
1. Type: **"How do I use default parameters?"**
2. Press Enter
3. **Expected:**
   - Answer references previous context
   - Provides specific information about default parameters
   - Citations still appear

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 4.6: Web Search Fallback (Optional)
1. Type: **"What's new in Python 3.13?"**
2. Press Enter
3. **Expected:**
   - Since this isn't in your uploaded docs, system should use web search
   - Answer should mention recent Python features
   - Citations may include web sources

**Status:** ⬜ Pass / ⬜ Fail / ⬜ Skipped

---

### Test 4.7: Streaming Mode
1. Toggle **🌊 Stream Responses** ON
2. Type: **"Explain function decorators"**
3. Press Enter
4. **Expected:**
   - Answer appears word-by-word in real-time
   - Streaming indicator visible
   - Final answer is complete

**Status:** ⬜ Pass / ⬜ Fail

---

## 📋 Phase 5: Quality Evaluation

### Test 5.1: Review Quality Metrics
1. Look at the last answer's quality evaluation
2. **Check these criteria:**
   - Groundedness & Citation: ____ / 20
   - Technical Correctness: ____ / 15
   - People-First Pedagogy: ____ / 15
   - PSW Actionability: ____ / 10
   - Mode Fidelity: ____ / 10
   - Self-Paced Scaffolding: ____ / 10
   - Retrieval Quality: ____ / 10
   - Clarity: ____ / 5
   - Bloom Alignment: ____ / 3
   - People-First Language: ____ / 2

**Status:** ⬜ Reviewed

---

### Test 5.2: Quality Gates
1. Check quality gates status:
   - Coverage Score ≥ 0.65: ⬜ Pass / ⬜ Fail
   - Citation Density ≥ 1.0: ⬜ Pass / ⬜ Fail
   - Execution OK: ⬜ Pass / ⬜ Fail
   - Scope OK: ⬜ Pass / ⬜ Fail

**Status:** ⬜ All Passed / ⬜ Some Failed

---

## 📋 Phase 6: Export Functionality

### Test 6.1: Export as Markdown
1. Scroll down to **💾 Export Conversation**
2. Click **📝 Export as Markdown**
3. Click **⬇️ Download Markdown**
4. **Expected:** File downloads as `conversation.md`
5. **Verify:** 
   - Open file
   - Contains question and answer
   - Formatted properly
   - Citations included

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 6.2: Export as JSON
1. Click **📊 Export as JSON**
2. Click **⬇️ Download JSON**
3. **Expected:** File downloads as `conversation.json`
4. **Verify:**
   - Open file
   - Valid JSON format
   - Contains all data (question, answer, citations, evaluation)

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 6.3: Export as PDF
1. Click **📄 Export as PDF**
2. Click **⬇️ Download PDF**
3. **Expected:** File downloads as `conversation.pdf`
4. **Verify:**
   - Open PDF
   - Readable format
   - Contains conversation

**Status:** ⬜ Pass / ⬜ Fail

---

## 📋 Phase 7: Library Management

### Test 7.1: Navigate to Library
1. Go to **📚 Library** page
2. **Expected:** Document grid displays
3. **Verify:** Your uploaded document appears

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 7.2: Search Functionality
1. Type "functions" in search box
2. **Expected:** Document filters to show only matching documents
3. **Verify:** "Python Functions Guide" appears

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 7.3: Sort Functionality
1. Change sort to **📅 Newest First**
2. **Expected:** Documents reorder by date
3. Try **🔤 Title A-Z**
4. **Expected:** Documents sort alphabetically

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 7.4: Document Details
1. Click **ℹ️ Details** on your document
2. **Expected:**
   - Details section expands
   - Shows full metadata
   - Action buttons available

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 7.5: Library Statistics
1. Scroll to **📈 Library Statistics**
2. **Expected:**
   - Total Documents: 1 (or more)
   - Markdown Files: 1
   - Other counts accurate

**Status:** ⬜ Pass / ⬜ Fail

---

## 📋 Additional Tests

### Test 8.1: Clear Chat History
1. Go to **💬 Chat** page
2. Click **🗑️ Clear Chat History**
3. **Expected:** All messages disappear

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 8.2: Error Handling
1. Go to **💬 Chat**
2. Try asking without API key configured
3. **Expected:** Error message appears
4. **Verify:** Helpful error message

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 8.3: Multiple Providers (Optional)
1. Configure Gemini or OpenRouter key
2. Switch provider in Settings
3. Ask a question
4. **Expected:** Different provider responds

**Status:** ⬜ Pass / ⬜ Fail / ⬜ Skipped

---

## 📊 Test Summary

### Results:
- **Total Tests:** 30
- **Passed:** _____
- **Failed:** _____
- **Skipped:** _____

### Pass Rate: _____ %

---

## 🐛 Issues Found

| Test | Issue | Severity | Notes |
|------|-------|----------|-------|
|      |       |          |       |
|      |       |          |       |
|      |       |          |       |

---

## ✅ Sign-Off

**Tested By:** _________________  
**Date:** _________________  
**Overall Status:** ⬜ Pass / ⬜ Fail  
**Ready for Production:** ⬜ Yes / ⬜ No

---

## 📝 Notes

_Add any additional observations or comments here:_

---

**Next Steps:**
- [ ] Fix any critical issues
- [ ] Retest failed scenarios
- [ ] Document workarounds
- [ ] Proceed to deployment



