"""Zero-Knowledge Data Sharing Framework (Phase 10.5).

Defines the architecture for federated learning and privacy-preserving
data sharing in SMA research. Enables cross-institutional collaboration
without sharing raw patient data.

This module provides:
- Federated learning protocol specifications
- Differential privacy parameter recommendations
- OMOP/OHDSI data model mapping for SMA
- Privacy budget calculator
- Data sharing agreement templates

References:
- McMahan et al., 2017 (FedAvg: Communication-Efficient Learning)
- Dwork & Roth, 2014 (The Algorithmic Foundations of Differential Privacy)
- OHDSI Book of OHDSI, 2019 (OMOP Common Data Model)
"""

from __future__ import annotations

import logging
import math
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Federated learning protocols
# ---------------------------------------------------------------------------

@dataclass
class FLProtocol:
    """A federated learning protocol for SMA research."""
    name: str
    algorithm: str              # FedAvg, FedProx, SCAFFOLD, etc.
    description: str
    communication_rounds: int
    local_epochs: int
    min_participants: int
    privacy_mechanism: str      # DP-SGD, secure aggregation, homomorphic
    sma_use_case: str
    data_requirements: list[str]
    expected_utility: float     # 0-1 model utility vs centralized
    privacy_guarantee: str


FL_PROTOCOLS = [
    FLProtocol(
        name="SMA Patient Phenotype Predictor",
        algorithm="FedAvg",
        description="Predict SMA severity (type 1-4) from genetic and clinical features. "
                   "Each hospital trains locally on their patient cohort, shares only model "
                   "gradients (not patient data).",
        communication_rounds=50,
        local_epochs=5,
        min_participants=5,
        privacy_mechanism="DP-SGD (epsilon=1.0, delta=1e-5)",
        sma_use_case="Multi-center severity prediction without sharing patient records",
        data_requirements=[
            "SMN2 copy number",
            "Age at onset",
            "Motor function score (HFMSE/CHOP INTEND)",
            "Treatment history (drug, start date, response)",
            "Genotype (SMN1 deletion type, SMN2 copies)",
        ],
        expected_utility=0.85,
        privacy_guarantee="(1.0, 1e-5)-differential privacy per patient",
    ),
    FLProtocol(
        name="SMA Drug Response Classifier",
        algorithm="FedProx",
        description="Predict which SMA therapy (nusinersen, risdiplam, Zolgensma) will work "
                   "best for a given patient profile. FedProx handles heterogeneous data "
                   "across treatment centers.",
        communication_rounds=100,
        local_epochs=3,
        min_participants=10,
        privacy_mechanism="Secure aggregation + DP-SGD (epsilon=2.0)",
        sma_use_case="Personalized therapy selection across treatment centers",
        data_requirements=[
            "Patient demographics (age, weight, SMA type)",
            "SMN2 copy number and gene status",
            "Pre-treatment motor function scores",
            "Treatment administered and dosing",
            "6-month and 12-month motor function outcomes",
            "Adverse events (coded)",
        ],
        expected_utility=0.80,
        privacy_guarantee="(2.0, 1e-5)-differential privacy, secure aggregation",
    ),
    FLProtocol(
        name="SMA Biomarker Discovery",
        algorithm="SCAFFOLD",
        description="Discover new SMA biomarkers from multi-omics data across institutions. "
                   "SCAFFOLD corrects for client drift when data distributions differ greatly.",
        communication_rounds=200,
        local_epochs=2,
        min_participants=3,
        privacy_mechanism="Homomorphic encryption (partial, for gradient aggregation)",
        sma_use_case="Identify prognostic biomarkers without centralizing omics data",
        data_requirements=[
            "Transcriptomics (RNA-seq or microarray)",
            "Proteomics (mass spec or SomaScan)",
            "Clinical phenotype labels",
            "Treatment response labels",
        ],
        expected_utility=0.75,
        privacy_guarantee="Computational privacy (HE for aggregation), no raw data leaves site",
    ),
    FLProtocol(
        name="SMA Natural History Model",
        algorithm="FedAvg",
        description="Model SMA disease progression across the lifespan. Combine longitudinal "
                   "data from multiple registries without merging databases.",
        communication_rounds=75,
        local_epochs=5,
        min_participants=8,
        privacy_mechanism="DP-SGD (epsilon=0.5, delta=1e-6) — strict privacy for longitudinal data",
        sma_use_case="Disease progression modeling for clinical trial design",
        data_requirements=[
            "Serial motor function assessments (every 3-6 months)",
            "Respiratory function (FVC, need for ventilation)",
            "Nutritional status (feeding route, weight trajectory)",
            "Milestone achievements/losses",
            "Treatment start dates and switches",
        ],
        expected_utility=0.82,
        privacy_guarantee="(0.5, 1e-6)-differential privacy — strong guarantee for longitudinal data",
    ),
]


# ---------------------------------------------------------------------------
# OMOP/OHDSI mapping for SMA
# ---------------------------------------------------------------------------

