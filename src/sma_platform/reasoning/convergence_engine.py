"""Evidence Convergence Engine — quantifies how strongly evidence converges on a target.

All scoring weights and ceiling constants are module-level constants.
Open source, auditable, debatable. If you disagree with a weight,
open a GitHub issue or submit a PR at:
https://github.com/Bryzant-Labs/sma-platform

Scoring dimensions (sum of weights = 1.0):
1. Volume (0.15)           — how many claims mention this target
2. Lab Independence (0.30) — unique research groups providing evidence
3. Method Diversity (0.20) — variety of experimental methods
4. Temporal Trend (0.15)   — consistency of evidence over time
5. Replication (0.20)      — same finding reproduced by different groups
"""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

from ..core.database import execute, fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)


# === CONVERGENCE SCORING WEIGHTS ===
# These determine how different evidence dimensions contribute to
# the overall convergence score.
#
# Why Lab Independence is highest (0.30):
#   Single-lab findings are the #1 source of irreproducible results.
#   Multi-lab confirmation is the strongest signal of real biology.
#
# Why Volume is lowest (0.15):
#   A target being "well-studied" doesn't mean the evidence converges.
#   100 papers that contradict each other != strong evidence.

CONVERGENCE_WEIGHTS: dict[str, float] = {
    "volume":            0.15,
    "lab_independence":  0.30,
    "method_diversity":  0.20,
    "temporal_trend":    0.15,
    "replication":       0.20,
}

# === NORMALIZATION CEILINGS ===
# Scores saturate at these values (diminishing returns).
VOLUME_CEILING = 50        # 50+ claims = max volume score
LAB_CEILING = 10           # 10+ unique labs = max independence
METHOD_CEILING = 6         # 6+ distinct methods = max diversity
YEAR_SPAN_CEILING = 10     # 10+ year span = max temporal credit

# === CONFIDENCE LEVEL THRESHOLDS ===
CONFIDENCE_THRESHOLDS = {
    "very_high": 0.75,
    "high":      0.55,
    "medium":    0.35,
    "low":       0.0,
}

# Version tag — stored with each score so cards can be re-scored on weight changes
WEIGHTS_VERSION = "v1"


def _clamp(value: float) -> float:
    """Clamp to [0, 1] and round to 3 decimals."""
    return round(max(0.0, min(1.0, value)), 3)


def _extract_lab_proxy(authors: list[str] | None) -> str | None:
    """Extract a proxy for 'lab' from the senior (last) author's last name.

    Papers from the same lab typically share a senior (last) author —
    the PI. Last-author last name is used as a lightweight proxy without
    requiring institution parsing.
    """
    if not authors or not isinstance(authors, list):
        return None
    senior_author = authors[-1] if authors else ""
    if not senior_author:
        return None
    parts = re.split(r"[,\s]+", senior_author.strip())
    return parts[0].lower() if parts else None


def _confidence_level(score: float) -> str:
    """Map composite score to confidence level string."""
    for level, threshold in sorted(
        CONFIDENCE_THRESHOLDS.items(),
        key=lambda x: x[1],
        reverse=True,
    ):
        if score >= threshold:
            return level
    return "low"


