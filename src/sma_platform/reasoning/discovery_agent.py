"""Auto-Discovery Pipeline — Breakthrough Signal Detection Agent.

Compares new claims against existing hypotheses and evidence, identifies
convergence signals where multiple independent sources suddenly agree on
a target, and generates "breakthrough alerts" for researchers.

This is the intelligence layer that transforms raw claim ingestion into
actionable research signals.

Architecture:
1. Scan recent claims (last N days)
2. Group by target — detect sudden spikes in claim volume
3. Cross-reference with existing hypotheses — find confirmation/contradiction
4. Score each signal by novelty, convergence, and impact
5. Generate breakthrough alerts and post to blackboard
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from ..core.database import execute, execute_script, fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DDL for breakthrough_signals table
# ---------------------------------------------------------------------------

_CREATE_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS breakthrough_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    target_symbol TEXT,
    confidence FLOAT DEFAULT 0.5,
    novelty_score FLOAT DEFAULT 0.0,
    convergence_score FLOAT DEFAULT 0.0,
    impact_score FLOAT DEFAULT 0.0,
    composite_score FLOAT DEFAULT 0.0,
    claim_ids UUID[],
    source_ids UUID[],
    hypothesis_ids UUID[],
    metadata JSONB DEFAULT '{}',
    status TEXT DEFAULT 'new',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_breakthrough_signals_score ON breakthrough_signals(composite_score DESC);
CREATE INDEX IF NOT EXISTS idx_breakthrough_signals_status ON breakthrough_signals(status);
CREATE INDEX IF NOT EXISTS idx_breakthrough_signals_created ON breakthrough_signals(created_at DESC);
"""

_table_ready = False


async def ensure_table() -> None:
    """Create the breakthrough_signals table if it doesn't exist."""
    global _table_ready
    if _table_ready:
        return
    try:
        await execute_script(_CREATE_TABLE_DDL)
        _table_ready = True
    except Exception as e:
        logger.error("Failed to create breakthrough_signals table: %s", e)


# ---------------------------------------------------------------------------
# Signal Detection
# ---------------------------------------------------------------------------

async def detect_claim_spikes(
    days_back: int = 7,
    min_claims: int = 5,
) -> list[dict[str, Any]]:
    """Detect targets with unusual claim volume in the last N days.

    A "spike" = more claims in the last N days than the monthly baseline.
    """
    rows = await fetch(
        """
        WITH recent AS (
            SELECT
                t.symbol,
                t.name,
                count(*) AS recent_claims,
                count(DISTINCT ev.source_id) AS recent_sources
            FROM claims c
            LEFT JOIN targets t ON c.subject_id = t.id
            LEFT JOIN evidence ev ON ev.claim_id = c.id
            WHERE c.created_at >= CURRENT_TIMESTAMP - ($1 || ' days')::interval
              AND t.symbol IS NOT NULL
            GROUP BY t.symbol, t.name
        ),
        baseline AS (
            SELECT
                t.symbol,
                count(*) / GREATEST(1, EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - MIN(c.created_at))) / 86400 / 30) AS monthly_avg
            FROM claims c
            LEFT JOIN targets t ON c.subject_id = t.id
            WHERE t.symbol IS NOT NULL
            GROUP BY t.symbol
        )
        SELECT
            r.symbol,
            r.name,
            r.recent_claims,
            r.recent_sources,
            COALESCE(b.monthly_avg, 0) AS monthly_baseline,
            CASE
                WHEN COALESCE(b.monthly_avg, 0) > 0
                THEN r.recent_claims::float / b.monthly_avg
                ELSE r.recent_claims::float
            END AS spike_ratio
        FROM recent r
        LEFT JOIN baseline b ON b.symbol = r.symbol
        WHERE r.recent_claims >= $2
        ORDER BY spike_ratio DESC
        """,
        str(days_back), min_claims,
    )

    spikes = []
    for row in rows:
        r = dict(row)
        spikes.append({
            "symbol": r["symbol"],
            "name": r["name"],
            "recent_claims": r["recent_claims"],
            "recent_sources": r["recent_sources"],
            "monthly_baseline": round(float(r["monthly_baseline"]), 1),
            "spike_ratio": round(float(r["spike_ratio"]), 2),
        })

    return spikes


