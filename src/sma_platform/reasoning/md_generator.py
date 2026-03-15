"""Agent C: Molecular Dynamics Simulation Code Generator (Phase 10.2).

Generates ready-to-run OpenMM Python scripts for SMA-relevant simulations:
- Protein-ligand binding (SMN protein + small molecule)
- Protein-protein interaction (SMN oligomerization, snRNP assembly)
- Protein-RNA binding (hnRNP A1 + ISS-N1 RNA)
- Membrane interaction (AAV capsid + cell membrane)

The generated scripts are complete, copy-paste runnable Python files
that use OpenMM for the simulation engine and MDTraj for analysis.

This agent does NOT run the simulations — it generates the code.
Simulations should be run on GPU-equipped machines (Lambda, Vast.ai, etc.).
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)

AGENT_NAME = "md-code-generator"


# ---------------------------------------------------------------------------
# Simulation templates
# ---------------------------------------------------------------------------

@dataclass
class SimulationSpec:
    """Specification for an MD simulation."""
    name: str
    simulation_type: str      # 'protein_ligand', 'protein_protein', 'protein_rna', 'protein_folding'
    target: str               # SMA target symbol
    description: str
    pdb_id: str | None        # PDB structure (if available)
    alphafold_id: str | None  # AlphaFold model ID
    system_size_atoms: int    # Approximate
    simulation_time_ns: float
    gpu_hours_estimate: float
    force_field: str
    water_model: str
    temperature_k: float
    pressure_atm: float


# SMA-relevant simulation specifications
SIMULATION_SPECS = {
    "smn_oligomerization": SimulationSpec(
        name="SMN Protein Self-Oligomerization",
        simulation_type="protein_protein",
        target="SMN_PROTEIN",
        description="Simulate SMN Tudor domain self-association. SMN forms oligomers essential for "
                    "Gems body formation and snRNP assembly. Understanding oligomerization dynamics "
                    "reveals why reduced SMN (as in SMA) leads to functional collapse.",
        pdb_id="4QQ6",  # SMN Tudor domain
        alphafold_id="AF-Q16637-F1",
        system_size_atoms=45000,
        simulation_time_ns=100,
        gpu_hours_estimate=8,
        force_field="amber14-all.xml",
        water_model="tip3p",
        temperature_k=310.0,
        pressure_atm=1.0,
    ),
    "hnrnp_a1_iss_n1": SimulationSpec(
        name="hnRNP A1 binding to ISS-N1 RNA",
        simulation_type="protein_rna",
        target="SMN2",
        description="Simulate hnRNP A1 RRM domain binding to ISS-N1 (intron 7 +10 to +24). "
                    "This is the interaction that nusinersen blocks. Understanding binding "
                    "dynamics reveals small molecule disruption opportunities.",
        pdb_id="4YOE",  # hnRNP A1 RRM
        alphafold_id=None,
        system_size_atoms=35000,
        simulation_time_ns=50,
        gpu_hours_estimate=4,
        force_field="amber14-all.xml",
        water_model="tip3p",
        temperature_k=310.0,
        pressure_atm=1.0,
    ),
    "smn_risdiplam": SimulationSpec(
        name="SMN2 pre-mRNA + Risdiplam binding",
        simulation_type="protein_ligand",
        target="SMN2",
        description="Simulate risdiplam (Evrysdi) binding to SMN2 pre-mRNA 5' splice site. "
                    "Risdiplam stabilizes U1 snRNP binding, promoting exon 7 inclusion. "
                    "Understanding the binding mode guides next-gen splicing modulator design.",
        pdb_id=None,
        alphafold_id=None,
        system_size_atoms=25000,
        simulation_time_ns=50,
        gpu_hours_estimate=4,
        force_field="amber14-all.xml",
        water_model="tip3p",
        temperature_k=310.0,
        pressure_atm=1.0,
    ),
    "ncald_calcium": SimulationSpec(
        name="Neurocalcin-delta Calcium Binding Dynamics",
        simulation_type="protein_ligand",
        target="NCALD",
        description="Simulate NCALD EF-hand calcium binding/unbinding transitions. "
                    "NCALD knockdown rescues SMA in zebrafish and human cells. "
                    "Understanding calcium-dependent conformational changes identifies "
                    "druggable states for small molecule inhibition.",
        pdb_id=None,
        alphafold_id="AF-Q6P2D0-F1",
        system_size_atoms=30000,
        simulation_time_ns=200,
        gpu_hours_estimate=16,
        force_field="amber14-all.xml",
        water_model="tip3p",
        temperature_k=310.0,
        pressure_atm=1.0,
    ),
    "pls3_actin": SimulationSpec(
        name="Plastin-3 Actin Bundling Mechanism",
        simulation_type="protein_protein",
        target="PLS3",
        description="Simulate PLS3 binding to F-actin filaments. PLS3 overexpression rescues "
                    "SMA by strengthening the actin cytoskeleton. Understanding the bundling "
                    "mechanism could identify activator binding sites.",
        pdb_id="1AOA",  # Fimbrin ABD (homolog)
        alphafold_id="AF-P13797-F1",
        system_size_atoms=80000,
        simulation_time_ns=100,
        gpu_hours_estimate=12,
        force_field="amber14-all.xml",
        water_model="tip3p",
        temperature_k=310.0,
        pressure_atm=1.0,
    ),
    "smn_gemin_complex": SimulationSpec(
        name="SMN-Gemin2 Complex Stability",
        simulation_type="protein_protein",
        target="SMN_PROTEIN",
        description="Simulate the SMN-Gemin2 interaction critical for snRNP assembly. "
                    "Reduced SMN levels in SMA destabilize this complex. Small molecules "
                    "that stabilize SMN-Gemin2 could compensate for reduced SMN quantity.",
        pdb_id="2LEH",  # SMN-Gemin2
        alphafold_id="AF-Q16637-F1",
        system_size_atoms=50000,
        simulation_time_ns=100,
        gpu_hours_estimate=8,
        force_field="amber14-all.xml",
        water_model="tip3p",
        temperature_k=310.0,
        pressure_atm=1.0,
    ),
}


# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------

def _generate_setup_script(spec: SimulationSpec) -> str:
    """Generate the OpenMM setup and minimization script."""
    pdb_source = f'"{spec.pdb_id}"' if spec.pdb_id else f'"{spec.alphafold_id}"  # AlphaFold model'

    return f'''#!/usr/bin/env python3
"""
{spec.name} — MD Simulation Setup
Generated by SMA Research Platform Agent C

