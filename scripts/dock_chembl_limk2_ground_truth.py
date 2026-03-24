#!/usr/bin/env python3
"""
ChEMBL LIMK2 Ground Truth Calibration via DiffDock v2.2
========================================================
Date: 2026-03-25

Dock the top 20 ChEMBL LIMK2 compounds (by pChEMBL value) against LIMK2
to calibrate DiffDock predictions against real experimental binding data.

Input:  data/chembl_limk2_bioactivity.json (301 compounds, SMILES included)
Target: data/structures/LIMK2_P53671_kinase.pdb (residues 309-595)
Output: data/docking/chembl_limk2_ground_truth_2026-03-25.json

Usage:
    export NVIDIA_API_KEY="nvapi-..."
    python scripts/dock_chembl_limk2_ground_truth.py
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# --- Configuration ---
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "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")
NVIDIA_API_KEY_2 = os.environ.get("NVIDIA_API_KEY_2", "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")

DIFFDOCK_URL = "https://health.api.nvidia.com/v1/biology/mit/diffdock"
NUM_POSES = 20
RATE_LIMIT_DELAY = 3.0  # conservative
RETRY_DELAY = 30
MAX_RETRIES = 3

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
STRUCTURES_DIR = DATA_DIR / "structures"
DOCKING_DIR = DATA_DIR / "docking"
DOCKING_DIR.mkdir(parents=True, exist_ok=True)

BIOACTIVITY_JSON = DATA_DIR / "chembl_limk2_bioactivity.json"
LIMK2_PDB = STRUCTURES_DIR / "LIMK2_P53671_kinase.pdb"
OUTPUT_FILE = DOCKING_DIR / "chembl_limk2_ground_truth_2026-03-25.json"

# LX-7101 reference (already docked, include in correlation)
LX7101_REFERENCE = {
    "chembl_id": "CHEMBL3356433",
    "name": "LX-7101",
    "smiles": "Cc1c[nH]c2ncnc(N3CCC(CN)(C(=O)Nc4cccc(OC(=O)N(C)C)c4)CC3)c12",
    "best_pchembl": 8.8,
    "mean_pchembl": 8.8,
    "source": "Phase 1 clinical LIMK inhibitor",
    "previously_docked_confidence": -0.314,
}

TOP_N = 20


def smiles_to_sdf(smiles: str, name: str = "") -> str:
    """Convert SMILES to SDF format using RDKit (required by DiffDock v2.2 NIM)."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    mol = Chem.AddHs(mol)
    result = AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
    if result == -1:
        AllChem.EmbedMolecule(mol, randomSeed=42)
    AllChem.MMFFOptimizeMolecule(mol)
    if name:
        mol.SetProp("_Name", name)
    return Chem.MolToMolBlock(mol)