async def find_hypothesis_confirmations(
    days_back: int = 7,
) -> list[dict[str, Any]]:
    """Find new claims that confirm or contradict existing hypotheses."""
    # Get recent claims with their targets
    recent_claims = await fetch(
        """
        SELECT c.id AS claim_id, c.claim_type, c.predicate, c.confidence,
               c.subject_id, t.symbol AS target_symbol,
               ev.source_id, s.title AS source_title, s.external_id AS pmid
        FROM claims c
        LEFT JOIN targets t ON c.subject_id = t.id
        LEFT JOIN evidence ev ON ev.claim_id = c.id
        LEFT JOIN sources s ON ev.source_id = s.id
        WHERE c.created_at >= CURRENT_TIMESTAMP - ($1 || ' days')::interval
          AND t.symbol IS NOT NULL
        ORDER BY c.confidence DESC
        """,
        str(days_back),
    )

    # Get all hypotheses with their target symbols
    hypotheses = await fetch(
        """
        SELECT id, title, description, confidence, status,
               metadata
        FROM hypotheses
        WHERE status NOT IN ('refuted')
        ORDER BY confidence DESC
        """
    )

    confirmations = []
    for hyp in hypotheses:
        h = dict(hyp)
        meta = {}
        try:
            meta = json.loads(h.get("metadata") or "{}")
        except (json.JSONDecodeError, TypeError):
            pass

        target_symbol = meta.get("target_symbol", "")
        if not target_symbol:
            continue

        # Find recent claims matching this hypothesis's target
        matching_claims = [
            dict(c) for c in recent_claims
            if dict(c).get("target_symbol") == target_symbol
        ]

        if not matching_claims:
            continue

        # Score: more matching claims with high confidence = stronger confirmation
        avg_conf = float(sum(float(c["confidence"] or 0) for c in matching_claims)) / len(matching_claims)
        n_sources = len(set(str(c.get("source_id", "")) for c in matching_claims if c.get("source_id")))
        claim_types = set(c["claim_type"] for c in matching_claims)

        confirmation_strength = min(1.0, (avg_conf * 0.4 + min(1.0, n_sources / 5) * 0.3 + min(1.0, len(claim_types) / 4) * 0.3))

        confirmations.append({
            "hypothesis_id": str(h["id"]),
            "hypothesis_title": h["title"][:200],
            "hypothesis_confidence": float(h["confidence"]) if h["confidence"] else 0,
            "target_symbol": target_symbol,
            "new_claims": len(matching_claims),
            "new_sources": n_sources,
            "claim_types": sorted(claim_types),
            "avg_claim_confidence": round(avg_conf, 3),
            "confirmation_strength": round(confirmation_strength, 3),
            "claim_ids": [str(c["claim_id"]) for c in matching_claims[:20]],
        })

    # Sort by confirmation strength
    confirmations.sort(key=lambda x: x["confirmation_strength"], reverse=True)
    return confirmations


async def detect_novel_targets(
    days_back: int = 30,
    min_claims: int = 3,
) -> list[dict[str, Any]]:
    """Find targets that appear in recent claims but have NO existing hypotheses.

    These are potentially novel discoveries that the platform hasn't formalized yet.
    """
    rows = await fetch(
        """
        SELECT t.symbol, t.name, t.target_type,
               count(DISTINCT c.id) AS claim_count,
               count(DISTINCT ev.source_id) AS source_count,
               array_agg(DISTINCT c.claim_type) AS claim_types
        FROM claims c
        JOIN targets t ON c.subject_id = t.id
        LEFT JOIN evidence ev ON ev.claim_id = c.id
        WHERE c.created_at >= CURRENT_TIMESTAMP - ($1 || ' days')::interval
        GROUP BY t.symbol, t.name, t.target_type
        HAVING count(DISTINCT c.id) >= $2
        ORDER BY count(DISTINCT c.id) DESC
        """,
        str(days_back), min_claims,
    )

    # Check which of these have hypotheses
    novel = []
    for row in rows:
        r = dict(row)
        symbol = r["symbol"]

        hyp_count = await fetchval(
            """SELECT count(*) FROM hypotheses
               WHERE CAST(metadata AS TEXT) LIKE $1""",
            f'%"{symbol}"%',
        )

        if (hyp_count or 0) == 0:
            novel.append({
                "symbol": symbol,
                "name": r["name"],
                "target_type": r["target_type"],
                "claim_count": r["claim_count"],
                "source_count": r["source_count"],
                "claim_types": r["claim_types"],
                "novelty": "high" if r["claim_count"] >= 10 else "medium",
                "suggestion": f"Generate hypotheses for {symbol} — {r['claim_count']} claims from {r['source_count']} sources, no hypotheses yet",
            })

    return novel


