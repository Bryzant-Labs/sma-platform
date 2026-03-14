"""Ingestion trigger endpoints — kick off data pulls from external sources."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter

from ...core.database import execute
from ...ingestion.adapters import clinicaltrials, pubmed

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ingest/pubmed")
async def trigger_pubmed_ingestion(days_back: int = 7):
    """Pull recent SMA papers from PubMed and store in sources table."""
    start = datetime.now(timezone.utc)
    papers = await pubmed.search_recent_sma(days_back=days_back)

    new_count = 0
    updated_count = 0
    errors: list[str] = []

    for paper in papers:
        try:
            result = await execute(
                """INSERT INTO sources (source_type, external_id, title, authors, journal, pub_date, doi, url, abstract)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                   ON CONFLICT (source_type, external_id) DO UPDATE
                   SET title = excluded.title, abstract = excluded.abstract, updated_at = datetime('now')""",
                "pubmed",
                paper["pmid"],
                paper["title"],
                json.dumps(paper["authors"]),
                paper["journal"],
                paper["pub_date"],
                paper["doi"],
                paper["url"],
                paper["abstract"],
            )
            if "INSERT" in result:
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

    return {
        "source": "pubmed",
        "papers_found": len(papers),
        "new": new_count,
        "updated": updated_count,
        "errors": len(errors),
        "duration_secs": round(duration, 2),
    }


@router.post("/ingest/trials")
async def trigger_trials_ingestion():
    """Pull all SMA clinical trials from ClinicalTrials.gov."""
    start = datetime.now(timezone.utc)
    trials = await clinicaltrials.fetch_all_sma_trials()

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
                       enrollment = excluded.enrollment, updated_at = datetime('now')""",
                trial["nct_id"],
                trial["title"],
                trial["status"],
                trial["phase"],
                json.dumps(trial["conditions"]),
                json.dumps(trial["interventions"]),
                trial["sponsor"],
                trial.get("start_date"),
                trial.get("completion_date"),
                trial.get("enrollment"),
                trial.get("brief_summary"),
                trial["url"],
            )
            if "INSERT" in result:
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

    return {
        "source": "clinicaltrials",
        "trials_found": len(trials),
        "new": new_count,
        "updated": updated_count,
        "errors": len(errors),
        "duration_secs": round(duration, 2),
    }
