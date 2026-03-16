"""Source quality scoring — rates each paper by 5 dimensions.

Dimensions (0-1 each):
1. Journal quality — top SMA/neuro journals score highest
2. Study type — RCTs > observational > reviews > case reports
3. Recency — linear decay from 2026 (1.0) to 2010 or older (0.3)
4. Evidence density — claims per paper, capped at 20 = 1.0
5. SMA specificity — keyword density in title + abstract

Composite = 0.25*journal + 0.20*study_type + 0.20*recency + 0.15*density + 0.20*specificity
"""

from __future__ import annotations

import logging
import re
from datetime import date
from typing import Any

from ..core.database import fetch, fetchrow

logger = logging.getLogger(__name__)

# ---------- Dimension 1: Journal quality ----------

TOP_JOURNALS: set[str] = {
    "nature",
    "new england journal of medicine",
    "nejm",
    "the lancet",
    "lancet",
    "science",
    "cell",
    "neurology",
    "pnas",
    "proceedings of the national academy of sciences",
    "brain",
    "journal of neuroscience",
    "j neurosci",
    "annals of neurology",
    "ann neurol",
    "neuromuscular disorders",
    "human molecular genetics",
    "hum mol genet",
    "journal of medical genetics",
    "j med genet",
    # Sub-journals of top publishers
    "nature medicine",
    "nature neuroscience",
    "nature genetics",
    "nature communications",
    "cell reports",
    "lancet neurology",
    "science translational medicine",
}

KNOWN_JOURNALS: set[str] = {
    "plos one",
    "plos genetics",
    "frontiers in neuroscience",
    "frontiers in molecular neuroscience",
    "molecular therapy",
    "gene therapy",
    "orphanet journal of rare diseases",
    "journal of clinical investigation",
    "embo journal",
    "nucleic acids research",
    "genome research",
    "bmc genomics",
    "scientific reports",
    "elife",
}


def _score_journal(journal: str | None) -> float:
    """Score journal quality: top=1.0, known=0.5, unknown=0.3."""
    if not journal:
        return 0.3
    j = journal.strip().lower()
    # Check top journals — substring match for partial names
    for top in TOP_JOURNALS:
        if top in j or j in top:
            return 1.0
    for known in KNOWN_JOURNALS:
        if known in j or j in known:
            return 0.5
    return 0.3


# ---------- Dimension 2: Study type ----------

# Keywords to detect study type from title + abstract
_STUDY_TYPE_PATTERNS: list[tuple[str, float]] = [
    # RCT / clinical trial (highest)
    (r"\b(randomized|randomised|rct|clinical\s+trial|phase\s+[1-4i]+|placebo[\s-]controlled|double[\s-]blind)\b", 1.0),
    # Observational studies
    (r"\b(cohort|longitudinal|prospective|retrospective|observational|cross[\s-]sectional|registry|natural\s+history)\b", 0.7),
    # Reviews / meta-analyses
    (r"\b(systematic\s+review|meta[\s-]analysis|review\s+of|literature\s+review|scoping\s+review)\b", 0.6),
    # Computational / in silico
    (r"\b(computational|in\s+silico|molecular\s+dynamics|simulation|bioinformatic|machine\s+learning|network\s+analysis)\b", 0.5),
    # Case reports
    (r"\b(case\s+report|case\s+series|single[\s-]patient|single[\s-]case)\b", 0.4),
]

_COMPILED_PATTERNS = [(re.compile(p, re.IGNORECASE), score) for p, score in _STUDY_TYPE_PATTERNS]


def _score_study_type(title: str | None, abstract: str | None) -> float:
    """Detect study type from title + abstract keywords. Highest match wins."""
    text = " ".join(filter(None, [title, abstract]))
    if not text:
        return 0.3

    best = 0.3
    for pattern, score in _COMPILED_PATTERNS:
        if pattern.search(text):
            best = max(best, score)
    return best


# ---------- Dimension 3: Recency ----------

REFERENCE_YEAR = 2026
MIN_YEAR = 2010
DECAY_RATE = 0.044  # (1.0 - 0.3) / (2026 - 2010)


def _score_recency(pub_date: date | str | None) -> float:
    """Linear decay from 1.0 (2026) to 0.3 (2010 or older)."""
    if pub_date is None:
        return 0.3

    if isinstance(pub_date, str):
        try:
            year = int(pub_date[:4])
        except (ValueError, IndexError):
            return 0.3
    else:
        year = pub_date.year

    return round(max(0.3, 1.0 - (REFERENCE_YEAR - year) * DECAY_RATE), 3)


# ---------- Dimension 4: Evidence density ----------

MAX_CLAIMS_CAP = 20


def _score_density(claim_count: int) -> float:
    """Normalize claim count to 0-1, capped at 20 claims = 1.0."""
    if claim_count <= 0:
        return 0.0
    return round(min(1.0, claim_count / MAX_CLAIMS_CAP), 3)


# ---------- Dimension 5: SMA specificity ----------

SMA_KEYWORDS: list[str] = [
    "spinal muscular atrophy", "sma", "smn1", "smn2", "smn protein",
    "survival motor neuron", "motor neuron", "motor neurone",
    "nusinersen", "spinraza", "onasemnogene", "zolgensma", "risdiplam", "evrysdi",
    "antisense oligonucleotide", "aso", "gene therapy",
    "5q sma", "werdnig-hoffmann", "kugelberg-welander",
    "neuromuscular", "muscle atrophy", "denervation",
    "splicing", "exon 7", "exon skipping", "splice modifier",
    "motor function", "chop intend", "hfmse", "rulm",
    "sma type 1", "sma type 2", "sma type 3", "sma type i", "sma type ii", "sma type iii",
]

