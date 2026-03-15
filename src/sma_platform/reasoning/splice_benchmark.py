"""SMN2 Exon 7 Splice Variant Benchmark (Phase 9.2).

Systematic single-nucleotide variant (SNV) scan of the SMN2 exon 7 region:
100 bp intron 6 flank + 54 bp exon 7 + 100 bp intron 7 flank = 254 positions.

Each of the ~762 possible SNVs is scored across four dimensions:
  1. splice_site_proximity  -- distance to nearest splice acceptor/donor
  2. motif_disruption       -- overlap with known ESE/ESS/ISS regulatory motifs
  3. conservation           -- known functional importance of the position
  4. therapeutic_relevance  -- relevance to approved/pipeline SMA therapies

The composite score is a weighted average that highlights variants most likely
to alter SMN2 exon 7 inclusion, prioritizing positions where biology meets
current therapeutic strategy.

Reference: NCBI Gene ID 6607 (SMN2), GenBank NG_008728.1
"""

from __future__ import annotations

import csv
import io
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Reference sequences
# ---------------------------------------------------------------------------

# SMN2 exon 7: 54 nucleotides (positions 1-54 in exon coordinates)
# Position 6 is T in SMN2 (C in SMN1) -- the disease-defining C-to-T transition
EXON7_SEQ = "GATATTTTATATTAGACAAAATCAAAAAGAAGGAAATGCTGGCATAGAGCAGCAC"

# Intron 6, 3' end (100 bp upstream of exon 7)
# Approximate sequence from NG_008728.1 region.  The critical 3' splice site
# (AG) sits at positions -2/-1.  The branch point (YNYURAY) is around -20 to -25.
INTRON6_FLANK = (
    "ATAATTCCCCCACCACCTCCCATATGTCCAGATTCTCTTGATGATGCTGATGCTTTGGGAAG"
    "TATGTTAATTTCATGGTACATGAGTGGCTATCATACTGGCTAG"
)  # 105 chars -- we use last 100

# Intron 7, 5' start (100 bp downstream of exon 7)
# Contains ISS-N1 at +10 to +24 (nusinersen target) and Element 2 at +40 to +60.
INTRON7_FLANK = (
    "GTAAGTCTGCCAGCATTATGAAAGTGAATCTTACTTACTCAATATATATATATATATATTT"
    "TTAACAGATGGGAGTTCTGAGTGGACTAAATGTTCACAG"
)  # 100 chars

# Trim intron 6 flank to exactly 100 bp
_INTRON6_100 = INTRON6_FLANK[-100:]

# Sanity checks
assert len(EXON7_SEQ) == 54, f"Exon 7 must be 54 nt, got {len(EXON7_SEQ)}"
assert len(INTRON7_FLANK) == 100, f"Intron 7 flank must be 100 nt, got {len(INTRON7_FLANK)}"
assert len(_INTRON6_100) == 100, f"Intron 6 flank must be 100 nt, got {len(_INTRON6_100)}"

FULL_REGION = _INTRON6_100 + EXON7_SEQ + INTRON7_FLANK  # 254 nt
assert len(FULL_REGION) == 254

# ---------------------------------------------------------------------------
# Coordinate system
# ---------------------------------------------------------------------------
# We use exon-relative coordinates where exon 7 position 1 = index 0 of EXON7_SEQ.
# Intron 6 positions are negative (-100 to -1).
# Intron 7 positions are +1 to +100 (relative to end of exon 7, i.e. after pos 54).
#
# full_region index 0   = intron 6 pos -100
# full_region index 99  = intron 6 pos -1
# full_region index 100 = exon 7 pos 1
# full_region index 153 = exon 7 pos 54
# full_region index 154 = intron 7 pos +1
# full_region index 253 = intron 7 pos +100

_BASES = "ACGT"


def _exon_relative_pos(full_idx: int) -> int:
    """Convert full_region index to exon-relative position."""
    if full_idx < 100:
        return full_idx - 100  # -100 to -1
    elif full_idx < 154:
        return full_idx - 100 + 1  # 1 to 54
    else:
        return full_idx - 154 + 1  # +1 to +100 (intron 7)


def _region_label(exon_pos: int) -> str:
    """Human-readable region label."""
    if exon_pos < 0:
        return "intron6"
    elif exon_pos >= 1 and exon_pos <= 54:
        return "exon7"
    else:
        return "intron7"


