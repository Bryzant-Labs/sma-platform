"""Automated Claim Quality Benchmark — Track 1 Scientific Credibility.

Evaluates claim extraction quality without manual labeling by using
multiple automated signals:

1. Specificity — word count, named entities (genes, measurements)
2. Source agreement — claims replicated across multiple papers
3. Type consistency — claim_type matches predicate keywords
4. Confidence calibration — confidence vs evidence strength signals
5. Evidence completeness — excerpt, method, p-value, effect size present

Each dimension scores 0-1; composite = weighted average.
"""

from __future__ import annotations

import logging
import re
import statistics
from typing import Any

from ..core.database import fetch

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def evaluate_claim_quality(limit: int = 100) -> dict[str, Any]:
    """Auto-evaluate quality of extracted claims using multiple signals.

    Samples up to `limit` claims, scores each on 6 quality dimensions,
    and returns aggregate statistics plus the worst-scoring samples.

    Args:
        limit: Maximum number of claims to sample.

    Returns:
        dict with distribution, averages, common issues, and sample results.
    """
    claims = await fetch("""
        SELECT c.id, c.claim_number, c.claim_type, c.predicate, c.confidence,
               c.subject_id, c.subject_type, c.object_id, c.object_type,
               c.value,
               s.title AS source_title, s.external_id AS pmid, s.journal,
               e.excerpt, e.method, e.p_value, e.effect_size, e.sample_size
        FROM claims c
        JOIN evidence e ON e.claim_id = c.id
        JOIN sources s ON e.source_id = s.id
        ORDER BY RANDOM()
        LIMIT $1
    """, limit)

    if not claims:
        return {"error": "No claims with evidence found to evaluate", "total_evaluated": 0}

    # Pre-compute replication counts (how many distinct sources back each claim)
    replication_map = await _build_replication_map()

    results: list[dict] = []
    quality_scores: list[float] = []
    dimension_scores: dict[str, list[float]] = {
        "specificity": [], "entities": [], "type_consistency": [],
        "evidence_strength": [], "source_attribution": [], "replication": [],
    }

    for row in claims:
        c = dict(row)
        score = _score_claim(c, replication_map)
        quality_scores.append(score["quality_score"])

        for dim, val in score["dimensions"].items():
            dimension_scores.setdefault(dim, []).append(val)

        results.append({
            "claim_number": c.get("claim_number"),
            "claim_type": c.get("claim_type"),
            "predicate": (c.get("predicate") or "")[:120],
            "quality_score": score["quality_score"],
            "dimensions": score["dimensions"],
            "issues": score["issues"],
        })

    avg = statistics.mean(quality_scores)
    median = statistics.median(quality_scores)
    stdev = statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0.0

    high_quality = sum(1 for s in quality_scores if s >= 0.7)
    medium = sum(1 for s in quality_scores if 0.4 <= s < 0.7)
    low = sum(1 for s in quality_scores if s < 0.4)
    n = len(results)

    # Per-dimension averages
    dim_averages = {
        dim: round(statistics.mean(vals), 3)
        for dim, vals in dimension_scores.items()
        if vals
    }

    return {
        "total_evaluated": n,
        "average_quality": round(avg, 3),
        "median_quality": round(median, 3),
        "stdev": round(stdev, 3),
        "high_quality_pct": round(high_quality / n * 100, 1),
        "medium_quality_pct": round(medium / n * 100, 1),
        "low_quality_pct": round(low / n * 100, 1),
        "distribution": {"high": high_quality, "medium": medium, "low": low},
        "dimension_averages": dim_averages,
        "common_issues": _summarize_issues(results),
        "worst_claims": sorted(results, key=lambda x: x["quality_score"])[:10],
        "best_claims": sorted(results, key=lambda x: x["quality_score"], reverse=True)[:5],
        "interpretation": _interpret_quality(avg),
    }


