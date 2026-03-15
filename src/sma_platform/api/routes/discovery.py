"""Auto-Discovery Pipeline API — breakthrough signal detection for researchers.

Endpoints:
- GET  /discovery/signals      — list detected breakthrough signals
- GET  /discovery/spikes       — view claim volume spikes per target
- GET  /discovery/novel        — targets with claims but no hypotheses
- POST /discovery/run          — trigger full discovery pipeline (admin)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query

from ...core.database import fetch
from ...reasoning.discovery_agent import (
    detect_claim_spikes,
    detect_novel_targets,
    find_hypothesis_confirmations,
    run_discovery,
)
from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/discovery/signals")
async def list_signals(
    signal_type: str | None = Query(default=None, description="Filter: claim_spike, hypothesis_confirmation, novel_target"),
    min_score: float = Query(default=0.0, ge=0, le=1),
    limit: int = Query(default=50, ge=1, le=500),
):
    """List breakthrough signals detected by the auto-discovery pipeline.

    Signals are ranked by composite_score (novelty × convergence × impact).
    Researchers can filter by type and minimum score threshold.
    """
    wheres = ["status != 'dismissed'"]
    params = []
    idx = 1

    if signal_type:
        wheres.append(f"signal_type = ${idx}")
        params.append(signal_type)
        idx += 1

    if min_score > 0:
        wheres.append(f"composite_score >= ${idx}")
        params.append(min_score)
        idx += 1

    params.append(limit)
    where_clause = " WHERE " + " AND ".join(wheres)

    rows = await fetch(
        f"""SELECT id, signal_type, title, description, target_symbol,
                   composite_score, novelty_score, convergence_score, impact_score,
                   status, created_at
            FROM breakthrough_signals
            {where_clause}
            ORDER BY composite_score DESC
            LIMIT ${idx}""",
        *params,
    )

    return {
        "total": len(rows),
        "signals": [dict(r) for r in rows],
    }


@router.get("/discovery/spikes")
async def get_spikes(
    days_back: int = Query(default=7, ge=1, le=90),
    min_claims: int = Query(default=3, ge=1, le=100),
):
    """View claim volume spikes per target in the last N days.

    A "spike" means a target received significantly more claims than its
    monthly baseline — indicates active research interest or new findings.
    """
    spikes = await detect_claim_spikes(days_back=days_back, min_claims=min_claims)
    return {
        "days_back": days_back,
        "total": len(spikes),
        "spikes": spikes,
    }


@router.get("/discovery/confirmations")
async def get_confirmations(
    days_back: int = Query(default=7, ge=1, le=90),
):
    """Find new claims that confirm existing hypotheses.

    Shows which hypotheses are receiving fresh supporting evidence.
    """
    confirmations = await find_hypothesis_confirmations(days_back=days_back)
    return {
        "days_back": days_back,
        "total": len(confirmations),
        "confirmations": confirmations,
    }


@router.get("/discovery/novel")
async def get_novel_targets(
    days_back: int = Query(default=30, ge=1, le=365),
    min_claims: int = Query(default=3, ge=1, le=100),
):
    """Find targets with claims but no hypotheses — potential discoveries.

    These are targets the platform has evidence for but hasn't formalized
    into testable hypotheses yet. Researchers should review these.
    """
    novel = await detect_novel_targets(days_back=days_back, min_claims=min_claims)
    return {
        "days_back": days_back,
        "total": len(novel),
        "novel_targets": novel,
    }


@router.post("/discovery/run", dependencies=[Depends(require_admin_key)])
async def trigger_discovery(
    days_back: int = Query(default=7, ge=1, le=90),
    persist: bool = Query(default=True),
):
    """Trigger the full auto-discovery pipeline (admin only).

    Detects claim spikes, hypothesis confirmations, and novel targets,
    then scores and stores breakthrough signals.
    """
    result = await run_discovery(days_back=days_back, persist=persist)
    return result
