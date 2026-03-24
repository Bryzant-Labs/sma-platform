#!/usr/bin/env python3
"""
DiffDock Batch Docking: 136 GenMol LIMK2 Molecules
===================================================
Date: 2026-03-24
Target: LIMK2 kinase domain (P53671, residues 309-595)
Molecules: GenMol-generated drug-like compounds (BBB-permeable, Lipinski)
Benchmark: H-1152 scored +0.90 against LIMK2 (14/20 poses)

Converts SMILES to SDF via RDKit (DiffDock v2.2 NIM rejects SMILES format).
20 poses per docking, 2s rate limit between requests.

Usage:
    export NVIDIA_API_KEY="nvapi-..."
    python scripts/dock_genmol_limk2_batch.py
"""

import asyncio
import json
import logging
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# --- Configuration ---
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
NVIDIA_API_KEY_BACKUP = os.environ.get("NVIDIA_API_KEY_BACKUP", "")
if not NVIDIA_API_KEY:
    raise RuntimeError("NVIDIA_API_KEY environment variable is required")

DIFFDOCK_URL = "https://health.api.nvidia.com/v1/biology/mit/diffdock"
NUM_POSES = 20  # NEVER less than 20
RATE_LIMIT_DELAY = 2.0  # seconds between requests
RETRY_DELAY = 60  # seconds on 429

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
STRUCTURES_DIR = DATA_DIR / "structures"
DOCKING_DIR = DATA_DIR / "docking"

INPUT_FILE = DOCKING_DIR / "genmol_limk2_2026-03-24.json"
PDB_FILE = STRUCTURES_DIR / "LIMK2_P53671_kinase.pdb"
OUTPUT_FILE = DOCKING_DIR / "genmol_limk2_docking_2026-03-24.json"

# Benchmark
H1152_BENCHMARK = 0.90  # H-1152 top_confidence against LIMK2


def smiles_to_sdf(smiles: str, name: str = "") -> str:
    """Convert SMILES to SDF format using RDKit.

    DiffDock NIM v2.2 rejects ligand_file_type='smiles' — requires SDF.
    """
    from rdkit import Chem
    from rdkit.Chem import AllChem

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
    """Load PDB and return ATOM-only lines (DiffDock prefers this)."""
    text = pdb_path.read_text()
    atom_lines = [l for l in text.split("\n") if l.startswith("ATOM")]
    logger.info(f"Loaded LIMK2 PDB: {len(atom_lines)} ATOM lines from {pdb_path.name}")
    return "\n".join(atom_lines)


async def dock_single(
    protein_pdb: str,
    smiles: str,
    mol_index: int,
    api_key: str,
) -> dict:
    """Dock a single molecule against LIMK2 using DiffDock NIM."""
    import httpx

    ligand_sdf = smiles_to_sdf(smiles, name=f"genmol_{mol_index:03d}")

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

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(DIFFDOCK_URL, json=payload, headers=headers)

        if resp.status_code == 400:
            logger.error(f"  400 Bad Request: {resp.text[:300]}")
            resp.raise_for_status()

        if resp.status_code in (403, 429):
            logger.warning(f"  Rate limited ({resp.status_code}), waiting {RETRY_DELAY}s...")
            if NVIDIA_API_KEY_BACKUP:
                headers["Authorization"] = f"Bearer {NVIDIA_API_KEY_BACKUP}"
            await asyncio.sleep(RETRY_DELAY)
            resp = await client.post(DIFFDOCK_URL, json=payload, headers=headers)

        resp.raise_for_status()
        result = resp.json()

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
        "raw_response_keys": list(result.keys()),
    }