async def claim_quality_by_type(limit: int = 500) -> dict[str, Any]:
    """Break down claim quality scores by claim_type.

    Returns per-type average quality, count, and top issues.
    """
    claims = await fetch("""
        SELECT c.id, c.claim_number, c.claim_type, c.predicate, c.confidence,
               c.subject_id, c.subject_type, c.object_id, c.object_type,
               c.value,
               s.title AS source_title, s.external_id AS pmid, s.journal,
               e.excerpt, e.method, e.p_value, e.effect_size, e.sample_size
        FROM claims c
        JOIN evidence e ON e.claim_id = c.id
        JOIN sources s ON e.source_id = s.id
        ORDER BY RANDOM()
        LIMIT $1
    """, limit)

    if not claims:
        return {"error": "No claims found", "types": {}}

    replication_map = await _build_replication_map()

    by_type: dict[str, list[dict]] = {}
    for row in claims:
        c = dict(row)
        score = _score_claim(c, replication_map)
        ct = c.get("claim_type") or "unknown"
        by_type.setdefault(ct, []).append(score)

    type_results = {}
    for ct, scores in sorted(by_type.items()):
        qs = [s["quality_score"] for s in scores]
        issues_flat: list[str] = []
        for s in scores:
            issues_flat.extend(s["issues"])
        issue_counts: dict[str, int] = {}
        for iss in issues_flat:
            issue_counts[iss] = issue_counts.get(iss, 0) + 1
        top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        type_results[ct] = {
            "count": len(qs),
            "average_quality": round(statistics.mean(qs), 3),
            "min": round(min(qs), 3),
            "max": round(max(qs), 3),
            "top_issues": [{"issue": i, "count": c} for i, c in top_issues],
        }

    return {"total_evaluated": len(claims), "types": type_results}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _build_replication_map() -> dict[str, int]:
    """Count distinct sources per claim for replication scoring.

    Returns a mapping of claim_id (str) -> number of distinct sources.
    """
    rows = await fetch("""
        SELECT claim_id::text, COUNT(DISTINCT source_id) AS src_count
        FROM evidence
        GROUP BY claim_id
    """)
    return {str(r["claim_id"]): r["src_count"] for r in rows}


