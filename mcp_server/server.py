"""SMA Research Platform — MCP Server.

Exposes the SMA knowledge base (SQLite) to Claude via Model Context Protocol.
Uses FastMCP pattern with aiosqlite for async database access.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import aiosqlite
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).resolve().parent.parent / "sma_platform.db"

mcp = FastMCP(
    "SMA Knowledge Base",
    description=(
        "Query the SMA (Spinal Muscular Atrophy) research knowledge base. "
        "Contains targets, drugs, trials, claims, evidence, hypotheses, "
        "and ingestion history from PubMed, ClinicalTrials.gov, and GEO."
    ),
)

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


async def _get_db() -> aiosqlite.Connection:
    """Open a read-only connection with row-factory enabled."""
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def _fetch_all(query: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Run a SELECT and return all rows as dicts."""
    db = await _get_db()
    try:
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        if not rows:
            return []
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    finally:
        await db.close()


async def _fetch_one(query: str, params: tuple = ()) -> dict[str, Any] | None:
    """Run a SELECT and return one row as a dict, or None."""
    db = await _get_db()
    try:
        cursor = await db.execute(query, params)
        row = await cursor.fetchone()
        if not row:
            return None
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    finally:
        await db.close()


async def _fetch_val(query: str, params: tuple = ()) -> Any:
    """Run a SELECT and return the first column of the first row."""
    db = await _get_db()
    try:
        cursor = await db.execute(query, params)
        row = await cursor.fetchone()
        return row[0] if row else None
    finally:
        await db.close()


def _safe_json(value: Any) -> Any:
    """Parse a JSON string field, returning the parsed value or the original."""
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return value
    return value


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_platform_stats() -> dict[str, Any]:
    """Get counts of all entities in the SMA knowledge base.

    Returns a summary with total counts per table: sources, targets, drugs,
    trials, datasets, claims, evidence, hypotheses, graph_edges, ingestion_log.
    """
    tables = [
        "sources", "targets", "drugs", "trials", "datasets",
        "claims", "evidence", "hypotheses", "graph_edges", "ingestion_log",
    ]
    counts: dict[str, int] = {}
    for table in tables:
        count = await _fetch_val(f"SELECT COUNT(*) FROM {table}")  # noqa: S608 — table names are hardcoded
        counts[table] = count or 0

    total = sum(counts.values())
    return {"entity_counts": counts, "total_records": total, "db_path": str(DB_PATH)}


@mcp.tool()
async def get_targets(target_type: Optional[str] = None) -> list[dict[str, Any]]:
    """List all molecular targets (genes, proteins, pathways, phenotypes).

    Args:
        target_type: Optional filter — one of: gene, protein, pathway,
                     cell_state, phenotype, other.
    """
    if target_type:
        rows = await _fetch_all(
            "SELECT id, symbol, name, target_type, organism, identifiers, description, created_at "
            "FROM targets WHERE target_type = ? ORDER BY symbol",
            (target_type,),
        )
    else:
        rows = await _fetch_all(
            "SELECT id, symbol, name, target_type, organism, identifiers, description, created_at "
            "FROM targets ORDER BY symbol"
        )
    for row in rows:
        row["identifiers"] = _safe_json(row.get("identifiers"))
    return rows


@mcp.tool()
async def get_target_detail(symbol: str) -> dict[str, Any]:
    """Get full details for a target by its symbol, including related claims count.

    Args:
        symbol: The target symbol (e.g. SMN1, SMN2, STMN2, PLS3).
    """
    target = await _fetch_one(
        "SELECT * FROM targets WHERE symbol = ?",
        (symbol,),
    )
    if not target:
        return {"error": f"Target '{symbol}' not found"}

    target["identifiers"] = _safe_json(target.get("identifiers"))
    target["metadata"] = _safe_json(target.get("metadata"))

    # Count claims where this target is subject or object
    claims_as_subject = await _fetch_val(
        "SELECT COUNT(*) FROM claims WHERE subject_id = ?",
        (target["id"],),
    )
    claims_as_object = await _fetch_val(
        "SELECT COUNT(*) FROM claims WHERE object_id = ?",
        (target["id"],),
    )

    # Count graph edges
    edges_out = await _fetch_val(
        "SELECT COUNT(*) FROM graph_edges WHERE src_id = ?",
        (target["id"],),
    )
    edges_in = await _fetch_val(
        "SELECT COUNT(*) FROM graph_edges WHERE dst_id = ?",
        (target["id"],),
    )

    target["claims_as_subject"] = claims_as_subject or 0
    target["claims_as_object"] = claims_as_object or 0
    target["graph_edges_outgoing"] = edges_out or 0
    target["graph_edges_incoming"] = edges_in or 0

    return target


