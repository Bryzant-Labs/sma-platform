"""Knowledge graph expansion — auto-create edges from evidence.

Scans claims, drug outcomes, and cross-species data to discover
relationships between targets that aren't yet in the graph.

Edge sources:
1. Claims with both subject_id and object_id → target↔target edges
2. Drug outcomes mentioning known targets → therapeutic relationship edges
3. Cross-species conservation co-occurrence → co_conserved edges
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from ..core.database import execute, fetch, fetchrow

logger = logging.getLogger(__name__)

# Map claim types to graph edge relations
CLAIM_TYPE_TO_RELATION = {
    "gene_expression": "regulates",
    "protein_interaction": "interacts_with",
    "pathway_membership": "part_of_pathway",
    "drug_target": "targeted_by",
    "drug_efficacy": "therapeutic_for",
    "biomarker": "biomarker_for",
    "splicing_event": "splicing_modifier",
    "neuroprotection": "neuroprotective",
    "motor_function": "motor_function",
    "survival": "survival_effect",
    "safety": "safety_signal",
    "other": "associated_with",
}

# Map claim types to edge effects
CLAIM_TYPE_TO_EFFECT = {
    "gene_expression": "activates",
    "protein_interaction": "associates",
    "pathway_membership": "associates",
    "drug_target": "inhibits",
    "drug_efficacy": "activates",
    "biomarker": "associates",
    "splicing_event": "activates",
    "neuroprotection": "activates",
    "motor_function": "activates",
    "survival": "activates",
    "safety": "inhibits",
    "other": "unknown",
}

# Known drug → target mappings for creating drug-mediated edges
DRUG_TARGET_MAP = {
    "nusinersen": "SMN2",
    "spinraza": "SMN2",
    "risdiplam": "SMN2",
    "evrysdi": "SMN2",
    "branaplam": "SMN2",
    "onasemnogene": "SMN1",
    "onasemnogene abeparvovec": "SMN1",
    "zolgensma": "SMN1",
    "apitegromab": "SMN_PROTEIN",
    "reldesemtiv": "NMJ_MATURATION",
}


async def expand_from_claims() -> dict:
    """Create graph edges from claims that link two targets.

    Finds claims where both subject_id and object_id are set
    and point to different targets. Creates an edge for each
    unique target pair + relation.
    """
    rows = await fetch(
        """SELECT c.id, c.claim_type, c.subject_id, c.object_id, c.confidence
           FROM claims c
           WHERE c.subject_id IS NOT NULL
             AND c.object_id IS NOT NULL
             AND c.subject_id != c.object_id"""
    )

    created = 0
    skipped = 0

    for row in rows:
        r = dict(row)
        claim_type = r.get("claim_type", "other")
        relation = CLAIM_TYPE_TO_RELATION.get(claim_type, "associated_with")
        effect = CLAIM_TYPE_TO_EFFECT.get(claim_type, "unknown")

        result = await execute(
            """INSERT INTO graph_edges (src_id, dst_id, relation, direction, effect, confidence, metadata)
               VALUES ($1, $2, $3, $4, $5, $6, $7)
               ON CONFLICT (src_id, dst_id, relation) DO UPDATE
               SET confidence = GREATEST(graph_edges.confidence, EXCLUDED.confidence),
                   metadata = EXCLUDED.metadata""",
            r["subject_id"],
            r["object_id"],
            relation,
            "src_to_dst",
            effect,
            r.get("confidence", 0.5),
            json.dumps({
                "source": "claim_expansion",
                "claim_id": str(r["id"]),
                "claim_type": claim_type,
                "expanded_at": datetime.now(timezone.utc).isoformat(),
            }),
        )
        # ON CONFLICT DO UPDATE returns "UPDATE" not "INSERT" when the row exists
        if "INSERT" in str(result):
            created += 1
        else:
            skipped += 1

    logger.info("Claim-based edges: %d created, %d skipped (already exist)", created, skipped)
    return {"claim_edges_created": created, "claim_edges_skipped": skipped}


async def expand_from_drug_outcomes() -> dict:
    """Create edges from drug outcome data.

    When a drug outcome mentions a target that maps to a known
    target in our DB, create an edge between that target and
    the drug's primary target.
    """
    # Load all target symbols → IDs
    targets = await fetch("SELECT id, symbol FROM targets")
    symbol_to_id = {dict(t)["symbol"]: str(dict(t)["id"]) for t in targets}

    # Get all drug outcomes with target info
    rows = await fetch(
        "SELECT DISTINCT compound_name, target, outcome, mechanism FROM drug_outcomes"
    )

    created = 0
    skipped = 0

    for row in rows:
        r = dict(row)
        compound = (r.get("compound_name") or "").lower().strip()
        outcome_target = (r.get("target") or "").upper().strip()

        # Find the drug's primary target
        drug_target_symbol = DRUG_TARGET_MAP.get(compound)
        if not drug_target_symbol:
            continue

        drug_target_id = symbol_to_id.get(drug_target_symbol)
        if not drug_target_id:
            continue

        # Find the outcome's mentioned target
        outcome_target_id = symbol_to_id.get(outcome_target)
        if not outcome_target_id or outcome_target_id == drug_target_id:
            continue

        # Determine relation based on outcome
        outcome_val = (r.get("outcome") or "").lower()
        if outcome_val in ("success", "partial_success"):
            relation = "therapeutic_synergy"
            effect = "activates"
        elif outcome_val in ("failure", "discontinued"):
            relation = "therapeutic_failure"
            effect = "inhibits"
        else:
            relation = "drug_interaction"
            effect = "unknown"

        result = await execute(
            """INSERT INTO graph_edges (src_id, dst_id, relation, direction, effect, confidence, metadata)
               VALUES ($1, $2, $3, $4, $5, $6, $7)
               ON CONFLICT (src_id, dst_id, relation) DO UPDATE
               SET confidence = GREATEST(graph_edges.confidence, EXCLUDED.confidence)""",
            drug_target_id,
            outcome_target_id,
            relation,
            "src_to_dst",
            effect,
            0.7,
            json.dumps({
                "source": "drug_outcome_expansion",
                "compound": compound,
                "outcome": outcome_val,
                "expanded_at": datetime.now(timezone.utc).isoformat(),
            }),
        )
        if "INSERT" in str(result):
            created += 1
        else:
            skipped += 1

    logger.info("Drug outcome edges: %d created, %d skipped", created, skipped)
    return {"drug_outcome_edges_created": created, "drug_outcome_edges_skipped": skipped}


async def expand_from_conservation() -> dict:
    """Create co_conserved edges between targets sharing species conservation.

    If two human targets both have orthologs in the same model organism,
    they may share evolutionary pathways worth investigating.
    """
    # Find pairs of targets conserved in ≥2 of the same species
    rows = await fetch(
        """SELECT a.human_symbol AS sym_a, b.human_symbol AS sym_b,
                  COUNT(DISTINCT a.species) AS shared_species
           FROM cross_species_targets a
           JOIN cross_species_targets b
             ON a.species = b.species AND a.human_symbol < b.human_symbol
           GROUP BY a.human_symbol, b.human_symbol
           HAVING COUNT(DISTINCT a.species) >= 2"""
    )

    # Load target IDs
    targets = await fetch("SELECT id, symbol FROM targets")
    symbol_to_id = {dict(t)["symbol"]: str(dict(t)["id"]) for t in targets}

    created = 0
    skipped = 0

    for row in rows:
        r = dict(row)
        src_id = symbol_to_id.get(r["sym_a"])
        dst_id = symbol_to_id.get(r["sym_b"])
        if not src_id or not dst_id:
            continue

        shared = r["shared_species"]
        confidence = min(1.0, shared / 5.0)  # 5 species = max confidence

        await execute(
            """INSERT INTO graph_edges (src_id, dst_id, relation, direction, effect, confidence, metadata)
               VALUES ($1, $2, $3, $4, $5, $6, $7)
               ON CONFLICT (src_id, dst_id, relation) DO UPDATE
               SET confidence = GREATEST(graph_edges.confidence, EXCLUDED.confidence)""",
            src_id,
            dst_id,
            "co_conserved",
            "undirected",
            "associates",
            confidence,
            json.dumps({
                "source": "cross_species_conservation",
                "shared_species_count": shared,
                "sym_a": r["sym_a"],
                "sym_b": r["sym_b"],
                "expanded_at": datetime.now(timezone.utc).isoformat(),
            }),
        )
        if "INSERT" in str(result):
            created += 1
        else:
            skipped += 1

    logger.info("Conservation edges: %d created, %d skipped", created, skipped)
    return {"conservation_edges_created": created, "conservation_edges_skipped": skipped}


async def expand_graph() -> dict:
    """Run all graph expansion strategies and return combined results."""
    logger.info("Starting knowledge graph expansion...")

    results = {}

    # 1. Claim-based edges
    claim_result = await expand_from_claims()
    results.update(claim_result)

    # 2. Drug outcome edges
    drug_result = await expand_from_drug_outcomes()
    results.update(drug_result)

    # 3. Cross-species conservation edges
    cons_result = await expand_from_conservation()
    results.update(cons_result)

    # Get final edge count
    total = await fetchrow("SELECT COUNT(*) as cnt FROM graph_edges")
    results["total_edges"] = total["cnt"] if total else 0

    total_created = (
        claim_result.get("claim_edges_created", 0)
        + drug_result.get("drug_outcome_edges_created", 0)
        + cons_result.get("conservation_edges_created", 0)
    )
    results["total_new_edges"] = total_created

    logger.info(
        "Graph expansion complete: %d new edges (total: %d)",
        total_created,
        results["total_edges"],
    )
    return results
