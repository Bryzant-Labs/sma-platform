"""M5 Uncertainty Quantification Engine.

Computes explicit confidence intervals and uncertainty estimates for every
target prediction on the platform. Goes beyond bootstrap resampling (see
uncertainty.py) by combining three orthogonal uncertainty signals:

1. **Wilson Score CI** on the support ratio — what fraction of claims
   support this target (confidence >= 0.6) vs oppose (confidence < 0.3)?
   Wilson score handles small sample sizes correctly, unlike naive
   proportion CIs.

2. **Source Diversity** — how many independent labs contribute evidence?
   Single-lab findings are the #1 cause of irreproducible results.
   More independent labs = narrower real uncertainty.

3. **Temporal Stability** — is evidence growing (more recent claims) or
   shrinking (old claims, no follow-up)? Stale evidence is less certain.

Each target receives:
- Point estimate (support ratio)
- 95% Wilson CI (lower, upper)
- Uncertainty grade (A = high certainty, D = high uncertainty)
- Contributing factor breakdown

References:
- Wilson, E.B. (1927). "Probable Inference, the Law of Succession, and
  Statistical Inference." JASA 22:209-212.
- Agresti, A. & Coull, B.A. (1998). "Approximate Is Better than Exact
  for Interval Estimation of Binomial Proportions." Am Statistician 52:119-126.
"""

from __future__ import annotations

import logging
import math
import re
from datetime import datetime, timezone
from typing import Any

from ..core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

# --- Thresholds for classifying claim stance from confidence ---
SUPPORT_THRESHOLD = 0.6   # claim confidence >= 0.6 = "supports"
OPPOSE_THRESHOLD = 0.3    # claim confidence < 0.3 = "opposes"
# Between 0.3 and 0.6 = "neutral / ambiguous"

# --- Grade thresholds (composite uncertainty score 0-1, higher = more certain) ---
GRADE_THRESHOLDS: dict[str, float] = {
    "A": 0.70,   # High certainty — tight CI, many labs, growing evidence
    "B": 0.50,   # Moderate certainty
    "C": 0.30,   # Low certainty — wide CI or few labs
    "D": 0.00,   # Very uncertain — sparse or conflicting evidence
}

# --- Weights for composite certainty score ---
CERTAINTY_WEIGHTS: dict[str, float] = {
    "ci_tightness": 0.40,       # How narrow is the Wilson CI?
    "source_diversity": 0.35,   # How many independent labs?
    "temporal_stability": 0.25, # Is evidence recent and growing?
}

# Ceilings for normalization
LAB_CEILING = 10
RECENT_YEAR_WINDOW = 5   # Claims within last 5 years count as "recent"


def wilson_ci(successes: int, total: int, z: float = 1.96) -> tuple[float, float, float]:
    """Wilson score confidence interval for a binomial proportion.

    Returns (lower, upper, center) for the 95% CI by default (z=1.96).
    Handles edge cases: total=0 returns (0, 1, 0.5) representing maximum
    uncertainty.

    Args:
        successes: Number of positive outcomes (supporting claims).
        total: Total number of observations (all classified claims).
        z: Z-score for desired confidence level (1.96 = 95%).

    Returns:
        Tuple of (ci_lower, ci_upper, center_estimate).
    """
    if total == 0:
        return 0.0, 1.0, 0.5

    p = successes / total
    z2 = z ** 2
    denom = 1 + z2 / total
    center = (p + z2 / (2 * total)) / denom
    spread = z * math.sqrt((p * (1 - p) + z2 / (4 * total)) / total) / denom

    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)

    return round(lower, 4), round(upper, 4), round(center, 4)


