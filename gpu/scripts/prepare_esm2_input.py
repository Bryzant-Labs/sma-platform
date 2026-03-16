"""Fetch protein sequences for SMA targets from UniProt and write FASTA file.

Fetches sequences for all 21 SMA targets. First tries the platform API
at sma-research.info to get the full target list, then fetches protein
sequences from UniProt for each target with a known UniProt ID.

Output: gpu/data/sma_proteins.fasta
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

try:
    import httpx
except ImportError:
    print("ERROR: httpx is required. Install with: pip install httpx")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Known UniProt IDs for core SMA targets
KNOWN_UNIPROT_IDS: dict[str, str] = {
    "SMN1": "Q16637",
    "SMN2": "Q16637",   # Same protein as SMN1
    "PLS3": "P13797",
    "STMN2": "Q93045",
    "NCALD": "P61601",
    "UBA1": "P22314",
    "CORO1C": "Q9ULV4",
}

PLATFORM_API = "https://sma-research.info/api/v2/targets"
UNIPROT_API = "https://rest.uniprot.org/uniprotkb"


def fetch_targets_from_platform(client: httpx.Client) -> list[dict]:
    """Fetch target list from the SMA platform API."""
    try:
        resp = client.get(PLATFORM_API, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        # API may return {"targets": [...]} or a list directly
        if isinstance(data, dict) and "targets" in data:
            return data["targets"]
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        logger.warning("Could not fetch targets from platform API: %s", e)
        return []


def fetch_uniprot_sequence(client: httpx.Client, uniprot_id: str) -> str | None:
    """Fetch protein FASTA sequence from UniProt."""
    url = f"{UNIPROT_API}/{uniprot_id}.fasta"
    try:
        resp = client.get(url, timeout=15)
        if resp.status_code == 200:
            lines = resp.text.strip().split("\n")
            # Skip header line, join sequence lines
            seq_lines = [l for l in lines if not l.startswith(">")]
            return "".join(seq_lines)
        logger.warning("UniProt %s returned status %d", uniprot_id, resp.status_code)
        return None
    except Exception as e:
        logger.warning("Failed to fetch UniProt %s: %s", uniprot_id, e)
        return None


def build_uniprot_map(platform_targets: list[dict]) -> dict[str, str]:
    """Build gene_symbol -> uniprot_id map from platform targets + known IDs."""
    mapping = dict(KNOWN_UNIPROT_IDS)

    for t in platform_targets:
        symbol = t.get("symbol") or t.get("gene_symbol") or t.get("name", "")
        uniprot = t.get("uniprot_id") or t.get("uniprot")
        if symbol and uniprot and symbol not in mapping:
            mapping[symbol] = uniprot

    return mapping


def generate_fasta(output_path: str) -> int:
    """Fetch protein sequences and write FASTA file.

    Returns the number of sequences written.
    """
    with httpx.Client() as client:
        # Try to get targets from platform
        platform_targets = fetch_targets_from_platform(client)
        logger.info("Got %d targets from platform API", len(platform_targets))

        # Build UniProt mapping
        uniprot_map = build_uniprot_map(platform_targets)
        logger.info("UniProt map has %d entries", len(uniprot_map))

        # Fetch sequences
        sequences: list[tuple[str, str, str]] = []  # (symbol, uniprot_id, sequence)
        seen_uniprot: set[str] = set()

        for symbol, uniprot_id in sorted(uniprot_map.items()):
            if uniprot_id in seen_uniprot:
                # Still write an alias entry but skip re-fetching
                for s, uid, seq in sequences:
                    if uid == uniprot_id:
                        sequences.append((symbol, uniprot_id, seq))
                        break
                continue

            logger.info("Fetching %s (%s)...", symbol, uniprot_id)
            seq = fetch_uniprot_sequence(client, uniprot_id)
            if seq:
                sequences.append((symbol, uniprot_id, seq))
                seen_uniprot.add(uniprot_id)
                logger.info("  %s: %d aa", symbol, len(seq))
            else:
                logger.warning("  %s: no sequence found", symbol)

            # Rate limiting — be polite to UniProt
            time.sleep(0.5)

    # Write FASTA
    count = 0
    with open(output_path, "w") as f:
        seen_written: set[str] = set()
        for symbol, uniprot_id, seq in sequences:
            # Avoid duplicate entries for same protein (e.g. SMN1/SMN2)
            entry_key = f"{symbol}_{uniprot_id}"
            if entry_key in seen_written:
                continue
            seen_written.add(entry_key)

            f.write(f">{symbol}|{uniprot_id} SMA target protein\n")
            # Write sequence in 80-char lines
            for i in range(0, len(seq), 80):
                f.write(seq[i : i + 80] + "\n")
            count += 1

    return count


def main():
    parser = argparse.ArgumentParser(description="Prepare ESM-2 input FASTA for SMA targets")
    parser.add_argument(
        "-o", "--output",
        default=os.path.join(os.path.dirname(__file__), "..", "data", "sma_proteins.fasta"),
        help="Output FASTA path (default: gpu/data/sma_proteins.fasta)",
    )
    args = parser.parse_args()

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    count = generate_fasta(str(output))
    print(f"Wrote {count} protein sequences to {output}")


if __name__ == "__main__":
    main()
