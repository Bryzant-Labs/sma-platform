"""Cross-Disease Drug Repurposing — find drugs from related diseases for SMA.

Identifies approved/clinical drugs from ALS, DMD, CMT, SBMA, and other
motor neuron diseases that share molecular targets with SMA.
"""

from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Drugs from related neuromuscular diseases with potential SMA relevance
CROSS_DISEASE_CANDIDATES = [
    # ALS drugs
    {
        "drug": "Riluzole",
        "approved_for": "ALS",
        "mechanism": "Glutamate release inhibitor, neuroprotective",
        "shared_pathway": "Motor neuron survival, excitotoxicity protection",
        "sma_targets": ["NMJ_MATURATION", "SMN_PROTEIN"],
        "rationale": "Riluzole's neuroprotective mechanism could complement SMN-targeting therapies. Aminothiazole scaffold matches our UBA1 screening hit.",
        "clinical_status": "FDA approved (ALS), not tested in SMA",
        "evidence_score": 0.65,
    },
    {
        "drug": "Edaravone (Radicava)",
        "approved_for": "ALS",
        "mechanism": "Free radical scavenger, antioxidant",
        "shared_pathway": "Oxidative stress, mitochondrial protection",
        "sma_targets": ["SPATA18", "MTOR_PATHWAY"],
        "rationale": "SMA motor neurons show mitochondrial dysfunction. Edaravone could reduce oxidative damage in SMN-deficient cells.",
        "clinical_status": "FDA approved (ALS)",
        "evidence_score": 0.55,
    },
    {
        "drug": "Tofersen (Qalsody)",
        "approved_for": "ALS (SOD1)",
        "mechanism": "ASO targeting SOD1 mRNA",
        "shared_pathway": "Antisense oligonucleotide technology, intrathecal delivery",
        "sma_targets": ["SMN2"],
        "rationale": "Same ASO technology platform as nusinersen. Delivery route and manufacturing learnings directly transferable.",
        "clinical_status": "FDA approved (ALS-SOD1)",
        "evidence_score": 0.75,
    },
    # DMD drugs
    {
        "drug": "Deflazacort (Emflaza)",
        "approved_for": "DMD",
        "mechanism": "Corticosteroid, anti-inflammatory",
        "shared_pathway": "Muscle preservation, NMJ stability",
        "sma_targets": ["NMJ_MATURATION", "PLS3"],
        "rationale": "Corticosteroids maintain muscle mass in DMD. SMA patients also lose muscle — deflazacort could slow denervation atrophy.",
        "clinical_status": "FDA approved (DMD)",
        "evidence_score": 0.45,
    },
    {
        "drug": "Eteplirsen (Exondys 51)",
        "approved_for": "DMD",
        "mechanism": "Exon-skipping ASO (exon 51)",
        "shared_pathway": "Exon skipping, pre-mRNA splicing modification",
        "sma_targets": ["SMN2"],
        "rationale": "Exon-skipping technology directly relevant to SMN2 exon 7 inclusion. Platform learnings applicable.",
        "clinical_status": "FDA approved (DMD)",
        "evidence_score": 0.70,
    },
    {
        "drug": "Givinostat (Duvyzat)",
        "approved_for": "DMD",
        "mechanism": "HDAC inhibitor",
        "shared_pathway": "Epigenetic regulation, SMN2 expression",
        "sma_targets": ["SMN2", "DNMT3B"],
        "rationale": "HDAC inhibitors increase SMN2 expression in preclinical SMA models. Givinostat is an approved HDAC inhibitor with known safety profile.",
        "clinical_status": "FDA approved (DMD), Phase 2 concepts for SMA",
        "evidence_score": 0.80,
    },
    # Myasthenia Gravis drugs
    {
        "drug": "Efgartigimod (Vyvgart)",
        "approved_for": "Myasthenia Gravis",
        "mechanism": "FcRn antagonist, reduces pathogenic antibodies",
        "shared_pathway": "NMJ protection, immune modulation",
        "sma_targets": ["NMJ_MATURATION"],
        "rationale": "NMJ dysfunction is central to both MG and SMA. Protecting NMJ integrity could complement SMN restoration.",
        "clinical_status": "FDA approved (MG)",
        "evidence_score": 0.40,
    },
    # Neuropathy drugs
    {
        "drug": "4-Aminopyridine (Dalfampridine/Fampyra)",
        "approved_for": "Multiple Sclerosis (walking improvement)",
        "mechanism": "K+ channel blocker, enhances nerve conduction",
        "shared_pathway": "Nerve conduction, motor function",
        "sma_targets": ["CORO1C", "SMN2", "UBA1", "NCALD"],
        "rationale": "Our DiffDock screening found 4-AP has the strongest binding to CORO1C (+0.251) of all tested compounds. Multi-target profile across 5 SMA proteins. Previously tested in SMA (NCT01645787) but failed — our binding data suggests a different mechanism beyond K+ channels.",
        "clinical_status": "FDA approved (MS), failed in SMA trial (NCT01645787)",
        "evidence_score": 0.70,
    },
    # Emerging
    {
        "drug": "Reldesemtiv",
        "approved_for": "Clinical trials (SMA, ALS)",
        "mechanism": "Fast skeletal muscle troponin activator",
        "shared_pathway": "Muscle function, NMJ output amplification",
        "sma_targets": ["NMJ_MATURATION"],
        "rationale": "Directly improves muscle contraction force without targeting SMN. Phase 3 in SMA (SAPPHIRE trial). Combination potential with nusinersen/risdiplam.",
        "clinical_status": "Phase 3 SMA (NCT05115110)",
        "evidence_score": 0.85,
    },
    {
        "drug": "Apitegromab (SRK-015)",
        "approved_for": "Clinical trials (SMA)",
        "mechanism": "Anti-myostatin antibody",
        "shared_pathway": "Muscle growth, anti-atrophy",
        "sma_targets": ["NMJ_MATURATION", "PLS3"],
        "rationale": "Myostatin inhibition promotes muscle growth. Phase 3 in SMA (SAPPHIRE) as combination with nusinersen.",
        "clinical_status": "Phase 3 SMA (SAPPHIRE)",
        "evidence_score": 0.85,
    },
]


async def get_repurposing_candidates(min_score: float = 0.0) -> list[dict[str, Any]]:
    """Get cross-disease drug repurposing candidates for SMA."""
    candidates = [c for c in CROSS_DISEASE_CANDIDATES if c["evidence_score"] >= min_score]
    candidates.sort(key=lambda x: x["evidence_score"], reverse=True)
    return candidates


async def get_candidates_by_target(target: str) -> list[dict[str, Any]]:
    """Get repurposing candidates that target a specific SMA protein."""
    return [c for c in CROSS_DISEASE_CANDIDATES if target.upper() in [t.upper() for t in c["sma_targets"]]]


async def get_candidates_by_disease(disease: str) -> list[dict[str, Any]]:
    """Get repurposing candidates from a specific disease."""
    disease_lower = disease.lower()
    return [c for c in CROSS_DISEASE_CANDIDATES if disease_lower in c["approved_for"].lower()]
