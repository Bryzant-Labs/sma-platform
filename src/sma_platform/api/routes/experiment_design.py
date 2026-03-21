"""Experiment Design & Dead-End Predictor API routes.

Endpoints:
- GET /experiment/suggest/{target_symbol}       — gap analysis + assay suggestions
- GET /experiment/gaps                          — all targets with evidence gaps
- GET /experiments/propose/{hypothesis_id}      — propose experiment for one hypothesis
- GET /experiments/propose/batch                — batch propose for a tier
- GET /dead-ends/patterns                       — known failure patterns
- GET /dead-ends/risks                          — risk for all active hypotheses
- GET /dead-ends/hypothesis/{id}                — single hypothesis risk assessment
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from ...reasoning.dead_end_predictor import (
    all_risks,
    assess_risk,
    get_failure_patterns,
)
from ...reasoning.experiment_designer import (
    all_evidence_gaps,
    suggest_experiments,
)
from ...reasoning.experiment_proposer import (
    batch_propose,
    propose_experiment,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Experiment Design Suggestions
# ---------------------------------------------------------------------------

@router.get("/experiment/suggest/{target_symbol}")
async def experiment_suggestions(target_symbol: str):
    """Analyze evidence gaps for a target and suggest experiments to fill them.

    Returns present evidence types, missing types, and prioritized
    assay recommendations ranked by gap_size * target_importance * cost_efficiency.
    """
    result = await suggest_experiments(target_symbol)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/experiment/gaps")
async def evidence_gaps(
    limit: int = Query(default=50, ge=1, le=500, description="Max targets to return"),
):
    """All targets with evidence gaps, sorted by priority.

    Shows which targets have the biggest gaps in evidence coverage
    and what experiments would be most valuable to fill those gaps.
    """
    results = await all_evidence_gaps()
    total = len(results)
    return {
        "total": total,
        "showing": min(limit, total),
        "targets": results[:limit],
    }


# ---------------------------------------------------------------------------
# Hypothesis-to-Experiment Proposer
# ---------------------------------------------------------------------------

@router.get("/experiments/propose/batch")
async def propose_batch(
    tier: str = Query(default="A", description="Hypothesis tier: A, B, C, or all"),
):
    """Batch-generate experimental proposals for all hypotheses in a tier.

    Converts prioritized hypotheses into concrete experimental proposals
    with assays, model systems, readouts, go/no-go criteria, timelines,
    reagents, and relevant literature.

    Tier A = top 5 high-conviction, Tier B = 6-15, Tier C = rest.
    """
    result = await batch_propose(tier=tier)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/experiments/propose/{hypothesis_id}")
async def propose_for_hypothesis(hypothesis_id: str):
    """Generate a concrete experimental proposal for a single hypothesis.

    Analyzes the hypothesis type (binding, expression, drug efficacy,
    splicing) and returns a structured proposal including:
    - Suggested assay (SPR, Western, qRT-PCR, iPSC-MN, mouse model)
    - Model system (cell line, organoid, animal model)
    - Primary readout (binding Kd, expression fold-change, survival)
    - Go/no-go threshold
    - Estimated timeline and cost
    - Required reagents/antibodies
    - Relevant prior experiments in the literature
    - Step-by-step escalation path
    """
    result = await propose_experiment(hypothesis_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ---------------------------------------------------------------------------
# Dead-End Predictor
# ---------------------------------------------------------------------------

@router.get("/dead-ends/patterns")
async def dead_end_patterns():
    """Known drug failure patterns extracted from drug_outcomes data.

    Shows which targets and mechanisms are most associated with
    drug failure — useful for avoiding known dead ends.
    """
    patterns = await get_failure_patterns()
    return {
        "total": len(patterns),
        "patterns": patterns,
    }


@router.get("/dead-ends/risks")
async def dead_end_risks(
    limit: int = Query(default=50, ge=1, le=500, description="Max hypotheses to return"),
    min_risk: float = Query(default=0.0, ge=0.0, le=1.0, description="Minimum risk score filter"),
):
    """Risk assessment for all active hypotheses based on failure patterns.

    Hypotheses are scored by overlap with known drug failure profiles.
    Higher risk_score = more overlap with historical failures.
    """
    results = await all_risks()
    if min_risk > 0:
        results = [r for r in results if r.get("risk_score", 0) >= min_risk]
    total = len(results)
    return {
        "total": total,
        "showing": min(limit, total),
        "hypotheses": results[:limit],
    }


@router.get("/dead-ends/hypothesis/{hypothesis_id}")
async def dead_end_hypothesis_risk(hypothesis_id: str):
    """Risk assessment for a single hypothesis.

    Returns risk_score (0-1), risk_level, and detailed risk_factors
    explaining why this hypothesis may be heading toward a dead end.
    """
    result = await assess_risk(hypothesis_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result
