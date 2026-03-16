"""Multi-criteria target prioritization engine.

Ranks all targets by composite score across 5 weighted dimensions:

1. Evidence Convergence (30%)  -- claim count * avg confidence * source diversity
2. Biological Plausibility (20%) -- breadth of evidence across claim types
3. Interventionability (20%)   -- drug claims, known drugs, docking results, screening hits
4. Network Centrality (15%)    -- graph_edges degree (more connected = more central)
5. Novelty (15%)               -- fraction of claims from the last 2 years

Distinct from the existing prioritizer.py (8-dimension Phase 2 scoring):
this module focuses on a streamlined 5-dimension ranking optimized for
therapeutic decision-making, with explicit time-aware novelty scoring
and richer interventionability signals (drugs table, docking, screening).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from ..core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dimension weights (must sum to 1.0)
# ---------------------------------------------------------------------------

WEIGHTS: dict[str, float] = {
    "evidence_convergence": 0.30,
    "biological_plausibility": 0.20,
    "interventionability": 0.20,
    "network_centrality": 0.15,
    "novelty": 0.15,
}

# Claim types that indicate biological mechanism breadth
_MECHANISM_TYPES = {
    "protein_interaction",
    "gene_expression",
    "pathway_membership",
}

# Claim types indicating drug-relevant evidence
_DRUG_TYPES = {
    "drug_target",
    "drug_efficacy",
}

# Total number of distinct claim_type values in the schema
_TOTAL_CLAIM_TYPES = 12

# Novelty window: claims from the last 2 years count as recent
_NOVELTY_YEARS = 2


def _clamp(value: float) -> float:
    """Clamp to [0.0, 1.0] and round to 4 decimals."""
    return round(max(0.0, min(1.0, value)), 4)


# ---------------------------------------------------------------------------
# Batch normalization ceilings (computed once per ranking run)
# ---------------------------------------------------------------------------


async def _normalization_ceilings() -> dict[str, float]:
    """Compute max values across all targets for normalization."""
    max_claims_row = await fetchrow(
        "SELECT MAX(cnt) AS mx FROM ("
        "  SELECT COUNT(*) AS cnt FROM claims"
        "  WHERE subject_id IS NOT NULL GROUP BY subject_id"
        ") sub"
    )
    max_claims = float(max_claims_row["mx"]) if max_claims_row and max_claims_row["mx"] else 1.0

    max_sources_row = await fetchrow(
        "SELECT MAX(cnt) AS mx FROM ("
        "  SELECT COUNT(DISTINCT s.source_type || ':' || COALESCE(s.journal, '')) AS cnt"
        "  FROM claims c"
        "  JOIN evidence e ON e.claim_id = c.id"
        "  JOIN sources s ON e.source_id = s.id"
        "  WHERE c.subject_id IS NOT NULL"
        "  GROUP BY c.subject_id"
        ") sub"
    )
    max_sources = float(max_sources_row["mx"]) if max_sources_row and max_sources_row["mx"] else 1.0

    max_edges_row = await fetchrow(
        "SELECT MAX(cnt) AS mx FROM ("
        "  SELECT target_id, SUM(cnt) AS cnt FROM ("
        "    SELECT src_id AS target_id, COUNT(*) AS cnt"
        "    FROM graph_edges GROUP BY src_id"
        "    UNION ALL"
        "    SELECT dst_id AS target_id, COUNT(*) AS cnt"
        "    FROM graph_edges GROUP BY dst_id"
        "  ) sub GROUP BY target_id"
        ") sub2"
    )
    max_edges = float(max_edges_row["mx"]) if max_edges_row and max_edges_row["mx"] else 1.0

    return {
        "max_claims": max_claims,
        "max_sources": max_sources,
        "max_edges": max_edges,
    }


# ---------------------------------------------------------------------------
# Per-dimension scoring functions
# ---------------------------------------------------------------------------


async def _score_evidence_convergence(
    target_id: str, *, max_claims: float, max_sources: float
) -> tuple[float, dict[str, Any]]:
    """Dimension 1: claim count * avg confidence * source diversity, normalized 0-1.

    Components:
    - volume: claim count / max_claims
    - quality: average confidence across claims
    - diversity: distinct source types+journals / max_sources

    Final = volume * quality * diversity, then re-normalized against a
    theoretical max of 1.0 (since each component is 0-1, the product
    already sits in [0, 1]).
    """
    claim_count_val = await fetchval(
        "SELECT COUNT(*) FROM claims WHERE subject_id = $1",
        target_id,
    )
    claim_count = int(claim_count_val) if claim_count_val else 0

    avg_conf_row = await fetchrow(
        "SELECT AVG(confidence) AS avg_conf FROM claims WHERE subject_id = $1",
        target_id,
    )
    avg_conf = float(avg_conf_row["avg_conf"]) if avg_conf_row and avg_conf_row["avg_conf"] is not None else 0.0

    source_div_val = await fetchval(
        "SELECT COUNT(DISTINCT s.source_type || ':' || COALESCE(s.journal, ''))"
        " FROM claims c"
        " JOIN evidence e ON e.claim_id = c.id"
        " JOIN sources s ON e.source_id = s.id"
        " WHERE c.subject_id = $1",
        target_id,
    )
    source_diversity = int(source_div_val) if source_div_val else 0

    volume_norm = claim_count / max_claims if max_claims > 0 else 0.0
    diversity_norm = source_diversity / max_sources if max_sources > 0 else 0.0

    # Geometric-mean-like composite: reward balance across all three
    raw = volume_norm * avg_conf * diversity_norm
    # Cube root to avoid overly punishing targets weak in one area
    score = _clamp(raw ** (1.0 / 3.0)) if raw > 0 else 0.0

    detail = {
        "claim_count": claim_count,
        "avg_confidence": round(avg_conf, 4),
        "source_diversity_count": source_diversity,
        "volume_normalized": round(volume_norm, 4),
        "diversity_normalized": round(diversity_norm, 4),
    }
    return score, detail


async def _score_biological_plausibility(target_id: str) -> tuple[float, dict[str, Any]]:
    """Dimension 2: evidence breadth across claim types.

    Checks for:
    - protein_interaction claims
    - gene_expression claims
    - pathway_membership claims
    Plus scores by total breadth: distinct claim_types / 12.

    Score = 0.5 * (mechanism_coverage / 3) + 0.5 * (type_breadth / 12)
    """
    type_rows = await fetch(
        "SELECT DISTINCT claim_type FROM claims WHERE subject_id = $1",
        target_id,
    )
    present_types = {r["claim_type"] for r in type_rows}
    type_breadth = len(present_types)

    mechanism_hits = present_types & _MECHANISM_TYPES
    mechanism_coverage = len(mechanism_hits)

    score = _clamp(
        0.5 * (mechanism_coverage / len(_MECHANISM_TYPES))
        + 0.5 * (type_breadth / _TOTAL_CLAIM_TYPES)
    )

    detail = {
        "has_protein_interaction": "protein_interaction" in present_types,
        "has_gene_expression": "gene_expression" in present_types,
        "has_pathway_membership": "pathway_membership" in present_types,
        "mechanism_coverage": mechanism_coverage,
        "distinct_claim_types": type_breadth,
        "claim_types_present": sorted(present_types),
    }
    return score, detail


async def _score_interventionability(target_id: str) -> tuple[float, dict[str, Any]]:
    """Dimension 3: druggability signals.

    Components (each 0 or 1, then averaged):
    - has drug_target or drug_efficacy claims
    - has entries in drugs table targeting this target
    - has docking results (graph_edges with docking-related relations)
    - has molecule screening hits
    """
    # Drug claims
    drug_claim_val = await fetchval(
        "SELECT COUNT(*) FROM claims"
        " WHERE subject_id = $1 AND claim_type IN ('drug_target', 'drug_efficacy')",
        target_id,
    )
    has_drug_claims = (int(drug_claim_val) if drug_claim_val else 0) > 0

    # Known drugs in drugs table (targets column contains UUID array)
    known_drugs_val = await fetchval(
        "SELECT COUNT(*) FROM drugs WHERE CAST(targets AS TEXT) LIKE $1",
        f"%{target_id}%",
    )
    has_known_drugs = (int(known_drugs_val) if known_drugs_val else 0) > 0

    # Docking results (graph_edges with docking-related relations)
    docking_val = await fetchval(
        "SELECT COUNT(*) FROM graph_edges"
        " WHERE (src_id = $1 OR dst_id = $1)"
        "   AND (relation LIKE '%docking%' OR relation LIKE '%binding_affinity%')",
        target_id, target_id,
    )
    has_docking = (int(docking_val) if docking_val else 0) > 0

    # Screening hits (compound_bioactivity edges)
    screening_val = await fetchval(
        "SELECT COUNT(*) FROM graph_edges"
        " WHERE (src_id = $1 OR dst_id = $1)"
        "   AND relation LIKE 'compound_bioactivity%'",
        target_id, target_id,
    )
    has_screening = (int(screening_val) if screening_val else 0) > 0

    signals = [has_drug_claims, has_known_drugs, has_docking, has_screening]
    signal_count = sum(1 for s in signals if s)
    score = _clamp(signal_count / len(signals))

    detail = {
        "has_drug_claims": has_drug_claims,
        "has_known_drugs": has_known_drugs,
        "has_docking_results": has_docking,
        "has_screening_hits": has_screening,
        "signal_count": signal_count,
    }
    return score, detail


async def _score_network_centrality(
    target_id: str, *, max_edges: float
) -> tuple[float, dict[str, Any]]:
    """Dimension 4: graph_edges degree (in + out), normalized by max."""
    out_val = await fetchval(
        "SELECT COUNT(*) FROM graph_edges WHERE src_id = $1",
        target_id,
    )
    in_val = await fetchval(
        "SELECT COUNT(*) FROM graph_edges WHERE dst_id = $1",
        target_id,
    )
    out_degree = int(out_val) if out_val else 0
    in_degree = int(in_val) if in_val else 0
    total_degree = out_degree + in_degree

    score = _clamp(total_degree / max_edges) if max_edges > 0 else 0.0

    detail = {
        "out_degree": out_degree,
        "in_degree": in_degree,
        "total_degree": total_degree,
        "max_degree_in_db": int(max_edges),
    }
    return score, detail


async def _score_novelty(target_id: str) -> tuple[float, dict[str, Any]]:
    """Dimension 5: fraction of claims from the last 2 years.

    Uses evidence.source -> sources.pub_date to determine recency.
    Claims without a dated source are excluded from both numerator and denominator.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=_NOVELTY_YEARS * 365)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    total_dated_val = await fetchval(
        "SELECT COUNT(DISTINCT c.id)"
        " FROM claims c"
        " JOIN evidence e ON e.claim_id = c.id"
        " JOIN sources s ON e.source_id = s.id"
        " WHERE c.subject_id = $1 AND s.pub_date IS NOT NULL",
        target_id,
    )
    total_dated = int(total_dated_val) if total_dated_val else 0

    if total_dated == 0:
        return 0.0, {"total_dated_claims": 0, "recent_claims": 0, "cutoff_date": cutoff_str}

    recent_val = await fetchval(
        "SELECT COUNT(DISTINCT c.id)"
        " FROM claims c"
        " JOIN evidence e ON e.claim_id = c.id"
        " JOIN sources s ON e.source_id = s.id"
        " WHERE c.subject_id = $1 AND s.pub_date IS NOT NULL AND s.pub_date >= $2",
        target_id, cutoff_str,
    )
    recent = int(recent_val) if recent_val else 0

    score = _clamp(recent / total_dated)

    detail = {
        "total_dated_claims": total_dated,
        "recent_claims": recent,
        "recent_fraction": round(recent / total_dated, 4),
        "cutoff_date": cutoff_str,
    }
    return score, detail