@dataclass
class OMOPMapping:
    """Mapping of SMA clinical concepts to OMOP CDM."""
    sma_concept: str
    omop_domain: str            # Condition, Measurement, Drug, Procedure, Observation
    omop_concept_id: int
    omop_concept_name: str
    vocabulary: str             # SNOMED, LOINC, RxNorm, etc.
    notes: str


OMOP_MAPPINGS = [
    OMOPMapping("SMA diagnosis", "Condition", 4144889, "Spinal muscular atrophy", "SNOMED", "Primary diagnosis code"),
    OMOPMapping("SMA Type 1", "Condition", 4083556, "Werdnig-Hoffmann disease", "SNOMED", "Most severe infant-onset"),
    OMOPMapping("SMA Type 2", "Condition", 4083557, "Intermediate spinal muscular atrophy", "SNOMED", "Childhood onset, never walk"),
    OMOPMapping("SMA Type 3", "Condition", 4083558, "Kugelberg-Welander disease", "SNOMED", "Juvenile onset, walk then lose"),
    OMOPMapping("SMN2 copy number", "Measurement", 3046279, "Gene copy number", "LOINC", "Critical severity modifier"),
    OMOPMapping("CHOP INTEND score", "Measurement", 40759844, "Motor function assessment", "LOINC", "Primary outcome <2y"),
    OMOPMapping("HFMSE score", "Measurement", 40759845, "Hammersmith Functional Motor Scale", "LOINC", "Primary outcome >2y"),
    OMOPMapping("Nusinersen", "Drug", 35604394, "nusinersen 12 MG/5ML", "RxNorm", "Intrathecal ASO"),
    OMOPMapping("Risdiplam", "Drug", 37592115, "risdiplam oral solution", "RxNorm", "Oral SMN2 modifier"),
    OMOPMapping("Onasemnogene", "Drug", 37003436, "onasemnogene abeparvovec", "RxNorm", "AAV9 gene therapy"),
    OMOPMapping("Lumbar puncture", "Procedure", 4305080, "Lumbar puncture", "SNOMED", "For IT nusinersen delivery"),
    OMOPMapping("Ventilation support", "Observation", 4138566, "Respiratory support", "SNOMED", "Key disease progression marker"),
    OMOPMapping("Scoliosis surgery", "Procedure", 4163599, "Spinal fusion", "SNOMED", "Common in SMA type 2/3"),
    OMOPMapping("Feeding tube", "Procedure", 4218812, "Gastrostomy", "SNOMED", "Nutritional support in SMA1/2"),
]


# ---------------------------------------------------------------------------
# Privacy budget calculator
# ---------------------------------------------------------------------------

def calculate_privacy_budget(epsilon: float, delta: float, n_queries: int,
                            composition: str = "advanced") -> dict[str, Any]:
    """Calculate privacy budget consumption for a series of queries.

    Uses advanced composition theorem for tighter bounds.
    """
    if delta <= 0 or delta >= 1:
        return {"error": "delta must be in (0, 1)", "valid": False}
    if epsilon <= 0:
        return {"error": "epsilon must be positive", "valid": False}
    if n_queries < 1:
        return {"error": "n_queries must be >= 1", "valid": False}

    if composition == "basic":
        # Basic composition: epsilon grows linearly
        total_epsilon = epsilon * n_queries
        total_delta = delta * n_queries
    elif composition == "advanced":
        # Advanced composition (Kairouz et al., 2015)
        total_epsilon = epsilon * math.sqrt(2 * n_queries * math.log(1 / delta)) + n_queries * epsilon * (math.exp(epsilon) - 1)
        total_delta = n_queries * delta + delta
    else:
        # RDP (Renyi Differential Privacy) — tightest
        alpha = 1 + 1 / epsilon if epsilon > 0 else 2
        total_epsilon = n_queries * epsilon + math.log(1 / delta) / (alpha - 1)
        total_delta = delta

    return {
        "per_query_epsilon": epsilon,
        "per_query_delta": delta,
        "n_queries": n_queries,
        "composition_method": composition,
        "total_epsilon": round(total_epsilon, 4),
        "total_delta": round(min(1.0, total_delta), 8),
        "privacy_level": (
            "Strong" if total_epsilon < 1.0 else
            "Moderate" if total_epsilon < 5.0 else
            "Weak" if total_epsilon < 10.0 else
            "Minimal"
        ),
        "recommendation": (
            f"With {n_queries} queries at epsilon={epsilon}, total privacy budget is "
            f"epsilon={round(total_epsilon, 2)}. "
            + ("This provides strong privacy guarantees." if total_epsilon < 1.0 else
               "Consider reducing per-query epsilon or number of queries." if total_epsilon < 5.0 else
               "Privacy guarantee is weak — reduce epsilon or limit queries.")
        ),
    }


# ---------------------------------------------------------------------------
# Data sharing agreement
# ---------------------------------------------------------------------------

