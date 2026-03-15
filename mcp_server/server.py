"""SMA Research Platform — MCP Server.

Exposes the SMA knowledge base to Claude via Model Context Protocol.
All data is fetched live from the REST API at https://sma-research.info/api/v2/.

Uses FastMCP pattern with httpx.AsyncClient for async HTTP access.
No local database or credentials required — all read endpoints are public.
"""

from __future__ import annotations

from typing import Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE = "https://sma-research.info/api/v2"
REQUEST_TIMEOUT = 30.0  # seconds

mcp = FastMCP(
    "SMA Knowledge Base",
    description=(
        "Query the SMA (Spinal Muscular Atrophy) research knowledge base. "
        "Contains targets, drugs, trials, claims, evidence, hypotheses, "
        "discovery signals, splice variant predictions, and computational "
        "screening results from PubMed, ClinicalTrials.gov, and GEO. "
        "All data is fetched live from https://sma-research.info/api/v2/."
    ),
)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


async def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    """Perform a GET request to the API and return the parsed JSON response.

    Raises a descriptive error dict if the request fails or the server
    returns a non-2xx status code.
    """
    url = f"{API_BASE}{path}"
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            return {
                "error": f"API returned {exc.response.status_code}",
                "url": url,
                "detail": exc.response.text[:500],
            }
        except httpx.RequestError as exc:
            return {
                "error": f"Request failed: {type(exc).__name__}",
                "url": url,
                "detail": str(exc),
            }


def _is_error(result: Any) -> bool:
    """Return True if the result is an error dict from _get()."""
    return isinstance(result, dict) and "error" in result


# ---------------------------------------------------------------------------
# Original 11 tools — rewritten to use the REST API
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_platform_stats() -> dict[str, Any]:
    """Get counts of all entities in the SMA knowledge base.

    Returns a live summary from the API with total counts per entity type:
    sources, targets, drugs, trials, claims, evidence, hypotheses, graph_edges,
    and ingestion log entries.
    """
    return await _get("/stats")


@mcp.tool()
async def get_targets(target_type: Optional[str] = None) -> list[dict[str, Any]]:
    """List all molecular targets (genes, proteins, pathways, phenotypes).

    Fetches the complete target catalogue from the knowledge base.  Results are
    sorted alphabetically by symbol.

    Args:
        target_type: Optional filter — one of: gene, protein, pathway,
                     cell_state, phenotype, other.

    Returns:
        List of target records, each containing id, symbol, name, target_type,
        organism, identifiers, description, and created_at.
    """
    params: dict[str, Any] = {}
    if target_type:
        params["target_type"] = target_type
    result = await _get("/targets", params=params or None)
    if _is_error(result):
        return [result]  # type: ignore[list-item]
    return result if isinstance(result, list) else result.get("items", result)


@mcp.tool()
async def get_target_detail(symbol: str) -> dict[str, Any]:
    """Get full details for a single target by its HGNC symbol.

    Fetches the target record together with related claim counts and graph
    connectivity metrics from the API.

    Args:
        symbol: The target symbol (e.g. SMN1, SMN2, STMN2, PLS3, NCALD).

    Returns:
        Target record with id, symbol, name, target_type, organism,
        identifiers, description, claims_as_subject, claims_as_object,
        graph_edges_outgoing, graph_edges_incoming, and created_at.
    """
    result = await _get(f"/targets/symbol/{symbol}")
    if _is_error(result):
        return result
    return result


