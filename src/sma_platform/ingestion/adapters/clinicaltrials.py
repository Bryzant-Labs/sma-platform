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


# ---------------------------------------------------------------------------
# Results fetching
# ---------------------------------------------------------------------------

async def fetch_trial_results(nct_id: str) -> dict[str, Any] | None:
    """Fetch results for a single completed trial from ClinicalTrials.gov v2 API.

    Requests the full study record and extracts the ``resultsSection`` if
    present.  Returns ``None`` when the trial has no results posted yet.

    Args:
        nct_id: NCT identifier, e.g. ``"NCT02193074"``

    Returns:
        Structured results dict ready for LLM claim extraction, or ``None``.
    """
    nct_id = nct_id.strip().upper()
    url = f"{BASE_URL}/studies/{nct_id}"

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, params={"format": "json"})
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                logger.debug("Trial %s not found on ClinicalTrials.gov", nct_id)
                return None
            logger.error("HTTP error fetching results for %s: %s", nct_id, exc)
            return None
        except httpx.RequestError as exc:
            logger.error("Request error fetching results for %s: %s", nct_id, exc)
            return None

    data = resp.json()
    results_section = data.get("resultsSection")
    if not results_section:
        logger.debug("No resultsSection for %s — results not yet posted", nct_id)
        return None

    proto = data.get("protocolSection", {})
    ident = proto.get("identificationModule", {})
    status_mod = proto.get("statusModule", {})
    design = proto.get("designModule", {})

    outcome_measures = parse_outcome_measures(results_section)
    adverse_events = parse_adverse_events(results_section)
    participant_flow = _parse_participant_flow(results_section)
    baseline = _parse_baseline_characteristics(results_section)

    result = {
        "nct_id": nct_id,
        "title": ident.get("officialTitle") or ident.get("briefTitle", ""),
        "status": status_mod.get("overallStatus", ""),
        "phase": ", ".join(design.get("phases", [])),
        "results_first_posted": status_mod.get("resultsFirstPostDateStruct", {}).get("date"),
        "last_update_posted": status_mod.get("lastUpdatePostDateStruct", {}).get("date"),
        "outcome_measures": outcome_measures,
        "adverse_events": adverse_events,
        "participant_flow": participant_flow,
        "baseline_characteristics": baseline,
        "url": f"https://clinicaltrials.gov/study/{nct_id}",
        # Flat text summary for LLM ingestion
        "results_summary": _build_results_summary(
            nct_id=nct_id,
            title=ident.get("officialTitle") or ident.get("briefTitle", ""),
            outcome_measures=outcome_measures,
            adverse_events=adverse_events,
            participant_flow=participant_flow,
        ),
    }

    logger.info(
        "Fetched results for %s: %d outcomes, %d AE groups",
        nct_id,
        len(outcome_measures),
        len(adverse_events),
    )
    return result


async def fetch_all_sma_trial_results() -> list[dict[str, Any]]:
    """Fetch results for all completed SMA trials that have results posted.

    Searches for completed SMA trials, then retrieves results for each one
    that has a ``resultsSection``.  Trials without posted results are silently
    skipped.

    Returns:
        List of structured results dicts (one per trial with results).
    """
    # Use the v2 search with hasResults filter to avoid unnecessary per-trial
    # requests.  ``filter.resultsRange`` is not available in v2; instead we
    # rely on the fact that resultsSection is absent from studies without results.
    completed = await search_trials(
        query="spinal muscular atrophy",
        max_results=500,
        status=["COMPLETED"],
    )

    logger.info(
        "Fetching results for %d completed SMA trials…", len(completed)
    )

    results: list[dict[str, Any]] = []
    for trial in completed:
        nct_id = trial.get("nct_id", "")
        if not nct_id:
            continue
        trial_results = await fetch_trial_results(nct_id)
        if trial_results is not None:
            results.append(trial_results)

    logger.info(
        "Found results for %d / %d completed SMA trials",
        len(results),
        len(completed),
    )
    return results


