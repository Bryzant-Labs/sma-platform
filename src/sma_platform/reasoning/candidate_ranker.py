"""Integrated drug candidate ranking for SMA.

Combines data from:
1. Drug screening (Lipinski, BBB, CNS MPO, QED, PAINS)
2. ADMET prediction (absorption, distribution, metabolism, excretion, toxicity)
3. Drug repurposing (cross-disease + ChEMBL bioactivity)
4. Target scores (composite evidence-based scoring)

Produces a unified ranked list of the most promising drug candidates.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ..core.database import fetch, fetchrow

logger = logging.getLogger(__name__)


async def _get_screening_data() -> dict[str, dict]:
    """Load drug screening results from graph_edges."""
    try:
        from .drug_screener import compute_molecular_profile
    except ImportError:
        logger.warning("RDKit not available — skipping screening data")
        return {}

    rows = await fetch(
        """SELECT metadata FROM graph_edges
           WHERE relation LIKE 'compound_bioactivity:%'"""
    )

    compounds = {}
    for row in rows:
        meta = row["metadata"]
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except json.JSONDecodeError:
                continue
        cid = meta.get("molecule_chembl_id", "")
        smiles = meta.get("canonical_smiles", "")
        pchembl = meta.get("pchembl_value")
        if not cid or not smiles or cid in compounds:
            continue

        profile = compute_molecular_profile(smiles, cid)
        if profile is None:
            continue

        compounds[cid] = {
            "chembl_id": cid,
            "smiles": smiles,
            "mw": profile.mw,
            "logp": profile.logp,
            "qed": profile.qed,
            "cns_mpo": profile.cns_mpo,
            "bbb_permeable": profile.bbb_permeable,
            "lipinski_pass": profile.lipinski_pass,
            "pains_alert": profile.pains_alert,
            "pchembl": float(pchembl) if pchembl else None,
            "target": profile.target_symbol,
        }

    return compounds


async def _get_admet_data() -> dict[str, dict]:
    """Load ADMET predictions."""
    try:
        from .admet_predictor import predict_admet
        from dataclasses import asdict
    except ImportError:
        logger.warning("RDKit not available — skipping ADMET data")
        return {}

    rows = await fetch(
        """SELECT metadata FROM graph_edges
           WHERE relation LIKE 'compound_bioactivity:%'"""
    )

    admet_data = {}
    seen = set()
    for row in rows:
        meta = row["metadata"]
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except json.JSONDecodeError:
                continue
        cid = meta.get("molecule_chembl_id", "")
        smiles = meta.get("canonical_smiles", "")
        if not cid or not smiles or cid in seen:
            continue
        seen.add(cid)

        profile = predict_admet(smiles, cid)
        if profile is None:
            continue

        admet_data[cid] = {
            "admet_score": profile.admet_score,
            "bbb_score": profile.bbb_score,
            "hia_score": profile.hia_score,
            "herg_risk": profile.herg_risk,
            "ames_risk": profile.ames_risk,
            "hepatotox_risk": profile.hepatotox_risk,
            "flags": profile.flags,
        }

    return admet_data


async def _get_repurposing_data() -> dict[str, dict]:
    """Load repurposing candidates."""
    from .repurposing import find_repurposing_candidates

    result = await find_repurposing_candidates(top_n=100)
    candidates = {}
    for c in result.get("candidates", []):
        name = c["compound_name"].lower()
        candidates[name] = {
            "repurposing_score": c["repurposing_score"],
            "source": c.get("source", ""),
            "proposed_target": c.get("proposed_sma_target", ""),
            "trial_phase": c.get("trial_phase", ""),
            "rationale": c.get("rationale", ""),
        }
    return candidates


async def _get_target_scores() -> dict[str, float]:
    """Load target scores for weighting."""
    rows = await fetch(
        "SELECT symbol, composite_score FROM target_scores ORDER BY composite_score DESC"
    )
    return {dict(r)["symbol"]: float(dict(r)["composite_score"]) for r in rows}


def _compute_integrated_score(
    screening: dict | None,
    admet: dict | None,
    repurposing: dict | None,
    target_score: float,
) -> float:
    """Compute integrated drug candidate score (0-1).

    Weights:
    - Drug-likeness (QED + Lipinski): 15%
    - BBB/CNS access: 15%
    - ADMET safety: 20%
    - Potency (pChEMBL): 15%
    - Target relevance: 20%
    - Repurposing evidence: 15%
    """
    score = 0.0

    # Drug-likeness (15%)
    if screening:
        qed = screening.get("qed", 0)
        lipinski = 1.0 if screening.get("lipinski_pass") else 0.5
        pains = 0.0 if screening.get("pains_alert") else 1.0
        score += 0.15 * (qed * 0.5 + lipinski * 0.3 + pains * 0.2)

    # BBB/CNS access (15%)
    if screening:
        bbb = 1.0 if screening.get("bbb_permeable") else 0.3
        cns = min(1.0, screening.get("cns_mpo", 0) / 6.0)
        score += 0.15 * (bbb * 0.6 + cns * 0.4)

    # ADMET safety (20%)
    if admet:
        safety = admet.get("admet_score", 0.5)
        # Penalty for high-risk flags
        if admet.get("herg_risk") == "high":
            safety *= 0.7
        if admet.get("ames_risk") == "high":
            safety *= 0.7
        if admet.get("hepatotox_risk") == "high":
            safety *= 0.8
        score += 0.20 * safety

    # Potency (15%)
    if screening and screening.get("pchembl"):
        potency = min(1.0, screening["pchembl"] / 10.0)
        score += 0.15 * potency

    # Target relevance (20%)
    score += 0.20 * min(1.0, target_score)

    # Repurposing evidence (15%)
    if repurposing:
        score += 0.15 * repurposing.get("repurposing_score", 0)

    return round(min(1.0, score), 4)


async def rank_all_candidates(top_n: int = 50) -> dict[str, Any]:
    """Produce integrated ranking of all drug candidates.

    Returns top_n candidates with full profiles.
    """
    target_scores = await _get_target_scores()
    repurposing_data = await _get_repurposing_data()

    # Get screening + ADMET in one pass to avoid double DB reads
    try:
        from .drug_screener import compute_molecular_profile
        from .admet_predictor import predict_admet
        from dataclasses import asdict
    except ImportError:
        return {
            "error": "RDKit not installed",
            "total": 0,
            "candidates": [],
        }

    rows = await fetch(
        """SELECT ge.metadata, t.symbol
           FROM graph_edges ge
           JOIN targets t ON ge.dst_id = t.id
           WHERE ge.relation LIKE 'compound_bioactivity:%'"""
    )

    # Also load top compounds from molecule_screenings (capped at 500)
    mol_screen_rows = []
    try:
        mol_screen_rows = await fetch(
            """SELECT DISTINCT ON (chembl_id)
                      chembl_id, smiles, pchembl_value, target_symbol,
                      molecular_weight, alogp
               FROM molecule_screenings
               WHERE drug_likeness_pass = TRUE
                 AND smiles IS NOT NULL AND smiles != ''
                 AND chembl_id IS NOT NULL
               ORDER BY chembl_id, pchembl_value DESC NULLS LAST
               LIMIT 500"""
        )
        logger.info("Loaded %d compounds from molecule_screenings", len(mol_screen_rows))
    except Exception as exc:
        logger.warning("Could not load molecule_screenings: %s", exc)

    candidates = []
    seen = set()

    for row in rows:
        meta = row["metadata"]
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except json.JSONDecodeError:
                continue

        cid = meta.get("molecule_chembl_id", "")
        smiles = meta.get("canonical_smiles", "")
        pchembl = meta.get("pchembl_value")
        target_sym = row["symbol"]

        if not cid or not smiles or cid in seen:
            continue
        seen.add(cid)

        # Compute screening profile
        profile = compute_molecular_profile(smiles, cid)
        if profile is None:
            continue

        screening_data = {
            "chembl_id": cid,
            "smiles": smiles,
            "mw": round(profile.mw, 1),
            "logp": round(profile.logp, 2),
            "qed": round(profile.qed, 3),
            "cns_mpo": round(profile.cns_mpo, 1),
            "bbb_permeable": profile.bbb_permeable,
            "lipinski_pass": profile.lipinski_pass,
            "pains_alert": profile.pains_alert,
            "pchembl": float(pchembl) if pchembl else None,
            "target": target_sym,
        }

        # Compute ADMET
        admet_profile = predict_admet(smiles, cid)
        admet_data = None
        if admet_profile:
            admet_data = {
                "admet_score": admet_profile.admet_score,
                "bbb_score": admet_profile.bbb_score,
                "hia_score": admet_profile.hia_score,
                "herg_risk": admet_profile.herg_risk,
                "ames_risk": admet_profile.ames_risk,
                "hepatotox_risk": admet_profile.hepatotox_risk,
                "flags": admet_profile.flags,
            }

        # Check repurposing
        repurp = repurposing_data.get(cid.lower())

        # Compute integrated score
        t_score = target_scores.get(target_sym, 0)
        integrated = _compute_integrated_score(
            screening_data, admet_data, repurp, t_score
        )

        # Determine risk tier
        if integrated >= 0.6:
            tier = "A"
        elif integrated >= 0.4:
            tier = "B"
        else:
            tier = "C"

        candidates.append({
            "rank": 0,
            "chembl_id": cid,
            "smiles": smiles[:80],
            "target": target_sym,
            "integrated_score": integrated,
            "tier": tier,
            # Breakdown
            "qed": screening_data["qed"],
            "cns_mpo": screening_data["cns_mpo"],
            "bbb_permeable": screening_data["bbb_permeable"],
            "lipinski_pass": screening_data["lipinski_pass"],
            "pains_alert": screening_data["pains_alert"],
            "mw": screening_data["mw"],
            "logp": screening_data["logp"],
            "pchembl": screening_data["pchembl"],
            "admet_score": admet_data["admet_score"] if admet_data else None,
            "herg_risk": admet_data["herg_risk"] if admet_data else None,
            "ames_risk": admet_data["ames_risk"] if admet_data else None,
            "flags": admet_data["flags"] if admet_data else [],
            "target_score": round(t_score, 4),
            "repurposing_score": repurp["repurposing_score"] if repurp else None,
            "repurposing_rationale": repurp["rationale"][:150] if repurp else None,
        })

    # --- Add compounds from molecule_screenings (not already seen) ---
    for mrow in mol_screen_rows:
        md = dict(mrow)
        cid = md.get("chembl_id", "")
        smiles = md.get("smiles", "")
        target_sym = md.get("target_symbol", "")
        pchembl_val = md.get("pchembl_value")

        if not cid or not smiles or cid in seen:
            continue
        seen.add(cid)

        profile = compute_molecular_profile(smiles, cid)
        if profile is None:
            continue

        screening_data = {
            "chembl_id": cid,
            "smiles": smiles,
            "mw": round(profile.mw, 1),
            "logp": round(profile.logp, 2),
            "qed": round(profile.qed, 3),
            "cns_mpo": round(profile.cns_mpo, 1),
            "bbb_permeable": profile.bbb_permeable,
            "lipinski_pass": profile.lipinski_pass,
            "pains_alert": profile.pains_alert,
            "pchembl": float(pchembl_val) if pchembl_val else None,
            "target": target_sym,
        }

        admet_profile = predict_admet(smiles, cid)
        admet_data = None
        if admet_profile:
            admet_data = {
                "admet_score": admet_profile.admet_score,
                "bbb_score": admet_profile.bbb_score,
                "hia_score": admet_profile.hia_score,
                "herg_risk": admet_profile.herg_risk,
                "ames_risk": admet_profile.ames_risk,
                "hepatotox_risk": admet_profile.hepatotox_risk,
                "flags": admet_profile.flags,
            }

        repurp = repurposing_data.get(cid.lower())
        t_score = target_scores.get(target_sym, 0)
        integrated = _compute_integrated_score(
            screening_data, admet_data, repurp, t_score
        )

        if integrated >= 0.6:
            tier = "A"
        elif integrated >= 0.4:
            tier = "B"
        else:
            tier = "C"

        candidates.append({
            "rank": 0,
            "chembl_id": cid,
            "smiles": smiles[:80],
            "target": target_sym,
            "integrated_score": integrated,
            "tier": tier,
            "qed": screening_data["qed"],
            "cns_mpo": screening_data["cns_mpo"],
            "bbb_permeable": screening_data["bbb_permeable"],
            "lipinski_pass": screening_data["lipinski_pass"],
            "pains_alert": screening_data["pains_alert"],
            "mw": screening_data["mw"],
            "logp": screening_data["logp"],
            "pchembl": screening_data["pchembl"],
            "admet_score": admet_data["admet_score"] if admet_data else None,
            "herg_risk": admet_data["herg_risk"] if admet_data else None,
            "ames_risk": admet_data["ames_risk"] if admet_data else None,
            "flags": admet_data["flags"] if admet_data else [],
            "target_score": round(t_score, 4),
            "repurposing_score": repurp["repurposing_score"] if repurp else None,
            "repurposing_rationale": repurp["rationale"][:150] if repurp else None,
        })

    logger.info("Total candidates: %d (graph_edges + molecule_screenings)", len(candidates))

    # Sort by integrated score
    candidates.sort(key=lambda x: x["integrated_score"], reverse=True)

    # Assign ranks
    for i, c in enumerate(candidates[:top_n]):
        c["rank"] = i + 1

    # Summary
    by_tier = {"A": 0, "B": 0, "C": 0}
    by_target = {}
    for c in candidates[:top_n]:
        by_tier[c["tier"]] = by_tier.get(c["tier"], 0) + 1
        t = c["target"]
        by_target[t] = by_target.get(t, 0) + 1

    return {
        "total_screened": len(candidates),
        "top_n": top_n,
        "candidates": candidates[:top_n],
        "by_tier": by_tier,
        "by_target": by_target,
        "scoring_weights": {
            "drug_likeness": "15%",
            "bbb_cns_access": "15%",
            "admet_safety": "20%",
            "potency": "15%",
            "target_relevance": "20%",
            "repurposing_evidence": "15%",
        },
    }