def _variant_id(region: str, exon_pos: int, ref: str, alt: str) -> str:
    """Generate a compact variant identifier, e.g. 'E7:6T>C' or 'I7:+15G>A'."""
    if region == "exon7":
        return f"E7:{exon_pos}{ref}>{alt}"
    elif region == "intron6":
        return f"I6:{exon_pos}{ref}>{alt}"
    else:
        return f"I7:+{exon_pos}{ref}>{alt}"


# ---------------------------------------------------------------------------
# Regulatory motif definitions (exon-relative coordinates)
# ---------------------------------------------------------------------------

# Splice sites
SPLICE_ACCEPTOR = (-3, -1)   # 3' splice site AG dinucleotide (intron 6 end)
SPLICE_DONOR = (55, 57)      # 5' splice site GU/GT (intron 7 start, just past exon 7)

# Branch point (approximate, intron 6)
BRANCH_POINT = (-25, -20)

# Exonic Splicing Enhancers (ESE)
ESE_SF2_ASF = (1, 20)        # SF2/ASF binding region in exon 7
ESE_TRA2_BETA = (19, 27)     # Tra2-beta1 binding region in exon 7

# Exonic Splicing Silencer (ESS)
ESS_HNRNPA1 = (30, 44)       # hnRNP A1 binding region in exon 7

# Intronic Splicing Silencer 1 (nusinersen target)
ISS_N1 = (1, 24)             # positions +10 to +24 in intron 7 (stored as intron7 +pos)
ISS_N1_INTRON7 = (10, 24)    # intron 7 positions for ISS-N1

# Element 2 in intron 7
ELEMENT_2_INTRON7 = (40, 60)

# Critical individual positions
DISEASE_VARIANT_POS = 6      # exon 7 position 6: T in SMN2, C in SMN1


# ---------------------------------------------------------------------------
# Motif membership helpers
# ---------------------------------------------------------------------------

def _in_range(pos: int, start: int, end: int) -> bool:
    """Inclusive range check."""
    return start <= pos <= end


def _is_splice_site(exon_pos: int, region: str) -> bool:
    """Is this position within a core splice site?"""
    if region == "intron6":
        return _in_range(exon_pos, SPLICE_ACCEPTOR[0], SPLICE_ACCEPTOR[1])
    if region == "intron7":
        # Donor site: positions +1 to +3 in intron 7
        return exon_pos <= 3
    if region == "exon7":
        # Last 2 bases of exon contribute to splice site definition
        return exon_pos >= 53
    return False


def _splice_site_distance(exon_pos: int, region: str) -> int:
    """Minimum distance to the nearest splice site boundary."""
    if region == "intron6":
        # Distance to the 3' splice site at position -1
        return abs(exon_pos - (-1))
    elif region == "exon7":
        # Distance to acceptor (pos 1) or donor (pos 54)
        return min(abs(exon_pos - 1), abs(exon_pos - 54))
    else:
        # intron7: distance to donor site at +1
        return abs(exon_pos - 1)


def _get_motif_hits(exon_pos: int, region: str) -> list[str]:
    """Return list of motif names this position falls in."""
    hits: list[str] = []
    if region == "exon7":
        if _in_range(exon_pos, *ESE_SF2_ASF):
            hits.append("ESE:SF2/ASF")
        if _in_range(exon_pos, *ESE_TRA2_BETA):
            hits.append("ESE:Tra2-beta1")
        if _in_range(exon_pos, *ESS_HNRNPA1):
            hits.append("ESS:hnRNP_A1")
    elif region == "intron7":
        if _in_range(exon_pos, *ISS_N1_INTRON7):
            hits.append("ISS-N1")
        if _in_range(exon_pos, *ELEMENT_2_INTRON7):
            hits.append("Element_2")
    elif region == "intron6":
        if _in_range(exon_pos, *BRANCH_POINT):
            hits.append("Branch_point")
    # Splice site motifs
    if _is_splice_site(exon_pos, region):
        hits.append("Splice_site")
    return hits


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------

def _clamp(v: float) -> float:
    """Clamp to [0.0, 1.0] and round to 4 decimals."""
    return round(max(0.0, min(1.0, v)), 4)


def _score_splice_site_proximity(exon_pos: int, region: str) -> float:
    """Score 0-1: how close the position is to a splice site.

    Within 3 bp of a splice site boundary -> 1.0
    Decays exponentially with distance, floor at 0.05.
    """
    dist = _splice_site_distance(exon_pos, region)
    if dist <= 3:
        return 1.0
    # Exponential decay: score = exp(-0.08 * (dist - 3))
    import math
    score = math.exp(-0.08 * (dist - 3))
    return _clamp(max(score, 0.05))


