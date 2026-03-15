"""Prime Editing Feasibility Assessment for SMA (Phase 6.2).

Evaluates prime editing (PE2/PE3/PEmax) feasibility for SMA-relevant edits:
- SMN2 C6T correction (exon 7 position 6: T→C)
- ISS-N1 disruption (intron 7 +10 to +24)
- ESE strengthening / ESS disruption

Prime editing = reverse transcriptase + Cas9 nickase + pegRNA.
No double-strand breaks, no donor template, precise edits.

References:
- Anzalone et al., Nature 2019 (Prime editing)
- Chen et al., Cell 2021 (PE3/PEmax improvements)
- Nelson et al., Nat Biotechnol 2022 (in vivo prime editing)
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# PE2 cargo size: ~6.3 kb (Cas9 nickase + RT + pegRNA)
PE2_CARGO_KB = 6.3
# PEmax cargo: ~6.5 kb (optimized codon + NLS)
PEMAX_CARGO_KB = 6.5
# AAV capacity
AAV_SS_CAPACITY_KB = 4.7
AAV_SC_CAPACITY_KB = 2.3

# Prime editing efficiency ranges from literature
# PE2: 0.1-50% (average ~10-20% for point mutations)
# PE3: 2-70% (average ~30-40%)
# PEmax: 5-75% (average ~40-50%)

# pegRNA design constraints
PEGRNA_PBS_MIN = 8
PEGRNA_PBS_MAX = 17
PEGRNA_RTT_MIN = 10
PEGRNA_RTT_MAX = 40  # Longer RTT for insertions


# ---------------------------------------------------------------------------
# Reference sequences
# ---------------------------------------------------------------------------

SMN2_EXON7 = "GATATTTTATATTAGACAAAATCAAAAAGAAGGAAATGCTGGCATAGAGCAGCAC"
SMN2_INTRON7 = (
    "GTAAGTCTGCCAGCATTATGAAAGTGAATCTTACTTACTCAATATATATATATATATATTT"
    "TTAACAGATGGGAGTTCTGAGTGGACTAAATGTTCACAG"
)
SMN2_INTRON6 = (
    "ATAATTCCCCCACCACCTCCCATATGTCCAGATTCTCTTGATGATGCTGATGCTTTGGGAAG"
    "TATGTTAATTTCATGGTACATGAGTGGCTATCATACTGGCTAG"
)[-100:]
SMN2_REGION = SMN2_INTRON6 + SMN2_EXON7 + SMN2_INTRON7


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class PrimeEditDesign:
    """A prime editing strategy for a specific SMA edit."""
    edit_name: str
    edit_type: str             # 'point_mutation', 'small_deletion', 'small_insertion'
    target_region: str         # 'exon7', 'intron7', etc.
    position: int              # 0-indexed in region
    ref_allele: str
    alt_allele: str
    pe_version: str            # 'PE2', 'PE3', 'PEmax'
    estimated_efficiency: float  # 0-1
    pbs_length: int            # Primer binding site length
    rtt_length: int            # RT template length
    nick_offset: int           # PE3 nicking guide offset
    cargo_size_kb: float
    delivery_feasible: bool    # Can fit in AAV?
    delivery_strategy: str
    biological_impact: str
    clinical_relevance: str
    feasibility_score: float   # 0-1 overall
    challenges: list[str]
    advantages: list[str]


# ---------------------------------------------------------------------------
# Scoring logic
# ---------------------------------------------------------------------------

def _estimate_efficiency(
    edit_type: str,
    gc_content: float,
    pbs_length: int,
    rtt_length: int,
    pe_version: str,
    chromatin_accessibility: float = 0.5,  # 0-1
) -> float:
    """Estimate prime editing efficiency based on edit parameters."""
    # Base efficiency by PE version
    base = {"PE2": 0.15, "PE3": 0.35, "PEmax": 0.45}.get(pe_version, 0.15)

    # Edit type modifier
    type_mod = {
        "point_mutation": 1.0,      # Easiest for PE
        "small_deletion": 0.7,      # 1-10 bp deletions
        "small_insertion": 0.5,     # 1-10 bp insertions
        "large_deletion": 0.2,      # >10 bp
        "large_insertion": 0.15,    # >10 bp
    }.get(edit_type, 0.3)

    # GC content modifier (40-60% optimal)
    if 0.4 <= gc_content <= 0.6:
        gc_mod = 1.0
    elif 0.3 <= gc_content <= 0.7:
        gc_mod = 0.8
    else:
        gc_mod = 0.5

    # PBS length modifier (13 nt optimal for most)
    pbs_mod = 1.0 if 10 <= pbs_length <= 15 else 0.7

    # RTT length modifier (shorter is generally better for point mutations)
    rtt_mod = 1.0 if rtt_length <= 20 else (0.8 if rtt_length <= 30 else 0.6)

    # Chromatin accessibility
    chrom_mod = 0.5 + 0.5 * chromatin_accessibility

    efficiency = base * type_mod * gc_mod * pbs_mod * rtt_mod * chrom_mod
    return round(min(0.75, max(0.01, efficiency)), 3)


def _compute_feasibility(design: dict) -> float:
    """Compute overall feasibility score (0-1)."""
    score = 0.0

    # Efficiency weight: 30%
    score += 0.30 * min(1.0, design["efficiency"] / 0.5)

    # Delivery feasibility: 25%
    score += 0.25 * (1.0 if design["delivery_feasible"] else 0.3)

    # Specificity (point mutations are most specific): 20%
    specificity = {"point_mutation": 1.0, "small_deletion": 0.8, "small_insertion": 0.7}.get(
        design["edit_type"], 0.5
    )
    score += 0.20 * specificity

    # Clinical relevance bonus: 15%
    if "therapeutic" in design.get("impact", "").lower() or "correction" in design.get("impact", "").lower():
        score += 0.15
    elif "disruption" in design.get("impact", "").lower():
        score += 0.10
    else:
        score += 0.05

    # Safety (no DSB): 10%
    score += 0.10  # PE never makes DSBs — inherent advantage

    return round(min(1.0, score), 3)


# ---------------------------------------------------------------------------
# SMA-specific prime editing designs
# ---------------------------------------------------------------------------

def assess_prime_editing_feasibility() -> dict[str, Any]:
    """Assess prime editing feasibility for all SMA-relevant edits."""
    designs = []

    # -----------------------------------------------------------------------
    # Edit 1: SMN2 C6T correction (THE key therapeutic edit)
    # -----------------------------------------------------------------------
    for pe_ver in ["PE2", "PE3", "PEmax"]:
        gc = sum(1 for c in SMN2_EXON7[0:20] if c in "GC") / 20
        pbs = 13
        rtt = 15
        eff = _estimate_efficiency("point_mutation", gc, pbs, rtt, pe_ver, chromatin_accessibility=0.6)
        cargo = {"PE2": PE2_CARGO_KB, "PE3": PE2_CARGO_KB + 0.3, "PEmax": PEMAX_CARGO_KB}.get(pe_ver, PE2_CARGO_KB)

        params = {
            "efficiency": eff,
            "delivery_feasible": False,  # Exceeds AAV capacity
            "edit_type": "point_mutation",
            "impact": "therapeutic correction — restores SMN1-like exon 7 inclusion",
        }

        designs.append(PrimeEditDesign(
            edit_name=f"SMN2 C6T correction ({pe_ver})",
            edit_type="point_mutation",
            target_region="exon7",
            position=5,
            ref_allele="T",
            alt_allele="C",
            pe_version=pe_ver,
            estimated_efficiency=eff,
            pbs_length=pbs,
            rtt_length=rtt,
            nick_offset=52 if pe_ver in ("PE3", "PEmax") else 0,
            cargo_size_kb=cargo,
            delivery_feasible=False,
            delivery_strategy="Dual AAV (split-intein PE) or lipid nanoparticle (mRNA)",
            biological_impact="Corrects the C→T transition at SMN2 exon 7 position 6, "
                              "restoring the ESE motif disrupted in SMN2. Expected to increase "
                              "full-length SMN protein from ~10% to ~90-100% of SMN1 levels.",
            clinical_relevance="HIGH — This is the single most impactful edit for SMA. "
                               "Permanent correction of the root cause (C6T) in every SMN2 copy. "
                               "Functionally converts SMN2 → SMN1.",
            feasibility_score=_compute_feasibility(params),
            challenges=[
                f"PE cargo ({cargo} kb) exceeds AAV capacity ({AAV_SS_CAPACITY_KB} kb) — requires dual vector or non-viral delivery",
                "Split-intein PE demonstrated in vivo but with reduced efficiency",
                "LNP delivery to motor neurons requires optimization for CNS penetration",
                "Off-target editing at SMN1 locus must be assessed (high homology)",
                f"Estimated efficiency: {eff*100:.0f}% — may need multiple doses or selection",
            ],
            advantages=[
                "No double-strand breaks (unlike CRISPR KO)",
                "Single nucleotide correction — most precise possible edit",
                "Does not disrupt surrounding regulatory elements",
                "Works on all SMN2 copies simultaneously",
                "Permanent fix — one treatment could be curative",
                "PE3/PEmax improvements increase efficiency to therapeutic range",
            ],
        ))

    # -----------------------------------------------------------------------
    # Edit 2: ISS-N1 disruption (mimic nusinersen permanently)
    # -----------------------------------------------------------------------
    gc_iss = sum(1 for c in SMN2_INTRON7[10:24] if c in "GC") / 14
    for pe_ver in ["PE3", "PEmax"]:
        eff = _estimate_efficiency("small_deletion", gc_iss, 13, 20, pe_ver, chromatin_accessibility=0.5)
        cargo = {"PE3": PE2_CARGO_KB + 0.3, "PEmax": PEMAX_CARGO_KB}.get(pe_ver, PE2_CARGO_KB)
        params = {
            "efficiency": eff,
            "delivery_feasible": False,
            "edit_type": "small_deletion",
            "impact": "disruption of ISS-N1 silencer",
        }

        designs.append(PrimeEditDesign(
            edit_name=f"ISS-N1 disruption ({pe_ver})",
            edit_type="small_deletion",
            target_region="intron7",
            position=10,
            ref_allele="GAAGTGAATCTTACT",
            alt_allele="---deleted---",
            pe_version=pe_ver,
            estimated_efficiency=eff,
            pbs_length=13,
            rtt_length=20,
            nick_offset=40,
            cargo_size_kb=cargo,
            delivery_feasible=False,
            delivery_strategy="Dual AAV (split-intein PE) or LNP mRNA",
            biological_impact="Permanently disrupts the ISS-N1 silencer element in intron 7 "
                              "(positions +10 to +24). This is the same mechanism as nusinersen "
                              "(Spinraza) but permanent instead of requiring repeated intrathecal injections.",
            clinical_relevance="HIGH — Permanent version of nusinersen mechanism. Eliminates need "
                               "for lifelong intrathecal injections ($750K/year). One-time treatment.",
            feasibility_score=_compute_feasibility(params),
            challenges=[
                "15 bp deletion is less efficient than point mutations in PE",
                f"Cargo size ({cargo} kb) still exceeds AAV capacity",
                "Must avoid disrupting nearby splice donor site (intron 7 +1 to +6)",
                "AT-rich region around ISS-N1 may reduce pegRNA stability",
            ],
            advantages=[
                "Permanent nusinersen-like effect",
                "Well-validated target (>10 years of clinical nusinersen data)",
                "No DSBs — safer than CRISPR KO approach",
                "Blocks hnRNP A1 binding permanently",
            ],
        ))

    # -----------------------------------------------------------------------
    # Edit 3: ESE strengthening at Tra2-beta site
    # -----------------------------------------------------------------------
    eff_ese = _estimate_efficiency("point_mutation", 0.45, 13, 15, "PEmax", chromatin_accessibility=0.6)
    params_ese = {
        "efficiency": eff_ese,
        "delivery_feasible": False,
        "edit_type": "point_mutation",
        "impact": "therapeutic enhancer strengthening",
    }
    designs.append(PrimeEditDesign(
        edit_name="ESE strengthening at Tra2-beta site (PEmax)",
        edit_type="point_mutation",
        target_region="exon7",
        position=22,
        ref_allele="A",
        alt_allele="G",
        pe_version="PEmax",
        estimated_efficiency=eff_ese,
        pbs_length=13,
        rtt_length=15,
        nick_offset=45,
        cargo_size_kb=PEMAX_CARGO_KB,
        delivery_feasible=False,
        delivery_strategy="Dual AAV or LNP mRNA",
        biological_impact="Strengthens the Tra2-beta binding ESE in exon 7 (positions 19-27). "
                          "Enhanced Tra2-beta binding promotes exon 7 inclusion in SMN2 mRNA. "
                          "Complementary to C6T correction — could work synergistically.",
        clinical_relevance="MODERATE — Experimental. Less validated than C6T correction or ISS-N1 "
                           "disruption, but could provide additional benefit in combination.",
        feasibility_score=_compute_feasibility(params_ese),
        challenges=[
            "Tra2-beta ESE function not as well characterized as ISS-N1",
            "Effect size uncertain — may not be sufficient alone",
            "Cargo delivery same challenge as other PE approaches",
        ],
        advantages=[
            "Precise single-nucleotide enhancement",
            "Could combine with C6T correction for maximal effect",
            "Orthogonal mechanism to antisense approaches",
        ],
    ))

    # -----------------------------------------------------------------------
    # Comparison with other approaches
    # -----------------------------------------------------------------------
    comparison = [
        {
            "approach": "Prime Editing (C6T correction)",
            "precision": "Single nucleotide",
            "permanence": "Permanent (one-time)",
            "delivery": "Dual AAV / LNP mRNA",
            "safety": "No DSBs — high safety profile",
            "efficiency": "15-45% (PE2-PEmax)",
            "cost_model": "One-time (vs $750K/year nusinersen)",
            "maturity": "Preclinical (in vivo PE demonstrated in mice/NHP)",
        },
        {
            "approach": "Nusinersen (ASO)",
            "precision": "ISS-N1 blocking (steric)",
            "permanence": "Temporary (repeated IT injections)",
            "delivery": "Intrathecal (proven)",
            "safety": "Good (10+ years clinical data)",
            "efficiency": "~50-60% exon 7 inclusion increase",
            "cost_model": "$750K/year lifetime",
            "maturity": "FDA-approved 2016 (>13,000 patients)",
        },
        {
            "approach": "Risdiplam (small molecule)",
            "precision": "SMN2 splicing modifier",
            "permanence": "Temporary (daily oral)",
            "delivery": "Oral (proven, crosses BBB)",
            "safety": "Good (4+ years clinical data)",
            "efficiency": "~2x SMN protein increase",
            "cost_model": "$340K/year lifetime",
            "maturity": "FDA-approved 2020",
        },
        {
            "approach": "Zolgensma (AAV9-SMN1)",
            "precision": "Full gene replacement",
            "permanence": "Permanent (one-time IV)",
            "delivery": "AAV9 IV (proven in neonates)",
            "safety": "Hepatotoxicity risk (dose-limiting)",
            "efficiency": "High (SMN1 expression from transgene)",
            "cost_model": "$2.1M one-time",
            "maturity": "FDA-approved 2019 (>3,000 patients)",
        },
        {
            "approach": "CRISPRi/dCas9 (ISS-N1 silencing)",
            "precision": "Regional (guide RNA targeting)",
            "permanence": "Permanent (epigenetic)",
            "delivery": "Dual AAV (split dCas9)",
            "safety": "No DSBs — moderate safety profile",
            "efficiency": "Variable (depends on guide + dCas9 expression)",
            "cost_model": "One-time (estimated $1-3M)",
            "maturity": "Preclinical (dCas9 in vivo demonstrated)",
        },
    ]

    # Sort by feasibility score
    designs.sort(key=lambda d: d.feasibility_score, reverse=True)
    for i, d in enumerate(designs):
        d_dict = asdict(d)
        d_dict["rank"] = i + 1

    return {
        "title": "Prime Editing Feasibility Assessment for SMA",
        "total_designs": len(designs),
        "top_edit": designs[0].edit_name if designs else None,
        "designs": [asdict(d) for d in designs],
        "comparison_with_approved_therapies": comparison,
        "key_insight": "Prime editing offers the most precise permanent correction (single nucleotide C6T fix) "
                       "but delivery remains the primary challenge. Split-intein dual-AAV or LNP mRNA approaches "
                       "are the most promising delivery strategies. PE could eventually replace lifelong ASO/small molecule therapy.",
        "delivery_challenge": {
            "problem": f"PE2/PEmax cargo ({PE2_CARGO_KB}-{PEMAX_CARGO_KB} kb) exceeds AAV packaging limit ({AAV_SS_CAPACITY_KB} kb)",
            "solutions": [
                "Split-intein dual AAV: PE split into N-terminal + C-terminal, reconstituted in cell (Nelson et al., 2022)",
                "LNP mRNA: Lipid nanoparticle delivery of PE mRNA + pegRNA (non-viral, BBB challenge)",
                "Engineered smaller PE: Mini-PE variants under development (~4.5 kb)",
                "Non-viral nanoparticles: PBAE, cyclodextrin, or exosome-based delivery",
            ],
        },
    }
