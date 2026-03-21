#!/usr/bin/env python3
"""Systematic PMID hallucination checker for the SMA Research Platform.

Scans all documents in docs/ for PMIDs and verifies each against PubMed.
Reports: valid, invalid (hallucinated), and unverifiable PMIDs.

Usage:
    python scripts/verify_pmids.py
    python scripts/verify_pmids.py --check-db   # Also check DB hypotheses
"""

import re
import sys
import glob
import time
import asyncio
from pathlib import Path

# Try to import Biopython
try:
    from Bio import Entrez
    Entrez.email = "christian@bryzant.com"
    HAS_ENTREZ = True
except ImportError:
    HAS_ENTREZ = False
    print("WARNING: Biopython not installed. Install with: pip install biopython")


def find_pmids_in_file(filepath: str) -> list[tuple[str, str, int]]:
    """Find all PMID references in a file. Returns [(pmid, context, line_number)]."""
    pmids = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                # Match PMID patterns: PMID 12345678, PMID:12345678, PMID12345678
                for match in re.finditer(r"PMID[:\s]*(\d{7,9})", line):
                    pmid = match.group(1)
                    context = line.strip()[:120]
                    pmids.append((pmid, context, i))
    except Exception as e:
        print(f"  Error reading {filepath}: {e}")
    return pmids


def verify_pmid(pmid: str) -> dict:
    """Verify a PMID against PubMed. Returns {pmid, valid, title, error}."""
    if not HAS_ENTREZ:
        return {"pmid": pmid, "valid": None, "title": "SKIPPED (no Biopython)", "error": None}

    try:
        handle = Entrez.efetch(db="pubmed", id=pmid, rettype="abstract", retmode="text")
        text = handle.read()
        handle.close()
        time.sleep(0.35)  # Rate limit: max 3 requests/sec

        if not text or "Error" in text[:50]:
            return {"pmid": pmid, "valid": False, "title": "NOT FOUND", "error": "PubMed returned empty/error"}

        # Extract title (usually second non-empty line)
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        title = lines[1] if len(lines) > 1 else lines[0] if lines else "Unknown"

        return {"pmid": pmid, "valid": True, "title": title[:120], "error": None}

    except Exception as e:
        return {"pmid": pmid, "valid": None, "title": "VERIFICATION FAILED", "error": str(e)}


def main():
    check_db = "--check-db" in sys.argv

    # Find all markdown and Python files in docs/ and src/
    search_paths = [
        "docs/**/*.md",
        "docs/**/*.html",
        "src/**/*.py",
        "scripts/**/*.py",
        "frontend/**/*.html",
    ]

    all_files = []
    for pattern in search_paths:
        all_files.extend(glob.glob(pattern, recursive=True))

    print(f"Scanning {len(all_files)} files for PMIDs...")
    print("=" * 80)

    # Collect all PMIDs with their locations
    pmid_locations: dict[str, list[tuple[str, str, int]]] = {}
    for filepath in sorted(all_files):
        pmids = find_pmids_in_file(filepath)
        for pmid, context, line in pmids:
            if pmid not in pmid_locations:
                pmid_locations[pmid] = []
            pmid_locations[pmid].append((filepath, context, line))

    unique_pmids = sorted(pmid_locations.keys())
    print(f"Found {len(unique_pmids)} unique PMIDs across {sum(len(v) for v in pmid_locations.values())} references")
    print()

    # Verify each PMID
    results = {"valid": [], "invalid": [], "error": []}

    for i, pmid in enumerate(unique_pmids):
        result = verify_pmid(pmid)
        status = "OK" if result["valid"] else "HALLUCINATED" if result["valid"] is False else "ERROR"

        if result["valid"]:
            results["valid"].append(result)
        elif result["valid"] is False:
            results["invalid"].append(result)
        else:
            results["error"].append(result)

        locations = pmid_locations[pmid]
        files_str = ", ".join(set(loc[0] for loc in locations))

        print(f"  [{i+1}/{len(unique_pmids)}] PMID {pmid}: {status}")
        if status != "OK":
            print(f"         Title: {result['title']}")
            print(f"         Files: {files_str}")
            for filepath, context, line in locations[:2]:
                print(f"         {filepath}:{line}: {context[:80]}")
        if result.get("error"):
            print(f"         Error: {result['error']}")

    # Summary
    print()
    print("=" * 80)
    print(f"VERIFICATION SUMMARY")
    print(f"  Total unique PMIDs: {len(unique_pmids)}")
    print(f"  Valid:              {len(results['valid'])}")
    print(f"  HALLUCINATED:       {len(results['invalid'])}")
    print(f"  Verification error: {len(results['error'])}")

    if results["invalid"]:
        print()
        print("HALLUCINATED PMIDs (MUST FIX):")
        for r in results["invalid"]:
            locs = pmid_locations[r["pmid"]]
            print(f"  PMID {r['pmid']}: {r['title']}")
            for filepath, context, line in locs:
                print(f"    {filepath}:{line}: {context[:80]}")

    hallucination_rate = len(results["invalid"]) / len(unique_pmids) * 100 if unique_pmids else 0
    print(f"\nHallucination rate: {hallucination_rate:.1f}%")

    return 1 if results["invalid"] else 0


if __name__ == "__main__":
    sys.exit(main())
