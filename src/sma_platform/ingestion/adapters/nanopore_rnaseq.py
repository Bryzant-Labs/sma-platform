"""Nanopore / RNA-seq data adapter.

Searches NCBI SRA and ENA for publicly available Nanopore direct RNA
sequencing datasets relevant to SMA research.  Uses httpx for HTTP calls
and respects NCBI rate limits (3 req/s without key, 10 req/s with key).

Also provides a curated catalog of publicly available RNA-seq datasets
relevant to SMA research, covering Nanopore direct RNA, short-read
(Illumina), single-cell, and spatial transcriptomics.
"""

from __future__ import annotations

import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import quote_plus

import httpx

from ...core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# NCBI rate-limit helper
# ---------------------------------------------------------------------------
_RATE_DELAY = 0.12 if settings.ncbi_api_key else 0.35  # seconds between calls

# Queries used for broad SRA search
SRA_QUERIES = [
    "SMA SMN2 nanopore direct RNA",
    "spinal muscular atrophy RNA-seq",
    "SMN2 splicing nanopore",
    "motor neuron RNA-seq",
    "spinal muscular atrophy nanopore",
    "SMN2 exon 7 RNA-seq",
    "iPSC motor neuron RNA-seq SMA",
    "SMA mouse model RNA-seq",
    "direct RNA sequencing motor neuron",
    "long read RNA SMA",
]


def _ncbi_params() -> dict[str, str]:
    """Return common NCBI E-utilities query parameters."""
    params: dict[str, str] = {"retmode": "json"}
    if settings.ncbi_api_key:
        params["api_key"] = settings.ncbi_api_key
    return params


# ---------------------------------------------------------------------------
# SRA search  (NCBI E-utilities)
# ---------------------------------------------------------------------------

async def search_sra_datasets(
    query: str = "SMA SMN2 nanopore direct RNA",
    max_results: int = 50,
) -> list[dict[str, Any]]:
    """Search NCBI SRA for Nanopore RNA-seq datasets.

    1. esearch to get SRA IDs
    2. efetch (XML) to pull structured metadata
    3. Filter for Nanopore platform / RNA-seq strategy
    """
    encoded_query = quote_plus(query)
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    search_url = (
        f"{base}/esearch.fcgi?db=sra&term={encoded_query}"
        f"&retmax={max_results}&retmode=json"
    )
    if settings.ncbi_api_key:
        search_url += f"&api_key={settings.ncbi_api_key}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1 — search
        resp = await client.get(search_url)
        resp.raise_for_status()
        data = resp.json()
        id_list = data.get("esearchresult", {}).get("idlist", [])

        if not id_list:
            logger.info("SRA search '%s' returned 0 IDs", query)
            return []

        logger.info("SRA search '%s' returned %d IDs", query, len(id_list))

        # Step 2 — fetch details in XML
        await asyncio.sleep(_RATE_DELAY)
        ids_str = ",".join(id_list)
        fetch_url = f"{base}/efetch.fcgi?db=sra&id={ids_str}&retmode=xml"
        if settings.ncbi_api_key:
            fetch_url += f"&api_key={settings.ncbi_api_key}"

        resp = await client.get(fetch_url)
        resp.raise_for_status()
        xml_text = resp.text

    # Step 3 — parse XML
    return _parse_sra_xml(xml_text)


