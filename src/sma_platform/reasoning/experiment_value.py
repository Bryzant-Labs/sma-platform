"""Expected Value of Experiment (EVE) scoring for hypotheses and targets.

Two complementary scoring systems:

1. **Hypothesis-centric EVE** (original):
       EVE = P(success) * Impact / (Cost_K + Time_months)
   Scores individual hypotheses using DB-derived convergence, claim types,
   and recommended assay costs.

2. **Target-centric EV** (new — "Which experiment should I run first?"):
       EV = P(success) * Scientific_Impact / (Cost_K / 10)
   Uses hardcoded target impact scores (1-10) and cost estimates ($K) so a
   researcher can immediately see ROI without needing hypotheses in the DB.
   Convergence level maps to P(success):
       very_high → 0.6, high → 0.4, medium → 0.2, low → 0.1

References:
- Expected Value of Information (EVI) framework in clinical trials
- Lab-OS assay library for cost/time estimates
- Convergence engine for target evidence strength
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ..core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Assay cost and time estimates (from Lab-OS)
# ---------------------------------------------------------------------------

ASSAY_COSTS: dict[str, dict[str, Any]] = {
    "rt_qpcr": {
        "name": "RT-qPCR (splicing reporter)",
        "cost_usd": 500,
        "time_weeks": 1,
        "evidence_types": ["gene_expression", "splicing_event"],
        "model_system": "SMA patient fibroblasts",
        "primary_readout": "FL-SMN / delta7-SMN mRNA ratio",
        "secondary_readouts": ["Ct values", "melt curve specificity"],
    },
    "western_blot": {
        "name": "Western Blot (protein quantification)",
        "cost_usd": 800,
        "time_weeks": 1,
        "evidence_types": ["protein_interaction", "drug_efficacy"],
        "model_system": "SMA patient fibroblasts or HEK293",
        "primary_readout": "SMN protein level (densitometry)",
        "secondary_readouts": ["loading control ratio", "band pattern"],
    },
    "splicing_reporter": {
        "name": "Splicing Reporter Assay (minigene)",
        "cost_usd": 2000,
        "time_weeks": 2,
        "evidence_types": ["splicing_event", "drug_efficacy", "gene_expression"],
        "model_system": "HEK293-SMN2-minigene stable line",
        "primary_readout": "Exon 7 inclusion ratio (luciferase or RT-qPCR)",
        "secondary_readouts": ["dose-response EC50", "time course"],
    },
    "ipsc_motor_neuron": {
        "name": "iPSC-derived Motor Neuron Survival",
        "cost_usd": 10000,
        "time_weeks": 8,
        "evidence_types": ["neuroprotection", "survival", "motor_function"],
        "model_system": "SMA patient iPSC-derived motor neurons",
        "primary_readout": "% surviving HB9+/ChAT+ motor neurons at day 28",
        "secondary_readouts": ["neurite length", "electrophysiology", "SMN protein by ICC"],
    },
    "mouse_model": {
        "name": "SMA Mouse Model (delta7 survival study)",
        "cost_usd": 50000,
        "time_weeks": 16,
        "evidence_types": ["survival", "motor_function", "neuroprotection", "drug_efficacy"],
        "model_system": "SMN-delta7 mice (Smn-/-; SMN2+/+; SMNdelta7+/+)",
        "primary_readout": "Median survival (days) + righting reflex",
        "secondary_readouts": ["body weight curve", "spinal cord MN count", "NMJ innervation ratio"],
    },
    "elisa": {
        "name": "SMN Protein ELISA",
        "cost_usd": 600,
        "time_weeks": 1,
        "evidence_types": ["protein_interaction", "drug_efficacy", "biomarker"],
        "model_system": "Cell lysate or CSF",
        "primary_readout": "SMN protein (ng/mL)",
        "secondary_readouts": ["standard curve R-squared", "CV% across replicates"],
    },
    "rna_binding_fp": {
        "name": "RNA-Binding Fluorescence Polarization",
        "cost_usd": 400,
        "time_weeks": 1,
        "evidence_types": ["drug_target", "drug_efficacy"],
        "model_system": "Purified RNA + compound (cell-free)",
        "primary_readout": "KD (dissociation constant)",
        "secondary_readouts": ["Hill coefficient", "competition with risdiplam"],
    },
    "seahorse": {
        "name": "Mitochondrial Function (Seahorse XF)",
        "cost_usd": 1500,
        "time_weeks": 1,
        "evidence_types": ["neuroprotection", "pathway_membership"],
        "model_system": "SMA iPSC-MNs or fibroblasts",
        "primary_readout": "OCR (basal, maximal, spare capacity)",
        "secondary_readouts": ["ECAR", "ATP production rate"],
    },
}


# ---------------------------------------------------------------------------
# Target-centric scoring: hardcoded impact & cost dictionaries
# ---------------------------------------------------------------------------
# Scientific Impact (1-10 scale):
#   SMN-targeting (direct mechanism) = 10
#   Modifier genes (PLS3, NCALD) = 8
#   Novel targets (discovery) = 6
#   Pathway targets = 5

TARGET_IMPACT: dict[str, int] = {
    "SMN1": 10, "SMN2": 10, "SMN_PROTEIN": 10,
    "STMN2": 9, "NMJ_MATURATION": 8,
    "PLS3": 8, "NCALD": 8, "UBA1": 7,
    "MTOR_PATHWAY": 7, "CORO1C": 6,
    "ANK3": 6, "CAST": 5, "CD44": 5,
    "CTNNA1": 5, "DNMT3B": 5, "GALNT6": 4,
    "LDHA": 5, "LY96": 5, "NEDD4L": 5,
    "SPATA18": 4, "SULF1": 4,
}

# Cost estimate in $K per experiment (from assay templates, 5-15K typical)
COST_ESTIMATES: dict[str, float] = {
    "SMN2": 8, "SMN1": 10, "STMN2": 12, "PLS3": 12,
    "NCALD": 10, "UBA1": 7, "CORO1C": 8, "TP53": 10,
}
_DEFAULT_COST_K = 10.0  # Default when target not in COST_ESTIMATES

# Convergence level → P(success) mapping
CONVERGENCE_PSUCCESS: dict[str, float] = {
    "very_high": 0.6,
    "high": 0.4,
    "medium": 0.2,
    "low": 0.1,
}

# Timeline estimates in weeks (keyed by target, with default)
TIMELINE_ESTIMATES: dict[str, int] = {
    "SMN2": 6, "SMN1": 8, "STMN2": 8, "PLS3": 8,
    "NCALD": 6, "UBA1": 4, "CORO1C": 6, "TP53": 10,
}
_DEFAULT_TIMELINE_WEEKS = 6


# ---------------------------------------------------------------------------
# Impact scoring by target characteristics (for hypothesis-centric EVE)
# ---------------------------------------------------------------------------

# Target types mapped to impact multiplier (0.0-1.0)
IMPACT_BY_TARGET_TYPE: dict[str, float] = {
    "gene": 0.7,
    "protein": 0.8,
    "pathway": 0.4,
    "cell_state": 0.5,
    "phenotype": 0.3,
    "other": 0.3,
}

# Claim types that indicate high therapeutic relevance
_HIGH_IMPACT_CLAIMS = {"drug_target", "drug_efficacy", "survival", "motor_function"}
_MEDIUM_IMPACT_CLAIMS = {"neuroprotection", "splicing_event", "gene_expression", "protein_interaction"}


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp to [lo, hi] and round to 4 decimals."""
    return round(max(lo, min(hi, value)), 4)


