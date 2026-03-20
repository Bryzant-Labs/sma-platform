"""Evidence Timeline — temporal view of how evidence grows per target."""

from __future__ import annotations
import logging
from fastapi import APIRouter, Query
from ...core.database import fetch, fetchval

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/claims")
async def claims_timeline():
    """Get claim creation timeline grouped by year."""
    rows = await fetch("""
        SELECT
            EXTRACT(YEAR FROM s.pub_date) as year,
            COUNT(DISTINCT c.id) as claims,
            COUNT(DISTINCT s.id) as sources
        FROM claims c
        JOIN evidence e ON e.claim_id = c.id
        JOIN sources s ON e.source_id = s.id
        WHERE s.pub_date IS NOT NULL
        GROUP BY EXTRACT(YEAR FROM s.pub_date)
        ORDER BY year
    """)

    timeline = []
    cumulative_claims = 0
    cumulative_sources = 0
    for r in rows:
        year = int(r["year"]) if r["year"] else None
        if year and 1990 <= year <= 2027:
            claims = r["claims"]
            sources = r["sources"]
            cumulative_claims += claims
            cumulative_sources += sources
            timeline.append({
                "year": year,
                "claims": claims,
                "sources": sources,
                "cumulative_claims": cumulative_claims,
                "cumulative_sources": cumulative_sources,
            })

    return {
        "timeline": timeline,
        "total_years": len(timeline),
        "peak_year": max(timeline, key=lambda x: x["claims"])["year"] if timeline else None,
    }


@router.get("/target/{symbol}")
async def target_timeline(symbol: str):
    """Get evidence timeline for a specific target."""
    sym = symbol.upper()

    target = await fetch("SELECT id FROM targets WHERE symbol = $1", sym)
    if not target:
        from fastapi import HTTPException
        raise HTTPException(404, detail=f"Target {sym} not found")

    tid = target[0]["id"]

    rows = await fetch("""
        SELECT
            EXTRACT(YEAR FROM s.pub_date) as year,
            COUNT(DISTINCT c.id) as claims,
            COUNT(DISTINCT s.id) as sources,
            ARRAY_AGG(DISTINCT c.claim_type) as claim_types
        FROM claims c
        JOIN evidence e ON e.claim_id = c.id
        JOIN sources s ON e.source_id = s.id
        WHERE (c.subject_id = $1 OR c.object_id = $1)
          AND s.pub_date IS NOT NULL
        GROUP BY EXTRACT(YEAR FROM s.pub_date)
        ORDER BY year
    """, tid)

    timeline = []
    cumulative = 0
    for r in rows:
        year = int(r["year"]) if r["year"] else None
        if year and 1990 <= year <= 2027:
            claims = r["claims"]
            cumulative += claims
            timeline.append({
                "year": year,
                "claims": claims,
                "sources": r["sources"],
                "cumulative": cumulative,
                "claim_types": r["claim_types"] if r.get("claim_types") else [],
            })

    # Trend analysis
    if len(timeline) >= 3:
        recent = sum(t["claims"] for t in timeline[-3:])
        earlier = sum(t["claims"] for t in timeline[:-3]) / max(1, len(timeline) - 3) * 3
        trend = "growing" if recent > earlier * 1.2 else "stable" if recent > earlier * 0.8 else "declining"
    else:
        trend = "insufficient_data"

    return {
        "target": sym,
        "timeline": timeline,
        "total_claims": cumulative,
        "trend": trend,
    }


@router.get("/growth")
async def platform_growth():
    """Get platform-wide evidence growth metrics."""
    # Sources over time
    source_growth = await fetch("""
        SELECT
            DATE_TRUNC('month', created_at) as month,
            COUNT(*) as new_sources
        FROM sources
        WHERE created_at IS NOT NULL
        GROUP BY DATE_TRUNC('month', created_at)
        ORDER BY month DESC
        LIMIT 12
    """)

    # Claims over time
    claim_growth = await fetch("""
        SELECT
            DATE_TRUNC('month', created_at) as month,
            COUNT(*) as new_claims
        FROM claims
        WHERE created_at IS NOT NULL
        GROUP BY DATE_TRUNC('month', created_at)
        ORDER BY month DESC
        LIMIT 12
    """)

    return {
        "source_growth": [{"month": str(r["month"])[:10], "count": r["new_sources"]} for r in source_growth],
        "claim_growth": [{"month": str(r["month"])[:10], "count": r["new_claims"]} for r in claim_growth],
    }