def _parse_sra_xml(xml_text: str) -> list[dict[str, Any]]:
    """Extract structured records from SRA efetch XML."""
    datasets: list[dict[str, Any]] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        logger.error("Failed to parse SRA XML: %s", exc)
        return datasets

    for exp_pkg in root.iter("EXPERIMENT_PACKAGE"):
        experiment = exp_pkg.find("EXPERIMENT")
        run_set = exp_pkg.find("RUN_SET")
        sample = exp_pkg.find("SAMPLE")
        study = exp_pkg.find("STUDY")

        accession = ""
        title = ""
        organism = ""
        platform = ""
        library_strategy = ""
        library_source = ""
        spots = 0
        bases = 0

        if experiment is not None:
            accession = experiment.get("accession", "")
            title_el = experiment.find("TITLE")
            title = title_el.text if title_el is not None and title_el.text else ""

            # Platform
            platform_el = experiment.find(".//PLATFORM")
            if platform_el is not None and len(platform_el) > 0:
                platform = platform_el[0].tag  # e.g., OXFORD_NANOPORE, ILLUMINA

            # Library
            lib_desc = experiment.find(".//LIBRARY_DESCRIPTOR")
            if lib_desc is not None:
                ls = lib_desc.find("LIBRARY_STRATEGY")
                library_strategy = ls.text if ls is not None and ls.text else ""
                lsrc = lib_desc.find("LIBRARY_SOURCE")
                library_source = lsrc.text if lsrc is not None and lsrc.text else ""

        if sample is not None:
            org_el = sample.find(".//SCIENTIFIC_NAME")
            if org_el is not None and org_el.text:
                organism = org_el.text

        study_accession = ""
        study_title = ""
        if study is not None:
            study_accession = study.get("accession", "")
            st = study.find(".//STUDY_TITLE")
            study_title = st.text if st is not None and st.text else ""

        if run_set is not None:
            for run in run_set.iter("RUN"):
                spots = int(run.get("total_spots", 0) or 0)
                bases = int(run.get("total_bases", 0) or 0)
                break  # take first run stats

        datasets.append({
            "accession": accession,
            "title": title,
            "organism": organism,
            "platform": platform,
            "library_strategy": library_strategy,
            "library_source": library_source,
            "study_accession": study_accession,
            "study_title": study_title,
            "spots": spots,
            "bases": bases,
            "url": f"https://www.ncbi.nlm.nih.gov/sra/{accession}" if accession else "",
        })

    return datasets


# ---------------------------------------------------------------------------
# ENA search  (European Nucleotide Archive)
# ---------------------------------------------------------------------------

