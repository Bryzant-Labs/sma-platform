"""Phase 2 target prioritization module.

Scores each target across 8 orthogonal dimensions (all normalized 0.0-1.0):

1. evidence_volume       -- claim count for target, normalized by max across all targets
2. evidence_quality      -- average confidence of claims linked to this target
3. biological_coherence  -- diversity of claim_type values (distinct types / 12)
4. source_independence   -- distinct source papers via evidence, normalized by max
5. interventionability   -- fraction of claims that are drug-related types
6. translational_readiness -- drugs or trials linked (binary/partial)
7. network_centrality    -- graph_edges degree, normalized by max
8. novelty_discovery     -- emerging/unconventional targets get a discovery bonus
                           (inverse of evidence saturation + recency bias)

Composite = weighted average with explicit weights.
Design principle: SMN2 being #1 is trivially obvious. The scoring should surface
non-obvious, high-potential targets that a human researcher might miss.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ..core.database import execute, fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Weights (must sum to 1.0)
# ---------------------------------------------------------------------------

WEIGHTS: dict[str, float] = {
    "evidence_volume": 0.08,         # reduced — being well-known shouldn't dominate
    "evidence_quality": 0.18,        # high-quality evidence matters
    "biological_coherence": 0.15,    # diverse evidence types = strong target
    "source_independence": 0.10,     # reduced — fewer papers ≠ less important
    "interventionability": 0.15,     # can we actually drug this?
    "translational_readiness": 0.10, # existing drugs/trials
    "network_centrality": 0.09,     # pathway connectivity
    "novelty_discovery": 0.15,       # NEW — emerging/unconventional targets boosted
}

# The 12 valid claim_type values defined in the schema.
_TOTAL_CLAIM_TYPES = 12

# Claim types that count towards interventionability.
_DRUG_RELATED_TYPES = {"drug_target", "drug_efficacy"}


def _clamp(value: float) -> float:
    """Clamp to [0.0, 1.0] and round to 4 decimals."""
    return round(max(0.0, min(1.0, value)), 4)


# ---------------------------------------------------------------------------
# Normalization helpers -- compute "max across all targets" once per batch run
# ---------------------------------------------------------------------------


async def _max_claims_per_target() -> int:
    """Return the maximum number of claims any single target has as subject_id."""
    row = await fetchrow(
        "SELECT MAX(cnt) AS mx FROM ("
        "  SELECT COUNT(*) AS cnt FROM claims"
        "  WHERE subject_id IS NOT NULL GROUP BY subject_id"
        ")"
    )
    return int(row["mx"]) if row and row["mx"] else 1


async def _max_sources_per_target() -> int:
    """Return the maximum count of distinct sources linked to any single target."""
    row = await fetchrow(
        "SELECT MAX(cnt) AS mx FROM ("
        "  SELECT COUNT(DISTINCT e.source_id) AS cnt"
        "  FROM claims c"
        "  JOIN evidence e ON e.claim_id = c.id"
        "  WHERE c.subject_id IS NOT NULL"
        "  GROUP BY c.subject_id"
        ")"
    )
    return int(row["mx"]) if row and row["mx"] else 1


async def _max_edges_per_target() -> int:
    """Return the maximum graph-edge degree (in + out) for any single target."""
    row = await fetchrow(
        "SELECT MAX(cnt) AS mx FROM ("
        "  SELECT target_id, SUM(cnt) AS cnt FROM ("
        "    SELECT src_id AS target_id, COUNT(*) AS cnt"
        "    FROM graph_edges GROUP BY src_id"
        "    UNION ALL"
        "    SELECT dst_id AS target_id, COUNT(*) AS cnt"
        "    FROM graph_edges GROUP BY dst_id"
        "  ) sub GROUP BY target_id"
        ")"
    )
    return int(row["mx"]) if row and row["mx"] else 1


# ---------------------------------------------------------------------------
# Per-target dimension scorers
# ---------------------------------------------------------------------------


async def _evidence_volume(target_id: str, *, max_claims: int) -> float:
    """Dimension 1: number of claims where target is subject_id, normalized."""
    val = await fetchval(
        "SELECT COUNT(*) FROM claims WHERE subject_id = $1",
        target_id,
    )
    n = int(val) if val else 0
    return _clamp(n / max_claims) if max_claims > 0 else 0.0


async def _evidence_quality(target_id: str) -> float:
    """Dimension 2: average confidence of claims linked to this target."""
    row = await fetchrow(
        "SELECT AVG(confidence) AS avg_conf FROM claims WHERE subject_id = $1",
        target_id,
    )
    if row and row["avg_conf"] is not None:
        return _clamp(float(row["avg_conf"]))
    return 0.0


async def _biological_coherence(target_id: str) -> float:
    """Dimension 3: diversity of claim_type values.

    Score = count(distinct claim_type) / 12.0  (12 valid types in schema).
    """
    val = await fetchval(
        "SELECT COUNT(DISTINCT claim_type) FROM claims WHERE subject_id = $1",
        target_id,
    )
    n = int(val) if val else 0
    return _clamp(n / _TOTAL_CLAIM_TYPES)


async def _source_independence(target_id: str, *, max_sources: int) -> float:
    """Dimension 4: count of distinct source papers via evidence table, normalized."""
    val = await fetchval(
        "SELECT COUNT(DISTINCT e.source_id)"
        " FROM claims c"
        " JOIN evidence e ON e.claim_id = c.id"
        " WHERE c.subject_id = $1",
        target_id,
    )
    n = int(val) if val else 0
    return _clamp(n / max_sources) if max_sources > 0 else 0.0


async def _interventionability(target_id: str) -> float:
    """Dimension 5: fraction of claims that are drug-related types."""
    total_val = await fetchval(
        "SELECT COUNT(*) FROM claims WHERE subject_id = $1",
        target_id,
    )
    total = int(total_val) if total_val else 0
    if total == 0:
        return 0.0

    drug_val = await fetchval(
        "SELECT COUNT(*) FROM claims"
        " WHERE subject_id = $1"
        "   AND claim_type IN ('drug_target', 'drug_efficacy')",
        target_id,
    )
    drug_count = int(drug_val) if drug_val else 0
    return _clamp(drug_count / total)


async def _translational_readiness(target_id: str) -> float:
    """Dimension 6: does the target have related drugs or trial mentions?

    Returns 1.0 if both drugs and trial mentions exist,
    0.5 for partial (one or the other), 0.0 for none.
    """
    target_row = await fetchrow(
        "SELECT symbol FROM targets WHERE id = $1",
        target_id,
    )
    if not target_row:
        return 0.0
    symbol = target_row["symbol"]

    # Check for drug-related claims
    drug_claim_val = await fetchval(
        "SELECT COUNT(*) FROM claims"
        " WHERE subject_id = $1"
        "   AND claim_type IN ('drug_target', 'drug_efficacy')",
        target_id,
    )
    has_drug_claims = (int(drug_claim_val) if drug_claim_val else 0) > 0

    # Check if any trials mention this target (via interventions JSON or title)
    trial_val = await fetchval(
        "SELECT COUNT(*) FROM trials"
        " WHERE CAST(interventions AS TEXT) LIKE $1 OR title LIKE $2",
        f"%{symbol}%",
        f"%{symbol}%",
    )
    has_trials = (int(trial_val) if trial_val else 0) > 0

    if has_drug_claims and has_trials:
        return 1.0
    elif has_drug_claims or has_trials:
        return 0.5
    return 0.0


async def _network_centrality(target_id: str, *, max_edges: int) -> float:
    """Dimension 7: (outgoing + incoming graph_edges), normalized by max."""
    out_val = await fetchval(
        "SELECT COUNT(*) FROM graph_edges WHERE src_id = $1",
        target_id,
    )
    in_val = await fetchval(
        "SELECT COUNT(*) FROM graph_edges WHERE dst_id = $1",
        target_id,
    )
    degree = (int(out_val) if out_val else 0) + (int(in_val) if in_val else 0)
    return _clamp(degree / max_edges) if max_edges > 0 else 0.0


# Discovery targets — these get a novelty bonus because they represent
# unconventional, emerging research directions that traditional scoring
# would rank low due to fewer publications.
_DISCOVERY_TARGETS = {
    "LY96", "NEDD4L", "SPATA18", "LDHA", "CAST",
    "SULF1", "ANK3", "DNMT3B", "CD44", "CTNNA1", "GALNT6",
}


async def _novelty_discovery(target_id: str, *, max_claims: int) -> float:
    """Dimension 8: emerging/unconventional targets get a discovery bonus.

    Components:
    - Inverse evidence saturation: targets with FEWER claims get a novelty boost
      (well-known targets like SMN2 are saturated, less room for breakthrough)
    - Discovery bonus: targets from omics convergence analysis get a flat bonus
    - Quality-to-volume ratio: high avg confidence with few claims = hidden gem
    """
    target = await fetchrow(
        "SELECT symbol, target_type FROM targets WHERE id = $1",
        target_id,
    )
    if not target:
        return 0.0

    symbol = target["symbol"]

    # 1. Inverse saturation: fewer claims = more novel (0.0-0.5)
    claim_count_val = await fetchval(
        "SELECT COUNT(*) FROM claims WHERE subject_id = $1",
        target_id,
    )
    n_claims = int(claim_count_val) if claim_count_val else 0
    if max_claims > 0:
        saturation = n_claims / max_claims  # 0.0 = no claims, 1.0 = most claims
        inverse_sat = 1.0 - saturation      # flip it: 1.0 = novel, 0.0 = saturated
    else:
        inverse_sat = 0.5
    inverse_sat_component = inverse_sat * 0.4  # max 0.4

    # 2. Discovery target bonus (0.0 or 0.3)
    discovery_bonus = 0.3 if symbol in _DISCOVERY_TARGETS else 0.0

    # 3. Quality-to-volume ratio: high confidence + few claims = hidden gem (0.0-0.3)
    avg_conf_row = await fetchrow(
        "SELECT AVG(confidence) AS avg_conf FROM claims WHERE subject_id = $1",
        target_id,
    )
    avg_conf = float(avg_conf_row["avg_conf"]) if avg_conf_row and avg_conf_row["avg_conf"] is not None else 0.0
    # Hidden gem: high confidence but not many claims
    if n_claims > 0 and n_claims < max_claims * 0.2:  # fewer than 20% of max
        gem_score = avg_conf * 0.3  # high confidence with few claims
    else:
        gem_score = 0.0

    total = inverse_sat_component + discovery_bonus + gem_score
    return _clamp(total)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def score_target(target_id: str) -> dict[str, Any]:
    """Score a single target across all 7 dimensions.

    Returns a dict with dimension scores, composite_score, and metadata.
    """
    target = await fetchrow(
        "SELECT id, symbol, name, target_type FROM targets WHERE id = $1",
        target_id,
    )
    if not target:
        return {"error": f"Target {target_id} not found"}

    # Compute normalization ceilings
    max_claims = await _max_claims_per_target()
    max_sources = await _max_sources_per_target()
    max_edges = await _max_edges_per_target()

    # Score each dimension
    ev_vol = await _evidence_volume(target_id, max_claims=max_claims)
    ev_qual = await _evidence_quality(target_id)
    bio_coh = await _biological_coherence(target_id)
    src_ind = await _source_independence(target_id, max_sources=max_sources)
    interv = await _interventionability(target_id)
    trans_r = await _translational_readiness(target_id)
    net_cen = await _network_centrality(target_id, max_edges=max_edges)
    novelty = await _novelty_discovery(target_id, max_claims=max_claims)

    dimensions = {
        "evidence_volume": ev_vol,
        "evidence_quality": ev_qual,
        "biological_coherence": bio_coh,
        "source_independence": src_ind,
        "interventionability": interv,
        "translational_readiness": trans_r,
        "network_centrality": net_cen,
        "novelty_discovery": novelty,
    }

    # Weighted composite
    composite = sum(WEIGHTS[dim] * dimensions[dim] for dim in WEIGHTS)
    composite = _clamp(composite)

    claim_count_val = await fetchval(
        "SELECT COUNT(*) FROM claims WHERE subject_id = $1",
        target_id,
    )

    return {
        "target_id": str(target["id"]),
        "symbol": target["symbol"],
        "name": target.get("name"),
        "target_type": target.get("target_type"),
        "dimensions": dimensions,
        "composite_score": composite,
        "weights": WEIGHTS,
        "metadata": {
            "claim_count": int(claim_count_val) if claim_count_val else 0,
        },
    }


async def score_all_targets() -> list[dict[str, Any]]:
    """Score all targets and return sorted by composite_score descending."""
    targets = await fetch("SELECT id FROM targets ORDER BY symbol")
    results: list[dict[str, Any]] = []

    # Pre-compute normalization ceilings once for the batch
    max_claims = await _max_claims_per_target()
    max_sources = await _max_sources_per_target()
    max_edges = await _max_edges_per_target()

    for t in targets:
        tid = str(t["id"])
        target = await fetchrow(
            "SELECT id, symbol, name, target_type FROM targets WHERE id = $1",
            tid,
        )
        if not target:
            continue

        ev_vol = await _evidence_volume(tid, max_claims=max_claims)
        ev_qual = await _evidence_quality(tid)
        bio_coh = await _biological_coherence(tid)
        src_ind = await _source_independence(tid, max_sources=max_sources)
        interv = await _interventionability(tid)
        trans_r = await _translational_readiness(tid)
        net_cen = await _network_centrality(tid, max_edges=max_edges)
        novelty = await _novelty_discovery(tid, max_claims=max_claims)

        dimensions = {
            "evidence_volume": ev_vol,
            "evidence_quality": ev_qual,
            "biological_coherence": bio_coh,
            "source_independence": src_ind,
            "interventionability": interv,
            "translational_readiness": trans_r,
            "network_centrality": net_cen,
            "novelty_discovery": novelty,
        }

        composite = _clamp(sum(WEIGHTS[d] * dimensions[d] for d in WEIGHTS))

        claim_count_val = await fetchval(
            "SELECT COUNT(*) FROM claims WHERE subject_id = $1",
            tid,
        )

        results.append({
            "target_id": str(target["id"]),
            "symbol": target["symbol"],
            "name": target.get("name"),
            "target_type": target.get("target_type"),
            "dimensions": dimensions,
            "composite_score": composite,
            "weights": WEIGHTS,
            "metadata": {
                "claim_count": int(claim_count_val) if claim_count_val else 0,
            },
        })

    results.sort(key=lambda x: x["composite_score"], reverse=True)

    # Persist scores to target_scores table
    await _persist_scores(results)

    logger.info(
        "Scored %d targets. Top: %s (%.4f), Bottom: %s (%.4f)",
        len(results),
        results[0]["symbol"] if results else "N/A",
        results[0]["composite_score"] if results else 0,
        results[-1]["symbol"] if results else "N/A",
        results[-1]["composite_score"] if results else 0,
    )
    return results


async def _ensure_scores_table():
    """Create target_scores table if it doesn't exist."""
    await execute("""
        CREATE TABLE IF NOT EXISTS target_scores (
            id TEXT PRIMARY KEY,
            target_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            composite_score REAL NOT NULL,
            dimensions TEXT NOT NULL,
            claim_count INTEGER DEFAULT 0,
            scored_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(target_id)
        )
    """)


