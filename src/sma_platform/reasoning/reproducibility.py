"""Score Reproducibility Testing — Track 1 Scientific Credibility.

Verifies that convergence scores, predictions, and rankings are
deterministic and reproducible. Runs scoring twice and compares.
"""

from __future__ import annotations
import logging
from typing import Any
from ..core.database import fetch

logger = logging.getLogger(__name__)


async def test_convergence_reproducibility() -> dict[str, Any]:
    """Run convergence scoring twice and compare results."""
    from .convergence_engine import compute_all_convergence

    # Run 1
    run1_raw = await compute_all_convergence()
    run1 = run1_raw.get("results", [])

    # Run 2
    run2_raw = await compute_all_convergence()
    run2 = run2_raw.get("results", [])

    # Compare
    mismatches = []
    for r1, r2 in zip(run1, run2):
        key1 = r1.get("target", r1.get("target_key", ""))
        key2 = r2.get("target", r2.get("target_key", ""))
        score1 = r1.get("composite_score", 0)
        score2 = r2.get("composite_score", 0)

        if abs(float(score1) - float(score2)) > 0.001:
            mismatches.append({
                "target": key1,
                "run1_score": float(score1),
                "run2_score": float(score2),
                "delta": abs(float(score1) - float(score2)),
            })

    reproducible = len(mismatches) == 0

    return {
        "test": "convergence_reproducibility",
        "targets_tested": len(run1),
        "reproducible": reproducible,
        "mismatches": mismatches,
        "verdict": "PASS — identical results across runs" if reproducible
                   else f"FAIL — {len(mismatches)} targets differ between runs",
    }


async def test_ranking_stability() -> dict[str, Any]:
    """Verify target ranking order is stable across runs."""
    from .convergence_engine import compute_all_convergence

    run1_raw = await compute_all_convergence()
    run1 = run1_raw.get("results", [])

    run2_raw = await compute_all_convergence()
    run2 = run2_raw.get("results", [])

    def get_ranking(results):
        return [r.get("target", r.get("target_key", "")) for r in results]

    rank1 = get_ranking(run1)
    rank2 = get_ranking(run2)

    order_matches = rank1 == rank2

    # Find rank changes
    rank_changes = []
    for i, (t1, t2) in enumerate(zip(rank1, rank2)):
        if t1 != t2:
            rank_changes.append({"position": i + 1, "run1": t1, "run2": t2})

    return {
        "test": "ranking_stability",
        "targets_ranked": len(rank1),
        "order_stable": order_matches,
        "rank_changes": rank_changes,
        "verdict": "PASS — ranking order identical" if order_matches
                   else f"FAIL — {len(rank_changes)} positions differ",
    }


async def test_claim_count_consistency() -> dict[str, Any]:
    """Verify claim counts match between scoring and database."""
    rows = await fetch("""
        SELECT t.symbol, COUNT(c.id) as db_count
        FROM targets t
        LEFT JOIN claims c ON (c.subject_id = t.id OR c.object_id = t.id)
        GROUP BY t.symbol
        ORDER BY t.symbol
    """)

    from .convergence_engine import compute_all_convergence
    scores_raw = await compute_all_convergence()
    scores = scores_raw.get("results", [])

    score_counts = {}
    for s in scores:
        key = s.get("target", s.get("target_key", ""))
        score_counts[key] = s.get("claim_count", 0)

    inconsistencies = []
    for row in rows:
        sym = row["symbol"]
        db = row["db_count"]
        scored = score_counts.get(sym, -1)
        if scored >= 0 and abs(db - scored) > db * 0.1:  # >10% difference
            inconsistencies.append({
                "target": sym,
                "db_count": db,
                "scored_count": scored,
                "difference_pct": round(abs(db - scored) / max(db, 1) * 100, 1),
            })

    return {
        "test": "claim_count_consistency",
        "targets_checked": len(rows),
        "consistent": len(inconsistencies) == 0,
        "inconsistencies": inconsistencies,
        "verdict": "PASS — counts consistent" if not inconsistencies
                   else f"WARN — {len(inconsistencies)} targets have >10% count discrepancy",
    }


async def run_all_reproducibility_tests() -> dict[str, Any]:
    """Run all reproducibility tests and return comprehensive report."""
    tests = [
        await test_convergence_reproducibility(),
        await test_ranking_stability(),
        await test_claim_count_consistency(),
    ]

    all_pass = all(
        t.get("reproducible", t.get("order_stable", t.get("consistent", False)))
        for t in tests
    )

    return {
        "overall": "ALL PASS" if all_pass else "SOME FAILURES",
        "tests_run": len(tests),
        "tests_passed": sum(1 for t in tests if "PASS" in t.get("verdict", "")),
        "results": tests,
    }