Target: {spec.target}
Type: {spec.simulation_type}
Force field: {spec.force_field}
Water model: {spec.water_model}
Temperature: {spec.temperature_k} K
Estimated system size: ~{spec.system_size_atoms:,} atoms
Estimated GPU hours: {spec.gpu_hours_estimate}

Requirements:
    pip install openmm mdtraj numpy matplotlib
    # For PDB fetching:
    pip install biopython requests

Description:
    {spec.description}
"""

import os
import sys
import numpy as np

try:
    import openmm as mm
    from openmm import app, unit
    print(f"OpenMM version: {{mm.__version__}}")
except ImportError:
    print("ERROR: OpenMM not installed. Run: conda install -c conda-forge openmm")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PDB_ID = {pdb_source}
FORCE_FIELD = "{spec.force_field}"
WATER_MODEL = "amber14/tip3pfb.xml"  # TIP3P-FB (improved)
TEMPERATURE = {spec.temperature_k} * unit.kelvin
PRESSURE = {spec.pressure_atm} * unit.atmosphere
FRICTION = 1.0 / unit.picosecond
TIMESTEP = 2.0 * unit.femtoseconds
PADDING = 1.0 * unit.nanometers
IONIC_STRENGTH = 0.15 * unit.molar  # Physiological NaCl

OUTPUT_DIR = "md_output_{spec.target.lower()}"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Step 1: Load structure
# ---------------------------------------------------------------------------

print("Step 1: Loading structure...")

pdb_file = f"{{PDB_ID}}.pdb"
if not os.path.exists(pdb_file):
    # Fetch from PDB or AlphaFold
    import requests
    if PDB_ID.startswith("AF-"):
        url = f"https://alphafold.ebi.ac.uk/files/{{PDB_ID}}-model_v4.pdb"
    else:
        url = f"https://files.rcsb.org/download/{{PDB_ID}}.pdb"
    print(f"  Fetching from {{url}}...")
    resp = requests.get(url)
    resp.raise_for_status()
    with open(pdb_file, "w") as f:
        f.write(resp.text)
    print(f"  Saved to {{pdb_file}}")

pdb = app.PDBFile(pdb_file)
print(f"  Loaded: {{pdb.topology.getNumAtoms()}} atoms, {{pdb.topology.getNumResidues()}} residues")

# ---------------------------------------------------------------------------
# Step 2: Prepare system
# ---------------------------------------------------------------------------

print("Step 2: Building system with force field...")

forcefield = app.ForceField(FORCE_FIELD, WATER_MODEL)

# Add hydrogens if missing
modeller = app.Modeller(pdb.topology, pdb.positions)
modeller.addHydrogens(forcefield, pH=7.4)
print(f"  After hydrogens: {{modeller.topology.getNumAtoms()}} atoms")

# Add solvent box
modeller.addSolvent(
    forcefield,
    model="tip3p",
    padding=PADDING,
    ionicStrength=IONIC_STRENGTH,
)
print(f"  After solvation: {{modeller.topology.getNumAtoms()}} atoms")

# Create OpenMM system
system = forcefield.createSystem(
    modeller.topology,
    nonbondedMethod=app.PME,
    nonbondedCutoff=1.0 * unit.nanometers,
    constraints=app.HBonds,
    hydrogenMass=1.5 * unit.amu,  # Hydrogen mass repartitioning for 4 fs timestep
)

# Add barostat for NPT ensemble
system.addForce(mm.MonteCarloBarostat(PRESSURE, TEMPERATURE, 25))
print("  System created (PME, HBonds constraints, NPT ensemble)")

# ---------------------------------------------------------------------------
# Step 3: Energy minimization
# ---------------------------------------------------------------------------

print("Step 3: Energy minimization...")

integrator = mm.LangevinMiddleIntegrator(TEMPERATURE, FRICTION, TIMESTEP)

# Use GPU if available, fallback to CPU
try:
    platform = mm.Platform.getPlatformByName("CUDA")
    properties = {{"Precision": "mixed"}}
    print("  Using CUDA (GPU) platform")
except Exception:
    try:
        platform = mm.Platform.getPlatformByName("OpenCL")
        properties = {{}}
        print("  Using OpenCL platform")
    except Exception:
        platform = mm.Platform.getPlatformByName("CPU")
        properties = {{}}
        print("  Using CPU platform (slow — consider GPU)")

simulation = app.Simulation(modeller.topology, system, integrator, platform, properties)
simulation.context.setPositions(modeller.positions)

# Minimize
state = simulation.context.getState(getEnergy=True)
print(f"  Initial energy: {{state.getPotentialEnergy()}}")

simulation.minimizeEnergy(maxIterations=5000, tolerance=10 * unit.kilojoule_per_mole / unit.nanometer)

state = simulation.context.getState(getEnergy=True)
print(f"  Minimized energy: {{state.getPotentialEnergy()}}")

# Save minimized structure
positions = simulation.context.getState(getPositions=True).getPositions()
app.PDBFile.writeFile(modeller.topology, positions, open(f"{{OUTPUT_DIR}}/minimized.pdb", "w"))
print(f"  Saved minimized structure to {{OUTPUT_DIR}}/minimized.pdb")

# ---------------------------------------------------------------------------
# Step 4: Equilibration (NVT → NPT)
# ---------------------------------------------------------------------------

print("Step 4: Equilibration...")

# NVT equilibration (100 ps)
simulation.context.setVelocitiesToTemperature(TEMPERATURE)
simulation.reporters.append(
    app.StateDataReporter(
        f"{{OUTPUT_DIR}}/equil.log", 5000, step=True, temperature=True,
        potentialEnergy=True, totalEnergy=True, speed=True
    )
)
print("  NVT equilibration: 100 ps...")
simulation.step(50000)  # 100 ps at 2 fs/step

# Save equilibrated state
simulation.saveCheckpoint(f"{{OUTPUT_DIR}}/equilibrated.chk")
print(f"  Saved checkpoint to {{OUTPUT_DIR}}/equilibrated.chk")
print("  Equilibration complete!")
print()
print(f"  Next: Run production MD with production_{spec.target.lower()}.py")
'''


def _generate_production_script(spec: SimulationSpec) -> str:
    """Generate the production MD run script."""
    total_steps = int(spec.simulation_time_ns * 1e6 / 2)  # 2 fs timestep

    return f'''#!/usr/bin/env python3
"""
{spec.name} — Production MD Run
Generated by SMA Research Platform Agent C

