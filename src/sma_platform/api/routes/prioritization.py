"""Multi-criteria target prioritization endpoints.

Routes:
- GET /prioritize/targets         -- Rank all targets by composite score
- GET /prioritize/target/{symbol} -- Detailed prioritization for one target
- GET /prioritize/compare         -- Side-by-side comparison of targets
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ...reasoning.target_prioritizer import (
    compare_targets,
    prioritize_single,
    prioritize_targets,
)

router = APIRouter()


@router.get("/prioritize/targets")
async def rank_all_targets(
    min_score: Optional[float] = Query(
        default=None,
        ge=0.0,
        le=1.0,
        description="Filter: only return targets with composite_score >= this value.",
    ),
    tier: Optional[str] = Query(
        default=None,
        description="Filter by tier: tier_1_high, tier_2_medium, tier_3_low, tier_4_insufficient.",
    ),
):
    """Rank all targets across 5 dimensions: evidence convergence (30%),
    biological plausibility (20%), interventionability (20%),
    network centrality (15%), and novelty (15%).

    Returns targets sorted by composite score with per-dimension breakdown.
    """
    results = await prioritize_targets()

    if min_score is not None:
        results = [r for r in results if r["composite_score"] >= min_score]

    if tier is not None:
        results = [r for r in results if r["tier"] == tier]

    return {
        "count": len(results),
        "targets": results,
    }


@router.get("/prioritize/target/{symbol}")
async def get_target_prioritization(symbol: str):
    """Detailed multi-criteria prioritization for a single target.

    Returns composite score, per-dimension scores with detailed breakdowns,
    rank among all targets, and priority tier.
    """
    result = await prioritize_single(symbol)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/prioritize/compare")
async def compare_target_priorities(
    targets: str = Query(
        ...,
        description="Comma-separated target symbols, e.g. SMN2,PLS3,NCALD",
    ),
):
    """Side-by-side comparison of multiple targets across all 5 dimensions.

    Returns each target's scorecard, dimension leaders, and score gaps.
    """
    symbols = [s.strip() for s in targets.split(",") if s.strip()]
    if len(symbols) < 2:
        raise HTTPException(
            status_code=400,
            detail="Provide at least 2 comma-separated target symbols for comparison.",
        )
    if len(symbols) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 targets per comparison.",
        )

    result = await compare_targets(symbols)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
