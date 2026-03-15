"""PubMed Central Open Access full-text fetcher.

Retrieves full paper text from Europe PMC REST API (free, no key required).
Falls back to NCBI E-utilities for PMC articles.
Uses Unpaywall as a secondary OA source for DOI-based lookups.

Rate limits: Europe PMC — generous; NCBI — 3 req/sec without API key.
"""

from __future__ import annotations

import logging
import re
from xml.etree import ElementTree

import httpx

from ...core.config import settings
from ...core.database import execute, fetch, fetchrow

logger = logging.getLogger(__name__)

EUROPEPMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"
NCBI_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
UNPAYWALL_BASE = "https://api.unpaywall.org/v2"
UNPAYWALL_EMAIL = getattr(settings, 'ncbi_email', 'christian@bryzant.com')


def _strip_xml_tags(xml_text: str) -> str:
    """Extract plain text from XML, stripping all tags."""
    try:
        # Wrap in root if needed
        if not xml_text.strip().startswith("<?xml"):
            xml_text = f"<root>{xml_text}</root>"
        root = ElementTree.fromstring(xml_text)
        return " ".join(root.itertext()).strip()
    except ElementTree.ParseError:
        # Fallback: regex strip
        return re.sub(r"<[^>]+>", " ", xml_text).strip()


def _clean_text(text: str) -> str:
    """Normalize whitespace and clean extracted text."""
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text if len(text) > 100 else ""


async def fetch_fulltext_europepmc(pmid: str) -> str | None:
    """Fetch full text from Europe PMC REST API by PMID."""
    url = f"{EUROPEPMC_BASE}/{pmid}/fullTextXML"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
            xml = resp.text
            if len(xml) < 200:
                return None

            # Extract body text sections
            try:
                root = ElementTree.fromstring(xml)
            except ElementTree.ParseError:
                return None

            sections = []
            for body in root.iter("body"):
                for sec in body.iter("sec"):
                    title_el = sec.find("title")
                    title = title_el.text if title_el is not None and title_el.text else ""
                    paragraphs = []
                    for p in sec.iter("p"):
                        p_text = " ".join(p.itertext()).strip()
                        if p_text:
                            paragraphs.append(p_text)
                    if paragraphs:
                        if title:
                            sections.append(f"## {title}\n" + "\n".join(paragraphs))
                        else:
                            sections.append("\n".join(paragraphs))

            if not sections:
                # Fallback: extract all paragraph text
                for p in root.iter("p"):
                    p_text = " ".join(p.itertext()).strip()
                    if p_text and len(p_text) > 30:
                        sections.append(p_text)

            full_text = "\n\n".join(sections)
            return _clean_text(full_text) or None

        except httpx.HTTPError as e:
            logger.debug("Europe PMC fetch failed for %s: %s", pmid, e)
            return None


async def fetch_fulltext_ncbi(pmid: str) -> str | None:
    """Fetch full text from NCBI PMC via E-utilities."""
    # First check if a PMC ID exists for this PMID
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Convert PMID to PMCID
            id_resp = await client.get(
                "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/",
                params={"ids": pmid, "format": "json"},
            )
            if id_resp.status_code != 200:
                return None

            id_data = id_resp.json()
            records = id_data.get("records", [])
            if not records or "pmcid" not in records[0]:
                return None

            pmcid = records[0]["pmcid"]

            # Fetch full text XML from PMC
            resp = await client.get(
                NCBI_EFETCH,
                params={"db": "pmc", "id": pmcid, "rettype": "xml"},
            )
            if resp.status_code != 200:
                return None

            xml = resp.text
            if len(xml) < 200:
                return None

            root = ElementTree.fromstring(xml)
            sections = []
            for body in root.iter("body"):
                for p in body.iter("p"):
                    p_text = " ".join(p.itertext()).strip()
                    if p_text and len(p_text) > 30:
                        sections.append(p_text)

            full_text = "\n\n".join(sections)
            return _clean_text(full_text) or None

        except (httpx.HTTPError, ElementTree.ParseError) as e:
            logger.debug("NCBI PMC fetch failed for %s: %s", pmid, e)
            return None


async def fetch_fulltext_unpaywall(doi: str) -> str | None:
    """Check Unpaywall for OA full-text URL and fetch it."""
    if not doi:
        return None

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            resp = await client.get(
                f"{UNPAYWALL_BASE}/{doi}",
                params={"email": UNPAYWALL_EMAIL},
            )
            if resp.status_code != 200:
                return None

            data = resp.json()
            best_oa = data.get("best_oa_location")
            if not best_oa:
                return None

            # Prefer PDF URL, then URL for scraping
            oa_url = best_oa.get("url_for_pdf") or best_oa.get("url")
            if not oa_url:
                return None

            # We can't easily parse PDFs, but if it's HTML we can extract text
            if oa_url.endswith(".pdf"):
                logger.debug("Unpaywall found PDF for %s (skipping — PDF parsing not implemented)", doi)
                return None

            # Try fetching HTML page and extracting text
            page_resp = await client.get(oa_url)
            if page_resp.status_code != 200:
                return None

            # Very basic HTML text extraction
            text = re.sub(r"<script[^>]*>.*?</script>", "", page_resp.text, flags=re.DOTALL)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", text)
            text = _clean_text(text)
            return text if text and len(text) > 500 else None

        except httpx.HTTPError as e:
            logger.debug("Unpaywall fetch failed for %s: %s", doi, e)
            return None


async def fetch_fulltext(pmid: str, doi: str | None = None) -> str | None:
    """Try all sources to get full text for a paper.

    Order: Europe PMC → NCBI PMC → Unpaywall
    """
    # Try Europe PMC first (best OA source)
    text = await fetch_fulltext_europepmc(pmid)
    if text:
        logger.info("Full text from Europe PMC for PMID %s (%d chars)", pmid, len(text))
        return text

    # Try NCBI PMC
    text = await fetch_fulltext_ncbi(pmid)
    if text:
        logger.info("Full text from NCBI PMC for PMID %s (%d chars)", pmid, len(text))
        return text

    # Try Unpaywall if we have a DOI
    if doi:
        text = await fetch_fulltext_unpaywall(doi)
        if text:
            logger.info("Full text from Unpaywall for DOI %s (%d chars)", doi, len(text))
            return text

    return None


async def fetch_all_fulltext(batch_size: int = 50) -> dict:
    """Fetch full text for all sources that don't have it yet.

    Returns stats dict with counts.
    """
    rows = await fetch(
        """SELECT id, external_id, doi FROM sources
           WHERE source_type = 'pubmed'
             AND full_text IS NULL
             AND abstract IS NOT NULL
           ORDER BY pub_date DESC NULLS LAST
           LIMIT $1""",
        batch_size,
    )

    fetched = 0
    skipped = 0
    errors = 0

    for row in rows:
        r = dict(row)
        try:
            text = await fetch_fulltext(r["external_id"], r.get("doi"))
            if text:
                await execute(
                    "UPDATE sources SET full_text = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2",
                    text, r["id"],
                )
                fetched += 1
            else:
                skipped += 1
        except Exception as e:
            logger.error("Failed to fetch full text for %s: %s", r["external_id"], e)
            errors += 1

    logger.info("Full text: fetched=%d skipped=%d errors=%d (of %d checked)", fetched, skipped, errors, len(rows))
    return {
        "checked": len(rows),
        "fetched": fetched,
        "skipped": skipped,
        "errors": errors,
    }
