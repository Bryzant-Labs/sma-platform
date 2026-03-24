#!/usr/bin/env python3
"""
SAR Campaign: genmol_119 Analogs vs LIMK2
==========================================
Date: 2026-03-24

genmol_119 (SMILES: CC(C)C(=O)N1CC[C@@H](C(F)(F)F)C[C@H]1c1ccncc1)
scored +1.058 against LIMK2 — our best hit.

This script:
1. Generates ~100 analogs via NVIDIA MolMIM with varied similarity (0.3-0.7)
2. Filters for drug-likeness (MW 200-500, LogP 1-4, Lipinski)
3. Docks all analogs against LIMK2 via DiffDock NIM (20 poses each)
4. Saves results and prints SAR analysis

Outputs:
  data/docking/genmol_119_analogs_2026-03-24.json
  data/docking/genmol_119_docking_2026-03-24.json
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
if not NVIDIA_API_KEY:
    raise RuntimeError("NVIDIA_API_KEY environment variable is required")

MOLMIM_URL = "https://health.api.nvidia.com/v1/biology/nvidia/molmim/generate"
DIFFDOCK_URL = "https://health.api.nvidia.com/v1/biology/mit/diffdock"
RATE_LIMIT_DELAY = 2.0
BATCH_SIZE = 10  # MolMIM crashes on >20
NUM_POSES = 20
RETRY_DELAY = 60

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCKING_DIR = DATA_DIR / "docking"
STRUCTURES_DIR = DATA_DIR / "structures"
PDB_FILE = STRUCTURES_DIR / "LIMK2_P53671_kinase.pdb"
ANALOGS_FILE = DOCKING_DIR / "genmol_119_analogs_2026-03-24.json"
DOCKING_FILE = DOCKING_DIR / "genmol_119_docking_2026-03-24.json"

DOCKING_DIR.mkdir(parents=True, exist_ok=True)

# Seed compound
GENMOL_119_SMILES = "CC(C)C(=O)N1CC[C@@H](C(F)(F)F)C[C@H]1c1ccncc1"
GENMOL_119_SCORE = 1.058  # benchmark

# Drug-likeness filters
MW_MIN, MW_MAX = 200, 500
LOGP_MIN, LOGP_MAX = 1.0, 4.0
HBA_MAX = 10
HBD_MAX = 5

# RDKit
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, QED, rdMolDescriptors, DataStructs
from rdkit.Chem.Fingerprints import FingerprintMols


def compute_properties(smiles):
    """Compute molecular properties using RDKit."""
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

    # Tanimoto similarity to parent
    parent_mol = Chem.MolFromSmiles(GENMOL_119_SMILES)
    parent_fp = FingerprintMols.FingerprintMol(parent_mol)
    child_fp = FingerprintMols.FingerprintMol(mol)
    similarity = DataStructs.TanimotoSimilarity(parent_fp, child_fp)

    # SAR features
    has_cf3 = "C(F)(F)F" in smiles or "C(F)(F)(F)" in Chem.MolToSmiles(mol)
    has_pyridine = mol.HasSubstructMatch(Chem.MolFromSmarts("c1ccncc1"))
    has_piperidine = mol.HasSubstructMatch(Chem.MolFromSmarts("C1CCNCC1"))
    has_amide = mol.HasSubstructMatch(Chem.MolFromSmarts("C(=O)N"))
    has_hydroxyl = mol.HasSubstructMatch(Chem.MolFromSmarts("[OH]"))
    has_amino = mol.HasSubstructMatch(Chem.MolFromSmarts("[NH2]"))
    num_fluorines = sum(1 for atom in mol.GetAtoms() if atom.GetAtomicNum() == 9)
    num_stereocenters = len(Chem.FindMolChiralCenters(mol, includeUnassigned=True))

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
        "similarity_to_parent": round(similarity, 4),
        "sar_features": {
            "has_cf3": has_cf3,
            "has_pyridine": has_pyridine,
            "has_piperidine": has_piperidine,
            "has_amide": has_amide,
            "has_hydroxyl": has_hydroxyl,
            "has_amino": has_amino,
            "num_fluorines": num_fluorines,
            "num_stereocenters": num_stereocenters,
        },
    }


def passes_filters(props):
    """Check drug-likeness and BBB filters."""
    if not props or not props.get("valid"):
        return False
    mw = props["mw"]
    logp = props["logp"]
    hba = props["hba"]
    hbd = props["hbd"]
    if not (MW_MIN <= mw <= MW_MAX):
        return False
    if not (LOGP_MIN <= logp <= LOGP_MAX):
        return False
    if hba > HBA_MAX or hbd > HBD_MAX:
        return False
    return True


# =====================
# STEP 1: Generate Analogs via MolMIM
# =====================

async def call_molmim(seed_smiles, num_molecules=10, min_similarity=0.3, iterations=20):
    """Call NVIDIA MolMIM to generate molecules from a seed."""
    import httpx

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "smi": seed_smiles,
        "num_molecules": str(num_molecules),
        "algorithm": "CMA-ES",
        "property_name": "QED",
        "min_similarity": str(min_similarity),
        "iterations": str(iterations),
    }

    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(MOLMIM_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    molecules = []
    if isinstance(data, dict) and "molecules" in data:
        mol_list = data["molecules"]
        if isinstance(mol_list, str):
            mol_list = json.loads(mol_list)
        for mol in mol_list:
            if isinstance(mol, dict):
                molecules.append({
                    "smiles": mol.get("sample", ""),
                    "score": mol.get("score"),
                })
            elif isinstance(mol, str):
                molecules.append({"smiles": mol})

    logger.info(f"  MolMIM: {len(molecules)} molecules (sim={min_similarity}, iter={iterations})")
    return molecules


async def generate_analogs():
    """Generate ~100 analogs with diverse similarity and iteration settings."""
    # Broad diversity strategy: 12 batches x 10 = 120 raw, expect ~100 unique after filtering
    batch_configs = [
        # Close analogs -- conservative modifications
        {"min_similarity": 0.7, "iterations": 10, "num": BATCH_SIZE},
        {"min_similarity": 0.6, "iterations": 15, "num": BATCH_SIZE},
        {"min_similarity": 0.6, "iterations": 20, "num": BATCH_SIZE},
        # Medium diversity
        {"min_similarity": 0.5, "iterations": 15, "num": BATCH_SIZE},
        {"min_similarity": 0.5, "iterations": 20, "num": BATCH_SIZE},
        {"min_similarity": 0.5, "iterations": 25, "num": BATCH_SIZE},
        # Higher diversity -- scaffold hops
        {"min_similarity": 0.4, "iterations": 20, "num": BATCH_SIZE},
        {"min_similarity": 0.4, "iterations": 25, "num": BATCH_SIZE},
        {"min_similarity": 0.4, "iterations": 30, "num": BATCH_SIZE},
        # Maximum diversity
        {"min_similarity": 0.3, "iterations": 20, "num": BATCH_SIZE},
        {"min_similarity": 0.3, "iterations": 25, "num": BATCH_SIZE},
        {"min_similarity": 0.3, "iterations": 30, "num": BATCH_SIZE},
    ]

    all_raw = []
    all_valid = []
    all_filtered = []
    seen_smiles = set()
    # Don't include the parent itself
    seen_smiles.add(Chem.MolToSmiles(Chem.MolFromSmiles(GENMOL_119_SMILES)))

    for batch_idx, config in enumerate(batch_configs):
        logger.info(f"\nBatch {batch_idx+1}/{len(batch_configs)}: sim={config['min_similarity']}, iter={config['iterations']}")
        try:
            molecules = await call_molmim(
                seed_smiles=GENMOL_119_SMILES,
                num_molecules=config["num"],
                min_similarity=config["min_similarity"],
                iterations=config["iterations"],
            )
        except Exception as e:
            logger.error(f"  Batch {batch_idx+1} failed: {e}")
            molecules = []

        for mol_data in molecules:
            smiles = mol_data.get("smiles", "")
            if not smiles:
                continue

            all_raw.append({
                "smiles": smiles,
                "api_score": mol_data.get("score"),
                "batch": batch_idx,
                "min_similarity": config["min_similarity"],
                "iterations": config["iterations"],
            })

            props = compute_properties(smiles)
            if props is None:
                continue

            canonical = props["smiles"]
            if canonical in seen_smiles:
                continue
            seen_smiles.add(canonical)

            entry = {
                **props,
                "api_score": mol_data.get("score"),
                "batch": batch_idx,
                "generation_similarity": config["min_similarity"],
                "generation_iterations": config["iterations"],
            }
            all_valid.append(entry)

            if passes_filters(props):
                all_filtered.append(entry)

        logger.info(f"  Running totals: raw={len(all_raw)}, valid_unique={len(all_valid)}, drug_like={len(all_filtered)}")
        await asyncio.sleep(RATE_LIMIT_DELAY)

    # Sort by QED
    all_filtered.sort(key=lambda x: x.get("qed", 0), reverse=True)
    all_valid.sort(key=lambda x: x.get("qed", 0), reverse=True)

    results = {
        "campaign": "genmol_119 SAR exploration",
        "date": datetime.now(timezone.utc).isoformat(),
        "parent": {
            "name": "genmol_119",
            "smiles": GENMOL_119_SMILES,
            "diffdock_score": GENMOL_119_SCORE,
        },
        "generation": {
            "method": "NVIDIA MolMIM (CMA-ES)",
            "batches": len(batch_configs),
            "batch_size": BATCH_SIZE,
            "similarity_range": "0.3-0.7",
        },
        "filters": {
            "mw_range": [MW_MIN, MW_MAX],
            "logp_range": [LOGP_MIN, LOGP_MAX],
            "hba_max": HBA_MAX,
            "hbd_max": HBD_MAX,
        },
        "stats": {
            "total_raw": len(all_raw),
            "total_valid_unique": len(all_valid),
            "total_drug_like": len(all_filtered),
        },
        "all_drug_like": all_filtered,
        "all_valid": all_valid,
    }

    with open(ANALOGS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"\nAnalogs saved to {ANALOGS_FILE}")
    logger.info(f"Stats: {len(all_raw)} raw -> {len(all_valid)} valid unique -> {len(all_filtered)} drug-like")

    return results


# =====================
# STEP 2: Dock All Against LIMK2
# =====================

def smiles_to_sdf(smiles, name=""):
    """Convert SMILES to SDF for DiffDock."""
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


def load_protein_pdb(pdb_path):
    """Load PDB ATOM lines."""
    text = pdb_path.read_text()
    atom_lines = [l for l in text.split("\n") if l.startswith("ATOM")]
    logger.info(f"Loaded LIMK2 PDB: {len(atom_lines)} ATOM lines")
    return "\n".join(atom_lines)


async def dock_single(protein_pdb, smiles, mol_name, api_key):
    """Dock a single molecule against LIMK2."""
    import httpx

    ligand_sdf = smiles_to_sdf(smiles, name=mol_name)

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

        if resp.status_code in (403, 429):
            logger.warning(f"  Rate limited ({resp.status_code}), waiting {RETRY_DELAY}s...")
            await asyncio.sleep(RETRY_DELAY)
            resp = await client.post(DIFFDOCK_URL, json=payload, headers=headers)

        resp.raise_for_status()
        result = resp.json()

    # Parse confidences
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
        "mean_confidence": mean_confidence if mean_confidence else None,
        "all_confidences": sorted(confidences, reverse=True) if confidences else [],
        "positive_poses": len([c for c in confidences if c > 0]),
    }


async def dock_all(analogs_data):
    """Dock all drug-like analogs against LIMK2."""
    molecules = analogs_data["all_drug_like"]
    if not molecules:
        logger.error("No drug-like analogs to dock!")
        return

    protein_pdb = load_protein_pdb(PDB_FILE)

    # Pre-validate SDF
    logger.info(f"\nPre-validating {len(molecules)} molecules for SDF conversion...")
    sdf_ok = []
    sdf_fail = []
    for i, mol in enumerate(molecules):
        try:
            smiles_to_sdf(mol["smiles"], name=f"analog_{i:03d}")
            sdf_ok.append(i)
        except Exception as e:
            sdf_fail.append((i, str(e)))
    logger.info(f"  SDF validation: {len(sdf_ok)} OK, {len(sdf_fail)} failed")

    sdf_fail_indices = {idx for idx, _ in sdf_fail}

    # Dock
    results = []
    total = len(molecules)
    start_time = time.time()

    for i, mol in enumerate(molecules):
        smiles = mol["smiles"]
        sim = mol.get("similarity_to_parent", "?")
        logger.info(f"\n[{i+1}/{total}] analog_{i:03d} (MW={mol['mw']:.1f}, QED={mol.get('qed',0):.3f}, sim={sim})")

        if i in sdf_fail_indices:
            logger.warning(f"  SKIP: SDF conversion failed")
            results.append({
                "index": i,
                "smiles": smiles,
                "error": "SDF conversion failed",
                "skipped": True,
                **{k: mol.get(k) for k in ["mw", "logp", "qed", "tpsa", "hbd", "hba", "rings",
                                             "rotatable_bonds", "similarity_to_parent", "sar_features"]},
            })
            continue

        try:
            dock_result = await dock_single(protein_pdb, smiles, f"analog_{i:03d}", NVIDIA_API_KEY)
            entry = {
                "index": i,
                "smiles": smiles,
                **{k: mol.get(k) for k in ["mw", "logp", "qed", "tpsa", "hbd", "hba", "rings",
                                             "rotatable_bonds", "similarity_to_parent", "sar_features",
                                             "generation_similarity", "generation_iterations"]},
                **dock_result,
            }
            results.append(entry)

            conf = dock_result.get("top_confidence")
            if conf is not None:
                beats = " *** BEATS genmol_119! ***" if conf > GENMOL_119_SCORE else ""
                label = "BINDING" if conf > 0 else "no binding"
                logger.info(
                    f"  -> conf={conf:+.4f} ({label}), "
                    f"pos_poses={dock_result['positive_poses']}/{dock_result['num_poses']}"
                    f"{beats}"
                )
        except Exception as e:
            logger.error(f"  -> FAILED: {e}")
            results.append({
                "index": i,
                "smiles": smiles,
                "error": str(e),
                **{k: mol.get(k) for k in ["mw", "logp", "qed", "similarity_to_parent", "sar_features"]},
            })

        if i < total - 1:
            await asyncio.sleep(RATE_LIMIT_DELAY)

    elapsed = time.time() - start_time

    # Save docking results
    output = {
        "campaign": "genmol_119 SAR docking vs LIMK2",
        "date": datetime.now(timezone.utc).isoformat(),
        "parent": analogs_data["parent"],
        "target": "LIMK2 kinase domain (P53671, res 309-595)",
        "diffdock_version": "v2.2 (NVIDIA NIM)",
        "num_poses": NUM_POSES,
        "total_molecules": len(molecules),
        "sdf_failures": len(sdf_fail),
        "elapsed_seconds": round(elapsed, 1),
        "benchmark": {
            "compound": "genmol_119",
            "smiles": GENMOL_119_SMILES,
            "top_confidence": GENMOL_119_SCORE,
        },
        "results": results,
    }

    with open(DOCKING_FILE, "w") as f:
        json.dump(output, f, indent=2)
    logger.info(f"\nDocking results saved to {DOCKING_FILE}")

    # Print SAR analysis
    print_sar_analysis(results, elapsed)

    return results


def print_sar_analysis(results, elapsed):
    """Print SAR analysis with structural insights."""
    successful = [r for r in results if r.get("top_confidence") is not None]
    positive = [r for r in successful if r["top_confidence"] > 0]
    beats_parent = [r for r in successful if r["top_confidence"] > GENMOL_119_SCORE]
    errors = [r for r in results if r.get("error")]

    print(f"\n{'='*80}")
    print(f"  SAR ANALYSIS: genmol_119 Analogs vs LIMK2")
    print(f"{'='*80}")
    print(f"  Parent: genmol_119  score={GENMOL_119_SCORE:+.3f}")
    print(f"  SMILES: {GENMOL_119_SMILES}")
    print(f"  Total analogs docked: {len(results)}")
    print(f"  Successful: {len(successful)}")
    print(f"  Errors/skipped: {len(errors)}")
    print(f"  Positive binding: {len(positive)}/{len(successful)} ({100*len(positive)/max(len(successful),1):.0f}%)")
    print(f"  Beat genmol_119 (+{GENMOL_119_SCORE:.3f}): {len(beats_parent)}")
    print(f"  Elapsed: {elapsed/60:.1f} min")

    if not successful:
        print("  No successful dockings.")
        return

    # Top 10 ranked
    ranked = sorted(successful, key=lambda x: x["top_confidence"], reverse=True)
    print(f"\n--- TOP 10 ANALOGS (ranked by confidence) ---")
    print(f"  {'Rank':<5} {'Conf':>8} {'MW':>6} {'LogP':>6} {'QED':>6} {'Sim':>6} {'Pos':>5} {'SMILES'}")
    print(f"  {'-'*5} {'-'*8} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*5} {'-'*50}")
    for rank, r in enumerate(ranked[:10], 1):
        beats = " ***" if r["top_confidence"] > GENMOL_119_SCORE else ""
        smiles = r["smiles"][:50] + ("..." if len(r["smiles"]) > 50 else "")
        print(
            f"  {rank:<5} {r['top_confidence']:+8.4f} "
            f"{r.get('mw', 0):6.1f} {r.get('logp', 0):6.2f} "
            f"{r.get('qed', 0):6.3f} {r.get('similarity_to_parent', 0):6.3f} "
            f"{r.get('positive_poses', 0):3d}/{r.get('num_poses', 0):d} "
            f"{smiles}{beats}"
        )

    # SAR: CF3 group
    print(f"\n--- SAR: CF3 Group ---")
    with_cf3 = [r for r in successful if r.get("sar_features", {}).get("has_cf3")]
    without_cf3 = [r for r in successful if not r.get("sar_features", {}).get("has_cf3")]
    if with_cf3:
        cf3_confs = [r["top_confidence"] for r in with_cf3]
        print(f"  With CF3:    n={len(with_cf3)}, mean={sum(cf3_confs)/len(cf3_confs):+.4f}, best={max(cf3_confs):+.4f}")
    if without_cf3:
        no_cf3_confs = [r["top_confidence"] for r in without_cf3]
        print(f"  Without CF3: n={len(without_cf3)}, mean={sum(no_cf3_confs)/len(no_cf3_confs):+.4f}, best={max(no_cf3_confs):+.4f}")

    # SAR: Pyridine
    print(f"\n--- SAR: Pyridine Ring ---")
    with_pyr = [r for r in successful if r.get("sar_features", {}).get("has_pyridine")]
    without_pyr = [r for r in successful if not r.get("sar_features", {}).get("has_pyridine")]
    if with_pyr:
        pyr_confs = [r["top_confidence"] for r in with_pyr]
        print(f"  With pyridine:    n={len(with_pyr)}, mean={sum(pyr_confs)/len(pyr_confs):+.4f}, best={max(pyr_confs):+.4f}")
    if without_pyr:
        no_pyr_confs = [r["top_confidence"] for r in without_pyr]
        print(f"  Without pyridine: n={len(without_pyr)}, mean={sum(no_pyr_confs)/len(no_pyr_confs):+.4f}, best={max(no_pyr_confs):+.4f}")

    # SAR: Stereochemistry
    print(f"\n--- SAR: Stereocenters ---")
    stereo_groups = {}
    for r in successful:
        n = r.get("sar_features", {}).get("num_stereocenters", 0)
        stereo_groups.setdefault(n, []).append(r["top_confidence"])
    for n, confs in sorted(stereo_groups.items()):
        print(f"  {n} stereocenters: n={len(confs)}, mean={sum(confs)/len(confs):+.4f}, best={max(confs):+.4f}")

    # SAR: Hydroxyl/Amino additions
    print(f"\n--- SAR: Polar Group Additions ---")
    with_oh = [r for r in successful if r.get("sar_features", {}).get("has_hydroxyl")]
    with_nh2 = [r for r in successful if r.get("sar_features", {}).get("has_amino")]
    if with_oh:
        oh_confs = [r["top_confidence"] for r in with_oh]
        print(f"  With -OH:  n={len(with_oh)}, mean={sum(oh_confs)/len(oh_confs):+.4f}, best={max(oh_confs):+.4f}")
    else:
        print(f"  With -OH:  n=0")
    if with_nh2:
        nh2_confs = [r["top_confidence"] for r in with_nh2]
        print(f"  With -NH2: n={len(with_nh2)}, mean={sum(nh2_confs)/len(nh2_confs):+.4f}, best={max(nh2_confs):+.4f}")
    else:
        print(f"  With -NH2: n=0")

    # SAR: MW vs confidence
    print(f"\n--- SAR: MW vs Binding ---")
    mw_bins = {"<250": [], "250-300": [], "300-350": [], "350-400": [], ">400": []}
    for r in successful:
        mw = r.get("mw", 0)
        if mw < 250:
            mw_bins["<250"].append(r["top_confidence"])
        elif mw < 300:
            mw_bins["250-300"].append(r["top_confidence"])
        elif mw < 350:
            mw_bins["300-350"].append(r["top_confidence"])
        elif mw < 400:
            mw_bins["350-400"].append(r["top_confidence"])
        else:
            mw_bins[">400"].append(r["top_confidence"])
    for label, confs in mw_bins.items():
        if confs:
            print(f"  MW {label:>7}: n={len(confs):2d}, mean={sum(confs)/len(confs):+.4f}, best={max(confs):+.4f}")

    # SAR: Similarity to parent
    print(f"\n--- SAR: Similarity to Parent vs Binding ---")
    sim_bins = {"0.8-1.0": [], "0.6-0.8": [], "0.4-0.6": [], "0.2-0.4": [], "<0.2": []}
    for r in successful:
        sim = r.get("similarity_to_parent", 0)
        if sim >= 0.8:
            sim_bins["0.8-1.0"].append(r["top_confidence"])
        elif sim >= 0.6:
            sim_bins["0.6-0.8"].append(r["top_confidence"])
        elif sim >= 0.4:
            sim_bins["0.4-0.6"].append(r["top_confidence"])
        elif sim >= 0.2:
            sim_bins["0.2-0.4"].append(r["top_confidence"])
        else:
            sim_bins["<0.2"].append(r["top_confidence"])
    for label, confs in sim_bins.items():
        if confs:
            print(f"  Sim {label:>7}: n={len(confs):2d}, mean={sum(confs)/len(confs):+.4f}, best={max(confs):+.4f}")

    # Statistics
    all_confs = [r["top_confidence"] for r in successful]
    print(f"\n--- OVERALL STATISTICS ---")
    print(f"  Best:   {max(all_confs):+.4f}")
    print(f"  Worst:  {min(all_confs):+.4f}")
    print(f"  Mean:   {sum(all_confs)/len(all_confs):+.4f}")
    print(f"  Median: {sorted(all_confs)[len(all_confs)//2]:+.4f}")
    print(f"  Binding rate: {len(positive)}/{len(successful)} ({100*len(positive)/len(successful):.0f}%)")
    print(f"  Beat parent: {len(beats_parent)}/{len(successful)}")
    print(f"{'='*80}\n")


# =====================
# MAIN
# =====================

async def main():
    start = time.time()
    print(f"\n{'='*80}")
    print(f"  SAR Campaign: genmol_119 Analogs vs LIMK2")
    print(f"  Parent: {GENMOL_119_SMILES}")
    print(f"  Benchmark: +{GENMOL_119_SCORE:.3f}")
    print(f"  Date: 2026-03-24")
    print(f"{'='*80}\n")

    # Step 1: Generate analogs
    logger.info("=" * 60)
    logger.info("STEP 1: Generating analogs via MolMIM")
    logger.info("=" * 60)
    analogs = await generate_analogs()

    # Step 2: Dock all
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: Docking all analogs vs LIMK2")
    logger.info("=" * 60)
    docking_results = await dock_all(analogs)

    total_elapsed = time.time() - start
    print(f"\nTotal campaign time: {total_elapsed/60:.1f} min")
    print(f"Output files:")
    print(f"  Analogs: {ANALOGS_FILE}")
    print(f"  Docking: {DOCKING_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
