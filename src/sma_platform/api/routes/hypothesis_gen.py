"""Hypothesis auto-generation endpoints — Agent D convergence analysis."""

from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...core.database import execute
from ...reasoning.convergence_hypothesis import (
    find_convergence_signals,
    run_hypothesis_generation,
)
from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic model for direct hypothesis creation
# ---------------------------------------------------------------------------


class HypothesisCreate(BaseModel):
    """Schema for creating a hypothesis directly (admin only)."""

    hypothesis_type: str = Field(
        default="mechanism",
        description="Type: mechanism, biomarker, therapeutic, target",
    )
    title: str = Field(..., max_length=500, description="Hypothesis statement")
    description: str = Field(..., description="Evidence summary")
    rationale: str = Field(..., description="Mechanistic rationale")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    status: str = Field(default="proposed")
    generated_by: str = Field(default="manual")
    metadata: Optional[dict] = Field(default=None)


# ---------------------------------------------------------------------------
# Direct hypothesis creation endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/hypotheses",
    dependencies=[Depends(require_admin_key)],
)
async def create_hypothesis(body: HypothesisCreate):
    """Create a hypothesis card directly (admin).

    Unlike /hypotheses/generate which uses LLM synthesis from claims,
    this endpoint allows direct insertion of curated hypotheses
    (e.g., from convergence synthesis documents or expert review).
    """
    metadata_json = json.dumps(body.metadata) if body.metadata else "{}"

    try:
        await execute(
            """INSERT INTO hypotheses
                   (hypothesis_type, title, description, rationale,
                    supporting_evidence, confidence, status,
                    generated_by, metadata)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
            body.hypothesis_type,
            body.title[:500],
            body.description,
            body.rationale,
            [],  # supporting_evidence UUID[] -- empty for manual entries
            body.confidence,
            body.status,
            body.generated_by,
            metadata_json,
        )
    except Exception as e:
        logger.error("Failed to create hypothesis: %s", e, exc_info=True)
        raise HTTPException(500, f"Failed to create hypothesis: {e}")

    logger.info("Created hypothesis: %s (confidence: %.2f)", body.title[:80], body.confidence)
    return {
        "status": "created",
        "title": body.title,
        "hypothesis_type": body.hypothesis_type,
        "confidence": body.confidence,
    }


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
