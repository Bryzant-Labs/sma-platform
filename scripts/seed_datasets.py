"""Seed the datasets table from the curated data inventory.

Run: python scripts/seed_datasets.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sma_platform.core.config import settings
from sma_platform.core.database import close_pool, execute, init_pool

DATASETS = [
    {
        "accession": "GSE69175", "source_db": "geo",
        "title": "RNA-seq of patient-derived iPSC motor neurons",
        "modality": "rna-seq", "organism": "Homo sapiens",
        "tissue": "purified patient-derived motor neurons",
        "evidence_tier": "tier1", "usage_class": "use_now",
        "description": "Direct human MN dataset; strong starting point for SMA MN vulnerability signals.",
        "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE69175",
    },
    {
        "accession": "GSE108094", "source_db": "geo",
        "title": "Deep RNA-seq expression and altered splicing in SMA motor neurons",
        "modality": "rna-seq", "organism": "Homo sapiens",
        "tissue": "motor neurons", "evidence_tier": "tier1", "usage_class": "use_now",
        "description": "Designed to detect altered splicing/expressed genes in SMA MNs.",
        "url": "https://www.omicsdi.org/dataset/geo/GSE108094",
    },
    {
        "accession": "GSE208629", "source_db": "geo",
        "title": "Single-cell RNA-seq of severe SMA mouse spinal cord",
        "modality": "scrna-seq", "organism": "Mus musculus",
        "tissue": "spinal cord", "evidence_tier": "tier1", "usage_class": "use_now",
        "description": "Single-cell atlas enables cell-type specificity and context slicing.",
        "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE208629",
    },
    {
        "accession": "GSE87281", "source_db": "geo",
        "title": "Bulk RNA-seq of inducible SMA mouse spinal cord (intron retention)",
        "modality": "rna-seq", "organism": "Mus musculus",
        "tissue": "spinal cord", "evidence_tier": "tier2", "usage_class": "use_later",
        "description": "Useful for validating broad splicing/intron-retention patterns.",
        "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE87281",
    },
    {
        "accession": "PXD033055", "source_db": "pride",
        "title": "SMA-relevant proteomics (splicing diseases context)",
        "modality": "proteomics", "organism": "Homo sapiens",
        "tissue": "see dataset metadata", "evidence_tier": "tier2", "usage_class": "use_later",
        "description": "Protein-layer cross-check to reject RNA-only artefacts.",
        "url": "https://proteomecentral.proteomexchange.org/cgi/GetDataset?ID=PXD033055",
    },
    {
        "accession": "PXD060060", "source_db": "pride",
        "title": "SMA multiomics profiling",
        "modality": "multiomics", "organism": "Homo sapiens",
        "tissue": "see project metadata", "evidence_tier": "tier3", "usage_class": "use_later",
        "description": "Potentially rich, but needs careful metadata/QC before use.",
        "url": "https://www.ebi.ac.uk/pride/archive/projects/PXD060060",
    },
    {
        "accession": "GSE65470", "source_db": "geo",
        "title": "NMJ-focused transcriptomics in SMA context",
        "modality": "transcriptomics", "organism": "Mus musculus",
        "tissue": "nmj / motor neuron", "evidence_tier": "tier3", "usage_class": "use_later",
        "description": "NMJ-framed dataset for later cross-checks.",
        "url": "https://www.omicsdi.org/dataset/geo/GSE65470",
    },
]


async def seed():
    await init_pool(settings.database_url)

    for d in DATASETS:
        await execute(
            """INSERT OR REPLACE INTO datasets (accession, source_db, title, modality, organism, tissue,
               evidence_tier, usage_class, description, url)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
            d["accession"], d["source_db"], d["title"], d["modality"], d["organism"],
            d["tissue"], d["evidence_tier"], d["usage_class"], d["description"], d["url"],
        )
        print(f"  Seeded: {d['accession']} ({d['evidence_tier']})")

    await close_pool()
    print(f"\nSeeded {len(DATASETS)} datasets.")


if __name__ == "__main__":
    asyncio.run(seed())
