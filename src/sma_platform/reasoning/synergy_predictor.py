"""M5: Drug-Target Synergy Prediction.

Predicts which drug-target combinations are most likely to be synergistic
based on multiple evidence sources:

1. Docking scores    — DiffDock results from gpu_jobs table
2. Literature co-occurrence — drug + target co-mentioned in claims
3. Pathway overlap   — shared pathway membership via graph_edges
4. Claim evidence    — direct claims linking drug to target

Composite score = 0.3*docking + 0.3*literature + 0.2*pathway + 0.2*claim

References:
- Jia et al., Brief Bioinform 2019 (multi-evidence drug-target prediction)
- Cheng et al., Nat Commun 2019 (network-based drug combination prediction)
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ..core.database import fetch, fetchval

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _table_exists(table_name: str) -> bool:
    """Check whether a table exists in the database (Postgres or SQLite)."""
    try:
        # Works on both Postgres (information_schema) and SQLite (pragma)
        await fetchval(f"SELECT 1 FROM {table_name} LIMIT 1")
        return True
    except Exception:
        return False


async def _get_docking_scores() -> dict[tuple[str, str], float]:
    """Extract DiffDock confidence scores from gpu_jobs results.

    Returns mapping of (drug_name_lower, target_symbol_lower) -> normalized score 0-1.
    """
    if not await _table_exists("gpu_jobs"):
        logger.info("gpu_jobs table not found — docking scores unavailable")
        return {}

    rows = await fetch(
        "SELECT results FROM gpu_jobs WHERE job_type = 'diffdock' AND status = 'completed'"
    )

    raw_scores: dict[tuple[str, str], float] = {}
    max_confidence = 0.0

    for row in rows:
        results = row.get("results")
        if not results:
            continue
        if isinstance(results, str):
            try:
                results = json.loads(results)
            except (json.JSONDecodeError, TypeError):
                continue

        # DiffDock results may store per-pose confidence under various keys
        drug_name = (results.get("drug") or results.get("ligand") or "").lower()
        target_sym = (results.get("target") or results.get("receptor") or "").lower()
        confidence = results.get("confidence") or results.get("top_confidence") or 0.0

        if not drug_name or not target_sym:
            continue

        try:
            confidence = float(confidence)
        except (ValueError, TypeError):
            continue

        key = (drug_name, target_sym)
        if confidence > raw_scores.get(key, 0.0):
            raw_scores[key] = confidence
        if confidence > max_confidence:
            max_confidence = confidence

    # Normalize to 0-1
    if max_confidence > 0:
        return {k: round(v / max_confidence, 4) for k, v in raw_scores.items()}
    return raw_scores


async def _get_literature_scores(
    drug_names: list[str],
    target_symbols: list[str],
) -> dict[tuple[str, str], float]:
    """Count papers where drug name AND target symbol co-occur in claims.

    Returns mapping of (drug_name_lower, target_symbol_lower) -> normalized score 0-1.
    """
    raw_counts: dict[tuple[str, str], int] = {}
    max_count = 0

    for drug in drug_names:
        if not drug:
            continue
        pattern = f"%{drug}%"
        for target in target_symbols:
            if not target:
                continue
            tpattern = f"%{target}%"
            try:
                count = await fetchval(
                    """SELECT COUNT(*) FROM claims
                       WHERE (LOWER(CAST(metadata AS TEXT)) LIKE $1
                              OR LOWER(predicate) LIKE $1)
                         AND (LOWER(CAST(metadata AS TEXT)) LIKE $2
                              OR LOWER(predicate) LIKE $2)""",
                    pattern,
                    tpattern,
                )
                count = count or 0
            except Exception:
                count = 0

            if count > 0:
                key = (drug.lower(), target.lower())
                raw_counts[key] = count
                if count > max_count:
                    max_count = count

    if max_count > 0:
        return {k: round(v / max_count, 4) for k, v in raw_counts.items()}
    return {k: 0.0 for k in raw_counts}


async def _get_pathway_overlap(
    drug_targets_map: dict[str, list[str]],
    all_target_ids: dict[str, str],
) -> dict[tuple[str, str], float]:
    """Check if a drug's known targets share pathway edges with a given target.

    drug_targets_map: drug_name -> list of target symbols this drug is known to act on
    all_target_ids:   target_symbol -> target_id

    Returns mapping of (drug_name_lower, target_symbol_lower) -> 0 or 1.
    """
    scores: dict[tuple[str, str], float] = {}

    for drug_name, drug_target_symbols in drug_targets_map.items():
        drug_target_id_set: set[str] = set()
        for sym in drug_target_symbols:
            tid = all_target_ids.get(sym.lower())
            if tid:
                drug_target_id_set.add(str(tid))

        if not drug_target_id_set:
            continue

        for target_sym, target_id in all_target_ids.items():
            tid_str = str(target_id)
            # Skip if this target is already one of the drug's known targets
            if tid_str in drug_target_id_set:
                scores[(drug_name.lower(), target_sym.lower())] = 1.0
                continue

            # Check for shared pathway edges between any of the drug's
            # known targets and this candidate target
            for dt_id in drug_target_id_set:
                try:
                    shared = await fetchval(
                        """SELECT COUNT(*) FROM graph_edges
                           WHERE ((src_id = $1 AND dst_id = $2)
                               OR (src_id = $2 AND dst_id = $1))
                             AND relation LIKE '%pathway%'""",
                        dt_id,
                        tid_str,
                    )
                    if shared and shared > 0:
                        scores[(drug_name.lower(), target_sym.lower())] = 1.0
                        break
                except Exception:
                    pass

    return scores


async def _get_claim_scores(
    drug_ids: dict[str, str],
    target_ids: dict[str, str],
) -> dict[tuple[str, str], float]:
    """Count direct claims linking a drug to a target.

    drug_ids:   drug_name_lower -> drug_id
    target_ids: target_symbol_lower -> target_id

    Returns mapping of (drug_name_lower, target_symbol_lower) -> normalized score 0-1.
    """
    raw_counts: dict[tuple[str, str], int] = {}
    max_count = 0

    for drug_name, drug_id in drug_ids.items():
        for target_sym, target_id in target_ids.items():
            try:
                count = await fetchval(
                    """SELECT COUNT(*) FROM claims
                       WHERE (subject_id = $1 AND object_id = $2)
                          OR (subject_id = $2 AND object_id = $1)""",
                    str(drug_id),
                    str(target_id),
                )
                count = count or 0
            except Exception:
                count = 0

            if count > 0:
                key = (drug_name, target_sym)
                raw_counts[key] = count
                if count > max_count:
                    max_count = count

    if max_count > 0:
        return {k: round(v / max_count, 4) for k, v in raw_counts.items()}
    return {k: 0.0 for k in raw_counts}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def predict_drug_target_synergy(limit: int = 20) -> list[dict[str, Any]]:
    """Predict synergistic drug-target combinations from multiple evidence sources.

    Returns top pairs sorted by composite synergy score, each containing:
    - drug_name, drug_type, approval_status
    - target_symbol, target_type
    - docking_score, literature_score, pathway_score, claim_score
    - synergy_score (composite)
    """
    # 1. Fetch all drugs
    try:
        drug_rows = await fetch(
            "SELECT id, name, drug_type, approval_status, mechanism, targets FROM drugs"
        )
    except Exception as e:
        logger.error("Failed to fetch drugs: %s", e)
        return []

    if not drug_rows:
        logger.info("No drugs found in database")
        return []

    # 2. Fetch all targets
    try:
        target_rows = await fetch(
            "SELECT id, symbol, name, target_type FROM targets"
        )
    except Exception as e:
        logger.error("Failed to fetch targets: %s", e)
        return []

    if not target_rows:
        logger.info("No targets found in database")
        return []

    # Build lookup maps
    drug_ids: dict[str, str] = {}      # drug_name_lower -> id
    drug_info: dict[str, dict] = {}    # drug_name_lower -> {drug_type, approval_status, mechanism}
    drug_targets_map: dict[str, list[str]] = {}  # drug_name_lower -> known target symbols

    for row in drug_rows:
        d = dict(row)
        name = (d.get("name") or "").lower()
        if not name:
            continue
        drug_ids[name] = str(d["id"])
        drug_info[name] = {
            "drug_type": d.get("drug_type") or "",
            "approval_status": d.get("approval_status") or "",
            "mechanism": d.get("mechanism") or "",
        }
        # Parse the targets field (stored as JSON array string)
        raw_targets = d.get("targets")
        if raw_targets:
            if isinstance(raw_targets, str):
                try:
                    raw_targets = json.loads(raw_targets)
                except (json.JSONDecodeError, TypeError):
                    raw_targets = []
            if isinstance(raw_targets, list):
                drug_targets_map[name] = [t.lower() for t in raw_targets if t]

    target_ids: dict[str, str] = {}     # symbol_lower -> id
    target_info: dict[str, dict] = {}   # symbol_lower -> {name, target_type}

    for row in target_rows:
        d = dict(row)
        sym = (d.get("symbol") or "").lower()
        if not sym:
            continue
        target_ids[sym] = str(d["id"])
        target_info[sym] = {
            "name": d.get("name") or "",
            "target_type": d.get("target_type") or "",
        }

    drug_names = list(drug_ids.keys())
    target_symbols = list(target_ids.keys())

    logger.info(
        "Synergy prediction: %d drugs x %d targets = %d pairs",
        len(drug_names), len(target_symbols), len(drug_names) * len(target_symbols),
    )

    # 3. Collect evidence scores
    docking_scores = await _get_docking_scores()
    literature_scores = await _get_literature_scores(drug_names, target_symbols)
    pathway_scores = await _get_pathway_overlap(drug_targets_map, target_ids)
    claim_scores = await _get_claim_scores(drug_ids, target_ids)

    # 4. Compute composite synergy score for all pairs that have at least one signal
    all_keys: set[tuple[str, str]] = set()
    all_keys.update(docking_scores.keys())
    all_keys.update(literature_scores.keys())
    all_keys.update(pathway_scores.keys())
    all_keys.update(claim_scores.keys())

    results: list[dict[str, Any]] = []
    for drug_name, target_sym in all_keys:
        if drug_name not in drug_ids or target_sym not in target_ids:
            continue

        d_score = docking_scores.get((drug_name, target_sym), 0.0)
        l_score = literature_scores.get((drug_name, target_sym), 0.0)
        p_score = pathway_scores.get((drug_name, target_sym), 0.0)
        c_score = claim_scores.get((drug_name, target_sym), 0.0)

        synergy = round(
            0.3 * d_score + 0.3 * l_score + 0.2 * p_score + 0.2 * c_score,
            4,
        )

        if synergy <= 0:
            continue

        di = drug_info.get(drug_name, {})
        ti = target_info.get(target_sym, {})

        results.append({
            "drug_name": drug_name,
            "drug_type": di.get("drug_type", ""),
            "approval_status": di.get("approval_status", ""),
            "mechanism": di.get("mechanism", ""),
            "target_symbol": target_sym,
            "target_name": ti.get("name", ""),
            "target_type": ti.get("target_type", ""),
            "docking_score": d_score,
            "literature_score": l_score,
            "pathway_score": p_score,
            "claim_score": c_score,
            "synergy_score": synergy,
            "evidence_sources": sum([
                d_score > 0,
                l_score > 0,
                p_score > 0,
                c_score > 0,
            ]),
        })

    # 5. Sort by synergy_score descending, return top N
    results.sort(key=lambda x: x["synergy_score"], reverse=True)
    return results[:limit]


async def predict_synergy_for_drug(drug_name: str, limit: int = 20) -> list[dict[str, Any]]:
    """Predict synergistic targets for a specific drug."""
    all_predictions = await predict_drug_target_synergy(limit=500)
    drug_lower = drug_name.lower()
    filtered = [p for p in all_predictions if p["drug_name"] == drug_lower]
    return filtered[:limit]


async def predict_synergy_for_target(target_symbol: str, limit: int = 20) -> list[dict[str, Any]]:
    """Predict synergistic drugs for a specific target."""
    all_predictions = await predict_drug_target_synergy(limit=500)
    target_lower = target_symbol.lower()
    filtered = [p for p in all_predictions if p["target_symbol"] == target_lower]
    return filtered[:limit]
