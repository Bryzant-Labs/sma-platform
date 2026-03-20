"""Biomarker Atlas — curated reference catalog + structured claim aggregation.

Two complementary data sources:
1. **SMA_BIOMARKERS** — expert-curated catalog of validated and emerging
   biomarkers with PMID references, specimen types, methods, and clinical
   utility descriptions.  Available instantly (no DB required).
2. **Claim-based atlas** — dynamic aggregation of biomarker-type claims
   from the evidence database, categorized into layers.

Layers / categories:
- molecular:         NfL, pNfH, SMN protein, SMN2 copy number, splicing biomarkers
- imaging:           MRI spinal cord, Muscle MRI, Ultrasound
- functional:        HFMSE, CHOP INTEND, RULM, 6MWT, FVC
- electrophysiology: CMAP, motor unit number estimation
- fluid:             CSF protein, Blood SMN, Plasma NfL

Biomarker types:
- prognostic:       predicts disease course independent of treatment
- pharmacodynamic:  changes in response to a specific drug mechanism
- efficacy:         measures clinical benefit in trials
- monitoring:       tracks disease progression over time
- exploratory:      early-stage research, not yet validated
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from ..core.database import fetch, fetchval

logger = logging.getLogger(__name__)

# =============================================================================
# Curated Biomarker Reference Catalog
# =============================================================================

SMA_BIOMARKERS: list[dict[str, Any]] = [
    # ── Molecular biomarkers ──────────────────────────────────────────────
    {
        "name": "SMN2 copy number",
        "category": "molecular",
        "type": "prognostic",
        "specimen": "blood/DNA",
        "method": "MLPA/qPCR/ddPCR",
        "clinical_use": (
            "Primary disease modifier — 2 copies = Type I, "
            "3 = Type II/III, 4+ = milder"
        ),
        "validated": True,
        "references": ["PMID:19209174", "PMID:25087612"],
    },
    {
        "name": "SMN protein level",
        "category": "molecular",
        "type": "pharmacodynamic",
        "specimen": "blood/CSF",
        "method": "ECL immunoassay",
        "clinical_use": (
            "Treatment response — increases with "
            "nusinersen/risdiplam/Zolgensma"
        ),
        "validated": True,
        "references": ["PMID:31451517", "PMID:33137810"],
    },
    {
        "name": "pNF-H (phosphorylated neurofilament heavy)",
        "category": "molecular",
        "type": "prognostic",
        "specimen": "blood/CSF",
        "method": "ELISA/Simoa",
        "clinical_use": (
            "Neurodegeneration marker — elevated in SMA, "
            "decreases with treatment"
        ),
        "validated": True,
        "references": ["PMID:31451517", "PMID:32424082"],
    },
    {
        "name": "NfL (neurofilament light chain)",
        "category": "molecular",
        "type": "prognostic",
        "specimen": "blood/CSF",
        "method": "Simoa/ELISA",
        "clinical_use": (
            "Axonal damage marker — correlates with motor function decline"
        ),
        "validated": True,
        "references": ["PMID:33230497", "PMID:34255344"],
    },
    {
        "name": "Splicing biomarkers (SMN2 exon 7 inclusion ratio)",
        "category": "molecular",
        "type": "pharmacodynamic",
        "specimen": "blood",
        "method": "RT-qPCR",
        "clinical_use": (
            "Direct measure of splicing modifier effect "
            "(risdiplam/branaplam)"
        ),
        "validated": False,
        "references": ["PMID:34403500"],
    },
    {
        "name": "Exosomal miRNAs",
        "category": "molecular",
        "type": "exploratory",
        "specimen": "blood/CSF",
        "method": "NGS/qPCR",
        "clinical_use": (
            "Motor neuron-derived exosomes — potential early detection"
        ),
        "validated": False,
        "references": [],
    },
    # ── Functional biomarkers ─────────────────────────────────────────────
    {
        "name": "CHOP INTEND",
        "category": "functional",
        "type": "efficacy",
        "specimen": "clinical assessment",
        "method": "26-item motor scale (0-64)",
        "clinical_use": (
            "Motor function in SMA Type I infants — "
            "primary endpoint in trials"
        ),
        "validated": True,
        "references": ["PMID:20008145"],
    },
    {
        "name": "HFMSE (Hammersmith Functional Motor Scale Expanded)",
        "category": "functional",
        "type": "efficacy",
        "specimen": "clinical assessment",
        "method": "33-item scale (0-66)",
        "clinical_use": (
            "Motor function in SMA Type II/III — "
            "primary endpoint in CHERISH/SUNFISH"
        ),
        "validated": True,
        "references": ["PMID:24698831"],
    },
    {
        "name": "RULM (Revised Upper Limb Module)",
        "category": "functional",
        "type": "efficacy",
        "specimen": "clinical assessment",
        "method": "20-item upper limb scale",
        "clinical_use": (
            "Upper limb function — important for non-ambulatory patients"
        ),
        "validated": True,
        "references": ["PMID:28399327"],
    },
    # ── Electrophysiology biomarkers ──────────────────────────────────────
    {
        "name": "CMAP (Compound Muscle Action Potential)",
        "category": "electrophysiology",
        "type": "prognostic",
        "specimen": "nerve conduction",
        "method": "EMG/NCS",
        "clinical_use": (
            "Motor unit integrity — low CMAP predicts poor outcome"
        ),
        "validated": True,
        "references": ["PMID:29305484"],
    },
    # ── Imaging biomarkers ────────────────────────────────────────────────
    {
        "name": "Muscle MRI (T2/STIR)",
        "category": "imaging",
        "type": "prognostic",
        "specimen": "MRI scan",
        "method": "Quantitative muscle MRI",
        "clinical_use": (
            "Fat infiltration pattern — tracks denervation "
            "and treatment response"
        ),
        "validated": True,
        "references": ["PMID:31451525"],
    },
    {
        "name": "Muscle ultrasound",
        "category": "imaging",
        "type": "monitoring",
        "specimen": "ultrasound",
        "method": "Quantitative muscle ultrasound",
        "clinical_use": (
            "Non-invasive muscle thickness/echointensity — "
            "portable bedside tool"
        ),
        "validated": False,
        "references": ["PMID:32871342"],
    },
]

# Convenience indexes
_BIOMARKER_BY_CATEGORY: dict[str, list[dict]] = defaultdict(list)
_BIOMARKER_BY_TYPE: dict[str, list[dict]] = defaultdict(list)
for _bm in SMA_BIOMARKERS:
    _BIOMARKER_BY_CATEGORY[_bm["category"]].append(_bm)
    _BIOMARKER_BY_TYPE[_bm["type"]].append(_bm)

BIOMARKER_CATEGORIES = sorted(_BIOMARKER_BY_CATEGORY.keys())
BIOMARKER_TYPES = sorted(_BIOMARKER_BY_TYPE.keys())

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
            "SMN2 copy number",
            "Splicing biomarkers (exon 7 inclusion)",
            "Exosomal miRNAs",
        ],
        "keywords": [
            "neurofilament", "nfl", "pnfh", "smn protein", "smn2 mrna",
            "smn2 copy", "copy number", "mlpa", "ddpcr",
            "splicing", "exon 7", "mirna", "exosom",
        ],
    },
    "imaging": {
        "markers": [
            "MRI spinal cord",
            "Muscle MRI (T2/STIR)",
            "Muscle ultrasound",
        ],
        "keywords": [
            "mri", "imaging", "ultrasound", "muscle volume", "fat fraction",
            "fat infiltration", "echointensity", "t2/stir",
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
            "upper limb", "motor scale",
        ],
    },
    "electrophysiology": {
        "markers": [
            "CMAP (compound muscle action potential)",
            "MUNE (motor unit number estimation)",
        ],
        "keywords": [
            "cmap", "motor unit", "emg", "nerve conduction",
            "electrophysiol", "mune", "action potential",
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


# =============================================================================
# Curated catalog query functions (no DB required)
# =============================================================================

def get_curated_catalog(
    *,
    category: str | None = None,
    biomarker_type: str | None = None,
    validated_only: bool = False,
) -> list[dict[str, Any]]:
    """Return biomarkers from the curated SMA_BIOMARKERS catalog.

    Filters:
    - category:       molecular | functional | imaging | electrophysiology
    - biomarker_type: prognostic | pharmacodynamic | efficacy | monitoring | exploratory
    - validated_only: if True, only return validated biomarkers

    Returns a list of biomarker dicts.
    """
    results = SMA_BIOMARKERS

    if category:
        cat_lower = category.lower()
        results = [b for b in results if b["category"] == cat_lower]

    if biomarker_type:
        type_lower = biomarker_type.lower()
        results = [b for b in results if b["type"] == type_lower]

    if validated_only:
        results = [b for b in results if b.get("validated")]

    return results


def get_treatment_response_catalog() -> list[dict[str, Any]]:
    """Return curated biomarkers relevant to monitoring treatment response.

    Includes pharmacodynamic biomarkers (direct drug response) plus
    prognostic/efficacy biomarkers whose clinical_use mentions treatment.
    """
    treatment_keywords = {"treatment", "nusinersen", "risdiplam", "zolgensma"}
    results: list[dict[str, Any]] = []

    for bm in SMA_BIOMARKERS:
        # Pharmacodynamic biomarkers are always treatment-relevant
        if bm["type"] == "pharmacodynamic":
            results.append(bm)
            continue
        # Efficacy biomarkers are treatment-relevant (trial endpoints)
        if bm["type"] == "efficacy":
            results.append(bm)
            continue
        # Check clinical_use text for treatment keywords
        use_lower = (bm.get("clinical_use") or "").lower()
        if any(kw in use_lower for kw in treatment_keywords):
            results.append(bm)

    return results


def get_catalog_summary() -> dict[str, Any]:
    """Return a summary of the curated biomarker catalog.

    Provides counts by category, type, and validation status.
    """
    total = len(SMA_BIOMARKERS)
    validated = sum(1 for b in SMA_BIOMARKERS if b.get("validated"))

    by_category: dict[str, int] = {}
    for cat in BIOMARKER_CATEGORIES:
        by_category[cat] = len(_BIOMARKER_BY_CATEGORY[cat])

    by_type: dict[str, int] = {}
    for t in BIOMARKER_TYPES:
        by_type[t] = len(_BIOMARKER_BY_TYPE[t])

    return {
        "total_biomarkers": total,
        "validated": validated,
        "emerging": total - validated,
        "by_category": by_category,
        "by_type": by_type,
        "categories": BIOMARKER_CATEGORIES,
        "types": BIOMARKER_TYPES,
    }
