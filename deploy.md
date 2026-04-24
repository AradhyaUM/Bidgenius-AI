# BidGenius AI — Deployment Guide

> **Last updated:** April 2026  
> **Maintainer:** DevOps / Platform team

---

## 1. Project Overview

| Layer | Technology | Details |
|-------|-----------|---------|
| **Backend API** | Python 3.12 · FastAPI | Agentic pipeline — search, extract, analyse, and draft bid proposals for Indian government tenders |
| **Frontend UI** | Python · Streamlit | Rich single-page dashboard with glassmorphism UI; communicates with backend via REST |
| **LLM Inference** | Groq (primary) → Ollama (local fallback) | Uses `llama-3.3-70b-versatile` via Groq cloud; round-robin across 18 API keys |
| **Search** | Tavily + Exa | Dual-source tender discovery from government procurement portals |
| **PDF Processing** | PyMuPDF (primary) → pdfminer.six → Tesseract OCR (fallback) | Multi-strategy text extraction |
| **Judge Agent** | Google Gemini (`gemini-2.0-flash`) | LLM-as-judge evaluation of generated bid proposals |
| **Backend Hosting** | Vercel Serverless Functions | `vercel.json` already configured for `python3.12` runtime |
| **Frontend Hosting** | Streamlit Community Cloud (recommended) | Or any VM / container that can run `streamlit run` |
| **DevContainer** | GitHub Codespaces ready | `.devcontainer/devcontainer.json` present with Python 3.11 image |

### Architecture

```
┌──────────────────┐         HTTPS          ┌────────────────────────┐
│  Streamlit UI    │ ──────────────────────► │  FastAPI on Vercel     │
│  (frontend/)     │   POST /api/run         │  (backend/)            │
│                  │   POST /api/list         │                        │
│  app.py          │   GET  /api/health      │  api/index.py          │
│                  │◄────────────────────────│  → app.main:app        │
└──────────────────┘        JSON             └────────┬───────────────┘
                                                      │
                                          ┌───────────┴───────────────┐
                                          │  Agent Pipeline           │
                                          │  search → reader →        │
                                          │  extractor → validator →  │
                                          │  analysis → bid → judge   │
                                          └───────────────────────────┘
```

---

## 2. Prerequisites

### Accounts Required

| Service | Purpose | Sign-up URL |
|---------|---------|-------------|
| **Vercel** | Backend API hosting | https://vercel.com/signup |
| **Streamlit Community Cloud** | Frontend hosting (free) | https://share.streamlit.io |
| **Groq** | LLM inference (free tier available) | https://console.groq.com |
| **Tavily** | Web search API | https://app.tavily.com |
| **Exa** | Semantic search API | https://dashboard.exa.ai |
| **Google AI Studio** | Gemini API for judge agent | https://aistudio.google.com/apikey |
| **GitHub** | Source control & Streamlit Cloud integration | https://github.com |

### Local Tools

| Tool | Minimum Version | Install |
|------|----------------|---------|
| **Python** | 3.11+ (3.12 recommended) | https://www.python.org/downloads/ |
| **pip** | 23.0+ | Bundled with Python |
| **Git** | 2.30+ | https://git-scm.com |
| **Node.js** (for Vercel CLI only) | 18+ | https://nodejs.org |
| **Vercel CLI** | Latest | `npm i -g vercel` |

### Optional (for OCR on scanned PDFs)