@mcp.tool()
async def get_claims(
    target_symbol: Optional[str] = None,
    claim_type: Optional[str] = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Query claims (factual assertions) from the evidence graph.

    Claims represent structured scientific assertions linking two entities
    (e.g. "SMN2 undergoes splicing_event") extracted from literature.  Each
    claim is backed by one or more pieces of evidence pointing to primary sources.

    Args:
        target_symbol: Optional — filter claims where this target is subject or
                       object (e.g. "STMN2").
        claim_type: Optional — one of: gene_expression, protein_interaction,
                    pathway_membership, drug_target, drug_efficacy, biomarker,
                    splicing_event, neuroprotection, motor_function, survival,
                    safety, other.
        limit: Maximum number of results to return (default 50, max 500).

    Returns:
        List of claim records sorted by confidence descending, each including
        id, claim_type, subject/object ids and types, predicate, value,
        confidence, evidence_count, and created_at.
    """
    params: dict[str, Any] = {"limit": limit}
    if target_symbol:
        # The API resolves the symbol to an id server-side
        params["target_symbol"] = target_symbol
    if claim_type:
        params["claim_type"] = claim_type
    result = await _get("/claims", params=params)
    if _is_error(result):
        return [result]  # type: ignore[list-item]
    return result if isinstance(result, list) else result.get("items", result)


@mcp.tool()
async def get_hypotheses(
    status: Optional[str] = None,
    min_confidence: Optional[float] = None,
) -> list[dict[str, Any]]:
    """Query hypotheses generated by the reasoning layer.

    Hypotheses are machine-generated or curator-submitted statements that
    synthesise patterns across multiple claims.  They carry a lifecycle status
    and a numeric confidence score.

    Args:
        status: Optional filter — one of: proposed, under_review, validated,
                refuted, published.
        min_confidence: Optional minimum confidence threshold (0.0 – 1.0).

    Returns:
        List of hypothesis records sorted by confidence descending, each
        including id, title, description, target_ids, supporting_evidence,
        contradicting_evidence, confidence, status, and timestamps.
    """
    params: dict[str, Any] = {}
    if status:
        params["status"] = status
    if min_confidence is not None:
        params["min_confidence"] = min_confidence
    result = await _get("/hypotheses", params=params or None)
    if _is_error(result):
        return [result]  # type: ignore[list-item]
    return result if isinstance(result, list) else result.get("items", result)


@mcp.tool()
async def get_sources(limit: int = 50) -> list[dict[str, Any]]:
    """List papers and data sources ingested into the knowledge base.

    Sources include PubMed articles, ClinicalTrials.gov records, and GEO
    datasets.  Sorted by publication date descending so the most recent
    literature appears first.

    Args:
        limit: Maximum number of results to return (default 50).

    Returns:
        List of source records, each including id, source_type, external_id,
        title, authors, journal, pub_date, doi, url, and created_at.
    """
    result = await _get("/sources", params={"limit": limit})
    if _is_error(result):
        return [result]  # type: ignore[list-item]
    return result if isinstance(result, list) else result.get("items", result)


@mcp.tool()
async def get_evidence_chain(claim_id: str) -> dict[str, Any]:
    """Get the full evidence chain for a specific claim: claim → evidence → source.

    Traces a claim all the way back to its primary literature sources.  Useful
    for verifying that an assertion is grounded in real experimental data and
    for building citations.

    Args:
        claim_id: The UUID of the claim to trace (obtain from get_claims).

    Returns:
        Dict with keys: claim (full record), subject_name, object_name,
        evidence (list of evidence records each joined to its source), and
        evidence_count.
    """
    result = await _get(f"/claims/{claim_id}/evidence")
    if _is_error(result):
        return result
    return result


@mcp.tool()
async def search_claims(query: str) -> list[dict[str, Any]]:
    """Full-text search across claim predicates and values.

    Searches the predicate and value fields of all claims using the API's
    built-in search endpoint.  Returns up to 50 results sorted by relevance
    and then confidence.

    Args:
        query: Search term (e.g. "upregulates neuroprotection", "splicing
               modifier", "motor neuron survival").

    Returns:
        List of matching claim records including id, claim_type,
        subject/object identifiers, predicate, value, confidence, and
        evidence_count.
    """
    result = await _get("/claims", params={"q": query, "limit": 50})
    if _is_error(result):
        return [result]  # type: ignore[list-item]
    return result if isinstance(result, list) else result.get("items", result)


@mcp.tool()
async def get_ingestion_history(limit: int = 10) -> list[dict[str, Any]]:
    """Get recent data ingestion runs (PubMed, ClinicalTrials.gov, GEO imports).

    Shows when the knowledge base was last updated, how many new records were
    added, and whether any errors occurred.  Useful for assessing data freshness
    before drawing conclusions.

    Args:
        limit: Maximum number of log entries to return (default 10).

    Returns:
        List of ingestion log records sorted by run date descending, each
        including id, source_type, query, items_found, items_new,
        items_updated, errors, run_at, and duration_secs.
    """
    result = await _get("/ingestion-log", params={"limit": limit})
    if _is_error(result):
        return [result]  # type: ignore[list-item]
    return result if isinstance(result, list) else result.get("items", result)


@mcp.tool()
async def get_drugs(approval_status: Optional[str] = None) -> list[dict[str, Any]]:
    """List drugs and therapies catalogued for SMA.

    Covers approved treatments (nusinersen/Spinraza, onasemnogene/Zolgensma,
    risdiplam/Evrysdi), clinical-stage compounds, and investigational molecules.

    Args:
        approval_status: Optional filter — one of: approved, phase3, phase2,
                         phase1, preclinical, discontinued, investigational.

    Returns:
        List of drug records sorted by name, each including id, name,
        brand_names, drug_type, mechanism, approval_status, approved_for,
        manufacturer, and created_at.
    """
    params: dict[str, Any] = {}
    if approval_status:
        params["approval_status"] = approval_status
    result = await _get("/drugs", params=params or None)
    if _is_error(result):
        return [result]  # type: ignore[list-item]
    return result if isinstance(result, list) else result.get("items", result)


@mcp.tool()
async def get_trials(
    status: Optional[str] = None,
    phase: Optional[str] = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List clinical trials for SMA therapies from ClinicalTrials.gov.

    Provides a structured view of the SMA clinical trial landscape, filterable
    by recruitment status and trial phase.

    Args:
        status: Optional filter on trial status (e.g. recruiting, completed,
                terminated, not_yet_recruiting, active_not_recruiting).
        phase: Optional filter on trial phase (e.g. Phase 1, Phase 2, Phase 3,
               Phase 1/Phase 2).
        limit: Maximum number of results to return (default 50).

    Returns:
        List of trial records sorted by start date descending, each including
        id, nct_id, title, status, phase, conditions, interventions, sponsor,
        start_date, completion_date, enrollment, and url.
    """
    params: dict[str, Any] = {"limit": limit}
    if status:
        params["status"] = status
    if phase:
        params["phase"] = phase
    result = await _get("/trials", params=params)
    if _is_error(result):
        return [result]  # type: ignore[list-item]
    return result if isinstance(result, list) else result.get("items", result)


# ---------------------------------------------------------------------------
# New tools — advanced researcher capabilities
# ---------------------------------------------------------------------------


@mcp.tool()
async def ask_about_target(question: str, target_symbol: str) -> dict[str, Any]:
    """Answer a natural language question about a specific SMA target.

    Fetches target details, related claims, hypotheses mentioning the target,
    and associated evidence in a single call, then assembles them so the calling
    model has all the raw material needed to compose a grounded answer.

    This is the recommended starting point for open-ended research questions
    such as "What evidence supports STMN2 as a therapy target?" or
    "What is known about PLS3's neuroprotective mechanism?"

    Args:
        question: The research question to answer (used as context label in the
                  returned dict; the calling model performs the actual reasoning).
        target_symbol: HGNC symbol of the target to focus on (e.g. STMN2,
                       PLS3, NCALD, SMN2, PLASTIN3).

    Returns:
        Dict containing:
          - question: the original question
          - target: full target record
          - claims: up to 50 claims where this target is subject or object
          - hypotheses: all hypotheses referencing this target
          - claim_count: total claim count for the target
          - hypothesis_count: total hypothesis count for this target
          - sources_sample: up to 10 most recent sources
    """
    # Fetch in parallel is not possible with sequential awaits but we make
    # four fast API calls which are all lightweight.
    target = await _get(f"/targets/symbol/{target_symbol}")
    if _is_error(target):
        return {"error": f"Target '{target_symbol}' not found", "detail": target}

    claims = await _get("/claims", params={"target_symbol": target_symbol, "limit": 50})
    if _is_error(claims):
        claims = []
    elif not isinstance(claims, list):
        claims = claims.get("items", [])

    hypotheses = await _get("/hypotheses")
    if _is_error(hypotheses):
        hypotheses = []
    elif not isinstance(hypotheses, list):
        hypotheses = hypotheses.get("items", [])

    # Filter hypotheses that reference this target's id
    target_id = target.get("id")
    related_hypotheses = [
        h for h in hypotheses
        if target_id and target_id in (h.get("target_ids") or [])
    ]

    sources = await _get("/sources", params={"limit": 10})
    if _is_error(sources):
        sources = []
    elif not isinstance(sources, list):
        sources = sources.get("items", [])

    return {
        "question": question,
        "target": target,
        "claims": claims,
        "claim_count": len(claims),
        "hypotheses": related_hypotheses,
        "hypothesis_count": len(related_hypotheses),
        "sources_sample": sources,
    }


@mcp.tool()
async def get_discovery_signals() -> dict[str, Any]:
    """Get auto-discovery breakthrough signals from the research platform.

    Discovery signals highlight statistically notable patterns in the knowledge
    base: sudden claim spikes (burst of new evidence on a topic), hypothesis
    confirmations (hypotheses that have crossed the validation threshold), and
    novel targets (entities appearing in literature for the first time).

    Returns:
        Dict with keys:
          - signals: all active signals (type, score, description, created_at)
          - spikes: claim-count spikes by topic
          - confirmations: recently validated hypotheses
          - novel_targets: newly identified research targets
    """
    signals = await _get("/discovery/signals")
    spikes = await _get("/discovery/spikes")
    confirmations = await _get("/discovery/confirmations")
    novel = await _get("/discovery/novel")

    return {
        "signals": signals if not _is_error(signals) else [],
        "spikes": spikes if not _is_error(spikes) else [],
        "confirmations": confirmations if not _is_error(confirmations) else [],
        "novel_targets": novel if not _is_error(novel) else [],
    }


@mcp.tool()
async def predict_splice_variant(variant: str) -> dict[str, Any]:
    """Predict the functional effect of an SMN2 splice variant.

    Queries the platform's splice-variant prediction model.  The model
    integrates position-specific scoring, known splicing regulatory elements,
    and historical variant data to estimate whether a given nucleotide change
    will affect exon 7 inclusion — the key determinant of SMA severity.

    Args:
        variant: HGVS-format variant string relative to the SMN2 transcript,
                 e.g. "c.6T>C", "c.−44A>G", "c.835−44A>G".

    Returns:
        Dict with keys: variant, prediction (enhances_inclusion | reduces_inclusion
        | neutral | unknown), confidence, mechanism_notes, known_variant (bool),
        and related_evidence.
    """
    result = await _get("/splice/predict", params={"variant": variant})
    if _is_error(result):
        return result

    # Supplement with known-variants catalogue for context
    known = await _get("/splice/known-variants")
    if not _is_error(known) and isinstance(known, list):
        # Find if this variant appears in the known list
        match = next(
            (v for v in known if v.get("variant") == variant or v.get("hgvs") == variant),
            None,
        )
        result["known_variant_record"] = match

    return result


@mcp.tool()
async def get_screening_results(
    target_symbol: Optional[str] = None,
    min_qed: Optional[float] = None,
) -> list[dict[str, Any]]:
    """Get computational drug screening results for SMA targets.

    Returns records from the platform's in silico screening pipeline, which
    docks drug-like small molecules against SMA target structures and scores
    them using the Quantitative Estimate of Drug-likeness (QED) metric plus
    docking energy.

    Args:
        target_symbol: Optional — filter results to a specific target
                       (e.g. "SMN2", "STMN2").
        min_qed: Optional minimum QED score threshold (0.0 – 1.0).
                 QED > 0.7 is generally considered drug-like.

    Returns:
        List of screening result records, each including compound_id, smiles,
        target_symbol, qed_score, docking_score, predicted_activity, and
        created_at.  Sorted by QED score descending.
    """
    params: dict[str, Any] = {}
    if target_symbol:
        params["target_symbol"] = target_symbol
    if min_qed is not None:
        params["min_qed"] = min_qed
    result = await _get("/screen/compounds/results", params=params or None)
    if _is_error(result):
        return [result]  # type: ignore[list-item]
    return result if isinstance(result, list) else result.get("items", result)


@mcp.tool()
async def search_evidence(query: str) -> dict[str, Any]:
    """Search across all evidence in the knowledge base.

    Performs a broad search spanning claims, hypotheses, sources, and trials.
    Useful when you do not know which entity type contains the information you
    are looking for, or when you want a panoramic view of what the platform
    knows about a concept.

    Args:
        query: Free-text search term (e.g. "neuroprotection", "exon 7
               inclusion", "motor neuron survival", "risdiplam mechanism").

    Returns:
        Dict with keys:
          - query: the original search term
          - claims: matching claims (up to 20)
          - hypotheses: matching hypotheses (up to 10)
          - sources: matching source titles (up to 10)
          - trials: matching trial titles (up to 10)
          - total_hits: sum of all matches
    """
    claims_result = await _get("/claims", params={"q": query, "limit": 20})
    claims = (
        claims_result if isinstance(claims_result, list)
        else claims_result.get("items", [])
        if not _is_error(claims_result)
        else []
    )

    hyp_result = await _get("/hypotheses", params={"q": query})
    hypotheses = (
        hyp_result if isinstance(hyp_result, list)
        else hyp_result.get("items", [])
        if not _is_error(hyp_result)
        else []
    )

    src_result = await _get("/sources", params={"q": query, "limit": 10})
    sources = (
        src_result if isinstance(src_result, list)
        else src_result.get("items", [])
        if not _is_error(src_result)
        else []
    )

    trial_result = await _get("/trials", params={"q": query, "limit": 10})
    trials = (
        trial_result if isinstance(trial_result, list)
        else trial_result.get("items", [])
        if not _is_error(trial_result)
        else []
    )

    return {
        "query": query,
        "claims": claims,
        "hypotheses": hypotheses[:10],
        "sources": sources,
        "trials": trials,
        "total_hits": len(claims) + len(hypotheses[:10]) + len(sources) + len(trials),
    }


@mcp.tool()
async def get_target_evidence_summary(target_symbol: str) -> dict[str, Any]:
    """Get a comprehensive evidence summary for a target.

    Aggregates all available evidence for a target into a structured summary
    suitable for writing a research overview or prioritising targets for
    experimental follow-up.

    Args:
        target_symbol: HGNC symbol of the target (e.g. STMN2, PLS3, NCALD).

    Returns:
        Dict containing:
          - target: core target record
          - claims_by_type: dict mapping claim_type → count
          - top_claims: up to 10 highest-confidence claims
          - hypotheses_by_status: dict mapping status → count
          - top_hypotheses: up to 5 highest-confidence hypotheses
          - related_trials: trials where the target name appears
          - related_drugs: drugs targeting this gene/protein
          - discovery_signals: any active signals for this target
          - evidence_strength_score: a 0–100 composite score
    """
    target = await _get(f"/targets/symbol/{target_symbol}")
    if _is_error(target):
        return {"error": f"Target '{target_symbol}' not found", "detail": target}

    claims_result = await _get(
        "/claims", params={"target_symbol": target_symbol, "limit": 100}
    )
    claims = (
        claims_result if isinstance(claims_result, list)
        else claims_result.get("items", [])
        if not _is_error(claims_result)
        else []
    )

    hypotheses_result = await _get("/hypotheses")
    all_hypotheses = (
        hypotheses_result if isinstance(hypotheses_result, list)
        else hypotheses_result.get("items", [])
        if not _is_error(hypotheses_result)
        else []
    )
    target_id = target.get("id")
    hypotheses = [
        h for h in all_hypotheses
        if target_id and target_id in (h.get("target_ids") or [])
    ]

    trials_result = await _get("/trials", params={"q": target_symbol, "limit": 20})
    trials = (
        trials_result if isinstance(trials_result, list)
        else trials_result.get("items", [])
        if not _is_error(trials_result)
        else []
    )

    drugs_result = await _get("/drugs", params={"q": target_symbol})
    drugs = (
        drugs_result if isinstance(drugs_result, list)
        else drugs_result.get("items", [])
        if not _is_error(drugs_result)
        else []
    )

    signals_result = await _get("/discovery/signals")
    all_signals = signals_result if isinstance(signals_result, list) else []
    signals = [
        s for s in all_signals
        if target_symbol.lower() in str(s).lower()
    ]

    # Build claim_type counts
    claims_by_type: dict[str, int] = {}
    for c in claims:
        ct = c.get("claim_type", "other")
        claims_by_type[ct] = claims_by_type.get(ct, 0) + 1

    # Build hypothesis status counts
    hypotheses_by_status: dict[str, int] = {}
    for h in hypotheses:
        st = h.get("status", "unknown")
        hypotheses_by_status[st] = hypotheses_by_status.get(st, 0) + 1

    # Simple composite evidence-strength score (0–100)
    validated_count = hypotheses_by_status.get("validated", 0)
    score = min(
        100,
        len(claims) * 2
        + validated_count * 10
        + len(trials) * 5
        + len(drugs) * 8,
    )

    # Top claims (already sorted by confidence from the API)
    top_claims = claims[:10]
    top_hypotheses = sorted(
        hypotheses, key=lambda h: h.get("confidence", 0), reverse=True
    )[:5]

    return {
        "target": target,
        "claims_by_type": claims_by_type,
        "top_claims": top_claims,
        "hypotheses_by_status": hypotheses_by_status,
        "top_hypotheses": top_hypotheses,
        "related_trials": trials,
        "related_drugs": drugs,
        "discovery_signals": signals,
        "evidence_strength_score": score,
    }


@mcp.tool()
async def compare_targets(symbols: list[str]) -> dict[str, Any]:
    """Compare multiple SMA targets side-by-side.

    Fetches evidence statistics for each target and returns a structured
    comparison table.  Useful for prioritising targets for experimental
    validation or understanding the relative maturity of the evidence base.

    Args:
        symbols: List of HGNC target symbols to compare, e.g.
                 ["SMN1", "SMN2", "STMN2", "PLS3"].
                 Between 2 and 10 symbols recommended.

    Returns:
        Dict containing:
          - symbols: the requested symbols
          - comparison: list of per-target dicts, each with symbol, found (bool),
            target_type, claim_count, hypothesis_count, validated_hypotheses,
            trial_count, drug_count, and evidence_strength_score.
          - ranking: symbols ordered by evidence_strength_score descending.
    """
    if not symbols:
        return {"error": "Provide at least one symbol to compare."}

    comparison = []
    for symbol in symbols:
        target = await _get(f"/targets/symbol/{symbol}")
        if _is_error(target):
            comparison.append({"symbol": symbol, "found": False})
            continue

        claims_result = await _get(
            "/claims", params={"target_symbol": symbol, "limit": 500}
        )
        claims = (
            claims_result if isinstance(claims_result, list)
            else claims_result.get("items", [])
            if not _is_error(claims_result)
            else []
        )

        hypotheses_result = await _get("/hypotheses")
        all_hyp = (
            hypotheses_result if isinstance(hypotheses_result, list)
            else hypotheses_result.get("items", [])
            if not _is_error(hypotheses_result)
            else []
        )
        target_id = target.get("id")
        related_hyp = [
            h for h in all_hyp
            if target_id and target_id in (h.get("target_ids") or [])
        ]
        validated = sum(1 for h in related_hyp if h.get("status") == "validated")

        trials_result = await _get("/trials", params={"q": symbol, "limit": 50})
        trials = (
            trials_result if isinstance(trials_result, list)
            else trials_result.get("items", [])
            if not _is_error(trials_result)
            else []
        )

        drugs_result = await _get("/drugs", params={"q": symbol})
        drugs = (
            drugs_result if isinstance(drugs_result, list)
            else drugs_result.get("items", [])
            if not _is_error(drugs_result)
            else []
        )

        score = min(
            100,
            len(claims) * 2 + validated * 10 + len(trials) * 5 + len(drugs) * 8,
        )

        comparison.append({
            "symbol": symbol,
            "found": True,
            "target_type": target.get("target_type"),
            "claim_count": len(claims),
            "hypothesis_count": len(related_hyp),
            "validated_hypotheses": validated,
            "trial_count": len(trials),
            "drug_count": len(drugs),
            "evidence_strength_score": score,
        })

    ranking = [
        c["symbol"]
        for c in sorted(
            [c for c in comparison if c.get("found")],
            key=lambda c: c.get("evidence_strength_score", 0),
            reverse=True,
        )
    ]

    return {"symbols": symbols, "comparison": comparison, "ranking": ranking}


@mcp.tool()
async def get_knowledge_graph_neighbors(target_symbol: str) -> dict[str, Any]:
    """Get all knowledge graph neighbors of a target.

    Retrieves every edge in the knowledge graph that connects to the specified
    target, then resolves the connected entity names.  Useful for understanding
    a target's biological context, identifying co-regulated genes, and
    discovering indirect therapeutic opportunities.

    Args:
        target_symbol: HGNC symbol of the focal target (e.g. SMN2, STMN2).

    Returns:
        Dict containing:
          - target: focal target record
          - edges: list of edge records (src_id, dst_id, relationship_type,
            weight, metadata)
          - neighbors: list of resolved neighbor dicts (symbol, name,
            target_type, direction, relationship_type, weight)
          - neighbor_count: total number of connected nodes
    """
    target = await _get(f"/targets/symbol/{target_symbol}")
    if _is_error(target):
        return {"error": f"Target '{target_symbol}' not found", "detail": target}

    target_id = target.get("id")
    edges_result = await _get("/graph/edges", params={"node_id": target_id})
    if _is_error(edges_result):
        return {"error": "Could not retrieve graph edges", "detail": edges_result}

    edges = edges_result if isinstance(edges_result, list) else edges_result.get("items", [])

    # Collect unique neighbour ids
    neighbor_ids: set[str] = set()
    for edge in edges:
        src = edge.get("src_id")
        dst = edge.get("dst_id")
        if src and src != target_id:
            neighbor_ids.add(src)
        if dst and dst != target_id:
            neighbor_ids.add(dst)

    # Resolve neighbour names from the targets list (single call)
    all_targets_result = await _get("/targets")
    all_targets = (
        all_targets_result if isinstance(all_targets_result, list)
        else all_targets_result.get("items", [])
        if not _is_error(all_targets_result)
        else []
    )
    id_to_target = {t["id"]: t for t in all_targets if "id" in t}

    neighbors = []
    for edge in edges:
        src = edge.get("src_id")
        dst = edge.get("dst_id")
        neighbour_id = dst if src == target_id else src
        direction = "outgoing" if src == target_id else "incoming"
        nb_rec = id_to_target.get(neighbour_id, {})
        neighbors.append({
            "symbol": nb_rec.get("symbol", neighbour_id),
            "name": nb_rec.get("name"),
            "target_type": nb_rec.get("target_type"),
            "direction": direction,
            "relationship_type": edge.get("relationship_type"),
            "weight": edge.get("weight"),
        })

    return {
        "target": target,
        "edges": edges,
        "neighbors": neighbors,
        "neighbor_count": len(neighbors),
    }


@mcp.tool()
async def export_target_bibliography(target_symbol: str) -> str:
    """Export a BibTeX bibliography for all sources related to a target.

    Generates a BibTeX file containing every source (journal article, preprint,
    clinical trial record) that has contributed evidence to claims about the
    specified target.  The output can be pasted directly into a LaTeX document
    or imported into reference managers (Zotero, Mendeley, etc.).

    Args:
        target_symbol: HGNC symbol of the target (e.g. STMN2, PLS3, SMN2).

    Returns:
        A UTF-8 BibTeX string.  Returns an error message string if the target
        is not found or the export endpoint is unavailable.
    """
    # First resolve symbol → id
    target = await _get(f"/targets/symbol/{target_symbol}")
    if _is_error(target):
        return f"% Error: Target '{target_symbol}' not found.\n"

    target_id = target.get("id")
    if not target_id:
        return f"% Error: Could not resolve id for '{target_symbol}'.\n"

    result = await _get(f"/export/bibtex/{target_id}")
    if _is_error(result):
        return (
            f"% Error exporting bibliography for '{target_symbol}': "
            f"{result.get('error', 'unknown error')}\n"
        )

    # The endpoint returns either a plain string or a dict with a bibtex key
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        return result.get("bibtex", str(result))
    return str(result)


@mcp.tool()
async def search_patents(query: str, limit: int = 20) -> dict:
    """Search SMA-related patent literature.

    Queries the 578+ patents indexed from Google Patents covering gene therapy,
    antisense oligonucleotides, splicing modifiers, and small molecule
    interventions for Spinal Muscular Atrophy.

    Args:
        query: Free-text search (searches title and abstract).
        limit: Max results (default 20, max 100).

    Returns:
        Dict with matching patents including patent_id, title, assignees,
        grant_date, and URL.
    """
    sources = await _get("/sources", params={
        "source_type": "patent",
        "limit": min(limit, 100),
    })
    if _is_error(sources):
        return {"error": "Failed to fetch patent sources", "detail": sources}

    # Client-side text filter since the API doesn't support full-text search yet
    q_lower = query.lower()
    matches = []
    for s in sources:
        title = (s.get("title") or "").lower()
        abstract = (s.get("abstract") or "").lower()
        if q_lower in title or q_lower in abstract:
            matches.append({
                "patent_id": s.get("external_id"),
                "title": s.get("title"),
                "assignees": s.get("authors", []),
                "grant_date": s.get("pub_date"),
                "url": s.get("url"),
                "abstract_snippet": (s.get("abstract") or "")[:300],
            })

    return {
        "query": query,
        "total_patents_indexed": len(sources),
        "matches": matches[:limit],
        "match_count": len(matches),
    }


@mcp.tool()
async def get_platform_stats() -> dict:
    """Get current platform-wide statistics.

    Returns counts of all major entities: sources (PubMed papers + patents),
    targets, drugs, trials, datasets, claims, evidence links, and hypotheses.
    Use this to understand the scale and coverage of the knowledge base.

    Returns:
        Dict with entity counts.
    """
    return await _get("/stats")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
