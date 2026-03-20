"""Bayesian Evidence Calibration — M5 Milestone.

Back-tests convergence scores against known drug outcomes to measure
how well the platform's evidence scoring predicts real-world results.

Calibration Logic:
1. Take all drugs with known outcomes (approved, failed, ongoing)
2. Compute their convergence scores from claims
3. Compare: do approved drugs score higher than failed ones?
4. Compute calibration metrics: AUC, Brier score, calibration curve

Ground truth comes from the drug_outcomes table (populated by the
failure_extractor) and the 3 approved SMA drugs (nusinersen, risdiplam,
onasemnogene abeparvovec).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from ..core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

# Outcome categories mapped to binary success labels
SUCCESS_OUTCOMES = {"success", "partial_success"}
FAILURE_OUTCOMES = {"failure", "discontinued"}
ONGOING_OUTCOMES = {"ongoing", "inconclusive"}

# Calibration curve bin edges
_BIN_EDGES = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
_BIN_LABELS = ["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"]


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _spearman_rank_correlation(x: list[float], y: list[float]) -> float:
    """Compute Spearman rank correlation between two lists.

    Uses the formula: rho = 1 - (6 * sum(d^2)) / (n * (n^2 - 1))
    where d = difference between ranks.
    """
    n = len(x)
    if n < 3:
        return 0.0

    # Rank the values (average rank for ties)
    def _rank(vals: list[float]) -> list[float]:
        indexed = sorted(enumerate(vals), key=lambda p: p[1])
        ranks = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j < n - 1 and indexed[j + 1][1] == indexed[j][1]:
                j += 1
            avg_rank = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                ranks[indexed[k][0]] = avg_rank
            i = j + 1
        return ranks

    rx = _rank(x)
    ry = _rank(y)

    d_sq_sum = sum((rx[i] - ry[i]) ** 2 for i in range(n))
    rho = 1.0 - (6.0 * d_sq_sum) / (n * (n * n - 1))
    return round(max(-1.0, min(1.0, rho)), 4)


def _brier_score(predicted: list[float], actual: list[int]) -> float:
    """Compute Brier score: mean squared error between predicted and actual.

    Lower is better. 0 = perfect, 0.25 = random baseline for binary outcomes.
    """
    if not predicted:
        return 0.0
    n = len(predicted)
    return round(sum((p - a) ** 2 for p, a in zip(predicted, actual)) / n, 6)


async def _get_outcome_convergence_pairs() -> list[dict]:
    """Fetch drug outcomes and match them with convergence scores via target.

    For each drug outcome that has a target field, find the corresponding
    convergence score from the convergence_scores table. Returns a list
    of dicts with outcome, convergence score, and metadata.
    """
    # Fetch all drug outcomes with a non-null target
    outcomes = await fetch(
        """SELECT d_o.id, d_o.compound_name, d_o.target, d_o.mechanism,
                  d_o.outcome, d_o.failure_reason, d_o.trial_phase,
                  d_o.confidence AS outcome_confidence, d_o.key_finding
           FROM drug_outcomes do
           WHERE d_o.target IS NOT NULL AND d_o.target != ''
           ORDER BY d_o.compound_name"""
    )

    if not outcomes:
        return []

    pairs = []
    # Cache convergence scores by target label (lowercase)
    conv_cache: dict[str, dict | None] = {}

    for row in outcomes:
        r = dict(row)
        target_label = (r.get("target") or "").strip().lower()
        if not target_label:
            continue

        # Look up convergence score for this target
        if target_label not in conv_cache:
            conv_row = await fetchrow(
                """SELECT composite_score, volume, lab_independence,
                          method_diversity, temporal_trend, replication,
                          confidence_level, claim_count, source_count
                   FROM convergence_scores
                   WHERE LOWER(target_label) = $1
                   ORDER BY computed_at DESC LIMIT 1""",
                target_label,
            )
            if not conv_row:
                # Try fuzzy match: target might be stored differently
                conv_row = await fetchrow(
                    """SELECT composite_score, volume, lab_independence,
                              method_diversity, temporal_trend, replication,
                              confidence_level, claim_count, source_count
                       FROM convergence_scores
                       WHERE LOWER(target_label) LIKE $1
                       ORDER BY computed_at DESC LIMIT 1""",
                    "%" + target_label + "%",
                )
            conv_cache[target_label] = dict(conv_row) if conv_row else None

        conv = conv_cache[target_label]
        composite = _safe_float(conv.get("composite_score")) if conv else None

        pairs.append({
            "compound_name": r["compound_name"],
            "target": r.get("target"),
            "mechanism": r.get("mechanism"),
            "outcome": r["outcome"],
            "failure_reason": r.get("failure_reason"),
            "trial_phase": r.get("trial_phase"),
            "outcome_confidence": _safe_float(r.get("outcome_confidence"), 0.5),
            "key_finding": r.get("key_finding"),
            "convergence_score": composite,
            "convergence_details": conv,
            "has_convergence": conv is not None,
        })

    return pairs


async def calibrate_against_outcomes() -> dict[str, Any]:
    """Compare convergence scores of approved vs failed drugs.

    Groups drug outcomes by outcome type (success, failure, ongoing),
    computes mean/median convergence scores for each group, and
    calculates separation metrics.
    """
    pairs = await _get_outcome_convergence_pairs()

    if not pairs:
        return {
            "status": "no_data",
            "message": "No drug outcomes found. Run outcome extraction first.",
            "total_outcomes": 0,
            "metrics": {},
        }

    # Group by outcome category
    groups: dict[str, list[dict]] = defaultdict(list)
    for p in pairs:
        outcome = p["outcome"]
        if outcome in SUCCESS_OUTCOMES:
            groups["success"].append(p)
        elif outcome in FAILURE_OUTCOMES:
            groups["failure"].append(p)
        else:
            groups["ongoing"].append(p)

    # Compute stats for each group (only for pairs that have convergence scores)
    group_stats: dict[str, dict] = {}
    for group_name, items in groups.items():
        scored = [p for p in items if p["convergence_score"] is not None]
        scores = [p["convergence_score"] for p in scored]

        if scores:
            scores_sorted = sorted(scores)
            n = len(scores_sorted)
            mean_score = sum(scores_sorted) / n
            median_score = scores_sorted[n // 2] if n % 2 == 1 else (
                (scores_sorted[n // 2 - 1] + scores_sorted[n // 2]) / 2.0
            )
            min_score = scores_sorted[0]
            max_score = scores_sorted[-1]
        else:
            mean_score = median_score = min_score = max_score = None

        group_stats[group_name] = {
            "count": len(items),
            "scored_count": len(scored),
            "mean_convergence": round(mean_score, 4) if mean_score is not None else None,
            "median_convergence": round(median_score, 4) if median_score is not None else None,
            "min_convergence": round(min_score, 4) if min_score is not None else None,
            "max_convergence": round(max_score, 4) if max_score is not None else None,
            "compounds": [
                {
                    "compound": p["compound_name"],
                    "target": p["target"],
                    "convergence_score": round(p["convergence_score"], 4) if p["convergence_score"] is not None else None,
                    "trial_phase": p["trial_phase"],
                }
                for p in sorted(scored, key=lambda x: x["convergence_score"] or 0, reverse=True)[:10]
            ],
        }

    # === Separation Score ===
    success_scores = [p["convergence_score"] for p in groups.get("success", [])
                      if p["convergence_score"] is not None]
    failure_scores = [p["convergence_score"] for p in groups.get("failure", [])
                      if p["convergence_score"] is not None]

    separation_score = None
    if success_scores and failure_scores:
        mean_success = sum(success_scores) / len(success_scores)
        mean_failure = sum(failure_scores) / len(failure_scores)
        separation_score = round(max(-1.0, min(1.0, mean_success - mean_failure)), 4)

    # === Rank Correlation ===
    all_scored = [p for p in pairs if p["convergence_score"] is not None
                  and p["outcome"] in (SUCCESS_OUTCOMES | FAILURE_OUTCOMES)]
    rank_correlation = None
    if len(all_scored) >= 3:
        x_scores = [p["convergence_score"] for p in all_scored]
        y_outcomes = [1.0 if p["outcome"] in SUCCESS_OUTCOMES else 0.0 for p in all_scored]
        rank_correlation = _spearman_rank_correlation(x_scores, y_outcomes)

    # === Prediction Accuracy ===
    prediction_accuracy = None
    if all_scored:
        all_conv_scores = sorted([p["convergence_score"] for p in all_scored])
        median_threshold = all_conv_scores[len(all_conv_scores) // 2]
        top_scored = [p for p in all_scored if p["convergence_score"] >= median_threshold]
        if top_scored:
            successes_in_top = sum(1 for p in top_scored if p["outcome"] in SUCCESS_OUTCOMES)
            prediction_accuracy = round(successes_in_top / len(top_scored), 4)

    # === Overall calibration score (0-1) ===
    calibration_components = []
    if separation_score is not None:
        calibration_components.append(max(0.0, min(1.0, (separation_score + 1) / 2)))
    if rank_correlation is not None:
        calibration_components.append(max(0.0, min(1.0, (rank_correlation + 1) / 2)))
    if prediction_accuracy is not None:
        calibration_components.append(prediction_accuracy)

    overall_calibration = None
    if calibration_components:
        overall_calibration = round(
            sum(calibration_components) / len(calibration_components), 4
        )

    # Interpretation
    if overall_calibration is not None:
        if overall_calibration >= 0.75:
            interpretation = "GOOD: Convergence scores align well with drug outcomes. High-scored targets tend to have successful drugs."
        elif overall_calibration >= 0.55:
            interpretation = "MODERATE: Some alignment between convergence scores and outcomes. Scoring may benefit from weight adjustments."
        elif overall_calibration >= 0.35:
            interpretation = "WEAK: Limited alignment between scoring and outcomes. Consider recalibrating convergence weights."
        else:
            interpretation = "POOR: Convergence scores do not predict drug outcomes. Fundamental recalibration needed."
    else:
        interpretation = "INSUFFICIENT DATA: Not enough scored outcomes to compute calibration."

    return {
        "status": "completed",
        "total_outcomes": len(pairs),
        "outcomes_with_convergence": sum(1 for p in pairs if p["convergence_score"] is not None),
        "group_stats": group_stats,
        "metrics": {
            "separation_score": separation_score,
            "rank_correlation": rank_correlation,
            "prediction_accuracy": prediction_accuracy,
            "overall_calibration": overall_calibration,
        },
        "interpretation": interpretation,
        "calibrated_at": datetime.now(timezone.utc).isoformat(),
    }


async def compute_calibration_curve() -> dict[str, Any]:
    """Bin predictions by convergence score, check actual outcome success rates.

    For each convergence score bin, computes the fraction of outcomes that
    are successful (approved/partial_success). A well-calibrated system
    would show higher success rates in higher convergence bins.
    """
    pairs = await _get_outcome_convergence_pairs()

    # Only keep pairs with convergence scores and definitive outcomes
    scored_pairs = [
        p for p in pairs
        if p["convergence_score"] is not None
        and p["outcome"] in (SUCCESS_OUTCOMES | FAILURE_OUTCOMES)
    ]

    if not scored_pairs:
        return {
            "status": "no_data",
            "message": "No scored drug outcomes with convergence data available.",
            "bins": [],
            "brier_score": None,
        }

    # Bin by convergence score
    bins: list[dict[str, Any]] = []
    all_predicted: list[float] = []
    all_actual: list[int] = []

    for i, (lo, hi) in enumerate(_BIN_EDGES):
        bin_items = [
            p for p in scored_pairs
            if lo <= p["convergence_score"] < hi
            or (hi == 1.0 and p["convergence_score"] == 1.0 and lo == 0.8)
        ]

        if not bin_items:
            bins.append({
                "bin": _BIN_LABELS[i],
                "range": [lo, hi],
                "outcome_count": 0,
                "mean_convergence": round((lo + hi) / 2, 2),
                "success_rate": None,
                "predicted_vs_actual_gap": None,
            })
            continue

        scores = [p["convergence_score"] for p in bin_items]
        mean_conv = sum(scores) / len(scores)

        successes = sum(1 for p in bin_items if p["outcome"] in SUCCESS_OUTCOMES)
        success_rate = successes / len(bin_items)

        gap = round(mean_conv - success_rate, 4)

        bins.append({
            "bin": _BIN_LABELS[i],
            "range": [lo, hi],
            "outcome_count": len(bin_items),
            "success_count": successes,
            "failure_count": len(bin_items) - successes,
            "mean_convergence": round(mean_conv, 4),
            "success_rate": round(success_rate, 4),
            "predicted_vs_actual_gap": gap,
            "compounds": [
                {"name": p["compound_name"], "target": p["target"], "outcome": p["outcome"]}
                for p in bin_items[:5]
            ],
        })

        # Accumulate for Brier score
        for p in bin_items:
            all_predicted.append(p["convergence_score"])
            all_actual.append(1 if p["outcome"] in SUCCESS_OUTCOMES else 0)

    # Brier score
    brier = _brier_score(all_predicted, all_actual)

    # Plot data
    plot_data = {
        "x_convergence": [b["mean_convergence"] for b in bins if b["outcome_count"] > 0],
        "y_success_rate": [b["success_rate"] for b in bins if b["outcome_count"] > 0],
        "perfect_calibration": [b["mean_convergence"] for b in bins if b["outcome_count"] > 0],
        "bin_sizes": [b["outcome_count"] for b in bins if b["outcome_count"] > 0],
    }

    # Interpretation
    if brier <= 0.1:
        quality = "EXCELLENT"
    elif brier <= 0.2:
        quality = "GOOD"
    elif brier <= 0.3:
        quality = "MODERATE"
    else:
        quality = "POOR"

    return {
        "status": "completed",
        "total_scored_outcomes": len(scored_pairs),
        "bins": bins,
        "brier_score": brier,
        "calibration_quality": quality,
        "plot_data": plot_data,
        "methodology": {
            "outcome_mapping": "success/partial_success = positive, failure/discontinued = negative",
            "score_source": "convergence_scores table (5-dimension composite)",
            "brier_range": "0 (perfect) to 1 (worst); <0.1 excellent, <0.2 good",
        },
        "calibrated_at": datetime.now(timezone.utc).isoformat(),
    }


async def validate_target_score(target_symbol: str) -> dict[str, Any]:
    """Validate a specific target's convergence score against its drug outcomes.

    Checks all drug outcomes that mention this target and compares the
    convergence score against the outcome distribution.
    """
    # Get convergence score for this target
    conv_row = await fetchrow(
        """SELECT composite_score, volume, lab_independence,
                  method_diversity, temporal_trend, replication,
                  confidence_level, claim_count, source_count,
                  target_label, weights_version
           FROM convergence_scores
           WHERE LOWER(target_label) = $1
           ORDER BY computed_at DESC LIMIT 1""",
        target_symbol.lower(),
    )

    if not conv_row:
        return {
            "status": "not_found",
            "message": "No convergence score found for target '%s'." % target_symbol,
            "target": target_symbol,
        }

    conv = dict(conv_row)
    composite = _safe_float(conv.get("composite_score"))

    # Get drug outcomes for this target
    outcomes = await fetch(
        """SELECT compound_name, target, outcome, failure_reason,
                  trial_phase, key_finding, confidence
           FROM drug_outcomes
           WHERE LOWER(target) LIKE $1
           ORDER BY compound_name""",
        "%" + target_symbol.lower() + "%",
    )

    if not outcomes:
        return {
            "status": "no_outcomes",
            "message": "No drug outcomes found for target '%s'." % target_symbol,
            "target": target_symbol,
            "convergence_score": round(composite, 4),
            "confidence_level": conv.get("confidence_level"),
            "claim_count": conv.get("claim_count"),
        }

    outcome_list = [dict(r) for r in outcomes]
    success_count = sum(1 for o in outcome_list if o["outcome"] in SUCCESS_OUTCOMES)
    failure_count = sum(1 for o in outcome_list if o["outcome"] in FAILURE_OUTCOMES)
    total_definitive = success_count + failure_count

    # Actual success rate for this target
    actual_success_rate = None
    if total_definitive > 0:
        actual_success_rate = round(success_count / total_definitive, 4)

    # Calibration gap: convergence score vs actual success rate
    calibration_gap = None
    if actual_success_rate is not None:
        calibration_gap = round(composite - actual_success_rate, 4)

    # Verdict
    if calibration_gap is not None:
        if abs(calibration_gap) <= 0.15:
            verdict = "WELL_CALIBRATED"
            explanation = (
                "Convergence score (%.0f%%) closely matches "
                "actual success rate (%.0f%%)." % (composite * 100, actual_success_rate * 100)
            )
        elif calibration_gap > 0.15:
            verdict = "OVERCONFIDENT"
            explanation = (
                "Convergence score (%.0f%%) exceeds actual "
                "success rate (%.0f%%). The evidence "
                "scoring may be overweighting this target." % (composite * 100, actual_success_rate * 100)
            )
        else:
            verdict = "UNDERCONFIDENT"
            explanation = (
                "Convergence score (%.0f%%) is below actual "
                "success rate (%.0f%%). This target "
                "may deserve a higher evidence score." % (composite * 100, actual_success_rate * 100)
            )
    else:
        verdict = "INSUFFICIENT_OUTCOMES"
        explanation = "Not enough definitive outcomes to evaluate calibration."

    return {
        "status": "completed",
        "target": target_symbol,
        "convergence_score": round(composite, 4),
        "confidence_level": conv.get("confidence_level"),
        "claim_count": conv.get("claim_count"),
        "source_count": conv.get("source_count"),
        "convergence_breakdown": {
            "volume": _safe_float(conv.get("volume")),
            "lab_independence": _safe_float(conv.get("lab_independence")),
            "method_diversity": _safe_float(conv.get("method_diversity")),
            "temporal_trend": _safe_float(conv.get("temporal_trend")),
            "replication": _safe_float(conv.get("replication")),
        },
        "outcomes": {
            "total": len(outcome_list),
            "success_count": success_count,
            "failure_count": failure_count,
            "ongoing_count": len(outcome_list) - success_count - failure_count,
            "actual_success_rate": actual_success_rate,
        },
        "calibration": {
            "gap": calibration_gap,
            "verdict": verdict,
            "explanation": explanation,
        },
        "compounds": [
            {
                "compound": o["compound_name"],
                "outcome": o["outcome"],
                "failure_reason": o.get("failure_reason"),
                "trial_phase": o.get("trial_phase"),
                "key_finding": o.get("key_finding"),
            }
            for o in outcome_list[:20]
        ],
        "calibrated_at": datetime.now(timezone.utc).isoformat(),
    }


async def get_bayesian_calibration_report() -> dict[str, Any]:
    """Full Bayesian evidence calibration report.

    Combines outcome calibration, calibration curves, and metrics
    to produce a comprehensive assessment of how well the platform's
    scoring predicts real-world drug outcomes.
    """
    outcome_cal = await calibrate_against_outcomes()
    curve_cal = await compute_calibration_curve()

    # Compute overall calibration percentage
    components: list[float] = []

    # From outcome calibration
    overall_cal = (outcome_cal.get("metrics") or {}).get("overall_calibration")
    if overall_cal is not None:
        components.append(overall_cal)

    # From calibration curve Brier score (inverted: 1 - brier)
    brier = curve_cal.get("brier_score")
    if brier is not None:
        components.append(max(0.0, 1.0 - brier))

    # From separation score (normalized to 0-1)
    sep = (outcome_cal.get("metrics") or {}).get("separation_score")
    if sep is not None:
        components.append(max(0.0, min(1.0, (sep + 1) / 2)))

    calibration_pct = None
    if components:
        calibration_pct = round(sum(components) / len(components) * 100, 1)

    # Grade
    if calibration_pct is not None:
        if calibration_pct >= 75:
            grade = "A"
            grade_label = "Well Calibrated"
        elif calibration_pct >= 55:
            grade = "B"
            grade_label = "Moderately Calibrated"
        elif calibration_pct >= 35:
            grade = "C"
            grade_label = "Weakly Calibrated"
        else:
            grade = "D"
            grade_label = "Poorly Calibrated"
    else:
        grade = "-"
        grade_label = "Insufficient Data"

    return {
        "calibration_pct": calibration_pct,
        "grade": grade,
        "grade_label": grade_label,
        "outcome_calibration": outcome_cal,
        "calibration_curve": curve_cal,
        "summary": {
            "total_outcomes": outcome_cal.get("total_outcomes", 0),
            "outcomes_with_convergence": outcome_cal.get("outcomes_with_convergence", 0),
            "separation_score": (outcome_cal.get("metrics") or {}).get("separation_score"),
            "rank_correlation": (outcome_cal.get("metrics") or {}).get("rank_correlation"),
            "prediction_accuracy": (outcome_cal.get("metrics") or {}).get("prediction_accuracy"),
            "brier_score": brier,
        },
        "methodology": {
            "description": (
                "Back-tests convergence scores against known drug outcomes "
                "(approved, failed, ongoing) from the drug_outcomes table. "
                "A well-calibrated system would show higher convergence scores "
                "for approved drugs and lower scores for failed drugs."
            ),
            "convergence_dimensions": [
                "volume (0.15)", "lab_independence (0.30)",
                "method_diversity (0.20)", "temporal_trend (0.15)",
                "replication (0.20)",
            ],
            "outcome_source": "drug_outcomes table (LLM-extracted from PubMed literature)",
        },
        "calibrated_at": datetime.now(timezone.utc).isoformat(),
    }
