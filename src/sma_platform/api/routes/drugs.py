"""Drug / therapy endpoints."""

from __future__ import annotations

import json
import re
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...core.database import execute, fetch, fetchrow
from ..auth import require_admin_key

router = APIRouter()

MAX_LIMIT = 2000


class DrugCreate(BaseModel):
    name: str
    brand_names: list[str] = []
    drug_type: str = "small_molecule"
    mechanism: str | None = None
    targets: list[str] = []
    approval_status: str = "preclinical"
    approved_for: list[str] = []
    manufacturer: str | None = None
    metadata: dict[str, Any] = {}


@router.get("/drugs")
async def list_drugs(
    approval_status: str | None = None,
    drug_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    if approval_status and drug_type:
        rows = await fetch(
            "SELECT * FROM drugs WHERE approval_status = $1 AND drug_type = $2 ORDER BY name LIMIT $3 OFFSET $4",
            approval_status, drug_type, limit, offset,
        )
    elif approval_status:
        rows = await fetch(
            "SELECT * FROM drugs WHERE approval_status = $1 ORDER BY name LIMIT $2 OFFSET $3",
            approval_status, limit, offset,
        )
    elif drug_type:
        rows = await fetch(
            "SELECT * FROM drugs WHERE drug_type = $1 ORDER BY name LIMIT $2 OFFSET $3",
            drug_type, limit, offset,
        )
    else:
        rows = await fetch(
            """SELECT * FROM drugs ORDER BY
               CASE approval_status
                 WHEN 'approved' THEN 0
                 WHEN 'phase3' THEN 1
                 WHEN 'phase2' THEN 2
                 WHEN 'phase1' THEN 3
                 WHEN 'investigational' THEN 4
                 WHEN 'preclinical' THEN 5
                 ELSE 6
               END, name LIMIT $1 OFFSET $2""",
            limit, offset,
        )
    return [dict(r) for r in rows]


@router.get("/drugs/{drug_id}")
async def get_drug(drug_id: UUID):
    row = await fetchrow("SELECT * FROM drugs WHERE id = $1", drug_id)
    if not row:
        raise HTTPException(404, "Drug not found")
    return dict(row)


@router.get("/drugs/name/{name}")
async def get_drug_by_name(name: str):
    row = await fetchrow("SELECT * FROM drugs WHERE name = $1", name.lower())
    if not row:
        raise HTTPException(404, f"Drug '{name}' not found")
    return dict(row)


@router.get("/drugs/{drug_id}/trials")
async def get_drug_trials(drug_id: str):
    """Get clinical trials related to a specific drug."""
    if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', drug_id, re.I):
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    drug = await fetchrow("SELECT * FROM drugs WHERE id = $1", drug_id)
    if not drug:
        raise HTTPException(404, "Drug not found")
    drug = dict(drug)

    # Build search terms: drug name + brand names
    search_terms = [drug["name"]]
    brands = drug.get("brand_names")
    if brands:
        try:
            parsed = json.loads(brands) if isinstance(brands, str) else brands
            if isinstance(parsed, list):
                search_terms.extend([b.lower() for b in parsed if b])
        except (json.JSONDecodeError, TypeError):
            pass

    # Search trials where interventions or title mention this drug
    matched_trials = []
    seen_ncts = set()
    for term in search_terms:
        if not term:
            continue
        pattern = f"%{term}%"
        rows = await fetch(
            """SELECT * FROM trials
               WHERE (LOWER(CAST(interventions AS TEXT)) LIKE $1 OR LOWER(title) LIKE $2)
               ORDER BY start_date DESC NULLS LAST
               LIMIT 50""",
            pattern, pattern,
        )
        for r in rows:
            rd = dict(r)
            if rd["nct_id"] not in seen_ncts:
                seen_ncts.add(rd["nct_id"])
                matched_trials.append(rd)

    return {"drug": drug["name"], "trial_count": len(matched_trials), "trials": matched_trials}


@router.post("/drugs", status_code=201, dependencies=[Depends(require_admin_key)])
async def create_drug(body: DrugCreate):
    existing = await fetchrow("SELECT * FROM drugs WHERE name = $1", body.name.lower())
    if existing:
        await execute(
            """UPDATE drugs SET drug_type = $1, mechanism = $2, approval_status = $3,
               manufacturer = $4, metadata = $5, brand_names = $6, targets = $7,
               approved_for = $8, updated_at = CURRENT_TIMESTAMP
               WHERE name = $9""",
            body.drug_type, body.mechanism, body.approval_status,
            body.manufacturer, json.dumps(body.metadata), json.dumps(body.brand_names),
            json.dumps(body.targets), json.dumps(body.approved_for), body.name.lower(),
        )
    else:
        await execute(
            """INSERT INTO drugs (name, brand_names, drug_type, mechanism, targets, approval_status, approved_for, manufacturer, metadata)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
            body.name.lower(), json.dumps(body.brand_names), body.drug_type,
            body.mechanism, json.dumps(body.targets), body.approval_status,
            json.dumps(body.approved_for), body.manufacturer, json.dumps(body.metadata),
        )
    row = await fetchrow("SELECT * FROM drugs WHERE name = $1", body.name.lower())
    if not row:
        raise HTTPException(500, "Failed to create drug")
    return dict(row)