async def run_batch():
    """Dock all 136 GenMol molecules against LIMK2."""
    # Load input
    with open(INPUT_FILE) as f:
        data = json.load(f)

    molecules = data["all_drug_like"]
    logger.info("=" * 70)
    logger.info("DiffDock Batch: GenMol LIMK2 Molecules (2026-03-24)")
    logger.info(f"Molecules: {len(molecules)}")
    logger.info(f"Target: LIMK2 kinase domain (P53671, res 309-595)")
    logger.info(f"Poses per docking: {NUM_POSES}")
    logger.info(f"Rate limit: {RATE_LIMIT_DELAY}s between requests")
    logger.info(f"Estimated time: ~{len(molecules) * (RATE_LIMIT_DELAY + 3) / 60:.0f} min")
    logger.info(f"Benchmark: H-1152 = +{H1152_BENCHMARK:.2f}")
    logger.info("=" * 70)

    # Load protein
    protein_pdb = load_protein_pdb(PDB_FILE)

    # Pre-validate SDF conversion
    logger.info("\nPre-validating SMILES -> SDF conversion...")
    sdf_failures = []
    for i, mol in enumerate(molecules):
        try:
            smiles_to_sdf(mol["smiles"], name=f"genmol_{i:03d}")
        except Exception as e:
            sdf_failures.append((i, mol["smiles"], str(e)))
            logger.warning(f"  SDF fail [{i}]: {mol['smiles'][:50]}... ({e})")
    logger.info(f"  SDF validation: {len(molecules) - len(sdf_failures)}/{len(molecules)} OK, {len(sdf_failures)} failed")

    # Dock
    results = []
    api_key = NVIDIA_API_KEY
    total = len(molecules)
    start_time = time.time()

    for i, mol in enumerate(molecules):
        smiles = mol["smiles"]
        logger.info(f"\n[{i+1}/{total}] Docking genmol_{i:03d} (MW={mol['mw']:.1f}, QED={mol.get('qed', 0):.3f}, seed={mol.get('seed', '?')})")
        logger.info(f"  SMILES: {smiles[:60]}{'...' if len(smiles) > 60 else ''}")

        # Skip known SDF failures
        if any(idx == i for idx, _, _ in sdf_failures):
            logger.warning(f"  SKIP: SDF conversion failed")
            results.append({
                "index": i,
                "smiles": smiles,
                "seed": mol.get("seed"),
                "mw": mol.get("mw"),
                "qed": mol.get("qed"),
                "error": "SDF conversion failed",
                "skipped": True,
            })
            continue

        try:
            dock_result = await dock_single(protein_pdb, smiles, i, api_key)
            entry = {
                "index": i,
                "smiles": smiles,
                "seed": mol.get("seed"),
                "mw": mol.get("mw"),
                "logp": mol.get("logp"),
                "qed": mol.get("qed"),
                "tpsa": mol.get("tpsa"),
                "hbd": mol.get("hbd"),
                "hba": mol.get("hba"),
                "rings": mol.get("rings"),
                "rotatable_bonds": mol.get("rotatable_bonds"),
                **dock_result,
            }
            results.append(entry)

            conf = dock_result.get("top_confidence")
            if conf is not None:
                beats = " ** BEATS H-1152! **" if conf > H1152_BENCHMARK else ""
                label = "BINDING" if conf > 0 else "no binding"
                logger.info(
                    f"  -> conf={conf:+.4f} ({label}), "
                    f"pos_poses={dock_result['positive_poses']}/{dock_result['num_poses']}"
                    f"{beats}"
                )
            else:
                logger.warning(f"  -> No confidence score returned")

        except Exception as e:
            logger.error(f"  -> FAILED: {e}")
            results.append({
                "index": i,
                "smiles": smiles,
                "seed": mol.get("seed"),
                "mw": mol.get("mw"),
                "qed": mol.get("qed"),
                "error": str(e),
            })

        # Rate limit
        if i < total - 1:
            await asyncio.sleep(RATE_LIMIT_DELAY)

    elapsed = time.time() - start_time

    # Save results
    DOCKING_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "campaign": "GenMol LIMK2 batch docking",
        "date": "2026-03-24",
        "target": "LIMK2 kinase domain (P53671, res 309-595)",
        "diffdock_version": "v2.2 (NVIDIA NIM)",
        "num_poses": NUM_POSES,
        "total_molecules": len(molecules),
        "sdf_failures": len(sdf_failures),
        "elapsed_seconds": round(elapsed, 1),
        "benchmark": {
            "compound": "H-1152",
            "top_confidence": H1152_BENCHMARK,
            "positive_poses": 14,
            "num_poses": 20,
        },
        "seeds": data.get("seeds", {}),
        "filters": data.get("filters", {}),
        "results": results,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    logger.info(f"\nResults saved to {OUTPUT_FILE}")

    # Print summary
    print_summary(results, elapsed)

    return results


