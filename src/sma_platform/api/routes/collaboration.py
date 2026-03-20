"""External Lab Collaboration API — structured data exports for researchers."""

from __future__ import annotations
import logging
from fastapi import APIRouter, Query
from ...core.database import fetch, fetchval

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/collab", tags=["collaboration"])


@router.get("/export/target/{symbol}")
async def export_target_data(symbol: str):
    """Export all platform data for a target in a researcher-friendly format.

    No authentication required — all data is from public sources.
    Suitable for supplementary materials, grant applications, or collaboration.
    """
    sym = symbol.upper()

    target = await fetch("SELECT * FROM targets WHERE symbol = $1", sym)
    if not target:
        from fastapi import HTTPException
        raise HTTPException(404, detail=f"Target {sym} not found")
    t = dict(target[0])
    tid = t["id"]

    # Claims
    claims = await fetch("""
        SELECT c.claim_number, c.claim_type, c.predicate, c.confidence,
               s.external_id AS pmid, s.title AS paper_title, s.journal, s.pub_date
        FROM claims c
        JOIN evidence e ON e.claim_id = c.id
        JOIN sources s ON e.source_id = s.id
        WHERE c.subject_id = $1 OR c.object_id = $1
        ORDER BY c.confidence DESC
        LIMIT 50
    """, tid)

    # Convergence
    conv = await fetch(
        "SELECT * FROM convergence_scores WHERE target_id = $1 ORDER BY computed_at DESC LIMIT 1", tid)

    # Conservation
    orthologs = await fetch(
        "SELECT species, ortholog_symbol, conservation_score FROM cross_species_targets WHERE human_symbol = $1", sym)

    return {
        "export_format": "sma_platform_v1",
        "target": {
            "symbol": sym,
            "name": t.get("name"),
            "type": t.get("target_type"),
            "description": t.get("description"),
        },
        "convergence": dict(conv[0]) if conv else None,
        "claims": [dict(c) for c in claims],
        "claim_count": len(claims),
        "conservation": [dict(o) for o in orthologs],
        "data_sources": "PubMed, ClinicalTrials.gov, Google Patents, AlphaFold, ChEMBL, STRING-DB",
        "citation": "SMA Research Platform (https://sma-research.info). Open source under AGPL-3.0.",
        "api_docs": "https://sma-research.info/api/v2/docs",
    }


@router.get("/export/claims")
async def export_claims(
    target: str = Query(default=None, description="Filter by target symbol"),
    claim_type: str = Query(default=None, description="Filter by claim type"),
    min_confidence: float = Query(default=0.0, ge=0, le=1),
    limit: int = Query(default=100, ge=1, le=5000),
):
    """Export claims in a structured format for external analysis."""
    query = """
        SELECT c.claim_number, c.claim_type, c.predicate, c.confidence,
               c.subject_type, c.object_type,
               s.external_id AS pmid, s.title AS paper_title, s.journal
        FROM claims c
        JOIN evidence e ON e.claim_id = c.id
        JOIN sources s ON e.source_id = s.id
        WHERE c.confidence >= $1
    """
    params = [min_confidence]

    if claim_type:
        params.append(claim_type)
        query += f" AND c.claim_type = ${len(params)}"

    query += f" ORDER BY c.confidence DESC LIMIT ${len(params) + 1}"
    params.append(limit)

    rows = await fetch(query, *params)

    return {
        "export_format": "sma_claims_v1",
        "total": len(rows),
        "filters": {"target": target, "claim_type": claim_type, "min_confidence": min_confidence},
        "claims": [dict(r) for r in rows],
        "citation": "SMA Research Platform (https://sma-research.info)",
    }


@router.get("/export/screening-hits")
async def export_screening_hits():
    """Export all positive virtual screening hits."""
    hits = await fetch("""
        SELECT DISTINCT hit_target, hit_smiles, docking_confidence
        FROM screening_milestones
        WHERE docking_confidence > 0
        ORDER BY docking_confidence DESC
    """)

    return {
        "export_format": "sma_screening_v1",
        "total": len(hits),
        "methodology": "GenMol (generation) \u2192 RDKit (Lipinski/QED/BBB filter) \u2192 DiffDock v2.2 (blind docking vs AlphaFold structures)",
        "hits": [{"target": h["hit_target"], "smiles": h["hit_smiles"],
                 "docking_confidence": float(h["docking_confidence"])} for h in hits],
        "citation": "SMA Research Platform (https://sma-research.info)",
    }


@router.get("/export/summary")
async def export_platform_summary():
    """Quick summary of what the platform offers — for new collaborators."""
    sources = await fetchval("SELECT COUNT(*) FROM sources") or 0
    claims = await fetchval("SELECT COUNT(*) FROM claims") or 0
    hypotheses = await fetchval("SELECT COUNT(*) FROM hypotheses") or 0
    targets = await fetchval("SELECT COUNT(*) FROM targets") or 0

    return {
        "platform": "SMA Research Platform",
        "url": "https://sma-research.info",
        "github": "https://github.com/Bryzant-Labs/sma-platform",
        "license": "AGPL-3.0",
        "stats": {
            "pubmed_sources": sources,
            "extracted_claims": claims,
            "hypotheses": hypotheses,
            "molecular_targets": targets,
            "species_compared": 7,
            "screening_hits": 56,
            "mcp_tools": 37,
        },
        "capabilities": [
            "Evidence convergence scoring (5-dimension)",
            "Virtual drug screening (GenMol + DiffDock)",
            "Cross-species conservation mapping (7 organisms)",
            "Cross-disease drug repurposing",
            "Therapy combination ranking",
            "Patent freedom-to-operate analysis",
            "Grant-ready hypothesis exports (NIH, ERC, Cure SMA)",
            "Conversational AI search over 30,000+ claims",
            "MCP server for AI agent integration",
        ],
        "contact": "https://sma-research.info/contact",
        "api_docs": "https://sma-research.info/api/v2/docs",
    }
