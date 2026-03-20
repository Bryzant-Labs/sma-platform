"""Biomarker Atlas API — curated catalog + structured claim aggregation.

Endpoints:
- GET /biomarker/atlas              — full atlas: curated catalog + DB claims by layer
- GET /biomarker/atlas/{category}   — filter curated catalog by category
- GET /biomarker/treatment-response — biomarkers for monitoring treatment response
- GET /biomarker/target/{symbol}    — biomarker claims linked to a specific target
- GET /biomarker/layers             — layer/category definitions
- GET /biomarker/catalog            — curated catalog with optional filters
- GET /biomarker/catalog/summary    — catalog statistics
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query

from ...reasoning.biomarker_atlas import (
    BIOMARKER_CATEGORIES,
    BIOMARKER_LAYERS,
    BIOMARKER_TYPES,
    build_atlas,
    biomarkers_for_target,
    get_catalog_summary,
    get_curated_catalog,
    get_treatment_response_catalog,
    treatment_response_biomarkers,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/biomarker", tags=["biomarker"])


@router.get("/atlas")
async def get_atlas():
    """Full biomarker atlas: curated reference catalog combined with
    dynamically aggregated claims from the evidence database.

    Returns:
    - curated_catalog: expert-curated biomarkers with PMID references
    - catalog_summary: counts by category, type, validation status
    - claims: DB-sourced claims categorized into layers
    """
    try:
        claims_atlas = await build_atlas()
        catalog = get_curated_catalog()
        summary = get_catalog_summary()
        return {
            "curated_catalog": catalog,
            "catalog_summary": summary,
            **claims_atlas,
        }
    except Exception as e:
        logger.error(f"Failed to build biomarker atlas: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build biomarker atlas: {str(e)}",
        )


@router.get("/atlas/{category}")
async def get_atlas_by_category(
    category: str = Path(
        ...,
        description=(
            "Biomarker category: molecular, functional, imaging, "
            "electrophysiology, fluid"
        ),
    ),
    validated_only: bool = Query(
        False,
        description="If true, return only validated biomarkers",
    ),
):
    """Filter the curated biomarker catalog by category.

    Valid categories: molecular, functional, imaging, electrophysiology.
    Optionally filter to only validated biomarkers.

    Also returns matching DB claims from that layer (if it exists).
    """
    cat_lower = category.lower()
    if cat_lower not in BIOMARKER_CATEGORIES and cat_lower not in BIOMARKER_LAYERS:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Unknown category '{category}'. "
                f"Valid categories: {BIOMARKER_CATEGORIES}"
            ),
        )

    curated = get_curated_catalog(
        category=cat_lower, validated_only=validated_only,
    )

    # Also fetch claim-based data for the matching layer
    layer_claims = None
    if cat_lower in BIOMARKER_LAYERS:
        try:
            full_atlas = await build_atlas()
            layer_claims = full_atlas["layers"].get(cat_lower)
        except Exception as e:
            logger.warning(
                f"Could not fetch DB claims for category '{cat_lower}': {e}",
            )

    return {
        "category": cat_lower,
        "curated_biomarkers": curated,
        "curated_count": len(curated),
        "validated_count": sum(1 for b in curated if b.get("validated")),
        "layer_claims": layer_claims,
    }


@router.get("/treatment-response")
async def get_treatment_response():
    """Biomarkers relevant to monitoring treatment response.

    Returns both:
    1. Curated pharmacodynamic/efficacy biomarkers from the reference catalog
    2. DB claims mentioning treatment-response keywords (nusinersen,
       risdiplam, post-treatment, change from baseline, etc.)
    """
    try:
        db_results = await treatment_response_biomarkers()
        curated = get_treatment_response_catalog()
        return {
            "curated_treatment_biomarkers": curated,
            "curated_count": len(curated),
            "total_claims": len(db_results),
            "biomarkers": db_results,
        }
    except Exception as e:
        logger.error(
            f"Failed to get treatment-response biomarkers: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get treatment-response biomarkers: {str(e)}",
        )


@router.get("/target/{symbol}")
async def get_biomarkers_for_target(
    symbol: str = Path(
        ...,
        description="Target gene/protein symbol (e.g. SMN1, SMN2, NfL)",
    ),
):
    """Biomarker claims linked to a specific target.

    Returns claims grouped by layer (molecular, imaging, functional,
    electrophysiology, fluid), with a separate treatment-response subset.
    """
    try:
        result = await biomarkers_for_target(symbol)
        return result
    except Exception as e:
        logger.error(
            f"Failed to get biomarkers for target '{symbol}': {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get biomarkers for target: {str(e)}",
        )


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
        },
        "categories": BIOMARKER_CATEGORIES,
        "types": BIOMARKER_TYPES,
    }


@router.get("/catalog")
async def get_catalog(
    category: Optional[str] = Query(
        None,
        description=(
            "Filter by category: molecular, functional, imaging, "
            "electrophysiology"
        ),
    ),
    biomarker_type: Optional[str] = Query(
        None,
        alias="type",
        description=(
            "Filter by type: prognostic, pharmacodynamic, efficacy, "
            "monitoring, exploratory"
        ),
    ),
    validated_only: bool = Query(
        False,
        description="If true, return only validated biomarkers",
    ),
):
    """Query the curated SMA biomarker reference catalog.

    Supports filtering by category, type, and validation status.
    No database required — returns instantly from the in-memory catalog.
    """
    if category and category.lower() not in BIOMARKER_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown category '{category}'. "
                f"Valid: {BIOMARKER_CATEGORIES}"
            ),
        )
    if biomarker_type and biomarker_type.lower() not in BIOMARKER_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown type '{biomarker_type}'. "
                f"Valid: {BIOMARKER_TYPES}"
            ),
        )

    results = get_curated_catalog(
        category=category,
        biomarker_type=biomarker_type,
        validated_only=validated_only,
    )
    return {
        "biomarkers": results,
        "total": len(results),
        "filters": {
            "category": category,
            "type": biomarker_type,
            "validated_only": validated_only,
        },
    }


@router.get("/catalog/summary")
async def get_catalog_stats():
    """Summary statistics for the curated biomarker catalog.

    Returns counts by category, type, and validation status.
    """
    return get_catalog_summary()
