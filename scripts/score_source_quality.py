#!/usr/bin/env python3
"""Score source (publication) quality based on abstract content.

Assigns a composite quality_score (0.0-1.0) to each source based on:
  1. Sample size (extracted via regex from abstract)
  2. Model system (patient tissue > iPSC > animal > cell line > in silico)
  3. Journal tier (Nature/Cell/Science > field-specific > other)

No LLM required — uses keyword/regex matching only.

Usage:
    # Via SSH tunnel to moltbot:
    ssh -L 5432:localhost:5432 moltbot -N &
    DATABASE_URL=postgresql://sma:sma-research-2026@localhost:5432/sma_platform \
        python scripts/score_source_quality.py

    # Dry-run:
    DATABASE_URL=... python scripts/score_source_quality.py --dry-run

    # Add quality_score column first (if not exists):
    DATABASE_URL=... python scripts/score_source_quality.py --migrate
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import re
import sys
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

# ---------------------------------------------------------------------------
# Scoring constants
# ---------------------------------------------------------------------------

# Sample size thresholds
SAMPLE_SIZE_SCORES = [
    (20, 1.0),   # n > 20
    (5, 0.6),    # 5 <= n <= 20
    (1, 0.3),    # 1 <= n < 5
]
NO_SAMPLE_SIZE_SCORE = 0.5  # if we can't extract sample size

# Regex patterns for extracting sample size from abstracts
SAMPLE_SIZE_PATTERNS = [
    re.compile(r"\bn\s*=\s*(\d+)", re.IGNORECASE),
    re.compile(r"sample(?:\s+size)?\s+(?:of\s+)?(\d+)", re.IGNORECASE),
    re.compile(r"cohort\s+of\s+(\d+)", re.IGNORECASE),
    re.compile(r"(\d+)\s+(?:patients|subjects|participants|individuals|cases|controls)", re.IGNORECASE),
    re.compile(r"(\d+)\s+(?:mice|rats|animals|zebrafish|drosophila|worms)", re.IGNORECASE),
    re.compile(r"(\d+)\s+(?:samples|specimens|biopsies)", re.IGNORECASE),
    re.compile(r"enrolled\s+(\d+)", re.IGNORECASE),
]

# Model system keywords -> score (first match wins)
MODEL_SYSTEM_RULES: list[tuple[re.Pattern, float]] = [
    (re.compile(r"\b(?:patient|human)\s+(?:tissue|biopsy|sample|spinal\s+cord|brain)", re.IGNORECASE), 1.0),
    (re.compile(r"\b(?:patient-derived|human\s+post-?mortem|autopsy)", re.IGNORECASE), 1.0),
    (re.compile(r"\b(?:clinical\s+trial|clinical\s+study|randomized)", re.IGNORECASE), 1.0),
    (re.compile(r"\b(?:meta-?analysis|systematic\s+review)", re.IGNORECASE), 0.9),
    (re.compile(r"\b(?:iPSC|iPS\s+cell|induced\s+pluripotent)", re.IGNORECASE), 0.8),
    (re.compile(r"\b(?:organoid|cerebral\s+organoid|motor\s+neuron\s+organoid)", re.IGNORECASE), 0.8),
    (re.compile(r"\b(?:mouse|mice|murine|rat|rodent|transgenic\s+mouse|knockout\s+mouse)", re.IGNORECASE), 0.7),
    (re.compile(r"\b(?:zebrafish|drosophila|C\.\s*elegans|worm|fly\s+model|fish\s+model)", re.IGNORECASE), 0.7),
    (re.compile(r"\b(?:pig|porcine|non-?human\s+primate|macaque|marmoset)", re.IGNORECASE), 0.7),
    (re.compile(r"\b(?:primary\s+(?:neuron|cell|culture))", re.IGNORECASE), 0.6),
    (re.compile(r"\b(?:SH-SY5Y|HEK293|HeLa|NSC-?34|N2a|PC12|Neuro-?2a|cell\s+line|cultured\s+cells)", re.IGNORECASE), 0.5),
    (re.compile(r"\b(?:in\s+silico|computational|bioinformatic|molecular\s+docking|machine\s+learning|network\s+analysis)", re.IGNORECASE), 0.3),
    (re.compile(r"\breview\b", re.IGNORECASE), 0.4),
]
NO_MODEL_SYSTEM_SCORE = 0.5

# Journal tiers
TIER1_JOURNALS = {
    "nature", "science", "cell", "the new england journal of medicine",
    "the lancet", "nature medicine", "nature neuroscience",
    "nature genetics", "nature biotechnology", "nature methods",
    "cell stem cell", "cell reports", "neuron", "jama",
    "jama neurology", "annals of neurology", "brain",
    "the lancet neurology", "science translational medicine",
    "proceedings of the national academy of sciences",
    "nature communications", "nature reviews neuroscience",
    "nature reviews genetics", "molecular cell",
}

TIER2_JOURNALS = {
    "human molecular genetics", "journal of neuroscience",
    "neurobiology of disease", "acta neuropathologica",
    "journal of clinical investigation", "embo journal",
    "embo molecular medicine", "nucleic acids research",
    "genome research", "plos genetics", "elife",
    "journal of neurology, neurosurgery, and psychiatry",
    "muscle & nerve", "neuromuscular disorders",
    "orphanet journal of rare diseases", "molecular therapy",
    "gene therapy", "human gene therapy",
    "journal of neuromuscular diseases",
    "frontiers in neuroscience", "frontiers in molecular neuroscience",
    "scientific reports", "plos one",
    "journal of biological chemistry", "biochemical journal",
    "journal of cell biology", "molecular biology of the cell",
    "developmental cell", "genes & development",
    "american journal of human genetics",
    "european journal of human genetics",
}


def extract_sample_size(abstract: str) -> int | None:
    """Extract the largest sample size mentioned in the abstract."""
    if not abstract:
        return None
    sizes = []
    for pattern in SAMPLE_SIZE_PATTERNS:
        for m in pattern.finditer(abstract):
            try:
                n = int(m.group(1))
                if 1 <= n <= 100000:  # sanity check
                    sizes.append(n)
            except (ValueError, IndexError):
                continue
    return max(sizes) if sizes else None


def score_sample_size(n: int | None) -> float:
    """Score based on sample size."""
    if n is None:
        return NO_SAMPLE_SIZE_SCORE
    for threshold, score in SAMPLE_SIZE_SCORES:
        if n > threshold:
            return score
    return 0.3


def score_model_system(abstract: str) -> float:
    """Score based on model system detected in abstract."""
    if not abstract:
        return NO_MODEL_SYSTEM_SCORE
    for pattern, score in MODEL_SYSTEM_RULES:
        if pattern.search(abstract):
            return score
    return NO_MODEL_SYSTEM_SCORE


def score_journal_tier(journal: str | None) -> float:
    """Score based on journal prestige tier."""
    if not journal:
        return 0.5
    j = journal.lower().strip()
    if j in TIER1_JOURNALS:
        return 1.0
    if j in TIER2_JOURNALS:
        return 0.7
    # Partial match for journals with subtitles
    for t1 in TIER1_JOURNALS:
        if t1 in j or j in t1:
            return 1.0
    for t2 in TIER2_JOURNALS:
        if t2 in j or j in t2:
            return 0.7
    return 0.5


def compute_quality_score(
    abstract: str | None,
    journal: str | None,
    weights: tuple[float, float, float] = (0.3, 0.4, 0.3),
) -> tuple[float, dict]:
    """Compute composite quality score.

    Args:
        abstract: Paper abstract text
        journal: Journal name
        weights: (sample_size_weight, model_system_weight, journal_weight)

    Returns:
        (score, breakdown_dict) where score is 0.0-1.0
    """
    abs_text = abstract or ""

    n = extract_sample_size(abs_text)
    s_sample = score_sample_size(n)
    s_model = score_model_system(abs_text)
    s_journal = score_journal_tier(journal)

    w_sample, w_model, w_journal = weights
    composite = (
        w_sample * s_sample
        + w_model * s_model
        + w_journal * s_journal
    )

    breakdown = {
        "sample_size": n,
        "sample_score": round(s_sample, 2),
        "model_score": round(s_model, 2),
        "journal_score": round(s_journal, 2),
        "composite": round(composite, 3),
    }
    return round(composite, 3), breakdown


async def migrate_schema(pool: asyncpg.Pool) -> None:
    """Add quality_score column to sources table if it doesn't exist."""
    async with pool.acquire() as conn:
        exists = await conn.fetchval(
            """SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'sources' AND column_name = 'quality_score'
            )"""
        )
        if not exists:
            await conn.execute(
                """ALTER TABLE sources
                   ADD COLUMN quality_score NUMERIC(4,3)
                   CHECK (quality_score >= 0 AND quality_score <= 1)"""
            )
            logger.info("Added quality_score column to sources table")
        else:
            logger.info("quality_score column already exists")


