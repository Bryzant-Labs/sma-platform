"""Confidence Calibration API routes.

Back-tests scoring models against known SMA drug approvals to measure
how well our predictions and hypotheses align with established biology.
Also provides calibration curves showing predicted confidence vs actual
replication rate across all claims.

M5 Bayesian Evidence Calibration endpoints back-test convergence scores
against known drug outcomes (approved vs failed) from the drug_outcomes table.

M5 Uncertainty Quantification endpoints provide Wilson score confidence
intervals and uncertainty grades (A-D) for every target prediction.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

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
