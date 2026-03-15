"""Generate hypothesis cards by cross-referencing claims across targets.

A hypothesis card synthesizes multiple claims about a target into a testable
biological hypothesis with:
- Supporting evidence (claims + sources)
- Contradicting evidence (if any)
- Confidence score based on convergence
- Rationale trace explaining why this target matters
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

HYPOTHESIS_PROMPT = """You are a senior SMA (Spinal Muscular Atrophy) research scientist synthesizing evidence.

Given the following claims about a biological target, generate a hypothesis card.

Target: {target_symbol} ({target_name})
Target type: {target_type}
Target description: {target_desc}

Claims from the evidence base:
{claims_text}

Generate a hypothesis card with:
1. title: A concise hypothesis statement (one sentence)
2. description: A 2-3 paragraph scientific rationale explaining:
   - What the evidence shows about this target in SMA
   - Why this target could be a therapeutic intervention point
   - What gaps remain in the evidence
3. confidence: Your confidence this is a real, testable hypothesis (0.0-1.0)
4. status: One of [proposed, under_review, validated]
5. modality_suggestion: Which therapeutic approach fits best (small_molecule, aso, gene_therapy, crispr, antibody, combination, unclear)
6. key_questions: 2-3 specific questions that need answering to validate this hypothesis

Return ONLY valid JSON. No markdown fences, no explanation."""


async def get_target_claims(target_id: str) -> list[dict]:
    """Get all claims linked to a target (via subject_id or metadata)."""
    # Direct links via subject_id
    direct = await fetch(
        """SELECT c.*, e.source_id, s.title as paper_title, s.external_id as pmid
           FROM claims c
           LEFT JOIN evidence e ON e.claim_id = c.id
           LEFT JOIN sources s ON e.source_id = s.id
           WHERE c.subject_id = $1
           ORDER BY c.confidence DESC""",
        target_id,
    )

    # Also find claims mentioning this target in metadata
    target_row = await fetchrow("SELECT symbol FROM targets WHERE id = $1", target_id)
    if not target_row:
        return [dict(r) for r in direct]

    symbol = dict(target_row)["symbol"]
    metadata_matches = await fetch(
        """SELECT c.*, e.source_id, s.title as paper_title, s.external_id as pmid
           FROM claims c
           LEFT JOIN evidence e ON e.claim_id = c.id
           LEFT JOIN sources s ON e.source_id = s.id
           WHERE CAST(c.metadata AS TEXT) LIKE $1
           ORDER BY c.confidence DESC""",
        f'%"{symbol}"%',
    )

    # Merge and deduplicate by claim id
    seen = set()
    results = []
    for row in list(direct) + list(metadata_matches):
        row = dict(row)
        if row["id"] not in seen:
            seen.add(row["id"])
            results.append(row)
    return results


async def generate_hypothesis_for_target(target_id: str) -> dict | None:
    """Generate a hypothesis card for a single target."""
    target = await fetchrow("SELECT * FROM targets WHERE id = $1", target_id)
    if not target:
        return None
    target = dict(target)

    claims = await get_target_claims(target_id)
    if len(claims) < 1:
        logger.info("No claims for target %s, skipping", target["symbol"])
        return None

    # Format claims for the prompt
    claims_lines = []
    source_ids = set()
    for i, c in enumerate(claims[:20], 1):  # Cap at 20 claims
        paper = f" (PMID: {c['pmid']})" if c.get("pmid") else ""
        conf = f" [confidence: {c['confidence']}]" if c.get("confidence") else ""
        claims_lines.append(f"{i}. {c['predicate']}{paper}{conf}")
        if c.get("source_id"):
            source_ids.add(c["source_id"])

    if not claims_lines:
        return None

    claims_text = "\n".join(claims_lines)

    api_key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("No ANTHROPIC_API_KEY — generating basic hypothesis without LLM")
        return _generate_basic_hypothesis(target, claims, source_ids)

    prompt = HYPOTHESIS_PROMPT.format(
        target_symbol=target["symbol"],
        target_name=target.get("name", ""),
        target_type=target.get("target_type", ""),
        target_desc=target.get("description", ""),
        claims_text=claims_text,
    )

    try:
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
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )

        if resp.status_code != 200:
            logger.error("Claude API error %d: %s", resp.status_code, resp.text[:200])
            return _generate_basic_hypothesis(target, claims, source_ids)

        content = resp.json()["content"][0]["text"].strip()
        # Strip markdown fences
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines).strip()

        hypothesis = json.loads(content)
    except (json.JSONDecodeError, KeyError, Exception) as e:
        logger.error("Failed to parse hypothesis from LLM: %s", e)
        return _generate_basic_hypothesis(target, claims, source_ids)

    # Store in database — map LLM status to valid CHECK constraint values
    VALID_STATUSES = {"proposed", "under_review", "validated", "refuted", "published"}
    STATUS_MAP = {
        "needs_validation": "under_review",
        "strong_candidate": "validated",
        "weak": "proposed",
    }
    raw_status = hypothesis.get("status", "proposed")
    mapped_status = STATUS_MAP.get(raw_status, raw_status)
    if mapped_status not in VALID_STATUSES:
        mapped_status = "proposed"

    claim_ids = [str(c["id"]) for c in claims]
    hyp_data = {
        "hypothesis_type": "target",
        "title": hypothesis.get("title", f"Hypothesis for {target['symbol']}"),
        "description": hypothesis.get("description", ""),
        "rationale": hypothesis.get("description", ""),
        "supporting_evidence": claim_ids,
        "confidence": hypothesis.get("confidence", 0.5),
        "status": mapped_status,
        "generated_by": "claude-haiku-4-5-20251001",
        "metadata": json.dumps({
            "target_id": str(target_id),
            "target_symbol": target["symbol"],
            "claim_count": len(claims),
            "source_count": len(source_ids),
            "modality_suggestion": hypothesis.get("modality_suggestion", "unclear"),
            "key_questions": hypothesis.get("key_questions", []),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }),
    }

    await execute(
        """INSERT INTO hypotheses (hypothesis_type, title, description, rationale,
           supporting_evidence, confidence, status, generated_by, metadata)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
        hyp_data["hypothesis_type"], hyp_data["title"], hyp_data["description"],
        hyp_data["rationale"], hyp_data["supporting_evidence"], hyp_data["confidence"],
        hyp_data["status"], hyp_data["generated_by"], hyp_data["metadata"],
    )

    logger.info("Generated hypothesis for %s: %s (confidence: %.2f)",
                target["symbol"], hyp_data["title"][:80], hyp_data["confidence"])
    return hyp_data


