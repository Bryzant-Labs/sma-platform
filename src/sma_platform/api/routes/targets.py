"""Target (gene/protein/pathway) endpoints."""

from __future__ import annotations

import json
import re
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...core.database import execute, fetch, fetchrow
from ..auth import require_admin_key

router = APIRouter()

MAX_LIMIT = 2000


class TargetCreate(BaseModel):
    symbol: str
    name: str | None = None
    target_type: str = "gene"
    organism: str = "Homo sapiens"
    identifiers: dict[str, Any] = {}
    description: str | None = None


@router.get("/targets")
async def list_targets(
    target_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    if target_type:
        rows = await fetch(
            "SELECT * FROM targets WHERE target_type = $1 ORDER BY symbol LIMIT $2 OFFSET $3",
            target_type, limit, offset,
        )
    else:
        rows = await fetch(
            "SELECT * FROM targets ORDER BY symbol LIMIT $1 OFFSET $2",
            limit, offset,
        )
    return [dict(r) for r in rows]


@router.get("/targets/{target_id}")
async def get_target(target_id: UUID):
    row = await fetchrow("SELECT * FROM targets WHERE id = $1", target_id)
    if not row:
        raise HTTPException(404, "Target not found")
    return dict(row)


@router.get("/targets/symbol/{symbol}")
async def get_target_by_symbol(symbol: str):
    row = await fetchrow("SELECT * FROM targets WHERE symbol = $1", symbol.upper())
    if not row:
        raise HTTPException(404, f"Target '{symbol}' not found")
    return dict(row)


@router.get("/targets/{target_id}/deep-dive")
async def get_target_deep_dive(target_id: str):
    """Get comprehensive view of a target: claims, hypotheses, drugs, trials, network edges."""
    if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', target_id, re.I):
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    target = await fetchrow("SELECT * FROM targets WHERE id = $1", target_id)
    if not target:
        raise HTTPException(404, "Target not found")
    target = dict(target)
    symbol = target["symbol"]
    tid = str(target["id"])

    # Claims mentioning this target (via subject_id / object_id foreign keys)
    claims = await fetch(
        """SELECT * FROM (
               SELECT DISTINCT ON (c.id) c.id, c.claim_number, c.claim_type, c.predicate, c.confidence,
                      c.metadata, s.title AS source_title, s.external_id AS pmid
               FROM claims c
               LEFT JOIN evidence e ON e.claim_id = c.id
               LEFT JOIN sources s ON e.source_id = s.id
               WHERE c.subject_id = $1 OR c.object_id = $1
               ORDER BY c.id, s.title NULLS LAST
           ) sub
           ORDER BY confidence DESC NULLS LAST
           LIMIT 50""",
        target["id"],
    )

    # Hypotheses for this target (search by symbol in title/description)
    hypotheses = await fetch(
        """SELECT id, hypothesis_type, title, description, confidence, status, metadata
           FROM hypotheses WHERE title ILIKE $1 OR description ILIKE $1
           ORDER BY confidence DESC LIMIT 20""",
        f'%{symbol}%',
    )

    # Drugs targeting this target
    drugs = await fetch(
        """SELECT id, name, brand_names, drug_type, mechanism, approval_status
           FROM drugs WHERE CAST(targets AS TEXT) LIKE $1
           ORDER BY approval_status LIMIT 20""",
        f'%{symbol}%',
    )

    # Graph edges involving this target
    edges = await fetch(
        """SELECT id, src_id, dst_id, relation, direction, confidence, metadata
           FROM graph_edges WHERE src_id = $1 OR dst_id = $1
           ORDER BY confidence DESC LIMIT 50""",
        tid,
    )

    # Resolve edge partner symbols
    edge_partner_ids = set()
    for e in edges:
        e = dict(e)
        partner = e["dst_id"] if str(e["src_id"]) == tid else e["src_id"]
        edge_partner_ids.add(str(partner))
    partner_symbols = {}
    if edge_partner_ids:
        id_list = list(edge_partner_ids)
        partner_rows = await fetch(
            "SELECT id, symbol FROM targets WHERE CAST(id AS TEXT) IN (" + ",".join(f"${i+1}" for i in range(len(id_list))) + ")",
            *id_list,
        )
        partner_symbols = {str(r["id"]): r["symbol"] for r in partner_rows}

    edges_out = []
    for e in edges:
        e = dict(e)
        partner_id = str(e["dst_id"]) if str(e["src_id"]) == tid else str(e["src_id"])
        e["partner_symbol"] = partner_symbols.get(partner_id, "?")
        meta = e.get("metadata")
        if isinstance(meta, str):
            try:
                e["metadata"] = json.loads(meta)
            except (json.JSONDecodeError, TypeError):
                pass
        edges_out.append(e)

    return {
        "target": target,
        "claims": [dict(c) for c in claims],
        "claims_count": len(claims),
        "hypotheses": [dict(h) for h in hypotheses],
        "hypotheses_count": len(hypotheses),
        "drugs": [dict(d) for d in drugs],
        "drugs_count": len(drugs),
        "edges": edges_out,
        "edges_count": len(edges_out),
    }


@router.get("/graph/full")
async def get_full_graph():
    """Get all nodes and edges for knowledge graph visualization."""
    targets = await fetch("SELECT id, symbol, name, target_type FROM targets ORDER BY symbol")
    edges = await fetch(
        """SELECT src_id, dst_id, relation, confidence, metadata
           FROM graph_edges ORDER BY confidence DESC LIMIT 5000"""
    )

    nodes = []
    for t in targets:
        t = dict(t)
        nodes.append({
            "id": str(t["id"]),
            "symbol": t["symbol"],
            "name": t["name"],
            "type": t["target_type"],
        })

    links = []
    for e in edges:
        e = dict(e)
        meta = e.get("metadata")
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except (json.JSONDecodeError, TypeError):
                meta = {}
        links.append({
            "source": str(e["src_id"]),
            "target": str(e["dst_id"]),
            "relation": e["relation"],
            "confidence": e["confidence"],
            "chembl_id": meta.get("molecule_chembl_id", "") if meta else "",
        })

    return {"nodes": nodes, "links": links}


@router.post("/targets", status_code=201, dependencies=[Depends(require_admin_key)])
async def create_target(body: TargetCreate):
    await execute(
        """INSERT INTO targets (symbol, name, target_type, organism, identifiers, description)
           VALUES ($1, $2, $3, $4, $5, $6)
           ON CONFLICT (symbol, target_type, organism) DO UPDATE
           SET name = EXCLUDED.name, identifiers = EXCLUDED.identifiers, description = EXCLUDED.description,
               updated_at = CURRENT_TIMESTAMP""",
        body.symbol.upper(), body.name, body.target_type, body.organism,
        json.dumps(body.identifiers), body.description,
    )
    row = await fetchrow(
        "SELECT * FROM targets WHERE symbol = $1 AND target_type = $2 AND organism = $3",
        body.symbol.upper(), body.target_type, body.organism,
    )
    if not row:
        raise HTTPException(500, "Failed to create target")
    return dict(row)
