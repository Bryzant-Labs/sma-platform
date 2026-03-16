"""Assay-Ready Hypothesis Output — converts top EVE-scored hypotheses into
structured, actionable experiment specifications.

Takes a hypothesis that has been scored by the EVE module and produces a
complete assay-ready packet that a CRO or wet-lab team can execute:

- Biological rationale (from hypothesis text + supporting claims)
- Recommended assay (cheapest valid assay for this evidence type)
- Model system (cell line, organoid, mouse)
- Primary readout + secondary readouts
- Go/No-Go criteria (what result means success/failure)
- Estimated cost and timeline
- Clinical translatability note

This is the final step before actual wet-lab execution.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ..core.database import fetch, fetchrow, fetchval
from .experiment_value import (
    ASSAY_COSTS,
    _clamp,
    _select_cheapest_assay,
    score_hypotheses_eve,
    score_single_eve,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Go/No-Go criteria templates by assay type
# ---------------------------------------------------------------------------

GO_NOGO_CRITERIA: dict[str, dict[str, Any]] = {
    "rt_qpcr": {
        "go": "FL-SMN/delta7-SMN ratio increases >= 1.5-fold over DMSO control (p < 0.05)",
        "no_go": "No significant change in splicing ratio, or effect < 1.2-fold",
        "borderline": "1.2-1.5 fold change — repeat with larger N, consider dose optimization",
    },
    "western_blot": {
        "go": "SMN protein level increases >= 2-fold over baseline (quantified by densitometry)",
        "no_go": "No detectable increase in SMN protein, or increase < 1.3-fold",
        "borderline": "1.3-2.0 fold — validate with ELISA for quantitative confirmation",
    },
    "splicing_reporter": {
        "go": "EC50 < 1 uM with >= 2-fold splicing shift; dose-response Hill slope 0.5-3",
        "no_go": "EC50 > 10 uM, or no dose-response relationship, or cytotoxicity at EC50",
        "borderline": "EC50 1-10 uM — may need medicinal chemistry optimization",
    },
    "ipsc_motor_neuron": {
        "go": ">= 30% increase in surviving HB9+/ChAT+ motor neurons vs DMSO (p < 0.01)",
        "no_go": "No survival benefit, or < 10% increase, or significant cytotoxicity",
        "borderline": "10-30% increase — consider combination with SMN-enhancing therapy",
    },
    "mouse_model": {
        "go": ">= 30% increase in median survival AND improved righting reflex (p < 0.01)",
        "no_go": "No survival benefit or < 10% improvement; adverse effects at effective dose",
        "borderline": "10-30% survival increase — consider dose optimization or combination",
    },
    "elisa": {
        "go": "SMN protein >= 2-fold increase over SMA baseline, approaching carrier levels",
        "no_go": "No significant change in SMN protein levels",
        "borderline": "1.5-2.0 fold increase — check if functionally meaningful by cell survival assay",
    },
    "rna_binding_fp": {
        "go": "KD < 500 nM with clean binding curve; competes with risdiplam at SMN2 site",
        "no_go": "No detectable binding (KD > 100 uM) or non-specific binding pattern",
        "borderline": "KD 500 nM - 10 uM — weak binder, may need structural optimization",
    },
    "seahorse": {
        "go": "Spare respiratory capacity increases >= 40% in SMA MNs (approaches WT levels)",
        "no_go": "No change in OCR parameters, or paradoxical decrease in mitochondrial function",
        "borderline": "15-40% improvement — partial rescue, test in combination with SMN enhancer",
    },
}


# ---------------------------------------------------------------------------
# Clinical translatability assessment
# ---------------------------------------------------------------------------

TRANSLATABILITY_NOTES: dict[str, str] = {
    "gene": (
        "Gene-level targets have clear translational paths via ASO (like nusinersen), "
        "small molecule splicing modifiers (like risdiplam), or gene therapy (like onasemnogene). "
        "Regulatory precedent exists for all three modalities in SMA."
    ),
    "protein": (
        "Protein-level targets can be addressed by small molecules, biologics (antibodies, "
        "fusion proteins), or protein stabilizers. Clinical development requires target "
        "validation in patient-derived cells and animal models."
    ),
    "pathway": (
        "Pathway-level interventions are typically addressed by repurposed drugs or "
        "combination therapies. Clinical path requires demonstrating that pathway "
        "modulation translates to motor neuron benefit in SMA context."
    ),
    "cell_state": (
        "Cell-state targets (e.g., motor neuron survival, NMJ integrity) are typically "
        "addressed indirectly via neuroprotective agents or trophic factors. Clinical "
        "readouts may include electrophysiology (CMAP) and motor function scores."
    ),
    "phenotype": (
        "Phenotype-level hypotheses require demonstration of mechanism before clinical "
        "translation. Biomarker development is critical to enable clinical trial endpoints."
    ),
    "other": (
        "Novel target class — clinical translatability requires establishing the causal "
        "chain from molecular target to motor neuron benefit in SMA."
    ),
}


# ---------------------------------------------------------------------------
# Biological rationale builder
# ---------------------------------------------------------------------------

async def _build_rationale(hyp: dict, meta: dict) -> str:
    """Build biological rationale from hypothesis text + supporting claims."""
    parts = []

    # Core hypothesis description
    description = hyp.get("description", "")
    rationale = hyp.get("rationale", "")
    if description:
        parts.append(description)
    if rationale and rationale != description:
        parts.append(f"Rationale: {rationale}")

    # Supporting evidence summary
    try:
        claim_ids = json.loads(hyp.get("supporting_evidence") or "[]")
    except (json.JSONDecodeError, TypeError):
        claim_ids = []

    if claim_ids:
        # Fetch up to 5 supporting claims for the rationale
        claims = await fetch(
            "SELECT predicate, confidence, claim_type FROM claims WHERE id = ANY($1::uuid[]) LIMIT 5",
            claim_ids[:5],
        )
        if not claims:
            # Fallback: try fetching claims linked to the target
            target_id = meta.get("target_id", "")
            if target_id:
                claims = await fetch(
                    "SELECT predicate, confidence, claim_type FROM claims "
                    "WHERE subject_id = $1 ORDER BY confidence DESC LIMIT 5",
                    target_id,
                )

        if claims:
            claim_texts = []
            for c in claims:
                c = dict(c)
                pred = c.get("predicate", "")
                conf = float(c.get("confidence") or 0.5)
                ct = c.get("claim_type", "")
                claim_texts.append(f"  - {pred} ({ct}, confidence: {conf:.2f})")
            if claim_texts:
                parts.append("Supporting evidence:\n" + "\n".join(claim_texts))
    else:
        # Fetch claims linked to the target as fallback
        target_id = meta.get("target_id", "")
        if target_id:
            claims = await fetch(
                "SELECT predicate, confidence, claim_type FROM claims "
                "WHERE subject_id = $1 ORDER BY confidence DESC LIMIT 5",
                target_id,
            )
            if claims:
                claim_texts = []
                for c in claims:
                    c = dict(c)
                    pred = c.get("predicate", "")
                    conf = float(c.get("confidence") or 0.5)
                    ct = c.get("claim_type", "")
                    claim_texts.append(f"  - {pred} ({ct}, confidence: {conf:.2f})")
                if claim_texts:
                    parts.append("Supporting evidence:\n" + "\n".join(claim_texts))

    return "\n\n".join(parts) if parts else "No detailed rationale available."


# ---------------------------------------------------------------------------
# Assay-ready output generator
# ---------------------------------------------------------------------------

async def get_assay_ready(hypothesis_id: str) -> dict[str, Any]:
    """Convert a single hypothesis into a structured assay-ready format.

    Returns a complete experiment specification that a CRO or wet-lab
    team can execute, including biological rationale, recommended assay,
    model system, readouts, Go/No-Go criteria, cost, timeline, and
    clinical translatability note.
    """
    # First get the EVE score for context
    eve = await score_single_eve(hypothesis_id)
    if "error" in eve:
        return eve

    # Fetch full hypothesis record
    hyp = await fetchrow(
        "SELECT * FROM hypotheses WHERE id = $1",
        hypothesis_id,
    )
    if not hyp:
        return {"error": f"Hypothesis {hypothesis_id} not found"}

    hyp = dict(hyp)

    try:
        meta = json.loads(hyp.get("metadata") or "{}")
    except (json.JSONDecodeError, TypeError):
        meta = {}

    target_id = meta.get("target_id", "")
    target_symbol = meta.get("target_symbol", "")
    claim_type = meta.get("claim_type", "other")

    # Fetch target info
    target_type = "other"
    if target_id:
        target_row = await fetchrow(
            "SELECT symbol, target_type FROM targets WHERE id = $1",
            target_id,
        )
        if target_row:
            target_type = target_row.get("target_type", "other")
            if not target_symbol:
                target_symbol = target_row.get("symbol", "")

    # --- Biological rationale ---
    rationale = await _build_rationale(hyp, meta)

    # --- Recommended assay ---
    assay = _select_cheapest_assay(claim_type)
    if assay is None:
        assay = {"assay_key": "rt_qpcr", **ASSAY_COSTS["rt_qpcr"]}

    assay_key = assay["assay_key"]

    # --- Go/No-Go criteria ---
    criteria = GO_NOGO_CRITERIA.get(assay_key, {
        "go": "Statistically significant effect in expected direction (p < 0.05)",
        "no_go": "No significant effect or effect in wrong direction",
        "borderline": "Trend in expected direction but not significant — increase N",
    })

    # --- Clinical translatability ---
    translatability = TRANSLATABILITY_NOTES.get(target_type, TRANSLATABILITY_NOTES["other"])

    # --- Escalation path (what comes next if GO) ---
    assay_cost = assay["cost_usd"]
    if assay_cost <= 1000:
        escalation = (
            "If GO: advance to splicing reporter assay ($2,000, 2 weeks) for "
            "dose-response characterization, then iPSC-MN survival ($10,000, 8 weeks)."
        )
    elif assay_cost <= 5000:
        escalation = (
            "If GO: advance to iPSC-derived motor neuron survival assay ($10,000, 8 weeks). "
            "If strong effect, consider NMJ co-culture and then SMA mouse model."
        )
    elif assay_cost <= 15000:
        escalation = (
            "If GO: advance to SMA mouse model (delta7, $50,000, 16 weeks). "
            "In parallel, begin pharmacokinetics and ADMET profiling."
        )
    else:
        escalation = (
            "If GO: this is an in vivo result — prepare for IND-enabling studies. "
            "Toxicology, formulation, and regulatory consultation required."
        )

    # --- Claim count for evidence depth ---
    claim_count = 0
    if target_id:
        claim_count_val = await fetchval(
            "SELECT COUNT(*) FROM claims WHERE subject_id = $1",
            target_id,
        )
        claim_count = int(claim_count_val) if claim_count_val else 0

    return {
        "hypothesis_id": str(hyp["id"]),
        "title": hyp.get("title", ""),
        "hypothesis_type": hyp.get("hypothesis_type", ""),
        "status": hyp.get("status", "proposed"),
        "target_symbol": target_symbol,
        "target_id": target_id,
        "target_type": target_type,
        "eve_score": eve["eve_score"],
        "eve_priority": eve["priority"],
        "biological_rationale": rationale,
        "recommended_assay": {
            "name": assay["name"],
            "assay_key": assay_key,
            "cost_usd": assay["cost_usd"],
            "time_weeks": assay["time_weeks"],
            "model_system": assay["model_system"],
            "primary_readout": assay["primary_readout"],
            "secondary_readouts": assay.get("secondary_readouts", []),
        },
        "go_nogo_criteria": criteria,
        "escalation_path": escalation,
        "estimated_cost_usd": assay["cost_usd"],
        "estimated_timeline_weeks": assay["time_weeks"],
        "evidence_depth": {
            "claim_count": claim_count,
            "hypothesis_confidence": float(hyp.get("confidence") or 0.5),
            "target_convergence": eve["components"]["target_convergence"],
        },
        "clinical_translatability": translatability,
        "metadata": {
            "claim_type": claim_type,
            "modality": meta.get("modality_suggestion", "unclear"),
            "key_questions": meta.get("key_questions", []),
        },
    }


async def get_assay_ready_top3() -> list[dict[str, Any]]:
    """Get the top 3 EVE-scored hypotheses in full assay-ready format.

    This is the primary output for researchers: the three best experiments
    to run next, with complete specifications.
    """
    eve_ranked = await score_hypotheses_eve(limit=50)

    if not eve_ranked:
        return []

    # Take top 3 by EVE score
    top3_ids = [r["hypothesis_id"] for r in eve_ranked[:3]]

    results = []
    for i, hyp_id in enumerate(top3_ids):
        assay_ready = await get_assay_ready(hyp_id)
        if "error" not in assay_ready:
            assay_ready["rank"] = i + 1
            results.append(assay_ready)

    logger.info(
        "Assay-ready top 3: %s",
        [r["title"] for r in results],
    )

    return results
