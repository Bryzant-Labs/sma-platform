#!/usr/bin/env python3
"""Create 3 new convergence v2 hypothesis cards via the SMA platform API.

Since there is no direct POST /hypotheses endpoint, this script uses the
database INSERT pattern from convergence_hypothesis.py. It can be run:
  1. Directly on the server with database access
  2. Or adapted to use the /hypotheses/generate endpoint after seeding claims

Usage:
  python scripts/create_convergence_v2_hypotheses.py [--dry-run]

Requires:
  - DATABASE_URL environment variable (asyncpg connection string)
  - Or run within the SMA platform's Python environment
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# The 3 new hypothesis cards based on convergence synthesis v2
HYPOTHESES = [
    {
        "hypothesis_type": "mechanism",
        "title": "ROCK-LIMK2-CFL2 axis is the primary druggable cascade in SMA motor neurons",
        "description": (
            "Cross-dataset convergence from GSE287257 (ALS snRNA-seq, 61,664 cells) and "
            "GSE208629 (SMA scRNA-seq, 39,136 cells) identifies the ROCK-LIMK2-CFL2 signaling "
            "cascade as the most consistently dysregulated druggable pathway in SMA motor neurons. "
            "LIMK2 is upregulated +2.81x (p=0.002) in SMA MNs, ROCK1/2 are both elevated, and "
            "CFL2 is up +1.83x (p=2e-4) as a compensatory response. Fasudil (ROCK inhibitor) "
            "has Phase 2 ALS safety data (PMID 39424560) and SMA mouse efficacy (PMID 22397316)."
        ),
        "rationale": (
            "SMN deficiency disrupts the SMN-PFN2a complex (PMID 21920940), leading to RhoA/ROCK "
            "hyperactivation (PMID 25221469). ROCK phosphorylates LIMK2 (not LIMK1 in SMA context), "
            "which in turn hyperphosphorylates CFL2 (cofilin-2), inactivating it and disrupting "
            "actin dynamics. 10/14 actin pathway genes are upregulated in SMA MNs (GSE208629), "
            "representing a coordinated but ultimately insufficient compensatory response. "
            "CORO1C was previously considered a target but is now deprioritized as a glial marker "
            "(depleted in SMA MNs: -1.81 log2FC, p=7.3e-4). The LIMK1-to-LIMK2 switch "
            "(LIMK2 UP +2.81x in SMA, LIMK1 DOWN -0.81x in ALS) indicates LIMK2 is the "
            "disease-relevant kinase in motor neuron diseases."
        ),
        "confidence": 0.82,
        "status": "proposed",
        "generated_by": "convergence-synthesis-v2",
        "metadata": {
            "convergence_version": "v2",
            "datasets": ["GSE287257", "GSE208629", "GSE69175", "GSE113924"],
            "key_genes": ["ROCK1", "ROCK2", "LIMK2", "CFL2", "PFN2"],
            "drug_candidates": ["Fasudil", "LIMK2 inhibitor (MDI-114215 class)", "Risdiplam"],
            "therapeutic_strategy": "Triple therapy: Risdiplam + Fasudil + LIMK2i",
            "evidence_streams": 4,
            "single_cell_validated": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    },
    {
        "hypothesis_type": "biomarker",
        "title": "CFL2 phosphorylation status as SMA-specific biomarker distinguishing compensation from failure",
        "description": (
            "CFL2 (cofilin-2) shows opposite regulation in SMA vs ALS motor neurons: "
            "UP +1.83x (p=2e-4) in SMA MNs (GSE208629) vs DOWN -0.94x (p=0.024) in ALS MNs "
            "(GSE287257). This disease-specific signature makes CFL2 and its phosphorylation "
            "state (p-CFL2/CFL2 ratio) a candidate biomarker for: (1) distinguishing SMA from "
            "ALS at the molecular level, (2) monitoring therapeutic response to ROCK/LIMK "
            "inhibitors, and (3) tracking the transition from compensatory (Stage 1) to "
            "failure (Stage 2) states in motor neuron diseases."
        ),
        "rationale": (
            "In SMA motor neurons, CFL2 upregulation represents active compensation -- the cell "
            "is increasing cofilin-2 production to maintain actin dynamics despite SMN-profilin "
            "disruption. In ALS motor neurons, CFL2 downregulation indicates this compensation "
            "has collapsed. The p-CFL2/CFL2 ratio reflects LIMK2 activity: high ratio = LIMK2 "
            "hyperphosphorylating cofilin (expected in SMA), low ratio = kinase failure (expected "
            "in late-stage ALS). This biomarker could be measured in CSF or via RNAscope/IHC on "
            "biopsy tissue. A decrease in p-CFL2/CFL2 ratio after Fasudil treatment would confirm "
            "target engagement. Bulk data from GSE69175 supports CFL2 upregulation (+2.9x in SMA "
            "iPSC-MNs), and the single-cell data now confirms this is MN-specific."
        ),
        "confidence": 0.68,
        "status": "proposed",
        "generated_by": "convergence-synthesis-v2",
        "metadata": {
            "convergence_version": "v2",
            "datasets": ["GSE287257", "GSE208629", "GSE69175"],
            "key_genes": ["CFL2"],
            "biomarker_type": "disease-specific molecular marker",
            "measurement_methods": ["Western blot (p-CFL2/CFL2)", "CSF proteomics", "RNAscope", "IHC"],
            "disease_comparison": {
                "SMA": "CFL2 UP +1.83x (compensation)",
                "ALS": "CFL2 DOWN -0.94x (failure)",
            },
            "single_cell_validated": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    },
    {
        "hypothesis_type": "therapeutic",
        "title": "LIMK2-selective inhibition as Fasudil augmentation strategy in SMA",
        "description": (
            "LIMK2 is upregulated +2.81x (p=0.002) in SMA motor neurons (GSE208629), making it "
            "the most strongly induced kinase in the ROCK-cofilin pathway. While Fasudil targets "
            "ROCK upstream, adding a LIMK2-selective inhibitor would provide dual-level pathway "
            "blockade: ROCK inhibition reduces LIMK2 phosphorylation, while LIMK2 inhibition "
            "directly prevents cofilin hyperphosphorylation. Tool compounds exist (MDI-114215 "
            "for LIMK, LX7101 reached Phase I for glaucoma), but no LIMK inhibitor has been "
            "tested in any motor neuron disease model."
        ),
        "rationale": (
            "The LIMK1-to-LIMK2 switch is a key finding: LIMK2 (not LIMK1) is the SMA-relevant "
            "kinase. In ALS MNs, LIMK1 is downregulated (-0.81, p=0.004) while LIMK2 is "
            "upregulated (+1.01, p=0.009) -- a compensatory switch. In SMA MNs, LIMK2 shows "
            "even stronger upregulation (+2.81x), suggesting the compensation is more active. "
            "Fasudil alone may be insufficient because: (1) ROCK has many substrates beyond LIMK, "
            "so partial ROCK inhibition may not sufficiently reduce LIMK2 activity; (2) LIMK2 "
            "can be activated by PAK independently of ROCK; (3) the SMA mouse Fasudil data shows "
            "improvement but not cure (PMID 22397316). A Fasudil + LIMK2i combination could "
            "achieve more complete pathway normalization. Priority experiment: test MDI-114215 "
            "or analog in SMA iPSC-derived motor neurons, measuring neurite length, actin rod "
            "formation, and p-CFL2/CFL2 ratio as readouts."
        ),
        "confidence": 0.72,
        "status": "proposed",
        "generated_by": "convergence-synthesis-v2",
        "metadata": {
            "convergence_version": "v2",
            "datasets": ["GSE287257", "GSE208629"],
            "key_genes": ["LIMK2", "LIMK1", "CFL2", "ROCK1", "ROCK2"],
            "drug_candidates": ["MDI-114215 (tool LIMK inhibitor)", "LX7101 (Phase I glaucoma)", "FRAX486 (PAK/LIMK)"],
            "combination_with": "Fasudil (ROCK inhibitor)",
            "therapeutic_strategy": "Dual kinase cascade blockade: ROCK + LIMK2",
            "priority_experiment": "MDI-114215 in SMA iPSC-MNs: neurite length, actin rods, p-CFL2/CFL2",
            "single_cell_validated": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    },
]


async def insert_hypotheses_db(dry_run: bool = False):
    """Insert hypotheses directly into the database."""
    # Import database functions from the platform
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from sma_platform.core.database import execute, init_pool, close_pool

    await init_pool()

    results = []
    for hyp in HYPOTHESES:
        logger.info("Processing: %s", hyp["title"][:80])

        if dry_run:
            logger.info("  [DRY RUN] Would insert hypothesis with confidence %.2f", hyp["confidence"])
            results.append({"title": hyp["title"], "status": "dry_run"})
            continue

        metadata_json = json.dumps(hyp["metadata"])
        try:
            await execute(
                """INSERT INTO hypotheses
                       (hypothesis_type, title, description, rationale,
                        supporting_evidence, confidence, status,
                        generated_by, metadata)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                hyp["hypothesis_type"],
                hyp["title"][:500],
                hyp["description"],
                hyp["rationale"],
                [],  # supporting_evidence (UUID array) -- no specific claim IDs yet
                hyp["confidence"],
                hyp["status"],
                hyp["generated_by"],
                metadata_json,
            )
            logger.info("  Inserted successfully (confidence: %.2f)", hyp["confidence"])
            results.append({"title": hyp["title"], "status": "inserted"})
        except Exception as e:
            logger.error("  Failed to insert: %s", e)
            results.append({"title": hyp["title"], "status": "error", "error": str(e)})

    await close_pool()
    return results


