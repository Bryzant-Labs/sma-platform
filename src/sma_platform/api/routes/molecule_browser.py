"""Molecule Browser API — paginated, filterable access to designed molecules.

Routes
------
GET  /molecules/browser         — paginated list with filters + sort
GET  /molecules/browser/stats   — aggregate counts by target, method, BBB
GET  /molecules/browser/{id}    — single molecule detail
GET  /molecules/browser/export  — CSV or SDF download
"""

from __future__ import annotations

import csv
import io
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from ...core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/molecules/browser", tags=["molecule-browser"])

# ---------------------------------------------------------------------------
# Ensure table + indexes exist (called lazily on first request)
# ---------------------------------------------------------------------------

_INIT_SQL = """
DO $$ BEGIN
    ALTER TABLE designed_molecules ADD COLUMN IF NOT EXISTS tpsa NUMERIC;
EXCEPTION WHEN OTHERS THEN NULL; END $$;
DO $$ BEGIN
    ALTER TABLE designed_molecules ADD COLUMN IF NOT EXISTS lipinski_pass BOOLEAN;
EXCEPTION WHEN OTHERS THEN NULL; END $$;
DO $$ BEGIN
    ALTER TABLE designed_molecules ADD COLUMN IF NOT EXISTS diffdock_target TEXT;
EXCEPTION WHEN OTHERS THEN NULL; END $$;
DO $$ BEGIN
    ALTER TABLE designed_molecules ADD COLUMN IF NOT EXISTS generation_batch TEXT;
EXCEPTION WHEN OTHERS THEN NULL; END $$;
DO $$ BEGIN
    ALTER TABLE designed_molecules ADD COLUMN IF NOT EXISTS svg_2d TEXT;
EXCEPTION WHEN OTHERS THEN NULL; END $$;

CREATE INDEX IF NOT EXISTS idx_dm_target ON designed_molecules(target_symbol);
CREATE INDEX IF NOT EXISTS idx_dm_qed ON designed_molecules(qed DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_dm_bbb ON designed_molecules(bbb_permeable) WHERE bbb_permeable = true;
CREATE INDEX IF NOT EXISTS idx_dm_method ON designed_molecules(method);
CREATE INDEX IF NOT EXISTS idx_dm_batch ON designed_molecules(generation_batch);
"""

_initialized = False


async def _ensure_schema():
    global _initialized
    if _initialized:
        return
    from ...core.database import execute_script
    try:
        await execute_script(_INIT_SQL)
        _initialized = True
    except Exception as e:
        logger.warning("Schema init (non-fatal): %s", e)
        _initialized = True


# ---------------------------------------------------------------------------
# GET /molecules/browser — paginated list
# ---------------------------------------------------------------------------

@router.get("")
async def list_molecules(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    target: Optional[str] = Query(None, description="Filter by target symbol"),
    min_qed: Optional[float] = Query(None, ge=0, le=1, description="Minimum QED"),
    max_mw: Optional[float] = Query(None, description="Maximum molecular weight"),
    bbb_only: bool = Query(False, description="Only BBB-permeable"),
    lipinski_only: bool = Query(False, description="Only Lipinski-passing"),
    method: Optional[str] = Query(None, description="Filter by generation method"),
    batch: Optional[str] = Query(None, description="Filter by generation batch"),
    sort: str = Query("newest", description="Sort: qed_desc, mw_asc, confidence_desc, newest"),
    search_smiles: Optional[str] = Query(None, description="Search by SMILES substring"),
):
    """Paginated molecule listing with filters and sorting."""
    await _ensure_schema()

    conditions = []
    args = []
    idx = 1

    if target:
        conditions.append(f"target_symbol = ${idx}")
        args.append(target)
        idx += 1
    if min_qed is not None:
        conditions.append(f"qed >= ${idx}")
        args.append(min_qed)
        idx += 1
    if max_mw is not None:
        conditions.append(f"mw <= ${idx}")
        args.append(max_mw)
        idx += 1
    if bbb_only:
        conditions.append("bbb_permeable = true")
    if lipinski_only:
        conditions.append("lipinski_pass = true")
    if method:
        conditions.append(f"method = ${idx}")
        args.append(method)
        idx += 1
    if batch:
        conditions.append(f"generation_batch = ${idx}")
        args.append(batch)
        idx += 1
    if search_smiles:
        conditions.append(f"smiles ILIKE ${idx}")
        args.append(f"%{search_smiles}%")
        idx += 1

    where = " WHERE " + " AND ".join(conditions) if conditions else ""

    sort_map = {
        "qed_desc": "qed DESC NULLS LAST",
        "mw_asc": "mw ASC NULLS LAST",
        "confidence_desc": "diffdock_confidence DESC NULLS LAST",
        "newest": "created_at DESC",
    }
    order = sort_map.get(sort, "created_at DESC")

    count_q = f"SELECT COUNT(*) FROM designed_molecules{where}"
    total = await fetchval(count_q, *args)

    offset = (page - 1) * per_page
    data_q = f"""
        SELECT id, target_symbol, smiles, scaffold_smiles, qed, mw, logp,
               hbd, hba, tpsa, bbb_permeable, cns_mpo, lipinski_pass,
               diffdock_confidence, diffdock_target, method, generation_batch,
               svg_2d, created_at, score
        FROM designed_molecules
        {where}
        ORDER BY {order}
        LIMIT ${idx} OFFSET ${idx + 1}
    """
    args.extend([per_page, offset])
    rows = await fetch(data_q, *args)

    molecules = []
    for r in rows:
        molecules.append({
            "id": r["id"],
            "target_symbol": r["target_symbol"],
            "smiles": r["smiles"],
            "scaffold_smiles": r.get("scaffold_smiles"),
            "qed": float(r["qed"]) if r.get("qed") is not None else None,
            "mw": float(r["mw"]) if r.get("mw") is not None else None,
            "logp": float(r["logp"]) if r.get("logp") is not None else None,
            "hbd": r.get("hbd"),
            "hba": r.get("hba"),
            "tpsa": float(r["tpsa"]) if r.get("tpsa") is not None else None,
            "bbb_permeable": r.get("bbb_permeable"),
            "cns_mpo": float(r["cns_mpo"]) if r.get("cns_mpo") is not None else None,
            "lipinski_pass": r.get("lipinski_pass"),
            "diffdock_confidence": float(r["diffdock_confidence"]) if r.get("diffdock_confidence") is not None else None,
            "diffdock_target": r.get("diffdock_target"),
            "method": r.get("method"),
            "generation_batch": r.get("generation_batch"),
            "svg_2d": r.get("svg_2d"),
            "created_at": str(r["created_at"]) if r.get("created_at") else None,
            "score": float(r["score"]) if r.get("score") is not None else None,
        })

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total else 0,
        "molecules": molecules,
    }


