"""Experiment Design Suggestions — gap-driven assay recommendations.

For each target, analyzes claim_type distribution to find MISSING evidence
types and maps those gaps to concrete experimental assay recommendations.

Priority scoring: gap_size * target_importance * cost_efficiency

Evidence gap → assay mapping is based on standard SMA biology readouts:
- protein_interaction → Co-IP / SPR
- drug_efficacy → dose-response
- motor_function → mouse behavioral
- splicing_event → RT-PCR reporter
- biomarker → ELISA
- neuroprotection → iPSC-MN survival
"""

from __future__ import annotations

import logging
from typing import Any

from ..core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

# All claim_types from the schema CHECK constraint
ALL_CLAIM_TYPES = {
    "gene_expression",
    "protein_interaction",
    "pathway_membership",
    "drug_target",
    "drug_efficacy",
    "biomarker",
    "splicing_event",
    "neuroprotection",
    "motor_function",
    "survival",
    "safety",
    "other",
}

# Map missing evidence types to recommended assays
GAP_TO_ASSAY: dict[str, dict[str, Any]] = {
    "protein_interaction": {
        "assay": "Co-immunoprecipitation or SPR binding assay",
        "description": (
            "Use co-immunoprecipitation (co-IP) to confirm physical protein-protein "
            "interactions in motor neuron lysates, or surface plasmon resonance (SPR) "
            "for quantitative binding kinetics with purified recombinant proteins."
        ),
        "model_systems": ["HEK293T overexpression", "iPSC-derived motor neurons", "recombinant protein (SPR)"],
        "estimated_cost": "medium",
        "timeline_weeks": 4,
        "cost_rank": 3,  # 1=cheapest, 6=most expensive
    },
    "drug_efficacy": {
        "assay": "Cell-based dose-response assay",
        "description": (
            "Perform dose-response curves in SMN-deficient cell lines (e.g., SMA "
            "patient fibroblasts or iPSC-MNs) measuring SMN protein levels by ELISA "
            "or cell viability by CellTiter-Glo to establish EC50 values."
        ),
        "model_systems": ["SMA patient fibroblasts", "iPSC-derived motor neurons", "NSC-34 cells"],
        "estimated_cost": "medium",
        "timeline_weeks": 3,
        "cost_rank": 3,
    },
    "motor_function": {
        "assay": "SMA mouse model behavioral testing",
        "description": (
            "Assess motor function in SMA delta-7 or Taiwanese SMA mouse models "
            "using righting reflex, grip strength, rotarod performance, and "
            "body weight tracking over postnatal days 1-21."
        ),
        "model_systems": ["SMN-delta7 mouse", "Taiwanese SMA mouse", "C. elegans smn-1 mutant"],
        "estimated_cost": "high",
        "timeline_weeks": 12,
        "cost_rank": 5,
    },
    "splicing_event": {
        "assay": "RT-PCR splicing reporter assay",
        "description": (
            "Design SMN2 minigene splicing reporters to quantify exon 7 inclusion "
            "by RT-PCR. Use both endogenous SMN2 splicing (in patient fibroblasts) "
            "and minigene reporters (in HEK293T) for orthogonal validation."
        ),
        "model_systems": ["SMN2 minigene in HEK293T", "SMA patient fibroblasts", "iPSC-derived motor neurons"],
        "estimated_cost": "low",
        "timeline_weeks": 2,
        "cost_rank": 1,
    },
    "biomarker": {
        "assay": "Quantitative NfL/SMN protein ELISA",
        "description": (
            "Measure neurofilament light chain (NfL) in CSF or plasma, and SMN "
            "protein levels in PBMCs, using validated quantitative ELISA kits "
            "(Simoa for NfL, sandwich ELISA for SMN)."
        ),
        "model_systems": ["patient plasma/CSF samples", "PBMCs", "iPSC-MN conditioned media"],
        "estimated_cost": "medium",
        "timeline_weeks": 3,
        "cost_rank": 2,
    },
    "neuroprotection": {
        "assay": "iPSC-MN survival assay",
        "description": (
            "Differentiate SMA patient iPSCs into motor neurons and measure "
            "neuronal survival over 4-8 weeks in culture. Use automated imaging "
            "(IncuCyte or similar) to track neurite length and cell death."
        ),
        "model_systems": ["SMA patient iPSC-derived motor neurons", "primary mouse spinal cord cultures"],
        "estimated_cost": "high",
        "timeline_weeks": 10,
        "cost_rank": 5,
    },
    "gene_expression": {
        "assay": "RT-qPCR or RNA-seq expression profiling",
        "description": (
            "Quantify target gene expression in SMA vs control tissues using "
            "RT-qPCR for candidate genes or bulk/single-cell RNA-seq for "
            "transcriptome-wide profiling in motor neurons and muscle."
        ),
        "model_systems": ["SMA patient fibroblasts", "iPSC-derived motor neurons", "SMA mouse spinal cord"],
        "estimated_cost": "low",
        "timeline_weeks": 2,
        "cost_rank": 1,
    },
    "pathway_membership": {
        "assay": "Pathway perturbation with phospho-proteomics",
        "description": (
            "Apply pathway-specific inhibitors or activators in SMA cell models "
            "and profile downstream signaling by phospho-proteomics (TMT-labeled "
            "mass spectrometry) to map pathway membership and crosstalk."
        ),
        "model_systems": ["iPSC-derived motor neurons", "SMA mouse spinal cord tissue"],
        "estimated_cost": "high",
        "timeline_weeks": 8,
        "cost_rank": 6,
    },
    "drug_target": {
        "assay": "Target engagement assay (CETSA or DARTS)",
        "description": (
            "Confirm direct drug-target binding using Cellular Thermal Shift "
            "Assay (CETSA) in intact cells or Drug Affinity Responsive Target "
            "Stability (DARTS) with cell lysates."
        ),
        "model_systems": ["HEK293T cells", "SMA patient fibroblasts"],
        "estimated_cost": "medium",
        "timeline_weeks": 3,
        "cost_rank": 3,
    },
    "survival": {
        "assay": "SMA mouse model survival study",
        "description": (
            "Conduct Kaplan-Meier survival analysis in SMA delta-7 mice treated "
            "with the compound, monitoring body weight, motor milestones, and "
            "lifespan compared to vehicle-treated controls."
        ),
        "model_systems": ["SMN-delta7 mouse", "Taiwanese SMA mouse"],
        "estimated_cost": "high",
        "timeline_weeks": 16,
        "cost_rank": 6,
    },
    "safety": {
        "assay": "In vitro toxicity panel (hERG, hepatotoxicity, genotoxicity)",
        "description": (
            "Screen for common safety liabilities using hERG channel inhibition "
            "assay, HepG2 hepatotoxicity, Ames test for genotoxicity, and "
            "mitochondrial toxicity (Glu/Gal assay)."
        ),
        "model_systems": ["HEK293-hERG cells", "HepG2 hepatocytes", "bacterial strains (Ames)"],
        "estimated_cost": "medium",
        "timeline_weeks": 4,
        "cost_rank": 4,
    },
}


