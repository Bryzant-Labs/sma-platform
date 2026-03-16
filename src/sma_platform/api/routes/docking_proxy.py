"""ML Docking Proxy API — fast surrogate screening endpoints.

Exposes the trained DiffDock proxy model for high-throughput virtual
screening.  The proxy predicts docking confidence ~1000x faster than
running DiffDock, enabling billion-molecule screening campaigns.

Endpoints
---------
POST /proxy/train    (admin)  — Train/retrain model on DiffDock results
POST /proxy/predict           — Predict single compound
POST /proxy/batch             — Batch predict (the fast screening step)
GET  /proxy/info              — Model stats and accuracy
POST /proxy/generate  (admin) — Generate random drug-like SMILES
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...reasoning.docking_proxy import (
    SMA_TARGETS,
    batch_predict,
    generate_random_smiles,
    get_model_info,
    predict_docking,
    train_proxy_model,
)
from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class PredictRequest(BaseModel):
    smiles: str = Field(..., description="SMILES string of the compound")
    target: str = Field(
        default="SMN2",
        description=f"SMA target protein. One of: {', '.join(SMA_TARGETS)}",
    )


class CompoundEntry(BaseModel):
    smiles: str = Field(..., description="SMILES string")
    name: str = Field(default="", description="Optional compound name/ID")


class BatchRequest(BaseModel):
    compounds: list[CompoundEntry] = Field(
        ..., description="List of compounds to screen", min_length=1, max_length=100_000,
    )
    target: str = Field(
        default="SMN2",
        description=f"SMA target protein. One of: {', '.join(SMA_TARGETS)}",
    )


class GenerateRequest(BaseModel):
    n: int = Field(
        default=10000,
        ge=1,
        le=1_000_000,
        description="Number of random SMILES to generate",
    )
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility",
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/proxy/train",
    dependencies=[Depends(require_admin_key)],
    summary="Train the ML docking proxy model",
)
async def train_proxy():
    """Train or retrain the proxy model on all available DiffDock results.

    Loads results from gpu/results/ (v1, multi-target, NIM batch),
    extracts SMILES features, and trains a GradientBoosting or k-NN model.

    Returns accuracy metrics (R², MAE), feature importances, and
    cross-validation scores.
    """
    try:
        result = await train_proxy_model()
        if "error" in result:
            raise HTTPException(400, result["error"])
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Proxy training failed: %s", exc, exc_info=True)
        raise HTTPException(500, f"Training failed: {exc}")


@router.post(
    "/proxy/predict",
    summary="Predict docking confidence for one compound",
)
async def predict_single(body: PredictRequest):
    """Predict DiffDock confidence for a single compound-target pair.

    ~1000x faster than running DiffDock (microseconds vs minutes).
    Returns predicted confidence score, uncertainty estimate, and
    binding interpretation.
    """
    try:
        result = await predict_docking(body.smiles, body.target)
        if "error" in result:
            raise HTTPException(400, result["error"])
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Proxy prediction failed: %s", exc, exc_info=True)
        raise HTTPException(500, f"Prediction failed: {exc}")


@router.post(
    "/proxy/batch",
    summary="Batch predict docking confidence (fast screening)",
)
async def predict_batch(body: BatchRequest):
    """Predict DiffDock confidence for many compounds at once.

    This is the core fast screening endpoint. Processes thousands of
    compounds in milliseconds where DiffDock would take days.
    Results are sorted by predicted confidence (best first).
    """
    try:
        compounds = [{"smiles": c.smiles, "name": c.name} for c in body.compounds]
        result = await batch_predict(compounds, body.target)
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(400, result["error"])
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Batch prediction failed: %s", exc, exc_info=True)
        raise HTTPException(500, f"Batch prediction failed: {exc}")


@router.get(
    "/proxy/info",
    summary="Get proxy model info and accuracy metrics",
)
async def proxy_info():
    """Return model statistics, training data info, and accuracy metrics.

    Includes R², MAE, feature importances, cross-validation scores,
    and training data distribution.
    """
    try:
        return await get_model_info()
    except Exception as exc:
        logger.error("Failed to get model info: %s", exc, exc_info=True)
        raise HTTPException(500, f"Failed to get model info: {exc}")


@router.post(
    "/proxy/generate",
    dependencies=[Depends(require_admin_key)],
    summary="Generate random drug-like SMILES",
)
async def generate_smiles(body: GenerateRequest):
    """Generate N random drug-like SMILES strings using a character-level
    Markov chain trained on the screening library.

    Uses three strategies: scaffold+substituent decoration,
    dual-fragment linking, and pure Markov generation.

    These generated SMILES can be fed into /proxy/batch for
    high-throughput virtual screening.
    """
    try:
        smiles_list = generate_random_smiles(n=body.n, seed=body.seed)
        return {
            "generated": len(smiles_list),
            "requested": body.n,
            "seed": body.seed,
            "smiles": smiles_list,
            "next_step": "POST /api/v2/proxy/batch with these SMILES to screen against a target",
        }
    except Exception as exc:
        logger.error("SMILES generation failed: %s", exc, exc_info=True)
        raise HTTPException(500, f"Generation failed: {exc}")