# ---------------------------------------------------------------------------
# GET /molecules/browser/stats — aggregate stats
# ---------------------------------------------------------------------------

@router.get("/stats")
async def molecule_stats():
    """Aggregate statistics for the molecule collection."""
    await _ensure_schema()

    total = await fetchval("SELECT COUNT(*) FROM designed_molecules") or 0
    bbb_count = await fetchval("SELECT COUNT(*) FROM designed_molecules WHERE bbb_permeable = true") or 0
    lipinski_count = await fetchval("SELECT COUNT(*) FROM designed_molecules WHERE lipinski_pass = true") or 0
    avg_qed = await fetchval("SELECT ROUND(AVG(qed)::numeric, 3) FROM designed_molecules WHERE qed IS NOT NULL")
    avg_mw = await fetchval("SELECT ROUND(AVG(mw)::numeric, 1) FROM designed_molecules WHERE mw IS NOT NULL")
    docked_count = await fetchval("SELECT COUNT(*) FROM designed_molecules WHERE diffdock_confidence IS NOT NULL") or 0

    by_target = await fetch("""
        SELECT target_symbol, COUNT(*) as count,
               ROUND(AVG(qed)::numeric, 3) as avg_qed,
               SUM(CASE WHEN bbb_permeable THEN 1 ELSE 0 END) as bbb_count
        FROM designed_molecules
        GROUP BY target_symbol
        ORDER BY count DESC
    """)

    by_method = await fetch("""
        SELECT COALESCE(method, 'unknown') as method, COUNT(*) as count
        FROM designed_molecules
        GROUP BY method
        ORDER BY count DESC
    """)

    by_batch = await fetch("""
        SELECT COALESCE(generation_batch, 'legacy') as batch, COUNT(*) as count
        FROM designed_molecules
        WHERE generation_batch IS NOT NULL
        GROUP BY generation_batch
        ORDER BY count DESC
    """)

    targets_covered = await fetchval("SELECT COUNT(DISTINCT target_symbol) FROM designed_molecules") or 0

    return {
        "total": total,
        "bbb_permeable": bbb_count,
        "lipinski_pass": lipinski_count,
        "docked": docked_count,
        "targets_covered": targets_covered,
        "avg_qed": float(avg_qed) if avg_qed is not None else None,
        "avg_mw": float(avg_mw) if avg_mw is not None else None,
        "by_target": [dict(r) for r in by_target],
        "by_method": [dict(r) for r in by_method],
        "by_batch": [dict(r) for r in by_batch],
    }


# ---------------------------------------------------------------------------
# GET /molecules/browser/export — CSV or SDF
# ---------------------------------------------------------------------------

