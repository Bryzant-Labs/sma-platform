"""Molecular docking score prediction endpoints (Phase 6.1)."""

from __future__ import annotations

import logging
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...reasoning.docking_scorer import (
    BINDING_POCKETS,
    predict_docking_score,
    score_top_compounds,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class DockInput(BaseModel):
    compound_id: str = "custom"
    mw: float
    logp: float
    hbd: int = 2
    hba: int = 4
    tpsa: float = 60.0
    rotatable_bonds: int = 5
    aromatic_rings: int = 2
    pocket: str = "SMN2_SPLICE_SITE"
    bbb_permeable: bool = False
    pchembl: float | None = None


@router.get("/dock/score")
async def dock_top_compounds(
    pocket: str = Query(default="SMN2_SPLICE_SITE", description="Binding pocket key"),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Score top drug-like compounds against a target binding pocket.

    Pharmacophore-based scoring proxy — predicts binding affinity from
    molecular descriptors and pocket characteristics without requiring
    AutoDock Vina installation.

    Available pockets: SMN2_ISS_N1, SMN2_SPLICE_SITE, HDAC_CATALYTIC,
    MTOR_ATP_SITE, NCALD_CALCIUM_SITE, PLS3_ACTIN_INTERFACE, UBA1_UBIQUITIN_SITE
    """
    if pocket not in BINDING_POCKETS:
        raise HTTPException(
            400,
            f"Unknown pocket: {pocket}. Available: {', '.join(BINDING_POCKETS.keys())}",
        )
    return await score_top_compounds(pocket_key=pocket, limit=limit)


@router.post("/dock/score")
async def dock_custom_compound(body: DockInput):
    """Score a single compound against a binding pocket."""
    if body.pocket not in BINDING_POCKETS:
        raise HTTPException(
            400,
            f"Unknown pocket: {body.pocket}. Available: {', '.join(BINDING_POCKETS.keys())}",
        )

    result = predict_docking_score(
        compound_id=body.compound_id,
        mw=body.mw,
        logp=body.logp,
        hbd=body.hbd,
        hba=body.hba,
        tpsa=body.tpsa,
        rotatable_bonds=body.rotatable_bonds,
        aromatic_rings=body.aromatic_rings,
        pocket_key=body.pocket,
        bbb_permeable=body.bbb_permeable,
        pchembl=body.pchembl,
    )
    if result is None:
        raise HTTPException(400, "Could not compute docking score")
    return asdict(result)


@router.get("/dock/pockets")
async def list_binding_pockets():
    """List all available target binding pockets with characteristics."""
    return {
        "total": len(BINDING_POCKETS),
        "pockets": {k: asdict(v) for k, v in BINDING_POCKETS.items()},
    }
