"""Drug-Target Interaction Network — comprehensive connection map."""

from __future__ import annotations
import logging
from fastapi import APIRouter, HTTPException, Query
from ...core.database import fetch, fetchval

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/network", tags=["interaction-network"])


@router.get("/interactions")
async def get_interaction_network(
    min_confidence: float = Query(default=0.0, ge=0, le=1),
):
    """Build the full drug-target interaction network.

    Returns nodes (drugs, targets) and edges (interactions) with evidence counts.
    Combines: graph_edges, ChEMBL bioactivity (molecule_screenings), claims,
    and screening funnel results.
    """
    # 1. Get all targets
    targets = await fetch("SELECT id, symbol, name, target_type FROM targets")

    # 2. Get all drugs
    drugs = await fetch("SELECT id, name, drug_type, approval_status FROM drugs")

    # 3. Get claim-based interactions (target <-> target, drug -> target)
    edges_claims = await fetch("""
        SELECT c.subject_id, c.subject_type, c.object_id, c.object_type,
               c.claim_type, COUNT(*) as claim_count,
               AVG(c.confidence) as avg_confidence
        FROM claims c
        WHERE c.subject_id IS NOT NULL AND c.object_id IS NOT NULL
          AND c.confidence >= $1
        GROUP BY c.subject_id, c.subject_type, c.object_id, c.object_type, c.claim_type
        HAVING COUNT(*) >= 2
        ORDER BY COUNT(*) DESC
        LIMIT 200
    """, min_confidence)

    # 4. Get top screening hits from molecule_screenings
    screening_edges = await fetch("""
        SELECT DISTINCT target_symbol, smiles, pchembl_value, compound_name
        FROM molecule_screenings
        WHERE drug_likeness_pass = TRUE AND pchembl_value > 0
        ORDER BY pchembl_value DESC
        LIMIT 100
    """)

    # 5. Get knowledge graph edges
    graph_edges = await fetch("""
        SELECT src_id, dst_id, relation, confidence, direction, effect
        FROM graph_edges
        ORDER BY confidence DESC
        LIMIT 200
    """)

    # Build node list
    nodes = []
    node_ids = set()

    for t in targets:
        nid = str(t["id"])
        nodes.append({
            "id": nid,
            "label": t["symbol"],
            "name": t.get("name", ""),
            "type": "target",
            "subtype": t.get("target_type", "gene"),
        })
        node_ids.add(nid)

    for d in drugs:
        nid = str(d["id"])
        nodes.append({
            "id": nid,
            "label": d["name"],
            "type": "drug",
            "subtype": d.get("drug_type", ""),
            "status": d.get("approval_status", ""),
        })
        node_ids.add(nid)

    # Build edge list
    edges = []

    for e in edges_claims:
        sid = str(e["subject_id"])
        oid = str(e["object_id"])
        if sid in node_ids and oid in node_ids:
            edges.append({
                "source": sid,
                "target": oid,
                "type": e["claim_type"],
                "evidence": "claims",
                "claim_count": e["claim_count"],
                "confidence": round(float(e["avg_confidence"]), 2) if e["avg_confidence"] else 0,
            })

    for se in screening_edges:
        edges.append({
            "source": se.get("compound_name") or se["smiles"],
            "target": se["target_symbol"],
            "type": "screening_hit",
            "evidence": "molecule_screening",
            "confidence": round(float(se["pchembl_value"]) / 10, 3) if se["pchembl_value"] else 0,
        })

    for ge in graph_edges:
        sid = str(ge["src_id"])
        tid = str(ge["dst_id"])
        if sid in node_ids and tid in node_ids:
            edges.append({
                "source": sid,
                "target": tid,
                "type": ge.get("relation", ""),
                "evidence": "knowledge_graph",
                "confidence": float(ge["confidence"]) if ge.get("confidence") else 0,
                "direction": ge.get("direction", ""),
                "effect": ge.get("effect", ""),
            })

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes": len(nodes),
            "targets": len(targets),
            "drugs": len(drugs),
            "total_edges": len(edges),
            "claim_edges": len(edges_claims),
            "screening_edges": len(screening_edges),
            "graph_edges": len(graph_edges),
        },
    }


@router.get("/interactions/target/{symbol}")
async def get_target_interactions(symbol: str):
    """Get all interactions for a specific target."""
    sym = symbol.upper()
    target = await fetch("SELECT id, symbol, name FROM targets WHERE symbol = $1", sym)
    if not target:
        raise HTTPException(404, detail=f"Target {sym} not found")

    tid = target[0]["id"]

    # Claims involving this target
    claims = await fetch("""
        SELECT c.claim_type, COUNT(*) as cnt,
               AVG(c.confidence) as avg_conf
        FROM claims c
        WHERE c.subject_id = $1 OR c.object_id = $1
        GROUP BY c.claim_type
        ORDER BY cnt DESC
    """, tid)

    # Connected targets via knowledge graph
    connected = await fetch("""
        SELECT t.symbol, ge.relation, ge.confidence, ge.effect
        FROM graph_edges ge
        JOIN targets t ON (t.id = ge.dst_id OR t.id = ge.src_id)
        WHERE (ge.src_id = $1 OR ge.dst_id = $1)
          AND t.id != $1
        ORDER BY ge.confidence DESC
        LIMIT 20
    """, tid)

    # Screening hits for this target symbol
    hits = await fetch("""
        SELECT smiles, pchembl_value, compound_name
        FROM molecule_screenings
        WHERE target_symbol = $1 AND drug_likeness_pass = TRUE
        ORDER BY pchembl_value DESC NULLS LAST
        LIMIT 20
    """, sym)

    return {
        "target": sym,
        "claim_types": [{"type": c["claim_type"], "count": c["cnt"],
                        "avg_confidence": round(float(c["avg_conf"]), 2) if c["avg_conf"] else 0}
                       for c in claims],
        "connected_targets": [{"symbol": c["symbol"], "relation": c["relation"],
                              "confidence": float(c["confidence"]) if c.get("confidence") else 0,
                              "effect": c.get("effect", "")}
                             for c in connected],
        "screening_hits": [{"smiles": h["smiles"],
                           "compound": h.get("compound_name", ""),
                           "pchembl": round(float(h["pchembl_value"]), 2) if h["pchembl_value"] else 0}
                          for h in hits],
    }
