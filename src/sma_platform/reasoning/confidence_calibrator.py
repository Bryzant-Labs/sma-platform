"""Confidence Calibration Module.

Back-tests our predictions against known outcomes (approved SMA therapies)
to calibrate confidence scores. Uses the 3 approved SMA drugs as ground truth:

1. Nusinersen (ASO) -> SMN2 (approved)
2. Risdiplam (small molecule) -> SMN2 (approved)
3. Onasemnogene abeparvovec (gene therapy) -> SMN1 (approved)

Calibration metrics:
- precision@k: fraction of top-k predictions that are known positives
- mean reciprocal rank (MRR): average 1/rank of known positives
- rank distribution: where each known positive falls in the ranked list
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from ..core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

# Ground truth: approved SMA drugs and their validated targets.
# These are the "known positives" every scoring system should rank highly.
GROUND_TRUTH = [
    {
        "drug_name": "nusinersen",
        "drug_type": "aso",
        "target_symbol": "smn2",
        "brand_name": "spinraza",
        "approval_year": 2016,
    },
    {
        "drug_name": "risdiplam",
        "drug_type": "small_molecule",
        "target_symbol": "smn2",
        "brand_name": "evrysdi",
        "approval_year": 2020,
    },
    {
        "drug_name": "onasemnogene abeparvovec",
        "drug_type": "gene_therapy",
        "target_symbol": "smn1",
        "brand_name": "zolgensma",
        "approval_year": 2019,
    },
]

# Known target symbols that any SMA scoring system should rank highly
GROUND_TRUTH_TARGETS = {"smn1", "smn2"}


def _precision_at_k(ranked_items: list[str], positives: set[str], k: int) -> float:
    """Compute precision@k: fraction of top-k items that are positives."""
    if k <= 0 or not positives:
        return 0.0
    top_k = ranked_items[:k]
    hits = sum(1 for item in top_k if item in positives)
    return round(hits / min(k, len(ranked_items)), 4) if ranked_items else 0.0


def _mean_reciprocal_rank(ranked_items: list[str], positives: set[str]) -> float:
    """Compute MRR: average of 1/rank for each positive found in the list."""
    if not ranked_items or not positives:
        return 0.0
    reciprocal_ranks = []
    for positive in positives:
        try:
            rank = ranked_items.index(positive) + 1  # 1-indexed
            reciprocal_ranks.append(1.0 / rank)
        except ValueError:
            reciprocal_ranks.append(0.0)  # not found
    return round(sum(reciprocal_ranks) / len(reciprocal_ranks), 4) if reciprocal_ranks else 0.0


def _rank_of(ranked_items: list[str], item: str) -> int | None:
    """Find 1-indexed rank of item in list, or None if absent."""
    try:
        return ranked_items.index(item) + 1
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Synergy / Drug-Target Prediction Calibration
# ---------------------------------------------------------------------------

async def calibrate_predictions() -> dict[str, Any]:
    """Calibrate synergy predictions against known approved drug-target pairs.

    Fetches all synergy predictions (from synergy_predictor logic), ranks them,
    and checks where the 3 approved drugs land for their known targets.

    Returns calibration metrics including precision@k and rank of each known positive.
    """
    from .synergy_predictor import predict_drug_target_synergy

    # Get a large set of predictions to evaluate ranking
    predictions = await predict_drug_target_synergy(limit=500)
    total_predictions = len(predictions)

    if total_predictions == 0:
        return {
            "status": "no_data",
            "message": "No synergy predictions available. Run synergy prediction first.",
            "total_predictions": 0,
            "ground_truth_count": len(GROUND_TRUTH),
            "metrics": {},
        }

    # Build ranked list of (drug_name, target_symbol) by synergy_score
    ranked_pairs = [
        (p["drug_name"].lower(), p["target_symbol"].lower())
        for p in predictions
    ]

    # Evaluate each ground truth drug-target pair
    ground_truth_results = []
    positive_pair_keys = []

    for gt in GROUND_TRUTH:
        drug = gt["drug_name"].lower()
        target = gt["target_symbol"].lower()
        pair = (drug, target)
        pair_key = f"{drug}|{target}"
        positive_pair_keys.append(pair_key)

        rank = None
        synergy_score = None
        for i, rp in enumerate(ranked_pairs):
            if rp == pair:
                rank = i + 1
                synergy_score = predictions[i]["synergy_score"]
                break

        ground_truth_results.append({
            "drug_name": gt["drug_name"],
            "drug_type": gt["drug_type"],
            "target_symbol": gt["target_symbol"],
            "brand_name": gt["brand_name"],
            "approval_year": gt["approval_year"],
            "rank": rank,
            "total_ranked": total_predictions,
            "percentile": round((1 - rank / total_predictions) * 100, 1) if rank else None,
            "synergy_score": synergy_score,
            "found_in_predictions": rank is not None,
        })

    # Compute aggregate metrics
    ranked_pair_keys = [f"{d}|{t}" for d, t in ranked_pairs]
    positive_set = set(positive_pair_keys)

    metrics = {
        "precision_at_5": _precision_at_k(ranked_pair_keys, positive_set, 5),
        "precision_at_10": _precision_at_k(ranked_pair_keys, positive_set, 10),
        "precision_at_20": _precision_at_k(ranked_pair_keys, positive_set, 20),
        "mean_reciprocal_rank": _mean_reciprocal_rank(ranked_pair_keys, positive_set),
        "known_positives_found": sum(1 for r in ground_truth_results if r["found_in_predictions"]),
        "known_positives_total": len(GROUND_TRUTH),
        "known_positives_in_top_10": sum(
            1 for r in ground_truth_results if r["rank"] is not None and r["rank"] <= 10
        ),
    }

    # Interpretation
    if metrics["mean_reciprocal_rank"] >= 0.5:
        interpretation = "GOOD: Known approved drugs rank in the top positions."
    elif metrics["mean_reciprocal_rank"] >= 0.1:
        interpretation = "MODERATE: Known approved drugs are present but not top-ranked. Consider adjusting scoring weights."
    elif metrics["known_positives_found"] > 0:
        interpretation = "WEAK: Known approved drugs rank low. Scoring model needs recalibration."
    else:
        interpretation = "NO OVERLAP: Approved drugs not found in predictions. Check if drug/target data is loaded."

    return {
        "status": "completed",
        "total_predictions": total_predictions,
        "ground_truth": ground_truth_results,
        "metrics": metrics,
        "interpretation": interpretation,
        "calibrated_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Hypothesis Calibration
# ---------------------------------------------------------------------------

async def calibrate_hypotheses() -> dict[str, Any]:
    """Calibrate hypothesis confidence scores against known SMA biology.

    Checks if hypotheses about SMN1/SMN2 targets have the highest confidence,
    since these are the validated therapeutic targets for SMA.

    Returns rank distribution of SMN1/SMN2 hypotheses among all hypotheses.
    """
    # Fetch all hypotheses ordered by confidence
    try:
        all_hypotheses = await fetch(
            """SELECT id, title, confidence, status, metadata
               FROM hypotheses
               ORDER BY confidence DESC"""
        )
    except Exception as e:
        logger.error("Failed to fetch hypotheses: %s", e)
        return {
            "status": "error",
            "message": f"Failed to fetch hypotheses: {e}",
            "metrics": {},
        }

    total_hypotheses = len(all_hypotheses)
    if total_hypotheses == 0:
        return {
            "status": "no_data",
            "message": "No hypotheses found. Run hypothesis generation first.",
            "total_hypotheses": 0,
            "metrics": {},
        }

    # Identify hypotheses linked to SMN1/SMN2 via metadata.target_symbol
    smn_hypotheses = []
    other_hypotheses = []

    for i, row in enumerate(all_hypotheses):
        h = dict(row)
        rank = i + 1
        metadata = h.get("metadata") or "{}"
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}

        target_symbol = (metadata.get("target_symbol") or "").lower()
        title_lower = (h.get("title") or "").lower()

        # Check if hypothesis is about SMN1 or SMN2
        is_smn = target_symbol in GROUND_TRUTH_TARGETS or any(
            t in title_lower for t in GROUND_TRUTH_TARGETS
        )

        entry = {
            "id": str(h["id"]),
            "title": h.get("title", ""),
            "confidence": float(h.get("confidence") or 0),
            "status": h.get("status", ""),
            "target_symbol": target_symbol or "(unknown)",
            "rank": rank,
            "total_ranked": total_hypotheses,
            "percentile": round((1 - rank / total_hypotheses) * 100, 1),
        }

        if is_smn:
            smn_hypotheses.append(entry)
        else:
            other_hypotheses.append(entry)

    # Compute metrics
    smn_confidences = [h["confidence"] for h in smn_hypotheses]
    other_confidences = [h["confidence"] for h in other_hypotheses]

    avg_smn_confidence = round(sum(smn_confidences) / len(smn_confidences), 4) if smn_confidences else 0.0
    avg_other_confidence = round(sum(other_confidences) / len(other_confidences), 4) if other_confidences else 0.0

    # Check if SMN hypotheses rank in top 10
    smn_in_top_10 = sum(1 for h in smn_hypotheses if h["rank"] <= 10)
    smn_in_top_25_pct = sum(
        1 for h in smn_hypotheses
        if h["rank"] <= max(1, total_hypotheses // 4)
    )

    # Rank the target symbols by their best (lowest) rank
    best_smn_rank = min((h["rank"] for h in smn_hypotheses), default=None)

    metrics = {
        "smn_hypothesis_count": len(smn_hypotheses),
        "other_hypothesis_count": len(other_hypotheses),
        "avg_smn_confidence": avg_smn_confidence,
        "avg_other_confidence": avg_other_confidence,
        "confidence_gap": round(avg_smn_confidence - avg_other_confidence, 4),
        "best_smn_rank": best_smn_rank,
        "smn_in_top_10": smn_in_top_10,
        "smn_in_top_25_pct": smn_in_top_25_pct,
    }

    # Interpretation
    if avg_smn_confidence > avg_other_confidence and best_smn_rank and best_smn_rank <= 5:
        interpretation = "GOOD: SMN1/SMN2 hypotheses have higher confidence and rank at the top."
    elif avg_smn_confidence >= avg_other_confidence:
        interpretation = "MODERATE: SMN1/SMN2 confidence is at or above average, but not clearly top-ranked."
    elif smn_hypotheses:
        interpretation = "WEAK: SMN1/SMN2 hypotheses exist but have below-average confidence. Model may need recalibration."
    else:
        interpretation = "NO SMN HYPOTHESES: No hypotheses found for SMN1/SMN2. Check hypothesis generation pipeline."

    return {
        "status": "completed",
        "total_hypotheses": total_hypotheses,
        "smn_hypotheses": smn_hypotheses[:20],  # Cap output for readability
        "metrics": metrics,
        "interpretation": interpretation,
        "calibrated_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Claim Confidence Calibration Curves
# ---------------------------------------------------------------------------

# Bin edges for confidence buckets
_BIN_EDGES = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
_BIN_LABELS = ["0.0–0.2", "0.2–0.4", "0.4–0.6", "0.6–0.8", "0.8–1.0"]


def _brier_score(confidences: list[float], outcomes: list[int]) -> float:
    """Compute Brier score: mean squared error between confidence and outcome.

    Lower is better. 0 = perfect calibration, 0.25 = random baseline for binary.
    outcome = 1 if claim is replicated (2+ independent sources), 0 otherwise.
    """
    if not confidences:
        return 0.0
    n = len(confidences)
    return round(sum((c - o) ** 2 for c, o in zip(confidences, outcomes)) / n, 6)


async def generate_calibration_curves() -> dict[str, Any]:
    """Generate calibration curve data — predicted confidence vs actual replication rate.

    For each confidence bin, computes:
    - mean_confidence: average confidence score in this bin
    - replication_rate: fraction of claims with 2+ independent sources
    - claim_type_consistency: fraction where multiple sources assert the same claim_type
    - claim_count: number of claims in this bin

    Also computes a Brier score (overall calibration quality metric) and
    recalibration suggestions for bins where confidence diverges from replication.
    """
    # 1) Fetch all claims with their confidence and source counts
    try:
        rows = await fetch(
            """SELECT c.id, c.confidence, c.claim_type,
                      COUNT(DISTINCT e.source_id) AS source_count
               FROM claims c
               LEFT JOIN evidence e ON e.claim_id = c.id
               GROUP BY c.id, c.confidence, c.claim_type
               ORDER BY c.confidence"""
        )
    except Exception as e:
        logger.error("Failed to fetch claims for calibration curves: %s", e)
        return {
            "status": "error",
            "message": f"Failed to fetch claims: {e}",
            "bins": [],
            "brier_score": None,
        }

    total_claims = len(rows)
    if total_claims == 0:
        return {
            "status": "no_data",
            "message": "No claims found. Run ingestion first.",
            "total_claims": 0,
            "bins": [],
            "brier_score": None,
        }

    # 2) For claims with 2+ sources, check claim_type consistency across sources.
    #    We need a separate query for multi-source claims to check if different
    #    sources corroborate the same claim type.
    multi_source_claim_ids = [
        str(r["id"]) for r in rows if int(r["source_count"] or 0) >= 2
    ]

    claim_type_consistent: set[str] = set()
    if multi_source_claim_ids:
        # For each multi-source claim, check if there are other claims with
        # the same subject+predicate+claim_type from different sources.
        # This measures whether independent sources assert the same kind of claim.
        try:
            consistency_rows = await fetch(
                """SELECT c1.id AS claim_id,
                          COUNT(DISTINCT c2.id) AS matching_claims
                   FROM claims c1
                   JOIN evidence e1 ON e1.claim_id = c1.id
                   JOIN claims c2 ON c2.claim_type = c1.claim_type
                                  AND c2.subject_id = c1.subject_id
                                  AND c2.predicate = c1.predicate
                                  AND c2.id != c1.id
                   JOIN evidence e2 ON e2.claim_id = c2.id
                                    AND e2.source_id != e1.source_id
                   WHERE c1.id IN (
                       SELECT c.id FROM claims c
                       JOIN evidence e ON e.claim_id = c.id
                       GROUP BY c.id
                       HAVING COUNT(DISTINCT e.source_id) >= 2
                   )
                   GROUP BY c1.id
                   HAVING COUNT(DISTINCT c2.id) >= 1"""
            )
            claim_type_consistent = {str(r["claim_id"]) for r in consistency_rows}
        except Exception as e:
            # Non-fatal: consistency check is supplementary
            logger.warning("Claim type consistency check failed: %s", e)

    # 3) Bin claims by confidence
    bins: list[dict[str, Any]] = []
    all_confidences: list[float] = []
    all_outcomes: list[int] = []

    for i, (lo, hi) in enumerate(_BIN_EDGES):
        bin_claims = [
            r for r in rows
            if lo <= float(r["confidence"] or 0) < hi
            or (hi == 1.0 and float(r["confidence"] or 0) == 1.0 and lo == 0.8)
        ]

        if not bin_claims:
            bins.append({
                "bin": _BIN_LABELS[i],
                "range": [lo, hi],
                "claim_count": 0,
                "mean_confidence": round((lo + hi) / 2, 2),
                "replication_rate": None,
                "claim_type_consistency_rate": None,
                "predicted_vs_actual_gap": None,
            })
            continue

        confidences = [float(r["confidence"] or 0) for r in bin_claims]
        mean_conf = sum(confidences) / len(confidences)

        # Replication: fraction with 2+ independent sources
        replicated = sum(1 for r in bin_claims if int(r["source_count"] or 0) >= 2)
        replication_rate = replicated / len(bin_claims)

        # Claim type consistency: among multi-source claims in this bin,
        # how many have matching claim types across independent sources?
        multi_in_bin = [r for r in bin_claims if int(r["source_count"] or 0) >= 2]
        if multi_in_bin:
            consistent_count = sum(
                1 for r in multi_in_bin if str(r["id"]) in claim_type_consistent
            )
            consistency_rate = consistent_count / len(multi_in_bin)
        else:
            consistency_rate = None

        gap = round(mean_conf - replication_rate, 4)

        bins.append({
            "bin": _BIN_LABELS[i],
            "range": [lo, hi],
            "claim_count": len(bin_claims),
            "mean_confidence": round(mean_conf, 4),
            "replication_rate": round(replication_rate, 4),
            "claim_type_consistency_rate": round(consistency_rate, 4) if consistency_rate is not None else None,
            "predicted_vs_actual_gap": gap,
        })

        # Accumulate for Brier score
        for r in bin_claims:
            conf = float(r["confidence"] or 0)
            outcome = 1 if int(r["source_count"] or 0) >= 2 else 0
            all_confidences.append(conf)
            all_outcomes.append(outcome)

    # 4) Brier score
    brier = _brier_score(all_confidences, all_outcomes)

    # 5) Build plot data (predicted vs actual)
    plot_data = {
        "x_predicted": [b["mean_confidence"] for b in bins if b["claim_count"] > 0],
        "y_actual": [b["replication_rate"] for b in bins if b["claim_count"] > 0],
        "perfect_calibration": [b["mean_confidence"] for b in bins if b["claim_count"] > 0],
        "bin_sizes": [b["claim_count"] for b in bins if b["claim_count"] > 0],
    }

    # 6) Recalibration suggestions
    suggestions: list[dict[str, Any]] = []
    for b in bins:
        if b["claim_count"] == 0 or b["replication_rate"] is None:
            continue
        gap = b["predicted_vs_actual_gap"]
        if gap is not None and abs(gap) > 0.15:
            if gap > 0:
                direction = "overconfident"
                action = (
                    f"Claims in the {b['bin']} range have confidence ~{b['mean_confidence']:.0%} "
                    f"but only {b['replication_rate']:.0%} are replicated by 2+ sources. "
                    f"Consider reducing confidence or requiring stronger evidence for this range."
                )
            else:
                direction = "underconfident"
                action = (
                    f"Claims in the {b['bin']} range have confidence ~{b['mean_confidence']:.0%} "
                    f"but {b['replication_rate']:.0%} are replicated. "
                    f"These claims may deserve higher confidence scores."
                )
            suggestions.append({
                "bin": b["bin"],
                "direction": direction,
                "gap": gap,
                "suggestion": action,
            })

    # 7) Interpretation
    if brier <= 0.1:
        calibration_quality = "EXCELLENT"
        interpretation = "Confidence scores are well-calibrated against replication evidence."
    elif brier <= 0.2:
        calibration_quality = "GOOD"
        interpretation = "Confidence scores are reasonably calibrated. Minor adjustments may help."
    elif brier <= 0.3:
        calibration_quality = "MODERATE"
        interpretation = "Confidence scores show meaningful miscalibration. Review suggestions below."
    else:
        calibration_quality = "POOR"
        interpretation = "Confidence scores are poorly calibrated against replication evidence. Significant recalibration needed."

    return {
        "status": "completed",
        "total_claims": total_claims,
        "bins": bins,
        "brier_score": brier,
        "calibration_quality": calibration_quality,
        "interpretation": interpretation,
        "plot_data": plot_data,
        "recalibration_suggestions": suggestions,
        "methodology": {
            "replication_threshold": "2+ independent sources per claim",
            "brier_score_range": "0 (perfect) to 1 (worst); <0.1 excellent, <0.2 good",
            "bin_count": len(_BIN_EDGES),
            "claim_type_consistency": "Fraction of multi-source claims where independent sources assert the same claim type",
        },
        "calibrated_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Combined Calibration Report
# ---------------------------------------------------------------------------

async def get_calibration_report() -> dict[str, Any]:
    """Generate a combined calibration report for predictions, hypotheses, and claim curves.

    This is the primary entry point for evaluating how well our scoring models
    align with known biology (approved SMA drugs) and how well confidence scores
    predict actual replication rates.
    """
    prediction_cal = await calibrate_predictions()
    hypothesis_cal = await calibrate_hypotheses()
    curves_cal = await generate_calibration_curves()

    # Overall health score: weighted average of key indicators
    scores = []

    # Prediction MRR (0-1)
    pred_mrr = prediction_cal.get("metrics", {}).get("mean_reciprocal_rank", 0)
    scores.append(pred_mrr)

    # Hypothesis confidence gap (positive = good, cap at 1)
    conf_gap = hypothesis_cal.get("metrics", {}).get("confidence_gap", 0)
    scores.append(min(max(conf_gap, 0), 1.0))

    # Known positives found ratio
    pred_metrics = prediction_cal.get("metrics", {})
    found = pred_metrics.get("known_positives_found", 0)
    total = pred_metrics.get("known_positives_total", 1)
    scores.append(found / total if total > 0 else 0)

    # Calibration quality: 1 - brier_score (inverted so higher = better)
    brier = curves_cal.get("brier_score")
    if brier is not None:
        scores.append(max(1.0 - brier, 0.0))

    overall_score = round(sum(scores) / len(scores), 4) if scores else 0.0

    if overall_score >= 0.6:
        overall_grade = "A"
        overall_message = "Scoring models align well with known SMA biology."
    elif overall_score >= 0.4:
        overall_grade = "B"
        overall_message = "Scoring models partially capture known biology. Room for improvement."
    elif overall_score >= 0.2:
        overall_grade = "C"
        overall_message = "Scoring models weakly capture known biology. Recalibration recommended."
    else:
        overall_grade = "D"
        overall_message = "Scoring models do not reflect known SMA biology. Check data completeness and scoring weights."

    return {
        "overall_score": overall_score,
        "overall_grade": overall_grade,
        "overall_message": overall_message,
        "ground_truth_drugs": GROUND_TRUTH,
        "prediction_calibration": prediction_cal,
        "hypothesis_calibration": hypothesis_cal,
        "claim_calibration_curves": curves_cal,
        "calibrated_at": datetime.now(timezone.utc).isoformat(),
    }
