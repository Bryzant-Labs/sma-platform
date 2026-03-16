"""Screening Funnel Pipeline API — billion-molecule virtual screening."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/funnel", tags=["funnel"])


class FunnelRunRequest(BaseModel):
    n_generate: int = 100_000
    target: str = "SMN2"


# POST /funnel/run (admin) — start a funnel run
@router.post("/run", dependencies=[Depends(require_admin_key)])
async def start_funnel_run(body: FunnelRunRequest):
    """Start a screening funnel pipeline run.

    Orchestrates: Generate -> Filter -> ML Proxy -> DiffDock -> Candidates.
    Pure SMILES-based drug-likeness estimation (no RDKit required).
    """
    from ...reasoning.screening_funnel import run_funnel

    if body.n_generate < 100:
        raise HTTPException(400, "n_generate must be at least 100")
    if body.n_generate > 10_000_000:
        raise HTTPException(400, "n_generate cannot exceed 10,000,000 per run")

    valid_targets = {"SMN2", "SMN1", "HDAC", "MTOR", "NCALD", "PLS3", "UBA1"}
    target_upper = body.target.upper()
    if target_upper not in valid_targets:
        raise HTTPException(
            400,
            f"Unknown target: {body.target}. Available: {', '.join(sorted(valid_targets))}",
        )

    try:
        result = await run_funnel(n_generate=body.n_generate, target=target_upper)
        return result
    except Exception as exc:
        logger.error("Funnel run failed: %s", exc, exc_info=True)
        raise HTTPException(500, f"Funnel run failed: {str(exc)[:500]}")


# GET /funnel/status — current funnel status
@router.get("/status")
async def funnel_status():
    """Get status of any running funnel job."""
    from ...reasoning.screening_funnel import get_funnel_status

    return await get_funnel_status()


# GET /funnel/results — latest funnel results
@router.get("/results")
async def funnel_results(
    run_id: str = Query(default="latest", description="Run ID or 'latest'"),
):
    """Get results from a completed funnel run."""
    from ...reasoning.screening_funnel import get_funnel_results

    result = await get_funnel_results(run_id=run_id)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


# GET /funnel/summary — all runs summary
@router.get("/summary")
async def funnel_summary_endpoint():
    """Get summary of all funnel runs with aggregate statistics."""
    from ...reasoning.screening_funnel import funnel_summary

    return await funnel_summary()


# POST /funnel/estimate — estimate drug-likeness for a single SMILES
@router.post("/estimate")
async def estimate_single(body: dict):
    """Estimate drug-likeness properties for a single SMILES (no RDKit)."""
    from ...reasoning.screening_funnel import estimate_drug_likeness

    smiles = body.get("smiles", "")
    if not smiles or len(smiles) > 5000:
        raise HTTPException(400, "Invalid or missing SMILES string")

    return estimate_drug_likeness(smiles)
