"""Daily autonomous research pipeline — full ingestion → analysis → notification cycle.

Run: python scripts/daily_research_pipeline.py
Cron: 0 6 * * * cd /home/bryzant/sma-platform && venv/bin/python scripts/daily_research_pipeline.py >> /var/log/sma-pipeline.log 2>&1

Pipeline stages:
  1. PubMed ingestion (7 days back)
  2. ClinicalTrials.gov update
  3. Claim extraction from new abstracts
  4. Hypothesis regeneration
  5. Evidence score refresh
  6. Slack summary notification
"""

import asyncio
import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sma_platform.core.config import settings
from sma_platform.core.database import close_pool, execute, fetch, fetchrow, init_pool
from sma_platform.ingestion.adapters import clinicaltrials, pmc, pubmed
from sma_platform.reasoning.claim_extractor import process_all_unprocessed, relink_all_claims
from sma_platform.reasoning.failure_extractor import process_all_drug_outcomes
from sma_platform.reasoning.graph_expander import expand_graph
from sma_platform.reasoning.hypothesis_generator import generate_all_hypotheses
from sma_platform.reasoning.scorer import score_all_claims

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("sma-pipeline")


async def stage_pubmed(days_back: int = 7) -> dict:
    """Stage 1: Pull recent SMA papers from PubMed."""
    logger.info("Stage 1: PubMed ingestion (days_back=%d)", days_back)
    start = datetime.now(timezone.utc)

    papers = await pubmed.search_recent_sma(days_back=days_back)
    new_count = 0
    updated_count = 0
    errors: list[str] = []

    for paper in papers:
        try:
            result = await execute(
                """INSERT INTO sources (source_type, external_id, title, authors, journal, pub_date, doi, url, abstract)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                   ON CONFLICT (source_type, external_id) DO UPDATE
                   SET title = excluded.title, abstract = excluded.abstract, updated_at = CURRENT_TIMESTAMP""",
                "pubmed", paper["pmid"], paper["title"],
                json.dumps(paper["authors"]), paper["journal"],
                paper["pub_date"], paper["doi"], paper["url"], paper["abstract"],
            )
            if "INSERT" in str(result):
                new_count += 1
            else:
                updated_count += 1
        except Exception as e:
            errors.append(f"PMID {paper.get('pmid')}: {e}")

    duration = (datetime.now(timezone.utc) - start).total_seconds()
    await execute(
        """INSERT INTO ingestion_log (source_type, query, items_found, items_new, items_updated, errors, duration_secs)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        "pubmed", "daily_pipeline", len(papers), new_count, updated_count,
        json.dumps(errors[:10]) if errors else None, duration,
    )

    result = {"papers_found": len(papers), "new": new_count, "updated": updated_count, "errors": len(errors), "duration": round(duration, 1)}
    logger.info("PubMed: %s", result)
    return result


async def stage_trials() -> dict:
    """Stage 2: Pull all SMA clinical trials from ClinicalTrials.gov."""
    logger.info("Stage 2: ClinicalTrials.gov ingestion")
    start = datetime.now(timezone.utc)

    trials = await clinicaltrials.fetch_all_sma_trials()
    new_count = 0
    updated_count = 0
    errors: list[str] = []

    for trial in trials:
        try:
            result = await execute(
                """INSERT INTO trials (nct_id, title, status, phase, conditions, interventions, sponsor,
                   start_date, completion_date, enrollment, results_summary, url)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                   ON CONFLICT (nct_id) DO UPDATE
                   SET title = excluded.title, status = excluded.status, phase = excluded.phase,
                       enrollment = excluded.enrollment, updated_at = CURRENT_TIMESTAMP""",
                trial["nct_id"], trial["title"], trial["status"], trial["phase"],
                json.dumps(trial["conditions"]), json.dumps(trial["interventions"]),
                trial["sponsor"], trial.get("start_date"), trial.get("completion_date"),
                trial.get("enrollment"), trial.get("brief_summary"), trial["url"],
            )
            if "INSERT" in str(result):
                new_count += 1
            else:
                updated_count += 1
        except Exception as e:
            errors.append(f"NCT {trial.get('nct_id')}: {e}")

    duration = (datetime.now(timezone.utc) - start).total_seconds()
    await execute(
        """INSERT INTO ingestion_log (source_type, query, items_found, items_new, items_updated, errors, duration_secs)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        "clinicaltrials", "daily_pipeline", len(trials), new_count, updated_count,
        json.dumps(errors[:10]) if errors else None, duration,
    )

    result = {"trials_found": len(trials), "new": new_count, "updated": updated_count, "errors": len(errors), "duration": round(duration, 1)}
    logger.info("Trials: %s", result)
    return result


