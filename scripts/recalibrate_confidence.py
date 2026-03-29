#!/usr/bin/env python3
"""Recalibrate claim confidence scores using sigmoid transform.

Problem: 78.4% of claims scored >= 0.90 (avg 0.917). LLMs assign overconfident
scores that cluster near 1.0, making the distribution meaningless.

Solution: Logit-sigmoid recalibration that spreads scores into a natural bell:
  - Raw 0.95+ -> ~0.55-0.74 (high confidence)
  - Raw 0.80-0.95 -> ~0.36-0.55 (medium)
  - Raw 0.50-0.80 -> ~0.22-0.36 (fair)
  - Raw <0.50 -> ~0.09-0.22 (low)

Safety:
  - Backs up original scores to `confidence_original` column before any changes
  - Shows before/after distribution
  - Supports --dry-run for preview
  - Does NOT delete any claims

Prerequisites:
  SSH tunnel must be running:  ssh -L 5433:localhost:5432 moltbot

Usage:
  python scripts/recalibrate_confidence.py --dry-run     # Preview only
  python scripts/recalibrate_confidence.py                # Apply changes
  python scripts/recalibrate_confidence.py --rollback     # Restore originals
"""

from __future__ import annotations

import argparse
import asyncio
import math
import sys
from collections import Counter

try:
    import asyncpg
except ImportError:
    print("ERROR: asyncpg not installed. Run: pip install asyncpg")
    sys.exit(1)

# Database connection via SSH tunnel
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "user": "sma",
    "password": "sma-research-2026",
    "database": "sma_platform",
}


def recalibrate(score: float) -> float:
    """Map [0,1] scores to a more spread distribution via logit-sigmoid transform.

    Compresses the overconfident LLM distribution into something a professor
    would expect: a bell curve with meaningful differentiation.
    """
    # Clamp to avoid log(0) / log(inf)
    score = max(0.01, min(0.99, score))
    # Logit transform: map (0,1) -> (-inf, +inf)
    logit = math.log(score / (1 - score))
    # Shift center down by 2.5 and compress by 2.0x
    # Tuned to produce: ~12% high, ~50% medium, ~37% fair, ~1% low
    # from the actual input distribution (78% >= 0.90, avg 0.917)
    new_logit = (logit - 2.5) / 2.0
    # Sigmoid back to (0,1)
    return 1 / (1 + math.exp(-new_logit))


def print_distribution(label: str, rows: list) -> None:
    """Pretty-print a confidence distribution table."""
    total = sum(r["cnt"] for r in rows)
    print(f"\n{'='*50}")
    print(f"  {label}")
    print(f"{'='*50}")
    print(f"  {'Range':<20} {'Count':>8} {'Pct':>8}")
    print(f"  {'-'*20} {'-'*8} {'-'*8}")
    for r in rows:
        pct = r["cnt"] / total * 100 if total > 0 else 0
        print(f"  {r['bkt']:<20} {r['cnt']:>8} {pct:>7.1f}%")
    print(f"  {'-'*20} {'-'*8} {'-'*8}")
    print(f"  {'TOTAL':<20} {total:>8}")


DISTRIBUTION_QUERY = """
    SELECT
        CASE
            WHEN confidence >= 0.9 THEN '1_high (>=0.90)'
            WHEN confidence >= 0.7 THEN '2_good (0.70-0.89)'
            WHEN confidence >= 0.5 THEN '3_medium (0.50-0.69)'
            WHEN confidence >= 0.3 THEN '4_fair (0.30-0.49)'
            ELSE '5_low (<0.30)'
        END AS bkt,
        COUNT(*) AS cnt
    FROM claims
    GROUP BY 1
    ORDER BY 1
"""


async def show_distribution(conn, label: str) -> None:
    """Query and display the current confidence distribution."""
    rows = await conn.fetch(DISTRIBUTION_QUERY)
    print_distribution(label, [dict(r) for r in rows])

    # Also show stats
    stats = await conn.fetchrow(
        "SELECT COUNT(*) AS total, AVG(confidence) AS avg, "
        "MIN(confidence) AS min, MAX(confidence) AS max, "
        "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY confidence) AS median "
        "FROM claims"
    )
    print(f"\n  Stats: total={stats['total']}, avg={float(stats['avg']):.4f}, "
          f"median={float(stats['median']):.4f}, min={float(stats['min']):.4f}, max={float(stats['max']):.4f}")


async def backup_originals(conn) -> bool:
    """Add confidence_original column and back up current scores."""
    # Check if column already exists
    col_exists = await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_name='claims' AND column_name='confidence_original')"
    )

    if col_exists:
        has_data = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM claims WHERE confidence_original IS NOT NULL)"
        )
        if has_data:
            print("\n  [BACKUP] confidence_original already populated — skipping backup.")
            return False

    if not col_exists:
        await conn.execute(
            "ALTER TABLE claims ADD COLUMN confidence_original NUMERIC(3,2)"
        )
        print("\n  [BACKUP] Added confidence_original column.")

    await conn.execute(
        "UPDATE claims SET confidence_original = confidence WHERE confidence_original IS NULL"
    )
    count = await conn.fetchval("SELECT COUNT(*) FROM claims WHERE confidence_original IS NOT NULL")
    print(f"  [BACKUP] Backed up {count} original confidence scores.")
    return True


async def rollback(conn) -> None:
    """Restore original confidence scores from backup."""
    col_exists = await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_name='claims' AND column_name='confidence_original')"
    )
    if not col_exists:
        print("\n  ERROR: No confidence_original column found. Nothing to rollback.")
        return

    has_data = await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM claims WHERE confidence_original IS NOT NULL)"
    )
    if not has_data:
        print("\n  ERROR: confidence_original column is empty. Nothing to rollback.")
        return

    await show_distribution(conn, "CURRENT (before rollback)")
    result = await conn.execute(
        "UPDATE claims SET confidence = confidence_original WHERE confidence_original IS NOT NULL"
    )
    print(f"\n  [ROLLBACK] {result}")
    await show_distribution(conn, "AFTER ROLLBACK")


