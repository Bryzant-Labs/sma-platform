"""Generative Virtual Screening API routes (GTC 2026 Blueprint)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/screening", tags=["virtual-screening"])


class VirtualScreeningRequest(BaseModel):
    scaffold_smiles: str = Field(default="Nc1ccncc1", description="Starting molecule (default: 4-AP)")
    target: str = Field(default="SMN2", description="SMA target to dock against")
    n_generate: int = Field(default=50, ge=10, le=500, description="Number of molecules to generate")
    pdb_content: Optional[str] = Field(default=None, description="PDB content for docking target")


@router.post("/virtual", dependencies=[Depends(require_admin_key)])
async def run_virtual_screening(req: VirtualScreeningRequest):
    """Run end-to-end generative virtual screening (GTC 2026 Blueprint pattern).

    Pipeline: GenMol (generate) -> RDKit (filter) -> DiffDock (dock) -> Rank.
    Requires NVIDIA_API_KEY for GenMol and DiffDock NIM calls.
    """
    from ...reasoning.virtual_screening import run_virtual_screening as _run

    try:
        result = await _run(
            scaffold_smiles=req.scaffold_smiles,
            target=req.target,
            n_generate=req.n_generate,
            pdb_content=req.pdb_content,
        )
    except Exception as e:
        logger.error("Virtual screening failed: %s", e, exc_info=True)
        raise HTTPException(500, detail=f"Virtual screening pipeline failed: {e}")

    return result
