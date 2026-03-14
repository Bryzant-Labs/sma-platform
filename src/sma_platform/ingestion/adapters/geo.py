"""GEO (Gene Expression Omnibus) adapter.

Fetches dataset metadata for SMA-related omics datasets.
Uses NCBI E-utilities (same as PubMed, different database).
"""

from __future__ import annotations

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


async def search_geo(
    query: str = "spinal muscular atrophy",
    max_results: int = 50,
) -> list[str]:
    """Search GEO for dataset accessions matching query."""
    handle = Entrez.esearch(db="gds", term=query, retmax=max_results)
    record = Entrez.read(handle)
    handle.close()

    ids = record.get("IdList", [])
    logger.info(f"GEO search '{query}' returned {len(ids)} dataset IDs")
    return ids


async def fetch_dataset_metadata(accession: str) -> dict[str, Any] | None:
    """Fetch metadata for a specific GEO accession (e.g., GSE69175)."""
    try:
        handle = Entrez.esearch(db="gds", term=f"{accession}[Accession]", retmax=1)
        record = Entrez.read(handle)
        handle.close()

        ids = record.get("IdList", [])
        if not ids:
            logger.warning(f"No GEO record found for {accession}")
            return None

        handle = Entrez.esummary(db="gds", id=ids[0])
        summary = Entrez.read(handle)
        handle.close()

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
        logger.error(f"Failed to fetch GEO metadata for {accession}: {e}")
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