def parse_outcome_measures(results_section: dict) -> list[dict]:
    """Parse primary and secondary outcome measures from ``resultsSection``.

    Each returned dict contains the measure title, type (primary/secondary),
    time frame, unit, groups, and a flat ``measurements`` list suitable for
    LLM summarisation.

    Args:
        results_section: The ``resultsSection`` dict from the v2 API response.

    Returns:
        List of outcome measure dicts.
    """
    module = results_section.get("outcomeMeasuresModule", {})
    raw_measures: list[dict] = module.get("outcomeMeasures", [])

    parsed: list[dict] = []
    for measure in raw_measures:
        measure_type = measure.get("type", "").upper()  # "PRIMARY" / "SECONDARY" / "OTHER_PRE_SPECIFIED"
        title = measure.get("title", "")
        description = measure.get("description", "")
        time_frame = measure.get("timeFrame", "")
        units = measure.get("unitOfMeasure", "")
        reporting_status = measure.get("reportingStatus", "")

        # Groups (arms/cohorts) for this measure
        groups: list[dict] = []
        for g in measure.get("groups", []):
            groups.append({
                "id": g.get("id", ""),
                "title": g.get("title", ""),
                "description": g.get("description", ""),
            })

        # Flatten classes → categories → measurements into a readable list
        measurements: list[dict] = []
        for cls in measure.get("classes", []):
            class_title = cls.get("title", "")
            for cat in cls.get("categories", []):
                cat_title = cat.get("title", "")
                for meas in cat.get("measurements", []):
                    entry: dict[str, Any] = {
                        "group_id": meas.get("groupId", ""),
                        "value": meas.get("value"),
                        "spread": meas.get("spread"),
                        "lower_limit": meas.get("lowerLimit"),
                        "upper_limit": meas.get("upperLimit"),
                    }
                    if class_title:
                        entry["class"] = class_title
                    if cat_title:
                        entry["category"] = cat_title
                    measurements.append(entry)

        # Denominator (participant counts per group)
        denoms: list[dict] = []
        for denom in measure.get("denoms", []):
            for cnt in denom.get("counts", []):
                denoms.append({
                    "group_id": cnt.get("groupId", ""),
                    "count": cnt.get("value"),
                    "units": denom.get("units", "Participants"),
                })

        # Statistical analyses (p-values, CIs)
        analyses: list[dict] = []
        for analysis in measure.get("analyses", []):
            analyses.append({
                "groups": analysis.get("groupIds", []),
                "method": analysis.get("statisticalMethod", ""),
                "p_value": analysis.get("pValue"),
                "p_value_comment": analysis.get("pValueComment", ""),
                "ci_pct": analysis.get("ciPct"),
                "ci_lower": analysis.get("ciLowerLimit"),
                "ci_upper": analysis.get("ciUpperLimit"),
                "estimate": analysis.get("estimateComment", ""),
                "non_inferiority": analysis.get("nonInferiorityType", ""),
            })

        parsed.append({
            "type": measure_type,
            "title": title,
            "description": description,
            "time_frame": time_frame,
            "units": units,
            "reporting_status": reporting_status,
            "groups": groups,
            "denoms": denoms,
            "measurements": measurements,
            "analyses": analyses,
        })

    return parsed


