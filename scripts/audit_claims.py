#!/usr/bin/env python3
"""
Claim Deduplication Audit
=========================
Connects to the SMA platform database via SSH tunnel and audits claims for:
1. Exact duplicate claims (same claim_text)
2. Near-duplicate claims (90%+ similarity via SequenceMatcher)
3. Claims with invalid claim_type values
4. Claims without target links
5. Generates SQL to remove exact duplicates (keeps highest-scored)

Usage:
  1. Start SSH tunnel:  ssh -L 5433:localhost:5432 moltbot
  2. Run:               python scripts/audit_claims.py
"""

import asyncio
import sys
from difflib import SequenceMatcher
from collections import defaultdict

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

VALID_CLAIM_TYPES = {
    "gene_expression", "protein_interaction", "drug_efficacy",
    "splicing_event", "biomarker", "pathway", "mechanism",
    "clinical_outcome", "animal_model", "cell_biology",
    "genetic_variant", "therapeutic_target",
}


async def get_all_claims(pool):
    """Fetch all claims with relevant fields."""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, claim_text, claim_type, confidence, score,
                   source_id, target_id, created_at
            FROM claims
            ORDER BY id
        """)
    return rows


async def get_claims_without_targets(pool):
    """Find claims not linked to any target."""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, claim_text, claim_type, confidence
            FROM claims
            WHERE target_id IS NULL
            ORDER BY id
        """)
    return rows


