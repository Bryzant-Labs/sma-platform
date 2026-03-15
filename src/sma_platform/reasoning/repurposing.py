"""Drug repurposing candidate identification for SMA.

Cross-references drug outcomes, ChEMBL bioactivity, and target scores
to identify compounds from other diseases that may work for SMA targets.

Strategies:
1. Cross-disease hits: Drugs successful in ALS/DMD/SBMA targeting SMA pathways
2. Failed-but-active: Compounds that failed one target but are active on another
3. High-score compounds: ChEMBL compounds targeting top-scored SMA targets
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ..core.database import fetch, fetchrow

logger = logging.getLogger(__name__)

# SMA-related diseases for cross-disease repurposing
RELATED_DISEASES = {
    "ALS", "amyotrophic lateral sclerosis",
    "DMD", "duchenne", "muscular dystrophy",
    "SBMA", "kennedy disease", "spinal bulbar",
    "myasthenia", "CMT", "charcot-marie-tooth",
    "friedreich", "ataxia", "motor neuron",
}

# Drug → target mapping for known compounds
KNOWN_DRUG_TARGETS = {
    "nusinersen": "SMN2", "risdiplam": "SMN2", "branaplam": "SMN2",
    "onasemnogene": "SMN1", "zolgensma": "SMN1",
    "tofersen": "SOD1", "edaravone": "oxidative_stress",
    "riluzole": "glutamate", "eteplirsen": "dystrophin",
}


async def _get_target_scores() -> dict[str, float]:
    """Load current target scores."""
    rows = await fetch(
        "SELECT symbol, composite_score FROM target_scores ORDER BY composite_score DESC"
    )
    return {dict(r)["symbol"]: float(dict(r)["composite_score"]) for r in rows}


async def _get_target_ids() -> dict[str, str]:
    """Load target symbol → ID mapping."""
    rows = await fetch("SELECT id, symbol FROM targets")
    return {dict(r)["symbol"]: str(dict(r)["id"]) for r in rows}


async def find_cross_disease_candidates() -> list[dict]:
    """Find drugs successful in related diseases that target SMA pathways."""
    candidates = []

    # Get successful drug outcomes from related diseases
    rows = await fetch(
        """SELECT compound_name, target, mechanism, outcome, model_system,
                  key_finding, confidence, trial_phase
           FROM drug_outcomes
           WHERE outcome IN ('success', 'partial_success')
           ORDER BY confidence DESC"""
    )

    target_scores = await _get_target_scores()
    target_ids = await _get_target_ids()

    for row in rows:
        r = dict(row)
        compound = r.get("compound_name", "")
        target = (r.get("target") or "").upper()
        model = (r.get("model_system") or "").lower()
        finding = r.get("key_finding", "")

        # Check if this is a cross-disease compound
        is_cross = any(d.lower() in model for d in RELATED_DISEASES)
        if not is_cross and compound.lower() not in KNOWN_DRUG_TARGETS:
            # Also check if the target overlaps with an SMA target
            if target not in target_ids:
                continue

        # Calculate repurposing score
        target_score = target_scores.get(target, 0)
        confidence = float(r.get("confidence", 0.5))
        phase_bonus = {"approved": 0.3, "phase3": 0.25, "phase2": 0.2,
                       "phase1": 0.1, "preclinical": 0.05}.get(
                           r.get("trial_phase", ""), 0)

        score = (target_score * 0.4 + confidence * 0.3 + phase_bonus + 0.1)
        score = min(1.0, score)

        if score < 0.2:
            continue

        rationale = f"{compound} shows {r.get('outcome', 'activity')} "
        if target:
            rationale += f"on {target} "
        rationale += f"({r.get('trial_phase', 'unknown phase')}). "
        if finding:
            rationale += finding[:150]

        candidates.append({
            "compound_name": compound,
            "original_indication": model or "SMA-related",
            "proposed_sma_target": target if target in target_ids else "multiple",
            "repurposing_score": round(score, 3),
            "rationale": rationale,
            "evidence_sources": 1,
            "source": "cross_disease",
            "trial_phase": r.get("trial_phase"),
            "outcome": r.get("outcome"),
        })

    return candidates


async def find_chembl_candidates() -> list[dict]:
    """Find ChEMBL compounds with high bioactivity on top-scored targets."""
    target_scores = await _get_target_scores()
    target_ids = await _get_target_ids()

    rows = await fetch(
        """SELECT ge.metadata, t.symbol
           FROM graph_edges ge
           JOIN targets t ON ge.dst_id = t.id
           WHERE ge.relation LIKE 'compound_bioactivity:%'"""
    )

    seen = set()
    candidates = []

    for row in rows:
        meta = row["metadata"]
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except json.JSONDecodeError:
                continue

        cid = meta.get("molecule_chembl_id", "")
        pchembl = meta.get("pchembl_value")
        smiles = meta.get("canonical_smiles", "")
        target_sym = row["symbol"]

        if not cid or cid in seen or not pchembl:
            continue

        try:
            pchembl = float(pchembl)
        except (ValueError, TypeError):
            continue

        if pchembl < 6.0:  # Only potent compounds (< 1µM)
            continue

        seen.add(cid)
        target_score = target_scores.get(target_sym, 0)
        potency_norm = min(1.0, pchembl / 10.0)
        score = target_score * 0.5 + potency_norm * 0.5

        if score < 0.3:
            continue

        candidates.append({
            "compound_name": cid,
            "original_indication": f"ChEMBL bioactivity on {target_sym}",
            "proposed_sma_target": target_sym,
            "repurposing_score": round(score, 3),
            "rationale": (
                f"{cid} has pChEMBL={pchembl:.1f} on {target_sym} "
                f"(target score: {target_score:.3f}). "
                f"SMILES: {smiles[:60]}{'...' if len(smiles) > 60 else ''}"
            ),
            "evidence_sources": 1,
            "source": "chembl_bioactivity",
            "trial_phase": "preclinical",
            "pchembl": pchembl,
        })

    return candidates


async def find_repurposing_candidates(top_n: int = 30) -> dict[str, Any]:
    """Find and rank all repurposing candidates."""
    # Collect from all strategies
    cross_disease = await find_cross_disease_candidates()
    chembl = await find_chembl_candidates()

    # Merge and deduplicate by compound name
    all_candidates = {}
    for c in cross_disease + chembl:
        name = c["compound_name"].lower()
        if name not in all_candidates or c["repurposing_score"] > all_candidates[name]["repurposing_score"]:
            all_candidates[name] = c

    # Sort by score
    ranked = sorted(all_candidates.values(), key=lambda x: x["repurposing_score"], reverse=True)

    # Add ranks
    for i, c in enumerate(ranked[:top_n]):
        c["rank"] = i + 1

    # Summary stats
    by_target = {}
    for c in ranked[:top_n]:
        t = c.get("proposed_sma_target", "unknown")
        by_target[t] = by_target.get(t, 0) + 1

    return {
        "total": len(ranked),
        "candidates": ranked[:top_n],
        "by_target": by_target,
        "cross_disease_hits": len(cross_disease),
        "chembl_hits": len(chembl),
    }
