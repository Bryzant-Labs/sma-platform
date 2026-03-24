#!/usr/bin/env python3
"""Relink orphaned or generically-linked claims to specific targets.

Scans claim text (predicate) for target symbols and known aliases,
then updates subject_id / object_id linkage where appropriate.

Usage:
    # Via SSH tunnel to moltbot (run locally):
    ssh -L 5432:localhost:5432 moltbot -N &
    DATABASE_URL=postgresql://sma:sma-research-2026@localhost:5432/sma_platform \
        python scripts/relink_claims_to_targets.py

    # Dry-run (no DB writes):
    DATABASE_URL=... python scripts/relink_claims_to_targets.py --dry-run

    # On moltbot directly:
    DATABASE_URL=postgresql://sma:sma-research-2026@localhost:5432/sma_platform \
        python scripts/relink_claims_to_targets.py
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# Load .env from project root
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

import asyncpg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# Known aliases for targets — symbol -> list of text patterns to search for.
# These supplement whatever is stored in the targets table.
# Patterns are case-insensitive and word-boundary matched.
EXTRA_ALIASES: dict[str, list[str]] = {
    "SMN1": ["SMN1", "survival motor neuron 1", "SMN-1"],
    "SMN2": ["SMN2", "survival motor neuron 2", "SMN-2", "exon 7"],
    "STMN2": ["STMN2", "stathmin-2", "stathmin 2", "SCG10"],
    "PLS3": ["PLS3", "plastin 3", "plastin-3", "T-plastin", "fimbrin"],
    "NCALD": ["NCALD", "neurocalcin delta", "neurocalcin-delta"],
    "UBA1": ["UBA1", "ubiquitin-activating enzyme", "UBE1"],
    "CORO1C": ["CORO1C", "coronin 1C", "coronin-1C"],
    "SMN_PROTEIN": ["SMN protein", "SMN complex", "snRNP assembly"],
    "MTOR_PATHWAY": ["mTOR", "rapamycin", "mTORC1", "mTORC2"],
    "NMJ_MATURATION": ["neuromuscular junction", "NMJ", "endplate"],
    "CFL2": ["CFL2", "cofilin-2", "cofilin 2"],
    "LIMK1": ["LIMK1", "LIMK-1", "LIM kinase 1", "LIM kinase"],
    "PFN1": ["PFN1", "profilin-1", "profilin 1"],
    "ACTG1": ["ACTG1", "gamma-actin", "actin gamma 1"],
    "ACTR2": ["ACTR2", "ARP2", "actin-related protein 2"],
    "ABI2": ["ABI2", "Abl interactor 2"],
    "CD44": ["CD44"],
    "SULF1": ["SULF1", "sulfatase 1"],
    "DNMT3B": ["DNMT3B", "DNA methyltransferase 3B"],
    "ANK3": ["ANK3", "ankyrin-G", "ankyrin G"],
    "NDRG1": ["NDRG1"],
    "ROCK1": ["ROCK1", "ROCK inhibitor", "Rho kinase", "Fasudil"],
    "ROCK2": ["ROCK2"],
}


def _build_pattern(aliases: list[str]) -> re.Pattern:
    """Build a compiled regex that matches any alias with word boundaries."""
    escaped = [re.escape(a) for a in aliases]
    return re.compile(r"\b(?:" + "|".join(escaped) + r")\b", re.IGNORECASE)


async def relink(dry_run: bool = False) -> dict[str, int]:
    """Main relinking logic.

    Returns:
        Dict of {target_symbol: relinked_count}
    """
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        logger.error("DATABASE_URL not set. See usage in docstring.")
        sys.exit(1)

    pool = await asyncpg.create_pool(dsn, min_size=2, max_size=5)

    # 1. Fetch all targets
    async with pool.acquire() as conn:
        targets = await conn.fetch(
            "SELECT id, symbol, name, identifiers, description FROM targets"
        )
    logger.info("Loaded %d targets from database", len(targets))

    # Build alias -> target_id mapping
    target_patterns: list[tuple[str, str, re.Pattern]] = []
    for t in targets:
        tid = str(t["id"])
        sym = t["symbol"]
        aliases = set()

        # From EXTRA_ALIASES
        if sym in EXTRA_ALIASES:
            aliases.update(EXTRA_ALIASES[sym])

        # Always include the symbol itself and name
        aliases.add(sym)
        if t["name"]:
            aliases.add(t["name"])

        if aliases:
            pattern = _build_pattern(list(aliases))
            target_patterns.append((tid, sym, pattern))

    logger.info("Built patterns for %d targets", len(target_patterns))

    # 2. Fetch claims with no subject_id (orphaned)
    async with pool.acquire() as conn:
        orphaned_claims = await conn.fetch(
            """SELECT id, predicate, claim_type, subject_id, subject_type
               FROM claims
               WHERE subject_id IS NULL
               ORDER BY created_at DESC"""
        )
    logger.info("Found %d orphaned claims (no subject_id)", len(orphaned_claims))

    # 3. Count current per-target linkage (before)
    async with pool.acquire() as conn:
        before_counts_raw = await conn.fetch(
            """SELECT t.symbol, COUNT(c.id) as cnt
               FROM targets t
               LEFT JOIN claims c ON c.subject_id = t.id
               GROUP BY t.symbol
               ORDER BY cnt DESC"""
        )
    before_counts = {r["symbol"]: r["cnt"] for r in before_counts_raw}

    # 4. Match and relink
    relinked: dict[str, int] = defaultdict(int)
    updates: list[tuple[str, str, str]] = []  # (claim_id, target_id, symbol)

    for claim in orphaned_claims:
        text = claim["predicate"] or ""
        if not text:
            continue

        best_match: tuple[str, str] | None = None
        best_pos = len(text)  # prefer earliest match

        for tid, sym, pattern in target_patterns:
            m = pattern.search(text)
            if m and m.start() < best_pos:
                best_match = (tid, sym)
                best_pos = m.start()

        if best_match:
            updates.append((str(claim["id"]), best_match[0], best_match[1]))
            relinked[best_match[1]] += 1

    logger.info("Matched %d claims to targets", len(updates))

    if dry_run:
        logger.info("DRY RUN — no database updates performed")
        for sym, count in sorted(relinked.items(), key=lambda x: -x[1]):
            logger.info("  Would relink %d claims to %s", count, sym)
    else:
        # 5. Batch update
        async with pool.acquire() as conn:
            async with conn.transaction():
                stmt = await conn.prepare(
                    """UPDATE claims
                       SET subject_id = $1::uuid, subject_type = 'target'
                       WHERE id = $2::uuid"""
                )
                for claim_id, target_id, sym in updates:
                    await stmt.fetchval(target_id, claim_id)

        logger.info("Updated %d claims in database", len(updates))

    # 6. Report
    async with pool.acquire() as conn:
        after_counts_raw = await conn.fetch(
            """SELECT t.symbol, COUNT(c.id) as cnt
               FROM targets t
               LEFT JOIN claims c ON c.subject_id = t.id
               GROUP BY t.symbol
               ORDER BY cnt DESC"""
        )
    after_counts = {r["symbol"]: r["cnt"] for r in after_counts_raw}

    print("\n" + "=" * 60)
    print("CLAIM-TARGET RELINKING REPORT")
    print("=" * 60)
    print(f"{'Target':<20} {'Before':>8} {'After':>8} {'Delta':>8}")
    print("-" * 60)
    all_symbols = sorted(set(list(before_counts.keys()) + list(after_counts.keys())))
    for sym in all_symbols:
        b = before_counts.get(sym, 0)
        a = after_counts.get(sym, 0)
        delta = a - b
        marker = f"+{delta}" if delta > 0 else str(delta) if delta < 0 else "0"
        print(f"{sym:<20} {b:>8} {a:>8} {marker:>8}")

    total_relinked = sum(relinked.values())
    remaining_orphans_count = len(orphaned_claims) - total_relinked
    print("-" * 60)
    print(f"Total relinked: {total_relinked}")
    print(f"Still orphaned:  {remaining_orphans_count}")
    print("=" * 60)

    await pool.close()
    return dict(relinked)


def main():
    parser = argparse.ArgumentParser(
        description="Relink orphaned claims to targets based on text matching"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without writing to database"
    )
    args = parser.parse_args()
    asyncio.run(relink(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
