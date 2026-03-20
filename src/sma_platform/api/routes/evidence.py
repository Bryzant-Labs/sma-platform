"""Evidence and claims endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from ...core.database import fetch, fetchrow

router = APIRouter()

MAX_LIMIT = 10000

VALID_CLAIM_TYPES = {
    "gene_expression", "protein_interaction", "pathway_membership",
    "drug_target", "drug_efficacy", "biomarker", "splicing_event",
    "neuroprotection", "motor_function", "survival", "safety", "other",
    "functional_interaction",
}


@router.get("/evidence")
async def list_evidence(
    limit: int = Query(default=500, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    """List evidence records linking claims to sources."""
    rows = await fetch(
        """SELECT e.id, e.claim_id, e.source_id, e.method, e.excerpt, e.created_at,
                  c.predicate as claim_text, c.claim_type, c.confidence as claim_confidence, c.claim_number,
                  s.title as source_title, s.external_id as source_pmid, s.journal, s.pub_date
           FROM evidence e
           JOIN claims c ON e.claim_id = c.id
           JOIN sources s ON e.source_id = s.id
           ORDER BY c.confidence DESC
           LIMIT $1 OFFSET $2""",
        limit, offset,
    )
    return [dict(r) for r in rows]


@router.get("/claims/count")
async def claims_count(
    claim_type: str | None = None,
    confidence_min: float | None = Query(default=None, ge=0, le=1),
    confidence_max: float | None = Query(default=None, ge=0, le=1),
    target: str | None = None,
    q: str | None = Query(default=None, max_length=200),
):
    """Get claim counts with optional filters — used for pagination."""
    wheres: list[str] = []
    params: list = []
    idx = 1

    if claim_type and claim_type in VALID_CLAIM_TYPES:
        wheres.append(f"c.claim_type = ${idx}")
        params.append(claim_type)
        idx += 1
    if confidence_min is not None:
        wheres.append(f"c.confidence >= ${idx}")
        params.append(confidence_min)
        idx += 1
    if confidence_max is not None:
        wheres.append(f"c.confidence <= ${idx}")
        params.append(confidence_max)
        idx += 1
    if target:
        wheres.append(f"CAST(c.metadata AS TEXT) LIKE ${idx}")
        params.append(f'%"{target.upper()}"%')
        idx += 1
    if q:
        wheres.append(f"LOWER(c.predicate) LIKE ${idx}")
        params.append(f"%{q.lower()}%")
        idx += 1

    where_clause = " WHERE " + " AND ".join(wheres) if wheres else ""

    total_row = await fetchrow(
        f"SELECT count(*) AS total FROM claims c{where_clause}", *params
    )
    total = total_row["total"] if total_row else 0

    # Type breakdown
    type_rows = await fetch(
        f"SELECT c.claim_type, count(*) AS cnt FROM claims c{where_clause} GROUP BY c.claim_type ORDER BY cnt DESC",
        *params,
    )
    by_type = {r["claim_type"]: r["cnt"] for r in type_rows}

    return {"total": total, "by_type": by_type}


@router.get("/claims")
async def list_claims(
    claim_type: str | None = None,
    confidence_min: float | None = Query(default=None, ge=0, le=1),
    confidence_max: float | None = Query(default=None, ge=0, le=1),
    target: str | None = None,
    q: str | None = Query(default=None, max_length=200),
    enriched: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    """List claims with filters, optionally enriched with source paper details."""
    wheres: list[str] = []
    params: list = []
    idx = 1

    if claim_type and claim_type in VALID_CLAIM_TYPES:
        wheres.append(f"c.claim_type = ${idx}")
        params.append(claim_type)
        idx += 1
    if confidence_min is not None:
        wheres.append(f"c.confidence >= ${idx}")
        params.append(confidence_min)
        idx += 1
    if confidence_max is not None:
        wheres.append(f"c.confidence <= ${idx}")
        params.append(confidence_max)
        idx += 1
    if target:
        wheres.append(f"CAST(c.metadata AS TEXT) LIKE ${idx}")
        params.append(f'%"{target.upper()}"%')
        idx += 1
    if q:
        wheres.append(f"LOWER(c.predicate) LIKE ${idx}")
        params.append(f"%{q.lower()}%")
        idx += 1

    where_clause = " WHERE " + " AND ".join(wheres) if wheres else ""

    if enriched:
        base = """SELECT c.id, c.claim_type, c.subject_id, c.subject_type,
                         c.predicate, c.object_id, c.object_type, c.value,
                         c.confidence, c.metadata, c.created_at,
                         s.title AS source_title, s.external_id AS source_pmid,
                         s.journal AS source_journal, s.pub_date AS source_date,
                         s.doi AS source_doi, s.abstract AS source_abstract,
                         s.authors AS source_authors, s.url AS source_url,
                         e.excerpt AS evidence_excerpt
                  FROM claims c
                  LEFT JOIN evidence e ON e.claim_id = c.id
                  LEFT JOIN sources s ON e.source_id = s.id"""
    else:
        base = "SELECT * FROM claims c"

    params.append(limit)
    limit_idx = idx
    idx += 1
    params.append(offset)
    offset_idx = idx

    rows = await fetch(
        base + where_clause + f" ORDER BY c.confidence DESC LIMIT ${limit_idx} OFFSET ${offset_idx}",
        *params,
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
    limit: int = Query(default=100, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    if source_type:
        rows = await fetch(
            "SELECT id, source_type, external_id, title, authors, journal, pub_date, doi, url, abstract, created_at "
            "FROM sources WHERE source_type = $1 ORDER BY pub_date DESC NULLS LAST LIMIT $2 OFFSET $3",
            source_type, limit, offset,
        )
    else:
        rows = await fetch(
            "SELECT id, source_type, external_id, title, authors, journal, pub_date, doi, url, abstract, created_at "
            "FROM sources ORDER BY pub_date DESC NULLS LAST LIMIT $1 OFFSET $2",
            limit, offset,
        )
    return [dict(r) for r in rows]


@router.get("/hypotheses")
async def list_hypotheses(
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
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
