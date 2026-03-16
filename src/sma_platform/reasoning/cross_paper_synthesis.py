"""Cross-Paper Synthesis Engine — Core Differentiator #1.

Finds non-obvious connections across 24k+ claims from different papers
that researchers wouldn't naturally read together. Unlike convergence_engine.py
(single-target focus), this module identifies *cross-target* bridges:

Example: Paper A says "PLS3 rescues motor neurons via actin bundling"
         Paper B says "NCALD knockdown restores endocytosis via actin dynamics"
         → Synthesis: PLS3 and NCALD may share an actin-dependent rescue pathway

Architecture:
1. Build claim co-occurrence matrix (targets mentioned in same paper)
2. Find transitive connections (A→B in paper1, B→C in paper2 → A→C)
3. Score connections by evidence strength + novelty
4. Use Claude to synthesize mechanistic explanations
5. Generate "synthesis cards" for display

This is what makes the SMA Research Platform unique — no other tool does
automated cross-paper synthesis for rare disease research.
"""

from __future__ import annotations

import json
import logging
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Optional

import anthropic

from ..core.database import execute, execute_script, fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"

# DDL for synthesis cards table
_CREATE_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS synthesis_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    synthesis_type TEXT NOT NULL,
    target_a TEXT NOT NULL,
    target_b TEXT NOT NULL,
    bridge_entity TEXT,
    mechanism TEXT NOT NULL,
    evidence_summary TEXT NOT NULL,
    testable_prediction TEXT,
    confidence FLOAT DEFAULT 0.5,
    novelty_score FLOAT DEFAULT 0.0,
    supporting_papers INT DEFAULT 0,
    claim_ids UUID[],
    source_ids UUID[],
    metadata JSONB DEFAULT '{}',
    status TEXT DEFAULT 'new',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_synthesis_target_a ON synthesis_cards(target_a);
CREATE INDEX IF NOT EXISTS idx_synthesis_target_b ON synthesis_cards(target_b);
CREATE INDEX IF NOT EXISTS idx_synthesis_type ON synthesis_cards(synthesis_type);
"""

# Synthesis types
COOCCURRENCE = "co_occurrence"        # Targets in the same paper
TRANSITIVE = "transitive_bridge"      # A→B→C chain across papers
SHARED_MECHANISM = "shared_mechanism" # Same predicate/mechanism, different targets
CONTRADICTION = "contradiction"       # Conflicting claims about same target pair


async def ensure_table():
    """Create synthesis_cards table if it doesn't exist."""
    await execute_script(_CREATE_TABLE_DDL)


# =============================================================================
# Step 1: Build Co-occurrence Matrix
# =============================================================================

async def build_cooccurrence_matrix() -> dict[tuple[str, str], list[dict]]:
    """
    Find target pairs that co-occur in the same source paper.
    Returns: {(target_a, target_b): [list of shared source_ids with claim details]}
    """
    # Get all claims with their source and target info
    rows = await fetch("""
        SELECT
            c.id as claim_id,
            c.claim_type,
            c.predicate,
            c.confidence,
            c.metadata,
            e.source_id,
            s.title as source_title,
            s.pub_date,
            COALESCE(t_subj.symbol, c.subject_type) as subject_symbol,
            COALESCE(t_obj.symbol, c.object_type) as object_symbol
        FROM claims c
        JOIN evidence e ON e.claim_id = c.id
        JOIN sources s ON s.id = e.source_id
        LEFT JOIN targets t_subj ON t_subj.id = c.subject_id
        LEFT JOIN targets t_obj ON t_obj.id = c.object_id
        WHERE c.confidence >= 0.5
        ORDER BY s.pub_date DESC NULLS LAST
    """)

    # Group claims by source
    source_claims: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        source_id = str(row["source_id"])
        source_claims[source_id].append({
            "claim_id": str(row["claim_id"]),
            "claim_type": row["claim_type"],
            "predicate": row["predicate"],
            "confidence": float(row["confidence"]) if row["confidence"] else 0.5,
            "subject": row["subject_symbol"],
            "object": row["object_symbol"],
            "source_title": row["source_title"],
            "pub_date": str(row["pub_date"]) if row["pub_date"] else None,
        })

    # Find target co-occurrences per source
    cooccurrences: dict[tuple[str, str], list[dict]] = defaultdict(list)

    for source_id, claims in source_claims.items():
        # Get unique targets mentioned in this paper
        targets_in_paper = set()
        for c in claims:
            if c["subject"]:
                targets_in_paper.add(c["subject"])
            if c["object"]:
                targets_in_paper.add(c["object"])

        # Generate all pairs (sorted to avoid duplicates)
        targets = sorted(t for t in targets_in_paper if t)
        for i in range(len(targets)):
            for j in range(i + 1, len(targets)):
                pair = (targets[i], targets[j])
                cooccurrences[pair].append({
                    "source_id": source_id,
                    "source_title": claims[0]["source_title"],
                    "claims": [c for c in claims if c["subject"] in pair or c["object"] in pair],
                })

    logger.info(f"Found {len(cooccurrences)} target co-occurrence pairs "
                f"across {len(source_claims)} papers")
    return cooccurrences


