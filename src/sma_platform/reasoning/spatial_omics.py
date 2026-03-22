"""Spatial Multi-Omics Analysis for SMA (Phase 7.1) — PostgreSQL-backed.

Zones and drug penetration data are stored in:
  - spatial_zones          — anatomical compartment metadata
  - spatial_drug_penetration — per-drug zone access scores (JSONB)

The compute functions (_zone_accessibility, identify_silent_zones) still run
in Python so the live endpoint stays interactive for novel compounds. Approved
drugs use DB-cached scores; dynamic queries compute on-the-fly and optionally
persist results.

References:
- Blum et al., Nature 2021 (spinal cord single-cell atlas)
- Häggmark et al., Science 2016 (Human Protein Atlas spinal cord)
- Nichterwitz et al., Cell Reports 2016 (laser-captured MN transcriptomes)
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ..core.database import execute, fetch, fetchrow

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Target expression profiles (kept in-memory — no DB dependency needed)
# Expression levels: 0=absent, 0.3=low, 0.6=moderate, 0.9=high, 1.0=very high
# ---------------------------------------------------------------------------

TARGET_EXPRESSION = {
    "SMN1":           {"ventral_horn": 0.95, "dorsal_horn": 0.70, "central_canal": 0.50, "white_matter": 0.40, "drg": 0.60, "nmj": 0.30},
    "SMN2":           {"ventral_horn": 0.95, "dorsal_horn": 0.70, "central_canal": 0.50, "white_matter": 0.40, "drg": 0.60, "nmj": 0.30},
    "SMN_PROTEIN":    {"ventral_horn": 0.90, "dorsal_horn": 0.65, "central_canal": 0.45, "white_matter": 0.35, "drg": 0.55, "nmj": 0.25},
    "STMN2":          {"ventral_horn": 0.85, "dorsal_horn": 0.50, "central_canal": 0.20, "white_matter": 0.60, "drg": 0.70, "nmj": 0.15},
    "PLS3":           {"ventral_horn": 0.70, "dorsal_horn": 0.40, "central_canal": 0.30, "white_matter": 0.20, "drg": 0.35, "nmj": 0.80},
    "NCALD":          {"ventral_horn": 0.75, "dorsal_horn": 0.60, "central_canal": 0.40, "white_matter": 0.15, "drg": 0.50, "nmj": 0.20},
    "UBA1":           {"ventral_horn": 0.80, "dorsal_horn": 0.70, "central_canal": 0.60, "white_matter": 0.50, "drg": 0.65, "nmj": 0.40},
    "MTOR_PATHWAY":   {"ventral_horn": 0.85, "dorsal_horn": 0.75, "central_canal": 0.70, "white_matter": 0.50, "drg": 0.60, "nmj": 0.45},
    "NMJ_MATURATION": {"ventral_horn": 0.40, "dorsal_horn": 0.10, "central_canal": 0.05, "white_matter": 0.05, "drg": 0.10, "nmj": 1.00},
    "CORO1C":         {"ventral_horn": 0.30, "dorsal_horn": 0.25, "central_canal": 0.20, "white_matter": 0.15, "drg": 0.20, "nmj": 0.35},
}


# ---------------------------------------------------------------------------
# Drug penetration model (kept for dynamic / novel compound queries)
# ---------------------------------------------------------------------------

def _zone_accessibility(mw: float, logp: float, bbb_perm: float, csf_exp: float, route: str) -> float:
    """Predict drug accessibility to a spinal cord zone."""
    if route == "intrathecal":
        return min(1.0, csf_exp * 0.8 + 0.30)
    elif route == "oral":
        bbb_score = 1.0 if (mw < 450 and 1 < logp < 3) else (0.5 if mw < 600 else 0.2)
        return min(1.0, bbb_perm * bbb_score)
    elif route == "iv":
        bbb_score = 1.0 if mw < 500 else (0.6 if mw < 1000 else 0.3)
        return min(1.0, bbb_perm * bbb_score * 1.2)
    elif route == "aav":
        return min(1.0, bbb_perm * 0.7 + 0.3)
    return 0.3


# ---------------------------------------------------------------------------
# DB-backed public API
# ---------------------------------------------------------------------------

async def analyze_drug_penetration() -> dict[str, Any]:
    """Return drug penetration data from DB (approved SMA therapies)."""
    rows = await fetch(
        """
        SELECT drug_name, route, molecular_weight, logp, drug_type,
               zone_scores, best_zone, worst_zone, mechanism, bbb_crossing, notes
        FROM spatial_drug_penetration
        ORDER BY drug_name
        """
    )

    zones_rows = await fetch(
        "SELECT zone_key, zone_name, bbb_score, csf_score, vascular_score, sma_relevance, anatomical_region, cell_types, drug_access, clinical_relevance FROM spatial_zones ORDER BY sma_relevance DESC"
    )

    zones_dict = {}
    for z in zones_rows:
        zones_dict[z["zone_key"]] = {
            "name": z["zone_name"],
            "anatomical_region": z["anatomical_region"],
            "cell_types": z["cell_types"],
            "bbb_permeability": z["bbb_score"],
            "csf_exposure": z["csf_score"],
            "vascular_density": z["vascular_score"],
            "sma_relevance": z["sma_relevance"],
            "drug_access": z["drug_access"],
            "description": z["clinical_relevance"],
        }

    penetration = []
    for r in rows:
        zone_scores = r["zone_scores"] if isinstance(r["zone_scores"], dict) else json.loads(r["zone_scores"])
        penetration.append({
            "name": r["drug_name"],
            "mw": r["molecular_weight"],
            "logp": r["logp"],
            "route": r["route"],
            "type": r["drug_type"],
            "zone_penetration": zone_scores,
            "best_zone": r["best_zone"],
            "worst_zone": r["worst_zone"],
            "mechanism": r["mechanism"],
            "bbb_crossing": r["bbb_crossing"],
            "notes": r["notes"],
        })

    return {
        "drugs_analyzed": len(penetration),
        "zones": zones_dict,
        "penetration": penetration,
        "source": "postgresql",
    }


async def get_spatial_expression_map() -> dict[str, Any]:
    """Return target × zone expression matrix (in-memory data, zone metadata from DB)."""
    rows = await fetch(
        "SELECT zone_key, zone_name, bbb_score, csf_score, vascular_score, sma_relevance, anatomical_region, cell_types, drug_access, clinical_relevance FROM spatial_zones ORDER BY sma_relevance DESC"
    )

    zone_keys = [r["zone_key"] for r in rows]
    zone_details = {
        r["zone_key"]: {
            "name": r["zone_name"],
            "anatomical_region": r["anatomical_region"],
            "cell_types": r["cell_types"],
            "bbb_permeability": r["bbb_score"],
            "csf_exposure": r["csf_score"],
            "vascular_density": r["vascular_score"],
            "sma_relevance": r["sma_relevance"],
            "description": r["clinical_relevance"],
        }
        for r in rows
    }

    return {
        "zones": zone_keys,
        "zone_details": zone_details,
        "targets": list(TARGET_EXPRESSION.keys()),
        "expression_matrix": TARGET_EXPRESSION,
        "source": "postgresql_zones+in_memory_expression",
        "note": (
            "Expression values 0-1 (absent to very high). Based on Human Protein Atlas, "
            "Allen Brain Atlas, and SMA single-cell RNA-seq literature. "
            "Zone metadata from spatial_zones table."
        ),
    }


async def identify_silent_zones() -> dict[str, Any]:
    """Identify therapeutic silent zones where current drugs underperform (DB-backed)."""
    zones_rows = await fetch(
        "SELECT zone_key, zone_name, bbb_score, csf_score, sma_relevance FROM spatial_zones WHERE sma_relevance >= 0.3 ORDER BY sma_relevance DESC"
    )

    drug_rows = await fetch(
        "SELECT drug_name, route, zone_scores FROM spatial_drug_penetration"
    )

    drugs = []
    for r in drug_rows:
        zone_scores = r["zone_scores"] if isinstance(r["zone_scores"], dict) else json.loads(r["zone_scores"])
        drugs.append({"name": r["drug_name"], "route": r["route"], "zone_scores": zone_scores})

    silent_zones = []
    for zone in zones_rows:
        zk = zone["zone_key"]
        drug_accesses = [d["zone_scores"].get(zk, 0.0) for d in drugs]
        best_access = max(drug_accesses) if drug_accesses else 0.0

        if best_access < 0.5 and zone["sma_relevance"] >= 0.4:
            per_drug = {d["name"]: round(d["zone_scores"].get(zk, 0.0), 2) for d in drugs}
            silent_zones.append({
                "zone": zk,
                "zone_name": zone["zone_name"],
                "sma_relevance": zone["sma_relevance"],
                "best_therapy_access": round(best_access, 2),
                **per_drug,
                "gap": round(zone["sma_relevance"] - best_access, 2),
                "recommendation": "Consider targeted delivery or alternative therapeutic modality",
            })

    return {
        "silent_zones": silent_zones,
        "total": len(silent_zones),
        "source": "postgresql",
        "insight": (
            "Silent zones are SMA-relevant regions where no current therapy achieves >50% penetration. "
            "These represent opportunities for next-generation targeted delivery."
        ),
    }
