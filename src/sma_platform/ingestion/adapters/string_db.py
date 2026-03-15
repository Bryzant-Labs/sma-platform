"""STRING database adapter — protein-protein interaction network data."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

STRING_API = "https://string-db.org/api"
SPECIES = 9606  # Homo sapiens

# Our 7 gene targets
SMA_GENES = ["SMN1", "SMN2", "STMN2", "PLS3", "NCALD", "UBA1", "CORO1C"]


async def fetch_interactions(
    genes: list[str] | None = None,
    required_score: int = 400,
) -> list[dict]:
    """Fetch protein-protein interactions from STRING for given genes.

    Args:
        genes: Gene symbols (defaults to SMA_GENES)
        required_score: Minimum combined score (0-1000, default 400 = medium)

    Returns:
        List of interaction dicts with source, target, score, etc.
    """
    genes = genes or SMA_GENES
    identifiers = "%0d".join(genes)

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{STRING_API}/json/network",
            params={
                "identifiers": identifiers,
                "species": SPECIES,
                "required_score": required_score,
                "caller_identity": "sma-research-platform",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    interactions = []
    for item in data:
        interactions.append({
            "source": item.get("preferredName_A", item.get("stringId_A", "")),
            "target": item.get("preferredName_B", item.get("stringId_B", "")),
            "combined_score": item.get("score", 0),
            "nscore": item.get("nscore", 0),
            "fscore": item.get("fscore", 0),
            "pscore": item.get("pscore", 0),
            "ascore": item.get("ascore", 0),
            "escore": item.get("escore", 0),
            "dscore": item.get("dscore", 0),
            "tscore": item.get("tscore", 0),
        })

    logger.info("STRING: fetched %d interactions for %d genes", len(interactions), len(genes))
    return interactions


async def fetch_enrichment(genes: list[str] | None = None) -> list[dict]:
    """Fetch functional enrichment from STRING (GO, KEGG, Reactome)."""
    genes = genes or SMA_GENES
    identifiers = "%0d".join(genes)

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{STRING_API}/json/enrichment",
            params={
                "identifiers": identifiers,
                "species": SPECIES,
                "caller_identity": "sma-research-platform",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    enrichments = []
    for item in data:
        enrichments.append({
            "category": item.get("category", ""),
            "term": item.get("term", ""),
            "description": item.get("description", ""),
            "p_value": item.get("p_value", 1.0),
            "fdr": item.get("fdr", 1.0),
            "genes_in_term": item.get("number_of_genes", 0),
            "input_genes": item.get("inputGenes", ""),
        })

    logger.info("STRING: fetched %d enrichment terms", len(enrichments))
    return enrichments
