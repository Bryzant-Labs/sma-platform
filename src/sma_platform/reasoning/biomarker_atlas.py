"""Biomarker Atlas — structured aggregation of biomarker claims across 4 layers.

Categorizes all biomarker-type claims into molecular, imaging, functional,
and fluid layers. Provides treatment-response biomarker discovery and
target-linked biomarker queries.

Layers:
- molecular:  NfL, pNfH, SMN protein, SMN2 mRNA, CMAP
- imaging:    MRI spinal cord, Muscle MRI, Ultrasound
- functional: HFMSE, CHOP INTEND, RULM, 6MWT, FVC
- fluid:      CSF protein, Blood SMN, Plasma NfL
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from ..core.database import fetch, fetchval

logger = logging.getLogger(__name__)

# =============================================================================
# Layer definitions
# =============================================================================

BIOMARKER_LAYERS: dict[str, dict[str, list[str]]] = {
    "molecular": {
        "markers": [
            "NfL (neurofilament light)",
            "pNfH (phosphorylated neurofilament heavy)",
            "SMN protein levels",
            "SMN2 mRNA",
            "CMAP (compound muscle action potential)",
        ],
        "keywords": [
            "neurofilament", "nfl", "pnfh", "smn protein", "smn2 mrna",
            "cmap", "motor unit",
        ],
    },
    "imaging": {
        "markers": [
            "MRI spinal cord",
            "Muscle MRI",
            "Ultrasound",
        ],
        "keywords": [
            "mri", "imaging", "ultrasound", "muscle volume", "fat fraction",
        ],
    },
    "functional": {
        "markers": [
            "HFMSE",
            "CHOP INTEND",
            "RULM",
            "6MWT",
            "FVC",
        ],
        "keywords": [
            "hfmse", "chop intend", "rulm", "6mwt", "fvc",
            "motor function", "walking distance", "hammersmith",
        ],
    },
    "fluid": {
        "markers": [
            "CSF protein",
            "Blood SMN",
            "Plasma NfL",
        ],
        "keywords": [
            "csf", "cerebrospinal", "blood", "plasma", "serum",
        ],
    },
}

# Keywords signalling treatment-response context
TREATMENT_RESPONSE_KEYWORDS = [
    "after treatment", "post-treatment", "nusinersen", "risdiplam",
    "response", "change from baseline", "onasemnogene", "zolgensma",
    "spinraza", "evrysdi",
]


def _classify_layer(text: str) -> list[str]:
    """Return all layers whose keywords appear in *text*."""
    text_lower = (text or "").lower()
    matched: list[str] = []
    for layer_name, layer_def in BIOMARKER_LAYERS.items():
        for kw in layer_def["keywords"]:
            if kw in text_lower:
                matched.append(layer_name)
                break
    return matched


def _match_markers(text: str, layer_name: str) -> list[str]:
    """Return specific marker names from *layer_name* found in *text*."""
    text_lower = (text or "").lower()
    hits: list[str] = []
    layer_def = BIOMARKER_LAYERS[layer_name]
    # Build keyword → marker mapping from marker names
    for marker in layer_def["markers"]:
        # Check marker name tokens against text
        marker_lower = marker.lower()
        # Use first meaningful token (before parentheses) as search key
        check_tokens = [marker_lower]
        if "(" in marker:
            abbrev = marker.split("(")[0].strip().lower()
            check_tokens.append(abbrev)
            inner = marker.split("(")[1].rstrip(")").strip().lower()
            check_tokens.append(inner)
        if any(tok in text_lower for tok in check_tokens):
            hits.append(marker)
    return hits


def _is_treatment_response(text: str) -> bool:
    """Return True if text mentions treatment response context."""
    text_lower = (text or "").lower()
    return any(kw in text_lower for kw in TREATMENT_RESPONSE_KEYWORDS)


# =============================================================================
# Core functions
# =============================================================================

async def build_atlas() -> dict:
    """Query all biomarker claims, categorize into layers, count per marker,
    and gather evidence sources.

    Returns a dict with:
    - total_biomarker_claims: int
    - layers: {layer_name: {markers: [...], claim_count, claims: [...]}}
    - uncategorized: claims that didn't match any layer keywords
    """
    rows = await fetch("""
        SELECT
            c.id AS claim_id,
            c.predicate,
            c.value,
            c.confidence,
            c.metadata AS claim_metadata,
            e.source_id,
            e.excerpt,
            s.title AS source_title,
            s.pub_date,
            s.doi,
            t_subj.symbol AS subject_symbol,
            t_obj.symbol AS object_symbol
        FROM claims c
        LEFT JOIN evidence e ON e.claim_id = c.id
        LEFT JOIN sources s ON s.id = e.source_id
        LEFT JOIN targets t_subj ON t_subj.id = c.subject_id
        LEFT JOIN targets t_obj ON t_obj.id = c.object_id
        WHERE c.claim_type = 'biomarker'
        ORDER BY c.confidence DESC NULLS LAST
    """)

    total = len(rows)

    # Initialize layer results
    layer_results: dict[str, dict[str, Any]] = {}
    for layer_name, layer_def in BIOMARKER_LAYERS.items():
        layer_results[layer_name] = {
            "markers": layer_def["markers"],
            "claim_count": 0,
            "marker_counts": {m: 0 for m in layer_def["markers"]},
            "claims": [],
            "sources": [],
        }

    uncategorized: list[dict] = []

    # Source tracking per layer to deduplicate
    layer_source_ids: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        # Build searchable text from predicate + value + excerpt
        search_text = " ".join(filter(None, [
            row.get("predicate"),
            row.get("value"),
            row.get("excerpt"),
        ]))

        matched_layers = _classify_layer(search_text)

        claim_record = {
            "claim_id": str(row["claim_id"]),
            "predicate": row["predicate"],
            "value": row["value"],
            "confidence": float(row["confidence"]) if row["confidence"] else 0.5,
            "subject": row.get("subject_symbol"),
            "object": row.get("object_symbol"),
            "source_title": row.get("source_title"),
            "pub_date": str(row["pub_date"]) if row.get("pub_date") else None,
            "doi": row.get("doi"),
        }

        if not matched_layers:
            uncategorized.append(claim_record)
            continue

        for layer_name in matched_layers:
            layer_results[layer_name]["claim_count"] += 1
            layer_results[layer_name]["claims"].append(claim_record)

            # Count specific markers
            markers_found = _match_markers(search_text, layer_name)
            for marker in markers_found:
                layer_results[layer_name]["marker_counts"][marker] += 1

            # Track sources
            src_id = row.get("source_id")
            if src_id and str(src_id) not in layer_source_ids[layer_name]:
                layer_source_ids[layer_name].add(str(src_id))
                layer_results[layer_name]["sources"].append({
                    "source_id": str(src_id),
                    "title": row.get("source_title"),
                    "pub_date": str(row["pub_date"]) if row.get("pub_date") else None,
                    "doi": row.get("doi"),
                })

    # Trim claim lists for response size (keep top 50 per layer by confidence)
    for layer_name in layer_results:
        layer_results[layer_name]["claims"] = layer_results[layer_name]["claims"][:50]
        layer_results[layer_name]["source_count"] = len(layer_results[layer_name]["sources"])
        layer_results[layer_name]["sources"] = layer_results[layer_name]["sources"][:30]

    logger.info(
        f"Biomarker atlas built: {total} claims across "
        f"{sum(lr['claim_count'] for lr in layer_results.values())} categorized, "
        f"{len(uncategorized)} uncategorized"
    )

    return {
        "total_biomarker_claims": total,
        "layers": layer_results,
        "uncategorized_count": len(uncategorized),
        "uncategorized": uncategorized[:20],
    }


async def treatment_response_biomarkers() -> list[dict]:
    """Find biomarker claims that mention treatment response.

    Searches predicate, value, and evidence excerpt for treatment-response
    keywords (nusinersen, risdiplam, post-treatment, change from baseline, etc.).

    Returns a list of dicts with claim details, layer classification, and source info.
    """
    rows = await fetch("""
        SELECT
            c.id AS claim_id,
            c.predicate,
            c.value,
            c.confidence,
            e.source_id,
            e.excerpt,
            s.title AS source_title,
            s.pub_date,
            s.doi,
            t_subj.symbol AS subject_symbol,
            t_obj.symbol AS object_symbol
        FROM claims c
        LEFT JOIN evidence e ON e.claim_id = c.id
        LEFT JOIN sources s ON s.id = e.source_id
        LEFT JOIN targets t_subj ON t_subj.id = c.subject_id
        LEFT JOIN targets t_obj ON t_obj.id = c.object_id
        WHERE c.claim_type = 'biomarker'
        ORDER BY c.confidence DESC NULLS LAST
    """)

    results: list[dict] = []
    seen_ids: set[str] = set()

    for row in rows:
        search_text = " ".join(filter(None, [
            row.get("predicate"),
            row.get("value"),
            row.get("excerpt"),
        ]))

        if not _is_treatment_response(search_text):
            continue

        claim_id = str(row["claim_id"])
        if claim_id in seen_ids:
            continue
        seen_ids.add(claim_id)

        layers = _classify_layer(search_text)

        # Identify which treatment keywords matched
        text_lower = search_text.lower()
        matched_treatments = [
            kw for kw in TREATMENT_RESPONSE_KEYWORDS if kw in text_lower
        ]

        results.append({
            "claim_id": claim_id,
            "predicate": row["predicate"],
            "value": row["value"],
            "confidence": float(row["confidence"]) if row["confidence"] else 0.5,
            "subject": row.get("subject_symbol"),
            "object": row.get("object_symbol"),
            "layers": layers if layers else ["unclassified"],
            "treatment_keywords": matched_treatments,
            "source_title": row.get("source_title"),
            "pub_date": str(row["pub_date"]) if row.get("pub_date") else None,
            "doi": row.get("doi"),
            "excerpt": row.get("excerpt"),
        })

    logger.info(f"Found {len(results)} treatment-response biomarker claims")
    return results


async def biomarkers_for_target(symbol: str) -> dict:
    """Find biomarker claims linked to a specific target (by symbol).

    Checks both subject_id and object_id for matches against the given symbol.

    Returns a dict with:
    - target: the symbol queried
    - total_claims: count
    - by_layer: {layer_name: [claims]}
    - treatment_response: claims that also mention treatment response
    """
    rows = await fetch("""
        SELECT
            c.id AS claim_id,
            c.predicate,
            c.value,
            c.confidence,
            e.source_id,
            e.excerpt,
            s.title AS source_title,
            s.pub_date,
            s.doi,
            t_subj.symbol AS subject_symbol,
            t_obj.symbol AS object_symbol
        FROM claims c
        LEFT JOIN evidence e ON e.claim_id = c.id
        LEFT JOIN sources s ON s.id = e.source_id
        LEFT JOIN targets t_subj ON t_subj.id = c.subject_id
        LEFT JOIN targets t_obj ON t_obj.id = c.object_id
        WHERE c.claim_type = 'biomarker'
          AND (
              t_subj.symbol ILIKE $1
              OR t_obj.symbol ILIKE $1
          )
        ORDER BY c.confidence DESC NULLS LAST
    """, symbol)

    by_layer: dict[str, list[dict]] = defaultdict(list)
    treatment_response: list[dict] = []
    seen_ids: set[str] = set()

    for row in rows:
        claim_id = str(row["claim_id"])
        if claim_id in seen_ids:
            continue
        seen_ids.add(claim_id)

        search_text = " ".join(filter(None, [
            row.get("predicate"),
            row.get("value"),
            row.get("excerpt"),
        ]))

        claim_record = {
            "claim_id": claim_id,
            "predicate": row["predicate"],
            "value": row["value"],
            "confidence": float(row["confidence"]) if row["confidence"] else 0.5,
            "subject": row.get("subject_symbol"),
            "object": row.get("object_symbol"),
            "source_title": row.get("source_title"),
            "pub_date": str(row["pub_date"]) if row.get("pub_date") else None,
            "doi": row.get("doi"),
            "excerpt": row.get("excerpt"),
        }

        matched_layers = _classify_layer(search_text)
        if matched_layers:
            for layer_name in matched_layers:
                by_layer[layer_name].append(claim_record)
        else:
            by_layer["unclassified"].append(claim_record)

        if _is_treatment_response(search_text):
            treatment_response.append(claim_record)

    total = len(seen_ids)
    logger.info(f"Biomarkers for target '{symbol}': {total} claims")

    return {
        "target": symbol,
        "total_claims": total,
        "by_layer": dict(by_layer),
        "layer_counts": {k: len(v) for k, v in by_layer.items()},
        "treatment_response_count": len(treatment_response),
        "treatment_response": treatment_response,
    }
