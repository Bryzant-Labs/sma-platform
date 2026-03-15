"""Spatial Multi-Omics Analysis for SMA (Phase 7.1).

Models drug penetration, target expression, and therapeutic silent zones
across spinal cord microanatomy. Predicts which SMA drugs reach which
tissue compartments based on molecular properties.

When Slide-seq/MERFISH data becomes available, this module will integrate
real spatial transcriptomics. Until then, uses curated expression profiles
from literature (Allen Brain Atlas, Human Protein Atlas, single-cell RNA-seq).

References:
- Blum et al., Nature 2021 (spinal cord single-cell atlas)
- Häggmark et al., Science 2016 (Human Protein Atlas spinal cord)
- Nichterwitz et al., Cell Reports 2016 (laser-captured MN transcriptomes)
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Spinal cord zones
# ---------------------------------------------------------------------------

@dataclass
class SpinalZone:
    """A spatial compartment in the spinal cord."""
    name: str
    anatomical_region: str
    cell_types: list[str]
    bbb_permeability: float     # 0-1 (0=impermeable, 1=fully permeable)
    csf_exposure: float         # 0-1 proximity to CSF (IT drug delivery)
    vascular_density: float     # 0-1 relative blood supply
    sma_relevance: float        # 0-1 importance for SMA pathology
    description: str


SPINAL_ZONES = {
    "ventral_horn": SpinalZone(
        name="Ventral Horn",
        anatomical_region="Gray matter, ventral",
        cell_types=["alpha motor neurons", "gamma motor neurons", "interneurons", "astrocytes", "microglia"],
        bbb_permeability=0.35,
        csf_exposure=0.50,
        vascular_density=0.70,
        sma_relevance=1.0,
        description="PRIMARY SMA target zone. Contains alpha motor neurons (the cells that die in SMA). "
                    "Lamina VIII-IX. Most vulnerable region — motor neuron loss is the hallmark of SMA.",
    ),
    "dorsal_horn": SpinalZone(
        name="Dorsal Horn",
        anatomical_region="Gray matter, dorsal",
        cell_types=["sensory neurons", "interneurons", "astrocytes", "microglia"],
        bbb_permeability=0.30,
        csf_exposure=0.55,
        vascular_density=0.60,
        sma_relevance=0.25,
        description="Sensory processing region. Relatively spared in SMA but sensory deficits "
                    "reported in severe cases. Lamina I-VI.",
    ),
    "central_canal": SpinalZone(
        name="Central Canal / Ependymal Zone",
        anatomical_region="Central gray matter",
        cell_types=["ependymal cells", "neural stem cells", "CSF-contacting neurons"],
        bbb_permeability=0.20,
        csf_exposure=1.0,
        vascular_density=0.40,
        sma_relevance=0.30,
        description="Highest CSF exposure — best reached by intrathecal drugs (nusinersen). "
                    "Contains neural stem cell niche. Potential for endogenous repair.",
    ),
    "white_matter": SpinalZone(
        name="White Matter Tracts",
        anatomical_region="Peripheral white matter",
        cell_types=["oligodendrocytes", "astrocytes", "myelinated axons"],
        bbb_permeability=0.25,
        csf_exposure=0.30,
        vascular_density=0.45,
        sma_relevance=0.40,
        description="Motor axon tracts. Axonal degeneration occurs in SMA. White matter "
                    "pathology may precede motor neuron death.",
    ),
    "drg": SpinalZone(
        name="Dorsal Root Ganglia",
        anatomical_region="Peripheral (outside CNS)",
        cell_types=["sensory neurons", "satellite glia"],
        bbb_permeability=0.80,  # DRG has fenestrated capillaries
        csf_exposure=0.15,
        vascular_density=0.75,
        sma_relevance=0.20,
        description="Outside BBB — accessible to systemic drugs. DRG toxicity is a concern "
                    "for AAV9 gene therapy (dorsal root ganglion pathology in NHP studies).",
    ),
    "nmj": SpinalZone(
        name="Neuromuscular Junction",
        anatomical_region="Peripheral (muscle)",
        cell_types=["motor neuron terminal", "muscle fiber", "terminal Schwann cells"],
        bbb_permeability=1.0,  # No BBB at NMJ
        csf_exposure=0.0,
        vascular_density=0.65,
        sma_relevance=0.85,
        description="CRITICAL SMA zone. NMJ denervation is an early event in SMA, often "
                    "preceding motor neuron death. Accessible to systemic drugs (no BBB). "
                    "Agrin/MuSK/rapsyn pathway is disrupted.",
    ),
}


# ---------------------------------------------------------------------------
# Target expression profiles by zone
# ---------------------------------------------------------------------------

# Expression levels: 0=absent, 0.3=low, 0.6=moderate, 0.9=high, 1.0=very high
TARGET_EXPRESSION = {
    "SMN1": {"ventral_horn": 0.95, "dorsal_horn": 0.70, "central_canal": 0.50, "white_matter": 0.40, "drg": 0.60, "nmj": 0.30},
    "SMN2": {"ventral_horn": 0.95, "dorsal_horn": 0.70, "central_canal": 0.50, "white_matter": 0.40, "drg": 0.60, "nmj": 0.30},
    "SMN_PROTEIN": {"ventral_horn": 0.90, "dorsal_horn": 0.65, "central_canal": 0.45, "white_matter": 0.35, "drg": 0.55, "nmj": 0.25},
    "STMN2": {"ventral_horn": 0.85, "dorsal_horn": 0.50, "central_canal": 0.20, "white_matter": 0.60, "drg": 0.70, "nmj": 0.15},
    "PLS3": {"ventral_horn": 0.70, "dorsal_horn": 0.40, "central_canal": 0.30, "white_matter": 0.20, "drg": 0.35, "nmj": 0.80},
    "NCALD": {"ventral_horn": 0.75, "dorsal_horn": 0.60, "central_canal": 0.40, "white_matter": 0.15, "drg": 0.50, "nmj": 0.20},
    "UBA1": {"ventral_horn": 0.80, "dorsal_horn": 0.70, "central_canal": 0.60, "white_matter": 0.50, "drg": 0.65, "nmj": 0.40},
    "MTOR_PATHWAY": {"ventral_horn": 0.85, "dorsal_horn": 0.75, "central_canal": 0.70, "white_matter": 0.50, "drg": 0.60, "nmj": 0.45},
    "NMJ_MATURATION": {"ventral_horn": 0.40, "dorsal_horn": 0.10, "central_canal": 0.05, "white_matter": 0.05, "drg": 0.10, "nmj": 1.00},
    "CORO1C": {"ventral_horn": 0.30, "dorsal_horn": 0.25, "central_canal": 0.20, "white_matter": 0.15, "drg": 0.20, "nmj": 0.35},
}


# ---------------------------------------------------------------------------
# Drug penetration model
# ---------------------------------------------------------------------------

def _zone_accessibility(mw: float, logp: float, bbb_perm: float, csf_exp: float, route: str) -> float:
    """Predict drug accessibility to a spinal cord zone."""
    if route == "intrathecal":
        # Intrathecal delivery bypasses BBB — CSF exposure is primary
        # Nusinersen clinical PK: 60-70% motor neuron engagement in ventral horn
        # Size penalty removed: once in CSF, ASO size doesn't limit parenchymal uptake
        return min(1.0, csf_exp * 0.8 + 0.30)
    elif route == "oral":
        # Oral: must cross BBB, logP and MW matter most
        bbb_score = 1.0 if (mw < 450 and 1 < logp < 3) else (0.5 if mw < 600 else 0.2)
        return min(1.0, bbb_perm * bbb_score)
    elif route == "iv":
        # IV: BBB is barrier, but higher concentrations possible
        bbb_score = 1.0 if mw < 500 else (0.6 if mw < 1000 else 0.3)
        return min(1.0, bbb_perm * bbb_score * 1.2)
    elif route == "aav":
        # AAV gene therapy: tropism-dependent, partially crosses BBB
        return min(1.0, bbb_perm * 0.7 + 0.3)  # Some transduction even with partial BBB
    return 0.3


def analyze_drug_penetration() -> dict[str, Any]:
    """Analyze drug penetration across spinal cord zones for approved SMA therapies."""
    drugs = [
        {"name": "Nusinersen (Spinraza)", "mw": 7501, "logp": -5, "route": "intrathecal", "type": "ASO"},
        {"name": "Risdiplam (Evrysdi)", "mw": 390, "logp": 2.1, "route": "oral", "type": "small_molecule"},
        {"name": "Zolgensma (AAV9-SMN1)", "mw": 4000000, "logp": 0, "route": "aav", "type": "gene_therapy"},
    ]

    results = []
    for drug in drugs:
        zone_scores = {}
        for zone_key, zone in SPINAL_ZONES.items():
            score = _zone_accessibility(drug["mw"], drug["logp"], zone.bbb_permeability, zone.csf_exposure, drug["route"])
            zone_scores[zone_key] = round(score, 2)

        results.append({
            **drug,
            "zone_penetration": zone_scores,
            "best_zone": max(zone_scores, key=zone_scores.get),
            "worst_zone": min(zone_scores, key=zone_scores.get),
        })

    return {
        "drugs_analyzed": len(results),
        "zones": {k: asdict(v) for k, v in SPINAL_ZONES.items()},
        "penetration": results,
    }


def get_spatial_expression_map() -> dict[str, Any]:
    """Return target×zone expression matrix."""
    return {
        "zones": list(SPINAL_ZONES.keys()),
        "zone_details": {k: asdict(v) for k, v in SPINAL_ZONES.items()},
        "targets": list(TARGET_EXPRESSION.keys()),
        "expression_matrix": TARGET_EXPRESSION,
        "note": "Expression values 0-1 (absent to very high). Based on Human Protein Atlas, "
                "Allen Brain Atlas, and SMA single-cell RNA-seq literature.",
    }


def identify_silent_zones() -> dict[str, Any]:
    """Identify therapeutic 'silent zones' where current drugs underperform."""
    silent_zones = []

    for zone_key, zone in SPINAL_ZONES.items():
        if zone.sma_relevance < 0.3:
            continue

        # Check each approved therapy
        nusinersen_access = _zone_accessibility(7501, -5, zone.bbb_permeability, zone.csf_exposure, "intrathecal")
        risdiplam_access = _zone_accessibility(390, 2.1, zone.bbb_permeability, zone.csf_exposure, "oral")
        zolgensma_access = _zone_accessibility(4e6, 0, zone.bbb_permeability, zone.csf_exposure, "aav")

        best_access = max(nusinersen_access, risdiplam_access, zolgensma_access)

        if best_access < 0.5 and zone.sma_relevance >= 0.4:
            silent_zones.append({
                "zone": zone_key,
                "zone_name": zone.name,
                "sma_relevance": zone.sma_relevance,
                "best_therapy_access": round(best_access, 2),
                "nusinersen": round(nusinersen_access, 2),
                "risdiplam": round(risdiplam_access, 2),
                "zolgensma": round(zolgensma_access, 2),
                "gap": round(zone.sma_relevance - best_access, 2),
                "recommendation": "Consider targeted delivery or alternative therapeutic modality",
            })

    return {
        "silent_zones": silent_zones,
        "total": len(silent_zones),
        "insight": "Silent zones are SMA-relevant regions where no current therapy achieves >50% penetration. "
                   "These represent opportunities for next-generation targeted delivery.",
    }