async def stage_claims() -> dict:
    """Stage 3: Extract claims from unprocessed abstracts."""
    logger.info("Stage 3: Claim extraction from new abstracts")
    start = datetime.now(timezone.utc)
    result = await process_all_unprocessed()
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration"] = round(duration, 1)
    logger.info("Claims: %s", result)
    return result


async def stage_hypotheses() -> dict:
    """Stage 4: Regenerate hypotheses for all targets."""
    logger.info("Stage 4: Hypothesis regeneration")
    start = datetime.now(timezone.utc)
    result = await generate_all_hypotheses()
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration"] = round(duration, 1)
    logger.info("Hypotheses: %s", result)
    return result


async def stage_fulltext() -> dict:
    """Stage 5: Fetch full-text papers from PubMed Central OA."""
    logger.info("Stage 5: Full-text paper fetching")
    start = datetime.now(timezone.utc)
    result = await pmc.fetch_all_fulltext(batch_size=30)
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration"] = round(duration, 1)
    logger.info("Full-text: %s", result)
    return result


async def stage_drug_outcomes() -> dict:
    """Stage 6: Extract drug failure/success outcomes from literature."""
    logger.info("Stage 6: Drug outcome extraction")
    start = datetime.now(timezone.utc)
    result = await process_all_drug_outcomes(batch_size=50)
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration"] = round(duration, 1)
    logger.info("Drug outcomes: %s", result)
    return result


async def stage_relink() -> dict:
    """Stage 7: Relink unlinked claims to targets."""
    logger.info("Stage 7: Claim relinking")
    start = datetime.now(timezone.utc)
    result = await relink_all_claims()
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration"] = round(duration, 1)
    logger.info("Relinking: %s", result)
    return result


async def stage_graph_expansion() -> dict:
    """Stage 8: Auto-expand knowledge graph from evidence."""
    logger.info("Stage 8: Knowledge graph expansion")
    start = datetime.now(timezone.utc)
    result = await expand_graph()
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration"] = round(duration, 1)
    logger.info("Graph expansion: %s", result)
    return result


async def stage_scoring() -> dict:
    """Stage 9: Refresh evidence confidence scores."""
    logger.info("Stage 9: Evidence score refresh")
    start = datetime.now(timezone.utc)
    result = await score_all_claims()
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration"] = round(duration, 1)
    logger.info("Scoring: %s", result)
    return result


async def get_platform_stats() -> dict:
    """Get current platform counts for the summary."""
    stats = {}
    for table in ["sources", "targets", "drugs", "trials", "datasets", "claims", "evidence", "hypotheses"]:
        row = await fetchrow(f"SELECT COUNT(*) as cnt FROM {table}")
        stats[table] = row["cnt"] if row else 0
    return stats


