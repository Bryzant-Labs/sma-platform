"""Digital Twin of the Motor Neuron API routes (Phase 10.3)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ...reasoning.digital_twin import (
    get_available_drugs,
    get_compartments,
    get_optimal_combinations,
    get_pathways,
    run_simulation,
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