async def compute_target_convergence(target_id: str) -> dict | None:
    """Compute convergence score for a single target.

    Returns dict with all 5 dimensions + composite, or None if <3 claims.
    """
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
        """,
        target_id,
    )

    if len(rows) < 3:
        return None

    claim_ids: list[str] = []
    source_ids: set[str] = set()
    lab_proxies: set[str] = set()
    methods: set[str] = set()
    years: list[int] = []
    predicates: Counter = Counter()
    predicate_sources: defaultdict[str, set[str]] = defaultdict(set)

    for row in rows:
        r = dict(row)
        cid = str(r["claim_id"])
        if cid not in claim_ids:
            claim_ids.append(cid)

        sid = str(r["source_id"]) if r.get("source_id") else None
        if sid:
            source_ids.add(sid)

        lab = _extract_lab_proxy(r.get("authors"))
        if lab:
            lab_proxies.add(lab)

        method = (r.get("method") or "").strip().lower()
        if method:
            methods.add(method)

        pub_date = r.get("pub_date")
        if pub_date:
            try:
                if hasattr(pub_date, "year"):
                    years.append(pub_date.year)
                else:
                    years.append(int(str(pub_date)[:4]))
            except (ValueError, TypeError):
                pass

        pred = (r.get("predicate") or "").strip().lower()[:100]
        if pred:
            predicates[pred] += 1
            if sid:
                predicate_sources[pred].add(sid)

    claim_count = len(claim_ids)
    source_count = len(source_ids)

    # --- Dimension 1: Volume ---
    volume = _clamp(claim_count / VOLUME_CEILING)

    # --- Dimension 2: Lab Independence ---
    lab_independence = _clamp(len(lab_proxies) / LAB_CEILING)

    # --- Dimension 3: Method Diversity ---
    method_diversity = _clamp(len(methods) / METHOD_CEILING)

    # --- Dimension 4: Temporal Trend ---
    if len(years) >= 2:
        year_span = max(years) - min(years)
        span_score = _clamp(year_span / YEAR_SPAN_CEILING)
        unique_years = len(set(years))
        consistency = _clamp(unique_years / (year_span + 1))
        current_year = datetime.now(timezone.utc).year
        most_recent = max(years)
        recency = _clamp(1.0 - (current_year - most_recent) / 10.0)
        temporal_trend = _clamp(span_score * 0.3 + consistency * 0.4 + recency * 0.3)
    else:
        temporal_trend = 0.1

    # --- Dimension 5: Replication ---
    total_predicates = len(predicates)
    replicated = sum(
        1 for pred, sources in predicate_sources.items()
        if len(sources) >= 2
    )
    replication = _clamp(replicated / max(total_predicates, 1))

    # --- Composite Score ---
    composite = _clamp(
        CONVERGENCE_WEIGHTS["volume"] * volume
        + CONVERGENCE_WEIGHTS["lab_independence"] * lab_independence
        + CONVERGENCE_WEIGHTS["method_diversity"] * method_diversity
        + CONVERGENCE_WEIGHTS["temporal_trend"] * temporal_trend
        + CONVERGENCE_WEIGHTS["replication"] * replication
    )

    return {
        "target_id": target_id,
        "volume": volume,
        "lab_independence": lab_independence,
        "method_diversity": method_diversity,
        "temporal_trend": temporal_trend,
        "replication": replication,
        "composite_score": composite,
        "confidence_level": _confidence_level(composite),
        "claim_count": claim_count,
        "source_count": source_count,
        "claim_ids": claim_ids,
        "methods_found": sorted(methods),
        "labs_found": sorted(lab_proxies),
        "year_range": [min(years), max(years)] if years else [],
    }


async def compute_all_convergence() -> dict:
    """Batch-compute convergence scores for all targets with >=3 claims.

    Upserts into convergence_scores table.
    """
    targets = await fetch("SELECT id, symbol, target_type FROM targets ORDER BY symbol")

    scored = 0
    skipped = 0
    results = []

    for t in targets:
        t = dict(t)
        tid = str(t["id"])
        result = await compute_target_convergence(tid)

        if result is None:
            skipped += 1
            continue

        target_key = f"target:{tid}"

        await execute(
            """
            INSERT INTO convergence_scores
                (target_key, target_label, target_type, target_id,
                 volume, lab_independence, method_diversity, temporal_trend, replication,
                 composite_score, confidence_level, claim_count, source_count, claim_ids,
                 computed_at, weights_version)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW(), $15)
            ON CONFLICT (target_key, weights_version)
            DO UPDATE SET
                target_label = EXCLUDED.target_label,
                volume = EXCLUDED.volume,
                lab_independence = EXCLUDED.lab_independence,
                method_diversity = EXCLUDED.method_diversity,
                temporal_trend = EXCLUDED.temporal_trend,
                replication = EXCLUDED.replication,
                composite_score = EXCLUDED.composite_score,
                confidence_level = EXCLUDED.confidence_level,
                claim_count = EXCLUDED.claim_count,
                source_count = EXCLUDED.source_count,
                claim_ids = EXCLUDED.claim_ids,
                computed_at = NOW()
            """,
            target_key,
            t["symbol"],
            t.get("target_type", "target"),
            tid,
            result["volume"],
            result["lab_independence"],
            result["method_diversity"],
            result["temporal_trend"],
            result["replication"],
            result["composite_score"],
            result["confidence_level"],
            result["claim_count"],
            result["source_count"],
            result["claim_ids"],
            WEIGHTS_VERSION,
        )

        results.append({
            "target": t["symbol"],
            "composite_score": result["composite_score"],
            "confidence_level": result["confidence_level"],
            "claim_count": result["claim_count"],
        })
        scored += 1

    logger.info("Convergence scoring complete: %d scored, %d skipped", scored, skipped)
    return {
        "targets_scored": scored,
        "targets_skipped": skipped,
        "weights_version": WEIGHTS_VERSION,
        "results": results,
    }
