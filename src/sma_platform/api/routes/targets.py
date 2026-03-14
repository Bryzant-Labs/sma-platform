"""Target (gene/protein/pathway) endpoints."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...core.database import execute, fetch, fetchrow

router = APIRouter()


class TargetCreate(BaseModel):
    symbol: str
    name: str | None = None
    target_type: str = "gene"
    organism: str = "Homo sapiens"
    identifiers: dict[str, Any] = {}
    description: str | None = None


@router.get("/targets")
async def list_targets(
    target_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    if target_type:
        rows = await fetch(
            "SELECT * FROM targets WHERE target_type = $1 ORDER BY symbol LIMIT $2 OFFSET $3",
            target_type, limit, offset,
        )
    else:
        rows = await fetch(
            "SELECT * FROM targets ORDER BY symbol LIMIT $1 OFFSET $2",
            limit, offset,
        )
    return [dict(r) for r in rows]


@router.get("/targets/{target_id}")
async def get_target(target_id: UUID):
    row = await fetchrow("SELECT * FROM targets WHERE id = $1", target_id)
    if not row:
        raise HTTPException(404, "Target not found")
    return dict(row)


@router.get("/targets/symbol/{symbol}")
async def get_target_by_symbol(symbol: str):
    row = await fetchrow("SELECT * FROM targets WHERE symbol = $1", symbol.upper())
    if not row:
        raise HTTPException(404, f"Target '{symbol}' not found")
    return dict(row)


@router.post("/targets", status_code=201)
async def create_target(body: TargetCreate):
    import json
    row = await fetchrow(
        """INSERT INTO targets (symbol, name, target_type, organism, identifiers, description)
           VALUES ($1, $2, $3, $4, $5::jsonb, $6)
           ON CONFLICT (symbol, target_type, organism) DO UPDATE
           SET name = EXCLUDED.name, identifiers = EXCLUDED.identifiers, description = EXCLUDED.description,
               updated_at = NOW()
           RETURNING *""",
        body.symbol.upper(), body.name, body.target_type, body.organism,
        json.dumps(body.identifiers), body.description,
    )
    return dict(row)
