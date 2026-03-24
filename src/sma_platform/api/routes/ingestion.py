"""Ingestion trigger endpoints — kick off data pulls from external sources."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query

from ...core.database import execute, fetch, fetchrow
from ...ingestion.adapters import biorxiv, chembl, clinicaltrials, kegg, pmc, pubmed, string_db, uniprot

from datetime import date as _date_type


def _parse_date_str(s: str | None) -> _date_type | None:
    """Parse a YYYY-MM-DD string into a date object for asyncpg."""
    if not s:
        return None
    try:
        parts = s.split("-")
        if len(parts) == 3:
            return _date_type(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        pass
    return None
from ...reasoning.claim_extractor import process_all_unprocessed, relink_all_claims
from ...reasoning.failure_extractor import process_all_drug_outcomes
from ...reasoning.graph_expander import expand_graph
from ...reasoning.hypothesis_generator import generate_all_hypotheses, generate_hypothesis_for_target
from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ingest/pubmed", dependencies=[Depends(require_admin_key)])
async def trigger_pubmed_ingestion(days_back: int = Query(default=7, ge=1, le=365)):
    """Pull recent SMA papers from PubMed and store in sources table."""
    start = datetime.now(timezone.utc)
    papers = await pubmed.search_recent_sma(days_back=days_back)

    new_count = 0
    updated_count = 0
    errors: list[str] = []

    for paper in papers:
        try:
            result = await execute(
                """INSERT INTO sources (source_type, external_id, title, authors, journal, pub_date, doi, url, abstract)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                   ON CONFLICT (source_type, external_id) DO UPDATE
                   SET title = excluded.title, abstract = excluded.abstract, updated_at = CURRENT_TIMESTAMP""",
                "pubmed",
                paper["pmid"],
                paper["title"],
                paper["authors"],
                paper["journal"],
                _parse_date_str(paper["pub_date"]),
                paper["doi"],
                paper["url"],
                paper["abstract"],
            )
            if "INSERT" in result:
                new_count += 1
            else:
                updated_count += 1
        except Exception as e:
            errors.append(f"PMID {paper.get('pmid')}: {e}")

    duration = (datetime.now(timezone.utc) - start).total_seconds()

    await execute(
        """INSERT INTO ingestion_log (source_type, query, items_found, items_new, items_updated, errors, duration_secs)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        "pubmed", "daily_sma_search", len(papers), new_count, updated_count,
        errors[:10] if errors else None, duration,
    )

    return {
        "source": "pubmed",
        "papers_found": len(papers),
        "new": new_count,
        "updated": updated_count,
        "errors": len(errors),
        "duration_secs": round(duration, 2),
    }


