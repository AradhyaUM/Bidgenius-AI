import os
import re
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Dynamically set current year
CURRENT_YEAR = datetime.now().year
logger = logging.getLogger("bidgenius.search")

now          = datetime.now()
m1 = now.strftime("%B %Y")
m2 = (now + timedelta(days=30)).strftime("%B %Y")
m3 = (now + timedelta(days=60)).strftime("%B %Y")
ACTIVE_WINDOW = f'("{m1}" OR "{m2}" OR "{m3}")'

CENTRAL_PORTALS = [
    "eprocure.gov.in",
    "gem.gov.in",
    "defproc.gov.in",
    "mstcecommerce.com",
]

STATE_PORTALS = [
    "mahatenders.gov.in",
    "tender.rajasthan.gov.in",
    "tenders.telangana.gov.in",
    "etenders.kerala.gov.in",
    "tntenders.gov.in",
    "wbtenders.gov.in",
    "etenders.punjab.gov.in",
    "eproc.karnataka.gov.in",
    "mptenders.gov.in",
    "tendersodisha.gov.in",
    "etender.up.nic.in",
    "eproc.gujarat.gov.in",
    "hptenders.gov.in",
    "eproc.bihar.gov.in",
    "tenderwizard.com/CHHATTISGARH",
]

MUNICIPAL_PORTALS = [
    "mcgm.gov.in",
    "punecorporation.org",
    "nmc.gov.in",
    "nmmc.gov.in",
    "kdmc.gov.in",
    "pcmcindia.gov.in",
    "ahmedabadcity.gov.in",
    "suratmunicipal.org",
    "rajkotmunicipal.org",
    "bbmp.gov.in",
    "chennaicorporation.gov.in",
    "ghmc.gov.in",
    "mcd.gov.in",
    "ndmc.gov.in",
    "kmcgov.in",
    "nagpurcorporation.com",
]

PSU_PORTALS = [
    "ireps.gov.in",
    "nhai.gov.in",
    "rites.com",
    "nhidcl.com",
    "ntpc.co.in",
    "powergrid.in",
    "gail.co.in",
    "bpcl.in",
    "ongcindia.com",
    "bhel.com",
    "coalindia.in",
    "sail.co.in",
]

STATE_TO_PORTALS = {
    "maharashtra": ["mahatenders.gov.in", "portal.mcgm.gov.in", "pmc.gov.in", "nmcnagpur.gov.in", "nmmc.gov.in", "kdmc.gov.in", "pcmcindia.gov.in"],
    "gujarat": ["tender.nprocure.com", "ahmedabadcity.gov.in", "suratmunicipal.gov.in", "rmc.gov.in", "vmc.gov.in"],
    "karnataka": ["kppp.karnataka.gov.in", "bbmp.gov.in", "mysorecity.mrc.gov.in"],
    "tamil nadu": ["tntenders.gov.in", "chennaicorporation.gov.in", "ccmc.gov.in"],
    "telangana": ["tender.telangana.gov.in", "ghmc.gov.in", "gwmc.gov.in"],
    "west bengal": ["wbtenders.gov.in", "kmcgov.in", "hmc.org.in"],
    "uttar pradesh": ["etender.up.nic.in", "lmc.up.nic.in", "kanpurnagar.nic.in"],
    "madhya pradesh": ["mptenders.gov.in", "imcindore.mp.gov.in", "bmconline.gov.in"],
    "andhra pradesh": ["apeprocurement.gov.in"],
    "arunachal pradesh": ["arunachaltenders.gov.in"],
    "assam": ["assamtenders.gov.in"],
    "bihar": ["eproc2.bihar.gov.in"],
    "chhattisgarh": ["eproc.cgstate.gov.in"],
    "goa": ["eprocure.goa.gov.in"],
    "haryana": ["etenders.hry.nic.in"],
    "himachal pradesh": ["hptenders.gov.in"],
    "jharkhand": ["jharkhandtenders.gov.in"],
    "kerala": ["etenders.kerala.gov.in", "kochicorporation.lsgkerala.gov.in"],
    "manipur": ["manipurtenders.gov.in"],
    "meghalaya": ["meghalayatenders.gov.in"],
    "mizoram": ["mizoramtenders.gov.in"],
    "nagaland": ["nagalandtenders.gov.in"],
    "odisha": ["tendersodisha.gov.in", "bmc.gov.in"],
    "punjab": ["eproc.punjab.gov.in"],
    "rajasthan": ["eproc.rajasthan.gov.in", "jaipurmc.org"],
    "sikkim": ["sikkimtender.gov.in"],
    "tripura": ["tripuratenders.gov.in"],
    "uttarakhand": ["uktenders.gov.in"],
    "delhi": ["mcdonline.nic.in", "ndmc.gov.in"],
    "andaman and nicobar": ["eprocure.andaman.gov.in"],
    "chandigarh": ["etenders.chd.nic.in", "mcchandigarh.gov.in"],
    "dadra and nagar haveli": ["dnhtenders.gov.in"],
    "daman and diu": ["ddtenders.gov.in"],
    "jammu and kashmir": ["jktenders.gov.in"],
    "ladakh": ["tenders.ladakh.gov.in"],
    "lakshadweep": ["tenders.lakshadweep.gov.in"],
    "puducherry": ["pudutenders.gov.in"],
}

