"""Preprint endpoints — bioRxiv/medRxiv scanner (Agent A, Phase 10.2)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query

from ...core.database import execute, fetch, fetchrow
from ...ingestion.adapters import biorxiv
from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter()

# DDL executed lazily on first scan so the table is always present
_CREATE_PREPRINTS_TABLE = """
CREATE TABLE IF NOT EXISTS preprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server TEXT NOT NULL,
    doi TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    authors TEXT,
    abstract TEXT,
    category TEXT,
    posted_date TEXT,
    relevance_score FLOAT DEFAULT 0.0,
    metadata TEXT DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
)
"""


@router.get("/preprints")
async def list_preprints(
    server: str | None = Query(default=None, description="Filter by server: biorxiv or medrxiv"),
    min_score: float = Query(default=0.0, ge=0.0, le=1.0, description="Minimum relevance score"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List recent SMA-relevant preprints stored in the database.

    Results are ordered by relevance score descending, then by posted_date descending.
    """
    if server:
        rows = await fetch(
            """SELECT id, server, doi, title, authors, category, posted_date,
                      relevance_score, created_at
               FROM preprints
               WHERE server = $1 AND relevance_score >= $2
               ORDER BY relevance_score DESC, posted_date DESC
               LIMIT $3 OFFSET $4""",
            server, min_score, limit, offset,
        )
    else:
        rows = await fetch(
            """SELECT id, server, doi, title, authors, category, posted_date,
                      relevance_score, created_at
               FROM preprints
               WHERE relevance_score >= $1
               ORDER BY relevance_score DESC, posted_date DESC
               LIMIT $2 OFFSET $3""",
            min_score, limit, offset,
        )

    results = []
    for row in rows:
        r = dict(row)
        # Parse authors JSON string back to list for cleaner output
        if r.get("authors"):
            try:
                r["authors"] = json.loads(r["authors"])
            except (json.JSONDecodeError, TypeError):
                pass  # Leave as-is if not valid JSON
        r["id"] = str(r["id"]) if r.get("id") else None
        r["created_at"] = str(r["created_at"]) if r.get("created_at") else None
        results.append(r)

    return {"preprints": results, "count": len(results), "offset": offset}


@router.post("/preprints/scan", dependencies=[Depends(require_admin_key)])
async def trigger_preprint_scan(
    days_back: int = Query(default=7, ge=1, le=90, description="Days back to scan"),
):
    """Trigger a fresh scan of bioRxiv and medRxiv for SMA-relevant preprints.

    Requires x-admin-key header. Creates the preprints table if it does not exist,
    then upserts all newly found preprints by DOI.
    """
    start = datetime.now(timezone.utc)

    # Ensure table exists
    try:
        await execute(_CREATE_PREPRINTS_TABLE)
    except Exception as exc:
        logger.error("Failed to create preprints table: %s", exc, exc_info=True)
        return {"error": f"Table creation failed: {exc}"}

    # Run the scan
    try:
        preprints = await biorxiv.scan_preprints(days_back=days_back)
    except Exception as exc:
        logger.error("bioRxiv scan failed: %s", exc, exc_info=True)
        return {"error": f"Scan failed: {exc}"}

    new_count = 0
    updated_count = 0
    errors: list[str] = []

    for paper in preprints:
        doi = paper.get("doi", "")
        if not doi:
            logger.warning("Skipping preprint with empty DOI: %s", paper.get("title", ""))
            continue

        try:
            result = await execute(
                """INSERT INTO preprints
                       (server, doi, title, authors, abstract, category, posted_date, relevance_score, metadata)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                   ON CONFLICT (doi) DO UPDATE
                       SET title = excluded.title,
                           abstract = excluded.abstract,
                           relevance_score = excluded.relevance_score,
                           category = excluded.category,
                           posted_date = excluded.posted_date""",
                paper["server"],
                doi,
                paper["title"],
                json.dumps(paper.get("authors", [])),
                paper.get("abstract", ""),
                paper.get("category", ""),
                paper.get("posted_date", ""),
                paper.get("relevance_score", 0.0),
                json.dumps({"url": paper.get("url", "")}),
            )
            if "INSERT" in result:
                new_count += 1
            else:
                updated_count += 1
        except Exception as exc:
            err_msg = f"DOI {doi}: {exc}"
            errors.append(err_msg)
            logger.error("Failed to upsert preprint %s: %s", doi, exc)

    duration = round((datetime.now(timezone.utc) - start).total_seconds(), 2)

    # Log to ingestion_log for pipeline observability
    try:
        await execute(
            """INSERT INTO ingestion_log
                   (source_type, query, items_found, items_new, items_updated, errors, duration_secs)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            "biorxiv_medrxiv",
            f"sma_preprints_days_back={days_back}",
            len(preprints),
            new_count,
            updated_count,
            json.dumps(errors[:10]) if errors else None,
            duration,
        )
    except Exception as exc:
        logger.warning("Failed to write ingestion_log for preprint scan: %s", exc)

    return {
        "source": "biorxiv+medrxiv",
        "days_back": days_back,
        "preprints_found": len(preprints),
        "new": new_count,
        "updated": updated_count,
        "errors": len(errors),
        "duration_secs": duration,
    }