def _score_motif_disruption(exon_pos: int, region: str) -> float:
    """Score 0-1: whether the position falls in a known regulatory motif.

    Direct splice site hit = 1.0
    ISS-N1 hit = 0.95
    ESE hit = 0.85
    ESS hit = 0.80
    Branch point = 0.85
    Element 2 = 0.60
    No motif = 0.05
    """
    hits = _get_motif_hits(exon_pos, region)
    if not hits:
        return 0.05

    # Score by highest-impact motif
    score = 0.0
    for h in hits:
        if h == "Splice_site":
            score = max(score, 1.0)
        elif h == "ISS-N1":
            score = max(score, 0.95)
        elif h.startswith("ESE"):
            score = max(score, 0.85)
        elif h == "Branch_point":
            score = max(score, 0.85)
        elif h.startswith("ESS"):
            score = max(score, 0.80)
        elif h == "Element_2":
            score = max(score, 0.60)
    return _clamp(score)


def _score_conservation(exon_pos: int, region: str) -> float:
    """Score 0-1: known functional importance of this position.

    Core splice sites = 1.0
    Disease variant position 6 = 1.0
    ISS-N1 region = 0.90
    Branch point = 0.85
    ESE core positions = 0.75
    Tra2-beta binding = 0.75
    ESS region = 0.65
    Element 2 = 0.50
    Other exonic = 0.40
    Other intronic = 0.20
    """
    # Splice sites
    if _is_splice_site(exon_pos, region):
        return 1.0

    if region == "exon7":
        # Disease variant
        if exon_pos == DISEASE_VARIANT_POS:
            return 1.0
        # ESE
        if _in_range(exon_pos, *ESE_SF2_ASF) or _in_range(exon_pos, *ESE_TRA2_BETA):
            return 0.75
        # ESS
        if _in_range(exon_pos, *ESS_HNRNPA1):
            return 0.65
        # Other exonic
        return 0.40

    if region == "intron7":
        if _in_range(exon_pos, *ISS_N1_INTRON7):
            return 0.90
        if _in_range(exon_pos, *ELEMENT_2_INTRON7):
            return 0.50
        return 0.20

    if region == "intron6":
        if _in_range(exon_pos, *BRANCH_POINT):
            return 0.85
        return 0.20

    return 0.10


def _score_therapeutic_relevance(exon_pos: int, region: str) -> float:
    """Score 0-1: relevance to existing or pipeline SMA therapies.

    ISS-N1 positions = 1.0  (nusinersen/Spinraza binds here)
    Disease variant pos 6 = 1.0  (the fundamental SMN2 defect)
    ESE region = 0.70  (risdiplam/Evrysdi modulates splicing via ESE/U1 snRNP)
    Tra2-beta region = 0.65
    Splice sites = 0.60  (general splice modulation target)
    Branch point = 0.55
    ESS region = 0.50  (potential ASO target)
    Element 2 = 0.45
    Other = 0.10
    """
    if region == "intron7" and _in_range(exon_pos, *ISS_N1_INTRON7):
        return 1.0

    if region == "exon7" and exon_pos == DISEASE_VARIANT_POS:
        return 1.0

    if region == "exon7":
        if _in_range(exon_pos, *ESE_SF2_ASF):
            return 0.70
        if _in_range(exon_pos, *ESE_TRA2_BETA):
            return 0.65
        if _in_range(exon_pos, *ESS_HNRNPA1):
            return 0.50

    if _is_splice_site(exon_pos, region):
        return 0.60

    if region == "intron6" and _in_range(exon_pos, *BRANCH_POINT):
        return 0.55

    if region == "intron7" and _in_range(exon_pos, *ELEMENT_2_INTRON7):
        return 0.45

    return 0.10


# Composite weights
WEIGHTS = {
    "splice_site_proximity": 0.25,
    "motif_disruption": 0.30,
    "conservation": 0.25,
    "therapeutic_relevance": 0.20,
}


