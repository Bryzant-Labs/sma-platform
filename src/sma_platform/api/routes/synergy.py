"""Drug-Target Synergy Prediction API routes (M5)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ...reasoning.synergy_predictor import (
    predict_drug_target_synergy,
    predict_synergy_for_drug,
    predict_synergy_for_target,
)

router = APIRouter()


@router.get("/synergy/predictions")
async def synergy_predictions(
    limit: int = Query(default=20, ge=1, le=200, description="Max results to return"),
):
    """Top synergistic drug-target pairs ranked by composite evidence score.

    Composite = 0.3*docking + 0.3*literature + 0.2*pathway + 0.2*claim
    """
    results = await predict_drug_target_synergy(limit=limit)
    return {
        "total": len(results),
        "predictions": results,
        "scoring_weights": {
            "docking": 0.3,
            "literature": 0.3,
            "pathway": 0.2,
            "claim": 0.2,
        },
    }


@router.get("/synergy/drug/{drug_name}")
async def synergy_for_drug(
    drug_name: str,
    limit: int = Query(default=20, ge=1, le=200),
):
    """Synergy predictions for a specific drug across all targets."""
    results = await predict_synergy_for_drug(drug_name, limit=limit)
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No synergy predictions found for drug '{drug_name}'. "
                   "Check spelling or ensure the drug exists in the database.",
        )
    return {
        "drug": drug_name,
        "total": len(results),
        "predictions": results,
    }


@router.get("/synergy/target/{target_symbol}")
async def synergy_for_target(
    target_symbol: str,
    limit: int = Query(default=20, ge=1, le=200),
):
    """Synergy predictions for a specific target across all drugs."""
    results = await predict_synergy_for_target(target_symbol, limit=limit)
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No synergy predictions found for target '{target_symbol}'. "
                   "Check spelling or ensure the target exists in the database.",
        )
    return {
        "target": target_symbol,
        "total": len(results),
        "predictions": results,
    }
