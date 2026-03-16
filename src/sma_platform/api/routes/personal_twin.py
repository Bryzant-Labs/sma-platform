# PRIVATE: Patient data — admin-only access, never expose publicly
"""Personal Digital Twin API routes — admin-only personalized SMA analysis.

All endpoints require the x-admin-key header. This is PRIVATE patient data
and must never be exposed to public access.

Endpoints:
- POST /twin/personal/profile    — create or update patient profile
- GET  /twin/personal/profile    — retrieve current profile
- GET  /twin/personal/analysis   — run full personal twin analysis
- GET  /twin/personal/trials     — relevant clinical trials
- GET  /twin/personal/optimize   — therapy optimization suggestions
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...reasoning.personal_twin import (
    create_or_update_profile,
    get_profile,
    get_relevant_trials,
    run_personal_twin,
    therapy_optimization,
)
from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ProfileInput(BaseModel):
    """Patient profile input — all fields optional except profile_name."""
    profile_name: str = Field(default="default", description="Profile identifier")
    sma_type: str | None = Field(
        default=None,
        description="SMA type: type0, type1, type2, type3, type4, presymptomatic, unknown",
    )
    smn2_copies: int | None = Field(
        default=None, ge=0, le=8,
        description="Number of SMN2 gene copies (0-8)",
    )
    age_years: int | None = Field(
        default=None, ge=0, le=150,
        description="Current age in years",
    )
    age_at_diagnosis_months: int | None = Field(
        default=None, ge=0,
        description="Age at SMA diagnosis in months",
    )
    current_therapies: list | None = Field(
        default=None,
        description="List of current therapies (strings or {name, dose, start_date} objects)",
    )
    therapy_history: list | None = Field(
        default=None,
        description="List of past therapies (strings or {name, dose, start_date, end_date} objects)",
    )
    functional_scores: dict | None = Field(
        default=None,
        description="Functional assessment scores, e.g. {HFMSE: 42, RULM: 28}",
    )
    biomarkers: dict | None = Field(
        default=None,
        description="Tracked biomarkers, e.g. {NfL: {value: 12.5, unit: 'pg/mL', date: '2026-01'}}",
    )
    genetic_modifiers: dict | None = Field(
        default=None,
        description="Modifier gene status, e.g. {PLS3: 'high', NCALD: 'low'}",
    )
    notes: str | None = Field(
        default=None,
        description="Free-text clinical notes",
    )


# ---------------------------------------------------------------------------
# Routes — all admin-protected
# ---------------------------------------------------------------------------

@router.post(
    "/twin/personal/profile",
    dependencies=[Depends(require_admin_key)],
    summary="Create or update patient profile",
    tags=["personal-twin"],
)
async def upsert_profile(body: ProfileInput):
    """Create or update a patient profile.

    Requires x-admin-key header. If a profile with the given name exists,
    it will be updated; otherwise a new one is created.
    """
    try:
        result = await create_or_update_profile(body.model_dump(exclude_none=True))
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Profile upsert failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save profile")


@router.get(
    "/twin/personal/profile",
    dependencies=[Depends(require_admin_key)],
    summary="Get patient profile",
    tags=["personal-twin"],
)
async def read_profile(
    profile_name: str = Query(default="default", description="Profile name to retrieve"),
):
    """Retrieve a patient profile by name.

    Requires x-admin-key header. Returns the full profile including all
    clinical data, therapies, biomarkers, and genetic modifiers.
    """
    result = await get_profile(profile_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get(
    "/twin/personal/analysis",
    dependencies=[Depends(require_admin_key)],
    summary="Run full personal Digital Twin analysis",
    tags=["personal-twin"],
)
async def personal_analysis(
    profile_name: str = Query(default="default", description="Profile to analyze"),
):
    """Run the full personalized Digital Twin analysis.

    Requires x-admin-key header. Integrates phenotype prediction, drug
    simulation, synergy scoring, trial filtering, biomarker recommendations,
    Bayesian evidence assessment, and experiment prioritization — all
    personalized to this patient's genetic and clinical profile.
    """
    result = await run_personal_twin(profile_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get(
    "/twin/personal/trials",
    dependencies=[Depends(require_admin_key)],
    summary="Get relevant clinical trials for patient",
    tags=["personal-twin"],
)
async def personal_trials(
    profile_name: str = Query(default="default", description="Profile to filter trials for"),
):
    """Filter clinical trials relevant to this patient.

    Requires x-admin-key header. Filters from all trials by SMA type,
    age, current therapies, trial status and phase. Results are scored
    and ranked by relevance.
    """
    trials = await get_relevant_trials(profile_name)
    return {
        "profile_name": profile_name,
        "total_relevant": len(trials),
        "trials": trials,
    }


@router.get(
    "/twin/personal/optimize",
    dependencies=[Depends(require_admin_key)],
    summary="Therapy optimization suggestions",
    tags=["personal-twin"],
)
async def personal_optimize(
    profile_name: str = Query(default="default", description="Profile to optimize"),
):
    """Suggest therapy optimizations for this patient.

    Requires x-admin-key header. Analyzes current therapies for modality
    gaps, simulates additions, ranks by marginal improvement, and provides
    biomarker monitoring recommendations.
    """
    result = await therapy_optimization(profile_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