@router.post("/ingest/biorxiv", dependencies=[Depends(require_admin_key)])
async def trigger_biorxiv_ingestion(days_back: int = Query(default=7, ge=1, le=90)):
    """Scan bioRxiv + medRxiv for SMA-relevant preprints and store as sources."""
    start = datetime.now(timezone.utc)
    preprints = await biorxiv.scan_preprints(days_back=days_back)

    new_count = 0
    updated_count = 0
    errors: list[str] = []

    for p in preprints:
        try:
            result = await execute(
                """INSERT INTO sources (source_type, external_id, title, authors, journal, pub_date, doi, url, abstract)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                   ON CONFLICT (source_type, external_id) DO UPDATE
                   SET title = excluded.title, abstract = excluded.abstract, updated_at = CURRENT_TIMESTAMP""",
                "preprint",
                p["doi"],
                p["title"],
                p["authors"] if isinstance(p["authors"], list) else [],
                p.get("server", "biorxiv"),
                _parse_date_str(p.get("posted_date")),
                p["doi"],
                p["url"],
                p["abstract"],
            )
            if "INSERT" in str(result):
                new_count += 1
            else:
                updated_count += 1
        except Exception as e:
            errors.append(f"DOI {p.get('doi')}: {e}")

    duration = (datetime.now(timezone.utc) - start).total_seconds()

    await execute(
        """INSERT INTO ingestion_log (source_type, query, items_found, items_new, items_updated, errors, duration_secs)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        "biorxiv", "sma_preprint_scan", len(preprints), new_count, updated_count,
        errors[:10] if errors else None, duration,
    )

    return {
        "source": "biorxiv+medrxiv",
        "papers_found": len(preprints),
        "new": new_count,
        "updated": updated_count,
        "errors": len(errors),
        "duration_secs": round(duration, 2),
    }


@router.post("/ingest/trials", dependencies=[Depends(require_admin_key)])
async def trigger_trials_ingestion():
    """Pull all SMA clinical trials from ClinicalTrials.gov."""
    start = datetime.now(timezone.utc)
    trials = await clinicaltrials.fetch_all_sma_trials()

    new_count = 0
    updated_count = 0
    errors: list[str] = []

    for trial in trials:
        try:
            result = await execute(
                """INSERT INTO trials (nct_id, title, status, phase, conditions, interventions, sponsor,
                   start_date, completion_date, enrollment, results_summary, url)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                   ON CONFLICT (nct_id) DO UPDATE
                   SET title = excluded.title, status = excluded.status, phase = excluded.phase,
                       enrollment = excluded.enrollment, updated_at = CURRENT_TIMESTAMP""",
                trial["nct_id"],
                trial["title"],
                trial["status"],
                trial["phase"],
                json.dumps(trial["conditions"]),
                json.dumps(trial["interventions"]),
                trial["sponsor"],
                trial.get("start_date"),
                trial.get("completion_date"),
                trial.get("enrollment"),
                trial.get("brief_summary"),
                trial["url"],
            )
            if "INSERT" in result:
                new_count += 1
            else:
                updated_count += 1
        except Exception as e:
            errors.append(f"NCT {trial.get('nct_id')}: {e}")

    duration = (datetime.now(timezone.utc) - start).total_seconds()

    await execute(
        """INSERT INTO ingestion_log (source_type, query, items_found, items_new, items_updated, errors, duration_secs)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        "clinicaltrials", "all_sma_trials", len(trials), new_count, updated_count,
        errors[:10] if errors else None, duration,
    )

    return {
        "source": "clinicaltrials",
        "trials_found": len(trials),
        "new": new_count,
        "updated": updated_count,
        "errors": len(errors),
        "duration_secs": round(duration, 2),
    }


