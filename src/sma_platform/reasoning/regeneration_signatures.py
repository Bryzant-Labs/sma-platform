"""Cross-Species Regeneration Signatures (Phase 7.2).

Compares regeneration programs in axolotl/zebrafish with degeneration
in human SMA motor neurons. Identifies conserved regeneration pathways
that are silenced in SMA and could be therapeutically reactivated.

References:
- Gerber et al., Science 2018 (axolotl limb regeneration single-cell)
- Mokalled et al., Science 2016 (zebrafish spinal cord regeneration)
- Nichterwitz et al., Cell Reports 2016 (human MN transcriptomes)
- Blum et al., Nature 2021 (spinal cord single-cell atlas)
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Regeneration gene programs
# ---------------------------------------------------------------------------

@dataclass
class RegenerationGene:
    """A gene involved in regeneration in model organisms."""
    symbol: str
    name: str
    organism: str               # axolotl, zebrafish, or both
    human_ortholog: str         # human gene symbol
    regeneration_role: str      # functional role in regeneration
    sma_status: str             # upregulated, downregulated, unchanged, unknown
    reactivation_potential: float  # 0-1 therapeutic reactivation feasibility
    pathway: str
    evidence_source: str


REGENERATION_GENES = [
    RegenerationGene(
        symbol="c-Fos", name="Proto-oncogene c-Fos", organism="axolotl",
        human_ortholog="FOS",
        regeneration_role="Immediate-early gene driving regeneration initiation. Sustained ERK→c-Fos "
                         "signaling distinguishes regeneration from scarring.",
        sma_status="downregulated",
        reactivation_potential=0.65,
        pathway="MAPK/ERK",
        evidence_source="Gerber et al., Science 2018",
    ),
    RegenerationGene(
        symbol="JunB", name="Transcription factor JunB", organism="axolotl",
        human_ortholog="JUNB",
        regeneration_role="AP-1 complex partner of c-Fos. JunB/c-Fos balance determines "
                         "regeneration vs fibrosis outcome.",
        sma_status="unchanged",
        reactivation_potential=0.55,
        pathway="AP-1 signaling",
        evidence_source="Gerber et al., Science 2018",
    ),
    RegenerationGene(
        symbol="ctgfa", name="Connective tissue growth factor a", organism="zebrafish",
        human_ortholog="CTGF",
        regeneration_role="Secreted by glial bridge cells. Essential for axon guidance across "
                         "spinal cord lesion site.",
        sma_status="downregulated",
        reactivation_potential=0.70,
        pathway="Wnt/TGF-beta",
        evidence_source="Mokalled et al., Science 2016",
    ),
    RegenerationGene(
        symbol="miR-200a", name="MicroRNA 200a", organism="axolotl",
        human_ortholog="MIR200A",
        regeneration_role="Master switch suppressing fibrotic program and enabling blastema "
                         "formation. Inhibits TGF-beta/Smad-driven scarring.",
        sma_status="unknown",
        reactivation_potential=0.60,
        pathway="TGF-beta/fibrosis",
        evidence_source="Aguirre et al., Dev Cell 2014",
    ),
    RegenerationGene(
        symbol="sox2", name="SRY-box transcription factor 2", organism="both",
        human_ortholog="SOX2",
        regeneration_role="Stemness maintenance in ependymal cells. Zebrafish ependymal cells "
                         "proliferate after spinal cord injury to regenerate neurons.",
        sma_status="downregulated",
        reactivation_potential=0.40,
        pathway="Stemness/pluripotency",
        evidence_source="Ogai et al., Neuroscience 2014",
    ),
    RegenerationGene(
        symbol="shha", name="Sonic hedgehog a", organism="zebrafish",
        human_ortholog="SHH",
        regeneration_role="Ventral patterning signal. Re-expressed during motor neuron regeneration "
                         "in zebrafish to re-specify MN identity.",
        sma_status="unchanged",
        reactivation_potential=0.35,
        pathway="Hedgehog",
        evidence_source="Reimer et al., J Neurosci 2009",
    ),
    RegenerationGene(
        symbol="mstn", name="Myostatin", organism="both",
        human_ortholog="MSTN",
        regeneration_role="Negative regulator of muscle growth. Myostatin inhibition promotes "
                         "muscle regeneration and NMJ remodeling.",
        sma_status="upregulated",
        reactivation_potential=0.80,
        pathway="TGF-beta/muscle",
        evidence_source="Sumner et al., Hum Mol Genet 2009",
    ),
    RegenerationGene(
        symbol="pgc1a", name="PGC-1 alpha", organism="both",
        human_ortholog="PPARGC1A",
        regeneration_role="Mitochondrial biogenesis master regulator. Axolotl limbs show massive "
                         "PGC-1alpha upregulation during regeneration for energy demand.",
        sma_status="downregulated",
        reactivation_potential=0.75,
        pathway="Mitochondrial biogenesis",
        evidence_source="Yun et al., eLife 2015",
    ),
    RegenerationGene(
        symbol="nrg1", name="Neuregulin 1", organism="zebrafish",
        human_ortholog="NRG1",
        regeneration_role="Schwann cell dedifferentiation signal. Drives peripheral nerve regeneration "
                         "and NMJ re-innervation after injury.",
        sma_status="downregulated",
        reactivation_potential=0.70,
        pathway="ErbB/neuregulin",
        evidence_source="Stassart et al., Neuron 2013",
    ),
    RegenerationGene(
        symbol="wnt", name="Wnt ligands (wnt1/3a/8)", organism="both",
        human_ortholog="WNT3A",
        regeneration_role="Canonical Wnt drives axon regeneration, neural progenitor proliferation, "
                         "and synaptic remodeling post-injury.",
        sma_status="downregulated",
        reactivation_potential=0.55,
        pathway="Wnt/beta-catenin",
        evidence_source="Strand et al., Cell Rep 2016",
    ),
    RegenerationGene(
        symbol="hmga2", name="High-mobility group AT-hook 2", organism="axolotl",
        human_ortholog="HMGA2",
        regeneration_role="Chromatin remodeling during dedifferentiation. Opens chromatin at "
                         "regeneration loci silenced in adult mammals.",
        sma_status="unknown",
        reactivation_potential=0.50,
        pathway="Chromatin remodeling",
        evidence_source="Zhu et al., Development 2012",
    ),
    RegenerationGene(
        symbol="bdnf", name="Brain-derived neurotrophic factor", organism="both",
        human_ortholog="BDNF",
        regeneration_role="Neurotrophic support for motor neuron survival and axon regrowth. "
                         "Upregulated in regenerating zebrafish spinal cord.",
        sma_status="downregulated",
        reactivation_potential=0.65,
        pathway="Neurotrophin/TrkB",
        evidence_source="Ogai et al., Neuroscience 2014",
    ),
]


# ---------------------------------------------------------------------------
# Regeneration pathway comparison
# ---------------------------------------------------------------------------

@dataclass
class PathwayComparison:
    """Comparison of a pathway between regeneration-capable and SMA."""
    pathway: str
    regeneration_state: str     # active, transiently_active, constitutive
    sma_state: str              # suppressed, dysregulated, absent, normal
    gap_score: float            # 0-1 therapeutic gap
    drug_candidates: list[str]  # known compounds that could bridge the gap
    strategy: str               # therapeutic approach


PATHWAY_COMPARISONS = [
    PathwayComparison(
        pathway="MAPK/ERK sustained signaling",
        regeneration_state="active",
        sma_state="suppressed",
        gap_score=0.75,
        drug_candidates=["ERK activators (FGF2)", "MEK modulators", "c-Fos inducers"],
        strategy="Reactivate sustained ERK signaling in MN progenitors to trigger regeneration-like response",
    ),
    PathwayComparison(
        pathway="TGF-beta/anti-fibrotic",
        regeneration_state="transiently_active",
        sma_state="dysregulated",
        gap_score=0.65,
        drug_candidates=["Myostatin inhibitors (apitegromab)", "miR-200a mimics", "Anti-CTGF antibodies"],
        strategy="Block pro-fibrotic TGF-beta while promoting regenerative CTGF signaling",
    ),
    PathwayComparison(
        pathway="Wnt/beta-catenin",
        regeneration_state="active",
        sma_state="suppressed",
        gap_score=0.60,
        drug_candidates=["GSK-3beta inhibitors (CHIR99021)", "Wnt agonists", "R-spondin"],
        strategy="Activate canonical Wnt to promote axon regeneration and progenitor expansion",
    ),
    PathwayComparison(
        pathway="Mitochondrial biogenesis (PGC-1alpha)",
        regeneration_state="constitutive",
        sma_state="suppressed",
        gap_score=0.70,
        drug_candidates=["Bezafibrate", "NAD+ precursors (NMN/NR)", "AMPK activators (metformin)"],
        strategy="Boost mitochondrial function to meet energy demands of motor neuron maintenance",
    ),
    PathwayComparison(
        pathway="ErbB/Neuregulin (Schwann cell)",
        regeneration_state="active",
        sma_state="suppressed",
        gap_score=0.65,
        drug_candidates=["Recombinant NRG1", "ErbB4 agonists"],
        strategy="Enhance Schwann cell support and NMJ re-innervation via NRG1 signaling",
    ),
    PathwayComparison(
        pathway="Neurotrophic support (BDNF/GDNF)",
        regeneration_state="active",
        sma_state="suppressed",
        gap_score=0.60,
        drug_candidates=["BDNF gene therapy", "TrkB agonists (7,8-DHF)", "GDNF delivery"],
        strategy="Provide trophic support to prevent motor neuron death and promote axon regrowth",
    ),
    PathwayComparison(
        pathway="Chromatin accessibility",
        regeneration_state="active",
        sma_state="absent",
        gap_score=0.55,
        drug_candidates=["HDAC inhibitors", "BET inhibitors", "HMGA2 overexpression"],
        strategy="Open chromatin at regeneration loci silenced in adult human motor neurons",
    ),
]


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def get_regeneration_genes() -> dict[str, Any]:
    """Return all regeneration-associated genes with SMA comparison."""
    genes_by_status = {"downregulated": [], "upregulated": [], "unchanged": [], "unknown": []}
    for g in REGENERATION_GENES:
        genes_by_status[g.sma_status].append(g.symbol)

    return {
        "total_genes": len(REGENERATION_GENES),
        "genes": [asdict(g) for g in REGENERATION_GENES],
        "sma_status_summary": {k: len(v) for k, v in genes_by_status.items()},
        "top_reactivation_candidates": [
            asdict(g) for g in sorted(REGENERATION_GENES, key=lambda x: x.reactivation_potential, reverse=True)[:5]
        ],
        "insight": "Regeneration genes downregulated in SMA represent silenced repair programs. "
                   "Reactivating these — especially MSTN inhibition (apitegromab in trials), "
                   "PGC-1alpha (mitochondrial boost), and NRG1 (Schwann cell support) — could "
                   "complement SMN-restoring therapies.",
    }


def get_pathway_comparisons() -> dict[str, Any]:
    """Compare regeneration pathways with SMA state."""
    return {
        "total_pathways": len(PATHWAY_COMPARISONS),
        "comparisons": [asdict(p) for p in PATHWAY_COMPARISONS],
        "highest_gap": asdict(max(PATHWAY_COMPARISONS, key=lambda x: x.gap_score)),
        "actionable_now": [
            asdict(p) for p in PATHWAY_COMPARISONS
            if any("trial" in d.lower() or "approved" in d.lower() or "metformin" in d.lower()
                   for d in p.drug_candidates)
        ],
        "insight": "The MAPK/ERK pathway shows the largest gap between regeneration-capable "
                   "organisms and SMA. Mitochondrial biogenesis (PGC-1alpha) is the most "
                   "immediately druggable gap — NAD+ precursors and AMPK activators are "
                   "clinically available.",
    }


def identify_silenced_programs() -> dict[str, Any]:
    """Identify regeneration programs silenced in human SMA."""
    silenced = [g for g in REGENERATION_GENES if g.sma_status == "downregulated"]
    high_potential = [g for g in silenced if g.reactivation_potential >= 0.65]

    return {
        "silenced_count": len(silenced),
        "high_reactivation_count": len(high_potential),
        "silenced_genes": [asdict(g) for g in silenced],
        "high_potential_targets": [asdict(g) for g in high_potential],
        "pathways_affected": list({g.pathway for g in silenced}),
        "translation_score": round(
            sum(g.reactivation_potential for g in high_potential) / max(1, len(high_potential)), 2
        ),
        "insight": f"{len(silenced)} regeneration genes are downregulated in SMA, of which "
                   f"{len(high_potential)} have high reactivation potential (>=0.65). "
                   "These represent silenced repair programs that could be therapeutically "
                   "unlocked to complement SMN-restoring approaches.",
    }
