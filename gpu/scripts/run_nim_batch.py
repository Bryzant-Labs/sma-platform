#!/usr/bin/env python3
"""
NVIDIA NIM Batch Runner — DiffDock v2.2 + GenMol
=================================================
Runs on moltbot (no GPU required). Calls NVIDIA NIM cloud APIs
to dock compounds against SMA protein targets and generate novel analogs.

Pipeline:
  1. Load compound library (reference + screening_library.csv + platform API)
  2. Download AlphaFold v6 PDB structures for 7 SMA targets
  3. Convert SMILES to SDF via RDKit
  4. DiffDock v2.2 NIM: dock all compounds against all targets
  5. GenMol NIM: generate 100 novel 4-AP analogs
  6. Upload results to SMA Research Platform API
  7. Save results locally + print top-20 hits summary

Environment variables:
  NVIDIA_API_KEY  — NVIDIA NIM API bearer token
  SMA_API         — Platform API base URL (default: https://sma-research.info/api/v2)
  SMA_ADMIN_KEY   — Admin key for result upload

Usage:
    python3 run_nim_batch.py
    python3 run_nim_batch.py --compounds 50 --skip-genmol
    python3 run_nim_batch.py --output-dir /data/nim_results --skip-docking
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError:
    print("ERROR: httpx required. pip install httpx")
    sys.exit(1)

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem
except ImportError:
    print("ERROR: rdkit required. pip install rdkit")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("nim-batch")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
SMA_API = os.environ.get("SMA_API", "https://sma-research.info/api/v2")
SMA_ADMIN_KEY = os.environ.get("SMA_ADMIN_KEY", "")

SCRIPT_DIR = Path(__file__).resolve().parent
GPU_DIR = SCRIPT_DIR.parent
DATA_DIR = GPU_DIR / "data"
DEFAULT_OUTPUT_DIR = GPU_DIR / "results" / "nim_batch"

SCREENING_LIBRARY_CSV = DATA_DIR / "screening_library.csv"

# NVIDIA NIM endpoints (free tier)
DIFFDOCK_URL = "https://health.api.nvidia.com/v1/biology/mit/diffdock"
GENMOL_URL = "https://health.api.nvidia.com/v1/biology/nvidia/genmol"

# Rate limiting
DIFFDOCK_DELAY_SECS = 2.0
DIFFDOCK_ERROR_DELAY_SECS = 5.0

# 4 reference compounds — always included in every batch
REFERENCE_COMPOUNDS: list[dict[str, str]] = [
    {"name": "4-aminopyridine", "smiles": "Nc1ccncc1"},
    {"name": "risdiplam", "smiles": "C1CC2=CC(=NN2C(=C1)C3=CC(=CC4=CC=C(N=C34)NC5=CC6=C(C(=C5)F)OCCO6)F)C(F)(F)F"},
    {"name": "valproic_acid", "smiles": "CCCC(CCC)C(=O)O"},
    {"name": "riluzole", "smiles": "Nc1nc2ccc(OC(F)(F)F)cc2s1"},
]

# 7 SMA protein targets with UniProt IDs
TARGETS: list[dict[str, str]] = [
    {"symbol": "SMN2", "uniprot_id": "Q16637"},
    {"symbol": "SMN1", "uniprot_id": "P62316"},
    {"symbol": "PLS3", "uniprot_id": "P13797"},
    {"symbol": "STMN2", "uniprot_id": "Q93045"},
    {"symbol": "NCALD", "uniprot_id": "P61601"},
    {"symbol": "UBA1", "uniprot_id": "P22314"},
    {"symbol": "CORO1C", "uniprot_id": "Q9ULV4"},
]

ALPHAFOLD_URL_TEMPLATE = "https://alphafold.ebi.ac.uk/files/AF-{uniprot}-F1-model_v6.pdb"


# ---------------------------------------------------------------------------
# Compound Loading
# ---------------------------------------------------------------------------

def load_reference_compounds() -> list[dict[str, str]]:
    """Return the 4 reference compounds that are always included."""
    return [dict(c) for c in REFERENCE_COMPOUNDS]


def load_screening_library(max_compounds: int) -> list[dict[str, str]]:
    """Load compounds from screening_library.csv (up to max_compounds)."""
    compounds: list[dict[str, str]] = []

    if not SCREENING_LIBRARY_CSV.exists():
        logger.warning("Screening library not found: %s", SCREENING_LIBRARY_CSV)
        return compounds

    with open(SCREENING_LIBRARY_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("name", "").strip()
            smiles = row.get("smiles", "").strip()
            if not name or not smiles:
                continue
            compounds.append({"name": name, "smiles": smiles})
            if len(compounds) >= max_compounds:
                break

    logger.info("Loaded %d compounds from screening library", len(compounds))
    return compounds


async def load_platform_compounds(
    client: httpx.AsyncClient, needed: int
) -> list[dict[str, str]]:
    """Fetch additional compounds from platform API to fill the batch."""
    if needed <= 0:
        return []

    url = f"{SMA_API}/screen/compounds/results"
    compounds: list[dict[str, str]] = []

    try:
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # API may return list or {"results": [...]}
        results = data if isinstance(data, list) else data.get("results", [])

        for item in results:
            name = item.get("name", item.get("compound_name", ""))
            smiles = item.get("smiles", "")
            if name and smiles:
                compounds.append({"name": name, "smiles": smiles})
            if len(compounds) >= needed:
                break

        logger.info("Loaded %d compounds from platform API", len(compounds))
    except httpx.HTTPStatusError as e:
        logger.warning("Platform API returned %d: %s", e.response.status_code, e.response.text[:200])
    except Exception as e:
        logger.warning("Failed to fetch compounds from platform API: %s", e)

    return compounds


async def build_compound_library(
    client: httpx.AsyncClient, max_total: int
) -> list[dict[str, str]]:
    """
    Build the compound library:
      1. 4 reference compounds (always)
      2. Up to 50 from screening_library.csv
      3. Fill remaining from platform API
    Deduplicate by SMILES.
    """
    seen_smiles: set[str] = set()
    library: list[dict[str, str]] = []

    def add_unique(compounds: list[dict[str, str]]) -> int:
        added = 0
        for c in compounds:
            canonical = canonicalize_smiles(c["smiles"])
            if canonical and canonical not in seen_smiles and len(library) < max_total:
                seen_smiles.add(canonical)
                library.append({"name": c["name"], "smiles": canonical})
                added += 1
        return added

    # Step 1: Reference compounds
    refs = load_reference_compounds()
    n_refs = add_unique(refs)
    logger.info("Reference compounds: %d", n_refs)

    # Step 2: Screening library (up to 50)
    csv_compounds = load_screening_library(max_compounds=50)
    n_csv = add_unique(csv_compounds)
    logger.info("Screening library compounds: %d", n_csv)

    # Step 3: Fill from platform API
    remaining = max_total - len(library)
    if remaining > 0:
        api_compounds = await load_platform_compounds(client, needed=remaining)
        n_api = add_unique(api_compounds)
        logger.info("Platform API compounds: %d", n_api)

    logger.info("Total compound library: %d compounds", len(library))
    return library


# ---------------------------------------------------------------------------
# Chemistry Utilities
# ---------------------------------------------------------------------------

def canonicalize_smiles(smiles: str) -> str | None:
    """Canonicalize SMILES string. Returns None if invalid."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return Chem.MolToSmiles(mol)
    except Exception:
        return None


