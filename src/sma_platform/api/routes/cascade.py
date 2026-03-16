"""Mutation-to-Function Cascade API — predict how variants flow through biology.

Endpoints:
- GET  /cascade/predict?variant=c.840C>T  — single variant cascade
- POST /cascade/batch                      — batch variants
- GET  /cascade/known                      — pre-computed cascades for known SMA variants
- GET  /cascade/compare?variant=c.840C>T   — WT vs mutant comparison
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ...reasoning.mutation_cascade import (
    batch_cascade,
    compare_wt_mutant,
    get_known_cascades,
    predict_cascade,
)

router = APIRouter()


@router.get("/cascade/predict")
async def cascade_predict(
    variant: str = Query(
        description="Variant notation: c.840C>T (coding DNA) or p.Gly287Arg / p.G287R (protein)",
        examples=["c.840C>T", "c.859G>C", "p.Gly287Arg", "p.Y272C"],
    ),
):
    """Predict the full mutation-to-function cascade for a single variant.

    Traces the variant through 5 steps:
    1. Splice impact (SpliceAI GPU scores or rule-based)
    2. Protein change (exon skip → truncation, or missense)
    3. ESM-2 embedding delta (GPU embeddings or domain estimate)
    4. Structure impact (AlphaFold missense or domain annotation)
    5. Functional integration (weighted score → classification)

    Example: /cascade/predict?variant=c.840C>T returns the cascade for
    THE SMA-causing mutation in SMN2.
    """
    return await predict_cascade(variant)


class BatchCascadeInput(BaseModel):
    variants: list[str]


@router.post("/cascade/batch")
async def cascade_batch(body: BatchCascadeInput):
    """Run the cascade for multiple variants in one call.

    Body: {"variants": ["c.840C>T", "c.859G>C", "p.Gly287Arg"]}
    Max 100 variants per request.
    """
    results = await batch_cascade(body.variants)
    return {"total": len(results), "cascades": results}


@router.get("/cascade/known")
async def cascade_known():
    """Return pre-computed cascades for well-known SMA variants.

    Includes the critical c.840C>T (THE cause of SMA), known pathogenic
    missense variants, modifier variants, and any high-impact variants
    identified from SpliceAI GPU analysis.
    """
    cascades = await get_known_cascades()
    return {"total": len(cascades), "cascades": cascades}


@router.get("/cascade/compare")
async def cascade_compare(
    variant: str = Query(
        description="Variant to compare against wild-type SMN1",
        examples=["c.840C>T", "p.Gly287Arg"],
    ),
):
    """Side-by-side comparison: wild-type SMN1 vs SMN2 with the variant.

    Shows exactly where the cascade diverges between the functional SMN1
    gene and the SMN2 copy carrying the specified variant. Identifies the
    primary point of divergence and quantifies the impact at each step.

    Example: /cascade/compare?variant=c.840C>T shows how the C-to-T change
    at exon 7 position 6 causes the entire downstream cascade to collapse.
    """
    return await compare_wt_mutant(variant)
