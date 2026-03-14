"""ClinicalTrials.gov adapter using the v2 API.

Searches for SMA-related clinical trials and retrieves structured metadata.
API docs: https://clinicaltrials.gov/data-api/api
No API key required, but rate limits apply (max 5 req/sec).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://clinicaltrials.gov/api/v2"


async def search_trials(
    query: str = "spinal muscular atrophy",
    max_results: int = 100,
    status: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Search ClinicalTrials.gov for SMA trials.

    Args:
        query: Search query
        max_results: Maximum results to return
        status: Filter by status (e.g., ["RECRUITING", "COMPLETED"])

    Returns:
        List of trial dicts with structured metadata
    """
    params: dict[str, Any] = {
        "query.term": query,
        "pageSize": min(max_results, 100),
        "format": "json",
    }
    if status:
        params["filter.overallStatus"] = "|".join(status)

    trials = []
    async with httpx.AsyncClient(timeout=30) as client:
        next_token = None
        while len(trials) < max_results:
            if next_token:
                params["pageToken"] = next_token

            resp = await client.get(f"{BASE_URL}/studies", params=params)
            resp.raise_for_status()
            data = resp.json()

            for study in data.get("studies", []):
                proto = study.get("protocolSection", {})
                ident = proto.get("identificationModule", {})
                status_mod = proto.get("statusModule", {})
                design = proto.get("designModule", {})
                desc = proto.get("descriptionModule", {})
                arms = proto.get("armsInterventionsModule", {})
                sponsors = proto.get("sponsorCollaboratorsModule", {})
                contacts = proto.get("contactsLocationsModule", {})

                nct_id = ident.get("nctId", "")
                trials.append({
                    "nct_id": nct_id,
                    "title": ident.get("officialTitle") or ident.get("briefTitle", ""),
                    "status": status_mod.get("overallStatus", ""),
                    "phase": ", ".join(design.get("phases", [])),
                    "conditions": proto.get("conditionsModule", {}).get("conditions", []),
                    "interventions": arms.get("interventions", []),
                    "sponsor": sponsors.get("leadSponsor", {}).get("name", ""),
                    "start_date": status_mod.get("startDateStruct", {}).get("date"),
                    "completion_date": status_mod.get("completionDateStruct", {}).get("date"),
                    "enrollment": design.get("enrollmentInfo", {}).get("count"),
                    "brief_summary": desc.get("briefSummary", ""),
                    "url": f"https://clinicaltrials.gov/study/{nct_id}",
                })

            next_token = data.get("nextPageToken")
            if not next_token:
                break

    logger.info(f"Found {len(trials)} trials for '{query}'")
    return trials


async def fetch_all_sma_trials() -> list[dict[str, Any]]:
    """Fetch all SMA-related trials (active + completed)."""
    active = await search_trials(
        query="spinal muscular atrophy",
        max_results=500,
        status=["RECRUITING", "NOT_YET_RECRUITING", "ENROLLING_BY_INVITATION", "ACTIVE_NOT_RECRUITING"],
    )
    completed = await search_trials(
        query="spinal muscular atrophy",
        max_results=500,
        status=["COMPLETED"],
    )

    # Deduplicate by NCT ID
    seen = set()
    all_trials = []
    for trial in active + completed:
        nct = trial["nct_id"]
        if nct not in seen:
            seen.add(nct)
            all_trials.append(trial)

    logger.info(f"Total unique SMA trials: {len(all_trials)} ({len(active)} active, {len(completed)} completed)")
    return all_trials
