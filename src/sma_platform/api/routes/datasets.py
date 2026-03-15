"""Omics dataset endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from ...core.database import fetch, fetchrow

router = APIRouter()

MAX_LIMIT = 2000


@router.get("/datasets")
async def list_datasets(
    evidence_tier: str | None = None,
    modality: str | None = None,
    organism: str | None = None,
    limit: int = Query(default=100, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    conditions = []
    params = []
    idx = 1

    if evidence_tier:
        conditions.append(f"evidence_tier = ${idx}")
        params.append(evidence_tier)
        idx += 1
    if modality:
        conditions.append(f"modality = ${idx}")
        params.append(modality)
        idx += 1
    if organism:
        conditions.append(f"organism = ${idx}")
        params.append(organism)
        idx += 1

    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    params.extend([limit, offset])

    rows = await fetch(
        f"SELECT * FROM datasets{where} ORDER BY evidence_tier, accession LIMIT ${idx} OFFSET ${idx + 1}",
        *params,
    )
    return [dict(r) for r in rows]


@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: UUID):
    row = await fetchrow("SELECT * FROM datasets WHERE id = $1", dataset_id)
    if not row:
        raise HTTPException(404, "Dataset not found")
    return dict(row)


@router.get("/datasets/accession/{accession}")
async def get_dataset_by_accession(accession: str):
    row = await fetchrow("SELECT * FROM datasets WHERE accession = $1", accession.upper())
    if not row:
        raise HTTPException(404, f"Dataset '{accession}' not found")
    return dict(row)
