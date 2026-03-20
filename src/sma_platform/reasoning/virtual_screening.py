"""Generative Virtual Screening Pipeline (NVIDIA GTC 2026 Blueprint pattern).

Orchestrates NIM microservices to generate, filter, and dock novel molecules:
  1. GenMol: generate candidate molecules from a scaffold
  2. RDKit: filter by drug-likeness (Lipinski, QED, BBB)
  3. DiffDock: dock filtered candidates against SMA targets
  4. Rank: composite score by docking confidence + drug-likeness

Based on: github.com/NVIDIA-BioNeMo-blueprints/generative-virtual-screening
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ScreeningResult:
    smiles: str
    name: str = ""
    qed: float = 0.0
    lipinski_pass: bool = False
    bbb_permeable: bool = False
    docking_confidence: float = -999.0
    docking_target: str = ""
    composite_score: float = 0.0
    stage: str = "generated"  # generated, filtered, docked, ranked


@dataclass
class ScreeningCampaign:
    scaffold_smiles: str
    target: str
    n_generate: int = 100
    results: list[ScreeningResult] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)


async def run_virtual_screening(
    scaffold_smiles: str,
    target: str = "SMN2",
    n_generate: int = 100,
    pdb_content: str | None = None,
) -> dict[str, Any]:
    """Run end-to-end generative virtual screening pipeline.

    Args:
        scaffold_smiles: Starting molecule scaffold (e.g., 4-AP "Nc1ccncc1")
        target: SMA target name for docking
        n_generate: Number of molecules to generate
        pdb_content: Optional PDB content for docking target

    Returns:
        Dict with campaign results, stats, and top candidates
    """
    campaign = ScreeningCampaign(
        scaffold_smiles=scaffold_smiles,
        target=target,
        n_generate=n_generate,
    )

    # Step 1: Generate molecules via GenMol NIM
    logger.info("Step 1: Generating %d molecules from scaffold %s", n_generate, scaffold_smiles)
    generated = await _generate_molecules(scaffold_smiles, n_generate)
    campaign.stats["generated"] = len(generated)
    logger.info("Generated %d molecules", len(generated))

    # Step 2: Filter by drug-likeness via RDKit
    logger.info("Step 2: Filtering by drug-likeness")
    filtered = _filter_druglike(generated)
    campaign.stats["filtered"] = len(filtered)
    logger.info("Passed filter: %d / %d", len(filtered), len(generated))

    # Step 3: Dock filtered molecules via DiffDock NIM
    logger.info("Step 3: Docking %d molecules against %s", len(filtered), target)
    docked = await _dock_molecules(filtered, target, pdb_content)
    campaign.stats["docked"] = len(docked)
    logger.info("Docked: %d molecules", len(docked))

    # Step 4: Rank by composite score
    logger.info("Step 4: Ranking candidates")
    ranked = _rank_candidates(docked)
    campaign.results = ranked
    campaign.stats["top_score"] = ranked[0].composite_score if ranked else 0.0

    return {
        "scaffold": scaffold_smiles,
        "target": target,
        "stats": campaign.stats,
        "top_candidates": [
            {
                "smiles": r.smiles,
                "qed": round(r.qed, 3),
                "lipinski": r.lipinski_pass,
                "bbb": r.bbb_permeable,
                "docking_confidence": round(r.docking_confidence, 4),
                "composite_score": round(r.composite_score, 4),
            }
            for r in ranked[:20]
        ],
        "total_generated": campaign.stats.get("generated", 0),
        "total_filtered": campaign.stats.get("filtered", 0),
        "total_docked": campaign.stats.get("docked", 0),
    }


async def _generate_molecules(scaffold: str, n: int) -> list[ScreeningResult]:
    """Generate molecules using GenMol NIM."""
    from ..ingestion.adapters.nvidia_nims import genmol_generate

    results = []
    try:
        # GenMol uses SAFE format with [*{N-N}] size masks
        # Simple scaffolds (< 10 heavy atoms) work better as de novo with size constraint
        if "[*" in scaffold:
            safe_input = scaffold  # Already in SAFE format
        elif len(scaffold) < 15:
            # Small scaffold: use de novo generation for diversity
            safe_input = "[*{15-30}]"
            logger.info("Small scaffold — switching to de novo generation with size mask")
        else:
            safe_input = f"{scaffold}.[*{{10-25}}]"
        gen_result = await genmol_generate(
            scaffold_smiles=safe_input,
            num_molecules=n,
            temperature=2.0,
            noise=1.5,
            unique=True,
        )
        molecules = gen_result.get("molecules", gen_result.get("generated_molecules", []))
        for i, mol in enumerate(molecules):
            smiles = mol if isinstance(mol, str) else mol.get("smiles", mol.get("molecule", ""))
            if smiles:
                results.append(ScreeningResult(
                    smiles=smiles,
                    name=f"GEN-{i+1:04d}",
                    stage="generated",
                ))
    except Exception as e:
        logger.error("GenMol generation failed: %s", e)
        # Fallback: return scaffold itself
        results.append(ScreeningResult(smiles=scaffold, name="SCAFFOLD", stage="generated"))

    return results


def _filter_druglike(molecules: list[ScreeningResult]) -> list[ScreeningResult]:
    """Filter molecules by Lipinski Rule of 5, QED, and BBB permeability."""
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors, QED
    except ImportError:
        logger.warning("RDKit not available — skipping drug-likeness filter")
        for m in molecules:
            m.stage = "filtered"
            m.lipinski_pass = True
            m.qed = 0.5
        return molecules

    filtered = []
    for mol_result in molecules:
        try:
            mol = Chem.MolFromSmiles(mol_result.smiles)
            if mol is None:
                continue

            mw = Descriptors.MolWt(mol)
            logp = Descriptors.MolLogP(mol)
            hbd = Descriptors.NumHDonors(mol)
            hba = Descriptors.NumHAcceptors(mol)
            tpsa = Descriptors.TPSA(mol)

            # Lipinski Rule of 5
            lipinski = mw <= 500 and logp <= 5 and hbd <= 5 and hba <= 10
            # BBB permeability estimate (TPSA < 90, MW < 450)
            bbb = tpsa < 90 and mw < 450 and logp > 0
            # QED score
            qed_score = QED.qed(mol)

            mol_result.lipinski_pass = lipinski
            mol_result.bbb_permeable = bbb
            mol_result.qed = qed_score
            mol_result.stage = "filtered"

            if lipinski and qed_score > 0.3:
                filtered.append(mol_result)
        except Exception as e:
            logger.debug("Filter error for %s: %s", mol_result.smiles, e)

    return filtered


async def _dock_molecules(
    molecules: list[ScreeningResult],
    target: str,
    pdb_content: str | None = None,
) -> list[ScreeningResult]:
    """Dock molecules against target using DiffDock NIM."""
    from ..ingestion.adapters.nvidia_nims import diffdock_dock

    # Get PDB content for target if not provided
    if not pdb_content:
        pdb_content = _get_target_pdb(target)
        if not pdb_content:
            logger.error("No PDB structure available for target %s", target)
            return molecules

    # Convert SMILES to SDF format for DiffDock
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
    except ImportError:
        logger.warning("RDKit not available — cannot convert SMILES to SDF for docking")
        return molecules

    docked = []
    docked_count = 0
    failed_count = 0
    for mol_result in molecules:
        try:
            # Convert SMILES → 3D SDF (DiffDock needs SDF, not SMILES)
            mol = Chem.MolFromSmiles(mol_result.smiles)
            if mol is None:
                raise ValueError(f"Invalid SMILES: {mol_result.smiles}")
            mol = Chem.AddHs(mol)
            AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
            AllChem.MMFFOptimizeMolecule(mol, maxIters=200)
            sdf_block = Chem.MolToMolBlock(mol)

            dock_result = await diffdock_dock(
                protein_pdb=pdb_content,
                ligand_sdf=sdf_block,
                num_poses=3,
            )
            confidence = dock_result.get("position_confidence", dock_result.get("confidence", -1.0))
            if isinstance(confidence, list):
                confidence = max(confidence) if confidence else -1.0
            mol_result.docking_confidence = float(confidence)
            mol_result.docking_target = target
            mol_result.stage = "docked"
            docked.append(mol_result)
            docked_count += 1
        except Exception as e:
            failed_count += 1
            if failed_count <= 3:
                logger.warning("Docking failed for %s: %s", mol_result.name, e)
            mol_result.docking_confidence = -999.0
            mol_result.stage = "dock_failed"
            docked.append(mol_result)

    return docked


def _rank_candidates(molecules: list[ScreeningResult]) -> list[ScreeningResult]:
    """Rank candidates by composite score: docking confidence + QED + BBB bonus."""
    for mol in molecules:
        score = 0.0
        # Docking confidence (primary, weight 0.5)
        if mol.docking_confidence > -900:
            score += mol.docking_confidence * 0.5
        # QED (weight 0.3)
        score += mol.qed * 0.3
        # BBB bonus (weight 0.2)
        if mol.bbb_permeable:
            score += 0.2
        mol.composite_score = score
        mol.stage = "ranked"

    return sorted(molecules, key=lambda m: m.composite_score, reverse=True)


# AlphaFold PDB files for SMA targets (downloaded from alphafold.ebi.ac.uk)
_TARGET_PDB_MAP = {
    "SMN2": "data/pdb/SMN2_Q16637.pdb",
    "SMN1": "data/pdb/SMN2_Q16637.pdb",  # Same protein
    "STMN2": "data/pdb/STMN2_Q93045.pdb",
    "PLS3": "data/pdb/PLS3_P13797.pdb",
    "NCALD": "data/pdb/NCALD_P61601.pdb",
    "UBA1": "data/pdb/UBA1_P22314.pdb",
    "CORO1C": "data/pdb/CORO1C_Q9ULV4.pdb",
    "TP53": "data/pdb/TP53_P04637.pdb",
}


def _get_target_pdb(target: str) -> str | None:
    """Get PDB content for a known SMA target from AlphaFold structures."""
    from pathlib import Path

    pdb_path = _TARGET_PDB_MAP.get(target.upper())
    if not pdb_path:
        logger.warning("No PDB structure for target %s. Available: %s", target, list(_TARGET_PDB_MAP.keys()))
        return None

    # Try both relative (local dev) and absolute (moltbot) paths
    for base in [Path("."), Path("/home/bryzant/sma-platform")]:
        full = base / pdb_path
        if full.exists():
            content = full.read_text()
            atoms = sum(1 for l in content.split("\n") if l.startswith("ATOM"))
            logger.info("Loaded PDB for %s: %d atoms from %s", target, atoms, full)
            return content

    logger.warning("PDB file not found for %s at %s", target, pdb_path)
    return None
