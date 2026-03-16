"""Biomarker Atlas API — structured biomarker aggregation across 4 layers.

Endpoints:
- GET /biomarker/atlas              — full atlas: all biomarker claims categorized by layer
- GET /biomarker/treatment-response — biomarker claims mentioning treatment response
- GET /biomarker/target/{symbol}    — biomarker claims linked to a specific target
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Path

from ...reasoning.biomarker_atlas import (
    BIOMARKER_LAYERS,
    build_atlas,
    biomarkers_for_target,
    treatment_response_biomarkers,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/biomarker", tags=["biomarker"])


@router.get("/atlas")
async def get_atlas():
    """Full biomarker atlas: all biomarker claims categorized into 4 layers
    (molecular, imaging, functional, fluid).

    Returns claim counts per layer, per marker, evidence sources, and
    uncategorized claims that didn't match any layer keywords.
    """
    try:
        atlas = await build_atlas()
        return atlas
    except Exception as e:
        logger.error(f"Failed to build biomarker atlas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to build biomarker atlas: {str(e)}")


@router.get("/treatment-response")
async def get_treatment_response():
    """Find biomarker claims that mention treatment response.

    Searches for keywords: nusinersen, risdiplam, post-treatment,
    change from baseline, onasemnogene, zolgensma, spinraza, evrysdi.
    Each result includes layer classification and matched treatment keywords.
    """
    try:
        results = await treatment_response_biomarkers()
        return {
            "total": len(results),
            "biomarkers": results,
        }
    except Exception as e:
        logger.error(f"Failed to get treatment-response biomarkers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get treatment-response biomarkers: {str(e)}")


@router.get("/target/{symbol}")
async def get_biomarkers_for_target(
    symbol: str = Path(..., description="Target gene/protein symbol (e.g. SMN1, SMN2, NfL)"),
):
    """Biomarker claims linked to a specific target.

    Returns claims grouped by layer (molecular, imaging, functional, fluid),
    with a separate treatment-response subset.
    """
    try:
        result = await biomarkers_for_target(symbol)
        return result
    except Exception as e:
        logger.error(f"Failed to get biomarkers for target '{symbol}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get biomarkers for target: {str(e)}")


@router.get("/layers")
async def get_layer_definitions():
    """Return the biomarker layer definitions (markers and keywords per layer).

    Useful for frontend to display layer metadata without querying claims.
    """
    return {
        "layers": {
            name: {
                "markers": defn["markers"],
                "keywords": defn["keywords"],
            }
            for name, defn in BIOMARKER_LAYERS.items()
        }
    }