async def score_sources(dry_run: bool = False, migrate: bool = False) -> None:
    """Main scoring logic."""
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        logger.error("DATABASE_URL not set. See usage in docstring.")
        sys.exit(1)

    pool = await asyncpg.create_pool(dsn, min_size=2, max_size=5)

    if migrate:
        await migrate_schema(pool)

    # Fetch all sources
    async with pool.acquire() as conn:
        sources = await conn.fetch(
            """SELECT id, title, journal, abstract, quality_score
               FROM sources
               ORDER BY pub_date DESC NULLS LAST"""
        )
    logger.info("Loaded %d sources", len(sources))

    # Score each source
    updates: list[tuple[str, float]] = []
    score_distribution = {
        "high (>0.7)": 0,
        "medium (0.4-0.7)": 0,
        "low (<0.4)": 0,
    }

    for src in sources:
        score, breakdown = compute_quality_score(src["abstract"], src["journal"])
        updates.append((str(src["id"]), score))

        if score > 0.7:
            score_distribution["high (>0.7)"] += 1
        elif score >= 0.4:
            score_distribution["medium (0.4-0.7)"] += 1
        else:
            score_distribution["low (<0.4)"] += 1

    if dry_run:
        logger.info("DRY RUN — no database updates")
        print("\nSample scores (first 20):")
        print(f"{'Title':<60} {'Journal':<25} {'Score':>6}")
        print("-" * 95)
        for src, (_, score) in zip(sources[:20], updates[:20]):
            title = (src["title"] or "")[:58]
            journal = (src["journal"] or "")[:23]
            print(f"{title:<60} {journal:<25} {score:>6.3f}")
    else:
        # Ensure column exists before writing
        await migrate_schema(pool)

        # Batch update
        async with pool.acquire() as conn:
            async with conn.transaction():
                stmt = await conn.prepare(
                    "UPDATE sources SET quality_score = $1 WHERE id = $2::uuid"
                )
                for source_id, score in updates:
                    await stmt.fetchval(score, source_id)

        logger.info("Updated quality_score for %d sources", len(updates))

    # Report
    print("\n" + "=" * 50)
    print("SOURCE QUALITY SCORING REPORT")
    print("=" * 50)
    print(f"Total sources scored: {len(updates)}")
    print(f"Score distribution:")
    for label, count in score_distribution.items():
        pct = (count / len(updates) * 100) if updates else 0
        print(f"  {label}: {count} ({pct:.1f}%)")

    if updates:
        scores = [s for _, s in updates]
        avg = sum(scores) / len(scores)
        print(f"Average score: {avg:.3f}")
        print(f"Min: {min(scores):.3f}, Max: {max(scores):.3f}")

    print("=" * 50)

    await pool.close()


def main():
    parser = argparse.ArgumentParser(
        description="Score publication quality based on abstract analysis"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview scores without writing to database"
    )
    parser.add_argument(
        "--migrate", action="store_true",
        help="Add quality_score column to sources table (run once)"
    )
    args = parser.parse_args()
    asyncio.run(score_sources(dry_run=args.dry_run, migrate=args.migrate))


if __name__ == "__main__":
    main()
