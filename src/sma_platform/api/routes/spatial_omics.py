"""Spatial Multi-Omics API routes (Phase 7.1)."""

from __future__ import annotations

from fastapi import APIRouter

from ...reasoning.spatial_omics import (
    analyze_drug_penetration,
    get_spatial_expression_map,
    identify_silent_zones,
)

router = APIRouter()


@router.get("/spatial/penetration")
async def drug_penetration():
    """Analyze drug penetration across spinal cord zones."""
    return analyze_drug_penetration()


@router.get("/spatial/expression")
async def spatial_expression():
    """Get target × zone expression matrix."""
    return get_spatial_expression_map()


@router.get("/spatial/silent-zones")
async def silent_zones():
    """Identify therapeutic silent zones."""
    return identify_silent_zones()
