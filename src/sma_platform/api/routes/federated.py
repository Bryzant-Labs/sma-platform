"""Zero-Knowledge Data Sharing API routes (Phase 10.5)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from ...reasoning.federated import (
    get_fl_protocols,
    get_omop_mappings,
    get_privacy_budget,
    get_data_sharing_tiers,
)

router = APIRouter()


@router.get("/federated/protocols")
async def fl_protocols():
    """Get federated learning protocol specifications for SMA research."""
    return get_fl_protocols()


@router.get("/federated/omop")
async def omop_mappings():
    """Get OMOP/OHDSI concept mappings for SMA clinical data."""
    return get_omop_mappings()


@router.get("/federated/privacy-budget")
async def privacy_budget(
    epsilon: float = Query(1.0, ge=0.01, le=20.0, description="Per-query epsilon"),
    delta: float = Query(1e-5, gt=0, lt=1.0, description="Per-query delta"),
    n_queries: int = Query(50, ge=1, le=10000, description="Number of queries"),
):
    """Calculate privacy budget for a research scenario."""
    return get_privacy_budget(epsilon, delta, n_queries)


@router.get("/federated/data-tiers")
async def data_tiers():
    """Get data sharing tier framework (4 tiers with privacy levels)."""
    return get_data_sharing_tiers()
