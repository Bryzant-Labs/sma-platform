"""UniProt adapter — protein annotations and gene mapping for SMA targets.

Queries the UniProt REST API for protein metadata, GO terms, pathways,
and gene-to-UniProt ID mapping.
API docs: https://www.uniprot.org/help/api
No API key required.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://rest.uniprot.org"


def _parse_protein_name(entry: dict) -> str:
    """Extract the recommended protein name from a UniProt entry."""
    desc = entry.get("proteinDescription", {})
    rec = desc.get("recommendedName", {})
    full_name = rec.get("fullName", {})
    if isinstance(full_name, dict):
        return full_name.get("value", "")
    # Sometimes it's a list
    if isinstance(full_name, list) and full_name:
        return full_name[0].get("value", "")
    # Fall back to submittedName
    sub_names = desc.get("submissionNames", [])
    if sub_names:
        return sub_names[0].get("fullName", {}).get("value", "")
    return ""


def _parse_gene_name(entry: dict) -> str:
    """Extract the primary gene name from a UniProt entry."""
    genes = entry.get("genes", [])
    if genes:
        gene_name = genes[0].get("geneName", {})
        if isinstance(gene_name, dict):
            return gene_name.get("value", "")
    return ""


def _parse_organism(entry: dict) -> str:
    """Extract organism scientific name."""
    org = entry.get("organism", {})
    return org.get("scientificName", "")


def _parse_function(entry: dict) -> str:
    """Extract function annotation from comments."""
    comments = entry.get("comments", [])
    for comment in comments:
        if comment.get("commentType") == "FUNCTION":
            texts = comment.get("texts", [])
            if texts:
                return texts[0].get("value", "")
    return ""


def _parse_go_terms(entry: dict) -> list[dict[str, str]]:
    """Extract GO terms from cross-references."""
    go_terms = []
    for xref in entry.get("uniProtKBCrossReferences", []):
        if xref.get("database") == "GO":
            go_id = xref.get("id", "")
            # Properties contain the GO term name and category
            props = {p.get("key", ""): p.get("value", "") for p in xref.get("properties", [])}
            term_value = props.get("GoTerm", "")
            # GoTerm format: "C:cytoplasm" or "F:RNA binding" or "P:mRNA splicing"
            category = ""
            name = term_value
            if ":" in term_value:
                cat_code, name = term_value.split(":", 1)
                category_map = {"C": "cellular_component", "F": "molecular_function", "P": "biological_process"}
                category = category_map.get(cat_code, cat_code)
            go_terms.append({
                "id": go_id,
                "name": name.strip(),
                "category": category,
            })
    return go_terms


def _parse_pathways(entry: dict) -> list[dict[str, str]]:
    """Extract pathway references from cross-references (Reactome, KEGG)."""
    pathways = []
    for xref in entry.get("uniProtKBCrossReferences", []):
        db = xref.get("database", "")
        if db in ("Reactome", "KEGG", "UniPathway"):
            props = {p.get("key", ""): p.get("value", "") for p in xref.get("properties", [])}
            pathways.append({
                "database": db,
                "id": xref.get("id", ""),
                "name": props.get("PathwayName", ""),
            })
    return pathways


def _parse_keywords(entry: dict) -> list[str]:
    """Extract keyword annotations."""
    return [kw.get("name", "") for kw in entry.get("keywords", []) if kw.get("name")]


async def get_protein(uniprot_id: str) -> dict[str, Any]:
    """Get full protein annotation from UniProt.

    Args:
        uniprot_id: UniProt accession (e.g. "Q16637" for SMN1)

    Returns:
        Dict with uniprot_id, protein_name, gene_name, organism, function,
        go_terms, pathways, keywords.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(
                f"{BASE_URL}/uniprotkb/{uniprot_id}.json",
                headers={"Accept": "application/json"},
            )
            if resp.status_code == 404:
                logger.warning("UniProt protein %s not found", uniprot_id)
                return {"uniprot_id": uniprot_id, "error": "not_found"}
            resp.raise_for_status()
            entry = resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning("UniProt protein %s failed: %s", uniprot_id, e)
            return {"uniprot_id": uniprot_id, "error": str(e)}
        except httpx.TimeoutException:
            logger.warning("UniProt protein %s timed out", uniprot_id)
            return {"uniprot_id": uniprot_id, "error": "timeout"}

    result = {
        "uniprot_id": entry.get("primaryAccession", uniprot_id),
        "protein_name": _parse_protein_name(entry),
        "gene_name": _parse_gene_name(entry),
        "organism": _parse_organism(entry),
        "function": _parse_function(entry),
        "go_terms": _parse_go_terms(entry),
        "pathways": _parse_pathways(entry),
        "keywords": _parse_keywords(entry),
    }

    logger.info(
        "UniProt %s: %s (%s), %d GO terms, %d pathways",
        uniprot_id, result["protein_name"], result["gene_name"],
        len(result["go_terms"]), len(result["pathways"]),
    )
    return result


