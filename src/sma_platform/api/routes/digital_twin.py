"""Digital Twin of the Motor Neuron API routes (Phase 10.3)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ...reasoning.digital_twin import (
    get_available_drugs,
    get_compartments,
    get_gpu_validated_drugs,
    get_optimal_combinations,
    get_pathways,
    run_simulation,
    simulate_temporal,
)

router = APIRouter()


class SimulationInput(BaseModel):
    drugs: list[str]


@router.get("/twin/compartments")
async def compartments():
    """Get motor neuron compartment model."""
    return get_compartments()


@router.get("/twin/pathways")
async def pathways():
    """Get signaling pathway model."""
    return get_pathways()


@router.get("/twin/drugs")
async def available_drugs():
    """Get drugs available for digital twin simulation."""
    return get_available_drugs()


@router.post("/twin/simulate")
async def simulate(body: SimulationInput):
    """Simulate a drug combination on the motor neuron digital twin."""
    return run_simulation(body.drugs)


@router.get("/twin/optimize")
async def optimize():
    """Find optimal drug combinations via exhaustive simulation."""
    return get_optimal_combinations()


class TemporalInput(BaseModel):
    drugs: list[str]
    duration_months: int = 12
    step_months: int = 1


@router.post("/twin/temporal")
async def temporal_simulation(body: TemporalInput):
    """Simulate motor neuron health trajectory over months of treatment.

    Shows progressive recovery (or decline) including drug onset delays,
    plateau effects, and compensatory mechanisms.
    """
    return simulate_temporal(body.drugs, body.duration_months, body.step_months)


@router.get("/twin/gpu-validated")
async def gpu_validated():
    """Get drugs with GPU computational validation (DiffDock, SpliceAI, Boltz-2, ESM-2).

    Shows which drugs in the digital twin have been validated by our
    GPU compute pipeline (Phase G1-G3).
    """
    return get_gpu_validated_drugs()