def _looks_active(snippet):
    if not snippet:
        return True
    lower = snippet.lower()
    blacklist = [
        "awarded", "cancelled", "corrigendum for cancellation",
        "financial evaluation result", "aoc", "archive",
        "expired", "tender concluded",
    ]
    if any(x in lower for x in blacklist):
        return False
    years = [int(y) for y in re.findall(r'\b(20\d{2})\b', snippet)]
    # Allow current year and previous year (to handle financial year 2025-26)
    if years and max(years) < CURRENT_YEAR - 1:
        return False
    return True

def _exa_search(keyword, region, scope):
    try:
        from exa_py import Exa
        api_key = os.getenv("EXA_API_KEY")
        if not api_key:
            return []

        client = Exa(api_key=api_key)
        region_lower = region.lower().strip()

        if scope == "municipal":
            domains = MUNICIPAL_PORTALS
        elif scope == "psu":
            domains = PSU_PORTALS
        elif scope == "state":
            if region_lower in STATE_TO_PORTALS:
                domains = STATE_TO_PORTALS[region_lower]
            else:
                domains = STATE_PORTALS
        elif scope == "central":
            domains = CENTRAL_PORTALS
        else:
            if region_lower in STATE_TO_PORTALS:
                domains = CENTRAL_PORTALS + STATE_TO_PORTALS[region_lower]
            else:
                domains = ["gov.in"] + [p for p in MUNICIPAL_PORTALS if not p.endswith(".gov.in")]

        queries = [
            f"{keyword} tender {region} notice inviting tender",
            f"{keyword} bid document {region}",
        ]

        results = []
        seen = set()

        for query in queries:
            print(f"\n🔵 Exa: {query[:80]}")
            try:
                response = client.search_and_contents(
                    query,
                    type="auto",
                    include_domains=domains,
                    text={"max_characters": 8000},
                    num_results=8,
                )
                for r in response.results:
                    url = r.url or ""
                    if url in seen:
                        continue
                    text_content = getattr(r, 'text', '') or ''
                    snippet = (text_content[:500] if text_content
                               else (getattr(r, 'highlights', [''])[0]
                                     if hasattr(r, 'highlights') else ''))
                    if not _looks_active(snippet):
                        print(f"   ⏭ Stale: {getattr(r,'title','')[:50]}")
                        continue
                    seen.add(url)
                    results.append({
                        "title":     getattr(r, 'title', 'Untitled') or 'Untitled',
                        "url":       url,
                        "snippet":   snippet,
                        "full_text": text_content,
                        "is_pdf":    ".pdf" in url.lower(),
                        "source":    "exa",
                    })
            except Exception as e:
                print(f"   ❌ Exa query error: {e}")

        print(f"   ✅ Exa: {len(results)} results")
        return results

    except ImportError:
        print("⚠️ exa-py not installed: pip install exa-py")
        return []
    except Exception as e:
        print(f"❌ Exa failed: {e}")
        return []

