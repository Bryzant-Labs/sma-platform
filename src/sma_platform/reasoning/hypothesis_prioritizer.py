"""Phase 2 hypothesis prioritization — rank 63 hypotheses into action tiers.

Scores each hypothesis across 5 dimensions (all 0.0-1.0):

1. evidence_depth      — claim count and average confidence backing this hypothesis
2. source_convergence  — independent sources supporting the claims
3. therapeutic_clarity — does the hypothesis have a clear modality suggestion?
4. target_strength     — composite score of the parent target
5. novelty             — is this a known pathway or a novel angle?

Output: ranked list with tier labels (Tier A: top 5, Tier B: 6-15, Tier C: rest).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ..core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

# Weights for hypothesis composite score (sum = 1.0)
HYP_WEIGHTS: dict[str, float] = {
    "evidence_depth": 0.25,
    "source_convergence": 0.20,
    "therapeutic_clarity": 0.20,
    "target_strength": 0.20,
    "novelty": 0.15,
}

# Modalities with clear therapeutic path score higher
_CLEAR_MODALITIES = {"aso", "small_molecule", "gene_therapy", "crispr", "antibody", "combination"}

# Claim types that indicate novel/emerging research angles
_NOVEL_TYPES = {"neuroprotection", "biomarker", "pathway_membership", "protein_interaction"}


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


async def score_hypothesis(hyp: dict, target_scores: dict[str, float], max_claims: int, max_sources: int) -> dict[str, Any]:
    """Score a single hypothesis across all 5 dimensions."""
    hyp_id = str(hyp["id"])

    try:
        meta = json.loads(hyp.get("metadata") or "{}")
    except (json.JSONDecodeError, TypeError):
        meta = {}

    try:
        claim_ids = json.loads(hyp.get("supporting_evidence") or "[]")
    except (json.JSONDecodeError, TypeError):
        claim_ids = []

    target_id = meta.get("target_id", "")
    target_symbol = meta.get("target_symbol", "")
    claim_type = meta.get("claim_type", "other")
    claim_count = meta.get("claim_count", len(claim_ids))
    source_count = meta.get("source_count", 0)
    modality = meta.get("modality_suggestion", "unclear")

    # Dimension 1: Evidence depth — claim count * avg confidence
    hyp_confidence = float(hyp.get("confidence") or 0.5)
    vol_score = _clamp(claim_count / max_claims) if max_claims > 0 else 0.0
    evidence_depth = _clamp((vol_score * 0.5) + (hyp_confidence * 0.5))

    # Dimension 2: Source convergence — independent papers
    source_convergence = _clamp(source_count / max_sources) if max_sources > 0 else 0.0

    # Dimension 3: Therapeutic clarity — clear modality vs "unclear"
    if modality in _CLEAR_MODALITIES:
        therapeutic_clarity = 0.9
    elif modality == "unclear":
        therapeutic_clarity = 0.2
    else:
        therapeutic_clarity = 0.5
    # Boost if claim_type is drug-related
    if claim_type in ("drug_efficacy", "drug_target"):
        therapeutic_clarity = _clamp(therapeutic_clarity + 0.1)

    # Dimension 4: Target strength — parent target's composite score
    target_strength = target_scores.get(target_id, 0.0)

    # Dimension 5: Novelty — novel claim types score higher (emerging angles)
    if claim_type in _NOVEL_TYPES:
        novelty = 0.8
    elif claim_type in ("drug_efficacy", "drug_target"):
        novelty = 0.4  # Well-trodden path
    elif claim_type == "other":
        novelty = 0.6  # Unknown = potentially novel
    else:
        novelty = 0.5

    dimensions = {
        "evidence_depth": evidence_depth,
        "source_convergence": source_convergence,
        "therapeutic_clarity": therapeutic_clarity,
        "target_strength": target_strength,
        "novelty": novelty,
    }

    composite = _clamp(sum(HYP_WEIGHTS[d] * dimensions[d] for d in HYP_WEIGHTS))

    return {
        "hypothesis_id": hyp_id,
        "title": hyp.get("title", ""),
        "target_symbol": target_symbol,
        "target_id": target_id,
        "claim_type": claim_type,
        "claim_count": claim_count,
        "source_count": source_count,
        "modality": modality,
        "confidence": hyp_confidence,
        "status": hyp.get("status", "proposed"),
        "dimensions": dimensions,
        "composite_score": composite,
        "description": hyp.get("description", ""),
        "key_questions": meta.get("key_questions", []),
    }


async def prioritize_all_hypotheses() -> dict[str, Any]:
    """Score and rank all hypotheses, assign tiers.

    Returns:
        {
            "total": int,
            "tier_a": [...],  # top 5 high-conviction
            "tier_b": [...],  # 6-15 medium
            "tier_c": [...],  # rest
            "all_ranked": [...],
        }
    """
    hypotheses = await fetch(
        "SELECT * FROM hypotheses ORDER BY confidence DESC"
    )

    if not hypotheses:
        return {"total": 0, "tier_a": [], "tier_b": [], "tier_c": [], "all_ranked": []}

    # Pre-compute target scores for lookup
    from .prioritizer import score_all_targets
    target_results = await score_all_targets()
    target_scores = {r["target_id"]: r["composite_score"] for r in target_results}

    # Compute normalization ceilings
    max_claims_row = await fetchrow(
        "SELECT MAX(cnt) AS mx FROM ("
        "  SELECT COUNT(*) AS cnt FROM claims"
        "  WHERE subject_id IS NOT NULL GROUP BY subject_id"
        ")"
    )
    max_claims = int(max_claims_row["mx"]) if max_claims_row and max_claims_row["mx"] else 1

    max_sources_row = await fetchrow(
        "SELECT MAX(cnt) AS mx FROM ("
        "  SELECT COUNT(DISTINCT e.source_id) AS cnt"
        "  FROM claims c JOIN evidence e ON e.claim_id = c.id"
        "  WHERE c.subject_id IS NOT NULL GROUP BY c.subject_id"
        ")"
    )
    max_sources = int(max_sources_row["mx"]) if max_sources_row and max_sources_row["mx"] else 1

    # Score each hypothesis
    scored = []
    for h in hypotheses:
        h = dict(h)
        result = await score_hypothesis(h, target_scores, max_claims, max_sources)
        scored.append(result)

    # Sort by composite score
    scored.sort(key=lambda x: x["composite_score"], reverse=True)

    # Assign tiers
    for i, s in enumerate(scored):
        if i < 5:
            s["tier"] = "A"
        elif i < 15:
            s["tier"] = "B"
        else:
            s["tier"] = "C"
        s["rank"] = i + 1

    tier_a = [s for s in scored if s["tier"] == "A"]
    tier_b = [s for s in scored if s["tier"] == "B"]
    tier_c = [s for s in scored if s["tier"] == "C"]

    logger.info(
        "Prioritized %d hypotheses: Tier A=%d, B=%d, C=%d",
        len(scored), len(tier_a), len(tier_b), len(tier_c),
    )

    return {
        "total": len(scored),
        "tier_a": tier_a,
        "tier_b": tier_b,
        "tier_c": tier_c,
        "all_ranked": scored,
    }
