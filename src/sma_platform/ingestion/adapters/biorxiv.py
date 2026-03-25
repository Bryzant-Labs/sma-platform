"""bioRxiv/medRxiv adapter — Agent A of the Agentic Research Swarm.

Scans both preprint servers for SMA-relevant papers using the bioRxiv REST API.
Also fetches full-text content from bioRxiv HTML pages and Europe PMC.

API docs: https://api.biorxiv.org/
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import date, timedelta
from typing import Any
from xml.etree import ElementTree

import httpx

logger = logging.getLogger(__name__)

# bioRxiv/medRxiv API base URL
_API_BASE = "https://api.biorxiv.org/details"

# Full-text sources
_BIORXIV_HTML_BASE = "https://www.biorxiv.org/content"
_MEDRXIV_HTML_BASE = "https://www.medrxiv.org/content"
_EUROPEPMC_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
_EUROPEPMC_FULLTEXT = "https://www.ebi.ac.uk/europepmc/webservices/rest"

# Rate-limit delay between full-text requests (seconds)
_FULLTEXT_DELAY = 1.0

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


def _clean_fulltext(text: str) -> str:
    """Normalize whitespace and clean extracted full text."""
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text if len(text) > 100 else ""


def _strip_html_tags(html: str) -> str:
    """Remove HTML tags, returning plain text."""
    # Remove script and style blocks first
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<noscript[^>]*>.*?</noscript>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove tags
    html = re.sub(r"<[^>]+>", " ", html)
    # Decode common HTML entities
    html = html.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    html = html.replace("&nbsp;", " ").replace("&quot;", '"')
    html = re.sub(r"&#\d+;", " ", html)
    return html


def _extract_sections_from_html(html: str) -> str:
    """Extract structured sections from bioRxiv full-text HTML.

    Parses the HTML to find article content sections (Introduction, Methods,
    Results, Discussion) and returns clean markdown with section headers.
    """
    sections: list[str] = []

    # Try to isolate article body content -- bioRxiv uses various container classes
    body_patterns = [
        r'<div[^>]*class="[^"]*article-fulltext-content[^"]*"[^>]*>(.*?)</div>\s*(?=<div[^>]*class="[^"]*(?:sidebar|footer))',
        r'<div[^>]*class="[^"]*highwire-markup[^"]*"[^>]*>(.*?)</div>\s*(?=<div[^>]*class="[^"]*(?:sidebar|footer))',
        r'<div[^>]*class="[^"]*article[^"]*content[^"]*"[^>]*>(.*)',
        r'<div[^>]*id="(?:content|article-content)"[^>]*>(.*)',
    ]

    content_html = ""
    for pattern in body_patterns:
        match = re.search(pattern, html, flags=re.DOTALL | re.IGNORECASE)
        if match:
            content_html = match.group(1)
            break

    if not content_html:
        # Fallback: use the whole body
        body_match = re.search(r"<body[^>]*>(.*)</body>", html, flags=re.DOTALL | re.IGNORECASE)
        content_html = body_match.group(1) if body_match else html

    # Extract sections by heading tags (h1-h4)
    heading_pattern = r"<h[1-4][^>]*>(.*?)</h[1-4]>"
    heading_matches = list(re.finditer(heading_pattern, content_html, flags=re.DOTALL | re.IGNORECASE))

    if heading_matches:
        for i, heading_match in enumerate(heading_matches):
            heading_text = _strip_html_tags(heading_match.group(1)).strip()

            # Skip navigation/UI headings
            if not heading_text or len(heading_text) > 200:
                continue

            # Get content between this heading and the next
            start_pos = heading_match.end()
            end_pos = heading_matches[i + 1].start() if i + 1 < len(heading_matches) else len(content_html)
            section_html = content_html[start_pos:end_pos]

            # Extract paragraphs from section
            paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", section_html, flags=re.DOTALL | re.IGNORECASE)
            if paragraphs:
                clean_paragraphs = []
                for p in paragraphs:
                    p_text = _strip_html_tags(p).strip()
                    p_text = re.sub(r"\s+", " ", p_text)
                    if p_text and len(p_text) > 20:
                        clean_paragraphs.append(p_text)

                if clean_paragraphs:
                    sections.append(f"## {heading_text}\n\n" + "\n\n".join(clean_paragraphs))
    else:
        # No headings found -- extract all paragraphs
        paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", content_html, flags=re.DOTALL | re.IGNORECASE)
        for p in paragraphs:
            p_text = _strip_html_tags(p).strip()
            p_text = re.sub(r"\s+", " ", p_text)
            if p_text and len(p_text) > 30:
                sections.append(p_text)

    return "\n\n".join(sections)


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
                logger.warning("Attempt %d failed for %s: %s -- retrying", attempt, url, exc)

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


# ---------------------------------------------------------------------------
# Full-text extraction
# ---------------------------------------------------------------------------

async def _fetch_fulltext_biorxiv_html(
    doi: str,
    client: httpx.AsyncClient,
) -> str | None:
    """Fetch full text directly from bioRxiv/medRxiv HTML page.

    Tries the bioRxiv HTML endpoint first, then medRxiv. bioRxiv serves
    full-text at: https://www.biorxiv.org/content/{doi}v{version}.full

    Args:
        doi: The bioRxiv/medRxiv DOI (e.g. "10.1101/2024.01.15.575123")
        client: Shared httpx async client

    Returns:
        Structured markdown text with section headers, or None if unavailable.
    """
    # Try both servers -- we may not know which one hosts this DOI
    bases = [_BIORXIV_HTML_BASE, _MEDRXIV_HTML_BASE]

    for base_url in bases:
        # Try without version suffix first (redirects to latest), then v1
        url_candidates = [
            f"{base_url}/{doi}.full",
            f"{base_url}/{doi}v1.full",
        ]
        for url in url_candidates:
            try:
                resp = await client.get(url)
                if resp.status_code == 200 and len(resp.text) > 1000:
                    extracted = _extract_sections_from_html(resp.text)
                    cleaned = _clean_fulltext(extracted)
                    if cleaned:
                        logger.debug(
                            "Fetched bioRxiv HTML full text for DOI %s (%d chars)",
                            doi, len(cleaned),
                        )
                        return cleaned
            except httpx.HTTPError as exc:
                logger.debug("bioRxiv HTML fetch failed for %s: %s", url, exc)
                continue

    return None


async def _fetch_fulltext_europepmc_by_doi(
    doi: str,
    client: httpx.AsyncClient,
) -> str | None:
    """Fetch full text from Europe PMC for a bioRxiv preprint by DOI.

    Europe PMC indexes many bioRxiv preprints and provides structured XML.

    Args:
        doi: The bioRxiv/medRxiv DOI
        client: Shared httpx async client

    Returns:
        Structured markdown text with section headers, or None if unavailable.
    """
    # Step 1: Search Europe PMC for this DOI to get the PMC/source ID
    try:
        search_resp = await client.get(
            _EUROPEPMC_SEARCH,
            params={"query": f"DOI:{doi}", "format": "json", "resultType": "core"},
        )
        if search_resp.status_code != 200:
            return None

        search_data = search_resp.json()
        results = search_data.get("resultList", {}).get("result", [])
        if not results:
            return None

        # Get the first matching result
        result = results[0]
        source = result.get("source", "")
        ext_id = result.get("id", "")

        if not ext_id:
            return None

        # Step 2: Fetch full text XML
        fulltext_url = f"{_EUROPEPMC_FULLTEXT}/{ext_id}/fullTextXML"
        if source:
            fulltext_url = f"{_EUROPEPMC_FULLTEXT}/{source}/{ext_id}/fullTextXML"

        ft_resp = await client.get(fulltext_url)
        if ft_resp.status_code != 200 or len(ft_resp.text) < 200:
            return None

        # Step 3: Parse XML sections (same pattern as pmc.py)
        try:
            root = ElementTree.fromstring(ft_resp.text)
        except ElementTree.ParseError:
            return None

        sections: list[str] = []
        for body in root.iter("body"):
            for sec in body.iter("sec"):
                title_el = sec.find("title")
                title = title_el.text if title_el is not None and title_el.text else ""
                paragraphs: list[str] = []
                for p in sec.iter("p"):
                    p_text = " ".join(p.itertext()).strip()
                    if p_text:
                        paragraphs.append(p_text)
                if paragraphs:
                    if title:
                        sections.append(f"## {title}\n\n" + "\n\n".join(paragraphs))
                    else:
                        sections.append("\n\n".join(paragraphs))

        if not sections:
            # Fallback: extract all paragraph text from body
            for p in root.iter("p"):
                p_text = " ".join(p.itertext()).strip()
                if p_text and len(p_text) > 30:
                    sections.append(p_text)

        full_text = "\n\n".join(sections)
        cleaned = _clean_fulltext(full_text)
        if cleaned:
            logger.debug(
                "Fetched Europe PMC full text for DOI %s (%d chars)",
                doi, len(cleaned),
            )
        return cleaned or None

    except httpx.HTTPError as exc:
        logger.debug("Europe PMC fetch failed for DOI %s: %s", doi, exc)
        return None
    except (KeyError, ValueError) as exc:
        logger.debug("Europe PMC parse error for DOI %s: %s", doi, exc)
        return None


async def fetch_fulltext_biorxiv(doi: str) -> str | None:
    """Fetch full text for a bioRxiv/medRxiv preprint by DOI.

    Tries two sources in order:
    1. bioRxiv/medRxiv HTML page (direct scrape)
    2. Europe PMC XML (structured, if indexed)

    Args:
        doi: The bioRxiv/medRxiv DOI (e.g. "10.1101/2024.01.15.575123")

    Returns:
        Clean markdown text with section headers, or None if all sources fail.
    """
    if not doi:
        return None

    async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
        # Try bioRxiv HTML first (always available for bioRxiv preprints)
        text = await _fetch_fulltext_biorxiv_html(doi, client)
        if text:
            logger.info("Full text from bioRxiv HTML for DOI %s (%d chars)", doi, len(text))
            return text

        # Try Europe PMC (may have structured XML)
        text = await _fetch_fulltext_europepmc_by_doi(doi, client)
        if text:
            logger.info("Full text from Europe PMC for DOI %s (%d chars)", doi, len(text))
            return text

    logger.debug("No full text available for DOI %s", doi)
    return None


async def fetch_biorxiv_fulltext_batch(
    dois: list[str],
) -> dict[str, str | None]:
    """Fetch full text for a batch of bioRxiv/medRxiv DOIs with rate limiting.

    Processes DOIs sequentially with a 1-second delay between requests to
    respect rate limits. Failures are logged and returned as None.

    Args:
        dois: List of DOIs to fetch full text for.

    Returns:
        Dict mapping each DOI to its full text (str) or None if unavailable.
    """
    results: dict[str, str | None] = {}

    if not dois:
        return results

    logger.info("Starting batch full-text fetch for %d bioRxiv DOIs", len(dois))

    async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
        for i, doi in enumerate(dois):
            if not doi:
                results[doi] = None
                continue

            try:
                # Try bioRxiv HTML first
                text = await _fetch_fulltext_biorxiv_html(doi, client)

                # Fall back to Europe PMC
                if not text:
                    text = await _fetch_fulltext_europepmc_by_doi(doi, client)

                results[doi] = text
                if text:
                    logger.info(
                        "Batch [%d/%d] fetched full text for DOI %s (%d chars)",
                        i + 1, len(dois), doi, len(text),
                    )
                else:
                    logger.debug("Batch [%d/%d] no full text for DOI %s", i + 1, len(dois), doi)

            except Exception as exc:
                logger.error(
                    "Batch [%d/%d] failed for DOI %s: %s",
                    i + 1, len(dois), doi, exc, exc_info=True,
                )
                results[doi] = None

            # Rate limit: wait between requests (skip after last)
            if i < len(dois) - 1:
                await asyncio.sleep(_FULLTEXT_DELAY)

    fetched_count = sum(1 for v in results.values() if v is not None)
    logger.info(
        "Batch full-text complete: %d/%d DOIs had full text available",
        fetched_count, len(dois),
    )
    return results


async def scan_preprints(
    days_back: int = 7,
    fetch_full_text: bool = False,
) -> list[dict[str, Any]]:
    """Scan bioRxiv and medRxiv for SMA-relevant preprints posted in the last N days.

    Args:
        days_back: How many days back to search (default 7)
        fetch_full_text: If True, attempt to fetch full-text content for each
            relevant preprint found. Full text is stored under the ``full_text``
            key. Failures are logged but do not stop the scan.

    Returns:
        List of structured preprint dicts filtered to SMA relevance, each with:
        server, doi, title, authors (list), abstract, category, posted_date,
        url, relevance_score, and optionally full_text
    """
    today = date.today()
    start = (today - timedelta(days=days_back)).isoformat()
    end = today.isoformat()

    logger.info("Scanning bioRxiv+medRxiv for SMA preprints: %s -> %s", start, end)

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

    # Optionally fetch full text for each relevant preprint
    if fetch_full_text and relevant:
        logger.info("Fetching full text for %d relevant preprints", len(relevant))
        dois = [p["doi"] for p in relevant]
        fulltext_map = await fetch_biorxiv_fulltext_batch(dois)
        for paper in relevant:
            paper["full_text"] = fulltext_map.get(paper["doi"])

    return relevant
