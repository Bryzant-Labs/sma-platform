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


# ---------------------------------------------------------------------------
# SMA-specific assay templates by target gene
# ---------------------------------------------------------------------------

TARGET_ASSAY_TEMPLATES: dict[str, dict[str, Any]] = {
    "SMN2": {
        "assay": "SMN2 splicing reporter assay (luciferase-based)",
        "model": "SMA patient fibroblasts or iPSC-derived motor neurons",
        "readout": "Full-length SMN2 mRNA (RT-qPCR) + SMN protein (Western blot)",
        "go_criteria": ">20% increase in full-length SMN2 mRNA vs DMSO control",
        "cost": "$5,000-10,000",
        "timeline": "4-6 weeks",
    },
    "STMN2": {
        "assay": "STMN2 protein stabilization assay",
        "model": "iPSC-derived motor neurons (SMA patient)",
        "readout": "STMN2 protein levels (Western), axon length measurement",
        "go_criteria": ">15% increase in STMN2 protein or >10% increase in axon length",
        "cost": "$8,000-15,000",
        "timeline": "6-8 weeks",
    },
    "UBA1": {
        "assay": "Ubiquitin pathway rescue assay",
        "model": "SMA patient fibroblasts + motor neuron differentiation",
        "readout": "Ubiquitin conjugate levels, UBA1 activity assay",
        "go_criteria": "Normalization of ubiquitin homeostasis markers",
        "cost": "$5,000-8,000",
        "timeline": "4-6 weeks",
    },
    "CORO1C": {
        "assay": "Actin dynamics / cell migration assay",
        "model": "Motor neuron-like NSC-34 cells or iPSC-MNs",
        "readout": "Actin polymerization (phalloidin staining), growth cone morphology",
        "go_criteria": ">15% improvement in growth cone area or neurite outgrowth",
        "cost": "$5,000-10,000",
        "timeline": "4-6 weeks",
    },
    "TP53": {
        "assay": "p53-dependent apoptosis assay",
        "model": "SMA mouse motor neuron primary cultures",
        "readout": "Caspase-3 activity, TUNEL staining, cell viability (MTT)",
        "go_criteria": ">25% reduction in apoptosis markers vs vehicle",
        "cost": "$8,000-12,000",
        "timeline": "6-8 weeks",
    },
    "PLS3": {
        "assay": "PLS3 functional enhancement assay",
        "model": "SMA patient fibroblasts or iPSC-MNs",
        "readout": "F-actin bundling (in vitro), NMJ formation (co-culture)",
        "go_criteria": "Enhanced actin bundling or improved NMJ morphology",
        "cost": "$10,000-15,000",
        "timeline": "8-10 weeks",
    },
    "NCALD": {
        "assay": "Calcium signaling + endocytosis assay",
        "model": "iPSC-derived motor neurons (SMA patient)",
        "readout": "Calcium imaging (Fura-2), FM1-43 endocytosis assay",
        "go_criteria": "Restored endocytic rate comparable to NCALD-knockdown control",
        "cost": "$8,000-12,000",
        "timeline": "6-8 weeks",
    },
}

# Default template for targets not in the map
_DEFAULT_ASSAY_TEMPLATE: dict[str, str] = {
    "assay": "Target-specific functional assay (phenotypic or biochemical)",
    "model": "SMA patient fibroblasts or iPSC-derived motor neurons",
    "readout": "Target protein level (Western), motor neuron viability",
    "go_criteria": ">15% improvement over vehicle control (p < 0.05)",
    "cost": "$5,000-10,000",
    "timeline": "4-8 weeks",
}


