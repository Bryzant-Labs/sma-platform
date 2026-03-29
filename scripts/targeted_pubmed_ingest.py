"""Targeted PubMed ingestion for ROCK-LIMK2-CFL2 pathway and related SMA queries.

Bypasses the daily pipeline date filter — searches ALL TIME with retmax=500 per query.
Designed to run directly on Moltbot where the DB is local.

Run:
    cd /home/bryzant/sma-platform && source venv/bin/activate
    python scripts/targeted_pubmed_ingest.py
    python scripts/targeted_pubmed_ingest.py --extract-claims   # also run claim extraction
"""

import argparse
import asyncio
import json
import logging
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from Bio import Entrez

# --- Configuration ---
DATABASE_URL = "postgresql://sma:sma-research-2026@localhost:5432/sma_platform"
ENTREZ_EMAIL = "christian@bryzant.com"
ENTREZ_TOOL = "sma-platform-targeted"
RETMAX = 500
BATCH_SIZE = 200  # Entrez efetch max IDs per request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("targeted-ingest")

# Configure Entrez
Entrez.email = ENTREZ_EMAIL
Entrez.tool = ENTREZ_TOOL

# --- Targeted Queries ---
QUERIES = [
    # ROCK-LIMK2-CFL2 pathway (primary focus)
    '"spinal muscular atrophy" AND "ROCK"',
    '"spinal muscular atrophy" AND "LIMK"',
    '"spinal muscular atrophy" AND cofilin',
    '"spinal muscular atrophy" AND "actin dynamics"',
    '"spinal muscular atrophy" AND fasudil',
    '"spinal muscular atrophy" AND profilin',
    '"SMN protein" AND "actin"',
    '"SMN protein" AND "cytoskeleton"',
    '"motor neuron" AND "ROCK inhibitor"',
    '"motor neuron" AND "LIMK2"',
    '"motor neuron" AND "cofilin-2"',
    '"motor neuron degeneration" AND "actin"',
    # Clinical / treatment queries
    '"SMN2" AND "splicing modifier" AND clinical',
    'nusinersen AND biomarker',
    'risdiplam AND "motor function"',
    '"spinal muscular atrophy" AND "NMJ" AND muscle',
    '"spinal muscular atrophy" AND biomarker AND neurofilament',
    '"spinal muscular atrophy" AND "gene therapy" AND outcome',
    'SMA AND "type 1" AND survival AND treatment',
    'SMA AND "type 2" AND ambulatory',
    # Wave 2: broader queries to push past 8,000
    '"ROCK inhibitor" AND "neurodegeneration"',
    '"ROCK inhibitor" AND "axon regeneration"',
    '"Rho kinase" AND "motor neuron"',
    '"Rho kinase" AND "neurodegeneration"',
    '"cofilin" AND "motor neuron"',
    '"cofilin" AND "actin" AND "neurodegeneration"',
    '"actin cytoskeleton" AND "motor neuron"',
    '"actin cytoskeleton" AND "neurodegeneration"',
    '"spinal muscular atrophy" AND "skeletal muscle" AND treatment',
    '"spinal muscular atrophy" AND "respiratory" AND outcome',
    '"spinal muscular atrophy" AND scoliosis',
    '"spinal muscular atrophy" AND "real world" AND outcome',
    'onasemnogene AND outcome',
    '"spinal muscular atrophy" AND "long term" AND treatment',
    '"SMA type 3" AND treatment AND outcome',
    '"spinal muscular atrophy" AND "adult" AND treatment',
    '"nusinersen" AND "long term" AND safety',
    '"risdiplam" AND biomarker',
    '"SMN" AND "axonal" AND transport',
    '"spinal muscular atrophy" AND "muscle strength"',
]

_MONTH_MAP = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}


def _normalise_date(year: str, month: str, day: str) -> date | None:
    if not year or not year.isdigit():
        return None
    m = int(_MONTH_MAP.get(month.lower()[:3], month.zfill(2) if month.isdigit() else "01"))
    d = int(day.zfill(2) if day.isdigit() else "01")
    try:
        return date(int(year), m, d)
    except ValueError:
        return date(int(year), m, 1)