def _assign_grade(certainty_score: float) -> tuple[str, str]:
    """Map a composite certainty score (0-1) to a letter grade and label."""
    for grade, threshold in sorted(
        GRADE_THRESHOLDS.items(), key=lambda x: x[1], reverse=True,
    ):
        if certainty_score >= threshold:
            labels = {
                "A": "High certainty -- tight CI, diverse sources, growing evidence",
                "B": "Moderate certainty -- some gaps remain",
                "C": "Low certainty -- limited sources or wide CI",
                "D": "Very uncertain -- sparse, conflicting, or stale evidence",
            }
            return grade, labels[grade]
    return "D", "Very uncertain -- sparse, conflicting, or stale evidence"


async def compute_target_uncertainty(target_symbol: str) -> dict[str, Any]:
    """Compute uncertainty quantification for a single target.

    For the given target:
    1. Counts claims for/against/neutral (based on confidence thresholds)
    2. Computes Wilson score CI for the support ratio
    3. Computes source diversity (independent labs)
    4. Computes temporal stability (evidence trend over time)
    5. Combines into a composite certainty score with A-D grade

    Args:
        target_symbol: Gene symbol (e.g. "SMN1", "STMN2").

    Returns:
        Dict with point estimate, 95% CI, uncertainty grade, and factors.
    """
    # Resolve target
    target = await fetchrow(
        "SELECT id, symbol, name FROM targets WHERE symbol = $1",
        target_symbol.upper(),
    )
    if not target:
        return {"error": f"Target '{target_symbol}' not found"}

    target_id = str(target["id"])

    # Fetch claims with evidence and source metadata
    rows = await fetch(
        """
        SELECT
            c.id            AS claim_id,
            c.confidence,
            c.claim_type,
            c.created_at    AS claim_created,
            e.source_id,
            s.authors,
            s.pub_date
        FROM claims c
        LEFT JOIN evidence e ON e.claim_id = c.id
        LEFT JOIN sources s  ON e.source_id = s.id
        WHERE c.subject_id = $1
        ORDER BY c.created_at
        """,
        target_id,
    )

    if not rows:
        return {
            "target_symbol": target["symbol"],
            "target_name": target.get("name"),
            "error": "No claims found for this target",
            "claim_count": 0,
            "grade": "D",
            "grade_label": "Very uncertain -- no evidence available",
        }

    claims = [dict(r) for r in rows]

    # --- 1. Classify claims: support / oppose / neutral ---
    support_count = 0
    oppose_count = 0
    neutral_count = 0
    seen_claim_ids: set[str] = set()

    for c in claims:
        cid = str(c.get("claim_id", ""))
        if cid in seen_claim_ids:
            continue  # Deduplicate (a claim may join to multiple evidence rows)
        seen_claim_ids.add(cid)

        conf = c.get("confidence") or 0.5
        if conf >= SUPPORT_THRESHOLD:
            support_count += 1
        elif conf < OPPOSE_THRESHOLD:
            oppose_count += 1
        else:
            neutral_count += 1

    total_classified = support_count + oppose_count + neutral_count
    total_for_wilson = support_count + oppose_count  # exclude neutral for ratio

    # Wilson CI on support ratio (support / (support + oppose))
    if total_for_wilson > 0:
        ci_lower, ci_upper, center = wilson_ci(support_count, total_for_wilson)
    else:
        # All claims are neutral -- use total_classified with support
        ci_lower, ci_upper, center = wilson_ci(support_count, total_classified)

    ci_width = round(ci_upper - ci_lower, 4)

    # CI tightness score: narrow CI = high certainty (1 - width, clamped)
    ci_tightness = max(0.0, min(1.0, 1.0 - ci_width))

    # --- 2. Source diversity ---
    source_ids: set[str] = set()
    lab_proxies: set[str] = set()

    for c in claims:
        sid = c.get("source_id")
        if sid:
            source_ids.add(str(sid))
        authors = c.get("authors")
        if authors and isinstance(authors, list) and authors:
            # Senior (last) author's last name as lab proxy
            senior = authors[-1] if authors else ""
            if senior:
                parts = re.split(r"[,\s]+", senior.strip())
                if parts:
                    lab_proxies.add(parts[0].lower())

    unique_sources = len(source_ids)
    unique_labs = len(lab_proxies)
    source_diversity_score = min(1.0, unique_labs / LAB_CEILING)

    # --- 3. Temporal stability ---
    current_year = datetime.now(timezone.utc).year
    years: list[int] = []

    for c in claims:
        pub_date = c.get("pub_date")
        if pub_date:
            try:
                if hasattr(pub_date, "year"):
                    years.append(pub_date.year)
                else:
                    years.append(int(str(pub_date)[:4]))
            except (ValueError, TypeError):
                pass

    if years:
        recent_claims = sum(1 for y in years if current_year - y <= RECENT_YEAR_WINDOW)
        recency_ratio = recent_claims / len(years)

        # Year span -- evidence covering more years is more stable
        year_span = max(years) - min(years)
        span_score = min(1.0, year_span / 10.0)

        # Is evidence growing? Compare first half vs second half by year
        sorted_years = sorted(years)
        mid = len(sorted_years) // 2
        first_half_count = mid
        second_half_count = len(sorted_years) - mid
        growth_ratio = second_half_count / max(first_half_count, 1)
        growth_score = min(1.0, growth_ratio / 2.0)  # 2x growth = max score

        temporal_stability = round(
            recency_ratio * 0.4 + span_score * 0.3 + growth_score * 0.3,
            4,
        )
    else:
        temporal_stability = 0.1  # No date info = low stability
        recency_ratio = 0.0
        growth_score = 0.0

    # --- 4. Composite certainty score ---
    certainty_score = round(
        CERTAINTY_WEIGHTS["ci_tightness"] * ci_tightness
        + CERTAINTY_WEIGHTS["source_diversity"] * source_diversity_score
        + CERTAINTY_WEIGHTS["temporal_stability"] * temporal_stability,
        4,
    )

    grade, grade_label = _assign_grade(certainty_score)

    return {
        "target_symbol": target["symbol"],
        "target_name": target.get("name"),
        "support_ratio": {
            "point_estimate": center,
            "ci_95_lower": ci_lower,
            "ci_95_upper": ci_upper,
            "ci_width": ci_width,
            "method": "wilson_score",
        },
        "claim_counts": {
            "support": support_count,
            "oppose": oppose_count,
            "neutral": neutral_count,
            "total": total_classified,
        },
        "source_diversity": {
            "unique_sources": unique_sources,
            "unique_labs": unique_labs,
            "score": round(source_diversity_score, 4),
        },
        "temporal_stability": {
            "years_covered": sorted(set(years)) if years else [],
            "recency_ratio": round(recency_ratio, 4) if years else 0.0,
            "growth_score": round(growth_score, 4) if years else 0.0,
            "score": temporal_stability,
        },
        "certainty_score": certainty_score,
        "grade": grade,
        "grade_label": grade_label,
        "contributing_factors": {
            "ci_tightness": {
                "weight": CERTAINTY_WEIGHTS["ci_tightness"],
                "value": round(ci_tightness, 4),
                "contribution": round(CERTAINTY_WEIGHTS["ci_tightness"] * ci_tightness, 4),
            },
            "source_diversity": {
                "weight": CERTAINTY_WEIGHTS["source_diversity"],
                "value": round(source_diversity_score, 4),
                "contribution": round(CERTAINTY_WEIGHTS["source_diversity"] * source_diversity_score, 4),
            },
            "temporal_stability": {
                "weight": CERTAINTY_WEIGHTS["temporal_stability"],
                "value": temporal_stability,
                "contribution": round(CERTAINTY_WEIGHTS["temporal_stability"] * temporal_stability, 4),
            },
        },
    }


