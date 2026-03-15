"""KEGG pathway adapter — disease pathway and gene mapping."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

KEGG_API = "https://rest.kegg.jp"
SMA_PATHWAY = "hsa05033"


async def fetch_pathway_genes(pathway_id: str = SMA_PATHWAY) -> list[dict]:
    """Fetch genes in a KEGG pathway using the conv endpoint for symbol mapping.

    Returns list of dicts with gene_id and symbol.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        # Step 1: Get gene IDs in pathway
        resp = await client.get(f"{KEGG_API}/link/hsa/{pathway_id}")
        resp.raise_for_status()

    gene_ids = []
    for line in resp.text.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            gene_ids.append(parts[1].strip())  # e.g., "hsa:6606"

    if not gene_ids:
        logger.warning("KEGG: no genes found for pathway %s", pathway_id)
        return []

    # Step 2: Convert KEGG gene IDs to NCBI gene symbols via /conv
    # Use /list to get names (more reliable)
    genes = []
    for i in range(0, len(gene_ids), 10):
        batch = gene_ids[i:i + 10]
        batch_str = "+".join(batch)
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{KEGG_API}/list/{batch_str}")
            if resp.status_code != 200:
                continue

        for line in resp.text.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                gene_id = parts[0].strip()
                # Name format: "SMN1, BCD541, SMA; survival of motor neuron 1"
                name_part = parts[1].strip()
                # First symbol before comma or semicolon
                symbol = name_part.split(",")[0].split(";")[0].strip()
                genes.append({
                    "gene_id": gene_id,
                    "symbol": symbol,
                    "description": name_part,
                })

    logger.info("KEGG: fetched %d genes from pathway %s", len(genes), pathway_id)
    return genes
