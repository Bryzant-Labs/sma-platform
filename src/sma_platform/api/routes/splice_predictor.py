"""Splice Variant Predictor API — predict effects of SMN2 sequence variants.

Endpoints:
- GET /splice/predict?variant=c.6T>C  — predict effect of a single variant
- GET /splice/known-variants           — list curated known variants
- GET /splice/elements                 — list key regulatory elements
- POST /splice/batch                   — predict effects for multiple variants
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ...reasoning.splice_predictor import (
    SPLICE_ELEMENTS,
    analyze_variant,
    get_known_variants,
    predict_splice_effect,
)

router = APIRouter()


@router.get("/splice/predict")
async def predict_variant(
    variant: str = Query(description="Variant notation: p.K42R (protein), c.6T>C (DNA), or exon7:6T>C"),
):
    """Predict the effect of an SMN2 sequence variant on splicing and protein function.

    Combines rule-based splice site analysis with ESM-2 protein language model
    predictions (via HuggingFace Inference API) to assess variant impact.

    Example queries:
    - /splice/predict?variant=c.6T>C (the critical SMN1/SMN2 difference)
    - /splice/predict?variant=p.K42R (protein-level variant)
    - /splice/predict?variant=exon7:25G>C (hnRNP A1 site disruption)
    """
    result = await analyze_variant(variant)
    return asdict(result)


@router.get("/splice/known-variants")
async def known_variants():
    """Return curated list of known SMN2 variants with clinical annotations."""
    variants = get_known_variants()
    return {"total": len(variants), "variants": variants}


@router.get("/splice/elements")
async def splice_elements():
    """Return key regulatory elements around SMN2 exon 7.

    These are the targets for ASO therapy (nusinersen targets ISS-N1)
    and small molecule therapy (risdiplam enhances SF2/ASF binding).
    """
    return {
        "elements": SPLICE_ELEMENTS,
        "context": {
            "exon7_length": 54,
            "key_position": "position 6 (C-to-T = SMN1 → SMN2 transition)",
            "nusinersen_target": "ISS-N1 in intron 7",
            "risdiplam_target": "5' splice site of exon 7",
        },
    }


class BatchVariantInput(BaseModel):
    variants: list[str]


@router.post("/splice/batch")
async def batch_predict(body: BatchVariantInput):
    """Predict effects for multiple variants in one call.

    Body: {"variants": ["c.6T>C", "p.K42R", "exon7:25G>C"]}
    """
    results = []
    for v in body.variants[:50]:  # Cap at 50
        result = await analyze_variant(v)
        results.append(asdict(result))
    return {"total": len(results), "predictions": results}
