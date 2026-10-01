# KnowledgeGuard AI
### *An Agentic RAG System for Detecting Outdated and Conflicting Knowledge in AI Systems*

---

## 1. Problem: Knowledge Decay in Modern AI Systems
Modern AI applications, enterprise agents, and conversational assistants rely heavily on external knowledge bases (internal documentation, Confluence pages, API specifications, and regulatory policy PDFs). 

However, **organizational knowledge changes continuously**:
* APIs and libraries are deprecated or upgraded.
* Architecture standards evolve from legacy protocols to zero-trust standards.
* Contradictory policies are published by different teams across different timeframes.

Standard Retrieval-Augmented Generation (RAG) pipelines blindly retrieve passages that match lexical or semantic query similarity without conducting a dedicated temporal or logical investigation. As a result, AI applications hallucinate outdated advice (e.g. recommending deprecated APIs) or assert invalid assumptions with unwarranted confidence.

---

## 2. Solution: The Knowledge Reliability Layer
**KnowledgeGuard AI** serves as an autonomous **Knowledge Reliability Layer** situated between external documentation and operational AI systems. 

Rather than treating retrieved knowledge as absolute truth, KnowledgeGuard AI systematically investigates claims against ingested source documents and classifies knowledge into four verified states:
* **`CURRENT`**: Available evidence actively corroborates the stored knowledge without deprecation or dispute.
* **`OUTDATED`**: Reliable newer or superseding evidence proves the stored knowledge has decayed or been deprecated.
* **`CONFLICTING`**: Multiple active documentation sources specify mutually contradictory requirements.
* **`UNCERTAIN`**: Available evidence is missing, ambiguous, or lacks conclusive proof.

---

## 3. Required Architecture: `RAG → AI Agent → LLM → Classification`

```
┌────────────────────────────────────────────────────────┐
│                      User Claim                        │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                     RAG Layer                          │
│   • Semantic Vector Retrieval via ChromaDB             │
│   • Metadata extraction (Source, Version, Doc Date)   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│         Knowledge Investigator Agent (LangGraph)       │
│   • Evaluates evidence sufficiency                     │
│   • Executes fallback query expansion if insufficient  │
│   • Cross-compares temporal & version evolution        │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                   LLM Reasoning                        │
│   • Strict evidence-bound prompt constraints           │
│   • Zero external hallucination                        │
│   • Calibrated confidence & recommendation             │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│               Knowledge Classification                 │
│       CURRENT | OUTDATED | CONFLICTING | UNCERTAIN     │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                 Human Verification                     │
│   • Human-in-the-loop audit & deprecation approvals   │
└────────────────────────────────────────────────────────┘
```

---

## 4. Technologies Used
* **Frontend**: React 19, Vite, Tailwind CSS v4, Lucide React, Axios (Render Static Site).
* **Backend**: Python 3.12+, FastAPI, Uvicorn, Pydantic v2 (Render Web Service).
* **Agent Framework**: LangGraph, LangChain Core (10-node state machine workflow).
* **Vector Database**: ChromaDB (Persistent Disk volume / HttpClient).
* **Embeddings**: ChromaDB default embedding model (`all-MiniLM-L6-v2`) with zero-dependency local embedding fallback.
* **Relational Database**: PostgreSQL via SQLAlchemy ORM (with seamless SQLite fallback for local development).
* **Document Processing**: `pypdf` for PDF parsing and recursive text chunking.
* **LLM Engine**: Groq API (`openai/gpt-oss-120b`) / Gemini / OpenAI client with integrated local semantic inference fallback.
* **Production Deployment**: Render (Full Blueprint via `render.yaml` & manual instructions in `DEPLOYMENT.md`).

---


## 5. Project Structure