# =============================================================================
# Step 2: Find Transitive Bridges
# =============================================================================

async def find_transitive_bridges() -> list[dict]:
    """
    Find A→B→C chains: Paper 1 connects A to B, Paper 2 connects B to C.
    This identifies targets connected through an intermediate entity.
    """
    # Get directional claim edges: subject → object
    rows = await fetch("""
        SELECT
            c.id as claim_id,
            COALESCE(t_subj.symbol, c.subject_type) as subject_symbol,
            COALESCE(t_obj.symbol, c.object_type) as object_symbol,
            c.predicate,
            c.claim_type,
            c.confidence,
            e.source_id
        FROM claims c
        JOIN evidence e ON e.claim_id = c.id
        LEFT JOIN targets t_subj ON t_subj.id = c.subject_id
        LEFT JOIN targets t_obj ON t_obj.id = c.object_id
        WHERE c.subject_id IS NOT NULL
          AND c.object_id IS NOT NULL
          AND c.confidence >= 0.5
    """)

    # Build adjacency: subject → [objects]
    edges: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        subj = row["subject_symbol"]
        obj = row["object_symbol"]
        if subj and obj and subj != obj:
            edges[subj].append({
                "object": obj,
                "predicate": row["predicate"],
                "claim_type": row["claim_type"],
                "confidence": float(row["confidence"]) if row["confidence"] else 0.5,
                "claim_id": str(row["claim_id"]),
                "source_id": str(row["source_id"]),
            })

    # Find 2-hop paths: A → B → C where A→B and B→C come from DIFFERENT sources
    bridges = []
    seen = set()

    for a, a_edges in edges.items():
        for ab_edge in a_edges:
            b = ab_edge["object"]
            if b in edges:
                for bc_edge in edges[b]:
                    c = bc_edge["object"]
                    # Skip self-loops and same-source connections
                    if c == a or ab_edge["source_id"] == bc_edge["source_id"]:
                        continue

                    bridge_key = tuple(sorted([a, c]) + [b])
                    if bridge_key in seen:
                        continue
                    seen.add(bridge_key)

                    bridges.append({
                        "target_a": a,
                        "bridge": b,
                        "target_c": c,
                        "a_to_b": {
                            "predicate": ab_edge["predicate"],
                            "claim_type": ab_edge["claim_type"],
                            "confidence": ab_edge["confidence"],
                            "source_id": ab_edge["source_id"],
                            "claim_id": ab_edge["claim_id"],
                        },
                        "b_to_c": {
                            "predicate": bc_edge["predicate"],
                            "claim_type": bc_edge["claim_type"],
                            "confidence": bc_edge["confidence"],
                            "source_id": bc_edge["source_id"],
                            "claim_id": bc_edge["claim_id"],
                        },
                        "combined_confidence": ab_edge["confidence"] * bc_edge["confidence"],
                    })

    # Sort by combined confidence
    bridges.sort(key=lambda x: x["combined_confidence"], reverse=True)
    logger.info(f"Found {len(bridges)} transitive bridges")
    return bridges[:200]  # Top 200


