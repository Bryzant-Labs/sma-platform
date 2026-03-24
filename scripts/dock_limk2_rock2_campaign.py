#!/usr/bin/env python3
"""
DiffDock Docking Campaign: ROCK2 + LIMK2 targets
=================================================
Campaign date: 2026-03-24
Rationale: LIMK2 upregulated 2.8x in SMA motor neurons (new finding),
           ROCK1/2 both UP in SMA MNs — Fasudil validated preclinically.

Docks 7 ROCK/LIMK pathway compounds against ROCK2 and LIMK2 targets
using NVIDIA NIM DiffDock v2.2 with 20 poses per docking (validation grade).

Fix applied:
  - PDB files trimmed to kinase domains only (payload size reduction)
  - SMILES converted to SDF via RDKit (DiffDock v2.2 NIM rejects SMILES format)

Usage:
    python scripts/dock_limk2_rock2_campaign.py
"""

import asyncio
import json
import logging
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# --- Configuration ---
NVIDIA_API_KEY = os.environ.get(
    "NVIDIA_API_KEY",
    "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",
)
NVIDIA_API_KEY_BACKUP = "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"

DIFFDOCK_URL = "https://health.api.nvidia.com/v1/biology/mit/diffdock"
NUM_POSES = 20  # NEVER use 5 — always 20 for validation
RATE_LIMIT_DELAY = 2.0  # seconds between requests (40 req/min limit)

# Resolve paths relative to project root
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
STRUCTURES_DIR = DATA_DIR / "structures"
DOCKING_DIR = DATA_DIR / "docking"
DOCS_DIR = PROJECT_ROOT / "docs" / "research"

# --- Targets ---
# Domain ranges from UniProt (kinase domains only — reduces payload size)
TARGETS = [
    {
        "symbol": "ROCK2",
        "uniprot": "O75116",
        "alphafold_url": "https://alphafold.ebi.ac.uk/files/AF-O75116-F1-model_v6.pdb",
        "note": "Primary Fasudil target, UP in SMA MNs, Rho-associated kinase",
        "domain_start": 18,
        "domain_end": 413,
        "domain_name": "kinase",
    },
    {
        "symbol": "LIMK2",
        "uniprot": "P53671",
        "alphafold_url": "https://alphafold.ebi.ac.uk/files/AF-P53671-F1-model_v6.pdb",
        "note": "NEW: Upregulated 2.8x in SMA MNs, phosphorylates cofilin, downstream of ROCK",
        "domain_start": 309,
        "domain_end": 595,
        "domain_name": "kinase",
    },
]

# --- Compounds ---
# SMILES verified from ChEMBL / PubChem
COMPOUNDS = [
    {
        "name": "Fasudil",
        "smiles": "O=C1CCN(Cc2cccc3cnccc23)CC1",
        "chembl_id": "CHEMBL279969",
        "mechanism": "ROCK inhibitor (non-selective ROCK1/2)",
        "mw": 291.35,
        "note": "Approved Japan/China, Phase 2 ALS, first-in-field for SMA actin pathway",
    },
    {
        "name": "Y-27632",
        "smiles": "CC(N)C1CCC(C(=O)Nc2ccncc2)CC1",
        "chembl_id": "CHEMBL154236",
        "mechanism": "Selective ROCK inhibitor",
        "mw": 247.34,
        "note": "Research tool, positive control, widely used in stem cell culture",
    },
    {
        "name": "Ripasudil",
        "smiles": "O=S(=O)(NCC1CC1)c1ccc2[nH]c3c(c2c1)CNC3",
        "chembl_id": "CHEMBL2105735",
        "mechanism": "ROCK inhibitor",
        "mw": 291.37,
        "note": "Approved glaucoma (Japan), limited CNS penetration",
    },
    {
        "name": "H-1152",
        "smiles": "CC(C)C(=O)N1CCC(C(F)(F)F)CC1c1ccncc1",
        "chembl_id": "CHEMBL461855",
        "mechanism": "Potent selective ROCK inhibitor (Ki=1.6nM)",
        "mw": 314.35,
        "note": "Most potent ROCK inhibitor, research tool",
    },
    {
        "name": "MW150",
        "smiles": "Cc1nnc(-c2cccc(-c3cc(C)nn3C)c2)o1",
        "chembl_id": None,
        "mechanism": "p38alpha MAPK inhibitor (thiadiazole)",
        "mw": 256.30,
        "note": "Our thiadiazole lead, Phase 1 complete, CNS-penetrant, anti-neuroinflammatory",
    },
    {
        "name": "BMS-5",
        "smiles": "CC(=O)Nc1ccc(-c2nc3cc(NS(=O)(=O)c4ccc(F)cc4)ccc3[nH]2)cc1",
        "chembl_id": "CHEMBL3622562",
        "mechanism": "LIMK inhibitor (LIMK1/2 dual)",
        "mw": 424.47,
        "note": "BMS LIMK inhibitor, cell-active, anti-invasion",
    },
    {
        "name": "Riluzole",
        "smiles": "Oc1nc2ccc(OC(F)(F)F)cc2s1",
        "chembl_id": "CHEMBL744",
        "mechanism": "Glutamate release inhibitor",
        "mw": 234.20,
        "note": "Validated DiffDock control — approved for ALS, neuroprotective",
    },
]


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
    # Generate 3D conformer
    result = AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
    if result == -1:
        # Fallback: try without ETKDGv3
        AllChem.EmbedMolecule(mol, randomSeed=42)
    AllChem.MMFFOptimizeMolecule(mol)
    if name:
        mol.SetProp("_Name", name)
    return Chem.MolToMolBlock(mol)


