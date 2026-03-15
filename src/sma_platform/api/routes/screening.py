"""Drug screening endpoints — computational molecular analysis."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter()


class SmilesInput(BaseModel):
    smiles: str


@router.post("/screen/compounds", dependencies=[Depends(require_admin_key)])
async def screen_all_compounds():
    """Screen all ChEMBL compounds for drug-likeness, BBB permeability, and CNS MPO.

    Analyzes compounds from graph_edges (ChEMBL bioactivity data) and returns:
    - Lipinski Rule of Five compliance
    - Blood-Brain Barrier permeability prediction
    - CNS Multi-Parameter Optimization score
    - QED (Quantitative Estimate of Drug-likeness)
    - PAINS filter alerts
    - Top candidate ranking
    """
    try:
        from ...reasoning.drug_screener import screen_all_compounds as do_screen
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"RDKit not installed on this server. Install: pip install rdkit. Error: {e}",
        )

    start = datetime.now(timezone.utc)
    result = await do_screen()
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration_secs"] = round(duration, 2)
    return result


@router.post("/screen/smiles")
async def screen_smiles(body: SmilesInput):
    """Screen a single SMILES string for drug-likeness properties.

    No authentication required — useful for quick lookups.
    """
    try:
        from ...reasoning.drug_screener import screen_single_smiles
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"RDKit not installed. Install: pip install rdkit. Error: {e}",
        )

    if not body.smiles or len(body.smiles) > 5000:
        raise HTTPException(400, "Invalid SMILES string")

    result = await screen_single_smiles(body.smiles)
    if result is None:
        raise HTTPException(400, "Could not parse SMILES — check syntax")
    return result


@router.post("/screen/admet")
async def screen_admet(body: SmilesInput):
    """Predict ADMET properties for a single SMILES string."""
    try:
        from ...reasoning.admet_predictor import predict_admet
        from dataclasses import asdict
    except ImportError as e:
        raise HTTPException(503, f"RDKit not installed: {e}")

    if not body.smiles or len(body.smiles) > 5000:
        raise HTTPException(400, "Invalid SMILES string")

    result = predict_admet(body.smiles)
    if result is None:
        raise HTTPException(400, "Could not parse SMILES — check syntax")
    return asdict(result)


@router.get("/screen/admet/batch", dependencies=[Depends(require_admin_key)])
async def screen_admet_batch():
    """Run ADMET prediction on all ChEMBL compounds."""
    try:
        from ...reasoning.admet_predictor import batch_predict_admet
    except ImportError as e:
        raise HTTPException(503, f"RDKit not installed: {e}")

    start = datetime.now(timezone.utc)
    result = await batch_predict_admet()
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration_secs"] = round(duration, 2)
    return result


@router.get("/screen/repurposing")
async def get_repurposing_candidates(
    top_n: int = Query(default=30, ge=1, le=100),
):
    """Get ranked drug repurposing candidates for SMA."""
    from ...reasoning.repurposing import find_repurposing_candidates

    start = datetime.now(timezone.utc)
    result = await find_repurposing_candidates(top_n=top_n)
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration_secs"] = round(duration, 2)
    return result


@router.get("/screen/candidates")
async def get_top_candidates(
    top_n: int = Query(default=50, ge=1, le=200),
):
    """Get integrated ranked drug candidates combining screening, ADMET, repurposing, and target scores.

    Each candidate has an integrated_score (0-1) computed from:
    - Drug-likeness (QED + Lipinski): 15%
    - BBB/CNS access: 15%
    - ADMET safety: 20%
    - Potency (pChEMBL): 15%
    - Target relevance: 20%
    - Repurposing evidence: 15%
    """
    try:
        from ...reasoning.candidate_ranker import rank_all_candidates
    except ImportError as e:
        raise HTTPException(503, f"RDKit not installed: {e}")

    start = datetime.now(timezone.utc)
    result = await rank_all_candidates(top_n=top_n)
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration_secs"] = round(duration, 2)
    return result
