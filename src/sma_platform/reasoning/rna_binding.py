"""RNA-Binding Prediction for SMN2 Splicing Modulators (Phase 9.4).

Predicts RNA-binding affinity of small molecules toward SMN2 pre-mRNA
regulatory elements. Identifies compounds that could modulate SMN2 exon 7
inclusion through direct RNA interaction (like risdiplam).

Key RNA targets in SMN2:
- ISS-N1 (Intronic Splicing Silencer N1): nusinersen target
- ESE (Exonic Splicing Enhancer): Tra2-beta binding site
- ESS (Exonic Splicing Silencer): hnRNP A1 binding site
- 5' splice site of exon 7 (weakened by C6T)
- U1 snRNA:5'ss duplex: risdiplam stabilizes this interaction

References:
- Palacino et al., Nature Chem Biol 2015 (risdiplam mechanism)
- Ratni et al., J Med Chem 2018 (SMN2 splicing modifiers)
- Campagne et al., Nature Chem Biol 2019 (branaplam RNA binding)
- Sivaramakrishnan et al., Nat Commun 2023 (splicing modifier SAR)
"""

from __future__ import annotations

import logging
import math
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RNA target sites
# ---------------------------------------------------------------------------

@dataclass
class RNATargetSite:
    """An RNA regulatory element in SMN2 that can be targeted."""
    name: str
    location: str
    sequence_motif: str
    binding_proteins: list[str]
    druggability: float         # 0-1 how druggable this RNA structure is
    mechanism: str
    approved_drug: str          # drug that targets this site, if any


RNA_TARGET_SITES = [
    RNATargetSite(
        name="ISS-N1",
        location="Intron 7, positions +10 to +24",
        sequence_motif="CCAGCAUUAUGAAAG",
        binding_proteins=["hnRNP A1", "hnRNP A2/B1"],
        druggability=0.90,
        mechanism="Silencer element — hnRNP A1 binding causes exon 7 skipping. "
                 "Blocking ISS-N1 promotes exon 7 inclusion.",
        approved_drug="Nusinersen (ASO)",
    ),
    RNATargetSite(
        name="5'ss/U1 snRNA interface",
        location="Exon 7 / Intron 7 junction",
        sequence_motif="GUAAGU",
        binding_proteins=["U1 snRNP"],
        druggability=0.85,
        mechanism="Weak 5' splice site due to C6T. Small molecules can stabilize U1 snRNA "
                 "binding to promote exon 7 recognition.",
        approved_drug="Risdiplam (small molecule)",
    ),
    RNATargetSite(
        name="ESE2 (Tra2-beta)",
        location="Exon 7, positions 19-27",
        sequence_motif="GAAGGAAGG",
        binding_proteins=["Tra2-beta", "SRp30c"],
        druggability=0.60,
        mechanism="Exonic splicing enhancer. Tra2-beta binding promotes exon 7 inclusion. "
                 "Enhancing this interaction could boost SMN2 full-length transcript.",
        approved_drug="None",
    ),
    RNATargetSite(
        name="ESS (hnRNP A1)",
        location="Exon 7, positions 33-39",
        sequence_motif="UAGACAA",
        binding_proteins=["hnRNP A1"],
        druggability=0.55,
        mechanism="Exonic splicing silencer. hnRNP A1 binding antagonizes Tra2-beta. "
                 "Blocking ESS could enhance exon 7 inclusion.",
        approved_drug="None",
    ),
    RNATargetSite(
        name="Element 1 (Intron 6 branch point)",
        location="Intron 6, positions -15 to -5",
        sequence_motif="UCUAAC",
        binding_proteins=["U2 snRNP", "SF1/BBP"],
        druggability=0.50,
        mechanism="Branch point recognition. Strengthening branch point interaction improves "
                 "exon 7 definition. Targeted by branaplam.",
        approved_drug="Branaplam (discontinued — off-target HTT toxicity)",
    ),
    RNATargetSite(
        name="Stem-loop TSL2",
        location="Exon 7, 3' end",
        sequence_motif="CAAAAAGAAGGAAGGU",
        binding_proteins=["hnRNP A1 (structural)"],
        druggability=0.45,
        mechanism="Terminal stem-loop that sequesters the 5'ss. Disrupting TSL2 structure "
                 "could free the splice site for U1 snRNA recognition.",
        approved_drug="None",
    ),
]


# ---------------------------------------------------------------------------
# RNA-binding score prediction
# ---------------------------------------------------------------------------

