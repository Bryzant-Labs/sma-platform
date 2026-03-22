"""Spatial Multi-Omics API routes (Phase 7.1) — PostgreSQL-backed."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Any

from ...core.database import execute, fetch
from ...reasoning.spatial_omics import (
    analyze_drug_penetration,
    get_spatial_expression_map,
    identify_silent_zones,
    _zone_accessibility,
    TARGET_EXPRESSION,
)

router = APIRouter()


@router.get("/spatial/penetration")
async def drug_penetration():
    """Analyze drug penetration across spinal cord zones (DB-backed)."""
    return await analyze_drug_penetration()


@router.get("/spatial/expression")
async def spatial_expression():
    """Get target × zone expression matrix (zone metadata from DB)."""
    return await get_spatial_expression_map()


@router.get("/spatial/silent-zones")
async def silent_zones():
    """Identify therapeutic silent zones (DB-backed)."""
    return await identify_silent_zones()


@router.get("/spatial/zones")
async def list_zones():
    """List all spatial zones with full metadata from DB."""
    rows = await fetch(
        "SELECT * FROM spatial_zones ORDER BY sma_relevance DESC"
    )
    return [dict(r) for r in rows]


@router.get("/spatial/zones/{zone_key}")
async def get_zone(zone_key: str):
    """Get a single spatial zone by key."""
    rows = await fetch(
        "SELECT * FROM spatial_zones WHERE zone_key = $1",
        zone_key,
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_key}' not found")
    return dict(rows[0])


@router.get("/spatial/drugs")
async def list_drug_penetration(route: str | None = None):
    """List all drug penetration profiles, optionally filtered by route."""
    if route:
        rows = await fetch(
            "SELECT * FROM spatial_drug_penetration WHERE route = $1 ORDER BY drug_name",
            route,
        )
    else:
        rows = await fetch(
            "SELECT * FROM spatial_drug_penetration ORDER BY drug_name"
        )
    return [dict(r) for r in rows]


class DynamicDrugQuery(BaseModel):
    drug_name: str
    molecular_weight: float
    logp: float
    route: str
    drug_type: str = "unknown"
    mechanism: str | None = None
    persist: bool = False  # if True, save result to DB


@router.post("/spatial/penetration/predict")
async def predict_drug_penetration(query: DynamicDrugQuery):
    """
    Predict penetration for a novel compound using the pharmacokinetic model.
    Set persist=true to save results to spatial_drug_penetration table.
    """
    zone_rows = await fetch(
        "SELECT zone_key, bbb_score, csf_score FROM spatial_zones"
    )

    zone_scores: dict[str, float] = {}
    for z in zone_rows:
        score = _zone_accessibility(
            query.molecular_weight, query.logp,
            z["bbb_score"], z["csf_score"],
            query.route,
        )
        zone_scores[z["zone_key"]] = round(score, 2)

    best_zone = max(zone_scores, key=zone_scores.get) if zone_scores else None
    worst_zone = min(zone_scores, key=zone_scores.get) if zone_scores else None

    if query.persist:
        import json as _json
        await execute(
            """
            INSERT INTO spatial_drug_penetration
                (drug_name, route, molecular_weight, logp, drug_type, zone_scores, best_zone, worst_zone, mechanism)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8, $9)
            ON CONFLICT (drug_name, route) DO UPDATE
                SET zone_scores = EXCLUDED.zone_scores,
                    best_zone = EXCLUDED.best_zone,
                    worst_zone = EXCLUDED.worst_zone
            """,
            query.drug_name, query.route, query.molecular_weight, query.logp,
            query.drug_type, _json.dumps(zone_scores), best_zone, worst_zone,
            query.mechanism,
        )

    return {
        "drug_name": query.drug_name,
        "route": query.route,
        "molecular_weight": query.molecular_weight,
        "logp": query.logp,
        "zone_penetration": zone_scores,
        "best_zone": best_zone,
        "worst_zone": worst_zone,
        "persisted": query.persist,
        "source": "computed",
    }
