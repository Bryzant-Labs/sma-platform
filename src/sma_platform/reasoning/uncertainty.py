"""Uncertainty Quantification — bootstrap confidence intervals on convergence scores.

For each target, resamples claims with replacement and recomputes a simplified
convergence score to produce confidence intervals. Wider CIs indicate less
certainty about a target's evidence strength.

Score formula per resample:
    claim_count * avg_confidence * source_diversity

Where source_diversity = unique_source_ids / total_evidence_links (0–1).
"""

from __future__ import annotations

import logging
from typing import Any

from ..core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)


def _clamp(value: float) -> float:
    """Clamp to [0, 1] and round to 4 decimals."""
    return round(max(0.0, min(1.0, value)), 4)


def _simplified_convergence(claims: list[dict]) -> float:
    """Compute a simplified convergence score for a set of claims.

    score = claim_count * avg_confidence * source_diversity

    Normalized so typical values fall in [0, 1].
    """
    if not claims:
        return 0.0

    count = len(claims)

    # Average confidence
    confidences = [c.get("confidence") or 0.5 for c in claims]
    avg_conf = sum(confidences) / len(confidences)

    # Source diversity: fraction of unique sources among all evidence links
    source_ids = set()
    total_links = 0
    for c in claims:
        sid = c.get("source_id")
        if sid:
            source_ids.add(str(sid))
            total_links += 1

    source_diversity = len(source_ids) / max(total_links, 1)

    # Raw score — normalize count by a ceiling of 50 (same as convergence engine)
    raw = (min(count, 50) / 50.0) * avg_conf * source_diversity
    return _clamp(raw)


async def compute_uncertainty(
    target_symbol: str,
    n_bootstrap: int = 500,
) -> dict[str, Any]:
    """Bootstrap confidence intervals on the convergence score for a target.

    1. Fetch all claims + evidence for this target (by symbol).
    2. Resample claims with replacement N times.
    3. For each resample, compute simplified convergence score.
    4. Return mean, std, 95% CI, and a 10-bin histogram of the distribution.
    """
    import numpy as np

    # Resolve target symbol to id
    target = await fetchrow(
        "SELECT id, symbol, name FROM targets WHERE symbol = $1",
        target_symbol.upper(),
    )
    if not target:
        return {"error": f"Target '{target_symbol}' not found"}

    target_id = str(target["id"])

    # Fetch claims with evidence source info
    rows = await fetch(
        """
        SELECT
            c.id            AS claim_id,
            c.confidence,
            c.claim_type,
            e.source_id
        FROM claims c
        LEFT JOIN evidence e ON e.claim_id = c.id
        WHERE c.subject_id = $1
        """,
        target_id,
    )

    if len(rows) < 3:
        return {
            "target_symbol": target["symbol"],
            "target_name": target.get("name"),
            "error": f"Too few claims ({len(rows)}) for bootstrap — need at least 3",
            "claim_count": len(rows),
        }

    claims = [dict(r) for r in rows]
    n_claims = len(claims)

    # Bootstrap resampling
    rng = np.random.default_rng(seed=42)
    bootstrap_scores = np.empty(n_bootstrap, dtype=np.float64)

    for i in range(n_bootstrap):
        indices = rng.integers(0, n_claims, size=n_claims)
        resample = [claims[idx] for idx in indices]
        bootstrap_scores[i] = _simplified_convergence(resample)

    # Statistics
    mean_score = float(np.mean(bootstrap_scores))
    std_score = float(np.std(bootstrap_scores, ddof=1))
    ci_lower = float(np.percentile(bootstrap_scores, 2.5))
    ci_upper = float(np.percentile(bootstrap_scores, 97.5))
    ci_width = round(ci_upper - ci_lower, 4)

    # Histogram (10 bins)
    counts, bin_edges = np.histogram(bootstrap_scores, bins=10)
    histogram = [
        {
            "bin_start": round(float(bin_edges[j]), 4),
            "bin_end": round(float(bin_edges[j + 1]), 4),
            "count": int(counts[j]),
        }
        for j in range(len(counts))
    ]

    # Original (non-bootstrapped) score for reference
    original_score = _simplified_convergence(claims)

    return {
        "target_symbol": target["symbol"],
        "target_name": target.get("name"),
        "claim_count": n_claims,
        "original_score": round(original_score, 4),
        "bootstrap": {
            "n_resamples": n_bootstrap,
            "mean": round(mean_score, 4),
            "std": round(std_score, 4),
            "ci_95_lower": round(ci_lower, 4),
            "ci_95_upper": round(ci_upper, 4),
            "ci_width": ci_width,
        },
        "histogram": histogram,
    }


