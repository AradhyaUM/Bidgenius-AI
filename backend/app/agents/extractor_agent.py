import re
import json
from datetime import datetime

# ─────────────────────────────────────────────
# INDIC NUMERALS
# ─────────────────────────────────────────────
INDIC_NUMERALS = {
    '०':'0','१':'1','२':'2','३':'3','४':'4',
    '५':'5','६':'6','७':'7','८':'8','९':'9'
}

def normalize_indic(text):
    for indic, arabic in INDIC_NUMERALS.items():
        text = text.replace(indic, arabic)
    return text


# ─────────────────────────────────────────────
# DATE PARSING
# ─────────────────────────────────────────────
DATE_FORMATS = [
    "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
    "%d-%m-%y", "%d/%m/%y", "%d.%m.%y",
    "%Y-%m-%d", "%d %b %Y", "%d %B %Y",
    "%d-%b-%Y", "%d/%b/%Y",
]

def parse_date(s):
    if not s:
        return None
    s = s.strip().rstrip(")").rstrip("/")
    s = re.sub(r'\s+\d{1,2}:\d{2}.*$', '', s).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None

def is_active_tender(end_date_str):
    dt = parse_date(end_date_str)
    if dt is None:
        return None
    return dt >= datetime.now()

def _is_valid_date(s):
    if not s:
        return False
    parts = re.split(r'[./-]', s.split()[0])
    if len(parts) != 3:
        return False
    try:
        d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
        return (1 <= d <= 31 and 1 <= m <= 12 and 2020 <= y <= 2030
                and parse_date(s) is not None)
    except (ValueError, TypeError):
        return False


# ─────────────────────────────────────────────
# MONEY CLEANING
# ─────────────────────────────────────────────
def clean_money(value):
    if not value:
        return None
    value = str(value).strip()
    value = normalize_indic(value)

    if re.search(r'\b(nil|free|exempted|zero)\b', value, re.IGNORECASE):
        return "0"

    value = re.sub(
        r'[₹$]|Rs\.?|INR|/-|only|inclusive|approx',
        '', value, flags=re.IGNORECASE
    ).strip()

    multiplier = 1
    lower = value.lower()
    if re.search(r'\bcrore\b|\bcr\.?\b', lower):
        multiplier = 10_000_000
    elif re.search(r'\blakh\b|\blac\b', lower):
        multiplier = 100_000
    elif re.search(r'\bthousand\b', lower):
        multiplier = 1_000

    digits = re.sub(r'[^\d.]', '', value)
    if not digits:
        return None
    try:
        num = float(digits) * multiplier
        if num < 0 or num > 1e12:
            return None
        return str(int(num))
    except ValueError:
        return None


# ─────────────────────────────────────────────
# KEYWORD SETS — English + 4 regional languages
# ─────────────────────────────────────────────
TENDER_FEE_KW = [
    "Tender Fee", "Tender Processing Fee", "Document Fee", "Bid Document Fee",
    "Tender Document Fee", "Processing Fee", "Cost of Tender Document",
    "Non-refundable fee", "Non refundable",
    "निविदा शुल्क", "प्रोसेसिंग शुल्क", "दस्तावेज़ शुल्क",
    "दरपुस्तिका शुल्क", "டெண்டர் கட்டணம்", "టెండర్ రుసుము",
]

EMD_KW = [
    "Tender Security", "Earnest Money Deposit", "Earnest Money",
    "Bid Security", "Security Deposit",
    r"\bEMD\b", r"\bE\.M\.D\b",
    "बयाना राशि", "धरोहर राशि", "इसारा रक्कम",
    "முன்வைப்புத் தொகை", "ధరావత్తు",
]

COST_KW = [
    "Estimated Cost", "Tender Value", "Contract Value", "Approximate Value",
    "Estimated Value", "Total Value", "Cost of Work", "Value of Work",
    "PAC", "Probable Amount of Contract", "Approximate Cost",
    "अनुमानित लागत", "अंदाजित खर्च", "మతిப్పீట్టుచ్ செலவு", "అంచనా వ్యయం",
]

BID_END_KW = [
    "Last Date", "Closing Date", "Bid End Date", "Submission End Date",
    "Submission Deadline", "Due Date", "Deadline", "Bid Due Date",
    "Last date of submission", "Date of closing", "Bid Closing",
    "Last Date & Time", "Last Date and Time",
    "अंतिम तिथि", "अंतिम दिनांक", "शेवटची तारीख",
    "முடிவுத் தேதி", "ముగింపు తేదీ",
]

