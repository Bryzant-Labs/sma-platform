"""Source quality scoring endpoints.

Scores each source paper across 5 dimensions (journal quality, study type,
recency, evidence density, SMA specificity) and returns composite scores.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from ...reasoning.source_quality import (
    get_source_quality_distribution,
    score_all_sources,
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
