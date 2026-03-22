#!/usr/bin/env python3
"""Seed script: populate bioelectric tables from hardcoded reasoning module data.

Run once after migration 023:
    cd /home/bryzant/sma-platform
    source venv/bin/activate
    python db/seeds/seed_bioelectric.py
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, "/home/bryzant/sma-platform/src")

from sma_platform.core.database import execute, init_pool

DSN = os.environ.get("DATABASE_URL", "postgresql://sma:sma-research-2026@localhost:5432/sma_platform")

CHANNELS = [
    {"gene": "SCN1A", "channel_name": "Nav1.1", "channel_type": "Na", "vmem_role": "depolarizing", "sma_expression": "downregulated", "sma_impact": "Reduced sodium channel density -> decreased excitability -> MN hypoexcitability", "therapeutic_target": True, "drug_candidates": ["Hm1a (Nav1.1 activator)", "Low-dose veratridine"]},
    {"gene": "SCN9A", "channel_name": "Nav1.7", "channel_type": "Na", "vmem_role": "depolarizing", "sma_expression": "downregulated", "sma_impact": "Reduced action potential initiation threshold -> sensorimotor deficits", "therapeutic_target": False, "drug_candidates": []},
    {"gene": "KCNQ2", "channel_name": "Kv7.2 (M-current)", "channel_type": "K", "vmem_role": "repolarizing", "sma_expression": "upregulated", "sma_impact": "Increased M-current -> excessive hyperpolarization -> MN silencing", "therapeutic_target": True, "drug_candidates": ["XE991 (Kv7 blocker)", "Linopirdine (Kv7 blocker)"]},
    {"gene": "KCNA2", "channel_name": "Kv1.2 (delayed rectifier)", "channel_type": "K", "vmem_role": "repolarizing", "sma_expression": "upregulated", "sma_impact": "Accelerated repolarization -> shortened action potential -> reduced neurotransmitter release", "therapeutic_target": True, "drug_candidates": ["4-Aminopyridine (K+ channel blocker)", "Dendrotoxin analogs"]},
    {"gene": "CACNA1A", "channel_name": "Cav2.1 (P/Q-type)", "channel_type": "Ca", "vmem_role": "modulatory", "sma_expression": "downregulated", "sma_impact": "Reduced calcium influx at presynaptic terminal -> impaired neurotransmitter release at NMJ", "therapeutic_target": True, "drug_candidates": ["GV-58 (Cav2.1 agonist)", "Roscovitine"]},
    {"gene": "CACNA1C", "channel_name": "Cav1.2 (L-type)", "channel_type": "Ca", "vmem_role": "modulatory", "sma_expression": "dysregulated", "sma_impact": "Altered calcium homeostasis -> excitotoxicity or deficient signaling depending on context", "therapeutic_target": False, "drug_candidates": ["Nimodipine (Cav1.2 modulator)"]},
    {"gene": "HCN1", "channel_name": "HCN1 (pacemaker)", "channel_type": "HCN", "vmem_role": "resting", "sma_expression": "downregulated", "sma_impact": "Reduced Ih current -> decreased MN spontaneous firing rate -> reduced muscle tone", "therapeutic_target": True, "drug_candidates": ["Lamotrigine (HCN enhancer)", "Gabapentin (indirect Ih modulation)"]},
    {"gene": "CLCN2", "channel_name": "ClC-2", "channel_type": "Cl", "vmem_role": "resting", "sma_expression": "unchanged", "sma_impact": "Chloride homeostasis maintained but may shift with NKCC1/KCC2 imbalance in immature MNs", "therapeutic_target": False, "drug_candidates": []},
    {"gene": "TRPV1", "channel_name": "TRPV1 (vanilloid)", "channel_type": "Ca", "vmem_role": "modulatory", "sma_expression": "upregulated", "sma_impact": "Pain and stress signaling. TRPV1 upregulation may contribute to sensory abnormalities in SMA.", "therapeutic_target": False, "drug_candidates": ["Capsaicin (desensitization)", "SB-705498 (TRPV1 antagonist)"]},
]

VMEM_STATES = [
    {"state_name": "Healthy resting", "vmem_range": "-65 to -70 mV", "phenotype": "Normal firing, appropriate NMJ transmission, stable synaptic connections", "sma_relevance": "Target state for therapeutic intervention", "prevalence_in_sma": 0.15, "therapeutic_target": False},
    {"state_name": "Hyperpolarized (silenced)", "vmem_range": "-75 to -85 mV", "phenotype": "MN is alive but electrically silent. Reduced firing -> NMJ denervation -> muscle atrophy. May be rescuable.", "sma_relevance": "PRIMARY therapeutic target. These MNs could be reactivated with depolarizing interventions (K+ blockers, spinal stimulation).", "prevalence_in_sma": 0.40, "therapeutic_target": True},
    {"state_name": "Depolarized (stressed)", "vmem_range": "-45 to -55 mV", "phenotype": "Chronic depolarization -> calcium overload -> excitotoxicity -> apoptosis pathway", "sma_relevance": "At-risk MNs heading toward death. Need calcium buffering and membrane potential stabilization.", "prevalence_in_sma": 0.25, "therapeutic_target": True},
    {"state_name": "Committed to death", "vmem_range": "-30 to -40 mV", "phenotype": "Severely depolarized, mitochondrial membrane permeabilized, caspase activation", "sma_relevance": "Beyond rescue. Focus on preventing other MNs from reaching this state.", "prevalence_in_sma": 0.20, "therapeutic_target": False},
]

INTERVENTIONS = [
    {"name": "Epidural Spinal Cord Stimulation (SCS)", "modality": "epidural", "target_vmem_state": "Hyperpolarized (silenced)", "mechanism": "Electrical stimulation of dorsal spinal cord activates proprioceptive afferents -> excites MN pools -> re-engages silent motor circuits. FDA-approved for SCI.", "evidence_level": "clinical", "feasibility": 0.75, "sma_specific_notes": "Gill et al., Nature Medicine 2024 showed SCS restored voluntary movement in spinal cord injury. SMA analogy: reactivate silenced-but-alive MNs."},
    {"name": "Transcutaneous Spinal Stimulation", "modality": "transcutaneous", "target_vmem_state": "Hyperpolarized (silenced)", "mechanism": "Non-invasive stimulation via surface electrodes. Lower precision than epidural but no surgery required. Can be combined with physical therapy.", "evidence_level": "preclinical", "feasibility": 0.85, "sma_specific_notes": "Most practical for SMA -- non-invasive, can be used in young children. Limited evidence specifically in SMA but strong rationale from SCI studies."},
    {"name": "Bioelectric Patch (Vmem modulation)", "modality": "patch", "target_vmem_state": "Hyperpolarized (silenced)", "mechanism": "Wearable ionotronic device that delivers targeted ion currents to modulate local tissue Vmem. Based on Levin lab bioelectric pattern approaches.", "evidence_level": "theoretical", "feasibility": 0.40, "sma_specific_notes": "Concept: apply depolarizing bioelectric patterns to motor points overlying muscle. Activate satellite cell proliferation + NMJ remodeling."},
    {"name": "FES (Functional Electrical Stimulation)", "modality": "transcutaneous", "target_vmem_state": "Hyperpolarized (silenced)", "mechanism": "Direct muscle stimulation bypassing MNs entirely. Prevents disuse atrophy and maintains NMJ through activity-dependent signals.", "evidence_level": "clinical", "feasibility": 0.90, "sma_specific_notes": "Already used in SMA rehabilitation. Maintains muscle mass and retrograde trophic signaling even when MNs are compromised. Combines well with SMN therapy."},
    {"name": "Optogenetic MN activation (research only)", "modality": "implantable", "target_vmem_state": "Hyperpolarized (silenced)", "mechanism": "Channelrhodopsin (ChR2) expression in MNs via AAV. Light activation restores precise MN firing patterns. Research tool, not yet clinical.", "evidence_level": "preclinical", "feasibility": 0.20, "sma_specific_notes": "Powerful research tool for organ-on-chip and animal models. Allows testing whether MN reactivation alone can rescue NMJ."},
]


async def seed():
    await init_pool(DSN)

    ch_ins = 0
    ch_skip = 0
    for ch in CHANNELS:
        try:
            r = await execute(
                """INSERT INTO bioelectric_channels
                   (gene, channel_name, channel_type, vmem_role, sma_expression,
                    sma_impact, therapeutic_target, drug_candidates)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                   ON CONFLICT (gene, channel_name) DO NOTHING""",
                ch["gene"], ch["channel_name"], ch["channel_type"],
                ch["vmem_role"], ch["sma_expression"], ch["sma_impact"],
                ch["therapeutic_target"], ch["drug_candidates"],
            )
            if "INSERT 0 1" in str(r):
                ch_ins += 1
            else:
                ch_skip += 1
        except Exception as e:
            print(f"  ERROR channel {ch['gene']}: {e}")
    print(f"Channels: {ch_ins} inserted, {ch_skip} skipped")

    vs_ins = 0
    vs_skip = 0
    for vs in VMEM_STATES:
        try:
            r = await execute(
                """INSERT INTO bioelectric_vmem_states
                   (state_name, vmem_range, phenotype, sma_relevance, prevalence_in_sma, therapeutic_target)
                   VALUES ($1, $2, $3, $4, $5, $6)
                   ON CONFLICT (state_name) DO NOTHING""",
                vs["state_name"], vs["vmem_range"], vs["phenotype"],
                vs["sma_relevance"], vs["prevalence_in_sma"], vs["therapeutic_target"],
            )
            if "INSERT 0 1" in str(r):
                vs_ins += 1
            else:
                vs_skip += 1
        except Exception as e:
            print(f"  ERROR vmem {vs['state_name']}: {e}")
    print(f"Vmem states: {vs_ins} inserted, {vs_skip} skipped")

    iv_ins = 0
    iv_skip = 0
    for iv in INTERVENTIONS:
        try:
            r = await execute(
                """INSERT INTO bioelectric_interventions
                   (name, modality, target_vmem_state, mechanism, evidence_level,
                    feasibility, sma_specific_notes)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)
                   ON CONFLICT (name) DO NOTHING""",
                iv["name"], iv["modality"], iv["target_vmem_state"],
                iv["mechanism"], iv["evidence_level"],
                iv["feasibility"], iv["sma_specific_notes"],
            )
            if "INSERT 0 1" in str(r):
                iv_ins += 1
            else:
                iv_skip += 1
        except Exception as e:
            print(f"  ERROR intervention {iv['name']}: {e}")
    print(f"Interventions: {iv_ins} inserted, {iv_skip} skipped")
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
