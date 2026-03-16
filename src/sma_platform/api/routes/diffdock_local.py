"""Self-hosted DiffDock endpoints — high-throughput GPU docking via Vast.ai."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class CompoundInput(BaseModel):
    name: str
    sdf_content: str


class BatchDockRequest(BaseModel):
    compounds: list[CompoundInput]
    target_pdb: str
    gpu_instance_url: str
    num_poses: int = 3


class DestroyRequest(BaseModel):
    instance_id: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/dock/local/batch", dependencies=[Depends(require_admin_key)])
async def dock_batch(body: BatchDockRequest):
    """Dock a batch of compounds against a self-hosted DiffDock instance.

    Sends compounds in parallel batches of 10 to the GPU instance.
    Requires admin key — this triggers GPU compute costs.
    """
    from ...ingestion.adapters.diffdock_local import dock_batch_local

    if not body.compounds:
        raise HTTPException(400, "No compounds provided")
    if not body.target_pdb.strip():
        raise HTTPException(400, "target_pdb cannot be empty")
    if not body.gpu_instance_url.strip():
        raise HTTPException(400, "gpu_instance_url cannot be empty")
    if len(body.compounds) > 100_000:
        raise HTTPException(400, "Maximum 100,000 compounds per batch request")

    compounds = [{"name": c.name, "sdf_content": c.sdf_content} for c in body.compounds]

    try:
        results = await dock_batch_local(
            compounds=compounds,
            target_pdb=body.target_pdb,
            gpu_instance_url=body.gpu_instance_url,
            num_poses=body.num_poses,
        )
    except Exception as e:
        logger.error("DiffDock local batch docking failed: %s", e, exc_info=True)
        raise HTTPException(502, f"Docking failed: {e}")

    succeeded = sum(1 for r in results if r.get("confidence") is not None)
    failed = len(results) - succeeded

    return {
        "total": len(results),
        "succeeded": succeeded,
        "failed": failed,
        "results": results,
    }


@router.post("/dock/local/launch", dependencies=[Depends(require_admin_key)])
async def launch_instance():
    """Launch a Vast.ai GPU instance with the DiffDock NIM container.

    Requires NGC_API_KEY env var and vastai CLI installed.
    Returns the instance ID, SSH URL, and API URL for docking.
    """
    from ...ingestion.adapters.diffdock_local import launch_diffdock_instance

    try:
        result = await launch_diffdock_instance()
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(502, str(e))
    except Exception as e:
        logger.error("Failed to launch DiffDock instance: %s", e, exc_info=True)
        raise HTTPException(500, f"Launch failed: {e}")

    return result


@router.get("/dock/local/health")
async def health_check(
    url: str = Query(..., description="Base URL of the DiffDock instance"),
):
    """Check if a self-hosted DiffDock instance is healthy and ready.

    No admin key required — useful for monitoring.
    """
    from ...ingestion.adapters.diffdock_local import check_instance_health

    if not url.strip():
        raise HTTPException(400, "url parameter is required")

    healthy = await check_instance_health(url)
    return {
        "url": url,
        "healthy": healthy,
        "status": "ready" if healthy else "not_ready",
    }


@router.post("/dock/local/destroy", dependencies=[Depends(require_admin_key)])
async def destroy(body: DestroyRequest):
    """Destroy a Vast.ai DiffDock instance when screening is complete.

    Always destroy instances after use to avoid ongoing GPU charges.
    """
    from ...ingestion.adapters.diffdock_local import destroy_instance

    if not body.instance_id.strip():
        raise HTTPException(400, "instance_id cannot be empty")

    success = await destroy_instance(body.instance_id)
    if not success:
        raise HTTPException(502, f"Failed to destroy instance {body.instance_id}")

    return {
        "instance_id": body.instance_id,
        "destroyed": True,
    }


@router.get("/dock/local/estimate")
async def cost_estimate(
    compounds: int = Query(..., ge=1, description="Number of compounds to screen"),
    targets: int = Query(default=1, ge=1, le=50, description="Number of protein targets"),
):
    """Estimate GPU cost and time for a virtual screening campaign.

    Based on ~5 compounds/sec throughput on A100 at ~$1.50/hr.
    No admin key required — informational endpoint.
    """
    from ...ingestion.adapters.diffdock_local import estimate_cost

    return estimate_cost(n_compounds=compounds, n_targets=targets)