def parse_adverse_events(results_section: dict) -> list[dict]:
    """Parse adverse event data from ``resultsSection``.

    Extracts both serious and other (non-serious) adverse events, with
    participant counts per event and per group.

    Args:
        results_section: The ``resultsSection`` dict from the v2 API response.

    Returns:
        List of adverse event dicts, each keyed by group/arm.
    """
    module = results_section.get("adverseEventsModule", {})

    frequency_threshold = module.get("frequencyThreshold", "")
    time_frame = module.get("timeFrame", "")
    description = module.get("description", "")

    # Group definitions (arms/cohorts)
    event_groups: list[dict] = []
    for g in module.get("eventGroups", []):
        event_groups.append({
            "id": g.get("id", ""),
            "title": g.get("title", ""),
            "description": g.get("description", ""),
            "deaths_num_affected": g.get("deathsNumAffected"),
            "deaths_num_at_risk": g.get("deathsNumAtRisk"),
            "serious_num_affected": g.get("seriousNumAffected"),
            "serious_num_at_risk": g.get("seriousNumAtRisk"),
            "other_num_affected": g.get("otherNumAffected"),
            "other_num_at_risk": g.get("otherNumAtRisk"),
        })

    def _parse_events(raw_list: list[dict], event_category: str) -> list[dict]:
        events: list[dict] = []
        for event in raw_list:
            stats: list[dict] = []
            for stat in event.get("stats", []):
                stats.append({
                    "group_id": stat.get("groupId", ""),
                    "num_events": stat.get("numEvents"),
                    "num_affected": stat.get("numAffected"),
                    "num_at_risk": stat.get("numAtRisk"),
                })
            events.append({
                "category": event_category,
                "term": event.get("term", ""),
                "organ_system": event.get("organSystem", ""),
                "source_vocabulary": event.get("sourceVocabulary", ""),
                "assessment_type": event.get("assessmentType", ""),
                "notes": event.get("notes", ""),
                "stats": stats,
            })
        return events

    serious = _parse_events(module.get("seriousEvents", []), "serious")
    other = _parse_events(module.get("otherEvents", []), "other")

    return [
        {
            "frequency_threshold": frequency_threshold,
            "time_frame": time_frame,
            "description": description,
            "event_groups": event_groups,
            "serious_events": serious,
            "other_events": other,
            "serious_event_count": len(serious),
            "other_event_count": len(other),
        }
    ]


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _parse_participant_flow(results_section: dict) -> dict:
    """Parse participant flow (enrolment, completion, dropout) from resultsSection."""
    module = results_section.get("participantFlowModule", {})
    if not module:
        return {}

    groups: list[dict] = []
    for g in module.get("groups", []):
        groups.append({
            "id": g.get("id", ""),
            "title": g.get("title", ""),
            "description": g.get("description", ""),
        })

    periods: list[dict] = []
    for period in module.get("periods", []):
        milestones: list[dict] = []
        for ms in period.get("milestones", []):
            counts: list[dict] = []
            for cnt in ms.get("achievements", []):
                counts.append({
                    "group_id": cnt.get("groupId", ""),
                    "num_subjects": cnt.get("numSubjects"),
                    "comment": cnt.get("comment", ""),
                })
            milestones.append({
                "type": ms.get("type", ""),
                "comment": ms.get("comment", ""),
                "counts": counts,
            })

        dropouts: list[dict] = []
        for drop in period.get("dropWithdraws", []):
            reasons: list[dict] = []
            for cnt in drop.get("reasons", []):
                reasons.append({
                    "group_id": cnt.get("groupId", ""),
                    "num_subjects": cnt.get("numSubjects"),
                })
            dropouts.append({
                "type": drop.get("type", ""),
                "reasons": reasons,
            })

        periods.append({
            "title": period.get("title", ""),
            "milestones": milestones,
            "dropouts": dropouts,
        })

    return {
        "pre_assignment_details": module.get("preAssignmentDetails", ""),
        "recruitment_details": module.get("recruitmentDetails", ""),
        "groups": groups,
        "periods": periods,
    }


def _parse_baseline_characteristics(results_section: dict) -> dict:
    """Parse baseline demographics and characteristics from resultsSection."""
    module = results_section.get("baselineCharacteristicsModule", {})
    if not module:
        return {}

    groups: list[dict] = []
    for g in module.get("groups", []):
        groups.append({
            "id": g.get("id", ""),
            "title": g.get("title", ""),
            "description": g.get("description", ""),
        })

    denoms: list[dict] = []
    for denom in module.get("denoms", []):
        for cnt in denom.get("counts", []):
            denoms.append({
                "group_id": cnt.get("groupId", ""),
                "count": cnt.get("value"),
                "units": denom.get("units", "Participants"),
            })

    measures: list[dict] = []
    for measure in module.get("measures", []):
        flat_values: list[dict] = []
        for cls in measure.get("classes", []):
            for cat in cls.get("categories", []):
                for meas in cat.get("measurements", []):
                    entry: dict[str, Any] = {
                        "group_id": meas.get("groupId", ""),
                        "value": meas.get("value"),
                        "spread": meas.get("spread"),
                        "lower_limit": meas.get("lowerLimit"),
                        "upper_limit": meas.get("upperLimit"),
                    }
                    if cls.get("title"):
                        entry["class"] = cls["title"]
                    if cat.get("title"):
                        entry["category"] = cat["title"]
                    flat_values.append(entry)
        measures.append({
            "title": measure.get("title", ""),
            "description": measure.get("description", ""),
            "param_type": measure.get("paramType", ""),
            "dispersion_type": measure.get("dispersionType", ""),
            "unit": measure.get("unitOfMeasure", ""),
            "values": flat_values,
        })

    return {
        "population_description": module.get("populationDescription", ""),
        "groups": groups,
        "denoms": denoms,
        "measures": measures,
    }


