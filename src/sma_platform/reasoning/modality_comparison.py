"""Therapeutic Modality Comparison — Small Molecule vs ASO vs CRISPR vs Gene Therapy.

For each SMA target, compare the feasibility, pros/cons, and current status
of different therapeutic approaches.
"""

from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)

MODALITIES = {
    "small_molecule": {
        "name": "Small Molecule",
        "pros": ["Oral dosing possible", "BBB penetration (some)", "Cheap to manufacture", "Reversible"],
        "cons": ["Off-target effects", "Limited to druggable pockets", "Requires chronic dosing"],
        "examples_sma": ["Risdiplam (Evrysdi)", "Branaplam (discontinued)"],
        "development_time": "8-12 years",
        "cost_per_patient_year": "$100K-350K",
    },
    "aso": {
        "name": "Antisense Oligonucleotide (ASO)",
        "pros": ["Sequence-specific", "Proven in SMA", "Long duration (months)"],
        "cons": ["Intrathecal delivery required", "Repeat dosing", "Manufacturing cost"],
        "examples_sma": ["Nusinersen (Spinraza)"],
        "development_time": "6-10 years",
        "cost_per_patient_year": "$375K-750K",
    },
    "gene_therapy": {
        "name": "AAV Gene Therapy",
        "pros": ["One-time treatment", "Targets root cause", "Durable expression"],
        "cons": ["Immune response", "Dosing limited by age/weight", "Extremely expensive"],
        "examples_sma": ["Onasemnogene (Zolgensma)"],
        "development_time": "8-15 years",
        "cost_per_patient_year": "$2.1M (one-time)",
    },
    "crispr": {
        "name": "CRISPR/Prime Editing",
        "pros": ["Permanent correction", "Highly specific", "One-time"],
        "cons": ["Off-target edits", "Delivery challenge", "Unproven in CNS"],
        "examples_sma": ["Preclinical only — ISS-N1 disruption, ESE strengthening"],
        "development_time": "10-20 years",
        "cost_per_patient_year": "Unknown (preclinical)",
    },
    "protein_binder": {
        "name": "Designed Protein Binder",
        "pros": ["High specificity", "Novel mechanism", "Targetable interfaces"],
        "cons": ["Delivery challenge", "Immunogenicity", "Unproven modality"],
        "examples_sma": ["Proteina-Complexa designs (computational)"],
        "development_time": "15+ years",
        "cost_per_patient_year": "Unknown",
    },
}

# Which modalities are applicable per target
TARGET_MODALITIES = {
    "SMN2": ["small_molecule", "aso", "crispr"],
    "SMN1": ["gene_therapy", "crispr"],
    "STMN2": ["small_molecule", "aso"],
    "PLS3": ["small_molecule", "gene_therapy"],
    "NCALD": ["aso", "small_molecule"],
    "UBA1": ["small_molecule", "protein_binder"],
    "CORO1C": ["small_molecule", "protein_binder"],
    "TP53": ["small_molecule"],
    "NMJ_MATURATION": ["small_molecule"],
    "MTOR_PATHWAY": ["small_molecule"],
}


def compare_modalities_for_target(target: str) -> dict[str, Any]:
    """Compare therapeutic modalities for a specific SMA target."""
    target_upper = target.upper()
    applicable = TARGET_MODALITIES.get(target_upper, ["small_molecule"])

    comparisons = []
    for mod_key in applicable:
        mod = MODALITIES.get(mod_key, {})
        # Score feasibility
        if mod_key in ("small_molecule", "aso"):
            feasibility = 0.8
        elif mod_key == "gene_therapy":
            feasibility = 0.7
        elif mod_key == "crispr":
            feasibility = 0.3
        else:
            feasibility = 0.2

        comparisons.append({
            "modality": mod.get("name", mod_key),
            "key": mod_key,
            "feasibility": feasibility,
            "pros": mod.get("pros", []),
            "cons": mod.get("cons", []),
            "examples": mod.get("examples_sma", []),
            "timeline": mod.get("development_time", "Unknown"),
            "cost": mod.get("cost_per_patient_year", "Unknown"),
        })

    comparisons.sort(key=lambda x: x["feasibility"], reverse=True)

    return {
        "target": target_upper,
        "modalities": comparisons,
        "recommended": comparisons[0]["modality"] if comparisons else None,
        "total_options": len(comparisons),
    }


def compare_all_targets() -> list[dict]:
    """Compare modalities for all targets."""
    results = []
    for target in TARGET_MODALITIES:
        r = compare_modalities_for_target(target)
        results.append(r)
    return results
