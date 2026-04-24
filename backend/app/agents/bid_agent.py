import time
import logging

logger = logging.getLogger("bidgenius.bid_agent")


def generate_bid(ui_details, analysis, company_profile=None):
    """
    Generate a bid proposal personalised to the company profile.
    Tries LLM twice (with key rotation handling), then structured fallback.
    """
    cp = company_profile or {}
    company_name = cp.get("company_name", "Our Company")

    try:
        proposal = _try_llm(ui_details, analysis, cp)
        if proposal:
            return {"proposal": proposal}

        logger.warning("First bid attempt returned empty — retrying after 3s...")
        time.sleep(3)
        proposal = _try_llm(ui_details, analysis, cp)
        if proposal:
            return {"proposal": proposal}

    except Exception as e:
        logger.error(f"Bid LLM error: {e}")

    logger.warning("Both LLM attempts failed — using structured fallback")
    return {"proposal": _fallback(ui_details, analysis, cp)}


def _try_llm(ui_details, analysis, cp):
    try:
        from app.llm.llm_router import generate

        company_name = cp.get("company_name", "Our Company")
        company_type = cp.get("company_type", "infrastructure")
        turnover     = cp.get("turnover_cr", "")
        experience   = cp.get("experience_yrs", "")
        certs        = cp.get("certifications", "")
        past         = cp.get("past_projects", "")

        # Compact tender context
        ctx = []
        for f in ["Organization", "Ministry", "Location", "Estimated Cost",
                  "EMD", "Tender Fee", "Bid End Date", "Turnover"]:
            v = ui_details.get(f)
            if v and v != "Refer to PDF":
                ctx.append(f"{f}: {v}")
        context = "\n".join(ctx) if ctx else "Details: refer to tender PDF"

        summary  = (analysis.get("summary") or "")[:300]
        category = analysis.get("fields_found", {}).get("primary_category", "infrastructure work")

        company_ctx = f"""Company: {company_name}
Sector: {company_type}
Annual Turnover: ₹{turnover} Crore
Experience: {experience} years
Certifications: {certs or 'Available on request'}
Past Projects: {past or 'Multiple successful government contracts'}"""

        prompt = f"""Write a professional Technical Bid Proposal for this Indian government tender.

BIDDING COMPANY:
{company_ctx}

TENDER DETAILS:
{context}
Work Category: {category}
Brief: {summary}

Write these 5 sections with ### headers. Address the procuring organization directly.
Use the company name "{company_name}" throughout. Be specific, not generic.

### Executive Summary
### Technical Approach
### Team & Qualifications
### Project Timeline
### Compliance Statement

In Compliance Statement: confirm Tender Fee payment, EMD arrangement, and turnover eligibility.
Keep each section 3-4 sentences. Professional tone. No pricing."""

        response = generate(prompt)
        if response and len(response.strip()) > 100:
            return response.strip()
        return None

    except Exception as e:
        logger.error(f"LLM bid error: {e}")
        return None


def _fallback(ui_details, analysis, cp):
    company_name = cp.get("company_name", "Our Company")
    company_type = cp.get("company_type", "")
    certs        = cp.get("certifications", "")
    experience   = cp.get("experience_yrs", "")

    def v(field):
        val = ui_details.get(field, "")
        return val if val and val != "Refer to PDF" else "as per tender document"

    return f"""### Technical Bid Proposal

**Submitted by:** {company_name}  
**For:** {v("Organization")}  
**Location:** {v("Location")}  
**Contract Value:** {v("Estimated Cost")}  
**Deadline:** {v("Bid End Date")}

---

### Executive Summary
{company_name} is pleased to submit this technical bid in response to the above tender. With {experience} years of experience in {company_type.lower() or "this sector"}, we are fully equipped to deliver the specified scope of work on time and within budget. Our team has successfully executed similar government contracts and we are committed to the highest standards of quality and compliance.

### Technical Approach
We will adopt a structured, milestone-based approach aligned with all technical specifications in the tender document. Our methodology includes thorough site assessment, detailed project planning, and staged execution with quality checkpoints at each phase. We will deploy qualified engineers and use proven techniques to ensure full specification compliance throughout the project lifecycle.

### Team & Qualifications
Our project team consists of experienced professionals holding all required qualifications for this category of work. {f'We hold {certs} certifications.' if certs else 'We are registered with all relevant statutory bodies.'} Our team has delivered similar projects for government clients and can demonstrate track records upon request.

### Project Timeline
We will submit a detailed Gantt chart with our final bid documents, showing key milestones from mobilisation through to final handover. All deliverables will be completed within the stipulated contract period with built-in contingency buffers to manage unforeseen circumstances.

### Compliance Statement
{company_name} confirms full compliance with all eligibility criteria:
- **Tender Fee:** {v("Tender Fee")} will be arranged via Demand Draft / online payment as specified
- **EMD / Tender Security:** {v("EMD")} will be submitted as Bank Guarantee / DD as required
- **Turnover Requirement:** {v("Turnover")} — our annual turnover meets or exceeds this threshold
- All required registrations, licences, and statutory compliances are in order

We undertake to abide by all terms and conditions of the tender document.

---
*Score: {analysis.get("score", 0)}/100 · Difficulty: {analysis.get("difficulty", "—")}*
"""