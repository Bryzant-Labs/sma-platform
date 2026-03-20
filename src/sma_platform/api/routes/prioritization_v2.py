"""M5 Target Prioritization Engine v2 — API endpoints.

Routes:
- GET /prioritize/v2/targets          -- All targets ranked by 6-dimension composite
- GET /prioritize/v2/target/{symbol}  -- Deep profile for one target
- GET /prioritize/v2/compare          -- Side-by-side comparison of targets
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ...reasoning.target_prioritizer_v2 import (
    WEIGHTS,
    compare_targets_v2,
    get_target_profile,
    prioritize_all_targets,
)

router = APIRouter()


@router.get("/prioritize/v2/targets")
async def rank_all_targets_v2(
    min_score: Optional[float] = Query(
        default=None,
        ge=0.0,
        le=1.0,
        description="Filter: only return targets with composite_score >= this value.",
    ),
    tier: Optional[str] = Query(
        default=None,
        description="Filter by tier: tier_1_actionable, tier_2_promising, tier_3_exploratory, tier_4_insufficient.",
    ),
    limit: Optional[int] = Query(
        default=None,
        ge=1,
        le=100,
        description="Limit number of results.",
    ),
):
    """Rank all targets across 6 dimensions: evidence convergence (25%),
    druggability (20%), structural uniqueness (15%), clinical validation (15%),
    conservation (10%), and novelty (15%).

    Integrates convergence engine scores, DiffDock screening, ESM-2 structural
    analysis, drug outcomes, and cross-species conservation data.

    Returns targets sorted by composite score with per-dimension breakdown,
    strengths, weaknesses, and tier classification.
    """
    results = await prioritize_all_targets()

    if min_score is not None:
        results = [r for r in results if r["composite_score"] >= min_score]

    if tier is not None:
        results = [r for r in results if r["tier"] == tier]

    if limit is not None:
        results = results[:limit]

    return {
        "count": len(results),
        "weights": WEIGHTS,
        "tiers": {
            "tier_1_actionable": ">= 0.60 — ready for drug design pipeline",
            "tier_2_promising": ">= 0.40 — strong candidate, needs validation",
            "tier_3_exploratory": ">= 0.20 — emerging target, needs more evidence",
            "tier_4_insufficient": "< 0.20 — insufficient data for prioritization",
        },
        "targets": results,
    }


@router.get("/prioritize/v2/target/{symbol}")
async def get_target_profile_v2(symbol: str):
    """Deep multi-criteria profile for a single target.

    Returns composite score, 6-dimension scores with detailed breakdowns,
    rank among all targets, strengths/weaknesses analysis, and radar chart data.
    """
    result = await get_target_profile(symbol)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/prioritize/v2/compare")
async def compare_target_priorities_v2(
    targets: str = Query(
        ...,
        description="Comma-separated target symbols, e.g. SMN2,CORO1C,UBA1",
    ),
):
    """Side-by-side comparison of multiple targets across all 6 dimensions.

    Returns each target's scorecard, dimension leaders, radar chart data,
    and score gaps from the top-ranked target.
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

    result = await compare_targets_v2(symbols)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
