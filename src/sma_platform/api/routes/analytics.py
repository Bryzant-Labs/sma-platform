"""Platform Analytics — comprehensive summary dashboard."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from ...core.database import fetch, fetchval

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def platform_summary():
    """Comprehensive platform analytics summary."""
    try:
        # Core counts
        sources = await fetchval("SELECT COUNT(*) FROM sources") or 0
        claims = await fetchval("SELECT COUNT(*) FROM claims") or 0
        hypotheses = await fetchval("SELECT COUNT(*) FROM hypotheses") or 0
        targets = await fetchval("SELECT COUNT(*) FROM targets") or 0
        trials = await fetchval("SELECT COUNT(*) FROM trials") or 0

        # Claims by type
        claim_types = await fetch(
            "SELECT claim_type, COUNT(*) as cnt FROM claims GROUP BY claim_type ORDER BY cnt DESC"
        )

        # Sources by type
        source_types = await fetch(
            "SELECT source_type, COUNT(*) as cnt FROM sources GROUP BY source_type ORDER BY cnt DESC"
        )

        # Recent activity (last 7 days)
        recent_sources = await fetchval(
            "SELECT COUNT(*) FROM sources WHERE created_at > NOW() - INTERVAL '7 days'"
        ) or 0
        recent_claims = await fetchval(
            "SELECT COUNT(*) FROM claims WHERE created_at > NOW() - INTERVAL '7 days'"
        ) or 0

        # Convergence summary
        try:
            convergence_rows = await fetch(
                "SELECT confidence_level, COUNT(*) as cnt FROM convergence_scores GROUP BY confidence_level"
            )
            convergence_summary = {r["confidence_level"]: r["cnt"] for r in convergence_rows}
        except Exception:
            convergence_summary = {}

        # Hypothesis status distribution
        try:
            hyp_status = await fetch(
                "SELECT status, COUNT(*) as cnt FROM hypotheses WHERE status IS NOT NULL GROUP BY status ORDER BY cnt DESC"
            )
        except Exception:
            hyp_status = []

        # Top sources by journal
        top_journals = await fetch(
            "SELECT journal, COUNT(*) as cnt FROM sources WHERE journal IS NOT NULL "
            "GROUP BY journal ORDER BY cnt DESC LIMIT 10"
        )

        # Dataset tier distribution
        try:
            dataset_tiers = await fetch(
                "SELECT evidence_tier, COUNT(*) as cnt FROM datasets "
                "WHERE evidence_tier IS NOT NULL GROUP BY evidence_tier ORDER BY evidence_tier"
            )
        except Exception:
            dataset_tiers = []

        return {
            "core": {
                "sources": sources,
                "claims": claims,
                "hypotheses": hypotheses,
                "targets": targets,
                "trials": trials,
            },
            "recent_7d": {
                "new_sources": recent_sources,
                "new_claims": recent_claims,
            },
            "claim_types": [{"type": r["claim_type"], "count": r["cnt"]} for r in claim_types],
            "source_types": [{"type": r["source_type"], "count": r["cnt"]} for r in source_types],
            "convergence": convergence_summary,
            "hypothesis_status": [{"status": r["status"], "count": r["cnt"]} for r in hyp_status],
            "top_journals": [{"journal": r["journal"], "count": r["cnt"]} for r in top_journals],
            "dataset_tiers": [{"tier": r["evidence_tier"], "count": r["cnt"]} for r in dataset_tiers],
        }
    except Exception as e:
        logger.error(f"Failed to build analytics summary: {e}", exc_info=True)
        return {"error": "Failed to load analytics summary"}
