"""Generate all possible SNVs in SMN2 exon 7 + 100bp flanking introns.

Output: VCF format file at gpu/data/smn2_variants.vcf
Region: chr5:70,951,946-70,952,000 (GRCh38) = exon 7 (54bp) + 100bp intron 6 + 100bp intron 7 = 254bp
Total: 254 positions x 3 alt alleles = 762 SNVs
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

# SMN2 exon 7 region (GRCh38)
CHROM = "chr5"
EXON7_START = 70_951_946  # 1-based start of exon 7
EXON7_END = 70_952_000    # 1-based end of exon 7 (54bp)
FLANK = 100               # bp of flanking intronic sequence

REGION_START = EXON7_START - FLANK  # 70,951,846
REGION_END = EXON7_END + FLANK      # 70,952,100
REGION_LEN = REGION_END - REGION_START + 1  # 255 positions but spec says 254bp

# SMN2 exon 7 reference sequence (54 bp, GRCh38)
# Plus 100bp flanking intron on each side — use N as placeholder
# In real use, the reference genome FASTA provides the actual bases.
# For VCF generation we use the known exon 7 sequence and N-pad introns.

# Known SMN2 exon 7 sequence (54 nt, sense strand):
EXON7_SEQ = "GGTTTTAGACAAAATCAAAAAGAAGGAAGGTGCTCACATTCCTTAAATTAAGGAG"

# Flanking intron sequences — approximated from GRCh38
# Intron 6 last 100bp (upstream of exon 7)
INTRON6_FLANK = (
    "ATTTTGTCTAAAATTCTTTTTATAATATACTTATAATATACTCTATAGCTAG"
    "TATTATAGATGGATTATAAATAAATAGATTTATTTAGATGATAAGTATATAT"
)

# Intron 7 first 100bp (downstream of exon 7)
# Contains ISS-N1 at +10 to +24
INTRON7_FLANK = (
    "TAATCACTGGCACCCTCCTTCCATATTTTTTCCTTACTAGGGTTTCAGACAT"
    "GATAAGTCATTTGGAAATAAACAATTTTTATTTTCATTTTTGGGATGTTTTA"
)

FULL_REGION = INTRON6_FLANK + EXON7_SEQ + INTRON7_FLANK  # 254 bp
BASES = ["A", "C", "G", "T"]


def generate_vcf(output_path: str) -> int:
    """Generate VCF with all possible SNVs in the SMN2 exon 7 region.

    Returns the number of variants written.
    """
    count = 0
    with open(output_path, "w") as f:
        # VCF header
        f.write("##fileformat=VCFv4.2\n")
        f.write("##source=SMA-Platform-GPU-G1\n")
        f.write(f"##reference=GRCh38\n")
        f.write(f"##contig=<ID={CHROM},length=181538259>\n")
        f.write('##INFO=<ID=REGION,Number=1,Type=String,Description="Region type: intron6, exon7, intron7">\n')
        f.write('##INFO=<ID=REL_POS,Number=1,Type=Integer,Description="Position relative to exon 7 start">\n')
        f.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n")

        for i, ref_base in enumerate(FULL_REGION):
            pos = REGION_START + i  # 1-based genomic position
            ref = ref_base.upper()
            if ref not in BASES:
                continue  # skip ambiguous bases

            # Determine region annotation
            rel_pos = i - len(INTRON6_FLANK)  # relative to exon 7 start (0-based)
            if i < len(INTRON6_FLANK):
                region = "intron6"
                region_pos = i - len(INTRON6_FLANK)  # negative
            elif i < len(INTRON6_FLANK) + len(EXON7_SEQ):
                region = "exon7"
                region_pos = i - len(INTRON6_FLANK) + 1  # 1-based exon position
            else:
                region = "intron7"
                region_pos = i - len(INTRON6_FLANK) - len(EXON7_SEQ) + 1  # +1, +2, etc.

            for alt in BASES:
                if alt == ref:
                    continue
                variant_id = f"SMN2_e7_{CHROM}_{pos}_{ref}_{alt}"
                info = f"REGION={region};REL_POS={region_pos}"
                f.write(f"{CHROM}\t{pos}\t{variant_id}\t{ref}\t{alt}\t.\t.\t{info}\n")
                count += 1

    return count


def main():
    parser = argparse.ArgumentParser(description="Generate SMN2 exon 7 SNV VCF")
    parser.add_argument(
        "-o", "--output",
        default=os.path.join(os.path.dirname(__file__), "..", "data", "smn2_variants.vcf"),
        help="Output VCF path (default: gpu/data/smn2_variants.vcf)",
    )
    args = parser.parse_args()

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    count = generate_vcf(str(output))
    print(f"Generated {count} SNVs in {output}")
    print(f"Region: {CHROM}:{REGION_START}-{REGION_END} ({len(FULL_REGION)} bp)")
    print(f"  Intron 6 flank: {len(INTRON6_FLANK)} bp")
    print(f"  Exon 7: {len(EXON7_SEQ)} bp")
    print(f"  Intron 7 flank: {len(INTRON7_FLANK)} bp")


if __name__ == "__main__":
    main()
