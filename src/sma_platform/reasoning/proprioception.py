"""Proprioceptive Pathway Analysis — sensory-motor circuit dysfunction in SMA.

Prof. Christian Simon (Leipzig) research: proprioceptive synapses are severely
affected in SMA. The field focuses on motor neurons but ignores the sensory
side. Simon et al. showed 50% reduction in proprioceptive responses in patients.
"""

from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)

PROPRIOCEPTIVE_KNOWLEDGE = {
    "overview": (
        "Proprioception — the sense of body position in space — is severely "
        "affected in SMA. Proprioceptive sensory neurons (DRG Ia afferents) form "
        "monosynaptic connections onto spinal motor neurons. These synapses are among "
        "the earliest pathological features in SMA, preceding motor neuron death."
    ),
    "key_findings": [
        {
            "finding": "Proprioceptive synaptic loss precedes motor neuron death",
            "source": "Mentis et al., Neuron 2011",
            "pmid": "21482353",
            "significance": "First demonstration that sensory-motor circuit dysfunction is a primary SMA feature, not secondary to motor neuron loss.",
        },
        {
            "finding": "50% reduction in H-reflex (proprioceptive response) in SMA patients",
            "source": "Simon et al., 2024-2025 (Leipzig)",
            "pmid": None,
            "significance": "Clinical evidence in humans that proprioceptive circuits are affected. H-reflex testing could be a biomarker.",
        },
        {
            "finding": "Proprioceptive synapse restoration improves motor function",
            "source": "Capogrosso et al., Pittsburgh",
            "pmid": None,
            "significance": "Epidural spinal cord stimulation activating proprioceptive circuits led to 'spectacular' motor improvements in pilot patients.",
        },
        {
            "finding": "Not all motor neurons are equally vulnerable — selective vulnerability is segment-specific",
            "source": "Simon et al., multiple publications",
            "pmid": "29281826",
            "significance": "Lumbar L1 motor neurons (proximal, vulnerable) vs L5 (distal, resistant). Understanding why requires studying the full sensory-motor circuit.",
        },
    ],
    "therapeutic_implications": [
        "Proprioceptive circuit restoration via epidural stimulation (Capogrosso approach)",
        "Combined therapy: SMN restoration + sensory circuit rehabilitation",
        "H-reflex testing as treatment response biomarker",
        "4-Aminopyridine enhances nerve conduction — may benefit proprioceptive circuits",
    ],
    "relevant_targets": ["SMN1", "SMN2", "NMJ_MATURATION", "STMN2"],
    "ignored_by_field": True,
    "field_controversy": "Most SMA clinicians maintain SMA is 'only a motor neuron disease' despite growing evidence of proprioceptive involvement. Diagnostic testing (H-reflex) exists but is rarely performed.",
}


def get_proprioceptive_analysis() -> dict[str, Any]:
    """Get comprehensive proprioceptive pathway analysis."""
    return PROPRIOCEPTIVE_KNOWLEDGE


def get_h_reflex_testing_info() -> dict[str, Any]:
    """Get information about H-reflex testing for SMA proprioception."""
    return {
        "test_name": "H-reflex (Hoffmann reflex)",
        "what_it_measures": "Proprioceptive monosynaptic circuit integrity",
        "procedure": "Stimulate tibial nerve at popliteal fossa, record from soleus muscle. Low-intensity stimulation activates Ia afferent → spinal cord → motor neuron → muscle pathway.",
        "sma_findings": "~50% reduction in H-reflex amplitude in SMA Type III patients (Simon et al.)",
        "clinical_utility": "Could serve as proprioceptive biomarker for treatment response. Not currently used in standard SMA clinical care.",
        "equipment": "Standard EMG/NCS equipment — available in any neurophysiology lab",
        "advantages": ["Non-invasive", "Quantitative", "Reproducible", "Available in any neuro lab", "Can be done at bedside"],
        "limitation": "Cannot be reliably tested in severely affected (non-ambulatory) patients due to motor weakness masking sensory deficits",
    }
