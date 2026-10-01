# KnowledgeGuard AI — Production Deployment Guide

This guide details how to deploy **KnowledgeGuard AI** to production on **Render** with **PostgreSQL**, **ChromaDB**, and **Groq LLM (`openai/gpt-oss-120b`)**, while maintaining full local development compatibility with SQLite.

---

## 1. System Architecture

```text
                             USER BROWSER
                                  │
                                  ▼
               React + Vite Frontend (Render Static Site)
                       https://<frontend>.onrender.com
                                  │
                                  │ HTTPS API Requests (VITE_API_BASE_URL)
                                  ▼
                FastAPI Backend (Render Web Service)
                       https://<backend>.onrender.com
                                  │
                ┌─────────────────┼──────────────────┐
                ▼                 ▼                  ▼
      ChromaDB (Vector Store)  Groq API         PostgreSQL
      - Persistent Disk Volume - Model:         (Render / Neon)
      - Embeddings:            openai/gpt-oss-  - Investigations,
        all-MiniLM-L6-v2       120b               Documents,
      - Collection:            - LangGraph Agent  Chunks, Audits
        knowledgeguard_        - Single Central
        documents                LLM
```

---

## 2. Environment Configuration Matrix

The application automatically adapts between **Local Development** and **Production**:

| Configuration | Local Development | Production (Render) | Environment Variable |
|---|---|---|---|
| **Database** | SQLite (`knowledgeguard.db`) | Managed PostgreSQL | `DATABASE_URL` |
| **ChromaDB Storage** | Local `./data/chromadb` | Persistent Disk `/var/data/chromadb` | `CHROMA_PERSIST_DIR` |
| **ChromaDB Remote (Optional)** | N/A | Optional Chroma HttpClient | `CHROMA_SERVER_HOST`, `CHROMA_SERVER_PORT` |
| **LLM Provider** | Groq / Gemini / OpenAI | Groq | `LLM_PROVIDER=groq` |
| **LLM Model** | Configured Model | `openai/gpt-oss-120b` | `LLM_MODEL=openai/gpt-oss-120b` |
| **API Secret Key** | Local `.env` | Render Secret Env Var | `GROQ_API_KEY` |
| **CORS Origins** | `localhost:5173` | Production Frontend Domain | `CORS_ORIGINS` |
| **Frontend API Target** | Vite Proxy (`/api` -> `:8000`) | Production Backend URL | `VITE_API_BASE_URL` |

---

## 3. Deployment Option A: Render Blueprint (Recommended 1-Click)

The repository includes a ready-to-use `render.yaml` Blueprint file.

1. Push your repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com), click **New +** > **Blueprint**.
3. Select your `KnowledgeGuardAI` repository.
4. Render will parse `render.yaml` and discover:
   - **PostgreSQL Database** (`knowledgeguard-postgres`)
   - **Backend Web Service** (`knowledgeguard-backend`) with Persistent Disk attached
   - **Frontend Static Site** (`knowledgeguard-frontend`)
5. Enter your `GROQ_API_KEY` under the prompted secret environment variables.
6. Click **Apply**. Render will automatically provision all three services.

---

## 4. Deployment Option B: Manual Step-by-Step Setup on Render

If you prefer provisioning each service individually via the Render web console:

