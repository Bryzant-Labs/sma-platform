"""Targeted bioRxiv/medRxiv preprint monitoring for SMA research.

Extends the daily pipeline's general scan with focused queries on:
- Core SMA biology (SMN, motor neurons)
- Therapeutic targets (ROCK, fasudil, p38 MAPK)
- Mechanistic pathways (actin-cofilin, profilin, complement)

Uses:
1. Europe PMC API for targeted keyword searches (indexes preprints)
2. bioRxiv details API for date-range scanning with extended keywords

Run: python scripts/monitor_biorxiv.py [--days-back 7] [--dry-run]
Cron: 0 4 * * * (after main pipeline at 3 UTC)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import httpx

from sma_platform.core.config import settings
from sma_platform.core.database import close_pool, execute, fetch, fetchval, init_pool
from sma_platform.ingestion.adapters import biorxiv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("biorxiv_monitor")

# ── Targeted Queries ────────────────────────────────────────────

TARGETED_QUERIES = [
    "spinal muscular atrophy",
    "SMN protein motor neuron",
    "ROCK inhibitor motor neuron",
    "actin cofilin rod neurodegeneration",
    "fasudil neuroprotection",
    "p38 MAPK motor neuron",
    "complement synapse elimination",
    "profilin actin motor neuron",
]

# Extended keywords for bioRxiv date-range filtering (superset of adapter defaults)
EXTENDED_KEYWORDS = [
    # Core SMA
    "spinal muscular atrophy",
    "smn1", "smn2", "motor neuron",
    "nusinersen", "risdiplam", "onasemnogene",
    # Therapeutic targets
    "rock inhibitor", "fasudil", "rock2 kinase",
    "p38 mapk", "p38 alpha",
    # Mechanistic pathways
    "actin cofilin", "cofilin rod",
    "profilin actin", "pfn1", "pfn2",
    "complement synapse", "complement c1q",
    # Related motor neuron disease
    "motor neuron disease", "amyotrophic lateral sclerosis",
    "neuromuscular junction",
]

# Europe PMC API
EUROPEPMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
EUROPEPMC_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


# ── Europe PMC Search ───────────────────────────────────────────

async def search_europepmc(
    query: str,
    days_back: int,
    client: httpx.AsyncClient,
) -> list[dict]:
    """Search Europe PMC for preprints matching a query in the last N days."""
    date_from = (date.today() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    date_to = date.today().strftime("%Y-%m-%d")

    params = {
        "query": f'"{query}" AND (SRC:PPR) AND (FIRST_PDATE:[{date_from} TO {date_to}])',
        "format": "json",
        "pageSize": 100,
        "resultType": "core",
    }

    results = []
    try:
        resp = await client.get(EUROPEPMC_BASE, params=params)
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("resultList", {}).get("result", []):
            doi = item.get("doi", "")
            if not doi:
                continue

            # Determine server from source
            source = item.get("source", "").lower()
            server = "medrxiv" if "medrxiv" in source else "biorxiv"

            authors_raw = item.get("authorString", "")
            authors_list = [a.strip() for a in authors_raw.split(",") if a.strip()]

            results.append({
                "server": server,
                "doi": doi,
                "title": item.get("title", "").strip(),
                "authors": authors_list,
                "abstract": item.get("abstractText", "").strip(),
                "category": item.get("journalTitle", ""),
                "posted_date": item.get("firstPublicationDate", ""),
                "url": f"https://doi.org/{doi}",
                "query_matched": query,
            })

    except Exception as exc:
        logger.warning("Europe PMC search failed for '%s': %s", query, exc)

    return results


# ── Extended bioRxiv Scan ───────────────────────────────────────

def is_relevant_extended(title: str, abstract: str) -> tuple[bool, float, list[str]]:
    """Check relevance against extended keyword set.

    Returns (is_relevant, score, matched_keywords).
    """
    title_lower = title.lower()
    abstract_lower = abstract.lower()
    matched = []
    hits = 0

    for kw in EXTENDED_KEYWORDS:
        in_title = kw in title_lower
        in_abstract = kw in abstract_lower
        if in_title:
            hits += 2
            matched.append(f"{kw} (title)")
        elif in_abstract:
            hits += 1
            matched.append(f"{kw} (abstract)")

    if hits == 0:
        return False, 0.0, []

    max_possible = len(EXTENDED_KEYWORDS) * 2
    score = round(min(1.0, hits / max_possible), 4)
    return True, score, matched


# ── Ingestion ───────────────────────────────────────────────────

async def ingest_preprint(paper: dict) -> str:
    """Insert or update a preprint in the sources table.

    Returns 'new', 'updated', or 'error'.
    """
    try:
        existing = await fetchval(
            "SELECT id FROM sources WHERE source_type = $1 AND external_id = $2",
            "biorxiv", paper["doi"],
        )

        await execute(
            """INSERT INTO sources (source_type, external_id, title, authors, journal, pub_date, doi, url, abstract)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
               ON CONFLICT (source_type, external_id) DO UPDATE
               SET title = excluded.title, abstract = excluded.abstract, updated_at = CURRENT_TIMESTAMP""",
            "biorxiv",
            paper["doi"],
            paper["title"],
            json.dumps(paper["authors"]),
            paper.get("server", "biorxiv"),
            paper.get("posted_date"),
            paper["doi"],
            paper["url"],
            paper.get("abstract", ""),
        )

        if existing is None:
            return "new"
        return "updated"

    except Exception as exc:
        logger.error("Failed to ingest DOI %s: %s", paper.get("doi"), exc)
        return "error"


# ── Claim Extraction Trigger ────────────────────────────────────

async def trigger_claim_extraction():
    """Call the platform API to extract claims from unprocessed sources."""
    api_base = "http://localhost:8090/api/v2"
    admin_key = "sma-admin-2026"

    async with httpx.AsyncClient(timeout=httpx.Timeout(1800.0)) as client:
        try:
            resp = await client.post(
                f"{api_base}/extract/claims",
                headers={"x-admin-key": admin_key},
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info("Claim extraction result: %s", json.dumps(data, indent=2))
            return data
        except Exception as exc:
            logger.error("Claim extraction failed: %s", exc)
            return None


# ── Main Pipeline ───────────────────────────────────────────────

async def run_monitor(days_back: int = 7, dry_run: bool = False):
    """Run the full monitoring pipeline."""
    start_time = datetime.now(timezone.utc)
    logger.info("=" * 60)
    logger.info("bioRxiv/medRxiv Targeted Monitor — %s", start_time.strftime("%Y-%m-%d %H:%M UTC"))
    logger.info("Days back: %d | Dry run: %s", days_back, dry_run)
    logger.info("=" * 60)

    all_papers: dict[str, dict] = {}  # Keyed by DOI to dedup

    # ── Phase 1: Europe PMC targeted searches ────────────────
    logger.info("Phase 1: Europe PMC targeted searches (%d queries)", len(TARGETED_QUERIES))

    async with httpx.AsyncClient(timeout=EUROPEPMC_TIMEOUT, follow_redirects=True) as client:
        for query in TARGETED_QUERIES:
            results = await search_europepmc(query, days_back, client)
            for paper in results:
                doi = paper["doi"]
                if doi not in all_papers:
                    all_papers[doi] = paper
                    logger.info("  [Europe PMC] NEW: %s — %s", doi, paper["title"][:80])
            logger.info("  Query '%s': %d results", query, len(results))
            # Rate limit: be polite to Europe PMC
            await asyncio.sleep(0.5)

    logger.info("Phase 1 complete: %d unique preprints from Europe PMC", len(all_papers))

    # ── Phase 2: bioRxiv date-range scan with extended keywords ──
    logger.info("Phase 2: bioRxiv date-range scan with extended keywords")

    today = date.today()
    start_date = (today - timedelta(days=days_back)).isoformat()
    end_date = today.isoformat()

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0), follow_redirects=True) as client:
        for server in ("biorxiv", "medrxiv"):
            try:
                raw_papers = await biorxiv._fetch_server(server, start_date, end_date, client)
                logger.info("  %s: %d total papers in date range", server, len(raw_papers))

                new_from_scan = 0
                for raw in raw_papers:
                    paper = biorxiv._parse_paper(raw, server)
                    doi = paper["doi"]
                    if doi in all_papers:
                        continue  # Already found via Europe PMC

                    is_rel, score, matched = is_relevant_extended(
                        paper["title"], paper.get("abstract", ""),
                    )
                    if is_rel:
                        paper["relevance_score"] = score
                        paper["matched_keywords"] = matched
                        all_papers[doi] = paper
                        new_from_scan += 1
                        logger.info(
                            "  [%s] NEW: %s (score=%.3f) — %s",
                            server, doi, score, paper["title"][:80],
                        )

                logger.info("  %s: %d new relevant papers from extended scan", server, new_from_scan)

            except Exception as exc:
                logger.error("  %s scan failed: %s", server, exc, exc_info=True)

    logger.info("Phase 2 complete: %d total unique preprints", len(all_papers))

    if dry_run:
        logger.info("DRY RUN — skipping ingestion and claim extraction")
        for doi, paper in sorted(
            all_papers.items(),
            key=lambda x: x[1].get("relevance_score", 0),
            reverse=True,
        ):
            logger.info(
                "  DOI: %s | Score: %.3f | %s",
                doi, paper.get("relevance_score", 0), paper["title"][:80],
            )
        return

    # ── Phase 3: Ingest into database ────────────────────────
    logger.info("Phase 3: Ingesting %d preprints into sources table", len(all_papers))

    if not all_papers:
        logger.info("No new preprints found — nothing to ingest")
        return

    await init_pool()

    stats = {"new": 0, "updated": 0, "error": 0}
    for doi, paper in all_papers.items():
        result = await ingest_preprint(paper)
        stats[result] += 1

    logger.info(
        "Ingestion complete: %d new, %d updated, %d errors",
        stats["new"], stats["updated"], stats["error"],
    )

    # ── Phase 4: Trigger claim extraction ────────────────────
    if stats["new"] > 0:
        logger.info("Phase 4: Triggering claim extraction for %d new sources", stats["new"])
        await trigger_claim_extraction()
    else:
        logger.info("Phase 4: Skipped — no new sources to process")

    # ── Log summary to ingestion_log ─────────────────────────
    try:
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        await execute(
            """INSERT INTO ingestion_log (source_type, query, items_found, items_new, items_updated, errors, duration_secs)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            "biorxiv_monitor",
            json.dumps(TARGETED_QUERIES),
            len(all_papers),
            stats["new"],
            stats["updated"],
            json.dumps([]) if stats["error"] == 0 else None,
            duration,
        )
    except Exception as exc:
        logger.warning("Failed to log to ingestion_log: %s", exc)

    await close_pool()

    duration = (datetime.now(timezone.utc) - start_time).total_seconds()
    logger.info("=" * 60)
    logger.info("Monitor complete in %.1fs", duration)
    logger.info(
        "  Total found: %d | New: %d | Updated: %d | Errors: %d",
        len(all_papers), stats["new"], stats["updated"], stats["error"],
    )
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="bioRxiv/medRxiv targeted preprint monitor")
    parser.add_argument("--days-back", type=int, default=7, help="Days to look back (default: 7)")
    parser.add_argument("--dry-run", action="store_true", help="Search only, don't ingest")
    args = parser.parse_args()

    asyncio.run(run_monitor(days_back=args.days_back, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
