"""Prime editing feasibility assessment endpoints (Phase 6.2)."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from ...reasoning.prime_editor import assess_prime_editing_feasibility

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/prime-editing/feasibility")
async def get_prime_editing_feasibility():
    """Assess prime editing feasibility for all SMA-relevant edits.

    Evaluates PE2/PE3/PEmax for:
    - SMN2 C6T correction (the root cause fix)
    - ISS-N1 disruption (permanent nusinersen)
    - ESE strengthening (Tra2-beta enhancer)

    Includes comparison with approved therapies (nusinersen, risdiplam, Zolgensma).
    """
    return assess_prime_editing_feasibility()
