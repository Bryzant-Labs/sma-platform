"""Confidence Calibration API routes.

Back-tests scoring models against known SMA drug approvals to measure
how well our predictions and hypotheses align with established biology.
Also provides calibration curves showing predicted confidence vs actual
replication rate across all claims.
"""

from __future__ import annotations

from fastapi import APIRouter

from ...reasoning.confidence_calibrator import (
    calibrate_hypotheses,
    calibrate_predictions,
    generate_calibration_curves,
    get_calibration_report,
)

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
