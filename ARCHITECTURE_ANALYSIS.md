# Curriculum Studio - Architecture Analysis
## Model Usage Across Both Systems

---

## SYSTEM 1: AXIS AI Chat Mode (`/chat/quick-qa`)
**Purpose:** Real-time tutoring with teaching modes  
**Entry Point:** `backend/app/api/routes/chat.py` → `quick_qa()` (line 212)

### Components:
1. **Teaching Mode System** (`app/services/teaching_modes.py`)
   - **Model:** Uses `request.model` OR `settings.openai_chat_model` (defaults to `gpt-4o`)
   - **Temperature:** Pulled from `TEACHING_MODE_CONFIG`:
     - Coach: `0.7` ❌ (NEEDS FIX for GPT-5)
     - Hybrid: `0.9` ❌ (NEEDS FIX for GPT-5)
     - Socratic: `1.0` ✅ (Already correct)

---

## SYSTEM 2: Curriculum Development Mode (`/chat/query`)
**Purpose:** Multi-agent pipeline for generating curriculum  
**Entry Point:** `backend/app/api/routes/chat.py` → `chat_query()` (line 100)  
**Orchestrator:** `ResearchGraph` (`app/graph/research_graph.py`)

### Multi-Agent Pipeline:

#### **Agent 1: Research & Synthesis** (`research_synthesis_agent.py`)
- **Model:** `gpt-4o` (hardcoded, line 122)
- **Temperature:** `settings.synthesis_temperature` (default: `0.3`) ❌ (NEEDS FIX if using GPT-5)
- **Purpose:** Combine RAG + web research into structured synthesis

#### **Agent 2: Structure Transformer** (`structure_transformer_agent.py`)
- **Model:** `gpt-4o` (hardcoded, line 126)
- **Temperature:** `settings.structure_temperature` (default: `0.4`) ❌ (NEEDS FIX if using GPT-5)
- **Purpose:** Transform into PSW framework

#### **Agent 3: Technical Compiler** (`technical_compiler.py`)
- **Model:** `gpt-4o` (hardcoded, line 222)
- **Temperature:** `settings.compiler_temperature` (default: `0.5`) ❌ (NEEDS FIX if using GPT-5)
- **Purpose:** Add code examples and technical details

#### **Agent 4: Narrative Enrichment** (`narrative_enrichment_v2.py`)
- **Model:** `settings.openai_chat_model` (via `get_chat_model`, line 66)
- **Temperature:** `settings.narrative_temperature` (default: `0.7`) ❌ (NEEDS FIX for GPT-5)
- **Purpose:** Add engaging narrative elements

---

### Additional Agents (Multi-Agent Legacy Pipeline):

#### **Complexity Classifier** (`complexity_classifier.py`)
- **Model:** `gpt-4o` (hardcoded, line 52)
- **Temperature:** `0.0` (hardcoded, line 54) ❌ (NEEDS FIX for GPT-5)
- **Purpose:** Classify question complexity

#### **Scenario Architect** (`scenario_architect.py`)
- **Model:** `gpt-4o` (hardcoded, line 97)
- **Temperature:** `0.4` (hardcoded, line 99) ❌ (NEEDS FIX for GPT-5)
- **Purpose:** Create real-world scenarios

#### **CoT Storyteller** (`cot_storyteller.py`)
- **Model:** `gpt-4o` (hardcoded, line 145)
- **Temperature:** `0.5` (hardcoded, line 147) ❌ (NEEDS FIX for GPT-5)
- **Purpose:** Chain-of-thought narrative generation

#### **Narrative Enricher (Legacy)** (`narrative_enricher.py`)
- **Model:** `gemini-1.5-pro` (Google Gemini, line 90) 🚨 **REMOVE - NOT USING GEMINI**
- **Temperature:** `settings.narrative_temperature` (default: `0.7`)
- **Purpose:** Aethelgard Academy brand polish

---

## Configuration File: `app/core/config.py`

### Temperature Settings (All need GPT-5 fixes):
```python
technical_temperature: 0.3      ❌ → 1.0
narrative_temperature: 0.7      ❌ → 1.0
scenario_temperature: 0.4       ❌ → 1.0
storyteller_temperature: 0.5    ❌ → 1.0
synthesis_temperature: 0.3      ❌ → 1.0
structure_temperature: 0.4      ❌ → 1.0
compiler_temperature: 0.5       ❌ → 1.0
```

### Model Settings:
```python
openai_chat_model: "gpt-4o"           # Can be overridden to "gpt-5"
openai_embedding_model: "text-embedding-3-small"  # ✅ OK (embeddings)
gemini_chat_model: "gemini-1.5-flash" # 🚨 REMOVE (not using)
```

---

## CRITICAL FINDINGS:

### ❌ Issues to Fix:
1. **Teaching Modes** (AXIS Chat):
   - Coach mode: temperature `0.7` → must be `1.0`
   - Hybrid mode: temperature `0.9` → must be `1.0`

2. **Multi-Agent Pipeline** (Curriculum):
   - All agents have hardcoded `gpt-4o` models
   - All agents have temperatures < 1.0 (incompatible with GPT-5)

3. **Gemini Reference** (NOT USED):
   - `narrative_enricher.py` imports and uses `ChatGoogleGenerativeAI`
   - This agent is conditionally enabled but should be removed entirely

### ✅ What's Safe:
- Embedding models (text-embedding-3-small) don't use temperature
- RAG/Tavily retrieval doesn't use LLMs directly

---

## DECISION NEEDED FROM YOU:

**Question 1:** Are you using `gpt-5` for ALL agents in the curriculum pipeline, or just some?
- If YES → I'll update ALL hardcoded `gpt-4o` references to use configurable model
- If NO → Which agents should stay on `gpt-4o` vs switch to `gpt-5`?

**Question 2:** For Narrative Enricher:
- Should I completely **delete** `narrative_enricher.py` (Gemini version)?
- Or just **disable** it in the config and keep the file for reference?

**Question 3:** Temperature strategy:
- Set ALL temperatures to `1.0` globally?
- Or keep some agents on `gpt-4o` with variable temperatures?

Once you answer these, I'll make surgical fixes across the codebase.