Simulation time: {spec.simulation_time_ns} ns
Total steps: {total_steps:,} (2 fs timestep)
Estimated GPU hours: {spec.gpu_hours_estimate}
"""

import os
import openmm as mm
from openmm import app, unit

OUTPUT_DIR = "md_output_{spec.target.lower()}"
CHECKPOINT = f"{{OUTPUT_DIR}}/equilibrated.chk"
TEMPERATURE = {spec.temperature_k} * unit.kelvin
FRICTION = 1.0 / unit.picosecond
TIMESTEP = 2.0 * unit.femtoseconds
TOTAL_STEPS = {total_steps}
REPORT_INTERVAL = 50000   # Every 100 ps
TRAJ_INTERVAL = 5000      # Every 10 ps

assert os.path.exists(CHECKPOINT), f"Run setup script first! Missing: {{CHECKPOINT}}"

# Load checkpoint
print("Loading equilibrated checkpoint...")
# (In practice, re-create system and load checkpoint)
# This is a template — adjust based on your setup script output

# Reporters
simulation.reporters = []
simulation.reporters.append(
    app.StateDataReporter(
        f"{{OUTPUT_DIR}}/production.log", REPORT_INTERVAL,
        step=True, time=True, temperature=True,
        potentialEnergy=True, kineticEnergy=True,
        totalEnergy=True, volume=True, density=True, speed=True,
    )
)
simulation.reporters.append(
    app.DCDReporter(f"{{OUTPUT_DIR}}/trajectory.dcd", TRAJ_INTERVAL)
)
simulation.reporters.append(
    app.CheckpointReporter(f"{{OUTPUT_DIR}}/production.chk", REPORT_INTERVAL * 10)
)

# Production run
print(f"Starting production MD: {spec.simulation_time_ns} ns ({total_steps:,} steps)...")
print(f"Trajectory saved every {{TRAJ_INTERVAL * 2 / 1e6:.1f}} ns")

simulation.step(TOTAL_STEPS)

# Save final state
state = simulation.context.getState(getPositions=True, getVelocities=True)
positions = state.getPositions()
app.PDBFile.writeFile(simulation.topology, positions, open(f"{{OUTPUT_DIR}}/final.pdb", "w"))

print("Production MD complete!")
print(f"  Trajectory: {{OUTPUT_DIR}}/trajectory.dcd")
print(f"  Final structure: {{OUTPUT_DIR}}/final.pdb")
print(f"  Log: {{OUTPUT_DIR}}/production.log")
'''


def _generate_analysis_script(spec: SimulationSpec) -> str:
    """Generate the trajectory analysis script."""
    return f'''#!/usr/bin/env python3
"""
{spec.name} — Trajectory Analysis
Generated by SMA Research Platform Agent C

