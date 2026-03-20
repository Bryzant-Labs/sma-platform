"""Organoid/NMJ Validation Scorecard API routes.

Endpoints:
- GET /organoid/scorecard          — score all targets for testability
- GET /organoid/scorecard/{symbol} — score a specific target
- GET /organoid/models             — list available model systems
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Path, Query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/organoid", tags=["organoid-scorecard"])


@router.get("/scorecard")
async def get_organoid_scorecard():
    """Score testability of all SMA target predictions in organoid/NMJ models.

    Returns a ranked list of targets with their best model systems,
    testability scores, estimated costs, and timelines.
    """
    from ...reasoning.organoid_scorecard import MODEL_SYSTEMS, score_all_targets

    try:
        results = score_all_targets()
        return {
            "scorecard": results,
            "total": len(results),
            "model_systems": len(MODEL_SYSTEMS),
        }
    except Exception as e:
        logger.error(f"Failed to build organoid scorecard: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build organoid scorecard: {str(e)}",
        )


@router.get("/scorecard/{symbol}")
async def get_target_testability(
    symbol: str = Path(
        ..., description="Target gene/pathway (e.g. SMN2, CORO1C, NMJ_MATURATION)"
    ),
    prediction_type: str = Query(
        "binding",
        description="Prediction type: binding, expression, or function",
    ),
):
    """Score testability for a specific target in available model systems.

    Returns recommended models ranked by endpoint overlap, with cost and
    timeline estimates.
    """
    from ...reasoning.organoid_scorecard import score_testability

    try:
        return score_testability(symbol, prediction_type)
    except Exception as e:
        logger.error(
            f"Failed to score testability for '{symbol}': {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to score testability for target: {str(e)}",
        )


@router.get("/models")
async def get_model_systems():
    """List available SMA model systems with capabilities and constraints.

    Useful for the frontend to display model system metadata without
    running the full scorecard.
    """
    from ...reasoning.organoid_scorecard import MODEL_SYSTEMS

    return {
        "model_systems": [
            {
                "name": m["name"],
                "abbreviation": m["abbreviation"],
                "source": m["source"],
                "strengths": m["strengths"],
                "limitations": m["limitations"],
                "testable_endpoints": m["testable_endpoints"],
                "cost": m["cost_range"],
                "timeline": m["timeline"],
            }
            for m in MODEL_SYSTEMS
        ],
        "total": len(MODEL_SYSTEMS),
    }
