"""SMA Mouse Model Quality Comparison.

Curated data on SMA mouse models and the reproducibility problem:
Prof. Simon found 0-80% variation in motor neuron loss reports across labs
for the same model due to methodology differences.
"""

from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)

SMA_MOUSE_MODELS = [
    {
        "name": "SMNΔ7 (Smn-/-;SMN2+/+;SMNΔ7+/+)",
        "abbreviation": "delta7",
        "severity": "severe (Type I-like)",
        "lifespan": "~13-15 days",
        "smn2_copies": 2,
        "motor_neuron_loss": {"reported_range": "30-80%", "simon_finding": "Highly variable across labs"},
        "strengths": ["Well-characterized", "Widely used", "Rapid disease course for drug testing"],
        "limitations": ["Short lifespan limits chronic studies", "Neonatal — not adult SMA"],
        "key_features": "Rapid onset, severe motor neuron loss in lumbar spinal cord, NMJ denervation, respiratory failure",
        "references": ["PMID:15731223"],
        "usage_frequency": "Most commonly used severe SMA model",
    },
    {
        "name": "Smn2B/- (Smn2B/-)",
        "abbreviation": "2B",
        "severity": "intermediate",
        "lifespan": "~25-30 days",
        "smn2_copies": "N/A (Smn point mutation)",
        "motor_neuron_loss": {"reported_range": "0-50%", "simon_finding": "Simon found 0% in some analyses — contradicts many publications"},
        "strengths": ["Longer lifespan than delta7", "Intermediate severity", "Good for drug timing studies"],
        "limitations": ["Less widely used", "Phenotype variability between colonies"],
        "key_features": "Progressive weakness, moderate motor neuron loss, proprioceptive deficits (Simon lab), used in p53 studies",
        "references": ["PMID:21172648"],
        "usage_frequency": "Second most common model",
    },
    {
        "name": "Taiwanese (Smn-/-;SMN2(2 copies))",
        "abbreviation": "taiwanese",
        "severity": "severe",
        "lifespan": "~10-12 days",
        "smn2_copies": 2,
        "motor_neuron_loss": {"reported_range": "50-70%", "simon_finding": "Consistent with other models when properly analyzed"},
        "strengths": ["Very severe — good for gene therapy testing", "Clean genetic background"],
        "limitations": ["Very short lifespan", "Breeding difficulties"],
        "key_features": "Severe phenotype, used in onasemnogene preclinical studies",
        "references": ["PMID:16100078"],
        "usage_frequency": "Common in gene therapy studies",
    },
    {
        "name": "4-copy SMN2 (Smn-/-;SMN2(4 copies))",
        "abbreviation": "4copy",
        "severity": "mild (Type III-like)",
        "lifespan": "Normal (~2 years)",
        "smn2_copies": 4,
        "motor_neuron_loss": {"reported_range": "0-20%", "simon_finding": "Minimal motor neuron loss, progressive motor dysfunction"},
        "strengths": ["Adult onset", "Chronic disease modeling", "Relevant to Type III patients"],
        "limitations": ["Slow progression", "Expensive (long studies)", "Less dramatic phenotype"],
        "key_features": "Late-onset, progressive motor dysfunction, astrocyte-mediated pathology",
        "references": ["PMID:41540953"],
        "usage_frequency": "Increasing use for late-onset SMA studies",
    },
    {
        "name": "Burghes Allele (SMN2 C>T only)",
        "abbreviation": "burghes",
        "severity": "varies by copy number",
        "lifespan": "Depends on SMN2 copies",
        "smn2_copies": "Variable",
        "motor_neuron_loss": {"reported_range": "Variable", "simon_finding": "Well-controlled genetic background"},
        "strengths": ["Clean genetic model", "Precise SMN2 copy control"],
        "limitations": ["Less commonly used"],
        "key_features": "Pure SMN2 copy-number model",
        "references": [],
        "usage_frequency": "Specialized studies",
    },
]

METHODOLOGY_PROBLEMS = {
    "variation": "0-80% reported motor neuron loss variation in same model across labs",
    "causes": [
        "Wrong spinal cord segment analyzed (L1 vs L5 — huge difference in motor neuron numbers)",
        "Non-stereological counting methods (profile counting overestimates loss)",
        "Non-specific antibodies (ChAT antibody specificity varies by lot)",
        "Incomplete tissue fixation and processing",
        "Counting motor neurons in wrong anatomical pools",
        "Not reporting which segments were analyzed",
    ],
    "simon_recommendation": "Use machine learning-based automated counting with segment verification. Always report exact segments analyzed.",
    "gold_standard": "Serial section reconstruction with stereological counting in identified segments",
}


def get_mouse_models() -> list[dict]:
    """Get all SMA mouse models with quality comparison."""
    return SMA_MOUSE_MODELS


def get_methodology_problems() -> dict[str, Any]:
    """Get the motor neuron counting reproducibility problem."""
    return METHODOLOGY_PROBLEMS


def compare_models(model_a: str, model_b: str) -> dict[str, Any]:
    """Compare two SMA mouse models."""
    ma = next((m for m in SMA_MOUSE_MODELS if m["abbreviation"] == model_a.lower()), None)
    mb = next((m for m in SMA_MOUSE_MODELS if m["abbreviation"] == model_b.lower()), None)
    if not ma or not mb:
        available = [m["abbreviation"] for m in SMA_MOUSE_MODELS]
        return {"error": f"Model not found. Available: {available}"}
    return {"model_a": ma, "model_b": mb}