| Tool | Purpose | Install |
|------|---------|---------|
| **Poppler** | PDF → image conversion | Windows: [poppler releases](https://github.com/oshliaer/google-poppler-windows/releases); Linux: `apt install poppler-utils` |
| **Tesseract** | OCR engine | Windows: [UB Mannheim installer](https://github.com/UB-Mannheim/tesseract/wiki); Linux: `apt install tesseract-ocr` |

> **Note:** OCR is a last-resort fallback. The primary PyMuPDF extraction works for most government tender PDFs without Poppler/Tesseract.

---

## 3. Environment Variables

Create a `.env` file in the `backend/` directory. **Never commit this file** (it is already in `.gitignore`).

```env
# ─── REQUIRED ───────────────────────────────────────────────────────

# Tavily — web search for tender discovery (primary search engine)
TAVILY_API_KEY=tvly-dev-xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Groq — LLM inference via round-robin key rotation
# You need AT LEAST 1 key. The system supports up to 18 keys for
# rate-limit resilience. More keys = fewer 429 errors on heavy workloads.
GROQ_API_KEY_1=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_API_KEY_2=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# ... add GROQ_API_KEY_3 through GROQ_API_KEY_18 as needed

# ─── RECOMMENDED ────────────────────────────────────────────────────

# Exa — semantic search (supplements Tavily; improves recall)
EXA_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Google Gemini — used by judge_agent to evaluate generated proposals
# Referenced as GEMINI_API_KEY in app/llm/gemini_llm.py
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ─── OPTIONAL ───────────────────────────────────────────────────────

# Google API key (listed in .env as GOOGLE_API_KEY — ensure you set
# GEMINI_API_KEY as well if you want judge evaluation to work)
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Application secret key
SECRET_KEY=your-random-secret-string

# Poppler path override (for OCR on Windows only)
# Leave unset on Linux/Vercel — it auto-detects via PATH
POPPLER_PATH=C:\path\to\poppler\bin
```

### Variable Reference

| Variable | Used By | Required? | Description |
|----------|---------|-----------|-------------|
| `TAVILY_API_KEY` | `search_agent.py`, `tavily_tool.py`, `scraper.py` | **Yes** | Powers tender search queries across government portals |
| `GROQ_API_KEY_1` … `_18` | `groq_llm.py` | **Yes** (min 1) | Round-robin LLM inference keys; system crashes if zero keys found |
| `EXA_API_KEY` | `search_agent.py`, `exa_tool.py` | Recommended | Exa semantic search; gracefully skipped if missing |
| `GEMINI_API_KEY` | `gemini_llm.py` | Recommended | Gemini judge evaluation; skipped with warning if missing |
| `GOOGLE_API_KEY` | `.env` (legacy) | Optional | May be identical to `GEMINI_API_KEY` |
| `SECRET_KEY` | `.env` | Optional | App-level secret; not currently enforced |
| `POPPLER_PATH` | `pdf_parser.py` | Optional | Override for Poppler binary location on Windows |

### Setting Environment Variables on Vercel

```bash
# Set each variable individually via CLI
vercel env add TAVILY_API_KEY production
vercel env add GROQ_API_KEY_1 production
vercel env add GROQ_API_KEY_2 production
# ... repeat for all keys

# Or use the Vercel dashboard:
# Project → Settings → Environment Variables
```

### Setting Environment Variables on Streamlit Cloud

In the Streamlit Cloud app dashboard:
1. Go to **App settings** → **Secrets**
2. Add variables in TOML format:

```toml
# No secrets needed in the frontend — it only talks to the backend API.
# But if you need to override the backend URL:
# API_BASE_URL = "https://your-vercel-project.vercel.app/api"
```

> **Important:** The frontend `app.py` has the backend URL hardcoded on line 6:
> ```python
> API_BASE_URL = "https://bidgenius-ai.vercel.app/api"
> ```
> Update this to your actual Vercel deployment URL before deploying the frontend.

---

## 4. Build Steps

### 4.1 Clone the Repository

```bash
git clone https://github.com/<your-org>/tender-ai-platform.git
cd tender-ai-platform
```

### 4.2 Backend — Local Build & Test

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Linux / macOS)
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install uvicorn (not in requirements.txt but needed to run locally)
pip install uvicorn

# Copy and fill environment variables
# (create .env from the template in Section 3 above)

# Run the backend locally
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Verify local backend:**

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "errors": [],
  "tavily": true,
  "groq": true,
  "exa": true
}
```

### 4.3 Frontend — Local Build & Test

```bash
cd frontend

# Install Streamlit (uses Python, not Node.js despite the empty package-lock.json)
pip install streamlit requests

# For local testing, temporarily change API_BASE_URL in app.py:
# API_BASE_URL = "http://localhost:8000/api"

# Run the frontend
streamlit run app.py --server.port 8501
```

Open `http://localhost:8501` in your browser.

---

## 5. Deployment Steps

### 5.1 Deploy Backend to Vercel

The backend is pre-configured for Vercel with:
- `backend/vercel.json` — maps `api/index.py` to Python 3.12 runtime
- `backend/api/index.py` — re-exports the FastAPI `app` object
- `backend/main.py` — secondary entrypoint that also re-exports `app`

#### Step-by-step

