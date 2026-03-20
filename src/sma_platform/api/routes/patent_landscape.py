"""Patent landscape analysis endpoints — competitive intelligence for SMA research.

Endpoints:
- GET  /patents/landscape              — full patent landscape overview
- GET  /patents/freedom-to-operate     — FTO risk assessment for a compound
- GET  /patents/recent                 — recent patent filings with target annotations
- GET  /patents/fto                    — FTO summary across all SMA target areas
- GET  /patents/fto/{symbol}           — FTO assessment for a specific target
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Path, Query

from ...reasoning.patent_fto import get_fto_for_target, get_fto_summary
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


@router.get("/patents/fto")
async def fto_summary():
    """Freedom-to-operate summary across all SMA target areas.

    Returns a risk-sorted overview of patent coverage for key SMA targets
    including SMN2 splicing, gene therapy, modifier genes (NCALD, PLS3),
    novel targets (CORO1C, UBA1), and repurposing candidates (4-AP, HDAC).

    Each entry includes risk level (high/medium/low), patent holders,
    key patent numbers, expiry ranges, and current status.
    """
    results = await get_fto_summary()
    return {
        "total_areas_assessed": len(results),
        "high_risk": sum(1 for r in results if r["risk"] == "high"),
        "medium_risk": sum(1 for r in results if r["risk"] == "medium"),
        "low_risk": sum(1 for r in results if r["risk"] == "low"),
        "areas": results,
    }


@router.get("/patents/fto/{symbol}")
async def fto_for_target(
    symbol: str = Path(..., description="Target gene symbol or compound (e.g. 'CORO1C', 'SMN2', '4-AP')"),
):
    """FTO assessment for a specific target or compound.

    Returns patent landscape details for the given target including:
    - Known patent holders and key patent numbers
    - Patent expiry ranges
    - Risk level (high/medium/low/unknown)
    - Count of patents mentioning this target in our database
    - Plain-language recommendation

    Example: /patents/fto/CORO1C
    """
    try:
        result = await get_fto_for_target(symbol)
    except Exception as exc:
        if "does not exist" in str(exc):
            logger.warning("sources table not available -- returning offline FTO for %s", symbol)
            # Still return the static landscape data even without DB
            from ...reasoning.patent_fto import PATENT_LANDSCAPE, _TARGET_KEY_MAP, _DEFAULT_LANDSCAPE, _fto_recommendation
            target_upper = symbol.strip().upper()
            landscape_key = _TARGET_KEY_MAP.get(target_upper)
            landscape = PATENT_LANDSCAPE.get(landscape_key, _DEFAULT_LANDSCAPE) if landscape_key else _DEFAULT_LANDSCAPE
            return {
                "target": target_upper,
                "patent_count_in_db": 0,
                "landscape": landscape,
                "recommendation": _fto_recommendation(landscape.get("risk", "unknown")),
                "note": "Patent database not available -- showing curated landscape data only.",
            }
        raise
    return result
