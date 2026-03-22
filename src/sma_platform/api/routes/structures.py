"""Protein Structures endpoints — GET /api/v2/structures."""

from __future__ import annotations

from fastapi import APIRouter, Query

from ...core.database import fetch, fetchrow

router = APIRouter()

MAX_LIMIT = 500


def _druggability(plddt: float | None, source: str | None) -> str:
    """Heuristic druggability label based on pLDDT confidence."""
    if plddt is None:
        return "Unknown"
    if plddt >= 85:
        return "High Confidence — Druggable"
    if plddt >= 70:
        return "Moderate Confidence — Assess Pocket"
    return "Low Confidence — Disordered Region"


@router.get("/structures")
async def list_structures(
    symbol: str | None = None,
    source_filter: str | None = None,
    min_plddt: float | None = None,
    limit: int = Query(default=200, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    """Return predicted structures — one best row per target symbol."""
    base_where = """
        WHERE source NOT LIKE '%RFdiffusion%'
          AND source NOT LIKE '%binder%'
          AND (uniprot_id IS NOT NULL AND uniprot_id NOT IN ('1A9U','2F2U','kinase'))
    """
    params: list = []
    extra: list[str] = []
    if symbol:
        params.append(symbol.upper())
        extra.append(f"AND target_symbol = ${len(params)}")
    if source_filter:
        params.append(f"%{source_filter}%")
        extra.append(f"AND source ILIKE ${len(params)}")
    if min_plddt is not None:
        params.append(min_plddt)
        extra.append(f"AND plddt_mean >= ${len(params)}")
    extra_sql = " ".join(extra)
    rows = await fetch(
        f"""
        SELECT DISTINCT ON (target_symbol)
            id, target_symbol, uniprot_id, source, plddt_mean, residue_count,
            pdb_path, alphafold_url, method, metadata, created_at
        FROM protein_structures
        {base_where}
        {extra_sql}
        ORDER BY target_symbol, plddt_mean DESC NULLS LAST
        LIMIT ${len(params)+1} OFFSET ${len(params)+2}
        """,
        *params, limit, offset,
    )
    symbols = [r["target_symbol"] for r in rows]
    if not symbols:
        return []
    binder_rows = await fetch(
        "SELECT target_symbol, COUNT(*) as cnt FROM designed_binders WHERE target_symbol = ANY($1) GROUP BY target_symbol",
        symbols,
    )
    binder_counts = {r["target_symbol"]: int(r["cnt"]) for r in binder_rows}
    mol_rows = await fetch(
        "SELECT target_symbol, COUNT(*) as cnt FROM designed_molecules WHERE target_symbol = ANY($1) GROUP BY target_symbol",
        symbols,
    )
    mol_counts = {r["target_symbol"]: int(r["cnt"]) for r in mol_rows}
    results = []
    for r in rows:
        sym = r["target_symbol"]
        uid = r["uniprot_id"] or ""
        plddt = float(r["plddt_mean"]) if r["plddt_mean"] is not None else None
        af_url = r["alphafold_url"]
        if not af_url and uid and len(uid) >= 6:
            af_url = f"https://alphafold.ebi.ac.uk/entry/{uid}"
        uniprot_url = f"https://www.uniprot.org/uniprot/{uid}" if uid and len(uid) >= 6 else None
        source = r["source"] or ""
        if "AlphaFold" in source:
            method_label = "AlphaFold DB"
        elif "ESMfold" in source or "ESMFold" in source:
            method_label = "ESMfold NIM"
        elif "Boltz" in source:
            method_label = "Boltz-2"
        elif "existing" in source.lower():
            method_label = "Pre-existing PDB"
        else:
            method_label = source
        results.append({
            "id": r["id"],
            "symbol": sym,
            "uniprot_id": uid,
            "source": source,
            "method_label": method_label,
            "plddt": round(plddt, 1) if plddt is not None else None,
            "residue_count": r["residue_count"],
            "druggability": _druggability(plddt, source),
            "alphafold_url": af_url,
            "uniprot_url": uniprot_url,
            "designed_binders": binder_counts.get(sym, 0),
            "designed_molecules": mol_counts.get(sym, 0),
        })
    return results


@router.get("/structures/stats")
async def structures_stats():
    """Summary counts for the structures section."""
    row = await fetchrow(
        """
        SELECT
            COUNT(DISTINCT target_symbol) FILTER (
                WHERE source NOT LIKE '%RFdiffusion%'
                  AND source NOT LIKE '%binder%'
            ) AS total_targets,
            COUNT(DISTINCT target_symbol) FILTER (
                WHERE source LIKE '%AlphaFold%'
                  AND source NOT LIKE '%RFdiffusion%'
            ) AS alphafold_count,
            COUNT(DISTINCT target_symbol) FILTER (
                WHERE (source LIKE '%ESMfold%' OR source LIKE '%ESMFold%')
                  AND source NOT LIKE '%RFdiffusion%'
            ) AS esmfold_count,
            COUNT(DISTINCT target_symbol) FILTER (
                WHERE plddt_mean >= 85
                  AND source NOT LIKE '%RFdiffusion%'
                  AND source NOT LIKE '%binder%'
            ) AS high_confidence,
            COUNT(DISTINCT target_symbol) FILTER (
                WHERE plddt_mean >= 70 AND plddt_mean < 85
                  AND source NOT LIKE '%RFdiffusion%'
                  AND source NOT LIKE '%binder%'
            ) AS moderate_confidence,
            COUNT(DISTINCT target_symbol) FILTER (
                WHERE (plddt_mean < 70 OR plddt_mean IS NULL)
                  AND source NOT LIKE '%RFdiffusion%'
                  AND source NOT LIKE '%binder%'
            ) AS low_confidence
        FROM protein_structures
        """
    )
    return dict(row) if row else {}
