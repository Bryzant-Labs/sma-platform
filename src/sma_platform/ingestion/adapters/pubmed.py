"""PubMed adapter using NCBI E-utilities.

Searches PubMed for disease-related papers and retrieves structured metadata.
Uses Biopython's Entrez module for reliable API access.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date
from typing import Any

from Bio import Entrez

from ...core.config import settings
from ...core.disease_config import get_disease_pubmed_queries, get_disease_short_name

logger = logging.getLogger(__name__)

_MONTH_MAP = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}


def _normalise_date(year: str, month: str, day: str) -> str | None:
    """Convert PubMed date parts to ISO YYYY-MM-DD, or None if unusable."""
    if not year or not year.isdigit():
        return None
    m = _MONTH_MAP.get(month.lower()[:3], month.zfill(2) if month.isdigit() else "01")
    d = day.zfill(2) if day.isdigit() else "01"
    return f"{year}-{m}-{d}"

# Configure Entrez
Entrez.email = settings.ncbi_email
Entrez.tool = settings.ncbi_tool
if settings.ncbi_api_key:
    Entrez.api_key = settings.ncbi_api_key

# Disease-specific PubMed queries (loaded from disease_config)
def _get_queries() -> list[str]:
    return get_disease_pubmed_queries()


async def _entrez_search(
    query: str,
    max_results: int,
    min_date: str = "",
    max_date: str = "",
) -> list[str]:
    """Run Entrez search in a thread to avoid blocking the event loop."""
    def _search() -> list[str]:
        params: dict[str, Any] = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "usehistory": "y",
        }
        if min_date:
            params["mindate"] = min_date
            params["maxdate"] = max_date
            params["datetype"] = "pdat"
        handle = Entrez.esearch(**params)
        record = Entrez.read(handle)
        handle.close()
        return record.get("IdList", [])

    return await asyncio.to_thread(_search)


async def _entrez_fetch(pmids: list[str]) -> list:
    """Run Entrez fetch in a thread to avoid blocking the event loop."""
    def _fetch() -> list:
        handle = Entrez.efetch(
            db="pubmed", id=",".join(pmids), rettype="xml", retmode="xml"
        )
        records = Entrez.read(handle)
        handle.close()
        return records.get("PubmedArticle", [])

    return await asyncio.to_thread(_fetch)


async def search_pubmed(
    query: str,
    max_results: int = 100,
    min_date: str | None = None,
    max_date: str | None = None,
) -> list[str]:
    """Search PubMed and return list of PMIDs.

    Args:
        query: PubMed search query
        max_results: Maximum number of results
        min_date: Minimum date (YYYY/MM/DD)
        max_date: Maximum date (YYYY/MM/DD)

    Returns:
        List of PMID strings
    """
    pmids = await _entrez_search(
        query=query,
        max_results=max_results,
        min_date=min_date or "",
        max_date=max_date or "",
    )
    logger.info("PubMed search '%s...' returned %d results", query[:60], len(pmids))
    return pmids


async def fetch_paper_details(pmids: list[str]) -> list[dict[str, Any]]:
    """Fetch detailed metadata for a list of PMIDs.

    Returns list of dicts with: pmid, title, authors, journal, pub_date, doi, abstract
    """
    if not pmids:
        return []

    raw_articles = await _entrez_fetch(pmids)

    papers = []
    for article in raw_articles:
        medline = article.get("MedlineCitation", {})
        art = medline.get("Article", {})

        # Extract PMID
        pmid = str(medline.get("PMID", ""))

        # Extract authors
        author_list = art.get("AuthorList", [])
        authors = []
        for a in author_list:
            last = a.get("LastName", "")
            first = a.get("ForeName", "")
            if last:
                authors.append(f"{last} {first}".strip())

        # Extract pub date
        pub_date_raw = art.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})
        year = pub_date_raw.get("Year", "")
        month = pub_date_raw.get("Month", "01")
        day = pub_date_raw.get("Day", "01")

        # Extract DOI
        doi = ""
        for eid in art.get("ELocationID", []):
            if str(eid.attributes.get("EIdType", "")) == "doi":
                doi = str(eid)

        # Extract abstract
        abstract_parts = art.get("Abstract", {}).get("AbstractText", [])
        abstract = " ".join(str(p) for p in abstract_parts)

        papers.append({
            "pmid": pmid,
            "title": str(art.get("ArticleTitle", "")),
            "authors": authors,
            "journal": art.get("Journal", {}).get("Title", ""),
            "pub_date": _normalise_date(year, month, day),
            "doi": doi,
            "abstract": abstract,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })

    logger.info(f"Fetched details for {len(papers)}/{len(pmids)} papers")
    return papers


async def search_recent_sma(days_back: int = 7, max_per_query: int = 50) -> list[dict[str, Any]]:
    """Search all disease-specific queries for recent papers.

    This is the main daily ingestion entry point.
    """
    today = date.today()
    from datetime import timedelta
    min_date = (today - timedelta(days=days_back)).strftime("%Y/%m/%d")
    max_date = today.strftime("%Y/%m/%d")

    all_pmids: set[str] = set()
    queries = _get_queries()
    for query in queries:
        pmids = await search_pubmed(query, max_results=max_per_query, min_date=min_date, max_date=max_date)
        all_pmids.update(pmids)
        # NCBI rate limit: 3 req/sec without API key, 10 req/sec with key
        await asyncio.sleep(0.35)

    logger.info(f"Total unique PMIDs from {len(queries)} queries: {len(all_pmids)}")

    if not all_pmids:
        return []

    return await fetch_paper_details(list(all_pmids))
