"""Platform statistics endpoint."""

from fastapi import APIRouter

from ...core.database import fetch, fetchrow

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


@router.get("/stats/pipeline")
async def get_pipeline_status():
    """Latest pipeline run results and ingestion log entries."""
    rows = await fetch(
        """SELECT source_type, query, items_found, items_new, items_updated,
                  errors, run_at, duration_secs
           FROM ingestion_log
           ORDER BY id DESC
           LIMIT 20"""
    )
    runs = []
    for row in rows:
        r = dict(row)
        r["run_at"] = str(r["run_at"]) if r.get("run_at") else None
        runs.append(r)

    # Get extended stats
    extra = await fetchrow("""
        SELECT
            (SELECT count(*) FROM graph_edges) AS graph_edges,
            (SELECT count(*) FROM drug_outcomes) AS drug_outcomes,
            (SELECT count(*) FROM target_scores) AS target_scores,
            (SELECT count(*) FROM cross_species_targets) AS orthologs
    """)

    return {
        "recent_runs": runs,
        "extended_stats": dict(extra) if extra else {},
    }
