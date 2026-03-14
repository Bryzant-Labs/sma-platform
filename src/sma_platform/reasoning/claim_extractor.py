"""Extract structured claims from paper abstracts using LLM.

Each claim is a factual assertion that can be evaluated against evidence.
Claims link back to their source paper and relate to known targets.

Schema reference:
  claims: id, claim_type, subject_id, subject_type, predicate, object_id, object_type, value, confidence, metadata
  evidence: id, claim_id, source_id, excerpt, figure_ref, method, sample_size, p_value, effect_size, metadata
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

VALID_CLAIM_TYPES = {
    "gene_expression", "protein_interaction", "pathway_membership",
    "drug_target", "drug_efficacy", "biomarker", "splicing_event",
    "neuroprotection", "motor_function", "survival", "safety", "other",
}

# Map LLM-generated types to valid DB claim types
TYPE_MAP = {
    "mechanism": "pathway_membership",
    "efficacy": "drug_efficacy",
    "epidemiology": "other",
    "methodology": "other",
    "drug_mechanism": "drug_target",
    "gene_regulation": "gene_expression",
    "splicing": "splicing_event",
    "neuroprotective": "neuroprotection",
    "motor": "motor_function",
}

EXTRACTION_PROMPT = """You are a biomedical research analyst specializing in Spinal Muscular Atrophy (SMA).

Given the following paper abstract, extract structured claims. Each claim should be:
- A single factual assertion from the abstract
- Relevant to SMA biology, treatment, or targets
- Specific enough to be verified or refuted

For each claim, provide:
- predicate: The factual assertion (1-2 sentences)
- claim_type: One of [gene_expression, protein_interaction, pathway_membership, drug_target, drug_efficacy, biomarker, splicing_event, neuroprotection, motor_function, survival, safety, other]
- confidence: Your confidence the abstract supports this claim (0.0-1.0)
- subject: The primary entity (gene symbol, drug name, pathway, or "SMA")
- subject_type: One of [gene, drug, pathway, disease, cell_type]
- object: The secondary entity if applicable, or null
- object_type: Same options as subject_type, or null
- related_targets: List of gene/protein symbols mentioned (e.g., SMN1, SMN2, STMN2)
- excerpt: The key sentence from the abstract supporting this claim

Return ONLY a JSON array of claim objects. No markdown, no explanation.

Paper title: {title}
Journal: {journal}
Abstract: {abstract}"""


async def extract_claims_from_abstract(
    source_id: str,
    title: str,
    abstract: str,
    journal: str | None = None,
) -> list[dict]:
    """Extract claims from a single paper abstract using Claude."""
    api_key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set — skipping claim extraction")
        return []

    if not abstract or len(abstract.strip()) < 50:
        logger.info("Abstract too short for %s, skipping", source_id)
        return []

    prompt = EXTRACTION_PROMPT.format(
        title=title or "Unknown",
        journal=journal or "Unknown",
        abstract=abstract,
    )

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": prompt}],
            },
        )

    if resp.status_code != 200:
        logger.error("Claude API error %d: %s", resp.status_code, resp.text[:200])
        return []

    try:
        body = resp.json()
        content = body["content"][0]["text"].strip()
        # Strip markdown code fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first line (```json) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines).strip()
        logger.debug("Claude raw response (first 200 chars): %s", content[:200])
        claims = json.loads(content)
        if not isinstance(claims, list):
            claims = [claims]
        return claims
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        raw = ""
        try:
            raw = resp.json()["content"][0]["text"][:300]
        except Exception:
            raw = resp.text[:300]
        logger.error("Failed to parse claims: %s | Raw: %s", e, raw)
        return []


async def process_source(source_id: str) -> int:
    """Extract claims from a source and store them in the database."""
    source = await fetchrow("SELECT * FROM sources WHERE id = $1", source_id)
    if not source:
        logger.error("Source %s not found", source_id)
        return 0

    source = dict(source)
    claims = await extract_claims_from_abstract(
        source_id=source["id"],
        title=source.get("title", ""),
        abstract=source.get("abstract", ""),
        journal=source.get("journal"),
    )

    stored = 0
    for claim in claims:
        try:
            predicate = claim.get("predicate", "")
            if not predicate:
                continue

            # Map claim_type to valid DB values
            raw_type = claim.get("claim_type", "other").lower().strip()
            claim_type = TYPE_MAP.get(raw_type, raw_type)
            if claim_type not in VALID_CLAIM_TYPES:
                claim_type = "other"

            # Resolve subject to a target ID if possible
            subject = claim.get("subject", "SMA")
            subject_type = claim.get("subject_type", "disease")
            subject_id = None
            target_row = await fetchrow("SELECT id FROM targets WHERE symbol = $1", subject.upper())
            if target_row:
                subject_id = dict(target_row)["id"]

            # Resolve object to a target ID if possible
            obj = claim.get("object")
            object_type = claim.get("object_type")
            object_id = None
            if obj:
                obj_row = await fetchrow("SELECT id FROM targets WHERE symbol = $1", obj.upper())
                if obj_row:
                    object_id = dict(obj_row)["id"]

            # Insert claim
            await execute(
                """INSERT INTO claims (claim_type, subject_id, subject_type, predicate, object_id, object_type, confidence, metadata)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                claim_type,
                subject_id,
                subject_type,
                predicate,
                object_id,
                object_type,
                claim.get("confidence", 0.5),
                json.dumps({
                    "subject_label": subject,
                    "object_label": obj,
                    "related_targets": claim.get("related_targets", []),
                    "extraction_model": "claude-haiku-4-5-20251001",
                    "extracted_at": datetime.now(timezone.utc).isoformat(),
                    "source_paper_id": source["id"],
                }),
            )

            # Get the claim we just inserted (last one matching this predicate)
            claim_row = await fetchrow(
                "SELECT id FROM claims WHERE predicate = $1 ORDER BY created_at DESC LIMIT 1",
                predicate,
            )
            if claim_row:
                claim_id = dict(claim_row)["id"]
                # Create evidence link back to source paper
                excerpt = claim.get("excerpt", predicate[:200])
                await execute(
                    """INSERT INTO evidence (claim_id, source_id, excerpt, method, metadata)
                       VALUES ($1, $2, $3, $4, $5)""",
                    claim_id,
                    source["id"],
                    excerpt,
                    "llm_abstract_extraction",
                    json.dumps({"confidence": claim.get("confidence", 0.5)}),
                )

            stored += 1

        except Exception as e:
            logger.error("Failed to store claim: %s", e)

    logger.info("Extracted %d claims from source %s (%s)", stored, source_id, source.get("title", "")[:60])
    return stored


async def process_all_unprocessed() -> dict:
    """Extract claims from all sources that haven't been processed yet."""
    # Find sources that have no evidence rows pointing to them
    rows = await fetch(
        """SELECT s.id FROM sources s
           LEFT JOIN evidence e ON e.source_id = s.id
           WHERE e.id IS NULL AND s.abstract IS NOT NULL AND length(s.abstract) > 50
           ORDER BY s.created_at DESC""",
    )

    total_claims = 0
    processed = 0
    errors = 0

    for row in rows:
        row = dict(row)
        try:
            count = await process_source(row["id"])
            total_claims += count
            processed += 1
        except Exception as e:
            logger.error("Failed to process source %s: %s", row["id"], e)
            errors += 1

    return {
        "sources_processed": processed,
        "claims_extracted": total_claims,
        "errors": errors,
    }
