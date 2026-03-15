"""Extract structured drug failure/success outcomes from SMA literature.

Builds the SMA Drug Failure & Success Database (Phase 9.1):
- Why did a drug/compound fail? (toxicity, bioavailability, efficacy, off-target)
- What worked? (approved drugs, positive trial results)
- Structured output: Molecule → Target → Result → Failure Reason

This is a unique contribution — no existing database captures SMA drug failures
in a structured, machine-readable format.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

import httpx

from ..core.config import settings
from ..core.database import execute, fetch, fetchrow

logger = logging.getLogger(__name__)

OUTCOME_PROMPT = """You are a biomedical drug development analyst specializing in SMA (Spinal Muscular Atrophy).

Analyze this paper and extract ALL drug/compound outcome data. We want to build a database of WHY drugs succeed or fail in SMA.

For each drug or compound mentioned, extract:
- compound_name: Generic drug name or compound ID (e.g., "nusinersen", "branaplam", "CHEMBL12345")
- target: Primary molecular target (e.g., "SMN2", "SMN1", "mTOR")
- mechanism: How it works (e.g., "ASO targeting ISS-N1", "small molecule splicing modifier")
- outcome: One of [success, partial_success, failure, inconclusive, discontinued, ongoing]
- failure_reason: If failed/discontinued, the primary reason. One of [toxicity, lack_of_efficacy, poor_bioavailability, off_target_effects, poor_bbb_penetration, manufacturing, commercial, safety_signal, patient_recruitment, null]
- failure_detail: Specific description of what went wrong (e.g., "hepatotoxicity at therapeutic doses", "no significant difference vs placebo in HFMSE score")
- trial_phase: Phase at which outcome was determined (preclinical, phase1, phase2, phase3, approved, post_market)
- model_system: What was tested in (e.g., "SMA type 1 patients", "delta7 mouse model", "iPSC motor neurons", "in vitro")
- key_finding: One-sentence summary of the main result
- confidence: Your confidence in this extraction (0.0-1.0)

IMPORTANT:
- Extract BOTH positive and negative outcomes
- For approved drugs (nusinersen, risdiplam, onasemnogene), note their success but also any limitations mentioned
- For experimental compounds, capture why they failed or were discontinued
- For preclinical compounds, note their efficacy and any issues
- Be specific about failure reasons — "toxicity" alone is not enough, say what kind

Return ONLY a JSON array of outcome objects. No markdown, no explanation. If no drug outcomes are mentioned, return [].

