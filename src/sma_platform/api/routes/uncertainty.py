"""Uncertainty Quantification API routes.

Bootstrap confidence intervals on convergence scores — measures how
robust our evidence assessments are for each target.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ...reasoning.uncertainty import (
    compute_all_intervals,
    compute_all_uncertainties,
    compute_uncertainty,
    compute_uncertainty_intervals,
    uncertainty_summary,
)

router = APIRouter()


@router.get("/uncertainty/target/{symbol}")
async def get_target_uncertainty(
    symbol: str,
    n_bootstrap: int = Query(
        default=500,
        ge=50,
        le=5000,
        description="Number of bootstrap resamples (higher = more precise, slower).",
    ),
):
    """Bootstrap confidence intervals for a single target's convergence score.

    Resamples claims with replacement N times and computes a simplified
    convergence score for each resample. Returns mean, std, 95% CI,
    and a 10-bin histogram of the bootstrap distribution.
    """
    result = await compute_uncertainty(symbol, n_bootstrap=n_bootstrap)
    if "error" in result and "not found" in result["error"].lower():
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/uncertainty/all")
async def get_all_uncertainties():
    """Bootstrap uncertainty for all targets with >10 claims.

    Returns a list sorted by CI width (descending) — targets with the
    widest confidence intervals (most uncertain) appear first.
    """
    results = await compute_all_uncertainties()
    return {
        "count": len(results),
        "sort": "ci_width_descending",
        "targets": results,
    }


@router.get("/uncertainty/summary")
async def get_uncertainty_summary():
    """Overall platform uncertainty report.

    Shows what fraction of targets have narrow CIs (<0.1) vs wide (>0.3),
    plus the top-5 most and least uncertain targets.
    """
    return await uncertainty_summary()


@router.get("/uncertainty/intervals")
async def get_uncertainty_intervals(
    n_bootstrap: int = Query(
        default=50,
        ge=20,
        le=2000,
        description="Number of bootstrap resamples per target.",
    ),
):
    """Compute 95% confidence intervals for all target convergence scores.

    Uses the full 5-dimension convergence engine formula (volume,
    lab_independence, method_diversity, temporal_trend, replication)
    with bootstrap resampling. Every prediction gets error bars.
    """
    results = await compute_all_intervals(n_bootstrap=n_bootstrap)
    return {
        "targets": results,
        "total": len(results),
        "method": "bootstrap",
        "scoring": "convergence_engine_5d",
        "n_bootstrap": n_bootstrap,
    }


@router.get("/uncertainty/intervals/{symbol}")
async def get_target_uncertainty_interval(
    symbol: str,
    n_bootstrap: int = Query(
        default=100,
        ge=20,
        le=5000,
        description="Number of bootstrap resamples (higher = more precise, slower).",
    ),
):
    """Compute uncertainty interval for a specific target.

    Returns the convergence score with 95% CI, e.g.
    "63% (95% CI: 58-68%)" instead of just "63%".
    """
    result = await compute_uncertainty_intervals(symbol, n_bootstrap=n_bootstrap)
    if "error" in result and "not found" in result.get("error", "").lower():
        raise HTTPException(status_code=404, detail=result["error"])
    return result