async def _get_target_claim_profile(target_symbol: str) -> dict[str, Any] | None:
    """Get claim type counts for a target, identified by symbol."""
    target = await fetchrow(
        "SELECT id, symbol, name, target_type, description FROM targets WHERE LOWER(symbol) = LOWER($1)",
        target_symbol,
    )
    if not target:
        return None

    target = dict(target)
    target_id = str(target["id"])

    # Count claims by type for this target
    rows = await fetch(
        """SELECT claim_type, COUNT(*) as cnt
           FROM claims
           WHERE subject_id = $1
           GROUP BY claim_type
           ORDER BY cnt DESC""",
        target_id,
    )

    type_counts: dict[str, int] = {}
    total_claims = 0
    for row in rows:
        r = dict(row)
        ct = r["claim_type"]
        cnt = r["cnt"]
        type_counts[ct] = cnt
        total_claims += cnt

    return {
        "target_id": target_id,
        "symbol": target["symbol"],
        "name": target.get("name") or "",
        "target_type": target.get("target_type") or "",
        "description": target.get("description") or "",
        "claim_type_counts": type_counts,
        "total_claims": total_claims,
    }


def _identify_gaps(claim_type_counts: dict[str, int]) -> list[str]:
    """Identify missing evidence types from claim distribution.

    Returns claim_types that are completely absent for this target.
    Excludes 'other' since it's a catch-all, not a specific gap.
    """
    present = set(claim_type_counts.keys())
    # Only consider biologically meaningful types as gaps
    meaningful = ALL_CLAIM_TYPES - {"other"}
    return sorted(meaningful - present)


def _compute_priority(
    gap_type: str,
    gap_count: int,
    total_claims: int,
    cost_rank: int,
) -> float:
    """Compute priority score for an experiment suggestion.

    priority = gap_size_norm * target_importance * cost_efficiency

    - gap_size_norm: fraction of total possible types that are missing (0-1)
    - target_importance: log-scaled claim count (more claims = more important target)
    - cost_efficiency: inverse of cost rank (cheaper experiments rank higher)
    """
    import math

    # Gap size: how many types are missing relative to total possible
    total_possible = len(ALL_CLAIM_TYPES) - 1  # exclude 'other'
    gap_size_norm = gap_count / total_possible if total_possible > 0 else 0.5

    # Target importance: log-scaled claim count, normalized
    target_importance = min(math.log2(total_claims + 1) / 10.0, 1.0)

    # Cost efficiency: cheaper experiments get higher priority (inverted, normalized)
    max_cost_rank = 6
    cost_efficiency = (max_cost_rank - cost_rank + 1) / max_cost_rank

    priority = round(gap_size_norm * 0.4 + target_importance * 0.35 + cost_efficiency * 0.25, 4)
    return min(max(priority, 0.0), 1.0)


