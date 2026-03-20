"""Uncertainty Quantification — bootstrap confidence intervals on convergence scores.

For each target, resamples claims with replacement and recomputes a simplified
convergence score to produce confidence intervals. Wider CIs indicate less
certainty about a target's evidence strength.

Score formula per resample:
    claim_count * avg_confidence * source_diversity

Where source_diversity = unique_source_ids / total_evidence_links (0–1).

Evidence Uncertainty Intervals (Track 1 credibility):
    Uses the real convergence engine's 5-dimension formula with bootstrap
    resampling. Instead of just "63% convergence", produces
    "63% (95% CI: 58-68%)".
"""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from ..core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

# --- Convergence engine weights (mirrored from convergence_engine.py) ---
_CE_WEIGHTS = {
    "volume":           0.15,
    "lab_independence":  0.30,
    "method_diversity":  0.20,
    "temporal_trend":    0.15,
    "replication":       0.20,
}
_VOLUME_CEILING = 50
_LAB_CEILING = 10
_METHOD_CEILING = 6
_YEAR_SPAN_CEILING = 10

# Default bootstrap iterations for interval computation
N_BOOTSTRAP = 100


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


# ---------------------------------------------------------------------------
# Evidence Uncertainty Intervals — real convergence engine formula
# ---------------------------------------------------------------------------

def _extract_lab_proxy(authors: list[str] | None) -> str | None:
    """Extract lab proxy from senior (last) author's last name."""
    if not authors or not isinstance(authors, list):
        return None
    senior = authors[-1] if authors else ""
    if not senior:
        return None
    parts = re.split(r"[,\s]+", senior.strip())
    return parts[0].lower() if parts else None


def _convergence_engine_score(claims: list[dict]) -> float:
    """Compute convergence score using the real 5-dimension formula.

    Mirrors convergence_engine.py weights exactly:
        volume (0.15), lab_independence (0.30), method_diversity (0.20),
        temporal_trend (0.15), replication (0.20).
    """
    if not claims:
        return 0.0

    # Collect dimensions from the claim set
    claim_ids: list[str] = []
    source_ids: set[str] = set()
    lab_proxies: set[str] = set()
    methods: set[str] = set()
    years: list[int] = []
    predicates: Counter = Counter()
    predicate_sources: defaultdict[str, set[str]] = defaultdict(set)

    for c in claims:
        cid = str(c.get("claim_id", c.get("id", "")))
        if cid and cid not in claim_ids:
            claim_ids.append(cid)

        sid = str(c["source_id"]) if c.get("source_id") else None
        if sid:
            source_ids.add(sid)

        lab = _extract_lab_proxy(c.get("authors"))
        if lab:
            lab_proxies.add(lab)

        method = (c.get("method") or "").strip().lower()
        if method:
            methods.add(method)

        pub_date = c.get("pub_date")
        if pub_date:
            try:
                if hasattr(pub_date, "year"):
                    years.append(pub_date.year)
                else:
                    years.append(int(str(pub_date)[:4]))
            except (ValueError, TypeError):
                pass

        pred = (c.get("predicate") or "").strip().lower()[:100]
        if pred:
            predicates[pred] += 1
            if sid:
                predicate_sources[pred].add(sid)

    claim_count = len(claim_ids) or len(claims)

    # Dimension 1: Volume
    volume = _clamp(claim_count / _VOLUME_CEILING)

    # Dimension 2: Lab Independence
    lab_independence = _clamp(len(lab_proxies) / _LAB_CEILING)

    # Dimension 3: Method Diversity
    method_diversity = _clamp(len(methods) / _METHOD_CEILING)

    # Dimension 4: Temporal Trend
    if len(years) >= 2:
        year_span = max(years) - min(years)
        span_score = _clamp(year_span / _YEAR_SPAN_CEILING)
        unique_years = len(set(years))
        consistency = _clamp(unique_years / (year_span + 1))
        current_year = datetime.now(timezone.utc).year
        most_recent = max(years)
        recency = _clamp(1.0 - (current_year - most_recent) / 10.0)
        temporal_trend = _clamp(span_score * 0.3 + consistency * 0.4 + recency * 0.3)
    else:
        temporal_trend = 0.1

    # Dimension 5: Replication
    total_predicates = len(predicates)
    replicated = sum(
        1 for _pred, sources in predicate_sources.items()
        if len(sources) >= 2
    )
    replication = _clamp(replicated / max(total_predicates, 1))

    # Composite
    composite = _clamp(
        _CE_WEIGHTS["volume"] * volume
        + _CE_WEIGHTS["lab_independence"] * lab_independence
        + _CE_WEIGHTS["method_diversity"] * method_diversity
        + _CE_WEIGHTS["temporal_trend"] * temporal_trend
        + _CE_WEIGHTS["replication"] * replication
    )
    return composite