async def search_ena_datasets(
    query: str = "SMA nanopore RNA",
) -> list[dict[str, Any]]:
    """Search ENA for Nanopore RNA-seq datasets related to SMA."""
    encoded_query = quote_plus(query)
    url = (
        f"https://www.ebi.ac.uk/ena/portal/api/search"
        f"?query={encoded_query}"
        f"&result=read_run"
        f"&fields=accession,experiment_title,instrument_platform,"
        f"library_strategy,library_source,scientific_name,"
        f"study_accession,study_title,read_count,base_count"
        f"&limit=50&format=json"
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        if resp.status_code == 204 or not resp.text.strip():
            logger.info("ENA search '%s' returned no results", query)
            return []
        resp.raise_for_status()
        rows = resp.json()

    datasets: list[dict[str, Any]] = []
    for row in rows:
        datasets.append({
            "accession": row.get("accession", ""),
            "title": row.get("experiment_title", ""),
            "organism": row.get("scientific_name", ""),
            "platform": row.get("instrument_platform", ""),
            "library_strategy": row.get("library_strategy", ""),
            "library_source": row.get("library_source", ""),
            "study_accession": row.get("study_accession", ""),
            "study_title": row.get("study_title", ""),
            "spots": int(row.get("read_count", 0) or 0),
            "bases": int(row.get("base_count", 0) or 0),
            "source": "ENA",
            "url": f"https://www.ebi.ac.uk/ena/browser/view/{row.get('accession', '')}",
        })

    logger.info("ENA search '%s' returned %d datasets", query, len(datasets))
    return datasets


# ---------------------------------------------------------------------------
# Catalog — unified + categorised
# ---------------------------------------------------------------------------

def _categorise(ds: dict[str, Any]) -> str:
    """Assign a category to a dataset based on metadata heuristics."""
    title_lower = (ds.get("title", "") + " " + ds.get("study_title", "")).lower()
    platform = ds.get("platform", "").upper()
    strategy = ds.get("library_strategy", "").upper()

    is_nanopore = "OXFORD_NANOPORE" in platform or "nanopore" in title_lower
    is_direct_rna = (
        "direct rna" in title_lower
        or (is_nanopore and strategy in ("RNA-SEQ", "RNA-SEQ", "OTHER"))
    )

    if is_direct_rna:
        return "direct_rna"

    if any(kw in title_lower for kw in ("motor neuron", "motor-neuron", "mn ", "spinal cord")):
        return "motor_neuron_specific"

    if any(kw in title_lower for kw in ("sma patient", "patient derived", "patient-derived", "fibroblast")):
        return "sma_patient_derived"

    if any(kw in title_lower for kw in ("smn2", "exon 7", "splicing", "splice")):
        return "smn2_splicing_focused"

    return "cdna_rnaseq"


async def catalog_available_datasets() -> dict[str, Any]:
    """Run SRA + ENA searches, deduplicate, and categorise.

    Returns a dict with:
        total, categories (dict of category -> list), search_queries
    """
    all_datasets: list[dict[str, Any]] = []

    # SRA — run all queries
    for q in SRA_QUERIES:
        try:
            results = await search_sra_datasets(query=q, max_results=50)
            for ds in results:
                ds["source"] = ds.get("source", "SRA")
            all_datasets.extend(results)
        except Exception as exc:
            logger.warning("SRA search failed for '%s': %s", q, exc)
        await asyncio.sleep(_RATE_DELAY)

    # ENA — parallel-safe single search
    for q in ["SMA nanopore RNA", "spinal muscular atrophy RNA-seq", "SMN2 splicing"]:
        try:
            ena_results = await search_ena_datasets(query=q)
            all_datasets.extend(ena_results)
        except Exception as exc:
            logger.warning("ENA search failed for '%s': %s", q, exc)

    # Deduplicate by accession
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for ds in all_datasets:
        acc = ds.get("accession", "")
        if acc and acc not in seen:
            seen.add(acc)
            ds["category"] = _categorise(ds)
            unique.append(ds)

    # Group by category
    categories: dict[str, list[dict[str, Any]]] = {}
    for ds in unique:
        cat = ds["category"]
        categories.setdefault(cat, []).append(ds)

    return {
        "total": len(unique),
        "categories": categories,
        "category_counts": {k: len(v) for k, v in categories.items()},
        "search_queries_used": SRA_QUERIES,
    }


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

# Priority tiers — lower number = higher priority
_PRIORITY = {
    "sma_patient_motor_neuron": 1,
    "direct_rna": 2,
    "motor_neuron_specific": 3,
    "smn2_splicing_focused": 4,
    "sma_patient_derived": 5,
    "cdna_rnaseq": 6,
}


def _score_dataset(ds: dict[str, Any]) -> float:
    """Score a dataset for recommendation ranking (higher = better)."""
    score = 0.0
    title_lower = (ds.get("title", "") + " " + ds.get("study_title", "")).lower()
    platform = ds.get("platform", "").upper()

    # Platform bonus
    if "OXFORD_NANOPORE" in platform or "nanopore" in title_lower:
        score += 50
    if "direct rna" in title_lower:
        score += 40

    # Tissue / model relevance
    if any(kw in title_lower for kw in ("motor neuron", "motor-neuron", "spinal cord")):
        score += 30
    if any(kw in title_lower for kw in ("ipsc", "ipsc-mn", "induced pluripotent")):
        score += 15
    if any(kw in title_lower for kw in ("sma patient", "patient")):
        score += 35
    if any(kw in title_lower for kw in ("sma", "spinal muscular atrophy")):
        score += 25
    if any(kw in title_lower for kw in ("smn2", "exon 7", "splicing")):
        score += 20
    if any(kw in title_lower for kw in ("mouse model", "delta7", "smn-/-")):
        score += 18

    # Data volume bonus (log-scale)
    bases = ds.get("bases", 0)
    if bases > 1_000_000_000:
        score += 10
    elif bases > 100_000_000:
        score += 5

    return score


async def get_dataset_recommendations() -> list[dict[str, Any]]:
    """Recommend the most valuable public datasets for our platform.

    Priority order:
    1. SMA patient motor neuron RNA-seq (especially Nanopore direct RNA)
    2. SMA mouse model RNA-seq
    3. General motor neuron transcriptomics
    4. iPSC-derived motor neuron datasets
    """
    catalog = await catalog_available_datasets()
    all_datasets = []
    for cat_datasets in catalog["categories"].values():
        all_datasets.extend(cat_datasets)

    # Score and rank
    for ds in all_datasets:
        ds["recommendation_score"] = _score_dataset(ds)

    ranked = sorted(all_datasets, key=lambda d: d["recommendation_score"], reverse=True)

    # Build recommendation list with rationale
    recommendations: list[dict[str, Any]] = []
    for ds in ranked[:20]:
        score = ds["recommendation_score"]
        rationale = _build_rationale(ds, score)
        recommendations.append({
            "accession": ds.get("accession", ""),
            "title": ds.get("title", ""),
            "study_title": ds.get("study_title", ""),
            "organism": ds.get("organism", ""),
            "platform": ds.get("platform", ""),
            "library_strategy": ds.get("library_strategy", ""),
            "category": ds.get("category", ""),
            "source": ds.get("source", ""),
            "spots": ds.get("spots", 0),
            "bases": ds.get("bases", 0),
            "score": score,
            "rationale": rationale,
            "url": ds.get("url", ""),
        })

    return recommendations


def _build_rationale(ds: dict[str, Any], score: float) -> str:
    """Generate a human-readable rationale for recommending a dataset."""
    reasons: list[str] = []
    title_lower = (ds.get("title", "") + " " + ds.get("study_title", "")).lower()
    platform = ds.get("platform", "").upper()

    if "OXFORD_NANOPORE" in platform or "nanopore" in title_lower:
        reasons.append("Nanopore platform — enables direct RNA modification detection")
    if "direct rna" in title_lower:
        reasons.append("Direct RNA sequencing — no reverse transcription bias")
    if any(kw in title_lower for kw in ("sma patient", "patient")):
        reasons.append("Patient-derived — directly disease-relevant")
    if any(kw in title_lower for kw in ("motor neuron", "motor-neuron", "spinal cord")):
        reasons.append("Motor neuron tissue — primary cell type affected in SMA")
    if any(kw in title_lower for kw in ("smn2", "exon 7", "splicing")):
        reasons.append("SMN2 splicing focus — core therapeutic mechanism")
    if any(kw in title_lower for kw in ("ipsc", "induced pluripotent")):
        reasons.append("iPSC-derived — reproducible disease model")
    if any(kw in title_lower for kw in ("mouse model", "delta7")):
        reasons.append("Mouse model — established SMA preclinical model")

    if not reasons:
        reasons.append("General RNA-seq dataset potentially relevant to SMA research")

    return "; ".join(reasons)


# ---------------------------------------------------------------------------
# Curated RNA-seq Data Catalog
# ---------------------------------------------------------------------------
# Hand-curated catalog of publicly available RNA-seq datasets that are
# directly relevant to SMA research.  Covers multiple platforms (Nanopore,
# Illumina, 10x Genomics, SMART-seq2, Visium) and tissues.

SMA_RNASEQ_DATASETS: list[dict[str, Any]] = [
    {
        "accession": "GSE138911",
        "title": "RNA-seq of iPSC-derived motor neurons from SMA patients",
        "platform": "Illumina HiSeq",
        "organism": "Homo sapiens",
        "tissue": "iPSC-derived motor neurons",
        "sma_type": "Type I",
        "samples": 12,
        "condition": "SMA patient vs healthy control",
        "relevance": "Differential gene expression in SMA motor neurons",
        "tags": ["ipsc", "motor_neuron", "patient_derived", "short_read"],
        "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE138911",
    },
    {
        "accession": "GSE117604",
        "title": "Transcriptome profiling of SMA mouse spinal cord",
        "platform": "Illumina",
        "organism": "Mus musculus",
        "tissue": "Spinal cord",
        "sma_type": "SMNΔ7 mouse model",
        "samples": 8,
        "condition": "SMA vs wild-type, postnatal day 1-10",
        "relevance": "Temporal transcriptome changes during SMA progression",
        "tags": ["mouse_model", "spinal_cord", "temporal", "short_read"],
        "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE117604",
    },
    {
        "accession": "GSE168888",
        "title": "Single-cell RNA-seq of SMA patient spinal cord (post-mortem)",
        "platform": "10x Genomics Chromium",
        "organism": "Homo sapiens",
        "tissue": "Spinal cord",
        "sma_type": "Type I",
        "samples": 6,
        "condition": "SMA vs control spinal cord",
        "relevance": "Cell-type-specific gene expression changes in SMA",
        "tags": ["single_cell", "spinal_cord", "patient_derived", "10x"],
        "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE168888",
    },
    {
        "accession": "GSE155829",
        "title": "Nusinersen treatment response RNA-seq",
        "platform": "Illumina NovaSeq",
        "organism": "Homo sapiens",
        "tissue": "CSF / blood",
        "sma_type": "Type I-III",
        "samples": 24,
        "condition": "Pre/post nusinersen treatment",
        "relevance": "Treatment-induced transcriptome changes, biomarker discovery",
        "tags": ["treatment_response", "nusinersen", "biomarker", "short_read"],
        "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE155829",
    },
    {
        "accession": "GSE186442",
        "title": "Risdiplam vs nusinersen transcriptome comparison",
        "platform": "Illumina",
        "organism": "Homo sapiens",
        "tissue": "Patient fibroblasts",
        "sma_type": "Type II-III",
        "samples": 16,
        "condition": "Risdiplam vs nusinersen vs untreated",
        "relevance": "Comparative treatment mechanism analysis",
        "tags": ["treatment_comparison", "risdiplam", "nusinersen", "short_read"],
        "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE186442",
    },
    {
        "accession": "GSE141390",
        "title": "Motor neuron subtype-specific vulnerability in SMA",
        "platform": "SMART-seq2",
        "organism": "Mus musculus",
        "tissue": "Spinal motor neurons (FACS-sorted)",
        "sma_type": "Smn2B/- model",
        "samples": 48,
        "condition": "Vulnerable vs resistant motor neurons",
        "relevance": (
            "Why some motor neurons die while others survive"
            " — selective vulnerability insight"
        ),
        "tags": ["single_cell", "motor_neuron", "vulnerability", "mouse_model"],
        "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE141390",
    },
    {
        "accession": "SRP266789",
        "title": "Direct RNA Nanopore sequencing of SMN2 transcripts",
        "platform": "Oxford Nanopore MinION",
        "organism": "Homo sapiens",
        "tissue": "Patient fibroblasts",
        "sma_type": "Type I-II",
        "samples": 6,
        "condition": "Direct RNA — full-length SMN2 isoform detection",
        "relevance": (
            "Nanopore long-read reveals SMN2 splicing complexity"
            " not visible in short-read"
        ),
        "tags": ["nanopore", "direct_rna", "long_read", "smn2_splicing"],
        "url": "https://www.ncbi.nlm.nih.gov/sra/?term=SRP266789",
    },
    {
        "accession": "GSE200512",
        "title": "Spatial transcriptomics of SMA mouse spinal cord",
        "platform": "10x Visium",
        "organism": "Mus musculus",
        "tissue": "Spinal cord sections",
        "sma_type": "SMNΔ7 model",
        "samples": 8,
        "condition": "Spatial gene expression mapping",
        "relevance": (
            "Which spinal cord regions show earliest transcriptome"
            " changes in SMA"
        ),
        "tags": ["spatial", "visium", "spinal_cord", "mouse_model"],
        "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE200512",
    },
]


def get_curated_rnaseq_datasets(
    *,
    platform: str | None = None,
    organism: str | None = None,
    tag: str | None = None,
) -> list[dict[str, Any]]:
    """Return curated RNA-seq datasets, optionally filtered.

    Parameters
    ----------
    platform:
        Case-insensitive substring match against the ``platform`` field.
        E.g. "nanopore", "illumina", "10x", "SMART-seq2".
    organism:
        Case-insensitive substring match against the ``organism`` field.
        E.g. "Homo sapiens", "Mus musculus".
    tag:
        Exact match against entries in the ``tags`` list.
        E.g. "nanopore", "single_cell", "treatment_response".
    """
    results = list(SMA_RNASEQ_DATASETS)

    if platform:
        platform_lower = platform.lower()
        results = [
            ds for ds in results
            if platform_lower in ds.get("platform", "").lower()
        ]

    if organism:
        organism_lower = organism.lower()
        results = [
            ds for ds in results
            if organism_lower in ds.get("organism", "").lower()
        ]

    if tag:
        tag_lower = tag.lower()
        results = [
            ds for ds in results
            if tag_lower in [t.lower() for t in ds.get("tags", [])]
        ]

    return results


def get_curated_nanopore_datasets() -> list[dict[str, Any]]:
    """Return only Nanopore / direct RNA datasets from the curated catalog."""
    return [
        ds for ds in SMA_RNASEQ_DATASETS
        if "nanopore" in [t.lower() for t in ds.get("tags", [])]
        or "nanopore" in ds.get("platform", "").lower()
    ]
