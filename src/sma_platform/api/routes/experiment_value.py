"""EVE (Expected Value of Experiment) and Assay-Ready API routes."""

from __future__ import annotations

from fastapi import APIRouter, Path, Query

from ...reasoning.assay_ready import get_assay_ready, get_assay_ready_top3
from ...reasoning.experiment_value import score_hypotheses_eve, score_single_eve

router = APIRouter()


# ---------------------------------------------------------------------------
# EVE scoring endpoints
# ---------------------------------------------------------------------------

@router.get("/experiment-value/hypotheses")
async def eve_scored_hypotheses(
    limit: int = Query(default=50, ge=1, le=200, description="Max hypotheses to score"),
):
    """Get all hypotheses ranked by Expected Value of Experiment (EVE).

    EVE = P(success) * Impact / (Cost + Time)

    Returns hypotheses sorted by EVE score descending, with full breakdown
    of success probability, impact, recommended assay, cost, and timeline.
    """
    results = await score_hypotheses_eve(limit=limit)
    return {
        "total": len(results),
        "hypotheses": results,
        "formula": "EVE = P(success) * Impact / (Cost_K + Time_months)",
        "insight": (
            "Hypotheses are ranked by expected information gain per dollar and per week. "
            "High EVE scores indicate cheap, fast experiments on well-supported hypotheses."
        ),
    }


@router.get("/experiment-value/hypothesis/{hypothesis_id}")
async def eve_single_hypothesis(
    hypothesis_id: str = Path(..., description="UUID of the hypothesis to score"),
):
    """Get EVE score for a single hypothesis with full breakdown."""
    return await score_single_eve(hypothesis_id)


# ---------------------------------------------------------------------------
# Assay-ready endpoints
# ---------------------------------------------------------------------------

@router.get("/assay-ready/top3")
async def assay_ready_top3():
    """Get the top 3 EVE-scored hypotheses in full assay-ready format.

    Returns complete experiment specifications: biological rationale,
    recommended assay, model system, readouts, Go/No-Go criteria,
    estimated cost, timeline, and clinical translatability notes.

    This is the primary output for researchers deciding what to test next.
    """
    results = await get_assay_ready_top3()
    return {
        "total": len(results),
        "assay_ready_hypotheses": results,
        "insight": (
            "These are the 3 best experiments to run next, ranked by expected "
            "value per dollar and per week. Each includes a complete protocol "
            "specification with Go/No-Go decision criteria."
        ),
    }


@router.get("/assay-ready/hypothesis/{hypothesis_id}")
async def assay_ready_single(
    hypothesis_id: str = Path(..., description="UUID of the hypothesis"),
):
    """Get a single hypothesis in full assay-ready format.

    Returns a complete experiment specification that a CRO or wet-lab
    team can execute directly.
    """
    return await get_assay_ready(hypothesis_id)
