"""Conversational Research Assistant — RAG over SMA evidence base.

Takes a natural language question, retrieves relevant claims and sources
via hybrid search, then synthesizes a grounded answer using Claude.

Part of Phase 8.1 — Knowledge Infrastructure.
"""

from __future__ import annotations

import logging
from typing import Any

import anthropic

from ..core.config import settings
from ..core.database import fetchrow
from .embeddings import hybrid_search, _ensure_index

logger = logging.getLogger(__name__)

# Use Sonnet for quality research answers (Pro, not Lite)
MODEL = "claude-sonnet-4-20250514"
MAX_CONTEXT_CLAIMS = 15
MAX_CONTEXT_SOURCES = 10

SYSTEM_PROMPT = """You are the SMA Research Platform AI assistant — an expert in Spinal Muscular Atrophy molecular biology and drug development.

You answer questions based ONLY on the evidence provided in the context below. If the evidence is insufficient, say so clearly rather than speculating.

Rules:
1. Cite specific claims by their number (e.g., "CLAIM-12345") and papers by PMID (e.g., "PMID: 12345678")
2. Distinguish between established facts and hypothetical connections
3. Note confidence levels when available
4. If asked about approved therapies (nusinersen, risdiplam, onasemnogene), provide accurate mechanism info
5. Be precise about molecular mechanisms — this is for researchers, not patients
6. If multiple claims conflict, present both sides with their evidence strength

Format your answer with clear sections when appropriate. Include a "Sources" section at the end listing the papers you referenced."""


async def _retrieve_context(query: str, top_k: int = 30) -> dict[str, Any]:
    """Search the evidence base and retrieve full context for the top results."""
    # Run hybrid search
    results = await hybrid_search(query, top_k=top_k)

    claim_ids = []
    source_ids = []
    for r in results:
        if r["type"] == "claim":
            claim_ids.append(r["id"])
        elif r["type"] == "source":
            source_ids.append(r["id"])

    # Fetch full claim details with source context
    claims_context = []
    for cid in claim_ids[:MAX_CONTEXT_CLAIMS]:
        row = await fetchrow(
            """SELECT c.id, c.claim_number, c.claim_type, c.predicate, c.subject_type, c.object_type,
                      c.confidence, c.metadata,
                      s.title AS source_title, s.external_id AS source_pmid,
                      s.journal, s.pub_date,
                      e.excerpt AS evidence_excerpt
               FROM claims c
               LEFT JOIN evidence e ON e.claim_id = c.id
               LEFT JOIN sources s ON e.source_id = s.id
               WHERE c.id = $1
               LIMIT 1""",
            cid,
        )
        if row:
            d = dict(row)
            # Serialize dates
            if d.get("pub_date"):
                d["pub_date"] = str(d["pub_date"])
            claims_context.append(d)

    # Fetch full source details
    sources_context = []
    for sid in source_ids[:MAX_CONTEXT_SOURCES]:
        row = await fetchrow(
            """SELECT id, title, external_id, journal, pub_date, doi,
                      LEFT(abstract, 500) AS abstract_snippet
               FROM sources WHERE id = $1""",
            sid,
        )
        if row:
            d = dict(row)
            if d.get("pub_date"):
                d["pub_date"] = str(d["pub_date"])
            sources_context.append(d)

    return {
        "claims": claims_context,
        "sources": sources_context,
        "search_results_count": len(results),
    }