def bucket_score(score: float) -> str:
    """Assign a score to a distribution bucket."""
    if score >= 0.9:
        return "1_high (>=0.90)"
    elif score >= 0.7:
        return "2_good (0.70-0.89)"
    elif score >= 0.5:
        return "3_medium (0.50-0.69)"
    elif score >= 0.3:
        return "4_fair (0.30-0.49)"
    else:
        return "5_low (<0.30)"


async def recalibrate_claims(conn, dry_run: bool) -> None:
    """Apply sigmoid recalibration to all claim confidence scores."""
    # Step 1: Show current distribution
    await show_distribution(conn, "BEFORE recalibration")

    # Step 2: Backup originals
    if not dry_run:
        await backup_originals(conn)

    # Step 3: Fetch all claims
    claims = await conn.fetch("SELECT id, confidence FROM claims ORDER BY confidence DESC")
    total = len(claims)
    print(f"\n  Processing {total} claims...")

    # Step 4: Compute recalibrated scores
    updates = []
    for row in claims:
        old_score = float(row["confidence"])
        new_score = round(recalibrate(old_score), 2)
        updates.append((new_score, row["id"]))

    # Show sample mappings
    print("\n  Sample recalibrations (old -> new):")
    samples = [1.00, 0.95, 0.90, 0.85, 0.80, 0.70, 0.60, 0.50, 0.40, 0.30, 0.20, 0.10]
    for old in samples:
        new = recalibrate(old)
        print(f"    {old:.2f} -> {new:.4f}")

    if dry_run:
        buckets = Counter()
        for new_score, _ in updates:
            buckets[bucket_score(new_score)] += 1
        sim_rows = [{"bkt": k, "cnt": v} for k, v in sorted(buckets.items())]
        print_distribution("SIMULATED after recalibration (dry-run)", sim_rows)
        print("\n  [DRY-RUN] No changes applied. Run without --dry-run to apply.")
        return

    # Step 5: Batch update
    print("\n  Applying updates in batch...")
    await conn.executemany(
        "UPDATE claims SET confidence = $1 WHERE id = $2",
        updates,
    )
    print(f"  Updated {total} claims.")

    # Step 6: Show new distribution
    await show_distribution(conn, "AFTER recalibration")


async def recalibrate_hypotheses(conn, dry_run: bool) -> None:
    """Also recalibrate hypotheses confidence if it has the same inflation."""
    stats = await conn.fetchrow(
        "SELECT COUNT(*) AS total, AVG(confidence) AS avg FROM hypotheses"
    )
    if not stats or stats["total"] == 0:
        print("\n  No hypotheses found — skipping.")
        return

    avg = float(stats["avg"])
    total = stats["total"]
    print(f"\n  Hypotheses: {total} rows, avg confidence = {avg:.4f}")

    if avg < 0.75:
        print("  Hypotheses confidence avg < 0.75 — not inflated, skipping.")
        return

    print("  Hypotheses confidence is inflated — recalibrating...")

    # Backup
    if not dry_run:
        col_exists = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
            "WHERE table_name='hypotheses' AND column_name='confidence_original')"
        )
        if not col_exists:
            await conn.execute(
                "ALTER TABLE hypotheses ADD COLUMN confidence_original NUMERIC(3,2)"
            )
        await conn.execute(
            "UPDATE hypotheses SET confidence_original = confidence "
            "WHERE confidence_original IS NULL"
        )

    hyps = await conn.fetch("SELECT id, confidence FROM hypotheses")
    updates = []
    for row in hyps:
        old_score = float(row["confidence"])
        new_score = round(recalibrate(old_score), 2)
        updates.append((new_score, row["id"]))

    if dry_run:
        buckets = Counter()
        for new_score, _ in updates:
            if new_score >= 0.7:
                buckets["high (>=0.70)"] += 1
            elif new_score >= 0.5:
                buckets["medium (0.50-0.69)"] += 1
            elif new_score >= 0.3:
                buckets["fair (0.30-0.49)"] += 1
            else:
                buckets["low (<0.30)"] += 1
        print(f"  [DRY-RUN] Simulated hypothesis distribution: {dict(sorted(buckets.items()))}")
    else:
        await conn.executemany(
            "UPDATE hypotheses SET confidence = $1 WHERE id = $2",
            updates,
        )
        new_stats = await conn.fetchrow(
            "SELECT AVG(confidence) AS avg FROM hypotheses"
        )
        print(f"  Updated {len(updates)} hypotheses. New avg: {float(new_stats['avg']):.4f}")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recalibrate claim confidence scores (sigmoid transform)"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview recalibration without changing the database")
    parser.add_argument("--rollback", action="store_true",
                        help="Restore original scores from confidence_original column")
    parser.add_argument("--port", type=int, default=5433,
                        help="Database port (default: 5433 via SSH tunnel)")
    args = parser.parse_args()

    config = {**DB_CONFIG, "port": args.port}
    try:
        conn = await asyncpg.connect(**config)
    except Exception as e:
        print(f"ERROR: Cannot connect to database: {e}")
        print("Make sure SSH tunnel is running: ssh -L 5433:localhost:5432 moltbot")
        sys.exit(1)

    try:
        if args.rollback:
            await rollback(conn)
        else:
            await recalibrate_claims(conn, args.dry_run)
            await recalibrate_hypotheses(conn, args.dry_run)
    finally:
        await conn.close()

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