def _build_results_summary(
    *,
    nct_id: str,
    title: str,
    outcome_measures: list[dict],
    adverse_events: list[dict],
    participant_flow: dict,
) -> str:
    """Build a plain-text summary of trial results for LLM ingestion.

    The summary is intentionally dense so that ``claim_extractor`` can treat
    it the same way it treats paper abstracts.

    Args:
        nct_id: NCT identifier.
        title: Trial title.
        outcome_measures: Parsed outcome measures (from ``parse_outcome_measures``).
        adverse_events: Parsed AE block (from ``parse_adverse_events``).
        participant_flow: Parsed participant flow (from ``_parse_participant_flow``).

    Returns:
        Multi-line plain-text string summarising results.
    """
    lines: list[str] = [f"Clinical trial results for {nct_id}: {title}"]

    # Participant flow summary
    if participant_flow.get("periods"):
        first_period = participant_flow["periods"][0]
        for ms in first_period.get("milestones", []):
            if ms.get("type", "").upper() == "STARTED":
                total = sum(
                    int(c.get("num_subjects") or 0) for c in ms.get("counts", [])
                )
                if total:
                    lines.append(f"Participants enrolled: {total}.")
                break

    # Primary outcomes
    primary = [m for m in outcome_measures if m.get("type") == "PRIMARY"]
    if primary:
        lines.append(f"Primary outcomes ({len(primary)}):")
        for m in primary:
            summary_parts = [f"  - {m['title']}"]
            if m.get("time_frame"):
                summary_parts.append(f"(time frame: {m['time_frame']})")
            if m.get("units"):
                summary_parts.append(f"[{m['units']}]")
            lines.append(" ".join(summary_parts) + ".")
            # Include statistical analyses if present
            for analysis in m.get("analyses", []):
                parts: list[str] = []
                if analysis.get("p_value") is not None:
                    parts.append(f"p={analysis['p_value']}")
                if analysis.get("ci_lower") is not None and analysis.get("ci_upper") is not None:
                    pct = analysis.get("ci_pct", "95")
                    parts.append(f"{pct}% CI [{analysis['ci_lower']}, {analysis['ci_upper']}]")
                if analysis.get("method"):
                    parts.append(f"method: {analysis['method']}")
                if parts:
                    lines.append(f"    Statistical analysis: {'; '.join(parts)}.")

    # Secondary outcomes (abbreviated)
    secondary = [m for m in outcome_measures if m.get("type") == "SECONDARY"]
    if secondary:
        lines.append(f"Secondary outcomes ({len(secondary)}): " + "; ".join(
            m["title"] for m in secondary[:5]
        ) + ("…" if len(secondary) > 5 else "") + ".")

    # Adverse events summary
    if adverse_events:
        ae_block = adverse_events[0]
        serious_count = ae_block.get("serious_event_count", 0)
        other_count = ae_block.get("other_event_count", 0)
        lines.append(
            f"Adverse events: {serious_count} serious event type(s), "
            f"{other_count} other event type(s) reported."
        )
        if ae_block.get("time_frame"):
            lines.append(f"Adverse event time frame: {ae_block['time_frame']}.")
        # Top 3 serious events by term
        top_serious = ae_block.get("serious_events", [])[:3]
        if top_serious:
            terms = ", ".join(e["term"] for e in top_serious if e.get("term"))
            if terms:
                lines.append(f"Notable serious adverse events: {terms}.")

    return "\n".join(lines)