def _score_claim(claim: dict, replication_map: dict[str, int]) -> dict:
    """Score a single claim on 6 quality dimensions.

    Dimensions:
        specificity     — predicate length (word count) vs ideal range
        entities        — presence of gene names, measurements, quantitative data
        type_consistency — claim_type keywords match the predicate text
        evidence_strength — excerpt, method, p_value, effect_size present
        source_attribution — PMID + journal present
        replication     — claim backed by multiple sources

    Returns dict with quality_score, dimensions, and issues list.
    """
    issues: list[str] = []
    dimensions: dict[str, float] = {}
    predicate = claim.get("predicate") or ""

    # --- 1. Specificity (word count) ---
    word_count = len(predicate.split())
    if word_count < 5:
        dimensions["specificity"] = 0.2
        issues.append("too_short")
    elif word_count < 10:
        dimensions["specificity"] = 0.5
    elif word_count <= 35:
        dimensions["specificity"] = 0.9
    else:
        # Very long predicates may be unfocused or copy-pasted abstracts
        dimensions["specificity"] = 0.6
        issues.append("possibly_unfocused")

    # --- 2. Named entities (genes, drugs, measurements) ---
    has_gene = bool(re.search(r'\b[A-Z][A-Z0-9]{2,}\b', predicate))
    has_number = bool(re.search(r'\d+\.?\d*\s*(%|mg|μM|nM|µM|fold|kDa|ng|ml|mL|mm|cm)', predicate))
    has_pvalue = bool(re.search(r'p\s*[<>=]\s*0\.\d', predicate, re.IGNORECASE))
    entity_signals = sum([has_gene, has_number, has_pvalue])
    if entity_signals >= 2:
        dimensions["entities"] = 1.0
    elif entity_signals == 1:
        dimensions["entities"] = 0.7
    else:
        dimensions["entities"] = 0.3
        issues.append("no_specific_entities")

    # --- 3. Type consistency ---
    claim_type = claim.get("claim_type") or "other"
    type_keywords: dict[str, list[str]] = {
        "gene_expression": ["express", "upregulat", "downregulat", "transcri", "mRNA", "RNA", "level"],
        "protein_interaction": ["interact", "bind", "complex", "associat", "phosphorylat", "co-locali"],
        "drug_efficacy": ["treat", "efficac", "improv", "reduc", "inhibit", "therapeutic", "dose", "respon"],
        "drug_target": ["target", "inhibit", "agonist", "antagonist", "modulat", "bind"],
        "splicing_event": ["splic", "exon", "intron", "inclusion", "skipping", "ISS", "ESE"],
        "biomarker": ["biomarker", "correlat", "predict", "marker", "indicator", "diagnos"],
        "neuroprotection": ["neuroprotect", "surviv", "rescue", "preserv", "protect", "apoptosis"],
        "motor_function": ["motor", "function", "CHOP", "HFMSE", "RULM", "ambulat", "strength"],
        "survival": ["surviv", "mortal", "lifespan", "median age", "event-free"],
        "safety": ["adverse", "safety", "tolerab", "side effect", "toxicity", "injection site"],
        "pathway_membership": ["pathway", "signal", "cascade", "downstream", "upstream", "activat"],
    }
    keywords = type_keywords.get(claim_type, [])
    if keywords:
        matches = sum(1 for kw in keywords if kw.lower() in predicate.lower())
        if matches >= 2:
            dimensions["type_consistency"] = 1.0
        elif matches == 1:
            dimensions["type_consistency"] = 0.7
        else:
            dimensions["type_consistency"] = 0.3
            issues.append("type_mismatch")
    else:
        dimensions["type_consistency"] = 0.5  # "other" type — no check possible

    # --- 4. Evidence strength (excerpt, method, statistical data) ---
    ev_signals = 0
    if claim.get("excerpt"):
        ev_signals += 1
    if claim.get("method"):
        ev_signals += 1
    if claim.get("p_value") is not None:
        ev_signals += 1
    if claim.get("effect_size") is not None:
        ev_signals += 1
    if claim.get("sample_size") is not None and claim["sample_size"] and claim["sample_size"] > 0:
        ev_signals += 1

    if ev_signals >= 4:
        dimensions["evidence_strength"] = 1.0
    elif ev_signals >= 3:
        dimensions["evidence_strength"] = 0.8
    elif ev_signals >= 2:
        dimensions["evidence_strength"] = 0.6
    elif ev_signals == 1:
        dimensions["evidence_strength"] = 0.4
    else:
        dimensions["evidence_strength"] = 0.1
        issues.append("weak_evidence")

    # --- 5. Source attribution ---
    source_score = 0.0
    if claim.get("pmid"):
        source_score += 0.5
    if claim.get("journal"):
        source_score += 0.3
    if claim.get("subject_type") and claim.get("object_type"):
        source_score += 0.2
    elif claim.get("subject_type") or claim.get("object_type"):
        source_score += 0.1
    else:
        issues.append("missing_entity_types")
    dimensions["source_attribution"] = min(1.0, source_score)
    if source_score < 0.3:
        issues.append("no_source_attribution")

    # --- 6. Replication (multi-source support) ---
    claim_id = str(claim.get("id", ""))
    src_count = replication_map.get(claim_id, 1)
    if src_count >= 3:
        dimensions["replication"] = 1.0
    elif src_count == 2:
        dimensions["replication"] = 0.7
    else:
        dimensions["replication"] = 0.4  # Single source is common, not penalized heavily

    # --- Composite (weighted) ---
    weights = {
        "specificity": 0.15,
        "entities": 0.15,
        "type_consistency": 0.20,
        "evidence_strength": 0.25,
        "source_attribution": 0.10,
        "replication": 0.15,
    }
    quality = sum(weights[d] * dimensions[d] for d in dimensions)

    return {
        "quality_score": round(quality, 3),
        "dimensions": {k: round(v, 3) for k, v in dimensions.items()},
        "issues": issues,
    }


def _summarize_issues(results: list[dict]) -> list[dict[str, Any]]:
    """Count and rank common issues across all evaluated claims."""
    issue_counts: dict[str, int] = {}
    for r in results:
        for issue in r.get("issues", []):
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
    total = len(results)
    ranked = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
    return [
        {"issue": iss, "count": cnt, "pct": round(cnt / total * 100, 1)}
        for iss, cnt in ranked
    ]


def _interpret_quality(avg: float) -> str:
    """Human-readable interpretation of the average quality score."""
    if avg >= 0.8:
        return (
            "Excellent: Claims are specific, well-typed, and backed by strong evidence. "
            "Extraction pipeline is performing at high quality."
        )
    elif avg >= 0.65:
        return (
            "Good: Most claims meet quality standards. Some may lack specificity "
            "or evidence detail. Suitable for hypothesis generation."
        )
    elif avg >= 0.5:
        return (
            "Moderate: Claims show quality gaps — common issues include vague predicates, "
            "type mismatches, or missing evidence metadata. Consider prompt tuning."
        )
    elif avg >= 0.35:
        return (
            "Below average: Significant quality issues detected. Review extraction prompts, "
            "consider filtering low-confidence claims, and verify claim_type assignment."
        )
    else:
        return (
            "Low: Most claims have quality problems. Extraction pipeline needs "
            "substantial revision — prompt engineering, better source selection, "
            "or manual review recommended."
        )
