"""Confidence Calibration API routes.

Back-tests scoring models against known SMA drug approvals to measure
how well our predictions and hypotheses align with established biology.
Also provides calibration curves showing predicted confidence vs actual
replication rate across all claims.

M5 Bayesian Evidence Calibration endpoints back-test convergence scores
against known drug outcomes (approved vs failed) from the drug_outcomes table.

M5 Uncertainty Quantification endpoints provide Wilson score confidence
intervals and uncertainty grades (A-D) for every target prediction.

A4 Prospective Backtesting endpoints simulate running the prioritizer at
past dates and compare its rankings against subsequently discovered outcomes.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, HTTPException, Query

from ...reasoning.confidence_calibrator import (
    calibrate_hypotheses,
    calibrate_predictions,
    generate_calibration_curves,
    get_calibration_report,
)
from ...reasoning.bayesian_calibration import (
    calibrate_against_outcomes,
    compute_calibration_curve as bayesian_calibration_curve,
    get_bayesian_calibration_report,
    validate_target_score,
)
from ...reasoning.uncertainty_engine import (
    compute_all_uncertainties as uq_compute_all,
    compute_target_uncertainty as uq_compute_target,
    get_uncertainty_report as uq_get_report,
)
from ...reasoning.prospective_backtest import (
    backtest_at_cutoff,
    compare_predictions_to_outcomes,
    get_backtest_report,
    run_temporal_backtest,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/calibration/report")
async def calibration_report():
    """Full confidence calibration report.

    Evaluates synergy predictions, hypothesis confidence scores, and claim
    calibration curves against the 3 approved SMA drugs (nusinersen, risdiplam,
    onasemnogene) and their validated targets (SMN1, SMN2).

    Returns an overall grade (A-D), per-system metrics, calibration curves,
    Brier score, and interpretation.
    """
    return await get_calibration_report()


@router.get("/calibration/predictions")
async def calibration_predictions():
    """Calibrate synergy predictions against approved drug-target pairs.

    Checks if the 3 approved SMA drugs rank in the top positions when
    predictions are sorted by synergy score. Returns precision@k,
    mean reciprocal rank, and per-drug rank information.
    """
    return await calibrate_predictions()


@router.get("/calibration/hypotheses")
async def calibration_hypotheses():
    """Calibrate hypothesis confidence for SMN1/SMN2 targets.

    Checks whether hypotheses about the validated SMA targets (SMN1, SMN2)
    have the highest confidence scores. Returns rank distribution and
    confidence gap analysis.
    """
    return await calibrate_hypotheses()


@router.get("/calibration/curves")
async def calibration_curves():
    """Generate calibration curve data -- predicted confidence vs actual replication rate.

    Bins all claims by confidence (0-0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0)
    and for each bin computes:
    - mean_confidence: average confidence score in the bin
    - replication_rate: fraction of claims with 2+ independent sources
    - claim_type_consistency_rate: fraction where independent sources assert the same claim type
    - predicted_vs_actual_gap: difference between confidence and replication rate

    Also returns:
    - brier_score: overall calibration metric (0=perfect, lower is better)
    - plot_data: arrays suitable for charting predicted vs actual calibration curves
    - recalibration_suggestions: actionable advice for bins where confidence diverges from evidence
    """
    return await generate_calibration_curves()


# =========================================================================
# M5 Bayesian Evidence Calibration — back-tests convergence vs drug outcomes
# =========================================================================

@router.get("/calibration/bayesian/report")
async def bayesian_report():
    """Full Bayesian evidence calibration report.

    Back-tests convergence scores against known drug outcomes (approved,
    failed, ongoing) from the drug_outcomes table. Returns calibration
    percentage, grade, separation score, rank correlation, Brier score,
    and calibration curve data.

    This is the primary endpoint for measuring how well the platform's
    5-dimension convergence scoring predicts real-world drug success.
    """
    try:
        return await get_bayesian_calibration_report()
    except Exception as e:
        logger.error("Bayesian calibration report failed: %s", e, exc_info=True)
        raise HTTPException(500, detail="Calibration report failed: %s" % str(e))


@router.get("/calibration/bayesian/outcomes")
async def bayesian_outcomes():
    """Compare convergence scores of approved vs failed drugs.

    Groups drug outcomes by type (success, failure, ongoing) and computes
    mean/median convergence scores per group. Measures separation between
    approved and failed drugs, rank correlation, and prediction accuracy.
    """
    try:
        return await calibrate_against_outcomes()
    except Exception as e:
        logger.error("Outcome calibration failed: %s", e, exc_info=True)
        raise HTTPException(500, detail="Outcome calibration failed: %s" % str(e))


@router.get("/calibration/bayesian/curve")
async def bayesian_curve():
    """Calibration curve: convergence score bins vs actual drug success rates.

    Bins drug outcomes by their target's convergence score (0-0.2, 0.2-0.4, etc.)
    and computes the actual success rate in each bin. A well-calibrated system
    shows increasing success rates in higher convergence bins. Also returns
    Brier score and plot-ready data arrays.
    """
    try:
        return await bayesian_calibration_curve()
    except Exception as e:
        logger.error("Calibration curve failed: %s", e, exc_info=True)
        raise HTTPException(500, detail="Calibration curve failed: %s" % str(e))


@router.get("/calibration/bayesian/validate/{target_symbol}")
async def bayesian_validate_target(target_symbol: str):
    """Validate a specific target's convergence score against its drug outcomes.

    For the given target, compares the convergence score with the actual
    success/failure rate of drugs targeting it. Returns calibration gap,
    verdict (well_calibrated / overconfident / underconfident), and
    per-compound outcome details.
    """
    try:
        result = await validate_target_score(target_symbol)
        if result.get("status") == "not_found":
            raise HTTPException(404, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Target validation failed for %s: %s", target_symbol, e, exc_info=True)
        raise HTTPException(500, detail="Target validation failed: %s" % str(e))

# =========================================================================
# M5 Uncertainty Quantification -- Wilson score CI + uncertainty grades
# =========================================================================

@router.get("/calibration/uncertainty")
async def uncertainty_report():
    """Full uncertainty quantification report for all targets.

    Computes Wilson score confidence intervals on the support ratio
    (fraction of high-confidence claims) for every target with >= 3 claims.
    Combines CI tightness, source diversity, and temporal stability into
    a composite certainty score with A-D grading.

    Returns per-target uncertainty bands, platform summary, and the
    highest/lowest certainty predictions.
    """
    try:
        return await uq_get_report()
    except Exception as e:
        logger.error("Uncertainty report failed: %s", e, exc_info=True)
        raise HTTPException(500, detail="Uncertainty report failed: %s" % str(e))


@router.get("/calibration/uncertainty/{target_symbol}")
async def uncertainty_target(target_symbol: str):
    """Uncertainty quantification for a single target.

    Returns:
    - Support ratio with 95% Wilson CI (lower, upper)
    - Claim counts: support / oppose / neutral
    - Source diversity (unique labs)
    - Temporal stability (recency, growth)
    - Composite certainty score and A-D grade
    - Contributing factor breakdown
    """
    try:
        result = await uq_compute_target(target_symbol)
        if "error" in result and "not found" in result.get("error", "").lower():
            raise HTTPException(404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Uncertainty computation failed for %s: %s", target_symbol, e, exc_info=True)
        raise HTTPException(500, detail="Uncertainty computation failed: %s" % str(e))

# =========================================================================
# A4 Prospective Backtesting — would our predictions have been right?
# =========================================================================

@router.get("/calibration/backtest")
async def backtest_lookback(
    months: int = Query(
        default=6,
        ge=1,
        le=60,
        description="Lookback period in months. The cutoff date is NOW minus this many months.",
    ),
):
    """Run a prospective backtest with the given lookback period.

    Simulates running the convergence engine at (now - months) and compares
    what it would have predicted against outcomes discovered since then.

    Example: GET /calibration/backtest?months=6
    Simulates: "If we had scored targets 6 months ago, would the top-ranked
    targets have had positive outcomes since then?"

    Returns: prediction accuracy, precision@5, precision@10, rank correlation,
    per-target matched predictions, and interpretation.
    """
    try:
        now = datetime.now(timezone.utc)
        cutoff = now - relativedelta(months=months)
        result = await compare_predictions_to_outcomes(cutoff, now)
        return result
    except Exception as e:
        logger.error("Backtest (months=%d) failed: %s", months, e, exc_info=True)
        raise HTTPException(500, detail="Backtest failed: %s" % str(e))


@router.get("/calibration/backtest/temporal")
async def backtest_temporal(
    step_months: int = Query(
        default=3,
        ge=1,
        le=24,
        description="Months between each backtest timepoint.",
    ),
):
    """Full temporal backtest curve.

    Automatically determines the data range and runs backtests at multiple
    timepoints (every step_months months). Shows how predictive accuracy
    evolves over time as more evidence accumulates.

    Returns: per-timepoint accuracy, temporal accuracy curve, rank stability
    for each target, and an overall grade (A-D).
    """
    try:
        result = await get_backtest_report()
        return result
    except Exception as e:
        logger.error("Temporal backtest failed: %s", e, exc_info=True)
        raise HTTPException(500, detail="Temporal backtest failed: %s" % str(e))


@router.get("/calibration/backtest/report")
async def backtest_full_report():
    """Full prospective backtest report (alias for /backtest/temporal).

    Comprehensive assessment including: temporal accuracy curve, midpoint
    comparison, recent predictions, rank stability, and overall grade.
    This is the primary endpoint for audit item A4.
    """
    try:
        return await get_backtest_report()
    except Exception as e:
        logger.error("Backtest report failed: %s", e, exc_info=True)
        raise HTTPException(500, detail="Backtest report failed: %s" % str(e))


@router.get("/calibration/backtest/at/{cutoff_date}")
async def backtest_at_date(cutoff_date: str):
    """Run convergence scoring at a specific historical cutoff date.

    Simulates what the convergence engine would have produced if run
    at the given date, using only claims created before that date.

    Path parameter: cutoff_date in YYYY-MM-DD format.

    Returns: ranked targets with convergence scores, claim counts,
    and dimension breakdowns.
    """
    try:
        cutoff = datetime.strptime(cutoff_date, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        raise HTTPException(
            400, detail="Invalid date format. Use YYYY-MM-DD."
        )

    try:
        result = await backtest_at_cutoff(cutoff)
        return result
    except Exception as e:
        logger.error("Backtest at %s failed: %s", cutoff_date, e, exc_info=True)
        raise HTTPException(500, detail="Backtest failed: %s" % str(e))