def _interpret_ci(score: float, lower: float, upper: float) -> str:
    """Human-readable interpretation of the confidence interval."""
    width = upper - lower
    if width < 0.05:
        return "Very stable -- narrow CI indicates robust evidence base"
    elif width < 0.10:
        return "Stable -- moderate CI suggests reliable scoring"
    elif width < 0.20:
        return "Moderate uncertainty -- additional evidence would narrow the interval"
    else:
        return "High uncertainty -- score may shift significantly with new evidence"


async def compute_uncertainty_intervals(
    target_symbol: str,
    n_bootstrap: int = N_BOOTSTRAP,
) -> dict[str, Any]:
    """Compute convergence score with 95% CI via bootstrap resampling.

    Uses the full 5-dimension convergence engine formula (volume,
    lab_independence, method_diversity, temporal_trend, replication)
    so the intervals match the real scores shown on target cards.
    """
    import numpy as np

    target = await fetchrow(
        "SELECT id, symbol, name FROM targets WHERE symbol = $1",
        target_symbol.upper(),
    )
    if not target:
        return {"target": target_symbol, "error": f"Target '{target_symbol}' not found"}

    target_id = str(target["id"])

    # Fetch claims with full evidence + source metadata for all 5 dimensions
    rows = await fetch(
        """
        SELECT
            c.id            AS claim_id,
            c.claim_type,
            c.predicate,
            c.confidence    AS claim_confidence,
            e.method,
            e.source_id,
            s.authors,
            s.pub_date,
            s.source_type
        FROM claims c
        LEFT JOIN evidence e ON e.claim_id = c.id
        LEFT JOIN sources s  ON e.source_id = s.id
        WHERE c.subject_id = $1
        ORDER BY c.created_at
        LIMIT 500
        """,
        target_id,
    )

    if len(rows) < 5:
        return {
            "target": target_symbol,
            "error": f"Insufficient claims ({len(rows)}) for bootstrapping -- need at least 5",
            "n_claims": len(rows),
        }

    claims = [dict(r) for r in rows]
    n_claims = len(claims)

    # Original score (no resampling)
    original_score = _convergence_engine_score(claims)

    # Bootstrap resampling
    rng = np.random.default_rng(seed=42)
    bootstrap_scores = np.empty(n_bootstrap, dtype=np.float64)

    for i in range(n_bootstrap):
        indices = rng.integers(0, n_claims, size=n_claims)
        sample = [claims[idx] for idx in indices]
        bootstrap_scores[i] = _convergence_engine_score(sample)

    # 95% CI from percentiles
    ci_lower = float(np.percentile(bootstrap_scores, 2.5))
    ci_upper = float(np.percentile(bootstrap_scores, 97.5))

    # Standard error
    std_err = float(np.std(bootstrap_scores, ddof=1)) if n_bootstrap > 1 else 0.0

    return {
        "target": target["symbol"],
        "target_name": target.get("name"),
        "score": round(original_score, 3),
        "ci_95_lower": round(ci_lower, 3),
        "ci_95_upper": round(ci_upper, 3),
        "ci_width": round(ci_upper - ci_lower, 3),
        "std_error": round(std_err, 3),
        "n_claims": n_claims,
        "n_bootstrap": n_bootstrap,
        "scoring_method": "convergence_engine_5d",
        "interpretation": _interpret_ci(original_score, ci_lower, ci_upper),
    }


async def compute_all_intervals(
    n_bootstrap: int = N_BOOTSTRAP,
) -> list[dict[str, Any]]:
    """Compute uncertainty intervals for all targets with >=5 claims.

    Returns list sorted by score descending (highest convergence first).
    """
    targets = await fetch(
        """
        SELECT t.symbol, COUNT(c.id) AS claim_count
        FROM targets t
        JOIN claims c ON c.subject_id = t.id
        GROUP BY t.symbol
        HAVING COUNT(c.id) >= 5
        ORDER BY t.symbol
        """
    )

    if not targets:
        return []

    results: list[dict[str, Any]] = []
    for t in targets:
        r = await compute_uncertainty_intervals(t["symbol"], n_bootstrap)
        if "error" not in r:
            results.append(r)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