BID_START_KW = [
    "Bid Start Date", "Start Date", "Document Sale Start",
    "Start of Bid", "Bid Submission Start", "From Date",
    "प्रारंभ तिथि", "सुरू होण्याची तारीख", "தொடக்கத் தேதி", "ప్రారంభ తేదీ",
]

OPENING_KW = [
    "Opening Date", "Bid Opening", "Technical Opening",
    "Date of Opening", "Open Date", "Technical Bid Opening", "Financial Bid Opening",
    "खोलने की तिथि", "उघडण्याची तारीख", "திறக்கும் தேதி", "తెరిచే తేదీ",
]

PUBLISH_KW = [
    "Publish Date", "Published", "Issue Date", "Date of Issue",
    "Publication Date", "NIT Date",
]

SECTION_HEADERS = [
    "Critical Date Sheet", "Critical Dates", "Important Dates",
    "Tender Information Summary", "TIS", "Notice Inviting Tender", "NIT",
    "Key Dates", "Tender Schedule", "Financial Details", "Bid Details",
    "महत्वपूर्ण तिथियां", "निविदा सूचना",
]


# ─────────────────────────────────────────────
# TEXT PREPARATION FOR LLM
# With paid Groq (128K context), send full document up to 25K chars
# ─────────────────────────────────────────────
def smart_chunk(text, max_size=25000):
    if len(text) <= max_size:
        return text
    # For very long documents, take first 20K + last 5K to capture
    # both header/summary info and appendix/schedule details
    return text[:20000] + "\n\n--- [DOCUMENT CONTINUES] ---\n\n" + text[-5000:]


# ─────────────────────────────────────────────
# REGEX EXTRACTION (fast, free, zero API calls)
# ─────────────────────────────────────────────
_DATE_RE  = r'(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})'
_MONEY_RE = r'(?:INR|Rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)\s*(?:/-|Lakh|Lac|Crore|Cr)?'

def _table_find(text, keywords, vtype):
    """Finds value on same line OR next 3 lines after keyword."""
    lines = text.split('\n')
    for i, line in enumerate(lines):
        ll = line.lower()
        matched = None
        for kw in keywords:
            pat = kw if kw.startswith(r'\b') else re.escape(kw)
            if re.search(pat, ll, re.IGNORECASE):
                matched = kw
                break
        if not matched:
            continue
        window = ' '.join(lines[i: min(i+4, len(lines))])
        pat = matched if matched.startswith(r'\b') else re.escape(matched)
        parts = re.split(pat, window, flags=re.IGNORECASE, maxsplit=1)
        if len(parts) < 2:
            continue
        after = parts[1]
        if vtype == "money":
            m = re.search(_MONEY_RE, after, re.IGNORECASE)
            if m:
                r = clean_money(m.group(1))
                if r:
                    return r
        elif vtype == "date":
            m = re.search(_DATE_RE, after)
            if m and _is_valid_date(m.group(1)):
                return m.group(1)
        elif vtype == "text":
            after = after.strip().lstrip(':- \t')
            m = re.match(r'([A-Za-z][A-Za-z0-9 ,.&()\-]{3,80})', after)
            if m and len(m.group(1).strip()) > 3:
                return m.group(1).strip()
    return None

def _inline_find(text, keywords, vtype):
    """Finds value within 200 chars after keyword on same line."""
    suffixes = {
        "date":  r'.{0,120}?' + _DATE_RE,
        "money": r'.{0,200}?' + _MONEY_RE,
        "text":  r'\s*[:\-]?\s*([A-Za-z][A-Za-z0-9 ,.&()\-]{3,80})',
    }
    for kw in keywords:
        pat = kw if kw.startswith(r'\b') else re.escape(kw)
        m = re.search(pat + suffixes[vtype], text, re.IGNORECASE | re.DOTALL)
        if not m:
            continue
        val = m.group(1).strip()
        if vtype == "date" and _is_valid_date(val.split()[0]):
            return val.split()[0]
        elif vtype == "money":
            r = clean_money(val)
            if r:
                return r
        elif vtype == "text":
            val = re.sub(r'\s+\d+$', '', val).strip()
            if len(val) > 3:
                return val
    return None

