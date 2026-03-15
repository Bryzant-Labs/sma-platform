#!/usr/bin/env python3
"""Batch re-score all claims for SMA relevance using Claude Haiku.

Sends batches of claims to the LLM asking: "Is this about SMA? Score 0-1."
Updates the confidence column in the claims table.

Usage:
    python scripts/rescore_claims.py                    # Re-score all claims
    python scripts/rescore_claims.py --dry-run          # Preview without updating
    python scripts/rescore_claims.py --batch-size 10    # Smaller batches
    python scripts/rescore_claims.py --min-conf 0.8     # Only re-score high-confidence claims (likely wrong)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

# Load .env from project root
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

import anthropic
import asyncpg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

MODEL = "claude-haiku-4-5-20251001"
BATCH_SIZE = 25

RELEVANCE_SYSTEM = (
    "You are an SMA (Spinal Muscular Atrophy) research relevance scorer. "
    "For each numbered claim, score its relevance to SMA research on a 0.0-1.0 scale:\n"
    "- 1.0 = Directly about SMA biology, treatment, or targets (SMN1, SMN2, motor neurons, approved therapies)\n"
    "- 0.8 = Strongly relevant — about SMA-related pathways, modifier genes (PLS3, NCALD, STMN2), or NMJ biology\n"
    "- 0.6 = Moderately relevant — about motor neuron disease generally, or targets with potential SMA crossover\n"
    "- 0.4 = Weakly relevant — tangentially related (general neuroscience, ubiquitin biology, muscle biology)\n"
    "- 0.2 = Barely relevant — mentions a keyword but is about a different disease entirely\n"
    "- 0.0 = Not relevant — wrong disease (e.g., CKD mentioning α-SMA, cancer mentioning SMA proteins)\n\n"
    "IMPORTANT: Papers about α-SMA (alpha smooth muscle actin) are NOT about Spinal Muscular Atrophy.\n"
    "Papers about CKD, renal fibrosis, liver fibrosis, or cancer that match 'SMA' are typically 0.0.\n\n"
    "Return ONLY a JSON array of objects: [{\"id\": 1, \"score\": 0.8, \"reason\": \"brief reason\"}, ...]\n"
    "No markdown fences. No explanation outside the JSON."
)


async def rescore_batch(
    client: anthropic.AsyncAnthropic,
    claims: list[dict],
) -> list[dict]:
    """Send a batch of claims to the LLM for relevance scoring."""
    lines = []
    for i, c in enumerate(claims, 1):
        pred = c["predicate"][:300]
        ct = c["claim_type"]
        lines.append(f"{i}. [{ct}] {pred}")

    user_prompt = "Score each claim for SMA relevance (0.0-1.0):\n\n" + "\n".join(lines)

    try:
        message = await client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=RELEVANCE_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
        )

        content = message.content[0].text.strip()
        if content.startswith("```"):
            content_lines = content.split("\n")
            content_lines = [ln for ln in content_lines if not ln.strip().startswith("```")]
            content = "\n".join(content_lines).strip()

        scores = json.loads(content)
        if not isinstance(scores, list):
            scores = [scores]
        return scores

    except (json.JSONDecodeError, KeyError) as e:
        logger.error("Failed to parse LLM response: %s", e)
        return []
    except anthropic.APIError as e:
        logger.error("Anthropic API error: %s", e)
        return []


async def main(
    dry_run: bool = False,
    batch_size: int = BATCH_SIZE,
    min_conf: float | None = None,
    max_conf: float | None = None,
    limit: int | None = None,
):
    db_url = os.environ.get("DATABASE_URL", "postgresql://sma:sma-research-2026@localhost:5432/sma_platform")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set")
        sys.exit(1)

    pool = await asyncpg.create_pool(db_url)
    client = anthropic.AsyncAnthropic(api_key=api_key)

    # Build query with optional confidence filters
    wheres = []
    params = []
    idx = 1

    if min_conf is not None:
        wheres.append(f"confidence >= ${idx}")
        params.append(min_conf)
        idx += 1
    if max_conf is not None:
        wheres.append(f"confidence <= ${idx}")
        params.append(max_conf)
        idx += 1

    where_clause = " WHERE " + " AND ".join(wheres) if wheres else ""
    limit_clause = f" LIMIT ${idx}" if limit else ""
    if limit:
        params.append(limit)

    query = f"SELECT id, claim_type, predicate, confidence FROM claims{where_clause} ORDER BY created_at DESC{limit_clause}"
    all_claims = await pool.fetch(query, *params)
    total = len(all_claims)
    logger.info("Found %d claims to re-score (dry_run=%s)", total, dry_run)

    updated = 0
    errors = 0
    start = time.time()

    for i in range(0, total, batch_size):
        batch = all_claims[i : i + batch_size]
        batch_dicts = [dict(r) for r in batch]

        scores = await rescore_batch(client, batch_dicts)

        if not scores:
            errors += len(batch)
            continue

        # Map scores back to claims by position
        score_map = {}
        for s in scores:
            pos = s.get("id")
            if pos is not None and isinstance(pos, int) and 1 <= pos <= len(batch):
                score_map[pos - 1] = s.get("score", 0.5)

        for j, claim in enumerate(batch):
            new_score = score_map.get(j)
            if new_score is None:
                errors += 1
                continue

            # Clamp to [0, 1]
            new_score = max(0.0, min(1.0, float(new_score)))

            if not dry_run:
                await pool.execute(
                    "UPDATE claims SET confidence = $1 WHERE id = $2",
                    new_score, claim["id"],
                )
            updated += 1

        elapsed = time.time() - start
        rate = updated / elapsed if elapsed > 0 else 0
        logger.info(
            "Progress: %d/%d (%.1f%%) — %d updated, %d errors — %.1f claims/sec",
            i + len(batch), total, (i + len(batch)) / total * 100,
            updated, errors, rate,
        )

        # Rate limit: ~0.5s between batches
        await asyncio.sleep(0.5)

    elapsed = time.time() - start
    logger.info(
        "Done: %d/%d claims re-scored in %.1fs (%.1f claims/sec). Errors: %d",
        updated, total, elapsed, updated / max(elapsed, 0.1), errors,
    )

    # Show new distribution
    if not dry_run:
        rows = await pool.fetch("""
            SELECT
                CASE
                    WHEN confidence >= 0.9 THEN 'A_0.9-1.0'
                    WHEN confidence >= 0.7 THEN 'B_0.7-0.89'
                    WHEN confidence >= 0.4 THEN 'C_0.4-0.69'
                    WHEN confidence >= 0.7 THEN 'D_0.2-0.39'
                    ELSE 'E_0.0-0.19'
                END AS bkt,
                count(*) AS cnt
            FROM claims GROUP BY 1 ORDER BY 1
        """)
        logger.info("New confidence distribution:")
        for r in rows:
            logger.info("  %s: %d", r["bkt"], r["cnt"])

    await pool.close()

    return {"updated": updated, "errors": errors, "total": total}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Re-score claims for SMA relevance")
    parser.add_argument("--dry-run", action="store_true", help="Preview without updating DB")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help=f"Claims per LLM call (default {BATCH_SIZE})")
    parser.add_argument("--min-conf", type=float, default=None, help="Only re-score claims with confidence >= this")
    parser.add_argument("--max-conf", type=float, default=None, help="Only re-score claims with confidence <= this")
    parser.add_argument("--limit", type=int, default=None, help="Max claims to process")
    args = parser.parse_args()

    asyncio.run(main(
        dry_run=args.dry_run,
        batch_size=args.batch_size,
        min_conf=args.min_conf,
        max_conf=args.max_conf,
        limit=args.limit,
    ))
