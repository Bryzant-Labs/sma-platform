"""
NVIDIA NIMs API Routes
=======================
Endpoints for running NVIDIA BioNeMo NIM jobs:
- DiffDock v2.2 re-docking
- OpenFold3 structure prediction
- GenMol molecule generation
- AlphaFold2 protein structure prediction
- ESMfold fast protein folding
- RFdiffusion protein binder design
- ProteinMPNN sequence design
- MSA Search alignment
- ESM-2 protein embeddings (with retry logic)
- RNAPro RNA 3D structure (container-only, requires self-hosted URL)
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/nims", tags=["nvidia-nims"])


# ---- Request Models ----

class DockRequest(BaseModel):
    smiles: str
    target: str = "SMN2"
    num_poses: int = 10
    pdb_content: Optional[str] = None


class GenMolRequest(BaseModel):
    scaffold_smiles: str = "Nc1ccncc1"  # 4-AP default
    num_molecules: int = 50
    mode: str = "scaffold_decoration"


class StructureRequest(BaseModel):
    protein_sequence: Optional[str] = None
    rna_sequence: Optional[str] = None
    ligand_smiles: Optional[str] = None


class RNAStructureRequest(BaseModel):
    rna_sequence: str
    name: str = "SMN2_ISS_N1"


class AF2Request(BaseModel):
    """AlphaFold2 single-protein structure prediction."""
    sequence: str
    algorithm: str = "jackhmmer"
    relax_prediction: bool = True


class AF2MultimerRequest(BaseModel):
    """AlphaFold2-Multimer complex structure prediction."""
    sequences: list[str]
    algorithm: str = "jackhmmer"
    relax_prediction: bool = True


class ESMfoldRequest(BaseModel):
    """ESMfold fast structure prediction."""
    sequence: str


class BinderDesignRequest(BaseModel):
    """RFdiffusion binder design."""
    target_pdb: str
    hotspot_residues: list[str]
    binder_length: int = 100
    num_designs: int = 10


class SequenceDesignRequest(BaseModel):
    """ProteinMPNN sequence design."""
    backbone_pdb: str
    num_sequences: int = 10
    temperature: float = 0.1
    fixed_residues: Optional[list[str]] = None


class MSARequest(BaseModel):
    """MSA Search."""
    sequence: str
    databases: Optional[list[str]] = None


class ESM2Request(BaseModel):
    """ESM-2 protein embeddings."""
    sequences: list[str]


# ---- Health check ----

@router.get("/health")
async def nim_health():
    """Check NVIDIA NIM API health and API key status."""
    from ...ingestion.adapters.nvidia_nims import check_api_key, check_nim_health

    if not check_api_key():
        return {
            "status": "not_configured",
            "message": "NVIDIA_API_KEY not set. Get a key at https://build.nvidia.com",
        }

    health = await check_nim_health()
    return {"status": "configured", "endpoints": health}


# ---- DiffDock v2.2 ----

@router.post("/dock", dependencies=[Depends(require_admin_key)])
async def dock_compound(req: DockRequest):
    """
    Dock a compound to a protein target using DiffDock v2.2 NIM.
    Default target: SMN2 (AlphaFold structure auto-downloaded).
    """
    from ...ingestion.adapters.nvidia_nims import diffdock_dock_smiles, check_api_key

    if not check_api_key():
        raise HTTPException(400, "NVIDIA_API_KEY not configured")

    try:
        if req.pdb_content:
            protein_pdb = req.pdb_content
        else:
            import httpx as _httpx
            target_uniprot = {
                "SMN2": "Q16637", "SMN1": "Q16637",
                "PLS3": "P13797", "STMN2": "Q93045",
                "NCALD": "P61601", "UBA1": "P22314",
                "CORO1C": "Q9ULV4", "ROCK2": "O75116",
                "MAPK14": "Q16539", "LIMK1": "P53667",
                "CFL2": "Q9Y281", "PFN1": "P07737",
            }
            uniprot_id = target_uniprot.get(req.target)
            if not uniprot_id:
                raise HTTPException(400, f"Unknown target: {req.target}")

            url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_v6.pdb"
            async with _httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                protein_pdb = resp.text

        result = await diffdock_dock_smiles(
            protein_pdb=protein_pdb,
            smiles=req.smiles,
            num_poses=req.num_poses,
        )

        return {
            "tool": "DiffDock v2.2 NIM",
            "target": req.target,
            "smiles": req.smiles,
            "result": result,
        }

    except Exception as e:
        logger.error(f"DiffDock NIM error: {e}", exc_info=True)
        raise HTTPException(500, f"DiffDock NIM failed: {str(e)}")


@router.post("/redock-4ap", dependencies=[Depends(require_admin_key)])
async def redock_4ap():
    """
    Re-dock 4-Aminopyridine against SMN2 using DiffDock v2.2.
    Validates our original finding (+0.100) with the improved model.
    """
    from ...ingestion.adapters.nvidia_nims import redock_4ap_with_diffdock_v2, check_api_key

    if not check_api_key():
        raise HTTPException(400, "NVIDIA_API_KEY not configured")

    try:
        result = await redock_4ap_with_diffdock_v2()
        return {
            "tool": "DiffDock v2.2 NIM",
            "description": "4-AP re-docking validation",
            "original_v1_confidence": 0.100,
            "result": result,
        }
    except Exception as e:
        logger.error(f"4-AP re-docking failed: {e}", exc_info=True)
        raise HTTPException(500, f"Re-docking failed: {str(e)}")


# ---- GenMol ----

@router.post("/generate-molecules", dependencies=[Depends(require_admin_key)])
async def generate_molecules(req: GenMolRequest):
    """
    Generate novel molecules based on a scaffold using GenMol v1.0 NIM.
    Default: 4-AP scaffold decoration for SMN2-targeting analogs.
    """
    from ...ingestion.adapters.nvidia_nims import genmol_generate, check_api_key

    if not check_api_key():
        raise HTTPException(400, "NVIDIA_API_KEY not configured")

    try:
        result = await genmol_generate(
            scaffold_smiles=req.scaffold_smiles,
            num_molecules=req.num_molecules,
        )
        return {
            "tool": "GenMol v1.0 NIM",
            "scaffold": req.scaffold_smiles,
            "mode": req.mode,
            "result": result,
        }
    except Exception as e:
        logger.error(f"GenMol NIM error: {e}", exc_info=True)
        raise HTTPException(500, f"GenMol failed: {str(e)}")


# ---- OpenFold3 ----

@router.post("/predict-structure", dependencies=[Depends(require_admin_key)])
async def predict_structure(req: StructureRequest):
    """
    Predict biomolecular complex structure using OpenFold3 NIM.
    Supports protein, RNA, and ligand inputs.
    """
    from ...ingestion.adapters.nvidia_nims import openfold3_predict, check_api_key

    if not check_api_key():
        raise HTTPException(400, "NVIDIA_API_KEY not configured")

    sequences = []
    if req.protein_sequence:
        sequences.append({"type": "protein", "sequence": req.protein_sequence})
    if req.rna_sequence:
        sequences.append({"type": "rna", "sequence": req.rna_sequence})
    if req.ligand_smiles:
        sequences.append({"type": "ligand", "smiles": req.ligand_smiles})

    if not sequences:
        raise HTTPException(400, "At least one sequence (protein/RNA/ligand) required")

    try:
        result = await openfold3_predict(sequences)
        return {
            "tool": "OpenFold3 NIM",
            "input_types": [s["type"] for s in sequences],
            "result": result,
        }
    except Exception as e:
        logger.error(f"OpenFold3 NIM error: {e}", exc_info=True)
        raise HTTPException(500, f"OpenFold3 failed: {str(e)}")


@router.post("/smn2-rna-structure", dependencies=[Depends(require_admin_key)])
async def predict_smn2_rna():
    """
    Predict SMN2 pre-mRNA 3D structure around exon 7 using OpenFold3.
    Novel analysis — no prior RNA structure prediction for this region.
    """
    from ...ingestion.adapters.nvidia_nims import predict_smn2_rna_structure, check_api_key

    if not check_api_key():
        raise HTTPException(400, "NVIDIA_API_KEY not configured")

    try:
        result = await predict_smn2_rna_structure()
        return {
            "tool": "OpenFold3 NIM",
            "description": "SMN2 exon 7 pre-mRNA 3D structure prediction",
            "region": "intron6(100nt) + exon7(54nt) + intron7(100nt)",
            "result": result,
        }
    except Exception as e:
        logger.error(f"SMN2 RNA structure prediction failed: {e}", exc_info=True)
        raise HTTPException(500, f"RNA structure prediction failed: {str(e)}")


# ---- RNAPro (container-only) ----

@router.post("/rna-structure", dependencies=[Depends(require_admin_key)])
async def predict_rna_structure(req: RNAStructureRequest):
    """Predict RNA 3D structure using RNAPro.

    NOTE: RNAPro has NO cloud API on build.nvidia.com (returns 404).
    This endpoint only works when RNAPRO_SELF_URL is configured
    (self-hosted on Vast.ai or similar GPU instance).
    """
    from ...ingestion.adapters.nvidia_nims import rnapro_predict, check_api_key, RNAPRO_URL

    if not RNAPRO_URL:
        raise HTTPException(
            503,
            "RNAPro has no cloud API (container-only). "
            "Set RNAPRO_SELF_URL to a self-hosted instance. "
            "See: https://github.com/NVIDIA-Digital-Bio/RNAPro",
        )

    if not check_api_key():
        raise HTTPException(400, "NVIDIA_API_KEY not configured")

    try:
        result = await rnapro_predict(
            rna_sequence=req.rna_sequence,
            name=req.name,
        )
    except ValueError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        logger.error("RNAPro prediction failed: %s", e)
        raise HTTPException(500, detail=f"RNAPro prediction failed: {e}")

    return {
        "status": "ok",
        "prediction": result,
        "model": "RNAPro (self-hosted)",
        "sequence_length": len(req.rna_sequence),
        "name": req.name,
    }


# ---- AlphaFold2 ----

@router.post("/alphafold2", dependencies=[Depends(require_admin_key)])
async def predict_structure_af2(req: AF2Request):
    """
    Predict protein structure using AlphaFold2 NIM.
    Uses MSA for high-accuracy structure prediction.
    Slower than ESMfold but more accurate for novel proteins.
    """
    from ...ingestion.adapters.nvidia_nims import predict_structure_af2 as _predict_af2, check_api_key

    if not check_api_key():
        raise HTTPException(400, "NVIDIA_API_KEY not configured")

    try:
        result = await _predict_af2(
            sequence=req.sequence,
            algorithm=req.algorithm,
            relax_prediction=req.relax_prediction,
        )
        return {
            "tool": "AlphaFold2 NIM",
            "sequence_length": len(req.sequence),
            "algorithm": req.algorithm,
            "result": result,
        }
    except Exception as e:
        logger.error(f"AlphaFold2 NIM error: {e}", exc_info=True)
        raise HTTPException(500, f"AlphaFold2 failed: {str(e)}")


@router.post("/alphafold2-multimer", dependencies=[Depends(require_admin_key)])
async def predict_complex_af2(req: AF2MultimerRequest):
    """
    Predict protein complex structure using AlphaFold2-Multimer NIM.
    Supports 1-6 protein chains.
    """
    from ...ingestion.adapters.nvidia_nims import predict_structure_af2_multimer, check_api_key

    if not check_api_key():
        raise HTTPException(400, "NVIDIA_API_KEY not configured")

    if len(req.sequences) > 6:
        raise HTTPException(400, "AlphaFold2-Multimer supports max 6 chains")

    try:
        result = await predict_structure_af2_multimer(
            sequences=req.sequences,
            algorithm=req.algorithm,
            relax_prediction=req.relax_prediction,
        )
        return {
            "tool": "AlphaFold2-Multimer NIM",
            "num_chains": len(req.sequences),
            "algorithm": req.algorithm,
            "result": result,
        }
    except Exception as e:
        logger.error(f"AlphaFold2-Multimer NIM error: {e}", exc_info=True)
        raise HTTPException(500, f"AlphaFold2-Multimer failed: {str(e)}")


# ---- ESMfold ----

@router.post("/esmfold", dependencies=[Depends(require_admin_key)])
async def predict_structure_esmfold(req: ESMfoldRequest):
    """
    Fast protein structure prediction using ESMfold NIM.
    No MSA required — uses protein language model directly.
    Much faster than AlphaFold2, good for screening many proteins.
    """
    from ...ingestion.adapters.nvidia_nims import predict_structure_esmfold as _predict_esmfold, check_api_key

    if not check_api_key():
        raise HTTPException(400, "NVIDIA_API_KEY not configured")

    try:
        result = await _predict_esmfold(sequence=req.sequence)
        return {
            "tool": "ESMfold NIM",
            "sequence_length": len(req.sequence),
            "result": result,
        }
    except Exception as e:
        logger.error(f"ESMfold NIM error: {e}", exc_info=True)
        raise HTTPException(500, f"ESMfold failed: {str(e)}")


# ---- RFdiffusion ----

@router.post("/design-binder", dependencies=[Depends(require_admin_key)])
async def design_protein_binder(req: BinderDesignRequest):
    """
    Design a protein binder for a target using RFdiffusion NIM.
    Creates novel protein backbones that bind to specified hotspot residues.
    Useful for designing therapeutic proteins against ROCK2, MAPK14, LIMK1.
    """
    from ...ingestion.adapters.nvidia_nims import design_binder as _design_binder, check_api_key

    if not check_api_key():
        raise HTTPException(400, "NVIDIA_API_KEY not configured")

    try:
        result = await _design_binder(
            target_pdb=req.target_pdb,
            hotspot_residues=req.hotspot_residues,
            binder_length=req.binder_length,
            num_designs=req.num_designs,
        )
        return {
            "tool": "RFdiffusion NIM",
            "binder_length": req.binder_length,
            "num_designs": req.num_designs,
            "hotspots": req.hotspot_residues,
            "result": result,
        }
    except Exception as e:
        logger.error(f"RFdiffusion NIM error: {e}", exc_info=True)
        raise HTTPException(500, f"RFdiffusion failed: {str(e)}")


# ---- ProteinMPNN ----

@router.post("/design-sequence", dependencies=[Depends(require_admin_key)])
async def design_protein_sequence(req: SequenceDesignRequest):
    """
    Design amino acid sequences for a protein backbone using ProteinMPNN NIM.
    Use after RFdiffusion to get sequences for designed backbones.
    """
    from ...ingestion.adapters.nvidia_nims import design_sequence as _design_sequence, check_api_key

    if not check_api_key():
        raise HTTPException(400, "NVIDIA_API_KEY not configured")

    try:
        result = await _design_sequence(
            backbone_pdb=req.backbone_pdb,
            num_sequences=req.num_sequences,
            temperature=req.temperature,
            fixed_residues=req.fixed_residues,
        )
        return {
            "tool": "ProteinMPNN NIM",
            "num_sequences": req.num_sequences,
            "temperature": req.temperature,
            "result": result,
        }
    except Exception as e:
        logger.error(f"ProteinMPNN NIM error: {e}", exc_info=True)
        raise HTTPException(500, f"ProteinMPNN failed: {str(e)}")


# ---- MSA Search ----

@router.post("/msa-search", dependencies=[Depends(require_admin_key)])
async def run_msa_search(req: MSARequest):
    """
    Run multiple sequence alignment using ColabFold MSA NIM.
    Searches Uniref30, PDB70, colabfold_envdb.
    Required as input for AlphaFold2 pipeline.
    """
    from ...ingestion.adapters.nvidia_nims import msa_search as _msa_search, check_api_key

    if not check_api_key():
        raise HTTPException(400, "NVIDIA_API_KEY not configured")

    try:
        result = await _msa_search(
            sequence=req.sequence,
            databases=req.databases,
        )
        return {
            "tool": "MSA Search NIM (ColabFold)",
            "sequence_length": len(req.sequence),
            "result": result,
        }
    except Exception as e:
        logger.error(f"MSA Search NIM error: {e}", exc_info=True)
        raise HTTPException(500, f"MSA Search failed: {str(e)}")


# ---- ESM-2 (with retry) ----

@router.post("/esm2-embed", dependencies=[Depends(require_admin_key)])
async def esm2_embed_sequences(req: ESM2Request):
    """
    Get protein embeddings using ESM-2 650M NIM.

    STATUS: DEGRADED — NVIDIA returns 500 errors intermittently.
    Includes automatic retry logic (3 attempts with exponential backoff).
    """
    from ...ingestion.adapters.nvidia_nims import esm2_embed as _esm2_embed, check_api_key

    if not check_api_key():
        raise HTTPException(400, "NVIDIA_API_KEY not configured")

    try:
        result = await _esm2_embed(sequences=req.sequences)
        return {
            "tool": "ESM-2 650M NIM",
            "num_sequences": len(req.sequences),
            "status": "ok",
            "result": result,
        }
    except Exception as e:
        logger.error(f"ESM-2 NIM error (after retries): {e}", exc_info=True)
        raise HTTPException(
            502,
            f"ESM-2 NIM failed after retries (NVIDIA endpoint degraded): {str(e)}",
        )


# ---- ROCK2 Binder Design Pipeline ----

@router.post("/design-rock2-binder", dependencies=[Depends(require_admin_key)])
async def design_rock2_binder():
    """
    End-to-end binder design pipeline for ROCK2:
    1. Download ROCK2 AlphaFold structure
    2. RFdiffusion: design binder backbones
    3. ProteinMPNN: design sequences for backbones
    """
    from ...ingestion.adapters.nvidia_nims import design_rock2_binder as _design_rock2, check_api_key

    if not check_api_key():
        raise HTTPException(400, "NVIDIA_API_KEY not configured")

    try:
        result = await _design_rock2()
        return {
            "tool": "RFdiffusion + ProteinMPNN pipeline",
            "target": "ROCK2 (O75116)",
            "result": result,
        }
    except Exception as e:
        logger.error(f"ROCK2 binder design failed: {e}", exc_info=True)
        raise HTTPException(500, f"ROCK2 binder design failed: {str(e)}")


# ---- AlphaFold Complex Check (GTC 2026) ----

@router.get("/alphafold/complexes", dependencies=[Depends(require_admin_key)])
async def check_alphafold_complexes():
    """Check AlphaFold DB for SMA protein complex predictions (GTC 2026 expansion)."""
    from ...ingestion.adapters.alphafold import check_complex_predictions

    results = await check_complex_predictions()
    found = [r for r in results if r["predicted"]]

    return {
        "total_checked": len(results),
        "found": len(found),
        "complexes": results,
    }