### Step 1: Create PostgreSQL Database
1. Go to [Render Dashboard](https://dashboard.render.com) > **New +** > **PostgreSQL**.
2. **Name**: `knowledgeguard-postgres`
3. **Database**: `knowledgeguard`
4. **User**: `knowledgeguard_user`
5. **Region**: Oregon (or matching your preferred region).
6. **Plan**: Free.
7. Click **Create Database**.
8. Copy the **Internal Database URL** (e.g., `postgres://knowledgeguard_user:...@dpg-...-a/knowledgeguard`).

> [!CAUTION]
> **DO NOT USE `npm run start` ON RENDER.**
> Render will fail with `/opt/render/project/src/package.json does not exist` if you accidentally create a **Node Web Service** at the root of the repository.
> KnowledgeGuard AI uses **TWO separate services**:
> 1. A **Python Web Service** for the FastAPI backend.
> 2. A **Static Site** (not a Web Service!) with **Root Directory: `frontend`** for the React frontend.

### Step 2: Create Backend Web Service
1. In Render Dashboard, click **New +** > **Web Service**.
2. Connect your GitHub repository.
3. Configure the service:
   - **Name**: `knowledgeguard-backend`
   - **Environment / Runtime**: Select **Python 3** (NOT Node!).
   - **Region**: Same as PostgreSQL (e.g., Oregon).
   - **Branch**: `main`
   - **Root Directory**: *(Leave empty — runs from repository root)*
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn backend.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Health Check Path**: `/health`

4. Add **Environment Variables**:
   | Key | Value | Description |
   |---|---|---|
   | `PYTHON_VERSION` | `3.11.9` | Recommended Python runtime |
   | `ENV` | `production` | Environment mode |
   | `LLM_PROVIDER` | `groq` | Centralized LLM provider |
   | `GROQ_API_KEY` | `gsk_...` | Your Groq API key |
   | `LLM_MODEL` | `openai/gpt-oss-120b` | Production LLM model |
   | `DATABASE_URL` | Paste your PostgreSQL connection URL | Automatically normalized by `db.py` |
   | `CHROMA_PERSIST_DIR` | `/var/data/chromadb` | Location of Chroma persistent index |
   | `CORS_ORIGINS` | `https://knowledgeguard-frontend.onrender.com,http://localhost:5173` | Allowed origins |
5. **Attach Persistent Disk (ChromaDB Persistence)**:
   - Scroll down to the **Disks** section.
   - Click **Add Disk**.
   - **Name**: `chroma-data`
   - **Mount Path**: `/var/data/chromadb`
   - **Size**: `1 GB` (or desired volume size).
6. Click **Create Web Service**. Wait for the build and deployment to succeed.
7. Copy your backend URL: `https://knowledgeguard-backend.onrender.com`.

### Step 3: Create Frontend Static Site
1. In Render Dashboard, click **New +** > **Static Site** *(Do NOT select "Web Service")*.
2. Connect the same GitHub repository.
3. Configure the static site:
   - **Name**: `knowledgeguard-frontend`
   - **Branch**: `main`
   - **Root Directory**: `frontend` *(CRITICAL: Must be set to `frontend` so Render locates `frontend/package.json`)*
   - **Build Command**:
     ```bash
     npm install && npm run build
     ```
   - **Publish Directory**: `dist`

4. Add **Environment Variables**:
   | Key | Value | Description |
   |---|---|---|
   | `VITE_API_BASE_URL` | `https://knowledgeguard-backend.onrender.com/api` | Points frontend directly to backend |
5. Verify SPA Routing:
   - The file `frontend/public/_redirects` contains:
     ```text
     /*    /index.html   200
     ```
   - This ensures React Router navigates properly without 404 errors on browser page reloads.
6. Click **Create Static Site**.

---

## 5. Post-Deployment Verification

### 1. Test System Health Check
Visit or `curl` the backend health check endpoint:
```bash
curl https://knowledgeguard-backend.onrender.com/health
```
Expected response:
```json
{
  "status": "healthy",
  "service": "KnowledgeGuard AI",
  "env": "production",
  "database": "PostgreSQL (connected)",
  "vector_store": "ChromaDB (connected)",
  "llm_provider": "groq",
  "llm_status": "configured"
}
```

### 2. Verify Relational Database & Vector Store
1. Open the deployed frontend: `https://knowledgeguard-frontend.onrender.com`.
2. Navigate to **Knowledge Base**.
3. Click **Seed Evaluation Corpus** or upload a document (`.txt` / `.pdf`).
4. Confirm the document appears in the table with chunk count and provenance metadata.

### 3. Verify LangGraph Investigation Agent
1. Navigate to **Investigation Sandbox**.
2. Enter a claim:
   > "API v2 is recommended for production services."
3. Click **Run Agent Investigation**.
4. Observe the 10-node investigation workflow, evidence retrieval, verdict (`OUTDATED`), and deductive reasoning explanation.

### 4. Verify Evaluation Benchmark
1. Navigate to **Evaluation Benchmark**.
2. Click **Run Benchmark**.
3. Verify all 24 evaluation claims run through the LangGraph pipeline, recording per-class accuracy, confusion matrix, and average latency.

---

## 6. Troubleshooting & Operational Tips

### Cold Starts (Render Free Tier)
Render's free tier spins down web services after 15 minutes of inactivity. When a user first opens the frontend, the backend may take 30–50 seconds to boot up. The frontend includes Axios interceptor error handling to inform the user gracefully during cold starts.

### PostgreSQL URI Scheme
Render provides PostgreSQL connection strings starting with `postgres://...`. SQLAlchemy 2.0 requires `postgresql://...`. KnowledgeGuard AI handles this automatically in `backend/database/db.py`:
```python
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
```

### CORS Issues
If you encounter `Access to XMLHttpRequest has been blocked by CORS policy`:
- Verify that your exact frontend domain is included in the backend's `CORS_ORIGINS` environment variable without trailing slashes.
- Multiple origins can be comma-separated: `http://localhost:5173,https://my-app.onrender.com`.
