"""ASO (Antisense Oligonucleotide) Sequence Generator for SMA.

Generates novel ASO sequences targeting SMN2 pre-mRNA regulatory elements
to promote exon 7 inclusion — the same therapeutic mechanism as nusinersen
(Spinraza), the first FDA-approved SMA drug.

Key biology:
- SMN2 exon 7 is skipped ~90% of the time due to C6T (vs SMN1)
- Nusinersen is an 18-nt 2'-MOE phosphorothioate ASO targeting ISS-N1
  in intron 7 (+10 to +24), blocking hnRNP A1 repressor binding
- Additional regulatory elements (ISS-N2, ESS, Element2) offer
  alternative or complementary ASO targets
- ASO design must balance: target affinity, GC content, self-complementarity
  avoidance, melting temperature, and BBB penetration potential

Chemistry:
- 2'-O-methoxyethyl (2'-MOE) sugar modification — gold standard for CNS ASOs
- Phosphorothioate (PS) backbone — nuclease resistance + protein binding
- Length 15-25 nt — shorter = better BBB penetration, longer = tighter binding

References:
- Hua et al. (2008) Antisense masking of an hnRNP A1/A2 intronic splicing
  silencer corrects SMN2 splicing in transgenic mice. Am J Hum Genet.
- Singh et al. (2006) A short antisense oligonucleotide masking a unique
  intronic motif prevents skipping of a critical exon in SMA. RNA Biol.
"""

from __future__ import annotations

import hashlib
import logging
import math
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants: SMN2 target regions
# ---------------------------------------------------------------------------

SMN2_REGIONS: dict[str, dict[str, Any]] = {
    "ISS-N1": {
        "sequence": "CCAGCATTATGAAAG",
        "location": "intron 7, +10 to +24",
        "mechanism": "Blocks hnRNP A1 binding, promotes exon 7 inclusion",
        "reference_aso": "nusinersen (5'-TCACTTTCATAATGCTGG-3')",
        "flanking_5p": "GTAAGTCTGC",  # intron 7 +0 to +9
        "flanking_3p": "TGAATCTTAC",  # intron 7 +25 to +34
    },
    "ISS-N2": {
        "sequence": "GCCTGAGAACTTT",
        "location": "intron 7, +69 to +81",
        "mechanism": "Secondary splicing silencer, cooperates with ISS-N1",
        "flanking_5p": "ATATATATTT",
        "flanking_3p": "TTAACAGATG",
    },
    "ESS_exon7": {
        "sequence": "TAAAGATTTTAAGCTG",
        "location": "exon 7, +35 to +51",
        "mechanism": "Exonic Splicing Silencer — hnRNP A1/A2 binding",
        "flanking_5p": "AAGGAAATGC",
        "flanking_3p": "GCATAGAGCA",
    },
    "element2": {
        "sequence": "AGGAA",
        "location": "exon 7, +7 to +11",
        "mechanism": "Key regulatory element affected by C6T — SF2/ASF binding disrupted in SMN2",
        "flanking_5p": "GATATTTTAT",
        "flanking_3p": "TGCTGGCATA",
    },
}

# Nusinersen reference
NUSINERSEN = {
    "sequence": "TCACTTTCATAATGCTGG",
    "length": 18,
    "target": "ISS-N1",
    "chemistry": "2'-MOE phosphorothioate, fully modified",
    "gc_content": 0.389,
    "tm_estimate": 59.2,
    "fda_approved": 2016,
    "brand_name": "Spinraza",
    "dosing": "12 mg intrathecal injection",
}

# Nearest-neighbor thermodynamic parameters (SantaLucia 1998)
# ΔH (kcal/mol) and ΔS (cal/mol·K) for DNA/RNA hybrid duplexes
# Simplified — uses DNA/DNA parameters as approximation
NN_PARAMS: dict[str, tuple[float, float]] = {
    "AA": (-7.9, -22.2),
    "AT": (-7.2, -20.4),
    "AG": (-7.8, -21.0),
    "AC": (-8.4, -22.4),
    "TA": (-7.2, -21.3),
    "TT": (-7.9, -22.2),
    "TG": (-8.5, -22.7),
    "TC": (-8.2, -22.2),
    "GA": (-8.2, -22.2),
    "GT": (-8.4, -22.4),
    "GG": (-8.0, -19.9),
    "GC": (-9.8, -24.4),
    "CA": (-8.5, -22.7),
    "CT": (-7.8, -21.0),
    "CG": (-10.6, -27.2),
    "CC": (-8.0, -19.9),
}

