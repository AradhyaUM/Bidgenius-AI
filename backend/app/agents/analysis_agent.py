from datetime import datetime

def analyze_tender(text, details):
    score = 0
    flags = []

    # ── DATA COMPLETENESS (45 pts) ─────────────
    if details.get("Bid End Date"): score += 15
    else: flags.append("Missing bid end date")

    if details.get("EMD"): score += 10
    else: flags.append("Missing EMD / Tender Security")

    if details.get("Tender Fee") is not None: score += 5 
    
    if details.get("Estimated Cost"): score += 10
    else: flags.append("Missing estimated cost")

    if details.get("Organization") or details.get("Ministry"): score += 5

    # ── ACTIVE STATUS (30 pts) ─────────────────
    is_active = details.get("is_active")
    if is_active is True:
        score += 30
    elif is_active is None:
        score += 15
        flags.append("Active status requires manual verification")
    else:
        flags.append("Tender deadline appears to have passed")

    # ── CONTENT QUALITY (25 pts) ───────────────
    if text:
        length = len(text)
        if length > 10_000: score += 10
        elif length > 3000: score += 7
        elif length > 500:  score += 3

        tl = text.lower()
        if "eligibility" in tl: score += 5
        if any(w in tl for w in ["technical", "specification", "scope of work"]): score += 5
        if any(w in tl for w in ["qualification", "experience", "criteria"]): score += 5

    # ── DIFFICULTY ────────────────────────────
    # A high score means highly detailed/structured.
    difficulty = "High" if score >= 80 else "Medium" if score >= 50 else "Low"

    # ── SUMMARY ───────────────────────────────
    summary = "Summary not available. Please refer to the original document."
    if text:
        start_idx = 0
        tl = text.lower()
        for kw in ["name of work", "scope of work", "tender for", "notice inviting", "description"]:
            idx = tl.find(kw)
            if idx != -1 and idx < 2000:
                start_idx = idx
                break
        
        # Safely extract a 500 character snippet without breaking strings
        extracted = text[start_idx: start_idx + 500].strip()
        if len(extracted) > 20:
            summary = extracted + "..."

    return {
        "summary":      summary,
        "difficulty":   difficulty,
        "score":        min(score, 100),
        "is_active":    is_active,
        "flags":        flags,
        "fields_found": {k: v for k, v in details.items() if v is not None and k != "is_active"},
    }