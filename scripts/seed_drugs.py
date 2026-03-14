"""Seed the drugs table with approved and pipeline SMA therapies.

Run: python scripts/seed_drugs.py
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sma_platform.core.config import settings
from sma_platform.core.database import close_pool, execute, init_pool

DRUGS = [
    {
        "name": "nusinersen",
        "brand_names": ["Spinraza"],
        "drug_type": "aso",
        "mechanism": "Antisense oligonucleotide targeting SMN2 pre-mRNA ISS-N1 to promote exon 7 inclusion.",
        "approval_status": "approved",
        "approved_for": ["type1", "type2", "type3", "presymptomatic"],
        "manufacturer": "Biogen",
    },
    {
        "name": "risdiplam",
        "brand_names": ["Evrysdi"],
        "drug_type": "splice_modifier",
        "mechanism": "Small molecule SMN2 splicing modifier. Promotes exon 7 inclusion. Oral, crosses BBB.",
        "approval_status": "approved",
        "approved_for": ["type1", "type2", "type3"],
        "manufacturer": "Roche/Genentech",
    },
    {
        "name": "onasemnogene abeparvovec",
        "brand_names": ["Zolgensma"],
        "drug_type": "gene_therapy",
        "mechanism": "AAV9-mediated gene replacement delivering functional SMN1. Single IV infusion.",
        "approval_status": "approved",
        "approved_for": ["type1", "presymptomatic"],
        "manufacturer": "Novartis Gene Therapies",
    },
    {
        "name": "apitegromab",
        "brand_names": [],
        "drug_type": "antibody",
        "mechanism": "Anti-myostatin antibody (SRK-015). Inhibits latent myostatin activation.",
        "approval_status": "phase3",
        "approved_for": [],
        "manufacturer": "Scholar Rock",
    },
    {
        "name": "taldefgrobep alfa",
        "brand_names": ["GYM329"],
        "drug_type": "antibody",
        "mechanism": "Anti-latent myostatin antibody. Muscle-enhancing adjunct to SMN-restoring therapies.",
        "approval_status": "phase3",
        "approved_for": [],
        "manufacturer": "Roche",
    },
    {
        "name": "reldesemtiv",
        "brand_names": [],
        "drug_type": "small_molecule",
        "mechanism": "Fast skeletal muscle troponin activator. Enhances muscle force production.",
        "approval_status": "phase2",
        "approved_for": [],
        "manufacturer": "Cytokinetics",
    },
    {
        "name": "pyridostigmine",
        "brand_names": ["Mestinon"],
        "drug_type": "small_molecule",
        "mechanism": "Acetylcholinesterase inhibitor. Improves neuromuscular transmission at the NMJ.",
        "approval_status": "phase2",
        "approved_for": [],
        "manufacturer": "Various",
    },
]


async def seed():
    await init_pool(settings.database_url)

    for d in DRUGS:
        await execute(
            """INSERT OR REPLACE INTO drugs (name, brand_names, drug_type, mechanism, approval_status, approved_for, manufacturer)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            d["name"], json.dumps(d["brand_names"]), d["drug_type"], d["mechanism"],
            d["approval_status"], json.dumps(d["approved_for"]), d["manufacturer"],
        )
        print(f"  Seeded: {d['name']} ({d['approval_status']})")

    await close_pool()
    print(f"\nSeeded {len(DRUGS)} drugs.")


if __name__ == "__main__":
    asyncio.run(seed())