def _select_cheapest_assay(claim_type: str) -> dict[str, Any] | None:
    """Pick the cheapest valid assay for a given claim/evidence type."""
    candidates = []
    for key, assay in ASSAY_COSTS.items():
        if claim_type in assay["evidence_types"]:
            candidates.append((key, assay))
    if not candidates:
        return None
    # Sort by cost ascending, return cheapest
    candidates.sort(key=lambda x: x[1]["cost_usd"])
    key, assay = candidates[0]
    return {"assay_key": key, **assay}


def _compute_impact(target_type: str, claim_type: str,
                    has_drugs: bool, has_trials: bool) -> float:
    """Compute impact score (0.0-1.0) based on therapeutic relevance."""
    base = IMPACT_BY_TARGET_TYPE.get(target_type, 0.3)

    # Boost for high-impact claim types
    if claim_type in _HIGH_IMPACT_CLAIMS:
        base = _clamp(base + 0.2)
    elif claim_type in _MEDIUM_IMPACT_CLAIMS:
        base = _clamp(base + 0.1)

    # Boost if target already has drugs or trials (translational readiness)
    if has_drugs and has_trials:
        base = _clamp(base + 0.15)
    elif has_drugs or has_trials:
        base = _clamp(base + 0.08)

    return _clamp(base)


