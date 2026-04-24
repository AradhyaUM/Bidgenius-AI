# Problem Statement

## BidGenius AI — Agentic Tender Intelligence Platform

---

## 1. Background

India's government procurement ecosystem operates across hundreds of fragmented portals — GeM, eProcure, state-level PWD portals, MahaTenders, municipal corporation sites, and PSU procurement boards. Together these platforms publish **tens of thousands of tenders per month**, each with unique document formats, eligibility criteria, fee structures, and submission deadlines.

Small and mid-size enterprises (SMEs) that depend on government contracts face a **critical information asymmetry problem**: they lack the resources to continuously monitor every portal, parse heterogeneous documents (PDFs, scanned images, multilingual text), evaluate compliance requirements, and draft competitive bids before strict deadlines.

## 2. Problem Definition

> **How can an intelligent, autonomous system discover, extract, evaluate, and respond to government tenders across disparate procurement portals — while accounting for multilingual documents, inconsistent data formats, and tight submission windows?**

### Core Challenges

| # | Challenge | Impact |
|---|-----------|--------|
| 1 | **Portal Fragmentation** | Tenders are scattered across 50+ central, state, and municipal portals with no unified API or schema. |
| 2 | **Unstructured / Multilingual Documents** | Tender notices arrive as scanned PDFs, HTML pages, or regional-language documents (Hindi, Marathi, Tamil, etc.), making automated extraction extremely difficult. |
| 3 | **Expired & Irrelevant Noise** | Raw search results return a mix of active, expired, and unrelated listings. Manual filtering is time-consuming and error-prone. |
| 4 | **Complex Eligibility Assessment** | Each tender has unique turnover thresholds, certification requirements, EMD amounts, and category restrictions that must be matched against company capabilities. |
| 5 | **Tight Deadlines** | Missing a submission window by even a single day disqualifies the bid entirely. Deadline information is often buried deep inside multi-page documents. |
| 6 | **Proposal Drafting Overhead** | Writing a compliant bid proposal from scratch for every opportunity is resource-intensive and repetitive. |

## 3. Research Gap

Existing procurement tools are either:
- **Simple aggregators** that list tender metadata without deep extraction or analysis.
- **Keyword-based search engines** that return noisy, unfiltered results.
- **Manual consulting services** that are expensive and do not scale.

There is no publicly available system that combines **autonomous web search**, **AI-powered document extraction**, **multi-format deadline parsing**, **bid-fit scoring**, and **automated proposal generation** into a single, end-to-end agentic pipeline.

## 4. Proposed Solution

**BidGenius AI** is an agentic, multi-model AI platform that automates the complete tender lifecycle:

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Web Search │ ──▶ │  Document    │ ──▶ │  Field       │ ──▶ │  Scoring &   │ ──▶ │  Bid Draft   │
│  Agent      │     │  Reader      │     │  Extractor   │     │  Validator   │     │  Generator   │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
     Tavily            PyMuPDF             Groq LLM             Rule-based           Groq LLM
     Exa API           OCR fallback        Gemini LLM           + LLM hybrid         + company profile
```

### Key Capabilities

1. **Multi-source discovery** — Searches across GeM, eProcure, state portals, and PSU sites using Tavily and Exa APIs.
2. **Intelligent document extraction** — Downloads PDFs, applies OCR when needed, and extracts structured fields (deadlines, fees, EMD, eligibility) using LLM-powered parsing.
3. **Expired tender filtering** — Compares extracted deadlines against the current date and **hides expired tenders** from the dashboard so users only see actionable opportunities.
4. **Deadline urgency visualization** — Each tender displays a **color-coded highlighted deadline box** (🔴 urgent / 🟡 warning / ✅ safe) for instant visual triage.
5. **Bid-fit scoring** — Evaluates each tender against the user's company profile (turnover, certifications, experience) and assigns a 0–100 compatibility score.
6. **Automated proposal drafting** — Generates a first-pass bid document personalized to the company's strengths and the tender's requirements.

## 5. Objectives

1. **Reduce discovery time** from hours of manual portal browsing to under 5 minutes of automated search.
2. **Eliminate expired noise** by automatically filtering tenders whose deadlines have passed.
3. **Surface deadline urgency** through prominent visual indicators on every tender card.
4. **Enable faster bid response** by auto-generating a proposal draft that the team can refine.
5. **Demonstrate agentic AI architecture** — a sequential multi-agent pipeline where each agent hands off structured output to the next.

## 6. Scope

### In Scope
- Indian government procurement portals (central, state, municipal, PSU)
- English and major regional language documents
- PDF and web-based tender documents
- Real-time search using live web APIs
- Streamlit-based interactive dashboard
- FastAPI-powered backend with modular agent architecture

### Out of Scope
- Automatic bid submission to portals
- Payment gateway integration for tender fee deposits
- Legal contract review or dispute resolution
- International procurement systems

## 7. Target Users

| User Segment | Use Case |
|-------------|----------|
| SME procurement teams | Discover and evaluate tenders matching their domain |
| Bid managers | Generate first-draft proposals from extracted tender data |
| Government affairs consultants | Monitor multiple sectors for client opportunities |
| Academic researchers | Study agentic AI pipeline design and evaluation |

## 8. Expected Outcomes

- A fully functional **agentic tender intelligence dashboard** deployable on localhost.
- Measurable reduction in tender discovery and evaluation time.
- Academic-grade demonstration of multi-agent AI orchestration with self-improving feedback loops.
- Clean, professional UI with **real-time deadline tracking** and **expired tender filtering**.

## 9. Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit (Python) |
| Backend API | FastAPI + Uvicorn |
| LLM Providers | Groq (Llama/Mixtral), Google Gemini |
| Search APIs | Tavily, Exa |
| Document Processing | PyMuPDF, OCR (Poppler) |
| Language | Python 3.14 |
| Environment | Windows, localhost deployment |

---

*BidGenius AI — Multilingual Tender & RFP Analyst Platform*
*Academic Project · 2026*
