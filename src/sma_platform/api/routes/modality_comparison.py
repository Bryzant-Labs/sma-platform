"""Therapeutic Modality Comparison API routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query

from ...reasoning.modality_comparison import (
    compare_all_targets,
    compare_modalities_for_target,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/modality/compare/{symbol}")
async def compare_modalities(symbol: str):
    """Compare therapeutic modalities for an SMA target.

    Returns all applicable modalities (small molecule, ASO, CRISPR, gene therapy,
    protein binder) ranked by feasibility, with pros/cons, development timelines,
    and cost estimates for the given target gene.
    """
    return compare_modalities_for_target(symbol)


@router.get("/modality/compare")
async def compare_all():
    """Compare modalities for all SMA targets.

    Returns a list of modality comparisons for every target in the platform,
    each ranked by feasibility.
    """
    return compare_all_targets()
