"""Semantic search endpoints for claims and sources."""

from __future__ import annotations

import logging
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query

from ...core.database import fetch, fetchrow
from ...reasoning.embeddings import (
    build_index,
    get_index_stats,
    hybrid_search,
    search as semantic_search,
    _keyword_search,
)
from ..auth import require_admin_key

logger = logging.getLogger(__name__)

router = APIRouter()


class SearchMode(str, Enum):
    semantic = "semantic"
    keyword = "keyword"
    hybrid = "hybrid"


async def _enrich_results(results: list[dict]) -> list[dict]:
    """Enrich raw search results with full claim/source details from DB."""
    enriched = []

    for r in results:
        item = {
            "type": r["type"],
            "id": r["id"],
            "score": r["score"],
        }
        if "match_modes" in r:
            item["match_modes"] = r["match_modes"]

        if r["type"] == "claim":
            row = await fetchrow(
                """SELECT c.id, c.claim_type, c.predicate, c.subject_type,
                          c.object_type, c.confidence, c.metadata,
                          s.title AS source_title, s.external_id AS source_pmid
                   FROM claims c
                   LEFT JOIN evidence e ON e.claim_id = c.id
                   LEFT JOIN sources s ON e.source_id = s.id
                   WHERE c.id = $1
                   LIMIT 1""",
                r["id"],
            )
            if row:
                d = dict(row)
                item["text"] = d.get("predicate", "")
                item["claim_type"] = d.get("claim_type")
                item["confidence"] = float(d["confidence"]) if d.get("confidence") is not None else None
                item["subject_type"] = d.get("subject_type")
                item["object_type"] = d.get("object_type")
                item["source_title"] = d.get("source_title")
                item["source_pmid"] = d.get("source_pmid")

        elif r["type"] == "source":
            row = await fetchrow(
                """SELECT id, title, external_id, journal, pub_date, doi, url,
                          LEFT(abstract, 300) AS abstract_snippet
                   FROM sources WHERE id = $1""",
                r["id"],
            )
            if row:
                d = dict(row)
                item["text"] = d.get("title", "")
                item["source_title"] = d.get("title")
                item["source_pmid"] = d.get("external_id")
                item["journal"] = d.get("journal")
                item["pub_date"] = str(d["pub_date"]) if d.get("pub_date") else None
                item["doi"] = d.get("doi")
                item["url"] = d.get("url")
                item["abstract_snippet"] = d.get("abstract_snippet")

        enriched.append(item)

    return enriched


@router.get("/search")
async def search_endpoint(
    q: str = Query(..., min_length=2, max_length=500, description="Search query"),
    top_k: int = Query(default=20, ge=1, le=100, description="Number of results"),
    mode: SearchMode = Query(default=SearchMode.hybrid, description="Search mode"),
):
    """Search across claims and sources using semantic, keyword, or hybrid mode.

    - **semantic**: Pure vector similarity (sentence-transformers + FAISS)
    - **keyword**: SQL ILIKE pattern matching
    - **hybrid**: Combines both, boosts items found by both methods
    """
    try:
        if mode == SearchMode.semantic:
            raw_results = await semantic_search(q, top_k=top_k)
        elif mode == SearchMode.keyword:
            raw_results = await _keyword_search(q, top_k=top_k)
        else:
            raw_results = await hybrid_search(q, top_k=top_k)
    except Exception as e:
        logger.error("Search failed: %s", e, exc_info=True)
        raise HTTPException(500, detail="Search engine error — index may not be built yet")

    if not raw_results:
        return {
            "results": [],
            "query": q,
            "total": 0,
            "mode": mode.value,
            "note": "No results found. The search index may not be built yet — POST /search/reindex to build it.",
        }

    enriched = await _enrich_results(raw_results)

    return {
        "results": enriched,
        "query": q,
        "total": len(enriched),
        "mode": mode.value,
    }


@router.post("/search/reindex", dependencies=[Depends(require_admin_key)])
async def reindex():
    """Rebuild the full FAISS search index from all claims and sources.

    Requires X-Admin-Key header. This is a long-running operation (may take
    several minutes depending on data volume).
    """
    try:
        meta = await build_index()
        return {
            "status": "ok",
            "message": "Index rebuilt successfully",
            **meta,
        }
    except Exception as e:
        logger.error("Reindex failed: %s", e, exc_info=True)
        raise HTTPException(500, detail=f"Reindex failed: {e}")


@router.get("/search/stats")
async def search_stats():
    """Return search index statistics — no authentication required."""
    stats = await get_index_stats()
    return stats
