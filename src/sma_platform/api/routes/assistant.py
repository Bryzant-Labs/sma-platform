"""Research Assistant API — conversational RAG over SMA evidence base."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from ...reasoning.research_assistant import ask

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/ask")
async def ask_question(
    q: str = Query(
        ..., min_length=5, max_length=1000, description="Research question"
    ),
    max_context: int = Query(
        default=30, ge=5, le=100, description="Max evidence items to consider"
    ),
):
    """Ask a research question about SMA — answered via RAG over the evidence base.

    Uses hybrid search (semantic + keyword) to find relevant claims and papers,
    then synthesizes an answer using Claude Sonnet (Pro model).

    Example questions:
    - What is the role of NCALD in SMA pathology?
    - How does risdiplam modify SMN2 splicing?
    - What evidence supports PLS3 as a disease modifier?
    - What are the main failure reasons for SMA drug candidates?
    """
    try:
        result = await ask(question=q, max_context=max_context)
    except Exception as e:
        logger.error("Research assistant error: %s", e, exc_info=True)
        raise HTTPException(500, detail="Research assistant temporarily unavailable")

    return result
