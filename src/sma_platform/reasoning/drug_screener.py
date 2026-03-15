"""Computational drug screening — analyze compounds for SMA drug-likeness.

Uses RDKit for molecular property calculation:
- Lipinski's Rule of Five (oral bioavailability)
- Blood-Brain Barrier permeability prediction
- CNS MPO (Multi-Parameter Optimization) score
- QED (Quantitative Estimate of Drug-likeness)
- PAINS (Pan-Assay Interference) filter

Data source: ChEMBL bioactivity data stored in graph_edges table.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict, field
from typing import Any

from ..core.database import execute, fetch, fetchrow

logger = logging.getLogger(__name__)


@dataclass
class MolecularProfile:
    """Computed molecular properties for a compound."""
    chembl_id: str
    smiles: str
    # Lipinski properties
    mw: float = 0.0           # Molecular weight
    logp: float = 0.0         # Partition coefficient
    hbd: int = 0              # H-bond donors
    hba: int = 0              # H-bond acceptors
    tpsa: float = 0.0         # Topological polar surface area
    rotatable_bonds: int = 0
    # Scores
    lipinski_violations: int = 0
    lipinski_pass: bool = False
    bbb_permeable: bool = False
    cns_mpo: float = 0.0
    qed: float = 0.0
    # Filters
    pains_alert: bool = False
    pains_patterns: list[str] | None = None
    # Bioactivity
    best_pchembl: float | None = None
    target_symbol: str = ""
    assay_type: str = ""
    # Composite ranking score (computed during screening)
    _composite: float = field(default=0.0, repr=False)


def _ensure_rdkit():
    """Import RDKit and raise clear error if not installed."""
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors, QED, FilterCatalog
        return Chem, Descriptors, QED, FilterCatalog
    except ImportError:
        raise ImportError(
            "RDKit is required for drug screening. Install: pip install rdkit "
            "or conda install -c conda-forge rdkit"
        )


def compute_molecular_profile(smiles: str, chembl_id: str = "") -> MolecularProfile | None:
    """Compute full molecular profile from a SMILES string."""
    Chem, Descriptors, QED_mod, FilterCatalog = _ensure_rdkit()

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        logger.warning("Invalid SMILES for %s: %s", chembl_id, smiles[:50])
        return None

    # Basic descriptors
    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    hbd = Descriptors.NumHDonors(mol)
    hba = Descriptors.NumHAcceptors(mol)
    tpsa = Descriptors.TPSA(mol)
    rot_bonds = Descriptors.NumRotatableBonds(mol)

    # Lipinski Rule of Five
    violations = sum([
        mw > 500,
        logp > 5,
        hbd > 5,
        hba > 10,
    ])

    # BBB permeability heuristic (Clark's rules)
    # MW < 450, TPSA < 90, HBD <= 3, logP 1-3
    bbb = (mw < 450 and tpsa < 90 and hbd <= 3 and 1 <= logp <= 3)

    # CNS MPO score (Wager et al., 2010)
    # 6-point scale: logP, logD, MW, TPSA, HBD, pKa (simplified)
    cns_mpo = 0.0
    # logP component (ideal: 1-3)
    if logp <= 3:
        cns_mpo += 1.0
    elif logp <= 5:
        cns_mpo += 0.5
    # MW component (ideal: < 360)
    if mw <= 360:
        cns_mpo += 1.0
    elif mw <= 500:
        cns_mpo += 1.0 - (mw - 360) / 140
    # TPSA component (ideal: 40-90)
    if 40 <= tpsa <= 90:
        cns_mpo += 1.0
    elif tpsa < 40:
        cns_mpo += 0.5
    elif tpsa <= 120:
        cns_mpo += 1.0 - (tpsa - 90) / 30
    # HBD component (ideal: 0-1)
    if hbd <= 1:
        cns_mpo += 1.0
    elif hbd <= 3:
        cns_mpo += 1.0 - (hbd - 1) / 2
    # Rotatable bonds (ideal: < 8 for CNS)
    if rot_bonds <= 8:
        cns_mpo += 1.0
    elif rot_bonds <= 12:
        cns_mpo += 0.5
    # Aromatic rings (simplified — count rings)
    num_aromatic = Descriptors.NumAromaticRings(mol)
    if num_aromatic <= 3:
        cns_mpo += 1.0
    elif num_aromatic <= 5:
        cns_mpo += 0.5
    cns_mpo = round(cns_mpo, 2)

    # QED score
    qed_score = round(QED_mod.qed(mol), 3)

    # PAINS filter
    pains_alerts = []
    try:
        params = FilterCatalog.FilterCatalogParams()
        params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS)
        catalog = FilterCatalog.FilterCatalog(params)
        entry = catalog.GetFirstMatch(mol)
        if entry:
            pains_alerts.append(entry.GetDescription())
    except Exception:
        pass

    return MolecularProfile(
        chembl_id=chembl_id,
        smiles=smiles,
        mw=round(mw, 1),
        logp=round(logp, 2),
        hbd=hbd,
        hba=hba,
        tpsa=round(tpsa, 1),
        rotatable_bonds=rot_bonds,
        lipinski_violations=violations,
        lipinski_pass=(violations <= 1),
        bbb_permeable=bbb,
        cns_mpo=cns_mpo,
        qed=qed_score,
        pains_alert=len(pains_alerts) > 0,
        pains_patterns=pains_alerts if pains_alerts else None,
    )


async def screen_all_compounds() -> dict[str, Any]:
    """Screen all compounds in graph_edges (from ChEMBL ingestion).

    Returns summary statistics and stores profiles in database.
    """
    _ensure_rdkit()

    # Fetch all compound bioactivity edges
    rows = await fetch(
        """SELECT metadata FROM graph_edges
           WHERE relation LIKE 'compound_bioactivity:%'
           ORDER BY confidence DESC"""
    )

    compounds: dict[str, dict] = {}  # chembl_id -> best record
    for row in rows:
        meta = row["metadata"]
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except json.JSONDecodeError:
                continue

        cid = meta.get("molecule_chembl_id", "")
        smiles = meta.get("canonical_smiles", "")
        if not cid or not smiles:
            continue

        pchembl = meta.get("pchembl_value")
        if pchembl is not None:
            try:
                pchembl = float(pchembl)
            except (ValueError, TypeError):
                pchembl = None

        # Keep the best pChEMBL record per compound
        existing = compounds.get(cid)
        if existing is None or (pchembl and (existing.get("pchembl") or 0) < pchembl):
            compounds[cid] = {
                "smiles": smiles,
                "pchembl": pchembl,
                "target_symbol": meta.get("target_symbol", ""),
                "assay_type": meta.get("assay_type", ""),
            }

    logger.info("Found %d unique compounds to screen", len(compounds))

    profiles: list[MolecularProfile] = []
    errors = 0
    for cid, info in compounds.items():
        profile = compute_molecular_profile(info["smiles"], cid)
        if profile is None:
            errors += 1
            continue
        profile.best_pchembl = info.get("pchembl")
        profile.target_symbol = info.get("target_symbol", "")
        profile.assay_type = info.get("assay_type", "")
        profiles.append(profile)

    # Sort by composite score: QED * CNS_MPO * (pChEMBL/10 or 0.5)
    for p in profiles:
        potency = (p.best_pchembl or 5.0) / 10.0
        p._composite = p.qed * (p.cns_mpo / 6.0) * potency

    profiles.sort(key=lambda p: p._composite, reverse=True)

    # Categorize results
    lipinski_pass = [p for p in profiles if p.lipinski_pass]
    bbb_pass = [p for p in profiles if p.bbb_permeable]
    cns_good = [p for p in profiles if p.cns_mpo >= 4.0]
    qed_good = [p for p in profiles if p.qed >= 0.5]
    pains_free = [p for p in profiles if not p.pains_alert]
    drug_like = [p for p in profiles if p.lipinski_pass and not p.pains_alert and p.qed >= 0.4]

    # Top candidates: drug-like + BBB permeable + high potency
    top_candidates = [
        p for p in profiles
        if p.lipinski_pass and p.bbb_permeable and not p.pains_alert
        and p.qed >= 0.4 and (p.best_pchembl or 0) >= 6.0
    ]

    return {
        "total_compounds": len(compounds),
        "screened": len(profiles),
        "errors": errors,
        "lipinski_pass": len(lipinski_pass),
        "bbb_permeable": len(bbb_pass),
        "cns_mpo_good": len(cns_good),
        "qed_good": len(qed_good),
        "pains_free": len(pains_free),
        "drug_like": len(drug_like),
        "top_candidates": len(top_candidates),
        "top_10": [{k: v for k, v in asdict(p).items() if not k.startswith("_")} for p in profiles[:10]],
        "top_bbb_cns": [{k: v for k, v in asdict(p).items() if not k.startswith("_")} for p in top_candidates[:10]],
    }


async def screen_single_smiles(smiles: str) -> dict[str, Any] | None:
    """Screen a single SMILES string and return its molecular profile."""
    profile = compute_molecular_profile(smiles, "user_input")
    if profile is None:
        return None
    return asdict(profile)
