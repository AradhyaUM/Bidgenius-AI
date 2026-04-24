<div align="center">

# 🏛️ BidGenius AI

### Agentic Tender Intelligence Platform

**Automate government tender discovery, analysis, and bid proposal generation using a multi-agent AI pipeline.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-F55036)](https://groq.com)
[![Deployed on Vercel](https://img.shields.io/badge/Backend-Vercel-black?logo=vercel)](https://vercel.com)

[Live Demo](#live-demo) · [Architecture](#architecture) · [Quick Start](#quick-start) · [Deployment](#deployment)

</div>

---

## 📌 What is BidGenius AI?

BidGenius AI is an **agentic AI system** that transforms the way businesses discover and respond to Indian government tenders. Instead of manually searching across dozens of procurement portals, downloading PDFs, and reading through hundreds of pages — BidGenius automates the entire workflow in under 5 minutes.

### The Problem

- **60+ government procurement portals** across India (central, state, municipal, PSU)
- Tender documents are buried in **poorly searchable PDFs** — often scanned images
- Businesses spend **days** finding relevant tenders and weeks drafting proposals
- Missing a deadline by one day means losing the opportunity entirely

### The Solution

BidGenius AI uses a **7-agent pipeline** that:

1. 🔍 **Searches** across 60+ government portals using Tavily + Exa APIs
2. 📄 **Downloads & parses** tender PDFs using PyMuPDF with OCR fallback
3. 🧠 **Extracts** structured fields (EMD, fees, dates, scope) using regex + one LLM call
4. ✅ **Validates** document authenticity and data quality
5. 📊 **Scores** each tender on a 100-point bid-fit scale
6. ✍️ **Generates** personalized 5-section bid proposals using company profile
7. ⚖️ **Judges** proposal quality using LLM-as-judge evaluation

---

## 🎯 Live Demo

| Service | URL |
|---------|-----|
| **Frontend** | [bidgenius-ai.streamlit.app](https://bidgenius-ai.streamlit.app) |
| **Backend API** | [bidgen-api.vercel.app/api](https://bidgen-api.vercel.app/api) |
| **Health Check** | [bidgen-api.vercel.app/api/health](https://bidgen-api.vercel.app/api/health) |

---

## 🏗️ Architecture

```
┌──────────────────────┐       HTTPS        ┌──────────────────────────┐
│   Streamlit Frontend │ ─────────────────► │   FastAPI Backend        │
│   (Streamlit Cloud)  │  POST /api/run     │   (Vercel Serverless)    │
│                      │  POST /api/list    │                          │
│   • Company profile  │  GET  /api/health  │   api/index.py           │
│   • Search config    │◄─────────────────  │   → app.main:app         │
│   • Results display  │      JSON          │                          │
└──────────────────────┘                    └────────┬─────────────────┘
                                                     │
                                         ┌───────────┴──────────────┐
                                         │   7-Agent Pipeline       │
                                         │                          │
                                         │   1. Search Agent        │
                                         │   2. Reader Agent        │
                                         │   3. Extractor Agent     │
                                         │   4. Validator Agent     │
                                         │   5. Analysis Agent      │
                                         │   6. Bid Agent           │
                                         │   7. Judge Agent         │
                                         └──────────────────────────┘
```

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend API | Python 3.12 · FastAPI |
| Frontend UI | Python · Streamlit |
| LLM Inference | Groq API · Llama 3.3 70B Versatile |
| Judge Evaluation | Google Gemini 2.0 Flash |
| Web Search | Tavily API + Exa API |
| PDF Extraction | PyMuPDF → pdfminer.six → Tesseract OCR |
| Backend Hosting | Vercel (Serverless Functions) |
| Frontend Hosting | Streamlit Community Cloud |

---

## 🤖 Agent Pipeline — Deep Dive

### Agent 1: Search Agent (`search_agent.py`)

Performs intelligent tender discovery across Indian government procurement infrastructure.

- **Dual-source search:** Tavily (web search) + Exa (semantic search) for maximum recall
- **60+ portals indexed:**
  - **Central:** eProcure, GeM, DefProc, MSTC
  - **State:** Maharashtra, Rajasthan, Karnataka, Tamil Nadu, Gujarat, Kerala, UP, MP, and more
  - **Municipal:** MCGM, PMC, BBMP, GHMC, NDMC, KMC, and 10+ city corporations
  - **PSU:** NHAI, IREPS, NTPC, PowerGrid, ONGC, BHEL, Coal India, SAIL
- **Region-aware:** Detects state names and prioritizes relevant state portals
- **Time-filtered:** Auto-generates date windows (current month ±2 months) to find active tenders

### Agent 2: Reader Agent (`reader_agent.py`)

Downloads and extracts text from tender documents.

- **PDF download** with SSL error handling (many government sites have expired certificates)
- **Three-tier text extraction:**
  1. PyMuPDF — fast, clean text extraction for digital PDFs
  2. pdfminer.six — better column/layout handling as fallback
  3. Tesseract OCR — for scanned documents (requires Poppler)
- **Garbage detection:** Identifies and rejects garbled output from encrypted or image-only PDFs
- **Configurable timeouts:** 15s download, 90s processing

### Agent 3: Extractor Agent (`extractor_agent.py`)

Extracts structured fields from unstructured tender text using a **hybrid approach**.

- **Regex-first strategy:** 20+ patterns for EMD, tender fees, dates, organization names
  - Handles Indian number formats (₹, lakhs, crores, Indic numerals)
  - Parses 11 date formats including `dd-mm-yyyy`, `dd/MMM/yyyy`, etc.
- **One LLM call:** Fills missing fields AND classifies relevance in a single prompt
- **Fields extracted:**
  - Tender ID, Title, Organization, Ministry/Department
  - EMD (Earnest Money Deposit), Tender Fee
  - Estimated Contract Value
  - Bid Start Date, Bid End Date
  - Location, Scope of Work
  - Primary category classification
  - Relevance flag with reasoning

### Agent 4: Validator Agent (`validator_agent.py`)

Ensures extracted data quality and rejects non-tender documents.

- **Document type filtering:** Rejects court orders, financial reports, meeting minutes
- **Data sanitization:** Fixes swapped dates, impossible EMD amounts, invalid formats
- **Permissive design:** Prefers to keep suspicious documents rather than risk false negatives

### Agent 5: Analysis Agent (`analysis_agent.py`)

Generates a bid-fit score and executive summary.

- **100-point scoring rubric:**
  - Data Completeness (30 pts) — How many fields were successfully extracted
  - Active Status (30 pts) — Is the tender still open for bidding
  - Content Quality (40 pts) — Text length, scope clarity, EMD presence
- **Difficulty rating:** Easy / Medium / Hard based on EMD thresholds
- **Executive summary:** LLM-generated 3-sentence overview

### Agent 6: Bid Agent (`bid_agent.py`)

Generates personalized bid proposals using the company profile.

- **5-section proposal:**
  1. Executive Summary
  2. Technical Approach & Methodology
  3. Team Qualifications & Past Experience
  4. Project Timeline & Milestones
  5. Compliance & Certifications
- **Company personalization:** Uses name, type, turnover, experience, certifications, and past projects
- **Resilient design:** LLM retry with 3s backoff + structured template fallback

### Agent 7: Judge Agent (`judge_agent.py`)

LLM-as-judge evaluation of generated proposals using Google Gemini.

- **5-criterion rubric (1–5 each):**
  1. Tender Alignment
  2. Compliance & Feasibility
  3. Professional Tone
  4. Strategy Quality
  5. Report Completeness
- **Independent scoring:** Recomputes overall score server-side (never trusts LLM math)
- **Normalized output:** Raw (0–5) + percentage (0–100) scores

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (3.12 recommended)
- API keys: [Groq](https://console.groq.com), [Tavily](https://app.tavily.com), [Exa](https://dashboard.exa.ai)
- Optional: [Google AI Studio](https://aistudio.google.com/apikey) (for judge agent)

### 1. Clone

```bash
git clone https://github.com/AradhyaUM/Bidgenius-AI.git
cd Bidgenius-AI
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install uvicorn
```

### 3. Configure Environment

Create `backend/.env`:

```env
# Required
GROQ_API_KEY=gsk_your_groq_api_key_here
TAVILY_API_KEY=tvly-your_tavily_key_here

# Recommended
EXA_API_KEY=your_exa_key_here
GEMINI_API_KEY=your_gemini_key_here

# Optional (Windows OCR only)
POPPLER_PATH=C:\path\to\poppler\bin
```

### 4. Run Backend

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Verify: `http://localhost:8000/health`

### 5. Run Frontend

```bash
cd ../frontend

# Temporarily point to local backend
# Edit app.py line 6: API_BASE_URL = "http://localhost:8000/api"

pip install streamlit requests
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## 🌐 Deployment

### Backend → Vercel

```bash
cd backend

# Install Vercel CLI
npm install -g vercel

# Login and deploy
vercel login
vercel --prod
```

Set environment variables:

```bash
vercel env add GROQ_API_KEY production
vercel env add TAVILY_API_KEY production
vercel env add EXA_API_KEY production
vercel env add GEMINI_API_KEY production

# Redeploy to pick up env vars
vercel --prod
```

### Frontend → Streamlit Cloud

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Create new app → select `frontend/app.py`
4. Deploy

> **Important:** Update `API_BASE_URL` in `frontend/app.py` to your Vercel URL before deploying.

### Vercel Timeout Warning

Vercel's free tier has a **10-second** function timeout. The **Quick List** mode works within this limit, but **Full Analysis** (which downloads PDFs and makes multiple LLM calls) takes 3–5 minutes. For full analysis, either:
- Upgrade to Vercel Pro (300s timeout), or
- Self-host the backend on Railway / Render / a VPS

---

## 📁 Project Structure

```
Bidgenius-AI/
├── backend/
│   ├── api/index.py              # Vercel serverless entrypoint
│   ├── main.py                   # Re-exports FastAPI app
│   ├── requirements.txt          # Python dependencies
│   ├── vercel.json               # Vercel build config
│   ├── .vercelignore             # Excludes venv from deployment
│   ├── app/
│   │   ├── main.py               # FastAPI app + routes (/run, /list, /health)
│   │   ├── agents/
│   │   │   ├── search_agent.py   # Tavily + Exa multi-portal search
│   │   │   ├── reader_agent.py   # PDF download + text extraction
│   │   │   ├── extractor_agent.py# Regex + LLM field extraction
│   │   │   ├── validator_agent.py# Data quality + document filtering
│   │   │   ├── analysis_agent.py # 100-point scoring + summary
│   │   │   ├── bid_agent.py      # Personalized proposal generation
│   │   │   └── judge_agent.py    # LLM-as-judge evaluation
│   │   ├── llm/
│   │   │   ├── llm_router.py     # Groq → Ollama fallback
│   │   │   ├── groq_llm.py       # Groq API client
│   │   │   ├── gemini_llm.py     # Google Gemini client (lazy)
│   │   │   └── ollama_llm.py     # Local Ollama fallback
│   │   ├── tools/
│   │   │   ├── tavily_tool.py    # Tavily search wrapper
│   │   │   ├── exa_tool.py       # Exa search wrapper
│   │   │   └── pdf_parser.py     # PyMuPDF → pdfminer → OCR
│   │   └── services/
│   │       └── pipeline.py       # Orchestrates the 7-agent pipeline
│
├── frontend/
│   ├── app.py                    # Streamlit UI (1082 lines)
│   └── requirements.txt          # streamlit, requests
│
├── .devcontainer/
│   └── devcontainer.json         # GitHub Codespaces config
├── .gitignore
├── deploy.md                     # Detailed deployment guide
└── README.md                     # ← This file
```

---

## 🔌 API Reference

### `GET /api/health`

Health check — returns API key status for all services.

```json
{
  "status": "ok",
  "errors": [],
  "tavily": true,
  "groq": true,
  "exa": true
}
```

### `POST /api/list`

Quick list mode — returns tender search results without full analysis.

```json
// Request
{
  "keyword": "road construction",
  "region": "Maharashtra"
}

// Response: array of { title, url, snippet, source_type }
```

### `POST /api/run`

Full analysis mode — runs the complete 7-agent pipeline.

```json
// Request
{
  "keyword": "smart city",
  "region": "India",
  "scope": "all",
  "profile": {
    "company_name": "Infra Solutions Pvt. Ltd.",
    "company_type": "Construction / Civil",
    "turnover_cr": "50",
    "experience_yrs": "12",
    "certifications": "ISO 9001, MSME",
    "past_projects": "Highway construction, bridge rehabilitation"
  }
}

// Response: array of analyzed tenders with scores, extracted data, and bid proposals
```

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | **Yes** | Groq API key for Llama 3.3 70B inference |
| `TAVILY_API_KEY` | **Yes** | Tavily web search API key |
| `EXA_API_KEY` | Recommended | Exa semantic search (improves recall) |
| `GEMINI_API_KEY` | Recommended | Google Gemini for judge agent evaluation |
| `POPPLER_PATH` | Optional | Poppler binary path for OCR (Windows only) |

---

## 🛡️ Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Regex before LLM** | Extracts ~60% of fields without any API call, saving tokens and latency |
| **Single LLM call per tender** | One combined extraction + relevance prompt instead of multiple calls |
| **Permissive validator** | False negatives (missing a real tender) are worse than false positives |
| **Lazy imports** | `fitz`, `google.generativeai`, `ollama` imported only when used — prevents crashes on Vercel |
| **`/tmp` for downloads** | Vercel's filesystem is read-only except `/tmp` |
| **Structured bid fallback** | If LLM fails, a template-based proposal is generated instead of returning nothing |
| **Judge recomputes score** | Never trusts the LLM's arithmetic — recomputes the average server-side |

---

## 📜 License

This project is for educational and demonstration purposes.

---

<div align="center">

**Built with ❤️ by [Aradhya UM](https://github.com/AradhyaUM)**

</div>