async def run_audit():
    print("=" * 70)
    print("SMA Platform - Claim Deduplication Audit")
    print("=" * 70)

    try:
        pool = await asyncpg.create_pool(**DB_CONFIG, min_size=1, max_size=3)
    except Exception as e:
        print(f"\nERROR: Cannot connect to database: {e}")
        print("Make sure SSH tunnel is running: ssh -L 5433:localhost:5432 moltbot")
        sys.exit(1)

    print("\nFetching all claims...")
    claims = await get_all_claims(pool)
    total = len(claims)
    print(f"Total claims in database: {total}")

    # 1. Exact duplicates
    print("\n" + "-" * 70)
    print("1. EXACT DUPLICATE CLAIMS (same claim_text)")
    print("-" * 70)

    text_groups = defaultdict(list)
    for c in claims:
        text = (c["claim_text"] or "").strip().lower()
        if text:
            text_groups[text].append(c)

    exact_dupes = {k: v for k, v in text_groups.items() if len(v) > 1}
    total_exact_dupes = sum(len(v) - 1 for v in exact_dupes.values())

    print(f"Unique texts with duplicates: {len(exact_dupes)}")
    print(f"Total duplicate rows (removable): {total_exact_dupes}")
    if total > 0:
        print(f"Percentage duplicated: {total_exact_dupes / total * 100:.1f}%")

    # Top 20 most duplicated
    sorted_dupes = sorted(exact_dupes.items(), key=lambda x: -len(x[1]))[:20]
    print(f"\nTop {len(sorted_dupes)} most duplicated claim texts:")
    for i, (text, rows) in enumerate(sorted_dupes, 1):
        display_text = text[:100] + "..." if len(text) > 100 else text
        print(f"  {i:2d}. [{len(rows)}x] {display_text}")

    # 2. Near-duplicates (90%+ similarity)
    print("\n" + "-" * 70)
    print("2. NEAR-DUPLICATE CLAIMS (90%+ similarity)")
    print("-" * 70)

    unique_texts = list(text_groups.keys())
    sample_size = min(len(unique_texts), 2000)
    if sample_size < len(unique_texts):
        print(f"Sampling {sample_size} of {len(unique_texts)} unique texts for similarity check...")
    sample = unique_texts[:sample_size]

    near_dupes = []
    for i in range(len(sample)):
        for j in range(i + 1, len(sample)):
            ratio = SequenceMatcher(None, sample[i], sample[j]).ratio()
            if ratio >= 0.90:
                near_dupes.append((sample[i], sample[j], ratio))

    print(f"Near-duplicate pairs found: {len(near_dupes)}")
    for pair in near_dupes[:15]:
        t1 = pair[0][:60] + "..." if len(pair[0]) > 60 else pair[0]
        t2 = pair[1][:60] + "..." if len(pair[1]) > 60 else pair[1]
        print(f"  [{pair[2]:.1%}] \"{t1}\"")
        print(f"       vs \"{t2}\"")

    # 3. Invalid claim_type values
    print("\n" + "-" * 70)
    print("3. CLAIMS WITH INVALID claim_type VALUES")
    print("-" * 70)

    type_counts = defaultdict(int)
    invalid_type_claims = []
    for c in claims:
        ct = c["claim_type"] or "NULL"
        type_counts[ct] += 1
        if ct not in VALID_CLAIM_TYPES and ct != "NULL":
            invalid_type_claims.append(c)

    print("Claim type distribution:")
    for ct, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        marker = " <-- INVALID" if ct not in VALID_CLAIM_TYPES and ct != "NULL" else ""
        print(f"  {ct:30s} {count:6d}{marker}")

    if invalid_type_claims:
        print(f"\nTotal claims with invalid types: {len(invalid_type_claims)}")
    else:
        print("\nNo invalid claim_type values found.")

    # 4. Claims without target links
    print("\n" + "-" * 70)
    print("4. CLAIMS WITHOUT TARGET LINKS")
    print("-" * 70)

    orphan_claims = await get_claims_without_targets(pool)
    if total > 0:
        print(f"Claims without target_id: {len(orphan_claims)} ({len(orphan_claims) / total * 100:.1f}%)")
    if orphan_claims:
        type_breakdown = defaultdict(int)
        for c in orphan_claims:
            type_breakdown[c["claim_type"] or "NULL"] += 1
        print("  By type:")
        for ct, count in sorted(type_breakdown.items(), key=lambda x: -x[1]):
            print(f"    {ct:30s} {count:6d}")

    # 5. Generate deduplication SQL
    print("\n" + "-" * 70)
    print("5. DEDUPLICATION SQL (keeps highest-scored duplicate)")
    print("-" * 70)

    if total_exact_dupes > 0:
        sql_lines = [
            "-- Auto-generated claim deduplication SQL",
            "-- Generated by audit_claims.py",
            "-- Removes exact duplicate claims, keeping the row with the highest score",
            "-- REVIEW BEFORE EXECUTING",
            "",
            "BEGIN;",
            "",
            "-- Delete exact duplicates (keep highest score per claim_text)",
            "DELETE FROM claims",
            "WHERE id NOT IN (",
            "    SELECT DISTINCT ON (LOWER(TRIM(claim_text))) id",
            "    FROM claims",
            "    WHERE claim_text IS NOT NULL AND TRIM(claim_text) != ''",
            "    ORDER BY LOWER(TRIM(claim_text)), COALESCE(score, 0) DESC, id",
            ")",
            "AND claim_text IS NOT NULL",
            "AND TRIM(claim_text) != '';",
            "",
            "-- Verify count after dedup",
            "SELECT COUNT(*) AS remaining_claims FROM claims;",
            "",
            "-- COMMIT only after verifying the count looks correct",
            "-- COMMIT;",
            "-- If something looks wrong: ROLLBACK;",
        ]
        sql_content = "\n".join(sql_lines)
        print(f"\nGenerated SQL:")
        print(sql_content)

        sql_file = "scripts/dedup_claims.sql"
        with open(sql_file, "w") as f:
            f.write(sql_content + "\n")
        print(f"\nFile saved: {sql_file}")
        print(f"Estimated rows to remove: {total_exact_dupes}")
    else:
        print("No exact duplicates found - no SQL needed.")

    # Summary
    print("\n" + "=" * 70)
    print("AUDIT SUMMARY")
    print("=" * 70)
    print(f"  Total claims:              {total:,}")
    if total > 0:
        print(f"  Exact duplicates:          {total_exact_dupes:,} ({total_exact_dupes / total * 100:.1f}%)")
    print(f"  Near-duplicates (90%+):    {len(near_dupes):,} pairs (sampled {sample_size} texts)")
    print(f"  Invalid claim_types:       {len(invalid_type_claims):,}")
    print(f"  Claims without targets:    {len(orphan_claims):,}")
    print("=" * 70)

    await pool.close()


if __name__ == "__main__":
    asyncio.run(run_audit())
