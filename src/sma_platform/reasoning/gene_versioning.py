"""Gene Edit Versioning — "GitHub for Life" (Phase 10.1).

Treats DNA sequences and splice modifications like code:
- Each SMN2 variant gets a deterministic "commit hash" (SHA-256 of sequence)
- Edits are tracked as diffs against the reference (NG_008728.1)
- CRISPR/base/prime edits can be simulated and versioned
- Variant lineage: reference → variant → edited variant

Think of it as git for genomes — every mutation is a commit,
every therapeutic edit is a pull request.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Reference sequences (from splice_benchmark.py / crispr_designer.py)
# ---------------------------------------------------------------------------

# SMN2 exon 7 reference (55 nt)
SMN2_EXON7_REF = "GATATTTTATATTAGACAAAATCAAAAAGAAGGAAATGCTGGCATAGAGCAGCAC"

# Intron 7 first 100 nt (contains ISS-N1)
SMN2_INTRON7_REF = (
    "GTAAGTCTGCCAGCATTATGAAAGTGAATCTTACTTACTCAATATATATATATATATATTT"
    "TTAACAGATGGGAGTTCTGAGTGGACTAAATGTTCACAG"
)

# Intron 6 last 100 nt
SMN2_INTRON6_REF = (
    "ATAATTCCCCCACCACCTCCCATATGTCCAGATTCTCTTGATGATGCTGATGCTTTGGGAAG"
    "TATGTTAATTTCATGGTACATGAGTGGCTATCATACTGGCTAG"
)[-100:]

# Full reference region: intron6(100) + exon7(55) + intron7(100) = 255 nt
SMN2_REGION_REF = SMN2_INTRON6_REF + SMN2_EXON7_REF + SMN2_INTRON7_REF

# SMN1 exon 7 (differs at position 6: C instead of T)
SMN1_EXON7_REF = SMN2_EXON7_REF[:5] + "C" + SMN2_EXON7_REF[6:]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class SequenceVersion:
    """A versioned DNA sequence — like a git commit."""
    commit_hash: str          # SHA-256 of the sequence (first 12 hex chars)
    full_hash: str            # Full SHA-256
    sequence: str             # The DNA sequence
    region: str               # 'exon7', 'intron7', 'full_region', etc.
    parent_hash: str | None   # Hash of the parent version (None = reference)
    edit_type: str            # 'reference', 'snv', 'deletion', 'insertion', 'base_edit', 'crispr_ko', 'prime_edit'
    edit_description: str     # Human-readable description
    position: int | None      # 0-indexed position of the edit
    ref_allele: str | None    # Reference allele at edit position
    alt_allele: str | None    # Alternate allele
    functional_impact: str    # Predicted impact on splicing/function


@dataclass
class EditDiff:
    """A diff between two sequence versions — like a git diff."""
    parent_hash: str
    child_hash: str
    changes: list[dict]       # List of {position, ref, alt, type}
    total_changes: int
    edit_distance: int        # Levenshtein-like measure


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def _sequence_hash(seq: str) -> str:
    """Compute SHA-256 hash of a DNA sequence (case-insensitive)."""
    return hashlib.sha256(seq.upper().encode()).hexdigest()


def _short_hash(full_hash: str) -> str:
    """First 12 characters of the hash — like git short SHA."""
    return full_hash[:12]


# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------

def create_version(
    sequence: str,
    region: str = "exon7",
    parent_hash: str | None = None,
    edit_type: str = "reference",
    edit_description: str = "Reference sequence",
    position: int | None = None,
    ref_allele: str | None = None,
    alt_allele: str | None = None,
    functional_impact: str = "none",
) -> SequenceVersion:
    """Create a versioned sequence entry."""
    full_hash = _sequence_hash(sequence)
    return SequenceVersion(
        commit_hash=_short_hash(full_hash),
        full_hash=full_hash,
        sequence=sequence.upper(),
        region=region,
        parent_hash=parent_hash,
        edit_type=edit_type,
        edit_description=edit_description,
        position=position,
        ref_allele=ref_allele,
        alt_allele=alt_allele,
        functional_impact=functional_impact,
    )


def compute_diff(parent_seq: str, child_seq: str) -> EditDiff:
    """Compute the diff between two sequences."""
    parent = parent_seq.upper()
    child = child_seq.upper()
    parent_hash = _short_hash(_sequence_hash(parent))
    child_hash = _short_hash(_sequence_hash(child))

    changes = []
    min_len = min(len(parent), len(child))

    # Point mutations / substitutions
    for i in range(min_len):
        if parent[i] != child[i]:
            changes.append({
                "position": i,
                "ref": parent[i],
                "alt": child[i],
                "type": "substitution",
            })

    # Length differences (insertions/deletions)
    if len(child) > len(parent):
        changes.append({
            "position": len(parent),
            "ref": "",
            "alt": child[len(parent):],
            "type": "insertion",
        })
    elif len(parent) > len(child):
        changes.append({
            "position": len(child),
            "ref": parent[len(child):],
            "alt": "",
            "type": "deletion",
        })

    return EditDiff(
        parent_hash=parent_hash,
        child_hash=child_hash,
        changes=changes,
        total_changes=len(changes),
        edit_distance=sum(1 for i in range(min_len) if parent[i] != child[i])
                      + abs(len(parent) - len(child)),
    )


# ---------------------------------------------------------------------------
# Edit Simulations
# ---------------------------------------------------------------------------

def simulate_snv(sequence: str, position: int, alt: str) -> str:
    """Simulate a single nucleotide variant."""
    seq = list(sequence.upper())
    if 0 <= position < len(seq):
        seq[position] = alt.upper()
    return "".join(seq)


def simulate_base_edit(sequence: str, position: int, edit_type: str = "C_to_T") -> str:
    """Simulate a base edit (ABE: A→G or CBE: C→T).

    For SMA: ABE could correct SMN2 exon 7 position 6 T→C (restoring SMN1-like splicing).
    """
    seq = list(sequence.upper())
    if edit_type == "C_to_T":
        if seq[position] == "C":
            seq[position] = "T"
    elif edit_type == "A_to_G":
        if seq[position] == "A":
            seq[position] = "G"
    elif edit_type == "T_to_C":
        # Reverse of C_to_T — this is what we want for SMN2 correction
        if seq[position] == "T":
            seq[position] = "C"
    return "".join(seq)


def simulate_crispr_ko(sequence: str, cut_position: int, indel_size: int = 1) -> str:
    """Simulate a CRISPR knockout (deletion at cut site)."""
    seq = sequence.upper()
    start = max(0, cut_position - indel_size // 2)
    end = min(len(seq), cut_position + (indel_size + 1) // 2)
    return seq[:start] + seq[end:]


# ---------------------------------------------------------------------------
# SMN2 Version Tree
# ---------------------------------------------------------------------------

def build_smn2_version_tree() -> dict[str, Any]:
    """Build the complete SMN2 exon 7 version tree.

    Shows how SMN1 → SMN2 (C6T disease mutation) → therapeutic edits create
    a lineage of sequence versions.
    """
    versions = []

    # Level 0: SMN1 reference (healthy gene)
    smn1_ref = create_version(
        SMN1_EXON7_REF, "exon7",
        edit_type="reference",
        edit_description="SMN1 exon 7 reference — healthy gene, 100% exon inclusion",
        functional_impact="normal_splicing",
    )
    versions.append(smn1_ref)

    # Level 1: SMN2 (C6T disease mutation — the root cause of SMA)
    smn2_ref = create_version(
        SMN2_EXON7_REF, "exon7",
        parent_hash=smn1_ref.commit_hash,
        edit_type="snv",
        edit_description="C→T at position 6 (SMN1→SMN2 divergence) — disrupts ESE, activates ESS, causes ~90% exon 7 skipping",
        position=5,  # 0-indexed
        ref_allele="C",
        alt_allele="T",
        functional_impact="disease_causing — 90% exon 7 skipping",
    )
    versions.append(smn2_ref)

    # Level 2: Therapeutic edits on SMN2
    # 2a: Base edit T→C at position 6 (restoring SMN1-like sequence)
    corrected = simulate_base_edit(SMN2_EXON7_REF, 5, "T_to_C")
    v_base_edit = create_version(
        corrected, "exon7",
        parent_hash=smn2_ref.commit_hash,
        edit_type="base_edit",
        edit_description="ABE base edit: T→C at position 6 — restores SMN1-like exon 7 inclusion",
        position=5,
        ref_allele="T",
        alt_allele="C",
        functional_impact="therapeutic — restores ~100% exon 7 inclusion",
    )
    versions.append(v_base_edit)

    # 2b: ESE-strengthening mutation (theoretical)
    ese_enhanced = simulate_snv(SMN2_EXON7_REF, 20, "A")
    v_ese = create_version(
        ese_enhanced, "exon7",
        parent_hash=smn2_ref.commit_hash,
        edit_type="snv",
        edit_description="G→A at position 21 (Tra2-beta ESE region) — predicted to strengthen enhancer binding",
        position=20,
        ref_allele="G",
        alt_allele="A",
        functional_impact="enhancer_strengthening — predicted moderate improvement",
    )
    versions.append(v_ese)

    # 2c: ESS disruption (knock out hnRNP A1 binding)
    ess_disrupted = simulate_snv(SMN2_EXON7_REF, 48, "T")
    v_ess = create_version(
        ess_disrupted, "exon7",
        parent_hash=smn2_ref.commit_hash,
        edit_type="snv",
        edit_description="G→T at position 49 (ESS region) — disrupts hnRNP A1 binding, reduces exon skipping",
        position=48,
        ref_allele="G",
        alt_allele="T",
        functional_impact="silencer_disruption — reduces exon 7 skipping",
    )
    versions.append(v_ess)

    # Full region version
    full_ref = create_version(
        SMN2_REGION_REF, "full_region",
        edit_type="reference",
        edit_description="SMN2 full exon 7 region: intron6[-100] + exon7[55] + intron7[+100] = 255 nt",
        functional_impact="disease — contains C6T and all regulatory elements",
    )
    versions.append(full_ref)

    # Compute diffs
    diffs = []
    smn1_to_smn2 = compute_diff(SMN1_EXON7_REF, SMN2_EXON7_REF)
    diffs.append({
        "name": "SMN1 → SMN2 (disease mutation)",
        **asdict(smn1_to_smn2),
    })

    smn2_to_corrected = compute_diff(SMN2_EXON7_REF, corrected)
    diffs.append({
        "name": "SMN2 → Base Edit Corrected (therapeutic)",
        **asdict(smn2_to_corrected),
    })

    return {
        "title": "SMN2 Exon 7 Version Tree — Gene Edit History",
        "description": "Each sequence variant is a 'commit' with a deterministic hash. "
                       "The disease (SMA) is a single-nucleotide 'bug' at position 6 (C→T). "
                       "Therapeutic edits are 'patches' that restore function.",
        "total_versions": len(versions),
        "versions": [asdict(v) for v in versions],
        "diffs": diffs,
        "lineage": {
            "smn1_healthy": smn1_ref.commit_hash,
            "smn2_disease": smn2_ref.commit_hash,
            "smn2_corrected": v_base_edit.commit_hash,
            "ese_enhanced": v_ese.commit_hash,
            "ess_disrupted": v_ess.commit_hash,
        },
    }


def version_custom_edit(
    base_sequence: str,
    edit_position: int,
    alt_allele: str,
    region: str = "custom",
    edit_description: str = "Custom edit",
) -> dict[str, Any]:
    """Version a custom sequence edit."""
    parent = create_version(base_sequence, region, edit_type="reference")
    edited = simulate_snv(base_sequence, edit_position, alt_allele)
    child = create_version(
        edited, region,
        parent_hash=parent.commit_hash,
        edit_type="snv",
        edit_description=edit_description,
        position=edit_position,
        ref_allele=base_sequence[edit_position] if edit_position < len(base_sequence) else None,
        alt_allele=alt_allele,
    )
    diff = compute_diff(base_sequence, edited)

    return {
        "parent": asdict(parent),
        "child": asdict(child),
        "diff": asdict(diff),
    }