async def _persist_scores(results: list[dict[str, Any]]):
    """Save computed scores to the database."""
    import hashlib
    await _ensure_scores_table()
    for r in results:
        score_id = hashlib.sha256(
            f"{r['target_id']}".encode()
        ).hexdigest()[:32]
        await execute(
            """INSERT INTO target_scores (id, target_id, symbol, composite_score, dimensions, claim_count, scored_at)
               VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
               ON CONFLICT(target_id) DO UPDATE
               SET composite_score = EXCLUDED.composite_score,
                   dimensions = EXCLUDED.dimensions,
                   claim_count = EXCLUDED.claim_count,
                   scored_at = CURRENT_TIMESTAMP""",
            score_id, r["target_id"], r["symbol"],
            r["composite_score"], json.dumps(r["dimensions"]),
            r["metadata"].get("claim_count", 0),
        )
    logger.info("Persisted scores for %d targets to target_scores table", len(results))


async def get_cached_scores() -> list[dict[str, Any]] | None:
    """Load scores from the database. Returns None if no scores stored."""
    await _ensure_scores_table()
    rows = await fetch(
        "SELECT target_id, symbol, composite_score, dimensions, claim_count, scored_at FROM target_scores ORDER BY composite_score DESC"
    )
    if not rows:
        return None
    results = []
    for r in rows:
        dims = json.loads(r["dimensions"]) if isinstance(r["dimensions"], str) else r["dimensions"]
        results.append({
            "target_id": r["target_id"],
            "symbol": r["symbol"],
            "dimensions": dims,
            "composite_score": r["composite_score"],
            "weights": WEIGHTS,
            "metadata": {"claim_count": r["claim_count"]},
            "scored_at": r["scored_at"],
        })
    return results


