"""
NVIDIA BioNeMo NIMs Adapter
============================
API client for NVIDIA's cloud-hosted Biology NIM microservices:
- DiffDock v2.2: Molecular docking (protein-ligand binding prediction)
- OpenFold3: Biomolecular structure prediction (protein/RNA/DNA/ligand)
- GenMol v1.0: De novo molecule generation and optimization
- RNAPro: RNA 3D structure prediction

Requires: NVIDIA_API_KEY environment variable (from build.nvidia.com)
Docs: https://docs.nvidia.com/nim/bionemo/
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# API configuration
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")

# NIM cloud API endpoints (build.nvidia.com hosted)
DIFFDOCK_URL = "https://health.api.nvidia.com/v1/biology/mit/diffdock"
OPENFOLD3_URL = "https://health.api.nvidia.com/v1/biology/openfold/openfold3"
GENMOL_URL = "https://health.api.nvidia.com/v1/biology/nvidia/genmol"
RNAPRO_URL = "https://health.api.nvidia.com/v1/biology/nvidia/rnapro"

TIMEOUT = 120  # seconds — structure prediction can be slow


def _headers() -> dict:
    """Standard auth headers for NVIDIA NIM API."""
    if not NVIDIA_API_KEY:
        raise ValueError(
            "NVIDIA_API_KEY environment variable not set. "
            "Get a key at https://build.nvidia.com"
        )
    return {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# =============================================================================
# DiffDock v2.2 — Molecular Docking
# =============================================================================

async def diffdock_dock(
    protein_pdb: str,
    ligand_sdf: str,
    num_poses: int = 10,
    time_divisions: int = 20,
    steps: int = 18,
) -> dict:
    """
    Dock a ligand to a protein using DiffDock v2.2 NIM.

    Args:
        protein_pdb: PDB file content as string
        ligand_sdf: SDF/MOL file content as string (or SMILES)
        num_poses: Number of binding poses to generate
        time_divisions: Time divisions for diffusion process
        steps: Number of diffusion steps

    Returns:
        dict with poses, confidence scores, and metadata
    """
    payload = {
        "ligand": ligand_sdf,
        "ligand_file_type": "sdf",
        "protein": protein_pdb,
        "num_poses": num_poses,
        "time_divisions": time_divisions,
        "steps": steps,
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        logger.info(f"DiffDock v2.2: Docking ligand to protein ({num_poses} poses)")
        resp = await client.post(
            DIFFDOCK_URL,
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        result = resp.json()

    logger.info(f"DiffDock v2.2: Got {len(result.get('poses', []))} poses")
    return result


async def diffdock_dock_smiles(
    protein_pdb: str,
    smiles: str,
    num_poses: int = 10,
) -> dict:
    """
    Dock a SMILES compound to a protein using DiffDock v2.2.

    Args:
        protein_pdb: PDB file content as string
        smiles: SMILES string of the ligand
        num_poses: Number of binding poses

    Returns:
        dict with poses, confidence scores
    """
    payload = {
        "ligand": smiles,
        "ligand_file_type": "smiles",
        "protein": protein_pdb,
        "num_poses": num_poses,
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        logger.info(f"DiffDock v2.2: Docking SMILES {smiles[:30]}...")
        resp = await client.post(
            DIFFDOCK_URL,
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json()


# =============================================================================
# OpenFold3 — Structure Prediction
# =============================================================================

async def openfold3_predict(
    sequences: list[dict],
) -> dict:
    """
    Predict biomolecular complex structure using OpenFold3 NIM.

    Args:
        sequences: List of sequence dicts, e.g.:
            [
                {"type": "protein", "sequence": "MKVL..."},
                {"type": "rna", "sequence": "AUGCGU..."},
                {"type": "ligand", "smiles": "Nc1ccncc1"},
            ]

    Returns:
        dict with mmCIF structure and confidence metrics
    """
    payload = {"sequences": sequences}

    async with httpx.AsyncClient(timeout=300) as client:
        logger.info(f"OpenFold3: Predicting structure for {len(sequences)} sequences")
        resp = await client.post(
            f"{OPENFOLD3_URL}/predict",
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json()


async def openfold3_protein_rna_complex(
    protein_sequence: str,
    rna_sequence: str,
    ligand_smiles: Optional[str] = None,
) -> dict:
    """
    Predict protein-RNA complex structure, optionally with a ligand.
    Directly relevant for SMN2 pre-mRNA + splicing modifier binding.

    Args:
        protein_sequence: Amino acid sequence
        rna_sequence: RNA sequence (e.g., SMN2 exon 7 region)
        ligand_smiles: Optional SMILES of a bound ligand

    Returns:
        dict with mmCIF structure
    """
    sequences = [
        {"type": "protein", "sequence": protein_sequence},
        {"type": "rna", "sequence": rna_sequence},
    ]
    if ligand_smiles:
        sequences.append({"type": "ligand", "smiles": ligand_smiles})

    return await openfold3_predict(sequences)


# =============================================================================
# GenMol v1.0 — De Novo Molecule Generation
# =============================================================================

async def genmol_generate(
    scaffold_smiles: str,
    num_molecules: int = 50,
    temperature: float = 1.0,
    noise: float = 0.5,
    step_size: int = 1,
    scoring: str = "QED",
    unique: bool = True,
) -> dict:
    """
    Generate novel molecules using GenMol NIM.

    Uses SAFE (Sequential Attachment-based Fragment Embedding) format.
    The input SMILES is used as a molecular template for generation.

    Args:
        scaffold_smiles: SMILES of the scaffold/seed molecule
        num_molecules: Number of molecules to generate (1-1000)
        temperature: Sampling temperature (0.01-10.0, higher = more diverse)
        noise: Randomness factor (0.0-2.0)
        step_size: Diffusion step size (1-10)
        scoring: Scoring method — "QED" or "LogP"
        unique: Return only distinct molecules

    Returns:
        dict with generated SMILES and scores
    """
    payload = {
        "smiles": scaffold_smiles,
        "num_molecules": str(num_molecules),
        "temperature": str(temperature),
        "noise": str(noise),
        "step_size": str(step_size),
        "scoring": scoring,
        "unique": unique,
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        logger.info(f"GenMol: Generating {num_molecules} molecules "
                     f"from {scaffold_smiles[:30]}... (scoring={scoring})")
        resp = await client.post(
            f"{GENMOL_URL}/generate",
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json()


async def genmol_from_4ap(num_molecules: int = 100) -> dict:
    """
    Generate novel molecules based on the 4-Aminopyridine scaffold.
    Uses scaffold decoration to create 4-AP analogs with potentially
    improved SMN2 binding properties.

    Returns:
        dict with generated SMILES
    """
    # 4-AP is too small for scaffold decoration — use fragment + mask
    return await genmol_generate(
        scaffold_smiles="c1cc(N)ncc1.[*{10-25}]",  # 4-AP fragment + size mask
        num_molecules=num_molecules,
        temperature=2.5,
        noise=1.5,
        scoring="QED",
        unique=True,
    )


# =============================================================================
# RNAPro — RNA 3D Structure Prediction (GTC 2026)
# =============================================================================

async def rnapro_predict(
    rna_sequence: str,
    name: str = "SMN2_ISS_N1",
) -> dict:
    """Predict RNA 3D structure using NVIDIA RNAPro NIM.

    Args:
        rna_sequence: RNA sequence (A/U/G/C)
        name: Identifier for the prediction

    Returns:
        dict with predicted 3D coordinates and confidence scores
    """
    logger.info("RNAPro prediction for %s (%d nt)", name, len(rna_sequence))
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            RNAPRO_URL,
            headers=_headers(),
            json={"sequence": rna_sequence, "name": name},
        )
        resp.raise_for_status()
        result = resp.json()
        logger.info("RNAPro prediction complete for %s", name)
        return result

# =============================================================================
# Batch Operations — SMA-specific workflows
# =============================================================================

async def redock_4ap_with_diffdock_v2(
    smn2_pdb_path: Optional[str] = None,
) -> dict:
    """
    Re-dock 4-Aminopyridine against SMN2 using DiffDock v2.2.
    This validates our original DiffDock v1 finding (+0.100 confidence)
    with the improved model (16% more accurate on PLINDER).

    Args:
        smn2_pdb_path: Path to SMN2 PDB file (downloads from AlphaFold if None)

    Returns:
        dict with docking results, confidence scores, and comparison
    """
    import urllib.request

    # Get SMN2 structure
    if smn2_pdb_path and Path(smn2_pdb_path).exists():
        protein_pdb = Path(smn2_pdb_path).read_text()
    else:
        logger.info("Downloading SMN2 AlphaFold structure...")
        url = "https://alphafold.ebi.ac.uk/files/AF-Q16637-F1-model_v6.pdb"
        with urllib.request.urlopen(url) as resp:
            protein_pdb = resp.read().decode()

    # Dock 4-AP (SMILES)
    result = await diffdock_dock_smiles(
        protein_pdb=protein_pdb,
        smiles="Nc1ccncc1",  # 4-Aminopyridine
        num_poses=20,
    )

    # Add comparison context
    result["comparison"] = {
        "diffdock_v1_confidence": 0.100,
        "diffdock_version": "v2.2",
        "compound": "4-aminopyridine",
        "target": "SMN2 (Q16637)",
        "note": "Re-docking with DiffDock v2.2 (16% more accurate than v1 on PLINDER)",
    }

    return result


async def predict_smn2_rna_structure() -> dict:
    """
    Predict SMN2 pre-mRNA structure around exon 7 using OpenFold3.
    This is directly relevant for understanding how splicing modifiers
    (risdiplam, branaplam) bind to SMN2 RNA.

    The key region: exon 7 (54nt) + flanking intron sequences.
    """
    # SMN2 exon 7 + flanking intronic sequences
    # Exon 7 is 54 nucleotides, we include 100nt flanking on each side
    smn2_exon7_region = (
        # Intron 6 3' end (100nt before exon 7)
        "AAAUAUAAAGAUUUAUUUCAAUUUUAAAUAAAUUAAAGAAGGAAAUGCUUUCAACAUUUAAG"
        "UGGAAAGACUAUUUCUAAUUUAUUCAAAACAAUUUUAUGA"
        # Exon 7 (54nt) — C→T at position 6 is the SMN2-specific change
        "AAAAUUCAAAAGAAGGAAGGUGUUCCUUUAAUUUUUAAGCUGUUCAAAAUUUUUAA"
        # Intron 7 5' start (100nt after exon 7)
        "GUAAGUUUGAUUUAAGUUUUAUAUAUAAUUAAAGAUAUAAAAUGUAAAGAGCUUAAAUGUUU"
        "UAACUGUAUUUUUAAAUAUAUUUUAGAUAAGAUUUUAGAA"
    )

    return await openfold3_predict([
        {"type": "rna", "sequence": smn2_exon7_region},
    ])


# =============================================================================
# Utility
# =============================================================================

def check_api_key() -> bool:
    """Check if NVIDIA API key is configured."""
    return bool(NVIDIA_API_KEY)


async def check_nim_health() -> dict:
    """Check health of all NIM endpoints."""
    results = {}
    # Cloud NIMs don't have a /health endpoint — just check if the API responds
    endpoints = {
        "diffdock": DIFFDOCK_URL,
        "openfold3": OPENFOLD3_URL,
        "genmol": GENMOL_URL,
        "rnapro": RNAPRO_URL,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        for name, url in endpoints.items():
            try:
                resp = await client.get(url, headers=_headers())
                results[name] = {
                    "status": "healthy" if resp.status_code == 200 else "unhealthy",
                    "code": resp.status_code,
                }
            except Exception as e:
                results[name] = {"status": "unreachable", "error": str(e)}

    return results