async def _get_target_convergence(target_id: str) -> float:
    """Get target convergence score from convergence_scores table, or compute live."""
    if not target_id:
        return 0.3  # default for hypotheses without linked target

    row = await fetchrow(
        "SELECT composite_score FROM convergence_scores WHERE target_id = $1 "
        "ORDER BY computed_at DESC LIMIT 1",
        target_id,
    )
    if row and row["composite_score"] is not None:
        return float(row["composite_score"])

    # Fallback: estimate from claim count
    count_val = await fetchval(
        "SELECT COUNT(*) FROM claims WHERE subject_id = $1",
        target_id,
    )
    count = int(count_val) if count_val else 0
    return _clamp(min(count / 20.0, 1.0) * 0.5 + 0.1)


async def _has_drug_claims(target_id: str) -> bool:
    """Check if target has drug-related claims."""
    if not target_id:
        return False
    val = await fetchval(
        "SELECT COUNT(*) FROM claims WHERE subject_id = $1 "
        "AND claim_type IN ('drug_target', 'drug_efficacy')",
        target_id,
    )
    return (int(val) if val else 0) > 0


async def _has_trial_mentions(target_id: str, symbol: str) -> bool:
    """Check if target is mentioned in clinical trials."""
    if not target_id or not symbol:
        return False
    val = await fetchval(
        "SELECT COUNT(*) FROM trials "
        "WHERE CAST(interventions AS TEXT) LIKE $1 OR title LIKE $2",
        f"%{symbol}%", f"%{symbol}%",
    )
    return (int(val) if val else 0) > 0


# ---------------------------------------------------------------------------
# EVE scoring
# ---------------------------------------------------------------------------

async def score_single_eve(hypothesis_id: str) -> dict[str, Any]:
    """Compute Expected Value of Experiment for a single hypothesis.

    EVE = P(success) * Impact / (Cost + Time)

    Returns dict with full breakdown: p_success, impact, cost, time,
    eve_score, recommended_assay, and interpretation.
    """
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
    hypothesis_confidence = float(hyp.get("confidence") or 0.5)

    # --- Fetch target info ---
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

    # --- P(success) ---
    convergence = await _get_target_convergence(target_id)
    p_success = _clamp(hypothesis_confidence * 0.6 + convergence * 0.4)

    # --- Impact ---
    has_drugs = await _has_drug_claims(target_id)
    has_trials = await _has_trial_mentions(target_id, target_symbol)
    impact = _compute_impact(target_type, claim_type, has_drugs, has_trials)

    # --- Recommended assay (cheapest valid) ---
    assay = _select_cheapest_assay(claim_type)
    if assay is None:
        # Fallback to RT-qPCR as general-purpose screen
        assay = {"assay_key": "rt_qpcr", **ASSAY_COSTS["rt_qpcr"]}

    cost_usd = assay["cost_usd"]
    time_weeks = assay["time_weeks"]

    # --- EVE score ---
    # Normalize cost to thousands and time to months for balanced formula
    cost_norm = cost_usd / 1000.0  # cost in $K
    time_norm = time_weeks / 4.0   # time in months
    denominator = cost_norm + time_norm
    if denominator <= 0:
        denominator = 0.01

    eve_raw = (p_success * impact) / denominator
    # Normalize EVE to 0-1 range (empirical max ~2.0 for cheap fast assays)
    eve_score = _clamp(eve_raw / 2.0)

    # --- Interpretation ---
    if eve_score >= 0.6:
        priority = "HIGH — strong candidate for immediate experiment"
    elif eve_score >= 0.3:
        priority = "MEDIUM — worth pursuing with available resources"
    elif eve_score >= 0.1:
        priority = "LOW — consider only if cheap assay available"
    else:
        priority = "SKIP — insufficient evidence or too expensive for current stage"

    return {
        "hypothesis_id": str(hyp["id"]),
        "title": hyp.get("title", ""),
        "description": hyp.get("description", ""),
        "target_symbol": target_symbol,
        "target_id": target_id,
        "claim_type": claim_type,
        "hypothesis_type": hyp.get("hypothesis_type", ""),
        "status": hyp.get("status", "proposed"),
        "eve_score": eve_score,
        "eve_raw": round(eve_raw, 4),
        "priority": priority,
        "components": {
            "p_success": p_success,
            "hypothesis_confidence": hypothesis_confidence,
            "target_convergence": convergence,
            "impact": impact,
            "target_type": target_type,
            "has_drugs": has_drugs,
            "has_trials": has_trials,
        },
        "recommended_assay": {
            "assay_key": assay["assay_key"],
            "name": assay["name"],
            "cost_usd": cost_usd,
            "time_weeks": time_weeks,
            "model_system": assay["model_system"],
            "primary_readout": assay["primary_readout"],
        },
        "formula": "EVE = P(success) * Impact / (Cost_K + Time_months)",
    }


