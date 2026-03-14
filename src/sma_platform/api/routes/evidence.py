"""Evidence and claims endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from ...core.database import fetch, fetchrow

router = APIRouter()


@router.get("/claims")
async def list_claims(
    claim_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    if claim_type:
        rows = await fetch(
            "SELECT * FROM claims WHERE claim_type = $1 ORDER BY confidence DESC LIMIT $2 OFFSET $3",
            claim_type, limit, offset,
        )
    else:
        rows = await fetch(
            "SELECT * FROM claims ORDER BY confidence DESC LIMIT $1 OFFSET $2",
            limit, offset,
        )
    return [dict(r) for r in rows]


@router.get("/claims/{claim_id}")
async def get_claim(claim_id: UUID):
    row = await fetchrow("SELECT * FROM claims WHERE id = $1", claim_id)
    if not row:
        raise HTTPException(404, "Claim not found")
    return dict(row)


@router.get("/claims/{claim_id}/evidence")
async def get_claim_evidence(claim_id: UUID):
    """Get all evidence supporting a specific claim."""
    rows = await fetch(
        """SELECT e.*, s.title as source_title, s.source_type, s.external_id, s.url as source_url
           FROM evidence e
           JOIN sources s ON e.source_id = s.id
           WHERE e.claim_id = $1
           ORDER BY e.created_at""",
        claim_id,
    )
    return [dict(r) for r in rows]


@router.get("/sources")
async def list_sources(
    source_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    if source_type:
        rows = await fetch(
            "SELECT id, source_type, external_id, title, journal, pub_date, doi, url, created_at "
            "FROM sources WHERE source_type = $1 ORDER BY pub_date DESC NULLS LAST LIMIT $2 OFFSET $3",
            source_type, limit, offset,
        )
    else:
        rows = await fetch(
            "SELECT id, source_type, external_id, title, journal, pub_date, doi, url, created_at "
            "FROM sources ORDER BY pub_date DESC NULLS LAST LIMIT $1 OFFSET $2",
            limit, offset,
        )
    return [dict(r) for r in rows]


@router.get("/hypotheses")
async def list_hypotheses(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    if status:
        rows = await fetch(
            "SELECT * FROM hypotheses WHERE status = $1 ORDER BY confidence DESC LIMIT $2 OFFSET $3",
            status, limit, offset,
        )
    else:
        rows = await fetch(
            "SELECT * FROM hypotheses ORDER BY confidence DESC LIMIT $1 OFFSET $2",
            limit, offset,
        )
    return [dict(r) for r in rows]
