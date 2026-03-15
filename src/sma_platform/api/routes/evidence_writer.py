"""Evidence Writer API — structured grant/paper/briefing generation (Agent E)."""

from __future__ import annotations

import logging
import re
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query

from ...reasoning.evidence_writer import (
    FormatType,
    generate_summary,
    generate_target_comparison,
)

logger = logging.getLogger(__name__)
router = APIRouter()

_VALID_FORMATS: set[str] = {
    "grant_section",
    "paper_intro",
    "briefing",
    "hypothesis_rationale",
}

_VALID_TYPES: set[str] = {"target", "topic"}


@router.get("/write/summary")
async def write_summary(
    subject: str = Query(
        ...,
        min_length=2,
        max_length=200,
        description=(
            "Gene symbol (e.g. SMN2, NCALD) or research topic "
            "(e.g. 'SMN2 splicing', 'neuroprotection')."
        ),
    ),
    format: str = Query(
        default="briefing",
        description=(
            "Output format. One of: grant_section (NIH R01 style, 800–1200 words), "
            "paper_intro (journal introduction, 500–800 words), "
            "briefing (executive briefing for non-specialists, 400–600 words), "
            "hypothesis_rationale (detailed testable hypothesis doc, 600–1000 words)."
        ),
    ),
    type: str = Query(
        default="target",
        description=(
            "Subject type. 'target' for gene/protein symbols, "
            "'topic' for free-text research topics."
        ),
    ),
):
    """Generate a structured evidence summary for a gene target or research topic.

    Gathers evidence from the SMA database (claims, trials, drug outcomes, hypotheses)
    and synthesises a grounded document in the requested format using Claude Sonnet.

    No admin key required — public endpoint.

    Examples:
    - `/write/summary?subject=SMN2&format=briefing&type=target`
    - `/write/summary?subject=PLS3&format=grant_section&type=target`
    - `/write/summary?subject=neuroprotection&format=paper_intro&type=topic`
    - `/write/summary?subject=NCALD&format=hypothesis_rationale&type=target`
    """
    if format not in _VALID_FORMATS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid format '{format}'. "
                f"Must be one of: {', '.join(sorted(_VALID_FORMATS))}"
            ),
        )

    if type not in _VALID_TYPES:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid type '{type}'. Must be one of: {', '.join(sorted(_VALID_TYPES))}"
            ),
        )

    try:
        result = await generate_summary(
            subject=subject,
            format_type=format,  # type: ignore[arg-type]
            subject_type=type,   # type: ignore[arg-type]
        )
    except Exception as e:
        logger.error("Evidence writer error for '%s': %s", subject, e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Evidence writer error: {e}",
        )

    if result.get("error"):
        raise HTTPException(status_code=503, detail=result["error"])

    return result


@router.get("/write/compare")
async def write_comparison(
    targets: str = Query(
        ...,
        description=(
            "Comma-separated gene symbols to compare (2–5 targets). "
            "Example: SMN2,NCALD,PLS3"
        ),
    ),
    format: str = Query(
        default="briefing",
        description=(
            "Output format. One of: grant_section, paper_intro, briefing, "
            "hypothesis_rationale."
        ),
    ),
):
    """Generate a comparative evidence summary across multiple gene targets.

    Gathers evidence for each target independently, then synthesises a
    single comparative document highlighting relative evidence strength,
    shared mechanisms, and clinical translation potential.

    No admin key required — public endpoint.

    Examples:
    - `/write/compare?targets=SMN2,NCALD,PLS3&format=briefing`
    - `/write/compare?targets=SMN2,STMN2&format=grant_section`
    """
    if format not in _VALID_FORMATS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid format '{format}'. "
                f"Must be one of: {', '.join(sorted(_VALID_FORMATS))}"
            ),
        )

    # Parse and validate target list
    target_list = [t.strip() for t in targets.split(",") if t.strip()]

    if len(target_list) < 2:
        raise HTTPException(
            status_code=422,
            detail="At least 2 targets required for comparison.",
        )

    if len(target_list) > 5:
        raise HTTPException(
            status_code=422,
            detail="Maximum 5 targets allowed per comparison.",
        )

    # Validate gene symbol format — must be alphanumeric with optional underscores/hyphens
    VALID_SYMBOL = re.compile(r'^[A-Za-z0-9_\-]{1,50}$')
    for t in target_list:
        if len(t) > 50:
            raise HTTPException(
                status_code=422,
                detail=f"Target symbol '{t[:50]}...' is too long (max 50 chars).",
            )
        if not VALID_SYMBOL.match(t):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid target symbol format: {t}",
            )

    try:
        result = await generate_target_comparison(
            targets=target_list,
            format_type=format,  # type: ignore[arg-type]
        )
    except Exception as e:
        logger.error(
            "Evidence writer comparison error for [%s]: %s",
            ", ".join(target_list), e, exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Evidence writer comparison error: {e}",
        )

    if result.get("error"):
        raise HTTPException(status_code=503, detail=result["error"])

    return result