async def suggest_experiments(target_symbol: str) -> dict[str, Any]:
    """Analyze evidence gaps and suggest experiments for one target.

    Returns:
        dict with target info, present evidence types, gaps, and
        prioritized experiment suggestions.
    """
    profile = await _get_target_claim_profile(target_symbol)
    if profile is None:
        return {
            "error": f"Target '{target_symbol}' not found in database",
            "target_symbol": target_symbol,
            "suggestions": [],
        }

    gaps = _identify_gaps(profile["claim_type_counts"])
    total_gaps = len(gaps)

    suggestions = []
    for gap_type in gaps:
        assay_info = GAP_TO_ASSAY.get(gap_type)
        if not assay_info:
            continue

        priority = _compute_priority(
            gap_type=gap_type,
            gap_count=total_gaps,
            total_claims=profile["total_claims"],
            cost_rank=assay_info["cost_rank"],
        )

        suggestions.append({
            "missing_evidence_type": gap_type,
            "recommended_assay": assay_info["assay"],
            "description": assay_info["description"],
            "model_systems": assay_info["model_systems"],
            "estimated_cost": assay_info["estimated_cost"],
            "timeline_weeks": assay_info["timeline_weeks"],
            "priority_score": priority,
        })

    # Sort by priority descending
    suggestions.sort(key=lambda x: x["priority_score"], reverse=True)

    return {
        "target_symbol": profile["symbol"],
        "target_name": profile["name"],
        "target_type": profile["target_type"],
        "total_claims": profile["total_claims"],
        "present_evidence_types": list(profile["claim_type_counts"].keys()),
        "present_evidence_counts": profile["claim_type_counts"],
        "evidence_gaps": gaps,
        "gap_count": total_gaps,
        "suggestions": suggestions,
    }


async def all_evidence_gaps() -> list[dict[str, Any]]:
    """Analyze evidence gaps across ALL targets, sorted by priority.

    Returns a list of targets with their gaps and top experiment
    suggestions, sorted by overall priority (biggest gaps on most
    important targets first).
    """
    # Get all targets that have at least one claim
    targets = await fetch(
        """SELECT DISTINCT t.id, t.symbol, t.name, t.target_type
           FROM targets t
           INNER JOIN claims c ON c.subject_id = t.id
           ORDER BY t.symbol"""
    )

    if not targets:
        return []

    results = []
    for row in targets:
        t = dict(row)
        symbol = t["symbol"]

        profile = await _get_target_claim_profile(symbol)
        if not profile or profile["total_claims"] == 0:
            continue

        gaps = _identify_gaps(profile["claim_type_counts"])
        if not gaps:
            continue  # No gaps — target has full coverage

        total_gaps = len(gaps)

        # Build top-3 suggestions for this target
        top_suggestions = []
        for gap_type in gaps:
            assay_info = GAP_TO_ASSAY.get(gap_type)
            if not assay_info:
                continue
            priority = _compute_priority(
                gap_type=gap_type,
                gap_count=total_gaps,
                total_claims=profile["total_claims"],
                cost_rank=assay_info["cost_rank"],
            )
            top_suggestions.append({
                "missing_evidence_type": gap_type,
                "recommended_assay": assay_info["assay"],
                "estimated_cost": assay_info["estimated_cost"],
                "timeline_weeks": assay_info["timeline_weeks"],
                "priority_score": priority,
            })

        top_suggestions.sort(key=lambda x: x["priority_score"], reverse=True)

        # Overall priority for sorting: average of top-3 suggestion priorities
        avg_priority = (
            sum(s["priority_score"] for s in top_suggestions[:3]) / min(len(top_suggestions), 3)
            if top_suggestions else 0.0
        )

        results.append({
            "target_symbol": profile["symbol"],
            "target_name": profile["name"],
            "target_type": profile["target_type"],
            "total_claims": profile["total_claims"],
            "present_types": list(profile["claim_type_counts"].keys()),
            "gap_count": total_gaps,
            "gaps": gaps,
            "overall_priority": round(avg_priority, 4),
            "top_suggestions": top_suggestions[:3],
        })

    # Sort by overall priority descending
    results.sort(key=lambda x: x["overall_priority"], reverse=True)
    return results
