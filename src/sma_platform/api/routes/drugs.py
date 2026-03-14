"""Drug / therapy endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from ...core.database import fetch, fetchrow

router = APIRouter()


@router.get("/drugs")
async def list_drugs(
    approval_status: str | None = None,
    drug_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
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
            "SELECT * FROM drugs ORDER BY name LIMIT $1 OFFSET $2",
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
