"""Daily ingestion cron — pulls fresh data from PubMed + ClinicalTrials.gov.

Run: python scripts/daily_ingest.py
Cron: 0 6 * * * cd /var/www/sma-research.info/app && /var/www/sma-research.info/app/venv/bin/python scripts/daily_ingest.py >> /var/log/sma-ingest.log 2>&1
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sma_platform.core.config import settings
from sma_platform.core.database import close_pool, execute, init_pool
from sma_platform.ingestion.adapters import biorxiv, clinicaltrials, pubmed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def ingest_pubmed(days_back: int = 7):
    """Pull recent SMA papers from PubMed."""
    logger.info("Starting PubMed ingestion (days_back=%d)", days_back)
    start = datetime.now(timezone.utc)

    try:
        papers = await pubmed.search_recent_sma(days_back=days_back)
    except Exception as e:
        logger.error("PubMed search failed: %s", e)
        return

    new_count = 0
    updated_count = 0
    errors: list[str] = []

    for paper in papers:
        try:
            result = await execute(
                """INSERT INTO sources (source_type, external_id, title, authors, journal, pub_date, doi, url, abstract)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                   ON CONFLICT (source_type, external_id) DO UPDATE
                   SET title = excluded.title, abstract = excluded.abstract, updated_at = CURRENT_TIMESTAMP""",
                "pubmed", paper["pmid"], paper["title"],
                json.dumps(paper["authors"]), paper["journal"],
                paper["pub_date"], paper["doi"], paper["url"], paper["abstract"],
            )
            if "INSERT" in str(result):
                new_count += 1
            else:
                updated_count += 1
        except Exception as e:
            errors.append(f"PMID {paper.get('pmid')}: {e}")

    duration = (datetime.now(timezone.utc) - start).total_seconds()

    await execute(
        """INSERT INTO ingestion_log (source_type, query, items_found, items_new, items_updated, errors, duration_secs)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        "pubmed", "daily_sma_search", len(papers), new_count, updated_count,
        json.dumps(errors[:10]) if errors else None, duration,
    )
    logger.info("PubMed: found=%d new=%d updated=%d errors=%d (%.1fs)", len(papers), new_count, updated_count, len(errors), duration)


async def ingest_trials():
    """Pull all SMA clinical trials from ClinicalTrials.gov."""
    logger.info("Starting ClinicalTrials.gov ingestion")
    start = datetime.now(timezone.utc)

    try:
        trials = await clinicaltrials.fetch_all_sma_trials()
    except Exception as e:
        logger.error("ClinicalTrials.gov fetch failed: %s", e)
        return

    new_count = 0
    updated_count = 0
    errors: list[str] = []

    for trial in trials:
        try:
            result = await execute(
                """INSERT INTO trials (nct_id, title, status, phase, conditions, interventions, sponsor,
                   start_date, completion_date, enrollment, results_summary, url)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                   ON CONFLICT (nct_id) DO UPDATE
                   SET title = excluded.title, status = excluded.status, phase = excluded.phase,
                       enrollment = excluded.enrollment, updated_at = CURRENT_TIMESTAMP""",
                trial["nct_id"], trial["title"], trial["status"], trial["phase"],
                json.dumps(trial["conditions"]), json.dumps(trial["interventions"]),
                trial["sponsor"], trial.get("start_date"), trial.get("completion_date"),
                trial.get("enrollment"), trial.get("brief_summary"), trial["url"],
            )
            if "INSERT" in str(result):
                new_count += 1
            else:
                updated_count += 1
        except Exception as e:
            errors.append(f"NCT {trial.get('nct_id')}: {e}")

    duration = (datetime.now(timezone.utc) - start).total_seconds()

    await execute(
        """INSERT INTO ingestion_log (source_type, query, items_found, items_new, items_updated, errors, duration_secs)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        "clinicaltrials", "all_sma_trials", len(trials), new_count, updated_count,
        json.dumps(errors[:10]) if errors else None, duration,
    )
    logger.info("Trials: found=%d new=%d updated=%d errors=%d (%.1fs)", len(trials), new_count, updated_count, len(errors), duration)


async def ingest_biorxiv(days_back: int = 7):
    """Scan bioRxiv + medRxiv for SMA preprints."""
    logger.info("Starting bioRxiv/medRxiv scan (days_back=%d)", days_back)
    start = datetime.now(timezone.utc)

    try:
        preprints = await biorxiv.scan_preprints(days_back=days_back)
    except Exception as e:
        logger.error("bioRxiv scan failed: %s", e)
        return

    new_count = 0
    updated_count = 0
    errors: list[str] = []

    for p in preprints:
        try:
            result = await execute(
                """INSERT INTO sources (source_type, external_id, title, authors, journal, pub_date, doi, url, abstract)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                   ON CONFLICT (source_type, external_id) DO UPDATE
                   SET title = excluded.title, abstract = excluded.abstract, updated_at = CURRENT_TIMESTAMP""",
                "biorxiv", p["doi"], p["title"],
                json.dumps(p["authors"]), p.get("server", "biorxiv"),
                p.get("posted_date"), p["doi"], p["url"], p["abstract"],
            )
            if "INSERT" in str(result):
                new_count += 1
            else:
                updated_count += 1
        except Exception as e:
            errors.append(f"DOI {p.get('doi')}: {e}")

    duration = (datetime.now(timezone.utc) - start).total_seconds()

    await execute(
        """INSERT INTO ingestion_log (source_type, query, items_found, items_new, items_updated, errors, duration_secs)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        "biorxiv", "daily_preprint_scan", len(preprints), new_count, updated_count,
        json.dumps(errors[:10]) if errors else None, duration,
    )
    logger.info("bioRxiv: found=%d new=%d updated=%d errors=%d (%.1fs)",
                len(preprints), new_count, updated_count, len(errors), duration)


async def main():
    logger.info("=== Daily SMA ingestion started ===")
    await init_pool(settings.database_url)

    await ingest_trials()
    await ingest_pubmed(days_back=7)
    await ingest_biorxiv(days_back=7)

    await close_pool()
    logger.info("=== Daily ingestion complete ===")


if __name__ == "__main__":
    asyncio.run(main())
