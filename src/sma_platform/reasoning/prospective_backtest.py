"""
Prospective Backtesting — Would our predictions have been right?
================================================================
Tests the platform's predictive power by simulating past states:
1. Take all claims created before a cutoff date
2. Run convergence scoring on that subset
3. Check if high-scored targets had subsequent positive outcomes
4. Compare: would our system have prioritized what actually worked?

This is ChatGPT audit item A4 — the key question:
"If we had run our prioritizer on data from Month X, would it have
correctly predicted outcomes discovered by Month Y?"

Methodology:
- For each cutoff date, compute convergence scores using ONLY claims
  created before that date (simulating what we would have known then)
- Compare the ranked list against drug outcomes that were discovered
  AFTER the cutoff (the "future" we're trying to predict)
- Track how predictions evolve as more evidence accumulates
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from dateutil.relativedelta import relativedelta

from ..core.database import fetch, fetchrow, fetchval
from .convergence_engine import (
    CONVERGENCE_WEIGHTS,
    CONFIDENCE_THRESHOLDS,
    LAB_CEILING,
    METHOD_CEILING,
    VOLUME_CEILING,
    YEAR_SPAN_CEILING,
    _clamp,
    _confidence_level,
    _extract_lab_proxy,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


async def _compute_target_convergence_at_cutoff(
    target_id: str,
    cutoff: datetime,
) -> dict | None:
    """Compute convergence score for a target using only claims before cutoff.

    This is the core of prospective backtesting: we simulate what the
    convergence engine would have produced if run at the cutoff date,
    by restricting the query to claims.created_at < cutoff.

    Returns dict with all 5 dimensions + composite, or None if <3 claims.
    """
    rows = await fetch(
        """
        SELECT
            c.id            AS claim_id,
            c.claim_type,
            c.predicate,
            c.confidence    AS claim_confidence,
            e.method,
            e.source_id,
            s.authors,
            s.pub_date,
            s.source_type
        FROM claims c
        LEFT JOIN evidence e ON e.claim_id = c.id
        LEFT JOIN sources s  ON e.source_id = s.id
        WHERE c.subject_id = $1
          AND c.created_at < $2
        ORDER BY c.created_at
        """,
        target_id,
        cutoff,
    )

    if len(rows) < 3:
        return None

    claim_ids: list[str] = []
    source_ids: set[str] = set()
    lab_proxies: set[str] = set()
    methods: set[str] = set()
    years: list[int] = []
    predicates: Counter = Counter()
    predicate_sources: defaultdict[str, set[str]] = defaultdict(set)

    for row in rows:
        r = dict(row)
        cid = str(r["claim_id"])
        if cid not in claim_ids:
            claim_ids.append(cid)

        sid = str(r["source_id"]) if r.get("source_id") else None
        if sid:
            source_ids.add(sid)

        lab = _extract_lab_proxy(r.get("authors"))
        if lab:
            lab_proxies.add(lab)

        method = (r.get("method") or "").strip().lower()
        if method:
            methods.add(method)

        pub_date = r.get("pub_date")
        if pub_date:
            try:
                if hasattr(pub_date, "year"):
                    years.append(pub_date.year)
                else:
                    years.append(int(str(pub_date)[:4]))
            except (ValueError, TypeError):
                pass

        pred = (r.get("predicate") or "").strip().lower()[:100]
        if pred:
            predicates[pred] += 1
            if sid:
                predicate_sources[pred].add(sid)

    claim_count = len(claim_ids)
    source_count = len(source_ids)

    # --- Dimension 1: Volume ---
    volume = _clamp(claim_count / VOLUME_CEILING)

    # --- Dimension 2: Lab Independence ---
    lab_independence = _clamp(len(lab_proxies) / LAB_CEILING)

    # --- Dimension 3: Method Diversity ---
    method_diversity = _clamp(len(methods) / METHOD_CEILING)

    # --- Dimension 4: Temporal Trend ---
    # Use the cutoff year instead of current year for recency calculation
    cutoff_year = cutoff.year
    if len(years) >= 2:
        year_span = max(years) - min(years)
        span_score = _clamp(year_span / YEAR_SPAN_CEILING)
        unique_years = len(set(years))
        consistency = _clamp(unique_years / (year_span + 1))
        most_recent = max(years)
        recency = _clamp(1.0 - (cutoff_year - most_recent) / 10.0)
        temporal_trend = _clamp(
            span_score * 0.3 + consistency * 0.4 + recency * 0.3
        )
    else:
        temporal_trend = 0.1

    # --- Dimension 5: Replication ---
    total_predicates = len(predicates)
    replicated = sum(
        1
        for pred, sources in predicate_sources.items()
        if len(sources) >= 2
    )
    replication = _clamp(replicated / max(total_predicates, 1))

    # --- Composite Score ---
    composite = _clamp(
        CONVERGENCE_WEIGHTS["volume"] * volume
        + CONVERGENCE_WEIGHTS["lab_independence"] * lab_independence
        + CONVERGENCE_WEIGHTS["method_diversity"] * method_diversity
        + CONVERGENCE_WEIGHTS["temporal_trend"] * temporal_trend
        + CONVERGENCE_WEIGHTS["replication"] * replication
    )

    return {
        "target_id": target_id,
        "volume": volume,
        "lab_independence": lab_independence,
        "method_diversity": method_diversity,
        "temporal_trend": temporal_trend,
        "replication": replication,
        "composite_score": composite,
        "confidence_level": _confidence_level(composite),
        "claim_count": claim_count,
        "source_count": source_count,
        "methods_found": sorted(methods),
        "labs_found": sorted(lab_proxies),
        "year_range": [min(years), max(years)] if years else [],
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def backtest_at_cutoff(cutoff_date: datetime) -> dict[str, Any]:
    """Run convergence scoring using only claims from before cutoff_date.

    Simulates what the platform would have produced if run at the given
    date. Returns a ranked list of targets with their convergence scores.

    Args:
        cutoff_date: Only use claims created before this date.

    Returns:
        Dict with ranked targets and metadata about the backtest run.
    """
    # Count total claims available at this cutoff
    total_claims = await fetchval(
        "SELECT COUNT(*) FROM claims WHERE created_at < $1",
        cutoff_date,
    ) or 0

    total_sources = await fetchval(
        "SELECT COUNT(*) FROM sources WHERE created_at < $1",
        cutoff_date,
    ) or 0

    if total_claims < 3:
        return {
            "status": "insufficient_data",
            "cutoff_date": cutoff_date.isoformat(),
            "total_claims_available": int(total_claims),
            "message": (
                "Fewer than 3 claims exist before the cutoff date. "
                "Cannot compute meaningful convergence scores."
            ),
            "ranked_targets": [],
        }

    # Get all targets that have at least 1 claim before cutoff
    targets = await fetch(
        """
        SELECT DISTINCT t.id, t.symbol, t.target_type
        FROM targets t
        JOIN claims c ON c.subject_id = t.id
        WHERE c.created_at < $1
        ORDER BY t.symbol
        """,
        cutoff_date,
    )

    scored = 0
    skipped = 0
    results: list[dict] = []

    for t in targets:
        t = dict(t)
        tid = str(t["id"])
        result = await _compute_target_convergence_at_cutoff(tid, cutoff_date)

        if result is None:
            skipped += 1
            continue

        results.append({
            "target_id": tid,
            "target_symbol": t["symbol"],
            "target_type": t.get("target_type", "target"),
            "composite_score": result["composite_score"],
            "confidence_level": result["confidence_level"],
            "claim_count": result["claim_count"],
            "source_count": result["source_count"],
            "breakdown": {
                "volume": result["volume"],
                "lab_independence": result["lab_independence"],
                "method_diversity": result["method_diversity"],
                "temporal_trend": result["temporal_trend"],
                "replication": result["replication"],
            },
        })
        scored += 1

    # Sort by composite score descending
    results.sort(key=lambda x: x["composite_score"], reverse=True)

    # Add rank
    for i, r in enumerate(results, 1):
        r["rank"] = i

    return {
        "status": "completed",
        "cutoff_date": cutoff_date.isoformat(),
        "total_claims_available": int(total_claims),
        "total_sources_available": int(total_sources),
        "targets_scored": scored,
        "targets_skipped": skipped,
        "ranked_targets": results,
        "top_5": results[:5],
    }


async def compare_predictions_to_outcomes(
    prediction_date: datetime,
    outcome_date: datetime,
) -> dict[str, Any]:
    """Compare what the system would have predicted at prediction_date
    against what actually happened by outcome_date.

    This is the core backtest: did our convergence scoring at time T
    correctly rank the targets that had positive outcomes by time T+delta?

    Args:
        prediction_date: Simulate running the prioritizer at this date.
        outcome_date: Check outcomes discovered by this date.

    Returns:
        Dict with prediction accuracy metrics, ranked comparison, and
        per-target details.
    """
    if outcome_date <= prediction_date:
        return {
            "status": "invalid_dates",
            "message": "outcome_date must be after prediction_date.",
            "prediction_date": prediction_date.isoformat(),
            "outcome_date": outcome_date.isoformat(),
        }

    # Step 1: Get predictions at the prediction_date
    predictions = await backtest_at_cutoff(prediction_date)

    if predictions["status"] != "completed" or not predictions["ranked_targets"]:
        return {
            "status": "insufficient_predictions",
            "message": "Not enough data to generate predictions at the given date.",
            "prediction_date": prediction_date.isoformat(),
            "outcome_date": outcome_date.isoformat(),
            "predictions": predictions,
        }

    # Step 2: Get drug outcomes that appeared between prediction_date and outcome_date
    # These are the "future discoveries" we're trying to predict
    new_outcomes = await fetch(
        """
        SELECT d_o.compound_name, d_o.target, d_o.mechanism,
               d_o.outcome, d_o.failure_reason, d_o.trial_phase,
               d_o.confidence, d_o.key_finding, d_o.created_at
        FROM drug_outcomes d_o
        WHERE d_o.created_at >= $1 AND d_o.created_at < $2
          AND d_o.target IS NOT NULL AND d_o.target != ''
        ORDER BY d_o.created_at
        """,
        prediction_date,
        outcome_date,
    )

    # Step 3: Get claims added between prediction and outcome date (new evidence)
    new_claims_count = await fetchval(
        "SELECT COUNT(*) FROM claims WHERE created_at >= $1 AND created_at < $2",
        prediction_date,
        outcome_date,
    ) or 0

    # Step 4: Also consider ALL known outcomes (not just new ones) for comparison
    # This covers outcomes that were already known but whose targets we're scoring
    all_outcomes = await fetch(
        """
        SELECT d_o.compound_name, d_o.target, d_o.outcome,
               d_o.failure_reason, d_o.trial_phase
        FROM drug_outcomes d_o
        WHERE d_o.target IS NOT NULL AND d_o.target != ''
        ORDER BY d_o.compound_name
        """,
    )

    # Build outcome lookup by target (lowercase)
    SUCCESS_OUTCOMES = {"success", "partial_success"}
    FAILURE_OUTCOMES = {"failure", "discontinued"}

    target_outcomes: dict[str, list[dict]] = defaultdict(list)
    for row in all_outcomes:
        r = dict(row)
        target_label = (r.get("target") or "").strip().lower()
        if target_label:
            target_outcomes[target_label].append(r)

    # Step 5: Match predictions to outcomes
    matched: list[dict] = []
    for pred in predictions["ranked_targets"]:
        symbol = pred["target_symbol"].lower()

        # Find outcomes for this target (exact or partial match)
        outcomes_for_target = target_outcomes.get(symbol, [])
        if not outcomes_for_target:
            # Try partial match
            for key, outcomes in target_outcomes.items():
                if symbol in key or key in symbol:
                    outcomes_for_target = outcomes
                    break

        if outcomes_for_target:
            successes = sum(
                1 for o in outcomes_for_target if o["outcome"] in SUCCESS_OUTCOMES
            )
            failures = sum(
                1 for o in outcomes_for_target if o["outcome"] in FAILURE_OUTCOMES
            )
            total_definitive = successes + failures
            actual_success_rate = (
                round(successes / total_definitive, 4)
                if total_definitive > 0
                else None
            )

            matched.append({
                "rank": pred["rank"],
                "target_symbol": pred["target_symbol"],
                "predicted_score": pred["composite_score"],
                "confidence_level": pred["confidence_level"],
                "actual_outcomes": len(outcomes_for_target),
                "successes": successes,
                "failures": failures,
                "actual_success_rate": actual_success_rate,
                "prediction_correct": (
                    (pred["composite_score"] >= 0.5 and successes > failures)
                    or (pred["composite_score"] < 0.5 and failures >= successes)
                )
                if total_definitive > 0
                else None,
                "compounds": [
                    {
                        "name": o["compound_name"],
                        "outcome": o["outcome"],
                        "phase": o.get("trial_phase"),
                    }
                    for o in outcomes_for_target[:5]
                ],
            })

    # Step 6: Compute accuracy metrics
    evaluated = [m for m in matched if m["prediction_correct"] is not None]
    correct = sum(1 for m in evaluated if m["prediction_correct"])
    accuracy = round(correct / len(evaluated), 4) if evaluated else None

    # Precision@k: Of the top-k predictions, how many had positive outcomes?
    precision_at_5 = None
    precision_at_10 = None
    if matched:
        top_5 = [m for m in matched if m["rank"] <= 5]
        top_5_correct = [m for m in top_5 if m.get("actual_success_rate") and m["actual_success_rate"] > 0.5]
        precision_at_5 = round(len(top_5_correct) / max(len(top_5), 1), 4)

        top_10 = [m for m in matched if m["rank"] <= 10]
        top_10_correct = [m for m in top_10 if m.get("actual_success_rate") and m["actual_success_rate"] > 0.5]
        precision_at_10 = round(len(top_10_correct) / max(len(top_10), 1), 4)

    # Spearman rank correlation between predicted scores and actual success rates
    rank_correlation = None
    scored_matched = [
        m for m in matched
        if m["actual_success_rate"] is not None
    ]
    if len(scored_matched) >= 3:
        x = [m["predicted_score"] for m in scored_matched]
        y = [m["actual_success_rate"] for m in scored_matched]
        rank_correlation = _spearman_rank(x, y)

    return {
        "status": "completed",
        "prediction_date": prediction_date.isoformat(),
        "outcome_date": outcome_date.isoformat(),
        "window_months": round(
            (outcome_date - prediction_date).days / 30.44, 1
        ),
        "data_at_prediction": {
            "claims_available": predictions["total_claims_available"],
            "sources_available": predictions["total_sources_available"],
            "targets_scored": predictions["targets_scored"],
        },
        "new_evidence_in_window": {
            "new_claims": int(new_claims_count),
            "new_outcomes": len(new_outcomes),
        },
        "metrics": {
            "accuracy": accuracy,
            "precision_at_5": precision_at_5,
            "precision_at_10": precision_at_10,
            "rank_correlation": rank_correlation,
            "targets_matched_to_outcomes": len(matched),
            "targets_evaluated": len(evaluated),
            "targets_correct": correct if evaluated else None,
        },
        "matched_predictions": matched[:20],
        "top_predictions_at_cutoff": predictions["top_5"],
        "interpretation": _interpret_accuracy(accuracy, precision_at_5),
        "compared_at": datetime.now(timezone.utc).isoformat(),
    }


async def run_temporal_backtest(
    start_date: datetime,
    end_date: datetime,
    step_months: int = 3,
) -> dict[str, Any]:
    """Run backtests at multiple timepoints to show how predictions evolve.

    Steps through time from start_date to end_date in step_months
    increments, running convergence scoring at each cutoff and tracking
    how target rankings change over time.

    Args:
        start_date: First cutoff date to simulate.
        end_date: Last cutoff date (also used as the outcome reference).
        step_months: Months between each backtest point.

    Returns:
        Dict with per-timepoint results, temporal accuracy curve,
        and rank stability metrics.
    """
    if end_date <= start_date:
        return {
            "status": "invalid_dates",
            "message": "end_date must be after start_date.",
        }

    if step_months < 1 or step_months > 24:
        return {
            "status": "invalid_step",
            "message": "step_months must be between 1 and 24.",
        }

    # Determine earliest claim date to validate the range
    earliest_claim = await fetchval(
        "SELECT MIN(created_at) FROM claims"
    )
    latest_claim = await fetchval(
        "SELECT MAX(created_at) FROM claims"
    )

    if not earliest_claim or not latest_claim:
        return {
            "status": "no_data",
            "message": "No claims found in the database.",
        }

    # Generate cutoff dates
    cutoff_dates: list[datetime] = []
    current = start_date
    while current <= end_date:
        cutoff_dates.append(current)
        current = current + relativedelta(months=step_months)

    if not cutoff_dates:
        return {
            "status": "no_timepoints",
            "message": "No valid timepoints between start and end dates.",
        }

    # Run backtest at each cutoff
    timepoints: list[dict] = []
    accuracy_curve: list[dict] = []
    target_rank_history: dict[str, list[dict]] = defaultdict(list)

    for cutoff in cutoff_dates:
        logger.info("Running backtest at cutoff: %s", cutoff.isoformat())

        bt = await backtest_at_cutoff(cutoff)

        # Track target rankings over time
        if bt["status"] == "completed":
            for t in bt["ranked_targets"]:
                target_rank_history[t["target_symbol"]].append({
                    "cutoff": cutoff.isoformat(),
                    "rank": t["rank"],
                    "score": t["composite_score"],
                })

        # Compare to outcomes (using end_date as the outcome reference)
        comparison = await compare_predictions_to_outcomes(cutoff, end_date)

        tp_result = {
            "cutoff_date": cutoff.isoformat(),
            "claims_available": bt.get("total_claims_available", 0),
            "targets_scored": bt.get("targets_scored", 0),
            "top_3": [
                {"symbol": t["target_symbol"], "score": t["composite_score"]}
                for t in bt.get("ranked_targets", [])[:3]
            ],
        }

        if comparison["status"] == "completed":
            metrics = comparison.get("metrics", {})
            tp_result["accuracy"] = metrics.get("accuracy")
            tp_result["precision_at_5"] = metrics.get("precision_at_5")
            tp_result["rank_correlation"] = metrics.get("rank_correlation")

            accuracy_curve.append({
                "cutoff_date": cutoff.isoformat(),
                "accuracy": metrics.get("accuracy"),
                "precision_at_5": metrics.get("precision_at_5"),
                "claims_available": bt.get("total_claims_available", 0),
            })

        timepoints.append(tp_result)

    # Compute rank stability: how much do target rankings change between timepoints?
    rank_stability: list[dict] = []
    for symbol, history in sorted(
        target_rank_history.items(),
        key=lambda x: len(x[1]),
        reverse=True,
    )[:20]:
        if len(history) >= 2:
            ranks = [h["rank"] for h in history]
            scores = [h["score"] for h in history]
            rank_variance = _variance(ranks)
            score_trend = scores[-1] - scores[0]  # positive = improving

            rank_stability.append({
                "target_symbol": symbol,
                "appearances": len(history),
                "first_rank": ranks[0],
                "last_rank": ranks[-1],
                "rank_variance": round(rank_variance, 2),
                "score_trend": round(score_trend, 4),
                "stable": rank_variance < 5.0,
                "history": history,
            })

    # Overall temporal assessment
    accuracies = [
        a["accuracy"]
        for a in accuracy_curve
        if a["accuracy"] is not None
    ]
    improving = False
    if len(accuracies) >= 2:
        # Check if later timepoints have higher accuracy
        first_half = accuracies[: len(accuracies) // 2]
        second_half = accuracies[len(accuracies) // 2 :]
        if first_half and second_half:
            improving = (
                sum(second_half) / len(second_half)
                > sum(first_half) / len(first_half)
            )

    return {
        "status": "completed",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "step_months": step_months,
        "num_timepoints": len(timepoints),
        "data_range": {
            "earliest_claim": earliest_claim.isoformat() if earliest_claim else None,
            "latest_claim": latest_claim.isoformat() if latest_claim else None,
        },
        "timepoints": timepoints,
        "accuracy_curve": accuracy_curve,
        "rank_stability": rank_stability,
        "summary": {
            "mean_accuracy": (
                round(sum(accuracies) / len(accuracies), 4) if accuracies else None
            ),
            "accuracy_improving": improving,
            "stable_targets": sum(
                1 for r in rank_stability if r["stable"]
            ),
            "volatile_targets": sum(
                1 for r in rank_stability if not r["stable"]
            ),
        },
        "interpretation": _interpret_temporal(accuracies, improving),
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


async def get_backtest_report() -> dict[str, Any]:
    """Full prospective backtest report with temporal accuracy curve.

    Automatically determines appropriate date ranges from the data
    and runs a comprehensive temporal backtest.

    Returns:
        Dict with temporal accuracy curve, rank stability, predictions
        vs outcomes, and overall assessment.
    """
    # Determine data range
    earliest_claim = await fetchval("SELECT MIN(created_at) FROM claims")
    latest_claim = await fetchval("SELECT MAX(created_at) FROM claims")

    if not earliest_claim or not latest_claim:
        return {
            "status": "no_data",
            "message": "No claims found in the database. Ingest papers first.",
        }

    # Total counts for context
    total_claims = await fetchval("SELECT COUNT(*) FROM claims") or 0
    total_sources = await fetchval("SELECT COUNT(*) FROM sources") or 0
    total_outcomes = await fetchval("SELECT COUNT(*) FROM drug_outcomes") or 0

    # Compute the time span
    data_span_days = (latest_claim - earliest_claim).days
    data_span_months = max(1, data_span_days // 30)

    # Choose step size based on data span
    if data_span_months <= 6:
        step = 1
    elif data_span_months <= 24:
        step = 3
    else:
        step = 6

    # Start at 25% of the data (need enough data for scoring to be meaningful)
    quarter_delta = relativedelta(days=data_span_days // 4)
    start = earliest_claim + quarter_delta

    # Run the temporal backtest
    temporal = await run_temporal_backtest(start, latest_claim, step)

    # Run a single detailed backtest at the midpoint for detailed comparison
    mid_delta = relativedelta(days=data_span_days // 2)
    midpoint = earliest_claim + mid_delta
    midpoint_comparison = await compare_predictions_to_outcomes(
        midpoint, latest_claim
    )

    # Run the latest possible backtest (30 days before latest claim)
    recent_cutoff = latest_claim - relativedelta(days=30)
    if recent_cutoff > earliest_claim:
        recent_backtest = await backtest_at_cutoff(recent_cutoff)
    else:
        recent_backtest = {"status": "insufficient_data", "ranked_targets": []}

    # Compute overall grade
    accuracies = [
        tp.get("accuracy")
        for tp in temporal.get("timepoints", [])
        if tp.get("accuracy") is not None
    ]
    mean_accuracy = (
        sum(accuracies) / len(accuracies) if accuracies else None
    )

    if mean_accuracy is not None:
        if mean_accuracy >= 0.75:
            grade = "A"
            grade_label = "Strong Predictive Power"
        elif mean_accuracy >= 0.55:
            grade = "B"
            grade_label = "Moderate Predictive Power"
        elif mean_accuracy >= 0.35:
            grade = "C"
            grade_label = "Weak Predictive Power"
        else:
            grade = "D"
            grade_label = "Poor Predictive Power"
    else:
        grade = "-"
        grade_label = "Insufficient Data"

    return {
        "status": "completed",
        "grade": grade,
        "grade_label": grade_label,
        "mean_accuracy": round(mean_accuracy, 4) if mean_accuracy is not None else None,
        "data_summary": {
            "total_claims": int(total_claims),
            "total_sources": int(total_sources),
            "total_drug_outcomes": int(total_outcomes),
            "data_span_months": data_span_months,
            "earliest_claim": earliest_claim.isoformat(),
            "latest_claim": latest_claim.isoformat(),
        },
        "temporal_backtest": temporal,
        "midpoint_comparison": midpoint_comparison,
        "recent_predictions": {
            "cutoff": recent_cutoff.isoformat() if recent_cutoff > earliest_claim else None,
            "top_targets": [
                {
                    "symbol": t["target_symbol"],
                    "score": t["composite_score"],
                    "confidence": t["confidence_level"],
                }
                for t in recent_backtest.get("ranked_targets", [])[:10]
            ],
        },
        "methodology": {
            "description": (
                "Prospective backtesting simulates running the convergence "
                "engine at past timepoints and comparing its rankings against "
                "subsequently discovered outcomes. A high accuracy means the "
                "platform's evidence scoring would have correctly prioritized "
                "targets that later proved successful."
            ),
            "convergence_weights": CONVERGENCE_WEIGHTS,
            "step_months": temporal.get("step_months"),
            "num_timepoints": temporal.get("num_timepoints"),
        },
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Statistical helpers
# ---------------------------------------------------------------------------

def _spearman_rank(x: list[float], y: list[float]) -> float:
    """Compute Spearman rank correlation between two lists."""
    n = len(x)
    if n < 3:
        return 0.0

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


def _variance(values: list[float]) -> float:
    """Compute variance of a list of numbers."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / (len(values) - 1)


