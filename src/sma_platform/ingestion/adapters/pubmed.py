"""PubMed adapter using NCBI E-utilities.

Searches PubMed for SMA-related papers and retrieves structured metadata.
Uses Biopython's Entrez module for reliable API access.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from Bio import Entrez

from ...core.config import settings

logger = logging.getLogger(__name__)

# Configure Entrez
Entrez.email = settings.ncbi_email
Entrez.tool = settings.ncbi_tool
if settings.ncbi_api_key:
    Entrez.api_key = settings.ncbi_api_key

# Base SMA search queries
SMA_QUERIES = [
    '"spinal muscular atrophy"',
    '"SMN1" OR "SMN2" AND "spinal muscular atrophy"',
    '"STMN2" AND ("motor neuron" OR "SMA")',
    '"nusinersen" OR "Spinraza"',
    '"risdiplam" OR "Evrysdi"',
    '"onasemnogene" OR "Zolgensma"',
    '"spinal muscular atrophy" AND ("gene therapy" OR "antisense oligonucleotide")',
]


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
    params: dict[str, Any] = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "sort": "pub_date",
    }
    if min_date:
        params["mindate"] = min_date
        params["datetype"] = "pdat"
    if max_date:
        params["maxdate"] = max_date

    handle = Entrez.esearch(**params)
    record = Entrez.read(handle)
    handle.close()

    pmids = record.get("IdList", [])
    logger.info(f"PubMed search '{query[:60]}...' returned {len(pmids)} results")
    return pmids


async def fetch_paper_details(pmids: list[str]) -> list[dict[str, Any]]:
    """Fetch detailed metadata for a list of PMIDs.

    Returns list of dicts with: pmid, title, authors, journal, pub_date, doi, abstract
    """
    if not pmids:
        return []

    handle = Entrez.efetch(db="pubmed", id=",".join(pmids), rettype="xml")
    records = Entrez.read(handle)
    handle.close()

    papers = []
    for article in records.get("PubmedArticle", []):
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
            "pub_date": f"{year}-{month}-{day}" if year else None,
            "doi": doi,
            "abstract": abstract,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })

    logger.info(f"Fetched details for {len(papers)}/{len(pmids)} papers")
    return papers


async def search_recent_sma(days_back: int = 7, max_per_query: int = 50) -> list[dict[str, Any]]:
    """Search all SMA queries for recent papers.

    This is the main daily ingestion entry point.
    """
    today = date.today()
    from datetime import timedelta
    min_date = (today - timedelta(days=days_back)).strftime("%Y/%m/%d")
    max_date = today.strftime("%Y/%m/%d")

    all_pmids: set[str] = set()
    for query in SMA_QUERIES:
        pmids = await search_pubmed(query, max_results=max_per_query, min_date=min_date, max_date=max_date)
        all_pmids.update(pmids)

    logger.info(f"Total unique PMIDs from {len(SMA_QUERIES)} queries: {len(all_pmids)}")

    if not all_pmids:
        return []

    return await fetch_paper_details(list(all_pmids))
