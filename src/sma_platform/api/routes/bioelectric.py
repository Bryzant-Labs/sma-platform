"""Bioelectric Reprogramming API routes (Phase 7.5 — DB-driven).

Replaces hardcoded data from reasoning/bioelectric_module.py with
PostgreSQL queries against bioelectric_channels, bioelectric_vmem_states,
and bioelectric_interventions tables.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ...core.database import execute, fetch, fetchrow
from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# GET /bioelectric/channels
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/bioelectric/channels")
async def ion_channels(
    channel_type: str | None = Query(default=None, description="Na, K, Ca, Cl, HCN"),
    vmem_role: str | None = Query(default=None, description="depolarizing, repolarizing, resting, modulatory"),
    sma_expression: str | None = Query(default=None, description="upregulated, downregulated, unchanged, dysregulated"),
    therapeutic_only: bool = Query(default=False),
):
    """Get ion channel expression profile in SMA motor neurons."""
    conditions = []
    args: list = []

    if channel_type:
        args.append(channel_type)
        conditions.append(f"channel_type = ${len(args)}")
    if vmem_role:
        args.append(vmem_role)
        conditions.append(f"vmem_role = ${len(args)}")
    if sma_expression:
        args.append(sma_expression)
        conditions.append(f"sma_expression = ${len(args)}")
    if therapeutic_only:
        conditions.append("therapeutic_target = TRUE")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = await fetch(
        f"SELECT * FROM bioelectric_channels {where} ORDER BY channel_type, gene",
        *args,
    )

    channels = [dict(r) for r in rows]

    # Build expression summary
    by_status: dict[str, list[str]] = {
        "upregulated": [], "downregulated": [], "unchanged": [], "dysregulated": []
    }
    for ch in channels:
        expr = ch.get("sma_expression") or "unchanged"
        if expr in by_status:
            by_status[expr].append(ch["gene"])

    therapeutic = [ch for ch in channels if ch.get("therapeutic_target")]

    return {
        "total_channels": len(channels),
        "channels": channels,
        "expression_summary": {k: len(v) for k, v in by_status.items()},
        "therapeutic_targets": therapeutic,
        "net_vmem_shift": "hyperpolarizing",
        "insight": (
            "SMA motor neurons show a net hyperpolarizing shift: Na+ channels downregulated "
            "(less depolarization) while K+ channels upregulated (more repolarization). "
            "This creates electrically silent MNs that are alive but non-functional — "
            "the key target for bioelectric intervention."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /bioelectric/vmem
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/bioelectric/vmem")
async def vmem_states():
    """Get Vmem state classification for SMA motor neurons."""
    rows = await fetch(
        "SELECT * FROM bioelectric_vmem_states ORDER BY prevalence_in_sma DESC NULLS LAST"
    )
    states = [dict(r) for r in rows]

    # Cast Decimal prevalence to float for arithmetic
    for s in states:
        if s.get("prevalence_in_sma") is not None:
            s["prevalence_in_sma"] = float(s["prevalence_in_sma"])

    rescuable_states = {"Healthy resting", "Hyperpolarized (silenced)"}
    rescuable_fraction = sum(
        s["prevalence_in_sma"]
        for s in states
        if s["state_name"] in rescuable_states and s.get("prevalence_in_sma") is not None
    )

    return {
        "total_states": len(states),
        "states": states,
        "rescuable_fraction": round(rescuable_fraction, 3),
        "insight": (
            f"~{int(rescuable_fraction * 100)}% of SMA motor neurons are potentially rescuable "
            "(15% healthy + 40% silenced). The 40% 'silenced' population is the prime target "
            "for bioelectric therapy — these MNs are alive but electrically dormant."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /bioelectric/electroceuticals
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/bioelectric/electroceuticals")
async def electroceuticals(
    modality: str | None = Query(default=None),
    evidence_level: str | None = Query(default=None, description="clinical, preclinical, theoretical"),
):
    """Get electroceutical interventions for SMA."""
    conditions = []
    args: list = []

    if modality:
        args.append(modality)
        conditions.append(f"modality = ${len(args)}")
    if evidence_level:
        args.append(evidence_level)
        conditions.append(f"evidence_level = ${len(args)}")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = await fetch(
        f"SELECT * FROM bioelectric_interventions {where} ORDER BY feasibility DESC NULLS LAST",
        *args,
    )

    interventions = [dict(r) for r in rows]
    for iv in interventions:
        if iv.get("feasibility") is not None:
            iv["feasibility"] = float(iv["feasibility"])

    most_feasible = max(interventions, key=lambda x: x.get("feasibility") or 0) if interventions else None
    clinical_ready = [iv for iv in interventions if iv.get("evidence_level") == "clinical"]

    return {
        "total_interventions": len(interventions),
        "interventions": interventions,
        "most_feasible": most_feasible,
        "clinical_ready": clinical_ready,
        "insight": (
            "FES (functional electrical stimulation) is the most immediately actionable "
            "bioelectric intervention for SMA — it's already clinically used and maintains "
            "muscle health while SMN therapy works on the neurons. Transcutaneous spinal "
            "stimulation is the most promising novel approach for reactivating silenced MNs."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /bioelectric/profile
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/bioelectric/profile")
async def bioelectric_profile():
    """Full bioelectric analysis of SMA motor neurons."""
    channels_data = await ion_channels(channel_type=None, vmem_role=None, sma_expression=None, therapeutic_only=False)
    vmem_data = await vmem_states()
    electro_data = await electroceuticals(modality=None, evidence_level=None)

    return {
        "ion_channels": channels_data,
        "vmem_states": vmem_data,
        "electroceuticals": electro_data,
        "bioelectric_hypothesis": (
            "SMA motor neurons don't just die — many enter a 'bioelectric dormancy' state "
            "where they're alive but electrically silent due to ion channel dysregulation. "
            "This dormancy can be reversed with targeted depolarization (K+ channel blockers, "
            "spinal cord stimulation) BEFORE the neuron commits to apoptosis. The therapeutic "
            "window for bioelectric rescue exists between SMN depletion and irreversible death."
        ),
        "combination_approach": {
            "step_1": "SMN restoration (nusinersen/risdiplam/Zolgensma) — address root cause",
            "step_2": "Bioelectric reactivation (spinal stimulation or 4-AP) — wake dormant MNs",
            "step_3": "NMJ maintenance (FES + exercise) — keep reactivated MNs connected",
            "step_4": "Retrograde support (muscle-derived BDNF) — sustain rescued MNs",
            "rationale": (
                "Four-pronged approach: fix the gene, wake the neuron, maintain the "
                "connection, feed the circuit."
            ),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Admin CRUD endpoints
# ─────────────────────────────────────────────────────────────────────────────

class ChannelCreate(BaseModel):
    gene: str
    channel_name: str
    channel_type: str
    vmem_role: str | None = None
    sma_expression: str | None = None
    sma_impact: str | None = None
    therapeutic_target: bool = False
    drug_candidates: list[str] = []
    metadata: dict = {}


class InterventionCreate(BaseModel):
    name: str
    modality: str | None = None
    target_vmem_state: str | None = None
    mechanism: str | None = None
    evidence_level: str | None = None
    feasibility: float | None = None
    sma_specific_notes: str | None = None
    metadata: dict = {}


@router.post("/admin/bioelectric/channels", dependencies=[Depends(require_admin_key)])
async def add_channel(body: ChannelCreate):
    """Add a new ion channel entry."""
    import json
    row = await fetchrow(
        """INSERT INTO bioelectric_channels
           (gene, channel_name, channel_type, vmem_role, sma_expression, sma_impact,
            therapeutic_target, drug_candidates, metadata)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb)
           RETURNING *""",
        body.gene.upper(), body.channel_name, body.channel_type, body.vmem_role,
        body.sma_expression, body.sma_impact, body.therapeutic_target,
        body.drug_candidates, json.dumps(body.metadata),
    )
    return dict(row)


@router.put("/admin/bioelectric/channels/{gene}", dependencies=[Depends(require_admin_key)])
async def update_channel(gene: str, body: ChannelCreate):
    """Update an existing ion channel by gene symbol."""
    import json
    row = await fetchrow(
        """UPDATE bioelectric_channels SET
           channel_name=$1, channel_type=$2, vmem_role=$3, sma_expression=$4,
           sma_impact=$5, therapeutic_target=$6, drug_candidates=$7, metadata=$8::jsonb
           WHERE gene=$9 RETURNING *""",
        body.channel_name, body.channel_type, body.vmem_role, body.sma_expression,
        body.sma_impact, body.therapeutic_target, body.drug_candidates,
        json.dumps(body.metadata), gene.upper(),
    )
    if not row:
        from fastapi import HTTPException
        raise HTTPException(404, f"Channel {gene} not found")
    return dict(row)


@router.post("/admin/bioelectric/interventions", dependencies=[Depends(require_admin_key)])
async def add_intervention(body: InterventionCreate):
    """Add a new bioelectric intervention."""
    import json
    row = await fetchrow(
        """INSERT INTO bioelectric_interventions
           (name, modality, target_vmem_state, mechanism, evidence_level,
            feasibility, sma_specific_notes, metadata)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8::jsonb)
           RETURNING *""",
        body.name, body.modality, body.target_vmem_state, body.mechanism,
        body.evidence_level, body.feasibility, body.sma_specific_notes,
        json.dumps(body.metadata),
    )
    return dict(row)
