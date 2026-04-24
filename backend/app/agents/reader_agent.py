import requests as http_requests
import os
import re
import uuid
import warnings
import threading
import logging
import asyncio

logger = logging.getLogger("bidgenius.reader")

from app.tools.pdf_parser import extract_text, extract_text_ocr
from app.agents.extractor_agent import extract_key_details
from app.agents.analysis_agent import analyze_tender
from app.agents.bid_agent import generate_bid
from app.agents.judge_agent import evaluate_bid

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

PDF_DOWNLOAD_TIMEOUT = 15
PDF_PROCESS_TIMEOUT  = 90

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*",
}

# ── INLINE VALIDATION ─────────────────────────────────────────────────────────
_COURT_PATS  = [r'\bcnr\s*no\b', r'\bpetitioner\b', r'\brespondent\b',
                r'\bwrit\s+petition\b', r'\bhon.?ble\s+court\b']
_TENDER_PATS = [r'\btender\b', r'\brfp\b', r'\brfq\b', r'\beoi\b', r'\bbid\b',
                r'\bprocurement\b', r'\bemd\b', r'\bearnest\s+money\b',
                r'\bbidder\b', r'\bnit\b', r'\bnivida\b']
_MIN_VALUES  = {"EMD": 1_000, "Tender Fee": 500, "Estimated Cost": 10_000, "Turnover": 10_000}


def _validate(text, details):
    lower = text[:8000].lower()
    has_tender = any(re.search(p, lower) for p in _TENDER_PATS)
    if not has_tender:
        court_hits = sum(1 for p in _COURT_PATS if re.search(p, lower))
        if court_hits >= 3:
            return False, []

    warnings_out = []
    for field, min_val in _MIN_VALUES.items():
        try:
            n = int(details.get(field) or 0)
            if 0 < n < min_val:
                logger.info(f"  {field}={n} below minimum ₹{min_val:,} — clearing")
                warnings_out.append(f"{field} ₹{n:,} appears to be a list index — check PDF")
                details[field] = None
        except (TypeError, ValueError):
            pass

    return True, warnings_out


# ── DOWNLOAD ──────────────────────────────────────────────────────────────────
def download_pdf(url):
    pdf_path = os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4()}.pdf")
    try:
        response = http_requests.get(
            url, timeout=PDF_DOWNLOAD_TIMEOUT,
            headers=HEADERS, allow_redirects=True
        )
    except http_requests.exceptions.SSLError:
        logger.warning("SSL error — retrying without verification")
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            warnings.filterwarnings("ignore")
            response = http_requests.get(
                url, timeout=PDF_DOWNLOAD_TIMEOUT,
                headers=HEADERS, allow_redirects=True, verify=False
            )
        except Exception as e:
            logger.error(f"SSL retry failed: {e}")
            return None
    except http_requests.Timeout:
        logger.warning(f"Download timeout: {url[:60]}")
        return None
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None

    if response.status_code != 200:
        logger.warning(f"HTTP {response.status_code}: {url[:60]}")
        return None

    content = response.content
    if len(content) < 3000:
        return None
    ct = response.headers.get("Content-Type", "").lower()
    if (not (content[:4] == b"%PDF" or b"PDF" in content[:20])
            and "pdf" not in ct and "octet" not in ct):
        return None
    with open(pdf_path, "wb") as f:
        f.write(content)
    return pdf_path


def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\f', ' ', text)
    text = text.replace("â€™", "'").replace("â€œ", '"').replace("â€", '"')
    text = text.replace("\x00", "")
    return text.strip()


def read_tender(url):
    pdf_path = None
    try:
        pdf_path = download_pdf(url)
        if not pdf_path:
            return None
        text = extract_text(pdf_path)
        if not text or len(text) < 200:
            if os.path.getsize(pdf_path) < 5_000_000:
                logger.info("Trying OCR...")
                text = extract_text_ocr(pdf_path)
        return clean_text(text) if text and len(text) >= 100 else None
    except Exception as e:
        logger.error(f"Reader error: {e}")
        return None
    finally:
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception:
                pass


