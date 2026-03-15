"""Translation & Impact API routes (Phase 11)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from ...reasoning.translation import (
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
