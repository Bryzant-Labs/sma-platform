"""Evidence Convergence Engine API routes — Differentiator #2.

Dedicated endpoints for convergence score browsing and on-demand
computation. Complements the existing /predictions routes by providing
a target-centric view of the 5-dimension scoring breakdown.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from ...core.database import fetch, fetchrow
from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/convergence", tags=["convergence"])


@router.get("/scores")
async def get_convergence_scores(
    min_score: float = Query(default=0.0, ge=0, le=1),
    confidence: str | None = Query(default=None, description="Filter by confidence level"),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Get evidence convergence scores for all SMA targets.

    Scores based on 5 dimensions: claim volume, lab independence,
    method diversity, temporal trend, and replication.
    Weights version v1.
    """
    wheres = ["composite_score >= $1"]
    params: list = [min_score]
    idx = 2

    if confidence:
        valid_levels = {"low", "medium", "high", "very_high"}
        if confidence not in valid_levels:
            raise HTTPException(400, f"Invalid confidence level. Must be one of: {valid_levels}")
        wheres.append(f"confidence_level = ${idx}")
        params.append(confidence)
        idx += 1

    params.append(limit)

    rows = await fetch(
        f"""SELECT target_key, target_label, target_type, target_id,
                   volume, lab_independence, method_diversity,
                   temporal_trend, replication, composite_score,
                   confidence_level, claim_count, source_count,
                   computed_at, weights_version
            FROM convergence_scores
            WHERE {' AND '.join(wheres)}
            ORDER BY composite_score DESC
            LIMIT ${idx}""",
        *params,
    )

    targets = []
    for r in rows:
        d = dict(r)
        # Ensure numeric fields are floats for JSON
        for key in ("volume", "lab_independence", "method_diversity",
                     "temporal_trend", "replication", "composite_score"):
            if d.get(key) is not None:
                d[key] = float(d[key])
        targets.append(d)

    return {
        "targets": targets,
        "total": len(targets),
        "weights_version": "v1",
    }


@router.get("/scores/{symbol}")
async def get_target_convergence(symbol: str):
    """Get detailed convergence score for a specific target by symbol."""
    row = await fetchrow(
        """SELECT cs.*, t.symbol, t.name AS target_name, t.description AS target_desc
           FROM convergence_scores cs
           LEFT JOIN targets t ON cs.target_id = t.id
           WHERE LOWER(cs.target_label) = $1
           ORDER BY cs.computed_at DESC
           LIMIT 1""",
        symbol.lower(),
    )
    if not row:
        # Try by target_id
        target_row = await fetchrow(
            "SELECT id FROM targets WHERE LOWER(symbol) = $1", symbol.lower()
        )
        if target_row:
            row = await fetchrow(
                "SELECT * FROM convergence_scores WHERE target_id = $1 ORDER BY computed_at DESC LIMIT 1",
                target_row["id"],
            )
    if not row:
        raise HTTPException(404, detail=f"No convergence score found for target {symbol}")

    d = dict(row)
    for key in ("volume", "lab_independence", "method_diversity",
                 "temporal_trend", "replication", "composite_score"):
        if d.get(key) is not None:
            d[key] = float(d[key])

    return d


@router.get("/predictions")
async def get_convergence_predictions(
    min_score: float = Query(default=0.0, ge=0, le=1),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Get prediction cards enriched with convergence breakdown.

    Each prediction includes: convergence score, confidence level,
    evidence breakdown, claim type distribution, and suggested experiments.
    """
    rows = await fetch(
        """SELECT pc.id, pc.target_label, pc.prediction_text,
                  pc.convergence_score, pc.convergence_breakdown,
                  pc.confidence_level, pc.status,
                  pc.suggested_experiments, pc.evidence_gaps,
                  cs.claim_count, cs.source_count,
                  cs.volume, cs.lab_independence, cs.method_diversity,
                  cs.temporal_trend, cs.replication
           FROM prediction_cards pc
           LEFT JOIN convergence_scores cs ON pc.convergence_score_id = cs.id
           WHERE pc.convergence_score >= $1
           ORDER BY pc.convergence_score DESC
           LIMIT $2""",
        min_score, limit,
    )

    predictions = []
    for r in rows:
        d = dict(r)
        for key in ("volume", "lab_independence", "method_diversity",
                     "temporal_trend", "replication", "convergence_score"):
            if d.get(key) is not None:
                d[key] = float(d[key])
        predictions.append(d)

    return {
        "predictions": predictions,
        "total": len(predictions),
    }


@router.get("/predictions/{symbol}")
async def get_target_prediction(symbol: str):
    """Get prediction card for a specific target by symbol."""
    row = await fetchrow(
        """SELECT pc.*, cs.volume, cs.lab_independence, cs.method_diversity,
                  cs.temporal_trend, cs.replication, cs.claim_count, cs.source_count
           FROM prediction_cards pc
           LEFT JOIN convergence_scores cs ON pc.convergence_score_id = cs.id
           WHERE LOWER(pc.target_label) = $1
           ORDER BY pc.convergence_score DESC
           LIMIT 1""",
        symbol.lower(),
    )
    if not row:
        raise HTTPException(404, detail=f"No prediction found for target {symbol}")

    d = dict(row)
    for key in ("volume", "lab_independence", "method_diversity",
                 "temporal_trend", "replication", "convergence_score"):
        if d.get(key) is not None:
            d[key] = float(d[key])
    return d


@router.post("/compute", dependencies=[Depends(require_admin_key)])
async def compute_convergence():
    """Trigger batch convergence score computation for all targets.

    Requires admin API key. Upserts into convergence_scores table.
    """
    from ...reasoning.convergence_engine import compute_all_convergence
    result = await compute_all_convergence()
    return result