@router.get("/export")
async def export_molecules(
    format: str = Query("csv", description="Export format: csv or sdf"),
    target: Optional[str] = Query(None),
    bbb_only: bool = Query(False),
):
    """Export molecules as CSV or SDF for researchers/chemists."""
    await _ensure_schema()

    conditions = []
    args = []
    idx = 1

    if target:
        conditions.append(f"target_symbol = ${idx}")
        args.append(target)
        idx += 1
    if bbb_only:
        conditions.append("bbb_permeable = true")

    where = " WHERE " + " AND ".join(conditions) if conditions else ""

    rows = await fetch(f"""
        SELECT id, target_symbol, smiles, scaffold_smiles, qed, mw, logp,
               hbd, hba, tpsa, bbb_permeable, cns_mpo, lipinski_pass,
               diffdock_confidence, diffdock_target, method, generation_batch,
               created_at
        FROM designed_molecules
        {where}
        ORDER BY qed DESC NULLS LAST
        LIMIT 10000
    """, *args)

    if format == "sdf":
        return _export_sdf(rows)
    return _export_csv(rows)


def _export_csv(rows):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "target", "smiles", "scaffold_smiles", "qed", "mw", "logp",
        "hbd", "hba", "tpsa", "bbb_permeable", "cns_mpo", "lipinski_pass",
        "diffdock_confidence", "diffdock_target", "method", "batch", "created_at"
    ])
    for r in rows:
        writer.writerow([
            r["id"], r["target_symbol"], r["smiles"], r.get("scaffold_smiles", ""),
            r.get("qed", ""), r.get("mw", ""), r.get("logp", ""),
            r.get("hbd", ""), r.get("hba", ""), r.get("tpsa", ""),
            r.get("bbb_permeable", ""), r.get("cns_mpo", ""),
            r.get("lipinski_pass", ""), r.get("diffdock_confidence", ""),
            r.get("diffdock_target", ""), r.get("method", ""),
            r.get("generation_batch", ""), r.get("created_at", ""),
        ])
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sma_molecules.csv"},
    )


def _export_sdf(rows):
    lines = []
    for r in rows:
        smiles = r.get("smiles", "")
        name = f"{r['target_symbol']}_{r['id']}"
        lines.append(name)
        lines.append(f"  SMA-Platform  {r.get('method', 'MolMIM')}")
        lines.append("")
        lines.append("  0  0  0  0  0  0  0  0  0  0  0 V2000")
        lines.append("M  END")
        lines.append(">  <SMILES>")
        lines.append(smiles)
        lines.append("")
        lines.append(">  <TARGET>")
        lines.append(r["target_symbol"])
        lines.append("")
        if r.get("qed") is not None:
            lines.append(">  <QED>")
            lines.append(str(r["qed"]))
            lines.append("")
        if r.get("mw") is not None:
            lines.append(">  <MW>")
            lines.append(str(r["mw"]))
            lines.append("")
        if r.get("bbb_permeable") is not None:
            lines.append(">  <BBB_PERMEABLE>")
            lines.append(str(r["bbb_permeable"]))
            lines.append("")
        if r.get("diffdock_confidence") is not None:
            lines.append(">  <DIFFDOCK_CONFIDENCE>")
            lines.append(str(r["diffdock_confidence"]))
            lines.append("")
        lines.append("$$$$")
    content = "\n".join(lines)
    return StreamingResponse(
        io.StringIO(content),
        media_type="chemical/x-mdl-sdfile",
        headers={"Content-Disposition": "attachment; filename=sma_molecules.sdf"},
    )


# ---------------------------------------------------------------------------
# GET /molecules/browser/{mol_id} — single molecule detail
# ---------------------------------------------------------------------------

@router.get("/{mol_id}")
async def get_molecule(mol_id: int):
    """Get full details for a single molecule."""
    await _ensure_schema()

    row = await fetchrow("""
        SELECT id, target_symbol, smiles, scaffold_smiles, qed, mw, logp,
               hbd, hba, tpsa, bbb_permeable, cns_mpo, lipinski_pass,
               diffdock_confidence, diffdock_target, method, generation_batch,
               svg_2d, created_at, score
        FROM designed_molecules WHERE id = $1
    """, mol_id)

    if not row:
        raise HTTPException(404, detail="Molecule not found")

    return {
        "id": row["id"],
        "target_symbol": row["target_symbol"],
        "smiles": row["smiles"],
        "scaffold_smiles": row.get("scaffold_smiles"),
        "qed": float(row["qed"]) if row.get("qed") is not None else None,
        "mw": float(row["mw"]) if row.get("mw") is not None else None,
        "logp": float(row["logp"]) if row.get("logp") is not None else None,
        "hbd": row.get("hbd"),
        "hba": row.get("hba"),
        "tpsa": float(row["tpsa"]) if row.get("tpsa") is not None else None,
        "bbb_permeable": row.get("bbb_permeable"),
        "cns_mpo": float(row["cns_mpo"]) if row.get("cns_mpo") is not None else None,
        "lipinski_pass": row.get("lipinski_pass"),
        "diffdock_confidence": float(row["diffdock_confidence"]) if row.get("diffdock_confidence") is not None else None,
        "diffdock_target": row.get("diffdock_target"),
        "method": row.get("method"),
        "generation_batch": row.get("generation_batch"),
        "svg_2d": row.get("svg_2d"),
        "created_at": str(row["created_at"]) if row.get("created_at") else None,
        "score": float(row["score"]) if row.get("score") is not None else None,
    }
