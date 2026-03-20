"""Agentic Drug Discovery API routes — autonomous campaign orchestration.

Endpoints
---------
POST /agent/discover/{target}  — Launch a drug discovery campaign (admin)
GET  /agent/campaigns          — List past campaigns
GET  /agent/tools              — List available agent tools
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["agent"])


class DiscoveryCampaignRequest(BaseModel):
    scaffold: str = Field(
        default="Nc1ccncc1",
        description="Starting molecule scaffold (SMILES). Default: 4-AP.",
    )
    goal: str = Field(
        default="Find novel binding compounds with BBB permeability",
        description="Natural language description of campaign goal.",
    )
    max_candidates: int = Field(
        default=50, ge=5, le=200,
        description="Maximum number of candidates to process.",
    )


# Background task tracking
_campaign_status: dict = {
    "running": False,
    "target": None,
    "last_result": None,
    "last_error": None,
}


async def _run_campaign_background(target: str, scaffold: str, goal: str, max_candidates: int):
    """Run campaign as background task to avoid HTTP timeout."""
    global _campaign_status
    _campaign_status["running"] = True
    _campaign_status["target"] = target
    _campaign_status["last_error"] = None

    try:
        from ...agents.drug_discovery_agent import run_discovery_campaign
        result = await run_discovery_campaign(
            target=target,
            scaffold=scaffold,
            goal=goal,
            max_candidates=max_candidates,
        )
        _campaign_status["last_result"] = result
    except Exception as exc:
        logger.error("Background discovery campaign failed: %s", exc, exc_info=True)
        _campaign_status["last_error"] = str(exc)
    finally:
        _campaign_status["running"] = False
        _campaign_status["target"] = None


@router.post("/discover/{target}", dependencies=[Depends(require_admin_key)])
async def launch_discovery_campaign(target: str, req: DiscoveryCampaignRequest):
    """Launch an autonomous drug discovery campaign for the given target.

    Orchestrates the full pipeline:
      1. Check baseline convergence score
      2. Get candidate compounds from screening library
      3. Filter by drug-likeness (Lipinski, QED > 0.3, BBB)
      4. Dock via DiffDock NIM
      5. Rank by composite score
      6. Store results + milestones
      7. Return campaign summary

    Runs as background task to avoid HTTP timeouts (docking can take minutes).
    Check progress via GET /agent/campaigns.

    Requires NVIDIA_API_KEY for docking step.
    """
    if _campaign_status["running"]:
        return {
            "status": "already_running",
            "current_target": _campaign_status["target"],
            "message": "A campaign is already in progress. Check GET /agent/campaigns for status.",
        }

    target = target.strip().upper()
    if not target:
        raise HTTPException(400, "Target symbol is required")

    asyncio.create_task(_run_campaign_background(
        target=target,
        scaffold=req.scaffold,
        goal=req.goal,
        max_candidates=req.max_candidates,
    ))

    return {
        "status": "started",
        "target": target,
        "scaffold": req.scaffold,
        "goal": req.goal,
        "max_candidates": req.max_candidates,
        "message": "Campaign launched in background. Poll GET /api/v2/agent/campaigns for results.",
    }


@router.get("/campaigns")
async def list_campaigns():
    """List past discovery campaigns (most recent first) and current status."""
    from ...agents.drug_discovery_agent import list_campaigns as _list

    campaigns = await _list()
    return {
        "campaigns": campaigns,
        "total": len(campaigns),
        "running": _campaign_status["running"],
        "current_target": _campaign_status["target"],
        "last_error": _campaign_status["last_error"],
    }


@router.get("/tools")
async def list_tools():
    """List available tools for the drug discovery agent.

    Shows which NVIDIA NIMs are configured and ready, based on
    environment variables (NVIDIA_API_KEY, etc.).
    """
    from ...agents.drug_discovery_agent import list_agent_tools

    return await list_agent_tools()