@router.post("/ingest/trial-results", dependencies=[Depends(require_admin_key)])
async def trigger_trial_results_ingestion():
    """Fetch results for completed SMA trials and store as sources for claim extraction.

    Calls ClinicalTrials.gov v2 API for all completed SMA trials that have posted
    results (outcome measures, adverse events, participant flow).  Each trial's
    ``results_summary`` text is stored in ``sources.abstract`` so the normal
    ``/extract/claims`` pipeline can pick it up.
    """
    start = datetime.now(timezone.utc)
    trial_results = await clinicaltrials.fetch_all_sma_trial_results()

    new_count = 0
    updated_count = 0
    claims_extracted = 0
    errors: list[str] = []

    for tr in trial_results:
        nct_id = tr["nct_id"]
        try:
            # Store as a source record so claim_extractor can process the results_summary
            result = await execute(
                """INSERT INTO sources (source_type, external_id, title, authors, journal, pub_date, doi, url, abstract, metadata)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                   ON CONFLICT (source_type, external_id) DO UPDATE
                   SET title = excluded.title, abstract = excluded.abstract,
                       metadata = excluded.metadata, updated_at = CURRENT_TIMESTAMP""",
                "clinicaltrials",
                f"{nct_id}_results",
                tr["title"],
                [],  # no individual authors for trial results (text[] column)
                "ClinicalTrials.gov Results",
                _parse_date_str(tr.get("results_first_posted")),
                None,  # no DOI for trial results
                tr["url"],
                tr.get("results_summary", ""),
                json.dumps({
                    "phase": tr.get("phase"),
                    "status": tr.get("status"),
                    "outcome_count": len(tr.get("outcome_measures", [])),
                    "adverse_event_groups": len(tr.get("adverse_events", [])),
                    "has_participant_flow": bool(tr.get("participant_flow")),
                    "last_update_posted": tr.get("last_update_posted"),
                }),
            )
            if "INSERT" in str(result):
                new_count += 1
            else:
                updated_count += 1

            # Also update the trials table results_summary if the trial exists there
            await execute(
                """UPDATE trials SET results_summary = $1, updated_at = CURRENT_TIMESTAMP
                   WHERE nct_id = $2""",
                tr.get("results_summary", ""),
                nct_id,
            )
        except Exception as e:
            errors.append(f"NCT {nct_id}: {e}")
            logger.error("Failed to store trial results for %s: %s", nct_id, e)

    # Trigger claim extraction on the newly stored trial result sources
    try:
        claim_result = await process_all_unprocessed()
        claims_extracted = claim_result.get("claims_extracted", 0)
    except Exception as e:
        errors.append(f"Claim extraction: {e}")
        logger.error("Claim extraction after trial results failed: %s", e)

    duration = (datetime.now(timezone.utc) - start).total_seconds()

    await execute(
        """INSERT INTO ingestion_log (source_type, query, items_found, items_new, items_updated, errors, duration_secs)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        "clinicaltrials_results", "sma_trial_results", len(trial_results), new_count, updated_count,
        errors[:10] if errors else None, duration,
    )

    return {
        "source": "clinicaltrials_results",
        "trials_checked": len(trial_results) + updated_count,
        "results_found": new_count + updated_count,
        "claims_extracted": claims_extracted,
        "new": new_count,
        "updated": updated_count,
        "errors": len(errors),
        "duration_secs": round(duration, 2),
    }


@router.post("/ingest/patents", dependencies=[Depends(require_admin_key)])
async def trigger_patent_ingestion(
    json_path: str = Query(default="", description="Path to pre-fetched JSON file (Google Patents blocks server IPs)"),
):
    """Import SMA-related patents into the sources table.

    Google Patents blocks server IPs (returns 503), so patents should be
    fetched locally and uploaded as JSON.  Two modes:

    1. **json_path** (recommended): Import from a pre-fetched JSON file on disk.
       Fetch locally: ``python -c "import asyncio; from sma_platform.ingestion.adapters.patents import fetch_all_sma_patents; print(asyncio.run(fetch_all_sma_patents()))"``
       Then SCP the JSON to the server and pass the path.

    2. **No json_path**: Attempt live fetch via Google Patents XHR (will fail from most servers).
    """
    try:
        from ...ingestion.adapters import patents
    except (ImportError, ModuleNotFoundError):
        from fastapi import HTTPException
        raise HTTPException(status_code=501, detail="Patents adapter not deployed yet.")

    import pathlib

    start = datetime.now(timezone.utc)

    if json_path:
        # Import from pre-fetched JSON file — restrict to data/ directory
        p = pathlib.Path(json_path).resolve()
        allowed_dir = pathlib.Path(__file__).resolve().parents[4] / "data"
        if not str(p).startswith(str(allowed_dir)):
            return {"error": "json_path must be within the data/ directory"}
        if not p.exists():
            return {"error": "File not found"}
        all_patents = json.loads(p.read_text())
        logger.info("Importing %d patents from %s", len(all_patents), p)
    else:
        # Try live fetch (may fail from server IPs)
        all_patents = await patents.fetch_all_sma_patents()

    new_count = 0
    updated_count = 0
    errors: list[str] = []

    for pat in all_patents:
        try:
            summary = patents.build_patent_summary(pat)
            result = await execute(
                """INSERT INTO sources (source_type, external_id, title, authors, journal, pub_date, doi, url, abstract)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                   ON CONFLICT (source_type, external_id) DO UPDATE
                   SET title = excluded.title, abstract = excluded.abstract, updated_at = CURRENT_TIMESTAMP""",
                "patent",
                pat["patent_id"],
                pat.get("title", ""),
                pat.get("assignees", []),  # text[] column
                "US Patent",
                pat.get("grant_date"),
                None,
                pat.get("url", ""),
                summary,
            )
            if "INSERT" in str(result):
                new_count += 1
            else:
                updated_count += 1
        except Exception as e:
            errors.append(f"Patent {pat.get('patent_id')}: {e}")

    duration = (datetime.now(timezone.utc) - start).total_seconds()

    await execute(
        """INSERT INTO ingestion_log (source_type, query, items_found, items_new, items_updated, errors, duration_secs)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        "patents", "sma_patents", len(all_patents), new_count, updated_count,
        errors[:10] if errors else None, duration,
    )

    return {
        "source": "patents",
        "patents_found": len(all_patents),
        "new": new_count,
        "updated": updated_count,
        "errors": len(errors),
        "duration_secs": round(duration, 2),
    }


