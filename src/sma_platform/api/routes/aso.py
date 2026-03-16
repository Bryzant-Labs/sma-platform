"""ASO (Antisense Oligonucleotide) design endpoints for SMA.

Provides endpoints to generate, score, and compare ASO sequences
targeting SMN2 pre-mRNA regulatory elements for exon 7 inclusion.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...reasoning.aso_generator import (
    compare_to_nusinersen,
    generate_aso_candidates,
    get_target_regions,
    score_custom_aso,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ASOScoreInput(BaseModel):
    """Request body for scoring a custom ASO sequence."""
    sequence: str = Field(
        ...,
        min_length=10,
        max_length=30,
        description="ASO sequence in DNA notation (5'->3'), 10-30 nt",
        examples=["TCACTTTCATAATGCTGG"],
    )
    target: str = Field(
        default="ISS-N1",
        description="Target region key: ISS-N1, ISS-N2, ESS_exon7, or element2",
    )


@router.get("/aso/generate")
async def generate_aso(
    target: str = Query(
        default="ISS-N1",
        description="SMN2 target region: ISS-N1, ISS-N2, ESS_exon7, or element2",
    ),
    n: int = Query(
        default=20,
        ge=1,
        le=50,
        description="Number of ASO candidates to generate (1-50)",
    ),
):
    """Generate novel ASO candidates targeting a SMN2 regulatory region.

    Designs antisense oligonucleotides with 2'-MOE phosphorothioate chemistry,
    scored by target complementarity, GC content, melting temperature,
    self-complementarity avoidance, and BBB penetration potential.

    The default target (ISS-N1) is the same region targeted by nusinersen
    (Spinraza), the first FDA-approved ASO therapy for SMA.
    """
    candidates = await generate_aso_candidates(target_region=target, n_candidates=n)

    if candidates and "error" in candidates[0]:
        raise HTTPException(status_code=400, detail=candidates[0]["error"])

    return {
        "target_region": target,
        "n_candidates": len(candidates),
        "candidates": candidates,
        "chemistry_note": "All candidates use 2'-MOE sugar + phosphorothioate backbone (same class as nusinersen/Spinraza)",
    }


@router.get("/aso/targets")
async def list_aso_targets():
    """List all known SMN2 regulatory regions targetable by ASOs.

    Returns sequence, location, mechanism, and antisense complement
    for each region. Includes ISS-N1 (nusinersen target), ISS-N2,
    exon 7 ESS, and Element 2.
    """
    regions = await get_target_regions()
    return {
        "total": len(regions),
        "regions": regions,
        "note": "ISS-N1 is the validated clinical target (nusinersen). Other regions are experimental.",
    }


@router.get("/aso/compare")
async def compare_aso(
    sequence: str = Query(
        ...,
        min_length=10,
        max_length=30,
        description="ASO sequence to compare against nusinersen (DNA notation, 5'->3')",
    ),
):
    """Compare a candidate ASO sequence to nusinersen (Spinraza).

    Provides side-by-side comparison on length, GC content, melting
    temperature, self-complementarity, BBB penetration score, and
    target overlap with ISS-N1.
    """
    result = await compare_to_nusinersen(aso_sequence=sequence)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/aso/score")
async def score_aso(body: ASOScoreInput):
    """Score a custom ASO sequence against a SMN2 target region.

    Evaluates the ASO on all design criteria: target complementarity,
    GC content (40-60% ideal), melting temperature (nearest-neighbor method),
    self-complementarity risk, and BBB penetration potential.

    Returns detailed metrics, sub-scores, chemistry recommendations,
    and design feedback.
    """
    result = await score_custom_aso(sequence=body.sequence, target=body.target)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result
