"""
NVIDIA NIMs API Routes
=======================
Endpoints for running NVIDIA BioNeMo NIM jobs:
- DiffDock v2.2 re-docking
- OpenFold3 structure prediction
- GenMol molecule generation
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/nims", tags=["nvidia-nims"])


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
            # Download AlphaFold structure for target
            import urllib.request
            # Map target names to UniProt IDs
            target_uniprot = {
                "SMN2": "Q16637", "SMN1": "Q16637",
                "PLS3": "P13797", "STMN2": "Q93045",
                "NCALD": "P61601", "UBA1": "P22314",
                "CORO1C": "Q9ULV4",
            }
            uniprot_id = target_uniprot.get(req.target)
            if not uniprot_id:
                raise HTTPException(400, f"Unknown target: {req.target}")

            url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_v6.pdb"
            with urllib.request.urlopen(url) as resp:
                protein_pdb = resp.read().decode()

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
            mode=req.mode,
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
