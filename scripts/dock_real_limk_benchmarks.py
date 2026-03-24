#!/usr/bin/env python3
"""
Real-World LIMK Inhibitor Benchmarking: LX-7101, MDI-114215, BMS-5
====================================================================
Date: 2026-03-25

Dock 3 real LIMK inhibitors against LIMK2 and ROCK2 to benchmark
our AI-designed candidates ((S,S)-H-1152, genmol_119).

Compounds:
  1. LX-7101 (CHEMBL3356433) — Phase 1 clinical, dual LIMK2/ROCK2, pChEMBL 8.8
  2. MDI-114215 — First CNS-penetrant LIMK1/2 inhibitor (J Med Chem 2024)
  3. BMS-5 — Known LIMK1/2 dual inhibitor

Usage:
    export NVIDIA_API_KEY="nvapi-..."
    python scripts/dock_real_limk_benchmarks.py
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
OUTPUT_FILE = DOCKING_DIR / "real_limk_benchmarks_2026-03-25.json"

# --- Real-world LIMK inhibitors ---
COMPOUNDS = [
    {
        "name": "LX-7101",
        "smiles": "Cc1c[nH]c2ncnc(N3CCC(CN)(C(=O)Nc4cccc(OC(=O)N(C)C)c4)CC3)c12",
        "chembl_id": "CHEMBL3356433",
        "source": "Phase 1 clinical, dual LIMK2/ROCK2 inhibitor, pChEMBL 8.8",
        "mw": 451.5,
    },
    {
        "name": "MDI-114215",
        "smiles": "O=S(NC1=CC=CC=C1)(C2=CC=C(C(N(CC3CC3)CC4=CC=C(NCCO)C=C4)=O)C=C2)=O",
        "chembl_id": None,
        "source": "First CNS-penetrant LIMK1/2 allosteric inhibitor (J Med Chem 2024, Baldwin et al.)",
        "mw": 479.6,
    },
    {
        "name": "BMS-5",
        "smiles": "CC(=O)Nc1ccc(-c2nc3cc(NS(=O)(=O)c4ccc(F)cc4)ccc3[nH]2)cc1",
        "chembl_id": None,
        "source": "Known LIMK1/2 dual inhibitor (Bristol-Myers Squibb)",
        "mw": 424.5,
    },
]

# Our AI candidates for comparison (from previous docking campaigns)
AI_CANDIDATES = [
    {
        "name": "(S,S)-H-1152",
        "limk2_top": 0.957,
        "rock2_top": 0.484,
        "source": "AI stereo-optimized (stereoisomer panel 2026-03-24)",
    },
    {
        "name": "genmol_119",
        "limk2_top": 0.704,
        "rock2_top": 0.400,
        "source": "AI designed (GenMol + DiffDock campaign 2026-03-24)",
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
    """Dock all benchmark compounds against a target."""
    protein_pdb = load_protein_pdb(pdb_path)
    results = []

    for i, comp in enumerate(COMPOUNDS):
        logger.info(f"\n  [{i+1}/{len(COMPOUNDS)}] {comp['name']} vs {target_name}")
        logger.info(f"    SMILES: {comp['smiles'][:60]}...")
        logger.info(f"    Source: {comp['source']}")

        try:
            dock_result = await dock_single(protein_pdb, comp["smiles"], comp["name"], NVIDIA_API_KEY)
            entry = {
                "name": comp["name"],
                "smiles": comp["smiles"],
                "chembl_id": comp.get("chembl_id"),
                "source": comp["source"],
                "mw": comp["mw"],
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
            results.append({
                "name": comp["name"],
                "smiles": comp["smiles"],
                "source": comp["source"],
                "target": target_name,
                "error": str(e),
            })

        if i < len(COMPOUNDS) - 1:
            await asyncio.sleep(RATE_LIMIT_DELAY)

    return results


def build_comparison_table(limk2_results: list, rock2_results: list) -> dict:
    """Build comparison table: real drugs vs AI candidates."""
    # Build lookup
    limk2_by_name = {r["name"]: r for r in limk2_results if r.get("top_confidence") is not None}
    rock2_by_name = {r["name"]: r for r in rock2_results if r.get("top_confidence") is not None}

    rows = []

    # AI candidates (from previous campaigns)
    for ai in AI_CANDIDATES:
        rows.append({
            "compound": ai["name"],
            "type": "AI-designed",
            "limk2_top": ai["limk2_top"],
            "rock2_top": ai["rock2_top"],
            "source": ai["source"],
        })

    # Real-world benchmarks
    for comp in COMPOUNDS:
        name = comp["name"]
        limk2_conf = limk2_by_name.get(name, {}).get("top_confidence")
        rock2_conf = rock2_by_name.get(name, {}).get("top_confidence")
        limk2_pos = limk2_by_name.get(name, {}).get("positive_poses")
        rock2_pos = rock2_by_name.get(name, {}).get("positive_poses")

        rows.append({
            "compound": name,
            "type": "real-world",
            "limk2_top": round(limk2_conf, 4) if limk2_conf is not None else None,
            "rock2_top": round(rock2_conf, 4) if rock2_conf is not None else None,
            "limk2_positive_poses": limk2_pos,
            "rock2_positive_poses": rock2_pos,
            "source": comp["source"],
        })

    # Sort by LIMK2 score descending
    rows.sort(key=lambda x: x.get("limk2_top") or -999, reverse=True)

    # Determine ranking
    for i, row in enumerate(rows):
        row["limk2_rank"] = i + 1

    # Also rank by ROCK2
    rock2_sorted = sorted(rows, key=lambda x: x.get("rock2_top") or -999, reverse=True)
    for i, row in enumerate(rock2_sorted):
        row["rock2_rank"] = i + 1

    return {
        "comparison_table": rows,
        "total_compounds": len(rows),
        "ai_compounds": len(AI_CANDIDATES),
        "real_world_compounds": len(COMPOUNDS),
    }


async def main():
    start = time.time()
    logger.info("=" * 70)
    logger.info("Real-World LIMK Inhibitor Benchmarking")
    logger.info("Compounds: LX-7101, MDI-114215, BMS-5")
    logger.info("Targets: LIMK2 (P53671), ROCK2 (O75116)")
    logger.info(f"Poses per docking: {NUM_POSES}")
    logger.info("=" * 70)

    # Verify structure files exist
    for pdb in [LIMK2_PDB, ROCK2_PDB]:
        if not pdb.exists():
            raise FileNotFoundError(f"PDB file not found: {pdb}")

    # Phase 1: Dock against LIMK2
    logger.info("\n" + "=" * 50)
    logger.info("PHASE 1: Docking against LIMK2")
    logger.info("=" * 50)
    limk2_results = await dock_panel("LIMK2", LIMK2_PDB)

    await asyncio.sleep(RATE_LIMIT_DELAY)

    # Phase 2: Dock against ROCK2
    logger.info("\n" + "=" * 50)
    logger.info("PHASE 2: Docking against ROCK2")
    logger.info("=" * 50)
    rock2_results = await dock_panel("ROCK2", ROCK2_PDB)

    # Phase 3: Build comparison
    logger.info("\n" + "=" * 50)
    logger.info("PHASE 3: Building comparison table")
    logger.info("=" * 50)
    comparison = build_comparison_table(limk2_results, rock2_results)

    elapsed = time.time() - start

    # Assemble output
    output = {
        "campaign": "Real-World LIMK Inhibitor Benchmarking",
        "date": "2026-03-25",
        "rationale": (
            "Dock 3 real-world LIMK inhibitors (LX-7101 Phase 1, MDI-114215 J Med Chem, "
            "BMS-5 known dual) against LIMK2 and ROCK2 to benchmark our AI-designed "
            "candidates ((S,S)-H-1152, genmol_119)."
        ),
        "diffdock_version": "v2.2 (NVIDIA NIM)",
        "num_poses_per_docking": NUM_POSES,
        "total_dockings": len(COMPOUNDS) * 2,
        "elapsed_seconds": round(elapsed, 1),
        "compounds": COMPOUNDS,
        "limk2_results": limk2_results,
        "rock2_results": rock2_results,
        "comparison": comparison,
    }

    # Save
    OUTPUT_FILE.write_text(json.dumps(output, indent=2))
    logger.info(f"\nResults saved to: {OUTPUT_FILE}")

    # Print summary table
    logger.info("\n" + "=" * 70)
    logger.info("BENCHMARKING SUMMARY")
    logger.info("=" * 70)
    logger.info(f"{'Compound':<20} {'Type':<15} {'LIMK2 top':>12} {'ROCK2 top':>12} {'LIMK2 rank':>12} {'ROCK2 rank':>12}")
    logger.info("-" * 83)

    for row in comparison["comparison_table"]:
        limk2 = f"{row['limk2_top']:+.4f}" if row.get("limk2_top") is not None else "N/A"
        rock2 = f"{row['rock2_top']:+.4f}" if row.get("rock2_top") is not None else "N/A"
        logger.info(
            f"{row['compound']:<20} {row['type']:<15} {limk2:>12} {rock2:>12} "
            f"{row.get('limk2_rank', 'N/A'):>12} {row.get('rock2_rank', 'N/A'):>12}"
        )

    logger.info(f"\nCompleted in {elapsed:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
