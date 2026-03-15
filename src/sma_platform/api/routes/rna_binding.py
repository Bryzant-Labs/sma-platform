"""RNA-Binding Prediction API routes (Phase 9.4)."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ...reasoning.rna_binding import (
    benchmark_compound,
    get_known_modulators,
    get_rna_targets,
    predict_compound_binding,
)

router = APIRouter()


class CompoundInput(BaseModel):
    name: str
    mw: float
    logp: float
    hba: int = 5
    hbd: int = 2
    aromatic_rings: int = 3
    rotatable_bonds: int = 4


@router.get("/rna/targets")
async def rna_targets():
    """Get all RNA target sites in SMN2."""
    return get_rna_targets()


@router.get("/rna/modulators")
async def known_modulators():
    """Get known RNA-binding SMN2 splicing modulators."""
    return get_known_modulators()


@router.post("/rna/predict")
async def predict_binding(body: CompoundInput):
    """Predict RNA-binding potential of a compound."""
    return predict_compound_binding(
        body.name, body.mw, body.logp, body.hba, body.hbd,
        body.aromatic_rings, body.rotatable_bonds,
    )


@router.post("/rna/benchmark")
async def benchmark(body: CompoundInput):
    """Benchmark a compound against known SMN2 modulators."""
    return benchmark_compound(
        body.name, body.mw, body.logp, body.hba, body.hbd,
        body.aromatic_rings, body.rotatable_bonds,
    )
