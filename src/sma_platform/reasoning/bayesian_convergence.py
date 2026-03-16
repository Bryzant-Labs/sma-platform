"""Bayesian evidence convergence — proper posterior updating for target validity.

Replaces simple weighted-average scoring with a Beta-Binomial Bayesian model.
Each claim about a target updates a Beta(alpha, beta) posterior for the
probability that the target is therapeutically valid.

Key design choices:
- Prior: Beta(1, 1) (uniform / uninformative) — no target starts with bias
- Likelihood weights vary by claim_type (drug_efficacy strongest)
- Positive claims increase alpha, negative claims increase beta
- Source prolificacy discount prevents double-counting from mega-labs
- Returns full posterior summary: mean, mode, 95% credible interval, Bayes factor

All weights and thresholds are module-level constants — auditable, debatable.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from ..core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

# === CLAIM TYPE LIKELIHOOD WEIGHTS ===
# Higher weight = stronger evidence signal per claim.
# Drug efficacy is the gold standard because it directly measures therapeutic value.
CLAIM_TYPE_WEIGHTS: dict[str, float] = {
    "drug_efficacy":        3.0,
    "protein_interaction":  2.0,
    "gene_expression":      1.5,
    "splicing_event":       1.5,
    "neuroprotection":      1.5,
    "motor_function":       1.5,
    "survival":             2.0,
    "biomarker":            1.0,
    "drug_target":          2.0,
    "pathway_membership":   1.0,
    "safety":               1.0,
    "other":                0.5,
}

# === PREDICATE DIRECTION KEYWORDS ===
# Determines whether a claim is positive (supports therapeutic validity)
# or negative (evidence against).
POSITIVE_KEYWORDS = [
    "increases", "upregulates", "improves", "rescues",
    "enhances", "activates", "promotes", "treats",
    "correlates_with", "protects", "restores",
]
NEGATIVE_KEYWORDS = [
    "decreases", "downregulates", "impairs", "inhibits",
    "reduces", "suppresses", "worsens", "fails",
    "no_effect", "toxicity",
]

# === SOURCE PROLIFICACY DISCOUNT ===
# Sources with many claims get a slight discount to prevent one prolific
# lab from dominating a target's score.
PROLIFICACY_THRESHOLD = 20   # claims from this source before discount kicks in
PROLIFICACY_DISCOUNT = 0.7   # multiply weight by this when source is prolific

# === EVIDENCE SUFFICIENCY ===
# Minimum effective sample size (alpha + beta - 2) to consider posterior reliable.
SUFFICIENCY_THRESHOLD = 5.0


def _classify_direction(predicate: str) -> str:
    """Classify a predicate as 'positive', 'negative', or 'neutral'."""
    pred_lower = (predicate or "").lower()
    for kw in POSITIVE_KEYWORDS:
        if kw in pred_lower:
            return "positive"
    for kw in NEGATIVE_KEYWORDS:
        if kw in pred_lower:
            return "negative"
    return "neutral"


def _source_discount(source_claim_count: int) -> float:
    """Apply prolificacy discount for sources with many claims."""
    if source_claim_count >= PROLIFICACY_THRESHOLD:
        return PROLIFICACY_DISCOUNT
    return 1.0


async def bayesian_score(target_symbol: str) -> dict:
    """Compute Bayesian posterior for P(target is therapeutically valid).

    Prior: Beta(1, 1) — uninformative.
    For each claim about this target, update alpha or beta based on
    claim direction (positive/negative), claim_type weight, confidence,
    and source quality.

    Returns:
        dict with posterior_mean, posterior_mode, credible_interval_95,
        bayes_factor, evidence_sufficiency, claim_breakdown, and more.
    """
    from scipy.stats import beta as beta_dist

    # Find target by symbol
    target = await fetchrow(
        "SELECT id, symbol, name, target_type FROM targets WHERE symbol = $1",
        target_symbol,
    )
    if not target:
        return {"error": f"Target '{target_symbol}' not found"}

    target_id = str(target["id"])

    # Fetch all claims for this target with their evidence and source info
    rows = await fetch(
        """
        SELECT
            c.id            AS claim_id,
            c.claim_type,
            c.predicate,
            c.confidence,
            e.source_id
        FROM claims c
        LEFT JOIN evidence e ON e.claim_id = c.id
        WHERE c.subject_id = $1
        ORDER BY c.created_at
        """,
        target_id,
    )

    if not rows:
        return {
            "target": target_symbol,
            "target_id": target_id,
            "posterior_mean": 0.5,
            "posterior_mode": None,
            "credible_interval_95": [0.025, 0.975],
            "bayes_factor": 1.0,
            "evidence_sufficiency": False,
            "effective_sample_size": 0.0,
            "claim_count": 0,
            "message": "No claims found — returning uninformative prior",
        }

    # Count claims per source for prolificacy discount
    source_claim_counts: dict[str, int] = {}
    for row in rows:
        sid = str(row["source_id"]) if row.get("source_id") else None
        if sid:
            source_claim_counts[sid] = source_claim_counts.get(sid, 0) + 1

    # --- Bayesian updating ---
    alpha = 1.0  # Beta prior parameter
    beta_param = 1.0  # Beta prior parameter

    positive_updates = 0
    negative_updates = 0
    neutral_skipped = 0
    seen_claims: set[str] = set()
    type_breakdown: dict[str, int] = {}

    for row in rows:
        cid = str(row["claim_id"])
        if cid in seen_claims:
            continue  # avoid double-counting from multiple evidence rows
        seen_claims.add(cid)

        claim_type = row.get("claim_type") or "other"
        predicate = row.get("predicate") or ""
        confidence = float(row.get("confidence") or 0.5)
        source_id = str(row["source_id"]) if row.get("source_id") else None

        # Track type breakdown
        type_breakdown[claim_type] = type_breakdown.get(claim_type, 0) + 1

        # Determine direction
        direction = _classify_direction(predicate)
        if direction == "neutral":
            neutral_skipped += 1
            continue

        # Compute update weight
        base_weight = CLAIM_TYPE_WEIGHTS.get(claim_type, 0.5)
        weight = base_weight * confidence

        # Source prolificacy discount
        if source_id and source_id in source_claim_counts:
            weight *= _source_discount(source_claim_counts[source_id])

        # Update posterior
        if direction == "positive":
            alpha += weight
            positive_updates += 1
        elif direction == "negative":
            beta_param += weight
            negative_updates += 1

    # --- Posterior analysis ---
    posterior_mean = alpha / (alpha + beta_param)

    # Mode of Beta distribution: (alpha - 1) / (alpha + beta - 2)
    # Only defined when alpha > 1 and beta > 1
    if alpha > 1 and beta_param > 1:
        posterior_mode = (alpha - 1) / (alpha + beta_param - 2)
    else:
        posterior_mode = None

    # 95% credible interval
    ci_lower = float(beta_dist.ppf(0.025, alpha, beta_param))
    ci_upper = float(beta_dist.ppf(0.975, alpha, beta_param))

    # Bayes factor: ratio of posterior odds to prior odds
    # Prior odds = 1 (Beta(1,1) → mean 0.5)
    # Posterior odds = alpha / beta_param
    prior_odds = 1.0
    posterior_odds = alpha / beta_param
    bayes_factor = posterior_odds / prior_odds

    # Evidence sufficiency: is the posterior concentrated enough?
    effective_sample_size = (alpha + beta_param) - 2  # subtract prior contribution
    is_sufficient = effective_sample_size >= SUFFICIENCY_THRESHOLD

    # Posterior variance for informativeness
    posterior_variance = (alpha * beta_param) / (
        (alpha + beta_param) ** 2 * (alpha + beta_param + 1)
    )

    # Interpret Bayes factor strength (Jeffreys' scale)
    if bayes_factor >= 100:
        bf_interpretation = "decisive"
    elif bayes_factor >= 30:
        bf_interpretation = "very_strong"
    elif bayes_factor >= 10:
        bf_interpretation = "strong"
    elif bayes_factor >= 3:
        bf_interpretation = "substantial"
    elif bayes_factor >= 1:
        bf_interpretation = "weak"
    elif bayes_factor >= 1 / 3:
        bf_interpretation = "weak_against"
    elif bayes_factor >= 1 / 10:
        bf_interpretation = "substantial_against"
    else:
        bf_interpretation = "strong_against"

    return {
        "target": target_symbol,
        "target_id": target_id,
        "target_name": target.get("name"),
        "target_type": target.get("target_type"),
        "prior": {"alpha": 1.0, "beta": 1.0, "distribution": "Beta(1,1)"},
        "posterior": {
            "alpha": round(alpha, 3),
            "beta": round(beta_param, 3),
            "distribution": f"Beta({round(alpha, 3)}, {round(beta_param, 3)})",
        },
        "posterior_mean": round(posterior_mean, 4),
        "posterior_mode": round(posterior_mode, 4) if posterior_mode is not None else None,
        "posterior_variance": round(posterior_variance, 6),
        "credible_interval_95": [round(ci_lower, 4), round(ci_upper, 4)],
        "bayes_factor": round(bayes_factor, 4),
        "bayes_factor_interpretation": bf_interpretation,
        "evidence_sufficiency": is_sufficient,
        "effective_sample_size": round(effective_sample_size, 2),
        "claim_count": len(seen_claims),
        "positive_claims": positive_updates,
        "negative_claims": negative_updates,
        "neutral_skipped": neutral_skipped,
        "claim_type_breakdown": type_breakdown,
    }


async def bayesian_all_targets() -> list[dict]:
    """Compute Bayesian posterior for all targets. Sort by posterior mean descending.

    Returns a list of score summaries (one per target with claims).
    """
    targets = await fetch("SELECT id, symbol FROM targets ORDER BY symbol")

    results = []
    for t in targets:
        symbol = t["symbol"]
        score = await bayesian_score(symbol)
        if "error" in score:
            continue
        if score["claim_count"] == 0:
            continue
        results.append(score)

    # Sort by posterior mean descending (strongest evidence first)
    results.sort(key=lambda x: x["posterior_mean"], reverse=True)
    return results


async def bayesian_compare(target_a: str, target_b: str) -> dict:
    """Compare Bayesian evidence between two targets.

    Uses Monte Carlo sampling to estimate P(A > B) — the probability
    that target A has higher therapeutic validity than target B.

    Returns comparison summary with both posteriors and the probability.
    """
    from scipy.stats import beta as beta_dist
    import numpy as np

    score_a = await bayesian_score(target_a)
    score_b = await bayesian_score(target_b)

    if "error" in score_a:
        return {"error": f"Target A: {score_a['error']}"}
    if "error" in score_b:
        return {"error": f"Target B: {score_b['error']}"}

    alpha_a = score_a["posterior"]["alpha"]
    beta_a = score_a["posterior"]["beta"]
    alpha_b = score_b["posterior"]["alpha"]
    beta_b = score_b["posterior"]["beta"]

    # Monte Carlo estimate of P(A > B)
    n_samples = 100_000
    rng = np.random.default_rng(42)
    samples_a = rng.beta(alpha_a, beta_a, size=n_samples)
    samples_b = rng.beta(alpha_b, beta_b, size=n_samples)
    prob_a_greater = float(np.mean(samples_a > samples_b))

    # Effect size: difference in posterior means
    mean_diff = score_a["posterior_mean"] - score_b["posterior_mean"]

    # Determine winner
    if prob_a_greater > 0.95:
        verdict = f"{target_a} has significantly stronger evidence"
    elif prob_a_greater < 0.05:
        verdict = f"{target_b} has significantly stronger evidence"
    elif prob_a_greater > 0.7:
        verdict = f"{target_a} likely has stronger evidence"
    elif prob_a_greater < 0.3:
        verdict = f"{target_b} likely has stronger evidence"
    else:
        verdict = "Evidence is comparable — no clear winner"

    return {
        "target_a": {
            "symbol": target_a,
            "posterior_mean": score_a["posterior_mean"],
            "credible_interval_95": score_a["credible_interval_95"],
            "claim_count": score_a["claim_count"],
            "bayes_factor": score_a["bayes_factor"],
            "evidence_sufficiency": score_a["evidence_sufficiency"],
        },
        "target_b": {
            "symbol": target_b,
            "posterior_mean": score_b["posterior_mean"],
            "credible_interval_95": score_b["credible_interval_95"],
            "claim_count": score_b["claim_count"],
            "bayes_factor": score_b["bayes_factor"],
            "evidence_sufficiency": score_b["evidence_sufficiency"],
        },
        "probability_a_greater_than_b": round(prob_a_greater, 4),
        "probability_b_greater_than_a": round(1 - prob_a_greater, 4),
        "mean_difference": round(mean_diff, 4),
        "verdict": verdict,
    }