def _tavily_search(keyword, region, scope):
    try:
        from tavily import TavilyClient
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return []

        client = TavilyClient(api_key=api_key)
        region_lower = region.lower().strip()

        if scope == "municipal":
            portals = MUNICIPAL_PORTALS[:6]
        elif scope == "psu":
            portals = PSU_PORTALS[:6]
        elif scope == "state":
            if region_lower in STATE_TO_PORTALS:
                portals = STATE_TO_PORTALS[region_lower][:6]
            else:
                portals = STATE_PORTALS[:6]
        elif scope == "central":
            portals = CENTRAL_PORTALS
        else:
            if region_lower in STATE_TO_PORTALS:
                portals = CENTRAL_PORTALS[:2] + STATE_TO_PORTALS[region_lower][:4]
            else:
                portals = CENTRAL_PORTALS[:2] + STATE_PORTALS[:2] + MUNICIPAL_PORTALS[:2]

        portal_filter = " OR ".join(f"site:{p}" for p in portals[:6])
        procedural    = '(NIT OR RFP OR RFQ OR EOI OR "Notice Inviting Tender")'
        closing_terms = '("Last Date" OR "Due Date" OR "Bid End Date" OR "Submission Deadline")'

        queries = [
            f'"{keyword}" {procedural} {region} pdf',
            f'"{keyword}" {closing_terms} {region} pdf',
            f'"{keyword}" ({portal_filter})',
            f'"{keyword}" tender {region} pdf',
        ]

        results = []
        seen = set()

        for query in queries:
            print(f"\n🟡 Tavily: {query[:80]}")
            try:
                response = client.search(query=query, max_results=8,
                                         search_depth="advanced")
                for r in response.get("results", []):
                    url     = r.get("url", "")
                    snippet = r.get("content", "")
                    if url in seen:
                        continue
                    if ".pdf" not in url.lower() and "DownloadFile" not in url:
                        continue
                    if not _looks_active(snippet):
                        print(f"   ⏭ Stale: {r.get('title','')[:50]}")
                        continue
                    seen.add(url)
                    results.append({
                        "title":     r.get("title", "Untitled"),
                        "url":       url,
                        "snippet":   snippet,
                        "full_text": "",
                        "is_pdf":    True,
                        "source":    "tavily",
                    })
            except Exception as e:
                print(f"   ❌ Tavily query error: {e}")

        print(f"   ✅ Tavily: {len(results)} results")
        return results

    except Exception as e:
        print(f"❌ Tavily failed: {e}")
        return []

def search_tenders(keyword, region, scope="all"):
    print(f"\n🔍 Dual search: '{keyword}' | '{region}' | [{scope}]")

    exa_results    = _exa_search(keyword, region, scope)
    tavily_results = _tavily_search(keyword, region, scope)

    seen, merged = set(), []
    for r in exa_results + tavily_results:
        url = r.get("url", "")
        if url and url not in seen:
            seen.add(url)
            merged.append(r)

    merged.sort(key=lambda x: len(x.get("full_text", "")), reverse=True)

    print(f"\n✅ Combined: {len(merged)} unique "
          f"({sum(1 for r in merged if r['source']=='exa')} Exa / "
          f"{sum(1 for r in merged if r['source']=='tavily')} Tavily)")

    return merged[:8]

def get_active_tenders_list(keyword, region, scope="all", max_results=15):
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        region_lower = region.lower().strip()
        
        portal_filter = ""
        if region_lower in STATE_TO_PORTALS:
            portals = CENTRAL_PORTALS[:2] + STATE_TO_PORTALS[region_lower][:4]
            portal_filter = " (" + " OR ".join(f"site:{p}" for p in portals) + ")"

        queries = [
            f'"{keyword}" (tender OR NIT OR RFP) {region} {CURRENT_YEAR} active{portal_filter}',
            f'"{keyword}" government tender {region} "last date" {CURRENT_YEAR}',
            f'"{keyword}" "municipal corporation" tender {region} {CURRENT_YEAR}',
        ]
        seen, results = set(), []
        for query in queries:
            try:
                resp = client.search(query=query, max_results=10)
                for r in resp.get("results", []):
                    url = r.get("url", "")
                    if url in seen or not _looks_active(r.get("content", "")):
                        continue
                    seen.add(url)
                    results.append({
                        "title":   r.get("title", "Untitled"),
                        "url":     url,
                        "snippet": r.get("content", ""),
                        "is_pdf":  ".pdf" in url.lower(),
                    })
            except Exception:
                pass
        return results[:max_results]
    except Exception:
        return []