def _format_context(context: dict[str, Any]) -> str:
    """Format retrieved context into a structured text block for the LLM."""
    parts = []

    if context["claims"]:
        parts.append("## Relevant Claims from Evidence Base\n")
        for i, c in enumerate(context["claims"], 1):
            conf = f" (confidence: {c['confidence']})" if c.get("confidence") else ""
            source = (
                f" — Source: {c.get('source_title', 'Unknown')}"
                f" (PMID: {c.get('source_pmid', 'N/A')})"
            )
            excerpt = (
                f"\n   Evidence: {c['evidence_excerpt']}"
                if c.get("evidence_excerpt")
                else ""
            )
            claim_label = f"CLAIM-{c['claim_number']:05d}" if c.get('claim_number') else f"#{str(c['id'])[:8]}"
            parts.append(
                f"{i}. [{claim_label}] [{c.get('claim_type', '')}] "
                f"{c.get('subject_type', '')} → {c.get('predicate', '')} → "
                f"{c.get('object_type', '')}"
                f"{conf}{source}{excerpt}\n"
            )

    if context["sources"]:
        parts.append("\n## Relevant Source Papers\n")
        for s in context["sources"]:
            parts.append(
                f"- [{s.get('title', 'Untitled')}] "
                f"PMID: {s.get('external_id', 'N/A')} | "
                f"{s.get('journal', '')} ({s.get('pub_date', '')})\n"
                f"  Abstract: {s.get('abstract_snippet', 'N/A')}\n"
            )

    return "\n".join(parts)


async def ask(
    question: str,
    max_context: int = 30,
    model: str | None = None,
) -> dict[str, Any]:
    """Answer a research question using RAG over the SMA evidence base.

    Args:
        question: Natural language research question
        max_context: Max search results to use as context
        model: Override the default model

    Returns:
        Dict with answer, sources_used, model, and context stats
    """
    # Check if index is available
    if not _ensure_index():
        return {
            "answer": (
                "The search index has not been built yet. "
                "Please run POST /search/reindex first."
            ),
            "sources_used": 0,
            "model": None,
            "error": "index_not_built",
        }

    # Retrieve relevant context
    context = await _retrieve_context(question, top_k=max_context)

    if not context["claims"] and not context["sources"]:
        return {
            "answer": (
                "No relevant evidence found in the database for this question. "
                "Try rephrasing or broadening your query."
            ),
            "sources_used": 0,
            "model": None,
        }

    # Format context for LLM
    context_text = _format_context(context)

    # Call Claude
    use_model = model or MODEL
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    response = await client.messages.create(
        model=use_model,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"## Evidence Context\n\n{context_text}\n\n"
                    f"## Research Question\n\n{question}"
                ),
            }
        ],
    )

    answer_text = (
        response.content[0].text if response.content else "No response generated."
    )

    return {
        "answer": answer_text,
        "question": question,
        "model": use_model,
        "sources_used": len(context["claims"]) + len(context["sources"]),
        "claims_in_context": len(context["claims"]),
        "sources_in_context": len(context["sources"]),
        "search_results_total": context["search_results_count"],
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
    }


