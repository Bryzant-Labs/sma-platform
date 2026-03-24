#!/usr/bin/env python3
"""
GenMol De Novo Molecule Generation: LIMK2 + ROCK2 Targets
==========================================================
Campaign date: 2026-03-24
Rationale: LIMK2 upregulated 2.8x in SMA motor neurons,
           ROCK1/2 both UP — Fasudil validated preclinically.
           ROCK-LIMK2-CFL2 = strongest therapeutic axis.

Generates novel drug-like molecules using NVIDIA GenMol NIM
from seed compounds for each target, then filters for:
  - Drug-likeness (Lipinski Rule of 5)
  - BBB permeability (MW 200-500, LogP 1-4)
  - QED score ranking

Seeds:
  LIMK2: H-1152 (best hit), BMS-5 (LIMK inhibitor)
  ROCK2: Fasudil (validated), Y-27632 (ROCK inhibitor)

Usage:
    python scripts/genmol_limk2_rock2.py
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

GENMOL_URL = "https://health.api.nvidia.com/v1/biology/nvidia/genmol/generate"
RATE_LIMIT_DELAY = 2.0  # seconds between requests

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCKING_DIR = DATA_DIR / "docking"

# Ensure output directory exists
DOCKING_DIR.mkdir(parents=True, exist_ok=True)

# --- Seed Compounds ---
LIMK2_SEEDS = {
    "H-1152": {
        "smiles": "CC(C)C(=O)N1CCC(C(F)(F)F)CC1c1ccncc1",
        "description": "ROCK/LIMK inhibitor -- best hit from DiffDock campaign",
        "source": "literature",
    },
    "BMS-5": {
        "smiles": "CC(=O)Nc1ccc(-c2nc3cc(NS(=O)(=O)c4ccc(F)cc4)ccc3[nH]2)cc1",
        "description": "Selective LIMK inhibitor (BMS compound)",
        "source": "literature",
    },
}

ROCK2_SEEDS = {
    "Fasudil": {
        "smiles": "O=C1CCN(Cc2cccc3cnccc23)CC1",
        "description": "Approved ROCK inhibitor -- validated preclinically in SMA",
        "source": "approved_drug",
    },
    "Y-27632": {
        "smiles": "CC(N)C1CCC(C(=O)Nc2ccncc2)CC1",
        "description": "Selective ROCK inhibitor -- research tool compound",
        "source": "literature",
    },
}

# --- Drug-likeness filters ---
MW_MIN, MW_MAX = 200, 500
LOGP_MIN, LOGP_MAX = 1.0, 4.0
HBA_MAX = 10   # Lipinski: H-bond acceptors
HBD_MAX = 5    # Lipinski: H-bond donors

# Try to import RDKit for validation
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, QED, rdMolDescriptors
    HAS_RDKIT = True
    logger.info("RDKit available -- will validate SMILES and compute properties")
except ImportError:
    HAS_RDKIT = False
    logger.warning("RDKit not available -- SMILES validation and property filtering disabled")


def compute_properties(smiles):
    """Compute molecular properties using RDKit. Returns None if invalid."""
    if not HAS_RDKIT:
        return {"smiles": smiles, "valid": True, "rdkit_available": False}

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    hba = rdMolDescriptors.CalcNumHBA(mol)
    hbd = rdMolDescriptors.CalcNumHBD(mol)
    tpsa = Descriptors.TPSA(mol)
    rotatable = rdMolDescriptors.CalcNumRotatableBonds(mol)
    rings = rdMolDescriptors.CalcNumRings(mol)
    qed_score = QED.qed(mol)
    canonical = Chem.MolToSmiles(mol)

    return {
        "smiles": canonical,
        "valid": True,
        "mw": round(mw, 2),
        "logp": round(logp, 2),
        "hba": hba,
        "hbd": hbd,
        "tpsa": round(tpsa, 2),
        "rotatable_bonds": rotatable,
        "rings": rings,
        "qed": round(qed_score, 4),
    }


def passes_filters(props):
    """Check if molecule passes drug-likeness and BBB filters."""
    if not props or not props.get("valid"):
        return False
    if not HAS_RDKIT or not props.get("mw"):
        return True  # Can't filter without RDKit -- keep all

    mw = props["mw"]
    logp = props["logp"]
    hba = props["hba"]
    hbd = props["hbd"]

    if not (MW_MIN <= mw <= MW_MAX):
        return False
    if not (LOGP_MIN <= logp <= LOGP_MAX):
        return False
    if hba > HBA_MAX:
        return False
    if hbd > HBD_MAX:
        return False
    return True


async def call_genmol(
    seed_smiles,
    num_molecules=100,
    temperature=1.5,
    noise=0.7,
    scoring="QED",
    api_key=None,
):
    """Call NVIDIA GenMol NIM API to generate molecules from a seed SMILES."""
    import httpx

    key = api_key or NVIDIA_API_KEY
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "smiles": seed_smiles,
        "num_molecules": str(num_molecules),
        "temperature": str(temperature),
        "noise": str(noise),
        "step_size": "1",
        "scoring": scoring,
        "unique": True,
    }

    async with httpx.AsyncClient(timeout=180) as client:
        logger.info(f"GenMol: Requesting {num_molecules} molecules from seed {seed_smiles[:40]}...")
        try:
            resp = await client.post(GENMOL_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403) and key != NVIDIA_API_KEY_BACKUP:
                logger.warning("Primary API key failed, trying backup key...")
                headers["Authorization"] = f"Bearer {NVIDIA_API_KEY_BACKUP}"
                resp = await client.post(GENMOL_URL, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
            else:
                logger.error(f"GenMol API error: {e.response.status_code} -- {e.response.text[:500]}")
                raise

    # Parse response -- GenMol returns various formats
    molecules = []
    if isinstance(data, dict):
        if "molecules" in data:
            for mol in data["molecules"]:
                if isinstance(mol, dict):
                    molecules.append(mol)
                elif isinstance(mol, str):
                    molecules.append({"smiles": mol})
        elif "smiles" in data and isinstance(data["smiles"], list):
            scores = data.get("scores", [None] * len(data["smiles"]))
            for s, sc in zip(data["smiles"], scores):
                entry = {"smiles": s}
                if sc is not None:
                    entry["score"] = sc
                molecules.append(entry)
        elif "output" in data:
            out = data["output"]
            if isinstance(out, list):
                for item in out:
                    if isinstance(item, dict) and "smiles" in item:
                        molecules.append(item)
                    elif isinstance(item, str):
                        molecules.append({"smiles": item})
        else:
            logger.warning(f"Unexpected GenMol response format. Keys: {list(data.keys())}")
            raw = json.dumps(data)
            logger.info(f"Raw response (first 500 chars): {raw[:500]}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "smiles" in item:
                molecules.append(item)
            elif isinstance(item, str):
                molecules.append({"smiles": item})

    logger.info(f"GenMol: Received {len(molecules)} molecules")
    return molecules


async def generate_for_target(target_name, seeds, num_per_seed=100):
    """Generate and filter molecules for a target from multiple seeds."""
    all_raw = []
    all_valid = []
    all_filtered = []
    seen_smiles = set()

    for seed_name, seed_info in seeds.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Target: {target_name} | Seed: {seed_name}")
        logger.info(f"SMILES: {seed_info['smiles']}")
        logger.info(f"{'='*60}")

        try:
            molecules = await call_genmol(
                seed_smiles=seed_info["smiles"],
                num_molecules=num_per_seed,
                temperature=1.5,
                noise=0.7,
                scoring="QED",
            )
        except Exception as e:
            logger.error(f"GenMol failed for {seed_name}: {e}")
            try:
                logger.info("Retrying with 50 molecules...")
                molecules = await call_genmol(
                    seed_smiles=seed_info["smiles"],
                    num_molecules=50,
                    temperature=1.2,
                    noise=0.5,
                    scoring="QED",
                )
            except Exception as e2:
                logger.error(f"GenMol retry also failed: {e2}")
                molecules = []

        for mol_data in molecules:
            smiles = mol_data.get("smiles", "")
            if not smiles:
                continue

            all_raw.append({
                "smiles": smiles,
                "seed": seed_name,
                "seed_smiles": seed_info["smiles"],
                "api_score": mol_data.get("score"),
            })

            props = compute_properties(smiles)
            if props is None:
                continue

            canonical = props.get("smiles", smiles)
            if canonical in seen_smiles:
                continue
            seen_smiles.add(canonical)

            entry = {
                **props,
                "seed": seed_name,
                "seed_smiles": seed_info["smiles"],
                "api_score": mol_data.get("score"),
            }
            all_valid.append(entry)

            if passes_filters(props):
                all_filtered.append(entry)

        logger.info(f"  Raw: {len(molecules)}, Valid total: {len(all_valid)}, Filtered total: {len(all_filtered)}")
        await asyncio.sleep(RATE_LIMIT_DELAY)

    # Sort by QED
    if HAS_RDKIT:
        all_filtered.sort(key=lambda x: x.get("qed", 0), reverse=True)
        all_valid.sort(key=lambda x: x.get("qed", 0), reverse=True)

    return {
        "target": target_name,
        "date": datetime.now(timezone.utc).isoformat(),
        "seeds": {name: info for name, info in seeds.items()},
        "filters": {
            "mw_range": [MW_MIN, MW_MAX],
            "logp_range": [LOGP_MIN, LOGP_MAX],
            "hba_max": HBA_MAX,
            "hbd_max": HBD_MAX,
            "rationale": "BBB-permeable + Lipinski drug-like",
        },
        "stats": {
            "total_raw": len(all_raw),
            "total_valid_unique": len(all_valid),
            "total_drug_like": len(all_filtered),
            "rdkit_available": HAS_RDKIT,
        },
        "top_candidates": all_filtered[:20],
        "all_drug_like": all_filtered,
        "all_valid": all_valid,
    }


def print_summary(results):
    """Print a human-readable summary of generation results."""
    target = results["target"]
    stats = results["stats"]
    top = results["top_candidates"]

    print(f"\n{'='*70}")
    print(f"  GenMol Results: {target}")
    print(f"{'='*70}")
    print(f"  Total raw generated:    {stats['total_raw']}")
    print(f"  Valid unique (RDKit):    {stats['total_valid_unique']}")
    print(f"  Drug-like (filtered):    {stats['total_drug_like']}")
    print(f"  RDKit available:         {stats['rdkit_available']}")
    print(f"  Filters: MW {MW_MIN}-{MW_MAX}, LogP {LOGP_MIN}-{LOGP_MAX}, Lipinski")
    print()

    if top:
        print(f"  Top {min(10, len(top))} candidates by QED:")
        print(f"  {'Rank':<5} {'QED':<7} {'MW':<8} {'LogP':<7} {'Seed':<12} {'SMILES'}")
        print(f"  {'-'*5} {'-'*7} {'-'*8} {'-'*7} {'-'*12} {'-'*40}")
        for i, mol in enumerate(top[:10], 1):
            qed = mol.get("qed", "?")
            mw = mol.get("mw", "?")
            logp = mol.get("logp", "?")
            seed = mol.get("seed", "?")
            smiles = mol.get("smiles", "?")
            if len(str(smiles)) > 50:
                smiles = str(smiles)[:47] + "..."
            print(f"  {i:<5} {qed:<7} {mw:<8} {logp:<7} {seed:<12} {smiles}")
    else:
        print("  No drug-like candidates found.")

    if HAS_RDKIT and results.get("all_drug_like"):
        ring_counts = set()
        for mol in results["all_drug_like"]:
            m = Chem.MolFromSmiles(mol["smiles"])
            if m:
                ri = m.GetRingInfo()
                ring_counts.add(ri.NumRings())
        print(f"\n  Scaffold diversity: {len(ring_counts)} distinct ring-count classes")
    print()


async def main():
    """Run GenMol generation for both LIMK2 and ROCK2 targets."""
    start = time.time()
    num_per_seed = 100

    print("\n" + "=" * 70)
    print("  NVIDIA GenMol NIM -- De Novo Molecule Generation")
    print("  Targets: LIMK2 + ROCK2 (SMA actin pathway)")
    print("  Date: 2026-03-24")
    print("=" * 70)

    logger.info("\n>>> Generating molecules for LIMK2 <<<")
    limk2_results = await generate_for_target("LIMK2", LIMK2_SEEDS, num_per_seed)

    logger.info("\n>>> Generating molecules for ROCK2 <<<")
    rock2_results = await generate_for_target("ROCK2", ROCK2_SEEDS, num_per_seed)

    # Save results
    limk2_path = DOCKING_DIR / "genmol_limk2_2026-03-24.json"
    rock2_path = DOCKING_DIR / "genmol_rock2_2026-03-24.json"

    with open(limk2_path, "w") as f:
        json.dump(limk2_results, f, indent=2)
    logger.info(f"Saved LIMK2 results to {limk2_path}")

    with open(rock2_path, "w") as f:
        json.dump(rock2_results, f, indent=2)
    logger.info(f"Saved ROCK2 results to {rock2_path}")

    print_summary(limk2_results)
    print_summary(rock2_results)

    total_raw = limk2_results["stats"]["total_raw"] + rock2_results["stats"]["total_raw"]
    total_valid = limk2_results["stats"]["total_valid_unique"] + rock2_results["stats"]["total_valid_unique"]
    total_dl = limk2_results["stats"]["total_drug_like"] + rock2_results["stats"]["total_drug_like"]

    elapsed = time.time() - start
    print(f"\n{'='*70}")
    print(f"  COMBINED SUMMARY")
    print(f"{'='*70}")
    print(f"  Total raw generated:     {total_raw}")
    print(f"  Total valid unique:      {total_valid}")
    print(f"  Total drug-like:         {total_dl}")
    print(f"  Time elapsed:            {elapsed:.1f}s")
    print(f"  Output files:")
    print(f"    {limk2_path}")
    print(f"    {rock2_path}")
    print(f"{'='*70}\n")

    return limk2_results, rock2_results


if __name__ == "__main__":
    results = asyncio.run(main())
