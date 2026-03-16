"""Cross-Paper Synthesis API Routes — Differentiator #1.

Endpoints for the cross-paper synthesis engine that finds non-obvious
connections across 24k+ claims from different papers.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/synthesis", tags=["cross-paper-synthesis"])


@router.get("/cards")
async def get_cards(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    synthesis_type: Optional[str] = None,
    target: Optional[str] = None,
):
    """Get cross-paper synthesis cards with optional filtering."""
    from ...reasoning.cross_paper_synthesis import get_synthesis_cards
    cards = await get_synthesis_cards(limit, offset, synthesis_type, target)
    return {"cards": cards, "count": len(cards)}


@router.get("/stats")
async def synthesis_stats():
    """Get synthesis card statistics."""
    from ...reasoning.cross_paper_synthesis import get_synthesis_stats
    return await get_synthesis_stats()


@router.get("/cooccurrences")
async def get_cooccurrences(limit: int = Query(20, ge=1, le=100)):
    """Get top target co-occurrence pairs (targets mentioned in same paper)."""
    from ...reasoning.cross_paper_synthesis import build_cooccurrence_matrix

    cooccurrences = await build_cooccurrence_matrix()

    # Score and sort
    scored = []
    for (a, b), sources in cooccurrences.items():
        if len(sources) >= 2:
            all_claims = [c for s in sources for c in s["claims"]]
            avg_conf = sum(c["confidence"] for c in all_claims) / max(len(all_claims), 1)
            scored.append({
                "target_a": a, "target_b": b,
                "shared_papers": len(sources),
                "total_claims": len(all_claims),
                "avg_confidence": round(avg_conf, 3),
                "score": round(len(sources) * avg_conf, 2),
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return {"cooccurrences": scored[:limit], "total": len(scored)}


@router.get("/bridges")
async def get_bridges(limit: int = Query(20, ge=1, le=100)):
    """Get transitive bridges: A→B→C chains across different papers."""
    from ...reasoning.cross_paper_synthesis import find_transitive_bridges

    bridges = await find_transitive_bridges()
    return {
        "bridges": [
            {
                "target_a": b["target_a"],
                "bridge": b["bridge"],
                "target_c": b["target_c"],
                "a_to_b_predicate": b["a_to_b"]["predicate"],
                "b_to_c_predicate": b["b_to_c"]["predicate"],
                "combined_confidence": round(b["combined_confidence"], 3),
            }
            for b in bridges[:limit]
        ],
        "total": len(bridges),
    }


@router.get("/shared-mechanisms")
async def get_shared_mechanisms(limit: int = Query(20, ge=1, le=100)):
    """Get mechanisms shared across different targets."""
    from ...reasoning.cross_paper_synthesis import find_shared_mechanisms

    shared = await find_shared_mechanisms()
    return {
        "mechanisms": [
            {
                "mechanism": m["mechanism"],
                "targets": m["targets"],
                "num_claims": m["num_claims"],
                "avg_confidence": round(m["avg_confidence"], 3),
            }
            for m in shared[:limit]
        ],
        "total": len(shared),
    }


@router.get("/temporal")
async def get_temporal_reinforcements(limit: int = Query(20, ge=1, le=100)):
    """Find when new evidence retroactively strengthens old findings.

    For each target, splits claims into old/new by median publication date,
    then identifies claim_types where new papers reinforce earlier discoveries.
    """
    from ...reasoning.cross_paper_synthesis import find_temporal_reinforcements
    results = await find_temporal_reinforcements()
    return {"reinforcements": results[:limit], "total": len(results)}


@router.get("/contradictions")
async def get_contradictions(limit: int = Query(20, ge=1, le=100)):
    """Find claims about the same target that may contradict each other.

    Groups claims by target + claim_type, then detects opposing signals
    (positive vs negative effect keywords) from different sources.
    Higher contradiction_score = more balanced contradiction.
    """
    from ...reasoning.cross_paper_synthesis import find_contradictions
    results = await find_contradictions()
    return {"contradictions": results[:limit], "total": len(results)}


@router.get("/surprise")
async def get_surprise_scores(limit: int = Query(30, ge=1, le=100)):
    """Rank target connections by how NON-OBVIOUS they are.

    Low paper overlap + high claim diversity + independent sources + recent
    = high surprise score. Pure math, no LLM calls.
    """
    from ...reasoning.cross_paper_synthesis import score_evidence_surprise
    results = await score_evidence_surprise()
    return {"surprises": results[:limit], "total": len(results)}


@router.post("/run", dependencies=[Depends(require_admin_key)])
async def run_synthesis(
    max_cards: int = Query(50, ge=1, le=200),
    synthesize: bool = Query(True),
):
    """
    Run the full cross-paper synthesis pipeline (admin).
    Finds co-occurrences, transitive bridges, shared mechanisms,
    and optionally uses Claude to generate synthesis cards.
    """
    from ...reasoning.cross_paper_synthesis import run_synthesis_pipeline

    try:
        result = await run_synthesis_pipeline(
            max_cards=max_cards,
            synthesize=synthesize,
        )
        return result
    except Exception as e:
        logger.error(f"Synthesis pipeline failed: {e}", exc_info=True)
        raise HTTPException(500, f"Synthesis pipeline failed: {str(e)}")
