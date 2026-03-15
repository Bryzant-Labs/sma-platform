"""AAV capsid evaluation endpoints (Phase 6.3)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from ...reasoning.aav_evaluator import (
    CARGO_SIZES,
    evaluate_capsids,
    get_capsid_details,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/aav/evaluate")
async def evaluate_aav_capsids(
    cargo: str = Query(
        default="SMN1_cDNA",
        description="Cargo type to evaluate packaging feasibility",
    ),
):
    """Evaluate AAV capsids for SMA gene therapy delivery.

    Ranks 9 AAV serotypes by composite suitability score considering:
    motor neuron tropism, BBB crossing, immunogenicity, manufacturing, and packaging.

    Cargo options: SMN1_cDNA, SMN1_full_length, dCas9_CRISPRi,
    dual_vector_dCas9, base_editor_ABE, prime_editor, micro_dystrophin
    """
    if cargo not in CARGO_SIZES:
        raise HTTPException(
            400,
            f"Unknown cargo: {cargo}. Available: {', '.join(CARGO_SIZES.keys())}",
        )
    return evaluate_capsids(cargo)


@router.get("/aav/capsid/{serotype}")
async def get_capsid(serotype: str):
    """Get detailed evaluation for a specific AAV serotype.

    Returns tropism, immunogenicity, clinical precedent, and
    packaging feasibility for all cargo types.
    """
    result = get_capsid_details(serotype)
    if result is None:
        raise HTTPException(404, f"AAV serotype '{serotype}' not found")
    return result


@router.get("/aav/cargos")
async def list_cargo_types():
    """List all therapeutic cargo types with sizes and genome configurations."""
    return {
        "cargos": {k: v for k, v in CARGO_SIZES.items()},
        "packaging_limits": {
            "self_complementary_kb": 2.3,
            "single_stranded_kb": 4.7,
        },
    }
