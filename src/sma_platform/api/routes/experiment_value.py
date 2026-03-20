"""EVE (Expected Value of Experiment) and Assay-Ready API routes.

Two scoring approaches:
1. Hypothesis-centric EVE — scores individual hypotheses from the DB.
2. Target-centric EV — scores targets using hardcoded impact/cost tables.
   Answers: "If I have $50K and 3 months, which experiment should I run first?"
"""

from __future__ import annotations

from fastapi import APIRouter, Path, Query

from ...reasoning.assay_ready import get_assay_ready, get_assay_ready_top3
from ...reasoning.experiment_value import (
    compute_experiment_value,
    rank_all_experiments,
    score_hypotheses_eve,
    score_single_eve,
)

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
# Target-centric EV scoring endpoints
# ---------------------------------------------------------------------------
# EV = P(success) * Scientific_Impact / (Cost_K / 10)
# Designed for researchers deciding which experiment to run first.

@router.get("/experiment-value/rankings")
async def ev_target_rankings(
    budget_k: float | None = Query(
        default=None, ge=1, le=1000,
        description="Max budget in $K — only show targets affordable within this budget",
    ),
    max_weeks: int | None = Query(
        default=None, ge=1, le=52,
        description="Max timeline in weeks — only show targets achievable within this window",
    ),
):
    """Rank all targets by Expected Value of experiment.

    EV = P(success) * Scientific_Impact / (Cost_K / 10)

    Answers: "If I have $50K and 3 months, which experiment should I run first?"

    Optionally filter by budget and/or timeline constraints. Targets are
    ranked by EV score descending (higher = better ROI).
    """
    results = await rank_all_experiments(budget_k=budget_k, max_weeks=max_weeks)
    total_cost = sum(r["breakdown"]["cost_k"] for r in results)
    return {
        "total": len(results),
        "total_cost_k": total_cost,
        "filters": {
            "budget_k": budget_k,
            "max_weeks": max_weeks,
        },
        "rankings": results,
        "formula": "EV = P(success) * Scientific_Impact / (Cost_K / 10)",
        "insight": (
            "Targets are ranked by expected scientific return per dollar invested. "
            "High EV scores indicate well-supported targets with high impact "
            "relative to experiment cost. Use budget_k and max_weeks filters "
            "to constrain to your available resources."
        ),
    }


@router.get("/experiment-value/target/{symbol}")
async def ev_single_target(
    symbol: str = Path(..., description="Target gene symbol (e.g. SMN2, CORO1C, PLS3)"),
    convergence: str | None = Query(
        default=None,
        description="Override convergence level: very_high, high, medium, low",
    ),
):
    """Get detailed EV score for a single target with full breakdown.

    EV = P(success) * Scientific_Impact / (Cost_K / 10)

    If convergence is not provided, it is looked up from the convergence_scores
    table in the database. Pass ?convergence=high to override.
    """
    result = await compute_experiment_value(
        target=symbol,
        convergence_score=convergence,
    )
    return result


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
