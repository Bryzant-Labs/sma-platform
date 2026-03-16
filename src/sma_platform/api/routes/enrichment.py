"""Claim-Target Enrichment API Routes.

Endpoints for monitoring and running the NER-based claim enrichment
that links unlinked claims to targets/drugs via pattern matching.
"""

import logging

from fastapi import APIRouter, Depends, Query

from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/enrichment", tags=["enrichment"])


@router.get("/stats")
async def enrichment_stats():
    """Get current claim-target linking status.

    Returns total claims, linked/unlinked counts, link rate,
    and breakdown by subject_type.
    """
    from ...reasoning.claim_enricher import get_enrichment_stats
    return await get_enrichment_stats()


@router.post("/run", dependencies=[Depends(require_admin_key)])
async def run_enrichment(
    batch_size: int = Query(1000, ge=100, le=10000),
):
    """Run claim enrichment — scan unlinked claims and link to targets/drugs.

    Scans predicate text for gene/protein/drug mentions using
    case-insensitive word-boundary pattern matching.
    Requires admin key.
    """
    from ...reasoning.claim_enricher import enrich_claims
    result = await enrich_claims(batch_size=batch_size, dry_run=False)
    return result


@router.post("/dry-run", dependencies=[Depends(require_admin_key)])
async def dry_run_enrichment(
    batch_size: int = Query(1000, ge=100, le=10000),
):
    """Preview enrichment without modifying data.

    Returns the same stats as /run plus sample_matches showing
    what would be linked.
    Requires admin key.
    """
    from ...reasoning.claim_enricher import enrich_claims
    result = await enrich_claims(batch_size=batch_size, dry_run=True)
    return result