Paper title: {title}
Journal: {journal}
Text: {text}"""


async def extract_outcomes_from_text(
    source_id: str,
    title: str,
    text: str,
    journal: str | None = None,
) -> list[dict]:
    """Extract drug outcomes from paper text using Claude."""
    api_key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set — skipping outcome extraction")
        return []

    if not text or len(text.strip()) < 100:
        return []

    # Truncate very long texts to stay within token limits
    max_chars = 12000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n[... truncated]"

    prompt = OUTCOME_PROMPT.format(
        title=title or "Unknown",
        journal=journal or "Unknown",
        text=text,
    )

    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
            },
        )

    if resp.status_code != 200:
        logger.error("Claude API error %d: %s", resp.status_code, resp.text[:200])
        return []

    try:
        body = resp.json()
        content = body["content"][0]["text"].strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines).strip()
        outcomes = json.loads(content)
        if not isinstance(outcomes, list):
            outcomes = [outcomes]
        return outcomes
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.error("Failed to parse outcomes: %s", e)
        return []


VALID_OUTCOMES = {"success", "partial_success", "failure", "inconclusive", "discontinued", "ongoing"}
VALID_FAILURE_REASONS = {
    "toxicity", "lack_of_efficacy", "poor_bioavailability", "off_target_effects",
    "poor_bbb_penetration", "manufacturing", "commercial", "safety_signal",
    "patient_recruitment", None,
}


async def process_source_outcomes(source_id: str) -> int:
    """Extract drug outcomes from a source and store in drug_outcomes table."""
    source = await fetchrow("SELECT * FROM sources WHERE id = $1", source_id)
    if not source:
        return 0

    source = dict(source)
    # Prefer full text, fall back to abstract
    text = source.get("full_text") or source.get("abstract") or ""
    if len(text) < 100:
        return 0

    outcomes = await extract_outcomes_from_text(
        source_id=str(source["id"]),
        title=source.get("title", ""),
        text=text,
        journal=source.get("journal"),
    )

    stored = 0
    for outcome in outcomes:
        try:
            compound = outcome.get("compound_name", "").strip()[:200]
            if not compound:
                continue

            result = outcome.get("outcome", "inconclusive").lower()
            if result not in VALID_OUTCOMES:
                result = "inconclusive"

            failure_reason = outcome.get("failure_reason")
            if failure_reason and failure_reason.lower() == "null":
                failure_reason = None
            if failure_reason and failure_reason not in VALID_FAILURE_REASONS:
                failure_reason = None

            # Cap LLM-supplied fields to prevent oversized inserts
            target_val = (outcome.get("target") or "")[:200] or None
            mechanism_val = (outcome.get("mechanism") or "")[:500] or None
            failure_detail_val = (outcome.get("failure_detail") or "")[:1000] or None
            trial_phase_val = (outcome.get("trial_phase") or "")[:100] or None
            model_system_val = (outcome.get("model_system") or "")[:200] or None
            key_finding_val = (outcome.get("key_finding") or "")[:1000] or None

            await execute(
                """INSERT INTO drug_outcomes
                   (compound_name, target, mechanism, outcome, failure_reason,
                    failure_detail, trial_phase, model_system, key_finding,
                    confidence, source_id, metadata)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                   ON CONFLICT (compound_name, source_id) DO UPDATE
                   SET outcome = EXCLUDED.outcome, failure_reason = EXCLUDED.failure_reason,
                       failure_detail = EXCLUDED.failure_detail, key_finding = EXCLUDED.key_finding,
                       updated_at = CURRENT_TIMESTAMP""",
                compound,
                target_val,
                mechanism_val,
                result,
                failure_reason,
                failure_detail_val,
                trial_phase_val,
                model_system_val,
                key_finding_val,
                outcome.get("confidence", 0.5),
                source["id"],
                json.dumps({
                    "extraction_model": "claude-haiku-4-5-20251001",
                    "extracted_at": datetime.now(timezone.utc).isoformat(),
                }),
            )
            stored += 1

        except Exception as e:
            logger.error("Failed to store outcome for %s: %s", outcome.get("compound_name"), e)

    logger.info("Extracted %d outcomes from source %s", stored, source.get("title", "")[:60])
    return stored


async def process_all_drug_outcomes(batch_size: int = 100) -> dict:
    """Extract drug outcomes from sources mentioning drugs/treatments.

    Prioritizes papers that mention SMA drugs or clinical trials.
    """
    # Find sources likely to contain drug outcome data
    rows = await fetch(
        """SELECT s.id FROM sources s
           WHERE s.abstract IS NOT NULL
             AND length(s.abstract) > 100
             AND (
                 LOWER(s.abstract) LIKE '%nusinersen%'
                 OR LOWER(s.abstract) LIKE '%risdiplam%'
                 OR LOWER(s.abstract) LIKE '%onasemnogene%'
                 OR LOWER(s.abstract) LIKE '%zolgensma%'
                 OR LOWER(s.abstract) LIKE '%spinraza%'
                 OR LOWER(s.abstract) LIKE '%evrysdi%'
                 OR LOWER(s.abstract) LIKE '%branaplam%'
                 OR LOWER(s.abstract) LIKE '%apitegromab%'
                 OR LOWER(s.abstract) LIKE '%reldesemtiv%'
                 OR LOWER(s.abstract) LIKE '%clinical trial%'
                 OR LOWER(s.abstract) LIKE '%phase %'
                 OR LOWER(s.abstract) LIKE '%efficacy%'
                 OR LOWER(s.abstract) LIKE '%toxicity%'
                 OR LOWER(s.abstract) LIKE '%adverse%'
                 OR LOWER(s.abstract) LIKE '%discontinued%'
                 OR LOWER(s.abstract) LIKE '%preclinical%'
                 OR LOWER(s.abstract) LIKE '%drug candidate%'
                 OR LOWER(s.abstract) LIKE '%compound%'
             )
             AND NOT EXISTS (
                 SELECT 1 FROM drug_outcomes dout WHERE dout.source_id = s.id
             )
           ORDER BY s.pub_date DESC NULLS LAST
           LIMIT $1""",
        batch_size,
    )

    total_outcomes = 0
    processed = 0
    errors = 0

    for row in rows:
        r = dict(row)
        try:
            count = await process_source_outcomes(str(r["id"]))
            total_outcomes += count
            processed += 1
        except Exception as e:
            logger.error("Failed to process source %s: %s", r["id"], e)
            errors += 1

    logger.info("Drug outcomes: processed=%d outcomes=%d errors=%d", processed, total_outcomes, errors)
    return {
        "sources_processed": processed,
        "outcomes_extracted": total_outcomes,
        "errors": errors,
    }