```bash
# 1. Install Vercel CLI globally
npm install -g vercel

# 2. Navigate to backend directory
cd backend

# 3. Login to Vercel
vercel login

# 4. Deploy (first time — will create a new project)
vercel --prod

# During setup:
#   - Set up and deploy? → Y
#   - Which scope? → select your team/personal
#   - Link to existing project? → N (first time)
#   - Project name? → bidgenius-ai (or your preferred name)
#   - Directory? → ./
#   - Override settings? → N

# 5. Set environment variables
vercel env add TAVILY_API_KEY production
# Enter the value when prompted

vercel env add GROQ_API_KEY_1 production
vercel env add GROQ_API_KEY_2 production
# ... repeat for all required env vars (see Section 3)

vercel env add EXA_API_KEY production
vercel env add GEMINI_API_KEY production
vercel env add SECRET_KEY production

# 6. Redeploy to pick up the new env vars
vercel --prod
```

#### Verify Vercel Deployment

```bash
curl https://<your-project>.vercel.app/api/health
```

Expected:
```json
{
  "status": "ok",
  "errors": [],
  "tavily": true,
  "groq": true,
  "exa": true
}
```

### 5.2 Deploy Frontend to Streamlit Community Cloud

#### Pre-deployment Checklist

1. **Update `API_BASE_URL`** in `frontend/app.py` line 6:
   ```python
   API_BASE_URL = "https://<your-project>.vercel.app/api"
   ```

2. **Create `frontend/requirements.txt`** (does not exist yet):
   ```bash
   # Create this file in the frontend/ directory
   ```
   ```txt
   streamlit
   requests
   ```

3. **Push everything to GitHub.**

#### Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click **"New app"**
3. Select your GitHub repository: `<your-org>/tender-ai-platform`
4. Set **Main file path**: `frontend/app.py`
5. Set **Python version**: 3.11 or 3.12
6. Click **"Deploy"**

The app will be live at `https://<your-app>.streamlit.app`.

### 5.3 Alternative — Deploy Frontend on a VM / VPS

```bash
# On the server
cd tender-ai-platform/frontend

pip install streamlit requests

# Run with nohup or systemd
nohup streamlit run app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.enableCORS false \
  --server.enableXsrfProtection false \
  > streamlit.log 2>&1 &
```

#### Systemd Service (Linux)

Create `/etc/systemd/system/bidgenius-frontend.service`:

```ini
[Unit]
Description=BidGenius AI Streamlit Frontend
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/opt/tender-ai-platform/frontend
ExecStart=/opt/tender-ai-platform/venv/bin/streamlit run app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.enableCORS false \
  --server.enableXsrfProtection false
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable bidgenius-frontend
sudo systemctl start bidgenius-frontend
```

### 5.4 Alternative — Deploy with GitHub Codespaces

The project includes a `.devcontainer/devcontainer.json` that automatically:
- Uses `mcr.microsoft.com/devcontainers/python:1-3.11-bookworm`
- Installs `requirements.txt` dependencies + `streamlit`
- Launches `streamlit run frontend/app.py` on port 8501

To use:
1. Open the repo on GitHub
2. Click **Code → Codespaces → New codespace**
3. The frontend starts automatically and a preview opens on port 8501
4. Start the backend manually: `cd backend && uvicorn main:app --port 8000`

---

## 6. Post-Deployment Checks

Run these checks **immediately after every deployment**.

### 6.1 Backend Health Check

```bash
# Health endpoint — verifies all agent modules can import
curl -s https://<your-project>.vercel.app/api/health | python -m json.tool
```

✅ **Expected:** `"status": "ok"`, all API key booleans `true`, empty `errors` array.

⚠️ **Degraded:** If `errors` is non-empty, specific agents failed to import — check the logs.

### 6.2 Root Endpoint

```bash
curl -s https://<your-project>.vercel.app/api
```

✅ **Expected:** `{"service": "BidGenius API", "status": "ok"}`

### 6.3 Quick List Mode Smoke Test

```bash
curl -s -X POST https://<your-project>.vercel.app/api/list \
  -H "Content-Type: application/json" \
  -d '{"keyword": "road construction", "region": "India"}' | python -m json.tool
```

✅ **Expected:** JSON array of tender results (may take 10–30 seconds).

### 6.4 Frontend Accessibility

Open `https://<your-app>.streamlit.app` in a browser and verify:
- [ ] Page loads with the dark glassmorphism theme
- [ ] Sidebar renders with company profile fields
- [ ] "Launch Search" button is visible in the search workspace
- [ ] A quick-list search for "road construction" returns results

