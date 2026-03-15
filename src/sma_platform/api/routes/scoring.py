"""Target prioritization scoring endpoints (Phase 2).

Provides endpoints to score, rank, and inspect targets across 7 dimensions,
plus hypothesis prioritization with tier assignments.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from ...reasoning.prioritizer import (
    get_cached_scores,
    get_target_scorecard,
    score_all_targets,
    score_target,
)
from ...reasoning.hypothesis_prioritizer import prioritize_all_hypotheses
from ..auth import require_admin_key

router = APIRouter()


@router.get("/scores")
async def list_scores(
    min_score: Optional[float] = Query(
        default=None,
        ge=0.0,
        le=1.0,
        description="Filter: only return targets with composite_score >= this value.",
    ),
):
    """Score and rank all targets by composite prioritization score.

    Returns cached scores if available (persist across restarts).
    Use POST /scores/refresh to recompute.
    """
    results = await get_cached_scores()
    if results is None:
        results = await score_all_targets()

    if min_score is not None:
        results = [r for r in results if r["composite_score"] >= min_score]

    return {
        "count": len(results),
        "targets": results,
    }


@router.get("/scores/{target_id}")
async def get_score(target_id: UUID):
    """Full scorecard for a single target."""
    scorecard = await get_target_scorecard(str(target_id))
    if "error" in scorecard:
        raise HTTPException(status_code=404, detail=scorecard["error"])
    return scorecard


@router.get("/hypotheses/prioritized")
async def get_prioritized_hypotheses(
    tier: Optional[str] = Query(
        default=None,
        description="Filter by tier: A (top 5), B (6-15), C (rest).",
    ),
):
    """Rank all hypotheses by multi-criteria score, assign action tiers.

    Tier A: Top 5 high-conviction hypotheses ready for Phase 3.
    Tier B: Medium-priority, need more evidence or refinement.
    Tier C: Low-priority or insufficient data.
    """
    result = await prioritize_all_hypotheses()

    if tier:
        tier_upper = tier.upper()
        if tier_upper == "A":
            return {"tier": "A", "count": len(result["tier_a"]), "hypotheses": result["tier_a"]}
        elif tier_upper == "B":
            return {"tier": "B", "count": len(result["tier_b"]), "hypotheses": result["tier_b"]}
        elif tier_upper == "C":
            return {"tier": "C", "count": len(result["tier_c"]), "hypotheses": result["tier_c"]}

    return {
        "total": result["total"],
        "tier_a_count": len(result["tier_a"]),
        "tier_b_count": len(result["tier_b"]),
        "tier_c_count": len(result["tier_c"]),
        "tier_a": result["tier_a"],
        "tier_b": result["tier_b"],
        "tier_c": result["tier_c"],
    }


@router.post("/scores/refresh", dependencies=[Depends(require_admin_key)])
async def refresh_scores():
    """Re-run scoring for all targets (admin only)."""
    results = await score_all_targets()
    return {
        "status": "ok",
        "targets_scored": len(results),
        "top_target": results[0]["symbol"] if results else None,
        "top_score": results[0]["composite_score"] if results else None,
    }
