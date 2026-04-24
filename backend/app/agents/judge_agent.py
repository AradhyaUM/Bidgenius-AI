# judge_agent.py — v2 (deployed 2026-04-25)
import json
from typing import Dict, Any


JUDGE_SYSTEM_PROMPT = """You are a senior Government Tender Evaluator. Your job is to score AI-generated bid proposals against a structured rubric.

RULES:
- Score each criterion independently on a scale of 1 to 5.
- Base your scores ONLY on the provided outputs.
- Return ONLY a valid JSON object.
- Do NOT include markdown or explanation outside JSON.
"""


JUDGE_EVAL_PROMPT = """Evaluate this Bid Proposal pipeline output.

=== TENDER SUMMARY ===
{tender_summary}

=== BID PROPOSAL ===
{bid_proposal}

=== RUBRIC ===

1. TENDER ALIGNMENT (1-5)
2. COMPLIANCE & FEASIBILITY (1-5)
3. PROFESSIONAL TONE (1-5)
4. STRATEGY QUALITY (1-5)
5. REPORT COMPLETENESS (1-5)

=== REQUIRED OUTPUT FORMAT ===
{{
  "scores": {{
    "tender_alignment": {{"score": 5, "reasoning": ""}},
    "compliance_feasibility": {{"score": 5, "reasoning": ""}},
    "professional_tone": {{"score": 5, "reasoning": ""}},
    "strategy_quality": {{"score": 5, "reasoning": ""}},
    "report_completeness": {{"score": 5, "reasoning": ""}}
  }},
  "overall_score": 5.0,
  "summary": "",
  "top_strength": "",
  "top_improvement": ""
}}
"""


def _safe_parse(response: Any) -> Dict:
    """Safely parse LLM JSON output"""
    try:
        if isinstance(response, str):
            return json.loads(response)
        return response
    except Exception:
        return {
            "scores": {},
            "overall_score": 0,
            "summary": "Evaluation failed (invalid JSON)",
            "top_strength": "",
            "top_improvement": "Retry evaluation"
        }


def _compute_overall(scores: Dict) -> float:
    """Compute average score (more reliable than trusting LLM)"""
    try:
        values = [v["score"] for v in scores.values() if "score" in v]
        if not values:
            return 0
        return round(sum(values) / len(values), 2)
    except Exception:
        return 0


def _normalize_100(score_5: float) -> int:
    """Convert 0–5 → 0–100"""
    return int((score_5 / 5) * 100)


async def evaluate_bid(
    tender_summary: str,
    bid_proposal: str,
    model_name: str = "gemini"
) -> Dict:
    """Judge Agent: evaluates proposal quality"""

    if not bid_proposal or not bid_proposal.strip():
        return {
            "scores": {},
            "overall_score": 0,
            "overall_score_100": 0,
            "summary": "No proposal generated",
            "top_strength": "",
            "top_improvement": "Generate proposal first"
        }

    prompt = JUDGE_EVAL_PROMPT.format(
        tender_summary=tender_summary[:2000],   # prevent token overflow
        bid_proposal=bid_proposal[:6000]
    )

    # Retry logic
    for _ in range(2):
        try:
            from app.llm.llm_router import generate
            response = generate(JUDGE_SYSTEM_PROMPT + "\n\n" + prompt)

            result = _safe_parse(response)

            # recompute score (do NOT trust LLM blindly)
            computed = _compute_overall(result.get("scores", {}))
            result["overall_score"] = computed
            result["overall_score_100"] = _normalize_100(computed)

            return result

        except Exception:
            continue

    return {
        "scores": {},
        "overall_score": 0,
        "overall_score_100": 0,
        "summary": "Evaluation failed after retries",
        "top_strength": "",
        "top_improvement": "Retry later"
    }