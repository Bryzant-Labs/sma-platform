"""Seed the targets table with core SMA genes and proteins.

Run: python scripts/seed_targets.py
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sma_platform.core.config import settings
from sma_platform.core.database import close_pool, execute, init_pool

TARGETS = [
    {
        "symbol": "SMN1",
        "name": "Survival Motor Neuron 1",
        "target_type": "gene",
        "identifiers": {"hgnc": "HGNC:11117", "ensembl": "ENSG00000172062", "uniprot": "Q16637"},
        "description": "Primary SMA gene. Homozygous deletion/mutation causes SMA. Located on chromosome 5q13.",
    },
    {
        "symbol": "SMN2",
        "name": "Survival Motor Neuron 2",
        "target_type": "gene",
        "identifiers": {"hgnc": "HGNC:11118", "ensembl": "ENSG00000205571", "uniprot": "Q16637"},
        "description": "Paralog of SMN1. Copy number is the primary modifier of SMA severity. C-to-T change in exon 7 causes ~90% exon skipping.",
    },
    {
        "symbol": "STMN2",
        "name": "Stathmin-2 (SCG10)",
        "target_type": "gene",
        "identifiers": {"hgnc": "HGNC:11125", "ensembl": "ENSG00000104435", "uniprot": "Q93045"},
        "description": "Microtubule regulator critical for axonal growth. Downregulated in SMA motor neurons. Top neuroprotective target.",
    },
    {
        "symbol": "PLS3",
        "name": "Plastin 3 (T-plastin)",
        "target_type": "gene",
        "identifiers": {"hgnc": "HGNC:9090", "ensembl": "ENSG00000214765", "uniprot": "P13797"},
        "description": "Actin-bundling protein. Natural modifier of SMA severity in discordant families.",
    },
    {
        "symbol": "NCALD",
        "name": "Neurocalcin Delta",
        "target_type": "gene",
        "identifiers": {"hgnc": "HGNC:7654", "ensembl": "ENSG00000104490", "uniprot": "P61601"},
        "description": "Calcium sensor. Reduced NCALD expression rescues SMA phenotype in animal models.",
    },
    {
        "symbol": "UBA1",
        "name": "Ubiquitin-Like Modifier Activating Enzyme 1",
        "target_type": "gene",
        "identifiers": {"hgnc": "HGNC:12469", "ensembl": "ENSG00000130985", "uniprot": "P22314"},
        "description": "Ubiquitin-activating enzyme. Dysregulated in SMA, linked to ubiquitin homeostasis defects.",
    },
    {
        "symbol": "CORO1C",
        "name": "Coronin 1C",
        "target_type": "gene",
        "identifiers": {"hgnc": "HGNC:2254"},
        "description": "Actin-binding protein. Potential SMA modifier through interactome studies.",
    },
    {
        "symbol": "SMN_PROTEIN",
        "name": "SMN Protein Complex",
        "target_type": "protein",
        "identifiers": {"uniprot": "Q16637"},
        "description": "Essential for snRNP biogenesis and pre-mRNA splicing. Loss of full-length SMN protein causes SMA.",
    },
    {
        "symbol": "MTOR_PATHWAY",
        "name": "mTOR Signaling Pathway",
        "target_type": "pathway",
        "identifiers": {"reactome": "R-HSA-165159", "kegg": "hsa04150"},
        "description": "Dysregulated in SMA motor neurons. mTOR hyperactivation may contribute to neurodegeneration.",
    },
    {
        "symbol": "NMJ_MATURATION",
        "name": "Neuromuscular Junction Maturation",
        "target_type": "pathway",
        "identifiers": {},
        "description": "NMJ defects are among the earliest pathological features of SMA.",
    },
]


async def seed():
    await init_pool(settings.database_url)

    for t in TARGETS:
        await execute(
            """INSERT INTO targets (symbol, name, target_type, organism, identifiers, description)
               VALUES ($1, $2, $3, $4, $5, $6)
               ON CONFLICT (symbol, target_type, organism) DO UPDATE
               SET name = excluded.name, identifiers = excluded.identifiers,
                   description = excluded.description, updated_at = datetime('now')""",
            t["symbol"], t["name"], t["target_type"], "Homo sapiens",
            json.dumps(t["identifiers"]), t["description"],
        )
        print(f"  Seeded: {t['symbol']} ({t['target_type']})")

    await close_pool()
    print(f"\nSeeded {len(TARGETS)} targets.")


if __name__ == "__main__":
    asyncio.run(seed())