async def search_proteins(
    query: str,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Search UniProt for proteins matching a query.

    Args:
        query: Search query (e.g. "spinal muscular atrophy", "SMN1")
        limit: Maximum results to return

    Returns:
        List of dicts with uniprot_id, protein_name, gene_name, organism.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(
                f"{BASE_URL}/uniprotkb/search",
                params={
                    "query": query,
                    "format": "json",
                    "size": limit,
                },
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning("UniProt search '%s' failed: %s", query, e)
            return []
        except httpx.TimeoutException:
            logger.warning("UniProt search '%s' timed out", query)
            return []

    results = []
    for entry in data.get("results", []):
        results.append({
            "uniprot_id": entry.get("primaryAccession", ""),
            "protein_name": _parse_protein_name(entry),
            "gene_name": _parse_gene_name(entry),
            "organism": _parse_organism(entry),
        })

    logger.info("UniProt search '%s': %d results", query, len(results))
    return results


async def map_gene_to_uniprot(
    gene_symbol: str,
    organism_id: str = "9606",
) -> str | None:
    """Map a gene symbol to its reviewed UniProt accession (Swiss-Prot).

    Args:
        gene_symbol: Gene symbol (e.g. "SMN1", "PLS3")
        organism_id: NCBI taxonomy ID (default "9606" for Homo sapiens)

    Returns:
        UniProt primary accession string, or None if not found.
    """
    query = f"(gene_exact:{gene_symbol}) AND (organism_id:{organism_id}) AND (reviewed:true)"

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(
                f"{BASE_URL}/uniprotkb/search",
                params={
                    "query": query,
                    "format": "json",
                    "size": 1,
                },
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning("UniProt gene mapping '%s' failed: %s", gene_symbol, e)
            return None
        except httpx.TimeoutException:
            logger.warning("UniProt gene mapping '%s' timed out", gene_symbol)
            return None

    results = data.get("results", [])
    if not results:
        logger.info("UniProt gene mapping '%s': no reviewed entry found", gene_symbol)
        return None

    accession = results[0].get("primaryAccession")
    logger.info("UniProt gene mapping '%s' -> %s", gene_symbol, accession)
    return accession


async def get_protein_annotations(
    gene_symbols: list[str],
) -> list[dict[str, Any]]:
    """Get full protein annotations for a list of gene symbols.

    For each symbol, maps to UniProt ID then fetches full annotation.

    Args:
        gene_symbols: List of gene symbols (e.g. ["SMN1", "SMN2", "PLS3"])

    Returns:
        List of full protein annotation dicts (one per successfully resolved gene).
    """
    annotations: list[dict[str, Any]] = []

    for symbol in gene_symbols:
        uniprot_id = await map_gene_to_uniprot(symbol)
        if not uniprot_id:
            logger.info("Skipping %s: no UniProt ID found", symbol)
            continue

        protein = await get_protein(uniprot_id)
        if protein.get("error"):
            logger.warning("Skipping %s (%s): %s", symbol, uniprot_id, protein["error"])
            continue

        protein["source_gene_symbol"] = symbol
        annotations.append(protein)

        # Be polite to the API
        await asyncio.sleep(0.2)

    logger.info(
        "UniProt annotations: resolved %d/%d gene symbols",
        len(annotations), len(gene_symbols),
    )
    return annotations
