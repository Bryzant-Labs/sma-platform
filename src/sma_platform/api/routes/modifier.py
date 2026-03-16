"""Modifier-Aware Phenotype Prediction API routes.

Predicts SMA phenotype severity from SMN2 copy number + modifier gene status.
Evidence-based rules from published discordant family studies and functional
genomics (PLS3, NCALD, NAIP, SERF1, GTF2H2, CORO1C).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ...reasoning.modifier_predictor import (
    MODIFIERS,
    VALID_LEVELS,
    get_modifier_evidence,
    get_modifier_factors,
    predict_phenotype,
)

router = APIRouter()

# Modifier gene symbols accepted as query parameters
_MODIFIER_PARAMS = {sym.lower() for sym in MODIFIERS}


@router.get("/modifier/predict")
async def modifier_predict(
    smn2_copies: int = Query(..., ge=0, le=8, description="Number of SMN2 gene copies (0-8)"),
    pls3: str | None = Query(default=None, description="PLS3 expression level: high, low, normal, absent"),
    ncald: str | None = Query(default=None, description="NCALD expression level: high, low, normal, absent"),
    naip: str | None = Query(default=None, description="NAIP status: high, normal, low, absent/deleted"),
    serf1: str | None = Query(default=None, description="SERF1 expression level: high, low, normal"),
    gtf2h2: str | None = Query(default=None, description="GTF2H2 expression level: high, low, normal"),
    coro1c: str | None = Query(default=None, description="CORO1C expression level: high, low, normal"),
):
    """Predict SMA phenotype severity from SMN2 copies and modifier gene status.

    Example: `/modifier/predict?smn2_copies=3&pls3=high&ncald=low`

    Returns predicted SMA type, severity score (0-1), confidence level,
    contributing factors for each modifier, and evidence summary with PMIDs.
    """
    # Build modifiers dict from query params
    modifiers: dict[str, str] = {}
    param_map = {
        "PLS3": pls3,
        "NCALD": ncald,
        "NAIP": naip,
        "SERF1": serf1,
        "GTF2H2": gtf2h2,
        "CORO1C": coro1c,
    }
    for symbol, value in param_map.items():
        if value is not None:
            value = value.strip().lower()
            if value not in VALID_LEVELS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid level '{value}' for {symbol}. "
                           f"Must be one of: {', '.join(sorted(VALID_LEVELS))}",
                )
            modifiers[symbol] = value

    try:
        result = await predict_phenotype(smn2_copies, modifiers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {type(e).__name__}",
        )

    return result


@router.get("/modifier/factors")
async def modifier_factors():
    """Return all known SMA modifier genes with evidence and effect details.

    Lists PLS3, NCALD, NAIP, SERF1, GTF2H2, CORO1C with their mechanisms,
    published PMIDs, magnitude of effect, and database claim counts.
    """
    factors = await get_modifier_factors()
    return {
        "total_modifiers": len(factors),
        "modifiers": factors,
        "valid_expression_levels": sorted(VALID_LEVELS),
        "insight": "PLS3 and NCALD are the strongest characterized protective modifiers, "
                   "discovered through discordant SMA families. NAIP deletion on 5q13 is "
                   "the best-known severity-worsening modifier. CORO1C is a computational "
                   "prediction only — no clinical validation yet.",
    }


@router.get("/modifier/evidence/{symbol}")
async def modifier_evidence(symbol: str):
    """Get all evidence supporting a specific modifier gene's role in SMA.

    Returns published literature references (PMIDs), mechanism details,
    and any related claims from the database.
    """
    result = await get_modifier_evidence(symbol)

    if not result.get("known", False):
        raise HTTPException(
            status_code=404,
            detail=result.get("error", f"Modifier '{symbol}' not found"),
        )

    return result
