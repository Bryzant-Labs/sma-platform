"""Gene Edit Versioning endpoints — 'GitHub for Life' (Phase 10.1)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...reasoning.gene_versioning import (
    build_smn2_version_tree,
    version_custom_edit,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class CustomEditInput(BaseModel):
    sequence: str
    position: int
    alt_allele: str
    region: str = "custom"
    description: str = "Custom edit"


@router.get("/gene-versions/smn2")
async def get_smn2_version_tree():
    """Get the SMN2 exon 7 version tree — all known variants as 'commits'.

    Shows the lineage: SMN1 (healthy) → SMN2 (C6T disease mutation)
    → therapeutic edits (base edit correction, ESE enhancement, ESS disruption).
    Each version has a deterministic SHA-256 hash like a git commit.
    """
    return build_smn2_version_tree()


@router.post("/gene-versions/edit")
async def create_custom_edit(body: CustomEditInput):
    """Simulate and version a custom sequence edit.

    Creates a parent→child version pair with diff, like a git commit.
    """
    if len(body.sequence) < 10:
        raise HTTPException(400, "Sequence too short (minimum 10 nt)")
    if len(body.sequence) > 10000:
        raise HTTPException(400, "Sequence too long (maximum 10,000 nt)")
    if body.position < 0 or body.position >= len(body.sequence):
        raise HTTPException(400, f"Position {body.position} out of range (0-{len(body.sequence)-1})")
    if len(body.alt_allele) != 1 or body.alt_allele.upper() not in "ATCGN":
        raise HTTPException(400, "alt_allele must be a single nucleotide (A, T, C, G, N)")

    return version_custom_edit(
        body.sequence,
        body.position,
        body.alt_allele,
        body.region,
        body.description,
    )
