"""Knowledge graph API — nodes, edges, and visualization data."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query

from ...core.database import fetch, fetchrow

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/graph")
async def get_graph(
    include_compounds: bool = Query(default=False, description="Include compound bioactivity edges"),
    limit: int = Query(default=500, ge=1, le=5000),
):
    """Return knowledge graph as nodes + edges for visualization.

    By default excludes compound_bioactivity edges (191 edges) to keep
    the graph focused on biological relationships.
    """
    # Build edge query
    if include_compounds:
        edge_query = """
            SELECT e.src_id, e.dst_id, e.relation, e.confidence, e.direction, e.effect
            FROM graph_edges e
            ORDER BY e.created_at DESC
            LIMIT $1
        """
    else:
        edge_query = """
            SELECT e.src_id, e.dst_id, e.relation, e.confidence, e.direction, e.effect
            FROM graph_edges e
            WHERE e.relation NOT LIKE 'compound_bioactivity%'
            ORDER BY e.created_at DESC
            LIMIT $1
        """

    edges_raw = await fetch(edge_query, limit)

    # Collect unique node IDs from edges
    node_ids = set()
    for e in edges_raw:
        node_ids.add(str(e["src_id"]))
        node_ids.add(str(e["dst_id"]))

    # Fetch target info for all node IDs
    targets = await fetch("SELECT id, symbol, name, target_type FROM targets")
    target_map = {str(t["id"]): t for t in targets}

    # Build nodes list
    nodes = []
    seen_nodes = set()
    for nid in node_ids:
        if nid in seen_nodes:
            continue
        seen_nodes.add(nid)
        t = target_map.get(nid)
        if t:
            nodes.append({
                "id": nid,
                "symbol": t["symbol"],
                "name": t["name"],
                "type": t["target_type"],
            })
        else:
            nodes.append({
                "id": nid,
                "symbol": nid[:8],
                "name": None,
                "type": "unknown",
            })

    # Build edges list
    edges = []
    for e in edges_raw:
        rel = e["relation"]
        # Simplify compound_bioactivity:CHEMBL123 to compound_bioactivity
        if rel.startswith("compound_bioactivity"):
            rel = "compound_bioactivity"
        edges.append({
            "source": str(e["src_id"]),
            "target": str(e["dst_id"]),
            "relation": rel,
            "confidence": float(e["confidence"]) if e["confidence"] else None,
            "direction": e["direction"],
            "effect": e["effect"],
        })

    # Aggregate edge types for legend
    edge_types = {}
    for e in edges:
        r = e["relation"]
        edge_types[r] = edge_types.get(r, 0) + 1

    return {
        "nodes": nodes,
        "edges": edges,
        "edge_types": edge_types,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
    }


@router.get("/graph/stats")
async def graph_stats():
    """Summary statistics for the knowledge graph."""
    total_edges = await fetchrow("SELECT COUNT(*) as cnt FROM graph_edges")
    bio_edges = await fetchrow(
        "SELECT COUNT(*) as cnt FROM graph_edges WHERE relation NOT LIKE 'compound_bioactivity%'"
    )
    compound_edges = await fetchrow(
        "SELECT COUNT(*) as cnt FROM graph_edges WHERE relation LIKE 'compound_bioactivity%'"
    )

    # Edge type breakdown
    types_raw = await fetch("""
        SELECT
            CASE WHEN relation LIKE 'compound_bioactivity%' THEN 'compound_bioactivity'
                 ELSE relation END as rel_type,
            COUNT(*) as cnt
        FROM graph_edges
        GROUP BY rel_type
        ORDER BY cnt DESC
    """)

    edge_breakdown = {r["rel_type"]: r["cnt"] for r in types_raw}

    # Node stats
    total_targets = await fetchrow("SELECT COUNT(*) as cnt FROM targets")

    return {
        "total_edges": total_edges["cnt"] if total_edges else 0,
        "biological_edges": bio_edges["cnt"] if bio_edges else 0,
        "compound_edges": compound_edges["cnt"] if compound_edges else 0,
        "total_nodes": total_targets["cnt"] if total_targets else 0,
        "edge_breakdown": edge_breakdown,
    }