def entrez_search(query: str) -> list[str]:
    """Search PubMed for a query, return list of PMIDs."""
    handle = Entrez.esearch(db="pubmed", term=query, retmax=RETMAX, usehistory="y")
    record = Entrez.read(handle)
    handle.close()
    return record.get("IdList", [])


def entrez_fetch(pmids: list[str]) -> list[dict[str, Any]]:
    """Fetch paper details for a batch of PMIDs."""
    handle = Entrez.efetch(db="pubmed", id=",".join(pmids), rettype="xml", retmode="xml")
    records = Entrez.read(handle)
    handle.close()

    papers = []
    for article in records.get("PubmedArticle", []):
        medline = article.get("MedlineCitation", {})
        art = medline.get("Article", {})

        pmid = str(medline.get("PMID", ""))

        # Authors
        author_list = art.get("AuthorList", [])
        authors = []
        for a in author_list:
            last = a.get("LastName", "")
            first = a.get("ForeName", "")
            if last:
                authors.append(f"{last} {first}".strip())

        # Date
        pub_date_raw = art.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})
        year = pub_date_raw.get("Year", "")
        month = pub_date_raw.get("Month", "01")
        day = pub_date_raw.get("Day", "01")

        # DOI
        doi = ""
        for eid in art.get("ELocationID", []):
            if str(eid.attributes.get("EIdType", "")) == "doi":
                doi = str(eid)

        # Abstract
        abstract_parts = art.get("Abstract", {}).get("AbstractText", [])
        abstract = " ".join(str(p) for p in abstract_parts)

        papers.append({
            "pmid": pmid,
            "title": str(art.get("ArticleTitle", "")),
            "authors": authors,  # list[str] for PostgreSQL ARRAY column
            "journal": art.get("Journal", {}).get("Title", ""),
            "pub_date": _normalise_date(year, month, day),
            "doi": doi,
            "abstract": abstract,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })

    return papers


