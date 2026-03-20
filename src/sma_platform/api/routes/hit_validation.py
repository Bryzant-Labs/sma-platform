"""Hit Validation and Milestone Tracking API routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/hits", tags=["hit-validation"])


class HitInput(BaseModel):
    smiles: str
    target: str
    docking_confidence: float = 0.0


class HitListInput(BaseModel):
    hits: list[HitInput]


@router.post("/validate", dependencies=[Depends(require_admin_key)])
async def validate_hits(body: HitListInput):
    """Validate screening hits against ChEMBL, PubMed, PubChem, and platform claims."""
    from ...reasoning.hit_validator import validate_all_hits
    results = await validate_all_hits([h.model_dump() for h in body.hits])
    novel = sum(1 for r in results if r.get("novelty") == "novel")
    known = sum(1 for r in results if r.get("novelty") == "well_known")
    return {
        "validated": len(results),
        "novel": novel,
        "partially_known": len(results) - novel - known,
        "well_known": known,
        "results": results,
    }


@router.post("/milestones/create", dependencies=[Depends(require_admin_key)])
async def create_hit_milestones(body: HitListInput):
    """Create validation milestones for positive screening hits."""
    from ...reasoning.milestone_tracker import create_milestones_for_campaign
    result = await create_milestones_for_campaign([h.model_dump() for h in body.hits])
    return result


@router.get("/milestones")
async def get_milestones():
    """Get summary of all screening hit milestones and their validation status."""
    from ...reasoning.milestone_tracker import get_milestone_summary
    return await get_milestone_summary()


@router.get("/validate/single", dependencies=[Depends(require_admin_key)])
async def validate_single_hit(
    smiles: str,
    target: str,
    docking_confidence: float = 0.0,
):
    """Validate a single screening hit."""
    from ...reasoning.hit_validator import validate_hit
    result = await validate_hit(smiles, target, docking_confidence)
    return {
        "smiles": result.smiles,
        "target": result.target,
        "pubchem_name": result.pubchem_name,
        "pubchem_cid": result.pubchem_cid,
        "chembl_known": result.chembl_known,
        "pubmed_papers": result.pubmed_papers,
        "pubmed_titles": result.pubmed_top_titles,
        "platform_claims": result.platform_claims,
        "novelty": result.novelty,
        "summary": result.validation_summary,
    }