def print_summary(results: list, elapsed: float):
    """Print ranked summary with scaffold analysis."""
    successful = [r for r in results if r.get("top_confidence") is not None]
    positive = [r for r in successful if r["top_confidence"] > 0]
    beats_h1152 = [r for r in successful if r["top_confidence"] > H1152_BENCHMARK]
    errors = [r for r in results if r.get("error")]
    skipped = [r for r in results if r.get("skipped")]

    logger.info("\n" + "=" * 70)
    logger.info("BATCH DOCKING SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total molecules: {len(results)}")
    logger.info(f"Successful dockings: {len(successful)}")
    logger.info(f"Errors: {len(errors)}")
    logger.info(f"Skipped (SDF fail): {len(skipped)}")
    logger.info(f"Positive confidence (binding): {len(positive)}")
    logger.info(f"Beat H-1152 (+{H1152_BENCHMARK:.2f}): {len(beats_h1152)}")
    logger.info(f"Elapsed: {elapsed/60:.1f} min ({elapsed:.0f}s)")

    if successful:
        # Top 20 ranked by confidence
        ranked = sorted(successful, key=lambda x: x["top_confidence"], reverse=True)
        logger.info("\n--- TOP 20 MOLECULES (ranked by confidence) ---")
        for rank, r in enumerate(ranked[:20], 1):
            beat = " ** BEATS H-1152" if r["top_confidence"] > H1152_BENCHMARK else ""
            logger.info(
                f"  #{rank:2d}  genmol_{r['index']:03d}  "
                f"conf={r['top_confidence']:+.4f}  "
                f"pos={r['positive_poses']:2d}/{r['num_poses']}  "
                f"MW={r.get('mw', 0):.0f}  "
                f"QED={r.get('qed', 0):.3f}  "
                f"seed={r.get('seed', '?')}"
                f"{beat}"
            )
            logger.info(f"        SMILES: {r['smiles'][:70]}")

        # Scaffold analysis by seed
        logger.info("\n--- SCAFFOLD ANALYSIS (by seed compound) ---")
        seed_groups = {}
        for r in successful:
            seed = r.get("seed", "unknown")
            seed_groups.setdefault(seed, []).append(r)

        for seed, group in sorted(seed_groups.items()):
            confs = [r["top_confidence"] for r in group]
            pos_count = len([c for c in confs if c > 0])
            beat_count = len([c for c in confs if c > H1152_BENCHMARK])
            logger.info(
                f"  {seed:15s}: {len(group):3d} mols, "
                f"best={max(confs):+.4f}, "
                f"mean={sum(confs)/len(confs):+.4f}, "
                f"binding={pos_count}/{len(group)}, "
                f"beat_H1152={beat_count}"
            )

        # Statistics
        all_confs = [r["top_confidence"] for r in successful]
        logger.info("\n--- STATISTICS ---")
        logger.info(f"  Best confidence: {max(all_confs):+.4f}")
        logger.info(f"  Worst confidence: {min(all_confs):+.4f}")
        logger.info(f"  Mean confidence: {sum(all_confs)/len(all_confs):+.4f}")
        logger.info(f"  Median confidence: {sorted(all_confs)[len(all_confs)//2]:+.4f}")
        logger.info(f"  Binding rate: {len(positive)}/{len(successful)} ({100*len(positive)/len(successful):.0f}%)")
        logger.info(f"  Beat H-1152 rate: {len(beats_h1152)}/{len(successful)} ({100*len(beats_h1152)/len(successful):.0f}%)")

    if errors:
        logger.info(f"\n--- ERRORS ({len(errors)}) ---")
        for r in errors[:10]:
            logger.info(f"  genmol_{r.get('index', '?'):03d}: {r['error'][:80]}")
        if len(errors) > 10:
            logger.info(f"  ... and {len(errors)-10} more")


if __name__ == "__main__":
    asyncio.run(run_batch())