# =============================================================================
# Step 3: Find Shared Mechanisms
# =============================================================================

async def find_shared_mechanisms() -> list[dict]:
    """
    Find different targets linked by the same mechanism/predicate.
    E.g., if claim 1 says "PLS3 rescues via actin bundling" and
    claim 2 says "NCALD knockdown rescues via actin dynamics",
    the shared mechanism is "actin-dependent rescue".
    """
    rows = await fetch("""
        SELECT
            c.claim_type,
            c.predicate,
            COALESCE(t_subj.symbol, c.subject_type) as subject_symbol,
            c.id as claim_id,
            c.confidence,
            e.source_id
        FROM claims c
        JOIN evidence e ON e.claim_id = c.id
        LEFT JOIN targets t_subj ON t_subj.id = c.subject_id
        WHERE c.subject_id IS NOT NULL
          AND c.confidence >= 0.6
    """)

    # Group by predicate keywords
    predicate_groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        predicate = (row["predicate"] or "").lower()
        # Extract key mechanism words
        key = _extract_mechanism_key(predicate, row["claim_type"])
        if key:
            predicate_groups[key].append({
                "target": row["subject_symbol"],
                "predicate": row["predicate"],
                "claim_type": row["claim_type"],
                "confidence": float(row["confidence"]) if row["confidence"] else 0.5,
                "claim_id": str(row["claim_id"]),
                "source_id": str(row["source_id"]),
            })

    # Find mechanisms shared across different targets
    shared = []
    for mechanism, claims in predicate_groups.items():
        targets = set(c["target"] for c in claims if c["target"])
        if len(targets) >= 2:
            shared.append({
                "mechanism": mechanism,
                "targets": sorted(targets),
                "num_claims": len(claims),
                "claims": claims[:10],  # Top 10
                "avg_confidence": sum(c["confidence"] for c in claims) / len(claims),
            })

    shared.sort(key=lambda x: x["num_claims"], reverse=True)
    logger.info(f"Found {len(shared)} shared mechanisms across targets")
    return shared[:100]


def _extract_mechanism_key(predicate: str, claim_type: str) -> Optional[str]:
    """Extract a mechanism keyword from a predicate for grouping."""
    mechanism_keywords = [
        "splicing", "exon", "intron", "axon", "synap", "endocyt",
        "actin", "ubiquitin", "proteasom", "autophagy", "apoptosis",
        "calcium", "phosphorylat", "transcript", "translat",
        "mitochondri", "oxidative", "inflammat", "neuro",
        "motor neuron", "nmj", "denervat", "regenerat",
        "smn", "survival", "neuroprotect",
    ]
    for kw in mechanism_keywords:
        if kw in predicate:
            return kw
    return claim_type if claim_type != "other" else None


# =============================================================================
# Step 4: Synthesize with Claude
# =============================================================================

SYNTHESIS_PROMPT = """You are analyzing cross-paper connections in SMA (Spinal Muscular Atrophy) research.

Given two targets that appear connected through shared evidence, synthesize a mechanistic explanation
of HOW they might be biologically linked. Focus on molecular pathways, not just correlation.

Target A: {target_a}
Target B: {target_b}
{bridge_info}
Supporting evidence:
{evidence}

Return a JSON object with these fields:
{{"title": "Short descriptive title (max 100 chars)",
 "mechanism": "2-3 sentences explaining the molecular pathway connecting these targets",
 "novelty": "What is non-obvious about this connection? Why wouldn't a researcher reading only papers about target A see this?",
 "testable_prediction": "A specific experiment to validate this connection",
 "confidence": float 0.0-1.0,
 "synthesis_type": "{synthesis_type}"}}

Return ONLY the JSON. No markdown fences."""