@router.post("/ingest/structures", dependencies=[Depends(require_admin_key)])
async def trigger_structure_ingestion():
    """Fetch AlphaFold protein structure predictions for core SMA proteins.

    Uses the pre-defined SMA_PROTEINS mapping (SMN1, SMN2, PLS3, STMN2,
    NCALD, UBA1, CORO1C) to fetch structure predictions and pLDDT scores.
    Stores structure metadata on the corresponding target records.
    """
    try:
        from ...ingestion.adapters import alphafold
    except (ImportError, ModuleNotFoundError):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=501,
            detail="AlphaFold adapter not deployed yet.",
        )

    start = datetime.now(timezone.utc)
    errors: list[str] = []

    # Fetch all SMA protein structures
    structures = await alphafold.fetch_sma_protein_structures()

    # Map symbols to target IDs
    targets = await fetch("SELECT id, symbol FROM targets WHERE target_type = 'gene'")
    symbol_to_id = {t["symbol"]: str(t["id"]) for t in targets}

    updated_count = 0
    for structure in structures:
        symbol = structure.get("symbol", "")
        target_id = symbol_to_id.get(symbol)
        if not target_id:
            continue

        try:
            summary = alphafold.build_structure_summary(structure)
            await execute(
                """UPDATE targets SET metadata = jsonb_set(
                       COALESCE(metadata, '{}')::jsonb,
                       '{alphafold}',
                       $1::jsonb
                   ), updated_at = CURRENT_TIMESTAMP
                   WHERE id = $2""",
                json.dumps({
                    "uniprot_id": structure.get("uniprot_id"),
                    "mean_plddt": structure.get("mean_plddt"),
                    "model_url": structure.get("model_url"),
                    "cif_url": structure.get("cif_url"),
                    "sequence_length": structure.get("sequence_length"),
                    "summary": summary,
                }),
                target_id,
            )
            updated_count += 1
        except Exception as e:
            errors.append(f"{symbol}: {e}")
            logger.error("AlphaFold store failed for %s: %s", symbol, e)

    duration = (datetime.now(timezone.utc) - start).total_seconds()

    await execute(
        """INSERT INTO ingestion_log (source_type, query, items_found, items_new, items_updated, errors, duration_secs)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        "alphafold", "sma_structures", len(alphafold.SMA_PROTEINS), updated_count, 0,
        errors[:10] if errors else None, duration,
    )

    return {
        "source": "alphafold",
        "proteins_queried": len(alphafold.SMA_PROTEINS),
        "structures_found": len(structures),
        "targets_updated": updated_count,
        "errors": len(errors),
        "duration_secs": round(duration, 2),
    }


@router.post("/extract/claims", dependencies=[Depends(require_admin_key)])
async def trigger_claim_extraction():
    """Extract structured claims from all unprocessed paper abstracts using LLM."""
    start = datetime.now(timezone.utc)
    result = await process_all_unprocessed()
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration_secs"] = round(duration, 2)
    return result


@router.post("/relink/claims", dependencies=[Depends(require_admin_key)])
async def trigger_claim_relinking():
    """Retroactively link existing claims to targets using fuzzy matching."""
    start = datetime.now(timezone.utc)
    result = await relink_all_claims()
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration_secs"] = round(duration, 2)
    return result


@router.post("/generate/hypotheses", dependencies=[Depends(require_admin_key)])
async def trigger_hypothesis_generation():
    """Generate hypothesis cards for all targets by cross-referencing claims."""
    start = datetime.now(timezone.utc)
    result = await generate_all_hypotheses()
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration_secs"] = round(duration, 2)
    return result


@router.post("/generate/hypothesis/{target_id}", dependencies=[Depends(require_admin_key)])
async def trigger_single_hypothesis(target_id: str):
    """Generate a hypothesis card for a single target."""
    result = await generate_hypothesis_for_target(target_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(404, "Target not found or no claims available")
    return result


@router.post("/ingest/network", dependencies=[Depends(require_admin_key)])
async def trigger_network_ingestion():
    """Pull protein-protein interactions from STRING and pathway data from KEGG.

    Populates graph_edges table for network_centrality scoring.
    """
    start = datetime.now(timezone.utc)
    errors: list[str] = []

    # Build symbol → target_id lookup
    targets = await fetch("SELECT id, symbol FROM targets WHERE target_type = 'gene'")
    symbol_to_id = {t["symbol"]: str(t["id"]) for t in targets}

    # --- STRING interactions ---
    string_edges = 0
    try:
        interactions = await string_db.fetch_interactions(required_score=400)
        for inter in interactions:
            src_sym = inter["source"]
            dst_sym = inter["target"]
            src_id = symbol_to_id.get(src_sym)
            dst_id = symbol_to_id.get(dst_sym)
            if not src_id or not dst_id or src_id == dst_id:
                continue

            await execute(
                """INSERT INTO graph_edges (src_id, dst_id, relation, direction, confidence, metadata)
                   VALUES ($1, $2, $3, $4, $5, $6)
                   ON CONFLICT DO NOTHING""",
                src_id, dst_id, "protein_interaction", "undirected",
                inter["combined_score"],
                json.dumps({"source": "STRING", "nscore": inter["nscore"],
                            "fscore": inter["fscore"], "escore": inter["escore"],
                            "dscore": inter["dscore"], "tscore": inter["tscore"]}),
            )
            string_edges += 1
    except Exception as e:
        errors.append(f"STRING: {e}")
        logger.error("STRING ingestion failed: %s", e)

    # --- KEGG pathway genes ---
    kegg_edges = 0
    our_kegg_genes: set[str] = set()
    try:
        pathway_genes = await kegg.fetch_pathway_genes()
        # Find which KEGG genes overlap with our targets
        kegg_symbols = {g["symbol"] for g in pathway_genes}
        our_kegg_genes = kegg_symbols & set(symbol_to_id.keys())

        # Create pathway membership edges (gene → pathway target if exists)
        pathway_target = await fetchrow(
            "SELECT id FROM targets WHERE symbol = 'MTOR_PATHWAY' OR target_type = 'pathway' LIMIT 1"
        )

        # Create co-pathway edges between genes that share the SMA pathway
        our_genes_list = sorted(our_kegg_genes)
        for i, g1 in enumerate(our_genes_list):
            for g2 in our_genes_list[i + 1:]:
                src_id = symbol_to_id.get(g1)
                dst_id = symbol_to_id.get(g2)
                if src_id and dst_id:
                    await execute(
                        """INSERT INTO graph_edges (src_id, dst_id, relation, direction, confidence, metadata)
                           VALUES ($1, $2, $3, $4, $5, $6)
                           ON CONFLICT DO NOTHING""",
                        src_id, dst_id, "shared_pathway", "undirected", 0.8,
                        json.dumps({"source": "KEGG", "pathway": "hsa05033",
                                    "pathway_name": "Spinal muscular atrophy"}),
                    )
                    kegg_edges += 1

        # Store all KEGG pathway gene symbols for reference
        kegg_gene_list = [g["symbol"] for g in pathway_genes]
    except Exception as e:
        errors.append(f"KEGG: {e}")
        logger.error("KEGG ingestion failed: %s", e)
        kegg_gene_list = []

    duration = (datetime.now(timezone.utc) - start).total_seconds()

    await execute(
        """INSERT INTO ingestion_log (source_type, query, items_found, items_new, items_updated, errors, duration_secs)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        "network", "string+kegg", string_edges + kegg_edges, string_edges + kegg_edges, 0,
        json.dumps(errors) if errors else None, duration,
    )

    return {
        "source": "network",
        "string_edges": string_edges,
        "kegg_edges": kegg_edges,
        "kegg_pathway_genes": len(kegg_gene_list) if kegg_gene_list else 0,
        "our_genes_in_kegg": len(our_kegg_genes),
        "errors": errors,
        "duration_secs": round(duration, 2),
    }