def _generate_basic_hypothesis(target: dict, claims: list, source_ids: set) -> dict:
    """Fallback hypothesis generation without LLM."""
    avg_conf = sum(c.get("confidence", 0.5) for c in claims) / max(len(claims), 1)
    claim_types = set(c.get("claim_type", "") for c in claims)

    title = f"{target['symbol']} is implicated in SMA pathogenesis based on {len(claims)} converging claims"
    desc = (
        f"{target.get('name', target['symbol'])} ({target.get('target_type', 'unknown')}) "
        f"has {len(claims)} claims from {len(source_ids)} independent sources. "
        f"Claim types: {', '.join(claim_types)}. "
        f"Average confidence: {avg_conf:.2f}. "
        f"{target.get('description', '')}"
    )

    return {
        "title": title,
        "description": desc,
        "confidence": round(avg_conf, 3),
        "status": "proposed",
        "modality_suggestion": "unclear",
        "key_questions": [],
    }


async def generate_all_hypotheses() -> dict:
    """Generate hypothesis cards for all targets that have claims.

    Uses modality-split generation: each target gets multiple hypotheses
    (one per claim-type cluster), producing 20-50+ hypothesis cards.

    Incremental: deletes old hypotheses per-target only after new ones
    are successfully generated, so a timeout won't wipe the database.
    """
    targets = await fetch("SELECT id, symbol FROM targets ORDER BY symbol")
    generated = 0
    skipped = 0

    for t in targets:
        t = dict(t)
        target_id = t["id"]

        # Generate new hypotheses for this target first
        results = await generate_modality_hypotheses_safe(target_id)
        if results:
            # Only delete old hypotheses for this target after success
            await execute(
                "DELETE FROM hypotheses WHERE CAST(metadata AS TEXT) LIKE $1",
                f'%"target_id": "{target_id}"%',
            )
            # Re-insert the new ones
            for hyp in results:
                await execute(
                    """INSERT INTO hypotheses (hypothesis_type, title, description, rationale,
                       supporting_evidence, confidence, status, generated_by, metadata)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                    hyp["hypothesis_type"], hyp["title"], hyp["description"],
                    hyp["rationale"], hyp["supporting_evidence"], hyp["confidence"],
                    hyp["status"], hyp["generated_by"], hyp["metadata"],
                )
            generated += len(results)
        else:
            skipped += 1

    total_claims = await fetchrow("SELECT count(*) as cnt FROM claims")
    total_evidence = await fetchrow("SELECT count(*) as cnt FROM evidence")

    return {
        "hypotheses_generated": generated,
        "targets_skipped": skipped,
        "total_claims": dict(total_claims)["cnt"] if total_claims else 0,
        "total_evidence": dict(total_evidence)["cnt"] if total_evidence else 0,
    }


async def generate_modality_hypotheses_safe(target_id: str) -> list[dict] | None:
    """Generate modality hypotheses for a target, returning raw data dicts
    without inserting into DB (caller handles insert/replace)."""
    target = await fetchrow("SELECT * FROM targets WHERE id = $1", target_id)
    if not target:
        return None
    target = dict(target)

    all_claims = await get_target_claims(target_id)
    if not all_claims:
        return None

    # Group claims by type
    clusters: dict[str, list[dict]] = {}
    for c in all_claims:
        ct = c.get("claim_type", "other")
        clusters.setdefault(ct, []).append(c)

    # Merge tiny clusters into "other"
    MIN_CLUSTER = 2
    merged = {}
    other = clusters.pop("other", [])
    for ct, claims in clusters.items():
        if len(claims) >= MIN_CLUSTER:
            merged[ct] = claims
        else:
            other.extend(claims)
    if other:
        merged["other"] = other

    results = []
    for claim_type, claims in merged.items():
        if len(claims) < 1:
            continue

        claims_lines = []
        source_ids = set()
        for i, c in enumerate(claims[:15], 1):
            paper = f" (PMID: {c['pmid']})" if c.get("pmid") else ""
            conf = f" [confidence: {c['confidence']}]" if c.get("confidence") else ""
            claims_lines.append(f"{i}. {c['predicate']}{paper}{conf}")
            if c.get("source_id"):
                source_ids.add(c["source_id"])

        if not claims_lines:
            continue

        modality_label = claim_type.replace("_", " ").title()
        prompt = HYPOTHESIS_PROMPT.format(
            target_symbol=target["symbol"],
            target_name=target.get("name", ""),
            target_type=target.get("target_type", ""),
            target_desc=target.get("description", ""),
            claims_text=f"[Focus area: {modality_label}]\n" + "\n".join(claims_lines),
        )

        api_key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            hyp = _generate_basic_hypothesis(target, claims, source_ids)
            hyp["title"] = f"[{modality_label}] {hyp['title']}"
        else:
            try:
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
                            "max_tokens": 2000,
                            "messages": [{"role": "user", "content": prompt}],
                        },
                    )

                if resp.status_code != 200:
                    hyp = _generate_basic_hypothesis(target, claims, source_ids)
                    hyp["title"] = f"[{modality_label}] {hyp['title']}"
                else:
                    content = resp.json()["content"][0]["text"].strip()
                    if content.startswith("```"):
                        lines = content.split("\n")
                        lines = [l for l in lines if not l.strip().startswith("```")]
                        content = "\n".join(lines).strip()
                    hyp = json.loads(content)
            except Exception as e:
                logger.error("Failed to generate modality hypothesis: %s", e)
                hyp = _generate_basic_hypothesis(target, claims, source_ids)
                hyp["title"] = f"[{modality_label}] {hyp['title']}"

        # Build storable dict (don't insert yet — caller handles that)
        VALID_STATUSES = {"proposed", "under_review", "validated", "refuted", "published"}
        STATUS_MAP = {"needs_validation": "under_review", "strong_candidate": "validated", "weak": "proposed"}
        raw_status = hyp.get("status", "proposed")
        mapped_status = STATUS_MAP.get(raw_status, raw_status)
        if mapped_status not in VALID_STATUSES:
            mapped_status = "proposed"

        claim_ids = [str(c["id"]) for c in claims]
        results.append({
            "hypothesis_type": "target",
            "title": hyp.get("title", f"[{modality_label}] Hypothesis for {target['symbol']}"),
            "description": hyp.get("description", ""),
            "rationale": hyp.get("description", ""),
            "supporting_evidence": claim_ids,
            "confidence": hyp.get("confidence", 0.5),
            "status": mapped_status,
            "generated_by": "claude-haiku-4-5-20251001",
            "metadata": json.dumps({
                "target_id": str(target_id),
                "target_symbol": target["symbol"],
                "claim_type": claim_type,
                "claim_count": len(claims),
                "source_count": len(source_ids),
                "modality_suggestion": hyp.get("modality_suggestion", "unclear"),
                "key_questions": hyp.get("key_questions", []),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }),
        })

        logger.info("Generated [%s] hypothesis for %s (confidence: %.2f)",
                     claim_type, target["symbol"], hyp.get("confidence", 0.5))

    return results if results else None