async def main():
    parser = argparse.ArgumentParser(description="Targeted PubMed ingestion for ROCK-LIMK2-CFL2 pathway")
    parser.add_argument("--extract-claims", action="store_true", help="Run claim extraction on new papers after ingestion")
    args = parser.parse_args()

    import asyncpg

    logger.info("=== Targeted PubMed Ingestion Started ===")
    logger.info("Queries: %d, retmax: %d per query", len(QUERIES), RETMAX)

    # Connect to DB
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=5)
    logger.info("Connected to database")

    # Get current source count
    async with pool.acquire() as conn:
        before_count = await conn.fetchval("SELECT COUNT(*) FROM sources")
    logger.info("Sources before: %d", before_count)

    # Get existing PMIDs to skip duplicates
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT external_id FROM sources WHERE source_type = 'pubmed'"
        )
    existing_pmids = {r["external_id"] for r in rows}
    logger.info("Existing PubMed PMIDs: %d", len(existing_pmids))

    # Phase 1: Collect all unique new PMIDs
    all_new_pmids: set[str] = set()
    query_stats: list[dict] = []

    for i, query in enumerate(QUERIES, 1):
        logger.info("[%d/%d] Searching: %s", i, len(QUERIES), query)
        try:
            pmids = entrez_search(query)
            new_pmids = set(pmids) - existing_pmids
            all_new_pmids.update(new_pmids)
            query_stats.append({
                "query": query,
                "total": len(pmids),
                "new": len(new_pmids),
            })
            logger.info("  -> %d results, %d new", len(pmids), len(new_pmids))
        except Exception as e:
            logger.error("  -> FAILED: %s", e)
            query_stats.append({"query": query, "total": 0, "new": 0, "error": str(e)})

        # NCBI rate limit: 3 req/sec without API key
        time.sleep(0.4)

    logger.info("Total unique new PMIDs to fetch: %d", len(all_new_pmids))

    if not all_new_pmids:
        logger.info("No new papers found. Exiting.")
        await pool.close()
        return

    # Phase 2: Fetch paper details in batches
    pmid_list = sorted(all_new_pmids)
    all_papers: list[dict] = []

    for batch_start in range(0, len(pmid_list), BATCH_SIZE):
        batch = pmid_list[batch_start:batch_start + BATCH_SIZE]
        logger.info("Fetching details for PMIDs %d-%d of %d",
                     batch_start + 1, min(batch_start + BATCH_SIZE, len(pmid_list)), len(pmid_list))
        try:
            papers = entrez_fetch(batch)
            all_papers.extend(papers)
        except Exception as e:
            logger.error("Fetch failed for batch starting at %d: %s", batch_start, e)
        time.sleep(0.4)

    logger.info("Fetched details for %d papers", len(all_papers))

    # Phase 3: Insert into database
    inserted = 0
    updated = 0
    errors = 0

    for paper in all_papers:
        try:
            async with pool.acquire() as conn:
                result = await conn.execute(
                    """INSERT INTO sources (source_type, external_id, title, authors, journal, pub_date, doi, url, abstract)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                       ON CONFLICT (source_type, external_id) DO UPDATE
                       SET title = excluded.title, abstract = excluded.abstract, updated_at = CURRENT_TIMESTAMP""",
                    "pubmed", paper["pmid"], paper["title"],
                    paper["authors"], paper["journal"],
                    paper["pub_date"], paper["doi"], paper["url"], paper["abstract"],
                )
                if "INSERT" in result:
                    inserted += 1
                else:
                    updated += 1
        except Exception as e:
            errors += 1
            if errors <= 5:
                logger.error("Insert error for PMID %s: %s", paper.get("pmid"), e)

    logger.info("Inserted: %d, Updated: %d, Errors: %d", inserted, updated, errors)

    # Get final source count
    async with pool.acquire() as conn:
        after_count = await conn.fetchval("SELECT COUNT(*) FROM sources")
    logger.info("Sources after: %d (delta: +%d)", after_count, after_count - before_count)

    # Log to ingestion_log
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO ingestion_log (source_type, query, items_found, items_new, items_updated, errors, duration_secs)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            "pubmed", "targeted_rock_limk2_cfl2",
            len(all_papers), inserted, updated,
            [] if errors == 0 else [f"{errors} errors"],
            0.0,
        )

    # Print summary
    print("\n" + "=" * 60)
    print("TARGETED PUBMED INGESTION SUMMARY")
    print("=" * 60)
    print(f"Queries run:      {len(QUERIES)}")
    print(f"Unique new PMIDs: {len(all_new_pmids)}")
    print(f"Papers fetched:   {len(all_papers)}")
    print(f"Inserted:         {inserted}")
    print(f"Updated:          {updated}")
    print(f"Errors:           {errors}")
    print(f"Sources before:   {before_count}")
    print(f"Sources after:    {after_count}")
    print(f"Net new:          +{after_count - before_count}")
    print("=" * 60)

    print("\nPer-query breakdown:")
    for qs in query_stats:
        status = f"  {qs['total']:>4d} results, {qs['new']:>4d} new"
        if "error" in qs:
            status += f" [ERROR: {qs['error']}]"
        print(f"  {qs['query'][:60]:<62s} {status}")

    await pool.close()

    # Phase 4 (optional): Trigger claim extraction
    if args.extract_claims:
        logger.info("=== Triggering claim extraction on unprocessed sources ===")
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from sma_platform.core.database import init_pool as app_init_pool, close_pool as app_close_pool
        from sma_platform.reasoning.claim_extractor import process_all_unprocessed

        await app_init_pool(DATABASE_URL)
        try:
            result = await process_all_unprocessed()
            logger.info("Claim extraction result: %s", result)
            print(f"\nClaim extraction: {result}")
        except Exception as e:
            logger.error("Claim extraction failed: %s", e)
        finally:
            await app_close_pool()

    logger.info("=== Targeted ingestion complete ===")


if __name__ == "__main__":
    asyncio.run(main())