def _find(text, keywords, vtype):
    return _inline_find(text, keywords, vtype) or _table_find(text, keywords, vtype)


# ─────────────────────────────────────────────
# LLM EXTRACTION
# Called in two modes:
#   mode="relevance"  — quick check + fill missing fields (full document)
#   mode="full"       — when regex got almost nothing (fallback only)
#
# Token budget per call (paid Groq, 128K context):
#   Full document up to 25K chars ≈ 6K tokens
#   Prompt overhead ≈ 300 tokens
#   Total input ≈ 6300 tokens — well within paid limits
# ─────────────────────────────────────────────
_CRITICAL = {
    "EMD", "Tender Fee", "Estimated Cost",
    "Bid End Date", "Bid Start Date", "Bid Opening Date"
}

def _llm_call(text, missing_fields, target_keyword, mode="relevance"):
    """
    Single LLM call that does relevance check + extracts only missing fields.
    This is the key optimization — one call, not two.
    """
    try:
        from app.llm.llm_router import generate

        chunk = smart_chunk(text, max_size=25000)

        # Only ask for fields that are actually missing
        critical_missing = [f for f in missing_fields if f in _CRITICAL]
        if not critical_missing and mode == "relevance":
            # No critical fields missing — just do relevance check
            fields_section = '(all critical fields already extracted — skip data extraction)'
        else:
            fields_section = "\n".join(
                f'  "{f}": {_FIELD_DESC.get(f, f)}'
                for f in (critical_missing or missing_fields)
                if f in _FIELD_DESC
            )

        prompt = f"""You are an Indian government tender analyst.

TASK 1 — RELEVANCE: Is this document primarily about "{target_keyword}"?
Set is_relevant = true only if the main work/subject matches. false if it's a different category that just mentions the word.

TASK 2 — EXTRACT MISSING FIELDS ONLY:
{fields_section}

Return ONLY a raw JSON object (no markdown, no backticks):
{{
  "is_relevant": true or false,
  "primary_category": "3-5 word description of actual work",
  {chr(10).join(f'  "{f}": null' for f in (critical_missing or []))}
}}

Rules:
- Tender Fee = small NON-REFUNDABLE doc fee (Rs 500–50,000). Label: "Tender Processing Fee", "Document Fee"
- EMD = LARGER REFUNDABLE deposit (usually lakhs). Label: "Tender Security", "Bid Security", "बयाना राशि", "इसारा रक्कम"
- Dates: DD-MM-YYYY only. Reject financial years like "2025-26"
- Money: digits only (4173000 for Rs 41.73 Lakh)
- null if not found — never guess

Document:
{chunk}

JSON:"""

        response = generate(prompt)
        if not response:
            return {"is_relevant": True, "primary_category": "Refer to PDF"}

        # Strip markdown if present
        response = re.sub(r'^```[a-z]*\n?', '', response.strip())
        response = re.sub(r'\n?```$', '', response).strip()

        # Extract JSON even if there's surrounding text
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            return {"is_relevant": True, "primary_category": "Refer to PDF"}

        parsed = json.loads(json_match.group(0))

        # Validate dates
        result = {}
        for k, v in parsed.items():
            if v is None or str(v).strip() in ('', 'null', 'None'):
                continue
            if k in ("Bid End Date", "Bid Start Date", "Bid Opening Date", "Publish Date"):
                if not _is_valid_date(str(v)):
                    continue
            result[k] = v

        return result

    except Exception as e:
        print(f"⚠️ LLM error: {e}")
        return {"is_relevant": True, "primary_category": "Refer to PDF"}


_FIELD_DESC = {
    "Tender Fee":       "Non-refundable doc fee INR digits only e.g. 25000",
    "EMD":              "Refundable Earnest Money / Tender Security INR digits only",
    "Estimated Cost":   "Contract value / PAC INR digits only",
    "Turnover":         "Min required annual turnover INR digits only",
    "Organization":     "Procuring organization name",
    "Ministry":         "Ministry or department name",
    "Location":         "City/district of work",
    "Publish Date":     "Publication date DD-MM-YYYY",
    "Bid Start Date":   "Bid start date DD-MM-YYYY",
    "Bid End Date":     "Last submission date DD-MM-YYYY",
    "Bid Opening Date": "Bid opening date DD-MM-YYYY",
}


