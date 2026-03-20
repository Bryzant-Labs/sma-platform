"""Translation & Impact API routes (Phase 11)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ...reasoning.translation import (
    GRANT_FORMATS,
    generate_grant_export,
    get_regulatory_pathways,
    get_grant_templates,
    get_validation_pipeline,
    validate_hypothesis,
)

router = APIRouter()


@router.get("/translate/regulatory")
async def regulatory_pathways():
    """Get regulatory pathway map for SMA therapeutics (FDA/EMA)."""
    return get_regulatory_pathways()


@router.get("/translate/grants")
async def grant_templates():
    """Get grant application templates for SMA research."""
    return get_grant_templates()


@router.get("/translate/grants/formats")
async def grant_formats():
    """List supported grant export formats and their requirements."""
    return {
        "formats": {
            k: {
                "funder": v["funder"],
                "mechanism": v["mechanism"],
                "budget_range": v["budget_range"],
                "duration_years": v["duration_years"],
            }
            for k, v in GRANT_FORMATS.items()
        },
        "total": len(GRANT_FORMATS),
    }


@router.get("/translate/grants/export/{symbol}")
async def export_grant_section(
    symbol: str,
    format: str = Query(
        default="NIH_R01",
        description="Grant format: NIH_R01, NIH_R21, ERC_StG, CURE_SMA",
    ),
):
    """Generate grant-ready text for a target.

    Fetches convergence score, top claims, screening hits, experiment
    suggestions, and assay recommendations, then composes structured
    prose sections suitable for the specified grant format.

    Supported formats: NIH_R01, NIH_R21, ERC_StG, CURE_SMA.
    """
    result = await generate_grant_export(symbol, grant_format=format)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/translate/validation")
async def validation_pipeline():
    """Get 5-level hypothesis validation pipeline."""
    return get_validation_pipeline()


@router.get("/translate/validate")
async def validate(
    hypothesis_id: str = Query(..., description="Hypothesis identifier"),
    evidence_score: float = Query(..., ge=0, le=1.0, description="Composite evidence score (0-1)"),
    twin_improvement: float = Query(..., ge=0, le=1.0, description="Digital twin functional improvement (0-1)"),
):
    """Run a hypothesis through the validation pipeline gate check."""
    return validate_hypothesis(hypothesis_id, evidence_score, twin_improvement)
