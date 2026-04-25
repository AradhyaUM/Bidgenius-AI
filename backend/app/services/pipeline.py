import logging
from app.agents.search_agent import search_tenders, get_active_tenders_list
from app.agents.reader_agent import process_tender
from datetime import datetime, timedelta
import re

logger = logging.getLogger("bidgenius.pipeline")


def _parse_date(s):
    if not s:
        return None
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(str(s).strip(), fmt)
        except ValueError:
            continue
    return None


def _tender_id_year(tid):
    m = re.match(r'^(20\d{2})', str(tid or ''))
    return int(m.group(1)) if m else None


def _decide_active(output):
    raw = output.get("raw_data", {})
    now = datetime.now()

    end_str = raw.get("Bid End Date")
    if end_str and end_str != "Refer to PDF":
        dt = _parse_date(end_str)
        if dt:
            if dt < now:
                return False, f"Expired ({end_str})"
            return True, f"Active until {end_str}"

    tid_year = _tender_id_year(raw.get("Tender ID"))
    if tid_year and tid_year < now.year - 1:
        return False, f"Tender ID year {tid_year} is too old"

    title   = output.get("tender", {}).get("title", "")
    snippet = output.get("tender", {}).get("snippet", "")
    years   = [int(y) for y in re.findall(r'\b(20\d{2})\b', title + " " + snippet)]
    if years and max(years) < now.year - 1:
        return False, f"Latest year in metadata is {max(years)}"

    return True, "Status unknown — no end date extracted"


def run_pipeline(keyword, region, scope="all", company_profile=None):
    logger.info(f"Pipeline start — '{keyword}' | '{region}' | [{scope}]")
    company_profile = company_profile or {}

    raw_tenders = search_tenders(keyword, region, scope=scope)
    if not raw_tenders:
        logger.warning("No tenders found from search")
        return []

    logger.info(f"Search returned {len(raw_tenders)} candidates")
    results = []
    skipped = {"expired": 0, "irrelevant": 0, "unreadable": 0}

    for i, tender in enumerate(raw_tenders, 1):
        title = tender.get("title", "Untitled")[:60]
        logger.info(f"[{i}/{len(raw_tenders)}] {title}")

        # Pass company profile into process_tender so bid writer can use it
        output = process_tender(
            tender,
            target_keyword=keyword,
            company_profile=company_profile
        )

        if not output:
            skipped["unreadable"] += 1
            continue

        if output.get("raw_data", {}).get("is_relevant") is False:
            cat = output.get("raw_data", {}).get("primary_category", "unknown")
            logger.info(f"  Irrelevant — '{cat}'")
            skipped["irrelevant"] += 1
            continue

        keep, reason = _decide_active(output)
        if not keep:
            logger.info(f"  Expired — {reason}")
            skipped["expired"] += 1
            continue

        logger.info(f"  Keeping — {reason}")
        results.append(output)

    logger.info(
        f"Done — {len(results)} kept | "
        f"expired={skipped['expired']} irrelevant={skipped['irrelevant']} "
        f"unreadable={skipped['unreadable']}"
    )
    return results


def run_list_mode(keyword, region):
    logger.info(f"List mode — '{keyword}' | '{region}'")
    return get_active_tenders_list(keyword, region, max_results=15)