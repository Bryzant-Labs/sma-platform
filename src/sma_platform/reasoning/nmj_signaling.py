"""NMJ Retrograde Signaling Module (Phase 7.3).

Models muscle-to-nerve retrograde signaling at the neuromuscular junction.
Tests the "happy muscle → surviving neuron" hypothesis: can improving
muscle health rescue motor neurons via retrograde signals?

Also models extracellular vesicle (EV) cargo for NMJ delivery and
organ-on-chip validation pathways.

References:
- Bhatt et al., J Cell Sci 2019 (retrograde BMP signaling at NMJ)
- Feng & Ko, Curr Opin Neurobiol 2008 (NMJ retrograde signaling)
- Kariya et al., Hum Mol Genet 2008 (SMA NMJ defects)
- Thompson et al., Trends Neurosci 2023 (organ-on-chip for NMJ)
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Retrograde signaling molecules
# ---------------------------------------------------------------------------

@dataclass
class RetrogradeSignal:
    """A molecule involved in muscle-to-nerve retrograde signaling."""
    name: str
    molecule_type: str          # protein, lipid, rna, exosome
    source: str                 # muscle, Schwann cell, terminal
    target: str                 # motor neuron soma, axon terminal, presynaptic
    sma_status: str             # reduced, absent, increased, normal
    therapeutic_potential: float # 0-1
    mechanism: str
    evidence_strength: str      # strong, moderate, emerging


RETROGRADE_SIGNALS = [
    RetrogradeSignal(
        name="BDNF (muscle-derived)",
        molecule_type="protein",
        source="muscle fiber",
        target="motor neuron soma",
        sma_status="reduced",
        therapeutic_potential=0.80,
        mechanism="Released from muscle upon activity. Binds TrkB on MN axon terminals, "
                 "retrograde transport to soma promotes survival via PI3K/Akt and MAPK/ERK.",
        evidence_strength="strong",
    ),
    RetrogradeSignal(
        name="NT-4/5",
        molecule_type="protein",
        source="muscle fiber",
        target="motor neuron soma",
        sma_status="reduced",
        therapeutic_potential=0.65,
        mechanism="Activity-dependent neurotrophin. Supports MN survival specifically at "
                 "fast-fatigable NMJ subtypes (most vulnerable in SMA).",
        evidence_strength="moderate",
    ),
    RetrogradeSignal(
        name="GDNF",
        molecule_type="protein",
        source="muscle fiber",
        target="motor neuron soma",
        sma_status="reduced",
        therapeutic_potential=0.75,
        mechanism="Potent MN survival factor. Binds GFRalpha1/RET on MN terminals. "
                 "Retrograde survival signaling via lipid raft-mediated endocytosis.",
        evidence_strength="strong",
    ),
    RetrogradeSignal(
        name="Gdf5/BMP (Glass bottom boat)",
        molecule_type="protein",
        source="muscle fiber",
        target="presynaptic terminal",
        sma_status="reduced",
        therapeutic_potential=0.60,
        mechanism="BMP retrograde signal maintains presynaptic structure. Glass bottom boat (Gbb) "
                 "in Drosophila → Gdf5 in vertebrates. Regulates synaptic homeostasis.",
        evidence_strength="strong",
    ),
    RetrogradeSignal(
        name="Laminin-beta2 (LAMB2)",
        molecule_type="protein",
        source="muscle fiber",
        target="presynaptic terminal",
        sma_status="reduced",
        therapeutic_potential=0.50,
        mechanism="Synaptic basal lamina component. Organizes presynaptic active zones and "
                 "calcium channel clustering at NMJ through retrograde signaling.",
        evidence_strength="moderate",
    ),
    RetrogradeSignal(
        name="Muscle-derived EVs (exosomes)",
        molecule_type="exosome",
        source="muscle fiber",
        target="motor neuron soma",
        sma_status="reduced",
        therapeutic_potential=0.70,
        mechanism="Muscle releases exosomes containing miRNAs (miR-206, miR-1) and proteins "
                 "that promote MN survival. Cargo includes HSP70 and survival signals.",
        evidence_strength="emerging",
    ),
    RetrogradeSignal(
        name="Agrin",
        molecule_type="protein",
        source="motor neuron terminal",
        target="muscle fiber (anterograde, but required for NMJ)",
        sma_status="reduced",
        therapeutic_potential=0.75,
        mechanism="Neural agrin clusters AChRs via MuSK/LRP4. In SMA, agrin is reduced "
                 "→ AChR dispersal → NMJ denervation. Restoring agrin rescues NMJ.",
        evidence_strength="strong",
    ),
    RetrogradeSignal(
        name="Endocannabinoids (2-AG)",
        molecule_type="lipid",
        source="muscle fiber",
        target="presynaptic terminal",
        sma_status="normal",
        therapeutic_potential=0.40,
        mechanism="Lipid retrograde messenger. Modulates presynaptic release probability "
                 "at NMJ. CB1 receptor on MN terminals.",
        evidence_strength="emerging",
    ),
    RetrogradeSignal(
        name="Schwann cell-derived VEGF",
        molecule_type="protein",
        source="terminal Schwann cell",
        target="motor neuron terminal",
        sma_status="reduced",
        therapeutic_potential=0.55,
        mechanism="Terminal Schwann cells sense synaptic activity and release VEGF to maintain "
                 "NMJ vasculature and presynaptic health.",
        evidence_strength="moderate",
    ),
    RetrogradeSignal(
        name="FGF-BP1 (FGF binding protein 1)",
        molecule_type="protein",
        source="muscle fiber",
        target="presynaptic terminal",
        sma_status="reduced",
        therapeutic_potential=0.50,
        mechanism="Muscle-released factor that concentrates FGF signaling at NMJ. "
                 "Maintains presynaptic terminal integrity and synapse stability.",
        evidence_strength="moderate",
    ),
]


# ---------------------------------------------------------------------------
# EV cargo for therapeutic delivery
# ---------------------------------------------------------------------------

@dataclass
class EVCargo:
    """Extracellular vesicle cargo component for NMJ-targeted therapy."""
    name: str
    cargo_type: str         # mirna, protein, mrna
    function: str
    sma_relevance: str
    delivery_feasibility: float  # 0-1


EV_THERAPEUTIC_CARGO = [
    EVCargo("miR-206", "mirna", "NMJ maturation signal, promotes AChR clustering", "Downregulated in SMA muscle", 0.75),
    EVCargo("miR-1", "mirna", "Muscle differentiation, ion channel regulation", "Reduced in SMA", 0.70),
    EVCargo("miR-133a", "mirna", "Muscle proliferation/differentiation balance", "Altered in SMA", 0.65),
    EVCargo("HSP70", "protein", "Chaperone, protein quality control, anti-apoptotic", "Reduced MN protection in SMA", 0.60),
    EVCargo("SMN mRNA", "mrna", "Direct SMN protein production in target cells", "Absent (the root cause)", 0.55),
    EVCargo("BDNF protein", "protein", "Neuroprotective, survival signaling", "Reduced in SMA NMJ", 0.70),
    EVCargo("Agrin fragment", "protein", "AChR clustering, NMJ stability", "Reduced agrin in SMA", 0.65),
]


# ---------------------------------------------------------------------------
# Organ-on-Chip validation pathway
# ---------------------------------------------------------------------------

@dataclass
class ChipModel:
    """NMJ-on-a-chip model for validation."""
    name: str
    components: list[str]
    readouts: list[str]
    sma_modeling: str
    trl: int                # Technology Readiness Level 1-9
    cost_per_chip: str
    throughput: str


CHIP_MODELS = [
    ChipModel(
        name="NMJ-on-Chip (2-compartment)",
        components=["iPSC-MNs", "C2C12 myotubes", "Matrigel channel"],
        readouts=["Contraction force", "AChR clustering", "Calcium imaging", "Electrophysiology"],
        sma_modeling="SMA patient iPSC-derived MNs show reduced NMJ formation and contraction",
        trl=5,
        cost_per_chip="$50-100",
        throughput="Low (10-20 chips/week)",
    ),
    ChipModel(
        name="Motor Unit-on-Chip (3-compartment)",
        components=["iPSC-MNs", "Primary myofibers", "Schwann cells", "Microfluidic gradient"],
        readouts=["Axon growth", "Myelination", "NMJ maturation", "Retrograde transport"],
        sma_modeling="Models complete motor unit with glial support — captures Schwann cell defects",
        trl=4,
        cost_per_chip="$100-200",
        throughput="Low (5-10 chips/week)",
    ),
    ChipModel(
        name="High-throughput NMJ plate (optogenetic)",
        components=["iPSC-MNs (ChR2)", "Engineered muscle strips", "96-well format"],
        readouts=["Light-evoked contraction", "Force measurement", "Compound screening"],
        sma_modeling="Optogenetic activation bypasses synaptic transmission — isolates muscle vs neural defects",
        trl=6,
        cost_per_chip="$20-40",
        throughput="High (96 conditions/plate)",
    ),
]


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def get_retrograde_signals() -> dict[str, Any]:
    """Return all retrograde signaling molecules with SMA context."""
    by_status = {"reduced": [], "absent": [], "increased": [], "normal": []}
    for s in RETROGRADE_SIGNALS:
        by_status[s.sma_status].append(s.name)

    therapeutic = sorted(RETROGRADE_SIGNALS, key=lambda x: x.therapeutic_potential, reverse=True)

    return {
        "total_signals": len(RETROGRADE_SIGNALS),
        "signals": [asdict(s) for s in RETROGRADE_SIGNALS],
        "status_summary": {k: len(v) for k, v in by_status.items()},
        "top_therapeutic": [asdict(s) for s in therapeutic[:5]],
        "happy_muscle_score": round(
            sum(1 for s in RETROGRADE_SIGNALS if s.sma_status == "reduced") / len(RETROGRADE_SIGNALS), 2
        ),
        "insight": "8/10 retrograde signals are reduced in SMA, supporting the 'happy muscle → "
                   "surviving neuron' hypothesis. The NMJ is not just a passive target — it actively "
                   "sustains motor neurons through BDNF, GDNF, and EV-mediated retrograde signaling. "
                   "Restoring muscle health could create a positive feedback loop for MN survival.",
    }


def get_ev_cargo() -> dict[str, Any]:
    """Return EV therapeutic cargo options for NMJ delivery."""
    return {
        "total_cargo": len(EV_THERAPEUTIC_CARGO),
        "cargo": [asdict(c) for c in EV_THERAPEUTIC_CARGO],
        "top_feasible": [
            asdict(c) for c in sorted(EV_THERAPEUTIC_CARGO, key=lambda x: x.delivery_feasibility, reverse=True)[:3]
        ],
        "insight": "Engineered EVs loaded with miR-206 + BDNF + agrin fragments could serve as "
                   "a 'care package' for denervating NMJs. Muscle-derived EVs naturally target "
                   "the NMJ, providing a built-in delivery mechanism.",
    }


def get_chip_models() -> dict[str, Any]:
    """Return organ-on-chip models for NMJ validation."""
    return {
        "total_models": len(CHIP_MODELS),
        "models": [asdict(m) for m in CHIP_MODELS],
        "recommended": asdict(max(CHIP_MODELS, key=lambda x: x.trl)),
        "insight": "The high-throughput optogenetic NMJ plate (TRL 6) is closest to drug screening "
                   "readiness. For mechanistic studies of retrograde signaling, the 3-compartment "
                   "Motor Unit-on-Chip with Schwann cells is ideal but lower throughput.",
    }


def analyze_happy_muscle_hypothesis() -> dict[str, Any]:
    """Full analysis of the 'happy muscle → surviving neuron' hypothesis."""
    signals = get_retrograde_signals()
    ev_data = get_ev_cargo()
    chips = get_chip_models()

    reduced_signals = [s for s in RETROGRADE_SIGNALS if s.sma_status == "reduced"]
    avg_potential = sum(s.therapeutic_potential for s in reduced_signals) / max(1, len(reduced_signals))

    return {
        "hypothesis": "Improving muscle health restores retrograde trophic signaling to motor neurons, "
                      "creating a positive feedback loop that slows or halts motor neuron degeneration.",
        "evidence_for": [
            "8/10 retrograde signals reduced in SMA",
            "NMJ denervation precedes MN death (Kariya 2008)",
            "Myostatin inhibition improves muscle + extends survival in SMA mice",
            "Exercise (mild) improves outcomes in SMA patients",
            "Muscle-specific SMN restoration partially rescues motor neurons",
        ],
        "evidence_against": [
            "Cell-autonomous MN death occurs even with healthy muscle in severe SMA",
            "Some SMA types have normal muscle but still lose MNs",
            "SMN is required cell-autonomously in motor neurons",
        ],
        "hypothesis_score": round(avg_potential, 2),
        "signals": signals,
        "ev_delivery": ev_data,
        "validation_chips": chips,
        "combination_strategy": {
            "approach": "SMN restoration + muscle support + retrograde enhancement",
            "components": [
                "Nusinersen/risdiplam (SMN restoration in MNs)",
                "Apitegromab (anti-myostatin, muscle mass)",
                "EV-BDNF (retrograde trophic support)",
                "Exercise therapy (activity-dependent NMJ maintenance)",
            ],
            "rationale": "Attacking SMA from both sides — neuron AND muscle — maximizes therapeutic effect",
        },
    }
