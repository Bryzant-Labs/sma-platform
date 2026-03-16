"""Nanopore / RNA-seq omics API routes.

Exposes endpoints for searching, cataloging, and recommending public
Nanopore direct RNA and standard RNA-seq datasets relevant to SMA.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from ...ingestion.adapters.nanopore_rnaseq import (
    catalog_available_datasets,
    get_dataset_recommendations,
    search_sra_datasets,
)

router = APIRouter()


@router.get("/omics/nanopore/search")
async def nanopore_search(
    query: str = Query(
        default="SMA SMN2 nanopore direct RNA",
        description="Search term for NCBI SRA Nanopore / RNA-seq datasets",
    ),
    max_results: int = Query(default=50, ge=1, le=200),
):
    """Search NCBI SRA for Nanopore RNA-seq datasets matching the query."""
    datasets = await search_sra_datasets(query=query, max_results=max_results)
    return {
        "query": query,
        "count": len(datasets),
        "datasets": datasets,
    }


@router.get("/omics/nanopore/catalog")
async def nanopore_catalog():
    """Full catalog of publicly available SMA-relevant RNA-seq data.

    Searches both NCBI SRA and ENA, deduplicates, and groups results
    into categories: direct_rna, cdna_rnaseq, motor_neuron_specific,
    sma_patient_derived, smn2_splicing_focused.
    """
    return await catalog_available_datasets()


@router.get("/omics/nanopore/recommendations")
async def nanopore_recommendations():
    """Recommend which public datasets to download and analyse next.

    Prioritises: SMA patient motor neuron RNA-seq > SMA mouse model >
    general motor neuron > iPSC-MN.  Each recommendation includes a
    rationale explaining why it is valuable for the platform.
    """
    recs = await get_dataset_recommendations()
    return {
        "count": len(recs),
        "recommendations": recs,
    }
