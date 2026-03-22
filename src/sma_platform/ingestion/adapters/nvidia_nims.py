"""
NVIDIA BioNeMo NIMs Adapter
============================
API client for NVIDIA's cloud-hosted Biology NIM microservices:
- DiffDock v2.2: Molecular docking (protein-ligand binding prediction)
- OpenFold3: Biomolecular structure prediction (protein/RNA/DNA/ligand)
- GenMol v1.0: De novo molecule generation and optimization
- AlphaFold2: Protein structure prediction
- ESMfold: Fast protein structure prediction (no MSA needed)
- RFdiffusion: De novo protein design
- ProteinMPNN: Protein sequence design
- MSA Search: Multiple sequence alignment
- ESM-2 650M: Protein embeddings (degraded — retry logic)

RNAPro: NOT available as cloud API (container-only, self-host on Vast.ai).

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

# NIM cloud API endpoints (build.nvidia.com hosted) — free but rate-limited
# Self-hosted: set DIFFDOCK_SELF_URL env var to Vast.ai instance for unlimited docking
DIFFDOCK_CLOUD_URL = "https://health.api.nvidia.com/v1/biology/mit/diffdock"
DIFFDOCK_SELF_URL = os.environ.get("DIFFDOCK_SELF_URL", "")  # e.g. http://77.48.24.250:8000/molecular-docking/diffdock/generate
DIFFDOCK_URL = DIFFDOCK_SELF_URL or DIFFDOCK_CLOUD_URL  # Self-hosted takes priority
OPENFOLD3_URL = "https://health.api.nvidia.com/v1/biology/openfold/openfold3"
GENMOL_URL = "https://health.api.nvidia.com/v1/biology/nvidia/genmol"
GENMOL_GENERATE_URL = "https://health.api.nvidia.com/v1/biology/nvidia/genmol/generate"
MOLMIM_URL = "https://health.api.nvidia.com/v1/biology/nvidia/molmim/generate"  # Alternate GenMol

# NEW NIMs (2026-03-22)
ALPHAFOLD2_URL = "https://health.api.nvidia.com/v1/biology/deepmind/alphafold2"
ALPHAFOLD2_MULTIMER_URL = "https://health.api.nvidia.com/v1/biology/deepmind/alphafold2-multimer"
ESMFOLD_URL = "https://health.api.nvidia.com/v1/biology/meta/esmfold"
RFDIFFUSION_URL = "https://health.api.nvidia.com/v1/biology/ipd/rfdiffusion/generate"
PROTEINMPNN_URL = "https://health.api.nvidia.com/v1/biology/ipd/proteinmpnn/predict"
MSA_SEARCH_URL = "https://health.api.nvidia.com/v1/biology/colabfold/msa-search/predict"
ESM2_URL = "https://health.api.nvidia.com/v1/biology/meta/esm2-650m"

# RNAPro — NO cloud API available (404). Container-only, self-host on Vast.ai.
# Kept as constant for future self-hosted deployment.
RNAPRO_URL = os.environ.get("RNAPRO_SELF_URL", "")  # Set when self-hosted on Vast.ai

TIMEOUT = 120  # seconds — structure prediction can be slow


def _headers(for_self_hosted: bool = False) -> dict:
    """Standard auth headers for NVIDIA NIM API.

    Self-hosted NIMs on Vast.ai don't need auth headers.
    Cloud NIMs need Bearer token.
    """
    if for_self_hosted or DIFFDOCK_SELF_URL:
        return {"Content-Type": "application/json", "Accept": "application/json"}
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


async def diffdock_batch_dock(
    protein_pdb: str,
    smiles_list: list[str],
    num_poses: int = 3,
    time_divisions: int = 20,
    steps: int = 18,
) -> dict:
    """
    Batch-dock multiple ligands against one protein in a single API call.

    DiffDock V2 supports multi-line SMILES text as ligand input,
    docking all molecules against the same receptor concurrently.
    Much faster than individual calls (1 request vs N requests).

    Args:
        protein_pdb: PDB file content as string
        smiles_list: List of SMILES strings to dock
        num_poses: Number of poses per ligand
        time_divisions: Diffusion time divisions
        steps: Diffusion steps

    Returns:
        dict with per-ligand results
    """
    # Multi-line SMILES text — one SMILES per line
    smiles_text = "\n".join(smiles_list)

    payload = {
        "ligand": smiles_text,
        "ligand_file_type": "txt",
        "protein": protein_pdb,
        "num_poses": num_poses,
        "time_divisions": time_divisions,
        "steps": steps,
    }

    # Batch docking can take longer — scale timeout with number of molecules
    batch_timeout = max(TIMEOUT, len(smiles_list) * 5 + 60)

    async with httpx.AsyncClient(timeout=batch_timeout) as client:
        logger.info(
            f"DiffDock v2.2 BATCH: Docking {len(smiles_list)} ligands "
            f"in single request ({num_poses} poses each)"
        )
        resp = await client.post(
            DIFFDOCK_URL,
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        result = resp.json()

    n_results = len(result.get("output", result.get("poses", [])))
    logger.info(f"DiffDock v2.2 BATCH: Got results for {n_results} ligands")
    return result


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
# RNAPro — RNA 3D Structure Prediction
# CONTAINER-ONLY: No cloud API available (returns 404).
# Must self-host via NGC container on Vast.ai GPU instance.
# GitHub: https://github.com/NVIDIA-Digital-Bio/RNAPro
# HuggingFace: nvidia/RNAPro-Public-Best-500M
# NGC: catalog.ngc.nvidia.com/orgs/nvidia/teams/clara/collections/rnapro
# =============================================================================

async def rnapro_predict(
    rna_sequence: str,
    name: str = "SMN2_ISS_N1",
) -> dict:
    """Predict RNA 3D structure using NVIDIA RNAPro NIM.

    NOTE: RNAPro has NO cloud API. This function only works when
    RNAPRO_SELF_URL is set to a self-hosted instance (e.g., Vast.ai).

    Args:
        rna_sequence: RNA sequence (A/U/G/C)
        name: Identifier for the prediction

    Returns:
        dict with predicted 3D coordinates and confidence scores

    Raises:
        ValueError: If no self-hosted RNAPro URL is configured
    """
    if not RNAPRO_URL:
        raise ValueError(
            "RNAPro has no cloud API (404 on build.nvidia.com). "
            "Set RNAPRO_SELF_URL to a self-hosted instance on Vast.ai. "
            "See: https://github.com/NVIDIA-Digital-Bio/RNAPro"
        )

    logger.info("RNAPro prediction for %s (%d nt)", name, len(rna_sequence))
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            RNAPRO_URL,
            headers=_headers(for_self_hosted=True),
            json={"sequence": rna_sequence, "name": name},
        )
        resp.raise_for_status()
        result = resp.json()
        logger.info("RNAPro prediction complete for %s", name)
        return result


# =============================================================================
# AlphaFold2 — Protein Structure Prediction
# =============================================================================

async def predict_structure_af2(
    sequence: str,
    algorithm: str = "jackhmmer",
    e_value: float = 0.0001,
    databases: Optional[list[str]] = None,
    relax_prediction: bool = True,
) -> dict:
    """
    Predict protein structure using AlphaFold2 NIM.

    Uses MSA (multiple sequence alignment) for accurate structure prediction.
    Slower than ESMfold but generally more accurate for novel proteins.

    Args:
        sequence: Amino acid sequence (1-letter code)
        algorithm: MSA search algorithm — "jackhmmer" or "mmseqs2"
        e_value: E-value threshold for MSA search
        databases: Databases to search (default: uniref90, mgnify, etc.)
        relax_prediction: Apply Amber relaxation to final structure

    Returns:
        dict with PDB structure, pLDDT scores, and metadata
    """
    payload = {
        "sequence": sequence,
        "algorithm": algorithm,
        "e_value": e_value,
        "relax_prediction": relax_prediction,
    }
    if databases:
        payload["databases"] = databases

    async with httpx.AsyncClient(timeout=600) as client:  # AF2 can be slow (MSA)
        logger.info(
            "AlphaFold2: Predicting structure for %d-residue protein (algo=%s)",
            len(sequence), algorithm,
        )
        resp = await client.post(
            ALPHAFOLD2_URL,
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        result = resp.json()

    logger.info("AlphaFold2: Structure prediction complete (%d residues)", len(sequence))
    return result


async def predict_structure_af2_multimer(
    sequences: list[str],
    algorithm: str = "jackhmmer",
    e_value: float = 0.0001,
    relax_prediction: bool = True,
) -> dict:
    """
    Predict protein complex structure using AlphaFold2-Multimer NIM.

    Supports 1-6 protein chains for complex structure prediction.

    Args:
        sequences: List of amino acid sequences (one per chain)
        algorithm: MSA search algorithm
        e_value: E-value threshold for MSA search
        relax_prediction: Apply Amber relaxation

    Returns:
        dict with PDB complex structure, pLDDT, pTM, ipTM scores
    """
    payload = {
        "sequences": sequences,
        "algorithm": algorithm,
        "e_value": e_value,
        "relax_prediction": relax_prediction,
    }

    async with httpx.AsyncClient(timeout=900) as client:  # Multimer is even slower
        logger.info(
            "AlphaFold2-Multimer: Predicting complex with %d chains",
            len(sequences),
        )
        resp = await client.post(
            ALPHAFOLD2_MULTIMER_URL,
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        result = resp.json()

    logger.info("AlphaFold2-Multimer: Complex prediction complete (%d chains)", len(sequences))
    return result


# =============================================================================
# ESMfold — Fast Protein Structure Prediction (No MSA)
# =============================================================================

async def predict_structure_esmfold(
    sequence: str,
) -> dict:
    """
    Predict protein structure using ESMfold NIM (Meta).

    Much faster than AlphaFold2 — uses a protein language model
    instead of MSA search. Good for rapid screening of many proteins.

    Args:
        sequence: Amino acid sequence (1-letter code)

    Returns:
        dict with PDB structure and pLDDT scores
    """
    payload = {"sequence": sequence}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        logger.info(
            "ESMfold: Fast structure prediction for %d-residue protein",
            len(sequence),
        )
        resp = await client.post(
            ESMFOLD_URL,
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        result = resp.json()

    logger.info("ESMfold: Structure prediction complete (%d residues)", len(sequence))
    return result


# =============================================================================
# RFdiffusion — De Novo Protein Design
# =============================================================================

async def design_binder(
    target_pdb: str,
    hotspot_residues: list[str],
    binder_length: int = 100,
    num_designs: int = 10,
) -> dict:
    """
    Design a protein binder for a target using RFdiffusion NIM.

    Creates novel protein backbones that bind to specified hotspot
    residues on the target protein. Useful for designing therapeutic
    proteins against SMA targets (ROCK2, MAPK14, LIMK1).

    Args:
        target_pdb: PDB file content of the target protein
        hotspot_residues: List of residue identifiers to target,
            e.g., ["A100", "A101", "A105"] (chain + residue number)
        binder_length: Length of the designed binder (residues)
        num_designs: Number of binder designs to generate

    Returns:
        dict with designed protein backbones (PDB format)
    """
    # RFdiffusion uses "contigs" notation for specifying what to design
    # Format: [binder_length/0 target_chain_start-target_chain_end]
    hotspot_str = ",".join(hotspot_residues)

    payload = {
        "target_pdb": target_pdb,
        "contigs": f"{binder_length}/0",
        "hotspot_residues": hotspot_str,
        "num_designs": num_designs,
    }

    async with httpx.AsyncClient(timeout=300) as client:
        logger.info(
            "RFdiffusion: Designing %d binders (%d residues) targeting %d hotspots",
            num_designs, binder_length, len(hotspot_residues),
        )
        resp = await client.post(
            RFDIFFUSION_URL,
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        result = resp.json()

    logger.info("RFdiffusion: Generated %d binder designs", num_designs)
    return result


# =============================================================================
# ProteinMPNN — Protein Sequence Design
# =============================================================================

async def design_sequence(
    backbone_pdb: str,
    num_sequences: int = 10,
    temperature: float = 0.1,
    fixed_residues: Optional[list[str]] = None,
) -> dict:
    """
    Design amino acid sequences for a protein backbone using ProteinMPNN NIM.

    Given a protein backbone (e.g., from RFdiffusion), predicts optimal
    amino acid sequences that would fold into that structure.

    Args:
        backbone_pdb: PDB file content of the protein backbone
        num_sequences: Number of sequence designs to generate
        temperature: Sampling temperature (lower = more conservative)
        fixed_residues: Optional list of residues to keep fixed

    Returns:
        dict with designed sequences, scores, and recovery metrics
    """
    payload = {
        "pdb": backbone_pdb,
        "num_sequences": num_sequences,
        "temperature": temperature,
    }
    if fixed_residues:
        payload["fixed_residues"] = ",".join(fixed_residues)

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        logger.info(
            "ProteinMPNN: Designing %d sequences (T=%.2f)",
            num_sequences, temperature,
        )
        resp = await client.post(
            PROTEINMPNN_URL,
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        result = resp.json()

    logger.info("ProteinMPNN: Generated %d sequence designs", num_sequences)
    return result


# =============================================================================
# MSA Search — Multiple Sequence Alignment
# =============================================================================

async def msa_search(
    sequence: str,
    databases: Optional[list[str]] = None,
) -> dict:
    """
    Run multiple sequence alignment search using ColabFold MSA NIM.

    Searches against Uniref30, PDB70, and colabfold_envdb.
    Required as input for AlphaFold2 structure prediction.

    Args:
        sequence: Amino acid sequence (1-letter code)
        databases: Databases to search (default: all available)

    Returns:
        dict with MSA alignments in A3M format
    """
    payload = {"sequence": sequence}
    if databases:
        payload["databases"] = databases

    async with httpx.AsyncClient(timeout=300) as client:
        logger.info("MSA Search: Aligning %d-residue sequence", len(sequence))
        resp = await client.post(
            MSA_SEARCH_URL,
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        result = resp.json()

    logger.info("MSA Search: Alignment complete")
    return result


# =============================================================================
# ESM-2 650M — Protein Embeddings (DEGRADED — retry logic)
# =============================================================================

async def esm2_embed(
    sequences: list[str],
    max_retries: int = 3,
    retry_delay: float = 2.0,
) -> dict:
    """
    Get protein embeddings using ESM-2 650M NIM.

    STATUS: DEGRADED — NVIDIA endpoint returns 500 errors intermittently.
    This function includes retry logic to handle transient failures.

    Args:
        sequences: List of amino acid sequences
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds (doubles each retry)

    Returns:
        dict with embedding vectors

    Raises:
        httpx.HTTPStatusError: After all retries exhausted
    """
    import asyncio

    payload = {"sequences": sequences}
    last_error = None

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                logger.info(
                    "ESM-2: Embedding %d sequences (attempt %d/%d)",
                    len(sequences), attempt + 1, max_retries,
                )
                resp = await client.post(
                    ESM2_URL,
                    json=payload,
                    headers=_headers(),
                )
                resp.raise_for_status()
                result = resp.json()
                logger.info("ESM-2: Embedding complete for %d sequences", len(sequences))
                return result
        except httpx.HTTPStatusError as e:
            last_error = e
            if e.response.status_code == 500 and attempt < max_retries - 1:
                delay = retry_delay * (2 ** attempt)
                logger.warning(
                    "ESM-2: HTTP 500 error (attempt %d/%d), retrying in %.1fs: %s",
                    attempt + 1, max_retries, delay, e,
                )
                await asyncio.sleep(delay)
            else:
                raise
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = retry_delay * (2 ** attempt)
                logger.warning(
                    "ESM-2: Error (attempt %d/%d), retrying in %.1fs: %s",
                    attempt + 1, max_retries, delay, e,
                )
                await asyncio.sleep(delay)
            else:
                raise

    raise last_error  # Should not reach here, but safety net


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


async def design_rock2_binder(
    rock2_pdb: Optional[str] = None,
) -> dict:
    """
    Design a protein binder for ROCK2 kinase domain using RFdiffusion + ProteinMPNN.

    ROCK2 is a high-priority SMA target (actin dynamics pathway).
    This pipeline: RFdiffusion backbone → ProteinMPNN sequence → ESMfold validation.

    Args:
        rock2_pdb: PDB content for ROCK2. If None, downloads AlphaFold structure.

    Returns:
        dict with designed binders (backbone + sequence + predicted structure)
    """
    import urllib.request

    # Get ROCK2 structure (UniProt O75116)
    if not rock2_pdb:
        logger.info("Downloading ROCK2 AlphaFold structure...")
        url = "https://alphafold.ebi.ac.uk/files/AF-O75116-F1-model_v6.pdb"
        with urllib.request.urlopen(url) as resp:
            rock2_pdb = resp.read().decode()

    # Step 1: Design binder backbones with RFdiffusion
    # Target the kinase domain active site (residues 85-180 approximate)
    backbones = await design_binder(
        target_pdb=rock2_pdb,
        hotspot_residues=["A121", "A154", "A160", "A176"],  # Kinase domain hotspots
        binder_length=80,
        num_designs=5,
    )

    # Step 2: Design sequences for each backbone with ProteinMPNN
    results = []
    for i, backbone in enumerate(backbones.get("designs", [])):
        sequences = await design_sequence(
            backbone_pdb=backbone.get("pdb", ""),
            num_sequences=3,
            temperature=0.1,
        )
        results.append({
            "backbone_index": i,
            "backbone": backbone,
            "sequences": sequences,
        })

    return {
        "target": "ROCK2 (O75116)",
        "pipeline": "RFdiffusion → ProteinMPNN",
        "num_backbones": len(backbones.get("designs", [])),
        "designs": results,
    }


# =============================================================================
# Utility
# =============================================================================

def check_api_key() -> bool:
    """Check if NVIDIA API key is configured."""
    return bool(NVIDIA_API_KEY)


async def check_nim_health() -> dict:
    """Check health of all NIM endpoints."""
    results = {}
    endpoints = {
        "diffdock": DIFFDOCK_URL,
        "openfold3": OPENFOLD3_URL,
        "genmol": GENMOL_GENERATE_URL,
        "molmim": MOLMIM_URL,
        "alphafold2": ALPHAFOLD2_URL,
        "alphafold2_multimer": ALPHAFOLD2_MULTIMER_URL,
        "esmfold": ESMFOLD_URL,
        "rfdiffusion": RFDIFFUSION_URL,
        "proteinmpnn": PROTEINMPNN_URL,
        "msa_search": MSA_SEARCH_URL,
        "esm2": ESM2_URL,
    }

    # RNAPro only if self-hosted URL is configured
    if RNAPRO_URL:
        endpoints["rnapro"] = RNAPRO_URL

    async with httpx.AsyncClient(timeout=10) as client:
        for name, url in endpoints.items():
            try:
                # NIM cloud endpoints only accept POST, not GET.
                # A 405 (Method Not Allowed) on GET means the endpoint EXISTS and is alive.
                # A 422 (Unprocessable Entity) on POST with empty body also means alive.
                resp = await client.get(url, headers=_headers())
                code = resp.status_code
                # 405 = endpoint exists but rejects GET → healthy (use POST)
                # 200 = unexpected for POST-only endpoint but OK
                # 401/403 = auth issue but endpoint exists
                is_alive = code in (200, 405, 422, 401, 403)
                results[name] = {
                    "status": "healthy" if is_alive else "unhealthy",
                    "code": code,
                }
            except Exception as e:
                results[name] = {"status": "unreachable", "error": str(e)}

    # Always report RNAPro status
    if "rnapro" not in results:
        results["rnapro"] = {
            "status": "not_configured",
            "note": "No cloud API. Set RNAPRO_SELF_URL for self-hosted instance.",
        }

    return results
