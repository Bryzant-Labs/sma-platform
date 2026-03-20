"""Target Report Card — comprehensive single-target profile."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ...core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/report", tags=["target-report"])


@router.get("/target/{symbol}")
async def get_target_report(symbol: str):
    """Get comprehensive report card for an SMA target.

    Returns everything the platform knows about this target in one view:
    convergence, claims, screening hits, structure, conservation, hypotheses.
    """
    sym = symbol.upper()

    # 1. Basic target info
    target = await fetchrow(
        "SELECT * FROM targets WHERE symbol = $1", sym
    )
    if not target:
        raise HTTPException(404, detail=f"Target {sym} not found")
    target = dict(target)
    target_id = str(target["id"])

    # 2. Evidence convergence
    convergence = None
    conv_row = await fetchrow(
        "SELECT * FROM convergence_scores WHERE target_id = $1 ORDER BY computed_at DESC LIMIT 1",
        target["id"]
    )
    if conv_row:
        c = dict(conv_row)
        convergence = {
            "composite_score": float(c.get("composite_score", 0)),
            "confidence_level": c.get("confidence_level"),
            "volume": float(c.get("volume", 0)),
            "lab_independence": float(c.get("lab_independence", 0)),
            "method_diversity": float(c.get("method_diversity", 0)),
            "temporal_trend": float(c.get("temporal_trend", 0)),
            "replication": float(c.get("replication", 0)),
            "claim_count": c.get("claim_count", 0),
            "source_count": c.get("source_count", 0),
        }

    # 3. Top claims (most recent, highest confidence)
    claim_rows = await fetch("""
        SELECT c.id, c.claim_number, c.claim_type, c.predicate, c.confidence,
               s.title AS source_title, s.external_id AS pmid
        FROM claims c
        JOIN evidence e ON e.claim_id = c.id
        JOIN sources s ON e.source_id = s.id
        WHERE c.subject_id = $1 OR c.object_id = $1
        ORDER BY c.confidence DESC, c.created_at DESC
        LIMIT 10
    """, target["id"])
    claims = []
    for r in claim_rows:
        d = dict(r)
        cn = d.get("claim_number")
        claims.append({
            "claim_id": f"CLAIM-{cn:05d}" if cn else str(d["id"])[:8],
            "type": d.get("claim_type"),
            "text": d.get("predicate"),
            "confidence": float(d["confidence"]) if d.get("confidence") is not None else None,
            "source": d.get("source_title"),
            "pmid": d.get("pmid"),
        })

    # 4. Screening hits (from milestone tracker)
    hit_rows = await fetch("""
        SELECT hit_smiles, docking_confidence, stage, status, result
        FROM screening_milestones
        WHERE hit_target = $1
        ORDER BY docking_confidence DESC
    """, sym)
    hits = {}
    for r in hit_rows:
        key = r["hit_smiles"]
        if key not in hits:
            hits[key] = {
                "smiles": key,
                "docking_confidence": float(r["docking_confidence"]),
                "stages_completed": 0,
                "stages_total": 0,
            }
        hits[key]["stages_total"] += 1
        if r["status"] == "completed":
            hits[key]["stages_completed"] += 1
    screening_hits = sorted(hits.values(), key=lambda x: x["docking_confidence"], reverse=True)

    # 5. Species conservation
    ortho_rows = await fetch("""
        SELECT species, ortholog_symbol, conservation_score
        FROM cross_species_targets
        WHERE human_symbol = $1
        ORDER BY conservation_score DESC
    """, sym)
    conservation = [{"species": r["species"], "ortholog": r["ortholog_symbol"],
                     "score": r["conservation_score"]} for r in ortho_rows]

    # 6. Related hypotheses
    hyp_rows = await fetch("""
        SELECT id, title, description, hypothesis_type, confidence
        FROM hypotheses
        WHERE title ILIKE $1 OR description ILIKE $1
        ORDER BY confidence DESC
        LIMIT 5
    """, f"%{sym}%")
    hypotheses = [{"id": str(r["id"])[:8], "title": r["title"],
                   "summary": r["description"][:200] if r.get("description") else None,
                   "type": r.get("hypothesis_type"),
                   "score": float(r["confidence"]) if r.get("confidence") is not None else None}
                  for r in hyp_rows]

    # 7. AlphaFold structure
    metadata = target.get("metadata") or {}
    alphafold = metadata.get("alphafold") if isinstance(metadata, dict) else None

    # 8. Assay suggestion
    from ...reasoning.assay_ready import generate_assay_card
    try:
        best_hit = screening_hits[0] if screening_hits else None
        assay = generate_assay_card(
            smiles=best_hit["smiles"] if best_hit else "",
            target=sym,
            docking_confidence=best_hit["docking_confidence"] if best_hit else 0,
        )
    except Exception:
        assay = None

    return {
        "target": {
            "symbol": sym,
            "name": target.get("name"),
            "type": target.get("target_type"),
            "description": target.get("description"),
            "identifiers": target.get("identifiers"),
        },
        "convergence": convergence,
        "claims": {"top_claims": claims, "total": len(claims)},
        "screening": {"hits": screening_hits, "total_positive": len(screening_hits)},
        "conservation": {"species": conservation, "conserved_in": len(conservation)},
        "hypotheses": {"related": hypotheses, "total": len(hypotheses)},
        "alphafold": alphafold,
        "assay_suggestion": assay,
    }