_SMA_PATTERNS = [re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE) for kw in SMA_KEYWORDS]
MAX_KEYWORD_HITS = 10  # cap for normalization


def _score_sma_specificity(title: str | None, abstract: str | None) -> float:
    """Count SMA-related keyword matches in title + abstract, normalized."""
    text = " ".join(filter(None, [title, abstract]))
    if not text:
        return 0.0

    hits = sum(1 for p in _SMA_PATTERNS if p.search(text))
    return round(min(1.0, hits / MAX_KEYWORD_HITS), 3)


# ---------- Composite ----------

WEIGHTS = {
    "journal": 0.25,
    "study_type": 0.20,
    "recency": 0.20,
    "density": 0.15,
    "specificity": 0.20,
}


def compute_source_quality(
    journal: str | None,
    title: str | None,
    abstract: str | None,
    pub_date: date | str | None,
    claim_count: int,
) -> dict[str, float]:
    """Compute all 5 dimension scores and composite for a single source."""
    journal_score = _score_journal(journal)
    study_type_score = _score_study_type(title, abstract)
    recency_score = _score_recency(pub_date)
    density_score = _score_density(claim_count)
    specificity_score = _score_sma_specificity(title, abstract)

    composite = (
        WEIGHTS["journal"] * journal_score
        + WEIGHTS["study_type"] * study_type_score
        + WEIGHTS["recency"] * recency_score
        + WEIGHTS["density"] * density_score
        + WEIGHTS["specificity"] * specificity_score
    )

    return {
        "journal_quality": round(journal_score, 3),
        "study_type": round(study_type_score, 3),
        "recency": round(recency_score, 3),
        "evidence_density": round(density_score, 3),
        "sma_specificity": round(specificity_score, 3),
        "composite": round(composite, 3),
    }


# ---------- DB-backed scoring ----------

async def score_all_sources(limit: int = 500) -> list[dict]:
    """Score all sources from the database.

    Joins sources with evidence to get claim counts, then scores each source
    across all 5 dimensions. Returns sorted by composite score descending.
    """
    rows = await fetch(
        """SELECT s.id, s.title, s.abstract, s.pub_date, s.journal,
                  s.source_type, s.external_id, s.doi, s.authors,
                  COUNT(e.id) AS claim_count
           FROM sources s
           LEFT JOIN evidence e ON e.source_id = s.id
           GROUP BY s.id, s.title, s.abstract, s.pub_date, s.journal,
                    s.source_type, s.external_id, s.doi, s.authors
           ORDER BY s.pub_date DESC NULLS LAST
           LIMIT $1""",
        limit,
    )

    results: list[dict] = []
    for row in rows:
        scores = compute_source_quality(
            journal=row.get("journal"),
            title=row.get("title"),
            abstract=row.get("abstract"),
            pub_date=row.get("pub_date"),
            claim_count=row.get("claim_count", 0),
        )
        results.append({
            "source_id": str(row["id"]),
            "title": row.get("title"),
            "journal": row.get("journal"),
            "pub_date": str(row["pub_date"]) if row.get("pub_date") else None,
            "source_type": row.get("source_type"),
            "external_id": row.get("external_id"),
            "claim_count": row.get("claim_count", 0),
            "scores": scores,
        })

    # Sort by composite score descending
    results.sort(key=lambda r: r["scores"]["composite"], reverse=True)

    logger.info("Scored %d sources, top composite=%.3f",
                len(results),
                results[0]["scores"]["composite"] if results else 0.0)
    return results


async def get_source_quality_distribution() -> dict:
    """Aggregate quality distribution across all scored sources.

    Returns histogram buckets, per-dimension averages, and tier breakdown
    (A: >= 0.7, B: 0.4-0.7, C: < 0.4).
    """
    # Score all sources (no limit for distribution)
    all_scored = await score_all_sources(limit=10000)

    if not all_scored:
        return {
            "total_sources": 0,
            "averages": {},
            "tiers": {"A": 0, "B": 0, "C": 0},
            "histogram": [],
        }

    composites = [s["scores"]["composite"] for s in all_scored]
    dimensions = ["journal_quality", "study_type", "recency", "evidence_density", "sma_specificity", "composite"]

    # Per-dimension averages
    averages: dict[str, float] = {}
    for dim in dimensions:
        vals = [s["scores"][dim] for s in all_scored]
        averages[dim] = round(sum(vals) / len(vals), 3)

    # Tier breakdown
    tier_a = sum(1 for c in composites if c >= 0.7)
    tier_b = sum(1 for c in composites if 0.4 <= c < 0.7)
    tier_c = sum(1 for c in composites if c < 0.4)

    # Histogram buckets (0.0-0.1, 0.1-0.2, ..., 0.9-1.0)
    buckets = [0] * 10
    for c in composites:
        idx = min(int(c * 10), 9)
        buckets[idx] += 1
    histogram = [
        {"range": f"{i/10:.1f}-{(i+1)/10:.1f}", "count": buckets[i]}
        for i in range(10)
    ]

    return {
        "total_sources": len(all_scored),
        "averages": averages,
        "tiers": {"A": tier_a, "B": tier_b, "C": tier_c},
        "histogram": histogram,
        "top_5": [
            {"title": s["title"], "composite": s["scores"]["composite"]}
            for s in all_scored[:5]
        ],
    }
