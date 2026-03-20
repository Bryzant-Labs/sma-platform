"""ML Docking Proxy v2 API -- fast surrogate screening with Morgan fingerprints.

Exposes the trained DiffDock proxy model v2 for high-throughput virtual
screening.  The proxy predicts docking confidence ~1000x faster than
running DiffDock, enabling million-molecule screening campaigns.

v2 upgrade: Uses RDKit Morgan fingerprints (ECFP4, 2048-bit) instead of
12 SMILES string-level features. Trained on 4,116 DiffDock v2.2 results.

Endpoints
---------
POST /ml-proxy/train             (admin)  -- Train/retrain model on DiffDock results
POST /ml-proxy/predict                    -- Predict binding for a list of SMILES
GET  /ml-proxy/status                     -- Model status, training metrics, scatter data
POST /ml-proxy/screen-library    (admin)  -- Screen the full ChEMBL library, return top hits
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...reasoning.ml_docking_proxy import (
    SMA_TARGETS,
    get_model_status,
    predict_binding,
    screen_chembl_library,
    train_proxy_model,
)
from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class MLProxyPredictRequest(BaseModel):
    smiles: list[str] = Field(
        ...,
        description="List of SMILES strings to predict binding for",
        min_length=1,
        max_length=100_000,
    )
    target: str = Field(
        default="SMN2",
        description=f"SMA target protein. One of: {', '.join(SMA_TARGETS)}",
    )


class MLProxyScreenRequest(BaseModel):
    target: str = Field(
        default="SMN2",
        description=f"SMA target protein. One of: {', '.join(SMA_TARGETS)}",
    )
    top_k: int = Field(
        default=1000,
        ge=10,
        le=10_000,
        description="Number of top predicted binders to return",
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/ml-proxy/train",
    dependencies=[Depends(require_admin_key)],
    summary="Train the ML docking proxy v2 (Morgan fingerprints)",
)
async def train_ml_proxy():
    """Train or retrain the v2 proxy model on all available DiffDock results.

    Uses RDKit Morgan fingerprints (ECFP4, 2048-bit) + target one-hot encoding
    with a RandomForestRegressor (500 trees). Falls back to GradientBoosting
    with string features if RDKit is not available.

    Loads training data from:
    - gpu/results/10k_screen/diffdock_results.json (4,116 entries, primary)
    - gpu/results/nim_batch/diffdock_results.json (378 entries)
    - gpu/results/diffdock_multi_results.json (120 entries)
    - gpu/results/diffdock_results.json (20 entries)

    Returns accuracy metrics (R2, MAE, OOB R2), cross-validation scores,
    feature importances, and scatter plot data.
    """
    try:
        # train_proxy_model is sync (CPU-bound sklearn) -- run directly
        result = train_proxy_model()
        if "error" in result:
            raise HTTPException(400, result["error"])
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("ML proxy v2 training failed: %s", exc, exc_info=True)
        raise HTTPException(500, f"Training failed: {exc}")


@router.post(
    "/ml-proxy/predict",
    summary="Predict binding for a list of SMILES (ML proxy v2)",
)
async def predict_ml_proxy(body: MLProxyPredictRequest):
    """Predict DiffDock confidence for a batch of compounds.

    ~1000x faster than running DiffDock. Processes thousands of compounds
    in milliseconds where DiffDock would take days. Results are sorted by
    predicted confidence (best first).

    Uses Morgan fingerprints (ECFP4) for molecular representation --
    captures real molecular topology instead of simple character counting.
    """
    try:
        result = await predict_binding(None, body.smiles, body.target)
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(400, result["error"])
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("ML proxy v2 prediction failed: %s", exc, exc_info=True)
        raise HTTPException(500, f"Prediction failed: {exc}")


@router.get(
    "/ml-proxy/status",
    summary="Get ML proxy v2 model status and metrics",
)
async def ml_proxy_status():
    """Return model statistics, training data info, and accuracy metrics.

    Includes R2, MAE, OOB R2 (RandomForest), feature importances (top 20),
    cross-validation scores, target/source distributions, and scatter plot
    data (actual vs predicted DiffDock confidence).
    """
    try:
        return await get_model_status()
    except Exception as exc:
        logger.error("Failed to get ML proxy status: %s", exc, exc_info=True)
        raise HTTPException(500, f"Failed to get model status: {exc}")


@router.post(
    "/ml-proxy/screen-library",
    dependencies=[Depends(require_admin_key)],
    summary="Screen the full ChEMBL library with ML proxy v2",
)
async def screen_library(body: MLProxyScreenRequest):
    """Screen all compounds in the molecule_screenings DB table using the
    trained ML proxy. Returns the top-K predicted binders ranked by
    predicted DiffDock confidence.

    This enables screening the full library (thousands of compounds) in
    seconds instead of weeks with DiffDock. Each compound gets a predicted
    confidence score, uncertainty estimate, and binding interpretation.
    """
    try:
        result = await screen_chembl_library(None, body.target, body.top_k)
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(400, result["error"])
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("ML proxy library screening failed: %s", exc, exc_info=True)
        raise HTTPException(500, f"Library screening failed: {exc}")
