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

# Known aliases for SMA-relevant targets.
# Keys are uppercased labels the LLM may produce; values are canonical DB symbols.
TARGET_ALIASES: dict[str, str] = {
    "SMN": "SMN_PROTEIN",
    "SMN PROTEIN": "SMN_PROTEIN",
    "SURVIVAL MOTOR NEURON": "SMN1",
    "SURVIVAL MOTOR NEURON 1": "SMN1",
    "SURVIVAL MOTOR NEURON 2": "SMN2",
    "STATHMIN": "STMN2",
    "STATHMIN-2": "STMN2",
    "STATHMIN2": "STMN2",
    "PLASTIN": "PLS3",
    "PLASTIN-3": "PLS3",
    "PLASTIN 3": "PLS3",
    "T-PLASTIN": "PLS3",
    "NEUROCALCIN DELTA": "NCALD",
    "NEUROCALCIN": "NCALD",
    "UBE1": "UBA1",
    "UBIQUITIN": "UBA1",
    "CORONIN": "CORO1C",
    "CORONIN-1C": "CORO1C",
    "MTOR": "MTOR_PATHWAY",
    "MAMMALIAN TARGET OF RAPAMYCIN": "MTOR_PATHWAY",
    "MTOR PATHWAY": "MTOR_PATHWAY",
    "NMJ": "NMJ_MATURATION",
    "NEUROMUSCULAR JUNCTION": "NMJ_MATURATION",
    # Discovery targets (TargetDiscovery_A omics convergence)
    "CD44 ANTIGEN": "CD44",
    "HERMES": "CD44",
    "SULFATASE 1": "SULF1",
    "HSULF-1": "SULF1",
    "DNA METHYLTRANSFERASE 3B": "DNMT3B",
    "DNMT3BETA": "DNMT3B",
    "ANKYRIN-G": "ANK3",
    "ANKYRIN 3": "ANK3",
    "ANKYRIN-3": "ANK3",
    "MD-2": "LY96",
    "MD2": "LY96",
    "LYMPHOCYTE ANTIGEN 96": "LY96",
    "MIEAP": "SPATA18",
    "LDH-A": "LDHA",
    "LACTATE DEHYDROGENASE A": "LDHA",
    "LACTATE DEHYDROGENASE": "LDHA",
    "CALPASTATIN": "CAST",
    "NEDD4-2": "NEDD4L",
    "NEDD4.2": "NEDD4L",
    "ALPHA-CATENIN": "CTNNA1",
    "ALPHA CATENIN": "CTNNA1",
    "CATENIN ALPHA-1": "CTNNA1",
}

# Drug names → their primary mechanism-of-action target.
# Used in relinking: if a claim is about a drug, link it to the target it acts on.
DRUG_TARGET_MAP: dict[str, str] = {
    "NUSINERSEN": "SMN2",
    "SPINRAZA": "SMN2",
    "RISDIPLAM": "SMN2",
    "EVRYSDI": "SMN2",
    "BRANAPLAM": "SMN2",
    "ONASEMNOGENE": "SMN1",
    "ONASEMNOGENE ABEPARVOVEC": "SMN1",
    "ZOLGENSMA": "SMN1",
}


async def _resolve_target_id(label: str) -> str | None:
    """Resolve a free-text target label to a target ID using multiple strategies.

    Strategies (tried in order):
    1. Exact symbol match in DB
    2. Alias map lookup → then exact symbol match
    3. Case-insensitive partial name match in DB
    """
    if not label or not label.strip():
        return None

    normalized = label.strip().upper()

    # Strategy 1: Exact symbol match
    row = await fetchrow("SELECT id FROM targets WHERE symbol = $1", normalized)
    if row:
        return dict(row)["id"]

    # Strategy 2: Alias map → symbol lookup
    alias_symbol = TARGET_ALIASES.get(normalized)
    if alias_symbol:
        row = await fetchrow("SELECT id FROM targets WHERE symbol = $1", alias_symbol)
        if row:
            return dict(row)["id"]

    # Strategy 3: Case-insensitive partial name match
    label_lower = label.strip().lower()
    row = await fetchrow(
        "SELECT id FROM targets WHERE LOWER(name) LIKE $1 LIMIT 1",
        f"%{label_lower}%",
    )
    if row:
        return dict(row)["id"]

    return None


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
            subject_id = await _resolve_target_id(subject)

            # If subject didn't resolve, try related_targets from the LLM
            if subject_id is None:
                for rt in claim.get("related_targets", []):
                    subject_id = await _resolve_target_id(rt)
                    if subject_id:
                        break

            # Resolve object to a target ID if possible
            obj = claim.get("object")
            object_type = claim.get("object_type")
            object_id = None
            if obj:
                object_id = await _resolve_target_id(obj)

            # Insert claim and retrieve its ID atomically via RETURNING
            claim_row = await fetchrow(
                """INSERT INTO claims (claim_type, subject_id, subject_type, predicate, object_id, object_type, confidence, metadata)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id""",
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
                    "source_paper_id": str(source["id"]),
                }),
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


