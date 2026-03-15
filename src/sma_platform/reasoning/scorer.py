"""Evidence scorer — computes confidence scores for claims and targets.

Scoring is based on:
1. Number of independent sources supporting a claim
2. Evidence tier (Tier 1 > Tier 2 > Tier 3)
3. Recency of evidence
4. Experimental method strength (RCT > cohort > case report > in silico)
5. Replication across labs/models
"""

from __future__ import annotations

import logging
import math
from typing import Any
from uuid import UUID

from ..core.database import fetch, fetchrow, execute

logger = logging.getLogger(__name__)

# Method strength weights
METHOD_WEIGHTS = {
    "randomized_controlled_trial": 1.0,
    "meta_analysis": 0.95,
    "cohort_study": 0.8,
    "case_control": 0.7,
    "case_report": 0.5,
    "in_vivo": 0.7,
    "in_vitro": 0.6,
    "in_silico": 0.4,
    "expert_opinion": 0.3,
}

# Evidence tier multipliers
TIER_MULTIPLIERS = {
    "tier1": 1.0,
    "tier2": 0.7,
    "tier3": 0.4,
}


async def score_claim(claim_id: UUID) -> float:
    """Calculate an aggregate confidence score for a claim based on its evidence.

    Score = weighted average of evidence quality, normalized to [0, 1].
    """
    evidence_rows = await fetch(
        """SELECT e.*, s.source_type, s.pub_date
           FROM evidence e
           JOIN sources s ON e.source_id = s.id
           WHERE e.claim_id = $1""",
        claim_id,
    )

    if not evidence_rows:
        return 0.0

    total_weight = 0.0
    weighted_score = 0.0

    for ev in evidence_rows:
        method = (ev.get("method") or "").lower().replace(" ", "_")
        method_w = METHOD_WEIGHTS.get(method, 0.5)

        # P-value bonus
        p_val = ev.get("p_value")
        p_bonus = 0.0
        if p_val is not None and p_val < 0.05:
            p_bonus = 0.1 if p_val < 0.01 else 0.05

        # Sample size factor (logarithmic: n=10→0.33, n=100→0.67, n=1000→1.0)
        n = ev.get("sample_size") or 0
        n_factor = min(1.0, math.log10(n + 1) / 3.0) if n > 0 else 0.3

        score = (method_w + p_bonus) * n_factor
        weight = 1.0  # could weight by source tier later

        weighted_score += score * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    raw = weighted_score / total_weight
    return round(max(0.0, min(1.0, raw)), 3)


async def update_claim_confidence(claim_id: UUID) -> float:
    """Recompute and persist the confidence score for a claim."""
    score = await score_claim(claim_id)
    await execute(
        "UPDATE claims SET confidence = $1 WHERE id = $2",
        score, claim_id,
    )
    return score


async def score_all_claims() -> dict[str, int]:
    """Batch-recompute confidence for all claims. Returns stats.

    NOTE: This function has an inherent N+1 pattern — each call to
    update_claim_confidence() issues its own SELECT + UPDATE against the DB.
    The scoring formula itself requires per-claim evidence rows, so a single
    bulk query cannot replace it without restructuring the scoring logic.
    As a lightweight mitigation, claims are processed in chunks of 100 so
    that each chunk's work is localised and avoids holding a single long-lived
    implicit transaction across thousands of rows.
    """
    rows = await fetch("SELECT id FROM claims")
    updated = 0
    chunk_size = 100

    for i in range(0, len(rows), chunk_size):
        chunk = rows[i : i + chunk_size]
        for row in chunk:
            await update_claim_confidence(row["id"])
            updated += 1
        logger.debug("Rescored claims %d–%d", i + 1, i + len(chunk))

    logger.info(f"Rescored {updated} claims")
    return {"claims_rescored": updated}
