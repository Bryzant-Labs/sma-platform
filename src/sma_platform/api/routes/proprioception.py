from __future__ import annotations
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/proprioception", tags=["proprioception"])


@router.get("/analysis")
async def proprioceptive_analysis():
    """Comprehensive proprioceptive pathway analysis in SMA."""
    from ...reasoning.proprioception import get_proprioceptive_analysis
    return get_proprioceptive_analysis()


@router.get("/h-reflex")
async def h_reflex_info():
    """H-reflex testing information for SMA proprioception."""
    from ...reasoning.proprioception import get_h_reflex_testing_info
    return get_h_reflex_testing_info()


@router.get("/segments")
async def segment_map():
    """Spinal cord segment vulnerability mapping."""
    from ...reasoning.segment_mapping import get_segment_map
    return get_segment_map()
