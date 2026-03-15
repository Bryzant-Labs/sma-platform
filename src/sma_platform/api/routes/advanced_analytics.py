"""Advanced Analytics API routes (Phase 7.2–7.5).

Combines:
- Phase 7.2: Cross-Species Regeneration Signatures
- Phase 7.3: NMJ Retrograde Signaling
- Phase 7.4: Multisystem SMA
- Phase 7.5: Bioelectric Reprogramming
"""

from __future__ import annotations

from fastapi import APIRouter

from ...reasoning.regeneration_signatures import (
    get_pathway_comparisons,
    get_regeneration_genes,
    identify_silenced_programs,
)
from ...reasoning.nmj_signaling import (
    analyze_happy_muscle_hypothesis,
    get_chip_models,
    get_ev_cargo,
    get_retrograde_signals,
)
from ...reasoning.multisystem_sma import (
    analyze_multisystem_sma,
    get_combination_therapies,
    get_energy_budget,
    get_organ_systems,
)
from ...reasoning.bioelectric_module import (
    analyze_bioelectric_profile,
    get_electroceuticals,
    get_ion_channels,
    get_vmem_states,
)

router = APIRouter()


# ---- Phase 7.2: Regeneration Signatures ----

@router.get("/regen/genes")
async def regeneration_genes():
    """Get regeneration-associated genes with SMA comparison."""
    return get_regeneration_genes()


@router.get("/regen/pathways")
async def pathway_comparisons():
    """Compare regeneration pathways with SMA state."""
    return get_pathway_comparisons()


@router.get("/regen/silenced")
async def silenced_programs():
    """Identify silenced regeneration programs in human SMA."""
    return identify_silenced_programs()


# ---- Phase 7.3: NMJ Retrograde Signaling ----

@router.get("/nmj/signals")
async def retrograde_signals():
    """Get retrograde signaling molecules at the NMJ."""
    return get_retrograde_signals()


@router.get("/nmj/ev-cargo")
async def ev_cargo():
    """Get EV therapeutic cargo options for NMJ delivery."""
    return get_ev_cargo()


@router.get("/nmj/chip-models")
async def chip_models():
    """Get organ-on-chip models for NMJ validation."""
    return get_chip_models()


@router.get("/nmj/happy-muscle")
async def happy_muscle():
    """Full analysis of the 'happy muscle → surviving neuron' hypothesis."""
    return analyze_happy_muscle_hypothesis()


# ---- Phase 7.4: Multisystem SMA ----

@router.get("/multisystem/organs")
async def organ_systems():
    """Get organ systems affected in SMA beyond motor neurons."""
    return get_organ_systems()


@router.get("/multisystem/combinations")
async def combination_therapies():
    """Get combination therapy strategies for multisystem SMA."""
    return get_combination_therapies()


@router.get("/multisystem/energy")
async def energy_budget():
    """Get energy budget analysis for SMA motor neurons."""
    return get_energy_budget()


@router.get("/multisystem/full")
async def multisystem_full():
    """Full multisystem SMA analysis."""
    return analyze_multisystem_sma()


# ---- Phase 7.5: Bioelectric Reprogramming ----

@router.get("/bioelectric/channels")
async def ion_channels():
    """Get ion channel expression profile in SMA motor neurons."""
    return get_ion_channels()


@router.get("/bioelectric/vmem")
async def vmem_states():
    """Get Vmem state classification for SMA motor neurons."""
    return get_vmem_states()


@router.get("/bioelectric/electroceuticals")
async def electroceuticals():
    """Get electroceutical interventions for SMA."""
    return get_electroceuticals()


@router.get("/bioelectric/profile")
async def bioelectric_profile():
    """Full bioelectric analysis of SMA motor neurons."""
    return analyze_bioelectric_profile()
