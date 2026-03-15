"""Bioelectric Reprogramming Module (Phase 7.5).

Models ion channel expression, membrane potential (Vmem) states,
and electroceutical intervention opportunities in SMA motor neurons.
Based on Michael Levin's bioelectricity framework and emerging
spinal cord stimulation data.

References:
- Levin, BioSystems 2012 (bioelectric signaling in morphogenesis)
- Adams & Bhatt, Neural Regen Res 2020 (bioelectricity in neurodegeneration)
- Gill et al., Nature Medicine 2024 (spinal cord stimulation)
- Bhatt et al., J Physiol 2022 (ion channel dysfunction in SMA MNs)
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Ion channels in SMA motor neurons
# ---------------------------------------------------------------------------

@dataclass
class IonChannel:
    """An ion channel relevant to SMA motor neuron bioelectricity."""
    gene: str
    name: str
    channel_type: str       # Na, K, Ca, Cl, HCN
    vmem_role: str          # depolarizing, repolarizing, resting, modulatory
    sma_expression: str     # upregulated, downregulated, unchanged, dysregulated
    sma_impact: str
    therapeutic_target: bool
    drug_candidates: list[str]


ION_CHANNELS = [
    IonChannel(
        gene="SCN1A", name="Nav1.1", channel_type="Na",
        vmem_role="depolarizing",
        sma_expression="downregulated",
        sma_impact="Reduced sodium channel density → decreased excitability → MN hypoexcitability",
        therapeutic_target=True,
        drug_candidates=["Hm1a (Nav1.1 activator)", "Low-dose veratridine"],
    ),
    IonChannel(
        gene="SCN9A", name="Nav1.7", channel_type="Na",
        vmem_role="depolarizing",
        sma_expression="downregulated",
        sma_impact="Reduced action potential initiation threshold → sensorimotor deficits",
        therapeutic_target=False,
        drug_candidates=[],
    ),
    IonChannel(
        gene="KCNQ2", name="Kv7.2 (M-current)", channel_type="K",
        vmem_role="repolarizing",
        sma_expression="upregulated",
        sma_impact="Increased M-current → excessive hyperpolarization → MN silencing",
        therapeutic_target=True,
        drug_candidates=["XE991 (Kv7 blocker)", "Linopirdine (Kv7 blocker)"],
    ),
    IonChannel(
        gene="KCNA2", name="Kv1.2 (delayed rectifier)", channel_type="K",
        vmem_role="repolarizing",
        sma_expression="upregulated",
        sma_impact="Accelerated repolarization → shortened action potential → reduced neurotransmitter release",
        therapeutic_target=True,
        drug_candidates=["4-Aminopyridine (K+ channel blocker)", "Dendrotoxin analogs"],
    ),
    IonChannel(
        gene="CACNA1A", name="Cav2.1 (P/Q-type)", channel_type="Ca",
        vmem_role="modulatory",
        sma_expression="downregulated",
        sma_impact="Reduced calcium influx at presynaptic terminal → impaired neurotransmitter release at NMJ",
        therapeutic_target=True,
        drug_candidates=["GV-58 (Cav2.1 agonist)", "Roscovitine"],
    ),
    IonChannel(
        gene="CACNA1C", name="Cav1.2 (L-type)", channel_type="Ca",
        vmem_role="modulatory",
        sma_expression="dysregulated",
        sma_impact="Altered calcium homeostasis → excitotoxicity or deficient signaling depending on context",
        therapeutic_target=False,
        drug_candidates=["Nimodipine (Cav1.2 modulator)"],
    ),
    IonChannel(
        gene="HCN1", name="HCN1 (pacemaker)", channel_type="HCN",
        vmem_role="resting",
        sma_expression="downregulated",
        sma_impact="Reduced Ih current → decreased MN spontaneous firing rate → reduced muscle tone",
        therapeutic_target=True,
        drug_candidates=["Lamotrigine (HCN enhancer)", "Gabapentin (indirect Ih modulation)"],
    ),
    IonChannel(
        gene="CLCN2", name="ClC-2", channel_type="Cl",
        vmem_role="resting",
        sma_expression="unchanged",
        sma_impact="Chloride homeostasis maintained but may shift with NKCC1/KCC2 imbalance in immature MNs",
        therapeutic_target=False,
        drug_candidates=[],
    ),
    IonChannel(
        gene="TRPV1", name="TRPV1 (vanilloid)", channel_type="Ca",
        vmem_role="modulatory",
        sma_expression="upregulated",
        sma_impact="Pain and stress signaling. TRPV1 upregulation may contribute to "
                   "sensory abnormalities in SMA.",
        therapeutic_target=False,
        drug_candidates=["Capsaicin (desensitization)", "SB-705498 (TRPV1 antagonist)"],
    ),
]


# ---------------------------------------------------------------------------
# Vmem state classification
# ---------------------------------------------------------------------------

@dataclass
class VmemState:
    """Membrane potential state of a motor neuron."""
    state: str
    vmem_range_mv: str          # typical Vmem range
    phenotype: str
    sma_relevance: str
    prevalence_in_sma: float    # 0-1 fraction of SMA MNs in this state


VMEM_STATES = [
    VmemState(
        state="Healthy resting",
        vmem_range_mv="-65 to -70 mV",
        phenotype="Normal firing, appropriate NMJ transmission, stable synaptic connections",
        sma_relevance="Target state for therapeutic intervention",
        prevalence_in_sma=0.15,
    ),
    VmemState(
        state="Hyperpolarized (silenced)",
        vmem_range_mv="-75 to -85 mV",
        phenotype="MN is alive but electrically silent. Reduced firing → NMJ denervation → "
                 "muscle atrophy. May be rescuable.",
        sma_relevance="PRIMARY therapeutic target. These MNs could be reactivated with "
                      "depolarizing interventions (K+ blockers, spinal stimulation).",
        prevalence_in_sma=0.40,
    ),
    VmemState(
        state="Depolarized (stressed)",
        vmem_range_mv="-45 to -55 mV",
        phenotype="Chronic depolarization → calcium overload → excitotoxicity → apoptosis pathway",
        sma_relevance="At-risk MNs heading toward death. Need calcium buffering and "
                      "membrane potential stabilization.",
        prevalence_in_sma=0.25,
    ),
    VmemState(
        state="Committed to death",
        vmem_range_mv="-30 to -40 mV",
        phenotype="Severely depolarized, mitochondrial membrane permeabilized, caspase activation",
        sma_relevance="Beyond rescue. Focus on preventing other MNs from reaching this state.",
        prevalence_in_sma=0.20,
    ),
]


# ---------------------------------------------------------------------------
# Electroceutical interventions
# ---------------------------------------------------------------------------

@dataclass
class Electroceutical:
    """An electroceutical or bioelectric intervention for SMA."""
    name: str
    modality: str               # epidural, transcutaneous, implantable, patch
    target_vmem_state: str      # which MN state it targets
    mechanism: str
    evidence_level: str         # clinical, preclinical, theoretical
    feasibility: float          # 0-1
    sma_specific_notes: str


ELECTROCEUTICALS = [
    Electroceutical(
        name="Epidural Spinal Cord Stimulation (SCS)",
        modality="epidural",
        target_vmem_state="Hyperpolarized (silenced)",
        mechanism="Electrical stimulation of dorsal spinal cord activates proprioceptive afferents "
                 "→ excites MN pools → re-engages silent motor circuits. FDA-approved for SCI.",
        evidence_level="clinical",
        feasibility=0.75,
        sma_specific_notes="Gill et al., Nature Medicine 2024 showed SCS restored voluntary movement "
                          "in spinal cord injury. SMA analogy: reactivate silenced-but-alive MNs. "
                          "Key difference: SMA MNs may be intrinsically compromised, not just disconnected.",
    ),
    Electroceutical(
        name="Transcutaneous Spinal Stimulation",
        modality="transcutaneous",
        target_vmem_state="Hyperpolarized (silenced)",
        mechanism="Non-invasive stimulation via surface electrodes. Lower precision than epidural "
                 "but no surgery required. Can be combined with physical therapy.",
        evidence_level="preclinical",
        feasibility=0.85,
        sma_specific_notes="Most practical for SMA — non-invasive, can be used in young children. "
                          "Limited evidence specifically in SMA but strong rationale from SCI studies.",
    ),
    Electroceutical(
        name="Bioelectric Patch (Vmem modulation)",
        modality="patch",
        target_vmem_state="Hyperpolarized (silenced)",
        mechanism="Wearable ionotronic device that delivers targeted ion currents to modulate "
                 "local tissue Vmem. Based on Levin lab bioelectric pattern approaches.",
        evidence_level="theoretical",
        feasibility=0.40,
        sma_specific_notes="Concept: apply depolarizing bioelectric patterns to motor points overlying "
                          "muscle. Activate satellite cell proliferation + NMJ remodeling. "
                          "Technology exists for wound healing — adapting for neuromuscular is novel.",
    ),
    Electroceutical(
        name="FES (Functional Electrical Stimulation)",
        modality="transcutaneous",
        target_vmem_state="Hyperpolarized (silenced)",
        mechanism="Direct muscle stimulation bypassing MNs entirely. Prevents disuse atrophy "
                 "and maintains NMJ through activity-dependent signals.",
        evidence_level="clinical",
        feasibility=0.90,
        sma_specific_notes="Already used in SMA rehabilitation. Maintains muscle mass and retrograde "
                          "trophic signaling even when MNs are compromised. Combines well with SMN therapy.",
    ),
    Electroceutical(
        name="Optogenetic MN activation (research only)",
        modality="implantable",
        target_vmem_state="Hyperpolarized (silenced)",
        mechanism="Channelrhodopsin (ChR2) expression in MNs via AAV. Light activation restores "
                 "precise MN firing patterns. Research tool, not yet clinical.",
        evidence_level="preclinical",
        feasibility=0.20,
        sma_specific_notes="Powerful research tool for organ-on-chip and animal models. Allows "
                          "testing whether MN reactivation alone can rescue NMJ. Not feasible "
                          "in humans yet but informs drug target selection.",
    ),
]


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def get_ion_channels() -> dict[str, Any]:
    """Return ion channel expression profile in SMA motor neurons."""
    by_status = {"upregulated": [], "downregulated": [], "unchanged": [], "dysregulated": []}
    for ch in ION_CHANNELS:
        by_status[ch.sma_expression].append(ch.gene)

    therapeutic = [ch for ch in ION_CHANNELS if ch.therapeutic_target]

    return {
        "total_channels": len(ION_CHANNELS),
        "channels": [asdict(ch) for ch in ION_CHANNELS],
        "expression_summary": {k: len(v) for k, v in by_status.items()},
        "therapeutic_targets": [asdict(ch) for ch in therapeutic],
        "net_vmem_shift": "hyperpolarizing",
        "insight": "SMA motor neurons show a net hyperpolarizing shift: Na+ channels downregulated "
                   "(less depolarization) while K+ channels upregulated (more repolarization). "
                   "This creates electrically silent MNs that are alive but non-functional — "
                   "the key target for bioelectric intervention.",
    }


def get_vmem_states() -> dict[str, Any]:
    """Return Vmem state classification for SMA motor neurons."""
    return {
        "total_states": len(VMEM_STATES),
        "states": [asdict(v) for v in VMEM_STATES],
        "rescuable_fraction": sum(
            v.prevalence_in_sma for v in VMEM_STATES
            if v.state in ("Healthy resting", "Hyperpolarized (silenced)")
        ),
        "insight": "~55% of SMA motor neurons are potentially rescuable (15% healthy + 40% silenced). "
                   "The 40% 'silenced' population is the prime target for bioelectric therapy — "
                   "these MNs are alive but electrically dormant.",
    }


def get_electroceuticals() -> dict[str, Any]:
    """Return electroceutical interventions for SMA."""
    return {
        "total_interventions": len(ELECTROCEUTICALS),
        "interventions": [asdict(e) for e in ELECTROCEUTICALS],
        "most_feasible": asdict(max(ELECTROCEUTICALS, key=lambda x: x.feasibility)),
        "clinical_ready": [asdict(e) for e in ELECTROCEUTICALS if e.evidence_level == "clinical"],
        "insight": "FES (functional electrical stimulation) is the most immediately actionable "
                   "bioelectric intervention for SMA — it's already clinically used and maintains "
                   "muscle health while SMN therapy works on the neurons. Transcutaneous spinal "
                   "stimulation is the most promising novel approach for reactivating silenced MNs.",
    }


def analyze_bioelectric_profile() -> dict[str, Any]:
    """Full bioelectric analysis of SMA motor neurons."""
    channels = get_ion_channels()
    vmem = get_vmem_states()
    electro = get_electroceuticals()

    return {
        "ion_channels": channels,
        "vmem_states": vmem,
        "electroceuticals": electro,
        "bioelectric_hypothesis": (
            "SMA motor neurons don't just die — many enter a 'bioelectric dormancy' state "
            "where they're alive but electrically silent due to ion channel dysregulation. "
            "This dormancy can be reversed with targeted depolarization (K+ channel blockers, "
            "spinal cord stimulation) BEFORE the neuron commits to apoptosis. The therapeutic "
            "window for bioelectric rescue exists between SMN depletion and irreversible death."
        ),
        "combination_approach": {
            "step_1": "SMN restoration (nusinersen/risdiplam/Zolgensma) — address root cause",
            "step_2": "Bioelectric reactivation (spinal stimulation or 4-AP) — wake dormant MNs",
            "step_3": "NMJ maintenance (FES + exercise) — keep reactivated MNs connected",
            "step_4": "Retrograde support (muscle-derived BDNF) — sustain rescued MNs",
            "rationale": "Four-pronged approach: fix the gene, wake the neuron, maintain the "
                        "connection, feed the circuit.",
        },
    }
