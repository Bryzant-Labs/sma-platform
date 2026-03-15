"""Cross-Species Splicing Map API routes (Phase 9.3)."""

from __future__ import annotations

from fastapi import APIRouter

from ...reasoning.splicing_map import (
    compare_splicing_patterns,
    get_actionable_targets,
    get_splicing_map,
)

router = APIRouter()


@router.get("/splice/cross-species")
async def cross_species_splicing():
    """Get the full cross-species splicing map (axolotl vs human)."""
    return get_splicing_map()


@router.get("/splice/cross-species/actionable")
async def actionable_splice_targets():
    """Get splice events with highest reactivation feasibility."""
    return get_actionable_targets()


@router.get("/splice/cross-species/compare")
async def compare_regen_vs_sma():
    """Compare regeneration vs degeneration splicing patterns."""
    return compare_splicing_patterns()