CHAT_SYSTEM_PROMPT = """You are the SMA Research Platform AI assistant — an expert in Spinal Muscular Atrophy molecular biology and drug development.

You combine the evidence database with deep SMA domain knowledge. Answer questions using the evidence context provided, supplemented by your knowledge of SMA biology when the database lacks specific claims.

## Key Platform Findings (as of March 2026):

### Targets & Pathways
- 58 molecular targets tracked. Primary: SMN1/SMN2. Key modifiers: PLS3, NCALD, STMN2, UBA1, CORO1C.
- **ROCK-LIMK-Cofilin-Actin Rod Axis**: strongest convergence signal across 5 research streams. ROCK2 hyperactivation → LIMK phosphorylation → cofilin inactivation → actin rod formation → axonal transport block.
- **p53-mediated motor neuron death** (Simon et al.): SMN deficiency → Mdm2/Mdm4 mis-splicing → p53 de-repression → selective motor neuron apoptosis. Context-dependent — works in severe models, not mild.
- **PFN1 = "Rosetta Stone"**: connects SMA and ALS. PFN1 mutations cause familial ALS; PFN1 +46% in SMA organoids.
- **CORO1C is a PASSENGER, not a driver** — downgraded after GSE290979 analysis.
- **SMA is a circuit disease**: proprioceptive synapse dysfunction precedes motor neuron death (Simon, Brain 2025, PMID 39982868).
- **STASIMON/TMEM41B**: U12 minor intron gene, dual role — protects both proprioceptive and motor neurons.
- **C1q complement**: marks ~25% of SMA proprioceptive synapses for microglial elimination.

### Therapeutic Landscape
- 3 approved: nusinersen (ASO, intrathecal), risdiplam (small molecule, oral), onasemnogene (AAV9 gene therapy).
- **Top combination**: Risdiplam + MW150 (p38 MAPK inhibitor) + Fasudil (ROCK inhibitor) — each targets a different mechanism.
- **MW150**: synergizes with SMN-inducing drugs (EMBO Mol Med 2025, PMID 40926051). Most promising SMN-independent drug.
- **Fasudil/Bravyl**: ROCK inhibitor, ALS Phase 2 safe, 15% NfL reduction. NEVER tested in SMA — first-in-field opportunity.
- **Panobinostat**: most potent SMN2 splicing corrector at 25nM, synergizes with nusinersen.
- **Apitegromab**: SAPPHIRE Phase 3 positive (Lancet Neurology Aug 2025). First muscle-directed SMA therapy.
- **CRITICAL**: Autophagy inducers (rapamycin) are HARMFUL in SMA — opposite of ALS.

### Data Quality
- 10,900+ curated claims from 6,400+ sources. Two-layer quality filter. Calibration Grade A (89.8%).
- Claims are extracted by LLM and may contain errors. Always verify PMIDs.

## Rules:
1. Cite papers by PMID when available. Reference specific claims when they appear in the context.
2. Distinguish established facts from hypotheses. Preserve authors' hedging language.
3. If the evidence context has relevant data, prioritize it. If not, use your domain knowledge but mark it clearly.
4. This is a conversation — reference previous answers, follow up naturally.
5. Be precise — this is for researchers, not patients.
6. If claims conflict, present both sides with evidence strength.
7. Answer in the same language as the question (German if asked in German, English if asked in English).

Format: Use markdown for structure. Include a "Sources" section at the end."""


async def chat(
    message: str,
    history: list[dict[str, str]] | None = None,
    max_context: int = 20,
    model: str | None = None,
) -> dict[str, Any]:
    """Multi-turn conversational RAG over the SMA evidence base."""
    if not _ensure_index():
        return {
            "answer": "The search index has not been built yet. Please run POST /search/reindex first.",
            "sources_used": 0,
            "model": None,
            "error": "index_not_built",
        }

    # Build search query from current message + recent conversation context
    # For follow-up questions (short or referencing previous answers), use
    # the most recent user question as primary search context
    search_query = message
    if history:
        recent_user_msgs = [m["content"] for m in history[-6:] if m["role"] == "user"]
        # If current message is short (likely a follow-up), combine with previous context
        if len(message.split()) < 10 and recent_user_msgs:
            search_query = " ".join(recent_user_msgs[-2:]) + " " + message
        elif recent_user_msgs:
            search_query = message + " " + " ".join(recent_user_msgs[-1:])

    context = await _retrieve_context(search_query, top_k=max_context)

    if not context["claims"] and not context["sources"]:
        return {
            "answer": "No relevant evidence found for this question. Try rephrasing or broadening your query.",
            "sources_used": 0,
            "model": None,
            "claims_cited": [],
            "sources_cited": [],
        }

    context_text = _format_context(context)

    # Build messages array with conversation history
    messages = []
    if history:
        for h in history[-10:]:
            messages.append({"role": h["role"], "content": h["content"]})

    messages.append({
        "role": "user",
        "content": f"## Evidence Context\n\n{context_text}\n\n## Question\n\n{message}",
    })

    use_model = model or MODEL
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    response = await client.messages.create(
        model=use_model,
        max_tokens=4000,
        system=CHAT_SYSTEM_PROMPT,
        messages=messages,
    )

    answer_text = response.content[0].text if response.content else "No response generated."

    import re
    cited_claims = re.findall(r'CLAIM-(\d+)', answer_text)
    cited_pmids = re.findall(r'PMID:\s*(\d+)', answer_text)

    return {
        "answer": answer_text,
        "message": message,
        "model": use_model,
        "sources_used": len(context["claims"]) + len(context["sources"]),
        "claims_in_context": len(context["claims"]),
        "sources_in_context": len(context["sources"]),
        "claims_cited": cited_claims,
        "sources_cited": cited_pmids,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
    }