@router.post("/ingest/compounds", dependencies=[Depends(require_admin_key)])
async def trigger_compound_ingestion(limit_per_target: int = Query(default=50, ge=1, le=500)):
    """Pull bioactivity data from ChEMBL for all gene targets.

    Searches ChEMBL for each gene target in the database, retrieves
    bioactivity records, and stores compound-target edges in graph_edges.
    """
    start = datetime.now(timezone.utc)
    errors: list[str] = []

    # Get all gene targets
    targets = await fetch("SELECT id, symbol FROM targets WHERE target_type = 'gene'")
    symbol_to_id = {t["symbol"]: str(t["id"]) for t in targets}
    symbols = list(symbol_to_id.keys())

    # Fetch bioactivities from ChEMBL
    compound_edges = 0
    compounds_seen: set[str] = set()
    try:
        activities = await chembl.search_sma_bioactivities(
            target_symbols=symbols,
            limit_per_target=limit_per_target,
        )

        for act in activities:
            mol_id = act.get("molecule_chembl_id", "")
            target_sym = act.get("target_symbol", "")
            target_id = symbol_to_id.get(target_sym)
            if not target_id or not mol_id:
                continue

            # We need a target node for the compound too; use the gene target as dst
            # and store compound info in metadata
            pchembl = act.get("pchembl_value")
            confidence = 0.5
            if pchembl is not None:
                try:
                    # pChEMBL >= 6 is moderately active, >= 8 is highly active
                    pval = float(pchembl)
                    confidence = min(1.0, max(0.1, pval / 10.0))
                except (ValueError, TypeError):
                    pass

            metadata = {
                "source": "ChEMBL",
                "molecule_chembl_id": mol_id,
                "canonical_smiles": act.get("canonical_smiles", ""),
                "standard_type": act.get("standard_type", ""),
                "standard_value": act.get("standard_value"),
                "standard_units": act.get("standard_units", ""),
                "pchembl_value": pchembl,
                "assay_type": act.get("assay_type", ""),
                "target_chembl_id": act.get("target_chembl_id", ""),
            }

            # Use a self-referential edge on the target to store compound binding data
            # (compound is not in targets table, so we store it as metadata on the gene target)
            await execute(
                """INSERT INTO graph_edges (src_id, dst_id, relation, direction, confidence, metadata)
                   VALUES ($1, $2, $3, $4, $5, $6)
                   ON CONFLICT DO NOTHING""",
                target_id, target_id, f"compound_bioactivity:{mol_id}", "undirected",
                confidence, json.dumps(metadata),
            )
            compound_edges += 1
            compounds_seen.add(mol_id)

    except Exception as e:
        errors.append(f"ChEMBL: {e}")
        logger.error("ChEMBL ingestion failed: %s", e, exc_info=True)

    duration = (datetime.now(timezone.utc) - start).total_seconds()

    await execute(
        """INSERT INTO ingestion_log (source_type, query, items_found, items_new, items_updated, errors, duration_secs)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        "chembl", "sma_bioactivities", compound_edges, compound_edges, 0,
        errors[:10] if errors else None, duration,
    )

    return {
        "source": "chembl",
        "bioactivity_edges": compound_edges,
        "unique_compounds": len(compounds_seen),
        "targets_queried": len(symbols),
        "errors": errors,
        "duration_secs": round(duration, 2),
    }


@router.post("/ingest/proteins", dependencies=[Depends(require_admin_key)])
async def trigger_protein_ingestion():
    """Pull protein annotations from UniProt for all gene targets.

    Maps each gene symbol to its UniProt accession, fetches full protein
    annotations (GO terms, pathways, function), and stores shared-pathway
    and shared-GO-process edges in graph_edges.
    """
    start = datetime.now(timezone.utc)
    errors: list[str] = []

    # Get all gene targets
    targets = await fetch("SELECT id, symbol FROM targets WHERE target_type = 'gene'")
    symbol_to_id = {t["symbol"]: str(t["id"]) for t in targets}
    symbols = list(symbol_to_id.keys())

    # Fetch protein annotations from UniProt
    protein_count = 0
    go_edges = 0
    pathway_edges = 0
    try:
        annotations = await uniprot.get_protein_annotations(gene_symbols=symbols)

        # Build lookup: gene_symbol -> {go_processes, pathways}
        gene_go: dict[str, set[str]] = {}
        gene_pathways: dict[str, set[str]] = {}

        for ann in annotations:
            symbol = ann.get("source_gene_symbol", "")
            if not symbol or symbol not in symbol_to_id:
                continue
            protein_count += 1

            # Store protein metadata on the target (update targets.metadata)
            target_id = symbol_to_id[symbol]
            protein_meta = {
                "uniprot_id": ann.get("uniprot_id", ""),
                "protein_name": ann.get("protein_name", ""),
                "function": ann.get("function", ""),
                "keywords": ann.get("keywords", []),
            }
            await execute(
                """UPDATE targets SET metadata = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2""",
                json.dumps(protein_meta), target_id,
            )

            # Collect GO biological_process terms
            go_procs = set()
            for go in ann.get("go_terms", []):
                if go.get("category") == "biological_process":
                    go_procs.add(go["id"])
            gene_go[symbol] = go_procs

            # Collect pathway IDs
            pw_ids = set()
            for pw in ann.get("pathways", []):
                pw_ids.add(pw["id"])
            gene_pathways[symbol] = pw_ids

        # Create shared-GO-process edges between genes that share GO BP terms
        sorted_symbols = sorted(gene_go.keys())
        for i, g1 in enumerate(sorted_symbols):
            for g2 in sorted_symbols[i + 1:]:
                shared = gene_go[g1] & gene_go[g2]
                if not shared:
                    continue
                src_id = symbol_to_id.get(g1)
                dst_id = symbol_to_id.get(g2)
                if not src_id or not dst_id:
                    continue

                await execute(
                    """INSERT INTO graph_edges (src_id, dst_id, relation, direction, confidence, metadata)
                       VALUES ($1, $2, $3, $4, $5, $6)
                       ON CONFLICT DO NOTHING""",
                    src_id, dst_id, "shared_go_process", "undirected",
                    min(1.0, 0.3 + 0.05 * len(shared)),
                    json.dumps({"source": "UniProt", "shared_go_terms": sorted(shared),
                                "count": len(shared)}),
                )
                go_edges += 1

        # Create shared-pathway edges between genes that share Reactome/KEGG pathways
        sorted_pw_symbols = sorted(gene_pathways.keys())
        for i, g1 in enumerate(sorted_pw_symbols):
            for g2 in sorted_pw_symbols[i + 1:]:
                shared = gene_pathways[g1] & gene_pathways[g2]
                if not shared:
                    continue
                src_id = symbol_to_id.get(g1)
                dst_id = symbol_to_id.get(g2)
                if not src_id or not dst_id:
                    continue

                await execute(
                    """INSERT INTO graph_edges (src_id, dst_id, relation, direction, confidence, metadata)
                       VALUES ($1, $2, $3, $4, $5, $6)
                       ON CONFLICT DO NOTHING""",
                    src_id, dst_id, "shared_pathway_uniprot", "undirected",
                    min(1.0, 0.4 + 0.1 * len(shared)),
                    json.dumps({"source": "UniProt", "shared_pathways": sorted(shared),
                                "count": len(shared)}),
                )
                pathway_edges += 1

    except Exception as e:
        errors.append(f"UniProt: {e}")
        logger.error("UniProt ingestion failed: %s", e, exc_info=True)

    duration = (datetime.now(timezone.utc) - start).total_seconds()

    await execute(
        """INSERT INTO ingestion_log (source_type, query, items_found, items_new, items_updated, errors, duration_secs)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        "uniprot", "protein_annotations", protein_count, go_edges + pathway_edges, 0,
        errors[:10] if errors else None, duration,
    )

    return {
        "source": "uniprot",
        "proteins_resolved": protein_count,
        "go_process_edges": go_edges,
        "pathway_edges": pathway_edges,
        "targets_queried": len(symbols),
        "errors": errors,
        "duration_secs": round(duration, 2),
    }


