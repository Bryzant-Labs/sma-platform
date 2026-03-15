"""Open-Source Lab-OS — Experiment Design Automation (Phase 10.4).

Generates structured experiment designs from hypotheses, including:
- Assay selection (cell-based, animal model, biochemical, clinical)
- Protocol generation with reagents, controls, readouts
- Cloud lab integration specs (Emerald Cloud Lab, Strateos, Opentrons)
- Cost estimation and timeline
- Automated result interpretation rules

This is the "hypothesis → experiment → data → new hypothesis" loop.

References:
- Emerald Cloud Lab API (cloud-based automated biology)
- Opentrons OT-2 Python API (open-source liquid handling)
- Strateos Platform (robotic experiment execution)
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Assay library
# ---------------------------------------------------------------------------

@dataclass
class Assay:
    """A standardized assay for SMA research."""
    name: str
    assay_type: str             # cell_based, biochemical, animal, clinical_biomarker
    target: str                 # what it measures
    readout: str                # primary readout
    throughput: str             # low, medium, high
    cost_per_sample: str
    time_days: int              # time to results
    automation_ready: bool      # can be run on cloud lab
    sma_relevance: str
    protocol_steps: list[str]
    controls: list[str]


ASSAY_LIBRARY = [
    Assay(
        name="SMN2 Splicing Reporter (RT-qPCR)",
        assay_type="cell_based",
        target="SMN2 exon 7 inclusion ratio",
        readout="FL-SMN / delta7-SMN mRNA ratio",
        throughput="high",
        cost_per_sample="$15-25",
        time_days=3,
        automation_ready=True,
        sma_relevance="PRIMARY screening assay — measures the core therapeutic mechanism",
        protocol_steps=[
            "1. Seed SMA patient fibroblasts (SMN1-/-, SMN2 3-copy) in 96-well plate",
            "2. Treat with compound (8-point dose response, 0.1 nM - 10 uM)",
            "3. Incubate 24h at 37C, 5% CO2",
            "4. Lyse cells, extract RNA (TRIzol or RNeasy 96)",
            "5. RT-qPCR with primers spanning exon 6-8 junction",
            "6. Calculate FL-SMN / delta7-SMN ratio vs DMSO control",
            "7. Fit dose-response curve, calculate EC50",
        ],
        controls=["DMSO vehicle", "Risdiplam 100 nM (positive)", "Untreated (baseline)"],
    ),
    Assay(
        name="SMN Protein ELISA",
        assay_type="biochemical",
        target="SMN protein levels",
        readout="SMN protein (ng/mL) by sandwich ELISA",
        throughput="high",
        cost_per_sample="$20-35",
        time_days=2,
        automation_ready=True,
        sma_relevance="Confirms that splicing change translates to protein increase",
        protocol_steps=[
            "1. Coat 96-well plate with anti-SMN capture antibody (2B1, overnight 4C)",
            "2. Block with 3% BSA/PBS, 1h RT",
            "3. Add cell lysate samples (from treated cells), 2h RT",
            "4. Wash 3x PBS-T",
            "5. Add biotinylated anti-SMN detection antibody, 1h RT",
            "6. Streptavidin-HRP, TMB substrate, read at 450 nm",
            "7. Quantify against recombinant SMN standard curve",
        ],
        controls=["Recombinant SMN standard curve", "SMA patient cells (low SMN)", "Carrier cells (normal SMN)"],
    ),
    Assay(
        name="Motor Neuron Survival (iPSC-MN)",
        assay_type="cell_based",
        target="Motor neuron viability",
        readout="% surviving MNs (HB9+/ChAT+ cells) at day 28",
        throughput="medium",
        cost_per_sample="$100-200",
        time_days=28,
        automation_ready=False,
        sma_relevance="Gold standard for motor neuron rescue — directly measures cell survival",
        protocol_steps=[
            "1. Differentiate SMA patient iPSCs to motor neurons (28-day protocol)",
            "2. Day 14: begin compound treatment (refresh every 48h)",
            "3. Day 28: fix and immunostain (HB9, ChAT, DAPI)",
            "4. Automated imaging (ImageXpress or Opera) — count HB9+/ChAT+ neurons",
            "5. Normalize to DMSO vehicle control",
            "6. Secondary: measure neurite length (beta-III tubulin)",
        ],
        controls=["DMSO vehicle", "Risdiplam 100 nM", "Healthy control iPSC-MNs"],
    ),
    Assay(
        name="NMJ Formation Assay (co-culture)",
        assay_type="cell_based",
        target="Neuromuscular junction formation and function",
        readout="AChR cluster count + co-localization with SV2 (presynaptic)",
        throughput="low",
        cost_per_sample="$200-400",
        time_days=21,
        automation_ready=False,
        sma_relevance="Measures NMJ rescue — the critical endpoint for functional recovery",
        protocol_steps=[
            "1. Co-culture iPSC-MNs with C2C12 myotubes in microfluidic device",
            "2. Allow NMJ formation (14 days)",
            "3. Day 14: begin compound treatment",
            "4. Day 21: stain with alpha-bungarotoxin (AChR), SV2 (presynaptic), DAPI",
            "5. Confocal imaging — quantify AChR clusters co-localized with SV2",
            "6. Optional: calcium imaging to test functional NMJ transmission",
        ],
        controls=["DMSO vehicle", "Agrin 10 nM (positive)", "Healthy MN co-culture"],
    ),
    Assay(
        name="SMA Mouse Survival Study (delta7)",
        assay_type="animal",
        target="Survival and motor function",
        readout="Median survival (days), righting reflex time, body weight",
        throughput="low",
        cost_per_sample="$500-1000",
        time_days=60,
        automation_ready=False,
        sma_relevance="In vivo efficacy — required before clinical trials",
        protocol_steps=[
            "1. Breed SMN-delta7 mice (Smn-/-; SMN2+/+; SMNΔ7+/+)",
            "2. PND1: begin treatment (IP or oral, daily)",
            "3. Monitor daily: body weight, righting reflex time",
            "4. Record survival endpoint (unable to right within 30s × 2 consecutive days)",
            "5. Tissue collection at endpoint: spinal cord MN count (ChAT staining)",
            "6. NMJ analysis: AChR/SV2 co-localization in gastrocnemius",
        ],
        controls=["Vehicle control (matched route)", "Risdiplam 3 mg/kg (positive)", "Wild-type littermates"],
    ),
    Assay(
        name="Ion Channel Electrophysiology (patch clamp)",
        assay_type="cell_based",
        target="Ion channel function in motor neurons",
        readout="Action potential parameters, firing frequency, resting Vmem",
        throughput="low",
        cost_per_sample="$300-500",
        time_days=7,
        automation_ready=False,
        sma_relevance="Validates bioelectric hypothesis — are rescued MNs electrically functional?",
        protocol_steps=[
            "1. Differentiate SMA iPSC-MNs (day 28+)",
            "2. Treat with compound (72h pre-treatment)",
            "3. Whole-cell patch clamp recording (room temp or 37C)",
            "4. Current-clamp: measure resting Vmem, AP threshold, AP frequency",
            "5. Voltage-clamp: measure Na+ and K+ currents",
            "6. Compare to healthy iPSC-MN recordings",
        ],
        controls=["DMSO vehicle", "4-AP 100 uM (K+ blocker, positive)", "TTX 1 uM (Na+ blocker, negative)"],
    ),
    Assay(
        name="RNA-Binding Fluorescence Polarization",
        assay_type="biochemical",
        target="Compound-RNA binding affinity",
        readout="KD (dissociation constant) by fluorescence polarization",
        throughput="high",
        cost_per_sample="$5-10",
        time_days=1,
        automation_ready=True,
        sma_relevance="Validates RNA-binding predictions from Phase 9.4 module",
        protocol_steps=[
            "1. Synthesize fluorescein-labeled SMN2 RNA oligo (ISS-N1 or 5'ss region)",
            "2. Serial dilute compound (12-point, 0.01 nM - 100 uM)",
            "3. Mix compound + labeled RNA (10 nM) in binding buffer",
            "4. Incubate 30 min RT in black 384-well plate",
            "5. Read fluorescence polarization (excitation 485, emission 535)",
            "6. Fit binding curve, calculate KD",
        ],
        controls=["DMSO (no binding)", "Risdiplam (known binder, KD ~100 nM)", "Scrambled RNA (specificity)"],
    ),
    Assay(
        name="Mitochondrial Function (Seahorse XF)",
        assay_type="cell_based",
        target="Mitochondrial respiration and glycolysis",
        readout="OCR (oxygen consumption rate), ECAR (extracellular acidification rate)",
        throughput="medium",
        cost_per_sample="$30-50",
        time_days=2,
        automation_ready=True,
        sma_relevance="Tests energy budget hypothesis — do mitochondrial boosters close the energy gap?",
        protocol_steps=[
            "1. Seed SMA iPSC-MNs in Seahorse XF96 plate (50k cells/well)",
            "2. Treat with compound (24h or 72h pre-treatment)",
            "3. Run Mito Stress Test: basal → oligomycin → FCCP → rotenone/antimycin A",
            "4. Calculate: basal respiration, ATP-linked, maximal, spare capacity",
            "5. Normalize to cell count (Hoechst 33342 post-run)",
        ],
        controls=["DMSO vehicle", "NMN 1 mM (NAD+ boost, positive)", "FCCP 1 uM (uncoupler, maximum)"],
    ),
]


# ---------------------------------------------------------------------------
# Experiment design generator
# ---------------------------------------------------------------------------

@dataclass
class ExperimentDesign:
    """A complete experiment design generated from a hypothesis."""
    hypothesis: str
    primary_assay: str
    secondary_assays: list[str]
    compounds_to_test: list[str]
    dose_range: str
    timeline_days: int
    estimated_cost: str
    cloud_lab_compatible: bool
    automation_protocol: str
    success_criteria: list[str]
    next_steps_if_positive: str
    next_steps_if_negative: str


def design_experiment(hypothesis: str) -> dict[str, Any]:
    """Generate an experiment design from a hypothesis description."""
    hypothesis_lower = hypothesis.lower()

    # Match hypothesis to appropriate assays
    primary = None
    secondary = []
    compounds = []

    if "smn2" in hypothesis_lower or "splicing" in hypothesis_lower:
        primary = "SMN2 Splicing Reporter (RT-qPCR)"
        secondary = ["SMN Protein ELISA", "Motor Neuron Survival (iPSC-MN)"]
        compounds = ["Risdiplam (reference)", "Test compound"]
        dose = "8-point: 0.1 nM - 10 uM"
        cost = "$2,000-5,000"
        timeline = 7
    elif "ion channel" in hypothesis_lower or "bioelectric" in hypothesis_lower or "vmem" in hypothesis_lower:
        primary = "Ion Channel Electrophysiology (patch clamp)"
        secondary = ["Motor Neuron Survival (iPSC-MN)", "Mitochondrial Function (Seahorse XF)"]
        compounds = ["4-AP (reference)", "GV-58", "Test compound"]
        dose = "6-point: 0.1 uM - 1 mM"
        cost = "$5,000-15,000"
        timeline = 14
    elif "nmj" in hypothesis_lower or "muscle" in hypothesis_lower or "retrograde" in hypothesis_lower:
        primary = "NMJ Formation Assay (co-culture)"
        secondary = ["Motor Neuron Survival (iPSC-MN)", "SMN Protein ELISA"]
        compounds = ["Apitegromab (reference)", "BDNF", "Test compound"]
        dose = "6-point: 1 nM - 10 uM"
        cost = "$10,000-25,000"
        timeline = 28
    elif "rna" in hypothesis_lower or "binding" in hypothesis_lower:
        primary = "RNA-Binding Fluorescence Polarization"
        secondary = ["SMN2 Splicing Reporter (RT-qPCR)", "SMN Protein ELISA"]
        compounds = ["Risdiplam (reference)", "Branaplam (reference)", "Test compound"]
        dose = "12-point: 0.01 nM - 100 uM"
        cost = "$1,000-3,000"
        timeline = 5
    elif "mitochond" in hypothesis_lower or "energy" in hypothesis_lower or "metabol" in hypothesis_lower:
        primary = "Mitochondrial Function (Seahorse XF)"
        secondary = ["Motor Neuron Survival (iPSC-MN)", "SMN Protein ELISA"]
        compounds = ["NMN (reference)", "Metformin", "CoQ10", "Test compound"]
        dose = "6-point: 0.1 uM - 10 mM"
        cost = "$3,000-8,000"
        timeline = 7
    else:
        primary = "Motor Neuron Survival (iPSC-MN)"
        secondary = ["SMN2 Splicing Reporter (RT-qPCR)", "SMN Protein ELISA"]
        compounds = ["Risdiplam (reference)", "Test compound"]
        dose = "8-point: 0.1 nM - 10 uM"
        cost = "$5,000-15,000"
        timeline = 28

    primary_assay = next((a for a in ASSAY_LIBRARY if a.name == primary), None)
    cloud_ok = primary_assay.automation_ready if primary_assay else False

    design = ExperimentDesign(
        hypothesis=hypothesis,
        primary_assay=primary,
        secondary_assays=secondary,
        compounds_to_test=compounds,
        dose_range=dose,
        timeline_days=timeline,
        estimated_cost=cost,
        cloud_lab_compatible=cloud_ok,
        automation_protocol="Emerald Cloud Lab" if cloud_ok else "Manual (CRO recommended)",
        success_criteria=[
            f"Primary assay EC50 < 1 uM",
            "SMN protein increase > 2-fold over DMSO",
            "No cytotoxicity at effective dose (>80% viability)",
            "Dose-response with Hill slope 0.5-3 (specific binding)",
        ],
        next_steps_if_positive="Advance to secondary assays → iPSC-MN survival → NMJ formation → animal model",
        next_steps_if_negative="Re-examine hypothesis, test alternative compounds, consider combination approach",
    )

    return {
        "design": asdict(design),
        "primary_assay_protocol": asdict(primary_assay) if primary_assay else None,
        "secondary_assay_protocols": [
            asdict(a) for a in ASSAY_LIBRARY if a.name in secondary
        ],
    }


# ---------------------------------------------------------------------------
# Cloud lab integration specs
# ---------------------------------------------------------------------------

@dataclass
class CloudLabSpec:
    """Integration spec for a cloud lab platform."""
    name: str
    url: str
    capabilities: list[str]
    sma_compatible_assays: list[str]
    api_type: str               # REST, Python SDK, GraphQL
    cost_model: str
    turnaround_days: int
    data_format: str


CLOUD_LABS = [
    CloudLabSpec(
        name="Emerald Cloud Lab",
        url="https://emeraldcloudlab.com",
        capabilities=[
            "Liquid handling (multichannel, 96/384-well)",
            "qPCR (QuantStudio 7)",
            "ELISA (plate reader)",
            "Cell culture (incubators, media exchange)",
            "Flow cytometry",
            "Mass spectrometry",
        ],
        sma_compatible_assays=[
            "SMN2 Splicing Reporter (RT-qPCR)",
            "SMN Protein ELISA",
            "RNA-Binding Fluorescence Polarization",
            "Mitochondrial Function (Seahorse XF)",
        ],
        api_type="Python SDK (Symbolic Lab Language)",
        cost_model="Pay-per-experiment + monthly platform fee",
        turnaround_days=7,
        data_format="CSV/JSON via API",
    ),
    CloudLabSpec(
        name="Strateos",
        url="https://strateos.com",
        capabilities=[
            "High-throughput screening (384/1536-well)",
            "Compound management",
            "Automated cell culture",
            "Imaging (Opera Phenix)",
            "Compound cherry-picking",
        ],
        sma_compatible_assays=[
            "SMN2 Splicing Reporter (RT-qPCR)",
            "SMN Protein ELISA",
            "Motor Neuron Survival (iPSC-MN)",
        ],
        api_type="REST API + Web UI",
        cost_model="Subscription + per-run fees",
        turnaround_days=14,
        data_format="JSON/CSV via API",
    ),
    CloudLabSpec(
        name="Opentrons (self-hosted)",
        url="https://opentrons.com",
        capabilities=[
            "Liquid handling (OT-2 or Flex)",
            "PCR prep",
            "ELISA prep",
            "Serial dilution",
            "Plate reformatting",
        ],
        sma_compatible_assays=[
            "SMN2 Splicing Reporter (RT-qPCR)",
            "SMN Protein ELISA",
            "RNA-Binding Fluorescence Polarization",
        ],
        api_type="Python API (opentrons package)",
        cost_model="$10,000 hardware + consumables only",
        turnaround_days=1,
        data_format="Python-generated CSV",
    ),
]


# ---------------------------------------------------------------------------
# API functions
# ---------------------------------------------------------------------------

def get_assay_library() -> dict[str, Any]:
    """Return the complete SMA assay library."""
    by_type = {}
    for a in ASSAY_LIBRARY:
        by_type.setdefault(a.assay_type, []).append(a.name)

    return {
        "total_assays": len(ASSAY_LIBRARY),
        "assays": [asdict(a) for a in ASSAY_LIBRARY],
        "by_type": {k: len(v) for k, v in by_type.items()},
        "automation_ready": [asdict(a) for a in ASSAY_LIBRARY if a.automation_ready],
        "insight": "8 assays cover the full SMA validation pipeline: from RNA binding → "
                   "splicing → protein → cell survival → NMJ → animal model. 4 are cloud-lab "
                   "compatible for automated screening.",
    }


def get_cloud_labs() -> dict[str, Any]:
    """Return cloud lab integration specs."""
    return {
        "total_labs": len(CLOUD_LABS),
        "labs": [asdict(c) for c in CLOUD_LABS],
        "most_sma_assays": asdict(max(CLOUD_LABS, key=lambda x: len(x.sma_compatible_assays))),
        "fastest": asdict(min(CLOUD_LABS, key=lambda x: x.turnaround_days)),
        "insight": "Emerald Cloud Lab supports the most SMA assays (4/8) and has a Python SDK "
                   "for automated experiment design. Opentrons is the cheapest option for labs "
                   "that want to run their own automation.",
    }


def generate_experiment(hypothesis: str) -> dict[str, Any]:
    """Generate a complete experiment design from a hypothesis."""
    return design_experiment(hypothesis)
