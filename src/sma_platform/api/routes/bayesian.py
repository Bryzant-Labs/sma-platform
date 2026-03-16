"""Bayesian evidence convergence API routes.

Provides endpoints for Bayesian posterior scoring of targets,
replacing simple weighted averages with proper Beta-Binomial updating.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ...reasoning.bayesian_convergence import (
    bayesian_all_targets,
    bayesian_compare,
    bayesian_score,
)

router = APIRouter()


@router.get("/bayesian/target/{symbol}")
async def get_bayesian_score(symbol: str):
    """Bayesian posterior for a single target's therapeutic validity.

    Uses Beta(1,1) prior updated with claim evidence. Returns posterior
    mean, mode, 95% credible interval, Bayes factor, and evidence sufficiency.
    """
    result = await bayesian_score(symbol)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/bayesian/all")
async def get_bayesian_all(
    min_claims: int = Query(default=0, ge=0, description="Minimum claim count to include"),
    sufficient_only: bool = Query(default=False, description="Only return targets with sufficient evidence"),
):
    """Bayesian posteriors for all targets, sorted by posterior mean.

    Optionally filter by minimum claim count or evidence sufficiency.
    """
    results = await bayesian_all_targets()

    if min_claims > 0:
        results = [r for r in results if r["claim_count"] >= min_claims]
    if sufficient_only:
        results = [r for r in results if r["evidence_sufficiency"]]

    return {
        "count": len(results),
        "targets": results,
    }


@router.get("/bayesian/compare")
async def get_bayesian_compare(
    a: str = Query(..., description="Symbol of target A (e.g. SMN2)"),
    b: str = Query(..., description="Symbol of target B (e.g. PLS3)"),
):
    """Compare Bayesian evidence between two targets.

    Returns P(A > B) via Monte Carlo sampling, posterior summaries,
    and a human-readable verdict.
    """
    result = await bayesian_compare(a, b)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