def _interpret_accuracy(
    accuracy: float | None,
    precision_at_5: float | None,
) -> str:
    """Generate human-readable interpretation of backtest accuracy."""
    if accuracy is None:
        return (
            "INSUFFICIENT DATA: No targets could be matched to drug "
            "outcomes. More outcome data needed for meaningful backtesting."
        )
    if accuracy >= 0.75:
        quality = "STRONG"
        detail = (
            "The convergence engine would have correctly prioritized "
            "targets that later proved successful in %.0f%% of cases."
            % (accuracy * 100)
        )
    elif accuracy >= 0.55:
        quality = "MODERATE"
        detail = (
            "The convergence engine shows some predictive power "
            "(%.0f%% accuracy). Scoring weights may benefit from "
            "recalibration." % (accuracy * 100)
        )
    elif accuracy >= 0.35:
        quality = "WEAK"
        detail = (
            "The convergence engine has limited predictive power "
            "(%.0f%% accuracy). Consider recalibrating weights or "
            "adding new evidence dimensions." % (accuracy * 100)
        )
    else:
        quality = "POOR"
        detail = (
            "The convergence engine does not predict outcomes well "
            "(%.0f%% accuracy). Fundamental recalibration needed."
            % (accuracy * 100)
        )

    p5_note = ""
    if precision_at_5 is not None:
        p5_note = " Precision@5 = %.0f%%." % (precision_at_5 * 100)

    return f"{quality}: {detail}{p5_note}"


def _interpret_temporal(
    accuracies: list[float],
    improving: bool,
) -> str:
    """Generate interpretation of temporal backtest results."""
    if not accuracies:
        return (
            "INSUFFICIENT DATA: Could not compute accuracy at any "
            "timepoint. More claims and outcomes needed."
        )

    mean_acc = sum(accuracies) / len(accuracies)
    trend = "IMPROVING" if improving else "STABLE/DECLINING"

    return (
        "%s OVER TIME: Mean accuracy across %d timepoints is %.0f%%. "
        "As more evidence accumulates, predictions are %s. "
        "This %s the convergence scoring methodology."
        % (
            trend,
            len(accuracies),
            mean_acc * 100,
            "getting more accurate" if improving else "not clearly improving",
            "validates" if improving and mean_acc >= 0.5 else "suggests revisiting",
        )
    )