@router.post("/ingest/fulltext", dependencies=[Depends(require_admin_key)])
async def trigger_fulltext_fetching(batch_size: int = Query(default=50, ge=1, le=200)):
    """Fetch full-text papers from PubMed Central OA for sources that only have abstracts.

    Sources: Europe PMC → NCBI PMC → Unpaywall (in order of preference).
    """
    start = datetime.now(timezone.utc)
    result = await pmc.fetch_all_fulltext(batch_size=batch_size)
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration_secs"] = round(duration, 2)

    await execute(
        """INSERT INTO ingestion_log (source_type, query, items_found, items_new, items_updated, errors, duration_secs)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        "pmc_fulltext", "fetch_all_fulltext", result["checked"], result["fetched"], 0,
        None, duration,
    )

    return result


@router.post("/extract/drug-outcomes", dependencies=[Depends(require_admin_key)])
async def trigger_drug_outcome_extraction(batch_size: int = Query(default=100, ge=1, le=500)):
    """Extract structured drug failure/success outcomes from SMA literature.

    Builds the Drug Failure & Success Database — captures why drugs succeeded or
    failed, with structured failure reasons (toxicity, efficacy, bioavailability, etc.).
    """
    start = datetime.now(timezone.utc)
    result = await process_all_drug_outcomes(batch_size=batch_size)
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration_secs"] = round(duration, 2)
    return result


@router.get("/drug-outcomes")
async def list_drug_outcomes(
    outcome: str | None = None,
    compound: str | None = None,
    limit: int = 200,
):
    """List drug outcomes with optional filtering."""
    if outcome and compound:
        rows = await fetch(
            """SELECT dout.*, s.title as source_title, s.external_id as pmid
               FROM drug_outcomes dout
               LEFT JOIN sources s ON dout.source_id = s.id
               WHERE dout.outcome = $1 AND LOWER(dout.compound_name) LIKE $2
               ORDER BY dout.confidence DESC LIMIT $3""",
            outcome, f"%{compound.lower()}%", limit,
        )
    elif outcome:
        rows = await fetch(
            """SELECT dout.*, s.title as source_title, s.external_id as pmid
               FROM drug_outcomes dout
               LEFT JOIN sources s ON dout.source_id = s.id
               WHERE dout.outcome = $1
               ORDER BY dout.confidence DESC LIMIT $2""",
            outcome, limit,
        )
    elif compound:
        rows = await fetch(
            """SELECT dout.*, s.title as source_title, s.external_id as pmid
               FROM drug_outcomes dout
               LEFT JOIN sources s ON dout.source_id = s.id
               WHERE LOWER(dout.compound_name) LIKE $1
               ORDER BY dout.confidence DESC LIMIT $2""",
            f"%{compound.lower()}%", limit,
        )
    else:
        rows = await fetch(
            """SELECT dout.*, s.title as source_title, s.external_id as pmid
               FROM drug_outcomes dout
               LEFT JOIN sources s ON dout.source_id = s.id
               ORDER BY dout.confidence DESC LIMIT $1""",
            limit,
        )
    return [dict(r) for r in rows]


@router.get("/drug-outcomes/summary")
async def drug_outcomes_summary():
    """Get summary statistics for the Drug Failure & Success Database."""
    total = await fetchrow("SELECT COUNT(*) as count FROM drug_outcomes")
    by_outcome = await fetch(
        "SELECT outcome, COUNT(*) as count FROM drug_outcomes GROUP BY outcome ORDER BY count DESC"
    )
    by_compound = await fetch(
        """SELECT compound_name, COUNT(*) as count,
                  COUNT(DISTINCT outcome) as distinct_outcomes
           FROM drug_outcomes GROUP BY compound_name ORDER BY count DESC LIMIT 20"""
    )
    by_failure = await fetch(
        """SELECT failure_reason, COUNT(*) as count FROM drug_outcomes
           WHERE failure_reason IS NOT NULL
           GROUP BY failure_reason ORDER BY count DESC"""
    )

    return {
        "total_outcomes": dict(total)["count"] if total else 0,
        "by_outcome": [dict(r) for r in by_outcome],
        "top_compounds": [dict(r) for r in by_compound],
        "failure_reasons": [dict(r) for r in by_failure],
    }


@router.post("/expand/graph", dependencies=[Depends(require_admin_key)])
async def trigger_graph_expansion():
    """Auto-expand the knowledge graph from claims, drug outcomes, and conservation data."""
    start = datetime.now(timezone.utc)
    result = await expand_graph()
    duration = (datetime.now(timezone.utc) - start).total_seconds()
    result["duration_secs"] = round(duration, 2)
    return result


