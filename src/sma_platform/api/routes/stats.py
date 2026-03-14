"""Platform statistics endpoint."""

from fastapi import APIRouter

from ...core.database import fetchrow

router = APIRouter()


@router.get("/stats")
async def get_stats():
    """Overview counts for all major tables."""
    row = await fetchrow("""
        SELECT
            (SELECT count(*) FROM sources) AS sources,
            (SELECT count(*) FROM targets) AS targets,
            (SELECT count(*) FROM drugs) AS drugs,
            (SELECT count(*) FROM trials) AS trials,
            (SELECT count(*) FROM datasets) AS datasets,
            (SELECT count(*) FROM claims) AS claims,
            (SELECT count(*) FROM evidence) AS evidence,
            (SELECT count(*) FROM hypotheses) AS hypotheses
    """)
    if row:
        return dict(row)
    return {}
