"""Extraction quality benchmarking for claim extraction pipeline.

Evaluates the quality of LLM-extracted claims by comparing against
human-reviewed gold-standard labels. Supports:

1. Gold standard creation: sample claims + source abstracts for review
2. Evaluation metrics: precision, recall estimate, F1, grouped by claim_type
3. Reproducibility testing: re-extract claims and compare overlap

Schema reference:
  benchmark_evaluations: id, claim_id, gold_label (correct/incorrect/partial), notes, evaluated_at
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime, timezone

from ..core.database import execute, fetch, fetchrow
from .claim_extractor import extract_claims_from_abstract

logger = logging.getLogger(__name__)


async def _ensure_table() -> None:
    """Create benchmark_evaluations table if it does not exist."""
    await execute("""
        CREATE TABLE IF NOT EXISTS benchmark_evaluations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            claim_id UUID REFERENCES claims(id),
            gold_label TEXT NOT NULL CHECK (gold_label IN ('correct', 'incorrect', 'partial')),
            notes TEXT,
            evaluated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )
    """)


async def build_gold_standard(sample_size: int = 50) -> dict:
    """Randomly sample claims with their source abstracts for manual review.

    Returns a list of claims paired with the source abstract they were
    extracted from, suitable for human evaluation. Excludes claims that
    have already been evaluated in the benchmark_evaluations table.

    Args:
        sample_size: Number of claims to sample (default 50).

    Returns:
        dict with 'sample_size', 'already_evaluated', and 'samples' list.
    """
    await _ensure_table()

    # Count already-evaluated claims
    eval_count_row = await fetchrow(
        "SELECT COUNT(DISTINCT claim_id) AS cnt FROM benchmark_evaluations"
    )
    already_evaluated = dict(eval_count_row)["cnt"] if eval_count_row else 0

    # Sample claims that have NOT yet been evaluated, joined with their source
    rows = await fetch(
        """
        SELECT
            c.id AS claim_id,
            c.claim_type,
            c.predicate,
            c.confidence,
            c.subject_type,
            c.metadata AS claim_metadata,
            s.id AS source_id,
            s.title AS source_title,
            s.abstract AS source_abstract,
            s.journal,
            s.pub_date,
            e.excerpt
        FROM claims c
        JOIN evidence e ON e.claim_id = c.id
        JOIN sources s ON e.source_id = s.id
        WHERE c.id NOT IN (SELECT claim_id FROM benchmark_evaluations WHERE claim_id IS NOT NULL)
          AND s.abstract IS NOT NULL
          AND length(s.abstract) > 50
        ORDER BY random()
        LIMIT $1
        """,
        sample_size,
    )

    samples = []
    for row in rows:
        r = dict(row)
        samples.append({
            "claim_id": str(r["claim_id"]),
            "claim_type": r["claim_type"],
            "predicate": r["predicate"],
            "confidence": float(r["confidence"]) if r["confidence"] is not None else None,
            "subject_type": r["subject_type"],
            "excerpt": r["excerpt"],
            "source_id": str(r["source_id"]),
            "source_title": r["source_title"],
            "source_abstract": r["source_abstract"],
            "journal": r["journal"],
            "pub_date": str(r["pub_date"]) if r["pub_date"] else None,
        })

    return {
        "sample_size": len(samples),
        "already_evaluated": already_evaluated,
        "total_claims_available": len(samples),
        "samples": samples,
    }


async def submit_evaluation(
    claim_id: str,
    gold_label: str,
    notes: str | None = None,
) -> dict:
    """Submit a single gold-standard evaluation for a claim.

    Args:
        claim_id: UUID of the claim being evaluated.
        gold_label: One of 'correct', 'incorrect', 'partial'.
        notes: Optional reviewer notes.

    Returns:
        dict with the created evaluation record.
    """
    await _ensure_table()

    if gold_label not in ("correct", "incorrect", "partial"):
        return {"error": f"Invalid gold_label: {gold_label}. Must be correct/incorrect/partial."}

    # Verify claim exists
    claim = await fetchrow("SELECT id FROM claims WHERE id = $1", claim_id)
    if not claim:
        return {"error": f"Claim {claim_id} not found"}

    row = await fetchrow(
        """
        INSERT INTO benchmark_evaluations (claim_id, gold_label, notes)
        VALUES ($1, $2, $3)
        RETURNING id, claim_id, gold_label, notes, evaluated_at
        """,
        claim_id,
        gold_label,
        notes,
    )

    if not row:
        return {"error": "Failed to insert evaluation"}

    r = dict(row)
    return {
        "id": str(r["id"]),
        "claim_id": str(r["claim_id"]),
        "gold_label": r["gold_label"],
        "notes": r["notes"],
        "evaluated_at": r["evaluated_at"].isoformat() if r["evaluated_at"] else None,
    }


async def evaluate_extraction() -> dict:
    """Compare claims against gold-standard labels and calculate metrics.

    Computes:
    - Precision: correct / (correct + incorrect)
    - Recall estimate: correct / (correct + partial) -- partial = missed detail
    - F1 score: harmonic mean of precision and recall estimate
    - Breakdown by claim_type

    Returns:
        dict with overall metrics and per-claim-type breakdown.
    """
    await _ensure_table()

    rows = await fetch(
        """
        SELECT
            be.gold_label,
            c.claim_type,
            c.confidence
        FROM benchmark_evaluations be
        JOIN claims c ON be.claim_id = c.id
        """
    )

    if not rows:
        return {
            "total_evaluated": 0,
            "message": "No evaluations found. Submit evaluations via POST /benchmark/evaluate first.",
        }

    # Overall counts
    total = len(rows)
    correct = 0
    incorrect = 0
    partial = 0

    # Per claim_type
    by_type: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "incorrect": 0, "partial": 0})
    confidence_by_label: dict[str, list[float]] = defaultdict(list)

    for row in rows:
        r = dict(row)
        label = r["gold_label"]
        claim_type = r["claim_type"] or "unknown"
        conf = float(r["confidence"]) if r["confidence"] is not None else 0.5

        if label == "correct":
            correct += 1
        elif label == "incorrect":
            incorrect += 1
        elif label == "partial":
            partial += 1

        by_type[claim_type][label] += 1
        confidence_by_label[label].append(conf)

    # Overall metrics
    precision = correct / (correct + incorrect) if (correct + incorrect) > 0 else 0.0
    recall_estimate = correct / (correct + partial) if (correct + partial) > 0 else 0.0
    f1 = (
        2 * precision * recall_estimate / (precision + recall_estimate)
        if (precision + recall_estimate) > 0
        else 0.0
    )

    # Per-type metrics
    type_breakdown = {}
    for claim_type, counts in sorted(by_type.items()):
        c = counts["correct"]
        i = counts["incorrect"]
        p = counts["partial"]
        t_total = c + i + p
        t_precision = c / (c + i) if (c + i) > 0 else 0.0
        t_recall = c / (c + p) if (c + p) > 0 else 0.0
        t_f1 = (
            2 * t_precision * t_recall / (t_precision + t_recall)
            if (t_precision + t_recall) > 0
            else 0.0
        )
        type_breakdown[claim_type] = {
            "total": t_total,
            "correct": c,
            "incorrect": i,
            "partial": p,
            "precision": round(t_precision, 4),
            "recall_estimate": round(t_recall, 4),
            "f1": round(t_f1, 4),
        }

    # Average confidence per label
    avg_confidence = {}
    for label, confs in confidence_by_label.items():
        avg_confidence[label] = round(sum(confs) / len(confs), 4) if confs else 0.0

    return {
        "total_evaluated": total,
        "counts": {
            "correct": correct,
            "incorrect": incorrect,
            "partial": partial,
        },
        "metrics": {
            "precision": round(precision, 4),
            "recall_estimate": round(recall_estimate, 4),
            "f1": round(f1, 4),
        },
        "avg_confidence_by_label": avg_confidence,
        "by_claim_type": type_breakdown,
    }


async def test_reproducibility(sample_size: int = 20) -> dict:
    """Test extraction reproducibility by re-extracting claims from source abstracts.

    Takes a random sample of sources that already have claims, re-runs
    extraction on their abstracts, and compares the new claims against
    existing claims to measure overlap/reproduction rate.

    Overlap is measured by fuzzy predicate matching: a new claim is
    considered a "match" if any existing claim from the same source has
    a predicate with >60% token overlap.

    Args:
        sample_size: Number of sources to re-extract (default 20).

    Returns:
        dict with reproduction_rate, per-source details, and summary stats.
    """
    # Find sources that have existing claims via evidence links
    source_rows = await fetch(
        """
        SELECT DISTINCT s.id, s.title, s.abstract, s.journal
        FROM sources s
        JOIN evidence e ON e.source_id = s.id
        JOIN claims c ON e.claim_id = c.id
        WHERE s.abstract IS NOT NULL AND length(s.abstract) > 50
        ORDER BY random()
        LIMIT $1
        """,
        sample_size,
    )

    if not source_rows:
        return {
            "sources_tested": 0,
            "message": "No sources with existing claims found for reproducibility testing.",
        }

    results = []
    total_existing = 0
    total_new = 0
    total_matched = 0

    for srow in source_rows:
        s = dict(srow)
        source_id = str(s["id"])

        # Get existing claims for this source
        existing_rows = await fetch(
            """
            SELECT c.predicate, c.claim_type
            FROM claims c
            JOIN evidence e ON e.claim_id = c.id
            WHERE e.source_id = $1
            """,
            s["id"],
        )
        existing_predicates = [dict(r)["predicate"] for r in existing_rows]
        existing_types = [dict(r)["claim_type"] for r in existing_rows]

        # Re-extract claims from the abstract
        new_claims = await extract_claims_from_abstract(
            source_id=source_id,
            title=s["title"] or "",
            abstract=s["abstract"],
            journal=s.get("journal"),
        )

        new_predicates = [c.get("predicate", "") for c in new_claims if c.get("predicate")]

        # Calculate overlap using token-level Jaccard similarity
        matched = 0
        for new_pred in new_predicates:
            new_tokens = set(new_pred.lower().split())
            best_overlap = 0.0
            for existing_pred in existing_predicates:
                existing_tokens = set(existing_pred.lower().split())
                if not new_tokens or not existing_tokens:
                    continue
                intersection = new_tokens & existing_tokens
                union = new_tokens | existing_tokens
                jaccard = len(intersection) / len(union) if union else 0.0
                best_overlap = max(best_overlap, jaccard)
            if best_overlap > 0.6:
                matched += 1

        n_existing = len(existing_predicates)
        n_new = len(new_predicates)
        reproduction_rate = matched / n_new if n_new > 0 else 0.0

        total_existing += n_existing
        total_new += n_new
        total_matched += matched

        results.append({
            "source_id": source_id,
            "source_title": (s["title"] or "")[:100],
            "existing_claims": n_existing,
            "new_claims": n_new,
            "matched": matched,
            "reproduction_rate": round(reproduction_rate, 4),
        })

    overall_rate = total_matched / total_new if total_new > 0 else 0.0

    return {
        "sources_tested": len(results),
        "total_existing_claims": total_existing,
        "total_new_claims": total_new,
        "total_matched": total_matched,
        "overall_reproduction_rate": round(overall_rate, 4),
        "interpretation": _interpret_reproduction_rate(overall_rate),
        "per_source": results,
    }


def _interpret_reproduction_rate(rate: float) -> str:
    """Human-readable interpretation of the reproduction rate."""
    if rate >= 0.8:
        return "Excellent reproducibility: extraction is highly consistent across runs."
    elif rate >= 0.6:
        return "Good reproducibility: most claims are reproduced, minor variations expected from LLM stochasticity."
    elif rate >= 0.4:
        return "Moderate reproducibility: significant variation between runs. Consider lowering temperature or improving prompts."
    else:
        return "Low reproducibility: extraction varies substantially between runs. Prompt engineering or model tuning recommended."
