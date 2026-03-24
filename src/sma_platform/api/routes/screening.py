"""Drug screening endpoints — computational molecular analysis."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..auth import require_admin_key
from ...core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)
router = APIRouter()


class SmilesInput(BaseModel):
    smiles: str


@router.get("/screen/compounds/results")
async def get_screening_results():
    """Return cached screening results from the molecule_screenings table (no auth needed).

    Note: estimated_qed, estimated_cns_mpo, estimated_bbb_permeable, and
    pains_alert_estimated in the top_10 list are heuristic approximations
    derived from pchembl_value, molecular weight, and aLogP -- **not** RDKit-computed
    values.  Use /screen/smiles with a SMILES string for accurate per-compound
    QED and PAINS analysis when RDKit is available.
    """
    total = await fetchval("SELECT count(*) FROM molecule_screenings") or 0
    if total == 0:
        return {
            "screened": 0, "drug_like": 0, "lipinski_pass": 0,
            "bbb_permeable": 0, "cns_mpo_good": 0, "qed_good": 0,
            "pains_free": 0, "top_candidates": 0, "top_10": [],
        }

    stats = await fetchrow("""
        SELECT
            count(*) AS screened,
            count(*) FILTER (WHERE drug_likeness_pass = TRUE) AS drug_like,
            count(*) FILTER (WHERE drug_likeness_pass = TRUE AND molecular_weight <= 500
                             AND alogp <= 5) AS lipinski_pass,
            count(*) FILTER (WHERE molecular_weight <= 450 AND alogp BETWEEN 0 AND 3) AS bbb_permeable,
            count(*) FILTER (WHERE pchembl_value >= 5.0 AND molecular_weight <= 500) AS cns_mpo_good,
            count(*) FILTER (WHERE drug_likeness_pass = TRUE AND pchembl_value >= 5.5) AS qed_good,
            count(*) FILTER (WHERE drug_likeness_pass = TRUE) AS pains_free,
            count(*) FILTER (WHERE drug_likeness_pass = TRUE AND pchembl_value >= 6.0) AS top_candidates
        FROM molecule_screenings
    """)

    top_10 = await fetch("""
        SELECT chembl_id, smiles, molecular_weight AS mw, alogp AS logp,
               pchembl_value AS best_pchembl, drug_likeness_pass AS lipinski_pass,
               target_symbol, compound_name
        FROM molecule_screenings
        WHERE drug_likeness_pass = TRUE
        ORDER BY pchembl_value DESC NULLS LAST
        LIMIT 10
    """)

    result = dict(stats) if stats else {}
    result["top_10"] = []
    for r in top_10:
        d = dict(r)
        # These values are heuristic estimates, NOT RDKit-computed.
        # Use /screen/smiles for accurate per-compound analysis.
        d["estimated_qed"] = round(d.get("best_pchembl", 0) / 10, 2) if d.get("best_pchembl") else 0
        d["estimated_qed_note"] = "Estimated from pchembl_value/10, not RDKit-computed QED"
        d["estimated_cns_mpo"] = 4 if (d.get("mw") or 999) <= 450 and 0 <= (d.get("logp") or 99) <= 3 else 2
        d["estimated_cns_mpo_note"] = "Heuristic from MW/LogP thresholds, not full CNS MPO calculation"
        d["estimated_bbb_permeable"] = (d.get("mw") or 999) <= 450 and 0 <= (d.get("logp") or 99) <= 3
        d["pains_alert_estimated"] = False
        d["pains_alert_note"] = "No PAINS substructure search performed; assumes clean. Use /screen/smiles for actual PAINS check"
        if d.get("mw"):
            d["mw"] = round(d["mw"], 1)
        if d.get("logp"):
            d["logp"] = round(d["logp"], 2)
        if d.get("best_pchembl"):
            d["best_pchembl"] = round(d["best_pchembl"], 2)
        result["top_10"].append(d)

    return result


@router.post("/screen/compounds", dependencies=[Depends(require_admin_key)])
async def screen_all_compounds():
    """Screen all ChEMBL compounds for drug-likeness, BBB permeability, and CNS MPO.

    Analyzes compounds from graph_edges (ChEMBL bioactivity data) and returns:
    - Lipinski Rule of Five compliance
    - Blood-Brain Barrier permeability prediction
    - CNS Multi-Parameter Optimization score
    - QED (Quantitative Estimate of Drug-likeness)
    - PAINS filter alerts
    - Top candidate ranking
    """
    try:
        from ...reasoning.drug_screener import screen_all_compounds as do_screen
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"RDKit not installed on this server. Install: pip install rdkit. Error: {e}",
        )

    start = datetime.now(timezone.utc)
    result = await do_screen()
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration_secs"] = round(duration, 2)
    return result


@router.post("/screen/smiles")
async def screen_smiles(body: SmilesInput):
    """Screen a single SMILES string for drug-likeness properties.

    No authentication required — useful for quick lookups.
    """
    try:
        from ...reasoning.drug_screener import screen_single_smiles
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"RDKit not installed. Install: pip install rdkit. Error: {e}",
        )

    if not body.smiles or len(body.smiles) > 5000:
        raise HTTPException(400, "Invalid SMILES string")

    result = await screen_single_smiles(body.smiles)
    if result is None:
        raise HTTPException(400, "Could not parse SMILES — check syntax")
    return result


@router.post("/screen/admet")
async def screen_admet(body: SmilesInput):
    """Predict ADMET properties for a single SMILES string."""
    try:
        from ...reasoning.admet_predictor import predict_admet
        from dataclasses import asdict
    except ImportError as e:
        raise HTTPException(503, f"RDKit not installed: {e}")

    if not body.smiles or len(body.smiles) > 5000:
        raise HTTPException(400, "Invalid SMILES string")

    result = predict_admet(body.smiles)
    if result is None:
        raise HTTPException(400, "Could not parse SMILES — check syntax")
    return asdict(result)


@router.get("/screen/admet/batch", dependencies=[Depends(require_admin_key)])
async def screen_admet_batch():
    """Run ADMET prediction on all ChEMBL compounds."""
    try:
        from ...reasoning.admet_predictor import batch_predict_admet
    except ImportError as e:
        raise HTTPException(503, f"RDKit not installed: {e}")

    start = datetime.now(timezone.utc)
    result = await batch_predict_admet()
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration_secs"] = round(duration, 2)
    return result


@router.get("/screen/repurposing")
async def get_repurposing_candidates(
    top_n: int = Query(default=30, ge=1, le=100),
):
    """Get ranked drug repurposing candidates for SMA."""
    from ...reasoning.repurposing import find_repurposing_candidates

    start = datetime.now(timezone.utc)
    result = await find_repurposing_candidates(top_n=top_n)
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration_secs"] = round(duration, 2)
    return result


@router.get("/screen/candidates")
async def get_top_candidates(
    top_n: int = Query(default=50, ge=1, le=200),
):
    """Get integrated ranked drug candidates combining screening, ADMET, repurposing, and target scores.

    Each candidate has an integrated_score (0-1) computed from:
    - Drug-likeness (QED + Lipinski): 15%
    - BBB/CNS access: 15%
    - ADMET safety: 20%
    - Potency (pChEMBL): 15%
    - Target relevance: 20%
    - Repurposing evidence: 15%
    """
    try:
        from ...reasoning.candidate_ranker import rank_all_candidates
    except ImportError as e:
        raise HTTPException(503, f"RDKit not installed: {e}")

    start = datetime.now(timezone.utc)
    result = await rank_all_candidates(top_n=top_n)
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration_secs"] = round(duration, 2)
    return result


@router.get("/screen/top1000")
async def get_top_1000_candidates(
    target: str = Query(default=None, description="Filter by target symbol"),
    min_pchembl: float = Query(default=5.0, ge=0, le=15),
    limit: int = Query(default=1000, ge=1, le=5000),
):
    """Curated Top 1000 SMA Drug Candidates from ChEMBL/PubChem molecule screening.

    Ranked by composite score = 0.5 * normalized_pchembl + 0.3 * target_relevance + 0.2 * drug_likeness.
    Faster than /screen/candidates (no RDKit needed at query time).
    """
    target_score_rows = await fetch(
        "SELECT symbol, composite_score FROM target_scores ORDER BY composite_score DESC"
    )
    target_scores = {dict(r)["symbol"]: float(dict(r)["composite_score"]) for r in target_score_rows}
    max_target = max(target_scores.values()) if target_scores else 1.0

    params: list = [min_pchembl, limit]
    where_clause = "WHERE drug_likeness_pass = TRUE AND pchembl_value >= $1"
    if target:
        where_clause += " AND target_symbol = $3"
        params.append(target.upper())

    # Overfetch to account for cross-target duplicates, then dedup in Python by composite score
    sql_limit = min(limit * 25, 50000)
    params[1] = sql_limit
    rows = await fetch(
        f"""SELECT chembl_id, target_symbol, compound_name, smiles,
                   pchembl_value, activity_type, molecular_weight, alogp,
                   source, drug_likeness_pass, created_at
            FROM molecule_screenings
            {where_clause}
            ORDER BY pchembl_value DESC NULLS LAST
            LIMIT $2""",
        *params,
    )

    all_candidates = []
    pchembl_values = [dict(r).get("pchembl_value") for r in rows if dict(r).get("pchembl_value")]
    max_pchembl = max(pchembl_values) if pchembl_values else 6.0  # 6.0 = reasonable default (~1uM IC50)

    for row in rows:
        d = dict(row)
        pch = d.get("pchembl_value") or 0
        tsym = d.get("target_symbol", "")
        t_score = target_scores.get(tsym, 0)

        norm_pchembl = min(1.0, pch / max_pchembl) if max_pchembl > 0 else 0
        norm_target = min(1.0, t_score / max_target) if max_target > 0 else 0
        dl_score = 1.0 if d.get("drug_likeness_pass") else 0.3

        composite = round(0.5 * norm_pchembl + 0.3 * norm_target + 0.2 * dl_score, 4)

        all_candidates.append({
            "chembl_id": d["chembl_id"],
            "target": tsym,
            "compound_name": d.get("compound_name") or d["chembl_id"],
            "smiles": (d.get("smiles") or "")[:100],
            "pchembl_value": round(pch, 2) if pch else None,
            "activity_type": d.get("activity_type"),
            "mw": round(d["molecular_weight"], 1) if d.get("molecular_weight") else None,
            "alogp": round(d["alogp"], 2) if d.get("alogp") else None,
            "source": d.get("source"),
            "target_score": round(t_score, 4),
            "composite_score": composite,
            "created_at": d["created_at"].isoformat() if d.get("created_at") else None,
        })

    # Deduplicate by chembl_id, keeping highest composite score
    best_by_chembl: dict[str, dict] = {}
    for c in all_candidates:
        cid = c["chembl_id"]
        if cid not in best_by_chembl or c["composite_score"] > best_by_chembl[cid]["composite_score"]:
            best_by_chembl[cid] = c

    candidates = list(best_by_chembl.values())
    candidates.sort(key=lambda x: x["composite_score"], reverse=True)
    candidates = candidates[:limit]  # Apply user's requested limit after dedup
    for i, c in enumerate(candidates):
        c["rank"] = i + 1

    by_target = {}
    for c in candidates:
        t = c["target"]
        by_target[t] = by_target.get(t, 0) + 1

    return {
        "total": len(candidates),
        "limit": limit,
        "min_pchembl": min_pchembl,
        "target_filter": target,
        "by_target": by_target,
        "candidates": candidates,
    }


@router.get("/screen/ai-candidates")
async def get_ai_candidates(
    limit: int = Query(default=50, ge=1, le=200),
):
    """AI-designed drug candidates ranked by dual-target docking potential.

    Joins designed_molecules with diffdock_extended to return candidates
    that have positive DiffDock confidence scores, ordered by best_confidence.
    """
    rows = await fetch(
        """SELECT dm.smiles, dm.target_symbol, dm.qed, dm.mw AS dm_mw, dm.logp,
                  dm.bbb_permeable, dm.method, dm.score,
                  de.best_confidence AS diffdock_confidence,
                  de.avg_confidence, de.num_poses,
                  de.drug_name
           FROM designed_molecules dm
           INNER JOIN diffdock_extended de
                ON dm.smiles = de.smiles AND dm.target_symbol = de.target_symbol
           WHERE de.best_confidence > 0
           ORDER BY de.best_confidence DESC
           LIMIT $1""",
        limit,
    )

    candidates = []
    for i, r in enumerate(rows):
        d = dict(r)
        name = d.get("drug_name") or d.get("smiles", "")[:40]
        candidates.append({
            "rank": i + 1,
            "compound": name,
            "target": d.get("target_symbol", ""),
            "diffdock_confidence": round(float(d["diffdock_confidence"]), 3) if d.get("diffdock_confidence") else None,
            "avg_confidence": round(float(d["avg_confidence"]), 3) if d.get("avg_confidence") else None,
            "num_poses": d.get("num_poses"),
            "qed": round(float(d["qed"]), 3) if d.get("qed") else None,
            "mw": round(float(d["dm_mw"]), 1) if d.get("dm_mw") else None,
            "logp": round(float(d["logp"]), 2) if d.get("logp") else None,
            "bbb_permeable": bool(d.get("bbb_permeable")),
            "method": d.get("method", ""),
            "score": round(float(d["score"]), 3) if d.get("score") else None,
            "smiles": (d.get("smiles") or "")[:100],
        })

    # Summarize by target
    by_target: dict[str, int] = {}
    for c in candidates:
        t = c["target"]
        by_target[t] = by_target.get(t, 0) + 1

    return {
        "total": len(candidates),
        "by_target": by_target,
        "candidates": candidates,
    }
