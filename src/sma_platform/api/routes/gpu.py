"""GPU job management and result ingestion endpoints (Phase G1)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...core.database import execute, execute_script, fetch, fetchrow, fetchval
from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Table creation (lazy)
# ---------------------------------------------------------------------------

_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS gpu_jobs (
    id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    provider TEXT,
    gpu_type TEXT,
    cost_usd FLOAT,
    results JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS splice_scores (
    id TEXT PRIMARY KEY,
    chrom TEXT NOT NULL,
    pos INT NOT NULL,
    ref TEXT NOT NULL,
    alt TEXT NOT NULL,
    ds_ag FLOAT DEFAULT 0,
    ds_al FLOAT DEFAULT 0,
    ds_dg FLOAT DEFAULT 0,
    ds_dl FLOAT DEFAULT 0,
    max_delta FLOAT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crispr_offtargets (
    id TEXT PRIMARY KEY,
    guide_sequence TEXT NOT NULL,
    chrom TEXT NOT NULL,
    position INT NOT NULL,
    matched_sequence TEXT,
    strand TEXT,
    mismatches INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

_INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_splice_scores_pos ON splice_scores (chrom, pos);
CREATE INDEX IF NOT EXISTS idx_splice_scores_delta ON splice_scores (max_delta DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_splice_scores_variant ON splice_scores (chrom, pos, ref, alt);
CREATE INDEX IF NOT EXISTS idx_crispr_offtargets_guide ON crispr_offtargets (guide_sequence);
CREATE INDEX IF NOT EXISTS idx_crispr_offtargets_pos ON crispr_offtargets (chrom, position);
CREATE INDEX IF NOT EXISTS idx_gpu_jobs_status ON gpu_jobs (status);
"""


async def _ensure_tables() -> None:
    """Create GPU-related tables if they do not exist."""
    await execute_script(_TABLES_SQL)
    await execute_script(_INDEXES_SQL)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class GpuJobCreate(BaseModel):
    job_type: str
    status: str = "pending"
    provider: Optional[str] = None
    gpu_type: Optional[str] = None
    cost_usd: Optional[float] = None
    results: Optional[dict] = None


class SpliceScore(BaseModel):
    chrom: str
    pos: int
    ref: str
    alt: str
    ds_ag: float = 0.0
    ds_al: float = 0.0
    ds_dg: float = 0.0
    ds_dl: float = 0.0
    max_delta: float = 0.0


class SpliceScoreBatch(BaseModel):
    scores: list[SpliceScore]


class EmbeddingRecord(BaseModel):
    symbol: str
    uniprot_id: Optional[str] = None
    sequence_length: Optional[int] = None
    embedding_dim: Optional[int] = None
    model: Optional[str] = None


class EmbeddingBatch(BaseModel):
    embeddings: list[EmbeddingRecord]


class OffTarget(BaseModel):
    guide_sequence: str
    chrom: str
    position: int
    matched_sequence: Optional[str] = None
    strand: Optional[str] = None
    mismatches: int = 0


class OffTargetBatch(BaseModel):
    offtargets: list[OffTarget]


# ---------------------------------------------------------------------------
# GPU Job endpoints
# ---------------------------------------------------------------------------

@router.post("/gpu/jobs", dependencies=[Depends(require_admin_key)])
async def create_gpu_job(body: GpuJobCreate):
    """Create a GPU job record."""
    await _ensure_tables()

    job_id = str(uuid4())
    results_json = json.dumps(body.results) if body.results else "{}"

    await execute(
        """INSERT INTO gpu_jobs (id, job_type, status, provider, gpu_type, cost_usd, results)
           VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)""",
        job_id,
        body.job_type,
        body.status,
        body.provider,
        body.gpu_type,
        body.cost_usd,
        results_json,
    )

    logger.info("Created GPU job %s (type=%s, status=%s)", job_id, body.job_type, body.status)

    return {
        "id": job_id,
        "job_type": body.job_type,
        "status": body.status,
    }