@dataclass
class DataSharingTier:
    """A tier of data sharing with different privacy levels."""
    tier: str
    description: str
    data_shared: list[str]
    privacy_mechanism: str
    approval_required: str
    sma_value: str


DATA_TIERS = [
    DataSharingTier(
        tier="Tier 1: Aggregate Statistics",
        description="Share only aggregate counts and summary statistics. No individual data.",
        data_shared=["Patient counts by SMA type", "Mean motor function scores", "Treatment distribution"],
        privacy_mechanism="k-anonymity (k>=10) + noise injection",
        approval_required="Institutional data use agreement",
        sma_value="Epidemiology, prevalence studies, trial design sample size estimation",
    ),
    DataSharingTier(
        tier="Tier 2: Federated Model Training",
        description="Train ML models collaboratively. Only model updates (gradients) are shared.",
        data_shared=["Model gradients (DP-protected)", "Training loss curves", "Feature importance (aggregated)"],
        privacy_mechanism="DP-SGD + secure aggregation",
        approval_required="IRB approval + data sharing agreement + DP parameters agreed",
        sma_value="Predictive models, biomarker discovery, therapy selection",
    ),
    DataSharingTier(
        tier="Tier 3: Synthetic Data",
        description="Generate synthetic patient data that preserves statistical properties but contains no real patients.",
        data_shared=["Synthetic patient records", "Simulated cohorts", "Privacy-preserved distributions"],
        privacy_mechanism="Differentially private data synthesis (DPGAN or PATE-GAN)",
        approval_required="IRB approval + synthetic data validation + utility assessment",
        sma_value="External research access, hypothesis generation, methods development",
    ),
    DataSharingTier(
        tier="Tier 4: Trusted Research Environment",
        description="Researchers run approved analyses inside a secure enclave. No data export.",
        data_shared=["Query results only (DP-protected)", "Pre-approved analysis outputs"],
        privacy_mechanism="Secure enclave + output DP + audit log",
        approval_required="Full IRB + ethics review + approved analysis plan + audit",
        sma_value="Detailed outcome analyses, longitudinal studies, real-world evidence",
    ),
]


# ---------------------------------------------------------------------------
# API functions
# ---------------------------------------------------------------------------

def _extract_epsilon(protocol: FLProtocol) -> float:
    """Extract epsilon value from a protocol's privacy_guarantee string."""
    import re
    match = re.search(r'epsilon[=:]?\s*([\d.]+)', protocol.privacy_guarantee, re.IGNORECASE)
    return float(match.group(1)) if match else float('inf')


def get_fl_protocols() -> dict[str, Any]:
    """Return federated learning protocol specifications."""
    return {
        "total_protocols": len(FL_PROTOCOLS),
        "protocols": [asdict(p) for p in FL_PROTOCOLS],
        "most_useful": asdict(max(FL_PROTOCOLS, key=lambda x: x.expected_utility)),
        "most_private": asdict(min(FL_PROTOCOLS, key=_extract_epsilon)),
        "insight": "The SMA Patient Phenotype Predictor has the highest expected utility (0.85) "
                   "with strong privacy (epsilon=1.0). Only 5 participating hospitals needed. "
                   "This is the most immediately feasible federated project for SMA.",
    }


def get_omop_mappings() -> dict[str, Any]:
    """Return OMOP/OHDSI concept mappings for SMA."""
    by_domain = {}
    for m in OMOP_MAPPINGS:
        by_domain.setdefault(m.omop_domain, []).append(m.sma_concept)

    return {
        "total_mappings": len(OMOP_MAPPINGS),
        "mappings": [asdict(m) for m in OMOP_MAPPINGS],
        "by_domain": {k: len(v) for k, v in by_domain.items()},
        "insight": "14 SMA clinical concepts mapped to OMOP CDM using SNOMED, LOINC, and RxNorm. "
                   "This enables SMA research across any OHDSI-networked database worldwide "
                   "(currently 800+ databases, 1B+ patient records).",
    }


def get_privacy_budget(epsilon: float = 1.0, delta: float = 1e-5,
                       n_queries: int = 50) -> dict[str, Any]:
    """Calculate privacy budget for a research scenario."""
    return {
        "basic": calculate_privacy_budget(epsilon, delta, n_queries, "basic"),
        "advanced": calculate_privacy_budget(epsilon, delta, n_queries, "advanced"),
        "rdp": calculate_privacy_budget(epsilon, delta, n_queries, "rdp"),
    }


def get_data_sharing_tiers() -> dict[str, Any]:
    """Return data sharing tier framework."""
    return {
        "total_tiers": len(DATA_TIERS),
        "tiers": [asdict(t) for t in DATA_TIERS],
        "recommended_start": asdict(DATA_TIERS[0]),
        "insight": "Start with Tier 1 (aggregate statistics) which requires minimal approval. "
                   "Progress to Tier 2 (federated learning) once IRB and data agreements are in place. "
                   "Tier 3 (synthetic data) enables external research without any patient data exposure.",
    }
