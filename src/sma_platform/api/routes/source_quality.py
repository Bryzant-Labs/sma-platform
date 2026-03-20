"""Source quality scoring endpoints.

Scores each source paper across 5 dimensions (journal quality, study type,
recency, evidence density, SMA specificity) and returns composite scores.

Also provides journal-tier-based source weighting (3-factor: journal tier,
recency, article type) for fast claim weighting.
"""

from __future__ import annotations

from fastapi import APIRouter, Path, Query

from ...reasoning.source_quality import (
    get_source_quality_distribution,
    score_all_sources,
)
from ...reasoning.source_weigher import (
    weight_all_sources,
    weight_source_by_id,
)

router = APIRouter()


@router.get("/source-quality/scores")
async def list_source_quality_scores(
    limit: int = Query(default=50, ge=1, le=500),
):
    """Score and rank all sources by composite quality score.

    Each source is scored across 5 dimensions (0-1 each):
    - journal_quality: top SMA journals = 1.0, known = 0.5, unknown = 0.3
    - study_type: RCT = 1.0, observational = 0.7, review = 0.6, case = 0.4
    - recency: linear decay from 2026 (1.0) to 2010 (0.3)
    - evidence_density: claims per paper, capped at 20 = 1.0
    - sma_specificity: SMA keyword density in title + abstract

    Composite = 0.25*journal + 0.20*study_type + 0.20*recency + 0.15*density + 0.20*specificity
    """
    results = await score_all_sources(limit=limit)
    return {
        "count": len(results),
        "sources": results,
    }


@router.get("/source-quality/distribution")
async def get_quality_distribution():
    """Aggregate quality distribution across all sources.

    Returns per-dimension averages, tier breakdown (A/B/C), histogram,
    and top-5 highest-scoring sources.
    """
    return await get_source_quality_distribution()


# ---------------------------------------------------------------------------
# Source Quality Weighting (3-factor: journal tier, recency, article type)
# ---------------------------------------------------------------------------

@router.get("/source-quality/weights")
async def source_quality_weights():
    """Compute quality weights for all sources based on journal tier, recency, and type.

    Uses a simplified 3-factor model (vs. the full 5-dimension scoring above):
    - Journal tier: Nature/Science/Cell = 1.0, high-impact specialty = 0.85,
      standard SMA journals = 0.7, other = 0.5
    - Recency: <2yr = 1.0, 2-5yr = 0.8, 5-10yr = 0.6, >10yr = 0.4
    - Article type: primary = 1.0, review = 0.8, correspondence = 0.5

    Composite = 0.40*journal + 0.35*recency + 0.25*type

    Returns aggregate statistics: total sources, high-quality count,
    tier and type distributions, average weight.
    """
    return await weight_all_sources()


@router.get("/source-quality/weights/{source_id}")
async def source_quality_weight_single(
    source_id: str = Path(..., description="UUID of the source"),
):
    """Compute quality weight for a single source by ID."""
    return await weight_source_by_id(source_id)
