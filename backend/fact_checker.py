import httpx
import urllib.parse
import re
from typing import Dict, Any, Tuple

# -----------------------------
# Wikipedia SEARCH (SAFE)
# -----------------------------
async def search_wikipedia(query: str) -> Tuple[str, str, str]:
    """Search Wikipedia safely using OpenSearch + REST API"""

    if not query.strip():
        return "", "", ""

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:

            # 1. Search
            search_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "opensearch",
                "search": query[:80],
                "limit": 1,
                "namespace": 0,
                "format": "json"
            }

            resp = await client.get(search_url, params=params)
            resp.raise_for_status()
            data = resp.json()

            if not data or len(data) < 2 or not data[1]:
                return "", "", ""

            title = data[1][0]

            # 2. Summary
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
            summary_resp = await client.get(summary_url)

            if summary_resp.status_code != 200:
                return title, "", ""

            summary_data = summary_resp.json()
            summary = summary_data.get("extract", "")
            page_url = summary_data.get("content_urls", {}).get("desktop", {}).get("page", "")

            return title, summary, page_url

    except Exception as e:
        print("Wikipedia error:", e)
        return "", "", ""


# -----------------------------
# SIMPLE KEYWORD FACT CHECK
# -----------------------------
def _fact_check_by_keywords(claim: str, summary: str) -> Dict[str, Any]:

    claim_words = set(re.findall(r'\b\w{4,}\b', claim.lower()))
    summary_words = set(re.findall(r'\b\w{4,}\b', summary.lower()))

    if not claim_words:
        return {"verdict": "Neutral", "confidence": 0.5, "details": "Claim too short"}

    overlap = claim_words.intersection(summary_words)
    ratio = len(overlap) / len(claim_words)

    if ratio > 0.4:
        return {
            "verdict": "Supported",
            "confidence": 0.8,
            "details": "High similarity with Wikipedia"
        }
    elif ratio > 0.15:
        return {
            "verdict": "Neutral",
            "confidence": 0.6,
            "details": "Partial similarity"
        }
    else:
        return {
            "verdict": "Neutral",
            "confidence": 0.5,
            "details": "No strong evidence"
        }


# -----------------------------
# MAIN FACT CHECK FUNCTION
# -----------------------------
def verify_claim(claim: str, summary: str, mock: bool = False) -> Dict[str, Any]:

    if not summary.strip():
        return {
            "verdict": "Neutral",
            "confidence": 0.5,
            "details": "No Wikipedia data found"
        }

    if mock:
        return _fact_check_by_keywords(claim, summary)

    return _fact_check_by_keywords(claim, summary)