def _annotate(exon_pos: int, region: str, ref: str, alt: str, scores: dict) -> str:
    """Generate a human-readable annotation for the variant."""
    parts: list[str] = []

    # Special cases
    if region == "exon7" and exon_pos == DISEASE_VARIANT_POS and alt == "C":
        parts.append(
            "CRITICAL: Reverts SMN2 disease-defining T>C at position 6, "
            "restoring SMN1-like splicing. This is THE variant that causes SMA."
        )

    motifs = _get_motif_hits(exon_pos, region)
    if motifs:
        parts.append(f"Regulatory motifs: {', '.join(motifs)}")

    if region == "intron7" and _in_range(exon_pos, *ISS_N1_INTRON7):
        parts.append("Within ISS-N1 (nusinersen/Spinraza binding site)")

    if _is_splice_site(exon_pos, region):
        if region == "intron6":
            parts.append("3' splice acceptor site (AG)")
        else:
            parts.append("5' splice donor site (GT)")

    if scores["composite_score"] >= 0.8:
        parts.append("HIGH IMPACT: likely to significantly affect exon 7 inclusion")
    elif scores["composite_score"] >= 0.5:
        parts.append("MODERATE IMPACT: may affect exon 7 splicing")
    else:
        parts.append("LOW IMPACT: unlikely to significantly alter splicing")

    return "; ".join(parts) if parts else "No specific annotation"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_reference_sequence() -> dict[str, Any]:
    """Return reference sequence data and annotations."""
    return {
        "exon7": EXON7_SEQ,
        "exon7_length": len(EXON7_SEQ),
        "intron6_flank": _INTRON6_100,
        "intron6_flank_length": len(_INTRON6_100),
        "intron7_flank": INTRON7_FLANK,
        "intron7_flank_length": len(INTRON7_FLANK),
        "full_region": FULL_REGION,
        "full_region_length": len(FULL_REGION),
        "gene": "SMN2",
        "gene_id": 6607,
        "annotations": {
            "disease_variant": {
                "position": DISEASE_VARIANT_POS,
                "region": "exon7",
                "smn2_base": "T",
                "smn1_base": "C",
                "description": (
                    "C-to-T transition at position 6 of exon 7 causes ~90% exon "
                    "skipping in SMN2. This is the molecular basis of SMA."
                ),
            },
            "splice_acceptor": {
                "positions": list(range(SPLICE_ACCEPTOR[0], SPLICE_ACCEPTOR[1] + 1)),
                "region": "intron6",
                "description": "3' splice site AG dinucleotide at intron 6 / exon 7 boundary",
            },
            "splice_donor": {
                "positions": list(range(SPLICE_DONOR[0], SPLICE_DONOR[1] + 1)),
                "region": "intron7",
                "description": "5' splice site GT at exon 7 / intron 7 boundary",
            },
            "branch_point": {
                "positions": list(range(BRANCH_POINT[0], BRANCH_POINT[1] + 1)),
                "region": "intron6",
                "description": "Approximate branch point sequence in intron 6",
            },
            "ese_sf2_asf": {
                "positions": list(range(ESE_SF2_ASF[0], ESE_SF2_ASF[1] + 1)),
                "region": "exon7",
                "description": "SF2/ASF exonic splicing enhancer in exon 7",
            },
            "ese_tra2_beta": {
                "positions": list(range(ESE_TRA2_BETA[0], ESE_TRA2_BETA[1] + 1)),
                "region": "exon7",
                "description": "Tra2-beta1 exonic splicing enhancer in exon 7",
            },
            "ess_hnrnpa1": {
                "positions": list(range(ESS_HNRNPA1[0], ESS_HNRNPA1[1] + 1)),
                "region": "exon7",
                "description": "hnRNP A1 exonic splicing silencer in exon 7",
            },
            "iss_n1": {
                "positions": list(range(ISS_N1_INTRON7[0], ISS_N1_INTRON7[1] + 1)),
                "region": "intron7",
                "description": (
                    "Intronic Splicing Silencer N1 — nusinersen (Spinraza) "
                    "antisense oligonucleotide binding target"
                ),
            },
            "element_2": {
                "positions": list(range(ELEMENT_2_INTRON7[0], ELEMENT_2_INTRON7[1] + 1)),
                "region": "intron7",
                "description": "Element 2 regulatory region in intron 7",
            },
        },
    }


def generate_all_snvs() -> list[dict[str, Any]]:
    """Generate ALL possible single-nucleotide variants for the 254-bp region.

    Returns ~762 variants (254 positions x 3 alternate bases each).
    """
    variants: list[dict[str, Any]] = []

    for full_idx in range(len(FULL_REGION)):
        ref_base = FULL_REGION[full_idx]
        exon_pos = _exon_relative_pos(full_idx)
        region = _region_label(exon_pos)

        for alt_base in _BASES:
            if alt_base == ref_base:
                continue

            vid = _variant_id(region, exon_pos, ref_base, alt_base)
            variants.append({
                "position": exon_pos,
                "full_region_index": full_idx,
                "region": region,
                "ref_base": ref_base,
                "alt_base": alt_base,
                "variant_id": vid,
            })

    return variants


