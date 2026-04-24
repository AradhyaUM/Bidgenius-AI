<div align="center">

<img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/FastAPI-0.136-009688?style=flat-square&logo=fastapi&logoColor=white" />
<img src="https://img.shields.io/badge/Streamlit-1.56-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" />
<img src="https://img.shields.io/badge/Groq-LLM-F55036?style=flat-square" />
<img src="https://img.shields.io/badge/Gemini-1.5_Flash-4285F4?style=flat-square&logo=google&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-22c55e?style=flat-square" />

<br /><br />

# BidGenius AI
### Agentic Tender Intelligence Platform

**Automatically discover, extract, score, and draft responses to Indian government tenders — end-to-end.**

[Overview](#-overview) · [Architecture](#-architecture) · [Features](#-features) · [Quick Start](#-quick-start) · [Usage](#-usage) · [Project Structure](#-project-structure)

</div>

---

## Overview

India's government procurement ecosystem is spread across **50+ fragmented portals** — GeM, eProcure, state PWD portals, MahaTenders, PSU procurement boards — publishing tens of thousands of tenders each month. Small and mid-size enterprises waste hours of manual work just discovering and filtering relevant opportunities before they can even assess or respond.

**BidGenius AI** automates the complete tender lifecycle through a sequential multi-agent pipeline:

- **Discovers** tenders across portals via multi-query web search
- **Extracts** structured fields from PDFs and HTML pages (fees, deadlines, eligibility, EMD)
- **Filters** expired tenders automatically — only active opportunities shown
- **Scores** each tender against your company profile (0–100 bid-fit)
- **Drafts** a personalized bid proposal, ready to refine and submit

> Academic project demonstrating agentic AI pipeline design with real-world procurement data.

---

## Architecture

```
User / Browser
      │
      ▼
┌──────────────────────────────────────────────────┐
│        Streamlit Dashboard  (frontend/app.py)    │
│   Sidebar · Search · Deadline Cards · Bid Draft  │
└─────────────────────┬────────────────────────────┘
                      │  HTTP REST  (localhost:8000)
                      ▼
┌──────────────────────────────────────────────────┐
│         FastAPI Backend  (uvicorn :8000)         │
│      POST /run  ·  POST /list  ·  GET /health    │
└─────────────────────┬────────────────────────────┘
                      │  Sequential Agent Pipeline
                      ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  Search  │→ │ Document │→ │  Field   │→ │ Scoring  │→ │   Bid    │
│  Agent   │  │  Reader  │  │Extractor │  │Validator │  │Generator │
│          │  │          │  │          │  │          │  │          │
│ Tavily   │  │ HTTP/PDF │  │ LLM Parse│  │  0–100   │  │ Proposal │
│ Exa API  │  │ PyMuPDF  │  │ JSON Norm│  │ Risk Flag│  │ .txt DL  │
│ Dedup    │  │ OCR Fall │  │ Date Norm│  │ Expired↓ │  │          │
└────┬─────┘  └──────────┘  └────┬─────┘  └──────────┘  └────┬─────┘
     │                           │                            │
     ▼                           ▼                            ▼
Tavily · Exa          Groq (Llama 3 / Mixtral)        Groq / Gemini
                      Google Gemini 1.5 Flash          Multi-key pool
```

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit 1.56 · Custom CSS (Glassmorphism) |
| Backend | FastAPI · Uvicorn |
| LLMs | Groq (Llama 3.3 / Mixtral) · Google Gemini 1.5 Flash |
| Search | Tavily API · Exa API |
| PDF Processing | PyMuPDF · Poppler OCR |
| Language | Python 3.11+ |
| Config | `.env` · multi-key rotation · exponential backoff |

---

## Features

| Feature | Description |
|---|---|
| **Multi-source Discovery** | Searches GeM, eProcure, state portals & PSUs via Tavily + Exa with multi-query strategy |
| **Document Extraction** | Downloads PDFs, applies OCR fallback, extracts all key fields using LLM-powered parsing |
| **Expired Tender Filter** | Auto-hides tenders past their deadline — only active results shown |
| **Deadline Urgency Box** | Color-coded 🔴 🟡 ✅ deadline indicator on every tender card |
| **Bid-Fit Scoring** | 0–100 score matching your company profile (turnover, certifications, experience) |
| **AI Proposal Draft** | First-pass bid proposal personalized to your company's strengths and tender requirements |
| **Quick List Mode** | Fast scan with deadline extraction — results in under 60 seconds |
| **LLM Failover** | 18 Groq API key slots with exponential backoff + Gemini fallback |

---

## Quick Start

### Prerequisites

- Python 3.11 or higher
- API keys from: [Tavily](https://tavily.com), [Groq](https://console.groq.com), [Google Gemini](https://ai.google.dev), [Exa](https://exa.ai)

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/bidgenius-ai.git
cd bidgenius-ai

# Create virtual environment
python -m venv backend/venv

# Activate (Windows)
backend\venv\Scripts\activate
# Activate (Linux / macOS)
# source backend/venv/bin/activate

# Install dependencies
pip install fastapi uvicorn python-dotenv pydantic requests groq \
            google-generativeai exa-py tavily-python PyMuPDF streamlit
```

### 2. Configure API Keys

Create `backend/.env`:

```env
TAVILY_API_KEY=tvly-xxxxxxxxxxxx
GOOGLE_API_KEY=AIzaSy-xxxxxxxxxxxx
EXA_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
GROQ_API_KEY_1=gsk_xxxxxxxxxxxx
GROQ_API_KEY_2=gsk_xxxxxxxxxxxx
# Add more as GROQ_API_KEY_3, _4 ... for higher throughput
SECRET_KEY=your-secret-here
```

### 3. Run

**Terminal 1 — Backend:**

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**

```bash
cd frontend
python -m streamlit run app.py --server.port 8501
```

Open **http://localhost:8501** in your browser.

---

## Usage

1. **Set Company Profile** — Fill in your company name, type, annual turnover, and certifications in the sidebar.
2. **Choose a mode:**
   - **Quick List** — Fast discovery with deadline indicators (~30–60 seconds)
   - **Full Analysis** — Deep extraction + scoring + bid draft (~3–5 minutes)
3. **Enter a keyword and region** — e.g. `road construction` + `Maharashtra`
4. **Launch Search** — View color-coded deadline urgency boxes, bid-fit scores, and proposal drafts.
5. **Download** — Export the generated bid proposal as a `.txt` file.

---

## Project Structure

```
bidgenius-ai/
├── backend/
│   ├── .env                       # API keys (gitignored)
│   ├── requirements.txt
│   └── app/
│       ├── main.py                # FastAPI entry point
│       ├── agents/
│       │   ├── search_agent.py    # Agent 1: Discover tenders
│       │   ├── reader_agent.py    # Agent 2: Read documents
│       │   ├── extractor_agent.py # Agent 3: Extract fields
│       │   ├── analysis_agent.py  # Agent 4: Score & validate
│       │   ├── validator_agent.py # Agent 4b: Active/expired check
│       │   └── bid_agent.py       # Agent 5: Generate proposal
│       ├── llm/
│       │   ├── groq_llm.py        # Groq with key rotation
│       │   ├── gemini_llm.py      # Google Gemini
│       │   └── llm_router.py      # Model selection logic
│       ├── tools/
│       │   ├── tavily_tool.py     # Tavily search wrapper
│       │   ├── exa_tool.py        # Exa search wrapper
│       │   └── pdf_parser.py      # PyMuPDF + OCR
│       └── services/
│           └── pipeline.py        # Full pipeline orchestrator
└── frontend/
    └── app.py                     # Streamlit dashboard
```

---

## API Keys

| Service | Purpose | Free Tier |
|---|---|---|
| [Tavily](https://tavily.com) | Web search for tenders | 1,000 searches/month |
| [Exa](https://exa.ai) | Semantic search | 1,000 searches/month |
| [Groq](https://console.groq.com) | Fast LLM inference | Free tier available |
| [Google Gemini](https://ai.google.dev) | LLM fallback + cleaning | Free tier available |

> Add multiple `GROQ_API_KEY_N` entries to increase throughput via key rotation.

---

## Scope

**In scope:** Indian government procurement portals (central, state, municipal, PSU) · English and major regional language documents · PDF and web-based tender documents · Real-time search using live APIs · Streamlit dashboard · FastAPI backend with modular agent architecture.

**Out of scope:** Automatic bid submission · Payment gateway integration · Legal contract review · International procurement systems.

---

## License

[MIT License](LICENSE) — Academic Project · 2026

---

<div align="center">
Built as an Academic Agentic AI Project · April 2026
</div>
