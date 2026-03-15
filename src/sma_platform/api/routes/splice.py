"""SMN2 Exon 7 Splice Variant Benchmark API (Phase 9.2).

Endpoints to query, filter, and generate the systematic SNV benchmark
covering the 254-bp region around SMN2 exon 7.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from ...core.database import execute, execute_script, fetch, fetchrow, fetchval
from ...reasoning.splice_benchmark import (
    export_benchmark,
    get_benchmark_stats,
    get_reference_sequence,
    score_all_variants,
)
from ..auth import require_admin_key

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Table creation (lazy)
# ---------------------------------------------------------------------------

_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS splice_variants (
    id SERIAL PRIMARY KEY,
    position INT NOT NULL,
    region TEXT NOT NULL,
    ref_base CHAR(1) NOT NULL,
    alt_base CHAR(1) NOT NULL,
    variant_id TEXT UNIQUE NOT NULL,
    splice_site_proximity FLOAT DEFAULT 0,
    motif_disruption FLOAT DEFAULT 0,
    conservation FLOAT DEFAULT 0,
    therapeutic_relevance FLOAT DEFAULT 0,
    composite_score FLOAT DEFAULT 0,
    annotation TEXT,
    metadata JSONB DEFAULT '{}'
);
"""

_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_splice_variants_composite ON splice_variants (composite_score DESC);
CREATE INDEX IF NOT EXISTS idx_splice_variants_region ON splice_variants (region);
CREATE INDEX IF NOT EXISTS idx_splice_variants_position ON splice_variants (position);
"""


async def _ensure_table() -> None:
    """Create the splice_variants table if it does not exist."""
    await execute_script(_TABLE_SQL)
    await execute_script(_INDEX_SQL)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_dict(row) -> dict:
    """Convert a DB row to a clean dict for API response."""
    return {
        "id": row["id"],
        "position": row["position"],
        "region": row["region"],
        "ref_base": row["ref_base"],
        "alt_base": row["alt_base"],
        "variant_id": row["variant_id"],
        "splice_site_proximity": row["splice_site_proximity"],
        "motif_disruption": row["motif_disruption"],
        "conservation": row["conservation"],
        "therapeutic_relevance": row["therapeutic_relevance"],
        "composite_score": row["composite_score"],
        "annotation": row["annotation"],
        "metadata": row["metadata"] if isinstance(row["metadata"], dict) else json.loads(row["metadata"] or "{}"),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/splice/benchmark")
async def list_benchmark(
    limit: int = Query(default=50, ge=1, le=1000, description="Max results per page"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    min_score: Optional[float] = Query(default=None, ge=0.0, le=1.0, description="Minimum composite score"),
    region: Optional[str] = Query(default=None, description="Filter by region: exon7, intron6, intron7"),
    sort: str = Query(default="composite_score", description="Sort field"),
    order: str = Query(default="desc", description="Sort order: asc or desc"),
):
    """Full benchmark with pagination and filtering.

    Returns scored splice variants from the database.
    Use POST /splice/benchmark/generate first to populate.
    """
    await _ensure_table()

    # Validate sort field
    allowed_sorts = {"composite_score", "position", "splice_site_proximity", "motif_disruption", "conservation", "therapeutic_relevance"}
    if sort not in allowed_sorts:
        raise HTTPException(status_code=400, detail=f"Invalid sort field. Allowed: {', '.join(sorted(allowed_sorts))}")

    order_dir = "DESC" if order.lower() == "desc" else "ASC"

    # Build query
    conditions: list[str] = []
    params: list = []
    param_idx = 1

    if min_score is not None:
        conditions.append(f"composite_score >= ${param_idx}")
        params.append(min_score)
        param_idx += 1

    if region is not None:
        valid_regions = {"exon7", "intron6", "intron7"}
        if region not in valid_regions:
            raise HTTPException(status_code=400, detail=f"Invalid region. Allowed: {', '.join(sorted(valid_regions))}")
        conditions.append(f"region = ${param_idx}")
        params.append(region)
        param_idx += 1

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Count total
    count_q = f"SELECT COUNT(*) FROM splice_variants {where}"
    total = await fetchval(count_q, *params)

    # Fetch page
    data_q = (
        f"SELECT * FROM splice_variants {where} "
        f"ORDER BY {sort} {order_dir} "
        f"LIMIT ${param_idx} OFFSET ${param_idx + 1}"
    )
    params.extend([limit, offset])
    rows = await fetch(data_q, *params)

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "count": len(rows),
        "variants": [_row_to_dict(r) for r in rows],
    }


@router.get("/splice/benchmark/stats")
async def benchmark_stats():
    """Summary statistics for the splice benchmark.

    Returns counts, score distributions, and therapeutic hotspot info.
    Can be computed from the scoring engine without requiring DB population.
    """
    stats = get_benchmark_stats()
    ref = get_reference_sequence()
    return {
        "reference": {
            "gene": ref["gene"],
            "gene_id": ref["gene_id"],
            "exon7_length": ref["exon7_length"],
            "full_region_length": ref["full_region_length"],
        },
        **stats,
    }


@router.get("/splice/benchmark/reference")
async def benchmark_reference():
    """Return the SMN2 exon 7 reference sequence, flanking regions, and annotations."""
    return get_reference_sequence()


@router.get("/splice/benchmark/position/{pos}")
async def variants_at_position(pos: int):
    """All 3 SNVs at a specific exon-relative position.

    Position coordinates:
      - Negative: intron 6 (e.g. -1 = last base of intron 6)
      - 1-54: exon 7
      - Positive >54 not used; intron 7 uses +1 to +100

    Note: intron 7 positions are stored as 1-100 in the DB, not 55-154.
    """
    await _ensure_table()

    rows = await fetch(
        "SELECT * FROM splice_variants WHERE position = $1 ORDER BY alt_base",
        pos,
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No variants found at position {pos}. Has the benchmark been generated?"
        )

    return {
        "position": pos,
        "count": len(rows),
        "variants": [_row_to_dict(r) for r in rows],
    }


@router.get("/splice/benchmark/region/{region}")
async def variants_by_region(
    region: str,
    min_score: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    """Variants in a named region.

    Supported regions:
      - exon7: all 54 exonic positions
      - intron6: 100 bp upstream flank
      - intron7: 100 bp downstream flank
      - iss_n1: ISS-N1 element (intron 7, +10 to +24) -- nusinersen target
      - ese: exonic splicing enhancers (exon 7, positions 1-27)
      - ess: exonic splicing silencer (exon 7, positions 30-44)
    """
    await _ensure_table()

    # Map named regions to SQL conditions
    region_map = {
        "exon7": "region = 'exon7'",
        "intron6": "region = 'intron6'",
        "intron7": "region = 'intron7'",
        "iss_n1": "region = 'intron7' AND position >= 10 AND position <= 24",
        "ese": "region = 'exon7' AND position >= 1 AND position <= 27",
        "ess": "region = 'exon7' AND position >= 30 AND position <= 44",
    }

    if region not in region_map:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid region '{region}'. Allowed: {', '.join(sorted(region_map.keys()))}"
        )

    where_clause = region_map[region]
    params: list = []
    param_idx = 1

    if min_score is not None:
        where_clause += f" AND composite_score >= ${param_idx}"
        params.append(min_score)
        param_idx += 1

    count_q = f"SELECT COUNT(*) FROM splice_variants WHERE {where_clause}"
    total = await fetchval(count_q, *params)

    data_q = (
        f"SELECT * FROM splice_variants WHERE {where_clause} "
        f"ORDER BY composite_score DESC "
        f"LIMIT ${param_idx} OFFSET ${param_idx + 1}"
    )
    params.extend([limit, offset])
    rows = await fetch(data_q, *params)

    return {
        "region": region,
        "total": total,
        "count": len(rows),
        "variants": [_row_to_dict(r) for r in rows],
    }


@router.get("/splice/benchmark/therapeutic")
async def therapeutic_variants(
    limit: int = Query(default=100, ge=1, le=1000),
):
    """Variants in therapeutically relevant regions.

    Returns variants from:
      - ISS-N1 (nusinersen/Spinraza binding site, intron 7 +10 to +24)
      - Position 6 of exon 7 (disease-defining variant)
      - ESE regions (risdiplam/Evrysdi target area, exon 7 positions 1-27)

    Sorted by composite score descending.
    """
    await _ensure_table()

    rows = await fetch(
        """
        SELECT * FROM splice_variants
        WHERE
            (region = 'intron7' AND position >= 10 AND position <= 24)
            OR (region = 'exon7' AND position = 6)
            OR (region = 'exon7' AND position >= 1 AND position <= 27)
        ORDER BY composite_score DESC
        LIMIT $1
        """,
        limit,
    )

    return {
        "description": "Variants in therapeutically relevant regions (ISS-N1, disease variant, ESE)",
        "count": len(rows),
        "variants": [_row_to_dict(r) for r in rows],
    }


@router.get("/splice/benchmark/export")
async def export_benchmark_data(
    fmt: str = Query(default="csv", description="Export format: csv or json"),
):
    """Export the full benchmark as CSV or JSON.

    Computed from the scoring engine (does not require DB population).
    """
    if fmt not in ("csv", "json"):
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'json'")

    data = export_benchmark(fmt=fmt)

    if fmt == "csv":
        return Response(
            content=data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=smn2_splice_benchmark.csv"},
        )
    return Response(
        content=data,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=smn2_splice_benchmark.json"},
    )


@router.post("/splice/benchmark/generate", dependencies=[Depends(require_admin_key)])
async def generate_benchmark():
    """Generate the full splice benchmark and store in the database (admin only).

    Computes all ~762 SNVs, scores them, and inserts into splice_variants.
    Replaces any existing data.
    """
    await _ensure_table()

    # Clear existing data
    await execute("DELETE FROM splice_variants")
    logger.info("Cleared existing splice_variants data")

    # Generate and score all variants
    scored = score_all_variants()
    logger.info("Scored %d splice variants", len(scored))

    # Batch insert
    inserted = 0
    for v in scored:
        metadata = json.dumps({
            "full_region_index": v.get("full_region_index"),
        })
        await execute(
            """
            INSERT INTO splice_variants
                (position, region, ref_base, alt_base, variant_id,
                 splice_site_proximity, motif_disruption, conservation,
                 therapeutic_relevance, composite_score, annotation, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb)
            ON CONFLICT (variant_id) DO UPDATE SET
                splice_site_proximity = EXCLUDED.splice_site_proximity,
                motif_disruption = EXCLUDED.motif_disruption,
                conservation = EXCLUDED.conservation,
                therapeutic_relevance = EXCLUDED.therapeutic_relevance,
                composite_score = EXCLUDED.composite_score,
                annotation = EXCLUDED.annotation,
                metadata = EXCLUDED.metadata
            """,
            v["position"],
            v["region"],
            v["ref_base"],
            v["alt_base"],
            v["variant_id"],
            v["splice_site_proximity"],
            v["motif_disruption"],
            v["conservation"],
            v["therapeutic_relevance"],
            v["composite_score"],
            v["annotation"],
            metadata,
        )
        inserted += 1

    # Get quick stats
    total = await fetchval("SELECT COUNT(*) FROM splice_variants")
    high_impact = await fetchval("SELECT COUNT(*) FROM splice_variants WHERE composite_score >= 0.7")
    top = await fetchrow("SELECT variant_id, composite_score FROM splice_variants ORDER BY composite_score DESC LIMIT 1")

    logger.info("Splice benchmark generated: %d variants, %d high-impact", total, high_impact)

    return {
        "status": "ok",
        "variants_generated": total,
        "high_impact_count": high_impact,
        "top_variant": {
            "variant_id": top["variant_id"] if top else None,
            "composite_score": top["composite_score"] if top else None,
        },
    }