async def get_target_scorecard(target_id: str) -> dict[str, Any]:
    """Full scorecard with scores, claim breakdown, evidence summary, and ranking.

    Enriches the basic ``score_target`` output with:
    - claims: per-claim breakdown (type, predicate, confidence)
    - evidence_summary: distinct sources, avg p-value, methods used
    - rank: position among all scored targets
    - tier: priority tier label (high / medium / low / insufficient_data)
    """
    score_data = await score_target(target_id)
    if "error" in score_data:
        return score_data

    # -- Claim breakdown --
    claims_rows = await fetch(
        "SELECT id, claim_type, predicate, confidence, object_id, object_type"
        " FROM claims WHERE subject_id = $1 ORDER BY confidence DESC",
        target_id,
    )
    claims_summary = [
        {
            "claim_id": str(c["id"]),
            "claim_type": c.get("claim_type"),
            "predicate": c.get("predicate"),
            "confidence": float(c["confidence"])
            if c.get("confidence") is not None
            else 0.5,
            "object_id": c.get("object_id"),
            "object_type": c.get("object_type"),
        }
        for c in claims_rows[:50]  # cap for readability
    ]

    # -- Evidence summary --
    evidence_rows = await fetch(
        "SELECT e.source_id, e.method, e.p_value, e.sample_size,"
        " s.source_type, s.title"
        " FROM evidence e"
        " JOIN sources s ON e.source_id = s.id"
        " JOIN claims c ON e.claim_id = c.id"
        " WHERE c.subject_id = $1",
        target_id,
    )
    distinct_sources = len({str(e["source_id"]) for e in evidence_rows})
    methods_used = sorted(
        {e["method"] for e in evidence_rows if e.get("method")}
    )
    p_values = [
        float(e["p_value"])
        for e in evidence_rows
        if e.get("p_value") is not None
    ]
    avg_p = round(sum(p_values) / len(p_values), 4) if p_values else None

    evidence_summary = {
        "distinct_sources": distinct_sources,
        "total_evidence_rows": len(evidence_rows),
        "methods_used": methods_used,
        "avg_p_value": avg_p,
    }

    # -- Ranking among all targets --
    all_scores = await score_all_targets()
    rank = None
    for i, s in enumerate(all_scores, start=1):
        if s["target_id"] == target_id:
            rank = i
            break

    # -- Priority tier --
    composite = score_data["composite_score"]
    if composite >= 0.7:
        tier = "high_priority"
    elif composite >= 0.4:
        tier = "medium_priority"
    elif composite >= 0.2:
        tier = "low_priority"
    else:
        tier = "insufficient_data"

    score_data["claims"] = claims_summary
    score_data["evidence_summary"] = evidence_summary
    score_data["rank"] = rank
    score_data["total_targets"] = len(all_scores)
    score_data["tier"] = tier

    return score_data