def smiles_to_sdf(smiles: str) -> str | None:
    """
    Convert a SMILES string to SDF format with 3D coordinates.
    Required by DiffDock NIM API.
    Returns SDF content as string, or None on failure.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None

        mol = Chem.AddHs(mol)

        # Generate 3D coordinates
        result = AllChem.EmbedMolecule(mol, randomSeed=42)
        if result == -1:
            # Retry with different parameters for difficult molecules
            params = AllChem.ETKDGv3()
            params.randomSeed = 42
            params.useSmallRingTorsions = True
            result = AllChem.EmbedMolecule(mol, params)
            if result == -1:
                logger.warning("Failed to embed molecule: %s", smiles)
                return None

        # Optimize geometry
        try:
            AllChem.MMFFOptimizeMolecule(mol, maxIters=500)
        except Exception:
            # MMFF may fail for some molecules — UFF fallback
            try:
                AllChem.UFFOptimizeMolecule(mol, maxIters=500)
            except Exception:
                pass  # Use unoptimized coordinates

        # Write to SDF string
        writer = Chem.SDWriter(StringIO())
        # Use a temporary file approach since SDWriter to StringIO can be tricky
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sdf", delete=False) as tmp:
            tmp_path = tmp.name

        w = Chem.SDWriter(tmp_path)
        w.write(mol)
        w.close()

        with open(tmp_path) as f:
            sdf_content = f.read()

        os.unlink(tmp_path)
        return sdf_content

    except Exception as e:
        logger.warning("SMILES to SDF conversion failed for %s: %s", smiles, e)
        return None


# ---------------------------------------------------------------------------
# AlphaFold Structure Download
# ---------------------------------------------------------------------------

async def download_alphafold_structures(
    client: httpx.AsyncClient, output_dir: Path
) -> dict[str, str]:
    """
    Download AlphaFold v6 PDB structures for all targets.
    Returns {symbol: pdb_content} dict.
    """
    pdb_cache_dir = output_dir / "pdb_cache"
    pdb_cache_dir.mkdir(parents=True, exist_ok=True)

    structures: dict[str, str] = {}

    for target in TARGETS:
        symbol = target["symbol"]
        uniprot = target["uniprot_id"]
        url = ALPHAFOLD_URL_TEMPLATE.format(uniprot=uniprot)
        pdb_path = pdb_cache_dir / f"AF-{uniprot}-F1-model_v6.pdb"

        # Use cached file if available
        if pdb_path.exists():
            logger.info("  %s (%s): using cached PDB", symbol, uniprot)
            with open(pdb_path) as f:
                structures[symbol] = f.read()
            continue

        try:
            resp = await client.get(url, timeout=60)
            resp.raise_for_status()
            pdb_content = resp.text

            # Cache to disk
            with open(pdb_path, "w") as f:
                f.write(pdb_content)

            structures[symbol] = pdb_content
            logger.info("  %s (%s): downloaded (%d bytes)", symbol, uniprot, len(pdb_content))

        except Exception as e:
            logger.error("  %s (%s): download failed: %s", symbol, uniprot, e)

    logger.info("Downloaded %d/%d AlphaFold structures", len(structures), len(TARGETS))
    return structures


# ---------------------------------------------------------------------------
# DiffDock v2.2 NIM API
# ---------------------------------------------------------------------------

async def run_diffdock_single(
    client: httpx.AsyncClient,
    compound_name: str,
    sdf_content: str,
    target_symbol: str,
    pdb_content: str,
) -> dict[str, Any] | None:
    """
    Run a single DiffDock v2.2 docking via NVIDIA NIM API.
    Returns parsed result dict or None on failure.
    """
    payload = {
        "ligand": sdf_content,
        "ligand_file_type": "sdf",
        "protein": pdb_content,
        "num_poses": 5,
        "time_divisions": 20,
        "steps": 18,
    }

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        resp = await client.post(
            DIFFDOCK_URL,
            json=payload,
            headers=headers,
            timeout=120,
        )
        resp.raise_for_status()
        result = resp.json()

        return {
            "compound": compound_name,
            "target": target_symbol,
            "status": "success",
            "response": result,
        }

    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        body = e.response.text[:300]
        logger.error(
            "DiffDock API error %d for %s vs %s: %s",
            status, compound_name, target_symbol, body,
        )
        return {
            "compound": compound_name,
            "target": target_symbol,
            "status": "error",
            "error": f"HTTP {status}: {body}",
        }

    except Exception as e:
        logger.error(
            "DiffDock request failed for %s vs %s: %s",
            compound_name, target_symbol, e,
        )
        return {
            "compound": compound_name,
            "target": target_symbol,
            "status": "error",
            "error": str(e),
        }


def extract_best_confidence(result: dict[str, Any]) -> float | None:
    """Extract the best (highest) confidence score from a DiffDock result."""
    if result.get("status") != "success":
        return None

    response = result.get("response", {})

    # DiffDock NIM returns poses with confidence scores
    # The response structure may vary — handle multiple formats
    best = None

    # Format 1: top-level "confidence" or "confidence_score"
    for key in ("confidence", "confidence_score", "score"):
        val = response.get(key)
        if val is not None:
            try:
                score = float(val)
                if best is None or score > best:
                    best = score
            except (ValueError, TypeError):
                pass

    # Format 2: list of poses with confidence
    poses = response.get("poses", response.get("results", []))
    if isinstance(poses, list):
        for pose in poses:
            if isinstance(pose, dict):
                for key in ("confidence", "confidence_score", "score"):
                    val = pose.get(key)
                    if val is not None:
                        try:
                            score = float(val)
                            if best is None or score > best:
                                best = score
                        except (ValueError, TypeError):
                            pass

    # Format 3: nested under "output" key
    output = response.get("output", {})
    if isinstance(output, dict):
        for key in ("confidence", "confidence_score", "score"):
            val = output.get(key)
            if val is not None:
                try:
                    score = float(val)
                    if best is None or score > best:
                        best = score
                except (ValueError, TypeError):
                    pass

    return best


async def run_diffdock_batch(
    client: httpx.AsyncClient,
    compounds: list[dict[str, str]],
    structures: dict[str, str],
    output_dir: Path,
) -> list[dict[str, Any]]:
    """
    Run DiffDock v2.2 for all compound-target pairs.
    Rate-limited with 2s delay between requests.
    """
    results: list[dict[str, Any]] = []

    # Pre-convert all SMILES to SDF
    logger.info("Converting %d compounds to SDF format...", len(compounds))
    sdf_cache: dict[str, str | None] = {}
    failed_conversions = 0

    for compound in compounds:
        sdf = smiles_to_sdf(compound["smiles"])
        sdf_cache[compound["name"]] = sdf
        if sdf is None:
            failed_conversions += 1
            logger.warning("  SDF conversion failed: %s (%s)", compound["name"], compound["smiles"])

    if failed_conversions:
        logger.warning("%d/%d compounds failed SDF conversion", failed_conversions, len(compounds))

    # Calculate total dockings
    valid_compounds = [c for c in compounds if sdf_cache.get(c["name"]) is not None]
    total_dockings = len(valid_compounds) * len(structures)
    logger.info(
        "Starting DiffDock batch: %d compounds x %d targets = %d dockings",
        len(valid_compounds), len(structures), total_dockings,
    )

    completed = 0
    errors = 0
    start_time = time.time()

    for compound in valid_compounds:
        sdf_content = sdf_cache[compound["name"]]
        if sdf_content is None:
            continue

        for target_symbol, pdb_content in structures.items():
            completed += 1
            elapsed = time.time() - start_time
            rate = completed / elapsed if elapsed > 0 else 0
            eta_secs = (total_dockings - completed) / rate if rate > 0 else 0

            logger.info(
                "  [%d/%d] %s vs %s (%.1f/min, ETA %.0fm)",
                completed, total_dockings,
                compound["name"], target_symbol,
                rate * 60, eta_secs / 60,
            )

            result = await run_diffdock_single(
                client, compound["name"], sdf_content, target_symbol, pdb_content,
            )

            if result:
                confidence = extract_best_confidence(result)
                result["best_confidence"] = confidence
                results.append(result)

                if result["status"] == "error":
                    errors += 1
                    await asyncio.sleep(DIFFDOCK_ERROR_DELAY_SECS)
                else:
                    await asyncio.sleep(DIFFDOCK_DELAY_SECS)
            else:
                errors += 1
                await asyncio.sleep(DIFFDOCK_ERROR_DELAY_SECS)

    duration = time.time() - start_time
    successful = sum(1 for r in results if r.get("status") == "success")
    logger.info(
        "DiffDock batch complete: %d successful, %d errors in %.1f minutes",
        successful, errors, duration / 60,
    )

    # Save raw DiffDock results
    diffdock_path = output_dir / "diffdock_results.json"
    with open(diffdock_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info("DiffDock results saved to %s", diffdock_path)

    return results


# ---------------------------------------------------------------------------
# GenMol NIM API
# ---------------------------------------------------------------------------

async def run_genmol(
    client: httpx.AsyncClient,
    seed_smiles: str,
    num_molecules: int,
    output_dir: Path,
) -> dict[str, Any]:
    """
    Generate novel molecules using NVIDIA GenMol NIM.
    Uses 4-aminopyridine as seed to generate analogs.
    """
    logger.info("GenMol: generating %d analogs from seed %s", num_molecules, seed_smiles)

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "smiles": seed_smiles,
        "num_molecules": num_molecules,
    }

    try:
        resp = await client.post(
            GENMOL_URL,
            json=payload,
            headers=headers,
            timeout=180,
        )
        resp.raise_for_status()
        result = resp.json()

        # Extract generated molecules
        molecules = result.get("molecules", result.get("results", []))
        if isinstance(result, list):
            molecules = result

        logger.info("GenMol generated %d molecules", len(molecules) if isinstance(molecules, list) else 0)

        genmol_result = {
            "seed_smiles": seed_smiles,
            "num_requested": num_molecules,
            "num_generated": len(molecules) if isinstance(molecules, list) else 0,
            "status": "success",
            "response": result,
        }

        # Save GenMol results
        genmol_path = output_dir / "genmol_results.json"
        with open(genmol_path, "w") as f:
            json.dump(genmol_result, f, indent=2)
        logger.info("GenMol results saved to %s", genmol_path)

        return genmol_result

    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        body = e.response.text[:300]
        logger.error("GenMol API error %d: %s", status, body)
        return {
            "seed_smiles": seed_smiles,
            "num_requested": num_molecules,
            "num_generated": 0,
            "status": "error",
            "error": f"HTTP {status}: {body}",
        }

    except Exception as e:
        logger.error("GenMol request failed: %s", e)
        return {
            "seed_smiles": seed_smiles,
            "num_requested": num_molecules,
            "num_generated": 0,
            "status": "error",
            "error": str(e),
        }


# ---------------------------------------------------------------------------
# Result Upload
# ---------------------------------------------------------------------------

async def upload_results(
    client: httpx.AsyncClient,
    diffdock_results: list[dict[str, Any]],
    genmol_result: dict[str, Any] | None,
) -> int:
    """Upload docking results to platform API. Returns count of successful uploads."""
    if not SMA_ADMIN_KEY:
        logger.warning("SMA_ADMIN_KEY not set — skipping result upload")
        return 0

    url = f"{SMA_API}/gpu/jobs"
    headers = {"x-admin-key": SMA_ADMIN_KEY, "Content-Type": "application/json"}
    uploaded = 0

    # Upload DiffDock results
    for result in diffdock_results:
        if result.get("status") != "success":
            continue

        payload = {
            "job_type": "diffdock_nim_v2",
            "target": result.get("target", ""),
            "compound": result.get("compound", ""),
            "parameters": {
                "num_poses": 5,
                "time_divisions": 20,
                "steps": 18,
                "model": "diffdock-v2.2-nim",
            },
            "results": {
                "best_confidence": result.get("best_confidence"),
                "response": result.get("response", {}),
            },
            "status": "completed",
        }

        try:
            resp = await client.post(url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            uploaded += 1
        except Exception as e:
            logger.warning(
                "Upload failed for %s vs %s: %s",
                result.get("compound"), result.get("target"), e,
            )

    # Upload GenMol result
    if genmol_result and genmol_result.get("status") == "success":
        payload = {
            "job_type": "genmol_nim",
            "target": "4-AP_analogs",
            "compound": "4-aminopyridine",
            "parameters": {
                "seed_smiles": genmol_result.get("seed_smiles"),
                "num_molecules": genmol_result.get("num_requested"),
                "model": "genmol-nim",
            },
            "results": {
                "num_generated": genmol_result.get("num_generated"),
                "response": genmol_result.get("response", {}),
            },
            "status": "completed",
        }

        try:
            resp = await client.post(url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            uploaded += 1
        except Exception as e:
            logger.warning("Upload failed for GenMol result: %s", e)

    logger.info("Uploaded %d results to platform API", uploaded)
    return uploaded


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_top_hits(results: list[dict[str, Any]], top_n: int = 20) -> None:
    """Print top-N hits sorted by best_confidence (descending)."""
    scored = [
        r for r in results
        if r.get("status") == "success" and r.get("best_confidence") is not None
    ]

    if not scored:
        logger.info("No scored docking results to rank")
        return

    scored.sort(key=lambda r: r.get("best_confidence", float("-inf")), reverse=True)

    print("\n" + "=" * 78)
    print(f"  TOP-{top_n} DOCKING HITS (by best_confidence)")
    print("=" * 78)
    print(f"  {'Rank':<6}{'Compound':<30}{'Target':<10}{'Confidence':>12}")
    print("  " + "-" * 68)

    for i, hit in enumerate(scored[:top_n], start=1):
        compound = hit.get("compound", "?")[:28]
        target = hit.get("target", "?")
        confidence = hit.get("best_confidence", 0.0)
        print(f"  {i:<6}{compound:<30}{target:<10}{confidence:>12.4f}")

    print("=" * 78)

    # Stats
    total = len(results)
    successful = sum(1 for r in results if r.get("status") == "success")
    errors = total - successful
    confidences = [r["best_confidence"] for r in scored]

    print(f"\n  Total dockings:  {total}")
    print(f"  Successful:      {successful}")
    print(f"  Errors:          {errors}")
    if confidences:
        avg = sum(confidences) / len(confidences)
        print(f"  Best confidence: {max(confidences):.4f}")
        print(f"  Avg confidence:  {avg:.4f}")
        print(f"  Worst (scored):  {min(confidences):.4f}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main_async(args: argparse.Namespace) -> int:
    """Async main entrypoint."""
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    logger.info("=" * 60)
    logger.info("NVIDIA NIM Batch Runner")
    logger.info("=" * 60)
    logger.info("Max compounds:  %d", args.compounds)
    logger.info("Output dir:     %s", output_dir)
    logger.info("Skip docking:   %s", args.skip_docking)
    logger.info("Skip GenMol:    %s", args.skip_genmol)
    logger.info("SMA API:        %s", SMA_API)
    logger.info("Admin key:      %s", "configured" if SMA_ADMIN_KEY else "NOT SET")
    logger.info("NVIDIA API key: %s", "configured" if NVIDIA_API_KEY else "NOT SET")

    if not NVIDIA_API_KEY:
        logger.error("NVIDIA_API_KEY environment variable is required")
        return 1

    diffdock_results: list[dict[str, Any]] = []
    genmol_result: dict[str, Any] | None = None

    async with httpx.AsyncClient() as client:
        # Step 1: Build compound library
        logger.info("\n--- Step 1: Loading compound library ---")
        compounds = await build_compound_library(client, max_total=args.compounds)

        if not compounds:
            logger.error("No compounds loaded — cannot proceed")
            return 1

        # Save compound list
        compounds_path = output_dir / "compounds.json"
        with open(compounds_path, "w") as f:
            json.dump(compounds, f, indent=2)
        logger.info("Compound list saved to %s", compounds_path)

        # Step 2: Download AlphaFold structures
        if not args.skip_docking:
            logger.info("\n--- Step 2: Downloading AlphaFold structures ---")
            structures = await download_alphafold_structures(client, output_dir)

            if not structures:
                logger.error("No structures downloaded — cannot run docking")
                return 1

            # Step 3 + 4: Convert SMILES and run DiffDock batch
            logger.info("\n--- Step 3+4: DiffDock v2.2 NIM batch ---")
            diffdock_results = await run_diffdock_batch(
                client, compounds, structures, output_dir,
            )

        # Step 5: GenMol
        if not args.skip_genmol:
            logger.info("\n--- Step 5: GenMol NIM ---")
            genmol_result = await run_genmol(
                client,
                seed_smiles="Nc1ccncc1",  # 4-aminopyridine
                num_molecules=100,
                output_dir=output_dir,
            )

        # Step 6: Upload to platform
        logger.info("\n--- Step 6: Uploading results to platform ---")
        uploaded = await upload_results(client, diffdock_results, genmol_result)

    # Step 7: Save summary and print top hits
    summary = {
        "timestamp": run_timestamp,
        "compounds_count": len(compounds),
        "targets_count": len(TARGETS),
        "docking": {
            "total": len(diffdock_results),
            "successful": sum(1 for r in diffdock_results if r.get("status") == "success"),
            "errors": sum(1 for r in diffdock_results if r.get("status") == "error"),
            "skipped": args.skip_docking,
        },
        "genmol": {
            "status": genmol_result.get("status") if genmol_result else "skipped",
            "num_generated": genmol_result.get("num_generated", 0) if genmol_result else 0,
            "skipped": args.skip_genmol,
        },
        "uploaded": uploaded,
    }

    summary_path = output_dir / "batch_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info("Batch summary saved to %s", summary_path)

    # Print top-20 hits
    if diffdock_results:
        print_top_hits(diffdock_results, top_n=20)

    # GenMol summary
    if genmol_result:
        if genmol_result.get("status") == "success":
            logger.info(
                "GenMol: %d novel 4-AP analogs generated",
                genmol_result.get("num_generated", 0),
            )
        else:
            logger.warning("GenMol failed: %s", genmol_result.get("error", "unknown"))

    logger.info("NIM batch run complete. Results in %s", output_dir)

    has_errors = any(r.get("status") == "error" for r in diffdock_results)
    if genmol_result and genmol_result.get("status") == "error":
        has_errors = True

    return 0 if not has_errors else 0  # Exit 0 — partial failures are OK


def main():
    parser = argparse.ArgumentParser(
        description="NVIDIA NIM Batch Runner: DiffDock v2.2 + GenMol for SMA drug discovery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 run_nim_batch.py                           # Full run: 100 compounds, all targets
  python3 run_nim_batch.py --compounds 10            # Quick test with 10 compounds
  python3 run_nim_batch.py --skip-genmol             # Docking only, no molecule generation
  python3 run_nim_batch.py --skip-docking            # GenMol only, no docking
  python3 run_nim_batch.py --output-dir /tmp/nim     # Custom output directory

Environment variables:
  NVIDIA_API_KEY   NVIDIA NIM API bearer token (required)
  SMA_API          Platform API base URL (default: https://sma-research.info/api/v2)
  SMA_ADMIN_KEY    Admin key for uploading results to platform
        """,
    )
    parser.add_argument(
        "--compounds", type=int, default=100,
        help="Maximum number of compounds to dock (default: 100)",
    )
    parser.add_argument(
        "--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR),
        help=f"Output directory for results (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--skip-docking", action="store_true",
        help="Skip DiffDock docking stage",
    )
    parser.add_argument(
        "--skip-genmol", action="store_true",
        help="Skip GenMol molecule generation stage",
    )

    args = parser.parse_args()

    exit_code = asyncio.run(main_async(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
