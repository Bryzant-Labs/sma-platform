"""Fetch CRISPR guide sequences from platform API and format for Cas-OFFinder.

Cas-OFFinder input format:
  Line 1: path to genome (2bit or FASTA)
  Line 2: PAM pattern + NRG fields (e.g., NNNNNNNNNNNNNNNNNNNNNGG 0 0)
  Line 3+: guide_sequence max_mismatches

Output: gpu/data/crispr_guides.txt
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    print("ERROR: httpx is required. Install with: pip install httpx")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PLATFORM_API = "https://sma-research.info/api/v2/crispr/guides"
DEFAULT_GENOME_PATH = "/data/GRCh38.fa"
PAM_PATTERN = "NNNNNNNNNNNNNNNNNNNNNGG"  # 20nt guide + NGG PAM = 23nt
MAX_MISMATCHES = 3


def fetch_guides(client: httpx.Client) -> list[dict]:
    """Fetch CRISPR guides from the platform API."""
    try:
        resp = client.get(PLATFORM_API, params={"max_guides": 50}, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        # Handle various response shapes
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # Try common keys
            for key in ("guides", "all_guides", "results"):
                if key in data and isinstance(data[key], list):
                    return data[key]
            # If it has strategies, flatten guides from all strategies
            if "strategies" in data:
                guides = []
                for strategy in data["strategies"]:
                    if isinstance(strategy, dict) and "guides" in strategy:
                        guides.extend(strategy["guides"])
                return guides
        return []
    except Exception as e:
        logger.warning("Could not fetch guides from API: %s", e)
        return []


def extract_sequence(guide: dict) -> str | None:
    """Extract the 20nt guide sequence from a guide dict."""
    for key in ("sequence", "guide_sequence", "protospacer", "spacer"):
        seq = guide.get(key)
        if seq and len(seq) >= 20:
            # Take only the protospacer (20nt), strip PAM if included
            clean = seq.upper().replace("U", "T")
            # If it includes PAM (23nt), take first 20
            if len(clean) >= 23 and clean[-2:] == "GG":
                return clean[:20]
            return clean[:20]
    return None


def generate_casoffinder_input(output_path: str, genome_path: str) -> int:
    """Fetch guides and write Cas-OFFinder input file.

    Returns the number of guides written.
    """
    with httpx.Client() as client:
        raw_guides = fetch_guides(client)
        logger.info("Fetched %d guides from platform API", len(raw_guides))

    # Extract unique sequences
    seen: set[str] = set()
    guide_sequences: list[str] = []
    for g in raw_guides:
        seq = extract_sequence(g)
        if seq and seq not in seen:
            seen.add(seq)
            guide_sequences.append(seq)

    if not guide_sequences:
        logger.warning("No guide sequences found — writing empty file with header only")

    # Write Cas-OFFinder input
    with open(output_path, "w") as f:
        f.write(f"{genome_path}\n")
        f.write(f"{PAM_PATTERN} 0 0\n")
        for seq in guide_sequences:
            # Pad to 20nt with N if shorter
            padded = seq.ljust(20, "N")
            f.write(f"{padded}NGG {MAX_MISMATCHES}\n")

    return len(guide_sequences)


def main():
    parser = argparse.ArgumentParser(description="Prepare Cas-OFFinder input from platform CRISPR guides")
    parser.add_argument(
        "-o", "--output",
        default=os.path.join(os.path.dirname(__file__), "..", "data", "crispr_guides.txt"),
        help="Output file path (default: gpu/data/crispr_guides.txt)",
    )
    parser.add_argument(
        "--genome",
        default=DEFAULT_GENOME_PATH,
        help=f"Path to genome file inside Docker container (default: {DEFAULT_GENOME_PATH})",
    )
    args = parser.parse_args()

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    count = generate_casoffinder_input(str(output), args.genome)
    print(f"Wrote {count} guide sequences to {output}")


if __name__ == "__main__":
    main()