@mcp.tool()
async def get_claims(
    target_symbol: Optional[str] = None,
    claim_type: Optional[str] = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Query claims (factual assertions) from the evidence graph.

    Args:
        target_symbol: Optional — filter claims where this target is subject or object.
        claim_type: Optional — one of: gene_expression, protein_interaction,
                    pathway_membership, drug_target, drug_efficacy, biomarker,
                    splicing_event, neuroprotection, motor_function, survival, safety, other.
        limit: Max results (default 50).
    """
    conditions: list[str] = []
    params: list[Any] = []

    if target_symbol:
        conditions.append(
            "(c.subject_id IN (SELECT id FROM targets WHERE symbol = ?) "
            "OR c.object_id IN (SELECT id FROM targets WHERE symbol = ?))"
        )
        params.extend([target_symbol, target_symbol])

    if claim_type:
        conditions.append("c.claim_type = ?")
        params.append(claim_type)

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    params.append(limit)

    rows = await _fetch_all(
        f"SELECT c.id, c.claim_type, c.subject_id, c.subject_type, "
        f"c.predicate, c.object_id, c.object_type, c.value, c.confidence, "
        f"c.created_at, "
        f"(SELECT COUNT(*) FROM evidence e WHERE e.claim_id = c.id) AS evidence_count "
        f"FROM claims c {where} "
        f"ORDER BY c.confidence DESC, c.created_at DESC LIMIT ?",
        tuple(params),
    )
    for row in rows:
        row["metadata"] = None  # omit for brevity
    return rows


@mcp.tool()
async def get_hypotheses(
    status: Optional[str] = None,
    min_confidence: Optional[float] = None,
) -> list[dict[str, Any]]:
    """Query hypotheses generated by the reasoning layer.

    Args:
        status: Optional filter — one of: proposed, under_review, validated, refuted, published.
        min_confidence: Optional minimum confidence threshold (0.0 to 1.0).
    """
    conditions: list[str] = []
    params: list[Any] = []

    if status:
        conditions.append("status = ?")
        params.append(status)

    if min_confidence is not None:
        conditions.append("confidence >= ?")
        params.append(min_confidence)

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    rows = await _fetch_all(
        f"SELECT id, title, description, target_ids, supporting_evidence, "
        f"contradicting_evidence, confidence, status, metadata, created_at, updated_at "
        f"FROM hypotheses {where} "
        f"ORDER BY confidence DESC, created_at DESC",
        tuple(params),
    )
    for row in rows:
        row["target_ids"] = _safe_json(row.get("target_ids"))
        row["supporting_evidence"] = _safe_json(row.get("supporting_evidence"))
        row["contradicting_evidence"] = _safe_json(row.get("contradicting_evidence"))
        row["metadata"] = _safe_json(row.get("metadata"))
    return rows


@mcp.tool()
async def get_sources(limit: int = 50) -> list[dict[str, Any]]:
    """List papers and data sources in the knowledge base.

    Args:
        limit: Max results (default 50).
    """
    rows = await _fetch_all(
        "SELECT id, source_type, external_id, title, authors, journal, "
        "pub_date, doi, url, created_at "
        "FROM sources ORDER BY pub_date DESC, created_at DESC LIMIT ?",
        (limit,),
    )
    for row in rows:
        row["authors"] = _safe_json(row.get("authors"))
    return rows


@mcp.tool()
async def get_evidence_chain(claim_id: str) -> dict[str, Any]:
    """Get the full evidence chain for a claim: claim -> evidence -> source.

    Args:
        claim_id: The UUID of the claim to trace.
    """
    claim = await _fetch_one(
        "SELECT * FROM claims WHERE id = ?",
        (claim_id,),
    )
    if not claim:
        return {"error": f"Claim '{claim_id}' not found"}

    claim["metadata"] = _safe_json(claim.get("metadata"))

    evidence_rows = await _fetch_all(
        "SELECT e.id, e.source_id, e.excerpt, e.figure_ref, e.method, "
        "e.sample_size, e.p_value, e.effect_size, e.created_at, "
        "s.title AS source_title, s.source_type, s.external_id, "
        "s.journal, s.pub_date, s.doi, s.url "
        "FROM evidence e "
        "JOIN sources s ON e.source_id = s.id "
        "WHERE e.claim_id = ? "
        "ORDER BY e.created_at",
        (claim_id,),
    )

    # Resolve subject/object names if they are targets
    subject_name = None
    object_name = None
    if claim.get("subject_id") and claim.get("subject_type") == "target":
        subject_name = await _fetch_val(
            "SELECT symbol FROM targets WHERE id = ?", (claim["subject_id"],)
        )
    if claim.get("object_id") and claim.get("object_type") == "target":
        object_name = await _fetch_val(
            "SELECT symbol FROM targets WHERE id = ?", (claim["object_id"],)
        )

    return {
        "claim": claim,
        "subject_name": subject_name,
        "object_name": object_name,
        "evidence": evidence_rows,
        "evidence_count": len(evidence_rows),
    }


@mcp.tool()
async def search_claims(query: str) -> list[dict[str, Any]]:
    """Full-text search on claim predicates and values.

    Args:
        query: Search term (matched with LIKE on predicate and value fields).
    """
    like_pattern = f"%{query}%"
    rows = await _fetch_all(
        "SELECT c.id, c.claim_type, c.subject_id, c.subject_type, "
        "c.predicate, c.object_id, c.object_type, c.value, c.confidence, "
        "c.created_at, "
        "(SELECT COUNT(*) FROM evidence e WHERE e.claim_id = c.id) AS evidence_count "
        "FROM claims c "
        "WHERE c.predicate LIKE ? OR c.value LIKE ? "
        "ORDER BY c.confidence DESC LIMIT 50",
        (like_pattern, like_pattern),
    )
    return rows


@mcp.tool()
async def get_ingestion_history(limit: int = 10) -> list[dict[str, Any]]:
    """Get recent data ingestion runs (PubMed, ClinicalTrials.gov, GEO imports).

    Args:
        limit: Max results (default 10).
    """
    rows = await _fetch_all(
        "SELECT id, source_type, query, items_found, items_new, items_updated, "
        "errors, run_at, duration_secs "
        "FROM ingestion_log ORDER BY run_at DESC LIMIT ?",
        (limit,),
    )
    for row in rows:
        row["errors"] = _safe_json(row.get("errors"))
    return rows


@mcp.tool()
async def get_drugs(approval_status: Optional[str] = None) -> list[dict[str, Any]]:
    """List drugs and therapies for SMA.

    Args:
        approval_status: Optional filter — one of: approved, phase3, phase2,
                         phase1, preclinical, discontinued, investigational.
    """
    if approval_status:
        rows = await _fetch_all(
            "SELECT id, name, brand_names, drug_type, mechanism, "
            "approval_status, approved_for, manufacturer, created_at "
            "FROM drugs WHERE approval_status = ? ORDER BY name",
            (approval_status,),
        )
    else:
        rows = await _fetch_all(
            "SELECT id, name, brand_names, drug_type, mechanism, "
            "approval_status, approved_for, manufacturer, created_at "
            "FROM drugs ORDER BY name"
        )
    for row in rows:
        row["brand_names"] = _safe_json(row.get("brand_names"))
        row["approved_for"] = _safe_json(row.get("approved_for"))
    return rows


@mcp.tool()
async def get_trials(
    status: Optional[str] = None,
    phase: Optional[str] = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List clinical trials for SMA therapies.

    Args:
        status: Optional filter on trial status (e.g. recruiting, completed, terminated).
        phase: Optional filter on trial phase (e.g. Phase 1, Phase 2, Phase 3).
        limit: Max results (default 50).
    """
    conditions: list[str] = []
    params: list[Any] = []

    if status:
        conditions.append("status = ?")
        params.append(status)

    if phase:
        conditions.append("phase = ?")
        params.append(phase)

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    params.append(limit)

    rows = await _fetch_all(
        f"SELECT id, nct_id, title, status, phase, conditions, interventions, "
        f"sponsor, start_date, completion_date, enrollment, url, created_at "
        f"FROM trials {where} "
        f"ORDER BY start_date DESC, created_at DESC LIMIT ?",
        tuple(params),
    )
    for row in rows:
        row["conditions"] = _safe_json(row.get("conditions"))
        row["interventions"] = _safe_json(row.get("interventions"))
    return rows


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
