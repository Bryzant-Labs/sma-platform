"""Literature Review API Routes.

Endpoints for automated literature review generation per target.
Supports both LLM-powered (Claude Sonnet) and data-only reviews.
"""

import logging

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/review", tags=["literature-review"])


@router.get("/targets")
async def list_reviewable_targets():
    """List targets with enough claims (>10) for meaningful literature review.

    Returns targets sorted by claim count descending, with metadata
    about evidence volume and source diversity.
    """
    from ...reasoning.literature_reviewer import list_reviewable_targets as _list

    targets = await _list()
    return {
        "targets": targets,
        "count": len(targets),
    }


@router.get("/{target_symbol}")
async def get_target_review(
    target_symbol: str,
    force_data_only: bool = Query(
        False,
        description="Force data-only mode even if ANTHROPIC_API_KEY is set",
    ),
):
    """Generate a structured literature review for a target.

    Uses Claude Sonnet if ANTHROPIC_API_KEY is set (unless force_data_only=true).
    Falls back to data-only aggregation otherwise.

    The review includes:
    - Overview (2-3 sentences)
    - Key findings grouped by evidence type
    - Therapeutic implications
    - Open questions
    - Key references (top 10 papers)
    """
    from ...reasoning.literature_reviewer import (
        generate_review_without_llm,
        generate_target_review,
    )

    try:
        if force_data_only:
            result = await generate_review_without_llm(target_symbol)
        else:
            result = await generate_target_review(target_symbol)
    except Exception as e:
        logger.error("Review generation failed for %s: %s", target_symbol, e, exc_info=True)
        raise HTTPException(500, f"Review generation failed: {str(e)}")

    if result.get("status") == "not_found":
        raise HTTPException(404, result.get("error", f"Target '{target_symbol}' not found"))

    return result


@router.get("/{target_symbol}/data")
async def get_target_data_review(target_symbol: str):
    """Generate a data-only literature review (no LLM).

    Pure data aggregation: claim counts, top papers, evidence summary
    grouped by type. Always available regardless of API key.
    """
    from ...reasoning.literature_reviewer import generate_review_without_llm

    try:
        result = await generate_review_without_llm(target_symbol)
    except Exception as e:
        logger.error("Data review failed for %s: %s", target_symbol, e, exc_info=True)
        raise HTTPException(500, f"Data review generation failed: {str(e)}")

    if result.get("status") == "not_found":
        raise HTTPException(404, result.get("error", f"Target '{target_symbol}' not found"))

    return result
