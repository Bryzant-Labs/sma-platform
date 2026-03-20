"""Omics dataset endpoints.

Provides database-backed dataset CRUD plus a curated RNA-seq data catalog
of publicly available SMA-relevant datasets (Nanopore, Illumina, 10x, etc.).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from ...core.database import fetch, fetchrow
from ...ingestion.adapters.nanopore_rnaseq import (
    get_curated_nanopore_datasets,
    get_curated_rnaseq_datasets,
)

router = APIRouter()

MAX_LIMIT = 2000


# ---------------------------------------------------------------------------
# Curated RNA-seq Data Catalog (static / hand-curated)
# ---------------------------------------------------------------------------
# These MUST be registered before /datasets/{dataset_id} so that FastAPI
# matches the literal path segments before the UUID path parameter.


@router.get("/datasets/rnaseq")
async def list_rnaseq_datasets(
    platform: str | None = Query(
        default=None,
        description=(
            "Filter by sequencing platform (case-insensitive substring). "
            "Examples: nanopore, illumina, 10x, SMART-seq2, Visium."
        ),
    ),
    organism: str | None = Query(
        default=None,
        description=(
            "Filter by organism (case-insensitive substring). "
            "Examples: Homo sapiens, Mus musculus."
        ),
    ),
    tag: str | None = Query(
        default=None,
        description=(
            "Filter by tag (exact match). "
            "Examples: nanopore, single_cell, treatment_response, "
            "spatial, motor_neuron, mouse_model, direct_rna."
        ),
    ),
):
    """List curated RNA-seq datasets relevant to SMA research.

    Returns a hand-curated catalog of publicly available RNA-seq datasets
    spanning multiple platforms (Nanopore direct RNA, Illumina short-read,
    10x Genomics single-cell, SMART-seq2, 10x Visium spatial) and tissues
    (motor neurons, spinal cord, fibroblasts, CSF/blood).

    Each entry includes accession, platform, organism, tissue, SMA type,
    sample count, experimental condition, scientific relevance, and a
    direct URL to the repository.
    """
    datasets = get_curated_rnaseq_datasets(
        platform=platform,
        organism=organism,
        tag=tag,
    )
    return {
        "count": len(datasets),
        "filters_applied": {
            k: v
            for k, v in {"platform": platform, "organism": organism, "tag": tag}.items()
            if v is not None
        },
        "datasets": datasets,
    }


@router.get("/datasets/rnaseq/nanopore")
async def list_nanopore_datasets():
    """List Nanopore direct RNA sequencing datasets for SMA.

    Returns entries from the curated catalog that use Oxford Nanopore
    technology.  These datasets are especially valuable because direct
    RNA sequencing preserves native RNA modifications and captures
    full-length transcript isoforms without reverse-transcription bias.
    """
    datasets = get_curated_nanopore_datasets()
    return {
        "count": len(datasets),
        "note": (
            "Nanopore direct RNA datasets are prioritised because they "
            "reveal SMN2 splicing complexity (exon 7 inclusion/skipping, "
            "cryptic exons, polyA tail lengths) not visible in short-read data."
        ),
        "datasets": datasets,
    }


# ---------------------------------------------------------------------------
# Database-backed dataset endpoints
# ---------------------------------------------------------------------------


@router.get("/datasets")
async def list_datasets(
    evidence_tier: str | None = None,
    modality: str | None = None,
    organism: str | None = None,
    limit: int = Query(default=100, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    conditions = []
    params = []
    idx = 1

    if evidence_tier:
        conditions.append(f"evidence_tier = ${idx}")
        params.append(evidence_tier)
        idx += 1
    if modality:
        conditions.append(f"modality = ${idx}")
        params.append(modality)
        idx += 1
    if organism:
        conditions.append(f"organism = ${idx}")
        params.append(organism)
        idx += 1

    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    params.extend([limit, offset])

    rows = await fetch(
        f"SELECT * FROM datasets{where} ORDER BY evidence_tier, accession LIMIT ${idx} OFFSET ${idx + 1}",
        *params,
    )
    return [dict(r) for r in rows]


@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: UUID):
    row = await fetchrow("SELECT * FROM datasets WHERE id = $1", dataset_id)
    if not row:
        raise HTTPException(404, "Dataset not found")
    return dict(row)


@router.get("/datasets/accession/{accession}")
async def get_dataset_by_accession(accession: str):
    row = await fetchrow("SELECT * FROM datasets WHERE accession = $1", accession.upper())
    if not row:
        raise HTTPException(404, f"Dataset '{accession}' not found")
    return dict(row)
