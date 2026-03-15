"""AAV Capsid Evaluation for SMA Gene Therapy (Phase 6.3).

Evaluates AAV serotypes for SMA gene therapy delivery based on:
- Motor neuron tropism (CNS biodistribution)
- Blood-Brain Barrier crossing ability
- Immunogenicity (pre-existing NAb seroprevalence)
- Packaging capacity vs cargo size
- Clinical precedent in SMA or neuromuscular diseases
- Manufacturing feasibility

Reference: Zolgensma uses AAV9 (scAAV9-SMN1, Novartis).

Capsid data from published literature:
- Foust et al., 2010 (AAV9 crosses BBB in neonates)
- Mendell et al., 2017 (AVXS-101/Zolgensma Phase 1)
- Hudry & Bhatt, Nat Rev Neurol 2019 (AAV for CNS review)
- Chan et al., 2017 (PHP.eB engineered capsid)
- Deverman et al., 2016 (Cre-based AAV capsid selection)
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# AAV packaging capacity (single-stranded ~4.7 kb, self-complementary ~2.3 kb)
SS_CAPACITY_KB = 4.7
SC_CAPACITY_KB = 2.3

# SMN1 cDNA: ~1.5 kb coding + promoter/polyA ≈ 2.5-3.0 kb total
SMN1_CARGO_KB = 2.8

# Typical therapeutic cargo sizes
CARGO_SIZES = {
    "SMN1_cDNA": {"size_kb": 2.8, "genome": "sc", "note": "Self-complementary AAV9-SMN1 (Zolgensma design)"},
    "SMN1_full_length": {"size_kb": 3.5, "genome": "ss", "note": "Full-length with regulatory elements"},
    "dCas9_CRISPRi": {"size_kb": 4.2, "genome": "ss", "note": "dCas9 + sgRNA for CRISPRi at ISS-N1"},
    "dual_vector_dCas9": {"size_kb": 2.5, "genome": "ss", "note": "Split-intein dCas9 (half per vector)"},
    "base_editor_ABE": {"size_kb": 4.5, "genome": "ss", "note": "Adenine base editor for C6T correction"},
    "prime_editor": {"size_kb": 6.3, "genome": "ss", "note": "PE2 — exceeds AAV capacity, requires dual vector"},
    "micro_dystrophin": {"size_kb": 3.8, "genome": "ss", "note": "For NMJ-focused approach (from DMD experience)"},
}


# ---------------------------------------------------------------------------
# AAV Capsid Database
# ---------------------------------------------------------------------------

@dataclass
class AAVCapsid:
    """An AAV serotype with delivery characteristics."""
    serotype: str
    motor_neuron_tropism: float  # 0-1 efficiency of MN transduction
    bbb_crossing: float          # 0-1 BBB penetration (IV route)
    immunogenicity: float        # 0-1 seroprevalence (higher = worse)
    manufacturing_score: float   # 0-1 production feasibility
    clinical_precedent: str      # summary of clinical use
    route: str                   # preferred delivery route
    species_data: str            # species where tropism was validated
    key_reference: str
    notes: str


# Curated AAV capsid data from literature
AAV_CAPSIDS = {
    "AAV9": AAVCapsid(
        serotype="AAV9",
        motor_neuron_tropism=0.90,
        bbb_crossing=0.85,
        immunogenicity=0.47,  # ~47% NAb seroprevalence in adults
        manufacturing_score=0.85,
        clinical_precedent="FDA-approved: Zolgensma (onasemnogene abeparvovec) for SMA Type 1. >3,000 patients treated globally.",
        route="IV (neonatal) or intrathecal (older patients)",
        species_data="Mouse, NHP, Human (Phase 1-3, commercial)",
        key_reference="Mendell et al., NEJM 2017; Foust et al., Nat Biotechnol 2010",
        notes="Gold standard for SMA. Crosses BBB efficiently in neonates. Reduced efficiency in adults. "
              "Pre-existing NAbs (~47% adults) can block transduction. Hepatotoxicity is dose-limiting.",
    ),
    "AAVrh10": AAVCapsid(
        serotype="AAVrh10",
        motor_neuron_tropism=0.82,
        bbb_crossing=0.70,
        immunogenicity=0.30,  # Lower seroprevalence than AAV9
        manufacturing_score=0.75,
        clinical_precedent="Phase 1/2 for CLN2 (Batten disease), GM1 gangliosidosis. No SMA trials yet.",
        route="IV or intrathecal",
        species_data="Mouse, NHP",
        key_reference="Zhang et al., Hum Gene Ther 2011",
        notes="Strong CNS tropism. Lower seroprevalence than AAV9 — may be viable for AAV9-seropositive patients. "
              "Potential second-generation SMA vector.",
    ),
    "PHP.eB": AAVCapsid(
        serotype="PHP.eB",
        motor_neuron_tropism=0.95,
        bbb_crossing=0.95,
        immunogenicity=0.25,  # Engineered, low pre-existing immunity
        manufacturing_score=0.55,  # Challenging production
        clinical_precedent="Preclinical only. Mouse-specific BBB crossing via LY6A receptor. Does NOT translate to NHP/human.",
        route="IV",
        species_data="Mouse only (C57BL/6)",
        key_reference="Chan et al., Nat Neurosci 2017; Deverman et al., Nat Biotechnol 2016",
        notes="CAUTION: Extraordinary BBB crossing in C57BL/6 mice but mechanism is LY6A-dependent — "
              "does NOT translate to primates. Not suitable for clinical development. "
              "Valuable as research tool for mouse SMA models only.",
    ),
    "AAV5": AAVCapsid(
        serotype="AAV5",
        motor_neuron_tropism=0.40,
        bbb_crossing=0.30,
        immunogenicity=0.25,
        manufacturing_score=0.90,
        clinical_precedent="FDA-approved: Roctavian (AAV5-FVIII) for hemophilia A. Not used for CNS.",
        route="IV",
        species_data="Mouse, NHP, Human",
        key_reference="Nathwani et al., NEJM 2011",
        notes="Low CNS tropism — poor choice for SMA motor neuron targeting. "
              "Strong liver tropism makes it suitable for hepatic gene therapy but not SMA.",
    ),
    "AAVhu68": AAVCapsid(
        serotype="AAVhu68",
        motor_neuron_tropism=0.80,
        bbb_crossing=0.75,
        immunogenicity=0.35,
        manufacturing_score=0.70,
        clinical_precedent="Phase 1/2 for GM1 gangliosidosis (intracisternal). No SMA trials.",
        route="Intracisternal magna or intrathecal",
        species_data="NHP (strong spinal MN transduction)",
        key_reference="Hinderer et al., Mol Ther 2018",
        notes="Derived from human tissue. Good spinal cord transduction in NHP via ICM route. "
              "Strong candidate for intrathecal SMA gene therapy in older patients.",
    ),
    "AAV-PHP.S": AAVCapsid(
        serotype="AAV-PHP.S",
        motor_neuron_tropism=0.70,
        bbb_crossing=0.20,
        immunogenicity=0.20,
        manufacturing_score=0.50,
        clinical_precedent="Preclinical only. Peripheral nervous system tropism.",
        route="IV or local injection",
        species_data="Mouse",
        key_reference="Chan et al., Nat Neurosci 2017",
        notes="Engineered for peripheral nervous system. May complement CNS-targeting vectors "
              "for systemic SMA (motor neurons + peripheral nerves + NMJ).",
    ),
    "AAV1": AAVCapsid(
        serotype="AAV1",
        motor_neuron_tropism=0.50,
        bbb_crossing=0.15,
        immunogenicity=0.55,
        manufacturing_score=0.90,
        clinical_precedent="FDA-approved: Glybera (lipoprotein lipase deficiency, withdrawn). Luxturna component.",
        route="Intramuscular or intrathecal",
        species_data="Mouse, NHP, Human",
        key_reference="Riviere et al., Lancet 2006",
        notes="Good muscle tropism — relevant for NMJ-focused SMA strategies. "
              "High seroprevalence limits systemic use. Could target muscle in combination with AAV9 for neurons.",
    ),
    "AAV-DJ": AAVCapsid(
        serotype="AAV-DJ",
        motor_neuron_tropism=0.45,
        bbb_crossing=0.25,
        immunogenicity=0.40,
        manufacturing_score=0.80,
        clinical_precedent="Preclinical only. Shuffled capsid from AAV2/8/9.",
        route="IV or intrathecal",
        species_data="Mouse, in vitro",
        key_reference="Grimm et al., J Virol 2008",
        notes="DNA shuffled hybrid capsid. High transduction efficiency in vitro. "
              "Moderate CNS tropism. Research tool, not yet clinical.",
    ),
    "MyoAAV": AAVCapsid(
        serotype="MyoAAV (2A/4A)",
        motor_neuron_tropism=0.30,
        bbb_crossing=0.10,
        immunogenicity=0.20,
        manufacturing_score=0.55,
        clinical_precedent="Preclinical only. Engineered for skeletal muscle.",
        route="IV",
        species_data="Mouse, NHP",
        key_reference="Tabebordbar et al., Cell 2021",
        notes="Engineered for skeletal muscle — 10-100x more efficient than AAV9 in muscle. "
              "Could complement CNS-targeting AAV for SMA multisystem approach. "
              "Muscle-directed SMN or PLS3 delivery.",
    ),
}


# ---------------------------------------------------------------------------
# Evaluation Logic
# ---------------------------------------------------------------------------

def _packaging_feasibility(capsid: AAVCapsid, cargo_key: str) -> dict[str, Any]:
    """Check if cargo fits in capsid."""
    if cargo_key not in CARGO_SIZES:
        return {"fits": False, "error": f"Unknown cargo: {cargo_key}"}

    cargo = CARGO_SIZES[cargo_key]
    capacity = SC_CAPACITY_KB if cargo["genome"] == "sc" else SS_CAPACITY_KB
    fits = cargo["size_kb"] <= capacity
    headroom = round(capacity - cargo["size_kb"], 1)

    return {
        "fits": fits,
        "cargo_kb": cargo["size_kb"],
        "capacity_kb": capacity,
        "genome_type": cargo["genome"],
        "headroom_kb": headroom,
        "note": cargo["note"],
        "warning": None if fits else f"Cargo exceeds capacity by {abs(headroom)} kb — dual-vector or truncation required",
    }


def _composite_score(capsid: AAVCapsid, cargo_key: str = "SMN1_cDNA") -> float:
    """Compute composite suitability score for SMA gene therapy.

    Weights reflect SMA-specific priorities:
    - Motor neuron tropism: 30% (primary target cell)
    - BBB crossing: 20% (IV delivery preferred for neonates)
    - Immunogenicity: 20% (inverted — lower is better)
    - Manufacturing: 15% (scalability)
    - Packaging: 15% (must fit cargo)
    """
    pkg = _packaging_feasibility(capsid, cargo_key)
    pkg_score = 1.0 if pkg["fits"] else 0.2  # Heavy penalty if cargo doesn't fit

    score = (
        0.30 * capsid.motor_neuron_tropism
        + 0.20 * capsid.bbb_crossing
        + 0.20 * (1.0 - capsid.immunogenicity)  # Invert: lower seroprevalence = better
        + 0.15 * capsid.manufacturing_score
        + 0.15 * pkg_score
    )
    return round(score, 3)


def evaluate_capsids(cargo: str = "SMN1_cDNA") -> dict[str, Any]:
    """Evaluate all AAV capsids for SMA gene therapy delivery.

    Returns capsids ranked by composite suitability score.
    """
    evaluations = []

    for name, capsid in AAV_CAPSIDS.items():
        pkg = _packaging_feasibility(capsid, cargo)
        score = _composite_score(capsid, cargo)

        evaluations.append({
            **asdict(capsid),
            "composite_score": score,
            "packaging": pkg,
        })

    evaluations.sort(key=lambda x: x["composite_score"], reverse=True)

    # Add rank
    for i, ev in enumerate(evaluations):
        ev["rank"] = i + 1

    # Categorize
    recommended = [e for e in evaluations if e["composite_score"] >= 0.65]
    viable = [e for e in evaluations if 0.45 <= e["composite_score"] < 0.65]
    not_recommended = [e for e in evaluations if e["composite_score"] < 0.45]

    return {
        "cargo": cargo,
        "cargo_details": CARGO_SIZES.get(cargo, {}),
        "total_capsids": len(evaluations),
        "recommended": len(recommended),
        "viable": len(viable),
        "not_recommended": len(not_recommended),
        "capsids": evaluations,
        "strategies": _sma_strategies(),
        "scoring_weights": {
            "motor_neuron_tropism": "30%",
            "bbb_crossing": "20%",
            "immunogenicity_inverted": "20%",
            "manufacturing": "15%",
            "packaging_feasibility": "15%",
        },
    }


def _sma_strategies() -> list[dict[str, str]]:
    """Return SMA-specific AAV delivery strategies."""
    return [
        {
            "strategy": "Neonatal IV (Zolgensma model)",
            "capsid": "AAV9 (scAAV9-SMN1)",
            "rationale": "Proven in >3,000 patients. BBB crossing excellent in neonates (<2 years). "
                         "One-time IV dose. Manufacturing scaled. NAb screening required.",
            "limitations": "Dose-limiting hepatotoxicity. NAb-positive patients excluded (~47%). "
                           "Declining BBB crossing with age.",
        },
        {
            "strategy": "Intrathecal for older patients",
            "capsid": "AAV9 or AAVhu68",
            "rationale": "Bypass BBB entirely. Lower dose (less hepatotoxicity). Proven IT route for CNS. "
                         "AAVhu68 shows strong spinal MN transduction in NHP.",
            "limitations": "Invasive procedure. Distribution may be uneven. "
                           "Repeat dosing unclear (immune response to capsid).",
        },
        {
            "strategy": "AAV9-seropositive rescue",
            "capsid": "AAVrh10",
            "rationale": "Lower seroprevalence (~30% vs 47%). Good CNS tropism. "
                         "Could treat patients excluded from Zolgensma due to anti-AAV9 NAbs.",
            "limitations": "Less clinical data than AAV9. Cross-reactivity possible.",
        },
        {
            "strategy": "Dual-vector CRISPRi",
            "capsid": "AAV9 (dual vector, split-intein dCas9)",
            "rationale": "Permanent epigenetic silencing of ISS-N1 — combines CRISPR guide (Phase 6.2) with "
                         "AAV delivery. Split-intein approach fits dCas9 in 2 AAV vectors.",
            "limitations": "Requires co-transduction of both vectors in same cell. Lower efficiency than "
                           "single vector. No clinical precedent for CNS split-intein.",
        },
        {
            "strategy": "Muscle + CNS dual targeting",
            "capsid": "AAV9 (CNS) + MyoAAV (muscle)",
            "rationale": "SMA is multisystem — motor neurons AND NMJ/muscle affected. "
                         "AAV9 for neuronal SMN1 + MyoAAV for muscle-specific PLS3 or trophic factors.",
            "limitations": "Two vectors = two manufacturing processes. Additive immune response. "
                           "Complex regulatory pathway.",
        },
    ]


def get_capsid_details(serotype: str) -> dict[str, Any] | None:
    """Get detailed information about a specific AAV capsid."""
    capsid = AAV_CAPSIDS.get(serotype.upper()) or AAV_CAPSIDS.get(serotype)
    if not capsid:
        # Try fuzzy match
        for name, cap in AAV_CAPSIDS.items():
            if serotype.upper() in name.upper():
                capsid = cap
                break
    if not capsid:
        return None

    result = asdict(capsid)
    # Add packaging for all cargo types
    result["packaging_by_cargo"] = {}
    for cargo_key in CARGO_SIZES:
        result["packaging_by_cargo"][cargo_key] = _packaging_feasibility(capsid, cargo_key)

    # Add composite scores for each cargo
    result["scores_by_cargo"] = {}
    for cargo_key in CARGO_SIZES:
        result["scores_by_cargo"][cargo_key] = _composite_score(capsid, cargo_key)

    return result
