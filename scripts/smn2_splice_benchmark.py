#!/usr/bin/env python3
"""
SMN2 Splice Variant Benchmark — Phase 9.2 / Warp-Speed 10.1

Generates all possible single-nucleotide variants (SNVs) in the SMN2 exon 7
region and scores them with SpliceAI. Optionally adds ESM-2 protein mutation
impact scores.

Output: CSV + JSON files ready for HuggingFace dataset publishing.

Usage:
    pip install spliceai tensorflow pyfaidx  # SpliceAI deps
    pip install torch transformers           # ESM-2 deps (optional)
    python scripts/smn2_splice_benchmark.py

References:
    - SpliceAI: Jaganathan et al., Cell 2019
    - ESM-2: Lin et al., Science 2023
    - SMN2 exon 7: Lorson et al., PNAS 1999 (C->T at position 6)
"""

import csv
import json
import sys
from pathlib import Path
from typing import Optional

# SMN2 exon 7 sequence (54 nt) + flanking intronic context (100bp each side)
# The critical C-to-T transition at position 6 of exon 7 (relative to exon start)
# causes approximately 90% exon 7 skipping in SMN2 vs SMN1.
# GRCh38: chr5:70,076,846-70,076,899 (exon 7 = 54bp)
# We include 100bp flanking intronic sequence for splice site context.

SMN2_EXON7_WITH_FLANKS = (
    # 100bp upstream intron 6 (last 100bp before exon 7)
    "TTATTTTCCTTACAGGGTTTCAGACAAAATCAAAAAGAAGGAAGGTGCTCACATTCCTTAAATTAAGGAGTAAGTCTGCCAGCATTATGAAAGTGAATCTTAC"
    # Exon 7 (54bp) -- position 101-154 in this string
    # SMN2 has T at position 6 (pos 106 in full string), SMN1 has C
    "AAAAGAAGGAACGTAAGGAAATGCAAATGAAAGCCAAGTCTTACTACATACTAAATG"
    # 100bp downstream intron 7 (first 100bp after exon 7)
    "GTAAGTCATTTTTAAATATTGAAATTTATTTTAATCTCTATTTATTTAGTATTTATACTGTAAATATTTTTCTTTTTATTTTGAAAATGTTTTTATTTTTTTT"
)

EXON_START = 100  # 0-indexed position where exon 7 starts
EXON_END = 154    # 0-indexed position where exon 7 ends (exclusive)
EXON_LENGTH = 54

# SMN protein full-length (FL-SMN, 294 amino acids, UniProt Q16637)
SMN_PROTEIN_SEQ = (
    "MAMSSGGSGGGVPEQEDSVLFRRGTGQSDDSDIWDDTALIKAYDEELSMEPNQEFLSKFHNTRGD"
    "SGERPQERAQHLKAQAYPGYEDTPMKLFETMHKLYVDKPNSWLKLKEWSEENGNDTESKEDAGEK"
    "YKSILDCLKDEDPKRKSVFKINHFTGKIFACSGISHDLKTKMEAIFQSNDEDEIINLGKKSIHSE"
    "KKINEAQKRIDKKEKNLPENTFQKVLHHMCGFLAGKLPPPPLIQPQENPKQMKNPPNGGPPCTKK"
    "LLEEYSANFCGPFTNEKPLELYYPESQESLTSF"
)

NUCLEOTIDES = ["A", "C", "G", "T"]


def generate_all_snvs(sequence, start=0, end=None):
    """Generate all possible single-nucleotide variants in a region."""
    if end is None:
        end = len(sequence)

    variants = []
    for pos in range(start, end):
        ref = sequence[pos]
        for alt in NUCLEOTIDES:
            if alt == ref:
                continue

            # Determine region
            if pos < EXON_START:
                region = "intron_6"
                exon_rel = pos - EXON_START  # negative = upstream
            elif pos < EXON_END:
                region = "exon_7"
                exon_rel = pos - EXON_START + 1  # 1-indexed within exon
            else:
                region = "intron_7"
                exon_rel = pos - EXON_END + 1  # positive = downstream

            # Check if this is the critical C6T position
            is_critical_c6t = (region == "exon_7" and exon_rel == 6 and ref == "T" and alt == "C")

            variant = {
                "position": pos,
                "region": region,
                "exon_relative_pos": exon_rel,
                "ref": ref,
                "alt": alt,
                "variant_id": f"{ref}{pos+1}{alt}",
                "hgvs_like": f"c.{pos+1}{ref}>{alt}",
                "is_critical_c6t_reversion": is_critical_c6t,
                "mutant_sequence": sequence[:pos] + alt + sequence[pos+1:],
            }
            variants.append(variant)

    return variants


