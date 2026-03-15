"""Dual-Target Molecule Screening API routes (Phase 6.1)."""

from __future__ import annotations

from fastapi import APIRouter

from ...reasoning.dual_target import (
    analyze_synergy_potential,
    get_dual_candidates,
    get_ion_channel_drug_map,
)

router = APIRouter()


@router.get("/screen/dual-target")
async def dual_target_candidates():
    """Get dual-target candidates (SMN2 splicing + ion channel)."""
    return get_dual_candidates()


@router.get("/screen/dual-target/channels")
async def ion_channel_map():
    """Map ion channel targets to available drugs."""
    return get_ion_channel_drug_map()


@router.get("/screen/dual-target/synergy")
async def synergy_analysis():
    """Analyze synergy potential across all dual-target candidates."""
    return analyze_synergy_potential()