async def score_hypotheses_eve(limit: int = 50) -> list[dict[str, Any]]:
    """Score and rank hypotheses by Expected Value of Experiment.

    Fetches up to `limit` hypotheses ordered by confidence, computes EVE
    for each, and returns them sorted by EVE score descending.

    Returns list of dicts, each with full EVE breakdown.
    """
    hypotheses = await fetch(
        "SELECT id FROM hypotheses ORDER BY confidence DESC LIMIT $1",
        limit,
    )

    if not hypotheses:
        return []

    results = []
    for h in hypotheses:
        h = dict(h)
        hyp_id = str(h["id"])
        result = await score_single_eve(hyp_id)
        if "error" not in result:
            results.append(result)

    # Sort by EVE score descending
    results.sort(key=lambda x: x["eve_score"], reverse=True)

    # Add rank
    for i, r in enumerate(results):
        r["rank"] = i + 1

    logger.info(
        "EVE scoring complete: %d hypotheses scored. Top: %s (EVE=%.4f)",
        len(results),
        results[0]["title"] if results else "N/A",
        results[0]["eve_score"] if results else 0,
    )

    return results


# ---------------------------------------------------------------------------
# Target-centric EV scoring
# ---------------------------------------------------------------------------
# Formula: EV = P(success) * Scientific_Impact / (Cost_K / 10)
# Higher EV = better ROI.  Designed to answer:
# "If I have $50K and 3 months, which experiment should I run first?"
# ---------------------------------------------------------------------------


async def _resolve_convergence_level(symbol: str) -> tuple[str, float]:
    """Look up the convergence level for a target symbol from the DB.

    Returns (confidence_level, composite_score).  Falls back to 'low'
    if no convergence score is stored.
    """
    row = await fetchrow(
        "SELECT cs.confidence_level, cs.composite_score "
        "FROM convergence_scores cs "
        "JOIN targets t ON cs.target_id = t.id "
        "WHERE UPPER(t.symbol) = $1 "
        "ORDER BY cs.computed_at DESC LIMIT 1",
        symbol.upper(),
    )
    if row and row["confidence_level"]:
        return row["confidence_level"], float(row["composite_score"] or 0)

    # Fallback: estimate from claim count
    count_row = await fetchrow(
        "SELECT COUNT(*) AS cnt FROM claims c "
        "JOIN targets t ON c.subject_id = t.id "
        "WHERE UPPER(t.symbol) = $1",
        symbol.upper(),
    )
    cnt = int(count_row["cnt"]) if count_row else 0
    if cnt >= 20:
        return "high", 0.60
    if cnt >= 8:
        return "medium", 0.40
    if cnt >= 3:
        return "low", 0.20
    return "low", 0.10