def score_variant(variant: dict[str, Any]) -> dict[str, Any]:
    """Score a single variant across 4 dimensions + composite.

    Args:
        variant: dict with at minimum {position, region, ref_base, alt_base, variant_id}

    Returns:
        Input dict augmented with scores, composite_score, and annotation.
    """
    pos = variant["position"]
    region = variant["region"]
    ref = variant["ref_base"]
    alt = variant["alt_base"]

    s1 = _score_splice_site_proximity(pos, region)
    s2 = _score_motif_disruption(pos, region)
    s3 = _score_conservation(pos, region)
    s4 = _score_therapeutic_relevance(pos, region)

    composite = _clamp(
        WEIGHTS["splice_site_proximity"] * s1
        + WEIGHTS["motif_disruption"] * s2
        + WEIGHTS["conservation"] * s3
        + WEIGHTS["therapeutic_relevance"] * s4
    )

    scores = {
        "splice_site_proximity": s1,
        "motif_disruption": s2,
        "conservation": s3,
        "therapeutic_relevance": s4,
        "composite_score": composite,
    }

    annotation = _annotate(pos, region, ref, alt, scores)

    result = {**variant, **scores, "annotation": annotation}
    return result


def score_all_variants() -> list[dict[str, Any]]:
    """Generate and score all ~762 SNVs, sorted by composite_score descending."""
    variants = generate_all_snvs()
    scored = [score_variant(v) for v in variants]
    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    return scored


def get_benchmark_stats() -> dict[str, Any]:
    """Summary statistics for the full benchmark."""
    scored = score_all_variants()
    total = len(scored)

    by_region: dict[str, int] = {}
    high_impact = 0  # composite >= 0.7
    moderate_impact = 0  # composite >= 0.5
    scores = []

    for v in scored:
        region = v["region"]
        by_region[region] = by_region.get(region, 0) + 1
        cs = v["composite_score"]
        scores.append(cs)
        if cs >= 0.7:
            high_impact += 1
        if cs >= 0.5:
            moderate_impact += 1

    scores_sorted = sorted(scores)
    n = len(scores_sorted)

    return {
        "total_variants": total,
        "total_positions": len(FULL_REGION),
        "by_region": by_region,
        "high_impact_count": high_impact,
        "moderate_impact_count": moderate_impact,
        "score_distribution": {
            "min": scores_sorted[0] if scores_sorted else 0,
            "max": scores_sorted[-1] if scores_sorted else 0,
            "median": scores_sorted[n // 2] if scores_sorted else 0,
            "p25": scores_sorted[n // 4] if scores_sorted else 0,
            "p75": scores_sorted[3 * n // 4] if scores_sorted else 0,
            "mean": round(sum(scores) / n, 4) if n else 0,
        },
        "top_10": [
            {"variant_id": v["variant_id"], "composite_score": v["composite_score"]}
            for v in scored[:10]
        ],
        "therapeutic_hotspots": {
            "iss_n1_variants": sum(
                1 for v in scored
                if v["region"] == "intron7"
                and _in_range(v["position"], *ISS_N1_INTRON7)
            ),
            "disease_variant_pos6": sum(
                1 for v in scored if v["region"] == "exon7" and v["position"] == 6
            ),
            "ese_variants": sum(
                1 for v in scored
                if v["region"] == "exon7"
                and (_in_range(v["position"], *ESE_SF2_ASF) or _in_range(v["position"], *ESE_TRA2_BETA))
            ),
        },
    }


def export_benchmark(fmt: str = "csv") -> str:
    """Export the full scored benchmark as CSV or JSON string.

    Args:
        fmt: 'csv' or 'json'

    Returns:
        Formatted string of all scored variants.
    """
    scored = score_all_variants()

    if fmt == "json":
        # Remove full_region_index from export for cleanliness
        export_data = []
        for v in scored:
            row = {k: v for k, v in v.items() if k != "full_region_index"}
            export_data.append(row)
        return json.dumps(export_data, indent=2)

    # CSV format
    fieldnames = [
        "variant_id", "position", "region", "ref_base", "alt_base",
        "splice_site_proximity", "motif_disruption", "conservation",
        "therapeutic_relevance", "composite_score", "annotation",
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for v in scored:
        writer.writerow(v)
    return output.getvalue()
