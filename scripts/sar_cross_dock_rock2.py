#!/usr/bin/env python3
"""
SAR Cross-Dock: Top 10 LIMK2 SAR Analogs Against ROCK2
=======================================================
Date: 2026-03-24
Target: ROCK2 kinase domain (O75116)
Source: data/docking/genmol_119_docking_2026-03-24.json (SAR campaign)

Key Question: Does the COOH analog (idx=13, +0.978 LIMK2) also bind ROCK2?
If yes with balanced profile → better dual-target candidate than genmol_059.

Usage:
    export NVIDIA_API_KEY="nvapi-..."
    python scripts/sar_cross_dock_rock2.py
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# --- Configuration ---
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
if not NVIDIA_API_KEY:
    raise RuntimeError("NVIDIA_API_KEY environment variable is required")

DIFFDOCK_URL = "https://health.api.nvidia.com/v1/biology/mit/diffdock"
NUM_POSES = 20
RATE_LIMIT_DELAY = 2.0
RETRY_DELAY = 60

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
STRUCTURES_DIR = DATA_DIR / "structures"
DOCKING_DIR = DATA_DIR / "docking"

PDB_FILE = STRUCTURES_DIR / "ROCK2_O75116_kinase.pdb"
SAR_FILE = DOCKING_DIR / "genmol_119_docking_2026-03-24.json"
OUTPUT_FILE = DOCKING_DIR / "sar_analogs_cross_dock_rock2_2026-03-24.json"

# Previous cross-dock benchmarks
BENCHMARKS = {
    "genmol_119_ROCK2": 0.509,   # from cross_dock_rock2_2026-03-24.json
    "genmol_119_LIMK2": 1.058,   # parent compound
    "genmol_059_ROCK2": 0.466,   # from cross-dock (COOH variant, #2 LIMK2)
    "H1152_ROCK2": 0.90,         # reference ROCK inhibitor
}


def load_top_analogs(sar_file: Path, n: int = 10) -> list:
    """Load top N SAR analogs from the LIMK2 campaign by docking score."""
    with open(sar_file) as f:
        data = json.load(f)

    results = [r for r in data["results"]
               if r.get("top_confidence") is not None]
    results.sort(key=lambda x: x["top_confidence"], reverse=True)

    analogs = []
    for i, r in enumerate(results[:n]):
        has_cooh = "C(=O)O" in r["smiles"] or "C(O)=O" in r["smiles"]
        analogs.append({
            "name": f"sar_analog_{r['index']:03d}",
            "sar_index": r["index"],
            "smiles": r["smiles"],
            "mw": r["mw"],
            "limk2_score": r["top_confidence"],
            "similarity_to_parent": r.get("similarity_to_parent", 0),
            "has_cooh": has_cooh,
            "sar_features": r.get("sar_features", {}),
            "note": f"SAR rank #{i+1} vs LIMK2" + (" [COOH analog]" if has_cooh else ""),
        })
    return analogs


def smiles_to_sdf(smiles: str, name: str = "") -> str:
    """Convert SMILES to SDF format using RDKit."""
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
    """Load PDB and return ATOM-only lines."""
    text = pdb_path.read_text()
    atom_lines = [l for l in text.split("\n") if l.startswith("ATOM")]
    logger.info(f"Loaded ROCK2 PDB: {len(atom_lines)} ATOM lines from {pdb_path.name}")
    return "\n".join(atom_lines)


async def dock_single(
    protein_pdb: str,
    smiles: str,
    name: str,
    api_key: str,
) -> dict:
    """Dock a single molecule against ROCK2 using DiffDock NIM."""
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

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(DIFFDOCK_URL, json=payload, headers=headers)

        if resp.status_code == 400:
            logger.error(f"  400 Bad Request: {resp.text[:300]}")
            resp.raise_for_status()

        if resp.status_code in (403, 429):
            logger.warning(f"  Rate limited ({resp.status_code}), waiting {RETRY_DELAY}s...")
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


async def run_cross_dock():
    """Dock top 10 SAR analogs against ROCK2."""
    analogs = load_top_analogs(SAR_FILE, n=10)

    logger.info("=" * 70)
    logger.info("SAR CROSS-DOCK: Top 10 LIMK2 SAR Analogs vs ROCK2")
    logger.info(f"Target: ROCK2 kinase domain (O75116)")
    logger.info(f"Source: {SAR_FILE.name}")
    logger.info(f"Compounds: {len(analogs)}")
    logger.info(f"Poses per docking: {NUM_POSES}")
    logger.info(f"Key question: COOH analog (+0.978 LIMK2) — does it bind ROCK2?")
    logger.info("=" * 70)

    for i, a in enumerate(analogs):
        logger.info(f"  {i+1}. {a['name']} LIMK2={a['limk2_score']:+.4f} MW={a['mw']} {a['note']}")

    protein_pdb = load_protein_pdb(PDB_FILE)

    # Pre-validate SDF
    logger.info("\nPre-validating SMILES -> SDF conversion...")
    for comp in analogs:
        try:
            smiles_to_sdf(comp["smiles"], name=comp["name"])
            logger.info(f"  {comp['name']}: OK")
        except Exception as e:
            logger.error(f"  {comp['name']}: FAILED - {e}")
            comp["sdf_failed"] = True

    analogs = [a for a in analogs if not a.get("sdf_failed")]

    results = []
    start_time = time.time()

    for i, comp in enumerate(analogs):
        logger.info(f"\n[{i+1}/{len(analogs)}] Docking {comp['name']} (idx={comp['sar_index']}) against ROCK2")
        logger.info(f"  SMILES: {comp['smiles']}")
        logger.info(f"  MW: {comp['mw']}, LIMK2 score: {comp['limk2_score']:+.4f}")

        try:
            dock_result = await dock_single(
                protein_pdb, comp["smiles"], comp["name"], NVIDIA_API_KEY
            )
            entry = {
                **comp,
                "target": "ROCK2",
                "rock2_top_confidence": dock_result["top_confidence"],
                "rock2_mean_confidence": dock_result["mean_confidence"],
                "rock2_positive_poses": dock_result["positive_poses"],
                "rock2_num_poses": dock_result["num_poses"],
                "rock2_all_confidences": dock_result["all_confidences"],
                "raw_response_keys": dock_result["raw_response_keys"],
            }
            results.append(entry)

            conf = dock_result.get("top_confidence")
            if conf is not None:
                binding = "BINDING" if conf > 0 else "no binding"
                dual = ""
                if conf > 0 and comp["limk2_score"] > 0:
                    ratio = min(conf, comp["limk2_score"]) / max(conf, comp["limk2_score"])
                    dual = f" *** DUAL BINDER (balance={ratio:.2f}) ***"
                logger.info(
                    f"  -> ROCK2 conf={conf:+.4f} ({binding}), "
                    f"pos_poses={dock_result['positive_poses']}/{dock_result['num_poses']}"
                    f"{dual}"
                )
            else:
                logger.warning(f"  -> No confidence score returned")

        except Exception as e:
            logger.error(f"  -> FAILED: {e}")
            results.append({
                **comp,
                "target": "ROCK2",
                "error": str(e),
            })

        if i < len(analogs) - 1:
            await asyncio.sleep(RATE_LIMIT_DELAY)

    elapsed = time.time() - start_time

    # Save results
    DOCKING_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "campaign": "SAR analogs cross-dock vs ROCK2",
        "date": datetime.now(timezone.utc).isoformat(),
        "target": "ROCK2 kinase domain (O75116)",
        "source": "genmol_119_docking_2026-03-24.json (top 10 by LIMK2 score)",
        "diffdock_version": "v2.2 (NVIDIA NIM)",
        "num_poses": NUM_POSES,
        "total_compounds": len(analogs),
        "elapsed_seconds": round(elapsed, 1),
        "benchmarks": BENCHMARKS,
        "key_question": "COOH analog (+0.978 LIMK2) — does it also bind ROCK2? Dual-target potential?",
        "results": results,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    logger.info(f"\nResults saved to {OUTPUT_FILE}")

    print_summary(results, elapsed)
    return results


def print_summary(results: list, elapsed: float):
    """Print ranked results with dual-target assessment."""
    logger.info("\n" + "=" * 70)
    logger.info("SAR CROSS-DOCK SUMMARY: Top 10 LIMK2 Analogs vs ROCK2")
    logger.info("=" * 70)
    logger.info(f"Elapsed: {elapsed:.0f}s ({elapsed/60:.1f} min)")

    successful = [r for r in results if r.get("rock2_top_confidence") is not None]

    logger.info(f"\n{'Rank':<5} {'Name':<18} {'LIMK2':>8} {'ROCK2':>8} {'R2pos':>6} {'Dual':>6} {'COOH':>5} {'MW':>7}")
    logger.info("-" * 70)

    ranked = sorted(successful, key=lambda x: x["rock2_top_confidence"], reverse=True)
    for i, r in enumerate(ranked):
        limk2 = r.get("limk2_score", 0)
        rock2 = r.get("rock2_top_confidence", 0)
        pos = r.get("rock2_positive_poses", 0)
        total = r.get("rock2_num_poses", 0)
        dual = "YES" if limk2 > 0 and rock2 > 0 else "no"
        cooh = "YES" if r.get("has_cooh") else ""
        mw = r.get("mw", 0)
        logger.info(
            f"  {i+1:<3} {r['name']:<18} {limk2:>+8.4f} {rock2:>+8.4f} {pos:>3}/{total:<3} {dual:>5} {cooh:>5} {mw:>7.1f}"
        )

    # Dual binder analysis
    dual_binders = [r for r in successful
                    if r.get("rock2_top_confidence", 0) > 0 and r.get("limk2_score", 0) > 0]
    logger.info(f"\nDual ROCK2/LIMK2 binders: {len(dual_binders)}/{len(successful)}")

    if dual_binders:
        logger.info("\n--- DUAL BINDER PROFILES ---")
        for r in sorted(dual_binders, key=lambda x: x["limk2_score"] + x["rock2_top_confidence"], reverse=True):
            limk2 = r["limk2_score"]
            rock2 = r["rock2_top_confidence"]
            combined = limk2 + rock2
            ratio = min(limk2, rock2) / max(limk2, rock2)
            logger.info(f"  {r['name']}: LIMK2={limk2:+.4f} ROCK2={rock2:+.4f} combined={combined:+.4f} balance={ratio:.2f}")
            logger.info(f"    SMILES: {r['smiles']}")
            if r.get("has_cooh"):
                logger.info(f"    ** COOH analog — key compound **")

    # COOH analog specific result
    cooh_results = [r for r in successful if r.get("has_cooh")]
    if cooh_results:
        logger.info("\n--- COOH ANALOG ASSESSMENT ---")
        for r in cooh_results:
            limk2 = r["limk2_score"]
            rock2 = r["rock2_top_confidence"]
            logger.info(f"  {r['name']} (idx={r['sar_index']})")
            logger.info(f"    LIMK2: {limk2:+.4f}")
            logger.info(f"    ROCK2: {rock2:+.4f}")
            if rock2 > 0:
                # Compare to genmol_059 (previous best COOH dual binder)
                g059_rock2 = BENCHMARKS.get("genmol_059_ROCK2", 0)
                if rock2 > g059_rock2:
                    logger.info(f"    BETTER than genmol_059 ROCK2 ({g059_rock2:+.3f}) — new lead!")
                else:
                    logger.info(f"    vs genmol_059 ROCK2 ({g059_rock2:+.3f})")
                combined = limk2 + rock2
                logger.info(f"    Combined score: {combined:+.4f}")
                logger.info(f"    VERDICT: DUAL-TARGET CANDIDATE for SMA triple therapy")
            else:
                logger.info(f"    VERDICT: LIMK2-selective only, not a ROCK2 binder")

    # Best overall compound
    if ranked:
        best = max(successful, key=lambda x: x["limk2_score"] + (x.get("rock2_top_confidence", 0) or 0))
        logger.info(f"\nBEST OVERALL (combined LIMK2+ROCK2): {best['name']}")
        logger.info(f"  LIMK2={best['limk2_score']:+.4f} ROCK2={best.get('rock2_top_confidence',0):+.4f}")
        logger.info(f"  Combined={best['limk2_score'] + (best.get('rock2_top_confidence',0) or 0):+.4f}")


if __name__ == "__main__":
    asyncio.run(run_cross_dock())