# ─────────────────────────────────────────────
# MAIN EXTRACTION
# Strategy:
#   1. Regex extracts structured fields (fast, free)
#   2. One LLM call: relevance check + fill only missing critical fields
#   3. Result: ~1 LLM call per tender instead of 1-2
# ─────────────────────────────────────────────
def extract_key_details(text, target_keyword="Tender"):
    if not text:
        return _empty()

    text = normalize_indic(text)
    d = {}

    # ── Tender ID ─────────────────────────────
    tid = re.search(r'\b(?:202[0-9])(?:[/_][A-Z0-9\-]+){2,}\b', text)
    d["Tender ID"] = tid.group(0) if tid else None

    # ── Dates (regex) ─────────────────────────
    d["Bid End Date"]     = _find(text, BID_END_KW,   "date")
    d["Bid Start Date"]   = _find(text, BID_START_KW, "date")
    d["Bid Opening Date"] = _find(text, OPENING_KW,   "date")
    d["Publish Date"]     = _find(text, PUBLISH_KW,   "date")

    # Validate — discard garbage dates
    for f in ("Bid End Date", "Bid Start Date", "Bid Opening Date", "Publish Date"):
        if d.get(f) and not _is_valid_date(d[f]):
            d[f] = None

    # ── Money (regex) — Tender Fee BEFORE EMD to avoid confusion ──
    d["Tender Fee"]     = _find(text, TENDER_FEE_KW, "money")
    d["EMD"]            = _find(text, EMD_KW,         "money")
    d["Estimated Cost"] = _find(text, COST_KW,        "money")
    d["Turnover"]       = _find(text,
        ["Turnover", "Annual Turnover", "Minimum Turnover",
         "Average Annual Turnover", "न्यूनतम टर्नओवर"], "money")

    # Sanity: EMD should be >= Tender Fee
    if d["EMD"] and d.get("Tender Fee"):
        try:
            if int(d["EMD"]) < int(d["Tender Fee"]):
                print(f"   ⚠️ EMD {d['EMD']} < Tender Fee {d['Tender Fee']} — clearing EMD")
                d["EMD"] = None
        except Exception:
            pass

    # ── Text fields (regex) ───────────────────
    d["Organization"] = _find(text, [
        "Organization", "Organisation", "Procuring Entity",
        "Buyer Organization", "Department", "Authority",
    ], "text")
    d["Ministry"]  = _find(text, ["Ministry", "Ministry of"], "text")
    d["Location"]  = _find(text, [
        "Location", "Place of Work", "Delivery Location", "District",
    ], "text")

    # ── ONE LLM call: relevance + missing critical fields ──
    missing = [k for k, v in d.items() if v is None]
    critical_missing = [f for f in missing if f in _CRITICAL]

    # Always call LLM for relevance check — costs ~1300 tokens, not 10K
    print(f"🤖 LLM call — relevance check + filling: {critical_missing or 'none'}")
    llm = _llm_call(text, missing, target_keyword, mode="relevance")

    # Merge LLM results into regex results (regex wins if it already found something)
    d["is_relevant"]      = llm.get("is_relevant", True)
    d["primary_category"] = llm.get("primary_category", "Refer to PDF")

    for field, value in llm.items():
        if field in ("is_relevant", "primary_category"):
            continue
        if value is not None and d.get(field) is None:
            if field in ("EMD", "Tender Fee", "Estimated Cost", "Turnover"):
                cleaned = clean_money(str(value))
                if cleaned:
                    d[field] = cleaned
            else:
                d[field] = str(value).strip()

    # ── Active status & flags ──────────────────
    d["is_active"]       = is_active_tender(d.get("Bid End Date"))
    d["is_corrigendum"]  = bool(re.search(
        r'corrigendum|extension|amendment', text, re.IGNORECASE
    ))

    return d


def _empty():
    return {
        "is_relevant": True, "primary_category": "Refer to PDF",
        "Tender ID": None, "Tender Fee": None, "EMD": None,
        "Estimated Cost": None, "Turnover": None,
        "Organization": None, "Ministry": None, "Location": None,
        "Publish Date": None, "Bid Start Date": None,
        "Bid End Date": None, "Bid Opening Date": None,
        "is_active": None, "is_corrigendum": False,
    }