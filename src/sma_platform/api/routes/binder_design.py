"""Protein Binder Design API routes (Proteina-Complexa, GTC 2026)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/binder", tags=["binder-design"])


class BinderDesignRequest(BaseModel):
    target: str = Field(default="SMN2", description="SMA target protein name")
    n_designs: int = Field(default=10, ge=1, le=100, description="Number of binder designs")
    pdb_content: Optional[str] = Field(default=None, description="Custom PDB content")


@router.get("/targets")
async def list_binder_targets():
    """List SMA targets available for protein binder design."""
    from ...reasoning.protein_binder_design import get_binder_targets
    targets = await get_binder_targets()
    return {"targets": targets, "total": len(targets)}


@router.post("/design", dependencies=[Depends(require_admin_key)])
async def design_protein_binder(req: BinderDesignRequest):
    """Design protein binders for an SMA target using Proteina-Complexa (GTC 2026).

    This is a new therapeutic modality — designed protein binders that can
    target SMA-relevant proteins with high specificity.

    NOTE: Requires GPU. Returns planned-status if GPU not configured.
    """
    from ...reasoning.protein_binder_design import design_binders

    try:
        result = await design_binders(
            target_name=req.target,
            n_designs=req.n_designs,
            pdb_content=req.pdb_content,
        )
    except Exception as e:
        logger.error("Binder design failed: %s", e, exc_info=True)
        raise HTTPException(500, detail=f"Binder design failed: {e}")

    return result
