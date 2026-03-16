"""Confidence Calibration API routes.

Back-tests scoring models against known SMA drug approvals to measure
how well our predictions and hypotheses align with established biology.
"""

from __future__ import annotations

from fastapi import APIRouter

from ...reasoning.confidence_calibrator import (
    calibrate_hypotheses,
    calibrate_predictions,
    get_calibration_report,
)

router = APIRouter()


@router.get("/calibration/report")
async def calibration_report():
    """Full confidence calibration report.

    Evaluates both synergy predictions and hypothesis confidence scores
    against the 3 approved SMA drugs (nusinersen, risdiplam, onasemnogene)
    and their validated targets (SMN1, SMN2).

    Returns an overall grade (A-D), per-system metrics, and interpretation.
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
