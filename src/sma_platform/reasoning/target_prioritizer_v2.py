"""M5 Target Prioritization Engine v2 — multi-criteria decision engine.

Ranks all SMA targets by combining ALL available data sources:

1. Evidence convergence (25%)  — 5-dimension convergence score (volume, independence, methods, temporal, replication)
2. Druggability (20%)          — DiffDock screening hits + compound bioactivity edges
3. Structural uniqueness (15%) — ESM-2 embedding-based uniqueness (lower avg cosine = more unique)
4. Clinical validation (15%)   — drug_outcomes track record (compounds tested, success rate)
5. Conservation (10%)          — cross_species_targets ortholog conservation
6. Novelty (15%)               — how underexplored / emerging the target is

Distinct from target_prioritizer.py (v1), this module integrates:
- Convergence engine scores (computed or from convergence_scores table)
- DiffDock GPU screening results
- ESM-2 structural similarity data
- Drug outcome calibration data
- Cross-species conservation scores
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

try:
    import numpy as np
except ImportError:
    np = None  # ESM-2 similarity scoring will be unavailable

from ..core.database import fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dimension weights (must sum to 1.0)
# ---------------------------------------------------------------------------

WEIGHTS: dict[str, float] = {
    "evidence": 0.25,
    "druggability": 0.20,
    "uniqueness": 0.15,
    "clinical": 0.15,
    "conservation": 0.10,
    "novelty": 0.15,
}

# Path to ESM-2 results (on GPU server or local dev)
_ESM2_RESULTS_DIR = Path(
    os.environ.get(
        "ESM2_RESULTS_DIR",
        "/home/bryzant/sma-platform/gpu/results/esm2",
    )
)
# Fallback path for local dev (Windows/WSL)
_ESM2_RESULTS_DIR_LOCAL = Path(__file__).resolve().parents[4] / "gpu" / "results" / "esm2"

# DiffDock multi-results file
_DIFFDOCK_RESULTS = Path(
    os.environ.get(
        "DIFFDOCK_RESULTS",
        "/home/bryzant/sma-platform/gpu/results/diffdock_multi_results.json",
    )
)
_DIFFDOCK_RESULTS_LOCAL = Path(__file__).resolve().parents[4] / "gpu" / "results" / "diffdock_multi_results.json"


def _clamp(value: float) -> float:
    """Clamp to [0.0, 1.0] and round to 4 decimals."""
    return round(max(0.0, min(1.0, value)), 4)


# ---------------------------------------------------------------------------
# Data loaders (cached per scoring run)
# ---------------------------------------------------------------------------


def _load_esm2_metadata() -> dict[str, dict[str, Any]]:
    """Load ESM-2 metadata.json with embedding norms and sequence lengths."""
    for path in [_ESM2_RESULTS_DIR / "metadata.json", _ESM2_RESULTS_DIR_LOCAL / "metadata.json"]:
        if path.exists():
            try:
                with open(path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Failed to load ESM-2 metadata from %s: %s", path, exc)
    logger.info("ESM-2 metadata not found — structural uniqueness will be scored at 0")
    return {}


def _load_esm2_embeddings() -> dict[str, Any]:
    """Load ESM-2 .npy embeddings and compute pairwise cosine similarity."""
    if np is None:
        logger.info('numpy not available — ESM-2 similarity scoring disabled')
        return {"metadata": {}, "similarities": {}, "avg_similarity": {}}

    metadata = _load_esm2_metadata()
    if not metadata:
        return {"metadata": {}, "similarities": {}, "avg_similarity": {}}

    embeddings = {}
    for symbol in metadata:
        for base_dir in [_ESM2_RESULTS_DIR, _ESM2_RESULTS_DIR_LOCAL]:
            npy_path = base_dir / f"{symbol}.npy"
            if npy_path.exists():
                try:
                    embeddings[symbol] = np.load(str(npy_path))
                except Exception as exc:
                    logger.warning("Failed to load embedding for %s: %s", symbol, exc)
                break

    if len(embeddings) < 2:
        return {"metadata": metadata, "similarities": {}, "avg_similarity": {}}

    # Compute pairwise cosine similarities
    symbols = sorted(embeddings.keys())
    similarities = {}
    for i, s1 in enumerate(symbols):
        for s2 in symbols[i + 1:]:
            e1 = embeddings[s1].flatten()
            e2 = embeddings[s2].flatten()
            norm1 = np.linalg.norm(e1)
            norm2 = np.linalg.norm(e2)
            if norm1 > 0 and norm2 > 0:
                cosine = float(np.dot(e1, e2) / (norm1 * norm2))
            else:
                cosine = 0.0
            similarities[(s1, s2)] = round(cosine, 4)
            similarities[(s2, s1)] = round(cosine, 4)

    # Average similarity per protein (lower = more unique)
    avg_similarity = {}
    for sym in symbols:
        sims = [similarities.get((sym, other), 0.0) for other in symbols if other != sym]
        avg_similarity[sym] = round(sum(sims) / len(sims), 4) if sims else 0.0

    return {
        "metadata": metadata,
        "similarities": {f"{k[0]}-{k[1]}": v for k, v in similarities.items()},
        "avg_similarity": avg_similarity,
    }


def _load_diffdock_results() -> list[dict[str, Any]]:
    """Load DiffDock multi-target screening results."""
    for path in [_DIFFDOCK_RESULTS, _DIFFDOCK_RESULTS_LOCAL]:
        if path.exists():
            try:
                with open(path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Failed to load DiffDock results from %s: %s", path, exc)
    logger.info("DiffDock results not found — druggability from file will be 0")
    return []


# ---------------------------------------------------------------------------
# Per-dimension scoring
# ---------------------------------------------------------------------------


async def _score_evidence(target_id: str, symbol: str, convergence_cache: dict) -> tuple[float, dict[str, Any]]:
    """Dimension 1: Evidence convergence score from convergence_scores table.

    Uses pre-computed convergence scores (5 dimensions: volume, lab independence,
    method diversity, temporal trend, replication).
    """
    # Try cache first (from batch query)
    if symbol in convergence_cache:
        cached = convergence_cache[symbol]
        return cached["composite_score"], cached

    # Fallback: query convergence_scores table directly
    row = await fetchrow(
        """SELECT composite_score, volume, lab_independence, method_diversity,
                  temporal_trend, replication, confidence_level, claim_count, source_count
           FROM convergence_scores
           WHERE target_id = $1
           ORDER BY computed_at DESC LIMIT 1""",
        target_id,
    )

    if not row:
        # Try by target label
        row = await fetchrow(
            """SELECT composite_score, volume, lab_independence, method_diversity,
                      temporal_trend, replication, confidence_level, claim_count, source_count
               FROM convergence_scores
               WHERE UPPER(target_label) = $1
               ORDER BY computed_at DESC LIMIT 1""",
            symbol.upper(),
        )

    if row:
        r = dict(row)
        score = _clamp(float(r.get("composite_score", 0) or 0))
        detail = {
            "composite_score": score,
            "volume": float(r.get("volume", 0) or 0),
            "lab_independence": float(r.get("lab_independence", 0) or 0),
            "method_diversity": float(r.get("method_diversity", 0) or 0),
            "temporal_trend": float(r.get("temporal_trend", 0) or 0),
            "replication": float(r.get("replication", 0) or 0),
            "confidence_level": r.get("confidence_level", "low"),
            "claim_count": int(r.get("claim_count", 0) or 0),
            "source_count": int(r.get("source_count", 0) or 0),
        }
        return score, detail

    # No convergence data — fallback to claim count ratio
    claim_count = int(await fetchval(
        "SELECT COUNT(*) FROM claims WHERE subject_id = $1", target_id
    ) or 0)
    max_claims = int(await fetchval(
        "SELECT MAX(cnt) FROM (SELECT COUNT(*) AS cnt FROM claims WHERE subject_id IS NOT NULL GROUP BY subject_id) sub"
    ) or 1)
    score = _clamp(claim_count / max_claims) if max_claims > 0 else 0.0
    return score, {"composite_score": score, "claim_count": claim_count, "source": "fallback_claim_count"}


async def _score_druggability(
    target_id: str,
    symbol: str,
    diffdock_by_target: dict[str, list],
    screening_counts: dict[str, int],
    drug_claim_counts: dict[str, int],
    docking_counts: dict[str, int],
) -> tuple[float, dict[str, Any]]:
    """Dimension 2: Druggability — DiffDock hits + compound bioactivity + drug claims.

    Components (weighted):
    - DiffDock positive hits (confidence > 0): 0.35
    - Compound bioactivity edges: 0.25
    - Drug claims present: 0.20
    - Docking edges present: 0.20
    """
    # DiffDock hits from file
    dd_hits = diffdock_by_target.get(symbol.upper(), [])
    dd_positive = [h for h in dd_hits if h.get("confidence", 0) > 0]
    dd_total = len(dd_hits)
    dd_score = _clamp(len(dd_positive) / max(dd_total, 1)) if dd_total > 0 else 0.0

    # Screening hits from graph_edges (compound_bioactivity)
    sc_count = screening_counts.get(target_id, 0)
    sc_score = _clamp(min(sc_count / 5.0, 1.0))  # Saturate at 5 hits

    # Drug claims
    dc_count = drug_claim_counts.get(target_id, 0)
    dc_score = 1.0 if dc_count > 0 else 0.0

    # Docking edges
    dk_count = docking_counts.get(target_id, 0)
    dk_score = 1.0 if dk_count > 0 else 0.0

    score = _clamp(0.35 * dd_score + 0.25 * sc_score + 0.20 * dc_score + 0.20 * dk_score)

    detail = {
        "diffdock_total_hits": dd_total,
        "diffdock_positive_hits": len(dd_positive),
        "diffdock_score": round(dd_score, 4),
        "screening_edge_count": sc_count,
        "screening_score": round(sc_score, 4),
        "drug_claim_count": dc_count,
        "docking_edge_count": dk_count,
    }
    if dd_positive:
        detail["top_diffdock_compound"] = dd_positive[0].get("compound", "unknown")
        detail["top_diffdock_confidence"] = dd_positive[0].get("confidence", 0)

    return score, detail


def _score_uniqueness(
    symbol: str,
    esm2_data: dict[str, Any],
) -> tuple[float, dict[str, Any]]:
    """Dimension 3: Structural uniqueness from ESM-2 embeddings.

    Lower average cosine similarity = more structurally unique = better drug target
    (fewer off-target binding risks, more specific druggability).
    """
    avg_sim = esm2_data.get("avg_similarity", {})
    metadata = esm2_data.get("metadata", {})

    if symbol.upper() not in avg_sim:
        # No ESM-2 data — give neutral score
        return 0.5, {"status": "no_esm2_data", "note": "ESM-2 embedding not available for this target"}

    sim_value = avg_sim[symbol.upper()]
    # Uniqueness = 1 - avg_similarity (lower similarity = higher uniqueness)
    score = _clamp(1.0 - sim_value)

    meta = metadata.get(symbol.upper(), {})
    detail = {
        "avg_cosine_similarity": sim_value,
        "uniqueness_score": score,
        "sequence_length": meta.get("sequence_length", 0),
        "embedding_norm": round(meta.get("embedding_norm", 0), 3),
        "proteins_compared": len(avg_sim),
    }
    return score, detail


async def _score_clinical(
    target_id: str,
    symbol: str,
    outcome_cache: dict[str, dict],
) -> tuple[float, dict[str, Any]]:
    """Dimension 4: Clinical validation from drug_outcomes table.

    Measures how well-validated a target is clinically:
    - Has compounds been tested?
    - What is the success rate?
    - What trial phases have been reached?

    Score = 0.4 * (has_outcomes) + 0.3 * (success_rate) + 0.3 * (phase_advancement)
    """
    if symbol.upper() in outcome_cache:
        cached = outcome_cache[symbol.upper()]
        return cached["score"], cached

    # Query drug_outcomes for this target
    rows = await fetch(
        """SELECT compound_name, outcome, trial_phase, confidence
           FROM drug_outcomes
           WHERE UPPER(target) = $1 OR UPPER(target) LIKE $2""",
        symbol.upper(),
        f"%{symbol.upper()}%",
    )

    if not rows:
        return 0.0, {
            "compounds_tested": 0,
            "success_count": 0,
            "failure_count": 0,
            "success_rate": 0.0,
            "score": 0.0,
        }

    compounds = set()
    successes = 0
    failures = 0
    max_phase = 0

    for r in rows:
        r = dict(r)
        compounds.add(r.get("compound_name", "unknown"))
        outcome = (r.get("outcome") or "").lower()
        if outcome in ("success", "partial_success", "approved"):
            successes += 1
        elif outcome in ("failure", "discontinued", "terminated"):
            failures += 1

        phase_str = (r.get("trial_phase") or "").lower()
        for p in [4, 3, 2, 1]:
            if str(p) in phase_str:
                max_phase = max(max_phase, p)
                break

    total = successes + failures
    success_rate = successes / total if total > 0 else 0.0
    has_outcomes = 1.0 if len(compounds) > 0 else 0.0
    phase_score = min(max_phase / 4.0, 1.0)

    score = _clamp(0.4 * has_outcomes + 0.3 * success_rate + 0.3 * phase_score)

    detail = {
        "compounds_tested": len(compounds),
        "compound_names": sorted(compounds),
        "success_count": successes,
        "failure_count": failures,
        "success_rate": round(success_rate, 4),
        "max_trial_phase": max_phase,
        "phase_score": round(phase_score, 4),
        "score": score,
    }
    return score, detail


async def _score_conservation(
    symbol: str,
    conservation_cache: dict[str, dict],
) -> tuple[float, dict[str, Any]]:
    """Dimension 5: Cross-species conservation.

    Measures how conserved the target is across model organisms.
    Higher conservation = more likely to translate from animal models to humans.
    """
    if symbol.upper() in conservation_cache:
        cached = conservation_cache[symbol.upper()]
        return cached["score"], cached

    rows = await fetch(
        "SELECT species, ortholog_symbol, conservation_score FROM cross_species_targets WHERE human_symbol = $1",
        symbol.upper(),
    )

    if not rows:
        return 0.0, {
            "species_count": 0,
            "avg_conservation": 0.0,
            "score": 0.0,
            "status": "no_ortholog_data",
        }

    species_list = []
    conservation_scores = []
    for r in rows:
        r = dict(r)
        species_list.append(r.get("species", "unknown"))
        cs = r.get("conservation_score")
        if cs is not None:
            conservation_scores.append(float(cs))

    species_count = len(species_list)
    avg_conservation = sum(conservation_scores) / len(conservation_scores) if conservation_scores else 0.0

    # Score: 0.5 * species_breadth (out of 7 model organisms) + 0.5 * avg_conservation
    breadth_score = min(species_count / 7.0, 1.0)
    score = _clamp(0.5 * breadth_score + 0.5 * avg_conservation)

    detail = {
        "species_count": species_count,
        "species": species_list,
        "avg_conservation": round(avg_conservation, 4),
        "breadth_score": round(breadth_score, 4),
        "score": score,
    }
    return score, detail


async def _score_novelty(target_id: str, novelty_cache: dict[str, dict]) -> tuple[float, dict[str, Any]]:
    """Dimension 6: Novelty / underexploration.

    Inverse of how well-studied a target is. Rewards emerging targets
    that are underexplored relative to the evidence base.

    Components:
    - Recent claim fraction (claims from last 2 years / total)
    - Low total claim count (fewer = more novel)
    """
    tid = str(target_id)
    if tid in novelty_cache:
        cached = novelty_cache[tid]
        return cached["score"], cached

    total_claims = int(await fetchval(
        "SELECT COUNT(*) FROM claims WHERE subject_id = $1", target_id
    ) or 0)

    max_claims = int(await fetchval(
        "SELECT MAX(cnt) FROM (SELECT COUNT(*) AS cnt FROM claims WHERE subject_id IS NOT NULL GROUP BY subject_id) sub"
    ) or 1)

    # Count claims with recent sources (last 2 years)
    from datetime import datetime, timedelta, timezone
    cutoff = (datetime.now(timezone.utc) - timedelta(days=730)).strftime('%Y-%m-%d')
    recent_val = await fetchval(
        """SELECT COUNT(DISTINCT c.id)
           FROM claims c
           JOIN evidence e ON e.claim_id = c.id
           JOIN sources s ON e.source_id = s.id
           WHERE c.subject_id = $1
             AND s.pub_date IS NOT NULL
             AND s.pub_date >= $2""",
        target_id, cutoff,
    )
    recent_claims = int(recent_val or 0)

    total_dated = int(await fetchval(
        """SELECT COUNT(DISTINCT c.id)
           FROM claims c
           JOIN evidence e ON e.claim_id = c.id
           JOIN sources s ON e.source_id = s.id
           WHERE c.subject_id = $1 AND s.pub_date IS NOT NULL""",
        target_id,
    ) or 0)

    # Recency fraction (higher = more recent activity)
    recency = recent_claims / total_dated if total_dated > 0 else 0.0

    # Underexploration (fewer claims = more novel, but not zero)
    # Use inverse log scale: novelty decreases as claims grow
    if total_claims == 0:
        exploration = 0.0  # No claims = not novel, just missing
    elif total_claims <= 10:
        exploration = 0.9  # Very underexplored
    elif total_claims <= 50:
        exploration = 0.6
    elif total_claims <= 200:
        exploration = 0.3
    else:
        exploration = 0.1  # Well-studied = low novelty

    score = _clamp(0.6 * recency + 0.4 * exploration)

    detail = {
        "total_claims": total_claims,
        "recent_claims": recent_claims,
        "total_dated_claims": total_dated,
        "recency_fraction": round(recency, 4),
        "exploration_score": round(exploration, 4),
        "score": score,
    }
    return score, detail


# ---------------------------------------------------------------------------
# Batch data loading (run once, used for all targets)
# ---------------------------------------------------------------------------


async def _load_batch_data() -> dict[str, Any]:
    """Load all batch data needed for scoring all targets."""

    # 1. Convergence scores (from convergence_scores table)
    convergence_rows = await fetch(
        """SELECT cs.target_id, cs.target_label, cs.composite_score,
                  cs.volume, cs.lab_independence, cs.method_diversity,
                  cs.temporal_trend, cs.replication, cs.confidence_level,
                  cs.claim_count, cs.source_count
           FROM convergence_scores cs
           INNER JOIN (
               SELECT target_id, MAX(computed_at) AS max_computed
               FROM convergence_scores
               GROUP BY target_id
           ) latest ON cs.target_id = latest.target_id AND cs.computed_at = latest.max_computed"""
    )
    convergence_cache = {}
    for r in convergence_rows:
        r = dict(r)
        label = (r.get("target_label") or "").upper()
        convergence_cache[label] = {
            "composite_score": _clamp(float(r.get("composite_score", 0) or 0)),
            "volume": float(r.get("volume", 0) or 0),
            "lab_independence": float(r.get("lab_independence", 0) or 0),
            "method_diversity": float(r.get("method_diversity", 0) or 0),
            "temporal_trend": float(r.get("temporal_trend", 0) or 0),
            "replication": float(r.get("replication", 0) or 0),
            "confidence_level": r.get("confidence_level", "low"),
            "claim_count": int(r.get("claim_count", 0) or 0),
            "source_count": int(r.get("source_count", 0) or 0),
        }

    # 2. Drug claims per target
    drug_claim_rows = await fetch(
        """SELECT subject_id, COUNT(*) as cnt FROM claims
           WHERE claim_type IN ('drug_target', 'drug_efficacy') AND subject_id IS NOT NULL
           GROUP BY subject_id"""
    )
    drug_claim_counts = {str(r["subject_id"]): int(r["cnt"]) for r in drug_claim_rows}

    # 3. Docking edges per target
    docking_rows = await fetch(
        """SELECT target_id, COUNT(*) as cnt FROM (
              SELECT src_id AS target_id FROM graph_edges
              WHERE relation LIKE '%docking%' OR relation LIKE '%binding_affinity%'
              UNION ALL
              SELECT dst_id AS target_id FROM graph_edges
              WHERE relation LIKE '%docking%' OR relation LIKE '%binding_affinity%'
           ) sub GROUP BY target_id"""
    )
    docking_counts = {str(r["target_id"]): int(r["cnt"]) for r in docking_rows}

    # 4. Screening edges per target (compound_bioactivity)
    screening_rows = await fetch(
        """SELECT target_id, COUNT(*) as cnt FROM (
              SELECT src_id AS target_id FROM graph_edges WHERE relation LIKE 'compound_bioactivity%'
              UNION ALL
              SELECT dst_id AS target_id FROM graph_edges WHERE relation LIKE 'compound_bioactivity%'
           ) sub GROUP BY target_id"""
    )
    screening_counts = {str(r["target_id"]): int(r["cnt"]) for r in screening_rows}

    # 5. DiffDock results from file
    dd_results = _load_diffdock_results()
    diffdock_by_target = {}
    for hit in dd_results:
        target_sym = (hit.get("target") or "").upper()
        if target_sym:
            diffdock_by_target.setdefault(target_sym, []).append(hit)

    # 6. ESM-2 embeddings
    esm2_data = _load_esm2_embeddings()

    # 7. Drug outcomes per target
    try:
        outcome_rows = await fetch(
            """SELECT compound_name, target, outcome, trial_phase, confidence
               FROM drug_outcomes
               WHERE target IS NOT NULL AND target != ''"""
        )
    except Exception:
        outcome_rows = []

    outcome_cache = {}
    for r in outcome_rows:
        r = dict(r)
        target_label = (r.get("target") or "").upper()
        if target_label not in outcome_cache:
            outcome_cache[target_label] = {
                "compounds": set(),
                "successes": 0,
                "failures": 0,
                "max_phase": 0,
            }
        entry = outcome_cache[target_label]
        entry["compounds"].add(r.get("compound_name", "unknown"))
        outcome_str = (r.get("outcome") or "").lower()
        if outcome_str in ("success", "partial_success", "approved"):
            entry["successes"] += 1
        elif outcome_str in ("failure", "discontinued", "terminated"):
            entry["failures"] += 1
        phase_str = (r.get("trial_phase") or "").lower()
        for p in [4, 3, 2, 1]:
            if str(p) in phase_str:
                entry["max_phase"] = max(entry["max_phase"], p)
                break

    # Post-process outcome_cache into score dicts
    clinical_cache = {}
    for sym, entry in outcome_cache.items():
        total = entry["successes"] + entry["failures"]
        success_rate = entry["successes"] / total if total > 0 else 0.0
        has_outcomes = 1.0 if len(entry["compounds"]) > 0 else 0.0
        phase_score = min(entry["max_phase"] / 4.0, 1.0)
        score = _clamp(0.4 * has_outcomes + 0.3 * success_rate + 0.3 * phase_score)
        clinical_cache[sym] = {
            "compounds_tested": len(entry["compounds"]),
            "compound_names": sorted(entry["compounds"]),
            "success_count": entry["successes"],
            "failure_count": entry["failures"],
            "success_rate": round(success_rate, 4),
            "max_trial_phase": entry["max_phase"],
            "phase_score": round(phase_score, 4),
            "score": score,
        }

    # 8. Cross-species conservation per target
    try:
        conservation_rows = await fetch(
            """SELECT human_symbol, species, ortholog_symbol, conservation_score
               FROM cross_species_targets"""
        )
    except Exception:
        conservation_rows = []

    conservation_grouped = {}
    for r in conservation_rows:
        r = dict(r)
        sym = (r.get("human_symbol") or "").upper()
        if sym not in conservation_grouped:
            conservation_grouped[sym] = {"species": [], "scores": []}
        conservation_grouped[sym]["species"].append(r.get("species", "unknown"))
        cs = r.get("conservation_score")
        if cs is not None:
            conservation_grouped[sym]["scores"].append(float(cs))

    conservation_cache = {}
    for sym, data in conservation_grouped.items():
        species_count = len(data["species"])
        avg_conservation = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0.0
        breadth_score = min(species_count / 7.0, 1.0)
        score = _clamp(0.5 * breadth_score + 0.5 * avg_conservation)
        conservation_cache[sym] = {
            "species_count": species_count,
            "species": data["species"],
            "avg_conservation": round(avg_conservation, 4),
            "breadth_score": round(breadth_score, 4),
            "score": score,
        }

    return {
        "convergence_cache": convergence_cache,
        "drug_claim_counts": drug_claim_counts,
        "docking_counts": docking_counts,
        "screening_counts": screening_counts,
        "diffdock_by_target": diffdock_by_target,
        "esm2_data": esm2_data,
        "clinical_cache": clinical_cache,
        "conservation_cache": conservation_cache,
    }


# ---------------------------------------------------------------------------
# Core scoring
# ---------------------------------------------------------------------------


async def _score_target(
    target_id: str,
    symbol: str,
    name: str | None,
    target_type: str | None,
    batch: dict[str, Any],
) -> dict[str, Any]:
    """Score a single target across all 6 dimensions."""

    # D1: Evidence convergence
    ev_score, ev_detail = await _score_evidence(
        target_id, symbol, batch["convergence_cache"]
    )

    # D2: Druggability
    dr_score, dr_detail = await _score_druggability(
        target_id,
        symbol,
        batch["diffdock_by_target"],
        batch["screening_counts"],
        batch["drug_claim_counts"],
        batch["docking_counts"],
    )

    # D3: Structural uniqueness
    un_score, un_detail = _score_uniqueness(symbol, batch["esm2_data"])

    # D4: Clinical validation
    clinical_cache = batch["clinical_cache"]
    sym_upper = symbol.upper()
    if sym_upper in clinical_cache:
        cl_data = clinical_cache[sym_upper]
        cl_score = cl_data["score"]
        cl_detail = cl_data
    else:
        cl_score, cl_detail = await _score_clinical(target_id, symbol, clinical_cache)

    # D5: Conservation
    conservation_cache = batch["conservation_cache"]
    if sym_upper in conservation_cache:
        co_data = conservation_cache[sym_upper]
        co_score = co_data["score"]
        co_detail = co_data
    else:
        co_score, co_detail = await _score_conservation(symbol, conservation_cache)

    # D6: Novelty
    no_score, no_detail = await _score_novelty(target_id, {})

    dimensions = {
        "evidence": ev_score,
        "druggability": dr_score,
        "uniqueness": un_score,
        "clinical": cl_score,
        "conservation": co_score,
        "novelty": no_score,
    }

    composite = _clamp(sum(WEIGHTS[d] * dimensions[d] for d in WEIGHTS))

    # Priority tier (stricter thresholds than v1)
    if composite >= 0.60:
        tier = "tier_1_actionable"
    elif composite >= 0.40:
        tier = "tier_2_promising"
    elif composite >= 0.20:
        tier = "tier_3_exploratory"
    else:
        tier = "tier_4_insufficient"

    # Strength/weakness analysis
    strengths = sorted(
        [(d, dimensions[d]) for d in dimensions if dimensions[d] >= 0.6],
        key=lambda x: x[1],
        reverse=True,
    )
    weaknesses = sorted(
        [(d, dimensions[d]) for d in dimensions if dimensions[d] < 0.3],
        key=lambda x: x[1],
    )

    return {
        "target_id": target_id,
        "symbol": symbol,
        "name": name,
        "target_type": target_type,
        "composite_score": composite,
        "tier": tier,
        "dimensions": dimensions,
        "dimension_details": {
            "evidence": ev_detail,
            "druggability": dr_detail,
            "uniqueness": un_detail,
            "clinical": cl_detail,
            "conservation": co_detail,
            "novelty": no_detail,
        },
        "strengths": [{"dimension": s[0], "score": s[1]} for s in strengths],
        "weaknesses": [{"dimension": w[0], "score": w[1]} for w in weaknesses],
        "weights": WEIGHTS,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def prioritize_all_targets() -> list[dict[str, Any]]:
    """Rank all targets by composite score across 6 dimensions.

    Returns a list sorted descending by composite_score, with per-dimension
    breakdown, detail objects, strengths, and weaknesses for each target.
    """
    targets = await fetch(
        "SELECT id, symbol, name, target_type FROM targets ORDER BY symbol"
    )

    if not targets:
        return []

    batch = await _load_batch_data()

    results = []
    for t in targets:
        t = dict(t)
        scored = await _score_target(
            str(t["id"]),
            t["symbol"],
            t.get("name"),
            t.get("target_type"),
            batch,
        )
        results.append(scored)

    results.sort(key=lambda x: x["composite_score"], reverse=True)
    for i, r in enumerate(results, start=1):
        r["rank"] = i

    logger.info(
        "v2 Prioritized %d targets. #1: %s (%.4f), #%d: %s (%.4f)",
        len(results),
        results[0]["symbol"] if results else "N/A",
        results[0]["composite_score"] if results else 0,
        len(results),
        results[-1]["symbol"] if results else "N/A",
        results[-1]["composite_score"] if results else 0,
    )

    return results


async def get_target_profile(symbol: str) -> dict[str, Any]:
    """Deep profile for one target — full 6-dimension breakdown with details.

    Returns the target's scorecard with rank among all targets.
    """
    all_ranked = await prioritize_all_targets()

    symbol_upper = symbol.strip().upper()
    for r in all_ranked:
        if r["symbol"].upper() == symbol_upper:
            r["total_targets"] = len(all_ranked)

            # Add radar chart data (normalized 0-1 for each dimension)
            r["radar_data"] = {
                "labels": list(WEIGHTS.keys()),
                "values": [r["dimensions"].get(d, 0) for d in WEIGHTS],
                "weights": [WEIGHTS[d] for d in WEIGHTS],
            }

            return r

    return {"error": f"Target '{symbol}' not found"}


async def compare_targets_v2(symbols: list[str]) -> dict[str, Any]:
    """Side-by-side comparison of multiple targets across all 6 dimensions.

    Returns each target's scorecard, dimension leaders, radar data,
    and score gaps from the top-ranked target.
    """
    if not symbols:
        return {"error": "No target symbols provided"}

    symbols_upper = [s.strip().upper() for s in symbols if s.strip()]

    all_ranked = await prioritize_all_targets()
    ranked_map = {r["symbol"].upper(): r for r in all_ranked}

    comparisons = []
    not_found = []

    for sym in symbols_upper:
        if sym in ranked_map:
            target_data = ranked_map[sym]
            target_data["radar_data"] = {
                "labels": list(WEIGHTS.keys()),
                "values": [target_data["dimensions"].get(d, 0) for d in WEIGHTS],
                "weights": [WEIGHTS[d] for d in WEIGHTS],
            }
            comparisons.append(target_data)
        else:
            not_found.append(sym)

    if not comparisons:
        return {"error": f"None of the targets found: {', '.join(symbols_upper)}"}

    comparisons.sort(key=lambda x: x["composite_score"], reverse=True)

    # Dimension leaders
    dimension_leaders = {}
    for dim in WEIGHTS:
        best = max(comparisons, key=lambda x: x["dimensions"].get(dim, 0))
        dimension_leaders[dim] = {
            "leader": best["symbol"],
            "score": best["dimensions"].get(dim, 0),
        }

    # Gaps from top
    gaps = {}
    if len(comparisons) >= 2:
        top = comparisons[0]
        for c in comparisons[1:]:
            delta = round(top["composite_score"] - c["composite_score"], 4)
            gaps[c["symbol"]] = {
                "composite_gap": delta,
                "dimension_gaps": {
                    dim: round(
                        top["dimensions"].get(dim, 0) - c["dimensions"].get(dim, 0), 4
                    )
                    for dim in WEIGHTS
                },
            }

    return {
        "compared_count": len(comparisons),
        "not_found": not_found,
        "targets": comparisons,
        "dimension_leaders": dimension_leaders,
        "gaps_from_top": gaps,
        "weights": WEIGHTS,
    }
