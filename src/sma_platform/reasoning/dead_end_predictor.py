"""Dead-End Predictor — learn failure patterns from drug_outcomes data.

Analyzes the drug_outcomes table to build failure profiles: which targets,
mechanisms, and claim types are associated with drug failure. Then compares
each active hypothesis to these failure profiles to compute a risk score.

Risk score (0-1): higher = more overlap with known failure patterns.

This is a unique analytical layer — no existing SMA database systematically
predicts dead ends from structured failure data.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from typing import Any

from ..core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

# Outcomes that count as failures
FAILURE_OUTCOMES = {"failure", "discontinued", "no_efficacy"}

# Outcomes that count as negative signals (broader than hard failures)
NEGATIVE_OUTCOMES = {"failure", "discontinued", "no_efficacy", "inconclusive"}


async def _table_has_data(table_name: str) -> bool:
    """Check whether a table exists and has at least one row."""
    try:
        count = await fetchval(f"SELECT COUNT(*) FROM {table_name}")
        return (count or 0) > 0
    except Exception:
        return False


async def _get_failed_outcomes() -> list[dict]:
    """Query drug_outcomes for failed drugs."""
    try:
        rows = await fetch(
            """SELECT id, compound_name, target, mechanism, outcome,
                      failure_reason, failure_detail, trial_phase,
                      model_system, key_finding, confidence, source_id
               FROM drug_outcomes
               WHERE outcome IN ('failure', 'discontinued')
               ORDER BY confidence DESC"""
        )
        return [dict(r) for r in rows]
    except Exception as e:
        # Table might not exist yet or might use different outcome values
        logger.warning("Failed to query drug_outcomes for failures: %s", e)
        # Try broader query including 'no_efficacy' variant
        try:
            rows = await fetch(
                """SELECT id, compound_name, target, mechanism, outcome,
                          failure_reason, failure_detail, trial_phase,
                          model_system, key_finding, confidence, source_id
                   FROM drug_outcomes
                   WHERE outcome NOT IN ('success', 'partial_success', 'ongoing')
                   ORDER BY confidence DESC"""
            )
            return [dict(r) for r in rows]
        except Exception as e2:
            logger.error("drug_outcomes table query failed: %s", e2)
            return []


def _build_failure_profiles(failed_outcomes: list[dict]) -> dict[str, Any]:
    """Build failure fingerprint from failed drug outcomes.

    Extracts which targets, mechanisms, failure reasons, and trial phases
    are most commonly associated with failure.
    """
    target_counts: Counter[str] = Counter()
    mechanism_counts: Counter[str] = Counter()
    failure_reason_counts: Counter[str] = Counter()
    phase_counts: Counter[str] = Counter()
    target_mechanism_pairs: Counter[tuple[str, str]] = Counter()

    for outcome in failed_outcomes:
        target = (outcome.get("target") or "").strip().lower()
        mechanism = (outcome.get("mechanism") or "").strip().lower()
        reason = (outcome.get("failure_reason") or "").strip().lower()
        phase = (outcome.get("trial_phase") or "").strip().lower()

        if target:
            target_counts[target] += 1
        if mechanism:
            mechanism_counts[mechanism] += 1
        if reason:
            failure_reason_counts[reason] += 1
        if phase:
            phase_counts[phase] += 1
        if target and mechanism:
            target_mechanism_pairs[(target, mechanism)] += 1

    return {
        "total_failures": len(failed_outcomes),
        "failed_targets": dict(target_counts.most_common(50)),
        "failed_mechanisms": dict(mechanism_counts.most_common(50)),
        "failure_reasons": dict(failure_reason_counts.most_common(20)),
        "failure_phases": dict(phase_counts.most_common(10)),
        "target_mechanism_pairs": {
            f"{t}|{m}": c for (t, m), c in target_mechanism_pairs.most_common(30)
        },
    }


async def get_failure_patterns() -> list[dict[str, Any]]:
    """Get known failure patterns with examples.

    Returns grouped failure patterns: each pattern is a cluster of
    related failures (same target or mechanism) with representative
    examples and frequency data.
    """
    failed = await _get_failed_outcomes()
    if not failed:
        return []

    profiles = _build_failure_profiles(failed)

    patterns: list[dict[str, Any]] = []

    # Group failures by target
    target_groups: dict[str, list[dict]] = {}
    for outcome in failed:
        target = (outcome.get("target") or "unknown").strip()
        target_groups.setdefault(target, []).append(outcome)

    for target, outcomes in sorted(target_groups.items(), key=lambda x: -len(x[1])):
        if target == "unknown" or target == "":
            continue

        reasons = Counter(
            (o.get("failure_reason") or "unspecified").strip()
            for o in outcomes
        )
        compounds = list(set(
            o.get("compound_name", "")
            for o in outcomes if o.get("compound_name")
        ))
        mechanisms = list(set(
            o.get("mechanism", "")
            for o in outcomes if o.get("mechanism")
        ))

        # Pick the best example (highest confidence)
        best = max(outcomes, key=lambda o: o.get("confidence", 0))

        patterns.append({
            "pattern_type": "target_failure",
            "target": target,
            "failure_count": len(outcomes),
            "compounds_involved": compounds[:10],
            "mechanisms": mechanisms[:5],
            "common_failure_reasons": dict(reasons.most_common(5)),
            "example": {
                "compound": best.get("compound_name"),
                "outcome": best.get("outcome"),
                "failure_reason": best.get("failure_reason"),
                "key_finding": best.get("key_finding"),
                "trial_phase": best.get("trial_phase"),
            },
            "risk_signal": (
                "high" if len(outcomes) >= 3
                else "medium" if len(outcomes) >= 2
                else "low"
            ),
        })

    # Also group by mechanism for mechanism-level patterns
    mechanism_groups: dict[str, list[dict]] = {}
    for outcome in failed:
        mech = (outcome.get("mechanism") or "").strip().lower()
        if mech:
            mechanism_groups.setdefault(mech, []).append(outcome)

    for mech, outcomes in sorted(mechanism_groups.items(), key=lambda x: -len(x[1])):
        if len(outcomes) < 2:
            continue  # Only report mechanism patterns with 2+ failures

        targets_hit = list(set(
            (o.get("target") or "").strip()
            for o in outcomes if o.get("target")
        ))
        compounds = list(set(
            o.get("compound_name", "")
            for o in outcomes if o.get("compound_name")
        ))

        patterns.append({
            "pattern_type": "mechanism_failure",
            "mechanism": mech,
            "failure_count": len(outcomes),
            "targets_hit": targets_hit[:10],
            "compounds_involved": compounds[:10],
            "risk_signal": (
                "high" if len(outcomes) >= 3
                else "medium"
            ),
        })

    # Sort by failure count descending
    patterns.sort(key=lambda p: p["failure_count"], reverse=True)
    return patterns


def _compute_risk_score(
    hypothesis: dict,
    failed_outcomes: list[dict],
    profiles: dict[str, Any],
) -> dict[str, Any]:
    """Compute risk score for a hypothesis based on overlap with failure patterns.

    Checks multiple dimensions:
    1. Target overlap: does the hypothesis target match failed drug targets?
    2. Mechanism overlap: does the hypothesis mention failed mechanisms?
    3. Claim-type overlap: is the hypothesis based on evidence types that
       frequently appear in failed drug contexts?

    Risk score = weighted average of dimension overlaps (0-1).
    """
    metadata = hypothesis.get("metadata") or {}
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except (json.JSONDecodeError, TypeError):
            metadata = {}

    title = (hypothesis.get("title") or "").lower()
    description = (hypothesis.get("description") or "").lower()
    rationale = (hypothesis.get("rationale") or "").lower()
    target_symbol = (metadata.get("target_symbol") or "").lower()
    full_text = f"{title} {description} {rationale}"

    failed_targets = profiles.get("failed_targets", {})
    failed_mechanisms = profiles.get("failed_mechanisms", {})
    failure_reasons = profiles.get("failure_reasons", {})
    total_failures = max(profiles.get("total_failures", 1), 1)

    risk_factors: list[dict[str, Any]] = []

    # 1. Target overlap
    target_risk = 0.0
    if target_symbol and target_symbol in failed_targets:
        count = failed_targets[target_symbol]
        target_risk = min(count / total_failures * 5, 1.0)  # Scale up — even 1 failure matters
        risk_factors.append({
            "factor": "target_overlap",
            "detail": f"Target '{target_symbol}' appeared in {count} failed drug outcome(s)",
            "contribution": round(target_risk, 3),
        })

    # Also check if target_symbol appears in any failed outcome
    if not target_risk and target_symbol:
        for outcome in failed_outcomes:
            failed_target = (outcome.get("target") or "").strip().lower()
            if target_symbol in failed_target or failed_target in target_symbol:
                target_risk = 0.3
                risk_factors.append({
                    "factor": "target_partial_match",
                    "detail": f"Target '{target_symbol}' partially matches failed target '{failed_target}'",
                    "contribution": 0.3,
                })
                break

    # 2. Mechanism overlap — check if hypothesis text mentions known failed mechanisms
    mechanism_risk = 0.0
    matched_mechanisms = []
    for mech, count in failed_mechanisms.items():
        if len(mech) >= 4 and mech in full_text:
            mech_score = min(count / total_failures * 3, 0.8)
            if mech_score > mechanism_risk:
                mechanism_risk = mech_score
            matched_mechanisms.append(mech)

    if matched_mechanisms:
        risk_factors.append({
            "factor": "mechanism_overlap",
            "detail": f"Hypothesis mentions mechanism(s) associated with failure: {', '.join(matched_mechanisms[:5])}",
            "contribution": round(mechanism_risk, 3),
        })

    # 3. Failure reason pattern — if hypothesis mentions areas with known failure reasons
    reason_risk = 0.0
    high_risk_reasons = {"toxicity", "lack_of_efficacy", "poor_bbb_penetration", "off_target_effects"}
    matched_reasons = []
    for reason in high_risk_reasons:
        normalized = reason.replace("_", " ")
        if normalized in full_text or reason in full_text:
            matched_reasons.append(reason)
            reason_risk = max(reason_risk, 0.2)

    if matched_reasons:
        risk_factors.append({
            "factor": "mentions_known_failure_modes",
            "detail": f"Hypothesis text references known failure modes: {', '.join(matched_reasons)}",
            "contribution": round(reason_risk, 3),
        })

    # 4. Compute similar-drug failure rate for this target
    target_failure_rate = 0.0
    if target_symbol:
        target_outcomes = [
            o for o in failed_outcomes
            if target_symbol in (o.get("target") or "").strip().lower()
        ]
        if target_outcomes:
            target_failure_rate = min(len(target_outcomes) / 5.0, 1.0)
            risk_factors.append({
                "factor": "target_failure_rate",
                "detail": f"{len(target_outcomes)} drug(s) targeting '{target_symbol}' have failed",
                "contribution": round(target_failure_rate, 3),
            })

    # Weighted composite risk score
    risk_score = round(
        0.35 * target_risk
        + 0.25 * mechanism_risk
        + 0.15 * reason_risk
        + 0.25 * target_failure_rate,
        4,
    )
    risk_score = min(max(risk_score, 0.0), 1.0)

    # Risk level
    if risk_score >= 0.6:
        risk_level = "high"
    elif risk_score >= 0.3:
        risk_level = "medium"
    elif risk_score > 0.0:
        risk_level = "low"
    else:
        risk_level = "none"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
    }


async def assess_risk(hypothesis_id: str) -> dict[str, Any]:
    """Assess dead-end risk for a single hypothesis.

    Returns risk score, risk level, and detailed risk factors
    based on overlap with known drug failure patterns.
    """
    hypothesis = await fetchrow(
        """SELECT id, hypothesis_type, title, description, rationale,
                  confidence, status, metadata
           FROM hypotheses WHERE id = $1""",
        hypothesis_id,
    )
    if not hypothesis:
        return {
            "error": f"Hypothesis '{hypothesis_id}' not found",
            "hypothesis_id": hypothesis_id,
            "risk_score": 0.0,
            "risk_level": "unknown",
            "risk_factors": [],
        }

    hypothesis = dict(hypothesis)
    failed = await _get_failed_outcomes()
    if not failed:
        return {
            "hypothesis_id": str(hypothesis["id"]),
            "title": hypothesis.get("title", ""),
            "risk_score": 0.0,
            "risk_level": "none",
            "risk_factors": [],
            "note": "No drug failure data available — risk assessment requires drug_outcomes records",
        }

    profiles = _build_failure_profiles(failed)
    risk_result = _compute_risk_score(hypothesis, failed, profiles)

    return {
        "hypothesis_id": str(hypothesis["id"]),
        "title": hypothesis.get("title", ""),
        "hypothesis_type": hypothesis.get("hypothesis_type", ""),
        "confidence": float(hypothesis.get("confidence", 0)),
        "status": hypothesis.get("status", ""),
        **risk_result,
    }


async def all_risks() -> list[dict[str, Any]]:
    """Assess dead-end risk for all active hypotheses.

    Returns a list of hypotheses with risk scores, sorted by
    risk_score descending (highest risk first).
    """
    # Get active hypotheses (not refuted)
    try:
        hypotheses = await fetch(
            """SELECT id, hypothesis_type, title, description, rationale,
                      confidence, status, metadata
               FROM hypotheses
               WHERE status NOT IN ('refuted')
               ORDER BY confidence DESC"""
        )
    except Exception as e:
        logger.error("Failed to fetch hypotheses: %s", e)
        return []

    if not hypotheses:
        return []

    failed = await _get_failed_outcomes()
    if not failed:
        return [{
            "hypothesis_id": str(dict(h)["id"]),
            "title": dict(h).get("title", ""),
            "risk_score": 0.0,
            "risk_level": "none",
            "note": "No drug failure data available",
        } for h in hypotheses[:50]]

    profiles = _build_failure_profiles(failed)

    results = []
    for row in hypotheses:
        h = dict(row)
        risk_result = _compute_risk_score(h, failed, profiles)

        results.append({
            "hypothesis_id": str(h["id"]),
            "title": h.get("title", ""),
            "hypothesis_type": h.get("hypothesis_type", ""),
            "confidence": float(h.get("confidence", 0)),
            "status": h.get("status", ""),
            **risk_result,
        })

    # Sort by risk score descending
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results
