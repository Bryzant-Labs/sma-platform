"""SMA Research Platform — MCP Server.

Exposes the SMA knowledge base to Claude via Model Context Protocol.
All data is fetched live from the REST API at https://sma-research.info/api/v2/.

Uses FastMCP pattern with httpx.AsyncClient for async HTTP access.
No local database or credentials required — all read endpoints are public.
"""

from __future__ import annotations

import os
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


async def _post(
    path: str,
    json_body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    """Perform a POST request to the API and return the parsed JSON response.

    Raises a descriptive error dict if the request fails or the server
    returns a non-2xx status code.
    """
    url = f"{API_BASE}{path}"
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            response = await client.post(url, json=json_body, headers=headers)
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
    params: dict[str, Any] = {"limit": min(limit, 500)}
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
    result = await _get("/sources", params={"limit": min(limit, 500)})
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
    result = await _get("/ingestion-log", params={"limit": min(limit, 200)})
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
    params: dict[str, Any] = {"limit": min(limit, 500)}
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
async def compare_targets(symbol_a: str, symbol_b: str) -> dict[str, Any]:
    """Compare two SMA targets side-by-side across all dimensions.

    Uses the dedicated comparison endpoint to compare convergence scores,
    claims, screening hits, species conservation, and hypotheses for two
    targets.  Useful for prioritising which target to pursue experimentally
    or understanding relative evidence maturity.

    Args:
        symbol_a: HGNC symbol of the first target (e.g. "SMN2", "STMN2").
        symbol_b: HGNC symbol of the second target (e.g. "PLS3", "NCALD").

    Returns:
        Dict containing side-by-side comparison across convergence, claims,
        screening hits, conservation, and hypotheses for both targets.
    """
    result = await _get("/compare/targets", params={"a": symbol_a, "b": symbol_b})
    if _is_error(result):
        return result
    return result


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
async def get_predictions(target: str = "", min_score: float = 0.0, limit: int = 10) -> dict:
    """Get prediction cards — falsifiable, evidence-grounded predictions for SMA targets.

    Each prediction card contains:
    - A falsifiable prediction statement
    - Convergence score (0-1) with 5-dimension breakdown
    - Supporting, contradicting, and neutral evidence
    - Suggested experiments and evidence gaps

    All scoring weights are open source at github.com/Bryzant-Labs/sma-platform

    Args:
        target: Optional target symbol to filter (e.g. "NCALD", "PLS3")
        min_score: Minimum convergence score threshold (0-1)
        limit: Maximum number of predictions to return

    Returns:
        Dict with prediction cards and count.
    """
    params: dict = {"min_score": min_score, "limit": min(limit, 50)}
    if target:
        params["target"] = target
    cards = await _get("/predictions", params=params)
    if _is_error(cards):
        return cards
    return {
        "predictions": cards,
        "count": len(cards) if isinstance(cards, list) else 0,
        "filter": {"target": target, "min_score": min_score},
    }


@mcp.tool()
async def get_convergence_score(target: str) -> dict:
    """Get the evidence convergence score breakdown for a specific SMA target.

    Shows 5 scoring dimensions:
    - Volume (weight: 0.15): claim count, normalized to ceiling of 50
    - Lab Independence (weight: 0.30): unique research groups
    - Method Diversity (weight: 0.20): experimental method variety
    - Temporal Trend (weight: 0.15): evidence consistency over time
    - Replication (weight: 0.20): findings reproduced by different groups

    All weights are open source at github.com/Bryzant-Labs/sma-platform

    Args:
        target: Target symbol (e.g. "SMN2", "NCALD", "PLS3")

    Returns:
        Dict with convergence score breakdown or error.
    """
    targets = await _get("/targets", params={"limit": 100})
    target_lower = target.lower()
    matched = [
        t for t in targets
        if target_lower in (t.get("symbol") or "").lower()
        or target_lower in (t.get("name") or "").lower()
    ]

    if not matched:
        return {
            "error": f"Target '{target}' not found",
            "available_targets": [t["symbol"] for t in targets],
        }

    target_id = matched[0]["id"]
    try:
        score = await _get(f"/convergence/{target_id}")
        return score
    except Exception:
        return {
            "error": f"No convergence score computed for {matched[0]['symbol']}. Run computation first.",
        }


# ---------------------------------------------------------------------------
# Cross-Paper Synthesis tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_synthesis_cards(
    target: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Get cross-paper synthesis cards that combine findings from multiple sources.

    Synthesis cards highlight emergent insights that only become visible when
    evidence from multiple papers is combined — for example, independent labs
    converging on the same pathway, or complementary mechanisms that suggest
    combination therapy opportunities.

    Args:
        target: Optional target symbol to filter cards (e.g. "STMN2", "PLS3").

    Returns:
        List of synthesis card records, each including id, title, summary,
        target_symbols, source_ids, convergence_score, synthesis_type,
        and created_at.
    """
    params: dict[str, Any] = {}
    if target:
        params["target"] = target
    result = await _get("/synthesis/cards", params=params or None)
    if _is_error(result):
        return [result]  # type: ignore[list-item]
    return result if isinstance(result, list) else result.get("items", result)


@mcp.tool()
async def get_cooccurrences() -> list[dict[str, Any]]:
    """Get target co-occurrence data from cross-paper analysis.

    Returns pairs of targets that frequently appear together in the same
    publications, along with co-occurrence counts and statistical significance.
    High co-occurrence often indicates shared pathways, regulatory relationships,
    or potential combination therapy candidates.

    Returns:
        List of co-occurrence records, each including target_a, target_b,
        cooccurrence_count, pmi_score (pointwise mutual information),
        top_shared_sources, and relationship_summary.
    """
    result = await _get("/synthesis/cooccurrences")
    if _is_error(result):
        return [result]  # type: ignore[list-item]
    return result if isinstance(result, list) else result.get("items", result)


@mcp.tool()
async def get_shared_mechanisms() -> list[dict[str, Any]]:
    """Get shared molecular mechanisms identified across multiple papers.

    Surfaces mechanisms (pathways, cellular processes, molecular interactions)
    that are supported by evidence from multiple independent studies.  These
    represent the most robust biological insights in the knowledge base and
    are prime candidates for therapeutic intervention.

    Returns:
        List of shared mechanism records, each including mechanism_id,
        mechanism_name, mechanism_type, supporting_papers_count,
        involved_targets, confidence, description, and evidence_summary.
    """
    result = await _get("/synthesis/shared-mechanisms")
    if _is_error(result):
        return [result]  # type: ignore[list-item]
    return result if isinstance(result, list) else result.get("items", result)


# ---------------------------------------------------------------------------
# NVIDIA NIMs tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def check_nim_health() -> dict[str, Any]:
    """Check the health status of all connected NVIDIA NIM microservices.

    NVIDIA NIMs (NVIDIA Inference Microservices) provide GPU-accelerated
    molecular docking (DiffDock), protein structure prediction (OpenFold3),
    and generative molecular design (GenMol).  This tool checks whether
    the NIM endpoints are reachable and reports their status.

    Returns:
        Dict with keys:
          - healthy: overall health (bool)
          - services: list of service status dicts, each with name, status
            (healthy/unhealthy/unavailable), latency_ms, and version.
          - checked_at: ISO timestamp of the health check.
    """
    result = await _get("/nims/health")
    if _is_error(result):
        return result
    return result


# Known SMA target symbols -> UniProt IDs (fast-path, avoids UniProt API call)
_SMA_UNIPROT: dict[str, str] = {
    "SMN1": "Q16637",
    "SMN2": "Q16637",
    "PLS3": "P13797",
    "STMN2": "Q93045",
    "NCALD": "P61601",
    "UBA1": "P22314",
    "CORO1C": "Q9ULV4",
    "ROCK2": "O75116",
    "MAPK14": "Q16539",
    "LIMK1": "P53667",
    "CFL2": "Q9Y281",
    "PFN1": "P07737",
}

# Valid amino acid single-letter codes (standard + ambiguous IUPAC)
_AA_CHARS = set("ACDEFGHIKLMNPQRSTVWYXBZUacdefghiklmnpqrstvwyxbzu")


def _looks_like_sequence(text: str) -> bool:
    """Return True if the string looks like a raw amino-acid sequence."""
    stripped = text.strip()
    if len(stripped) < 10:
        return False
    return all(c in _AA_CHARS for c in stripped)


async def _resolve_symbol_to_sequence(symbol: str) -> dict[str, Any]:
    """Resolve a protein gene symbol to its canonical amino-acid sequence.

    Fast path for 12 known SMA targets: directly fetches from UniProt by
    accession.  Fallback for any other symbol: queries the UniProt search API
    (human reviewed entries only).

    Returns a dict with keys ``sequence`` (str) and ``uniprot_id`` (str),
    or an ``error`` key describing why resolution failed.
    """
    upper = symbol.upper()
    uniprot_id: Optional[str] = _SMA_UNIPROT.get(upper)

    if not uniprot_id:
        # Query UniProt REST search for human reviewed entry
        search_url = "https://rest.uniprot.org/uniprotkb/search"
        params = {
            "query": f"gene:{symbol} AND organism_id:9606 AND reviewed:true",
            "fields": "accession",
            "format": "json",
            "size": "1",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(search_url, params=params)
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                if not results:
                    return {
                        "error": f"Unknown protein symbol: '{symbol}'",
                        "detail": (
                            f"Could not find '{symbol}' in UniProt "
                            "(Homo sapiens, reviewed). "
                            "Known SMA targets: "
                            + ", ".join(sorted(_SMA_UNIPROT.keys()))
                        ),
                    }
                uniprot_id = results[0]["primaryAccession"]
        except httpx.RequestError as exc:
            return {"error": f"UniProt search failed: {exc}"}

    # Fetch canonical sequence from UniProt FASTA
    fasta_url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.fasta"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(fasta_url)
            resp.raise_for_status()
            lines = resp.text.splitlines()
            sequence = "".join(line for line in lines if not line.startswith(">"))
            if not sequence:
                return {"error": f"Empty sequence returned for UniProt {uniprot_id}"}
            return {"sequence": sequence, "uniprot_id": uniprot_id}
    except httpx.RequestError as exc:
        return {"error": f"UniProt FASTA fetch failed: {exc}"}


def _parse_plddt(result: dict[str, Any]) -> tuple[Optional[float], list[float]]:
    """Extract mean pLDDT and per-residue pLDDT from a NIM response dict.

    Tries multiple paths since ESMfold and AlphaFold2 responses differ.
    Returns (mean_plddt, per_residue_list) or (None, []) if not found.
    """
    inner = result.get("result", result)

    # ESMfold returns a flat list under "plddt"
    per_residue: list[float] = inner.get("plddt", [])
    if isinstance(per_residue, list) and per_residue:
        mean = round(sum(per_residue) / len(per_residue), 2)
        return mean, [round(v, 2) for v in per_residue]

    # AlphaFold2 returns a scalar
    mean_scalar = inner.get("mean_plddt") or inner.get("plddt_mean")
    if mean_scalar is not None:
        return round(float(mean_scalar), 2), []

    return None, []


def _confidence_category(plddt_mean: Optional[float]) -> str:
    """Map mean pLDDT to a human-readable confidence tier."""
    if plddt_mean is None:
        return "unknown"
    if plddt_mean >= 90:
        return "very_high"
    if plddt_mean >= 70:
        return "high"
    if plddt_mean >= 50:
        return "medium"
    return "low"


@mcp.tool()
async def predict_protein_structure(
    protein: str,
    method: str = "auto",
) -> dict[str, Any]:
    """Predict the 3D structure of a protein using AlphaFold2 or ESMfold.

    Accepts a protein gene symbol (e.g. "NCALD", "PLS3", "SMN2") or a raw
    amino-acid sequence.  When a symbol is provided the canonical human
    sequence is fetched automatically from UniProt.

    Method selection:
    - ``"auto"``       -- ESMfold for < 300 residues, AlphaFold2 for >= 300.
    - ``"esmfold"``    -- Force ESMfold.  Fast (~15 s), no MSA needed.
    - ``"alphafold2"`` -- Force AlphaFold2.  Slower (minutes), MSA-based.

    Requires the ``SMA_ADMIN_KEY`` environment variable.

    Args:
        protein: Gene symbol (e.g. "NCALD") or amino-acid sequence
                 (>= 10 and <= 2000 single-letter residues).
        method:  "auto" (default), "esmfold", or "alphafold2".

    Returns:
        Dict containing: protein, sequence_length, method (chosen),
        pdb_structure (PDB text), plddt_mean, plddt_per_residue,
        confidence_category ("very_high"/"high"/"medium"/"low"/"unknown"),
        uniprot_id (if resolved from symbol), alphafold_db_available,
        alphafold_db_url (if available), runtime_seconds.
        Returns an error dict on auth failure, unknown symbol, invalid
        sequence length, or NIM service error.
    """
    import time

    t0 = time.monotonic()

    # 1. Validate method
    method = method.lower().strip()
    if method not in ("auto", "esmfold", "alphafold2"):
        return {
            "error": f"Unknown method: '{method}'",
            "detail": "Use 'auto', 'esmfold', or 'alphafold2'.",
        }

    # 2. Resolve input to sequence
    uniprot_id: Optional[str] = None
    protein_label: str = protein.strip()

    if _looks_like_sequence(protein):
        sequence = protein.strip().upper()
    else:
        resolution = await _resolve_symbol_to_sequence(protein_label)
        if _is_error(resolution):
            return resolution
        sequence = resolution["sequence"].upper()
        uniprot_id = resolution.get("uniprot_id")

    # 3. Validate length
    seq_len = len(sequence)
    if seq_len < 10:
        return {
            "error": "Sequence too short",
            "detail": f"Got {seq_len} residues; minimum is 10.",
        }
    if seq_len > 2000:
        return {
            "error": "Sequence too long",
            "detail": (
                f"Got {seq_len} residues; maximum is 2000. "
                "For large proteins consider fetching a pre-computed structure "
                "from AlphaFold DB: https://alphafold.ebi.ac.uk"
            ),
        }

    # 4. Select method
    if method == "auto":
        chosen_method = "esmfold" if seq_len < 300 else "alphafold2"
    else:
        chosen_method = method

    # 5. Auth check
    admin_key = os.environ.get("SMA_ADMIN_KEY")
    if not admin_key:
        return {
            "error": "SMA_ADMIN_KEY environment variable is not set",
            "detail": (
                "Structure prediction requires admin authentication. "
                "Set SMA_ADMIN_KEY to your platform admin key."
            ),
        }

    headers = {"X-Admin-Key": admin_key}

    # 6. Build request body and set appropriate timeout
    # AlphaFold2 (MSA-based) can take up to 15 minutes for long sequences
    nim_timeout = 900.0 if chosen_method == "alphafold2" else 120.0

    if chosen_method == "esmfold":
        body: dict[str, Any] = {"sequence": sequence}
        nim_path = "/nims/esmfold"
    else:
        body = {
            "sequence": sequence,
            "algorithm": "jackhmmer",
            "relax_prediction": True,
        }
        nim_path = "/nims/alphafold2"

    # 7. Call the platform NIM endpoint
    url = f"{API_BASE}{nim_path}"
    try:
        async with httpx.AsyncClient(timeout=nim_timeout) as client:
            response = await client.post(url, json=body, headers=headers)
            response.raise_for_status()
            nim_result = response.json()
    except httpx.TimeoutException:
        timeout_minutes = int(nim_timeout // 60)
        suggestion = (
            f"AlphaFold2 can take up to {timeout_minutes} min for long sequences. "
            "Try method='esmfold' for a faster (~15 s) result, or retry later."
            if chosen_method == "alphafold2"
            else f"ESMfold timed out after {int(nim_timeout)} s. "
            "The NIM service may be overloaded — retry later."
        )
        return {
            "error": "NIM request timed out",
            "method": chosen_method,
            "timeout_seconds": nim_timeout,
            "detail": suggestion,
        }
    except httpx.HTTPStatusError as exc:
        return {
            "error": f"NIM endpoint returned {exc.response.status_code}",
            "method": chosen_method,
            "url": url,
            "detail": exc.response.text[:500],
        }
    except httpx.RequestError as exc:
        return {
            "error": f"NIM request failed: {type(exc).__name__}",
            "method": chosen_method,
            "url": url,
            "detail": str(exc),
        }

    if _is_error(nim_result):
        nim_result["method"] = chosen_method
        return nim_result

    # 8. Parse and return structured response
    plddt_mean, plddt_per_residue = _parse_plddt(nim_result)
    inner = nim_result.get("result", nim_result)
    pdb_structure: str = inner.get("pdb", inner.get("pdb_structure", ""))

    runtime = round(time.monotonic() - t0, 1)
    alphafold_db_url: Optional[str] = (
        f"https://alphafold.ebi.ac.uk/entry/{uniprot_id}" if uniprot_id else None
    )

    out: dict[str, Any] = {
        "protein": protein_label,
        "sequence_length": seq_len,
        "method": chosen_method,
        "pdb_structure": pdb_structure,
        "plddt_mean": plddt_mean,
        "plddt_per_residue": plddt_per_residue,
        "confidence_category": _confidence_category(plddt_mean),
        "runtime_seconds": runtime,
        "alphafold_db_available": uniprot_id is not None,
    }
    if uniprot_id:
        out["uniprot_id"] = uniprot_id
        out["alphafold_db_url"] = alphafold_db_url

    return out



@mcp.tool()
async def dock_compound(
    compound: str,
    target: str = "SMN2",
    num_poses: int = 10,
    compare_existing: bool = True,
) -> dict[str, Any]:
    """Dock a compound against an SMA target using DiffDock v2.2 (NVIDIA NIM).

    Enhanced docking tool that accepts a drug name OR SMILES string and a target
    protein name (not a raw PDB ID).  The tool resolves the compound to SMILES
    via the platform drug registry (falling back to PubChem/ChEMBL), resolves
    the target via the platform target registry, runs DiffDock v2.2, and
    optionally compares the result with existing screening hits.

    Requires SMA_ADMIN_KEY environment variable for authentication.

    SMA targets supported: SMN1, SMN2, STMN2, PLS3, NCALD, UBA1, CORO1C, TP53,
    ROCK1, ROCK2, NRXN1, GEMIN2 (and any other target in the platform registry).

    Args:
        compound: Drug name (e.g. "riluzole", "fasudil", "4-AP"), SMILES string
                  (detected automatically by presence of =, #, (, ), [, ] etc.),
                  or PubChem CID prefixed with "CID:" (e.g. "CID:5353940").
        target:   Target protein symbol (e.g. "SMN2", "ROCK2", "CORO1C").
                  Defaults to "SMN2".
        num_poses: Number of binding poses to generate (1-20). Default 10.
        compare_existing: If True (default), fetch existing screening hits for
                          this target and rank the new compound among them.

    Returns:
        Dict with keys:
          - compound: resolved compound name
          - smiles: SMILES string used for docking
          - smiles_source: "input", "platform_drugs", "pubchem", or "chembl"
          - target: target symbol
          - target_uniprot: UniProt accession (if resolved)
          - nim: "DiffDock v2.2"
          - poses: list of pose dicts with pose_id, confidence,
            binding_site_residues (if available), sdf_content (if available)
          - top_confidence: highest confidence score across all poses
          - binding_assessment: "strong" (>0.4), "moderate" (0.2-0.4),
            "weak" (0-0.2), or "unlikely" (<0)
          - comparison: dict with existing_hits_for_target, rank_among_existing,
            percentile, better_than_riluzole, riluzole_confidence (only when
            compare_existing=True and screening hits are available)
          - runtime_seconds: elapsed wall-clock time
          - error: present only on failure
    """
    import time
    import re as _re

    t0 = time.monotonic()

    admin_key = os.environ.get("SMA_ADMIN_KEY")
    if not admin_key:
        return {
            "error": "SMA_ADMIN_KEY environment variable is not set",
            "detail": (
                "Docking requires admin authentication. "
                "Set SMA_ADMIN_KEY to your platform admin key."
            ),
        }

    headers = {"X-Admin-Key": admin_key}

    # ------------------------------------------------------------------
    # Step 1: Resolve compound to SMILES
    # ------------------------------------------------------------------
    # Detect raw SMILES by presence of characters that never appear in plain
    # drug names: = # ( ) [ ] / \ @ +
    smiles_chars = _re.compile(r"[=#()\[\]/\@\+]")
    compound_name: str
    smiles: str
    smiles_source: str

    if smiles_chars.search(compound):
        # Already a SMILES string
        smiles = compound
        compound_name = compound
        smiles_source = "input"
    elif compound.upper().startswith("CID:"):
        # PubChem CID shorthand
        cid = compound[4:].strip()
        pubchem_result = await _get(f"/drugs/pubchem/{cid}")
        if _is_error(pubchem_result) or not pubchem_result.get("smiles"):
            return {
                "error": f"Could not resolve PubChem CID {cid} to SMILES",
                "detail": pubchem_result.get("detail", "PubChem lookup failed") if _is_error(pubchem_result) else "No SMILES in response",
                "hint": "Provide the SMILES string directly instead.",
            }
        smiles = pubchem_result["smiles"]
        compound_name = pubchem_result.get("name", compound)
        smiles_source = "pubchem"
    else:
        # Drug name — look up in platform drug registry first
        drugs_result = await _get("/drugs", params={"q": compound, "limit": 5})
        resolved_smiles: Optional[str] = None
        resolved_name: str = compound
        smiles_source = "platform_drugs"

        if not _is_error(drugs_result):
            hits = drugs_result if isinstance(drugs_result, list) else drugs_result.get("results", [])
            for hit in hits:
                if hit.get("smiles"):
                    resolved_smiles = hit["smiles"]
                    resolved_name = hit.get("name", compound)
                    break

        if resolved_smiles:
            smiles = resolved_smiles
            compound_name = resolved_name
        else:
            # Fall back to PubChem name search via platform proxy
            pubchem_result = await _get("/drugs/pubchem/search", params={"name": compound})
            if not _is_error(pubchem_result) and pubchem_result.get("smiles"):
                smiles = pubchem_result["smiles"]
                compound_name = pubchem_result.get("name", compound)
                smiles_source = "pubchem"
            else:
                # Last resort: ChEMBL name lookup
                chembl_result = await _get("/drugs/chembl/search", params={"name": compound})
                if not _is_error(chembl_result) and chembl_result.get("smiles"):
                    smiles = chembl_result["smiles"]
                    compound_name = chembl_result.get("name", compound)
                    smiles_source = "chembl"
                else:
                    available: list[str] = []
                    all_drugs = await _get("/drugs", params={"limit": 30})
                    if not _is_error(all_drugs):
                        drug_list = all_drugs if isinstance(all_drugs, list) else all_drugs.get("results", [])
                        available = [d.get("name", "") for d in drug_list if d.get("name")]
                    return {
                        "error": f"Could not resolve compound '{compound}' to a SMILES string",
                        "detail": (
                            "No match found in platform drug registry, PubChem, or ChEMBL. "
                            "Provide the SMILES string directly."
                        ),
                        "available_platform_drugs": available[:20],
                        "hint": "Example SMILES for riluzole: 'CCOc1ccc2nc(N)sc2c1'",
                    }

    # ------------------------------------------------------------------
    # Step 2: Resolve target via platform registry
    # ------------------------------------------------------------------
    target_result = await _get(f"/targets/symbol/{target}")
    target_uniprot: Optional[str] = None

    if _is_error(target_result):
        all_targets = await _get("/targets", params={"limit": 50})
        available_targets: list[str] = []
        if not _is_error(all_targets):
            tlist = all_targets if isinstance(all_targets, list) else all_targets.get("results", [])
            available_targets = [t.get("symbol", "") for t in tlist if t.get("symbol")]
        return {
            "error": f"Target '{target}' not found in platform registry",
            "detail": target_result.get("detail", "Unknown target symbol"),
            "available_targets": available_targets[:20],
            "hint": "Common SMA targets: SMN2, STMN2, PLS3, NCALD, UBA1, CORO1C, ROCK2",
        }

    target_uniprot = target_result.get("uniprot_id") or target_result.get("uniprot")

    # ------------------------------------------------------------------
    # Step 3: Call DiffDock v2.2 via /api/v2/nims/dock
    # ------------------------------------------------------------------
    dock_body: dict[str, Any] = {
        "smiles": smiles,
        "target_symbol": target,
        "num_poses": max(1, min(num_poses, 20)),
    }
    if target_uniprot:
        dock_body["target_uniprot"] = target_uniprot

    dock_result = await _post("/nims/dock", json_body=dock_body, headers=headers)

    if _is_error(dock_result):
        return {
            "error": "DiffDock docking failed",
            "compound": compound_name,
            "smiles": smiles,
            "target": target,
            "detail": dock_result.get("detail", dock_result.get("error", "Unknown error")),
            "hint": (
                "Check NIM health with check_nim_health(). "
                "If DiffDock is unavailable, try reducing num_poses."
            ),
        }

    # ------------------------------------------------------------------
    # Step 4: Parse poses and compute top confidence
    # ------------------------------------------------------------------
    raw_poses = dock_result.get("poses", [])
    poses: list[dict[str, Any]] = []
    for i, p in enumerate(raw_poses):
        pose: dict[str, Any] = {
            "pose_id": i + 1,
            "confidence": float(p.get("confidence", p.get("score", 0.0))),
        }
        if p.get("binding_site_residues"):
            pose["binding_site_residues"] = p["binding_site_residues"]
        if p.get("sdf_content") or p.get("sdf"):
            pose["sdf_content"] = p.get("sdf_content") or p.get("sdf")
        poses.append(pose)

    # Sort by confidence descending
    poses.sort(key=lambda x: x["confidence"], reverse=True)

    if poses:
        top_confidence = poses[0]["confidence"]
    else:
        top_confidence = float(dock_result.get("top_score", dock_result.get("top_confidence", 0.0)))

    # Binding assessment thresholds based on DiffDock v2.2 score distribution
    if top_confidence > 0.4:
        binding_assessment = "strong"
    elif top_confidence > 0.2:
        binding_assessment = "moderate"
    elif top_confidence >= 0.0:
        binding_assessment = "weak"
    else:
        binding_assessment = "unlikely"

    # Warn if all poses are negative confidence
    if poses and all(p["confidence"] < 0 for p in poses):
        binding_assessment = "unlikely"

    # ------------------------------------------------------------------
    # Step 5: Compare with existing screening hits (optional)
    # ------------------------------------------------------------------
    comparison: dict[str, Any] = {}
    if compare_existing:
        screen_result = await _get(
            "/screen/compounds/results",
            params={"target": target, "limit": 500},
        )
        if not _is_error(screen_result):
            existing_hits = (
                screen_result
                if isinstance(screen_result, list)
                else screen_result.get("results", screen_result.get("hits", []))
            )
            if existing_hits:
                existing_scores = [
                    float(h.get("top_confidence", h.get("top_score", h.get("confidence", 0.0))))
                    for h in existing_hits
                    if h.get("top_confidence") is not None
                    or h.get("top_score") is not None
                    or h.get("confidence") is not None
                ]
                if existing_scores:
                    n_total = len(existing_scores)
                    rank = sum(1 for s in existing_scores if s > top_confidence) + 1
                    percentile = round(100.0 * (1 - (rank - 1) / max(n_total, 1)), 1)

                    # Find riluzole baseline
                    riluzole_confidence: Optional[float] = None
                    for h in existing_hits:
                        name_field = h.get("compound_name", h.get("name", "")).lower()
                        if "riluzole" in name_field:
                            riluzole_confidence = float(
                                h.get("top_confidence", h.get("top_score", h.get("confidence", 0.0)))
                            )
                            break

                    comparison = {
                        "existing_hits_for_target": n_total,
                        "rank_among_existing": rank,
                        "percentile": percentile,
                    }
                    if riluzole_confidence is not None:
                        comparison["better_than_riluzole"] = top_confidence > riluzole_confidence
                        comparison["riluzole_confidence"] = riluzole_confidence

    runtime_seconds = round(time.monotonic() - t0, 2)

    # ------------------------------------------------------------------
    # Assemble final result
    # ------------------------------------------------------------------
    output: dict[str, Any] = {
        "compound": compound_name,
        "smiles": smiles,
        "smiles_source": smiles_source,
        "target": target,
        "nim": "DiffDock v2.2",
        "poses": poses,
        "top_confidence": top_confidence,
        "binding_assessment": binding_assessment,
        "runtime_seconds": runtime_seconds,
    }
    if target_uniprot:
        output["target_uniprot"] = target_uniprot
    if comparison:
        output["comparison"] = comparison
    if dock_result.get("warning"):
        output["warning"] = dock_result["warning"]

    return output



# ---------------------------------------------------------------------------
# Drug Discovery & Virtual Screening tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def run_virtual_screening(
    target_symbol: str,
    n_molecules: int = 100,
    lipinski_filter: bool = True,
) -> dict[str, Any]:
    """Run generative virtual screening pipeline: GenMol generates molecules,
    RDKit filters by drug-likeness, DiffDock docks against AlphaFold structures,
    and results are ranked by composite score.

    Targets: SMN2, STMN2, PLS3, NCALD, UBA1, CORO1C, TP53.

    This is a multi-step computational chemistry pipeline that:
    1. Generates novel molecules using GenMol NIM
    2. Filters for drug-likeness (Lipinski rule of five) via RDKit
    3. Docks passing molecules against AlphaFold-predicted structures via DiffDock
    4. Ranks candidates by a composite score (docking affinity + drug-likeness)

    Args:
        target_symbol: Target gene symbol to screen against (e.g. "SMN2",
                       "CORO1C", "UBA1").
        n_molecules: Number of molecules to generate (default 100, max 1000).
        lipinski_filter: Whether to apply Lipinski drug-likeness filter
                         (default True).

    Returns:
        Dict with keys: target, n_generated, n_passed_filter, n_docked,
        top_candidates (list of ranked molecules with SMILES, docking_score,
        druglikeness_score, composite_score), pipeline_duration_s, and status.
        Requires SMA_ADMIN_KEY environment variable.
    """
    admin_key = os.environ.get("SMA_ADMIN_KEY")
    if not admin_key:
        return {
            "error": "SMA_ADMIN_KEY environment variable is not set",
            "detail": "Virtual screening requires admin authentication.",
        }

    headers = {"X-Admin-Key": admin_key}
    body = {
        "target_symbol": target_symbol,
        "n_molecules": min(n_molecules, 1000),
        "lipinski_filter": lipinski_filter,
    }
    result = await _post("/nims/virtual-screening", json_body=body, headers=headers)
    if _is_error(result):
        return result
    return result


@mcp.tool()
async def generate_molecules(
    target: str = "SMN2",
    scaffold_smiles: str = "",
    num_molecules: int = 50,
    filter_druglike: bool = True,
) -> dict[str, Any]:
    """Generate novel drug-like molecules using GenMol NIM for an SMA target.

    Calls NVIDIA GenMol to generate novel molecules from a scaffold SMILES,
    then optionally filters candidates for drug-likeness using the platform's
    Lipinski estimator.  Returns top candidates ranked by QED score.

    Default scaffolds are chosen based on the target:
    - SMN2: 4-aminopyridine (Nc1ccncc1) — validated DiffDock hit
    - ROCK2: fasudil-like indazole (c1ccc2[nH]c(-c3ccncc3)nc2c1)
    - CORO1C / PLS3: de novo generation (empty scaffold)
    - All other targets: de novo generation

    Args:
        target: SMA target symbol to generate molecules for (e.g. "SMN2",
                "ROCK2", "CORO1C", "PLS3", "NCALD", "UBA1").  Used to select
                a default scaffold when scaffold_smiles is not provided.
        scaffold_smiles: Starting molecule in SMILES notation.  If empty,
                         the target default scaffold is used.  Pass "" to
                         trigger de novo generation for novel targets.
        num_molecules: Number of molecules for GenMol to generate (10–500).
                       Larger values produce more diversity but take longer.
        filter_druglike: When True (default), each generated molecule is
                         scored against Lipinski Rule-of-Five + QED.  Only
                         molecules that pass are included in the final output.
                         Set to False to return all generated molecules.

    Returns:
        Dict with keys: scaffold, target, num_generated, num_passed_filter,
        molecules (list of candidates sorted by qed, each with smiles, qed,
        lipinski_pass, molecular_weight, hbd, hba, logp), nim, and
        filter_applied.  Returns an error dict if SMA_ADMIN_KEY is not set
        or GenMol is unavailable.
    """
    # --- Default scaffolds by target ---
    _DEFAULT_SCAFFOLDS: dict[str, str] = {
        "SMN2": "Nc1ccncc1",                          # 4-AP — validated DiffDock hit
        "ROCK2": "c1ccc2[nH]c(-c3ccncc3)nc2c1",       # fasudil-like ROCK inhibitor
        # CORO1C and PLS3 have no known small-molecule binders → de novo
        "CORO1C": "",
        "PLS3": "",
    }

    admin_key = os.environ.get("SMA_ADMIN_KEY")
    if not admin_key:
        return {
            "error": "SMA_ADMIN_KEY environment variable is not set",
            "detail": (
                "generate_molecules requires admin authentication. "
                "Set SMA_ADMIN_KEY to your platform admin key."
            ),
        }

    # Resolve scaffold
    resolved_scaffold = scaffold_smiles.strip()
    if not resolved_scaffold:
        resolved_scaffold = _DEFAULT_SCAFFOLDS.get(target.upper(), "")

    # Clamp num_molecules to valid range
    n = max(10, min(num_molecules, 500))

    # --- Step 1: Generate molecules via GenMol NIM ---
    headers = {"X-Admin-Key": admin_key}
    body: dict[str, Any] = {
        "scaffold_smiles": resolved_scaffold if resolved_scaffold else "C",
        "num_molecules": n,
    }
    gen_result = await _post("/nims/generate-molecules", json_body=body, headers=headers)
    if _is_error(gen_result):
        return gen_result

    # Extract generated SMILES from GenMol response.
    # GenMol returns {"result": {"smiles": [...], "scores": [...]}} or a flat
    # list under various keys depending on API version — handle both shapes.
    raw_smiles: list[str] = []
    if isinstance(gen_result, dict):
        inner = gen_result.get("result", gen_result)
        if isinstance(inner, dict):
            raw_smiles = inner.get("smiles", inner.get("molecules", []))
        elif isinstance(inner, list):
            raw_smiles = inner
    elif isinstance(gen_result, list):
        raw_smiles = gen_result

    # Normalise: entries may be bare strings or dicts with a "smiles" key
    normalised: list[str] = []
    for entry in raw_smiles:
        if isinstance(entry, str) and entry.strip():
            normalised.append(entry.strip())
        elif isinstance(entry, dict) and entry.get("smiles"):
            normalised.append(str(entry["smiles"]).strip())

    num_generated = len(normalised)

    # --- Step 2: Drug-likeness filtering via platform funnel API ---
    candidates: list[dict[str, Any]] = []
    for smi in normalised:
        dl_result = await _post("/funnel/estimate", json_body={"smiles": smi})
        if _is_error(dl_result):
            # Estimation failed for this molecule — skip silently
            continue

        mw = dl_result.get("mw", 0.0)
        logp = dl_result.get("logp", 0.0)
        hbd = dl_result.get("hbd", 0)
        hba = dl_result.get("hba", 0)
        rotatable = dl_result.get("rotatable", 0)
        lipinski_pass = bool(dl_result.get("lipinski_pass", False))

        # Approximate QED-like score: reward low MW, moderate LogP, low donors
        # (platform does not expose a standalone QED endpoint — this is a
        # simple surrogate based on the Bickerton 2012 desirability formula
        # applied to the Lipinski descriptors we have available)
        mw_score = max(0.0, 1.0 - max(0.0, mw - 200) / 300)
        logp_score = max(0.0, 1.0 - abs(logp - 2.5) / 4.0)
        hbd_score = max(0.0, 1.0 - hbd / 5.0)
        hba_score = max(0.0, 1.0 - hba / 10.0)
        rot_score = max(0.0, 1.0 - rotatable / 10.0)
        qed = round((mw_score + logp_score + hbd_score + hba_score + rot_score) / 5.0, 3)

        if filter_druglike and not lipinski_pass:
            continue

        candidates.append(
            {
                "smiles": smi,
                "qed": qed,
                "lipinski_pass": lipinski_pass,
                "molecular_weight": round(mw, 2),
                "logp": round(logp, 2),
                "hbd": hbd,
                "hba": hba,
            }
        )

    # Sort by QED descending
    candidates.sort(key=lambda m: m["qed"], reverse=True)

    return {
        "scaffold": resolved_scaffold or "(de novo)",
        "target": target,
        "num_generated": num_generated,
        "num_passed_filter": len(candidates),
        "filter_applied": filter_druglike,
        "molecules": candidates,
        "nim": "GenMol v1.0",
    }


@mcp.tool()
async def check_alphafold_complexes() -> list[dict[str, Any]]:
    """Check AlphaFold DB for predicted structures of 8 SMA protein complexes.

    Queries AlphaFold Database for predicted structures of key SMA-related
    protein complexes: SMN-Gemin2, SMN-Gemin3, SMN-Gemin5, SMN-p53,
    SMN-UBA1, PLS3-actin, NCALD-CaM, and STMN2-tubulin.

    Returns confidence scores (pLDDT and PAE) for each complex, indicating
    how reliable the predicted structure is for downstream docking studies.

    Returns:
        List of complex records, each including complex_name, uniprot_ids,
        alphafold_id, plddt_mean, pae_score, structure_url, found (bool),
        and confidence_category (high/medium/low).
    """
    result = await _get("/structures/alphafold-complexes")
    if _is_error(result):
        return [result]  # type: ignore[list-item]
    return result if isinstance(result, list) else result.get("items", result)


@mcp.tool()
async def list_binder_targets() -> list[dict[str, Any]]:
    """List 6 SMA targets available for protein binder design via Proteina-Complexa.

    Returns the set of SMA targets that have been prepared for de novo protein
    binder design: SMN2, SMN-p53 interface, NCALD, UBA1, PLS3, and STMN2.

    Each target includes the binding interface definition, AlphaFold structure
    availability, and readiness status for Proteina-Complexa submission.

    Returns:
        List of binder target records, each including target_symbol,
        interface_description, alphafold_structure (bool), pdb_id,
        binding_site_residues, proteina_ready (bool), and notes.
    """
    result = await _get("/structures/binder-targets")
    if _is_error(result):
        return [result]  # type: ignore[list-item]
    return result if isinstance(result, list) else result.get("items", result)


@mcp.tool()
async def design_protein_binder(
    target: str,
    hotspot_residues: Optional[list[str]] = None,
    binder_length: int = 100,
    num_designs: int = 5,
) -> dict[str, Any]:
    """Design a novel protein binder for an SMA target using RFdiffusion + ProteinMPNN.

    Runs a 2-step NIM pipeline:
    1. RFdiffusion generates binder backbone structures conditioned on the target
       interface (and optionally on specific hotspot residues).
    2. ProteinMPNN optimises an amino-acid sequence for each backbone, maximising
       packing and binding contacts.

    The target is resolved to a UniProt ID and AlphaFold structure automatically.
    If no hotspot residues are provided, the server uses pre-configured default
    interface residues from the SMA binder target catalogue.

    Args:
        target: Target protein symbol or name (e.g. "ROCK2", "NCALD", "SMN2").
        hotspot_residues: Optional list of residues to focus the binding interface
                          on, in chain+position format (e.g. ["A100", "A105",
                          "A230"]).  Leave empty to use defaults.
        binder_length: Length of the designed binder in residues (50 – 200,
                       default 100).
        num_designs: Number of independent binder designs to return (1 – 20,
                     default 5).

    Returns:
        Dict with keys:
          - target: resolved target symbol
          - target_uniprot: UniProt accession used for structure lookup
          - num_designs: number of designs returned
          - designs: list of dicts, each containing design_id, backbone_pdb
            (ATOM records as string), sequence (single-letter AA sequence),
            mpnn_score (0 – 1, higher = better packing), binder_length, and
            hotspot_contacts (residues contacted in final design)
          - pipeline: ordered list of NIM steps executed
          - runtime_seconds: wall-clock time of the pipeline
          - error (if applicable): human-readable failure reason

    Example::

        design_protein_binder(
            target="ROCK2",
            hotspot_residues=["A160", "A165", "A230"],
            binder_length=100,
            num_designs=5,
        )
        # -> 5 binder designs ready for ESMfold validation
    """
    admin_key = os.environ.get("SMA_ADMIN_KEY")
    if not admin_key:
        return {
            "error": "SMA_ADMIN_KEY environment variable is not set",
            "detail": (
                "Protein binder design requires admin authentication. "
                "Set SMA_ADMIN_KEY to an authorised API key."
            ),
        }

    # Clamp parameters to allowed ranges
    binder_length = max(50, min(200, binder_length))
    num_designs = max(1, min(20, num_designs))

    headers = {"X-Admin-Key": admin_key}

    # ------------------------------------------------------------------ #
    # Step 1: RFdiffusion — generate binder backbones
    # ------------------------------------------------------------------ #
    rfdiffusion_body: dict[str, Any] = {
        "target": target,
        "binder_length": binder_length,
        "num_designs": num_designs,
    }
    if hotspot_residues:
        rfdiffusion_body["hotspot_residues"] = hotspot_residues

    backbone_result = await _post(
        "/nims/design-binder",
        json_body=rfdiffusion_body,
        headers=headers,
    )

    if _is_error(backbone_result):
        # Surface the RFdiffusion error with helpful context
        return {
            "error": "RFdiffusion backbone design failed",
            "target": target,
            "rfdiffusion_error": backbone_result,
            "suggestion": (
                "Verify the target symbol is correct and has an available "
                "AlphaFold structure.  Use list_binder_targets() to see "
                "pre-configured targets."
            ),
        }

    # ------------------------------------------------------------------ #
    # Step 2: ProteinMPNN — design sequences for each backbone
    # ------------------------------------------------------------------ #
    # backbone_result is expected to contain backbone PDB data keyed by
    # design_id; pass the full backbone payload to the sequence design NIM.
    mpnn_body: dict[str, Any] = {
        "target": target,
        "backbones": backbone_result.get("backbones", backbone_result),
        "num_designs": num_designs,
    }

    sequence_result = await _post(
        "/nims/design-sequence",
        json_body=mpnn_body,
        headers=headers,
    )

    if _is_error(sequence_result):
        # Partial success: return backbone data even if MPNN failed
        return {
            "target": target,
            "target_uniprot": backbone_result.get("target_uniprot", "unknown"),
            "num_designs": 0,
            "designs": [],
            "pipeline": ["RFdiffusion (backbone)", "ProteinMPNN (sequence) — FAILED"],
            "runtime_seconds": backbone_result.get("runtime_seconds", 0),
            "warning": "ProteinMPNN sequence design failed; backbone data only.",
            "backbone_data": backbone_result,
            "mpnn_error": sequence_result,
        }

    # ------------------------------------------------------------------ #
    # Merge and return final result
    # ------------------------------------------------------------------ #
    # The sequence design endpoint is expected to return the complete merged
    # result with backbone + sequence data.  Pass it through, enriching with
    # pipeline metadata if the backend does not include it.
    if "pipeline" not in sequence_result:
        sequence_result["pipeline"] = [
            "RFdiffusion (backbone)",
            "ProteinMPNN (sequence)",
        ]
    if "target" not in sequence_result:
        sequence_result["target"] = target

    return sequence_result



# ---------------------------------------------------------------------------
# Target Report, Advisory, Analytics & Experiment tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_target_report(symbol: str) -> dict[str, Any]:
    """Get comprehensive report card for any SMA target.

    Returns a single-call overview combining convergence score, top claims,
    screening hits, species conservation, hypotheses, AlphaFold structure
    availability, and an assay suggestion.  This is the go-to tool for
    quickly understanding the full evidence landscape for a target.

    Args:
        symbol: HGNC symbol of the target (e.g. "SMN2", "STMN2", "PLS3",
                "NCALD", "CORO1C", "UBA1").

    Returns:
        Dict containing convergence_score, top_claims, screening_hits,
        conservation, hypotheses, alphafold_structure, assay_suggestion,
        and overall_summary.
    """
    result = await _get(f"/report/target/{symbol}")
    if _is_error(result):
        return result
    return result


@mcp.tool()
async def get_advisory_pack() -> dict[str, Any]:
    """Generate a comprehensive Scientific Advisory Pack.

    Produces a 5-section document suitable for sharing with external
    collaborators such as Scientific Advisory Board members, grant reviewers,
    or potential research partners.  Sections cover: platform overview, top
    targets with convergence scores, computational screening highlights,
    hypothesis landscape, and strengths/limitations assessment.

    Returns:
        Dict with keys: overview, top_targets, screening_hits, hypotheses,
        strengths_and_limitations, generated_at.
    """
    result = await _get("/advisory/pack")
    if _is_error(result):
        return result
    return result


@mcp.tool()
async def get_experiment_rankings(
    budget_k: Optional[float] = None,
    max_weeks: Optional[int] = None,
) -> dict[str, Any]:
    """Rank all SMA targets by Expected Value of Experiment.

    Computes P(success) x Impact / Cost for each target to help prioritise
    which experiments to run first given limited resources.  Optionally
    constrain by budget (in thousands of USD) and timeline (weeks).

    Args:
        budget_k: Optional budget constraint in thousands of USD (e.g. 50.0
                  for $50,000).  Filters out experiments exceeding this cost.
        max_weeks: Optional timeline constraint in weeks.  Filters out
                   experiments taking longer than this.

    Returns:
        Dict containing ranked list of targets with expected_value, p_success,
        impact_score, estimated_cost_k, estimated_weeks, and suggested_assay
        for each.
    """
    params: dict[str, Any] = {}
    if budget_k is not None:
        params["budget_k"] = budget_k
    if max_weeks is not None:
        params["max_weeks"] = max_weeks
    result = await _get("/experiment-value/rankings", params=params or None)
    if _is_error(result):
        return result
    return result


@mcp.tool()
async def get_analytics_summary() -> dict[str, Any]:
    """Get real-time platform analytics summary.

    Returns a comprehensive snapshot of the knowledge base including source
    counts by type, claim type distribution, convergence score distribution
    across targets, journal impact rankings, hypothesis status breakdown,
    and recent ingestion activity.

    Returns:
        Dict with keys: source_counts, claim_types, convergence_distribution,
        journal_rankings, hypothesis_status, recent_activity, generated_at.
    """
    result = await _get("/analytics/summary")
    if _is_error(result):
        return result
    return result


@mcp.tool()
async def test_reproducibility() -> dict[str, Any]:
    """Run reproducibility tests on convergence scores.

    Verifies that the platform's scoring algorithms are deterministic and
    that target rankings are stable across repeated computations.  This is
    a scientific integrity check — important for demonstrating that the
    platform's outputs are reliable and not subject to hidden randomness.

    Returns:
        Dict with keys: deterministic (bool), ranking_stable (bool),
        tests_run (int), tests_passed (int), details (list of individual
        test results), and tested_at.
    """
    result = await _get("/reproducibility/test")
    if _is_error(result):
        return result
    return result


@mcp.tool()
async def get_repurposing_candidates(
    min_score: Optional[float] = None,
) -> list[dict[str, Any]]:
    """List cross-disease drug repurposing candidates for SMA.

    Identifies approved or clinical-stage drugs from related neuromuscular
    diseases (ALS, DMD, myasthenia gravis, other motor neuron diseases) that
    share molecular targets or pathways with SMA and may be candidates for
    repurposing.

    Args:
        min_score: Optional minimum repurposing relevance score (0.0 – 1.0).
                   Higher values return only the most promising candidates.

    Returns:
        List of repurposing candidate records, each including drug_name,
        original_indication, shared_targets, shared_pathways, repurposing_score,
        approval_status, mechanism, and evidence_summary.
    """
    params: dict[str, Any] = {}
    if min_score is not None:
        params["min_score"] = min_score
    result = await _get("/repurpose/candidates", params=params or None)
    if _is_error(result):
        return [result]  # type: ignore[list-item]
    return result if isinstance(result, list) else result.get("items", result)



# ---------------------------------------------------------------------------
# NIM Tools: Molecule Optimisation, Sequence Alignment, Protein Embedding
# ---------------------------------------------------------------------------


@mcp.tool()
async def optimize_molecule(
    smiles: str,
    optimize_for: str = "drug_likeness",
    num_variants: int = 20,
) -> dict[str, Any]:
    """Optimise a molecule for improved properties using MolMIM NIM.

    Takes an existing SMILES string and generates optimised variants using
    NVIDIA MolMIM (CMA-ES guided latent-space optimisation).  Variants are
    scored for drug-likeness via the platform funnel and ranked by
    improvement over the input molecule.

    Args:
        smiles: Input molecule in SMILES notation
                (e.g. "Nc1ccncc1" for 4-aminopyridine).
        optimize_for: Optimisation objective -- one of:
                      - ``"drug_likeness"`` (default): maximise QED score
                      - ``"bbb_permeability"``: lower MW + logP for CNS access
                      - ``"potency"``: scaffold-preserving analogue expansion
        num_variants: Number of optimised variants to generate (5-100,
                      default 20).

    Returns:
        Dict with keys: input_smiles, input_qed, optimization_target,
        variants (list sorted by qed, each with smiles, qed,
        tanimoto_similarity, and improvement), nim, and filter_applied.
        Returns an error dict if SMA_ADMIN_KEY is not set, the SMILES is
        invalid, or MolMIM is unavailable.
    """
    admin_key = os.environ.get("SMA_ADMIN_KEY")
    if not admin_key:
        return {
            "error": "SMA_ADMIN_KEY environment variable is not set",
            "detail": (
                "optimize_molecule requires admin authentication. "
                "Set SMA_ADMIN_KEY to your platform admin key."
            ),
        }

    smiles = smiles.strip()
    if not smiles:
        return {
            "error": "smiles parameter is required",
            "detail": "Provide a valid SMILES string, e.g. \'Nc1ccncc1\' for 4-aminopyridine.",
        }

    # Clamp num_variants to valid range
    num_variants = max(5, min(100, num_variants))

    # --- Compute input molecule properties for baseline comparison ---
    input_props = await _post("/funnel/estimate", json_body={"smiles": smiles})
    if _is_error(input_props):
        input_qed: Optional[float] = None
    else:
        mw_in = input_props.get("mw", 0.0)
        logp_in = input_props.get("logp", 0.0)
        hbd_in = input_props.get("hbd", 0)
        hba_in = input_props.get("hba", 0)
        rot_in = input_props.get("rotatable", 0)
        mw_score_in = max(0.0, 1.0 - max(0.0, mw_in - 200) / 300)
        logp_score_in = max(0.0, 1.0 - abs(logp_in - 2.5) / 4.0)
        hbd_score_in = max(0.0, 1.0 - hbd_in / 5.0)
        hba_score_in = max(0.0, 1.0 - hba_in / 10.0)
        rot_score_in = max(0.0, 1.0 - rot_in / 10.0)
        input_qed = round(
            (mw_score_in + logp_score_in + hbd_score_in + hba_score_in + rot_score_in) / 5.0,
            3,
        )

    headers = {"X-Admin-Key": admin_key}
    body: dict[str, Any] = {
        "smiles": smiles,
        "optimize_for": optimize_for,
        "num_variants": num_variants,
        "algorithm": "CMA-ES",
    }

    molmim_result = await _post("/nims/generate-molecules", json_body=body, headers=headers)
    if _is_error(molmim_result):
        return {
            "error": "MolMIM optimisation failed",
            "input_smiles": smiles,
            "nim_error": molmim_result,
            "suggestion": (
                "Verify the SMILES is valid and that MolMIM is reachable. "
                "Use check_nim_health() to inspect NIM endpoint status."
            ),
        }

    # Extract generated variants -- same multi-shape handling as generate_molecules
    raw_smiles: list[str] = []
    if isinstance(molmim_result, dict):
        inner = molmim_result.get("result", molmim_result)
        if isinstance(inner, dict):
            raw_smiles = inner.get("smiles", inner.get("molecules", []))
        elif isinstance(inner, list):
            raw_smiles = inner
    elif isinstance(molmim_result, list):
        raw_smiles = molmim_result

    normalised: list[str] = []
    for entry in raw_smiles:
        if isinstance(entry, str) and entry.strip():
            normalised.append(entry.strip())
        elif isinstance(entry, dict) and entry.get("smiles"):
            normalised.append(str(entry["smiles"]).strip())

    # Remove duplicates and the input molecule itself
    seen: set[str] = {smiles}
    unique_smiles: list[str] = []
    for s in normalised:
        if s not in seen:
            seen.add(s)
            unique_smiles.append(s)

    # Score each variant
    variants: list[dict[str, Any]] = []
    for variant_smi in unique_smiles:
        props = await _post("/funnel/estimate", json_body={"smiles": variant_smi})
        if _is_error(props):
            continue

        mw = props.get("mw", 0.0)
        logp = props.get("logp", 0.0)
        hbd = props.get("hbd", 0)
        hba = props.get("hba", 0)
        rot = props.get("rotatable", 0)
        mw_s = max(0.0, 1.0 - max(0.0, mw - 200) / 300)
        logp_s = max(0.0, 1.0 - abs(logp - 2.5) / 4.0)
        hbd_s = max(0.0, 1.0 - hbd / 5.0)
        hba_s = max(0.0, 1.0 - hba / 10.0)
        rot_s = max(0.0, 1.0 - rot / 10.0)
        qed = round((mw_s + logp_s + hbd_s + hba_s + rot_s) / 5.0, 3)

        # Approximate Tanimoto similarity using character-level overlap
        # (true Tanimoto would require RDKit; this is a fast surrogate)
        len_union = max(len(smiles), len(variant_smi), 1)
        len_intersect = sum(1 for c in variant_smi if c in smiles)
        tanimoto = round(min(1.0, len_intersect / len_union), 3)

        improvement_delta = round(qed - (input_qed or 0.0), 3)
        improvement_str = (
            f"+{improvement_delta:.3f} QED" if improvement_delta >= 0
            else f"{improvement_delta:.3f} QED"
        )

        variants.append(
            {
                "smiles": variant_smi,
                "qed": qed,
                "tanimoto_similarity": tanimoto,
                "improvement": improvement_str,
            }
        )

    # Sort by QED descending
    variants.sort(key=lambda v: v["qed"], reverse=True)

    return {
        "input_smiles": smiles,
        "input_qed": input_qed,
        "optimization_target": optimize_for,
        "num_variants_requested": num_variants,
        "num_variants_returned": len(variants),
        "variants": variants,
        "nim": "MolMIM (CMA-ES)",
    }


@mcp.tool()
async def search_sequence_alignment(
    protein: str,
    databases: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Search for homologous protein sequences using MSA Search (ColabFold).

    Queries the NVIDIA MSA Search NIM to find evolutionary homologs of an
    SMA target protein across multiple sequence databases.  Useful for
    understanding conservation across species and identifying potential
    model organisms for experiments.

    Args:
        protein: Protein name/symbol (e.g. "SMN1", "NCALD", "PLS3") or a
                 raw amino acid sequence in single-letter code.  Symbols are
                 resolved to sequences automatically via the platform's target
                 registry.
        databases: Optional list of databases to search.  Supported values:
                   ``"uniref30"``, ``"pdb70"``, ``"colabfold_envdb"``.
                   Defaults to all three when omitted.

    Returns:
        Dict with keys: query_protein, query_length, num_hits, top_hits
        (list of up to 20 hits, each with species, identity_percent,
        alignment_length, and accession), conservation_summary, and
        databases_searched.  Returns an error dict if the protein cannot be
        resolved or MSA Search is unavailable.
    """
    admin_key = os.environ.get("SMA_ADMIN_KEY")
    if not admin_key:
        return {
            "error": "SMA_ADMIN_KEY environment variable is not set",
            "detail": (
                "search_sequence_alignment requires admin authentication. "
                "Set SMA_ADMIN_KEY to your platform admin key."
            ),
        }

    protein = protein.strip()
    if not protein:
        return {
            "error": "protein parameter is required",
            "detail": "Provide a protein symbol (e.g. \'SMN1\') or amino acid sequence.",
        }

    headers = {"X-Admin-Key": admin_key}
    body: dict[str, Any] = {"protein": protein}
    if databases:
        body["databases"] = databases

    msa_result = await _post("/nims/msa-search", json_body=body, headers=headers)
    if _is_error(msa_result):
        return {
            "error": "MSA Search failed",
            "query_protein": protein,
            "nim_error": msa_result,
            "suggestion": (
                "Verify the protein symbol is a known SMA target or supply "
                "a raw amino acid sequence.  Use check_nim_health() to "
                "inspect NIM endpoint status."
            ),
        }

    # Normalise the MSA result to the documented output schema.
    hits_raw: list[dict[str, Any]] = []
    if isinstance(msa_result, dict):
        hits_raw = msa_result.get(
            "hits", msa_result.get("alignments", msa_result.get("results", []))
        )
    elif isinstance(msa_result, list):
        hits_raw = msa_result

    # Normalise hit records
    top_hits: list[dict[str, Any]] = []
    for hit in hits_raw[:20]:
        top_hits.append(
            {
                "species": hit.get("species", hit.get("organism", "unknown")),
                "identity_percent": hit.get(
                    "identity_percent",
                    hit.get("identity", hit.get("pident", 0.0)),
                ),
                "alignment_length": hit.get(
                    "alignment_length", hit.get("length", 0)
                ),
                "accession": hit.get(
                    "accession", hit.get("id", hit.get("target_id", ""))
                ),
            }
        )

    num_hits = (
        msa_result.get("num_hits", len(hits_raw))
        if isinstance(msa_result, dict)
        else len(hits_raw)
    )
    query_length = (
        msa_result.get("query_length", 0) if isinstance(msa_result, dict) else 0
    )
    databases_searched = (
        msa_result.get(
            "databases_searched",
            databases or ["uniref30", "pdb70", "colabfold_envdb"],
        )
        if isinstance(msa_result, dict)
        else (databases or ["uniref30", "pdb70", "colabfold_envdb"])
    )

    # Derive a brief conservation summary from the top hits
    if top_hits:
        strong_hits = [
            h["identity_percent"]
            for h in top_hits
            if isinstance(h["identity_percent"], (int, float))
            and h["identity_percent"] > 70
        ]
        if len(strong_hits) >= 5:
            mean_id = round(sum(strong_hits) / len(strong_hits), 1)
            conservation_summary = (
                f"Highly conserved across {len(strong_hits)} top hits "
                f"(mean identity {mean_id}%)"
            )
        else:
            best = max(
                (
                    h["identity_percent"]
                    for h in top_hits
                    if isinstance(h["identity_percent"], (int, float))
                ),
                default=0,
            )
            conservation_summary = (
                f"Best hit identity {best}% -- moderate/low conservation"
            )
    else:
        conservation_summary = "No alignment hits returned"

    return {
        "query_protein": protein,
        "query_length": query_length,
        "num_hits": num_hits,
        "top_hits": top_hits,
        "conservation_summary": conservation_summary,
        "databases_searched": databases_searched,
    }


@mcp.tool()
async def embed_protein(
    proteins: list[str],
) -> dict[str, Any]:
    """Get protein sequence embeddings using ESM-2 650M NIM.

    Generates 1280-dimensional sequence embeddings for one or more proteins
    using NVIDIA\'s ESM-2 650M model.  Embeddings capture evolutionary and
    structural features and can be used for similarity search, clustering,
    and downstream ML tasks.

    Includes retry logic because the ESM-2 endpoint is intermittently
    degraded (HTTP 500 errors).  Up to 3 attempts with exponential backoff.

    Args:
        proteins: List of 1-10 protein names/symbols (e.g. ["SMN1", "SMN2",
                  "NCALD"]) or amino acid sequences.  Symbols are resolved
                  automatically.  More than 10 proteins are rejected to
                  avoid rate-limit issues.

    Returns:
        Dict with keys: proteins (list of resolved names), embeddings (dict
        mapping protein name to 1280-dim float list), similarity_matrix
        (pairwise cosine similarities for all pairs), embedding_dim (1280),
        nim ("ESM-2 650M"), and status_note.  Returns partial results if
        some proteins fail.  Returns an error dict if SMA_ADMIN_KEY is not
        set.
    """
    import asyncio
    import math

    admin_key = os.environ.get("SMA_ADMIN_KEY")
    if not admin_key:
        return {
            "error": "SMA_ADMIN_KEY environment variable is not set",
            "detail": (
                "embed_protein requires admin authentication. "
                "Set SMA_ADMIN_KEY to your platform admin key."
            ),
        }

    if not proteins:
        return {
            "error": "proteins list is required",
            "detail": "Provide at least one protein symbol or sequence.",
        }

    if len(proteins) > 10:
        return {
            "error": "Too many proteins",
            "detail": (
                f"Received {len(proteins)} proteins -- maximum is 10 to avoid "
                "ESM-2 rate limits.  Split into smaller batches."
            ),
        }

    headers = {"X-Admin-Key": admin_key}
    esm2_url = "/nims/esm2-embed"

    async def _embed_single(protein_input: str) -> tuple[str, Any]:
        """Embed one protein with up to 3 retries (exponential backoff)."""
        body: dict[str, Any] = {"protein": protein_input}
        last_err: Any = None
        for attempt in range(3):
            if attempt > 0:
                await asyncio.sleep(2 ** attempt)  # 2s, 4s backoff
            result = await _post(esm2_url, json_body=body, headers=headers)
            if not _is_error(result):
                return protein_input, result
            # Retry only on transient HTTP errors
            err_str = str(result.get("error", ""))
            if "500" in err_str or "502" in err_str or "503" in err_str:
                last_err = result
                continue
            # Non-transient error -- stop retrying
            return protein_input, result
        return protein_input, last_err or {"error": "ESM-2 failed after 3 attempts"}

    # Embed all proteins concurrently
    tasks = [_embed_single(p.strip()) for p in proteins if p.strip()]
    results = await asyncio.gather(*tasks)

    embeddings: dict[str, list[float]] = {}
    failed: list[str] = []
    embedding_dim = 1280

    for protein_name, emb_result in results:
        if _is_error(emb_result):
            failed.append(protein_name)
            continue

        # Extract the embedding vector -- handle different response shapes
        vec: list[float] = []
        if isinstance(emb_result, dict):
            vec = emb_result.get(
                "embedding",
                emb_result.get("vector", emb_result.get("embeddings", [])),
            )
            # Some adapters return {protein: {embedding: [...]}} nested
            if isinstance(vec, dict):
                vec = vec.get("embedding", vec.get("vector", []))
        elif isinstance(emb_result, list):
            vec = emb_result

        if vec and isinstance(vec, list):
            embeddings[protein_name] = [float(x) for x in vec[:embedding_dim]]
            if len(embeddings[protein_name]) > 0:
                embedding_dim = len(embeddings[protein_name])

    # Compute pairwise cosine similarity for all successfully embedded proteins
    def _cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return round(dot / (norm_a * norm_b), 4)

    similarity_matrix: dict[str, float] = {}
    embedded_names = list(embeddings.keys())
    for i, name_a in enumerate(embedded_names):
        for name_b in embedded_names[i + 1:]:
            key = f"{name_a}-{name_b}"
            similarity_matrix[key] = _cosine(embeddings[name_a], embeddings[name_b])

    status_note = (
        "ESM-2 endpoint is intermittently degraded -- results may require retry"
    )
    if failed:
        status_note += f". Failed to embed: {", ".join(failed)}"

    return {
        "proteins": [p.strip() for p in proteins if p.strip()],
        "embeddings": embeddings,
        "similarity_matrix": similarity_matrix,
        "embedding_dim": embedding_dim,
        "nim": "ESM-2 650M",
        "status_note": status_note,
        "failed": failed,
    }


# ---------------------------------------------------------------------------
# PMID Verification Tool
# ---------------------------------------------------------------------------


@mcp.tool()
async def verify_pmid(pmid: str) -> str:
    """Verify a PubMed ID (PMID) against the NCBI database.

    Use this EVERY TIME a Codex/LLM research query returns a PMID.
    LLMs hallucinate ~11% of PMIDs. This tool checks if the PMID exists
    and returns the actual paper title.

    Args:
        pmid: The PubMed ID to verify (e.g., "21920940").
    """
    import re

    pmid = re.sub(r"\D", "", pmid.strip())
    if not pmid or len(pmid) < 7:
        return f"Invalid PMID format: '{pmid}'. Must be 7-9 digits."

    try:
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url)
            data = r.json()

        result = data.get("result", {}).get(pmid, {})
        title = result.get("title", "")
        source = result.get("source", "")
        pubdate = result.get("pubdate", "")

        if not title or "cannot" in title.lower():
            return f"PMID {pmid}: NOT FOUND — this PMID does not exist in PubMed. Likely HALLUCINATED."

        return (
            f"PMID {pmid}: VERIFIED\n"
            f"Title: {title}\n"
            f"Journal: {source}\n"
            f"Date: {pubdate}"
        )
    except Exception as e:
        return f"PMID {pmid}: VERIFICATION ERROR — {e}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
