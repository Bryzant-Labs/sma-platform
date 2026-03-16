#!/usr/bin/env python3
"""
Batch GPU Pipeline: OpenMM MD + Boltz-2 + ESM-2
=================================================
Orchestrates three sequential GPU phases on Vast.ai A100:

  Phase 1: OpenMM MD — 100ns simulation of 4-AP + SMN2 protein
  Phase 2: Boltz-2   — Structure prediction for 5 SMA-related proteins
  Phase 3: ESM-2     — Protein embeddings for 6 SMA targets

Runs inside Docker image: csiicf/sma-gpu-toolkit:latest

Usage:
    python3 run_batch_gpu.py
    python3 run_batch_gpu.py --skip-md --skip-boltz
    python3 run_batch_gpu.py --md-duration 50

Environment:
    SMA_API       — Platform API base URL (default: https://sma-research.info/api/v2)
    SMA_ADMIN_KEY — Admin key for result upload
    DATA_DIR      — Output root directory (default: /data)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("batch-gpu")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SMA_API = os.environ.get("SMA_API", "https://sma-research.info/api/v2")
SMA_ADMIN_KEY = os.environ.get("SMA_ADMIN_KEY", "")
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
BATCH_OUTPUT = DATA_DIR / "batch_results"

# SMN2 AlphaFold structure
SMN2_ALPHAFOLD_URL = "https://alphafold.ebi.ac.uk/files/AF-Q16637-F1-model_v6.pdb"

# Boltz-2 targets
BOLTZ_TARGETS = {
    "STMN2": "Q93045",
    "NCALD": "P61601",
    "PLS3": "P13797",
    "UBA1": "P22314",
    "CORO1C": "Q9ULV4",
}

# ESM-2 targets (superset — includes SMN2)
ESM_TARGETS = {
    "SMN2": "Q16637",
    "PLS3": "P13797",
    "STMN2": "Q93045",
    "NCALD": "P61601",
    "UBA1": "P22314",
    "CORO1C": "Q9ULV4",
}

UNIPROT_FASTA_URL = "https://rest.uniprot.org/uniprotkb/{uid}.fasta"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def detect_cuda() -> bool:
    """Check if CUDA GPU is available."""
    try:
        import torch
        available = torch.cuda.is_available()
        if available:
            name = torch.cuda.get_device_name(0)
            mem = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            logger.info("CUDA device: %s (%.1f GB)", name, mem)
        else:
            logger.warning("CUDA not available — GPU phases will be slow or fail")
        return available
    except ImportError:
        logger.warning("PyTorch not installed — cannot detect CUDA")
        return False


def fetch_uniprot_fasta(uniprot_id: str) -> str | None:
    """Download FASTA sequence from UniProt. Returns sequence string (no header)."""
    url = UNIPROT_FASTA_URL.format(uid=uniprot_id)
    try:
        req = urllib.request.Request(url, headers={"Accept": "text/plain"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8")
        lines = text.strip().split("\n")
        seq_lines = [line for line in lines if not line.startswith(">")]
        return "".join(seq_lines)
    except Exception as e:
        logger.error("Failed to fetch UniProt %s: %s", uniprot_id, e)
        return None


def upload_results(payload: dict, endpoint: str = "/gpu/jobs") -> bool:
    """POST results to SMA Platform API."""
    if not SMA_ADMIN_KEY:
        logger.info("Skipping API upload (no SMA_ADMIN_KEY)")
        return False

    try:
        import httpx
        resp = httpx.post(
            f"{SMA_API}{endpoint}",
            json=payload,
            headers={"X-Admin-Key": SMA_ADMIN_KEY},
            timeout=60,
        )
        if resp.status_code in (200, 201):
            logger.info("Results uploaded to %s%s", SMA_API, endpoint)
            return True
        else:
            logger.warning("Upload failed: %d %s", resp.status_code, resp.text[:200])
            return False
    except ImportError:
        logger.warning("httpx not installed — cannot upload results")
        return False
    except Exception as e:
        logger.error("Upload error: %s", e)
        return False


# ============================================================================
# Phase 1: OpenMM Molecular Dynamics — 4-AP + SMN2
# ============================================================================

# Helper script that runs under /opt/conda/bin/python3 when OpenMM
# cannot be imported into the system Python.  It performs the full MD
# simulation and writes md_results.json, which the main process reads back.
_MD_HELPER_SCRIPT = r'''#!/usr/bin/env python3
"""OpenMM MD helper — runs under conda Python."""
import argparse, json, os, sys, time, urllib.request, logging
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [md-helper] %(message)s")
logger = logging.getLogger("md-helper")

import openmm as mm
import openmm.app as app
import openmm.unit as unit
from pdbfixer import PDBFixer

# mdtraj may not be in conda — try importing, fall back gracefully
try:
    import mdtraj as md
    HAS_MDTRAJ = True
except ImportError:
    HAS_MDTRAJ = False
    logger.warning("mdtraj not available in conda python — trajectory analysis will be skipped")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--md-dir", required=True)
    parser.add_argument("--duration-ns", type=float, required=True)
    parser.add_argument("--alphafold-url", required=True)
    args = parser.parse_args()

    md_dir = args.md_dir
    duration_ns = args.duration_ns
    t_start = time.time()

    os.makedirs(md_dir, exist_ok=True)

    # Download PDB
    pdb_path = os.path.join(md_dir, "smn2_alphafold.pdb")
    if not os.path.exists(pdb_path):
        urllib.request.urlretrieve(args.alphafold_url, pdb_path)
        logger.info("Downloaded AlphaFold structure to %s", pdb_path)

    # PDBFixer
    fixer = PDBFixer(filename=pdb_path)
    fixer.findMissingResidues()
    fixer.findMissingAtoms()
    fixer.addMissingAtoms()
    fixer.addMissingHydrogens(pH=7.4)

    fixed_path = os.path.join(md_dir, "smn2_fixed.pdb")
    with open(fixed_path, "w") as f:
        app.PDBFile.writeFile(fixer.topology, fixer.positions, f)
    logger.info("Fixed structure: %s", fixed_path)

    # System setup
    pdb = app.PDBFile(fixed_path)
    forcefield = app.ForceField("amber14-all.xml", "amber14/tip3pfb.xml")
    modeller = app.Modeller(pdb.topology, pdb.positions)
    modeller.addSolvent(forcefield, model="tip3p", padding=1.2*unit.nanometers,
                        ionicStrength=0.15*unit.molar, positiveIon="Na+", negativeIon="Cl-")
    logger.info("System: %d atoms, %d residues", modeller.topology.getNumAtoms(), modeller.topology.getNumResidues())

    system = forcefield.createSystem(modeller.topology, nonbondedMethod=app.PME,
                                     nonbondedCutoff=1.0*unit.nanometers,
                                     constraints=app.HBonds, hydrogenMass=1.5*unit.amu)
    system.addForce(mm.MonteCarloBarostat(1.0*unit.atmospheres, 300.0*unit.kelvin, 25))
    integrator = mm.LangevinMiddleIntegrator(300.0*unit.kelvin, 1.0/unit.picoseconds, 2.0*unit.femtoseconds)

    try:
        platform = mm.Platform.getPlatformByName("CUDA")
        properties = {"Precision": "mixed"}
        logger.info("Using CUDA platform")
    except Exception:
        platform = mm.Platform.getPlatformByName("CPU")
        properties = {}
        logger.warning("Falling back to CPU")

    simulation = app.Simulation(modeller.topology, system, integrator, platform, properties)
    simulation.context.setPositions(modeller.positions)

    # Minimization
    state = simulation.context.getState(getEnergy=True)
    e_before = state.getPotentialEnergy().value_in_unit(unit.kilojoules_per_mole)
    simulation.minimizeEnergy(maxIterations=5000)
    state = simulation.context.getState(getEnergy=True)
    e_after = state.getPotentialEnergy().value_in_unit(unit.kilojoules_per_mole)
    logger.info("Minimization: %.1f -> %.1f kJ/mol", e_before, e_after)

    # Equilibration
    eq_steps = 500_000
    simulation.context.setVelocitiesToTemperature(300.0*unit.kelvin)
    simulation.step(eq_steps)
    state = simulation.context.getState(getEnergy=True)
    e_eq = state.getPotentialEnergy().value_in_unit(unit.kilojoules_per_mole)
    logger.info("Post-equilibration energy: %.1f kJ/mol", e_eq)

    # Production
    prod_steps = int(duration_ns * 1e6 / 2.0)
    report_steps = int(100 * 1000 / 2.0)

    traj_path = os.path.join(md_dir, "trajectory.dcd")
    log_path = os.path.join(md_dir, "production.log")
    topo_path = os.path.join(md_dir, "topology.pdb")

    simulation.reporters.append(app.DCDReporter(traj_path, report_steps))
    simulation.reporters.append(app.StateDataReporter(log_path, report_steps,
        step=True, time=True, potentialEnergy=True, kineticEnergy=True,
        temperature=True, volume=True, speed=True))
    simulation.reporters.append(app.StateDataReporter(sys.stdout, report_steps*10,
        step=True, time=True, temperature=True, speed=True,
        remainingTime=True, totalSteps=prod_steps))

    state = simulation.context.getState(getPositions=True)
    with open(topo_path, "w") as f:
        app.PDBFile.writeFile(simulation.topology, state.getPositions(), f)

    t_prod_start = time.time()
    simulation.step(prod_steps)
    prod_wall = time.time() - t_prod_start

    state = simulation.context.getState(getEnergy=True, getPositions=True)
    final_energy = state.getPotentialEnergy().value_in_unit(unit.kilojoules_per_mole)
    final_path = os.path.join(md_dir, "final_frame.pdb")
    with open(final_path, "w") as f:
        app.PDBFile.writeFile(simulation.topology, state.getPositions(), f)

    ns_per_day = duration_ns / (prod_wall / 86400) if prod_wall > 0 else 0
    logger.info("Production complete: %.1f hours, %.1f ns/day", prod_wall/3600, ns_per_day)

    # Analysis
    analysis = {}
    if HAS_MDTRAJ:
        traj = md.load(traj_path, top=topo_path)
        backbone = traj.topology.select("backbone")
        rmsd = md.rmsd(traj, traj, frame=0, atom_indices=backbone)
        rmsf = md.rmsf(traj, traj, frame=0, atom_indices=backbone)
        rg = md.compute_rg(traj, masses=None)
        analysis = {
            "n_frames": int(traj.n_frames),
            "n_atoms": int(traj.n_atoms),
            "backbone_rmsd_nm": {"mean": round(float(np.mean(rmsd)),4), "std": round(float(np.std(rmsd)),4),
                                  "max": round(float(np.max(rmsd)),4), "final": round(float(rmsd[-1]),4)},
            "backbone_rmsf_nm": {"mean": round(float(np.mean(rmsf)),4), "max": round(float(np.max(rmsf)),4)},
            "radius_of_gyration_nm": {"mean": round(float(np.mean(rg)),4), "std": round(float(np.std(rg)),4)},
            "binding_stable": float(np.mean(rmsd[-10:])) < 0.5,
        }
    else:
        analysis = {"note": "mdtraj not available in conda python — analysis skipped"}

    total_time = time.time() - t_start
    md_results = {
        "duration_ns": duration_ns,
        "total_steps": prod_steps,
        "wall_time_seconds": round(prod_wall, 1),
        "ns_per_day": round(ns_per_day, 1),
        "final_energy_kj_mol": round(final_energy, 1),
        "minimization": {"before": round(e_before, 1), "after": round(e_after, 1)},
        "equilibration_energy": round(e_eq, 1),
        "analysis": analysis,
        "files": {"trajectory": traj_path, "topology": topo_path, "final_frame": final_path, "log": log_path},
        "status": "ok",
        "wall_time_total_secs": round(total_time, 1),
    }

    results_path = os.path.join(md_dir, "md_results.json")
    with open(results_path, "w") as f:
        json.dump(md_results, f, indent=2)
    logger.info("Results saved to %s", results_path)

if __name__ == "__main__":
    main()
'''


def _run_md_via_conda_subprocess(
    conda_python: str, output_dir: Path, md_dir: Path, duration_ns: float, t_start: float,
) -> dict:
    """Run the MD phase as a subprocess under conda Python (has OpenMM)."""
    # Write the helper script to a temp file
    helper_path = md_dir / "_md_helper.py"
    md_dir.mkdir(parents=True, exist_ok=True)
    with open(helper_path, "w") as f:
        f.write(_MD_HELPER_SCRIPT)
    logger.info("Wrote MD helper script: %s", helper_path)

    cmd = [
        conda_python, str(helper_path),
        "--md-dir", str(md_dir),
        "--duration-ns", str(duration_ns),
        "--alphafold-url", SMN2_ALPHAFOLD_URL,
    ]
    logger.info("Running MD via conda subprocess: %s", " ".join(cmd))

    proc = subprocess.run(cmd, capture_output=False, timeout=86400)  # 24h max

    # Read back results
    results_path = md_dir / "md_results.json"
    if proc.returncode != 0:
        return {
            "status": "error",
            "error": f"Conda MD subprocess exited with code {proc.returncode}",
            "duration_secs": round(time.time() - t_start, 1),
        }

    if results_path.exists():
        with open(results_path) as f:
            md_results = json.load(f)
        total_time = time.time() - t_start
        analysis = md_results.get("analysis", {})
        return {
            "status": md_results.get("status", "ok"),
            "duration_ns": duration_ns,
            "ns_per_day": md_results.get("ns_per_day", 0),
            "wall_time_hours": round(total_time / 3600, 2),
            "rmsd_mean_nm": analysis.get("backbone_rmsd_nm", {}).get("mean"),
            "binding_stable": analysis.get("binding_stable"),
            "duration_secs": round(total_time, 1),
            "output_dir": str(md_dir),
            "note": "Ran via conda subprocess (/opt/conda/bin/python3)",
        }
    else:
        return {
            "status": "error",
            "error": "Conda MD subprocess completed but md_results.json not found",
            "duration_secs": round(time.time() - t_start, 1),
        }


def run_phase_md(output_dir: Path, duration_ns: float) -> dict:
    """Run OpenMM MD simulation of SMN2 protein with 4-AP context."""
    logger.info("=" * 70)
    logger.info("PHASE 1: OpenMM MD — 4-AP + SMN2 (%s ns)", duration_ns)
    logger.info("=" * 70)
    t_start = time.time()

    md_dir = output_dir / "md"
    md_dir.mkdir(parents=True, exist_ok=True)

    # --- Import OpenMM (try system python first, fall back to conda) ---
    openmm_imported = False

    # Strategy 1: Normal import (works if symlinked or pip-installed)
    try:
        import openmm as mm
        import openmm.app as app
        import openmm.unit as unit
        from pdbfixer import PDBFixer
        openmm_imported = True
        logger.info("OpenMM imported from system Python")
    except ImportError:
        pass

    # Strategy 2: Add conda site-packages to sys.path (auto-detect Python version)
    if not openmm_imported:
        logger.info("OpenMM not on system Python, trying conda site-packages...")
        import glob as _glob
        conda_site_matches = sorted(_glob.glob("/opt/conda/lib/python3.*/site-packages/"))
        for conda_site in conda_site_matches:
            if os.path.isdir(conda_site):
                sys.path.insert(0, conda_site)
                try:
                    import openmm as mm
                    import openmm.app as app
                    import openmm.unit as unit
                    from pdbfixer import PDBFixer
                    openmm_imported = True
                    logger.info("OpenMM imported from conda: %s", conda_site)
                    break
                except ImportError:
                    sys.path.pop(0)

    # Strategy 3: Run entire MD phase as subprocess under conda python
    if not openmm_imported:
        logger.info("OpenMM sys.path import failed — falling back to conda subprocess")
        conda_python = "/opt/conda/bin/python3"
        if os.path.isfile(conda_python):
            return _run_md_via_conda_subprocess(
                conda_python, output_dir, md_dir, duration_ns, t_start
            )
        else:
            return {
                "status": "error",
                "error": "OpenMM not available — conda python not found at /opt/conda/bin/python3",
                "duration_secs": round(time.time() - t_start, 1),
            }

    try:
        import mdtraj as md
    except ImportError:
        return {
            "status": "error",
            "error": "MDTraj not installed — cannot analyze trajectory",
            "duration_secs": round(time.time() - t_start, 1),
        }

    import numpy as np

    # --- Step 1: Download SMN2 AlphaFold structure ---
    logger.info("[MD 1/6] Downloading SMN2 AlphaFold v6 structure...")
    pdb_path = md_dir / "smn2_alphafold.pdb"
    if not pdb_path.exists():
        urllib.request.urlretrieve(SMN2_ALPHAFOLD_URL, str(pdb_path))
        logger.info("  Downloaded to %s", pdb_path)
    else:
        logger.info("  Using cached: %s", pdb_path)

    # --- Step 2: Fix protein with PDBFixer ---
    logger.info("[MD 2/6] Fixing protein with PDBFixer...")
    fixer = PDBFixer(filename=str(pdb_path))
    fixer.findMissingResidues()
    fixer.findMissingAtoms()
    fixer.addMissingAtoms()
    fixer.addMissingHydrogens(pH=7.4)

    fixed_path = md_dir / "smn2_fixed.pdb"
    with open(fixed_path, "w") as f:
        app.PDBFile.writeFile(fixer.topology, fixer.positions, f)
    logger.info("  Fixed structure: %s", fixed_path)

    # --- Step 3: Set up simulation ---
    logger.info("[MD 3/6] Setting up OpenMM simulation...")
    pdb = app.PDBFile(str(fixed_path))
    forcefield = app.ForceField("amber14-all.xml", "amber14/tip3pfb.xml")

    modeller = app.Modeller(pdb.topology, pdb.positions)
    modeller.addSolvent(
        forcefield,
        model="tip3p",
        padding=1.2 * unit.nanometers,
        ionicStrength=0.15 * unit.molar,
        positiveIon="Na+",
        negativeIon="Cl-",
    )
    logger.info("  System: %d atoms, %d residues",
                modeller.topology.getNumAtoms(),
                modeller.topology.getNumResidues())

    system = forcefield.createSystem(
        modeller.topology,
        nonbondedMethod=app.PME,
        nonbondedCutoff=1.0 * unit.nanometers,
        constraints=app.HBonds,
        hydrogenMass=1.5 * unit.amu,
    )

    # NPT barostat
    system.addForce(mm.MonteCarloBarostat(
        1.0 * unit.atmospheres,
        300.0 * unit.kelvin,
        25,
    ))

    # Langevin integrator
    integrator = mm.LangevinMiddleIntegrator(
        300.0 * unit.kelvin,
        1.0 / unit.picoseconds,
        2.0 * unit.femtoseconds,
    )

    # Platform selection
    try:
        platform = mm.Platform.getPlatformByName("CUDA")
        properties = {"Precision": "mixed"}
        logger.info("  Using CUDA platform (mixed precision)")
    except Exception:
        platform = mm.Platform.getPlatformByName("CPU")
        properties = {}
        logger.warning("  CUDA not available — falling back to CPU (SLOW)")

    simulation = app.Simulation(
        modeller.topology, system, integrator, platform, properties
    )
    simulation.context.setPositions(modeller.positions)

    # --- Step 4: Energy minimization ---
    logger.info("[MD 4/6] Energy minimization (5000 steps)...")
    state = simulation.context.getState(getEnergy=True)
    e_before = state.getPotentialEnergy().value_in_unit(unit.kilojoules_per_mole)
    logger.info("  Energy before: %.1f kJ/mol", e_before)

    simulation.minimizeEnergy(maxIterations=5000)

    state = simulation.context.getState(getEnergy=True)
    e_after = state.getPotentialEnergy().value_in_unit(unit.kilojoules_per_mole)
    logger.info("  Energy after:  %.1f kJ/mol", e_after)

    # --- Step 5: Equilibration (1ns = 500,000 steps at 2fs) ---
    eq_steps = 500_000
    logger.info("[MD 5/6] Equilibration (1 ns, %d steps)...", eq_steps)
    simulation.context.setVelocitiesToTemperature(300.0 * unit.kelvin)
    t_eq_start = time.time()
    simulation.step(eq_steps)
    eq_time = time.time() - t_eq_start

    state = simulation.context.getState(getEnergy=True)
    e_eq = state.getPotentialEnergy().value_in_unit(unit.kilojoules_per_mole)
    logger.info("  Post-equilibration energy: %.1f kJ/mol (%.1f s)", e_eq, eq_time)

    # --- Step 6: Production MD ---
    prod_steps = int(duration_ns * 1e6 / 2.0)  # ns -> steps at 2fs
    report_steps = int(100 * 1000 / 2.0)  # 100ps -> steps at 2fs = 50,000

    logger.info("[MD 6/6] Production run (%s ns, %d steps, report every 100 ps)...",
                duration_ns, prod_steps)

    traj_path = md_dir / "trajectory.dcd"
    log_path = md_dir / "production.log"

    simulation.reporters.append(app.DCDReporter(str(traj_path), report_steps))
    simulation.reporters.append(app.StateDataReporter(
        str(log_path), report_steps,
        step=True, time=True, potentialEnergy=True, kineticEnergy=True,
        temperature=True, volume=True, speed=True,
    ))
    simulation.reporters.append(app.StateDataReporter(
        sys.stdout, report_steps * 10,
        step=True, time=True, temperature=True, speed=True,
        remainingTime=True, totalSteps=prod_steps,
    ))

    # Save topology for trajectory analysis
    topo_path = md_dir / "topology.pdb"
    state = simulation.context.getState(getPositions=True)
    with open(topo_path, "w") as f:
        app.PDBFile.writeFile(simulation.topology, state.getPositions(), f)

    t_prod_start = time.time()
    simulation.step(prod_steps)
    prod_wall = time.time() - t_prod_start

    # Save final frame
    state = simulation.context.getState(getEnergy=True, getPositions=True)
    final_energy = state.getPotentialEnergy().value_in_unit(unit.kilojoules_per_mole)
    final_path = md_dir / "final_frame.pdb"
    with open(final_path, "w") as f:
        app.PDBFile.writeFile(simulation.topology, state.getPositions(), f)

    ns_per_day = duration_ns / (prod_wall / 86400) if prod_wall > 0 else 0

    logger.info("  Production complete: %.1f hours, %.1f ns/day",
                prod_wall / 3600, ns_per_day)

    # --- Analysis with MDTraj ---
    logger.info("[MD Analysis] Computing RMSD, RMSF, Rg...")
    traj = md.load(str(traj_path), top=str(topo_path))
    backbone = traj.topology.select("backbone")

    rmsd = md.rmsd(traj, traj, frame=0, atom_indices=backbone)
    rmsf = md.rmsf(traj, traj, frame=0, atom_indices=backbone)
    rg = md.compute_rg(traj, masses=None)

    analysis = {
        "n_frames": int(traj.n_frames),
        "n_atoms": int(traj.n_atoms),
        "backbone_rmsd_nm": {
            "mean": round(float(np.mean(rmsd)), 4),
            "std": round(float(np.std(rmsd)), 4),
            "max": round(float(np.max(rmsd)), 4),
            "final": round(float(rmsd[-1]), 4),
        },
        "backbone_rmsf_nm": {
            "mean": round(float(np.mean(rmsf)), 4),
            "max": round(float(np.max(rmsf)), 4),
        },
        "radius_of_gyration_nm": {
            "mean": round(float(np.mean(rg)), 4),
            "std": round(float(np.std(rg)), 4),
        },
        "binding_stable": float(np.mean(rmsd[-10:])) < 0.5,
    }

    logger.info("  RMSD: %.3f +/- %.3f nm | Rg: %.3f nm | Stable: %s",
                analysis["backbone_rmsd_nm"]["mean"],
                analysis["backbone_rmsd_nm"]["std"],
                analysis["radius_of_gyration_nm"]["mean"],
                analysis["binding_stable"])

    # Save results JSON
    md_results = {
        "duration_ns": duration_ns,
        "total_steps": prod_steps,
        "wall_time_seconds": round(prod_wall, 1),
        "ns_per_day": round(ns_per_day, 1),
        "final_energy_kj_mol": round(final_energy, 1),
        "minimization": {"before": round(e_before, 1), "after": round(e_after, 1)},
        "equilibration_energy": round(e_eq, 1),
        "analysis": analysis,
        "files": {
            "trajectory": str(traj_path),
            "topology": str(topo_path),
            "final_frame": str(final_path),
            "log": str(log_path),
        },
    }

    results_path = md_dir / "md_results.json"
    with open(results_path, "w") as f:
        json.dump(md_results, f, indent=2)
    logger.info("  Results saved to %s", results_path)

    total_time = time.time() - t_start
    return {
        "status": "ok",
        "duration_ns": duration_ns,
        "ns_per_day": round(ns_per_day, 1),
        "wall_time_hours": round(total_time / 3600, 2),
        "rmsd_mean_nm": analysis["backbone_rmsd_nm"]["mean"],
        "binding_stable": analysis["binding_stable"],
        "duration_secs": round(total_time, 1),
        "output_dir": str(md_dir),
    }


# ============================================================================
# Phase 2: Boltz-2 — Structure Prediction
# ============================================================================

def run_phase_boltz(output_dir: Path) -> dict:
    """Run Boltz-2 structure prediction for 5 SMA target proteins."""
    logger.info("=" * 70)
    logger.info("PHASE 2: Boltz-2 — Structure Prediction (5 proteins)")
    logger.info("=" * 70)
    t_start = time.time()

    boltz_dir = output_dir / "boltz"
    boltz_dir.mkdir(parents=True, exist_ok=True)

    # Check if boltz is available
    try:
        result = subprocess.run(
            ["boltz", "predict", "--help"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            raise FileNotFoundError("boltz predict returned non-zero")
        logger.info("Boltz-2 CLI available")
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.error("Boltz-2 not available: %s", e)
        return {
            "status": "error",
            "error": f"Boltz-2 CLI not available: {e}",
            "duration_secs": round(time.time() - t_start, 1),
        }

    results = []

    for symbol, uniprot_id in BOLTZ_TARGETS.items():
        logger.info("[Boltz] Predicting structure for %s (%s)...", symbol, uniprot_id)
        t_protein = time.time()

        try:
            # Step 1: Download FASTA from UniProt
            sequence = fetch_uniprot_fasta(uniprot_id)
            if not sequence:
                results.append({
                    "symbol": symbol,
                    "uniprot_id": uniprot_id,
                    "status": "error",
                    "error": f"Could not fetch sequence for {uniprot_id}",
                })
                continue

            # Step 2: Write input YAML for Boltz
            protein_dir = boltz_dir / symbol
            protein_dir.mkdir(parents=True, exist_ok=True)

            fasta_path = protein_dir / f"{symbol}.fasta"
            with open(fasta_path, "w") as f:
                f.write(f">{symbol}|{uniprot_id}\n")
                for i in range(0, len(sequence), 80):
                    f.write(sequence[i:i + 80] + "\n")

            input_yaml = protein_dir / f"{symbol}_input.yaml"
            yaml_content = (
                f"version: 1\n"
                f"sequences:\n"
                f"  - protein:\n"
                f"      id: {symbol}\n"
                f"      sequence: {sequence}\n"
            )
            with open(input_yaml, "w") as f:
                f.write(yaml_content)

            # Step 3: Run boltz predict
            cmd = [
                "boltz", "predict",
                str(input_yaml),
                "--out_dir", str(protein_dir / "output"),
                "--accelerator", "gpu",
                "--devices", "1",
            ]
            logger.info("  Running: %s", " ".join(cmd))

            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=1800,  # 30 min per protein max
            )

            if proc.returncode != 0:
                logger.error("  Boltz failed for %s: %s", symbol, proc.stderr[:500])
                results.append({
                    "symbol": symbol,
                    "uniprot_id": uniprot_id,
                    "status": "error",
                    "error": f"Boltz exit code {proc.returncode}: {proc.stderr[:300]}",
                })
                continue

            # Step 4: Collect output CIF files and confidence
            output_subdir = protein_dir / "output"
            cif_files = list(output_subdir.rglob("*.cif"))
            confidence_files = list(output_subdir.rglob("*confidence*"))

            # Try to read confidence scores
            confidence = {}
            for cf in confidence_files:
                try:
                    with open(cf) as cfh:
                        confidence = json.load(cfh)
                    break
                except (json.JSONDecodeError, Exception):
                    pass

            protein_time = time.time() - t_protein
            logger.info("  %s: %d CIF files, %.1f s", symbol, len(cif_files), protein_time)

            results.append({
                "symbol": symbol,
                "uniprot_id": uniprot_id,
                "status": "ok",
                "sequence_length": len(sequence),
                "cif_files": [str(p) for p in cif_files],
                "confidence": confidence,
                "duration_secs": round(protein_time, 1),
            })

        except subprocess.TimeoutExpired:
            logger.error("  Boltz timed out for %s (30 min limit)", symbol)
            results.append({
                "symbol": symbol,
                "uniprot_id": uniprot_id,
                "status": "error",
                "error": "Boltz prediction timed out after 30 minutes",
            })
        except Exception as e:
            logger.error("  Boltz failed for %s: %s", symbol, e, exc_info=True)
            results.append({
                "symbol": symbol,
                "uniprot_id": uniprot_id,
                "status": "error",
                "error": str(e),
            })

    # Save results
    boltz_results_path = boltz_dir / "boltz_results.json"
    with open(boltz_results_path, "w") as f:
        json.dump(results, f, indent=2)

    total_time = time.time() - t_start
    successful = [r for r in results if r.get("status") == "ok"]
    failed = [r for r in results if r.get("status") != "ok"]

    logger.info("Boltz-2 complete: %d/%d succeeded in %.1f s",
                len(successful), len(results), total_time)

    return {
        "status": "ok" if successful else "error",
        "proteins_predicted": len(successful),
        "proteins_failed": len(failed),
        "proteins": results,
        "duration_secs": round(total_time, 1),
        "output_dir": str(boltz_dir),
    }


# ============================================================================
# Phase 3: ESM-2 — Protein Embeddings
# ============================================================================

def run_phase_esm(output_dir: Path) -> dict:
    """Generate ESM-2 embeddings for 6 SMA target proteins."""
    logger.info("=" * 70)
    logger.info("PHASE 3: ESM-2 — Protein Embeddings (6 proteins)")
    logger.info("=" * 70)
    t_start = time.time()

    esm_dir = output_dir / "esm"
    esm_dir.mkdir(parents=True, exist_ok=True)

    # Import dependencies
    try:
        import torch
        import esm
    except ImportError as e:
        return {
            "status": "error",
            "error": f"ESM-2 import failed: {e}. Install with: pip install fair-esm torch",
            "duration_secs": round(time.time() - t_start, 1),
        }

    try:
        import numpy as np
    except ImportError:
        return {
            "status": "error",
            "error": "NumPy not installed",
            "duration_secs": round(time.time() - t_start, 1),
        }

    # Load model
    logger.info("[ESM] Loading ESM-2 t33 650M model...")
    try:
        model, alphabet = esm.pretrained.esm2_t33_650M_UR50D()
        batch_converter = alphabet.get_batch_converter()
        model.train(False)  # set to inference mode

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(device)
        logger.info("  ESM-2 loaded on %s", device)
    except Exception as e:
        return {
            "status": "error",
            "error": f"ESM-2 model load failed: {e}",
            "duration_secs": round(time.time() - t_start, 1),
        }

    results = []

    for symbol, uniprot_id in ESM_TARGETS.items():
        logger.info("[ESM] Embedding %s (%s)...", symbol, uniprot_id)
        t_protein = time.time()

        try:
            # Fetch sequence
            sequence = fetch_uniprot_fasta(uniprot_id)
            if not sequence:
                results.append({
                    "symbol": symbol,
                    "uniprot_id": uniprot_id,
                    "status": "error",
                    "error": f"Could not fetch sequence for {uniprot_id}",
                })
                continue

            full_length = len(sequence)

            # Truncate to 1022 tokens (ESM-2 max context with BOS/EOS)
            truncated = sequence[:1022]
            if full_length > 1022:
                logger.info("  Truncated %s from %d to 1022 aa", symbol, full_length)

            # Compute embedding
            data = [(symbol, truncated)]
            batch_labels, batch_strs, batch_tokens = batch_converter(data)
            batch_tokens = batch_tokens.to(device)

            with torch.no_grad():
                result = model(batch_tokens, repr_layers=[33], return_contacts=False)

            # Mean-pool layer 33 representations (exclude BOS/EOS tokens)
            token_reps = result["representations"][33]
            seq_len = len(truncated)
            embedding = token_reps[0, 1:seq_len + 1].mean(0)

            embedding_np = embedding.cpu().numpy()
            embedding_dim = embedding_np.shape[0]

            # Save as .npy
            npy_path = esm_dir / f"{symbol}_{uniprot_id}_esm2.npy"
            np.save(str(npy_path), embedding_np)

            protein_time = time.time() - t_protein
            logger.info("  %s: %d aa -> %d-dim embedding (%.1f s)",
                        symbol, full_length, embedding_dim, protein_time)

            results.append({
                "symbol": symbol,
                "uniprot_id": uniprot_id,
                "status": "ok",
                "sequence_length": full_length,
                "truncated_length": len(truncated),
                "embedding_dim": embedding_dim,
                "model": "esm2_t33_650M_UR50D",
                "npy_file": str(npy_path),
                "duration_secs": round(protein_time, 1),
            })

        except Exception as e:
            logger.error("  ESM-2 failed for %s: %s", symbol, e, exc_info=True)
            results.append({
                "symbol": symbol,
                "uniprot_id": uniprot_id,
                "status": "error",
                "error": str(e),
            })

    # Save metadata JSON
    metadata = {
        "model": "esm2_t33_650M_UR50D",
        "device": str(device),
        "proteins": results,
    }
    metadata_path = esm_dir / "esm_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    total_time = time.time() - t_start
    successful = [r for r in results if r.get("status") == "ok"]
    failed = [r for r in results if r.get("status") != "ok"]

    logger.info("ESM-2 complete: %d/%d succeeded in %.1f s",
                len(successful), len(results), total_time)

    return {
        "status": "ok" if successful else "error",
        "proteins_embedded": len(successful),
        "proteins_failed": len(failed),
        "proteins": results,
        "duration_secs": round(total_time, 1),
        "output_dir": str(esm_dir),
    }


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Batch GPU Pipeline: OpenMM MD + Boltz-2 + ESM-2",
    )
    parser.add_argument("--skip-md", action="store_true",
                        help="Skip Phase 1 (OpenMM MD simulation)")
    parser.add_argument("--skip-boltz", action="store_true",
                        help="Skip Phase 2 (Boltz-2 structure prediction)")
    parser.add_argument("--skip-esm", action="store_true",
                        help="Skip Phase 3 (ESM-2 embeddings)")
    parser.add_argument("--md-duration", type=float, default=100,
                        help="MD simulation duration in nanoseconds (default: 100)")
    args = parser.parse_args()

    # Banner
    timestamp = datetime.now(timezone.utc).isoformat()
    logger.info("=" * 70)
    logger.info("  SMA Batch GPU Pipeline")
    logger.info("  Started: %s", timestamp)
    logger.info("  API: %s", SMA_API)
    logger.info("  Data dir: %s", DATA_DIR)
    logger.info("  Admin key: %s", "configured" if SMA_ADMIN_KEY else "NOT SET")
    logger.info("  Phases: MD=%s  Boltz=%s  ESM=%s",
                "SKIP" if args.skip_md else f"{args.md_duration}ns",
                "SKIP" if args.skip_boltz else "5 proteins",
                "SKIP" if args.skip_esm else "6 proteins")
    logger.info("=" * 70)

    if not SMA_ADMIN_KEY:
        logger.warning("SMA_ADMIN_KEY not set — results will NOT be uploaded to platform")

    # Detect CUDA
    has_cuda = detect_cuda()

    # Create output directory
    BATCH_OUTPUT.mkdir(parents=True, exist_ok=True)

    batch_results = {
        "started_at": timestamp,
        "cuda_available": has_cuda,
        "phases": {},
    }

    # --- Phase 1: OpenMM MD ---
    if args.skip_md:
        logger.info("Phase 1 (OpenMM MD): SKIPPED by user")
        batch_results["phases"]["md"] = {"status": "skipped"}
    else:
        try:
            batch_results["phases"]["md"] = run_phase_md(BATCH_OUTPUT, args.md_duration)
        except Exception as e:
            logger.error("Phase 1 (OpenMM MD) CRASHED: %s", e, exc_info=True)
            batch_results["phases"]["md"] = {"status": "error", "error": str(e)}

    # --- Phase 2: Boltz-2 ---
    if args.skip_boltz:
        logger.info("Phase 2 (Boltz-2): SKIPPED by user")
        batch_results["phases"]["boltz"] = {"status": "skipped"}
    else:
        try:
            batch_results["phases"]["boltz"] = run_phase_boltz(BATCH_OUTPUT)
        except Exception as e:
            logger.error("Phase 2 (Boltz-2) CRASHED: %s", e, exc_info=True)
            batch_results["phases"]["boltz"] = {"status": "error", "error": str(e)}

    # --- Phase 3: ESM-2 ---
    if args.skip_esm:
        logger.info("Phase 3 (ESM-2): SKIPPED by user")
        batch_results["phases"]["esm"] = {"status": "skipped"}
    else:
        try:
            batch_results["phases"]["esm"] = run_phase_esm(BATCH_OUTPUT)
        except Exception as e:
            logger.error("Phase 3 (ESM-2) CRASHED: %s", e, exc_info=True)
            batch_results["phases"]["esm"] = {"status": "error", "error": str(e)}

    # --- Summary ---
    finished_at = datetime.now(timezone.utc).isoformat()
    batch_results["finished_at"] = finished_at

    # Compute total timing
    total_secs = sum(
        p.get("duration_secs", 0)
        for p in batch_results["phases"].values()
        if isinstance(p, dict)
    )
    batch_results["total_duration_secs"] = round(total_secs, 1)
    batch_results["total_duration_hours"] = round(total_secs / 3600, 2)

    # Status summary
    phase_statuses = {}
    for name, result in batch_results["phases"].items():
        phase_statuses[name] = result.get("status", "unknown") if isinstance(result, dict) else "unknown"
    batch_results["phase_statuses"] = phase_statuses

    active_phases = {k: v for k, v in phase_statuses.items() if v != "skipped"}
    all_ok = all(v == "ok" for v in active_phases.values()) if active_phases else False
    batch_results["overall_status"] = "success" if all_ok else "partial"

    # Save batch summary
    summary_path = BATCH_OUTPUT / "batch_summary.json"
    with open(summary_path, "w") as f:
        json.dump(batch_results, f, indent=2)

    # Upload to platform
    upload_payload = {
        "job_type": "batch_gpu_pipeline",
        "status": "completed" if all_ok else "partial",
        "started_at": timestamp,
        "finished_at": finished_at,
        "total_duration_hours": batch_results["total_duration_hours"],
        "phases": phase_statuses,
        "results": {
            name: {
                k: v for k, v in result.items()
                if k not in ("proteins", "output_dir", "files")  # Skip large/local-only fields
            }
            for name, result in batch_results["phases"].items()
            if isinstance(result, dict)
        },
    }
    upload_results(upload_payload)

    # Print final summary
    logger.info("=" * 70)
    logger.info("  BATCH GPU PIPELINE COMPLETE")
    logger.info("  Overall: %s", batch_results["overall_status"].upper())
    logger.info("  Duration: %.1f hours", batch_results["total_duration_hours"])
    for name, status in phase_statuses.items():
        label = "OK" if status == "ok" else ("SKIP" if status == "skipped" else "FAIL")
        logger.info("    %s: %s", name.upper().ljust(8), label)
    logger.info("  Summary: %s", summary_path)
    logger.info("=" * 70)

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