async def relink_all_claims() -> dict:
    """Retroactively link existing unlinked claims to targets using fuzzy matching.

    Scans all claims where subject_id IS NULL and attempts to resolve them
    using the alias map, case-insensitive name matching, related_targets
    metadata, and predicate text scanning. Also resolves object_id where possible.
    """
    rows = await fetch(
        "SELECT id, predicate, metadata FROM claims WHERE subject_id IS NULL",
    )

    # Pre-load all target symbols for predicate scanning
    all_targets = await fetch("SELECT id, symbol, name FROM targets")
    target_lookup = {dict(t)["symbol"]: str(dict(t)["id"]) for t in all_targets}
    # Build reverse alias map: alias → target_id
    alias_to_id: dict[str, str] = {}
    for alias, symbol in TARGET_ALIASES.items():
        tid = target_lookup.get(symbol)
        if tid:
            alias_to_id[alias] = tid

    claims_checked = 0
    claims_updated = 0
    targets_linked: dict[str, int] = {}

    for row in rows:
        row = dict(row)
        claims_checked += 1

        try:
            meta = json.loads(row.get("metadata") or "{}")
        except (json.JSONDecodeError, TypeError):
            meta = {}

        subject_label = meta.get("subject_label", "")
        related_targets = meta.get("related_targets", [])
        object_label = meta.get("object_label")
        predicate = row.get("predicate", "")

        # Try to resolve subject_id
        subject_id = None
        if subject_label:
            subject_id = await _resolve_target_id(subject_label)

        # If subject is a drug name, map to its MOA target
        if subject_id is None and subject_label:
            drug_target_sym = DRUG_TARGET_MAP.get(subject_label.strip().upper())
            if drug_target_sym:
                subject_id = target_lookup.get(drug_target_sym)

        # If subject didn't resolve, try each symbol in related_targets
        if subject_id is None and related_targets:
            for rt in related_targets:
                subject_id = await _resolve_target_id(rt)
                if subject_id:
                    break

        # If still not resolved, scan predicate text for target symbols/aliases
        if subject_id is None and predicate:
            pred_upper = predicate.upper()
            # Check exact target symbols in predicate
            for symbol, tid in target_lookup.items():
                if symbol in pred_upper:
                    subject_id = tid
                    break
            # Check aliases in predicate
            if subject_id is None:
                for alias, tid in alias_to_id.items():
                    if alias in pred_upper:
                        subject_id = tid
                        break
            # Check drug names in predicate → MOA target
            if subject_id is None:
                for drug_name, target_sym in DRUG_TARGET_MAP.items():
                    if drug_name in pred_upper:
                        subject_id = target_lookup.get(target_sym)
                        if subject_id:
                            break

        # Try to resolve object_id
        object_id = None
        if object_label:
            object_id = await _resolve_target_id(object_label)

        # Update if we resolved at least one
        if subject_id or object_id:
            if subject_id and object_id:
                await execute(
                    "UPDATE claims SET subject_id = $1, object_id = $2 WHERE id = $3",
                    subject_id, object_id, row["id"],
                )
            elif subject_id:
                await execute(
                    "UPDATE claims SET subject_id = $1 WHERE id = $2",
                    subject_id, row["id"],
                )
            else:
                await execute(
                    "UPDATE claims SET object_id = $1 WHERE id = $2",
                    object_id, row["id"],
                )
            claims_updated += 1

            # Track which target symbols got linked (for reporting)
            if subject_id:
                # Look up the symbol for the resolved target
                t_row = await fetchrow("SELECT symbol FROM targets WHERE id = $1", subject_id)
                if t_row:
                    sym = dict(t_row)["symbol"]
                    targets_linked[sym] = targets_linked.get(sym, 0) + 1

    logger.info(
        "Relinked %d/%d claims (targets: %s)",
        claims_updated, claims_checked, targets_linked,
    )

    return {
        "claims_checked": claims_checked,
        "claims_updated": claims_updated,
        "targets_linked": targets_linked,
    }


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
