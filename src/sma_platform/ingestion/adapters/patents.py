"""Patent literature adapter for disease-related inventions.

Searches Google Patents (via the internal XHR API) for disease-relevant patents
including gene therapy, antisense oligonucleotides, splicing modifiers,
and small molecule interventions.

This uses the public Google Patents search endpoint which returns JSON results.
No API key required. Rate limit: be respectful (2s between requests).
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import httpx

from ...core.disease_config import get_disease_config

logger = logging.getLogger(__name__)

# Google Patents XHR endpoint — public, returns JSON
GOOGLE_PATENTS_XHR = "https://patents.google.com/xhr/query"

# Disease-specific patent search queries (derived from disease_config)
def _build_patent_queries() -> list[str]:
    """Build patent queries from disease config: name, targets, drugs."""
    cfg = get_disease_config()
    queries: list[str] = []
    queries.append(cfg["name"])
    # Top target symbols joined
    symbols = [t["symbol"] for t in cfg.get("targets", [])[:5]]
    if symbols:
        queries.append(" ".join(symbols) + " " + cfg["short_name"])
    # Drug names
    for d in cfg.get("drugs", [])[:5]:
        queries.append(d["name"] + " " + cfg["short_name"])
    return queries


_SMA_SEARCH_QUERIES: list[str] | None = None

def _get_patent_queries() -> list[str]:
    global _SMA_SEARCH_QUERIES
    if _SMA_SEARCH_QUERIES is None:
        _SMA_SEARCH_QUERIES = _build_patent_queries()
    return _SMA_SEARCH_QUERIES


def _strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    return re.sub(r"<[^>]+>", "", text).strip()


def _parse_patent_result(result: dict[str, Any]) -> dict[str, Any] | None:
    """Parse a single patent result from Google Patents XHR response."""
    patent_data = result.get("patent", {})
    if not patent_data:
        return None

    patent_id_raw = result.get("id", "")
    # id format: "patent/US20240000886A1/en"
    parts = patent_id_raw.split("/")
    patent_id = parts[1] if len(parts) >= 2 else patent_id_raw

    title = _strip_html(patent_data.get("title", ""))
    snippet = _strip_html(patent_data.get("snippet", ""))

    # Extract filing/publication info from the patent data
    filing_date = patent_data.get("filing_date", "")
    pub_date = patent_data.get("publication_date", "")
    priority_date = patent_data.get("priority_date", "")
    assignee = patent_data.get("assignee", "")
    inventor = patent_data.get("inventor", "")

    return {
        "patent_id": patent_id,
        "title": title,
        "abstract": snippet,
        "grant_date": pub_date,
        "filing_date": filing_date or priority_date,
        "assignees": [assignee] if assignee else [],
        "inventors": [inventor] if inventor else [],
        "url": f"https://patents.google.com/patent/{patent_id}/en",
    }


async def search_patents(
    query: str,
    num_results: int = 50,
) -> list[dict[str, Any]]:
    """Search Google Patents for patents matching a text query.

    Args:
        query: Free-text search query.
        num_results: Maximum results to return (max 100).

    Returns:
        List of patent dicts with structured metadata.
    """
    params = {
        "url": f"q={query.replace(' ', '+')}&num={min(num_results, 100)}&oq={query.replace(' ', '+')}",
    }

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            resp = await client.get(GOOGLE_PATENTS_XHR, params=params)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Google Patents HTTP %d for query '%s': %s",
                exc.response.status_code,
                query[:60],
                exc.response.text[:300],
            )
            return []
        except httpx.RequestError as exc:
            logger.error("Google Patents request error for '%s': %s", query[:60], exc)
            return []

    try:
        data = resp.json()
    except Exception:
        logger.error("Google Patents returned non-JSON for '%s'", query[:60])
        return []

    results_obj = data.get("results", {})
    clusters = results_obj.get("cluster", [])

    patents: list[dict[str, Any]] = []
    for cluster in clusters:
        for result in cluster.get("result", []):
            parsed = _parse_patent_result(result)
            if parsed and parsed["title"]:
                patents.append(parsed)

    logger.info(
        "Google Patents: %d results for '%s'",
        len(patents),
        query[:60],
    )
    return patents


async def fetch_all_sma_patents() -> list[dict[str, Any]]:
    """Fetch all disease-related patents across multiple search strategies.

    Deduplicates by patent_id across all queries.

    Returns:
        List of unique patent dicts sorted by publication date descending.
    """
    seen: set[str] = set()
    all_patents: list[dict[str, Any]] = []

    queries = _get_patent_queries()
    for i, query in enumerate(queries):
        results = await search_patents(query, num_results=100)
        for patent in results:
            pid = patent.get("patent_id", "")
            if pid and pid not in seen:
                seen.add(pid)
                all_patents.append(patent)

        logger.debug(
            "Patent query %d/%d ('%s'): %d results, %d unique total",
            i + 1,
            len(queries),
            query[:40],
            len(results),
            len(all_patents),
        )
        # Be respectful with rate limiting
        await asyncio.sleep(2.0)

    # Sort by grant/publication date descending
    all_patents.sort(key=lambda p: p.get("grant_date") or "", reverse=True)

    logger.info(
        "fetch_all_sma_patents: %d unique patents from %d queries",
        len(all_patents),
        len(queries),
    )
    return all_patents


def build_patent_summary(patent: dict[str, Any]) -> str:
    """Build a plain-text summary of a patent for LLM claim extraction.

    The summary mirrors the format used by clinicaltrials.py so the
    claim_extractor can process it uniformly.

    Args:
        patent: A patent dict from ``search_patents()``.

    Returns:
        Multi-line plain-text string.
    """
    lines: list[str] = []

    title = patent.get("title", "Untitled")
    pid = patent.get("patent_id", "unknown")
    lines.append(f"Patent {pid}: {title}")

    assignees = patent.get("assignees", [])
    if assignees and assignees[0]:
        lines.append(f"Assignee(s): {', '.join(a for a in assignees[:5] if a)}")

    inventors = patent.get("inventors", [])
    if inventors and inventors[0]:
        lines.append(f"Inventor(s): {', '.join(v for v in inventors[:5] if v)}")

    grant = patent.get("grant_date")
    filing = patent.get("filing_date")
    if grant:
        lines.append(f"Published: {grant}")
    if filing:
        lines.append(f"Filed: {filing}")

    abstract = patent.get("abstract", "")
    if abstract:
        lines.append(f"Abstract: {abstract}")

    return "\n".join(lines)
