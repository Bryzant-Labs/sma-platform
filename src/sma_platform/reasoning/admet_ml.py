"""ML-based ADMET prediction using ADMET-AI.

Adds deep learning ADMET predictions (41 endpoints from Therapeutics Data Commons)
on top of the existing RDKit rule-based predictions in admet_predictor.py.

ADMET-AI uses Chemprop-RDKit models trained on experimental data.
Install: pip install admet-ai

References:
- Swanson et al., 2024 (Bioinformatics, btae416)
- Therapeutics Data Commons (TDC) benchmarks
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_model = None
_available = None


def _ensure_admet_ai() -> bool:
    """Check if admet-ai is installed and load the model."""
    global _model, _available
    if _available is not None:
        return _available
    try:
        from admet_ai import ADMETModel
        _model = ADMETModel()
        _available = True
        logger.info("ADMET-AI model loaded successfully")
        return True
    except ImportError:
        logger.warning("admet-ai not installed — ML ADMET predictions unavailable. Install: pip install admet-ai")
        _available = False
        return False
    except Exception as e:
        logger.error("Failed to load ADMET-AI model: %s", e)
        _available = False
        return False


def predict_admet_ml(smiles: str) -> dict[str, Any] | None:
    """Predict ADMET properties for a single SMILES using ML models.

    Returns dict mapping property names to predicted values,
    or None if ADMET-AI is not available or SMILES is invalid.
    """
    if not _ensure_admet_ai():
        return None

    try:
        preds = _model.predict(smiles=smiles)
        if preds is None:
            return None
        # Convert any numpy types to Python natives for JSON serialization
        return {k: float(v) if hasattr(v, 'item') else v for k, v in preds.items()}
    except Exception as e:
        logger.debug("ADMET-AI prediction failed for %s: %s", smiles, e)
        return None


def predict_admet_ml_batch(smiles_list: list[str]) -> list[dict[str, Any]]:
    """Predict ADMET properties for a batch of SMILES strings.

    Returns list of dicts (one per SMILES). Invalid SMILES get None entries.
    """
    if not _ensure_admet_ai() or not smiles_list:
        return []

    try:
        import pandas as pd
        df = _model.predict(smiles=smiles_list)
        if df is None or df.empty:
            return []

        results = []
        for idx, row in df.iterrows():
            entry = {"smiles": str(idx)}
            for col in df.columns:
                val = row[col]
                if hasattr(val, 'item'):
                    entry[col] = float(val)
                elif isinstance(val, float) and val != val:  # NaN check
                    entry[col] = None
                else:
                    entry[col] = val
            results.append(entry)
        return results
    except Exception as e:
        logger.error("ADMET-AI batch prediction failed: %s", e)
        return []


# Key ADMET-AI property categories for interpretation
PROPERTY_CATEGORIES = {
    "absorption": [
        "Caco2_Wang", "HIA_Hou", "Pgp_Broccatelli", "Bioavailability_Ma",
        "PAMPA_NCATS", "Solubility_AqSolDB",
    ],
    "distribution": [
        "BBB_Martins", "PPBR_AZ", "VDss_Lombardo",
    ],
    "metabolism": [
        "CYP1A2_Veith", "CYP2C19_Veith", "CYP2C9_Veith",
        "CYP2D6_Veith", "CYP3A4_Veith", "CYP2C9_Substrate_CarbonMangels",
        "CYP2D6_Substrate_CarbonMangels", "CYP3A4_Substrate_CarbonMangels",
    ],
    "excretion": [
        "Half_Life_Obach", "Clearance_Hepatocyte_AZ", "Clearance_Microsome_AZ",
    ],
    "toxicity": [
        "hERG", "AMES", "DILI", "LD50_Zhu", "Skin_Reaction",
        "Carcinogens_Lagunin", "ClinTox",
    ],
}


def categorize_predictions(preds: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Organize raw ADMET-AI predictions into ADMET categories.

    Returns dict with keys: absorption, distribution, metabolism, excretion, toxicity, other.
    Each value is a dict of property_name → value.
    """
    categorized: dict[str, dict[str, Any]] = {
        "absorption": {},
        "distribution": {},
        "metabolism": {},
        "excretion": {},
        "toxicity": {},
        "other": {},
    }

    known = set()
    for cat, props in PROPERTY_CATEGORIES.items():
        for prop in props:
            known.add(prop)
            if prop in preds:
                categorized[cat][prop] = preds[prop]

    for k, v in preds.items():
        if k not in known and k != "smiles":
            categorized["other"][k] = v

    return categorized


def compute_druglikeness_summary(preds: dict[str, Any]) -> dict[str, Any]:
    """Compute a summary of drug-likeness from ADMET-AI predictions.

    Returns interpretive summary with traffic-light ratings.
    """
    summary = {
        "overall_rating": "unknown",
        "flags": [],
        "strengths": [],
    }

    # BBB penetration (critical for CNS drugs like SMA therapeutics)
    bbb = preds.get("BBB_Martins")
    if bbb is not None:
        if bbb > 0.7:
            summary["strengths"].append("BBB permeable (ML predicted)")
        elif bbb < 0.3:
            summary["flags"].append("Poor BBB penetration (ML predicted)")

    # hERG liability
    herg = preds.get("hERG")
    if herg is not None:
        if herg > 0.5:
            summary["flags"].append("hERG liability risk")

    # AMES mutagenicity
    ames = preds.get("AMES")
    if ames is not None:
        if ames > 0.5:
            summary["flags"].append("AMES mutagenicity risk")

    # Drug-induced liver injury
    dili = preds.get("DILI")
    if dili is not None:
        if dili > 0.5:
            summary["flags"].append("Hepatotoxicity risk (DILI)")

    # Bioavailability
    bioavail = preds.get("Bioavailability_Ma")
    if bioavail is not None:
        if bioavail > 0.7:
            summary["strengths"].append("Good oral bioavailability")
        elif bioavail < 0.3:
            summary["flags"].append("Poor oral bioavailability")

    # HIA
    hia = preds.get("HIA_Hou")
    if hia is not None:
        if hia > 0.7:
            summary["strengths"].append("Good intestinal absorption")

    # Overall rating
    n_flags = len(summary["flags"])
    n_strengths = len(summary["strengths"])
    if n_flags == 0 and n_strengths >= 2:
        summary["overall_rating"] = "favorable"
    elif n_flags <= 1 and n_strengths >= 1:
        summary["overall_rating"] = "moderate"
    elif n_flags >= 2:
        summary["overall_rating"] = "concerning"
    else:
        summary["overall_rating"] = "moderate"

    return summary
