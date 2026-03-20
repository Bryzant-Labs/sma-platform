"""Milestone Tracker — auto-creates follow-up tasks for screening hits.

When virtual screening finds positive hits, automatically generates
a validation pipeline with concrete next steps for each hit.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from ..core.database import execute, fetch, fetchval

logger = logging.getLogger(__name__)

# Validation pipeline stages for each hit
VALIDATION_STAGES = [
    {"stage": "computational_validation", "description": "Cross-reference against ChEMBL, PubMed, PubChem. Assess novelty.", "effort": "1h"},
    {"stage": "structural_analysis", "description": "Analyze binding pose, key interactions, pharmacophore features.", "effort": "2h"},
    {"stage": "analog_search", "description": "Search for structurally similar approved drugs or clinical candidates.", "effort": "1h"},
    {"stage": "admet_prediction", "description": "Predict ADMET properties: absorption, metabolism, toxicity, BBB penetration.", "effort": "1h"},
    {"stage": "literature_review", "description": "Deep literature review on this scaffold class for the target.", "effort": "2h"},
    {"stage": "experimental_suggestion", "description": "Design wet-lab validation experiment: assay, model, readouts, go/no-go.", "effort": "2h"},
]


async def ensure_milestone_table():
    """Create milestones table if it doesn't exist."""
    await execute("""
        CREATE TABLE IF NOT EXISTS screening_milestones (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            hit_smiles TEXT NOT NULL,
            hit_target TEXT NOT NULL,
            docking_confidence NUMERIC(6,3),
            stage TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'skipped')),
            result TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            completed_at TIMESTAMPTZ,
            UNIQUE(hit_smiles, hit_target, stage)
        )
    """)


async def create_milestones_for_hit(
    smiles: str,
    target: str,
    docking_confidence: float,
    compound_name: str | None = None,
) -> list[dict]:
    """Create validation milestones for a positive screening hit."""
    await ensure_milestone_table()

    milestones = []
    for stage_info in VALIDATION_STAGES:
        try:
            mid = await fetchval(
                """INSERT INTO screening_milestones
                   (hit_smiles, hit_target, docking_confidence, stage, description)
                   VALUES ($1, $2, $3, $4, $5)
                   ON CONFLICT (hit_smiles, hit_target, stage) DO NOTHING
                   RETURNING id""",
                smiles, target, docking_confidence,
                stage_info["stage"], stage_info["description"],
            )
            milestones.append({
                "id": str(mid) if mid else "exists",
                "stage": stage_info["stage"],
                "description": stage_info["description"],
                "effort": stage_info["effort"],
                "status": "pending",
            })
        except Exception as e:
            logger.debug("Milestone creation: %s", e)

    logger.info(
        "Created %d milestones for %s → %s (dock=%+.3f)",
        len(milestones), smiles[:20], target, docking_confidence,
    )
    return milestones


async def create_milestones_for_campaign(hits: list[dict]) -> dict:
    """Create milestones for all positive hits in a screening campaign."""
    await ensure_milestone_table()

    total_created = 0
    hit_milestones = []

    for hit in hits:
        if hit.get("docking_confidence", -999) <= 0:
            continue
        ms = await create_milestones_for_hit(
            smiles=hit["smiles"],
            target=hit["target"],
            docking_confidence=hit["docking_confidence"],
            compound_name=hit.get("pubchem_name"),
        )
        total_created += len(ms)
        hit_milestones.append({
            "smiles": hit["smiles"],
            "target": hit["target"],
            "confidence": hit["docking_confidence"],
            "milestones": len(ms),
        })

    return {
        "hits_processed": len(hit_milestones),
        "milestones_created": total_created,
        "stages_per_hit": len(VALIDATION_STAGES),
        "hits": hit_milestones,
    }


async def get_milestone_summary() -> dict:
    """Get summary of all screening milestones."""
    await ensure_milestone_table()

    rows = await fetch("""
        SELECT hit_target, hit_smiles, docking_confidence, stage, status
        FROM screening_milestones
        ORDER BY docking_confidence DESC, hit_target, stage
    """)

    by_hit = {}
    for r in rows:
        key = f"{r['hit_target']}:{r['hit_smiles']}"
        if key not in by_hit:
            by_hit[key] = {
                "target": r["hit_target"],
                "smiles": r["hit_smiles"],
                "confidence": float(r["docking_confidence"]),
                "stages": {},
            }
        by_hit[key]["stages"][r["stage"]] = r["status"]

    total = len(rows)
    completed = sum(1 for r in rows if r["status"] == "completed")
    pending = sum(1 for r in rows if r["status"] == "pending")

    return {
        "total_milestones": total,
        "completed": completed,
        "pending": pending,
        "in_progress": total - completed - pending,
        "hits": list(by_hit.values()),
    }