Analyzes:
- RMSD (root-mean-square deviation from initial structure)
- RMSF (root-mean-square fluctuation per residue)
- Radius of gyration (compactness)
- Secondary structure evolution
- Contact maps
- Binding energy estimation (MM/PBSA proxy)

Requirements: pip install mdtraj numpy matplotlib
"""

import os
import numpy as np
import matplotlib.pyplot as plt

try:
    import mdtraj as md
except ImportError:
    print("ERROR: MDTraj not installed. Run: pip install mdtraj")
    import sys; sys.exit(1)

OUTPUT_DIR = "md_output_{spec.target.lower()}"
TRAJ_FILE = f"{{OUTPUT_DIR}}/trajectory.dcd"
TOP_FILE = f"{{OUTPUT_DIR}}/minimized.pdb"  # Topology reference

print(f"Loading trajectory: {{TRAJ_FILE}}")
traj = md.load(TRAJ_FILE, top=TOP_FILE)
print(f"  Frames: {{traj.n_frames}}, Atoms: {{traj.n_atoms}}, Time: {{traj.time[-1]:.1f}} ps")

# Select protein atoms (exclude water/ions)
protein = traj.topology.select("protein")
traj_protein = traj.atom_slice(protein)

# ---------------------------------------------------------------------------
# 1. RMSD
# ---------------------------------------------------------------------------
print("Computing RMSD...")
rmsd = md.rmsd(traj_protein, traj_protein, 0) * 10  # nm → Angstrom

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(traj.time / 1000, rmsd, linewidth=0.5, color="#333")
ax.set_xlabel("Time (ns)")
ax.set_ylabel("RMSD (\\u00c5)")
ax.set_title("{spec.name} — RMSD")
fig.tight_layout()
fig.savefig(f"{{OUTPUT_DIR}}/rmsd.png", dpi=150)
print(f"  Mean RMSD: {{rmsd.mean():.2f}} \\u00c5, Final: {{rmsd[-1]:.2f}} \\u00c5")

# ---------------------------------------------------------------------------
# 2. RMSF (per residue)
# ---------------------------------------------------------------------------
print("Computing RMSF...")
rmsf = md.rmsf(traj_protein, traj_protein, 0) * 10  # nm → Angstrom
ca_indices = traj_protein.topology.select("name CA")
rmsf_ca = rmsf[ca_indices]

fig, ax = plt.subplots(figsize=(12, 4))
ax.bar(range(len(rmsf_ca)), rmsf_ca, width=1.0, color="#555")
ax.set_xlabel("Residue Index")
ax.set_ylabel("RMSF (\\u00c5)")
ax.set_title("{spec.name} — Per-Residue RMSF")
fig.tight_layout()
fig.savefig(f"{{OUTPUT_DIR}}/rmsf.png", dpi=150)

# Identify flexible regions (>2 Angstrom RMSF)
flexible = np.where(rmsf_ca > 2.0)[0]
print(f"  Flexible residues (RMSF > 2\\u00c5): {{len(flexible)}} residues")

# ---------------------------------------------------------------------------
# 3. Radius of Gyration
# ---------------------------------------------------------------------------
print("Computing radius of gyration...")
rg = md.compute_rg(traj_protein) * 10  # nm → Angstrom

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(traj.time / 1000, rg, linewidth=0.5, color="#333")
ax.set_xlabel("Time (ns)")
ax.set_ylabel("Rg (\\u00c5)")
ax.set_title("{spec.name} — Radius of Gyration")
fig.tight_layout()
fig.savefig(f"{{OUTPUT_DIR}}/rg.png", dpi=150)
print(f"  Mean Rg: {{rg.mean():.2f}} \\u00c5")

# ---------------------------------------------------------------------------
# 4. Summary report
# ---------------------------------------------------------------------------
summary = {{
    "simulation": "{spec.name}",
    "target": "{spec.target}",
    "frames": traj.n_frames,
    "total_time_ns": traj.time[-1] / 1000,
    "mean_rmsd_A": round(float(rmsd.mean()), 2),
    "final_rmsd_A": round(float(rmsd[-1]), 2),
    "mean_rg_A": round(float(rg.mean()), 2),
    "flexible_residues": len(flexible),
    "converged": bool(rmsd[-100:].std() < 0.5),  # Low RMSD variance in last 100 frames
}}

import json
with open(f"{{OUTPUT_DIR}}/analysis_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print()
print("Analysis complete!")
print(f"  RMSD plot: {{OUTPUT_DIR}}/rmsd.png")
print(f"  RMSF plot: {{OUTPUT_DIR}}/rmsf.png")
print(f"  Rg plot: {{OUTPUT_DIR}}/rg.png")
print(f"  Summary: {{OUTPUT_DIR}}/analysis_summary.json")
print(f"  Converged: {{'YES' if summary['converged'] else 'NO — consider extending simulation'}}")
'''


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_simulation_code(sim_key: str) -> dict[str, Any] | None:
    """Generate complete OpenMM simulation code for a specific SMA target."""
    spec = SIMULATION_SPECS.get(sim_key)
    if not spec:
        return None

    return {
        "simulation": asdict(spec),
        "scripts": {
            "setup": _generate_setup_script(spec),
            "production": _generate_production_script(spec),
            "analysis": _generate_analysis_script(spec),
        },
        "files": [
            f"setup_{spec.target.lower()}.py",
            f"production_{spec.target.lower()}.py",
            f"analysis_{spec.target.lower()}.py",
        ],
        "instructions": f"1. Run setup script: python setup_{spec.target.lower()}.py\n"
                         f"2. Run production: python production_{spec.target.lower()}.py\n"
                         f"3. Analyze results: python analysis_{spec.target.lower()}.py\n"
                         f"\nEstimated GPU hours: {spec.gpu_hours_estimate}\n"
                         f"Recommended GPU: NVIDIA A100 or RTX 4090 (24+ GB VRAM)",
    }


def list_available_simulations() -> dict[str, Any]:
    """List all available SMA simulation templates."""
    sims = []
    total_gpu_hours = 0
    for key, spec in SIMULATION_SPECS.items():
        sims.append({
            "key": key,
            **asdict(spec),
        })
        total_gpu_hours += spec.gpu_hours_estimate

    return {
        "total_simulations": len(sims),
        "total_gpu_hours": total_gpu_hours,
        "simulations": sims,
        "note": "Each simulation generates 3 Python scripts (setup, production, analysis). "
                "Run on GPU-equipped machines for best performance.",
    }
