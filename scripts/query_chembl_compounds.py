"""Query ChEMBL REST API for bioactive compounds targeting key SMA targets.

Searches ChEMBL by target name, fetches bioactivities with pChEMBL >= 5,
filters for drug-like properties (MW 150-500, LogP < 5), and saves results.

Usage:
    python scripts/query_chembl_compounds.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Priority SMA targets
TARGETS = ["ROCK1", "ROCK2", "LIMK1", "LIMK2", "MAPK14", "PLS3", "CORO1C", "SMN2"]

# Drug-likeness filters
MW_MIN = 150
MW_MAX = 500
LOGP_MAX = 5.0
PCHEMBL_MIN = 5.0

# ChEMBL pagination
PAGE_SIZE = 1000
MAX_PAGES = 10  # Safety limit per target


async def search_target(client: httpx.AsyncClient, target_name: str) -> list[dict]:
    """Search ChEMBL for targets matching the given name. Returns target records."""
    url = f"{BASE_URL}/target/search.json"
    params = {
        "q": target_name,
        "limit": 25,
        "format": "json",
    }
    try:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        targets = data.get("targets", [])
        # Filter for human targets preferentially
        human = [t for t in targets if t.get("organism", "").lower() == "homo sapiens"]
        return human if human else targets[:5]
    except (httpx.HTTPError, json.JSONDecodeError) as e:
        logger.warning("Failed to search target %s: %s", target_name, e)
        return []


async def fetch_bioactivities(
    client: httpx.AsyncClient,
    chembl_target_id: str,
    target_name: str,
) -> list[dict]:
    """Fetch all bioactivities for a ChEMBL target ID with pChEMBL >= 5."""
    all_activities: list[dict] = []
    offset = 0

    for page in range(MAX_PAGES):
        url = f"{BASE_URL}/activity.json"
        params = {
            "target_chembl_id": chembl_target_id,
            "pchembl_value__gte": PCHEMBL_MIN,
            "limit": PAGE_SIZE,
            "offset": offset,
            "format": "json",
        }
        try:
            resp = await client.get(url, params=params, timeout=60)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            logger.warning(
                "HTTP error fetching activities for %s (page %d): %s",
                target_name, page, e,
            )
            break
        except json.JSONDecodeError:
            logger.warning("Invalid JSON from ChEMBL for %s page %d", target_name, page)
            break

        activities = data.get("activities", [])
        if not activities:
            break

        all_activities.extend(activities)
        logger.info(
            "  %s (%s): fetched %d activities (page %d, total so far: %d)",
            target_name, chembl_target_id, len(activities), page + 1, len(all_activities),
        )

        # Check if there are more pages
        page_meta = data.get("page_meta", {})
        if not page_meta.get("next"):
            break
        offset += PAGE_SIZE

        # Small delay to be polite to ChEMBL API
        await asyncio.sleep(0.5)

    return all_activities


def filter_drug_like(activities: list[dict]) -> list[dict]:
    """Filter activities for drug-like compounds (MW 150-500, LogP < 5)."""
    filtered = []
    seen_molecules: set[str] = set()

    for act in activities:
        mol_id = act.get("molecule_chembl_id", "")
        if not mol_id or mol_id in seen_molecules:
            continue

        # Extract molecular properties if available
        mw = act.get("molecular_weight")
        alogp = act.get("alogp")

        # Try to parse MW and LogP
        try:
            mw_val = float(mw) if mw is not None else None
        except (ValueError, TypeError):
            mw_val = None

        try:
            logp_val = float(alogp) if alogp is not None else None
        except (ValueError, TypeError):
            logp_val = None

        # Apply drug-likeness filters (pass if data unavailable)
        if mw_val is not None and (mw_val < MW_MIN or mw_val > MW_MAX):
            continue
        if logp_val is not None and logp_val > LOGP_MAX:
            continue

        try:
            pchembl = float(act.get("pchembl_value", 0))
        except (ValueError, TypeError):
            pchembl = 0

        seen_molecules.add(mol_id)
        filtered.append({
            "molecule_chembl_id": mol_id,
            "compound_name": act.get("molecule_pref_name", ""),
            "canonical_smiles": act.get("canonical_smiles", ""),
            "pchembl_value": pchembl,
            "activity_type": act.get("standard_type", ""),
            "activity_value": act.get("standard_value"),
            "activity_units": act.get("standard_units", ""),
            "activity_relation": act.get("standard_relation", ""),
            "molecular_weight": mw_val,
            "alogp": logp_val,
            "assay_chembl_id": act.get("assay_chembl_id", ""),
            "assay_type": act.get("assay_type", ""),
            "document_chembl_id": act.get("document_chembl_id", ""),
        })

    return filtered


async def fetch_molecule_details(
    client: httpx.AsyncClient,
    molecule_chembl_id: str,
) -> dict | None:
    """Fetch molecule details including MW and LogP from ChEMBL molecule endpoint."""
    url = f"{BASE_URL}/molecule/{molecule_chembl_id}.json"
    try:
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, json.JSONDecodeError):
        return None


async def enrich_compounds_batch(
    client: httpx.AsyncClient,
    compounds: list[dict],
) -> list[dict]:
    """Enrich compounds missing MW/LogP by fetching molecule details."""
    needs_enrichment = [
        c for c in compounds
        if c.get("molecular_weight") is None or c.get("alogp") is None
    ]

    if not needs_enrichment:
        return compounds

    logger.info("Enriching %d compounds missing MW/LogP...", len(needs_enrichment))

    # Batch in groups of 10 to avoid overwhelming the API
    for i in range(0, len(needs_enrichment), 10):
        batch = needs_enrichment[i:i + 10]
        tasks = [
            fetch_molecule_details(client, c["molecule_chembl_id"])
            for c in batch
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for compound, result in zip(batch, results):
            if isinstance(result, Exception) or result is None:
                continue
            props = result.get("molecule_properties", {})
            if props:
                if compound.get("molecular_weight") is None:
                    try:
                        compound["molecular_weight"] = float(props.get("full_mwt", 0))
                    except (ValueError, TypeError):
                        pass
                if compound.get("alogp") is None:
                    try:
                        compound["alogp"] = float(props.get("alogp", 0))
                    except (ValueError, TypeError):
                        pass
                if not compound.get("canonical_smiles"):
                    structs = result.get("molecule_structures", {})
                    if structs:
                        compound["canonical_smiles"] = structs.get("canonical_smiles", "")

        await asyncio.sleep(0.3)

    # Re-filter after enrichment
    final = []
    for c in compounds:
        mw = c.get("molecular_weight")
        logp = c.get("alogp")
        if mw is not None and (mw < MW_MIN or mw > MW_MAX):
            continue
        if logp is not None and logp > LOGP_MAX:
            continue
        final.append(c)

    return final


async def query_target(client: httpx.AsyncClient, target_name: str) -> dict:
    """Query ChEMBL for a single SMA target. Returns summary dict."""
    logger.info("Querying ChEMBL for target: %s", target_name)

    # Step 1: Search for the target
    targets = await search_target(client, target_name)
    if not targets:
        logger.warning("No ChEMBL targets found for %s", target_name)
        return {
            "target_name": target_name,
            "chembl_target_ids": [],
            "compounds": [],
            "total_found": 0,
            "drug_like_count": 0,
        }

    # Step 2: Fetch bioactivities from top target matches
    all_activities: list[dict] = []
    chembl_ids = []
    for t in targets[:3]:  # Top 3 matches
        tid = t.get("target_chembl_id", "")
        if tid:
            chembl_ids.append(tid)
            activities = await fetch_bioactivities(client, tid, target_name)
            all_activities.extend(activities)
            await asyncio.sleep(0.3)

    # Step 3: Filter for drug-like compounds
    drug_like = filter_drug_like(all_activities)

    # Step 4: Enrich missing properties
    drug_like = await enrich_compounds_batch(client, drug_like)

    # Sort by potency (highest pChEMBL first)
    drug_like.sort(key=lambda x: x.get("pchembl_value", 0), reverse=True)

    logger.info(
        "  %s: %d total activities -> %d drug-like compounds",
        target_name, len(all_activities), len(drug_like),
    )

    return {
        "target_name": target_name,
        "chembl_target_ids": chembl_ids,
        "compounds": drug_like,
        "total_activities": len(all_activities),
        "drug_like_count": len(drug_like),
        "top_hits": drug_like[:5],  # Top 5 by potency
    }


async def main():
    """Query ChEMBL for all priority SMA targets and save results."""
    logger.info("Starting ChEMBL compound query for %d targets", len(TARGETS))

    results: dict[str, dict] = {}
    headers = {
        "Accept": "application/json",
        "User-Agent": "SMA-Research-Platform/1.0 (academic research)",
    }

    async with httpx.AsyncClient(
        headers=headers,
        timeout=httpx.Timeout(60.0, connect=15.0),
        follow_redirects=True,
    ) as client:
        for target in TARGETS:
            result = await query_target(client, target)
            results[target] = result
            # Polite delay between targets
            await asyncio.sleep(1.0)

    # Summary report
    print("\n" + "=" * 60)
    print("ChEMBL Compound Query Results")
    print("=" * 60)
    total_compounds = 0
    for target, data in results.items():
        count = data["drug_like_count"]
        total_compounds += count
        top = data.get("top_hits", [])
        top_str = ""
        if top:
            top_names = [
                f"{h.get('compound_name') or h['molecule_chembl_id']} (pChEMBL={h['pchembl_value']:.1f})"
                for h in top[:3]
            ]
            top_str = " | Top: " + ", ".join(top_names)
        print(f"  {target:10s}: {count:4d} compounds{top_str}")

    print(f"\n  TOTAL: {total_compounds} drug-like compounds across {len(TARGETS)} targets")
    print("=" * 60)

    # Save to JSON
    output = {
        "query_date": datetime.now(timezone.utc).isoformat(),
        "targets_queried": TARGETS,
        "filters": {
            "pchembl_min": PCHEMBL_MIN,
            "mw_range": [MW_MIN, MW_MAX],
            "logp_max": LOGP_MAX,
        },
        "total_compounds": total_compounds,
        "results": results,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / "chembl_compounds.json"
    out_path.write_text(json.dumps(output, indent=2, default=str))
    logger.info("Results saved to %s", out_path)


if __name__ == "__main__":
    asyncio.run(main())