### 6.5 Full Pipeline End-to-End Test

1. Open the frontend
2. Fill in company name (e.g., "Test Corp") in the sidebar
3. Set mode to **Full analysis**
4. Enter keyword "road construction", region "Maharashtra"
5. Click **Launch Search**
6. Wait 3–5 minutes
7. Verify: tender cards appear with scores, detail tabs, and bid proposals

---

## 7. Rollback Instructions

### 7.1 Vercel Backend Rollback

Vercel maintains immutable deployments. Every push creates a new deployment.

```bash
# List recent deployments
vercel ls

# Promote a previous deployment to production
vercel promote <deployment-url> --prod

# Example:
vercel promote bidgenius-ai-abc123.vercel.app --prod
```

**Via Vercel Dashboard:**
1. Go to **Project → Deployments**
2. Find the last known-good deployment
3. Click the **⋯** menu → **Promote to Production**

### 7.2 Streamlit Cloud Frontend Rollback

Streamlit Cloud auto-deploys from a GitHub branch. To rollback:

```bash
# Revert the last commit
git revert HEAD
git push origin main

# Or reset to a known-good commit
git log --oneline -10
git reset --hard <good-commit-sha>
git push origin main --force
```

### 7.3 Git-Level Rollback (Both Services)

```bash
# Find the last good state
git log --oneline -20

# Create a rollback branch
git checkout -b rollback/<ticket-id> <good-commit-sha>
git push origin rollback/<ticket-id>

# Redeploy backend
cd backend && vercel --prod

# Frontend will auto-deploy if Streamlit Cloud is on the same branch
```

---

## 8. Common Errors & Fixes

### 8.1 `ValueError: No GROQ_API_KEY_* found in environment`

**When:** Backend startup / first request  
**Cause:** No `GROQ_API_KEY_*` environment variables are set.  
**Fix:**
```bash
# Vercel
vercel env add GROQ_API_KEY_1 production
vercel --prod

# Local
echo "GROQ_API_KEY_1=gsk_xxxx" >> backend/.env
```

---

### 8.2 `Cannot connect to the backend on port 8000`

**When:** Frontend shows this error after clicking "Launch Search"  
**Cause:** `API_BASE_URL` in `frontend/app.py` points to the wrong backend URL.  
**Fix:** Update line 6 of `frontend/app.py`:
```python
API_BASE_URL = "https://<your-actual-vercel-project>.vercel.app/api"
```

---

### 8.3 Vercel 504 Gateway Timeout

**When:** Full analysis mode times out on Vercel  
**Cause:** Vercel Hobby plan has a **10-second** function timeout. The full pipeline takes 3–5 minutes.  
**Fix:**
- Upgrade to **Vercel Pro** ($20/month) for a 300-second timeout, **or**
- Use the **Quick list** mode (usually completes within 10 seconds), **or**
- Self-host the backend on a VPS / Railway / Render instead of Vercel:
  ```bash
  # On a VPS with no timeout constraints
  pip install uvicorn
  uvicorn main:app --host 0.0.0.0 --port 8000
  ```

> **Critical:** This is the most likely production issue. The full pipeline is compute-heavy (multiple LLM calls, PDF downloads, OCR). Vercel's free/hobby tier is insufficient for `/api/run`. Consider Railway, Render, or a $5/month VPS for production.

---

### 8.4 `RateLimitError` on All Groq Keys

**When:** Logs show `Rate limit on key slot N — rotating` for every key  
**Cause:** All 18 Groq keys have hit their rate limits simultaneously.  
**Fix:**
- Wait 60 seconds (Groq rate limits reset quickly)
- Add more Groq API keys (create additional accounts)
- The system has a 2-second sleep between calls — reduce concurrent requests
- If persistent, consider Ollama as a local fallback (requires GPU server)

---

### 8.5 `Ollama also failed` / `Ollama Failed`

**When:** All Groq keys exhausted and Ollama fallback also fails  
**Cause:** Ollama is not installed on the deployment server (expected on Vercel).  
**Fix:** This is informational on cloud deployments. Ollama is a local-only fallback. To enable:
```bash
# Install Ollama on a GPU server
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3
```

---

### 8.6 `⛔ OCR skipped — Poppler not available`

