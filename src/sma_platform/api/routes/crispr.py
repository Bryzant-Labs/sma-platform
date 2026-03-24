"""CRISPR guide RNA design endpoints (Phase 6.2 → DB-backed).

GET  /crispr/guides          — list guides from DB (filter by strategy, region, motif)
POST /crispr/guides          — design guides for a custom sequence (compute-only, not persisted)
GET  /crispr/strategies      — list all therapeutic strategies
GET  /crispr/strategies/{id} — one strategy with its guides
GET  /crispr/motifs          — SMN2 exon 7 regulatory motifs reference
POST /crispr/seed            — (admin) re-seed DB from computed SMN2 guides
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel

from ...core.database import execute, execute_script, fetch, fetchrow, fetchval
from ...reasoning.crispr_designer import (
    MOTIFS,
    design_guides_for_target,
    design_smn2_guides,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# DDL (lazy init)
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS crispr_strategies (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    target_gene TEXT NOT NULL DEFAULT 'SMN2',
    target_region TEXT NOT NULL,
    mechanism   TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crispr_guides (
    id              SERIAL PRIMARY KEY,
    strategy_id     INT REFERENCES crispr_strategies(id) ON DELETE SET NULL,
    sequence        TEXT NOT NULL,
    pam             TEXT NOT NULL,
    strand          CHAR(1) NOT NULL,
    position        INT NOT NULL,
    region          TEXT NOT NULL,
    gc_pct          FLOAT NOT NULL,
    on_target_score FLOAT NOT NULL,
    cfd_score       FLOAT NOT NULL DEFAULT 0.0,
    motifs          TEXT[] NOT NULL DEFAULT '{}',
    notes           TEXT NOT NULL DEFAULT '',
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_crispr_guides_strategy ON crispr_guides(strategy_id);
CREATE INDEX IF NOT EXISTS idx_crispr_guides_on_target ON crispr_guides(on_target_score DESC);
CREATE INDEX IF NOT EXISTS idx_crispr_guides_region ON crispr_guides(region);
"""

_tables_ready = False


async def _ensure_tables() -> None:
    global _tables_ready
    if _tables_ready:
        return
    await execute_script(_DDL)
    await execute_script(_INDEXES)
    _tables_ready = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _guide_row(row) -> dict:
    meta = row["metadata"] if isinstance(row["metadata"], dict) else json.loads(row["metadata"] or "{}")
    return {
        "id": row["id"],
        "strategy_id": row["strategy_id"],
        "sequence": row["sequence"],
        "pam": row["pam"],
        "strand": row["strand"],
        "position": row["position"],
        "region": row["region"],
        "gc_pct": row["gc_pct"],
        # Frontend compat aliases
        "gc_content": row["gc_pct"],
        "specificity_score": meta.get("specificity_score"),
        "off_target_count": meta.get("off_target_count", 0),
        "target_gene": meta.get("target_gene", "SMN2"),
        "strategy": meta.get("strategy", "SpCas9"),
        "on_target_score": row["on_target_score"],
        "cfd_score": row["cfd_score"],
        "motifs": list(row["motifs"]) if row["motifs"] else [],
        "notes": row["notes"],
        "metadata": meta,
    }


def _strategy_row(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "target_gene": row["target_gene"],
        "target_region": row["target_region"],
        "mechanism": row["mechanism"],
        "description": row["description"],
    }


# ---------------------------------------------------------------------------
# Input model
# ---------------------------------------------------------------------------

