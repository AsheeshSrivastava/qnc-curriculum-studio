# 🔍 **OUTPUT QUALITY ANALYSIS & FIXES**

**Date**: November 8, 2025  
**Analyst**: Expert Prompt Engineer + Software Architect  
**Status**: 🚧 **IN PROGRESS**

---

## 🎯 **USER FEEDBACK**

> "The output of the recent is not very user-friendly. It's like a big chunk of text in a whole large paragraph is shown. So the output needs to be user-friendly. There is no code."

---

## 📊 **CURRENT STATE ANALYSIS**

### **Problem 1: Poor Formatting (Wall of Text)**

**Symptoms**:
- Large paragraphs with no breaks
- No visual hierarchy
- No code blocks despite Python content
- Hard to scan/read

**Root Cause**: Generation prompt doesn't ENFORCE structure strongly enough

### **Problem 2: Missing Code Examples**

**Symptoms**:
- `exec_ok` check failing (no ``` blocks)
- Evaluator looking for: `"```" in answer or "import", "def", "class"`
- Generation quality: 57-81/85 (failing)

**Root Cause**: Model not following "3-5 code blocks" instruction

### **Problem 3: Inconsistent Quality**

**Generation Scores** (gpt-4o-mini):
```
Attempt 1: 65.83/85
Attempt 2: 57.5/85  ← Got WORSE
Attempt 3: 80.17/85  ← Close!
Attempt 4: 66.83/85
Attempt 5: 68.33/85
Attempt 6: 68.33/85 ← Gave up
```

**Variance**: 57.5 → 80.17 (22.67 point swing!)

---

## 🔬 **DEEP DIVE: WHAT'S BEING EVALUATED**

### **Quality Rubric** (100 points total):

| Criterion | Points | What It Checks |
|-----------|--------|----------------|
| **Groundedness** | 20 | Citations + coverage |
| **Technical Correctness** | 15 | Python keywords, no errors |
| **People-First Pedagogy** | 15 | "Let's", "You will", "Consider" |
| **PSW Actionability** | 10 | Problem, System, Win elements |
| **Mode Fidelity** | 10 | Coaching mode alignment |
| **Self-Paced Scaffolding** | 10 | Progressive difficulty |
| **Retrieval Quality** | 10 | Source diversity |
| **Clarity** | 5 | Sentence length (8-28 words) |
| **Bloom Alignment** | 3 | Cognitive depth |
| **People-First Language** | 2 | Inclusive language |

### **Quality Gates** (Must ALL pass):
- ✅ Total score ≥ 85/100
- ✅ Coverage ≥ 0.65 (use 65% of sources)
- ✅ Citation density ≥ 1.0 (1 citation per 150 words)
- ✅ `exec_ok`: Has code blocks OR Python keywords
- ✅ `scope_ok`: Mentions question terms + "python"

---

## 🚨 **CRITICAL ISSUES IDENTIFIED**

### **Issue 1: Generation Prompt Too Vague**

**Current Prompt Structure**:
```
=== RESPONSE STRUCTURE ===

**PART 1: FOUNDATION (2-3 paragraphs)**
- Define the concept clearly [cite official docs]
- Explain why it matters [cite multiple sources]
- Show simplest example [cite syntax source]
```

**Problem**: Says "2-3 paragraphs" but doesn't FORCE line breaks!

**Fix Needed**: Explicit markdown formatting instructions

---

### **Issue 2: Code Block Instructions Buried**

**Current**:
```
**CODE BLOCKS**: Include 3-5 runnable examples
```python
# Simple example with output
numbers = [x**2 for x in range(5)]
# Output: [0, 1, 4, 9, 16]
```
```

**Problem**: 
- Instruction is in middle of long prompt
- No explicit "YOU MUST" language
- No verification checkpoint

**Fix Needed**: Move to top, make mandatory, add checklist

---

### **Issue 3: No Formatting Template**

**Current**: Describes structure in prose  
**Needed**: Actual markdown template to copy

---

## 💡 **SOLUTION: 3-LAYER FIX**

### **Layer 1: MANDATORY Code Blocks (Immediate)**

Add to top of SYSTEM_PROMPT:

```markdown
=== NON-NEGOTIABLE REQUIREMENTS ===

1. **CODE BLOCKS**: You MUST include 3-5 code examples in ```python blocks
2. **FORMATTING**: Use markdown headers (##, ###) and line breaks
3. **STRUCTURE**: Follow the exact template below

If you don't include code blocks, you FAIL automatically.
```

### **Layer 2: Explicit Markdown Template**

Replace vague "PART 1: FOUNDATION (2-3 paragraphs)" with:

```markdown
## Understanding [Concept Name]

[Opening paragraph: What is it?]

[Second paragraph: Why does it matter?]

### Basic Syntax

```python
# Simplest example
[code here]
```

[Explanation paragraph]
```

### **Layer 3: Pre-Submission Checklist**

Add at end of prompt:

```markdown
=== BEFORE YOU SUBMIT, VERIFY ===

Count these in your response:
□ Code blocks (```python): ____ (need 3-5)
□ Markdown headers (##, ###): ____ (need 4-6)
□ Paragraphs with line breaks: ____ (need 8-12)
□ Citations: ____ (need 15-25)

If ANY count is below minimum, REVISE before submitting.
```

---

## 🎯 **RECOMMENDED FIXES (Priority Order)**

### **FIX 1: Upgrade to GPT-4o** ✅ **DONE**
- **Status**: Committed (commit `09ebb02`)
- **Expected Impact**: +10-15 points, better instruction following
- **Cost**: $0.10/query (vs $0.018)

### **FIX 2: Add Mandatory Code Block Requirement** 🔄 **NEXT**
- **Where**: Top of `SYSTEM_PROMPT` in `research_graph.py`
- **What**: Explicit "YOU MUST" language
- **Expected Impact**: `exec_ok` passes 100% of time

### **FIX 3: Add Markdown Template** 🔄 **NEXT**
- **Where**: Replace prose structure with actual template
- **What**: Copy-paste markdown structure
- **Expected Impact**: Consistent formatting, visual hierarchy

### **FIX 4: Add Pre-Submission Checklist** 🔄 **NEXT**
- **Where**: End of `SYSTEM_PROMPT`
- **What**: Force LLM to count before submitting
- **Expected Impact**: Self-correction, fewer retries

### **FIX 5: Lower Quality Threshold Temporarily** ⏸️ **OPTIONAL**
- **Where**: `app/core/config.py`
- **What**: Change `min_total_score` from 85 → 80
- **Why**: Give GPT-4o a chance to stabilize
- **Risk**: May accept lower quality

---

## 📈 **EXPECTED RESULTS AFTER FIXES**

### **Before** (gpt-4o-mini):
```
Generation: 57-80/85 (inconsistent)
Compiler: 56-79/95 (failing structure)
Output: Wall of text, no code
User Experience: ❌ Poor
```

### **After** (gpt-4o + prompt fixes):
```
Generation: 85-92/85 (passing first try)
Compiler: 95-100/95 (passing)
Output: Structured markdown with code
User Experience: ✅ Excellent
```

---

## 🔧 **IMPLEMENTATION PLAN**

### **Phase 1: Model Upgrade** ✅ **COMPLETE**
- [x] Change `openai_chat_model` to `gpt-4o`
- [x] Update `complexity_classifier` to `gpt-4o`
- [x] Commit and deploy

### **Phase 2: Prompt Engineering** 🔄 **IN PROGRESS**
- [ ] Add mandatory code block requirement
- [ ] Create explicit markdown template
- [ ] Add pre-submission checklist
- [ ] Test with 3 queries
- [ ] Measure improvement

### **Phase 3: Fine-Tuning** ⏸️ **IF NEEDED**
- [ ] Adjust quality thresholds
- [ ] Optimize retry logic
- [ ] Add more specific examples

---

## 🎓 **PROMPT ENGINEERING PRINCIPLES APPLIED**

1. **Explicit > Implicit**: "You MUST" vs "Include"
2. **Template > Description**: Show exact format vs describe it
3. **Verification > Trust**: Force counting before submission
4. **Top-Heavy**: Critical requirements at START of prompt
5. **Examples with Markers**: Use ✅/❌ to show good/bad

---

## 📝 **NEXT ACTIONS**

1. ✅ **Deploy GPT-4o upgrade** (pushing now)
2. 🔄 **Update SYSTEM_PROMPT** with 3 fixes
3. 🔄 **Test with sample query**
4. 🔄 **Measure improvement**
5. 🔄 **Iterate if needed**

---

**Status**: Ready to implement Phase 2 (Prompt Engineering)  
**ETA**: 30-45 minutes  
**Expected Quality**: 85-95/100 (vs 57-80 now)