# ---------------------------------------------------------------------------
# Composite Discovery Run
# ---------------------------------------------------------------------------

async def run_discovery(
    days_back: int = 7,
    persist: bool = True,
) -> dict[str, Any]:
    """Run the full auto-discovery pipeline.

    1. Detect claim volume spikes per target
    2. Find hypothesis confirmations from new evidence
    3. Identify novel targets without hypotheses
    4. Score and rank all signals
    5. Optionally persist breakthrough signals
    """
    await ensure_table()

    spikes = await detect_claim_spikes(days_back=days_back, min_claims=3)
    confirmations = await find_hypothesis_confirmations(days_back=days_back)
    novel_targets = await detect_novel_targets(days_back=30, min_claims=3)

    signals = []

    # Spike signals
    for spike in spikes:
        if spike["spike_ratio"] >= 1.5:
            signals.append({
                "signal_type": "claim_spike",
                "title": f"Claim spike for {spike['symbol']}: {spike['recent_claims']} claims in {days_back} days ({spike['spike_ratio']}x baseline)",
                "description": f"{spike['name']} ({spike['symbol']}) has {spike['recent_claims']} new claims from {spike['recent_sources']} sources in the last {days_back} days — {spike['spike_ratio']}x the monthly average.",
                "target_symbol": spike["symbol"],
                "novelty_score": min(1.0, spike["spike_ratio"] / 5),
                "convergence_score": min(1.0, spike["recent_sources"] / 10),
                "impact_score": 0.5,
            })

    # Confirmation signals
    for conf in confirmations:
        if conf["confirmation_strength"] >= 0.4:
            signals.append({
                "signal_type": "hypothesis_confirmation",
                "title": f"New evidence confirms hypothesis for {conf['target_symbol']} (strength: {conf['confirmation_strength']:.0%})",
                "description": f"{conf['new_claims']} new claims from {conf['new_sources']} independent sources support: \"{conf['hypothesis_title'][:150]}\"",
                "target_symbol": conf["target_symbol"],
                "novelty_score": 0.3,
                "convergence_score": conf["confirmation_strength"],
                "impact_score": min(1.0, conf["hypothesis_confidence"] * 1.2),
                "hypothesis_id": conf["hypothesis_id"],
                "claim_ids": conf["claim_ids"],
            })

    # Novel target signals
    for novel in novel_targets:
        signals.append({
            "signal_type": "novel_target",
            "title": f"Novel target without hypotheses: {novel['symbol']} ({novel['claim_count']} claims)",
            "description": f"{novel['name']} ({novel['symbol']}) has {novel['claim_count']} claims from {novel['source_count']} sources but no hypotheses generated yet. Types: {', '.join(novel['claim_types'])}",
            "target_symbol": novel["symbol"],
            "novelty_score": 0.9,
            "convergence_score": min(1.0, novel["source_count"] / 5),
            "impact_score": 0.6,
        })

    # Score all signals
    for s in signals:
        s["composite_score"] = round(
            s["novelty_score"] * 0.3 + s["convergence_score"] * 0.4 + s["impact_score"] * 0.3,
            3,
        )

    # Sort by composite score
    signals.sort(key=lambda x: x["composite_score"], reverse=True)

    # Persist top signals
    stored = 0
    if persist:
        for s in signals[:50]:
            try:
                await execute(
                    """INSERT INTO breakthrough_signals
                       (signal_type, title, description, target_symbol, confidence,
                        novelty_score, convergence_score, impact_score, composite_score,
                        claim_ids, metadata)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)""",
                    s["signal_type"],
                    s["title"][:500],
                    s["description"],
                    s.get("target_symbol"),
                    s["composite_score"],
                    s["novelty_score"],
                    s["convergence_score"],
                    s["impact_score"],
                    s["composite_score"],
                    s.get("claim_ids", []),
                    json.dumps({
                        "hypothesis_id": s.get("hypothesis_id"),
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "days_back": days_back,
                    }),
                )
                stored += 1
            except Exception as e:
                logger.error("Failed to store signal: %s", e)

    return {
        "days_back": days_back,
        "spikes_detected": len(spikes),
        "hypothesis_confirmations": len(confirmations),
        "novel_targets": len(novel_targets),
        "total_signals": len(signals),
        "signals_stored": stored,
        "top_signals": signals[:10],
    }
