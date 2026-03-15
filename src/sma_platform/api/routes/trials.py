"""Clinical trial endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from ...core.database import fetch, fetchrow

router = APIRouter()

MAX_LIMIT = 2000


@router.get("/trials")
async def list_trials(
    status: str | None = None,
    phase: str | None = None,
    limit: int = Query(default=100, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    conditions = []
    params: list = []
    idx = 1

    if status:
        conditions.append(f"status = ${idx}")
        params.append(status)
        idx += 1
    if phase:
        conditions.append(f"phase = ${idx}")
        params.append(phase)
        idx += 1

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.extend([limit, offset])

    rows = await fetch(
        f"SELECT * FROM trials {where} ORDER BY start_date DESC NULLS LAST LIMIT ${idx} OFFSET ${idx + 1}",
        *params,
    )
    return [dict(r) for r in rows]


@router.get("/trials/{trial_id}")
async def get_trial(trial_id: UUID):
    row = await fetchrow("SELECT * FROM trials WHERE id = $1", trial_id)
    if not row:
        raise HTTPException(404, "Trial not found")
    return dict(row)


@router.get("/trials/nct/{nct_id}")
async def get_trial_by_nct(nct_id: str):
    row = await fetchrow("SELECT * FROM trials WHERE nct_id = $1", nct_id.upper())
    if not row:
        raise HTTPException(404, f"Trial '{nct_id}' not found")
    return dict(row)
