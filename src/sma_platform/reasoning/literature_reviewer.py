"""Automated Literature Review Generator.

Generates structured literature reviews per target from all evidence claims.
Two modes:
1. LLM-powered (Claude Sonnet) — full narrative synthesis with sections
2. Data-only — pure aggregation (claim counts, top papers, evidence summary)

The data-only mode always works. The LLM mode requires ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import json
import logging
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

import httpx

from ..core.config import settings
from ..core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"

# Valid claim types for display grouping
CLAIM_TYPE_LABELS = {
    "gene_expression": "Gene Expression",
    "protein_interaction": "Protein Interaction",
    "pathway_membership": "Pathway Membership",
    "drug_target": "Drug Target",
    "drug_efficacy": "Drug Efficacy",
    "biomarker": "Biomarker",
    "splicing_event": "Splicing Event",
    "neuroprotection": "Neuroprotection",
    "motor_function": "Motor Function",
    "survival": "Survival",
    "safety": "Safety",
    "functional_interaction": "Functional Interaction",
    "other": "Other",
}

REVIEW_PROMPT = """You are a senior SMA (Spinal Muscular Atrophy) researcher writing a structured literature review for the target "{target_symbol}" ({target_name}).

Target type: {target_type}
Description: {target_desc}

Evidence claims from the literature ({total_claims} total, showing top {shown_claims}):

{claims_by_type}

Source papers (top {num_papers} by recency):
{papers_text}

Write a structured literature review. Return ONLY valid JSON with these fields:

{{
  "overview": "2-3 sentences summarizing the current state of knowledge about this target in the context of SMA. Include the number of supporting papers and claim types.",
  "findings_by_type": {{
    "<evidence_type>": "1-2 paragraph summary of key findings for this evidence type, citing PMIDs where available"
  }},
  "therapeutic_implications": "2-3 paragraphs on what the evidence suggests for therapeutic development. Discuss potential modalities (ASO, small molecule, gene therapy, etc.) and any existing drugs targeting this.",
  "open_questions": ["List of 3-5 specific unanswered questions that future research should address"],
  "key_references": [
    {{"title": "Paper title", "pmid": "PMID or null", "year": "publication year or null", "journal": "journal name or null", "relevance": "1-sentence why this paper matters"}}
  ],
  "review_quality": "high/medium/low based on evidence depth"
}}

Be specific and mechanistic. Cite PMIDs when available. Focus on SMA relevance.
Return ONLY the JSON. No markdown fences."""


async def _get_target_by_symbol(symbol: str) -> dict | None:
    """Look up a target by symbol (case-insensitive)."""
    row = await fetchrow(
        "SELECT * FROM targets WHERE UPPER(symbol) = $1",
        symbol.upper(),
    )
    return dict(row) if row else None


async def _get_claims_for_target(target_id: str, symbol: str) -> list[dict]:
    """Fetch all claims for a target via subject_id, object_id, or metadata."""
    # Claims where target is the subject
    subject_claims = await fetch(
        """SELECT c.id, c.claim_type, c.predicate, c.confidence, c.subject_id,
                  c.object_id, c.value, c.metadata, c.created_at,
                  e.source_id,
                  s.title AS source_title, s.external_id AS pmid,
                  s.journal, s.pub_date, s.doi, s.authors
           FROM claims c
           LEFT JOIN evidence e ON e.claim_id = c.id
           LEFT JOIN sources s ON e.source_id = s.id
           WHERE c.subject_id = $1
           ORDER BY c.confidence DESC""",
        target_id,
    )

    # Claims where target is the object
    object_claims = await fetch(
        """SELECT c.id, c.claim_type, c.predicate, c.confidence, c.subject_id,
                  c.object_id, c.value, c.metadata, c.created_at,
                  e.source_id,
                  s.title AS source_title, s.external_id AS pmid,
                  s.journal, s.pub_date, s.doi, s.authors
           FROM claims c
           LEFT JOIN evidence e ON e.claim_id = c.id
           LEFT JOIN sources s ON e.source_id = s.id
           WHERE c.object_id = $1
           ORDER BY c.confidence DESC""",
        target_id,
    )

    # Claims mentioning symbol in metadata
    metadata_claims = await fetch(
        """SELECT c.id, c.claim_type, c.predicate, c.confidence, c.subject_id,
                  c.object_id, c.value, c.metadata, c.created_at,
                  e.source_id,
                  s.title AS source_title, s.external_id AS pmid,
                  s.journal, s.pub_date, s.doi, s.authors
           FROM claims c
           LEFT JOIN evidence e ON e.claim_id = c.id
           LEFT JOIN sources s ON e.source_id = s.id
           WHERE CAST(c.metadata AS TEXT) LIKE $1
           ORDER BY c.confidence DESC""",
        f'%"{symbol}"%',
    )

    # Deduplicate by claim ID
    seen: set[str] = set()
    results: list[dict] = []
    for row in list(subject_claims) + list(object_claims) + list(metadata_claims):
        row = dict(row)
        claim_id = str(row["id"])
        if claim_id not in seen:
            seen.add(claim_id)
            results.append(row)

    return results


def _group_claims_by_type(claims: list[dict]) -> dict[str, list[dict]]:
    """Group claims by claim_type."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for c in claims:
        ct = c.get("claim_type") or "other"
        groups[ct].append(c)
    return dict(groups)


