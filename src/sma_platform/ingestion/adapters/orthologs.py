"""Ortholog adapter — cross-species gene ortholog mapping via NCBI.

Queries the NCBI Datasets API to find orthologous genes across model organisms
relevant to SMA cross-species comparative biology.

Strategy: For each human gene symbol, search each target species directly
using the NCBI Gene API. Gene symbols vary across species (e.g., SMN1 in
human = smn1 in zebrafish = Smn in Drosophila = smn-1 in C. elegans).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

NCBI_API = "https://api.ncbi.nlm.nih.gov/datasets/v2"

MODEL_ORGANISMS = {
    "9606": "Homo sapiens",
    "8296": "Ambystoma mexicanum",
    "7955": "Danio rerio",
    "10181": "Heterocephalus glaber",
    "6239": "Caenorhabditis elegans",
    "7227": "Drosophila melanogaster",
}

# Default species to search (excluding human)
DEFAULT_SPECIES = ["8296", "7955", "10181", "6239", "7227"]


async def _search_gene_in_species(
    client: httpx.AsyncClient,
    gene_symbol: str,
    taxon_id: str,
) -> dict[str, Any] | None:
    """Search for a gene symbol in a specific species.

    Tries the exact symbol first, then common case variants.
    Returns the first match or None.
    """
    # Try variants: exact, lowercase, capitalized (Drosophila convention)
    variants = [gene_symbol, gene_symbol.lower(), gene_symbol.capitalize()]
    # Add special C. elegans convention (lowercase with dash)
    if gene_symbol.upper() != gene_symbol.lower():
        variants.append(gene_symbol.lower().replace("_", "-"))

    for variant in variants:
        try:
            resp = await client.get(
                f"{NCBI_API}/gene/symbol/{variant}/taxon/{taxon_id}",
                headers={"Accept": "application/json"},
            )
            if resp.status_code != 200:
                continue
            data = resp.json()
            reports = data.get("reports", [])
            if reports:
                gene = reports[0].get("gene", {})
                return {
                    "species_name": gene.get("taxname", MODEL_ORGANISMS.get(taxon_id, "Unknown")),
                    "species_taxon_id": taxon_id,
                    "ortholog_symbol": gene.get("symbol", variant),
                    "ortholog_gene_id": str(gene.get("gene_id", "")),
                    "gene_name": gene.get("description", ""),
                }
        except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.RequestError, ValueError) as exc:
            logger.debug("Ortholog lookup %s/%s variant=%s: %s", gene_symbol, taxon_id, variant, exc)
            continue

    return None


async def find_orthologs(
    gene_symbol: str,
    species_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Find orthologous genes across species via NCBI Datasets API.

    Searches each target species individually for the gene symbol,
    trying multiple naming conventions per species.

    Args:
        gene_symbol: Human gene symbol (e.g. "SMN1", "PLS3")
        species_ids: NCBI taxonomy IDs to search (defaults to DEFAULT_SPECIES)

    Returns:
        List of ortholog dicts with species_name, species_taxon_id,
        ortholog_symbol, ortholog_gene_id, gene_name.
    """
    species_ids = species_ids or DEFAULT_SPECIES
    orthologs: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=30) as client:
        for taxon_id in species_ids:
            result = await _search_gene_in_species(client, gene_symbol, taxon_id)
            if result:
                orthologs.append(result)
            # Rate limit
            await asyncio.sleep(0.2)

    logger.info(
        "NCBI orthologs for %s: %d found across %d species",
        gene_symbol, len(orthologs), len(set(o["species_taxon_id"] for o in orthologs)),
    )
    return orthologs


async def get_ortholog_conservation(human_gene: str) -> dict[str, Any]:
    """Get conservation score and ortholog presence across model organisms.

    Args:
        human_gene: Human gene symbol

    Returns:
        Dict with gene_symbol, orthologs list, total_species_with_ortholog,
        conservation_breadth (0-1 based on fraction of model organisms with ortholog).
    """
    orthologs = await find_orthologs(human_gene)

    species_found = set(o["species_taxon_id"] for o in orthologs)
    total_model_organisms = len(DEFAULT_SPECIES)
    breadth = len(species_found) / total_model_organisms if total_model_organisms > 0 else 0.0

    return {
        "gene_symbol": human_gene,
        "orthologs": orthologs,
        "total_species_with_ortholog": len(species_found),
        "total_model_organisms": total_model_organisms,
        "conservation_breadth": round(breadth, 2),
        "species_with_ortholog": [
            MODEL_ORGANISMS.get(sid, sid) for sid in sorted(species_found)
        ],
        "species_without_ortholog": [
            MODEL_ORGANISMS.get(sid, sid)
            for sid in DEFAULT_SPECIES
            if sid not in species_found
        ],
    }


async def batch_ortholog_search(
    gene_symbols: list[str],
) -> list[dict[str, Any]]:
    """Run ortholog conservation analysis for multiple genes.

    Args:
        gene_symbols: List of human gene symbols

    Returns:
        List of conservation result dicts, sorted by conservation_breadth descending.
    """
    results: list[dict[str, Any]] = []

    for symbol in gene_symbols:
        result = await get_ortholog_conservation(symbol)
        results.append(result)
        # Be polite to the API
        await asyncio.sleep(0.3)

    # Sort by conservation breadth (most conserved first)
    results.sort(key=lambda r: r["conservation_breadth"], reverse=True)

    logger.info(
        "Ortholog batch search: %d/%d genes have orthologs in at least one species",
        sum(1 for r in results if r["total_species_with_ortholog"] > 0),
        len(gene_symbols),
    )
    return results
