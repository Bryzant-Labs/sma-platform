"""SMN Locus Resolution API routes.

Explains why SMN2 copy number alone doesn't predict SMA phenotype —
covering the 5q13.2 locus architecture, phenotype modifiers, and
clinical genotype-phenotype discordance cases.
"""

from __future__ import annotations

from fastapi import APIRouter

from ...reasoning.smn_locus import (
    get_discordant_cases,
    get_locus_info,
    get_modifiers,
)

router = APIRouter()


@router.get("/locus/smn")
async def smn_locus_info():
    """Get comprehensive SMN locus information — why copy number alone doesn't predict phenotype.

    Returns locus architecture (SMN1 vs SMN2, the critical C>T difference),
    all known phenotype modifiers with their mechanisms, examples of
    genotype-phenotype discordance, and a summary key message.
    """
    return get_locus_info()


@router.get("/locus/modifiers")
async def phenotype_modifiers():
    """List known phenotype modifiers beyond SMN2 copy number.

    Covers SMN2 splicing efficiency, modifier genes (PLS3, NCALD, NAIP),
    gene conversion events, intragenic variants, epigenetics, and
    polygenic background effects — with contribution estimates and
    mechanistic explanations.
    """
    return {
        "count": len(get_modifiers()),
        "modifiers": get_modifiers(),
    }


@router.get("/locus/discordant")
async def discordant_cases():
    """Examples of genotype-phenotype discordance in SMA.

    Returns clinical scenarios where SMN2 copy number alone fails to
    predict disease severity — including asymptomatic carriers, discordant
    siblings, unexpectedly mild or severe cases, and their explanations.
    """
    cases = get_discordant_cases()
    return {
        "count": len(cases),
        "cases": cases,
    }
