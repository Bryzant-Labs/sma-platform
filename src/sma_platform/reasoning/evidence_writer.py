"""Evidence Summary / Grant Writing Assistant — Agent E.

Generates structured evidence summaries from the SMA evidence base using
Claude Sonnet. Supports multiple output formats: NIH grant sections, journal
introductions, executive briefings, and hypothesis rationale documents.

All summaries are grounded in database evidence — no hallucination.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

import anthropic

from ..core.config import settings
from ..core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-20250514"
AGENT_NAME = "evidence-writer-agent"

FormatType = Literal["grant_section", "paper_intro", "briefing", "hypothesis_rationale"]

# Writing instructions keyed by format type
FORMAT_INSTRUCTIONS: dict[str, str] = {
    "grant_section": (
        "Write an NIH R01-style grant section covering: "
        "1) Significance — why this target/topic matters for SMA; "
        "2) Innovation — what is new about this approach; "
        "3) Approach — the proposed experimental strategy; "
        "4) Preliminary Data — evidence from the database supporting feasibility; "
        "5) Expected Outcomes — what success looks like and alternative interpretations. "
        "Length: 800–1200 words. Use formal NIH language. "
        "Cite PMIDs inline (e.g., [PMID: 12345678]). "
        "Bold each section heading. Do not use markdown code blocks."
    ),
    "paper_intro": (
        "Write a journal introduction covering: "
        "1) Background — disease context and clinical burden of SMA; "
        "2) Landscape — current therapeutic approaches and their limitations; "
        "3) Rationale — why this specific target/topic is relevant; "
        "4) Gaps — what remains unknown; "
        "5) Aim — the specific scientific question addressed. "
        "Length: 500–800 words. Use present tense for established facts, "
        "past tense for specific experimental findings. "
        "Cite PMIDs inline. Suitable for a high-impact neuroscience journal."
    ),
    "briefing": (
        "Write an executive briefing for non-specialists (clinicians, patient advocates, funders). "
        "Structure: opening hook, what the evidence shows, why it matters for patients, "
        "key uncertainties, and recommended next steps. "
        "Length: 400–600 words. Plain language — no unexplained jargon. "
        "Still cite PMIDs for credibility but explain the findings in accessible terms. "
        "Conclude with a clear 'bottom line' paragraph."
    ),
    "hypothesis_rationale": (
        "Write a detailed hypothesis rationale document covering: "
        "1) Central Hypothesis — one precise testable statement; "
        "2) Evidence Base — systematic review of supporting claims with confidence levels; "
        "3) Mechanistic Model — proposed biological mechanism step by step; "
        "4) Testable Predictions — 3–5 specific, falsifiable predictions; "
        "5) Contradicting Evidence — any conflicting data and how to reconcile it; "
        "6) Experimental Priority — recommended first experiment with justification. "
        "Length: 600–1000 words. Scientific precision required. Cite PMIDs throughout."
    ),
}

SYSTEM_PROMPT = (
    "You are a senior scientific writer specializing in Spinal Muscular Atrophy (SMA) "
    "molecular biology and drug development. Your writing is precise, evidence-grounded, "
    "and publication-ready.\n\n"
    "Core rules:\n"
    "1. Write ONLY from the evidence provided — never introduce facts not in the context.\n"
    "2. Cite every factual claim with its PMID or source identifier.\n"
    "3. Describe mechanisms precisely: name genes, proteins, pathways, and molecular events.\n"
    "4. Acknowledge uncertainty honestly — distinguish established facts from preliminary findings.\n"
    "5. Never speculate beyond what the evidence supports.\n"
    "6. If the evidence is sparse, state the limitation explicitly.\n"
    "7. Use standard scientific nomenclature (gene symbols in italics notation if plain text: e.g., SMN2)."
)


# ---------------------------------------------------------------------------
# Evidence gathering helpers
# ---------------------------------------------------------------------------

async def _gather_target_evidence(symbol: str) -> dict[str, Any]:
    """Gather all evidence related to a gene/protein target symbol."""
    pattern = f"%{symbol}%"

    claims = await fetch(
        """SELECT c.id, c.claim_type, c.predicate, c.subject_type, c.object_type,
                  c.value, c.confidence,
                  s.title AS paper_title, s.external_id AS pmid,
                  s.journal, s.pub_date,
                  e.excerpt AS evidence_excerpt, e.method, e.p_value, e.effect_size
           FROM claims c
           LEFT JOIN evidence e ON e.claim_id = c.id
           LEFT JOIN sources s ON e.source_id = s.id
           WHERE c.subject_type ILIKE $1
              OR CAST(c.metadata AS TEXT) ILIKE $2
              OR c.predicate ILIKE $2
           ORDER BY c.confidence DESC NULLS LAST
           LIMIT 40""",
        pattern, pattern,
    )

    hypotheses = await fetch(
        """SELECT id, title, description, confidence, status, generated_by
           FROM hypotheses
           WHERE title ILIKE $1 OR description ILIKE $1
           ORDER BY confidence DESC NULLS LAST
           LIMIT 10""",
        pattern,
    )

    trials = await fetch(
        """SELECT nct_id, title, status, phase, sponsor, enrollment,
                  results_summary, start_date, completion_date
           FROM trials
           WHERE title ILIKE $1
              OR CAST(interventions AS TEXT) ILIKE $1
           ORDER BY start_date DESC NULLS LAST
           LIMIT 10""",
        pattern,
    )

    drug_outcomes = await fetch(
        """SELECT compound_name, target, outcome, mechanism, failure_reason,
                  key_finding
           FROM drug_outcomes
           WHERE target ILIKE $1
              OR compound_name ILIKE $1
           LIMIT 10""",
        pattern,
    )

    drugs = await fetch(
        """SELECT name, drug_type, mechanism, approval_status, approved_for, manufacturer
           FROM drugs
           WHERE name ILIKE $1
              OR mechanism ILIKE $1
              OR CAST(brand_names AS TEXT) ILIKE $1
           LIMIT 10""",
        pattern,
    )

    return {
        "claims": [dict(r) for r in claims],
        "hypotheses": [dict(r) for r in hypotheses],
        "trials": [dict(r) for r in trials],
        "drug_outcomes": [dict(r) for r in drug_outcomes],
        "drugs": [dict(r) for r in drugs],
    }


async def _gather_topic_evidence(topic: str) -> dict[str, Any]:
    """Gather evidence for a free-text topic (pathway, phenotype, mechanism)."""
    pattern = f"%{topic}%"

    claims = await fetch(
        """SELECT c.id, c.claim_type, c.predicate, c.subject_type, c.object_type,
                  c.value, c.confidence,
                  s.title AS paper_title, s.external_id AS pmid,
                  s.journal, s.pub_date,
                  e.excerpt AS evidence_excerpt, e.method
           FROM claims c
           LEFT JOIN evidence e ON e.claim_id = c.id
           LEFT JOIN sources s ON e.source_id = s.id
           WHERE c.predicate ILIKE $1
              OR c.claim_type ILIKE $1
              OR CAST(c.metadata AS TEXT) ILIKE $1
           ORDER BY c.confidence DESC NULLS LAST
           LIMIT 40""",
        pattern,
    )

    hypotheses = await fetch(
        """SELECT id, title, description, confidence, status
           FROM hypotheses
           WHERE title ILIKE $1 OR description ILIKE $1
           ORDER BY confidence DESC NULLS LAST
           LIMIT 10""",
        pattern,
    )

    sources = await fetch(
        """SELECT id, external_id AS pmid, title, journal, pub_date,
                  LEFT(abstract, 400) AS abstract_snippet
           FROM sources
           WHERE title ILIKE $1
              OR abstract ILIKE $1
           ORDER BY pub_date DESC NULLS LAST
           LIMIT 15""",
        pattern,
    )

    return {
        "claims": [dict(r) for r in claims],
        "hypotheses": [dict(r) for r in hypotheses],
        "sources": [dict(r) for r in sources],
        "trials": [],
        "drug_outcomes": [],
        "drugs": [],
    }


def _format_evidence_context(evidence: dict[str, Any]) -> str:
    """Format gathered evidence into structured text sections for the LLM."""
    parts: list[str] = []

    # Claims section
    claims = evidence.get("claims", [])
    if claims:
        parts.append("## Evidence Claims\n")
        for i, c in enumerate(claims, 1):
            pmid_str = f" [PMID: {c['pmid']}]" if c.get("pmid") else ""
            conf_str = f" (confidence: {c['confidence']})" if c.get("confidence") is not None else ""
            journal_str = f" — {c.get('journal', '')}" if c.get("journal") else ""
            pub_str = f" ({str(c['pub_date'])[:4]})" if c.get("pub_date") else ""
            method_str = f"\n   Method: {c['method']}" if c.get("method") else ""
            excerpt_str = f"\n   Excerpt: {c['evidence_excerpt']}" if c.get("evidence_excerpt") else ""
            effect_str = ""
            if c.get("effect_size") is not None:
                effect_str = f"\n   Effect size: {c['effect_size']}"
            if c.get("p_value") is not None:
                effect_str += f", p={c['p_value']}"
            paper_str = f" | Paper: {c['paper_title']}" if c.get("paper_title") else ""

            parts.append(
                f"{i}. [{c.get('claim_type', 'unknown')}] "
                f"{c.get('predicate', 'N/A')}"
                f"{conf_str}{pmid_str}{journal_str}{pub_str}{paper_str}"
                f"{method_str}{excerpt_str}{effect_str}\n"
            )

    # Hypotheses section
    hypotheses = evidence.get("hypotheses", [])
    if hypotheses:
        parts.append("\n## Generated Hypotheses\n")
        for h in hypotheses:
            conf_str = f" (confidence: {h['confidence']})" if h.get("confidence") is not None else ""
            parts.append(
                f"- [{h.get('status', 'unknown')}]{conf_str} {h.get('title', '')}\n"
                f"  {h.get('description', '')[:300]}...\n"
            )

    # Trials section
    trials = evidence.get("trials", [])
    if trials:
        parts.append("\n## Clinical Trials\n")
        for t in trials:
            enrollment_str = f", n={t['enrollment']}" if t.get("enrollment") else ""
            results_str = f"\n  Results: {t['results_summary']}" if t.get("results_summary") else ""
            parts.append(
                f"- {t.get('nct_id', 'N/A')}: {t.get('title', '')}\n"
                f"  Status: {t.get('status', 'unknown')}, Phase: {t.get('phase', 'N/A')}"
                f"{enrollment_str}, Sponsor: {t.get('sponsor', 'N/A')}"
                f"{results_str}\n"
            )

    # Drug outcomes section
    drug_outcomes = evidence.get("drug_outcomes", [])
    if drug_outcomes:
        parts.append("\n## Drug Outcomes / Failure Database\n")
        for d in drug_outcomes:
            reason_str = f", Failure reason: {d['failure_reason']}" if d.get("failure_reason") else ""
            notes_str = f"\n  Key Finding: {d['key_finding']}" if d.get("key_finding") else ""
            parts.append(
                f"- {d.get('compound_name', 'N/A')} targeting {d.get('target', 'N/A')}\n"
                f"  Outcome: {d.get('outcome', 'N/A')}, Mechanism: {d.get('mechanism', 'N/A')}"
                f"{reason_str}{notes_str}\n"
            )

    # Drugs section
    drugs = evidence.get("drugs", [])
    if drugs:
        parts.append("\n## Known Drugs & Therapies\n")
        for d in drugs:
            approved_str = f", Approved for: {', '.join(d['approved_for'])}" if d.get("approved_for") else ""
            parts.append(
                f"- {d.get('name', 'N/A')} [{d.get('drug_type', 'N/A')}]\n"
                f"  Status: {d.get('approval_status', 'N/A')}, "
                f"Mechanism: {d.get('mechanism', 'N/A')}"
                f"{approved_str}\n"
            )

    # Sources section (topic-based search)
    sources = evidence.get("sources", [])
    if sources:
        parts.append("\n## Source Papers\n")
        for s in sources:
            pub_str = f" ({str(s['pub_date'])[:4]})" if s.get("pub_date") else ""
            abstract_str = f"\n  Abstract: {s['abstract_snippet']}" if s.get("abstract_snippet") else ""
            parts.append(
                f"- PMID: {s.get('pmid', 'N/A')} | {s.get('title', 'Untitled')}"
                f" — {s.get('journal', '')}{pub_str}"
                f"{abstract_str}\n"
            )

    if not parts:
        return "No evidence found in the database for this subject."

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Main generation functions
# ---------------------------------------------------------------------------

def _count_evidence(evidence: dict[str, Any]) -> dict[str, int]:
    """Return evidence item counts per section."""
    return {
        "claims": len(evidence.get("claims", [])),
        "hypotheses": len(evidence.get("hypotheses", [])),
        "trials": len(evidence.get("trials", [])),
        "drug_outcomes": len(evidence.get("drug_outcomes", [])),
        "drugs": len(evidence.get("drugs", [])),
        "sources": len(evidence.get("sources", [])),
    }


async def generate_summary(
    subject: str,
    format_type: FormatType = "briefing",
    subject_type: Literal["target", "topic"] = "target",
    model: str | None = None,
) -> dict[str, Any]:
    """Generate a structured evidence summary for a gene target or research topic.

    Args:
        subject: Gene symbol (e.g. 'SMN2', 'PLS3') or free-text topic.
        format_type: Output format — grant_section, paper_intro, briefing,
                     or hypothesis_rationale.
        subject_type: 'target' for gene/protein symbols, 'topic' for free text.
        model: Override the default model (claude-sonnet-4-20250514).

    Returns:
        Dict with summary text, evidence counts, model used, and token usage.
    """
    if not settings.anthropic_api_key:
        return {
            "error": "ANTHROPIC_API_KEY not configured",
            "subject": subject,
            "format_type": format_type,
        }

    # Gather evidence from database
    if subject_type == "target":
        evidence = await _gather_target_evidence(subject)
    else:
        evidence = await _gather_topic_evidence(subject)

    evidence_counts = _count_evidence(evidence)
    total_items = sum(evidence_counts.values())

    if total_items == 0:
        return {
            "summary": (
                f"No evidence found in the database for '{subject}'. "
                "This subject may not yet be indexed. "
                "Try ingesting relevant PubMed papers or ClinicalTrials data first."
            ),
            "subject": subject,
            "format_type": format_type,
            "subject_type": subject_type,
            "evidence_counts": evidence_counts,
            "model": None,
            "usage": None,
        }

    context_text = _format_evidence_context(evidence)
    format_instruction = FORMAT_INSTRUCTIONS[format_type]
    use_model = model or MODEL

    user_message = (
        f"## Subject\n{subject}\n\n"
        f"## Format Required\n{format_instruction}\n\n"
        f"## Evidence from SMA Research Database\n\n{context_text}"
    )

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    response = await client.messages.create(
        model=use_model,
        max_tokens=2500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    summary_text = response.content[0].text if response.content else "No content generated."

    logger.info(
        "%s: generated %s for '%s' — %d evidence items, %d tokens in / %d out",
        AGENT_NAME, format_type, subject, total_items,
        response.usage.input_tokens, response.usage.output_tokens,
    )

    return {
        "summary": summary_text,
        "subject": subject,
        "format_type": format_type,
        "subject_type": subject_type,
        "evidence_counts": evidence_counts,
        "model": use_model,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
    }


async def generate_target_comparison(
    targets: list[str],
    format_type: FormatType = "briefing",
) -> dict[str, Any]:
    """Generate a comparative evidence summary across multiple gene targets.

    Gathers evidence for each target independently, then synthesises a
    comparative analysis highlighting commonalities, differences, and
    relative evidence strength.

    Args:
        targets: List of gene symbols (2–5 targets).
        format_type: Output format for the comparative document.

    Returns:
        Dict with comparative summary, per-target evidence counts, and usage.
    """
    if not settings.anthropic_api_key:
        return {
            "error": "ANTHROPIC_API_KEY not configured",
            "targets": targets,
            "format_type": format_type,
        }

    targets = targets[:5]  # Hard cap at 5 targets to control context size

    # Gather evidence per target in sequence (avoid overwhelming the DB)
    per_target_evidence: dict[str, dict[str, Any]] = {}
    per_target_counts: dict[str, dict[str, int]] = {}
    combined_context_parts: list[str] = []

    for symbol in targets:
        evidence = await _gather_target_evidence(symbol)
        per_target_evidence[symbol] = evidence
        per_target_counts[symbol] = _count_evidence(evidence)
        section_text = _format_evidence_context(evidence)
        combined_context_parts.append(f"### Target: {symbol}\n\n{section_text}")

    combined_context = "\n\n---\n\n".join(combined_context_parts)
    format_instruction = FORMAT_INSTRUCTIONS[format_type]

    comparison_instruction = (
        f"{format_instruction}\n\n"
        "Additionally, include a comparative section that:\n"
        "- Ranks the targets by total evidence strength\n"
        "- Identifies shared pathways or mechanisms\n"
        "- Highlights which target has the strongest clinical translation support\n"
        "- Notes where evidence is contradictory across targets"
    )

    user_message = (
        f"## Comparative Analysis Request\n"
        f"Targets: {', '.join(targets)}\n\n"
        f"## Format Required\n{comparison_instruction}\n\n"
        f"## Evidence from SMA Research Database\n\n{combined_context}"
    )

    use_model = MODEL
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    response = await client.messages.create(
        model=use_model,
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    summary_text = response.content[0].text if response.content else "No content generated."

    total_items = sum(sum(c.values()) for c in per_target_counts.values())
    logger.info(
        "%s: generated comparative %s for [%s] — %d total evidence items, "
        "%d tokens in / %d out",
        AGENT_NAME, format_type, ", ".join(targets), total_items,
        response.usage.input_tokens, response.usage.output_tokens,
    )

    return {
        "summary": summary_text,
        "targets": targets,
        "format_type": format_type,
        "evidence_counts_per_target": per_target_counts,
        "model": use_model,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
    }