```
c:/Users/pardhu/Downloads/FAI_PROJECT_2NDYEAR_TERM1/
├── frontend/                     # React + Vite + Tailwind frontend
│   ├── src/
│   │   ├── components/           # Sidebar, StatusBadge, ResultCard, AgentStepsProgress
│   │   ├── pages/                # Dashboard, KnowledgeBase, Investigate, History, About
│   │   ├── services/             # Axios API client (proxied to backend)
│   │   ├── App.jsx               # Main React application
│   │   └── index.css             # Tailwind base styles
│   ├── package.json
│   └── vite.config.js
├── backend/                      # FastAPI Python backend
│   ├── api/                      # REST endpoints (documents, investigate, dashboard)
│   ├── agents/                   # LangGraph Knowledge Investigator Agent & tools
│   ├── rag/                      # ChromaDB manager, text splitter, document loader
│   ├── llm/                      # Prompt templates & LLM client
│   ├── database/                 # SQLite connection & CRUD operations
│   ├── models/                   # SQLAlchemy entities & Pydantic schemas
│   ├── services/                 # Document & investigation coordination services
│   ├── utils/                    # Config settings and logging
│   └── main.py                   # FastAPI entrypoint
├── data/
│   ├── sample_documents/         # Official demonstration documents (.txt and .pdf)
│   ├── uploads/                  # Ingested user documents
│   └── chroma_db/                # Persistent vector database directory
├── .env                          # Local environment settings
├── .env.example                  # Template configuration file
├── .gitignore                    # Git exclusions
├── requirements.txt              # Python dependencies
└── test_scenarios.py             # Automated scenario verification test suite
```

---

## 6. Installation & Setup

### Prerequisites
* Python 3.10+ (tested on Python 3.14)
* Node.js 18+ and npm

### 1. Backend Setup
```bash
# In project root:
# 1. Create and activate virtual environment:
python -m venv .venv
.\.venv\Scripts\activate   # Windows PowerShell
# source .venv/bin/activate  # macOS/Linux

# 2. Install Python dependencies:
pip install -r requirements.txt

# 3. Configure environment:
cp .env.example .env
```

### 2. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

---

## 7. Environment Variables (`.env`)
The application is pre-configured to work immediately out of the box with its resilient local reasoning engine. To connect live cloud LLM reasoning (OpenAI or Groq), configure:

```ini
# LLM Provider: openai | groq
LLM_PROVIDER=openai
LLM_API_KEY=your_api_key_here
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=

# ChromaDB & Port
PORT=8000
HOST=127.0.0.1
ENV=development
```

---

## 8. Running the Application

### Start Backend Server:
```bash
# In project root with active .venv:
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Backend API will be accessible at: `http://127.0.0.1:8000` (API documentation at `http://127.0.0.1:8000/docs`).

### Start Frontend Server:
```bash
# In a separate terminal:
cd frontend
npm run dev
```
Frontend will be accessible at: `http://localhost:5173`.

---

## 9. Automated Testing
To run the automated verification suite covering all 4 core scenarios:
```bash
.\.venv\Scripts\python.exe test_scenarios.py
```
Expected output:
```
--- RUNNING SCENARIO VERIFICATION TESTS ---
[PASS] Claim: 'Is API v2 still recommended?' -> Result: OUTDATED
[PASS] Claim: 'Is Python 3.12 supported?' -> Result: CURRENT
[PASS] Claim: 'What authentication protocol is required?' -> Result: CONFLICTING
[PASS] Claim: 'Is quantum encryption mandated for all internal APIs?' -> Result: UNCERTAIN

Final Result: ALL TESTS PASSED
```

---

## 9.5. Production Deployment (Render + PostgreSQL + ChromaDB)

KnowledgeGuard AI is production-ready for deployment on **Render**:

