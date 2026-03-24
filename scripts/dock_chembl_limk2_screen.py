#!/usr/bin/env python3
"""
ChEMBL LIMK2 Virtual Screen via DiffDock NIM v2.2
==================================================
Screen 20 pre-selected ChEMBL compounds against LIMK2 kinase domain.

Benchmark: H-1152 scored +0.90 against LIMK2 (14/20 positive poses).

Input:  data/docking/limk2_candidates_top20.json
Target: data/structures/LIMK2_P53671_kinase.pdb (residues 309-595)
Output: data/docking/chembl_limk2_screen_2026-03-24.json

Usage:
    python scripts/dock_chembl_limk2_screen.py
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# --- Configuration ---
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
NVIDIA_API_KEY_BACKUP = os.environ.get("NVIDIA_API_KEY_BACKUP", "")
if not NVIDIA_API_KEY:
    raise RuntimeError("NVIDIA_API_KEY environment variable is required")

DIFFDOCK_URL = "https://health.api.nvidia.com/v1/biology/mit/diffdock"
NUM_POSES = 20  # NEVER use 5 — always 20 for validation
RATE_LIMIT_DELAY = 2.0  # seconds between requests

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
STRUCTURES_DIR = DATA_DIR / "structures"
DOCKING_DIR = DATA_DIR / "docking"

# Input files
CANDIDATES_JSON = DOCKING_DIR / "limk2_candidates_top20.json"
LIMK2_PDB = STRUCTURES_DIR / "LIMK2_P53671_kinase.pdb"

# Output
OUTPUT_FILE = DOCKING_DIR / "chembl_limk2_screen_2026-03-24.json"

# Benchmark
H1152_BENCHMARK = 0.90  # H-1152 top confidence against LIMK2


def smiles_to_sdf(smiles, name=""):
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


def load_candidates():
    """Load candidates from the JSON file."""
    with open(CANDIDATES_JSON) as f:
        data = json.load(f)
    candidates = data["candidates"]
    logger.info(f"Loaded {len(candidates)} candidates from {CANDIDATES_JSON.name}")
    return candidates


def load_protein():
    """Load LIMK2 kinase domain PDB — ATOM lines only."""
    content = LIMK2_PDB.read_text()
    atom_lines = [l for l in content.split('\n') if l.startswith('ATOM')]
    logger.info(f"Loaded LIMK2 PDB: {len(atom_lines)} ATOM lines")
    return '\n'.join(atom_lines)


async def dock_compound(protein_pdb, smiles, name, api_key):
    """Dock a single compound against LIMK2 using DiffDock NIM."""
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

    payload_size = len(json.dumps(payload))
    logger.info(f"  Payload size: {payload_size // 1024}KB")

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(DIFFDOCK_URL, json=payload, headers=headers)

        if resp.status_code == 400:
            logger.error(f"  400 Bad Request — response: {resp.text[:500]}")
            resp.raise_for_status()

        if resp.status_code in (403, 429):
            logger.warning(f"Rate limited ({resp.status_code}), switching to backup key...")
            headers["Authorization"] = f"Bearer {NVIDIA_API_KEY_BACKUP}"
            await asyncio.sleep(5)
            resp = await client.post(DIFFDOCK_URL, json=payload, headers=headers)

        resp.raise_for_status()
        result = resp.json()

    # Parse confidences from DiffDock v2.2 response
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


async def run_screen():
    """Run the full ChEMBL LIMK2 virtual screen."""
    candidates = load_candidates()
    protein_pdb = load_protein()

    logger.info("=" * 70)
    logger.info("ChEMBL LIMK2 Virtual Screen (2026-03-24)")
    logger.info(f"Compounds: {len(candidates)}")
    logger.info(f"Target: LIMK2 kinase domain (residues 309-595)")
    logger.info(f"Poses per docking: {NUM_POSES}")
    logger.info(f"Benchmark: H-1152 = +{H1152_BENCHMARK:.2f}")
    logger.info(f"SDF conversion: RDKit (required for DiffDock v2.2 NIM)")
    logger.info("=" * 70)

    # Pre-validate all SMILES
    logger.info("\nPre-converting SMILES to SDF via RDKit...")
    for c in candidates:
        try:
            sdf = smiles_to_sdf(c["smiles"], name=c["chembl_id"])
            logger.info(f"  {c['chembl_id']} (rank {c['rank']}): OK ({len(sdf)} chars)")
        except Exception as e:
            logger.error(f"  {c['chembl_id']}: FAILED ({e})")
            return

    # Dock each compound
    results = []
    api_key = NVIDIA_API_KEY
    total = len(candidates)

    for i, candidate in enumerate(candidates, 1):
        chembl_id = candidate["chembl_id"]
        rank = candidate["rank"]
        mw = candidate["mw"]

        logger.info(f"\n[{i}/{total}] Docking {chembl_id} (rank {rank}, MW={mw}) vs LIMK2...")

        # MW filter
        if mw < 150:
            logger.warning(f"  SKIP: MW {mw} < 150")
            results.append({
                **candidate,
                "target": "LIMK2",
                "skipped": True,
                "reason": f"MW {mw} < 150",
            })
            continue

        try:
            dock_result = await dock_compound(
                protein_pdb, candidate["smiles"], chembl_id, api_key
            )

            entry = {
                **candidate,
                "target": "LIMK2",
                **dock_result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            results.append(entry)

            conf = dock_result.get("top_confidence")
            if conf is not None:
                label = "BINDING" if conf > 0 else "no binding"
                beats_h1152 = " ** BEATS H-1152 **" if conf > H1152_BENCHMARK else ""
                logger.info(f"  -> top_confidence: {conf:+.4f} ({label}){beats_h1152}")
                logger.info(f"  -> positive poses: {dock_result['positive_poses']}/{dock_result['num_poses']}")
                logger.info(f"  -> mean confidence: {dock_result['mean_confidence']:.4f}")
            else:
                logger.warning(f"  -> No confidence score returned")

        except Exception as e:
            logger.error(f"  -> FAILED: {e}")
            results.append({
                **candidate,
                "target": "LIMK2",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        # Rate limiting
        if i < total:
            logger.info(f"  (rate limit delay: {RATE_LIMIT_DELAY}s)")
            await asyncio.sleep(RATE_LIMIT_DELAY)

    # Save results
    DOCKING_DIR.mkdir(parents=True, exist_ok=True)

    output = {
        "campaign": "ChEMBL LIMK2 virtual screen",
        "date": "2026-03-24",
        "diffdock_version": "v2.2 (NVIDIA NIM)",
        "num_poses": NUM_POSES,
        "target": {
            "symbol": "LIMK2",
            "uniprot": "P53671",
            "domain": "kinase (residues 309-595)",
            "pdb_file": "LIMK2_P53671_kinase.pdb",
        },
        "benchmark": {
            "compound": "H-1152",
            "top_confidence": H1152_BENCHMARK,
            "note": "From limk2_rock2_campaign_2026-03-24. 14/20 positive poses.",
        },
        "num_candidates": len(candidates),
        "results": results,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    logger.info(f"\nResults saved to {OUTPUT_FILE}")

    # Print summary
    print_summary(results)

    return results


def print_summary(results):
    """Print ranked summary with benchmark comparison."""
    successful = [r for r in results if r.get("top_confidence") is not None]
    errors = [r for r in results if r.get("error")]
    skipped = [r for r in results if r.get("skipped")]

    logger.info("\n" + "=" * 70)
    logger.info("SCREEN SUMMARY — ChEMBL LIMK2 Virtual Screen")
    logger.info("=" * 70)
    logger.info(f"Total: {len(results)} | Successful: {len(successful)} | Errors: {len(errors)} | Skipped: {len(skipped)}")
    logger.info(f"Benchmark: H-1152 = +{H1152_BENCHMARK:.2f} (14/20 positive poses)")

    if successful:
        ranked = sorted(successful, key=lambda x: x["top_confidence"], reverse=True)
        positive = [r for r in ranked if r["top_confidence"] > 0]
        beats_benchmark = [r for r in ranked if r["top_confidence"] > H1152_BENCHMARK]

        logger.info(f"\nPositive binders: {len(positive)}/{len(successful)}")
        logger.info(f"Beat H-1152 benchmark (+{H1152_BENCHMARK:.2f}): {len(beats_benchmark)}/{len(successful)}")

        logger.info("\n--- Full Ranking (by top confidence) ---")
        for i, r in enumerate(ranked, 1):
            binding = "BIND" if r["top_confidence"] > 0 else "----"
            flag = " ** BEATS H-1152 **" if r["top_confidence"] > H1152_BENCHMARK else ""
            logger.info(
                f"  {i:2d}. [{binding}] {r['chembl_id']:15s} "
                f"(rank {r['rank']:2d}, MW={r['mw']:.0f}, pChEMBL={r['pchembl']}) "
                f"conf={r['top_confidence']:+.4f} "
                f"(pos={r['positive_poses']}/{r['num_poses']}, "
                f"mean={r['mean_confidence']:.4f}){flag}"
            )

        # Top 5
        logger.info("\n--- TOP 5 BINDERS ---")
        for i, r in enumerate(ranked[:5], 1):
            logger.info(
                f"  {i}. {r['chembl_id']} — {r.get('original_target', 'N/A')}"
            )
            logger.info(
                f"     conf={r['top_confidence']:+.4f}, "
                f"pos_poses={r['positive_poses']}/{r['num_poses']}, "
                f"MW={r['mw']:.0f}, pChEMBL={r['pchembl']}, logP={r['logp']}"
            )
            logger.info(f"     {r.get('rationale', '')}")

        # Scaffold analysis
        logger.info("\n--- SCAFFOLD ANALYSIS ---")
        scaffolds = {}
        for r in ranked:
            rat = r.get("rationale", "").lower()
            if "diaminopyrimidine" in rat:
                scaffold = "Diaminopyrimidines"
            elif "quinazoline" in rat or "anilinoquinazoline" in rat:
                scaffold = "Anilinoquinazolines"
            elif "xanthine" in rat or "pde" in rat:
                scaffold = "Xanthine/PDE"
            elif "quinoline" in rat:
                scaffold = "Quinolines"
            elif "purine" in rat:
                scaffold = "Purines"
            elif "folate" in rat or "pteridine" in rat or "aminopteridine" in rat:
                scaffold = "Folate analogs"
            elif "pyrazolopyridine" in rat:
                scaffold = "Pyrazolopyridines"
            else:
                scaffold = "Other"
            scaffolds.setdefault(scaffold, []).append(r)

        for scaffold, members in sorted(scaffolds.items(), key=lambda x: max(m["top_confidence"] for m in x[1]), reverse=True):
            confs = [m["top_confidence"] for m in members]
            best = max(confs)
            avg = sum(confs) / len(confs)
            logger.info(f"  {scaffold} ({len(members)} compounds): best={best:+.4f}, avg={avg:+.4f}")

    if errors:
        logger.info("\n--- ERRORS ---")
        for r in errors:
            logger.info(f"  {r['chembl_id']}: {r['error']}")


if __name__ == "__main__":
    asyncio.run(run_screen())