async def synthesize_connection(
    target_a: str,
    target_b: str,
    evidence: list[dict],
    bridge_entity: Optional[str] = None,
    synthesis_type: str = COOCCURRENCE,
) -> Optional[dict]:
    """Use Claude to synthesize a cross-paper connection into a card."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("No ANTHROPIC_API_KEY — skipping synthesis")
        return None

    bridge_info = f"Bridge entity: {bridge_entity}" if bridge_entity else ""
    evidence_text = "\n".join(
        f"- [{e.get('claim_type', 'claim')}] {e.get('predicate', 'N/A')} "
        f"(conf: {e.get('confidence', '?')}, source: {e.get('source_title', 'N/A')})"
        for e in evidence[:15]
    )

    prompt = SYNTHESIS_PROMPT.format(
        target_a=target_a,
        target_b=target_b,
        bridge_info=bridge_info,
        evidence=evidence_text,
        synthesis_type=synthesis_type,
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)
    except Exception as e:
        logger.error(f"Synthesis failed for {target_a}↔{target_b}: {e}")
        return None


# =============================================================================
# Step 5: Store Synthesis Cards
# =============================================================================

async def store_card(card: dict, target_a: str, target_b: str,
                     bridge: Optional[str], claim_ids: list[str],
                     source_ids: list[str]) -> Optional[str]:
    """Store a synthesis card in the database."""
    await ensure_table()

    # Check for duplicates
    existing = await fetchval("""
        SELECT id FROM synthesis_cards
        WHERE target_a = $1 AND target_b = $2
          AND synthesis_type = $3
          AND status != 'archived'
    """, target_a, target_b, card.get("synthesis_type", COOCCURRENCE))

    if existing:
        logger.info(f"Card already exists for {target_a}↔{target_b}")
        return str(existing)

    row = await fetchrow("""
        INSERT INTO synthesis_cards (
            title, synthesis_type, target_a, target_b, bridge_entity,
            mechanism, evidence_summary, testable_prediction,
            confidence, novelty_score, supporting_papers,
            claim_ids, source_ids
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::uuid[], $13::uuid[]
        ) RETURNING id
    """,
        card.get("title", f"{target_a}↔{target_b}"),
        card.get("synthesis_type", COOCCURRENCE),
        target_a, target_b, bridge,
        card.get("mechanism", ""),
        card.get("novelty", ""),
        card.get("testable_prediction", ""),
        card.get("confidence", 0.5),
        card.get("novelty_score", 0.0) if "novelty_score" in card else 0.5,
        len(set(source_ids)),
        claim_ids[:50],  # Limit array size
        list(set(source_ids))[:50],
    )
    return str(row["id"]) if row else None


# =============================================================================
# Main Pipeline
# =============================================================================

async def run_synthesis_pipeline(
    max_cards: int = 50,
    synthesize: bool = True,
) -> dict:
    """
    Run the full cross-paper synthesis pipeline.

    1. Build co-occurrence matrix
    2. Find transitive bridges
    3. Find shared mechanisms
    4. (Optional) Synthesize top connections with Claude
    5. Store synthesis cards

    Args:
        max_cards: Maximum cards to generate
        synthesize: Whether to use Claude for synthesis (costs API credits)

    Returns:
        Summary with counts and top connections
    """
    await ensure_table()

    logger.info("Starting cross-paper synthesis pipeline...")

    # Step 1: Co-occurrences
    cooccurrences = await build_cooccurrence_matrix()

    # Score co-occurrences: more shared papers + higher avg confidence = better
    scored_cooccurrences = []
    for (a, b), sources in cooccurrences.items():
        if len(sources) >= 2:  # Only pairs in 2+ papers
            all_claims = [c for s in sources for c in s["claims"]]
            avg_conf = sum(c["confidence"] for c in all_claims) / max(len(all_claims), 1)
            scored_cooccurrences.append({
                "target_a": a, "target_b": b,
                "shared_papers": len(sources),
                "total_claims": len(all_claims),
                "avg_confidence": avg_conf,
                "score": len(sources) * avg_conf,
                "sources": sources,
            })

    scored_cooccurrences.sort(key=lambda x: x["score"], reverse=True)

    # Step 2: Transitive bridges
    bridges = await find_transitive_bridges()

    # Step 3: Shared mechanisms
    shared = await find_shared_mechanisms()

    # Step 4: Synthesize top connections
    cards_created = 0
    if synthesize:
        # Top co-occurrences
        for conn in scored_cooccurrences[:max_cards // 3]:
            evidence = [c for s in conn["sources"] for c in s["claims"]]
            card = await synthesize_connection(
                conn["target_a"], conn["target_b"],
                evidence, synthesis_type=COOCCURRENCE,
            )
            if card:
                claim_ids = [c["claim_id"] for c in evidence if "claim_id" in c]
                source_ids = [s["source_id"] for s in conn["sources"]]
                await store_card(card, conn["target_a"], conn["target_b"],
                                 None, claim_ids, source_ids)
                cards_created += 1

        # Top bridges
        for br in bridges[:max_cards // 3]:
            evidence = [br["a_to_b"], br["b_to_c"]]
            card = await synthesize_connection(
                br["target_a"], br["target_c"],
                evidence, bridge_entity=br["bridge"],
                synthesis_type=TRANSITIVE,
            )
            if card:
                claim_ids = [br["a_to_b"]["claim_id"], br["b_to_c"]["claim_id"]]
                source_ids = [br["a_to_b"]["source_id"], br["b_to_c"]["source_id"]]
                await store_card(card, br["target_a"], br["target_c"],
                                 br["bridge"], claim_ids, source_ids)
                cards_created += 1

    result = {
        "cooccurrences": len(scored_cooccurrences),
        "bridges": len(bridges),
        "shared_mechanisms": len(shared),
        "cards_created": cards_created,
        "top_cooccurrences": [
            {"targets": f"{c['target_a']}↔{c['target_b']}",
             "shared_papers": c["shared_papers"],
             "score": round(c["score"], 2)}
            for c in scored_cooccurrences[:10]
        ],
        "top_bridges": [
            {"path": f"{b['target_a']}→{b['bridge']}→{b['target_c']}",
             "confidence": round(b["combined_confidence"], 3)}
            for b in bridges[:10]
        ],
        "top_mechanisms": [
            {"mechanism": m["mechanism"],
             "targets": m["targets"][:5],
             "claims": m["num_claims"]}
            for m in shared[:10]
        ],
    }

    logger.info(f"Synthesis complete: {cards_created} cards, "
                f"{len(scored_cooccurrences)} co-occurrences, "
                f"{len(bridges)} bridges")
    return result


# =============================================================================
# Query functions
# =============================================================================

async def get_synthesis_cards(
    limit: int = 50,
    offset: int = 0,
    synthesis_type: Optional[str] = None,
    target: Optional[str] = None,
) -> list[dict]:
    """Get synthesis cards with optional filtering."""
    await ensure_table()

    conditions = ["status != 'archived'"]
    params: list[Any] = []
    idx = 1

    if synthesis_type:
        conditions.append(f"synthesis_type = ${idx}")
        params.append(synthesis_type)
        idx += 1

    if target:
        conditions.append(f"(target_a = ${idx} OR target_b = ${idx})")
        params.append(target)
        idx += 1

    where = " AND ".join(conditions)
    params.extend([limit, offset])

    rows = await fetch(f"""
        SELECT * FROM synthesis_cards
        WHERE {where}
        ORDER BY confidence DESC, supporting_papers DESC
        LIMIT ${idx} OFFSET ${idx + 1}
    """, *params)

    return [dict(row) for row in rows]


async def get_synthesis_stats() -> dict:
    """Get synthesis card statistics."""
    await ensure_table()

    total = await fetchval("SELECT COUNT(*) FROM synthesis_cards WHERE status != 'archived'")
    by_type = await fetch("""
        SELECT synthesis_type, COUNT(*) as count
        FROM synthesis_cards WHERE status != 'archived'
        GROUP BY synthesis_type
    """)

    return {
        "total_cards": total or 0,
        "by_type": {row["synthesis_type"]: row["count"] for row in by_type},
    }
