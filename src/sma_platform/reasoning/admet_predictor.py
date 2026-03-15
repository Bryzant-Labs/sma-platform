"""ADMET prediction — Absorption, Distribution, Metabolism, Excretion, Toxicity.

Extends the drug screening pipeline with computed ADMET properties
using RDKit molecular descriptors. No external APIs required.

References:
- Caco-2: Hou et al., 2004 (PSA/logP model)
- HIA: Zhao et al., 2003 (logP/PSA thresholds)
- BBB: Clark, 2003 (MW/PSA/HBD/logP)
- hERG: Aronov, 2005 (logP/MW/aromatic rings)
- Ames: Hansen et al., 2009 (alerts-based)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, asdict, field
from typing import Any

from ..core.database import fetch

logger = logging.getLogger(__name__)


def _ensure_rdkit():
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors, rdMolDescriptors
        return Chem, Descriptors, rdMolDescriptors
    except ImportError:
        raise ImportError("RDKit required: pip install rdkit")


@dataclass
class ADMETProfile:
    """Computed ADMET properties for a compound."""
    smiles: str
    chembl_id: str = ""
    # Absorption
    caco2_permeable: bool = False
    caco2_score: float = 0.0
    hia_absorbed: bool = False
    hia_score: float = 0.0
    pgp_substrate: bool = False
    # Distribution
    bbb_score: float = 0.0
    bbb_permeable: bool = False
    ppb_high: bool = False
    ppb_estimate: float = 0.0
    vd_category: str = "medium"
    # Metabolism
    cyp_risk: str = "low"
    cyp_risk_score: float = 0.0
    metabolic_soft_spots: int = 0
    # Excretion
    clearance_category: str = "moderate"
    halflife_category: str = "medium"
    # Toxicity
    herg_risk: str = "low"
    herg_score: float = 0.0
    ames_risk: str = "low"
    ames_score: float = 0.0
    hepatotox_risk: str = "low"
    hepatotox_score: float = 0.0
    # Overall
    admet_score: float = 0.0
    flags: list[str] = field(default_factory=list)


def _predict_absorption(mol, mw, logp, tpsa, hbd) -> dict:
    """Predict absorption properties."""
    Chem, Desc, _ = _ensure_rdkit()

    # Caco-2 permeability: PSA < 140 and logP > 0 suggests permeability
    caco2_score = max(0, min(1, 1.0 - tpsa / 200)) * max(0, min(1, logp / 3))
    caco2_permeable = tpsa < 140 and logp > 0 and mw < 700

    # Human Intestinal Absorption: logP-PSA model
    hia_score = max(0, min(1, (1.0 - tpsa / 200) * 0.6 + min(logp / 5, 1) * 0.4))
    hia_absorbed = tpsa < 140 and -0.5 < logp < 6 and mw < 600

    # P-gp substrate: large, lipophilic, many HBD
    pgp = mw > 400 and hbd >= 3 and tpsa > 75

    return {
        "caco2_permeable": caco2_permeable,
        "caco2_score": round(caco2_score, 3),
        "hia_absorbed": hia_absorbed,
        "hia_score": round(hia_score, 3),
        "pgp_substrate": pgp,
    }


def _predict_distribution(mol, mw, logp, tpsa, hbd, hba) -> dict:
    """Predict distribution properties."""
    # BBB: Clark's rules refined
    bbb_score = 0.0
    bbb_score += max(0, 1.0 - mw / 500) * 0.25
    bbb_score += max(0, 1.0 - tpsa / 120) * 0.25
    bbb_score += max(0, min(1, logp / 3)) * 0.25 if logp > 0 else 0
    bbb_score += max(0, 1.0 - hbd / 4) * 0.25
    bbb_permeable = mw < 450 and tpsa < 90 and hbd <= 3 and 1 <= logp <= 3

    # Plasma protein binding: lipophilic compounds bind more
    ppb_estimate = min(0.99, max(0.1, 0.5 + logp * 0.1))
    ppb_high = ppb_estimate > 0.9

    # Volume of distribution: logP-dependent
    if logp < 1:
        vd = "low"
    elif logp < 3:
        vd = "medium"
    else:
        vd = "high"

    return {
        "bbb_score": round(bbb_score, 3),
        "bbb_permeable": bbb_permeable,
        "ppb_high": ppb_high,
        "ppb_estimate": round(ppb_estimate, 3),
        "vd_category": vd,
    }


def _predict_metabolism(mol, mw, logp, num_aromatic) -> dict:
    """Predict metabolism properties."""
    Chem, Desc, rdMol = _ensure_rdkit()

    # CYP inhibition risk: lipophilic + aromatic compounds inhibit CYPs
    cyp_score = 0.0
    if logp > 3:
        cyp_score += 0.3
    if num_aromatic >= 3:
        cyp_score += 0.3
    if mw > 400:
        cyp_score += 0.2
    n_count = sum(1 for a in mol.GetAtoms() if a.GetSymbol() == 'N')
    if n_count >= 2:
        cyp_score += 0.2
    cyp_score = min(1.0, cyp_score)

    if cyp_score > 0.6:
        cyp_risk = "high"
    elif cyp_score > 0.3:
        cyp_risk = "moderate"
    else:
        cyp_risk = "low"

    # Metabolic soft spots: count oxidizable groups
    soft_spots = 0
    for atom in mol.GetAtoms():
        sym = atom.GetSymbol()
        if sym == 'S' and atom.GetDegree() <= 2:
            soft_spots += 1
        if sym == 'N' and not atom.GetIsAromatic() and atom.GetDegree() <= 2:
            soft_spots += 1
    # Benzylic positions (simplified)
    soft_spots += Desc.NumAliphaticCarbocycles(mol)

    return {
        "cyp_risk": cyp_risk,
        "cyp_risk_score": round(cyp_score, 3),
        "metabolic_soft_spots": soft_spots,
    }


def _predict_excretion(mw, logp, tpsa) -> dict:
    """Predict excretion properties."""
    # Renal clearance: small, hydrophilic compounds cleared renally
    if mw < 300 and logp < 1 and tpsa > 60:
        clearance = "high_renal"
    elif mw < 500 and logp < 3:
        clearance = "moderate"
    else:
        clearance = "low_hepatic"

    # Half-life estimate: lipophilic/large = longer
    if logp > 4 or mw > 500:
        halflife = "long"
    elif logp > 2 or mw > 350:
        halflife = "medium"
    else:
        halflife = "short"

    return {"clearance_category": clearance, "halflife_category": halflife}


def _predict_toxicity(mol, mw, logp, tpsa, num_aromatic) -> dict:
    """Predict toxicity properties."""
    Chem, Desc, _ = _ensure_rdkit()
    flags = []

    # hERG liability: lipophilic amines are high risk
    herg_score = 0.0
    if logp > 3:
        herg_score += 0.3
    basic_n = sum(1 for a in mol.GetAtoms()
                  if a.GetSymbol() == 'N' and not a.GetIsAromatic()
                  and a.GetFormalCharge() >= 0)
    if basic_n >= 1:
        herg_score += 0.3
    if mw > 350:
        herg_score += 0.2
    if num_aromatic >= 2:
        herg_score += 0.2
    herg_score = min(1.0, herg_score)
    herg_risk = "high" if herg_score > 0.6 else "moderate" if herg_score > 0.3 else "low"
    if herg_risk == "high":
        flags.append("hERG_liability")

    # Ames mutagenicity: aromatic amines, nitro groups
    ames_score = 0.0
    smiles = Chem.MolToSmiles(mol)
    if '[N+](=O)[O-]' in smiles or 'N(=O)=O' in smiles:
        ames_score += 0.5
        flags.append("nitro_group")
    aromatic_n = sum(1 for a in mol.GetAtoms()
                     if a.GetSymbol() == 'N' and a.GetIsAromatic())
    if aromatic_n >= 2:
        ames_score += 0.3
    if num_aromatic >= 4:
        ames_score += 0.2
    ames_score = min(1.0, ames_score)
    ames_risk = "high" if ames_score > 0.5 else "moderate" if ames_score > 0.2 else "low"
    if ames_risk == "high":
        flags.append("Ames_mutagen_risk")

    # Hepatotoxicity: reactive metabolites, large lipophilic
    hepato_score = 0.0
    if logp > 3 and mw > 400:
        hepato_score += 0.4
    if Desc.NumHDonors(mol) >= 3 and tpsa > 75:
        hepato_score += 0.2
    heavy = mol.GetNumHeavyAtoms()
    if heavy > 35:
        hepato_score += 0.2
    # Check for known hepatotoxic groups
    carbonyl = Chem.MolFromSmarts('[#6]=[#8]')
    nitrogen = Chem.MolFromSmarts('[#7]')
    if carbonyl and nitrogen and mol.HasSubstructMatch(carbonyl) and mol.HasSubstructMatch(nitrogen):
        hepato_score += 0.2
    hepato_score = min(1.0, hepato_score)
    hepato_risk = "high" if hepato_score > 0.6 else "moderate" if hepato_score > 0.3 else "low"
    if hepato_risk == "high":
        flags.append("hepatotoxicity_risk")

    return {
        "herg_risk": herg_risk,
        "herg_score": round(herg_score, 3),
        "ames_risk": ames_risk,
        "ames_score": round(ames_score, 3),
        "hepatotox_risk": hepato_risk,
        "hepatotox_score": round(hepato_score, 3),
        "flags": flags,
    }


def predict_admet(smiles: str, chembl_id: str = "") -> ADMETProfile | None:
    """Full ADMET prediction for a single SMILES string."""
    Chem, Desc, _ = _ensure_rdkit()

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    mw = Desc.MolWt(mol)
    logp = Desc.MolLogP(mol)
    tpsa = Desc.TPSA(mol)
    hbd = Desc.NumHDonors(mol)
    hba = Desc.NumHAcceptors(mol)
    num_aromatic = Desc.NumAromaticRings(mol)

    absorption = _predict_absorption(mol, mw, logp, tpsa, hbd)
    distribution = _predict_distribution(mol, mw, logp, tpsa, hbd, hba)
    metabolism = _predict_metabolism(mol, mw, logp, num_aromatic)
    excretion = _predict_excretion(mw, logp, tpsa)
    toxicity = _predict_toxicity(mol, mw, logp, tpsa, num_aromatic)

    # Overall ADMET score (0-1, higher = better drug candidate)
    score = 0.0
    score += 0.2 * absorption["hia_score"]
    score += 0.2 * distribution["bbb_score"]
    score += 0.2 * (1.0 - metabolism["cyp_risk_score"])
    score += 0.2 * (1.0 - toxicity["herg_score"])
    score += 0.1 * (1.0 - toxicity["ames_score"])
    score += 0.1 * (1.0 - toxicity["hepatotox_score"])

    return ADMETProfile(
        smiles=smiles,
        chembl_id=chembl_id,
        **absorption,
        **distribution,
        **metabolism,
        **excretion,
        **{k: v for k, v in toxicity.items() if k != "flags"},
        flags=toxicity["flags"],
        admet_score=round(score, 3),
    )


async def batch_predict_admet() -> dict[str, Any]:
    """Run ADMET prediction on all ChEMBL compounds with SMILES data."""
    import json

    rows = await fetch(
        """SELECT metadata FROM graph_edges
           WHERE relation LIKE 'compound_bioactivity:%'
           LIMIT 5000"""
    )

    seen: dict[str, str] = {}
    for row in rows:
        meta = row["metadata"]
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except json.JSONDecodeError:
                continue
        cid = meta.get("molecule_chembl_id", "")
        smiles = meta.get("canonical_smiles", "")
        if cid and smiles and cid not in seen:
            seen[cid] = smiles

    results = []
    risk_counts = {"low": 0, "moderate": 0, "high": 0}

    for cid, smiles in seen.items():
        profile = predict_admet(smiles, cid)
        if profile is None:
            continue
        results.append(asdict(profile))
        # Count overall risk
        if profile.admet_score >= 0.6:
            risk_counts["low"] += 1
        elif profile.admet_score >= 0.4:
            risk_counts["moderate"] += 1
        else:
            risk_counts["high"] += 1

    results.sort(key=lambda r: r["admet_score"], reverse=True)

    return {
        "total_screened": len(results),
        "risk_summary": risk_counts,
        "top_20": results[:20],
        "flagged_compounds": [r for r in results if r["flags"]],
    }
