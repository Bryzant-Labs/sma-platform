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


@router.get("/assay-cards")
async def get_assay_cards():
    """Generate assay-ready validation cards for all positive screening hits.

    For each drug-like hit (pChEMBL >= 5.0, Lipinski pass), returns a
    target-specific wet-lab validation plan with:
    - Hypothesis: what we predict
    - Assay: how to test it (SMA-specific protocol)
    - Model system: cell line, organoid, or mouse model
    - Readout: what to measure
    - Go/No-Go criteria: what constitutes success
    - Estimated cost and timeline

    Cards are sorted by docking confidence / pChEMBL value descending.
    """
    from ...reasoning.assay_ready import get_assay_cards_for_positive_hits
    return await get_assay_cards_for_positive_hits()


@router.post("/assay-cards/custom")
async def generate_custom_assay_cards(body: HitListInput):
    """Generate assay cards for custom screening hits (not from the database).

    Accepts a list of hits with smiles, target, and docking_confidence.
    Returns target-specific wet-lab validation plans.
    """
    from ...reasoning.assay_ready import generate_assay_cards_batch
    cards = generate_assay_cards_batch([h.model_dump() for h in body.hits])
    targets_covered = set(c["target"] for c in cards)
    high_priority = sum(1 for c in cards if c["priority"] == "high")
    return {
        "total_hits": len(cards),
        "high_priority": high_priority,
        "targets_covered": sorted(targets_covered),
        "assay_cards": cards,
    }


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
