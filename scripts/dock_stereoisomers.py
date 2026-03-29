#!/usr/bin/env python3
"""
Stereoisomer Panel: All 4 H-1152 Stereoisomers vs LIMK2 and ROCK2
==================================================================
Date: 2026-03-24

H-1152 has 2 stereocenters → 4 stereoisomers.
genmol_119 = (R,S) enantiomer.

Key question: Does stereochemistry matter for binding? If one enantiomer
is significantly better → eutomer/distomer separation → clear IP position.

Usage:
    export NVIDIA_API_KEY="nvapi-..."
    python scripts/dock_stereoisomers.py
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
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
if not NVIDIA_API_KEY:
    raise RuntimeError("NVIDIA_API_KEY environment variable is required")

DIFFDOCK_URL = "https://health.api.nvidia.com/v1/biology/mit/diffdock"
NUM_POSES = 20
RATE_LIMIT_DELAY = 3.0
RETRY_DELAY = 60

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
STRUCTURES_DIR = DATA_DIR / "structures"
DOCKING_DIR = DATA_DIR / "docking"
DOCKING_DIR.mkdir(parents=True, exist_ok=True)

LIMK2_PDB = STRUCTURES_DIR / "LIMK2_P53671_kinase.pdb"
ROCK2_PDB = STRUCTURES_DIR / "ROCK2_O75116_kinase.pdb"
OUTPUT_FILE = DOCKING_DIR / "stereoisomer_panel_2026-03-24.json"

# --- The 4 stereoisomers of H-1152 ---
STEREOISOMERS = [
    {
        "name": "H1152_SR",
        "smiles": "CC(C)C(=O)N1CC[C@H](C(F)(F)F)C[C@@H]1c1ccncc1",
        "config": "(S,R)",
        "note": "Enantiomer of genmol_119",
    },
    {
        "name": "H1152_RR",
        "smiles": "CC(C)C(=O)N1CC[C@@H](C(F)(F)F)C[C@@H]1c1ccncc1",
        "config": "(R,R)",
        "note": "Diastereomer — trans configuration",
    },
    {
        "name": "H1152_SS",
        "smiles": "CC(C)C(=O)N1CC[C@H](C(F)(F)F)C[C@H]1c1ccncc1",
        "config": "(S,S)",
        "note": "Diastereomer — trans configuration",
    },
    {
        "name": "genmol_119",
        "smiles": "CC(C)C(=O)N1CC[C@@H](C(F)(F)F)C[C@H]1c1ccncc1",
        "config": "(R,S)",
        "note": "Original hit — cis configuration",
    },
]


def smiles_to_sdf(smiles: str, name: str = "") -> str:
    """Convert SMILES to SDF format using RDKit."""
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


def load_protein_pdb(pdb_path: Path) -> str:
    """Load PDB and return ATOM-only lines."""
    text = pdb_path.read_text()
    atom_lines = [l for l in text.split("\n") if l.startswith("ATOM")]
    logger.info(f"Loaded PDB: {len(atom_lines)} ATOM lines from {pdb_path.name}")
    return "\n".join(atom_lines)


async def dock_single(
    protein_pdb: str,
    smiles: str,
    name: str,
    api_key: str,
) -> dict:
    """Dock a single molecule using DiffDock NIM."""
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

    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=180) as client:
                resp = await client.post(DIFFDOCK_URL, json=payload, headers=headers)

                if resp.status_code == 400:
                    logger.error(f"  400 Bad Request: {resp.text[:300]}")
                    resp.raise_for_status()

                if resp.status_code in (403, 429):
                    wait = RETRY_DELAY * (attempt + 1)
                    logger.warning(f"  Rate limited ({resp.status_code}), waiting {wait}s (attempt {attempt+1}/{max_retries})...")
                    await asyncio.sleep(wait)
                    continue

                resp.raise_for_status()
                result = resp.json()
                break
        except Exception as e:
            if attempt < max_retries - 1:
                wait = RETRY_DELAY * (attempt + 1)
                logger.warning(f"  Error: {e}, retrying in {wait}s...")
                await asyncio.sleep(wait)
            else:
                raise
    else:
        raise RuntimeError(f"Failed after {max_retries} retries")

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


async def dock_panel(target_name: str, pdb_path: Path) -> list:
    """Dock all 4 stereoisomers against a target."""
    protein_pdb = load_protein_pdb(pdb_path)
    results = []

    for i, comp in enumerate(STEREOISOMERS):
        logger.info(f"\n  [{i+1}/4] {comp['name']} {comp['config']} vs {target_name}")
        logger.info(f"    SMILES: {comp['smiles']}")

        try:
            dock_result = await dock_single(protein_pdb, comp["smiles"], comp["name"], NVIDIA_API_KEY)
            entry = {
                **comp,
                "target": target_name,
                **dock_result,
            }
            results.append(entry)

            conf = dock_result.get("top_confidence")
            if conf is not None:
                binding = "BINDING" if conf > 0 else "no binding"
                logger.info(
                    f"    -> {target_name} top={conf:+.4f} ({binding}), "
                    f"pos_poses={dock_result['positive_poses']}/{dock_result['num_poses']}, "
                    f"mean={dock_result['mean_confidence']:+.4f}"
                )
            else:
                logger.warning(f"    -> No confidence returned")

        except Exception as e:
            logger.error(f"    -> FAILED: {e}")
            results.append({**comp, "target": target_name, "error": str(e)})

        if i < len(STEREOISOMERS) - 1:
            await asyncio.sleep(RATE_LIMIT_DELAY)

    return results


def analyze_results(limk2_results: list, rock2_results: list) -> dict:
    """Analyze stereoisomer preferences."""
    analysis = {}

    for target_name, results in [("LIMK2", limk2_results), ("ROCK2", rock2_results)]:
        scored = [r for r in results if r.get("top_confidence") is not None]
        if not scored:
            analysis[target_name] = {"error": "No results"}
            continue

        scored_sorted = sorted(scored, key=lambda x: x["top_confidence"], reverse=True)
        best = scored_sorted[0]
        worst = scored_sorted[-1]

        genmol_119 = next((r for r in scored if r["name"] == "genmol_119"), None)
        genmol_rank = next((i+1 for i, r in enumerate(scored_sorted) if r["name"] == "genmol_119"), None)

        # Eudismic ratio: best / enantiomer (mirror image)
        # (R,S) mirror is (S,R)
        enantiomer_pairs = {
            "genmol_119": "H1152_SR",  # (R,S) <-> (S,R)
            "H1152_SR": "genmol_119",
            "H1152_RR": "H1152_SS",    # (R,R) <-> (S,S)
            "H1152_SS": "H1152_RR",
        }

        # Calculate stereo preference magnitude
        conf_range = best["top_confidence"] - worst["top_confidence"]
        mean_range = best.get("mean_confidence", 0) - worst.get("mean_confidence", 0)

        analysis[target_name] = {
            "ranking": [
                {
                    "rank": i+1,
                    "name": r["name"],
                    "config": r["config"],
                    "top_confidence": round(r["top_confidence"], 4),
                    "mean_confidence": round(r.get("mean_confidence", 0), 4),
                    "positive_poses": r.get("positive_poses", 0),
                }
                for i, r in enumerate(scored_sorted)
            ],
            "best_stereoisomer": {
                "name": best["name"],
                "config": best["config"],
                "top_confidence": round(best["top_confidence"], 4),
            },
            "worst_stereoisomer": {
                "name": worst["name"],
                "config": worst["config"],
                "top_confidence": round(worst["top_confidence"], 4),
            },
            "confidence_range": round(conf_range, 4),
            "mean_confidence_range": round(mean_range, 4),
            "genmol_119_rank": genmol_rank,
            "genmol_119_is_best": best["name"] == "genmol_119",
            "stereo_matters": conf_range > 0.2,  # >0.2 = significant
            "stereo_significance": (
                "STRONG" if conf_range > 0.5 else
                "MODERATE" if conf_range > 0.2 else
                "WEAK"
            ),
        }

    # Cross-target analysis
    limk2_best = analysis.get("LIMK2", {}).get("best_stereoisomer", {}).get("name")
    rock2_best = analysis.get("ROCK2", {}).get("best_stereoisomer", {}).get("name")

    analysis["cross_target"] = {
        "same_best_for_both": limk2_best == rock2_best,
        "limk2_best": limk2_best,
        "rock2_best": rock2_best,
        "genmol_119_optimal_for_limk2": analysis.get("LIMK2", {}).get("genmol_119_is_best", False),
        "genmol_119_optimal_for_rock2": analysis.get("ROCK2", {}).get("genmol_119_is_best", False),
    }

    # IP implications
    limk2_range = analysis.get("LIMK2", {}).get("confidence_range", 0)
    rock2_range = analysis.get("ROCK2", {}).get("confidence_range", 0)

    if limk2_range > 0.3 or rock2_range > 0.3:
        ip_note = (
            "SIGNIFICANT stereopreference detected. Pure enantiomer would be superior "
            "to racemic H-1152. Eutomer/distomer separation provides IP differentiation "
            "(similar to omeprazole → esomeprazole strategy)."
        )
    elif limk2_range > 0.1 or rock2_range > 0.1:
        ip_note = (
            "MODERATE stereopreference. Racemic H-1152 may work, but pure enantiomer "
            "could provide improved potency. Worth investigating in vitro."
        )
    else:
        ip_note = (
            "MINIMAL stereopreference. Racemic H-1152 likely has similar activity "
            "to any pure enantiomer. Less IP differentiation opportunity."
        )

    analysis["ip_implications"] = {
        "note": ip_note,
        "racemic_prediction": (
            "Racemic would show ~50% of optimal enantiomer activity "
            "if stereopreference is strong (eutomer diluted by distomer)"
            if max(limk2_range, rock2_range) > 0.3
            else "Racemic would show similar activity to pure enantiomers"
        ),
    }

    return analysis


async def main():
    logger.info("=" * 70)
    logger.info("STEREOISOMER PANEL: H-1152 (4 isomers) vs LIMK2 + ROCK2")
    logger.info(f"Date: 2026-03-24")
    logger.info(f"Poses per docking: {NUM_POSES}")
    logger.info(f"Total dockings: 8 (4 isomers x 2 targets)")
    logger.info("=" * 70)

    # Pre-validate all SMILES -> SDF
    logger.info("\nPre-validating SMILES -> SDF conversion...")
    for comp in STEREOISOMERS:
        try:
            smiles_to_sdf(comp["smiles"], name=comp["name"])
            logger.info(f"  {comp['name']} {comp['config']}: OK")
        except Exception as e:
            logger.error(f"  {comp['name']}: FAILED - {e}")
            raise

    start_time = time.time()

    # Dock against LIMK2
    logger.info("\n" + "=" * 50)
    logger.info("PHASE 1: All stereoisomers vs LIMK2")
    logger.info("=" * 50)
    limk2_results = await dock_panel("LIMK2", LIMK2_PDB)

    # Brief pause between targets
    await asyncio.sleep(5)

    # Dock against ROCK2
    logger.info("\n" + "=" * 50)
    logger.info("PHASE 2: All stereoisomers vs ROCK2")
    logger.info("=" * 50)
    rock2_results = await dock_panel("ROCK2", ROCK2_PDB)

    elapsed = time.time() - start_time

    # Analyze
    analysis = analyze_results(limk2_results, rock2_results)

    # Build output
    output = {
        "campaign": "Stereoisomer Panel: H-1152 enantiomers vs LIMK2 + ROCK2",
        "date": "2026-03-24",
        "rationale": (
            "H-1152 has 2 stereocenters. genmol_119 is the (R,S) enantiomer "
            "that scored +1.058 on LIMK2. This panel docks all 4 stereoisomers "
            "to determine if stereochemistry drives binding affinity."
        ),
        "diffdock_version": "v2.2 (NVIDIA NIM)",
        "num_poses_per_docking": NUM_POSES,
        "total_dockings": 8,
        "elapsed_seconds": round(elapsed, 1),
        "stereoisomers": [
            {
                "name": s["name"],
                "smiles": s["smiles"],
                "config": s["config"],
                "note": s["note"],
            }
            for s in STEREOISOMERS
        ],
        "limk2_results": limk2_results,
        "rock2_results": rock2_results,
        "analysis": analysis,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    logger.info(f"\n{'=' * 70}")
    logger.info(f"Results saved to {OUTPUT_FILE}")
    logger.info(f"Total time: {elapsed:.0f}s")

    # Print summary
    logger.info(f"\n{'=' * 70}")
    logger.info("STEREOISOMER PANEL SUMMARY")
    logger.info(f"{'=' * 70}")

    for target in ["LIMK2", "ROCK2"]:
        a = analysis.get(target, {})
        logger.info(f"\n{target}:")
        for r in a.get("ranking", []):
            marker = " ← genmol_119" if r["name"] == "genmol_119" else ""
            logger.info(
                f"  #{r['rank']} {r['name']} {r['config']}: "
                f"top={r['top_confidence']:+.4f}, "
                f"mean={r['mean_confidence']:+.4f}, "
                f"pos_poses={r['positive_poses']}/20"
                f"{marker}"
            )
        logger.info(f"  Confidence range: {a.get('confidence_range', 0):.4f}")
        logger.info(f"  Stereo significance: {a.get('stereo_significance', 'N/A')}")
        logger.info(f"  genmol_119 is best: {a.get('genmol_119_is_best', 'N/A')}")

    ct = analysis.get("cross_target", {})
    logger.info(f"\nCross-target:")
    logger.info(f"  Same best for both targets: {ct.get('same_best_for_both')}")
    logger.info(f"  LIMK2 best: {ct.get('limk2_best')}")
    logger.info(f"  ROCK2 best: {ct.get('rock2_best')}")

    ip = analysis.get("ip_implications", {})
    logger.info(f"\nIP Implications:")
    logger.info(f"  {ip.get('note', 'N/A')}")
    logger.info(f"  Racemic prediction: {ip.get('racemic_prediction', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())