async def notify_slack(results: dict, stats: dict, total_duration: float) -> None:
    """Send pipeline summary to Slack."""
    if not settings.slack_bot_token or not settings.slack_channel_id:
        logger.warning("Slack not configured — skipping notification")
        return

    try:
        import httpx

        pubmed = results.get("pubmed", {})
        trials = results.get("trials", {})
        claims = results.get("claims", {})
        hypotheses = results.get("hypotheses", {})
        fulltext = results.get("fulltext", {})
        drug_outcomes = results.get("drug_outcomes", {})
        relink = results.get("relink", {})
        graph_exp = results.get("graph_expansion", {})
        scoring = results.get("scoring", {})

        text = (
            f"*SMA Research Pipeline — Daily Report*\n"
            f"_{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_\n\n"
            f"*Stage 1 — PubMed*: {pubmed.get('new', 0)} new papers, {pubmed.get('updated', 0)} updated\n"
            f"*Stage 2 — Trials*: {trials.get('new', 0)} new, {trials.get('updated', 0)} updated (total: {trials.get('trials_found', 0)})\n"
            f"*Stage 3 — Claims*: {claims.get('sources_processed', 0)} abstracts → {claims.get('claims_extracted', 0)} claims\n"
            f"*Stage 4 — Hypotheses*: {hypotheses.get('hypotheses_generated', 0)} generated\n"
            f"*Stage 5 — Full Text*: {fulltext.get('fetched', 0)} papers fetched from PMC OA\n"
            f"*Stage 6 — Drug Outcomes*: {drug_outcomes.get('outcomes_extracted', 0)} outcomes from {drug_outcomes.get('sources_processed', 0)} papers\n"
            f"*Stage 7 — Relinking*: {relink.get('claims_updated', 0)}/{relink.get('claims_checked', 0)} claims linked to targets\n"
            f"*Stage 8 — Graph*: {graph_exp.get('total_new_edges', 0)} new edges (total: {graph_exp.get('total_edges', 0)})\n"
            f"*Stage 9 — Scoring*: {scoring.get('claims_rescored', 0)} claims rescored\n\n"
            f"*Platform Totals*: {stats.get('sources', 0)} papers | {stats.get('claims', 0)} claims | "
            f"{stats.get('hypotheses', 0)} hypotheses | {stats.get('trials', 0)} trials\n"
            f"Total pipeline time: {total_duration:.0f}s"
        )

        # Check for errors
        errors = []
        for stage_name, stage_result in results.items():
            if isinstance(stage_result, dict) and stage_result.get("error"):
                errors.append(f"{stage_name}: {stage_result['error']}")
        if errors:
            text += f"\n\n:warning: *Errors*:\n" + "\n".join(f"• {e}" for e in errors)

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {settings.slack_bot_token}"},
                json={"channel": settings.slack_channel_id, "text": text},
            )
            data = resp.json()
            if not data.get("ok"):
                logger.error("Slack API error: %s", data.get("error"))
            else:
                logger.info("Slack notification sent")
    except Exception as e:
        logger.error("Failed to send Slack notification: %s", e)


async def main():
    pipeline_start = datetime.now(timezone.utc)
    logger.info("=" * 60)
    logger.info("SMA Research Pipeline started at %s", pipeline_start.isoformat())
    logger.info("=" * 60)

    await init_pool(settings.database_url)

    results = {}
    stages = [
        ("pubmed", stage_pubmed),
        ("trials", stage_trials),
        ("claims", stage_claims),
        ("hypotheses", stage_hypotheses),
        ("fulltext", stage_fulltext),
        ("drug_outcomes", stage_drug_outcomes),
        ("relink", stage_relink),
        ("graph_expansion", stage_graph_expansion),
        ("scoring", stage_scoring),
    ]

    for name, stage_fn in stages:
        try:
            results[name] = await stage_fn()
        except Exception as e:
            logger.error("Stage '%s' failed: %s", name, e)
            logger.error(traceback.format_exc())
            results[name] = {"error": str(e)}

    total_duration = (datetime.now(timezone.utc) - pipeline_start).total_seconds()

    # Get final stats
    stats = await get_platform_stats()

    # Log pipeline run
    await execute(
        """INSERT INTO ingestion_log (source_type, query, items_found, items_new, items_updated, errors, duration_secs)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        "pipeline", "daily_research_pipeline", 0, 0, 0,
        json.dumps(results), total_duration,
    )

    # Send Slack notification
    await notify_slack(results, stats, total_duration)

    await close_pool()

    logger.info("=" * 60)
    logger.info("Pipeline complete in %.1fs", total_duration)
    logger.info("Stats: %s", json.dumps(stats))
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
