"""Molecule screening endpoints — ChEMBL / PubChem bioactive compound search.

Routes
------
GET  /screen/molecules              — public stats (no auth required)
GET  /screen/molecules/status       — background screening status
POST /screen/molecules/target       — screen a single target symbol  (admin, background)
POST /screen/molecules/all          — screen every target in the DB   (admin, background)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter()

# Background task tracking
_screen_status: dict = {
    "running": False,
    "current_target": None,
    "last_result": None,
    "last_error": None,
    "started_at": None,
}


async def _run_screen_background(symbol: str | None, batch_size: int, force: bool):
    """Run molecule screening as background task."""
    global _screen_status
    _screen_status["running"] = True
    _screen_status["last_error"] = None
    _screen_status["started_at"] = datetime.now(timezone.utc).isoformat()

    try:
        if symbol:
            from ...reasoning.molecule_screener import screen_target
            _screen_status["current_target"] = symbol
            result = await screen_target(symbol=symbol, skip_existing=not force)
        else:
            from ...reasoning.molecule_screener import screen_all_targets
            _screen_status["current_target"] = "all"
            result = await screen_all_targets(skip_existing=not force, batch_size=batch_size)
        _screen_status["last_result"] = result
    except Exception as exc:
        logger.error("Background molecule screen failed: %s", exc, exc_info=True)
        _screen_status["last_error"] = str(exc)
    finally:
        _screen_status["running"] = False
        _screen_status["current_target"] = None


@router.get("/screen/molecules")
async def get_molecule_screening_stats():
    """Return aggregate statistics for the molecule_screenings table."""
    from ...reasoning.molecule_screener import get_screening_stats

    try:
        stats = await get_screening_stats()
        stats["screening_running"] = _screen_status["running"]
        return stats
    except Exception as exc:
        logger.error("Failed to fetch molecule screening stats: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve screening statistics")


@router.get("/screen/molecules/status")
async def get_screening_status():
    """Get background screening task status."""
    return _screen_status


@router.post("/screen/molecules/target", dependencies=[Depends(require_admin_key)])
async def screen_molecules_for_target(
    symbol: str = Query(..., description="Gene/target symbol, e.g. SMN1 or NCALD"),
    force: bool = Query(default=False, description="Re-screen even if results already exist"),
):
    """Screen ChEMBL and PubChem for bioactive compounds against *symbol*.

    Runs as a background task to avoid Nginx timeout. Check status via
    GET /screen/molecules/status.
    """
    if _screen_status["running"]:
        return {
            "status": "already_running",
            "current_target": _screen_status["current_target"],
            "started_at": _screen_status["started_at"],
        }

    if not symbol or len(symbol.strip()) == 0:
        raise HTTPException(status_code=400, detail="symbol query parameter is required")

    symbol = symbol.strip().upper()
    asyncio.create_task(_run_screen_background(symbol=symbol, batch_size=1, force=force))
    return {"status": "started", "target": symbol, "force": force}


@router.post("/screen/molecules/all", dependencies=[Depends(require_admin_key)])
async def screen_molecules_all_targets(
    batch_size: int = Query(default=5, ge=1, le=21, description="Targets per batch"),
    force: bool = Query(default=False, description="Re-screen targets that already have results"),
):
    """Screen every target in the targets table against ChEMBL and PubChem.

    Runs as a background task. Check progress via GET /screen/molecules/status.
    """
    if _screen_status["running"]:
        return {
            "status": "already_running",
            "current_target": _screen_status["current_target"],
            "started_at": _screen_status["started_at"],
        }

    asyncio.create_task(_run_screen_background(symbol=None, batch_size=batch_size, force=force))
    return {"status": "started", "batch_size": batch_size, "force": force}