@dataclass
class RNABindingPrediction:
    """Predicted RNA-binding affinity of a compound for an RNA target."""
    compound_name: str
    target_site: str
    binding_score: float        # 0-1 predicted binding affinity
    selectivity: float          # 0-1 selectivity for SMN2 vs off-targets
    mechanism: str
    drug_likeness: float        # 0-1
    cns_penetration: float      # 0-1
    overall_score: float        # 0-1 composite


def _predict_rna_binding(mw: float, logp: float, hba: int, hbd: int,
                         aromatic_rings: int, rotatable_bonds: int,
                         target: str) -> float:
    """Predict RNA-binding affinity based on physicochemical properties.

    RNA-binding small molecules tend to be:
    - Planar (aromatic systems for stacking)
    - Positively charged or H-bond donors (for phosphate backbone)
    - MW 300-500 (smaller than protein-binding drugs)
    - Moderate logP (need some lipophilicity for RNA groove binding)
    """
    score = 0.5  # baseline

    # Aromatic rings: RNA binders need planar systems for base stacking
    if 2 <= aromatic_rings <= 4:
        score += 0.15
    elif aromatic_rings == 1:
        score += 0.05
    elif aromatic_rings > 4:
        score -= 0.05  # too rigid

    # MW sweet spot: 300-500 for RNA-binding small molecules
    if 300 <= mw <= 500:
        score += 0.10
    elif mw < 250 or mw > 600:
        score -= 0.10

    # H-bond donors: important for phosphate backbone interaction
    if 2 <= hbd <= 4:
        score += 0.10
    elif hbd > 5:
        score -= 0.05  # too many limits cell permeability

    # H-bond acceptors: moderate
    if 3 <= hba <= 7:
        score += 0.05

    # LogP: moderate lipophilicity for RNA groove binding
    if 1.0 <= logp <= 3.5:
        score += 0.10
    elif logp < 0 or logp > 5:
        score -= 0.10

    # Rotatable bonds: some flexibility needed to adapt to RNA structure
    if 3 <= rotatable_bonds <= 7:
        score += 0.05

    # Target-specific bonuses
    target_bonuses = {
        "ISS-N1": 0.05,           # Well-validated, easier to design for
        "5'ss/U1 snRNA interface": 0.10,  # Risdiplam proves this works
        "ESE2 (Tra2-beta)": 0.0,
        "ESS (hnRNP A1)": -0.05,  # Harder target
        "Element 1 (Intron 6 branch point)": 0.0,
        "Stem-loop TSL2": -0.05,  # Structural target, harder
    }
    score += target_bonuses.get(target, 0)

    return max(0.0, min(1.0, score))


def predict_compound_binding(name: str, mw: float, logp: float,
                             hba: int, hbd: int, aromatic_rings: int,
                             rotatable_bonds: int) -> dict[str, Any]:
    """Predict RNA-binding potential of a compound across all SMN2 target sites."""
    predictions = []
    for site in RNA_TARGET_SITES:
        binding = _predict_rna_binding(mw, logp, hba, hbd, aromatic_rings, rotatable_bonds, site.name)

        # CNS penetration (simplified BBB score)
        cns = 1.0 if (mw < 450 and 1 < logp < 3 and hbd <= 3) else (0.5 if mw < 500 else 0.2)

        # Drug-likeness (Lipinski-like)
        violations = sum([mw > 500, logp > 5, hba > 10, hbd > 5])
        drug_like = max(0, 1.0 - violations * 0.25)

        # Selectivity estimate (higher for well-characterized sites)
        selectivity = site.druggability * 0.8

        # Composite
        overall = binding * 0.35 + selectivity * 0.25 + drug_like * 0.20 + cns * 0.20

        predictions.append(RNABindingPrediction(
            compound_name=name,
            target_site=site.name,
            binding_score=round(binding, 2),
            selectivity=round(selectivity, 2),
            mechanism=f"Predicted interaction with {site.name} ({site.location})",
            drug_likeness=round(drug_like, 2),
            cns_penetration=round(cns, 2),
            overall_score=round(overall, 2),
        ))

    predictions.sort(key=lambda x: x.overall_score, reverse=True)

    return {
        "compound": name,
        "properties": {
            "mw": mw, "logp": logp, "hba": hba, "hbd": hbd,
            "aromatic_rings": aromatic_rings, "rotatable_bonds": rotatable_bonds,
        },
        "predictions": [asdict(p) for p in predictions],
        "best_target": asdict(predictions[0]) if predictions else None,
        "rna_binder_likelihood": round(
            max(p.overall_score for p in predictions) if predictions else 0, 2
        ),
    }


