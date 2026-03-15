"""Agent D — Hypothesis Auto-Generator via Evidence Convergence.

Scans recent claims, groups them by target (subject/object), identifies
convergence signals where 3+ claims from different sources point to the
same target, and uses Claude Haiku to synthesize testable hypotheses.

Differs from hypothesis_generator.py (target-centric, regenerates all)
in that this module is *incremental* — it only processes new evidence
and avoids re-generating hypotheses for already-covered convergences.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

import anthropic

from ..core.config import settings
from ..core.database import execute, fetch, fetchrow, fetchval
from .blackboard import auto_post_discovery

logger = logging.getLogger(__name__)

AGENT_NAME = "convergence-hypothesis-agent"
MODEL = "claude-sonnet-4-6"

SYNTHESIS_SYSTEM_PROMPT = (
    "You are a principal investigator at a major SMA (Spinal Muscular Atrophy) research institute. "
    "Given converging evidence claims about a molecular target, synthesize one specific, "
    "mechanistic, testable hypothesis. Go beyond 'X is implicated in SMA' — explain the "
    "specific molecular pathway and how it connects to motor neuron survival or SMN biology.\n\n"
    "Format your response as valid JSON with these fields:\n"
    '{"hypothesis": "Precise mechanistic statement (e.g. PLS3 rescues motor neuron degeneration '
    'by compensating for impaired actin dynamics at the growth cone)", '
    '"mechanism": "2-3 sentences explaining the molecular pathway with citations to PMIDs from the evidence", '
    '"testable_prediction": "A specific, experimentally testable prediction with model system and readout", '
    '"confidence": float 0-1, '
    '"evidence_summary": "How many sources, what types of evidence, and how they converge", '
    '"contradictions": "Any conflicting evidence or caveats (empty string if none)", '
    '"experimental_suggestion": "One concrete experiment to test this hypothesis"}\n'
    "Return ONLY the JSON object. No markdown fences, no explanation."
)


# ---------------------------------------------------------------------------
# Step 1 — Find convergence signals
# ---------------------------------------------------------------------------

async def find_convergence_signals(
    days_back: int = 7,
    min_claims: int = 3,
) -> list[dict]:
    """Find claim clusters where multiple sources converge on the same target.

    Groups claims from the last *days_back* days by their subject (type + id)
    and returns groups that have >= *min_claims* from >= 2 different sources.
    """
    # Get recent claims joined to evidence/sources so we can count distinct sources
    rows = await fetch(
        """
        SELECT
            c.id            AS claim_id,
            c.claim_type,
            c.subject_id,
            c.subject_type,
            c.object_id,
            c.object_type,
            c.predicate,
            c.confidence,
            c.value,
            e.source_id,
            s.title         AS source_title,
            s.external_id   AS pmid
        FROM claims c
        LEFT JOIN evidence e ON e.claim_id = c.id
        LEFT JOIN sources s  ON e.source_id = s.id
        WHERE c.created_at >= CURRENT_TIMESTAMP - ($1 || ' days')::interval
        ORDER BY c.created_at DESC
        """,
        str(days_back),
    )

    # Group by target key = (subject_type, subject_id)
    groups: dict[str, dict] = {}
    for row in rows:
        r = dict(row)
        # Use subject as the primary grouping target
        key = f"{r['subject_type'] or 'unknown'}:{r['subject_id'] or 'none'}"
        if key not in groups:
            groups[key] = {
                "target_key": key,
                "subject_type": r["subject_type"],
                "subject_id": str(r["subject_id"]) if r["subject_id"] else None,
                "claims": [],
                "source_ids": set(),
                "claim_types": set(),
            }
        g = groups[key]
        g["claims"].append({
            "claim_id": str(r["claim_id"]),
            "claim_type": r["claim_type"],
            "predicate": r["predicate"],
            "confidence": float(r["confidence"]) if r["confidence"] is not None else 0.5,
            "value": r["value"],
            "source_id": str(r["source_id"]) if r["source_id"] else None,
            "source_title": r["source_title"],
            "pmid": r["pmid"],
            "object_id": str(r["object_id"]) if r["object_id"] else None,
            "object_type": r["object_type"],
        })
        if r["source_id"]:
            g["source_ids"].add(str(r["source_id"]))
        if r["claim_type"]:
            g["claim_types"].add(r["claim_type"])

    # Also group by object key for bidirectional convergence
    for row in rows:
        r = dict(row)
        if not r["object_id"]:
            continue
        key = f"{r['object_type'] or 'unknown'}:{r['object_id']}"
        if key not in groups:
            groups[key] = {
                "target_key": key,
                "subject_type": r["object_type"],
                "subject_id": str(r["object_id"]),
                "claims": [],
                "source_ids": set(),
                "claim_types": set(),
            }
        g = groups[key]
        # Avoid duplicating the same claim_id
        existing_ids = {c["claim_id"] for c in g["claims"]}
        claim_id_str = str(r["claim_id"])
        if claim_id_str not in existing_ids:
            g["claims"].append({
                "claim_id": claim_id_str,
                "claim_type": r["claim_type"],
                "predicate": r["predicate"],
                "confidence": float(r["confidence"]) if r["confidence"] is not None else 0.5,
                "value": r["value"],
                "source_id": str(r["source_id"]) if r["source_id"] else None,
                "source_title": r["source_title"],
                "pmid": r["pmid"],
                "object_id": str(r["subject_id"]) if r["subject_id"] else None,
                "object_type": r["subject_type"],
            })
            if r["source_id"]:
                g["source_ids"].add(str(r["source_id"]))
            if r["claim_type"]:
                g["claim_types"].add(r["claim_type"])

    # Filter: require min_claims AND >= 2 different sources
    signals: list[dict] = []
    for g in groups.values():
        claim_count = len(g["claims"])
        source_count = len(g["source_ids"])
        if claim_count >= min_claims and source_count >= 2:
            # Try to resolve a human-readable target name
            target_label = await _resolve_target_label(
                g["subject_type"], g["subject_id"]
            )
            signals.append({
                "target_key": g["target_key"],
                "target_label": target_label,
                "subject_type": g["subject_type"],
                "subject_id": g["subject_id"],
                "claim_count": claim_count,
                "source_count": source_count,
                "claim_types": sorted(g["claim_types"]),
                "claims": g["claims"],
            })

    # Sort by claim_count desc so strongest signals come first
    signals.sort(key=lambda s: s["claim_count"], reverse=True)
    return signals


async def _resolve_target_label(subject_type: str | None, subject_id: str | None) -> str:
    """Best-effort resolve a human-readable label for the target."""
    if not subject_id:
        return "unknown"

    if subject_type == "target":
        row = await fetchrow(
            "SELECT symbol, name FROM targets WHERE id = $1",
            subject_id,
        )
        if row:
            r = dict(row)
            return r.get("symbol") or r.get("name") or subject_id

    if subject_type == "drug":
        row = await fetchrow(
            "SELECT name FROM drugs WHERE id = $1",
            subject_id,
        )
        if row:
            return dict(row).get("name") or subject_id

    return subject_id


# ---------------------------------------------------------------------------
# Step 2 — Generate a hypothesis from a convergence signal
# ---------------------------------------------------------------------------

async def generate_hypothesis(signal: dict) -> dict:
    """Call Claude Haiku to synthesize a testable hypothesis from converging claims."""
    # Format claims for the prompt
    claims_text_lines = []
    for i, c in enumerate(signal["claims"][:20], 1):  # Cap at 20 for context window
        source = ""
        if c.get("pmid"):
            source = f" (PMID: {c['pmid']})"
        elif c.get("source_title"):
            source = f" (Source: {c['source_title'][:60]})"
        conf = f" [confidence: {c['confidence']:.2f}]" if c.get("confidence") else ""
        claims_text_lines.append(
            f"{i}. [{c['claim_type']}] {c['predicate']}{source}{conf}"
        )

    claims_text = "\n".join(claims_text_lines)
    target_label = signal.get("target_label", signal["target_key"])

    user_prompt = (
        f"Target: {target_label} ({signal['subject_type']})\n"
        f"Number of converging claims: {signal['claim_count']} "
        f"from {signal['source_count']} independent sources\n"
        f"Claim types represented: {', '.join(signal['claim_types'])}\n\n"
        f"Claims:\n{claims_text}"
    )

    api_key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("No ANTHROPIC_API_KEY — generating fallback hypothesis")
        return _fallback_hypothesis(signal)

    try:
        client = anthropic.AsyncAnthropic(api_key=api_key)
        message = await client.messages.create(
            model=MODEL,
            max_tokens=1500,
            system=SYNTHESIS_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        content = message.content[0].text.strip()
        # Strip markdown fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [ln for ln in lines if not ln.strip().startswith("```")]
            content = "\n".join(lines).strip()

        hypothesis = json.loads(content)

    except (json.JSONDecodeError, KeyError) as e:
        logger.error("Failed to parse LLM hypothesis JSON: %s", e)
        return _fallback_hypothesis(signal)
    except anthropic.APIError as e:
        logger.error("Anthropic API error during hypothesis generation: %s", e)
        return _fallback_hypothesis(signal)
    except Exception as e:
        logger.error("Unexpected error generating hypothesis: %s", e, exc_info=True)
        return _fallback_hypothesis(signal)

    # Normalize and validate confidence
    raw_conf = hypothesis.get("confidence", 0.5)
    try:
        confidence = max(0.0, min(1.0, float(raw_conf)))
    except (ValueError, TypeError):
        confidence = 0.5

    return {
        "hypothesis": hypothesis.get("hypothesis", ""),
        "mechanism": hypothesis.get("mechanism", ""),
        "testable_prediction": hypothesis.get("testable_prediction", ""),
        "confidence": round(confidence, 2),
        "evidence_summary": hypothesis.get("evidence_summary", ""),
        "target_key": signal["target_key"],
        "target_label": signal.get("target_label", ""),
        "claim_count": signal["claim_count"],
        "source_count": signal["source_count"],
        "claim_types": signal["claim_types"],
        "claim_ids": [c["claim_id"] for c in signal["claims"]],
        "generated_by": MODEL,
    }


def _fallback_hypothesis(signal: dict) -> dict:
    """Generate a basic hypothesis without LLM when API is unavailable."""
    target_label = signal.get("target_label", signal["target_key"])
    avg_conf = sum(
        c.get("confidence", 0.5) for c in signal["claims"]
    ) / max(len(signal["claims"]), 1)

    claim_types_str = ", ".join(signal["claim_types"])
    return {
        "hypothesis": (
            f"{target_label} is a convergent node in SMA pathogenesis based on "
            f"{signal['claim_count']} claims from {signal['source_count']} "
            f"independent sources ({claim_types_str})."
        ),
        "mechanism": "Multiple lines of evidence converge on this target. Manual review required.",
        "testable_prediction": (
            f"Modulating {target_label} activity should affect SMN protein levels "
            f"or motor neuron survival in SMA model systems."
        ),
        "confidence": round(avg_conf, 2),
        "evidence_summary": (
            f"{signal['claim_count']} claims spanning {claim_types_str} "
            f"from {signal['source_count']} sources."
        ),
        "target_key": signal["target_key"],
        "target_label": target_label,
        "claim_count": signal["claim_count"],
        "source_count": signal["source_count"],
        "claim_types": signal["claim_types"],
        "claim_ids": [c["claim_id"] for c in signal["claims"]],
        "generated_by": "fallback",
    }


# ---------------------------------------------------------------------------
# Step 3 — Check for existing hypotheses to avoid duplicates
# ---------------------------------------------------------------------------

async def _hypothesis_exists_for_target(target_key: str) -> bool:
    """Check if a convergence hypothesis already exists for this target key."""
    # Search metadata JSONB for the target_key
    count = await fetchval(
        """SELECT COUNT(*) FROM hypotheses
           WHERE generated_by = $1
             AND CAST(metadata AS TEXT) LIKE $2""",
        AGENT_NAME,
        f'%"target_key": "{target_key}"%',
    )
    return (count or 0) > 0


# ---------------------------------------------------------------------------
# Step 4 — Orchestrator: find signals, generate, store, post
# ---------------------------------------------------------------------------

async def run_hypothesis_generation(
    days_back: int = 7,
    min_claims: int = 3,
    dry_run: bool = False,
) -> dict:
    """Full pipeline: find convergence signals, generate and store hypotheses.

    Parameters
    ----------
    days_back : look back this many days for recent claims
    min_claims : minimum claims required for a convergence signal
    dry_run : if True, find signals and generate hypotheses but do NOT persist

    Returns
    -------
    dict with keys: signals_found, hypotheses_generated, hypotheses_skipped, details
    """
    signals = await find_convergence_signals(
        days_back=days_back,
        min_claims=min_claims,
    )

    generated: list[dict] = []
    skipped: list[dict] = []

    for signal in signals:
        # Dedup check
        if await _hypothesis_exists_for_target(signal["target_key"]):
            skipped.append({
                "target_key": signal["target_key"],
                "target_label": signal.get("target_label", ""),
                "reason": "hypothesis already exists",
            })
            continue

        hypothesis = await generate_hypothesis(signal)

        if not dry_run:
            # Insert into hypotheses table
            hyp_metadata = json.dumps({
                "target_key": signal["target_key"],
                "target_label": signal.get("target_label", ""),
                "claim_count": signal["claim_count"],
                "source_count": signal["source_count"],
                "claim_types": signal["claim_types"],
                "claim_ids": hypothesis.get("claim_ids", []),
                "mechanism": hypothesis.get("mechanism", ""),
                "testable_prediction": hypothesis.get("testable_prediction", ""),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            })

            await execute(
                """INSERT INTO hypotheses
                       (hypothesis_type, title, description, rationale,
                        supporting_evidence, confidence, status,
                        generated_by, metadata)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                "mechanism",  # hypothesis_type — convergence is mechanistic
                hypothesis["hypothesis"][:500],  # title (capped)
                hypothesis["evidence_summary"],  # description
                hypothesis["mechanism"],  # rationale
                hypothesis.get("claim_ids", []),  # supporting_evidence UUID[]
                hypothesis["confidence"],
                "proposed",
                AGENT_NAME,  # generated_by
                hyp_metadata,
            )

            # Post to blackboard
            try:
                await auto_post_discovery(
                    agent_name=AGENT_NAME,
                    title=f"Convergence hypothesis: {signal.get('target_label', signal['target_key'])}",
                    findings_dict={
                        "hypothesis": hypothesis["hypothesis"],
                        "mechanism": hypothesis.get("mechanism", ""),
                        "testable_prediction": hypothesis.get("testable_prediction", ""),
                        "confidence": hypothesis["confidence"],
                        "targets": [signal.get("target_label", signal["target_key"])],
                        "claim_count": signal["claim_count"],
                        "source_count": signal["source_count"],
                    },
                )
            except Exception as e:
                logger.error(
                    "Failed to post hypothesis to blackboard for %s: %s",
                    signal["target_key"], e,
                )

        generated.append({
            "target_key": signal["target_key"],
            "target_label": signal.get("target_label", ""),
            "hypothesis": hypothesis["hypothesis"],
            "confidence": hypothesis["confidence"],
            "claim_count": signal["claim_count"],
            "source_count": signal["source_count"],
            "dry_run": dry_run,
        })

    return {
        "signals_found": len(signals),
        "hypotheses_generated": len(generated),
        "hypotheses_skipped": len(skipped),
        "dry_run": dry_run,
        "details": generated,
        "skipped": skipped,
    }