# ---------------------------------------------------------------------------
# Core scoring function for a single target
# ---------------------------------------------------------------------------


async def _score_single_target(
    target_id: str,
    symbol: str,
    name: str | None,
    target_type: str | None,
    ceilings: dict[str, float],
) -> dict[str, Any]:
    """Score one target across all 5 dimensions and compute composite."""
    ev_score, ev_detail = await _score_evidence_convergence(
        target_id,
        max_claims=ceilings["max_claims"],
        max_sources=ceilings["max_sources"],
    )
    bio_score, bio_detail = await _score_biological_plausibility(target_id)
    int_score, int_detail = await _score_interventionability(target_id)
    net_score, net_detail = await _score_network_centrality(
        target_id, max_edges=ceilings["max_edges"]
    )
    nov_score, nov_detail = await _score_novelty(target_id)

    dimensions = {
        "evidence_convergence": ev_score,
        "biological_plausibility": bio_score,
        "interventionability": int_score,
        "network_centrality": net_score,
        "novelty": nov_score,
    }

    composite = _clamp(sum(WEIGHTS[d] * dimensions[d] for d in WEIGHTS))

    # Priority tier
    if composite >= 0.65:
        tier = "tier_1_high"
    elif composite >= 0.40:
        tier = "tier_2_medium"
    elif composite >= 0.20:
        tier = "tier_3_low"
    else:
        tier = "tier_4_insufficient"

    return {
        "target_id": target_id,
        "symbol": symbol,
        "name": name,
        "target_type": target_type,
        "composite_score": composite,
        "tier": tier,
        "dimensions": dimensions,
        "dimension_details": {
            "evidence_convergence": ev_detail,
            "biological_plausibility": bio_detail,
            "interventionability": int_detail,
            "network_centrality": net_detail,
            "novelty": nov_detail,
        },
        "weights": WEIGHTS,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def prioritize_targets() -> list[dict[str, Any]]:
    """Rank all targets by composite score across 5 dimensions.

    Returns a list sorted descending by composite_score, with per-dimension
    breakdown and detail objects for each target.
    """
    targets = await fetch(
        "SELECT id, symbol, name, target_type FROM targets ORDER BY symbol"
    )
    if not targets:
        return []

    ceilings = await _normalization_ceilings()
    results: list[dict[str, Any]] = []

    for t in targets:
        tid = str(t["id"])
        scored = await _score_single_target(
            tid,
            t["symbol"],
            t.get("name"),
            t.get("target_type"),
            ceilings,
        )
        results.append(scored)

    results.sort(key=lambda x: x["composite_score"], reverse=True)

    # Assign rank
    for i, r in enumerate(results, start=1):
        r["rank"] = i

    logger.info(
        "Prioritized %d targets. #1: %s (%.4f), #%d: %s (%.4f)",
        len(results),
        results[0]["symbol"] if results else "N/A",
        results[0]["composite_score"] if results else 0,
        len(results),
        results[-1]["symbol"] if results else "N/A",
        results[-1]["composite_score"] if results else 0,
    )
    return results


async def prioritize_single(symbol: str) -> dict[str, Any]:
    """Detailed prioritization for one target by gene symbol.

    Returns the full 5-dimension scorecard plus rank among all targets.
    """
    row = await fetchrow(
        "SELECT id, symbol, name, target_type FROM targets WHERE symbol = $1",
        symbol.upper(),
    )
    if not row:
        return {"error": f"Target '{symbol}' not found"}

    ceilings = await _normalization_ceilings()
    scored = await _score_single_target(
        str(row["id"]),
        row["symbol"],
        row.get("name"),
        row.get("target_type"),
        ceilings,
    )

    # Compute rank among all targets
    all_ranked = await prioritize_targets()
    for i, r in enumerate(all_ranked, start=1):
        if r["target_id"] == str(row["id"]):
            scored["rank"] = i
            scored["total_targets"] = len(all_ranked)
            break

    return scored


async def compare_targets(symbols: list[str]) -> dict[str, Any]:
    """Side-by-side comparison of multiple targets.

    Returns each target's full scorecard plus a comparative summary
    highlighting which target leads in each dimension.
    """
    if not symbols:
        return {"error": "No target symbols provided"}

    # Normalize
    symbols_upper = [s.strip().upper() for s in symbols if s.strip()]

    # Get full ranking for rank context
    all_ranked = await prioritize_targets()
    ranked_map: dict[str, dict[str, Any]] = {
        r["symbol"]: r for r in all_ranked
    }

    comparisons: list[dict[str, Any]] = []
    not_found: list[str] = []

    for sym in symbols_upper:
        if sym in ranked_map:
            comparisons.append(ranked_map[sym])
        else:
            not_found.append(sym)

    if not comparisons:
        return {"error": f"None of the targets found: {', '.join(symbols_upper)}"}

    # Sort compared targets by composite score
    comparisons.sort(key=lambda x: x["composite_score"], reverse=True)

    # Determine dimension leaders
    dimension_leaders: dict[str, dict[str, Any]] = {}
    for dim in WEIGHTS:
        best = max(comparisons, key=lambda x: x["dimensions"][dim])
        dimension_leaders[dim] = {
            "leader": best["symbol"],
            "score": best["dimensions"][dim],
        }

    # Compute deltas between top and rest
    if len(comparisons) >= 2:
        top = comparisons[0]
        gaps = {}
        for c in comparisons[1:]:
            delta = round(top["composite_score"] - c["composite_score"], 4)
            gaps[c["symbol"]] = {
                "composite_gap": delta,
                "dimension_gaps": {
                    dim: round(top["dimensions"][dim] - c["dimensions"][dim], 4)
                    for dim in WEIGHTS
                },
            }
    else:
        gaps = {}

    return {
        "compared_count": len(comparisons),
        "not_found": not_found,
        "targets": comparisons,
        "dimension_leaders": dimension_leaders,
        "gaps_from_top": gaps,
        "weights": WEIGHTS,
    }