async def compute_all_uncertainties() -> list[dict[str, Any]]:
    """Compute bootstrap uncertainty for all targets with >10 claims.

    Returns a list sorted by CI width (descending) — widest (most uncertain) first.
    """
    import numpy as np

    # Find targets with >10 claims
    targets = await fetch(
        """
        SELECT t.symbol, COUNT(c.id) AS claim_count
        FROM targets t
        JOIN claims c ON c.subject_id = t.id
        GROUP BY t.symbol
        HAVING COUNT(c.id) > 10
        ORDER BY t.symbol
        """
    )

    if not targets:
        return []

    results: list[dict[str, Any]] = []
    for t in targets:
        symbol = t["symbol"]
        result = await compute_uncertainty(symbol)
        if "error" not in result:
            results.append(result)

    # Sort by CI width descending (most uncertain first)
    results.sort(
        key=lambda r: r.get("bootstrap", {}).get("ci_width", 0),
        reverse=True,
    )

    return results


async def uncertainty_summary() -> dict[str, Any]:
    """Overall platform uncertainty summary.

    Reports what fraction of targets have narrow CIs (<0.1) vs wide (>0.3),
    plus overall statistics.
    """
    all_results = await compute_all_uncertainties()

    if not all_results:
        return {
            "total_targets_analyzed": 0,
            "message": "No targets with >10 claims found",
        }

    ci_widths = [
        r["bootstrap"]["ci_width"]
        for r in all_results
        if "bootstrap" in r
    ]

    narrow = [w for w in ci_widths if w < 0.1]
    medium = [w for w in ci_widths if 0.1 <= w <= 0.3]
    wide = [w for w in ci_widths if w > 0.3]

    total = len(ci_widths)

    return {
        "total_targets_analyzed": total,
        "narrow_ci": {
            "threshold": "< 0.1",
            "count": len(narrow),
            "fraction": round(len(narrow) / total, 3) if total else 0,
            "interpretation": "High confidence — evidence is consistent",
        },
        "medium_ci": {
            "threshold": "0.1 – 0.3",
            "count": len(medium),
            "fraction": round(len(medium) / total, 3) if total else 0,
            "interpretation": "Moderate uncertainty — more evidence may help",
        },
        "wide_ci": {
            "threshold": "> 0.3",
            "count": len(wide),
            "fraction": round(len(wide) / total, 3) if total else 0,
            "interpretation": "High uncertainty — evidence is sparse or conflicting",
        },
        "overall": {
            "mean_ci_width": round(sum(ci_widths) / total, 4) if total else 0,
            "min_ci_width": round(min(ci_widths), 4) if ci_widths else 0,
            "max_ci_width": round(max(ci_widths), 4) if ci_widths else 0,
        },
        "most_uncertain": [
            {
                "symbol": r["target_symbol"],
                "ci_width": r["bootstrap"]["ci_width"],
                "claim_count": r["claim_count"],
            }
            for r in all_results[:5]  # already sorted by CI width desc
        ],
        "most_certain": [
            {
                "symbol": r["target_symbol"],
                "ci_width": r["bootstrap"]["ci_width"],
                "claim_count": r["claim_count"],
            }
            for r in all_results[-5:][::-1]  # reverse for ascending certainty
        ],
    }
