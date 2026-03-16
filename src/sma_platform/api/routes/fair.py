"""FAIR Data Compliance API routes.

Provides endpoints for auditing the platform's compliance with FAIR
principles (Findable, Accessible, Interoperable, Reusable) and
generating machine-readable data dictionaries.
"""

from __future__ import annotations

from fastapi import APIRouter

from ...reasoning.fair_compliance import (
    audit_fair,
    generate_data_dictionary,
    get_fair_recommendations,
)

router = APIRouter()


@router.get("/fair/audit")
async def fair_audit():
    """Full FAIR compliance audit of the SMA Research Platform.

    Scores the platform across all 14 FAIR sub-principles (F1-F4, A1-A4,
    I1-I3, R1-R3), returning per-dimension scores, an overall score (0-1),
    a letter grade, and specific recommendations for improvement.
    """
    return await audit_fair()


@router.get("/fair/recommendations")
async def fair_recommendations():
    """Actionable recommendations to improve FAIR compliance.

    Returns prioritised recommendations with effort estimates, expected
    impact, and concrete implementation steps.
    """
    recommendations = await get_fair_recommendations()
    return {
        "count": len(recommendations),
        "recommendations": recommendations,
        "insight": (
            "The two highest-impact improvements are: "
            "(1) Add JSON-LD @context to API responses (raises Interoperability from 67% to 83%), "
            "and (2) Mint a DOI for the HuggingFace dataset (strengthens Findability persistence). "
            "Both are achievable with moderate effort."
        ),
    }


@router.get("/fair/data-dictionary")
async def fair_data_dictionary():
    """Auto-generated data dictionary for the platform database.

    Lists all tables, columns, types, constraints, and descriptions.
    Includes controlled vocabularies and external identifier mappings.
    Uses live database introspection when available, falls back to
    static schema definitions.
    """
    return await generate_data_dictionary()
