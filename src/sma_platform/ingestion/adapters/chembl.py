"""ChEMBL adapter — bioactivity and compound data for SMA drug targets.

Queries the ChEMBL REST API for target bioactivities and compound metadata.
API docs: https://www.ebi.ac.uk/chembl/api/data/
No API key required. Rate-limited; we add small delays between batch calls.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"


async def search_target(query: str) -> dict | None:
    """Search ChEMBL for a target matching the query string.

    Args:
        query: Target name or gene symbol (e.g. "SMN1", "survival motor neuron")

    Returns:
        First matching target dict with chembl_id, pref_name, organism, target_type,
        or None if no results found.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(
                f"{BASE_URL}/target/search.json",
                params={"q": query, "limit": 5},
            )
            if resp.status_code == 404:
                logger.info("ChEMBL target search '%s': no results (404)", query)
                return None
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning("ChEMBL target search '%s' failed: %s", query, e)
            return None
        except httpx.TimeoutException:
            logger.warning("ChEMBL target search '%s' timed out", query)
            return None

    targets = data.get("targets", [])
    if not targets:
        logger.info("ChEMBL target search '%s': no results", query)
        return None

    # Return first hit
    t = targets[0]
    result = {
        "target_chembl_id": t.get("target_chembl_id", ""),
        "pref_name": t.get("pref_name", ""),
        "organism": t.get("organism", ""),
        "target_type": t.get("target_type", ""),
    }
    logger.info("ChEMBL target search '%s': found %s", query, result["target_chembl_id"])
    return result


async def get_bioactivities(
    target_chembl_id: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Get bioactivity data for a ChEMBL target.

    Args:
        target_chembl_id: ChEMBL target ID (e.g. "CHEMBL2093868")
        limit: Maximum number of activity records

    Returns:
        List of bioactivity dicts with molecule_chembl_id, canonical_smiles,
        standard_type, standard_value, standard_units, pchembl_value, assay_type.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(
                f"{BASE_URL}/activity.json",
                params={
                    "target_chembl_id": target_chembl_id,
                    "limit": limit,
                },
            )
            if resp.status_code == 404:
                logger.info("ChEMBL bioactivities for %s: not found", target_chembl_id)
                return []
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning("ChEMBL bioactivities for %s failed: %s", target_chembl_id, e)
            return []
        except httpx.TimeoutException:
            logger.warning("ChEMBL bioactivities for %s timed out", target_chembl_id)
            return []

    activities = []
    for act in data.get("activities", []):
        activities.append({
            "molecule_chembl_id": act.get("molecule_chembl_id", ""),
            "canonical_smiles": act.get("canonical_smiles", ""),
            "standard_type": act.get("standard_type", ""),
            "standard_value": act.get("standard_value"),
            "standard_units": act.get("standard_units", ""),
            "pchembl_value": act.get("pchembl_value"),
            "assay_type": act.get("assay_type", ""),
        })

    logger.info(
        "ChEMBL bioactivities for %s: %d records",
        target_chembl_id, len(activities),
    )
    return activities


async def get_compound(chembl_id: str) -> dict[str, Any]:
    """Get compound/molecule metadata from ChEMBL.

    Args:
        chembl_id: ChEMBL molecule ID (e.g. "CHEMBL25")

    Returns:
        Dict with chembl_id, pref_name, molecule_type, max_phase, molecular_weight.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(f"{BASE_URL}/molecule/{chembl_id}.json")
            if resp.status_code == 404:
                logger.warning("ChEMBL compound %s not found", chembl_id)
                return {"chembl_id": chembl_id, "error": "not_found"}
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning("ChEMBL compound %s failed: %s", chembl_id, e)
            return {"chembl_id": chembl_id, "error": str(e)}
        except httpx.TimeoutException:
            logger.warning("ChEMBL compound %s timed out", chembl_id)
            return {"chembl_id": chembl_id, "error": "timeout"}

    props = data.get("molecule_properties", {}) or {}
    return {
        "chembl_id": data.get("molecule_chembl_id", chembl_id),
        "pref_name": data.get("pref_name"),
        "molecule_type": data.get("molecule_type", ""),
        "max_phase": data.get("max_phase"),
        "molecular_weight": props.get("full_mwt"),
    }


async def search_sma_bioactivities(
    target_symbols: list[str],
    limit_per_target: int = 50,
) -> list[dict[str, Any]]:
    """Search ChEMBL bioactivities for multiple SMA-related gene targets.

    For each gene symbol, searches for the ChEMBL target and retrieves
    bioactivity data. Deduplicates by molecule_chembl_id + target.

    Args:
        target_symbols: Gene symbols to search (e.g. ["SMN1", "SMN2", "UBA1"])
        limit_per_target: Max bioactivities per target

    Returns:
        Combined, deduplicated list of bioactivity dicts (each with a
        'target_symbol' and 'target_chembl_id' field added).
    """
    all_activities: list[dict[str, Any]] = []
    seen: set[str] = set()

    for symbol in target_symbols:
        target = await search_target(symbol)
        if not target:
            continue

        activities = await get_bioactivities(
            target["target_chembl_id"],
            limit=limit_per_target,
        )

        for act in activities:
            # Deduplicate by molecule + target
            key = f"{act['molecule_chembl_id']}:{target['target_chembl_id']}"
            if key in seen:
                continue
            seen.add(key)

            act["target_symbol"] = symbol
            act["target_chembl_id"] = target["target_chembl_id"]
            all_activities.append(act)

        # Be polite to the API
        await asyncio.sleep(0.3)

    logger.info(
        "ChEMBL SMA search: %d unique bioactivities across %d targets",
        len(all_activities), len(target_symbols),
    )
    return all_activities
