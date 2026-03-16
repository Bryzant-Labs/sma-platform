"""Extraction quality benchmark API routes.

Provides endpoints to evaluate claim extraction quality:
- GET  /benchmark/extraction       — metrics from existing gold-standard evaluations
- GET  /benchmark/gold-standard    — sample claims for manual review
- POST /benchmark/evaluate         — submit a gold-standard evaluation (admin)
- GET  /benchmark/reproducibility  — re-extract and measure consistency
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...reasoning.extraction_benchmark import (
    build_gold_standard,
    evaluate_extraction,
    submit_evaluation,
    test_reproducibility,
)
from ..auth import require_admin_key

router = APIRouter()


class EvaluationRequest(BaseModel):
    """Request body for submitting a gold-standard evaluation."""

    claim_id: str = Field(..., description="UUID of the claim being evaluated")
    gold_label: str = Field(
        ...,
        description="Evaluation label: 'correct', 'incorrect', or 'partial'",
        pattern="^(correct|incorrect|partial)$",
    )
    notes: str | None = Field(None, description="Optional reviewer notes")


@router.get("/benchmark/extraction")
async def benchmark_extraction_stats():
    """Get extraction quality metrics from existing gold-standard evaluations.

    Returns precision, recall estimate, F1 score, and per-claim-type breakdown.
    Requires evaluations to have been submitted via POST /benchmark/evaluate.
    """
    return await evaluate_extraction()


@router.get("/benchmark/gold-standard")
async def benchmark_gold_standard(
    sample_size: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Number of claims to sample for review",
    ),
):
    """Sample claims with their source abstracts for manual gold-standard review.

    Returns claims paired with the abstract they were extracted from,
    excluding claims that have already been evaluated.
    """
    return await build_gold_standard(sample_size=sample_size)


@router.post("/benchmark/evaluate", dependencies=[Depends(require_admin_key)])
async def benchmark_submit_evaluation(body: EvaluationRequest):
    """Submit a gold-standard evaluation for a single claim.

    Requires admin authentication via X-Admin-Key header.

    Labels:
    - **correct**: Claim accurately represents what the abstract states
    - **incorrect**: Claim is wrong, hallucinated, or unsupported by the abstract
    - **partial**: Claim captures the gist but misses key detail or nuance
    """
    result = await submit_evaluation(
        claim_id=body.claim_id,
        gold_label=body.gold_label,
        notes=body.notes,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/benchmark/reproducibility")
async def benchmark_reproducibility(
    sample_size: int = Query(
        default=20,
        ge=1,
        le=50,
        description="Number of sources to re-extract for reproducibility testing",
    ),
):
    """Test extraction reproducibility by re-extracting claims from source abstracts.

    Re-runs the claim extraction pipeline on a random sample of sources
    that already have claims, then measures how many of the new claims
    match existing ones (token-level Jaccard similarity > 0.6).

    Note: This endpoint calls the Claude API for each source in the sample,
    so it may take a few minutes to complete for larger sample sizes.
    """
    return await test_reproducibility(sample_size=sample_size)
