"""Lab-OS Experiment Design API routes (Phase 10.4)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ...reasoning.lab_os import (
    get_assay_library,
    get_cloud_labs,
    generate_experiment,
)

router = APIRouter()


@router.get("/lab/assays")
async def assay_library():
    """Get standardized SMA assay library (8 assays)."""
    return get_assay_library()


@router.get("/lab/cloud-labs")
async def cloud_labs():
    """Get cloud lab integration specs (Emerald, Strateos, Opentrons)."""
    return get_cloud_labs()


@router.get("/lab/design")
async def design_experiment(
    hypothesis: str = Query(..., max_length=1000, description="Hypothesis text to design experiment for"),
):
    """Generate experiment design from a hypothesis."""
    return generate_experiment(hypothesis)