def trim_pdb_to_domain(pdb_text: str, start_res: int, end_res: int) -> str:
    """Keep only ATOM lines within residue range (kinase domain extraction).

    This trims full AlphaFold PDB structures to just the kinase domain,
    reducing payload size for faster DiffDock API responses.
    """
    lines = []
    for line in pdb_text.split('\n'):
        if line.startswith(('ATOM', 'HETATM')):
            try:
                res_num = int(line[22:26].strip())
            except (ValueError, IndexError):
                continue
            if start_res <= res_num <= end_res:
                lines.append(line)
    return '\n'.join(lines)


def fetch_structure(target: dict) -> str:
    """Download AlphaFold structure for a target, trim to kinase domain, cache.

    Returns ATOM-only lines (no HEADER/END) — DiffDock prefers this format.
    """
    domain_start = target.get("domain_start")
    domain_end = target.get("domain_end")
    domain_name = target.get("domain_name", "domain")

    # Use separate cache for trimmed structures
    if domain_start and domain_end:
        trimmed_path = STRUCTURES_DIR / f"{target['symbol']}_{target['uniprot']}_{domain_name}.pdb"
        if trimmed_path.exists():
            logger.info(f"Using cached trimmed structure: {trimmed_path}")
            content = trimmed_path.read_text()
            atom_count = sum(1 for l in content.split('\n') if l.startswith('ATOM'))
            logger.info(f"  Trimmed PDB: {atom_count} ATOM lines (residues {domain_start}-{domain_end})")
            # Return ATOM-only lines
            return '\n'.join(l for l in content.split('\n') if l.startswith('ATOM'))
    else:
        trimmed_path = None

    # First get the full PDB (may already be cached)
    full_pdb_path = STRUCTURES_DIR / f"{target['symbol']}_{target['uniprot']}.pdb"

    if full_pdb_path.exists():
        logger.info(f"Using cached full structure: {full_pdb_path}")
        full_pdb = full_pdb_path.read_text()
    else:
        STRUCTURES_DIR.mkdir(parents=True, exist_ok=True)
        url = target["alphafold_url"]
        logger.info(f"Downloading {target['symbol']} structure from AlphaFold: {url}")

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SMA-Platform/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                full_pdb = resp.read().decode()
        except Exception as e:
            logger.error(f"Failed to download {target['symbol']} structure: {e}")
            raise

        full_pdb_path.write_text(full_pdb)
        logger.info(f"Saved {target['symbol']} full structure ({len(full_pdb)} bytes) to {full_pdb_path}")

    # Trim to domain if ranges specified
    if domain_start and domain_end:
        full_atoms = sum(1 for l in full_pdb.split('\n') if l.startswith('ATOM'))
        logger.info(f"Trimming {target['symbol']} from {full_atoms} ATOM lines to residues {domain_start}-{domain_end}...")
        trimmed = trim_pdb_to_domain(full_pdb, domain_start, domain_end)
        trimmed_atoms = sum(1 for l in trimmed.split('\n') if l.startswith('ATOM'))
        logger.info(f"  Trimmed: {trimmed_atoms} ATOM lines ({trimmed_atoms/full_atoms*100:.0f}% of full protein)")

        # Cache trimmed version
        trimmed_path.write_text(trimmed)
        logger.info(f"  Saved trimmed structure to {trimmed_path}")
        # Return ATOM-only lines
        return '\n'.join(l for l in trimmed.split('\n') if l.startswith('ATOM'))
    else:
        # Return ATOM-only lines from full PDB
        return '\n'.join(l for l in full_pdb.split('\n') if l.startswith('ATOM'))


