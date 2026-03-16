"""Convergence scoring and prediction card endpoints."""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse

from ...core.database import execute, fetch, fetchrow
from ..auth import require_admin_key

router = APIRouter()


# --- Convergence Scores ---

@router.get("/convergence")
async def list_convergence_scores(
    min_score: float = Query(default=0.0, ge=0, le=1),
    limit: int = Query(default=50, ge=1, le=200),
):
    """List convergence scores for all scored targets."""
    rows = await fetch(
        """SELECT * FROM convergence_scores
           WHERE composite_score >= $1
           ORDER BY composite_score DESC
           LIMIT $2""",
        min_score, limit,
    )
    return [dict(r) for r in rows]


@router.get("/convergence/{target_id}")
async def get_convergence_score(target_id: UUID):
    """Get convergence score breakdown for a specific target."""
    row = await fetchrow(
        "SELECT * FROM convergence_scores WHERE target_id = $1",
        target_id,
    )
    if not row:
        raise HTTPException(404, "No convergence score for this target")
    return dict(row)


@router.post("/convergence/compute", dependencies=[Depends(require_admin_key)])
async def compute_convergence():
    """Trigger batch convergence score computation for all targets."""
    from ...reasoning.convergence_engine import compute_all_convergence
    result = await compute_all_convergence()
    return result


# --- Prediction Cards ---

@router.get("/predictions")
async def list_predictions(
    target: str | None = None,
    status: str | None = None,
    min_score: float = Query(default=0.0, ge=0, le=1),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List prediction cards with optional filters."""
    wheres = ["convergence_score >= $1"]
    params: list = [min_score]
    idx = 2

    if target:
        wheres.append(f"LOWER(target_label) = ${idx}")
        params.append(target.lower())
        idx += 1
    if status:
        wheres.append(f"status = ${idx}")
        params.append(status)
        idx += 1

    where_clause = " WHERE " + " AND ".join(wheres)

    params.append(limit)
    limit_idx = idx
    idx += 1
    params.append(offset)
    offset_idx = idx

    rows = await fetch(
        f"SELECT * FROM prediction_cards{where_clause} ORDER BY convergence_score DESC LIMIT ${limit_idx} OFFSET ${offset_idx}",
        *params,
    )
    return [dict(r) for r in rows]


@router.get("/predictions/{prediction_id}")
async def get_prediction(prediction_id: UUID):
    """Get a single prediction card with full detail."""
    row = await fetchrow(
        "SELECT * FROM prediction_cards WHERE id = $1",
        prediction_id,
    )
    if not row:
        raise HTTPException(404, "Prediction not found")
    return dict(row)


@router.get("/predictions/{prediction_id}/export")
async def export_prediction(prediction_id: UUID, format: str = "markdown"):
    """Export prediction card as Markdown (for grant applications)."""
    row = await fetchrow(
        "SELECT * FROM prediction_cards WHERE id = $1",
        prediction_id,
    )
    if not row:
        raise HTTPException(404, "Prediction not found")

    card = dict(row)

    if format != "markdown":
        raise HTTPException(400, "Only 'markdown' format supported")

    breakdown = card.get("convergence_breakdown") or {}
    if isinstance(breakdown, str):
        breakdown = json.loads(breakdown)

    experiments = card.get("suggested_experiments") or []
    if isinstance(experiments, str):
        experiments = json.loads(experiments)

    gaps = card.get("evidence_gaps") or []

    md_lines = [
        f"# Prediction Card: {card['target_label']}",
        "",
        f"**Status:** {card['status']}  ",
        f"**Convergence Score:** {card['convergence_score']:.3f} ({card['confidence_level'].upper()})  ",
        f"**Generated:** {card['created_at']}  ",
        f"**Weights Version:** {card.get('weights_version', 'v1')}",
        "",
        "---",
        "",
        "## Prediction",
        "",
        f"> {card['prediction_text']}",
        "",
        "## Convergence Score Breakdown",
        "",
        "| Dimension | Score | Weight |",
        "|-----------|-------|--------|",
        f"| Volume | {breakdown.get('volume', 0):.3f} | 0.15 |",
        f"| Lab Independence | {breakdown.get('lab_independence', 0):.3f} | 0.30 |",
        f"| Method Diversity | {breakdown.get('method_diversity', 0):.3f} | 0.20 |",
        f"| Temporal Trend | {breakdown.get('temporal_trend', 0):.3f} | 0.15 |",
        f"| Replication | {breakdown.get('replication', 0):.3f} | 0.20 |",
        "",
    ]

    summary = card.get("evidence_summary") or {}
    if isinstance(summary, str):
        summary = json.loads(summary)

    if summary:
        md_lines.extend(["## Evidence Summary", ""])
        for category in ["supporting", "contradicting", "neutral"]:
            items = summary.get(category, [])
            if items:
                md_lines.append(f"### {category.title()} ({len(items)} claims)")
                md_lines.append("")
                for item in items:
                    if isinstance(item, dict):
                        md_lines.append(f"- {item.get('text', str(item))}")
                    else:
                        md_lines.append(f"- {item}")
                md_lines.append("")

    if experiments:
        md_lines.extend(["## Suggested Experiments", ""])
        for i, exp in enumerate(experiments, 1):
            if isinstance(exp, dict):
                md_lines.append(f"### {i}. {exp.get('title', 'Experiment')}")
                if exp.get("protocol"):
                    md_lines.append(f"**Protocol:** {exp['protocol']}")
                if exp.get("readout"):
                    md_lines.append(f"**Readout:** {exp['readout']}")
                if exp.get("timeline"):
                    md_lines.append(f"**Timeline:** {exp['timeline']}")
                if exp.get("priority"):
                    md_lines.append(f"**Priority:** {exp['priority']}")
                md_lines.append("")
            else:
                md_lines.append(f"{i}. {exp}")

    if gaps:
        md_lines.extend(["## Evidence Gaps", ""])
        for gap in gaps:
            md_lines.append(f"- {gap}")
        md_lines.append("")

    md_lines.extend([
        "---",
        f"*Generated by SMA Research Platform (sma-research.info) | Weights version: {card.get('weights_version', 'v1')}*",
    ])

    return PlainTextResponse(
        content="\n".join(md_lines),
        media_type="text/markdown",
    )


@router.post("/predictions/generate", dependencies=[Depends(require_admin_key)])
async def generate_predictions():
    """Generate prediction cards from convergence scores >= 0.5."""
    from ...reasoning.prediction_generator import generate_all_predictions
    result = await generate_all_predictions()
    return result


@router.patch("/predictions/{prediction_id}/status", dependencies=[Depends(require_admin_key)])
async def update_prediction_status(prediction_id: UUID, status: str = Query(...)):
    """Update prediction card status."""
    valid = {"draft", "validated", "monitoring", "strengthened", "weakened", "confirmed", "refuted"}
    if status not in valid:
        raise HTTPException(400, f"Invalid status. Must be one of: {valid}")

    row = await fetchrow("SELECT id FROM prediction_cards WHERE id = $1", prediction_id)
    if not row:
        raise HTTPException(404, "Prediction not found")

    await execute(
        "UPDATE prediction_cards SET status = $1, updated_at = NOW() WHERE id = $2",
        status, prediction_id,
    )
    return {"id": str(prediction_id), "status": status}
