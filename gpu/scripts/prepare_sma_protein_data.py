"""Prepare SMA protein dataset for ESM-2 fine-tuning via BioNeMo Recipes.

Extracts UniProt protein sequences for all 21 SMA targets + known interactors.
Output: data/sma_proteins.fasta (input for BioNeMo Recipe esm2_sma_finetune.yaml)

Usage: python gpu/scripts/prepare_sma_protein_data.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import httpx

# SMA target proteins — UniProt IDs
SMA_PROTEINS = {
    # Core SMA proteins
    "SMN1": "Q16637",
    "SMN2": "Q16637",  # Same protein, different gene
    "STMN2": "Q93045",
    "PLS3": "P13797",
    "NCALD": "P61601",
    "UBA1": "P22314",
    # SMN complex members
    "GEMIN2": "O14893",
    "GEMIN3": "O15541",
    "GEMIN4": "P57678",
    "GEMIN5": "Q8TEQ6",
    # Discovery targets
    "ANK3": "Q12955",
    "CD44": "P16070",
    "CORO1C": "Q9ULV4",
    "CTNNA1": "P35221",
    "DNMT3B": "Q9UBC3",
    "SULF1": "Q8IWU6",
    "LY96": "Q9Y6Y9",
    "LDHA": "P00338",
    "CAST": "P20810",
    "NEDD4L": "Q96PU5",
    "SPATA18": "Q8TC71",
    "GALNT6": "Q8NCL4",
    # Key interactors
    "TP53": "P04637",  # p53 — motor neuron death pathway
    "MTOR": "P42345",  # mTOR signaling
}

UNIPROT_API = "https://rest.uniprot.org/uniprotkb"


async def fetch_sequence(uniprot_id: str) -> str | None:
    """Fetch protein sequence from UniProt."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{UNIPROT_API}/{uniprot_id}.fasta")
        if resp.status_code == 200:
            lines = resp.text.strip().split("\n")
            return "".join(lines[1:])  # Skip header
    return None


async def main():
    output = Path("data/sma_proteins.fasta")
    output.parent.mkdir(exist_ok=True)

    print(f"Fetching {len(SMA_PROTEINS)} protein sequences from UniProt...")

    seen_ids = set()
    entries = []

    for name, uid in SMA_PROTEINS.items():
        if uid in seen_ids:
            continue
        seen_ids.add(uid)

        seq = await fetch_sequence(uid)
        if seq:
            entries.append(f">{name}|{uid}|SMA_target\n{seq}")
            print(f"  {name} ({uid}): {len(seq)} aa")
        else:
            print(f"  {name} ({uid}): FAILED")
        await asyncio.sleep(0.2)

    with open(output, "w") as f:
        f.write("\n".join(entries) + "\n")

    print(f"\nWrote {len(entries)} sequences to {output}")


if __name__ == "__main__":
    asyncio.run(main())