@router.get("/gpu/jobs")
async def list_gpu_jobs(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List GPU jobs with optional status filter."""
    await _ensure_tables()

    if status:
        total = await fetchval(
            "SELECT COUNT(*) FROM gpu_jobs WHERE status = $1", status
        )
        rows = await fetch(
            "SELECT * FROM gpu_jobs WHERE status = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3",
            status, limit, offset,
        )
    else:
        total = await fetchval("SELECT COUNT(*) FROM gpu_jobs")
        rows = await fetch(
            "SELECT * FROM gpu_jobs ORDER BY created_at DESC LIMIT $1 OFFSET $2",
            limit, offset,
        )

    return {
        "total": total,
        "count": len(rows),
        "jobs": [dict(r) for r in rows],
    }


@router.get("/gpu/jobs/{job_id}")
async def get_gpu_job(job_id: str):
    """Get a single GPU job by ID."""
    await _ensure_tables()

    row = await fetchrow("SELECT * FROM gpu_jobs WHERE id = $1", job_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return dict(row)


# ---------------------------------------------------------------------------
# Read-only summary endpoints (no auth required)
# ---------------------------------------------------------------------------

@router.get("/gpu/splice-summary")
async def splice_summary(
    top_n: int = Query(default=10, ge=1, le=100, description="Number of top variants to return"),
):
    """Return SpliceAI splice-score statistics and top variants by max delta score.

    Used by the frontend GPU Results section.
    """
    await _ensure_tables()

    total_scored = await fetchval("SELECT COUNT(*) FROM splice_scores") or 0
    high_impact = await fetchval(
        "SELECT COUNT(*) FROM splice_scores WHERE max_delta > 0.5"
    ) or 0
    medium_impact = await fetchval(
        "SELECT COUNT(*) FROM splice_scores WHERE max_delta > 0.1 AND max_delta <= 0.5"
    ) or 0
    low_impact = await fetchval(
        "SELECT COUNT(*) FROM splice_scores WHERE max_delta <= 0.1"
    ) or 0

    top_rows = await fetch(
        "SELECT chrom, pos, ref, alt, ds_ag, ds_al, ds_dg, ds_dl, max_delta "
        "FROM splice_scores ORDER BY max_delta DESC LIMIT $1",
        top_n,
    )

    return {
        "total_scored": total_scored,
        "high_impact": high_impact,
        "medium_impact": medium_impact,
        "low_impact": low_impact,
        "top_variants": [
            {
                "chrom": r["chrom"],
                "pos": r["pos"],
                "ref": r["ref"],
                "alt": r["alt"],
                "ds_ag": r["ds_ag"],
                "ds_al": r["ds_al"],
                "ds_dg": r["ds_dg"],
                "ds_dl": r["ds_dl"],
                "max_delta": r["max_delta"],
            }
            for r in top_rows
        ],
    }


@router.get("/gpu/offtarget-summary")
async def offtarget_summary():
    """Return CRISPR off-target statistics grouped by mismatch count.

    Used by the frontend GPU Results section.
    """
    await _ensure_tables()

    total_offtargets = await fetchval("SELECT COUNT(*) FROM crispr_offtargets") or 0
    total_guides = await fetchval(
        "SELECT COUNT(DISTINCT guide_sequence) FROM crispr_offtargets"
    ) or 0
    exact_matches = await fetchval(
        "SELECT COUNT(*) FROM crispr_offtargets WHERE mismatches = 0"
    ) or 0
    unique_sites = await fetchval(
        "SELECT COUNT(DISTINCT (chrom, position)) FROM crispr_offtargets"
    ) or 0

    by_mismatch_rows = await fetch(
        "SELECT mismatches, COUNT(*) AS count FROM crispr_offtargets "
        "GROUP BY mismatches ORDER BY mismatches ASC"
    )

    return {
        "total_guides": total_guides,
        "total_offtargets": total_offtargets,
        "exact_matches": exact_matches,
        "unique_sites": unique_sites,
        "by_mismatch": [
            {"mismatches": r["mismatches"], "count": r["count"]}
            for r in by_mismatch_rows
        ],
    }


# ---------------------------------------------------------------------------
# Ingestion endpoints
# ---------------------------------------------------------------------------

@router.post("/ingest/spliceai", dependencies=[Depends(require_admin_key)])
async def ingest_spliceai(body: SpliceScoreBatch):
    """Import SpliceAI delta scores into splice_scores table.

    Uses UPSERT on (chrom, pos, ref, alt) to avoid duplicates.
    """
    await _ensure_tables()

    inserted = 0
    updated = 0
    errors: list[str] = []

    for s in body.scores:
        try:
            score_id = str(uuid4())
            result = await execute(
                """INSERT INTO splice_scores (id, chrom, pos, ref, alt, ds_ag, ds_al, ds_dg, ds_dl, max_delta)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                   ON CONFLICT (chrom, pos, ref, alt) DO UPDATE SET
                       ds_ag = EXCLUDED.ds_ag,
                       ds_al = EXCLUDED.ds_al,
                       ds_dg = EXCLUDED.ds_dg,
                       ds_dl = EXCLUDED.ds_dl,
                       max_delta = EXCLUDED.max_delta""",
                score_id,
                s.chrom,
                s.pos,
                s.ref,
                s.alt,
                s.ds_ag,
                s.ds_al,
                s.ds_dg,
                s.ds_dl,
                s.max_delta,
            )
            if "INSERT" in result:
                inserted += 1
            else:
                updated += 1
        except Exception as e:
            errors.append(f"{s.chrom}:{s.pos} {s.ref}>{s.alt}: {e}")

    logger.info("SpliceAI ingest: %d inserted, %d updated, %d errors", inserted, updated, len(errors))

    return {
        "status": "ok",
        "inserted": inserted,
        "updated": updated,
        "errors": errors[:10] if errors else [],
    }


@router.post("/ingest/embeddings", dependencies=[Depends(require_admin_key)])
async def ingest_embeddings(body: EmbeddingBatch):
    """Update target metadata with ESM-2 embedding information.

    Stores embedding metadata (model, dim, sequence length) in the targets
    table metadata column for each matching target symbol.
    """
    await _ensure_tables()

    updated = 0
    not_found: list[str] = []

    for emb in body.embeddings:
        # Look up target by symbol
        target = await fetchrow(
            "SELECT id, metadata FROM targets WHERE symbol = $1",
            emb.symbol,
        )
        if not target:
            not_found.append(emb.symbol)
            continue

        # Merge ESM-2 info into existing metadata
        existing_meta = target["metadata"] if isinstance(target["metadata"], dict) else {}
        existing_meta["esm2"] = {
            "model": emb.model,
            "embedding_dim": emb.embedding_dim,
            "sequence_length": emb.sequence_length,
            "uniprot_id": emb.uniprot_id,
        }

        await execute(
            "UPDATE targets SET metadata = $1::jsonb, updated_at = NOW() WHERE id = $2",
            json.dumps(existing_meta),
            target["id"],
        )
        updated += 1

    logger.info("Embeddings ingest: %d updated, %d not found", updated, len(not_found))

    return {
        "status": "ok",
        "updated": updated,
        "not_found": not_found,
    }


@router.post("/ingest/offtargets", dependencies=[Depends(require_admin_key)])
async def ingest_offtargets(body: OffTargetBatch):
    """Import Cas-OFFinder off-target results into crispr_offtargets table."""
    await _ensure_tables()

    inserted = 0
    errors: list[str] = []

    for ot in body.offtargets:
        try:
            ot_id = str(uuid4())
            await execute(
                """INSERT INTO crispr_offtargets (id, guide_sequence, chrom, position, matched_sequence, strand, mismatches)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                ot_id,
                ot.guide_sequence,
                ot.chrom,
                ot.position,
                ot.matched_sequence,
                ot.strand,
                ot.mismatches,
            )
            inserted += 1
        except Exception as e:
            errors.append(f"{ot.guide_sequence} @ {ot.chrom}:{ot.position}: {e}")

    logger.info("Off-targets ingest: %d inserted, %d errors", inserted, len(errors))

    return {
        "status": "ok",
        "inserted": inserted,
        "errors": errors[:10] if errors else [],
    }
