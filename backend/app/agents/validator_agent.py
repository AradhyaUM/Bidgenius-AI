"""
Validator Agent — v2
====================
Lesson learned: be permissive, not strict.
A false negative (rejecting a real tender) is worse than a false positive
(showing a slightly wrong result). The user can always check the PDF.

Only reject documents that are OBVIOUSLY not tenders.
Only null out financial values that are OBVIOUSLY wrong (single digits).
"""
import re
from datetime import datetime


# ── HARD REJECTION — only the most obvious non-tender documents ──────────────
# These patterns appearing together (not alone) signal a non-tender document.
# A single signal is NOT enough to reject.

COURT_SIGNALS = [
    r'\bcnr\s*no\b',           # CNR No. — court case reference number
    r'\bpetitioner\b',
    r'\brespondent\b',
    r'\bwrit\s+petition\b',
    r'\bfir\s+no\b',
    r'\bhon.?ble\s+court\b',
    r'\bjudgment\b',
]

NEWS_SIGNALS = [
    r'\bby\s+our\s+correspondent\b',
    r'\bspecial\s+correspondent\b',
    r'\bnews\s+desk\b',
]

FINANCIAL_REPORT_SIGNALS = [
    r'\bbalance\s+sheet\b',
    r'\bprofit\s+and\s+loss\b',
    r'\bshareholder\b',
    r'\bdividend\b',
    r'\bauditor.s\s+report\b',
]

# Any TENDER signal — if even one is present, keep the document
TENDER_SIGNALS = [
    r'\btender\b', r'\b(n\.?i\.?t\.?|notice\s+inviting\s+tender)\b',
    r'\brfp\b', r'\brfq\b', r'\beoi\b', r'\bbid\b',
    r'\bprocurement\b', r'\bemd\b', r'\bearnest\s+money\b',
    r'\btendering\b', r'\bbidder\b', r'\bsubmission\s+of\s+bid\b',
    r'\bnivida\b', r'\btendar\b',
]


def _is_likely_tender(text):
    """
    Returns (keep: bool, reason: str)
    
    Logic:
    - If ANY tender signal found → keep (return True immediately)
    - If 3+ court signals with NO tender signal → reject
    - If 3+ financial report signals with NO tender signal → reject
    - Otherwise → keep (benefit of the doubt)
    """
    lower = text[:8000].lower()

    # Check for tender signals first — if found, immediately keep
    for pat in TENDER_SIGNALS:
        if re.search(pat, lower):
            return True, "Tender signal found"

    # No tender signals at all — now check for definitive non-tender patterns
    court_hits = sum(1 for p in COURT_SIGNALS if re.search(p, lower))
    if court_hits >= 3:
        return False, f"Court document ({court_hits} court signals, no tender signals)"

    news_hits = sum(1 for p in NEWS_SIGNALS if re.search(p, lower))
    if news_hits >= 2:
        return False, "News article (no tender signals)"

    fin_hits = sum(1 for p in FINANCIAL_REPORT_SIGNALS if re.search(p, lower))
    if fin_hits >= 3:
        return False, "Financial report (no tender signals)"

    # Benefit of the doubt — keep it
    return True, "Keeping (no clear rejection signal)"


# ── FINANCIAL PLAUSIBILITY — only reject obviously wrong values ───────────────
def _clean_financials(details):
    """
    Only nulls out values that are OBVIOUSLY wrong:
    - Single digit values (1, 2, 3) — clearly list indexes
    - Negative values
    Does NOT reject based on EMD/cost ratios — too many edge cases.
    """
    warnings = []

    def to_int(v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    for field in ("EMD", "Tender Fee", "Estimated Cost", "Turnover"):
        val = to_int(details.get(field))
        if val is None:
            continue
        # Only reject single/double digit values — these are list indexes
        if 0 < val < 50:
            warnings.append(
                f"{field} value ₹{val} looks like a list index, not a real amount — "
                "check original PDF"
            )
            details[field] = None
        elif val < 0:
            details[field] = None

    return warnings


# ── DATE PLAUSIBILITY ─────────────────────────────────────────────────────────
def _clean_dates(details):
    warnings = []
    now = datetime.now()

    def parse(s):
        if not s:
            return None
        for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        return None

    end_dt = parse(details.get("Bid End Date"))

    # End date more than 3 years in future — almost certainly wrong
    if end_dt and (end_dt - now).days > 1095:
        warnings.append(
            f"Bid End Date {details['Bid End Date']} is more than 3 years away — "
            "likely a parse error, check PDF"
        )
        details["Bid End Date"] = None
        details["is_active"]    = None

    return warnings


# ── MAIN VALIDATOR ────────────────────────────────────────────────────────────
def validate_tender(text, details, title=""):
    """
    Validates extracted tender data.
    
    Philosophy: permissive. Only reject/warn when something is clearly wrong.
    A tender with missing fields is still useful — user can open the PDF.
    """
    warnings = []

    # 1. Document type check (permissive)
    keep, reason = _is_likely_tender(text)
    if not keep:
        return {
            "is_valid":         False,
            "rejection_reason": reason,
            "warnings":         [],
            "cleaned_details":  details,
        }

    # 2. Clean obviously wrong financial values
    fin_warnings = _clean_financials(details)
    warnings.extend(fin_warnings)

    # 3. Clean obviously wrong dates
    date_warnings = _clean_dates(details)
    warnings.extend(date_warnings)

    return {
        "is_valid":         True,
        "rejection_reason": None,
        "warnings":         warnings,
        "cleaned_details":  details,
    }