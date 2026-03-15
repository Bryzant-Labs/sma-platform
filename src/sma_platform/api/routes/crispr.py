"""CRISPR guide RNA design endpoints (Phase 6.2)."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...reasoning.crispr_designer import (
    MOTIFS,
    design_guides_for_target,
    design_smn2_guides,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class GuideDesignInput(BaseModel):
    symbol: str
    sequence: str
    max_guides: int = 20


@router.get("/crispr/guides")
async def get_crispr_guides(
    symbol: str = Query(default="SMN2", description="Gene symbol (SMN2, SMN1, or custom)"),
    max_guides: int = Query(default=20, ge=1, le=50),
):
    """Design CRISPR sgRNA guides for SMA-relevant targets.

    For SMN2/SMN1: returns guides targeting ISS-N1, ESE, and ESS motifs
    with three therapeutic strategies (CRISPRi at ISS-N1, CRISPRi at ESS, CRISPRa at ESE).

    For other genes: use POST with a DNA sequence.
    """
    if symbol.upper() in ("SMN2", "SMN1"):
        result = design_smn2_guides()
        # Trim to max_guides
        if result.get("all_guides"):
            result["all_guides"] = result["all_guides"][:max_guides]
        return result

    return {
        "error": f"No built-in reference for {symbol}. Use POST /api/v2/crispr/guides with a DNA sequence.",
        "hint": "POST body: {\"symbol\": \"GENE\", \"sequence\": \"ATCG...\", \"max_guides\": 20}",
    }


@router.post("/crispr/guides")
async def post_crispr_guides(body: GuideDesignInput):
    """Design CRISPR guides for a custom DNA sequence.

    Accepts 23-10000 nt DNA sequence and scans both strands for
    20nt protospacer + NGG PAM sites.
    """
    if len(body.sequence) < 23:
        raise HTTPException(400, "Sequence too short — need at least 23 nt (20 protospacer + 3 PAM)")
    if len(body.sequence) > 10000:
        raise HTTPException(400, "Sequence too long — maximum 10,000 nt")

    result = await design_guides_for_target(body.symbol, body.sequence)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.get("/crispr/motifs")
async def get_smn2_motifs():
    """Return all known SMN2 exon 7 regulatory motifs.

    Includes ISS-N1 (nusinersen target), ESE (Tra2-beta), ESS (hnRNP A1),
    Element2, C6T disease position, and branch point.
    """
    return {
        "reference": "SMN2 NG_008728.1, exon 7 region",
        "motifs": {name: info for name, info in MOTIFS.items()},
        "note": "Positions are 0-indexed within their respective region (intron6/exon7/intron7)",
    }