# ---------------------------------------------------------------------------
# Known RNA-binding SMN2 modulators (reference set)
# ---------------------------------------------------------------------------

KNOWN_MODULATORS = [
    {"name": "Risdiplam", "mw": 390, "logp": 2.1, "hba": 7, "hbd": 2, "aromatic_rings": 3, "rotatable_bonds": 4,
     "target": "5'ss/U1 snRNA interface", "status": "Approved (2020)", "ec50_nm": 74},
    {"name": "Branaplam", "mw": 424, "logp": 2.8, "hba": 6, "hbd": 2, "aromatic_rings": 4, "rotatable_bonds": 3,
     "target": "Element 1 (branch point)", "status": "Discontinued (HTT toxicity)", "ec50_nm": 3},
    {"name": "RG7800", "mw": 356, "logp": 1.9, "hba": 5, "hbd": 1, "aromatic_rings": 3, "rotatable_bonds": 3,
     "target": "5'ss/U1 snRNA interface", "status": "Discontinued (retinal toxicity)", "ec50_nm": 15},
    {"name": "SMN-C3", "mw": 382, "logp": 2.3, "hba": 6, "hbd": 2, "aromatic_rings": 3, "rotatable_bonds": 5,
     "target": "5'ss/U1 snRNA interface", "status": "Preclinical (Roche lead)", "ec50_nm": 200},
    {"name": "NVS-SM1", "mw": 398, "logp": 2.5, "hba": 5, "hbd": 1, "aromatic_rings": 3, "rotatable_bonds": 4,
     "target": "5'ss/U1 snRNA interface", "status": "Preclinical (Novartis)", "ec50_nm": 50},
]


# ---------------------------------------------------------------------------
# API functions
# ---------------------------------------------------------------------------

def get_rna_targets() -> dict[str, Any]:
    """Return all RNA target sites in SMN2."""
    return {
        "total_sites": len(RNA_TARGET_SITES),
        "sites": [asdict(s) for s in RNA_TARGET_SITES],
        "most_druggable": asdict(max(RNA_TARGET_SITES, key=lambda x: x.druggability)),
        "insight": "ISS-N1 (nusinersen target) and the 5'ss/U1 interface (risdiplam target) are "
                   "the most druggable RNA elements. ESE2 and ESS represent underexplored targets "
                   "for next-generation splicing modulators. TSL2 structural disruption is the "
                   "most challenging but potentially most impactful approach.",
    }


def get_known_modulators() -> dict[str, Any]:
    """Return known RNA-binding SMN2 splicing modulators."""
    return {
        "total_modulators": len(KNOWN_MODULATORS),
        "modulators": KNOWN_MODULATORS,
        "approved": [m for m in KNOWN_MODULATORS if "Approved" in m["status"]],
        "discontinued": [m for m in KNOWN_MODULATORS if "Discontinued" in m["status"]],
        "insight": "Risdiplam is the only approved small molecule RNA-binding SMN2 modulator. "
                   "Branaplam was more potent (EC50 3 nM vs 74 nM) but caused off-target "
                   "huntingtin knockdown. The key lesson: selectivity matters more than potency "
                   "for RNA-binding drugs.",
    }


def benchmark_compound(name: str, mw: float, logp: float,
                       hba: int, hbd: int, aromatic_rings: int,
                       rotatable_bonds: int) -> dict[str, Any]:
    """Benchmark a compound against known SMN2 modulators."""
    prediction = predict_compound_binding(name, mw, logp, hba, hbd, aromatic_rings, rotatable_bonds)

    # Compare to known modulators
    reference_scores = []
    for mod in KNOWN_MODULATORS:
        ref = predict_compound_binding(
            mod["name"], mod["mw"], mod["logp"], mod["hba"], mod["hbd"],
            mod["aromatic_rings"], mod["rotatable_bonds"]
        )
        reference_scores.append({
            "name": mod["name"],
            "best_score": ref["rna_binder_likelihood"],
            "status": mod["status"],
        })

    prediction["benchmark"] = {
        "reference_modulators": reference_scores,
        "percentile": round(
            sum(1 for r in reference_scores if prediction["rna_binder_likelihood"] >= r["best_score"])
            / max(1, len(reference_scores)) * 100
        ),
    }

    return prediction