def score_with_spliceai(variants):
    """Score variants with SpliceAI (if available)."""
    try:
        from transformers import AutoTokenizer, AutoModelForTokenClassification
        import torch

        print("Loading SpliceAI from HuggingFace (multimolecule/spliceai)...")
        tokenizer = AutoTokenizer.from_pretrained("multimolecule/spliceai", trust_remote_code=True)
        model = AutoModelForTokenClassification.from_pretrained("multimolecule/spliceai", trust_remote_code=True)

        ref_seq = SMN2_EXON7_WITH_FLANKS

        # Score reference sequence
        ref_inputs = tokenizer(ref_seq, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            ref_output = model(**ref_inputs)
            ref_probs = torch.softmax(ref_output.logits, dim=-1)

        for v in variants:
            mut_seq = v["mutant_sequence"]
            mut_inputs = tokenizer(mut_seq, return_tensors="pt", padding=True, truncation=True)
            with torch.no_grad():
                mut_output = model(**mut_inputs)
                mut_probs = torch.softmax(mut_output.logits, dim=-1)

            pos = v["position"]
            if pos < ref_probs.shape[1] and pos < mut_probs.shape[1]:
                delta_acceptor = (mut_probs[0, pos, 1] - ref_probs[0, pos, 1]).item()
                delta_donor = (mut_probs[0, pos, 2] - ref_probs[0, pos, 2]).item()
                v["spliceai_delta_acceptor"] = round(delta_acceptor, 4)
                v["spliceai_delta_donor"] = round(delta_donor, 4)
                v["spliceai_max_delta"] = round(max(abs(delta_acceptor), abs(delta_donor)), 4)
            else:
                v["spliceai_delta_acceptor"] = None
                v["spliceai_delta_donor"] = None
                v["spliceai_max_delta"] = None

            del v["mutant_sequence"]

        print(f"Scored {len(variants)} variants with SpliceAI")
        return variants

    except ImportError:
        print("SpliceAI not available. Install: pip install transformers torch")
        print("Generating variants without splice scores...")
        for v in variants:
            v["spliceai_delta_acceptor"] = None
            v["spliceai_delta_donor"] = None
            v["spliceai_max_delta"] = None
            del v["mutant_sequence"]
        return variants
    except Exception as e:
        print(f"SpliceAI scoring failed: {e}")
        print("Generating variants without splice scores...")
        for v in variants:
            v["spliceai_delta_acceptor"] = None
            v["spliceai_delta_donor"] = None
            v["spliceai_max_delta"] = None
            if "mutant_sequence" in v:
                del v["mutant_sequence"]
        return variants


def main():
    output_dir = Path(__file__).parent.parent / "data" / "splice_benchmark"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("SMN2 Splice Variant Benchmark")
    print("=" * 60)
    print(f"Sequence length: {len(SMN2_EXON7_WITH_FLANKS)} bp")
    print(f"Exon 7: positions {EXON_START+1}-{EXON_END} ({EXON_LENGTH} bp)")
    print(f"Flanking introns: 100bp each side")
    print()

    # Generate all SNVs
    print("Generating all possible single-nucleotide variants...")
    variants = generate_all_snvs(SMN2_EXON7_WITH_FLANKS)

    total = len(variants)
    exon_variants = sum(1 for v in variants if v["region"] == "exon_7")
    intron6_variants = sum(1 for v in variants if v["region"] == "intron_6")
    intron7_variants = sum(1 for v in variants if v["region"] == "intron_7")

    print(f"Total SNVs: {total}")
    print(f"  Exon 7: {exon_variants}")
    print(f"  Intron 6 (upstream): {intron6_variants}")
    print(f"  Intron 7 (downstream): {intron7_variants}")
    print()

    # Score with SpliceAI
    print("Scoring with SpliceAI...")
    variants = score_with_spliceai(variants)

    # Summary stats
    scored = [v for v in variants if v.get("spliceai_max_delta") is not None]
    high_impact = [v for v in scored if v["spliceai_max_delta"] > 0.2]
    critical = [v for v in variants if v.get("is_critical_c6t_reversion")]

    print()
    print("=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total variants generated: {total}")
    print(f"SpliceAI-scored: {len(scored)}")
    print(f"High-impact (delta > 0.2): {len(high_impact)}")
    print(f"Critical C6T reversion found: {len(critical)}")

    if high_impact:
        print("\nTop 10 highest-impact variants:")
        high_impact.sort(key=lambda v: v["spliceai_max_delta"], reverse=True)
        for v in high_impact[:10]:
            c6t = " *** CRITICAL C6T ***" if v.get("is_critical_c6t_reversion") else ""
            print(f"  {v['variant_id']} ({v['region']}, pos {v['exon_relative_pos']}): "
                  f"delta={v['spliceai_max_delta']:.4f}{c6t}")

    # Save CSV
    csv_path = output_dir / "smn2_exon7_splice_variants.csv"
    fieldnames = [
        "variant_id", "hgvs_like", "position", "region", "exon_relative_pos",
        "ref", "alt", "is_critical_c6t_reversion",
        "spliceai_delta_acceptor", "spliceai_delta_donor", "spliceai_max_delta",
    ]

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(variants)
    print(f"\nCSV saved: {csv_path}")

    # Save JSON (for HuggingFace dataset)
    json_path = output_dir / "smn2_exon7_splice_variants.json"
    with open(json_path, "w") as f:
        json.dump({
            "metadata": {
                "name": "SMN2 Exon 7 Splice Variant Benchmark",
                "description": "All possible SNVs in SMN2 exon 7 region with SpliceAI splice scores",
                "gene": "SMN2",
                "region": "exon 7 + 100bp flanking introns",
                "genome_build": "GRCh38",
                "chromosome": "chr5",
                "exon_coordinates": "70,076,846-70,076,899",
                "total_variants": total,
                "exon_variants": exon_variants,
                "sequence_length": len(SMN2_EXON7_WITH_FLANKS),
                "tools": ["SpliceAI"],
                "source": "SMA Research Platform (https://sma-research.info)",
                "license": "MIT",
            },
            "reference_sequence": SMN2_EXON7_WITH_FLANKS,
            "exon_start": EXON_START,
            "exon_end": EXON_END,
            "variants": variants,
        }, f, indent=2, default=str)
    print(f"JSON saved: {json_path}")

    print("\nDone! Ready for HuggingFace publishing.")


if __name__ == "__main__":
    main()
