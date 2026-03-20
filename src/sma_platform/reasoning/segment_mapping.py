"""Spinal Cord Segment Mapping — L1-L5 motor neuron vulnerability in SMA.

Different spinal cord segments have vastly different motor neuron vulnerability.
Prof. Simon found 0-80% variation in reported motor neuron loss depending on
which segment was analyzed — a major source of irreproducibility in SMA research.
"""

from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)

SPINAL_SEGMENTS = [
    {
        "segment": "C3-C5",
        "region": "Cervical",
        "innervation": "Diaphragm (phrenic nerve)",
        "vulnerability": "moderate",
        "sma_relevance": "Respiratory failure in Type I — phrenic motor neurons affected",
        "motor_neurons": "~200-300 per segment",
    },
    {
        "segment": "C5-T1",
        "region": "Cervical",
        "innervation": "Upper limbs (biceps, deltoid, hand muscles)",
        "vulnerability": "moderate",
        "sma_relevance": "Upper limb weakness — RULM score reflects this",
        "motor_neurons": "~300-500 per segment",
    },
    {
        "segment": "L1-L3",
        "region": "Lumbar (proximal)",
        "innervation": "Hip flexors, quadriceps (proximal muscles)",
        "vulnerability": "HIGH — most vulnerable",
        "sma_relevance": "Proximal weakness is hallmark of SMA. L1 motor neurons preferentially lost. Simon: this is where you see the most consistent degeneration.",
        "motor_neurons": "~700 per segment (L1 pool is round and flat)",
    },
    {
        "segment": "L4-L5",
        "region": "Lumbar (distal)",
        "innervation": "Tibialis anterior, foot muscles (distal muscles)",
        "vulnerability": "LOW — relatively resistant",
        "sma_relevance": "Distal muscles spared longer. L5 motor neurons resistant in mouse models. Simon: L5 pool is large and elongated — distinct morphology from L1.",
        "motor_neurons": "~500-700 per segment (L5 pool is large, elongated)",
    },
    {
        "segment": "S1-S2",
        "region": "Sacral",
        "innervation": "Calf muscles, foot intrinsics",
        "vulnerability": "low",
        "sma_relevance": "Relatively spared — patients retain some distal function",
        "motor_neurons": "~200-400 per segment",
    },
]

SEGMENT_CONTROVERSY = {
    "problem": (
        "Simon et al. (5-year study) found 0-80% reported motor neuron loss "
        "variation in the SAME mouse model across different labs. Main causes: "
        "wrong segment analyzed, poor tissue preparation, non-specific antibodies, "
        "lack of stereological counting methods."
    ),
    "simon_solution": "Machine learning-based automated motor neuron counting with segment verification",
    "implication": "Many published SMA mouse model studies have unreliable motor neuron counts",
    "recommendation": "Always report which specific segment was analyzed (L1 vs L5 matters enormously)",
}


def get_segment_map() -> dict[str, Any]:
    """Get comprehensive spinal cord segment vulnerability map."""
    return {
        "segments": SPINAL_SEGMENTS,
        "controversy": SEGMENT_CONTROVERSY,
        "key_message": (
            "Proximal motor neurons (L1-L3) are highly vulnerable in SMA while "
            "distal motor neurons (L4-L5) are relatively resistant. This gradient "
            "explains why SMA patients lose proximal function first (climbing stairs, "
            "getting up from chairs) while retaining distal function (hand grip, foot movement)."
        ),
    }
