"""Therapy Combination Ranking API."""

from __future__ import annotations
import logging
from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/combinations", tags=["combinations"])


@router.get("/rank")
async def rank_combinations(limit: int = Query(default=20, ge=1, le=100)):
    """Rank all possible SMA therapy combinations by composite score."""
    from ...reasoning.combination_ranker import rank_all_combinations

    combos = rank_all_combinations()
    return {
        "combinations": combos[:limit],
        "total_evaluated": len(combos),
        "methodology": (
            "Scored on: mechanistic complementarity (30%), "
            "target coverage (25%), evidence strength (25%), "
            "clinical feasibility (15%), route compatibility (5%)"
        ),
    }


@router.get("/top3")
async def top3_combinations():
    """Get the top 3 recommended therapy combinations for SMA."""
    from ...reasoning.combination_ranker import rank_all_combinations

    combos = rank_all_combinations()[:3]
    return {"top_3": combos}
