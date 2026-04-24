# Task Decomposition — BidGenius AI

## Pipeline Flow

```
User Input → Search Agent → Document Reader → Field Extractor → Scoring → Bid Generator → Dashboard
```

---

## Tasks by Module

### 1. Search Agent
- Discover tenders via Tavily & Exa APIs with multi-query strategy
- Support portal scope filtering (central, state, municipal, PSU)
- Deduplicate results and handle API rate limits

### 2. Document Reader
- Download tender pages (HTML/PDF) with timeout handling
- Extract text from PDFs using PyMuPDF; OCR fallback for scanned docs

### 3. Field Extractor
- LLM-powered extraction of structured fields (ID, Org, Fees, EMD, Deadlines, Budget)
- Normalize dates across multiple formats; sanitize malformed JSON output

### 4. Scoring & Validation
- Classify tenders as active/expired based on deadline
- Score bid-fit (0–100) against company profile (turnover, certs, experience)
- Generate executive summary and flag risks

### 5. Bid Generator
- Generate personalized bid proposal draft using company profile + tender data
- Provide downloadable `.txt` output

### 6. Dashboard (Streamlit)
- Premium dark glassmorphism UI with company profile sidebar
- **Filter out expired tenders** by comparing deadline to current date
- **Highlighted deadline box** per tender with color-coded urgency (🔴🟡✅)
- Tabbed detail view (summary, details, proposal) with download support

### 7. Backend API (FastAPI)
- `/run` — full pipeline, `/list` — quick scan, `/health` — status check
- `.env`-based API key configuration

---

*BidGenius AI · April 2026*