class GuideDesignInput(BaseModel):
    symbol: str
    sequence: str
    max_guides: int = 20


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/crispr/guides")
async def get_crispr_guides(
    symbol: str = Query(default="SMN2", description="Gene symbol filter (SMN2/SMN1 = DB; others need POST)"),
    strategy_id: Optional[int] = Query(default=None, description="Filter by strategy ID"),
    region: Optional[str] = Query(default=None, description="Filter by region: exon7, intron6, intron7"),
    motif: Optional[str] = Query(default=None, description="Filter guides that overlap a specific motif"),
    min_score: Optional[float] = Query(default=None, ge=0.0, le=1.0, description="Minimum on_target_score"),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Retrieve CRISPR guides from the database.

    For SMN2/SMN1: returns pre-computed guides with therapeutic motif annotations.
    Use POST /crispr/guides to design guides for a custom DNA sequence.
    """
    await _ensure_tables()

    if symbol.upper() not in ("SMN2", "SMN1"):
        return {
            "error": f"No DB reference for {symbol}.",
            "hint": "POST /api/v2/crispr/guides with {\"symbol\": \"GENE\", \"sequence\": \"ATCG...\"}",
        }

    conditions: list[str] = []
    params: list = []
    idx = 1

    if strategy_id is not None:
        conditions.append(f"g.strategy_id = ${idx}")
        params.append(strategy_id)
        idx += 1

    if region is not None:
        conditions.append(f"g.region = ${idx}")
        params.append(region)
        idx += 1

    if motif is not None:
        conditions.append(f"${idx} = ANY(g.motifs)")
        params.append(motif)
        idx += 1

    if min_score is not None:
        conditions.append(f"g.on_target_score >= ${idx}")
        params.append(min_score)
        idx += 1

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    rows = await fetch(
        f"""
        SELECT g.*, s.name AS strategy_name
        FROM crispr_guides g
        LEFT JOIN crispr_strategies s ON s.id = g.strategy_id
        {where}
        ORDER BY g.on_target_score DESC
        LIMIT ${idx} OFFSET ${idx + 1}
        """,
        *params,
        limit,
        offset,
    )

    total = await fetchval(
        f"SELECT count(*) FROM crispr_guides g {where}",
        *params,
    )

    guides = []
    for row in rows:
        d = _guide_row(row)
        d["strategy_name"] = row["strategy_name"]
        # Frontend reads g.strategy for filter/display
        d["strategy"] = row["strategy_name"] or d.get("strategy", "SpCas9")
        guides.append(d)

    return {
        "symbol": symbol.upper(),
        "total": total,
        "limit": limit,
        "offset": offset,
        "guides": guides,
    }


@router.post("/crispr/guides")
async def post_crispr_guides(body: GuideDesignInput):
    """Design CRISPR guides for a custom DNA sequence (compute-only, not persisted).

    Accepts 23-10000 nt DNA and scans both strands for 20nt protospacer + NGG PAM.
    """
    if len(body.sequence) < 23:
        raise HTTPException(400, "Sequence too short — need at least 23 nt (20 protospacer + 3 PAM)")
    if len(body.sequence) > 10000:
        raise HTTPException(400, "Sequence too long — maximum 10,000 nt")

    result = await design_guides_for_target(body.symbol, body.sequence)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.get("/crispr/strategies")
async def get_strategies():
    """List all CRISPR therapeutic strategies stored in the database."""
    await _ensure_tables()

    rows = await fetch(
        """
        SELECT s.*, count(g.id) AS guide_count
        FROM crispr_strategies s
        LEFT JOIN crispr_guides g ON g.strategy_id = s.id
        GROUP BY s.id
        ORDER BY s.id
        """
    )

    return {
        "strategies": [
            {**_strategy_row(r), "guide_count": r["guide_count"]}
            for r in rows
        ]
    }


@router.get("/crispr/strategies/{strategy_id}")
async def get_strategy(
    strategy_id: int = Path(..., description="Strategy ID"),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Return a single therapeutic strategy with its top guides."""
    await _ensure_tables()

    s = await fetchrow("SELECT * FROM crispr_strategies WHERE id = $1", strategy_id)
    if not s:
        raise HTTPException(404, f"Strategy {strategy_id} not found")

    guides = await fetch(
        """
        SELECT * FROM crispr_guides
        WHERE strategy_id = $1
        ORDER BY on_target_score DESC
        LIMIT $2
        """,
        strategy_id,
        limit,
    )

    return {
        **_strategy_row(s),
        "guides": [_guide_row(g) for g in guides],
        "guide_count": len(guides),
    }


@router.get("/crispr/motifs")
async def get_smn2_motifs():
    """Return all known SMN2 exon 7 regulatory motifs.

    Includes ISS-N1 (nusinersen target), ESE (Tra2-beta), ESS (hnRNP A1),
    Element2, C6T disease position, and branch point.
    """
    return {
        "reference": "SMN2 NG_008728.1, exon 7 region",
        "motifs": {name: info for name, info in MOTIFS.items()},
        "note": "Positions are 0-indexed within their respective region (intron6/exon7/intron7)",
    }


@router.post("/crispr/seed")
async def seed_smn2_guides():
    """(Admin) Re-seed the database with computed SMN2 guides.

    Clears existing SMN2 guides and strategies, then re-computes from
    the reference sequence and inserts fresh results.
    """
    await _ensure_tables()

    result = design_smn2_guides()
    strategies_data = result["strategies"]
    all_guides = result["all_guides"]

    # Clear existing
    await execute("DELETE FROM crispr_guides")
    await execute("DELETE FROM crispr_strategies")

    # Insert strategies
    strategy_ids: dict[str, int] = {}
    mechanisms = {
        "CRISPRi at ISS-N1": "CRISPRi",
        "CRISPRi at Exon 7 ESS": "CRISPRi",
        "CRISPRa at Tra2-beta ESE": "CRISPRa",
    }
    target_regions_map = {
        "CRISPRi at ISS-N1": "intron7",
        "CRISPRi at Exon 7 ESS": "exon7",
        "CRISPRa at Tra2-beta ESE": "exon7",
    }
    for s in strategies_data:
        name = s["strategy"]
        sid = await fetchval(
            """
            INSERT INTO crispr_strategies (name, target_gene, target_region, mechanism, description)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description
            RETURNING id
            """,
            name,
            "SMN2",
            target_regions_map.get(name, "unknown"),
            mechanisms.get(name, "CRISPR"),
            s["rationale"],
        )
        strategy_ids[name] = sid

    # Build seq -> strategy_id map
    seq_to_strat: dict[str, int] = {}
    for s in strategies_data:
        sid = strategy_ids[s["strategy"]]
        for g in s["guides"]:
            seq_to_strat[g["sequence"]] = sid

    # Insert guides
    inserted = 0
    for g in all_guides:
        sid = seq_to_strat.get(g["sequence"])
        meta = json.dumps({
            "specificity_score": g["specificity_score"],
            "has_polyT": g["has_polyT"],
            "reference": "SMN2 NG_008728.1",
        })
        await execute(
            """
            INSERT INTO crispr_guides
                (strategy_id, sequence, pam, strand, position, region,
                 gc_pct, on_target_score, cfd_score, motifs, notes, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """,
            sid,
            g["sequence"],
            g["pam"],
            g["strand"],
            g["position"],
            g["region"],
            g["gc_content"],
            g["on_target_score"],
            0.0,
            g["overlapping_motifs"],
            g["notes"],
            meta,
        )
        inserted += 1

    return {
        "status": "ok",
        "strategies_inserted": len(strategy_ids),
        "guides_inserted": inserted,
        "reference": result["reference"],
    }