def _get_unique_sources(claims: list[dict]) -> list[dict]:
    """Extract unique source papers from claims, sorted by pub_date descending."""
    seen: set[str] = set()
    sources: list[dict] = []
    for c in claims:
        sid = c.get("source_id")
        if not sid or str(sid) in seen:
            continue
        seen.add(str(sid))
        sources.append({
            "source_id": str(sid),
            "title": c.get("source_title") or "Untitled",
            "pmid": c.get("pmid"),
            "journal": c.get("journal"),
            "pub_date": str(c["pub_date"]) if c.get("pub_date") else None,
            "doi": c.get("doi"),
            "authors": c.get("authors"),
        })

    # Sort by pub_date descending (most recent first), nulls last
    sources.sort(
        key=lambda s: s["pub_date"] or "0000-00-00",
        reverse=True,
    )
    return sources


async def generate_target_review(target_symbol: str) -> dict:
    """Generate a structured literature review for a target using Claude Sonnet.

    Falls back to data-only review if no API key is available or if the
    LLM call fails.

    Args:
        target_symbol: Gene/protein symbol (e.g., "SMN1", "PLS3")

    Returns:
        Dict with review text, metadata, and source information.
    """
    target = await _get_target_by_symbol(target_symbol)
    if not target:
        return {"error": f"Target '{target_symbol}' not found", "status": "not_found"}

    target_id = str(target["id"])
    claims = await _get_claims_for_target(target_id, target["symbol"])

    if not claims:
        return {
            "target": target["symbol"],
            "error": "No claims found for this target",
            "status": "no_data",
        }

    # Check for API key
    api_key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.info("No ANTHROPIC_API_KEY — falling back to data-only review for %s", target["symbol"])
        return await generate_review_without_llm(target_symbol)

    # Group claims and get sources
    grouped = _group_claims_by_type(claims)
    sources = _get_unique_sources(claims)

    # Format claims by type for the prompt
    claims_sections = []
    for ct, ct_claims in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True):
        label = CLAIM_TYPE_LABELS.get(ct, ct.replace("_", " ").title())
        lines = []
        for i, c in enumerate(ct_claims[:10], 1):  # Cap at 10 per type
            pmid_str = f" (PMID: {c['pmid']})" if c.get("pmid") else ""
            conf_str = f" [confidence: {c['confidence']:.2f}]" if c.get("confidence") is not None else ""
            lines.append(f"  {i}. {c['predicate']}{pmid_str}{conf_str}")
        claims_sections.append(f"[{label}] ({len(ct_claims)} claims):\n" + "\n".join(lines))

    claims_by_type_text = "\n\n".join(claims_sections)

    # Format top papers
    top_papers = sources[:10]
    papers_lines = []
    for i, s in enumerate(top_papers, 1):
        pmid_str = f" PMID:{s['pmid']}" if s.get("pmid") else ""
        journal_str = f" ({s['journal']})" if s.get("journal") else ""
        date_str = f" [{s['pub_date']}]" if s.get("pub_date") else ""
        papers_lines.append(f"  {i}. {s['title']}{pmid_str}{journal_str}{date_str}")

    papers_text = "\n".join(papers_lines) if papers_lines else "  No source papers available."

    prompt = REVIEW_PROMPT.format(
        target_symbol=target["symbol"],
        target_name=target.get("name") or target["symbol"],
        target_type=target.get("target_type", "unknown"),
        target_desc=target.get("description") or "No description available.",
        total_claims=len(claims),
        shown_claims=min(len(claims), sum(min(len(v), 10) for v in grouped.values())),
        claims_by_type=claims_by_type_text,
        num_papers=len(top_papers),
        papers_text=papers_text,
    )

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": MODEL,
                    "max_tokens": 4000,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )

        if resp.status_code != 200:
            logger.error("Claude API error %d: %s", resp.status_code, resp.text[:300])
            return await generate_review_without_llm(target_symbol)

        content = resp.json()["content"][0]["text"].strip()

        # Strip markdown fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [ln for ln in lines if not ln.strip().startswith("```")]
            content = "\n".join(lines).strip()

        review = json.loads(content)

    except (json.JSONDecodeError, KeyError, Exception) as e:
        logger.error("Failed to parse review from LLM for %s: %s", target["symbol"], e)
        return await generate_review_without_llm(target_symbol)

    # Build response
    claim_type_counts = {ct: len(cls) for ct, cls in grouped.items()}

    return {
        "target": target["symbol"],
        "target_name": target.get("name"),
        "target_type": target.get("target_type"),
        "status": "success",
        "mode": "llm",
        "model": MODEL,
        "overview": review.get("overview", ""),
        "findings_by_type": review.get("findings_by_type", {}),
        "therapeutic_implications": review.get("therapeutic_implications", ""),
        "open_questions": review.get("open_questions", []),
        "key_references": review.get("key_references", [])[:10],
        "review_quality": review.get("review_quality", "medium"),
        "metadata": {
            "total_claims": len(claims),
            "claim_type_counts": claim_type_counts,
            "total_sources": len(sources),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }


async def generate_review_without_llm(target_symbol: str) -> dict:
    """Generate a data-only literature review without Claude.

    Pure data aggregation: claim counts, top papers, evidence summary
    grouped by type. Useful when no API key is available or for fast
    responses.

    Args:
        target_symbol: Gene/protein symbol (e.g., "SMN1", "PLS3")

    Returns:
        Dict with structured data review and metadata.
    """
    target = await _get_target_by_symbol(target_symbol)
    if not target:
        return {"error": f"Target '{target_symbol}' not found", "status": "not_found"}

    target_id = str(target["id"])
    claims = await _get_claims_for_target(target_id, target["symbol"])

    if not claims:
        return {
            "target": target["symbol"],
            "error": "No claims found for this target",
            "status": "no_data",
        }

    grouped = _group_claims_by_type(claims)
    sources = _get_unique_sources(claims)

    # Build overview from data
    claim_type_counts = {ct: len(cls) for ct, cls in grouped.items()}
    top_types = sorted(claim_type_counts.items(), key=lambda x: x[1], reverse=True)
    type_summary = ", ".join(
        f"{CLAIM_TYPE_LABELS.get(ct, ct)} ({cnt})"
        for ct, cnt in top_types[:5]
    )

    avg_confidence = sum(
        c.get("confidence", 0.5) for c in claims
    ) / max(len(claims), 1)

    overview = (
        f"{target.get('name') or target['symbol']} has {len(claims)} evidence claims "
        f"from {len(sources)} source papers. "
        f"Primary evidence types: {type_summary}. "
        f"Average confidence: {avg_confidence:.2f}."
    )

    if target.get("description"):
        overview = f"{target['description']} " + overview

    # Build findings by type
    findings_by_type: dict[str, dict[str, Any]] = {}
    for ct, ct_claims in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True):
        label = CLAIM_TYPE_LABELS.get(ct, ct.replace("_", " ").title())
        ct_avg_conf = sum(c.get("confidence", 0.5) for c in ct_claims) / max(len(ct_claims), 1)

        # Top claims by confidence
        sorted_claims = sorted(ct_claims, key=lambda c: c.get("confidence", 0), reverse=True)
        top_predicates = []
        seen_predicates: set[str] = set()
        for c in sorted_claims[:10]:
            pred = c.get("predicate", "")
            if pred and pred not in seen_predicates:
                seen_predicates.add(pred)
                entry: dict[str, Any] = {
                    "predicate": pred,
                    "confidence": c.get("confidence"),
                }
                if c.get("pmid"):
                    entry["pmid"] = c["pmid"]
                top_predicates.append(entry)

        # Sources for this type
        ct_source_ids = set(str(c["source_id"]) for c in ct_claims if c.get("source_id"))

        findings_by_type[label] = {
            "claim_count": len(ct_claims),
            "avg_confidence": round(ct_avg_conf, 3),
            "source_count": len(ct_source_ids),
            "top_claims": top_predicates[:5],
        }

    # Top papers by recency
    key_references = []
    for s in sources[:10]:
        ref: dict[str, Any] = {"title": s["title"]}
        if s.get("pmid"):
            ref["pmid"] = s["pmid"]
        if s.get("pub_date"):
            ref["year"] = s["pub_date"][:4] if len(s["pub_date"]) >= 4 else s["pub_date"]
        if s.get("journal"):
            ref["journal"] = s["journal"]
        if s.get("doi"):
            ref["doi"] = s["doi"]
        key_references.append(ref)

    # Open questions (generated from data patterns)
    open_questions = _generate_open_questions(target, grouped, sources)

    # Therapeutic implications (data-driven)
    therapeutic_implications = _generate_therapeutic_summary(target, grouped, claims)

    return {
        "target": target["symbol"],
        "target_name": target.get("name"),
        "target_type": target.get("target_type"),
        "status": "success",
        "mode": "data_only",
        "overview": overview,
        "findings_by_type": findings_by_type,
        "therapeutic_implications": therapeutic_implications,
        "open_questions": open_questions,
        "key_references": key_references,
        "review_quality": _assess_review_quality(claims, sources, grouped),
        "metadata": {
            "total_claims": len(claims),
            "claim_type_counts": claim_type_counts,
            "total_sources": len(sources),
            "avg_confidence": round(avg_confidence, 3),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def _generate_open_questions(
    target: dict, grouped: dict[str, list[dict]], sources: list[dict]
) -> list[str]:
    """Generate open questions based on data gaps."""
    questions: list[str] = []
    symbol = target["symbol"]

    # Check for missing evidence types
    present_types = set(grouped.keys())
    important_missing = []
    if "drug_efficacy" not in present_types and "drug_target" not in present_types:
        important_missing.append("drug efficacy or drug target data")
    if "splicing_event" not in present_types:
        important_missing.append("splicing event data")
    if "neuroprotection" not in present_types:
        important_missing.append("neuroprotection data")

    if important_missing:
        questions.append(
            f"What is the {important_missing[0]} for {symbol} in the context of SMA?"
        )

    # Low-confidence areas
    for ct, ct_claims in grouped.items():
        avg_conf = sum(c.get("confidence", 0.5) for c in ct_claims) / max(len(ct_claims), 1)
        if avg_conf < 0.5 and len(ct_claims) >= 2:
            label = CLAIM_TYPE_LABELS.get(ct, ct)
            questions.append(
                f"Can the {label.lower()} evidence for {symbol} be strengthened with additional studies?"
            )

    # Few sources
    if len(sources) < 5:
        questions.append(
            f"Are there additional unpublished or recent studies on {symbol} in SMA that could expand the evidence base?"
        )

    # Single-type dominance
    if len(grouped) == 1:
        dominant_type = list(grouped.keys())[0]
        label = CLAIM_TYPE_LABELS.get(dominant_type, dominant_type)
        questions.append(
            f"Beyond {label.lower()}, what other roles might {symbol} play in SMA pathogenesis?"
        )

    # Always include a translational question
    questions.append(
        f"What is the translational potential of {symbol} as a therapeutic target or biomarker for SMA?"
    )

    return questions[:5]


def _generate_therapeutic_summary(
    target: dict, grouped: dict[str, list[dict]], claims: list[dict]
) -> str:
    """Generate a data-driven therapeutic implications summary."""
    symbol = target["symbol"]
    parts: list[str] = []

    # Drug-related claims
    drug_claims = grouped.get("drug_target", []) + grouped.get("drug_efficacy", [])
    if drug_claims:
        drug_predicates = [c.get("predicate", "") for c in drug_claims[:5]]
        parts.append(
            f"{symbol} has {len(drug_claims)} drug-related claims. "
            f"Key findings: {'; '.join(p for p in drug_predicates if p)[:300]}."
        )
    else:
        parts.append(
            f"No direct drug target or efficacy data is currently available for {symbol} in SMA."
        )

    # Neuroprotection / motor function
    neuro_claims = grouped.get("neuroprotection", []) + grouped.get("motor_function", [])
    if neuro_claims:
        parts.append(
            f"There are {len(neuro_claims)} claims related to neuroprotection or motor function, "
            f"suggesting potential for disease-modifying therapeutic approaches."
        )

    # Gene expression / splicing
    expr_claims = grouped.get("gene_expression", []) + grouped.get("splicing_event", [])
    if expr_claims:
        parts.append(
            f"{len(expr_claims)} gene expression or splicing claims suggest that RNA-targeted "
            f"approaches (ASO, splice-switching) may be relevant for {symbol}."
        )

    if not parts:
        parts.append(f"Therapeutic implications for {symbol} require further investigation.")

    return " ".join(parts)


def _assess_review_quality(
    claims: list[dict], sources: list[dict], grouped: dict[str, list[dict]]
) -> str:
    """Assess review quality based on evidence depth."""
    score = 0

    # Claim volume
    if len(claims) >= 50:
        score += 3
    elif len(claims) >= 20:
        score += 2
    elif len(claims) >= 10:
        score += 1

    # Source diversity
    if len(sources) >= 10:
        score += 2
    elif len(sources) >= 5:
        score += 1

    # Evidence type diversity
    if len(grouped) >= 4:
        score += 2
    elif len(grouped) >= 2:
        score += 1

    # Average confidence
    avg_conf = sum(c.get("confidence", 0.5) for c in claims) / max(len(claims), 1)
    if avg_conf >= 0.7:
        score += 2
    elif avg_conf >= 0.5:
        score += 1

    if score >= 7:
        return "high"
    elif score >= 4:
        return "medium"
    return "low"


async def list_reviewable_targets() -> list[dict]:
    """Return targets with enough claims (>10) for meaningful review.

    Returns a list of targets with claim counts, sorted by claim count
    descending.
    """
    # Count claims per target via subject_id
    subject_counts = await fetch("""
        SELECT t.id, t.symbol, t.name, t.target_type, t.description,
               COUNT(c.id) AS claim_count
        FROM targets t
        JOIN claims c ON c.subject_id = t.id
        GROUP BY t.id, t.symbol, t.name, t.target_type, t.description
        HAVING COUNT(c.id) > 10
        ORDER BY claim_count DESC
    """)

    # Also count claims via object_id
    object_counts = await fetch("""
        SELECT t.id, t.symbol, COUNT(c.id) AS obj_claim_count
        FROM targets t
        JOIN claims c ON c.object_id = t.id
        GROUP BY t.id, t.symbol
    """)
    obj_count_map = {str(r["id"]): r["obj_claim_count"] for r in object_counts}

    # Count unique sources per target
    source_counts = await fetch("""
        SELECT t.id, COUNT(DISTINCT e.source_id) AS source_count
        FROM targets t
        JOIN claims c ON c.subject_id = t.id
        JOIN evidence e ON e.claim_id = c.id
        GROUP BY t.id
    """)
    src_count_map = {str(r["id"]): r["source_count"] for r in source_counts}

    results = []
    for row in subject_counts:
        row = dict(row)
        tid = str(row["id"])
        total_claims = row["claim_count"] + obj_count_map.get(tid, 0)
        results.append({
            "id": tid,
            "symbol": row["symbol"],
            "name": row.get("name"),
            "target_type": row.get("target_type"),
            "description": (row.get("description") or "")[:200],
            "claim_count": total_claims,
            "source_count": src_count_map.get(tid, 0),
        })

    # Re-sort by total claims
    results.sort(key=lambda x: x["claim_count"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# Citation-Grade Evidence Summary
# ---------------------------------------------------------------------------

def _format_vancouver_reference(source: dict, ref_num: int) -> str:
    """Format a source as a Vancouver-style numbered reference.

    Example output:
      1. Wirth B, et al. Spinal Muscular Atrophy: Disease Mechanisms and Therapy.
         Hum Mol Genet. 2024. PMID: 38401234. doi:10.1093/hmg/ddae001
    """
    parts: list[str] = [f"{ref_num}."]

    # Authors — first author + "et al." if multiple
    authors = source.get("authors")
    if authors and isinstance(authors, list) and len(authors) > 0:
        first_author = authors[0]
        if len(authors) > 1:
            parts.append(f"{first_author}, et al.")
        else:
            parts.append(f"{first_author}.")
    else:
        parts.append("[Authors unknown].")

    # Title
    title = source.get("title") or "Untitled"
    if not title.endswith("."):
        title += "."
    parts.append(title)

    # Journal + year
    journal = source.get("journal")
    pub_date = source.get("pub_date")
    year = pub_date[:4] if pub_date and len(pub_date) >= 4 else None
    if journal:
        journal_part = journal
        if year:
            journal_part += f". {year}"
        parts.append(journal_part + ".")
    elif year:
        parts.append(f"{year}.")

    # PMID
    pmid = source.get("pmid")
    if pmid:
        parts.append(f"PMID: {pmid}.")

    # DOI
    doi = source.get("doi")
    if doi:
        parts.append(f"doi:{doi}")

    return " ".join(parts)


def _compose_narrative(
    target: dict,
    claims: list[dict],
    grouped: dict[str, list[dict]],
    sources: list[dict],
    pmid_to_refnum: dict[str, int],
    convergence_score: float | None,
) -> str:
    """Compose a narrative evidence paragraph with inline Vancouver citations.

    Builds prose from the data — no LLM required. Sentences reference PMIDs
    as [1], [2], etc. following the numbered reference list.
    """
    symbol = target["symbol"]
    name = target.get("name") or symbol
    num_claims = len(claims)
    num_sources = len(sources)

    # Opening sentence
    sentences: list[str] = []
    desc = target.get("description")
    if desc:
        sentences.append(desc.rstrip(".") + ".")

    sentences.append(
        f"{name} ({symbol}) has been investigated in {num_sources} "
        f"publication{'s' if num_sources != 1 else ''}, yielding {num_claims} "
        f"evidence claim{'s' if num_claims != 1 else ''} across "
        f"{len(grouped)} evidence type{'s' if len(grouped) != 1 else ''}."
    )

    # Convergence context
    if convergence_score is not None:
        if convergence_score >= 0.75:
            conv_word = "strong"
        elif convergence_score >= 0.55:
            conv_word = "moderate"
        elif convergence_score >= 0.35:
            conv_word = "emerging"
        else:
            conv_word = "limited"
        sentences.append(
            f"Evidence convergence is {conv_word} "
            f"(score: {convergence_score:.2f}/1.00)."
        )

    # Per-type summaries with inline citations
    type_order = sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True)
    for ct, ct_claims in type_order[:5]:  # Top 5 evidence types
        label = CLAIM_TYPE_LABELS.get(ct, ct.replace("_", " ").title())
        count = len(ct_claims)

        # Collect inline citation numbers for this type
        cite_nums: list[int] = []
        seen_pmids: set[str] = set()
        for c in ct_claims:
            pmid = c.get("pmid")
            if pmid and pmid not in seen_pmids and pmid in pmid_to_refnum:
                seen_pmids.add(pmid)
                cite_nums.append(pmid_to_refnum[pmid])
        cite_nums.sort()

        # Pick the highest-confidence predicate as representative
        best = max(ct_claims, key=lambda c: c.get("confidence") or 0)
        predicate = best.get("predicate", "")

        cite_str = ""
        if cite_nums:
            cite_str = " [" + ",".join(str(n) for n in cite_nums[:5]) + "]"

        if predicate:
            sentences.append(
                f"{label} evidence ({count} claim{'s' if count != 1 else ''}): "
                f"{predicate}{cite_str}."
            )
        else:
            sentences.append(
                f"{label}: {count} claim{'s' if count != 1 else ''}{cite_str}."
            )

    return " ".join(sentences)


async def generate_citation_summary(target_symbol: str) -> dict:
    """Generate a citation-grade evidence summary for a target.

    Returns publication-ready text with PMID citations (Vancouver style)
    suitable for paper introductions, review articles, or grant backgrounds.

    This is a pure data-driven function — no LLM required.

    Args:
        target_symbol: Gene/protein symbol (e.g., "SMN1", "PLS3")

    Returns:
        Dict with narrative text, numbered reference list, claim breakdown,
        convergence context, and suggested platform citation.
    """
    target = await _get_target_by_symbol(target_symbol)
    if not target:
        return {"error": f"Target '{target_symbol}' not found", "status": "not_found"}

    target_id = str(target["id"])
    claims = await _get_claims_for_target(target_id, target["symbol"])

    if not claims:
        return {
            "target": target["symbol"],
            "error": "No claims found for this target",
            "status": "no_data",
        }

    # Sort by confidence descending
    claims.sort(key=lambda c: c.get("confidence") or 0, reverse=True)

    grouped = _group_claims_by_type(claims)
    sources = _get_unique_sources(claims)

    # Build PMID → reference number mapping (Vancouver style)
    # Only include sources with PMIDs; order by first appearance in top claims
    pmid_order: list[str] = []
    seen_pmids: set[str] = set()
    for c in claims:
        pmid = c.get("pmid")
        if pmid and pmid not in seen_pmids:
            seen_pmids.add(pmid)
            pmid_order.append(pmid)

    pmid_to_refnum: dict[str, int] = {
        pmid: i + 1 for i, pmid in enumerate(pmid_order)
    }

    # Build source lookup for reference formatting
    source_by_pmid: dict[str, dict] = {}
    for s in sources:
        if s.get("pmid"):
            source_by_pmid[s["pmid"]] = s

    # Numbered reference list (Vancouver)
    reference_list: list[dict] = []
    for pmid in pmid_order:
        ref_num = pmid_to_refnum[pmid]
        src = source_by_pmid.get(pmid, {"pmid": pmid, "title": "Unknown"})
        formatted = _format_vancouver_reference(src, ref_num)
        reference_list.append({
            "ref_number": ref_num,
            "pmid": pmid,
            "formatted": formatted,
            "title": src.get("title"),
            "journal": src.get("journal"),
            "year": src["pub_date"][:4] if src.get("pub_date") and len(src["pub_date"]) >= 4 else None,
            "doi": src.get("doi"),
        })

    # Get convergence score if available
    convergence_score: float | None = None
    try:
        conv_row = await fetchrow(
            "SELECT composite_score FROM convergence_scores WHERE target_id = $1 "
            "ORDER BY computed_at DESC LIMIT 1",
            target["id"],
        )
        if conv_row:
            convergence_score = float(conv_row["composite_score"])
    except Exception:
        pass  # convergence_scores table may not exist yet

    # Compose narrative
    narrative = _compose_narrative(
        target, claims, grouped, sources, pmid_to_refnum, convergence_score,
    )

    # Claim evidence breakdown
    claim_breakdown: list[dict] = []
    for ct, ct_claims in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True):
        label = CLAIM_TYPE_LABELS.get(ct, ct.replace("_", " ").title())
        ct_avg_conf = sum(c.get("confidence", 0.5) for c in ct_claims) / max(len(ct_claims), 1)

        # Unique PMIDs for this type
        ct_pmids = list({
            c["pmid"] for c in ct_claims if c.get("pmid")
        })
        ct_refs = sorted(pmid_to_refnum[p] for p in ct_pmids if p in pmid_to_refnum)

        top_predicates = []
        seen_preds: set[str] = set()
        for c in sorted(ct_claims, key=lambda x: x.get("confidence") or 0, reverse=True)[:5]:
            pred = c.get("predicate", "")
            if pred and pred not in seen_preds:
                seen_preds.add(pred)
                entry: dict[str, Any] = {
                    "predicate": pred,
                    "confidence": round(c.get("confidence") or 0, 3),
                }
                if c.get("pmid"):
                    entry["citation"] = f"[{pmid_to_refnum[c['pmid']]}]"
                    entry["pmid"] = c["pmid"]
                top_predicates.append(entry)

        claim_breakdown.append({
            "evidence_type": label,
            "claim_count": len(ct_claims),
            "avg_confidence": round(ct_avg_conf, 3),
            "citation_refs": [f"[{n}]" for n in ct_refs[:10]],
            "top_claims": top_predicates,
        })

    # Suggested platform citation
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    platform_citation = (
        f"SMA Research Platform. Evidence summary for {target['symbol']}. "
        f"Generated {today}. https://sma-research.com/review/{target['symbol']}"
    )

    # Average confidence across all claims
    avg_confidence = sum(c.get("confidence", 0.5) for c in claims) / max(len(claims), 1)

    return {
        "target": target["symbol"],
        "target_name": target.get("name"),
        "target_type": target.get("target_type"),
        "status": "success",
        "narrative": narrative,
        "reference_list": reference_list,
        "claim_breakdown": claim_breakdown,
        "convergence_score": convergence_score,
        "suggested_citation": platform_citation,
        "metadata": {
            "total_claims": len(claims),
            "total_references": len(reference_list),
            "total_sources": len(sources),
            "evidence_types": len(grouped),
            "avg_confidence": round(avg_confidence, 3),
            "citation_style": "Vancouver",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }
