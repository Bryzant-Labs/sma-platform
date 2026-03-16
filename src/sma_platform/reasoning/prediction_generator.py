"""Prediction Card Generator — structures evidence into falsifiable predictions.

Uses Claude Sonnet 4.6 for structuring ONLY. All evidence comes from the claims
table. The LLM's job is to:
1. Classify claims as supporting/contradicting/neutral
2. Formulate a falsifiable prediction statement
3. Suggest experiments based on evidence gaps
4. Identify what's missing (evidence gaps)

It does NOT invent evidence or make up citations.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

import anthropic

from ..core.config import settings
from ..core.database import execute, fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
AGENT_NAME = "convergence-prediction-agent"

PREDICTION_SYSTEM_PROMPT = """You are a senior SMA researcher writing a prediction card for a grant review panel.

You are given a target name, its convergence score, and a list of evidence claims from the published literature. Your job is to:

1. CLASSIFY each claim as "supporting", "contradicting", or "neutral" for the overall research direction
2. Write ONE precise, falsifiable prediction statement (not vague — it must be testable in a lab)
3. Suggest 2-3 concrete experiments to test this prediction (model system, readout, timeline)
4. Identify 2-4 evidence gaps (what's missing that would strengthen or refute the prediction)

CRITICAL RULES:
- Every claim you reference MUST come from the provided list — do NOT invent citations
- The prediction must be falsifiable — a clear yes/no experiment could confirm or refute it
- Experiments should be practical (iPSC, mouse model, cell culture — not "launch clinical trial")

Return ONLY valid JSON with this structure:
{
    "prediction_text": "One sentence falsifiable prediction",
    "evidence_summary": {
        "supporting": [{"claim_id": "uuid", "text": "brief summary"}],
        "contradicting": [{"claim_id": "uuid", "text": "brief summary"}],
        "neutral": [{"claim_id": "uuid", "text": "brief summary"}]
    },
    "suggested_experiments": [
        {
            "title": "Short title",
            "protocol": "Model system + intervention",
            "readout": "What to measure",
            "timeline": "Estimated weeks",
            "priority": "HIGH/MEDIUM/LOW"
        }
    ],
    "evidence_gaps": ["Gap 1", "Gap 2"]
}

No markdown fences. No explanation outside JSON."""


async def generate_prediction_for_target(convergence_row: dict) -> dict | None:
    """Generate a prediction card for a target with a convergence score."""
    target_id = convergence_row.get("target_id")
    target_label = convergence_row.get("target_label", "Unknown")

    if not target_id:
        return None

    claims = await fetch(
        """SELECT c.id, c.claim_type, c.predicate, c.confidence, c.value,
                  e.source_id, e.method, e.excerpt,
                  s.title AS source_title, s.external_id AS pmid, s.source_type
           FROM claims c
           LEFT JOIN evidence e ON e.claim_id = c.id
           LEFT JOIN sources s ON e.source_id = s.id
           WHERE c.subject_id = $1
           ORDER BY c.confidence DESC""",
        target_id,
    )

    if not claims:
        return None

    # Format claims for LLM
    claims_text_lines = []
    for i, c in enumerate(claims[:30], 1):
        c = dict(c)
        source_info = ""
        if c.get("pmid"):
            source_info = f" (PMID: {c['pmid']})"
        elif c.get("source_title"):
            source_info = f" ({c['source_title'][:50]})"
        method_info = f" [method: {c['method']}]" if c.get("method") else ""
        conf = f" [confidence: {c['confidence']:.2f}]" if c.get("confidence") else ""

        claims_text_lines.append(
            f"{i}. [ID: {c['id']}] [{c['claim_type']}] {c['predicate']}{source_info}{method_info}{conf}"
        )

    claims_text = "\n".join(claims_text_lines)

    # Find linked patents
    patent_rows = await fetch(
        """SELECT id FROM sources
           WHERE source_type = 'patent'
             AND (LOWER(title) LIKE $1 OR LOWER(abstract) LIKE $1)
           LIMIT 10""",
        f"%{target_label.lower()}%",
    )
    linked_patent_ids = [str(r["id"]) for r in patent_rows]

    user_prompt = (
        f"Target: {target_label}\n"
        f"Convergence Score: {convergence_row['composite_score']:.3f} "
        f"({convergence_row['confidence_level']})\n"
        f"Claims: {convergence_row['claim_count']} from "
        f"{convergence_row['source_count']} sources\n\n"
        f"Evidence Claims:\n{claims_text}"
    )

    api_key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("No ANTHROPIC_API_KEY — generating fallback prediction for %s", target_label)
        return _fallback_prediction(convergence_row, claims, linked_patent_ids)

    try:
        client = anthropic.AsyncAnthropic(api_key=api_key)
        message = await client.messages.create(
            model=MODEL,
            max_tokens=3000,
            system=PREDICTION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        content = message.content[0].text.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [ln for ln in lines if not ln.strip().startswith("```")]
            content = "\n".join(lines).strip()

        result = json.loads(content)

    except (json.JSONDecodeError, KeyError) as e:
        logger.error("Failed to parse prediction JSON for %s: %s", target_label, e)
        return _fallback_prediction(convergence_row, claims, linked_patent_ids)
    except anthropic.APIError as e:
        logger.error("Anthropic API error for %s: %s", target_label, e)
        return _fallback_prediction(convergence_row, claims, linked_patent_ids)
    except Exception as e:
        logger.error("Unexpected error generating prediction for %s: %s", target_label, e, exc_info=True)
        return _fallback_prediction(convergence_row, claims, linked_patent_ids)

    # Extract claim IDs from LLM classification
    summary = result.get("evidence_summary", {})
    supporting_ids = [
        item["claim_id"] for item in summary.get("supporting", [])
        if isinstance(item, dict) and "claim_id" in item
    ]
    contradicting_ids = [
        item["claim_id"] for item in summary.get("contradicting", [])
        if isinstance(item, dict) and "claim_id" in item
    ]
    neutral_ids = [
        item["claim_id"] for item in summary.get("neutral", [])
        if isinstance(item, dict) and "claim_id" in item
    ]

    return {
        "prediction_text": result.get("prediction_text", ""),
        "target_label": target_label,
        "target_id": target_id,
        "convergence_score": convergence_row["composite_score"],
        "convergence_breakdown": json.dumps({
            "volume": float(convergence_row["volume"]),
            "lab_independence": float(convergence_row["lab_independence"]),
            "method_diversity": float(convergence_row["method_diversity"]),
            "temporal_trend": float(convergence_row["temporal_trend"]),
            "replication": float(convergence_row["replication"]),
        }),
        "confidence_level": convergence_row["confidence_level"],
        "supporting_claims": supporting_ids,
        "contradicting_claims": contradicting_ids,
        "neutral_claims": neutral_ids,
        "evidence_summary": json.dumps(summary),
        "suggested_experiments": json.dumps(result.get("suggested_experiments", [])),
        "evidence_gaps": result.get("evidence_gaps", []),
        "linked_patents": linked_patent_ids,
        "convergence_score_id": convergence_row.get("id"),
    }


def _fallback_prediction(convergence_row: dict, claims: list, patent_ids: list) -> dict:
    """Generate a basic prediction without LLM."""
    target_label = convergence_row.get("target_label", "Unknown")
    claim_ids = [str(dict(c)["id"]) for c in claims]

    return {
        "prediction_text": (
            f"Modulating {target_label} activity will affect SMN-dependent motor neuron "
            f"survival pathways, based on {convergence_row['claim_count']} converging claims "
            f"from {convergence_row['source_count']} independent sources."
        ),
        "target_label": target_label,
        "target_id": convergence_row.get("target_id"),
        "convergence_score": convergence_row["composite_score"],
        "convergence_breakdown": json.dumps({
            "volume": float(convergence_row["volume"]),
            "lab_independence": float(convergence_row["lab_independence"]),
            "method_diversity": float(convergence_row["method_diversity"]),
            "temporal_trend": float(convergence_row["temporal_trend"]),
            "replication": float(convergence_row["replication"]),
        }),
        "confidence_level": convergence_row["confidence_level"],
        "supporting_claims": [],
        "contradicting_claims": [],
        "neutral_claims": claim_ids,
        "evidence_summary": json.dumps({"supporting": [], "contradicting": [], "neutral": claim_ids}),
        "suggested_experiments": json.dumps([]),
        "evidence_gaps": ["LLM unavailable — all claims marked as neutral pending manual review"],
        "linked_patents": patent_ids,
        "convergence_score_id": convergence_row.get("id"),
    }


async def generate_all_predictions(min_score: float = 0.5) -> dict:
    """Generate prediction cards for all targets with convergence score >= min_score."""
    convergence_rows = await fetch(
        "SELECT * FROM convergence_scores WHERE composite_score >= $1 ORDER BY composite_score DESC",
        min_score,
    )

    generated = 0
    skipped = 0

    for conv in convergence_rows:
        conv = dict(conv)

        # Check if prediction already exists for this target + weight version
        existing = await fetchval(
            "SELECT COUNT(*) FROM prediction_cards WHERE target_id = $1 AND weights_version = $2",
            conv.get("target_id"),
            conv.get("weights_version", "v1"),
        )
        if existing and existing > 0:
            skipped += 1
            continue

        result = await generate_prediction_for_target(conv)
        if not result:
            skipped += 1
            continue

        await execute(
            """INSERT INTO prediction_cards
                (convergence_score_id, prediction_text, target_label, target_id,
                 convergence_score, convergence_breakdown, confidence_level,
                 supporting_claims, contradicting_claims, neutral_claims,
                 evidence_summary, suggested_experiments, evidence_gaps,
                 linked_patents, status, score_history, weights_version)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                       'draft', $15, $16)""",
            result["convergence_score_id"],
            result["prediction_text"],
            result["target_label"],
            result["target_id"],
            result["convergence_score"],
            result["convergence_breakdown"],
            result["confidence_level"],
            result["supporting_claims"],
            result["contradicting_claims"],
            result["neutral_claims"],
            result["evidence_summary"],
            result["suggested_experiments"],
            result["evidence_gaps"],
            result["linked_patents"],
            json.dumps([{
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "score": float(result["convergence_score"]),
                "delta": 0.0,
                "new_claims": 0,
                "note": "Initial generation",
            }]),
            conv.get("weights_version", "v1"),
        )
        generated += 1
        logger.info("Generated prediction for %s (score: %.3f)", result["target_label"], result["convergence_score"])

    logger.info("Prediction generation complete: %d generated, %d skipped", generated, skipped)
    return {
        "predictions_generated": generated,
        "predictions_skipped": skipped,
        "min_score_threshold": min_score,
    }
