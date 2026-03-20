"""Score Reproducibility Testing API — Track 1 Scientific Credibility."""

from __future__ import annotations
import logging
from fastapi import APIRouter, Depends
from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reproducibility", tags=["reproducibility"])


@router.get("/test")
async def run_reproducibility_tests():
    """Run all reproducibility tests on convergence scores and rankings."""
    from ...reasoning.reproducibility import run_all_reproducibility_tests
    return await run_all_reproducibility_tests()


@router.get("/test/convergence")
async def test_convergence():
    """Test convergence score reproducibility (run twice, compare)."""
    from ...reasoning.reproducibility import test_convergence_reproducibility
    return await test_convergence_reproducibility()


@router.get("/test/ranking")
async def test_ranking():
    """Test ranking order stability."""
    from ...reasoning.reproducibility import test_ranking_stability
    return await test_ranking_stability()


@router.get("/test/claims")
async def test_claims():
    """Test claim count consistency between scoring and database."""
    from ...reasoning.reproducibility import test_claim_count_consistency
    return await test_claim_count_consistency()