def sanitize_for_display(details):
    ui = {}
    money_fields = {"EMD", "Tender Fee", "Estimated Cost", "Turnover"}
    for k, v in details.items():
        if v is None or str(v).strip() in ("", "None", "null"):
            ui[k] = "Refer to PDF"
        elif k in money_fields:
            try:
                n = int(v)
                if n == 0:              ui[k] = "₹0 (Exempted)"
                elif n >= 10_000_000:   ui[k] = f"₹{n/10_000_000:.2f} Cr"
                elif n >= 100_000:      ui[k] = f"₹{n/100_000:.2f} L"
                else:                   ui[k] = f"₹{n:,}"
            except (ValueError, TypeError):
                ui[k] = "Refer to PDF"
        else:
            ui[k] = v
    return ui


# ── MAIN ENTRY POINT ──────────────────────────────────────────────────────────
def process_tender(tender, target_keyword="Tender", company_profile=None):
    result, error = [None], [None]

    def _run():
        try:
            result[0] = _process(tender, target_keyword, company_profile or {})
        except Exception as e:
            error[0] = e

    t = threading.Thread(target=_run)
    t.start()
    t.join(timeout=PDF_PROCESS_TIMEOUT)

    if t.is_alive():
        logger.warning(f"Timeout — skipping: {tender.get('title','')[:50]}")
        return None
    if error[0]:
        logger.error(f"Processing error: {error[0]}")
        return None
    return result[0]


def _process(tender, target_keyword, company_profile):
    url   = tender.get("url", "")
    title = tender.get("title", "Unknown")
    logger.info(f"  {title[:70]}")

    full_text = tender.get("full_text", "")
    if full_text and len(full_text) > 500:
        logger.info(f"  Using Exa text ({len(full_text):,} chars)")
        text = clean_text(full_text)
    else:
        text = read_tender(url)

    if not text:
        logger.warning("  No readable text")
        return None

    logger.info(f"  {len(text):,} chars extracted")

    combined = text + "\n\n" + tender.get("snippet", "")
    raw = extract_key_details(combined, target_keyword=target_keyword)

    keep, val_warnings = _validate(text, raw)
    if not keep:
        logger.info("  Rejected by validator (not a tender document)")
        return None

    logger.info(
        f"  relevant={raw.get('is_relevant')}  "
        f"Fee={raw.get('Tender Fee')}  EMD={raw.get('EMD')}  "
        f"Cost={raw.get('Estimated Cost')}  End={raw.get('Bid End Date')}  "
        f"Active={raw.get('is_active')}"
    )

    analysis = analyze_tender(text, raw)
    analysis["flags"] = analysis.get("flags", []) + val_warnings
    logger.info(f"  Score={analysis['score']}  Difficulty={analysis['difficulty']}")

    ui  = sanitize_for_display(raw)

    # Pass company profile to bid writer
    bid = generate_bid(ui, analysis, company_profile=company_profile)
    proposal = (bid or {}).get("proposal", "")

    # LLM-as-judge review for generated proposal quality.
    judge_review = {
        "scores": {},
        "overall_score": 0,
        "overall_score_100": 0,
        "summary": "Judge review skipped",
        "top_strength": "",
        "top_improvement": "",
    }
    if proposal:
        try:
            tender_summary = (
                f"Title: {title}\n"
                f"Organization: {ui.get('Organization', 'Refer to PDF')}\n"
                f"Location: {ui.get('Location', 'Refer to PDF')}\n"
                f"Bid End Date: {ui.get('Bid End Date', 'Refer to PDF')}\n"
                f"Estimated Cost: {ui.get('Estimated Cost', 'Refer to PDF')}"
            )
            judge_review = asyncio.run(
                evaluate_bid(
                    tender_summary=tender_summary,
                    bid_proposal=proposal,
                    model_name="gemini",
                )
            )
        except Exception as e:
            logger.warning(f"  Judge evaluation failed: {e}")

    return {
        "tender":   {"title": title, "url": url, "snippet": tender.get("snippet", "")},
        "raw_data": raw,
        "ui_data":  ui,
        "analysis": analysis,
        "bid":      bid,
        "judge_review": judge_review,
    }