def generate_assay_card(
    smiles: str,
    target: str,
    docking_confidence: float = 0.0,
) -> dict[str, Any]:
    """Generate a wet-lab validation assay card for a single screening hit.

    Returns an assay card with: hypothesis, assay, model system, readout,
    go/no-go criteria, estimated cost and timeline, and docking context.
    """
    target_upper = target.upper().strip()
    template = TARGET_ASSAY_TEMPLATES.get(
        target_upper, _DEFAULT_ASSAY_TEMPLATE
    )

    # Build hypothesis text
    if docking_confidence >= 0.7:
        confidence_label = "high"
    elif docking_confidence >= 0.4:
        confidence_label = "moderate"
    else:
        confidence_label = "low"

    hypothesis = (
        f"Compound ({smiles[:60]}{'...' if len(smiles) > 60 else ''}) "
        f"binds {target_upper} with {confidence_label} docking confidence "
        f"({docking_confidence:.2f}) and modulates its activity in SMA-relevant "
        f"cellular context."
    )

    return {
        "smiles": smiles,
        "target": target_upper,
        "docking_confidence": docking_confidence,
        "hypothesis": hypothesis,
        "assay": template["assay"],
        "model_system": template["model"],
        "readout": template["readout"],
        "go_nogo_criteria": template["go_criteria"],
        "estimated_cost": template["cost"],
        "estimated_timeline": template["timeline"],
        "priority": (
            "high" if docking_confidence >= 0.7
            else "medium" if docking_confidence >= 0.4
            else "low"
        ),
    }


def generate_assay_cards_batch(
    hits: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Generate assay cards for multiple screening hits.

    Each hit should have keys: smiles, target, docking_confidence (optional).
    Returns cards sorted by docking confidence descending.
    """
    cards = []
    for hit in hits:
        card = generate_assay_card(
            smiles=hit.get("smiles", ""),
            target=hit.get("target", ""),
            docking_confidence=float(hit.get("docking_confidence", 0.0)),
        )
        cards.append(card)

    # Sort by docking confidence descending
    cards.sort(key=lambda c: c["docking_confidence"], reverse=True)
    return cards


async def get_assay_cards_for_positive_hits() -> dict[str, Any]:
    """Generate assay-ready validation cards for all positive screening hits.

    Queries the molecule_screenings table for top drug-like hits, then
    generates target-specific assay cards with go/no-go criteria.
    """
    # Fetch positive screening hits — drug-like with good pChEMBL
    rows = await fetch(
        """SELECT smiles, target_symbol, pchembl_value, compound_name,
                  chembl_id, molecular_weight, alogp, drug_likeness_pass
           FROM molecule_screenings
           WHERE drug_likeness_pass = TRUE
             AND pchembl_value >= 5.0
           ORDER BY pchembl_value DESC
           LIMIT 20"""
    )

    if not rows:
        # Fallback: try any hits with target symbol
        rows = await fetch(
            """SELECT smiles, target_symbol, pchembl_value, compound_name,
                      chembl_id, molecular_weight, alogp, drug_likeness_pass
               FROM molecule_screenings
               WHERE target_symbol IS NOT NULL
               ORDER BY pchembl_value DESC NULLS LAST
               LIMIT 20"""
        )

    if not rows:
        return {
            "total_hits": 0,
            "assay_cards": [],
            "insight": "No positive screening hits found. Run drug screening first.",
        }

    cards = []
    for row in rows:
        row = dict(row)
        # Use pChEMBL as a proxy for docking confidence (normalized to 0-1)
        pchembl = float(row.get("pchembl_value") or 0)
        confidence = min(1.0, pchembl / 10.0)  # pChEMBL 10 = perfect

        card = generate_assay_card(
            smiles=row.get("smiles", ""),
            target=row.get("target_symbol", ""),
            docking_confidence=round(confidence, 3),
        )
        # Enrich with screening metadata
        card["compound_name"] = row.get("compound_name")
        card["chembl_id"] = row.get("chembl_id")
        card["molecular_weight"] = row.get("molecular_weight")
        card["alogp"] = row.get("alogp")
        card["pchembl_value"] = pchembl
        cards.append(card)

    # Sort by confidence
    cards.sort(key=lambda c: c["docking_confidence"], reverse=True)

    # Summary stats
    targets_covered = set(c["target"] for c in cards)
    high_priority = sum(1 for c in cards if c["priority"] == "high")

    return {
        "total_hits": len(cards),
        "high_priority": high_priority,
        "targets_covered": sorted(targets_covered),
        "assay_cards": cards,
        "insight": (
            f"{len(cards)} screening hits with assay-ready validation plans "
            f"covering {len(targets_covered)} targets. "
            f"{high_priority} are high-priority (docking confidence >= 0.7)."
        ),
    }
