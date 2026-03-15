"""Hypothesis auto-generation endpoints — Agent D convergence analysis."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query

from ...reasoning.convergence_hypothesis import (
    find_convergence_signals,
    run_hypothesis_generation,
)
from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/hypotheses/convergence")
async def get_convergence_signals(
    days_back: int = Query(default=30, ge=1, le=365, description="Look back this many days"),
    min_claims: int = Query(default=3, ge=2, le=50, description="Minimum claims for a convergence signal"),
):
    """View current convergence signals without generating hypotheses.

    Returns claim clusters where multiple independent sources converge on
    the same molecular target — candidates for hypothesis generation.
    """
    signals = await find_convergence_signals(
        days_back=days_back,
        min_claims=min_claims,
    )

    # Strip full claim lists for the overview response (keep it lightweight)
    summary = []
    for s in signals:
        summary.append({
            "target_key": s["target_key"],
            "target_label": s["target_label"],
            "subject_type": s["subject_type"],
            "claim_count": s["claim_count"],
            "source_count": s["source_count"],
            "claim_types": s["claim_types"],
        })

    return {
        "signals": summary,
        "total": len(summary),
        "params": {"days_back": days_back, "min_claims": min_claims},
    }


@router.post(
    "/hypotheses/generate",
    dependencies=[Depends(require_admin_key)],
)
async def trigger_generation(
    days_back: int = Query(default=7, ge=1, le=365, description="Look back this many days for new claims"),
    min_claims: int = Query(default=3, ge=2, le=50, description="Minimum claims for a convergence signal"),
    dry_run: bool = Query(default=False, description="If true, find and synthesize but do not persist"),
):
    """Trigger hypothesis generation from new evidence convergence.

    Scans claims from the last *days_back* days, identifies convergence
    signals, synthesizes hypotheses via Claude Haiku, and stores results
    in the hypotheses table + blackboard.

    Requires X-Admin-Key header.
    """
    result = await run_hypothesis_generation(
        days_back=days_back,
        min_claims=min_claims,
        dry_run=dry_run,
    )

    logger.info(
        "Hypothesis generation complete: %d signals, %d generated, %d skipped (dry_run=%s)",
        result["signals_found"],
        result["hypotheses_generated"],
        result["hypotheses_skipped"],
        result["dry_run"],
    )

    return result
