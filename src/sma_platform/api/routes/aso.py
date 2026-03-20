"""ASO (Antisense Oligonucleotide) design endpoints for SMA.

Provides endpoints to generate, score, and compare ASO sequences
targeting SMN2 pre-mRNA regulatory elements for exon 7 inclusion.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

from ...reasoning.aso_generator import (
    compare_to_nusinersen,
    generate_aso_candidates,
    get_target_regions,
    score_aso as score_aso_intrinsic,
    score_custom_aso,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Valid region keys for path-parameter validation
_VALID_REGIONS = {"ISS-N1", "ISS-N2", "ESS_exon7", "element2"}


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


# ---------------------------------------------------------------------------
# Generation endpoints
# ---------------------------------------------------------------------------

@router.get("/aso/generate/{region}")
async def generate_asos(
    region: str = Path(
        ...,
        description="SMN2 target region: ISS-N1, ISS-N2, ESS_exon7, or element2",
    ),
    n: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Number of ASO candidates to generate (1-50)",
    ),
):
    """Generate candidate ASO sequences for a target region.

    Designs antisense oligonucleotides targeting the specified SMN2 regulatory
    element, scored by target complementarity, GC content, melting temperature,
    predicted binding energy, self-complementarity avoidance, and BBB
    penetration potential. Each candidate includes region-specific chemistry
    recommendations.
    """
    candidates = await generate_aso_candidates(target_region=region, n_candidates=n)

    if candidates and "error" in candidates[0]:
        raise HTTPException(status_code=400, detail=candidates[0]["error"])

    return {
        "target_region": region,
        "n_candidates": len(candidates),
        "candidates": candidates,
        "chemistry_note": (
            "Chemistry recommendations are region-specific. ISS-N1/ISS-N2 use "
            "2'-MOE PS (nusinersen class). Exonic targets (ESS, Element2) may "
            "benefit from PMO chemistry to avoid RNase H cleavage."
        ),
    }


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

    Designs antisense oligonucleotides scored by target complementarity,
    GC content, melting temperature, predicted binding energy (delta-G),
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
        "chemistry_note": (
            "Chemistry recommendations are region-specific. ISS-N1/ISS-N2 use "
            "2'-MOE PS (nusinersen class). Exonic targets (ESS, Element2) may "
            "benefit from PMO chemistry to avoid RNase H cleavage."
        ),
    }


# ---------------------------------------------------------------------------
# Region listing endpoints
# ---------------------------------------------------------------------------

@router.get("/aso/regions")
async def list_target_regions():
    """List available ASO target regions on SMN2.

    Returns sequence, location, mechanism, antisense complement, and GC
    content for each targetable regulatory element. Includes ISS-N1
    (nusinersen target), ISS-N2, exon 7 ESS, and Element 2.
    """
    regions = await get_target_regions()
    return {
        "total": len(regions),
        "regions": regions,
        "note": "ISS-N1 is the validated clinical target (nusinersen). Other regions are experimental.",
    }


@router.get("/aso/targets")
async def list_aso_targets():
    """List all known SMN2 regulatory regions targetable by ASOs.

    Alias for /aso/regions. Returns sequence, location, mechanism, and
    antisense complement for each region.
    """
    regions = await get_target_regions()
    return {
        "total": len(regions),
        "regions": regions,
        "note": "ISS-N1 is the validated clinical target (nusinersen). Other regions are experimental.",
    }


# ---------------------------------------------------------------------------
# Comparison endpoint
# ---------------------------------------------------------------------------

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
    temperature, predicted binding energy, self-complementarity, BBB
    penetration score, and target overlap with ISS-N1.
    """
    result = await compare_to_nusinersen(aso_sequence=sequence)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


# ---------------------------------------------------------------------------
# Scoring endpoints
# ---------------------------------------------------------------------------

@router.get("/aso/score")
async def score_aso_quick(
    sequence: str = Query(
        ...,
        min_length=10,
        max_length=30,
        description="ASO sequence in DNA notation (5'->3'), 10-30 nt",
    ),
):
    """Quick intrinsic score of an ASO sequence (no target required).

    Evaluates GC content, melting temperature, binding energy, length,
    self-complementarity, and BBB penetration potential. Returns pass/fail
    checks and a letter grade (A-D).

    Use POST /aso/score for full target-specific scoring with complementarity
    analysis and design feedback.
    """
    result = await score_aso_intrinsic(sequence=sequence)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/aso/score")
async def score_aso_full(body: ASOScoreInput):
    """Score a custom ASO sequence against a SMN2 target region.

    Evaluates the ASO on all design criteria: target complementarity,
    GC content (40-60% ideal), melting temperature (nearest-neighbor method),
    predicted binding energy, self-complementarity risk, and BBB penetration
    potential.

    Returns detailed metrics, sub-scores, region-specific chemistry
    recommendations, and design feedback.
    """
    result = await score_custom_aso(sequence=body.sequence, target=body.target)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result
