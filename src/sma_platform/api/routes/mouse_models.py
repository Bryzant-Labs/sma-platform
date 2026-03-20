from __future__ import annotations
import logging
from fastapi import APIRouter, Query
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/models", tags=["mouse-models"])

@router.get("/mouse")
async def list_mouse_models():
    """List all SMA mouse models with phenotype data."""
    from ...reasoning.mouse_models import get_mouse_models
    models = get_mouse_models()
    return {"models": models, "total": len(models)}

@router.get("/mouse/methodology")
async def methodology_problems():
    """Motor neuron counting reproducibility problem (0-80% variation)."""
    from ...reasoning.mouse_models import get_methodology_problems
    return get_methodology_problems()

@router.get("/mouse/compare")
async def compare(a: str = Query(...), b: str = Query(...)):
    """Compare two SMA mouse models."""
    from ...reasoning.mouse_models import compare_models
    return compare_models(a, b)
