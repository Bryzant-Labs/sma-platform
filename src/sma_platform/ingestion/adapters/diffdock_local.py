"""
Self-hosted DiffDock Adapter (Vast.ai GPU)
===========================================
Runs DiffDock locally on a rented A100 GPU instead of the NVIDIA NIM cloud API.
Designed for high-throughput virtual screening (100k+ compounds).

Architecture:
- Launch a Vast.ai instance with the official NVIDIA DiffDock container
- Send batches of compounds to the self-hosted DiffDock REST API
- Tear down the instance when the screening campaign is done

Container: nvcr.io/nim/mit/diffdock:2.0.1
Requires: NGC_API_KEY env var for pulling the container, vastai CLI installed.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import os

import httpx

logger = logging.getLogger(__name__)

# DiffDock local REST API path (the NIM container exposes this)
DOCK_ENDPOINT = "/molecular-docking/diffdock/generate"
HEALTH_ENDPOINT = "/v1/health/ready"

# Vast.ai configuration
DIFFDOCK_IMAGE = "nvcr.io/nim/mit/diffdock:2.0.1"
DEFAULT_GPU_TYPE = "RTX_A6000"  # Fallback; A100 preferred
BATCH_CONCURRENCY = 10  # Parallel requests per batch
REQUEST_TIMEOUT = 120  # seconds per docking request

# Cost model (approximate, A100 80GB on Vast.ai)
A100_COST_PER_HOUR = 1.50  # USD
COMPOUNDS_PER_SEC_A100 = 5.0  # Empirical throughput


# =============================================================================
# Core: Batch Docking
# =============================================================================

async def dock_batch_local(
    compounds: list[dict],
    target_pdb: str,
    gpu_instance_url: str,
    num_poses: int = 3,
) -> list[dict]:
    """Send a batch of compounds to a self-hosted DiffDock instance on Vast.ai.

    Processes compounds in parallel batches of BATCH_CONCURRENCY concurrent
    requests for maximum GPU utilization.

    Args:
        compounds: List of dicts, each with 'name' and 'sdf_content' keys.
        target_pdb: PDB file content (string) of the protein target.
        gpu_instance_url: Base URL of the DiffDock instance (e.g. http://1.2.3.4:8000).
        num_poses: Number of binding poses to generate per compound.

    Returns:
        List of result dicts with keys: compound, target, confidence, poses.
    """
    if not compounds:
        return []

    url = f"{gpu_instance_url.rstrip('/')}{DOCK_ENDPOINT}"
    results: list[dict] = []
    total = len(compounds)

    logger.info(
        "DiffDock local: Docking %d compounds (%d poses each) against %s",
        total, num_poses, gpu_instance_url,
    )

    # Process in batches of BATCH_CONCURRENCY
    for batch_start in range(0, total, BATCH_CONCURRENCY):
        batch = compounds[batch_start : batch_start + BATCH_CONCURRENCY]
        batch_num = batch_start // BATCH_CONCURRENCY + 1
        total_batches = math.ceil(total / BATCH_CONCURRENCY)

        logger.info(
            "DiffDock local: Batch %d/%d (%d compounds)",
            batch_num, total_batches, len(batch),
        )

        tasks = [
            _dock_single(url, compound, target_pdb, num_poses)
            for compound in batch
        ]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        for compound, result in zip(batch, batch_results):
            if isinstance(result, Exception):
                logger.warning(
                    "DiffDock local: Failed to dock '%s': %s",
                    compound.get("name", "unknown"), result,
                )
                results.append({
                    "compound": compound.get("name", "unknown"),
                    "target": "protein",
                    "confidence": None,
                    "poses": [],
                    "error": str(result),
                })
            else:
                results.append(result)

    succeeded = sum(1 for r in results if r.get("confidence") is not None)
    logger.info(
        "DiffDock local: Completed %d/%d compounds successfully",
        succeeded, total,
    )
    return results


async def _dock_single(
    url: str,
    compound: dict,
    target_pdb: str,
    num_poses: int,
) -> dict:
    """Dock a single compound against the target via the local DiffDock API.

    Args:
        url: Full endpoint URL for docking.
        compound: Dict with 'name' and 'sdf_content'.
        target_pdb: PDB file content.
        num_poses: Number of poses to generate.

    Returns:
        Dict with compound name, confidence, and poses.
    """
    payload = {
        "ligand": compound["sdf_content"],
        "ligand_file_type": "sdf",
        "protein": target_pdb,
        "num_poses": num_poses,
        "time_divisions": 20,
        "steps": 18,
    }

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    # Extract best confidence from poses
    poses = data.get("poses", [])
    best_confidence = None
    if poses:
        confidences = [p.get("confidence", 0) for p in poses if "confidence" in p]
        best_confidence = max(confidences) if confidences else None

    return {
        "compound": compound.get("name", "unknown"),
        "target": "protein",
        "confidence": best_confidence,
        "poses": poses,
    }


# =============================================================================
# Instance Lifecycle: Launch / Health / Destroy
# =============================================================================

async def launch_diffdock_instance() -> dict:
    """Launch a Vast.ai instance with the DiffDock NIM container.

    Uses the vastai CLI to find an available A100 GPU and start the container.
    The NGC_API_KEY environment variable must be set for pulling the NVIDIA
    container from nvcr.io.

    Returns:
        Dict with instance_id, ssh_url, api_url.

    Raises:
        RuntimeError: If vastai CLI is not installed or launch fails.
        ValueError: If NGC_API_KEY is not set.
    """
    ngc_key = os.environ.get("NGC_API_KEY", "")
    if not ngc_key:
        raise ValueError(
            "NGC_API_KEY environment variable not set. "
            "Required to pull the DiffDock container from nvcr.io."
        )

    # Verify vastai CLI is available
    try:
        proc = await asyncio.create_subprocess_exec(
            "vastai", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.wait()
        if proc.returncode != 0:
            raise RuntimeError("vastai CLI returned non-zero exit code")
    except FileNotFoundError:
        raise RuntimeError(
            "vastai CLI not installed. Install: pip install vastai"
        )

    # Search for available A100 instances
    logger.info("DiffDock local: Searching for A100 GPU instances on Vast.ai...")
    try:
        search_proc = await asyncio.create_subprocess_exec(
            "vastai", "search", "offers",
            "--type", "on-demand",
            "--gpu-name", "A100_SXM4",
            "--num-gpus", "1",
            "--disk", "50",
            "--order", "dph",
            "--limit", "1",
            "--raw",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await search_proc.communicate()
    except Exception as e:
        raise RuntimeError(f"Failed to search Vast.ai offers: {e}")

    if search_proc.returncode != 0:
        error_msg = stderr.decode().strip() if stderr else "Unknown error"
        raise RuntimeError(f"vastai search failed: {error_msg}")

    # Parse the cheapest offer
    raw_output = stdout.decode().strip()
    if not raw_output:
        raise RuntimeError("No A100 instances available on Vast.ai right now")

    try:
        offers = json.loads(raw_output)
        if isinstance(offers, list) and offers:
            offer = offers[0]
        else:
            raise RuntimeError("No A100 instances available on Vast.ai right now")
    except json.JSONDecodeError:
        raise RuntimeError(f"Could not parse vastai output: {raw_output[:200]}")

    offer_id = offer.get("id")
    if not offer_id:
        raise RuntimeError("Vast.ai offer has no ID")

    cost_per_hour = offer.get("dph_total", 0)
    gpu_name = offer.get("gpu_name", "A100")
    logger.info(
        "DiffDock local: Found %s at $%.2f/hr (offer %s)",
        gpu_name, cost_per_hour, offer_id,
    )

    # Launch the instance with DiffDock container
    env_args = f"-e NGC_API_KEY={ngc_key}"
    create_proc = await asyncio.create_subprocess_exec(
        "vastai", "create", "instance", str(offer_id),
        "--image", DIFFDOCK_IMAGE,
        "--env", env_args,
        "--disk", "50",
        "--direct",
        "--raw",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    create_stdout, create_stderr = await create_proc.communicate()

    if create_proc.returncode != 0:
        error_msg = create_stderr.decode().strip() if create_stderr else "Unknown error"
        raise RuntimeError(f"Failed to create Vast.ai instance: {error_msg}")

    try:
        create_data = json.loads(create_stdout.decode())
        instance_id = str(create_data.get("new_contract") or create_data.get("id", ""))
    except (json.JSONDecodeError, AttributeError):
        # Fallback: parse text output
        instance_id = create_stdout.decode().strip().split()[-1] if create_stdout else ""

    if not instance_id:
        raise RuntimeError("Could not determine instance ID from vastai output")

    logger.info("DiffDock local: Instance %s created. Waiting for SSH info...", instance_id)

    # Poll for instance to become ready (get SSH info and public IP)
    ssh_url = ""
    api_url = ""
    for _attempt in range(30):
        await asyncio.sleep(10)
        info_proc = await asyncio.create_subprocess_exec(
            "vastai", "show", "instance", instance_id, "--raw",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        info_stdout, _ = await info_proc.communicate()
        try:
            info = json.loads(info_stdout.decode())
            if isinstance(info, list) and info:
                info = info[0]
            status = info.get("actual_status", "")
            public_ip = info.get("public_ipaddr", "")
            ports = info.get("ports", {})

            if status == "running" and public_ip:
                # Find the mapped port for 8000
                port_8000 = ports.get("8000/tcp", [{}])
                if isinstance(port_8000, list) and port_8000:
                    mapped_port = port_8000[0].get("HostPort", "8000")
                elif isinstance(port_8000, (int, str)):
                    mapped_port = str(port_8000)
                else:
                    mapped_port = "8000"

                ssh_port = ports.get("22/tcp", [{}])
                if isinstance(ssh_port, list) and ssh_port:
                    ssh_mapped = ssh_port[0].get("HostPort", "22")
                elif isinstance(ssh_port, (int, str)):
                    ssh_mapped = str(ssh_port)
                else:
                    ssh_mapped = "22"

                ssh_url = f"ssh://root@{public_ip}:{ssh_mapped}"
                api_url = f"http://{public_ip}:{mapped_port}"
                break
        except (json.JSONDecodeError, KeyError, TypeError):
            continue

    if not api_url:
        logger.warning(
            "DiffDock local: Instance %s created but API URL not yet available. "
            "Check status manually: vastai show instance %s",
            instance_id, instance_id,
        )

    result = {
        "instance_id": instance_id,
        "ssh_url": ssh_url,
        "api_url": api_url,
        "gpu": gpu_name,
        "cost_per_hour": cost_per_hour,
        "image": DIFFDOCK_IMAGE,
        "status": "running" if api_url else "starting",
    }

    logger.info("DiffDock local: Instance ready: %s", result)
    return result


async def check_instance_health(api_url: str) -> bool:
    """Check if the DiffDock instance is ready to accept docking requests.

    Args:
        api_url: Base URL of the DiffDock instance (e.g. http://1.2.3.4:8000).

    Returns:
        True if the instance is healthy and ready, False otherwise.
    """
    url = f"{api_url.rstrip('/')}{HEALTH_ENDPOINT}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                logger.info("DiffDock local: Instance at %s is healthy", api_url)
                return True
            logger.warning(
                "DiffDock local: Health check returned %d at %s",
                resp.status_code, api_url,
            )
            return False
    except httpx.TimeoutException:
        logger.warning("DiffDock local: Health check timed out at %s", api_url)
        return False
    except httpx.ConnectError:
        logger.warning("DiffDock local: Cannot connect to %s", api_url)
        return False
    except Exception as e:
        logger.warning("DiffDock local: Health check failed at %s: %s", api_url, e)
        return False


async def destroy_instance(instance_id: str) -> bool:
    """Destroy a Vast.ai instance when the screening campaign is done.

    Args:
        instance_id: The Vast.ai instance/contract ID to destroy.

    Returns:
        True if the instance was successfully destroyed, False otherwise.
    """
    logger.info("DiffDock local: Destroying instance %s", instance_id)
    try:
        proc = await asyncio.create_subprocess_exec(
            "vastai", "destroy", "instance", str(instance_id),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            logger.info("DiffDock local: Instance %s destroyed successfully", instance_id)
            return True

        error_msg = stderr.decode().strip() if stderr else "Unknown error"
        logger.warning(
            "DiffDock local: Failed to destroy instance %s: %s",
            instance_id, error_msg,
        )
        return False
    except FileNotFoundError:
        logger.error("DiffDock local: vastai CLI not found — cannot destroy instance")
        return False
    except Exception as e:
        logger.error("DiffDock local: Error destroying instance %s: %s", instance_id, e)
        return False


# =============================================================================
# Cost Estimation
# =============================================================================

def estimate_cost(n_compounds: int, n_targets: int = 1) -> dict:
    """Estimate GPU cost for a virtual screening campaign.

    Based on empirical throughput of ~5 compounds/sec on an A100 80GB GPU
    running DiffDock 2.0.1.

    Args:
        n_compounds: Number of compounds to screen.
        n_targets: Number of protein targets to dock against (multiplier).

    Returns:
        Dict with estimated_time (human-readable), estimated_hours,
        estimated_cost (USD), compounds_per_dollar, and breakdown.
    """
    total_dockings = n_compounds * n_targets
    total_seconds = total_dockings / COMPOUNDS_PER_SEC_A100
    total_hours = total_seconds / 3600
    total_cost = total_hours * A100_COST_PER_HOUR
    compounds_per_dollar = total_dockings / total_cost if total_cost > 0 else float("inf")

    # Human-readable time
    if total_seconds < 60:
        time_str = f"{total_seconds:.0f} seconds"
    elif total_seconds < 3600:
        time_str = f"{total_seconds / 60:.1f} minutes"
    elif total_hours < 24:
        time_str = f"{total_hours:.1f} hours"
    else:
        time_str = f"{total_hours / 24:.1f} days"

    return {
        "n_compounds": n_compounds,
        "n_targets": n_targets,
        "total_dockings": total_dockings,
        "estimated_time": time_str,
        "estimated_hours": round(total_hours, 2),
        "estimated_cost_usd": round(total_cost, 2),
        "compounds_per_dollar": round(compounds_per_dollar, 0),
        "throughput": f"~{COMPOUNDS_PER_SEC_A100:.0f} compounds/sec on A100",
        "gpu_cost_per_hour": A100_COST_PER_HOUR,
        "breakdown": {
            "per_compound_seconds": round(n_targets / COMPOUNDS_PER_SEC_A100, 3),
            "per_compound_cost_usd": round(
                (n_targets / COMPOUNDS_PER_SEC_A100) * (A100_COST_PER_HOUR / 3600), 6
            ),
        },
    }
