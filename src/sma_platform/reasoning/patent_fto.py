"""IP/Patent Freedom-to-Operate -- assess patent risk for screening hits.

Provides a basic FTO signal for each target and compound class,
based on known SMA patents in our database (578 patents).
"""

from __future__ import annotations

import logging
from typing import Any

from ..core.database import fetch, fetchval

logger = logging.getLogger(__name__)

# Known patent holders for key SMA targets
PATENT_LANDSCAPE: dict[str, dict[str, Any]] = {
    "SMN2_splicing": {
        "holders": ["Ionis Pharmaceuticals", "Roche/Genentech", "Novartis"],
        "key_patents": [
            "US 8,980,853 (nusinersen core)",
            "US 10,308,681 (risdiplam)",
            "WO 2020/234459 (branaplam)",
        ],
        "status": "Active -- heavily patented space",
        "risk": "high",
        "expiry_range": "2028-2037",
    },
    "SMN1_gene_therapy": {
        "holders": ["Novartis/AveXis"],
        "key_patents": [
            "US 9,409,953 (AAV9-SMN1)",
            "US 10,383,920",
        ],
        "status": "Active -- Novartis holds broad AAV-SMN patents",
        "risk": "high",
        "expiry_range": "2033-2038",
    },
    "NCALD_modifier": {
        "holders": ["University of Cologne (Brunhilde Wirth)"],
        "key_patents": ["EP 3 144 389 (NCALD as SMA modifier)"],
        "status": "Academic patent -- potential licensing",
        "risk": "medium",
        "expiry_range": "2035+",
    },
    "PLS3_modifier": {
        "holders": ["University of Cologne (Brunhilde Wirth)"],
        "key_patents": ["EP 2 585 097 (PLS3 in SMA)"],
        "status": "Academic patent",
        "risk": "low",
        "expiry_range": "2031+",
    },
    "4AP_repurposing": {
        "holders": ["Acorda Therapeutics", "Various"],
        "key_patents": [
            "US 8,007,826 (dalfampridine formulation)",
            "JP2015512409A (4-AP in SMA)",
        ],
        "status": "Base compound off-patent. Formulation patents active.",
        "risk": "low",
        "expiry_range": "Expired (base), 2030 (formulations)",
    },
    "UBA1_targeting": {
        "holders": ["None identified"],
        "key_patents": [],
        "status": "No SMA-specific UBA1 patents found -- open space",
        "risk": "low",
        "expiry_range": "N/A",
    },
    "CORO1C_targeting": {
        "holders": ["None identified"],
        "key_patents": [],
        "status": "No CORO1C-targeting patents found -- novel target",
        "risk": "low",
        "expiry_range": "N/A",
    },
    "HDAC_inhibitors": {
        "holders": ["Italfarmaco (givinostat)", "Various"],
        "key_patents": ["Givinostat compound patents"],
        "status": "Compound-specific patents. Class is broad with expired patents.",
        "risk": "medium",
        "expiry_range": "Mixed",
    },
    "p53_pathway": {
        "holders": ["Various pharma"],
        "key_patents": ["Multiple p53 modulator patents (nutlin class, etc.)"],
        "status": "Competitive space but no SMA-specific p53 patents",
        "risk": "medium",
        "expiry_range": "Mixed",
    },
}

# Mapping from gene/target symbol to landscape key
_TARGET_KEY_MAP: dict[str, str] = {
    "SMN2": "SMN2_splicing",
    "SMN1": "SMN1_gene_therapy",
    "NCALD": "NCALD_modifier",
    "PLS3": "PLS3_modifier",
    "UBA1": "UBA1_targeting",
    "CORO1C": "CORO1C_targeting",
    "TP53": "p53_pathway",
    "P53": "p53_pathway",
    "4-AP": "4AP_repurposing",
    "4AP": "4AP_repurposing",
    "DALFAMPRIDINE": "4AP_repurposing",
    "FAMPRIDINE": "4AP_repurposing",
    "4-AMINOPYRIDINE": "4AP_repurposing",
    "HDAC": "HDAC_inhibitors",
    "GIVINOSTAT": "HDAC_inhibitors",
}

_DEFAULT_LANDSCAPE: dict[str, Any] = {
    "holders": ["Unknown"],
    "key_patents": [],
    "status": "Not yet assessed",
    "risk": "unknown",
    "expiry_range": "Unknown",
}


async def get_fto_for_target(target: str) -> dict[str, Any]:
    """Get freedom-to-operate assessment for a target.

    Args:
        target: Gene symbol or compound name (e.g. "CORO1C", "SMN2", "4-AP").

    Returns:
        Dict with target, patent_count_in_db, landscape details, and
        a plain-language recommendation.
    """
    target_upper = target.strip().upper()

    # Map target to patent landscape key
    landscape_key = _TARGET_KEY_MAP.get(target_upper)
    landscape = PATENT_LANDSCAPE.get(landscape_key, _DEFAULT_LANDSCAPE) if landscape_key else _DEFAULT_LANDSCAPE

    # Count SMA patents mentioning this target in our database
    patent_count = 0
    try:
        patent_count = await fetchval(
            "SELECT COUNT(*) FROM sources WHERE source_type = 'patent' AND "
            "(title ILIKE $1 OR abstract ILIKE $1)",
            f"%{target_upper}%",
        ) or 0
    except Exception as exc:
        if "does not exist" not in str(exc):
            logger.warning("Failed to query patent count for %s: %s", target_upper, exc)

    return {
        "target": target_upper,
        "patent_count_in_db": patent_count,
        "landscape": landscape,
        "recommendation": _fto_recommendation(landscape.get("risk", "unknown")),
    }


def _fto_recommendation(risk: str) -> str:
    """Return a plain-language recommendation based on risk level."""
    if risk == "high":
        return (
            "Heavily patented. Consider licensing, design-around, or focus on "
            "novel compound classes not covered by existing claims."
        )
    if risk == "medium":
        return (
            "Some patent coverage. Review specific claims before advancing. "
            "Academic patents may be licensable."
        )
    if risk == "low":
        return (
            "Open space -- low patent risk. Good freedom-to-operate for "
            "novel compounds."
        )
    return "Patent landscape not yet assessed for this target."


async def get_fto_summary() -> list[dict[str, Any]]:
    """Get FTO summary for all assessed targets, sorted by risk (high first)."""
    results: list[dict[str, Any]] = []
    for key, landscape in PATENT_LANDSCAPE.items():
        results.append({
            "area": key,
            "risk": landscape["risk"],
            "holders": landscape["holders"],
            "key_patents": landscape["key_patents"],
            "status": landscape["status"],
            "expiry_range": landscape["expiry_range"],
        })
    results.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["risk"], 3))
    return results
