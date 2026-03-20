"""Organoid/NMJ Validation Scorecard — which predictions are testable?

Evaluates computational predictions against available model systems:
iPSC-derived motor neurons, NMJ organoids, muscle organoids, mouse models.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Available SMA model systems with capabilities
MODEL_SYSTEMS = [
    {
        "name": "iPSC-derived motor neurons",
        "abbreviation": "iPSC-MN",
        "source": "SMA patient fibroblasts → iPSC → motor neuron differentiation",
        "strengths": ["Human cells", "Patient-specific", "Scalable", "Rapid (4-6 weeks)"],
        "limitations": ["2D culture", "No NMJ context", "Maturity concerns"],
        "testable_endpoints": [
            "cell_survival", "smn_levels", "axon_length",
            "gene_expression", "protein_levels", "splicing",
        ],
        "cost_range": "$5K-15K",
        "timeline": "4-6 weeks",
    },
    {
        "name": "NMJ organoid (motor neuron + muscle co-culture)",
        "abbreviation": "NMJ-org",
        "source": "iPSC-MN + skeletal myotubes in 3D culture",
        "strengths": ["Functional NMJ", "Contractility readout", "Human cells"],
        "limitations": ["Complex protocol", "Variable", "Low throughput"],
        "testable_endpoints": [
            "nmj_formation", "muscle_contraction", "synapse_function",
            "axon_length", "cell_survival",
        ],
        "cost_range": "$15K-30K",
        "timeline": "8-12 weeks",
    },
    {
        "name": "SMA mouse model (SMNΔ7 or Smn2B/-)",
        "abbreviation": "Mouse",
        "source": "Transgenic SMA mice",
        "strengths": ["In vivo", "Full organ system", "Established"],
        "limitations": ["Species differences", "Expensive", "Ethics"],
        "testable_endpoints": [
            "survival", "motor_function", "nmj_morphology",
            "muscle_mass", "biomarkers", "drug_pharmacokinetics",
        ],
        "cost_range": "$20K-50K",
        "timeline": "12-20 weeks",
    },
    {
        "name": "SMA patient fibroblasts",
        "abbreviation": "Fibro",
        "source": "Skin biopsy from SMA patients",
        "strengths": ["Easy to obtain", "Cheap", "Fast"],
        "limitations": ["Not neuronal", "Limited disease modeling"],
        "testable_endpoints": [
            "smn_levels", "splicing", "gene_expression", "drug_screening",
        ],
        "cost_range": "$2K-5K",
        "timeline": "2-4 weeks",
    },
]

# Map target types to best model systems
TARGET_MODEL_MAP: dict[str, list[str]] = {
    "SMN2": ["Fibro", "iPSC-MN", "Mouse"],
    "SMN1": ["iPSC-MN", "Mouse"],
    "STMN2": ["iPSC-MN", "NMJ-org"],
    "PLS3": ["iPSC-MN", "NMJ-org"],
    "NCALD": ["iPSC-MN", "Mouse"],
    "UBA1": ["iPSC-MN", "Fibro"],
    "CORO1C": ["iPSC-MN"],
    "TP53": ["iPSC-MN", "Mouse"],
    "NMJ_MATURATION": ["NMJ-org", "Mouse"],
    "MTOR_PATHWAY": ["iPSC-MN", "Fibro"],
}

# Prediction type → relevant functional endpoints
_PREDICTION_ENDPOINTS: dict[str, list[str]] = {
    "binding": ["drug_screening", "protein_levels", "cell_survival"],
    "expression": ["gene_expression", "smn_levels", "splicing"],
    "function": ["nmj_formation", "muscle_contraction", "motor_function"],
}


def score_testability(
    target: str,
    prediction_type: str = "binding",
) -> dict[str, Any]:
    """Score how testable a prediction is in available model systems.

    Args:
        target: Gene/pathway name (e.g. "SMN2", "CORO1C").
        prediction_type: One of "binding", "expression", "function".

    Returns:
        Dict with overall testability score, recommended models, and verdict.
    """
    models = TARGET_MODEL_MAP.get(target.upper(), ["iPSC-MN"])
    relevant_endpoints = _PREDICTION_ENDPOINTS.get(prediction_type)

    best_models: list[dict[str, Any]] = []
    for m in MODEL_SYSTEMS:
        if m["abbreviation"] not in models:
            continue

        if relevant_endpoints is not None:
            overlap = len(set(relevant_endpoints) & set(m["testable_endpoints"]))
            score = overlap / max(len(relevant_endpoints), 1)
        else:
            # Unknown prediction type — all endpoints count
            score = 1.0

        best_models.append({
            "model": m["name"],
            "abbreviation": m["abbreviation"],
            "testability_score": round(score, 2),
            "relevant_endpoints": sorted(
                set(relevant_endpoints or m["testable_endpoints"])
                & set(m["testable_endpoints"])
            ),
            "cost": m["cost_range"],
            "timeline": m["timeline"],
        })

    best_models.sort(key=lambda x: x["testability_score"], reverse=True)

    overall = max((m["testability_score"] for m in best_models), default=0)

    if overall >= 0.6:
        verdict = "Highly testable"
    elif overall >= 0.3:
        verdict = "Testable"
    else:
        verdict = "Difficult to test"

    return {
        "target": target,
        "prediction_type": prediction_type,
        "overall_testability": round(overall, 2),
        "recommended_models": best_models,
        "verdict": verdict,
    }


def score_all_targets() -> list[dict[str, Any]]:
    """Score testability for all known targets across prediction types."""
    results: list[dict[str, Any]] = []
    for target in TARGET_MODEL_MAP:
        s = score_testability(target, "binding")
        results.append(s)
    results.sort(key=lambda x: x["overall_testability"], reverse=True)
    return results
