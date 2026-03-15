"""GEO (Gene Expression Omnibus) adapter.

Fetches dataset metadata for SMA-related omics datasets.
Uses NCBI E-utilities (same as PubMed, different database).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from Bio import Entrez

from ...core.config import settings

logger = logging.getLogger(__name__)

Entrez.email = settings.ncbi_email
Entrez.tool = settings.ncbi_tool
if settings.ncbi_api_key:
    Entrez.api_key = settings.ncbi_api_key

# Known SMA datasets from the data inventory
KNOWN_DATASETS = [
    {"accession": "GSE69175", "tier": "tier1", "modality": "rna-seq", "tissue": "motor neurons"},
    {"accession": "GSE108094", "tier": "tier1", "modality": "rna-seq", "tissue": "motor neurons"},
    {"accession": "GSE208629", "tier": "tier1", "modality": "scrna-seq", "tissue": "spinal cord"},
    {"accession": "GSE87281", "tier": "tier2", "modality": "rna-seq", "tissue": "spinal cord"},
    {"accession": "GSE65470", "tier": "tier3", "modality": "transcriptomics", "tissue": "nmj"},
]


async def _geo_search(query: str, max_results: int) -> list[str]:
    """Run GEO Entrez search in a thread to avoid blocking the event loop."""
    def _search() -> list[str]:
        handle = Entrez.esearch(db="gds", term=query, retmax=max_results)
        record = Entrez.read(handle)
        handle.close()
        return record.get("IdList", [])

    return await asyncio.to_thread(_search)


async def _geo_summary(geo_id: str) -> list:
    """Run GEO Entrez esummary in a thread to avoid blocking the event loop."""
    def _summarise() -> list:
        handle = Entrez.esummary(db="gds", id=geo_id)
        summary = Entrez.read(handle)
        handle.close()
        return summary

    return await asyncio.to_thread(_summarise)


async def search_geo(
    query: str = "spinal muscular atrophy",
    max_results: int = 50,
) -> list[str]:
    """Search GEO for dataset accessions matching query."""
    ids = await _geo_search(query, max_results)
    logger.info("GEO search '%s' returned %d dataset IDs", query, len(ids))
    return ids


async def fetch_dataset_metadata(accession: str) -> dict[str, Any] | None:
    """Fetch metadata for a specific GEO accession (e.g., GSE69175)."""
    try:
        ids = await _geo_search(f"{accession}[Accession]", max_results=1)
        if not ids:
            logger.warning("No GEO record found for %s", accession)
            return None

        summary = await _geo_summary(ids[0])
        if not summary:
            return None

        doc = summary[0]
        return {
            "accession": accession,
            "title": doc.get("title", ""),
            "summary": doc.get("summary", ""),
            "organism": doc.get("taxon", ""),
            "platform": doc.get("GPL", ""),
            "sample_count": doc.get("n_samples", 0),
            "series_type": doc.get("gdsType", ""),
            "pub_date": doc.get("PDAT", ""),
            "url": f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}",
        }
    except Exception as e:
        logger.error("Failed to fetch GEO metadata for %s: %s", accession, e)
        return None


async def fetch_known_datasets() -> list[dict[str, Any]]:
    """Fetch metadata for all known SMA datasets from the data inventory."""
    results = []
    for ds in KNOWN_DATASETS:
        meta = await fetch_dataset_metadata(ds["accession"])
        if meta:
            meta["evidence_tier"] = ds["tier"]
            meta["modality"] = ds["modality"]
            meta["tissue"] = ds["tissue"]
            results.append(meta)
    return results