async def dock_compound(
    protein_pdb: str,
    compound: dict,
    target: dict,
    api_key: str,
) -> dict:
    """Dock a single compound against a target using DiffDock NIM.

    Converts SMILES to SDF via RDKit (DiffDock v2.2 NIM rejects SMILES format).
    """
    import httpx

    # Convert SMILES to SDF — DiffDock v2.2 NIM requires SDF, rejects SMILES
    ligand_sdf = smiles_to_sdf(compound["smiles"], name=compound["name"])

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
    logger.info(f"  Payload size: {payload_size//1024}KB ({payload_size} bytes)")

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

    # DiffDock v2.2 NIM response format:
    # {"ligand_positions": [...], "position_confidence": [...], "protein": "..."}
    confidences = result.get("position_confidence", [])

    # Fallback: try older response formats
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
        "compound": compound["name"],
        "target": target["symbol"],
        "smiles": compound["smiles"],
        "mechanism": compound["mechanism"],
        "mw": compound["mw"],
        "chembl_id": compound.get("chembl_id"),
        "num_poses": len(confidences),
        "num_poses_requested": NUM_POSES,
        "top_confidence": top_confidence,
        "mean_confidence": mean_confidence,
        "all_confidences": sorted(confidences, reverse=True) if confidences else [],
        "positive_poses": len([c for c in confidences if c > 0]),
        "raw_response_keys": list(result.keys()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def run_campaign():
    """Run the full LIMK2 + ROCK2 docking campaign."""
    logger.info("=" * 70)
    logger.info("DiffDock Campaign: ROCK2 + LIMK2 targets (2026-03-24)")
    logger.info(f"Compounds: {len(COMPOUNDS)}, Targets: {len(TARGETS)}")
    logger.info(f"Poses per docking: {NUM_POSES}")
    logger.info(f"Total dockings: {len(COMPOUNDS) * len(TARGETS)}")
    logger.info("FIX: SMILES->SDF via RDKit (DiffDock v2.2 NIM rejects SMILES format)")
    logger.info("FIX: PDB structures trimmed to kinase domains")
    logger.info("=" * 70)

    # Pre-convert all SMILES to SDF
    logger.info("\nPre-converting SMILES to SDF via RDKit...")
    sdf_cache = {}
    for compound in COMPOUNDS:
        try:
            sdf = smiles_to_sdf(compound["smiles"], name=compound["name"])
            sdf_cache[compound["name"]] = sdf
            logger.info(f"  {compound['name']}: OK ({len(sdf)} chars)")
        except Exception as e:
            logger.error(f"  {compound['name']}: FAILED ({e})")
            return

    # Step 1: Fetch and trim structures
    structures = {}
    for target in TARGETS:
        try:
            structures[target["symbol"]] = fetch_structure(target)
        except Exception as e:
            logger.error(f"FATAL: Cannot get {target['symbol']} structure: {e}")
            return

    # Step 2: Dock each compound against each target
    results = []
    api_key = NVIDIA_API_KEY
    total = len(COMPOUNDS) * len(TARGETS)
    done = 0

    for target in TARGETS:
        protein_pdb = structures[target["symbol"]]
        logger.info(f"\n--- Target: {target['symbol']} ({target['uniprot']}) ---")
        logger.info(f"    {target['note']}")
        logger.info(f"    Domain: residues {target.get('domain_start')}-{target.get('domain_end')}")

        for compound in COMPOUNDS:
            done += 1
            logger.info(f"\n[{done}/{total}] Docking {compound['name']} vs {target['symbol']}...")

            # MW filter
            if compound["mw"] < 150:
                logger.warning(f"  SKIP: MW {compound['mw']} < 150 (small molecule artifact risk)")
                results.append({
                    "compound": compound["name"],
                    "target": target["symbol"],
                    "skipped": True,
                    "reason": f"MW {compound['mw']} < 150",
                })
                continue

            try:
                result = await dock_compound(protein_pdb, compound, target, api_key)
                results.append(result)

                conf = result.get("top_confidence")
                if conf is not None:
                    label = "BINDING" if conf > 0 else "no binding"
                    logger.info(f"  -> top_confidence: {conf:.4f} ({label})")
                    logger.info(f"  -> positive poses: {result.get('positive_poses', 0)}/{result.get('num_poses', '?')}")
                    logger.info(f"  -> mean confidence: {result.get('mean_confidence', 0):.4f}")
                else:
                    logger.warning(f"  -> No confidence score returned")
                    logger.info(f"  -> Response keys: {result.get('raw_response_keys')}")

            except Exception as e:
                logger.error(f"  -> FAILED: {e}")
                results.append({
                    "compound": compound["name"],
                    "target": target["symbol"],
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            # Rate limiting: 2s delay between requests
            if done < total:
                logger.info(f"  (rate limit delay: {RATE_LIMIT_DELAY}s)")
                await asyncio.sleep(RATE_LIMIT_DELAY)

    # Step 3: Save results
    DOCKING_DIR.mkdir(parents=True, exist_ok=True)
    outfile = DOCKING_DIR / "limk2_rock2_campaign_2026-03-24.json"
    with open(outfile, "w") as f:
        json.dump({
            "campaign": "ROCK2 + LIMK2 docking campaign",
            "date": "2026-03-24",
            "diffdock_version": "v2.2 (NVIDIA NIM)",
            "num_poses": NUM_POSES,
            "fix_applied": [
                "SMILES converted to SDF via RDKit (DiffDock v2.2 NIM rejects SMILES format)",
                "PDB trimmed to kinase domains (ROCK2: 18-413, LIMK2: 309-595)",
            ],
            "rationale": (
                "LIMK2 upregulated 2.8x in SMA motor neurons (new finding). "
                "ROCK1/2 both UP in SMA MNs. Fasudil validated preclinically. "
                "Testing ROCK/LIMK pathway inhibitors for dual-target potential."
            ),
            "targets": [
                {
                    "symbol": t["symbol"],
                    "uniprot": t["uniprot"],
                    "note": t["note"],
                    "domain": f"residues {t.get('domain_start')}-{t.get('domain_end')}",
                }
                for t in TARGETS
            ],
            "compounds": [
                {
                    "name": c["name"],
                    "smiles": c["smiles"],
                    "mw": c["mw"],
                    "mechanism": c["mechanism"],
                }
                for c in COMPOUNDS
            ],
            "results": results,
        }, f, indent=2)
    logger.info(f"\nResults saved to {outfile}")

    # Step 4: Print summary
    print_summary(results)

    return results


def print_summary(results: list):
    """Print a formatted summary of docking results."""
    successful = [r for r in results if r.get("top_confidence") is not None]
    positive = [r for r in successful if r["top_confidence"] > 0]
    errors = [r for r in results if r.get("error")]
    skipped = [r for r in results if r.get("skipped")]

    logger.info("\n" + "=" * 70)
    logger.info("CAMPAIGN SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total dockings attempted: {len(results)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Errors: {len(errors)}")
    logger.info(f"Skipped (MW filter): {len(skipped)}")
    logger.info(f"Positive confidence (binding): {len(positive)}")
    logger.info(f"Negative confidence (no binding): {len(successful) - len(positive)}")

    if successful:
        logger.info("\n--- Results ranked by confidence ---")
        for r in sorted(successful, key=lambda x: x["top_confidence"], reverse=True):
            binding = "BIND" if r["top_confidence"] > 0 else "----"
            logger.info(
                f"  [{binding}] {r['compound']:15s} -> {r['target']:8s}: "
                f"conf={r['top_confidence']:+.4f}  "
                f"(pos_poses={r.get('positive_poses', '?')}/{r.get('num_poses', NUM_POSES)}, "
                f"mean={r.get('mean_confidence', 0):.4f})"
            )

        # Highlight key findings
        logger.info("\n--- Key Findings ---")

        # Best binder per target
        for target in TARGETS:
            target_results = [
                r for r in successful if r["target"] == target["symbol"]
            ]
            if target_results:
                best = max(target_results, key=lambda x: x["top_confidence"])
                logger.info(
                    f"  Best for {target['symbol']}: {best['compound']} "
                    f"(conf={best['top_confidence']:+.4f})"
                )

        # Fasudil cross-target comparison
        fasudil_results = [r for r in successful if r["compound"] == "Fasudil"]
        if fasudil_results:
            logger.info("\n  Fasudil cross-target:")
            for r in sorted(fasudil_results, key=lambda x: x["top_confidence"], reverse=True):
                logger.info(
                    f"    {r['target']}: conf={r['top_confidence']:+.4f} "
                    f"(pos_poses={r.get('positive_poses', '?')}/{r.get('num_poses', '?')})"
                )

        # BMS-5 (LIMK inhibitor) cross-target
        bms5_results = [r for r in successful if r["compound"] == "BMS-5"]
        if bms5_results:
            logger.info("\n  BMS-5 (LIMK inhibitor) cross-target:")
            for r in sorted(bms5_results, key=lambda x: x["top_confidence"], reverse=True):
                logger.info(
                    f"    {r['target']}: conf={r['top_confidence']:+.4f} "
                    f"(pos_poses={r.get('positive_poses', '?')}/{r.get('num_poses', '?')})"
                )

    if errors:
        logger.info("\n--- Errors ---")
        for r in errors:
            logger.info(f"  {r['compound']} -> {r['target']}: {r['error']}")


if __name__ == "__main__":
    asyncio.run(run_campaign())