**When:** A scanned PDF cannot be read  
**Cause:** Poppler binaries are not installed.  
**Fix:**
```bash
# Linux (including Vercel/Railway)
apt install poppler-utils tesseract-ocr

# Windows
# Download from: https://github.com/oshliaer/google-poppler-windows/releases
# Set POPPLER_PATH in .env
```

> **Note:** Most government tender PDFs are text-based. OCR is only needed for scanned documents. This error can usually be safely ignored.

---

### 8.7 `Judge evaluation failed` / `get_llm_client` Import Error

**When:** The judge agent fails to score proposals  
**Cause:** `judge_agent.py` imports `get_llm_client` from `llm_router.py`, but that function is not defined in the current `llm_router.py` (it only exports `generate`).  
**Fix:** The judge agent will fail silently — proposals are still generated, just not scored. To fix the judge:
- Implement `get_llm_client()` in `app/llm/llm_router.py`, or
- Set `GEMINI_API_KEY` and update the judge to call `gemini_llm.py` directly

---

### 8.8 SSL Errors When Downloading Government PDFs

**When:** Logs show `SSL error — retrying without verification`  
**Cause:** Many Indian government portals have expired or misconfigured SSL certificates.  
**Fix:** The code already handles this automatically by retrying with `verify=False`. No action needed. If downloads still fail, the tender is skipped gracefully.

---

### 8.9 Streamlit Cloud — `ModuleNotFoundError: No module named 'requests'`

**When:** Frontend crashes on Streamlit Cloud  
**Cause:** Missing `requirements.txt` in the `frontend/` directory.  
**Fix:** Create `frontend/requirements.txt`:
```txt
streamlit
requests
```

---

### 8.10 Empty Search Results

**When:** "No results found" for every query  
**Cause:** Usually `TAVILY_API_KEY` is invalid/expired, or `EXA_API_KEY` is missing.  
**Fix:**
1. Check `/api/health` — verify `tavily: true` and `exa: true`
2. Regenerate API keys at https://app.tavily.com and https://dashboard.exa.ai
3. Redeploy after updating keys

---

## Appendix: File Structure Reference

```
tender-ai-platform/
├── .devcontainer/
│   └── devcontainer.json        # GitHub Codespaces config
├── .gitignore
├── deploy.md                    # ← This file
│
├── backend/
│   ├── .env                     # Environment variables (NOT committed)
│   ├── main.py                  # Entrypoint: re-exports app from app.main
│   ├── requirements.txt         # Python dependencies
│   ├── vercel.json              # Vercel serverless config
│   ├── api/
│   │   └── index.py             # Vercel function entrypoint
│   ├── app/
│   │   ├── main.py              # FastAPI app definition + routes
│   │   ├── agents/
│   │   │   ├── search_agent.py  # Dual-source tender search (Exa + Tavily)
│   │   │   ├── reader_agent.py  # PDF download + text extraction orchestrator
│   │   │   ├── extractor_agent.py # Regex + LLM field extraction
│   │   │   ├── validator_agent.py # Document type & data validation
│   │   │   ├── analysis_agent.py  # Scoring & summary generation
│   │   │   ├── bid_agent.py     # Bid proposal generation (LLM + fallback)
│   │   │   └── judge_agent.py   # LLM-as-judge proposal evaluation
│   │   ├── llm/
│   │   │   ├── llm_router.py    # Groq (primary) → Ollama (fallback)
│   │   │   ├── groq_llm.py      # Groq client with 18-key rotation
│   │   │   ├── gemini_llm.py    # Google Gemini client
│   │   │   └── ollama_llm.py    # Local Ollama fallback
│   │   ├── tools/
│   │   │   ├── tavily_tool.py   # Tavily search wrapper
│   │   │   ├── exa_tool.py      # Exa search wrapper
│   │   │   └── pdf_parser.py    # PyMuPDF → pdfminer → OCR pipeline
│   │   ├── services/
│   │   │   ├── pipeline.py      # Main orchestration pipeline
│   │   │   └── scraper.py       # Legacy search (unused, kept for reference)
│   │   ├── models/
│   │   │   └── tender.py
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── pipeline.py
│   │   │   └── tender.py
│   │   └── schemas/             # (empty)
│   └── downloads/               # Temporary PDF storage (auto-cleaned)
│
└── frontend/
    ├── app.py                   # Streamlit UI (1082 lines)
    └── package-lock.json        # Empty — not a Node.js project
```
