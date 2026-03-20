"""Off-Target Splice Impact Prediction API routes.

Endpoints for predicting unintended splicing effects of ASO therapeutics
used in SMA treatment (nusinersen, risdiplam).
"""

from __future__ import annotations

from fastapi import APIRouter

from ...reasoning.splice_offtarget import (
    get_all_aso_safety,
    predict_iss_n1_offtargets,
    predict_offtargets,
)

router = APIRouter()


@router.get("/splice/safety")
async def aso_safety_profiles():
    """Get safety profiles for all known SMA ASO therapeutics.

    Returns a summary of off-target risks and clinical safety data
    for nusinersen (Spinraza) and risdiplam (Evrysdi).
    """
    profiles = get_all_aso_safety()
    return {"total": len(profiles), "profiles": profiles}


@router.get("/splice/offtarget/iss-n1")
async def predict_iss_n1():
    """Predict off-targets for ISS-N1-targeting ASOs (nusinersen class).

    Scans for transcriptome-wide sequence similarity to the ISS-N1
    binding site in SMN2 intron 7. Returns genes with partial matches
    and their assessed risk levels.
    """
    return predict_iss_n1_offtargets()


@router.get("/splice/offtarget/{aso_name}")
async def predict_aso_offtargets(aso_name: str):
    """Predict off-target splicing effects for an ASO therapeutic.

    Available ASOs: nusinersen, risdiplam.

    Returns known off-target genes, sequence similarity scores,
    risk assessments, and clinical safety summaries.
    """
    return predict_offtargets(aso_name)
