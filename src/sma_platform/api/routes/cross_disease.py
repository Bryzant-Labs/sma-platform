"""Cross-Disease Drug Repurposing API."""

from __future__ import annotations
import logging
from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/repurpose", tags=["cross-disease"])


@router.get("/candidates")
async def list_repurposing_candidates(min_score: float = Query(default=0.0, ge=0, le=1)):
    """List cross-disease drug repurposing candidates for SMA."""
    from ...reasoning.cross_disease_repurposing import get_repurposing_candidates
    candidates = await get_repurposing_candidates(min_score)
    return {"candidates": candidates, "total": len(candidates)}


@router.get("/candidates/target/{symbol}")
async def candidates_by_target(symbol: str):
    """Get repurposing candidates targeting a specific SMA protein."""
    from ...reasoning.cross_disease_repurposing import get_candidates_by_target
    candidates = await get_candidates_by_target(symbol)
    return {"target": symbol, "candidates": candidates, "total": len(candidates)}


@router.get("/candidates/disease/{disease}")
async def candidates_by_disease(disease: str):
    """Get repurposing candidates from a specific disease (ALS, DMD, etc.)."""
    from ...reasoning.cross_disease_repurposing import get_candidates_by_disease
    candidates = await get_candidates_by_disease(disease)
    return {"disease": disease, "candidates": candidates, "total": len(candidates)}