def compute_descriptors(smiles: str) -> dict:
    """Compute basic molecular descriptors."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {}
    return {
        "mw": round(Descriptors.MolWt(mol), 1),
        "logp": round(Descriptors.MolLogP(mol), 2),
        "hbd": Descriptors.NumHDonors(mol),
        "hba": Descriptors.NumHAcceptors(mol),
        "tpsa": round(Descriptors.TPSA(mol), 1),
        "rotatable_bonds": Descriptors.NumRotatableBonds(mol),
        "heavy_atoms": mol.GetNumHeavyAtoms(),
    }


def load_protein_pdb(pdb_path: Path) -> str:
    """Load PDB and return ATOM-only lines."""
    text = pdb_path.read_text()
    atom_lines = [l for l in text.split("\n") if l.startswith("ATOM")]
    logger.info(f"Loaded PDB: {len(atom_lines)} ATOM lines from {pdb_path.name}")
    return "\n".join(atom_lines)


def load_top_compounds() -> list:
    """Load top N compounds from ChEMBL bioactivity data, sorted by best_pchembl."""
    with open(BIOACTIVITY_JSON) as f:
        data = json.load(f)
    compounds = data["compounds"]
    # Sort by best_pchembl descending, take top N
    sorted_compounds = sorted(compounds, key=lambda x: x["best_pchembl"], reverse=True)
    top = sorted_compounds[:TOP_N]
    logger.info(f"Selected top {len(top)} compounds from {len(compounds)} total")
    logger.info(f"  pChEMBL range: {top[-1]['best_pchembl']} - {top[0]['best_pchembl']}")
    return top


async def dock_single(
    protein_pdb: str,
    smiles: str,
    name: str,
    api_key: str,
    backup_key: str,
) -> dict:
    """Dock a single molecule using DiffDock NIM v2.2."""
    import httpx

    ligand_sdf = smiles_to_sdf(smiles, name=name)

    payload = {
        "ligand": ligand_sdf,
        "ligand_file_type": "sdf",
        "protein": protein_pdb,
        "num_poses": NUM_POSES,
        "time_divisions": 20,
        "steps": 18,
        "save_trajectory": False,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    current_key = api_key
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=180) as client:
                resp = await client.post(DIFFDOCK_URL, json=payload, headers=headers)

                if resp.status_code == 400:
                    logger.error(f"  400 Bad Request: {resp.text[:300]}")
                    resp.raise_for_status()

                if resp.status_code in (403, 429):
                    if current_key == api_key and backup_key:
                        logger.warning(f"  Rate limited ({resp.status_code}), switching to backup key...")
                        current_key = backup_key
                        headers["Authorization"] = f"Bearer {backup_key}"
                        await asyncio.sleep(5)
                        continue
                    else:
                        wait = RETRY_DELAY * (attempt + 1)
                        logger.warning(f"  Rate limited ({resp.status_code}), waiting {wait}s...")
                        await asyncio.sleep(wait)
                        continue

                if resp.status_code == 500:
                    wait = RETRY_DELAY * (attempt + 1)
                    logger.warning(f"  Server error 500, retrying in {wait}s (attempt {attempt+1}/{MAX_RETRIES})...")
                    await asyncio.sleep(wait)
                    continue

                resp.raise_for_status()
                result = resp.json()
                break
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY * (attempt + 1)
                logger.warning(f"  Error: {e}, retrying in {wait}s...")
                await asyncio.sleep(wait)
            else:
                raise
    else:
        raise RuntimeError(f"Failed after {MAX_RETRIES} retries")

    # Parse DiffDock v2.2 response
    confidences = result.get("position_confidence", [])
    if not confidences:
        poses = result.get("output", []) if isinstance(result.get("output"), list) else []
        if not poses:
            poses = result.get("poses", [])
        for pose in poses:
            if isinstance(pose, dict):
                conf = pose.get("confidence", pose.get("score", None))
                if conf is not None:
                    confidences.append(float(conf))
        if not confidences and "confidence" in result:
            confidences = [float(result["confidence"])]

    confidences = [float(c) for c in confidences]
    top_confidence = max(confidences) if confidences else None
    mean_confidence = sum(confidences) / len(confidences) if confidences else None

    return {
        "num_poses": len(confidences),
        "top_confidence": top_confidence,
        "mean_confidence": mean_confidence,
        "all_confidences": sorted(confidences, reverse=True) if confidences else [],
        "positive_poses": len([c for c in confidences if c > 0]),
    }


async def main():
    start = time.time()

    logger.info("=" * 70)
    logger.info("ChEMBL LIMK2 Ground Truth Calibration")
    logger.info("=" * 70)
    logger.info(f"Purpose: Calibrate DiffDock predictions vs real pChEMBL values")
    logger.info(f"Compounds: Top {TOP_N} by pChEMBL from 301 ChEMBL LIMK2 compounds")
    logger.info(f"Target: LIMK2 kinase domain (P53671, residues 309-595)")
    logger.info(f"DiffDock: v2.2 NIM, {NUM_POSES} poses per compound")
    logger.info(f"Rate limit: {RATE_LIMIT_DELAY}s between requests")
    logger.info("=" * 70)

    # Load data
    compounds = load_top_compounds()
    protein_pdb = load_protein_pdb(LIMK2_PDB)

    # Pre-validate SMILES and compute descriptors
    logger.info("\nPre-validating SMILES and computing descriptors...")
    for c in compounds:
        try:
            sdf = smiles_to_sdf(c["smiles"], name=c["chembl_id"])
            desc = compute_descriptors(c["smiles"])
            c["descriptors"] = desc
            logger.info(f"  {c['chembl_id']} pChEMBL={c['best_pchembl']}: OK (MW={desc['mw']})")
        except Exception as e:
            logger.error(f"  {c['chembl_id']}: FAILED ({e})")
            return

    # Also dock LX-7101 fresh for direct comparison
    lx7101_compound = {
        "chembl_id": LX7101_REFERENCE["chembl_id"],
        "smiles": LX7101_REFERENCE["smiles"],
        "best_pchembl": LX7101_REFERENCE["best_pchembl"],
        "mean_pchembl": LX7101_REFERENCE["mean_pchembl"],
        "n_measurements": 1,
        "descriptors": compute_descriptors(LX7101_REFERENCE["smiles"]),
        "is_reference": True,
        "source": LX7101_REFERENCE["source"],
    }

    all_compounds = compounds + [lx7101_compound]
    total = len(all_compounds)

    # Dock each compound
    results = []
    for i, comp in enumerate(all_compounds, 1):
        chembl_id = comp["chembl_id"]
        pchembl = comp["best_pchembl"]
        mw = comp.get("descriptors", {}).get("mw", "?")
        is_ref = comp.get("is_reference", False)
        tag = " [REFERENCE]" if is_ref else ""

        logger.info(f"\n[{i}/{total}] {chembl_id} (pChEMBL={pchembl}, MW={mw}){tag}")

        try:
            dock_result = await dock_single(
                protein_pdb, comp["smiles"], chembl_id,
                NVIDIA_API_KEY, NVIDIA_API_KEY_2
            )

            entry = {
                "rank": i,
                "chembl_id": chembl_id,
                "smiles": comp["smiles"],
                "best_pchembl": pchembl,
                "mean_pchembl": comp.get("mean_pchembl", pchembl),
                "n_measurements": comp.get("n_measurements", 1),
                "descriptors": comp.get("descriptors", {}),
                "is_reference": is_ref,
                **dock_result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            if is_ref:
                entry["source"] = comp["source"]
                entry["previous_confidence"] = LX7101_REFERENCE["previously_docked_confidence"]

            results.append(entry)

            conf = dock_result.get("top_confidence")
            if conf is not None:
                binding = "BINDING" if conf > 0 else "no binding"
                logger.info(
                    f"  -> top_confidence: {conf:+.4f} ({binding}), "
                    f"positive: {dock_result['positive_poses']}/{dock_result['num_poses']}, "
                    f"mean: {dock_result['mean_confidence']:+.4f}"
                )
            else:
                logger.warning(f"  -> No confidence returned")

        except Exception as e:
            logger.error(f"  -> FAILED: {e}")
            results.append({
                "rank": i,
                "chembl_id": chembl_id,
                "smiles": comp["smiles"],
                "best_pchembl": pchembl,
                "mean_pchembl": comp.get("mean_pchembl", pchembl),
                "is_reference": is_ref,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        # Rate limiting
        if i < total:
            logger.info(f"  (waiting {RATE_LIMIT_DELAY}s)")
            await asyncio.sleep(RATE_LIMIT_DELAY)

    elapsed = time.time() - start

    # Compute correlation analysis
    analysis = compute_correlation(results)

    # Assemble output
    output = {
        "campaign": "ChEMBL LIMK2 Ground Truth Calibration",
        "date": "2026-03-25",
        "purpose": (
            "Dock top 20 ChEMBL LIMK2 compounds (real experimental pChEMBL) against LIMK2 "
            "to calibrate DiffDock confidence scores against ground truth binding data. "
            "This tells us how trustworthy our DiffDock predictions are."
        ),
        "diffdock_version": "v2.2 (NVIDIA NIM)",
        "num_poses": NUM_POSES,
        "target": {
            "symbol": "LIMK2",
            "uniprot": "P53671",
            "domain": "kinase (residues 309-595)",
            "pdb_file": "LIMK2_P53671_kinase.pdb",
        },
        "source_data": {
            "file": "chembl_limk2_bioactivity.json",
            "total_compounds": 301,
            "top_n_selected": TOP_N,
            "pchembl_range": f"{results[-1]['best_pchembl']} - {results[0]['best_pchembl']}",
            "plus_lx7101_reference": True,
        },
        "elapsed_seconds": round(elapsed, 1),
        "results": results,
        "correlation_analysis": analysis,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    logger.info(f"\nResults saved to {OUTPUT_FILE}")

    # Print summary
    print_summary(results, analysis, elapsed)


def compute_correlation(results: list) -> dict:
    """Compute correlation between pChEMBL and DiffDock confidence."""
    # Filter successful results
    valid = [r for r in results if r.get("top_confidence") is not None and r.get("best_pchembl") is not None]

    if len(valid) < 3:
        return {"error": "Too few valid results for correlation", "n": len(valid)}

    pchembl_values = [r["best_pchembl"] for r in valid]
    confidence_values = [r["top_confidence"] for r in valid]

    # Pearson correlation (manual, no scipy dependency)
    n = len(valid)
    mean_p = sum(pchembl_values) / n
    mean_c = sum(confidence_values) / n

    cov = sum((p - mean_p) * (c - mean_c) for p, c in zip(pchembl_values, confidence_values))
    std_p = (sum((p - mean_p) ** 2 for p in pchembl_values)) ** 0.5
    std_c = (sum((c - mean_c) ** 2 for c in confidence_values)) ** 0.5

    if std_p == 0 or std_c == 0:
        pearson_r = 0.0
    else:
        pearson_r = cov / (std_p * std_c)

    r_squared = pearson_r ** 2

    # Spearman rank correlation (manual)
    def rank_list(values):
        sorted_indices = sorted(range(len(values)), key=lambda i: values[i])
        ranks = [0] * len(values)
        for rank, idx in enumerate(sorted_indices, 1):
            ranks[idx] = rank
        return ranks

    pchembl_ranks = rank_list(pchembl_values)
    confidence_ranks = rank_list(confidence_values)

    # Spearman = Pearson on ranks
    mean_pr = sum(pchembl_ranks) / n
    mean_cr = sum(confidence_ranks) / n
    cov_r = sum((pr - mean_pr) * (cr - mean_cr) for pr, cr in zip(pchembl_ranks, confidence_ranks))
    std_pr = (sum((pr - mean_pr) ** 2 for pr in pchembl_ranks)) ** 0.5
    std_cr = (sum((cr - mean_cr) ** 2 for cr in confidence_ranks)) ** 0.5
    if std_pr == 0 or std_cr == 0:
        spearman_rho = 0.0
    else:
        spearman_rho = cov_r / (std_pr * std_cr)

    # Rank agreement: does DiffDock rank the top 5 real binders in its top 10?
    sorted_by_pchembl = sorted(valid, key=lambda x: x["best_pchembl"], reverse=True)
    sorted_by_confidence = sorted(valid, key=lambda x: x["top_confidence"], reverse=True)

    top5_real = set(r["chembl_id"] for r in sorted_by_pchembl[:5])
    top10_diffdock = set(r["chembl_id"] for r in sorted_by_confidence[:10])
    top5_overlap = top5_real & top10_diffdock

    # Binding detection: does DiffDock give positive confidence to known strong binders?
    strong_binders = [r for r in valid if r["best_pchembl"] >= 9.0]
    strong_with_positive = [r for r in strong_binders if r["top_confidence"] > 0]

    return {
        "n_compounds": n,
        "pearson_r": round(pearson_r, 4),
        "r_squared": round(r_squared, 4),
        "spearman_rho": round(spearman_rho, 4),
        "interpretation": interpret_correlation(pearson_r, spearman_rho),
        "pchembl_range": {
            "min": min(pchembl_values),
            "max": max(pchembl_values),
            "mean": round(sum(pchembl_values) / n, 2),
        },
        "confidence_range": {
            "min": round(min(confidence_values), 4),
            "max": round(max(confidence_values), 4),
            "mean": round(mean_c, 4),
        },
        "rank_agreement": {
            "top5_real_in_top10_diffdock": len(top5_overlap),
            "top5_real_ids": list(top5_real),
            "top10_diffdock_ids": list(r["chembl_id"] for r in sorted_by_confidence[:10]),
            "overlap": list(top5_overlap),
        },
        "binding_detection": {
            "strong_binders_pchembl_ge9": len(strong_binders),
            "with_positive_confidence": len(strong_with_positive),
            "detection_rate": round(len(strong_with_positive) / len(strong_binders), 2) if strong_binders else 0,
        },
        "per_compound": [
            {
                "chembl_id": r["chembl_id"],
                "pchembl": r["best_pchembl"],
                "diffdock_confidence": round(r["top_confidence"], 4),
                "pchembl_rank": next(i for i, x in enumerate(sorted_by_pchembl, 1) if x["chembl_id"] == r["chembl_id"]),
                "diffdock_rank": next(i for i, x in enumerate(sorted_by_confidence, 1) if x["chembl_id"] == r["chembl_id"]),
            }
            for r in sorted_by_pchembl
        ],
    }


def interpret_correlation(pearson_r: float, spearman_rho: float) -> str:
    """Interpret the correlation values in plain language."""
    if pearson_r > 0.7:
        strength = "STRONG positive"
    elif pearson_r > 0.4:
        strength = "MODERATE positive"
    elif pearson_r > 0.1:
        strength = "WEAK positive"
    elif pearson_r > -0.1:
        strength = "NO"
    elif pearson_r > -0.4:
        strength = "WEAK negative"
    elif pearson_r > -0.7:
        strength = "MODERATE negative"
    else:
        strength = "STRONG negative"

    msg = f"{strength} correlation (Pearson r={pearson_r:.3f}, Spearman rho={spearman_rho:.3f}). "

    if pearson_r > 0.5 and spearman_rho > 0.5:
        msg += "DiffDock confidence tracks real binding potency well — predictions are calibrated."
    elif pearson_r > 0.2 or spearman_rho > 0.3:
        msg += "DiffDock shows some ability to rank binders but is not quantitatively reliable."
    elif abs(pearson_r) < 0.2 and abs(spearman_rho) < 0.2:
        msg += "DiffDock confidence does NOT correlate with real binding — use only for pose generation, not ranking."
    else:
        msg += "Unexpected pattern — investigate possible confounders (MW bias, scaffold bias)."

    return msg


def print_summary(results: list, analysis: dict, elapsed: float):
    """Print summary with correlation analysis."""
    valid = [r for r in results if r.get("top_confidence") is not None]
    errors = [r for r in results if r.get("error")]

    logger.info("\n" + "=" * 80)
    logger.info("GROUND TRUTH CALIBRATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Compounds docked: {len(valid)} | Errors: {len(errors)} | Time: {elapsed:.0f}s")

    if valid:
        # Ranked table
        sorted_by_pchembl = sorted(valid, key=lambda x: x["best_pchembl"], reverse=True)

        logger.info(f"\n{'Rank':>4} {'ChEMBL ID':>15} {'pChEMBL':>8} {'DiffDock':>10} {'Pos/Tot':>8} {'Mean':>8} {'Ref':>4}")
        logger.info("-" * 65)

        for i, r in enumerate(sorted_by_pchembl, 1):
            ref = "*" if r.get("is_reference") else ""
            binding = "+" if r["top_confidence"] > 0 else "-"
            logger.info(
                f"{i:4d} {r['chembl_id']:>15s} {r['best_pchembl']:>8.2f} "
                f"{r['top_confidence']:>+10.4f} "
                f"{r['positive_poses']:>3d}/{r['num_poses']:<3d} "
                f"{r['mean_confidence']:>+8.4f} {ref:>4s}"
            )

        # Correlation
        logger.info(f"\n--- CORRELATION ANALYSIS ---")
        logger.info(f"  Pearson r:     {analysis['pearson_r']:+.4f}")
        logger.info(f"  R-squared:     {analysis['r_squared']:.4f}")
        logger.info(f"  Spearman rho:  {analysis['spearman_rho']:+.4f}")
        logger.info(f"  Interpretation: {analysis['interpretation']}")

        # Rank agreement
        ra = analysis["rank_agreement"]
        logger.info(f"\n--- RANK AGREEMENT ---")
        logger.info(f"  Top 5 real binders found in DiffDock top 10: {ra['top5_real_in_top10_diffdock']}/5")
        logger.info(f"  Overlap: {ra['overlap']}")

        # Binding detection
        bd = analysis["binding_detection"]
        logger.info(f"\n--- BINDING DETECTION ---")
        logger.info(f"  Strong binders (pChEMBL >= 9.0): {bd['strong_binders_pchembl_ge9']}")
        logger.info(f"  With positive DiffDock confidence: {bd['with_positive_confidence']}")
        logger.info(f"  Detection rate: {bd['detection_rate']:.0%}")

        # Key question
        logger.info(f"\n--- KEY QUESTION: How trustworthy are DiffDock predictions? ---")
        if analysis["pearson_r"] > 0.5:
            logger.info("  ANSWER: TRUSTWORTHY — DiffDock confidence correlates with real binding.")
        elif analysis["pearson_r"] > 0.2:
            logger.info("  ANSWER: PARTIALLY — DiffDock shows some predictive power but use with caution.")
        else:
            logger.info("  ANSWER: NOT RELIABLE for ranking — DiffDock confidence does not track real potency.")
            logger.info("  USE FOR: pose generation and binding site identification only.")


if __name__ == "__main__":
    asyncio.run(main())
