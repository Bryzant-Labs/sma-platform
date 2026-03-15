"""bioRxiv/medRxiv adapter — Agent A of the Agentic Research Swarm.

Scans both preprint servers for SMA-relevant papers using the bioRxiv REST API.
API docs: https://api.biorxiv.org/
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# bioRxiv/medRxiv API base URL
_API_BASE = "https://api.biorxiv.org/details"

# Keywords to match in title or abstract (lowercased for comparison)
SMA_KEYWORDS = [
    "spinal muscular atrophy",
    "smn1",
    "smn2",
    "motor neuron",
    "nusinersen",
    "risdiplam",
    "onasemnogene",
    "gene therapy sma",
]

# Maximum results to fetch per server per cursor page
_PAGE_SIZE = 100

# HTTP client settings
_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
_MAX_RETRIES = 3


def _is_relevant(title: str, abstract: str) -> tuple[bool, float]:
    """Return (is_relevant, relevance_score) based on keyword hits.

    Scoring:
    - Each unique keyword match contributes 1.0 / len(SMA_KEYWORDS)
    - Title matches are weighted 2x vs abstract matches
    """
    title_lower = title.lower()
    abstract_lower = abstract.lower()

    hits = 0
    title_hits = 0
    for kw in SMA_KEYWORDS:
        in_title = kw in title_lower
        in_abstract = kw in abstract_lower
        if in_title:
            hits += 2
            title_hits += 1
        elif in_abstract:
            hits += 1

    if hits == 0:
        return False, 0.0

    max_possible = len(SMA_KEYWORDS) * 2
    score = round(min(1.0, hits / max_possible), 4)
    return True, score


async def _fetch_server(
    server: str,
    start_date: str,
    end_date: str,
    client: httpx.AsyncClient,
) -> list[dict[str, Any]]:
    """Fetch all pages from one server (biorxiv or medrxiv) between two dates.

    Args:
        server: "biorxiv" or "medrxiv"
        start_date: ISO format YYYY-MM-DD
        end_date: ISO format YYYY-MM-DD
        client: Shared httpx async client

    Returns:
        List of raw paper dicts from the API (all pages combined)
    """
    results: list[dict[str, Any]] = []
    cursor = 0

    while True:
        url = f"{_API_BASE}/{server}/{start_date}/{end_date}/{cursor}"
        logger.debug("Fetching %s", url)

        resp = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                break
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                if attempt == _MAX_RETRIES:
                    logger.error(
                        "Failed to fetch %s after %d attempts: %s",
                        url, _MAX_RETRIES, exc,
                    )
                    return results
                logger.warning("Attempt %d failed for %s: %s — retrying", attempt, url, exc)

        if resp is None:
            return results

        data = resp.json()
        collection = data.get("collection", [])
        if not collection:
            break  # No more results

        results.extend(collection)
        logger.info("Server=%s cursor=%d fetched %d papers (total so far: %d)",
                    server, cursor, len(collection), len(results))

        # The API returns up to 100 items per page; if fewer returned, we're done
        if len(collection) < _PAGE_SIZE:
            break

        cursor += _PAGE_SIZE

    return results


def _parse_paper(raw: dict[str, Any], server: str) -> dict[str, Any]:
    """Normalise a raw API record into a structured preprint dict."""
    authors_raw = raw.get("authors", "")
    # Authors arrive as a semicolon-separated string
    authors_list = [a.strip() for a in authors_raw.split(";") if a.strip()]

    return {
        "server": server,
        "doi": raw.get("doi", ""),
        "title": raw.get("title", "").strip(),
        "authors": authors_list,
        "abstract": raw.get("abstract", "").strip(),
        "category": raw.get("category", ""),
        "posted_date": raw.get("date", ""),
        "url": f"https://doi.org/{raw.get('doi', '')}",
    }


async def scan_preprints(days_back: int = 7) -> list[dict[str, Any]]:
    """Scan bioRxiv and medRxiv for SMA-relevant preprints posted in the last N days.

    Args:
        days_back: How many days back to search (default 7)

    Returns:
        List of structured preprint dicts filtered to SMA relevance, each with:
        server, doi, title, authors (list), abstract, category, posted_date,
        url, relevance_score
    """
    today = date.today()
    start = (today - timedelta(days=days_back)).isoformat()
    end = today.isoformat()

    logger.info("Scanning bioRxiv+medRxiv for SMA preprints: %s → %s", start, end)

    relevant: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
        for server in ("biorxiv", "medrxiv"):
            try:
                raw_papers = await _fetch_server(server, start, end, client)
            except Exception as exc:
                logger.error("Unexpected error scanning %s: %s", server, exc, exc_info=True)
                continue

            logger.info("Server=%s raw papers in date range: %d", server, len(raw_papers))

            for raw in raw_papers:
                paper = _parse_paper(raw, server)
                is_rel, score = _is_relevant(paper["title"], paper["abstract"])
                if not is_rel:
                    continue
                paper["relevance_score"] = score
                relevant.append(paper)

    # Sort by relevance score descending
    relevant.sort(key=lambda p: p["relevance_score"], reverse=True)

    logger.info(
        "scan_preprints(days_back=%d): %d SMA-relevant preprints found",
        days_back, len(relevant),
    )
    return relevant
