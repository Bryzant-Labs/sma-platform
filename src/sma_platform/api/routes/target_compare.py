"""Target Comparison — side-by-side comparison of any two SMA targets."""

from __future__ import annotations
import logging
from fastapi import APIRouter, HTTPException, Query
from ...core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/compare", tags=["target-compare"])


@router.get("/targets")
async def compare_targets(
    a: str = Query(..., description="First target symbol"),
    b: str = Query(..., description="Second target symbol"),
):
    """Compare two SMA targets across all dimensions."""
    sym_a = a.upper()
    sym_b = b.upper()

    async def get_target_data(sym):
        target = await fetchrow("SELECT * FROM targets WHERE symbol = $1", sym)
        if not target:
            raise HTTPException(404, detail=f"Target {sym} not found")
        target = dict(target)
        tid = target["id"]

        # Convergence
        conv = await fetchrow(
            "SELECT composite_score, confidence_level, claim_count, source_count, "
            "volume, lab_independence, method_diversity, temporal_trend, replication "
            "FROM convergence_scores WHERE target_id = $1 ORDER BY computed_at DESC LIMIT 1", tid)

        # Claims count
        claim_count = await fetchval(
            "SELECT COUNT(*) FROM claims WHERE subject_id = $1 OR object_id = $1", tid) or 0

        # Screening hits
        hits = await fetch(
            "SELECT hit_smiles, docking_confidence FROM screening_milestones "
            "WHERE hit_target = $1 AND docking_confidence > 0 ORDER BY docking_confidence DESC LIMIT 5", sym)

        # Conservation
        ortho_count = await fetchval(
            "SELECT COUNT(*) FROM cross_species_targets WHERE human_symbol = $1", sym) or 0

        # Hypotheses
        hyp_count = await fetchval(
            "SELECT COUNT(*) FROM hypotheses WHERE description ILIKE $1", f"%{sym}%") or 0

        conv_dict = {}
        if conv:
            c = dict(conv)
            conv_dict = {k: float(v) if isinstance(v, (int, float)) else v for k, v in c.items() if v is not None}

        return {
            "symbol": sym,
            "name": target.get("name", ""),
            "type": target.get("target_type", ""),
            "description": (target.get("description") or "")[:200],
            "convergence": conv_dict,
            "claim_count": claim_count,
            "screening_hits": [{"smiles": r["hit_smiles"], "confidence": float(r["docking_confidence"])} for r in hits],
            "positive_hits": len(hits),
            "conservation_species": ortho_count,
            "hypothesis_count": hyp_count,
        }

    data_a = await get_target_data(sym_a)
    data_b = await get_target_data(sym_b)

    # Generate comparison summary
    winner_convergence = sym_a if (data_a["convergence"].get("composite_score",0) > data_b["convergence"].get("composite_score",0)) else sym_b
    winner_hits = sym_a if data_a["positive_hits"] > data_b["positive_hits"] else sym_b
    winner_evidence = sym_a if data_a["claim_count"] > data_b["claim_count"] else sym_b

    return {
        "target_a": data_a,
        "target_b": data_b,
        "comparison": {
            "higher_convergence": winner_convergence,
            "more_screening_hits": winner_hits,
            "more_evidence": winner_evidence,
            "both_conserved": data_a["conservation_species"] > 0 and data_b["conservation_species"] > 0,
        },
    }
