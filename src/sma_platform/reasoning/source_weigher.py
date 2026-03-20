"""Source Quality Weighting — not all PubMed papers are equal.

Assigns quality weights to sources based on journal tier, recency,
and article type. Used to weight evidence claims.

Complementary to source_quality.py (which scores 5 dimensions for detailed
analysis), this module provides a fast 3-factor composite weight suitable
for weighting claims during hypothesis generation and convergence scoring.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Journal tiers for SMA research
# ---------------------------------------------------------------------------

TIER_1: set[str] = {
    "nature", "science", "cell", "nature medicine", "nature genetics",
    "nature neuroscience", "nature biotechnology", "nature methods",
    "new england journal of medicine", "the lancet", "lancet neurology",
}

TIER_2: set[str] = {
    "brain", "neuron", "pnas", "human molecular genetics",
    "annals of neurology", "journal of clinical investigation",
    "embo journal", "molecular therapy", "nucleic acids research",
    "genome research", "cell reports", "american journal of human genetics",
    "journal of neuroscience", "science translational medicine",
    "nature communications", "elife",
}

TIER_3: set[str] = {
    "neuromuscular disorders", "journal of neuromuscular diseases",
    "orphanet journal of rare diseases", "european journal of human genetics",
    "muscle & nerve", "journal of neurology", "neuropediatrics",
    "frontiers in molecular neuroscience", "human gene therapy",
    "frontiers in neuroscience", "plos genetics", "gene therapy",
    "scientific reports",
}


def compute_source_weight(
    journal: str | None = None,
    pub_date: date | str | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    """Compute quality weight for a source.

    Returns a dict with individual factor weights and a composite weight:
    - journal_weight: 1.0 (tier 1), 0.85 (tier 2), 0.7 (tier 3), 0.5 (other)
    - recency_weight: 1.0 (<2yr), 0.8 (2-5yr), 0.6 (5-10yr), 0.4 (>10yr)
    - type_weight: 1.0 (primary), 0.8 (review/meta), 0.5 (correspondence)
    - composite_weight: 0.4*journal + 0.35*recency + 0.25*type
    """
    # --- Journal tier ---
    journal_lower = (journal or "").lower().strip()
    if any(j in journal_lower for j in TIER_1):
        journal_weight = 1.0
        journal_tier = "tier_1"
    elif any(j in journal_lower for j in TIER_2):
        journal_weight = 0.85
        journal_tier = "tier_2"
    elif any(j in journal_lower for j in TIER_3):
        journal_weight = 0.7
        journal_tier = "tier_3"
    else:
        journal_weight = 0.5
        journal_tier = "other"

    # --- Recency ---
    recency_weight = 0.5
    if pub_date:
        if isinstance(pub_date, str):
            try:
                pub_date = date.fromisoformat(pub_date[:10])
            except (ValueError, IndexError):
                pub_date = None
        if pub_date:
            years_old = (date.today() - pub_date).days / 365.25
            if years_old < 2:
                recency_weight = 1.0
            elif years_old < 5:
                recency_weight = 0.8
            elif years_old < 10:
                recency_weight = 0.6
            else:
                recency_weight = 0.4

    # --- Article type estimate from title ---
    title_lower = (title or "").lower()
    if any(w in title_lower for w in ["review", "systematic review", "meta-analysis"]):
        type_weight = 0.8
        article_type = "review"
    elif any(w in title_lower for w in ["case report", "letter", "comment", "editorial"]):
        type_weight = 0.5
        article_type = "correspondence"
    else:
        type_weight = 1.0
        article_type = "primary"

    composite = round(
        journal_weight * 0.4 + recency_weight * 0.35 + type_weight * 0.25, 3
    )

    return {
        "journal_weight": journal_weight,
        "journal_tier": journal_tier,
        "recency_weight": recency_weight,
        "type_weight": type_weight,
        "article_type": article_type,
        "composite_weight": composite,
    }


async def weight_all_sources() -> dict[str, Any]:
    """Compute quality weights for all sources in the database.

    Returns aggregate statistics: total sources, high-quality count,
    tier distribution, and percentage of high-quality sources.
    """
    from ..core.database import fetch

    rows = await fetch(
        "SELECT id, journal, pub_date, title FROM sources LIMIT 10000"
    )

    tier_counts: dict[str, int] = {"tier_1": 0, "tier_2": 0, "tier_3": 0, "other": 0}
    type_counts: dict[str, int] = {"primary": 0, "review": 0, "correspondence": 0}
    total = 0
    high_quality = 0
    weight_sum = 0.0

    for row in rows:
        w = compute_source_weight(
            journal=row.get("journal"),
            pub_date=str(row["pub_date"]) if row.get("pub_date") else None,
            title=row.get("title"),
        )
        tier_counts[w["journal_tier"]] += 1
        type_counts[w["article_type"]] += 1
        total += 1
        weight_sum += w["composite_weight"]
        if w["composite_weight"] >= 0.7:
            high_quality += 1

    avg_weight = round(weight_sum / total, 3) if total else 0.0

    return {
        "total_sources": total,
        "high_quality": high_quality,
        "high_quality_pct": round(high_quality / total * 100, 1) if total else 0,
        "average_weight": avg_weight,
        "tier_distribution": tier_counts,
        "type_distribution": type_counts,
    }


async def weight_source_by_id(source_id: str) -> dict[str, Any]:
    """Compute quality weight for a single source by ID."""
    from ..core.database import fetchrow

    row = await fetchrow(
        "SELECT id, journal, pub_date, title FROM sources WHERE id = $1",
        source_id,
    )
    if not row:
        return {"error": f"Source {source_id} not found"}

    w = compute_source_weight(
        journal=row.get("journal"),
        pub_date=str(row["pub_date"]) if row.get("pub_date") else None,
        title=row.get("title"),
    )
    return {
        "source_id": str(row["id"]),
        "title": row.get("title"),
        "journal": row.get("journal"),
        "pub_date": str(row["pub_date"]) if row.get("pub_date") else None,
        **w,
    }