* **Frontend**: Render Static Site (React 19 + Vite + Tailwind CSS v4)
* **Backend**: Render Web Service (FastAPI + LangGraph)
* **Relational Database**: Managed PostgreSQL on Render or Neon (automatic schema creation & migration via SQLAlchemy)
* **Vector Database**: ChromaDB attached via Render Persistent Disk volume (`/var/data/chromadb`) or Chroma HttpClient
* **LLM Reasoning**: Centralized Groq API (`openai/gpt-oss-120b`)
* **1-Click Blueprint**: Fully declared in [`render.yaml`](file:///c:/Users/pardhu/Downloads/FAI_PROJECT_2NDYEAR_TERM1/render.yaml)

For the complete step-by-step setup walkthrough, environment variable reference, and troubleshooting tips, see the **[Production Deployment Manual](file:///c:/Users/pardhu/Downloads/FAI_PROJECT_2NDYEAR_TERM1/DEPLOYMENT.md)**.

---


## 10. Demonstration Guide (3–5 Minute Presentation)
1. **Open Dashboard (`http://localhost:5173`)**:
   * Point out the real-time dynamic statistics loaded directly from SQLite.
   * Click **"Load Sample Documents"** (or inspect ingested documents).
2. **Navigate to Knowledge Base**:
   * View the uploaded documents with metadata: Version, Topic, Document Date, and Chunk counts.
   * Click the eye icon to view the raw chunk breakdowns.
3. **Navigate to Investigate**:
   * Click the **Scenario 1** button: *"Is API v2 still recommended?"*
   * Click **"Investigate Claim"**.
   * Observe the live animated LangGraph agent progress stepper:
     1. Claim Understood
     2. Searching Knowledge Base
     3. Evidence Retrieved
     4. Agent Investigating
     5. Comparing Evidence
     6. LLM Reasoning
     7. Generating Result
   * Review the resulting card:
     * Classification: **`OUTDATED`**
     * Confidence: **92.0%**
     * Evidence breakdown: Compares Version 2.0 (recommended) with Version 3.0 (deprecated in Q1 2026).
     * Human verification alert: **`REQUIRED`**.
4. **Test the other 3 Scenarios**:
   * *"Is Python 3.12 supported?"* → **`CURRENT`**
   * *"What authentication protocol is required?"* → **`CONFLICTING`**
   * *"Is quantum encryption mandated for all internal APIs?"* → **`UNCERTAIN`**
5. **Open Investigation History**:
   * Show that all investigations, steps, confidence scores, and evidence links are permanently logged in SQLite and filterable.

---

## 11. AI Syllabus Connections
The architecture and implementation of KnowledgeGuard AI directly demonstrate key modules of the academic Artificial Intelligence curriculum:
* **Module I — LLMs & Intelligent Agents**: Implements a dedicated goal-directed agent with tool access and structured JSON reasoning.
* **Module V — Inference & Reasoning**: Conducts temporal inference and cross-document deduction to detect obsolescence and semantic divergence.
* **Module VI — Knowledge Representation**: Uses dense vector embeddings in ChromaDB, structured relational metadata, and provenance tracking.
* **Module VII — Planning & Agent Workflows**: Uses a LangGraph state graph with conditional branching (evidence sufficiency check, query expansion, and report generation).
* **Module VIII — Uncertainty**: Explicitly handles incomplete or ambiguous evidence by outputting `UNCERTAIN` with calibrated confidence scores rather than guessing.
* **Module X — Real-World AI Applications**: Demonstrates an enterprise AI reliability layer solving knowledge decay in production systems.

---

## 12. Limitations & Future Work

### Current Limitations:
1. **Retrieval Granularity**: Vector similarity search can occasionally pull adjacent sections; fine-tuned semantic chunking can further improve precision.
2. **Source Quality Variance**: Assumes ingested corporate documents have authentic date and version metadata.
3. **Human Verification Mandate**: The AI does not claim absolute ground truth; human-in-the-loop review remains essential for mission-critical deployments.

### Future Work:
* **Continuous Monitoring**: Automatic periodic re-investigation of knowledge as new documents are committed.
* **Live Enterprise Integrations**: Direct connectors for Jira, Confluence, GitHub, and Notion.
* **Knowledge Graphs**: Graph-RAG linking entity relationships alongside vector similarity.
* **Role-Based Access Control (RBAC)**: Fine-grained enterprise permissions and audit logging.