async def insert_hypotheses_api(dry_run: bool = False):
    """Alternative: use the generate endpoint to trigger hypothesis generation.

    Since there is no direct POST /hypotheses endpoint, this function
    triggers the convergence hypothesis generator which will pick up
    recent claims and create hypotheses from them.

    For direct insertion of custom hypotheses, use insert_hypotheses_db().
    """
    try:
        import httpx
    except ImportError:
        logger.error("httpx not installed. Install with: pip install httpx")
        return []

    base_url = "https://sma-research.info/api/v2"
    admin_key = "sma-admin-2026"

    async with httpx.AsyncClient(timeout=60) as client:
        # Trigger convergence generation which will scan recent claims
        logger.info("Triggering convergence hypothesis generation...")
        resp = await client.post(
            f"{base_url}/hypotheses/generate",
            params={"days_back": 30, "min_claims": 2, "dry_run": dry_run},
            headers={"x-admin-key": admin_key},
        )
        if resp.status_code == 200:
            result = resp.json()
            logger.info("Generation result: %s", json.dumps(result, indent=2))
            return result
        else:
            logger.error("API returned %d: %s", resp.status_code, resp.text[:500])
            return {"error": resp.status_code, "detail": resp.text[:500]}


def main():
    parser = argparse.ArgumentParser(description="Create convergence v2 hypothesis cards")
    parser.add_argument("--dry-run", action="store_true", help="Preview without inserting")
    parser.add_argument(
        "--method",
        choices=["db", "api"],
        default="db",
        help="Insert method: 'db' for direct database insert, 'api' for API trigger",
    )
    args = parser.parse_args()

    if args.method == "db":
        results = asyncio.run(insert_hypotheses_db(dry_run=args.dry_run))
    else:
        results = asyncio.run(insert_hypotheses_api(dry_run=args.dry_run))

    print("\n=== Results ===")
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
