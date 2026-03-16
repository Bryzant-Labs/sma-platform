"""Patent landscape analysis endpoints — competitive intelligence for SMA research.

Endpoints:
- GET  /patents/landscape              — full patent landscape overview
- GET  /patents/freedom-to-operate     — FTO risk assessment for a compound
- GET  /patents/recent                 — recent patent filings with target annotations
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query

from ...reasoning.patent_landscape import (
    freedom_to_operate,
    get_landscape,
    recent_patents,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/patents/landscape")
async def patent_landscape_overview():
    """Full SMA patent landscape analysis.

    Returns temporal filing trends, mechanism clustering (splicing, gene therapy,
    antisense, small molecule, CRISPR, biomarker, screening, delivery),
    top assignees, and recent competitive filings.
    """
    try:
        result = await get_landscape()
    except Exception as exc:
        if "does not exist" in str(exc):
            logger.warning("sources table not available — returning empty landscape")
            return {
                "total_patents": 0,
                "note": "Patent data not yet ingested. Run the patent ingestion pipeline first.",
            }
        raise
    return result


@router.get("/patents/freedom-to-operate")
async def patent_fto(
    compound: str = Query(..., description="Compound name to check (e.g. '4-aminopyridine')"),
):
    """Freedom-to-operate assessment for a specific compound.

    Searches all SMA patents for mentions of the compound (including known synonyms).
    Returns risk level: 'clear' (no patents), 'caution' (related patents),
    or 'blocked' (direct patent coverage).

    Example: /patents/freedom-to-operate?compound=4-aminopyridine
    """
    try:
        result = await freedom_to_operate(compound)
    except Exception as exc:
        if "does not exist" in str(exc):
            logger.warning("sources table not available — returning empty FTO")
            return {
                "compound": compound,
                "risk_level": "unknown",
                "note": "Patent data not yet ingested.",
            }
        raise
    return result


@router.get("/patents/recent")
async def recent_patent_filings(
    days: int = Query(default=365, ge=1, le=3650, description="Look back N days"),
):
    """Most recent SMA patent filings.

    Returns patents filed within the specified window, with mechanism classification
    and annotations for any that mention our discovery targets (SMN2, PLS3, STMN2,
    4-AP, etc.).
    """
    try:
        results = await recent_patents(days_back=days)
    except Exception as exc:
        if "does not exist" in str(exc):
            logger.warning("sources table not available — returning empty recent patents")
            return {"days_back": days, "total": 0, "patents": [], "note": "Patent data not yet ingested."}
        raise
    return {
        "days_back": days,
        "total": len(results),
        "targeting_our_discoveries": sum(1 for r in results if r.get("highlights_our_targets")),
        "patents": results,
    }