async def compute_all_uncertainties() -> list[dict[str, Any]]:
    """Batch compute uncertainty quantification for all targets with claims.

    Returns a list sorted by certainty score ascending (most uncertain first).
    """
    targets = await fetch(
        """
        SELECT t.symbol, COUNT(c.id) AS claim_count
        FROM targets t
        JOIN claims c ON c.subject_id = t.id
        GROUP BY t.symbol
        HAVING COUNT(c.id) >= 3
        ORDER BY t.symbol
        """
    )

    if not targets:
        return []

    results: list[dict[str, Any]] = []
    for t in targets:
        result = await compute_target_uncertainty(t["symbol"])
        if "error" not in result:
            results.append(result)

    # Sort by certainty score ascending (most uncertain first)
    results.sort(key=lambda r: r.get("certainty_score", 0))

    return results


async def get_uncertainty_report() -> dict[str, Any]:
    """Full uncertainty quantification report.

    Returns:
    - Per-target uncertainty bands (Wilson CI + grade)
    - Overall platform uncertainty summary
    - Highest-certainty predictions (most actionable)
    - Highest-uncertainty predictions (need more evidence)
    """
    all_results = await compute_all_uncertainties()

    if not all_results:
        return {
            "status": "no_data",
            "total_targets": 0,
            "message": "No targets with >= 3 claims found",
        }

    # Grade distribution
    grade_counts: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}
    ci_widths: list[float] = []
    certainty_scores: list[float] = []

    for r in all_results:
        grade = r.get("grade", "D")
        grade_counts[grade] = grade_counts.get(grade, 0) + 1
        ci_widths.append(r["support_ratio"]["ci_width"])
        certainty_scores.append(r["certainty_score"])

    total = len(all_results)
    mean_certainty = round(sum(certainty_scores) / total, 4) if total else 0.0
    mean_ci_width = round(sum(ci_widths) / total, 4) if total else 0.0

    # Overall platform grade
    platform_grade, platform_label = _assign_grade(mean_certainty)

    # Most certain (last 5, since sorted ascending)
    most_certain = [
        {
            "symbol": r["target_symbol"],
            "name": r.get("target_name"),
            "certainty_score": r["certainty_score"],
            "grade": r["grade"],
            "ci_width": r["support_ratio"]["ci_width"],
            "support_ratio": r["support_ratio"]["point_estimate"],
            "unique_labs": r["source_diversity"]["unique_labs"],
        }
        for r in reversed(all_results[-5:])
    ]

    # Most uncertain (first 5, sorted ascending)
    most_uncertain = [
        {
            "symbol": r["target_symbol"],
            "name": r.get("target_name"),
            "certainty_score": r["certainty_score"],
            "grade": r["grade"],
            "ci_width": r["support_ratio"]["ci_width"],
            "support_ratio": r["support_ratio"]["point_estimate"],
            "unique_labs": r["source_diversity"]["unique_labs"],
        }
        for r in all_results[:5]
    ]

    return {
        "status": "completed",
        "total_targets": total,
        "platform_summary": {
            "mean_certainty": mean_certainty,
            "mean_ci_width": mean_ci_width,
            "platform_grade": platform_grade,
            "platform_label": platform_label,
            "grade_distribution": grade_counts,
            "grade_fractions": {
                g: round(c / total, 3) for g, c in grade_counts.items()
            },
        },
        "most_certain": most_certain,
        "most_uncertain": most_uncertain,
        "all_targets": all_results,
        "methodology": {
            "support_ratio": (
                "Wilson score CI on the fraction of claims with confidence >= 0.6 "
                "(supporting) vs confidence < 0.3 (opposing). Wilson score is "
                "preferred over naive proportion CIs because it handles small "
                "sample sizes correctly."
            ),
            "source_diversity": (
                "Number of independent research labs (estimated from senior "
                f"authors) normalized by ceiling of {LAB_CEILING}."
            ),
            "temporal_stability": (
                "Combination of recency (fraction of claims within last "
                f"{RECENT_YEAR_WINDOW} years), year span, and evidence growth trend."
            ),
            "grading": {
                "A": ">= 0.70 — High certainty",
                "B": ">= 0.50 — Moderate certainty",
                "C": ">= 0.30 — Low certainty",
                "D": "< 0.30 — Very uncertain",
            },
            "weights": CERTAINTY_WEIGHTS,
        },
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }
