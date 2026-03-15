"""Molecular dynamics simulation code generator endpoints (Phase 10.2 — Agent C)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from ...reasoning.md_generator import (
    generate_simulation_code,
    list_available_simulations,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/md/simulations")
async def get_available_simulations():
    """List all available SMA molecular dynamics simulation templates.

    6 simulation types covering: SMN oligomerization, hnRNP A1-ISS-N1 binding,
    risdiplam-SMN2 interaction, NCALD calcium dynamics, PLS3 actin bundling,
    SMN-Gemin2 complex stability.
    """
    return list_available_simulations()


@router.get("/md/generate/{sim_key}")
async def generate_simulation(sim_key: str):
    """Generate complete OpenMM MD simulation scripts for an SMA target.

    Returns 3 ready-to-run Python scripts:
    1. Setup (structure loading, solvation, minimization, equilibration)
    2. Production (NPT ensemble MD run)
    3. Analysis (RMSD, RMSF, Rg, contact maps)

    Available simulation keys: smn_oligomerization, hnrnp_a1_iss_n1,
    smn_risdiplam, ncald_calcium, pls3_actin, smn_gemin_complex
    """
    result = generate_simulation_code(sim_key)
    if result is None:
        available = list_available_simulations()
        keys = [s["key"] for s in available["simulations"]]
        raise HTTPException(
            404,
            f"Unknown simulation: {sim_key}. Available: {', '.join(keys)}",
        )
    return result