async def compute_experiment_value(
    target: str,
    convergence_score: str | None = None,
    confidence_level: str | None = None,
) -> dict[str, Any]:
    """Compute Expected Value for a single target experiment.

    Parameters
    ----------
    target : str
        Gene/target symbol (e.g. "SMN2", "CORO1C").
    convergence_score : str | None
        Override convergence level ("very_high", "high", "medium", "low").
        If *None*, the value is looked up from the convergence_scores table.
    confidence_level : str | None
        Alias for *convergence_score* (accepted for backward compat).

    Returns
    -------
    dict with EV score, breakdown, and recommendation.
    """
    symbol = target.upper()

    # --- Resolve convergence ---
    level_override = convergence_score or confidence_level
    if level_override:
        level = level_override.lower().replace(" ", "_")
        if level not in CONVERGENCE_PSUCCESS:
            level = "low"
        composite = CONVERGENCE_PSUCCESS.get(level, 0.1)
    else:
        level, composite = await _resolve_convergence_level(symbol)

    p_success = CONVERGENCE_PSUCCESS.get(level, 0.1)

    # --- Impact ---
    impact = TARGET_IMPACT.get(symbol, 5)  # default 5 for unknown targets

    # --- Cost ---
    cost_k = COST_ESTIMATES.get(symbol, _DEFAULT_COST_K)

    # --- Timeline ---
    timeline_weeks = TIMELINE_ESTIMATES.get(symbol, _DEFAULT_TIMELINE_WEEKS)

    # --- EV formula ---
    # EV = P(success) * Impact / (Cost_K / 10)
    denominator = cost_k / 10.0
    if denominator <= 0:
        denominator = 0.01
    ev_score = round(p_success * impact / denominator, 4)

    # --- Interpretation ---
    if ev_score >= 5.0:
        priority = "HIGH PRIORITY — run this experiment first"
        recommendation = (
            f"{symbol} has strong evidence convergence and high scientific "
            f"impact relative to cost. Recommended for immediate execution."
        )
    elif ev_score >= 2.0:
        priority = "MEDIUM PRIORITY — strong candidate with available resources"
        recommendation = (
            f"{symbol} offers good ROI. Consider running if budget and "
            f"timeline allow after higher-priority targets."
        )
    elif ev_score >= 1.0:
        priority = "LOW PRIORITY — pursue if resources permit"
        recommendation = (
            f"{symbol} has moderate expected value. Evidence or impact "
            f"may need strengthening before committing resources."
        )
    else:
        priority = "DEFER — insufficient evidence for current investment"
        recommendation = (
            f"{symbol} currently shows low expected return. Gather more "
            f"evidence or wait for convergence to improve."
        )

    return {
        "target": symbol,
        "ev_score": ev_score,
        "priority": priority,
        "recommendation": recommendation,
        "breakdown": {
            "p_success": p_success,
            "convergence_level": level,
            "convergence_composite": composite,
            "scientific_impact": impact,
            "cost_k": cost_k,
            "timeline_weeks": timeline_weeks,
        },
        "formula": "EV = P(success) * Scientific_Impact / (Cost_K / 10)",
        "formula_values": (
            f"EV = {p_success} * {impact} / ({cost_k} / 10) = {ev_score}"
        ),
    }


async def rank_all_experiments(
    budget_k: float | None = None,
    max_weeks: int | None = None,
) -> list[dict[str, Any]]:
    """Rank all known targets by Expected Value, optionally filtered by budget/timeline.

    Parameters
    ----------
    budget_k : float | None
        If set, only include targets with cost_k <= budget_k.
    max_weeks : int | None
        If set, only include targets with timeline_weeks <= max_weeks.

    Returns
    -------
    list of dicts sorted by ev_score descending, each with full breakdown.
    """
    results: list[dict[str, Any]] = []

    for symbol in TARGET_IMPACT:
        cost_k = COST_ESTIMATES.get(symbol, _DEFAULT_COST_K)
        timeline = TIMELINE_ESTIMATES.get(symbol, _DEFAULT_TIMELINE_WEEKS)

        # Apply budget/timeline filters
        if budget_k is not None and cost_k > budget_k:
            continue
        if max_weeks is not None and timeline > max_weeks:
            continue

        result = await compute_experiment_value(symbol)
        results.append(result)

    # Sort by EV descending
    results.sort(key=lambda x: x["ev_score"], reverse=True)

    # Add rank
    for i, r in enumerate(results):
        r["rank"] = i + 1

    total_cost = sum(r["breakdown"]["cost_k"] for r in results)

    logger.info(
        "Target EV ranking complete: %d targets scored. Top: %s (EV=%.4f)",
        len(results),
        results[0]["target"] if results else "N/A",
        results[0]["ev_score"] if results else 0,
    )

    return results