# Initiation parameters
NN_INIT_H = 0.1   # kcal/mol
NN_INIT_S = -2.8   # cal/mol·K

# ---------------------------------------------------------------------------
# Chemistry recommendations per target region
# ---------------------------------------------------------------------------

CHEMISTRY_BY_REGION: dict[str, dict[str, str]] = {
    "ISS-N1": {
        "sugar": "2'-O-methoxyethyl (2'-MOE) at all positions",
        "backbone": "Full phosphorothioate (PS)",
        "bases": "5-methylcytosine at all CpG sites",
        "design": "Steric-blocker (mixmer or fully modified)",
        "note": "Same chemistry class as nusinersen (Spinraza). "
                "Blocks hnRNP A1/A2 access to ISS-N1 by steric occlusion.",
        "delivery": "Intrathecal injection (proven CNS route)",
    },
    "ISS-N2": {
        "sugar": "2'-O-methoxyethyl (2'-MOE) at all positions",
        "backbone": "Full phosphorothioate (PS)",
        "bases": "5-methylcytosine at all CpG sites",
        "design": "Steric-blocker (fully modified)",
        "note": "Secondary silencer — may synergize with ISS-N1-targeting ASOs. "
                "Consider combination therapy with nusinersen.",
        "delivery": "Intrathecal injection",
    },
    "ESS_exon7": {
        "sugar": "2'-O-methoxyethyl (2'-MOE) or PMO (phosphorodiamidate morpholino)",
        "backbone": "Full phosphorothioate (PS) for 2'-MOE; charge-neutral for PMO",
        "bases": "5-methylcytosine at all CpG sites (for 2'-MOE)",
        "design": "Steric-blocker — exonic target requires careful splice-site avoidance",
        "note": "Exonic targeting carries higher off-target risk — must confirm no "
                "disruption of ESE elements. PMO chemistry avoids RNase H cleavage.",
        "delivery": "Intrathecal injection; PMO may offer better safety profile",
    },
    "element2": {
        "sugar": "PMO (phosphorodiamidate morpholino) preferred; 2'-MOE alternative",
        "backbone": "Charge-neutral (PMO) or phosphorothioate (2'-MOE)",
        "bases": "Standard (PMO) or 5-methylcytosine (2'-MOE)",
        "design": "Enhancer-modulating — steric block to redirect splicing factor binding",
        "note": "Element 2 is a short exonic motif (AGGAA) affected by C6T. "
                "Targeting requires extended flanking to achieve 15+ nt length. "
                "PMO avoids immune stimulation risk in this exonic context.",
        "delivery": "Intrathecal injection; consider peptide-PMO conjugate for enhanced uptake",
    },
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ASOCandidate:
    """A designed ASO candidate."""
    id: str
    sequence: str
    length: int
    target_region: str
    target_location: str
    position_offset: int         # offset within extended target window
    gc_content: float
    tm_estimate: float           # predicted melting temperature (°C)
    binding_energy: float        # predicted ΔG at 37°C (kcal/mol), more negative = stronger
    self_complementarity_score: float  # 0-1, lower is better (less self-pairing)
    bbb_score: float             # 0-1, predicted BBB penetration likelihood
    target_complementarity: float  # 0-1, fraction of perfect base pairing
    overall_score: float
    chemistry_modifications: dict[str, str]
    mechanism: str
    comparison_to_nusinersen: str


# ---------------------------------------------------------------------------
# Sequence utilities
# ---------------------------------------------------------------------------

_COMPLEMENT = {"A": "T", "T": "A", "G": "C", "C": "G", "N": "N"}


def _complement(seq: str) -> str:
    """Return DNA complement."""
    return "".join(_COMPLEMENT.get(c, "N") for c in seq.upper())


def _reverse_complement(seq: str) -> str:
    """Return reverse complement (antisense strand)."""
    return _complement(seq)[::-1]


def _gc_content(seq: str) -> float:
    """Calculate GC content as fraction 0-1."""
    if not seq:
        return 0.0
    gc = sum(1 for c in seq.upper() if c in "GC")
    return round(gc / len(seq), 3)


def _tm_nearest_neighbor(seq: str, oligo_conc_nm: float = 250.0, na_conc_m: float = 0.15) -> float:
    """Estimate melting temperature using nearest-neighbor method.

    Uses SantaLucia (1998) unified parameters. Includes salt correction.
    For 2'-MOE ASOs, Tm is typically 1-2°C higher per modification — we add
    a chemistry bonus since all positions are modified.

    Args:
        seq: ASO sequence (DNA notation)
        oligo_conc_nm: oligonucleotide concentration in nM
        na_conc_m: sodium ion concentration in M
    """
    seq = seq.upper()
    n = len(seq)
    if n < 2:
        return 0.0

    # Sum ΔH and ΔS for all nearest-neighbor pairs
    dH = NN_INIT_H
    dS = NN_INIT_S

    for i in range(n - 1):
        dinuc = seq[i:i + 2]
        h, s = NN_PARAMS.get(dinuc, (-7.5, -21.0))  # fallback for ambiguous
        dH += h
        dS += s

    # Convert oligo concentration to M, use non-self-complementary formula
    ct = oligo_conc_nm * 1e-9
    R = 1.987  # cal/(mol·K)

    # Tm = ΔH / (ΔS + R·ln(Ct/4)) - 273.15
    try:
        tm = (dH * 1000) / (dS + R * math.log(ct / 4)) - 273.15
    except (ValueError, ZeroDivisionError):
        # Fallback to simple 2+4 rule
        gc = sum(1 for c in seq if c in "GC")
        at = n - gc
        tm = 2 * at + 4 * gc

    # Salt correction (Owczarzy 2004 simplified)
    if na_conc_m > 0:
        tm += 16.6 * math.log10(na_conc_m)

    # 2'-MOE chemistry bonus: ~1.5°C per modification (fully modified)
    moe_bonus = n * 1.5

    return round(tm + moe_bonus, 1)


def _tm_simple(seq: str) -> float:
    """Simple Tm estimate using the Wallace rule (2+4 rule).

    For short oligos (<14 nt): Tm = 2(A+T) + 4(G+C)
    For longer oligos: use a modified version.
    """
    seq = seq.upper()
    gc = sum(1 for c in seq if c in "GC")
    at = len(seq) - gc

    if len(seq) < 14:
        return float(2 * at + 4 * gc)

    # Modified for longer oligos: 64.9 + 41*(G+C-16.4)/N
    n = len(seq)
    return round(64.9 + 41 * (gc - 16.4) / n, 1)


def _self_complementarity(seq: str) -> float:
    """Score self-complementarity risk (0 = no risk, 1 = high risk).

    Checks for internal hairpins and self-dimers by looking at all
    possible self-pairings >=4 nt.
    """
    seq = seq.upper()
    n = len(seq)
    rc = _reverse_complement(seq)

    max_match = 0

    # Check for self-dimer: slide sequence against its reverse complement
    for offset in range(-(n - 4), n - 3):
        matches = 0
        for i in range(n):
            j = i + offset
            if 0 <= j < n:
                if seq[i] == rc[j]:
                    matches += 1
        max_match = max(max_match, matches)

    # Normalize: what fraction of the sequence can self-pair
    score = max_match / n if n > 0 else 0
    return round(min(1.0, score), 3)


def _bbb_score(length: int, gc_content: float) -> float:
    """Predict blood-brain barrier penetration likelihood.

    Shorter ASOs penetrate BBB better (intrathecal delivery is standard,
    but systemic delivery is the goal). Key factors:
    - Length: shorter = better (15-18 optimal for systemic)
    - Molecular weight: lower = better
    - PS backbone: helps protein binding and cellular uptake
    - 2'-MOE: improves stability but increases MW

    This is a simplified heuristic; real BBB penetration requires
    in vivo pharmacokinetic studies.
    """
    score = 0.5

    # Length penalty/bonus (nusinersen is 18, works intrathecally)
    if length <= 16:
        score += 0.25  # shorter = better BBB penetration
    elif length <= 18:
        score += 0.15
    elif length <= 20:
        score += 0.05
    elif length <= 22:
        score -= 0.05
    else:
        score -= 0.15  # 23-25 nt — poor systemic BBB penetration

    # GC content: moderate GC helps cellular uptake
    if 0.4 <= gc_content <= 0.6:
        score += 0.1
    elif 0.35 <= gc_content <= 0.65:
        score += 0.05

    # PS backbone bonus (assumed for all candidates)
    score += 0.1

    # 2'-MOE bonus (metabolic stability helps CNS exposure)
    score += 0.05

    return round(max(0.0, min(1.0, score)), 3)


def _binding_energy(seq: str, temp_c: float = 37.0) -> float:
    """Estimate Gibbs free energy (ΔG) at a given temperature.

    Uses the nearest-neighbor thermodynamic parameters.
    ΔG = ΔH - T·ΔS (at the specified temperature, default 37°C).

    For 2'-MOE ASOs hybridized to RNA, actual ΔG is typically ~1-2 kcal/mol
    more favorable — we add a chemistry correction.

    Returns:
        ΔG in kcal/mol (more negative = stronger binding).
    """
    seq = seq.upper()
    n = len(seq)
    if n < 2:
        return 0.0

    dH = NN_INIT_H  # kcal/mol
    dS = NN_INIT_S  # cal/mol·K

    for i in range(n - 1):
        dinuc = seq[i:i + 2]
        h, s = NN_PARAMS.get(dinuc, (-7.5, -21.0))
        dH += h
        dS += s

    temp_k = temp_c + 273.15
    dG = dH - (temp_k * dS / 1000.0)  # convert dS from cal to kcal

    # 2'-MOE chemistry correction: ~0.5 kcal/mol more stable per modification
    # (conservative estimate; literature reports 0.3-1.0 kcal/mol per mod)
    moe_correction = -0.5 * n

    return round(dG + moe_correction, 2)


def _sequence_hash(seq: str, target: str) -> str:
    """Generate a short deterministic ID for an ASO candidate."""
    h = hashlib.md5(f"{seq}:{target}".encode()).hexdigest()[:8]
    return f"ASO-{target[:4].upper()}-{h}"


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------

def _generate_candidates_for_region(
    region_key: str,
    n_candidates: int = 20,
) -> list[ASOCandidate]:
    """Generate ASO candidates by sliding windows across a target region.

    Strategy: take the target sequence + flanking regions, then generate
    antisense oligos of varying lengths (15-25 nt) at different positions
    across this extended window.
    """
    region = SMN2_REGIONS[region_key]
    target_seq = region["sequence"].upper()
    flank_5p = region.get("flanking_5p", "").upper()
    flank_3p = region.get("flanking_3p", "").upper()

    # Extended target window: flanking + target + flanking
    extended = flank_5p + target_seq + flank_3p
    ext_len = len(extended)

    candidates: list[ASOCandidate] = []
    seen: set[str] = set()

    # Generate ASOs of varying length across the window
    for aso_len in range(15, 26):  # 15 to 25 nt
        for start in range(0, ext_len - aso_len + 1):
            sense_fragment = extended[start:start + aso_len]
            aso_seq = _reverse_complement(sense_fragment)

            if aso_seq in seen:
                continue
            seen.add(aso_seq)

            gc = _gc_content(aso_seq)
            tm = _tm_nearest_neighbor(aso_seq)
            dG = _binding_energy(aso_seq)
            self_comp = _self_complementarity(aso_seq)
            bbb = _bbb_score(aso_len, gc)

            # Target complementarity: how much of the ASO overlaps
            # with the core target (not flanking)
            flank_5p_len = len(flank_5p)
            target_len = len(target_seq)
            overlap_start = max(start, flank_5p_len)
            overlap_end = min(start + aso_len, flank_5p_len + target_len)
            overlap = max(0, overlap_end - overlap_start)
            complementarity = overlap / target_len if target_len > 0 else 0.0
            complementarity = round(min(1.0, complementarity), 3)

            # Comparison note to nusinersen
            comparison = _quick_nusinersen_comparison(aso_seq, region_key)

            # Overall score: weighted combination
            # - Target complementarity (30%): want high overlap with regulatory element
            # - GC content optimality (20%): 40-60% ideal
            # - Low self-complementarity (15%): avoid hairpins
            # - Tm in therapeutic range (15%): 55-75°C ideal for 2'-MOE
            # - BBB penetration (20%): shorter and moderate GC
            gc_score = 1.0 - abs(gc - 0.50) * 2  # peaks at 50% GC
            gc_score = max(0.0, gc_score)

            tm_score = 0.0
            if 55 <= tm <= 75:
                tm_score = 1.0 - abs(tm - 65) / 10  # peaks at 65°C
            elif 45 <= tm <= 85:
                tm_score = 0.3

            self_comp_score = 1.0 - self_comp  # lower self-comp is better

            overall = (
                0.30 * complementarity
                + 0.20 * gc_score
                + 0.15 * self_comp_score
                + 0.15 * max(0, tm_score)
                + 0.20 * bbb
            )

            # Use region-specific chemistry recommendations
            chem = CHEMISTRY_BY_REGION.get(region_key, CHEMISTRY_BY_REGION["ISS-N1"])

            candidates.append(ASOCandidate(
                id=_sequence_hash(aso_seq, region_key),
                sequence=aso_seq,
                length=aso_len,
                target_region=region_key,
                target_location=region["location"],
                position_offset=start - len(flank_5p),
                gc_content=gc,
                tm_estimate=tm,
                binding_energy=dG,
                self_complementarity_score=round(self_comp, 3),
                bbb_score=bbb,
                target_complementarity=complementarity,
                overall_score=round(overall, 3),
                chemistry_modifications=chem,
                mechanism=region["mechanism"],
                comparison_to_nusinersen=comparison,
            ))

    # Sort by overall score descending
    candidates.sort(key=lambda c: c.overall_score, reverse=True)
    return candidates[:n_candidates]


def _quick_nusinersen_comparison(aso_seq: str, target_region: str) -> str:
    """Generate a brief comparison note to nusinersen."""
    nus_seq = NUSINERSEN["sequence"]
    aso_len = len(aso_seq)

    if target_region == "ISS-N1":
        # Check sequence overlap
        overlap = _count_overlap(aso_seq, nus_seq)
        if aso_seq == nus_seq:
            return "Identical to nusinersen"
        elif overlap >= len(nus_seq) * 0.8:
            return f"High overlap with nusinersen ({overlap}/{len(nus_seq)} nt shared)"
        elif overlap >= len(nus_seq) * 0.5:
            return f"Partial overlap with nusinersen ({overlap}/{len(nus_seq)} nt shared)"
        else:
            return f"Low overlap with nusinersen — targets adjacent ISS-N1 region"
    else:
        return f"Novel target ({target_region}) — not targeted by nusinersen"


def _count_overlap(seq1: str, seq2: str) -> int:
    """Count the maximum overlapping nucleotides between two sequences."""
    seq1 = seq1.upper()
    seq2 = seq2.upper()
    max_overlap = 0

    # Slide seq2 across seq1
    for offset in range(-(len(seq2) - 1), len(seq1)):
        matches = 0
        for i in range(len(seq1)):
            j = i - offset
            if 0 <= j < len(seq2):
                if seq1[i] == seq2[j]:
                    matches += 1
        max_overlap = max(max_overlap, matches)

    return max_overlap


# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------

async def generate_aso_candidates(
    target_region: str = "ISS-N1",
    n_candidates: int = 20,
) -> list[dict[str, Any]]:
    """Generate novel ASO candidates targeting a SMN2 regulatory region.

    Args:
        target_region: One of ISS-N1, ISS-N2, ESS_exon7, element2
        n_candidates: Number of top candidates to return (max 50)

    Returns:
        List of ASO candidate dicts, sorted by overall_score descending.
    """
    if target_region not in SMN2_REGIONS:
        available = ", ".join(SMN2_REGIONS.keys())
        return [{"error": f"Unknown target region '{target_region}'. Available: {available}"}]

    n_candidates = max(1, min(50, n_candidates))

    logger.info("Generating %d ASO candidates for %s", n_candidates, target_region)
    candidates = _generate_candidates_for_region(target_region, n_candidates)

    return [asdict(c) for c in candidates]


async def compare_to_nusinersen(aso_sequence: str) -> dict[str, Any]:
    """Compare a candidate ASO sequence to nusinersen (Spinraza).

    Compares on: length, GC content, target overlap, predicted binding
    affinity (via Tm), self-complementarity, and BBB penetration score.

    Args:
        aso_sequence: The ASO sequence to compare (DNA notation, 5'->3')

    Returns:
        Dict with side-by-side comparison metrics.
    """
    aso_seq = aso_sequence.upper().strip()

    if not aso_seq or not all(c in "ATGCN" for c in aso_seq):
        return {"error": "Invalid sequence — must contain only A, T, G, C, N"}

    if len(aso_seq) < 10 or len(aso_seq) > 30:
        return {"error": "Sequence length must be 10-30 nt"}

    nus_seq = NUSINERSEN["sequence"]

    # Candidate metrics
    aso_gc = _gc_content(aso_seq)
    aso_tm = _tm_nearest_neighbor(aso_seq)
    aso_dG = _binding_energy(aso_seq)
    aso_self_comp = _self_complementarity(aso_seq)
    aso_bbb = _bbb_score(len(aso_seq), aso_gc)

    # Nusinersen metrics
    nus_gc = _gc_content(nus_seq)
    nus_tm = _tm_nearest_neighbor(nus_seq)
    nus_dG = _binding_energy(nus_seq)
    nus_self_comp = _self_complementarity(nus_seq)
    nus_bbb = _bbb_score(len(nus_seq), nus_gc)

    # Sequence overlap
    overlap = _count_overlap(aso_seq, nus_seq)

    # Target overlap with ISS-N1
    iss_n1 = _reverse_complement(SMN2_REGIONS["ISS-N1"]["sequence"])
    aso_target_overlap = _count_overlap(aso_seq, iss_n1)
    nus_target_overlap = _count_overlap(nus_seq, iss_n1)

    # Advantages/disadvantages
    advantages = []
    disadvantages = []

    if aso_gc > nus_gc and 0.4 <= aso_gc <= 0.6:
        advantages.append("Better GC content (closer to 50% ideal)")
    elif nus_gc > aso_gc and 0.4 <= nus_gc <= 0.6:
        disadvantages.append("GC content further from 50% ideal than nusinersen")

    if aso_tm > nus_tm:
        advantages.append(f"Higher predicted Tm ({aso_tm}°C vs {nus_tm}°C) — stronger binding")
    elif aso_tm < nus_tm - 5:
        disadvantages.append(f"Lower predicted Tm ({aso_tm}°C vs {nus_tm}°C) — weaker binding")

    if aso_self_comp < nus_self_comp:
        advantages.append("Lower self-complementarity risk")
    elif aso_self_comp > nus_self_comp + 0.1:
        disadvantages.append("Higher self-complementarity risk (potential hairpin formation)")

    if len(aso_seq) < len(nus_seq):
        advantages.append(f"Shorter ({len(aso_seq)} vs {len(nus_seq)} nt) — potentially better BBB penetration")
    elif len(aso_seq) > len(nus_seq) + 2:
        disadvantages.append(f"Longer ({len(aso_seq)} vs {len(nus_seq)} nt) — may reduce BBB penetration")

    if aso_bbb > nus_bbb:
        advantages.append("Better predicted BBB penetration score")

    if aso_dG < nus_dG:
        advantages.append(f"Stronger predicted binding (ΔG {aso_dG} vs {nus_dG} kcal/mol)")
    elif aso_dG > nus_dG + 3:
        disadvantages.append(f"Weaker predicted binding (ΔG {aso_dG} vs {nus_dG} kcal/mol)")

    return {
        "candidate": {
            "sequence": aso_seq,
            "length": len(aso_seq),
            "gc_content": aso_gc,
            "tm_estimate": aso_tm,
            "binding_energy_kcal_mol": aso_dG,
            "self_complementarity": aso_self_comp,
            "bbb_score": aso_bbb,
            "iss_n1_overlap": aso_target_overlap,
        },
        "nusinersen": {
            "sequence": nus_seq,
            "length": len(nus_seq),
            "gc_content": nus_gc,
            "tm_estimate": nus_tm,
            "binding_energy_kcal_mol": nus_dG,
            "self_complementarity": nus_self_comp,
            "bbb_score": nus_bbb,
            "iss_n1_overlap": nus_target_overlap,
            "brand_name": "Spinraza",
            "fda_approved": 2016,
            "chemistry": "2'-MOE phosphorothioate, fully modified",
        },
        "sequence_overlap": {
            "shared_nucleotides": overlap,
            "fraction_of_nusinersen": round(overlap / len(nus_seq), 3),
        },
        "advantages": advantages if advantages else ["No clear advantages identified"],
        "disadvantages": disadvantages if disadvantages else ["No clear disadvantages identified"],
        "verdict": _comparison_verdict(advantages, disadvantages),
    }


def _comparison_verdict(advantages: list[str], disadvantages: list[str]) -> str:
    """Generate a summary verdict."""
    n_adv = len(advantages)
    n_dis = len(disadvantages)

    if n_adv > n_dis + 1:
        return "Promising candidate — shows multiple improvements over nusinersen in silico. Warrants experimental validation."
    elif n_adv > n_dis:
        return "Potentially interesting — marginal in silico improvements. Consider for experimental screening panel."
    elif n_adv == n_dis:
        return "Comparable to nusinersen in silico. Novelty depends on target region and mechanism differences."
    else:
        return "Nusinersen appears superior on these metrics. Consider alternative design strategies."


async def get_target_regions() -> list[dict[str, Any]]:
    """Return all known SMN2 regulatory regions targetable by ASOs.

    Returns:
        List of dicts with region name, sequence, location, mechanism,
        and whether a reference ASO exists.
    """
    regions = []
    for key, info in SMN2_REGIONS.items():
        region = {
            "name": key,
            "sequence": info["sequence"],
            "length": len(info["sequence"]),
            "antisense_complement": _reverse_complement(info["sequence"]),
            "location": info["location"],
            "mechanism": info["mechanism"],
            "gc_content": _gc_content(info["sequence"]),
            "has_reference_aso": "reference_aso" in info,
        }
        if "reference_aso" in info:
            region["reference_aso"] = info["reference_aso"]
        regions.append(region)

    return regions


async def score_custom_aso(
    sequence: str,
    target: str = "ISS-N1",
) -> dict[str, Any]:
    """Score a user-provided ASO sequence against a target region.

    Evaluates the ASO on all design criteria: complementarity to target,
    GC content, Tm, self-complementarity, and BBB penetration.

    Args:
        sequence: ASO sequence in DNA notation (5'->3')
        target: Target region key (default: ISS-N1)

    Returns:
        Dict with comprehensive scoring and design feedback.
    """
    seq = sequence.upper().strip()

    if not seq or not all(c in "ATGCN" for c in seq):
        return {"error": "Invalid sequence — must contain only A, T, G, C, N"}

    if len(seq) < 10 or len(seq) > 30:
        return {"error": "Sequence length must be 10-30 nt"}

    if target not in SMN2_REGIONS:
        available = ", ".join(SMN2_REGIONS.keys())
        return {"error": f"Unknown target '{target}'. Available: {available}"}

    region = SMN2_REGIONS[target]
    target_seq = region["sequence"].upper()

    # Compute metrics
    gc = _gc_content(seq)
    tm_nn = _tm_nearest_neighbor(seq)
    tm_simple = _tm_simple(seq)
    dG = _binding_energy(seq)
    self_comp = _self_complementarity(seq)
    bbb = _bbb_score(len(seq), gc)

    # Target complementarity: compare ASO to the reverse complement of target
    target_rc = _reverse_complement(target_seq)
    overlap = _count_overlap(seq, target_rc)
    complementarity = round(overlap / len(target_seq), 3) if target_seq else 0.0

    # GC score
    gc_score = max(0.0, 1.0 - abs(gc - 0.50) * 2)

    # Tm score
    tm_score = 0.0
    if 55 <= tm_nn <= 75:
        tm_score = 1.0 - abs(tm_nn - 65) / 10
    elif 45 <= tm_nn <= 85:
        tm_score = 0.3

    self_comp_score = 1.0 - self_comp

    overall = (
        0.30 * min(1.0, complementarity)
        + 0.20 * gc_score
        + 0.15 * self_comp_score
        + 0.15 * max(0, tm_score)
        + 0.20 * bbb
    )

    # Design feedback
    feedback = []
    if gc < 0.35:
        feedback.append("Low GC content — may have weak target binding")
    elif gc > 0.65:
        feedback.append("High GC content — risk of off-target binding and aggregation")
    else:
        feedback.append("GC content in optimal range (40-60%)")

    if tm_nn < 50:
        feedback.append("Low predicted Tm — may not form stable duplex at 37°C")
    elif tm_nn > 80:
        feedback.append("Very high Tm — strong binding but potential off-target issues")
    else:
        feedback.append(f"Tm ({tm_nn}°C) in therapeutic range")

    if self_comp > 0.5:
        feedback.append("High self-complementarity — likely forms hairpin structures")
    elif self_comp > 0.3:
        feedback.append("Moderate self-complementarity — check for secondary structures")
    else:
        feedback.append("Low self-complementarity — good")

    if len(seq) <= 18:
        feedback.append("Length suitable for systemic/intrathecal delivery")
    elif len(seq) <= 22:
        feedback.append("Moderate length — intrathecal delivery preferred")
    else:
        feedback.append("Long ASO — likely requires intrathecal delivery only")

    if complementarity >= 0.8:
        feedback.append(f"Excellent complementarity to {target}")
    elif complementarity >= 0.5:
        feedback.append(f"Partial complementarity to {target}")
    else:
        feedback.append(f"Low complementarity to {target} — may be targeting a different region")

    return {
        "sequence": seq,
        "length": len(seq),
        "target": target,
        "target_sequence": target_seq,
        "target_antisense": target_rc,
        "metrics": {
            "gc_content": gc,
            "tm_nearest_neighbor": tm_nn,
            "tm_simple_rule": tm_simple,
            "binding_energy_kcal_mol": dG,
            "self_complementarity": self_comp,
            "bbb_penetration_score": bbb,
            "target_complementarity": min(1.0, complementarity),
        },
        "scores": {
            "gc_score": round(gc_score, 3),
            "tm_score": round(max(0, tm_score), 3),
            "self_comp_score": round(self_comp_score, 3),
            "bbb_score": bbb,
            "complementarity_score": round(min(1.0, complementarity), 3),
            "overall_score": round(overall, 3),
        },
        "chemistry": CHEMISTRY_BY_REGION.get(target, CHEMISTRY_BY_REGION["ISS-N1"]),
        "feedback": feedback,
        "overall_score": round(overall, 3),
        "id": _sequence_hash(seq, target),
    }


async def score_aso(sequence: str) -> dict[str, Any]:
    """Score an ASO sequence on intrinsic design properties (no target needed).

    Evaluates: GC content, melting temperature, binding energy, length,
    self-complementarity, and BBB penetration potential. Provides pass/fail
    flags for key design criteria.

    This is a lightweight check useful for filtering before full target-specific
    scoring via ``score_custom_aso``.

    Args:
        sequence: ASO sequence in DNA notation (5'->3'), 10-30 nt.

    Returns:
        Dict with metrics, pass/fail flags, and design recommendations.
    """
    seq = sequence.upper().strip()

    if not seq or not all(c in "ATGCN" for c in seq):
        return {"error": "Invalid sequence — must contain only A, T, G, C, N"}

    if len(seq) < 10 or len(seq) > 30:
        return {"error": "Sequence length must be 10-30 nt"}

    gc = _gc_content(seq)
    tm_nn = _tm_nearest_neighbor(seq)
    tm_simple = _tm_simple(seq)
    dG = _binding_energy(seq)
    self_comp = _self_complementarity(seq)
    bbb = _bbb_score(len(seq), gc)

    # Pass/fail design criteria
    checks = {
        "length_ok": 15 <= len(seq) <= 25,
        "gc_optimal": 0.35 <= gc <= 0.65,
        "gc_ideal": 0.40 <= gc <= 0.60,
        "low_self_complementarity": self_comp < 0.35,
        "tm_therapeutic_range": 50.0 <= tm_nn <= 80.0,
        "strong_binding": dG < -15.0,
    }

    passed = sum(1 for v in checks.values() if v)
    total = len(checks)

    # Quick grade
    if passed == total:
        grade = "A — excellent intrinsic properties"
    elif passed >= total - 1:
        grade = "B — good, minor issue"
    elif passed >= total - 2:
        grade = "C — acceptable, review flagged criteria"
    else:
        grade = "D — poor, redesign recommended"

    return {
        "sequence": seq,
        "length": len(seq),
        "metrics": {
            "gc_content": gc,
            "tm_nearest_neighbor": tm_nn,
            "tm_simple_rule": tm_simple,
            "binding_energy_kcal_mol": dG,
            "self_complementarity": round(self_comp, 3),
            "bbb_penetration_score": bbb,
        },
        "checks": checks,
        "passed": passed,
        "total_checks": total,
        "grade": grade,
        "id": _sequence_hash(seq, "GENERIC"),
    }
