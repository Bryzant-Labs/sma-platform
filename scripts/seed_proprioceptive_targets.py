"""Seed the targets table with proprioceptive circuit pathway targets.

These targets are relevant to Prof. Simon's proprioceptive circuit research
and the intersection of actin pathway disruption with sensory-motor circuitry in SMA.

Run: python scripts/seed_proprioceptive_targets.py
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sma_platform.core.config import settings
from sma_platform.core.database import close_pool, execute, init_pool

PROPRIOCEPTIVE_TARGETS = [
    {
        "symbol": "CHAT",
        "name": "Choline O-Acetyltransferase",
        "gene_id": 1103,
        "target_type": "gene",
        "identifiers": {
            "hgnc": "HGNC:1917",
            "ensembl": "ENSG00000070748",
            "uniprot": "P28329",
            "ncbi_gene": "1103",
        },
        "description": (
            "Motor neuron marker enzyme that catalyzes acetylcholine synthesis. "
            "Used to identify and quantify motor neurons in spinal cord sections. "
            "ChAT+ cell counts are a standard readout for motor neuron survival in SMA mouse models. "
            "Expression decreases in SMA motor neurons before cell death."
        ),
        "aliases": ["ChAT", "CMS1A", "CMS6"],
    },
    {
        "symbol": "PVALB",
        "name": "Parvalbumin",
        "gene_id": 5816,
        "target_type": "gene",
        "identifiers": {
            "hgnc": "HGNC:9704",
            "ensembl": "ENSG00000100362",
            "uniprot": "P20472",
            "ncbi_gene": "5816",
        },
        "description": (
            "Calcium-binding protein that serves as a definitive marker for proprioceptive "
            "(Ia afferent) sensory neurons in dorsal root ganglia. PVALB+ neurons form "
            "monosynaptic connections with motor neurons via VGLUT1+ boutons. These "
            "proprioceptive synapses are lost early in SMA, before motor neuron death "
            "(Mentis et al., 2011, PMID 21315257). PVALB-Cre mice are used to "
            "genetically label and manipulate proprioceptive neurons."
        ),
        "aliases": ["PV", "parvalbumin alpha"],
    },
    {
        "symbol": "RUNX3",
        "name": "RUNX Family Transcription Factor 3",
        "gene_id": 864,
        "target_type": "gene",
        "identifiers": {
            "hgnc": "HGNC:10473",
            "ensembl": "ENSG00000020633",
            "uniprot": "Q13761",
            "ncbi_gene": "864",
        },
        "description": (
            "Transcription factor essential for proprioceptive neuron development and "
            "specification. RUNX3 knockout mice lack proprioceptive neurons entirely, "
            "resulting in severe ataxia. RUNX3 cooperates with ETV1/Er81 to establish "
            "the proprioceptive neuron identity program. Relevant to understanding why "
            "proprioceptive synapses are selectively vulnerable in SMA -- developmental "
            "programming may determine adult vulnerability."
        ),
        "aliases": ["CBFA3", "AML2", "PEBP2aC"],
    },
    {
        "symbol": "SLC17A7",
        "name": "Vesicular Glutamate Transporter 1 (VGLUT1)",
        "gene_id": 57030,
        "target_type": "gene",
        "identifiers": {
            "hgnc": "HGNC:16704",
            "ensembl": "ENSG00000104888",
            "uniprot": "Q9P2U7",
            "ncbi_gene": "57030",
        },
        "description": (
            "Vesicular glutamate transporter expressed in proprioceptive Ia afferent "
            "terminals. VGLUT1+ bouton count on motor neurons is the gold-standard "
            "histological readout for proprioceptive synapse integrity in SMA research. "
            "Reduced VGLUT1+ boutons precede motor neuron death in SMA mice (Mentis et al., "
            "2011). VGLUT1 reduction correlates with H-reflex impairment in SMA patients "
            "(Simon et al., 2025, PMID 39982868)."
        ),
        "aliases": ["VGLUT1", "BNPI"],
    },
    {
        "symbol": "ETV1",
        "name": "ETS Variant Transcription Factor 1 (Er81)",
        "gene_id": 2115,
        "target_type": "gene",
        "identifiers": {
            "hgnc": "HGNC:3490",
            "ensembl": "ENSG00000006468",
            "uniprot": "P50549",
            "ncbi_gene": "2115",
        },
        "description": (
            "ETS family transcription factor (also known as Er81) that specifies "
            "proprioceptive neuron identity during development. ETV1 works with RUNX3 "
            "to establish the proprioceptive lineage in DRG neurons. ETV1 is also "
            "expressed in specific motor neuron pools, potentially linking sensory and "
            "motor neuron identity programs. Relevant to understanding circuit-level "
            "vulnerability in SMA."
        ),
        "aliases": ["ER81", "ETS-related protein 81"],
    },
    {
        "symbol": "GDNF",
        "name": "Glial Cell Derived Neurotrophic Factor",
        "gene_id": 2668,
        "target_type": "gene",
        "identifiers": {
            "hgnc": "HGNC:4232",
            "ensembl": "ENSG00000168621",
            "uniprot": "P39905",
            "ncbi_gene": "2668",
        },
        "description": (
            "Neurotrophic factor critical for motor neuron survival and NMJ maintenance. "
            "GDNF supports both motor neuron cell bodies and their peripheral synapses. "
            "GDNF signaling through RET/GFRalpha1 promotes motor neuron survival in "
            "neurodegenerative conditions. Relevant to proprioceptive circuit maintenance "
            "as GDNF also influences sensory neuron survival and central synapse formation. "
            "Potential therapeutic target for SMN-independent neuroprotection in SMA."
        ),
        "aliases": ["ATF1", "ATF2", "HFG3"],
    },
]


async def seed():
    """Seed proprioceptive circuit targets into the database."""
    await init_pool(settings.database_url)

    seeded = 0
    for t in PROPRIOCEPTIVE_TARGETS:
        identifiers = t["identifiers"].copy()
        identifiers["ncbi_gene"] = str(t["gene_id"])
        if t.get("aliases"):
            identifiers["aliases"] = t["aliases"]

        await execute(
            """INSERT INTO targets (symbol, name, target_type, organism, identifiers, description)
               VALUES ($1, $2, $3, $4, $5, $6)
               ON CONFLICT (symbol, target_type, organism) DO UPDATE
               SET name = excluded.name,
                   identifiers = excluded.identifiers,
                   description = excluded.description,
                   updated_at = CURRENT_TIMESTAMP""",
            t["symbol"],
            t["name"],
            t["target_type"],
            "Homo sapiens",
            json.dumps(identifiers),
            t["description"],
        )
        print(f"  Seeded: {t['symbol']} (Gene ID: {t['gene_id']}, type: {t['target_type']})")
        seeded += 1

    await close_pool()
    print(f"\nSeeded {seeded} proprioceptive circuit targets.")


if __name__ == "__main__":
    asyncio.run(seed())
