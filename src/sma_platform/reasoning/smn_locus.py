"""SMN Locus Resolution — why copy number alone doesn't explain phenotype.

The SMN locus on chromosome 5q13 is one of the most complex regions in the
human genome. This module provides structured knowledge about the locus
architecture and factors beyond copy number that influence SMA severity.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

SMN_LOCUS_INFO = {
    "chromosome": "5q13.2",
    "region_size": "~500 kb inverted duplication",
    "genes": {
        "SMN1": {
            "position": "telomeric copy",
            "exons": 9,
            "key_feature": "C at position +6 of exon 7 → full-length SMN protein",
            "sma_role": "Homozygous deletion/mutation causes SMA",
        },
        "SMN2": {
            "position": "centromeric copy",
            "exons": 9,
            "key_feature": "T at position +6 of exon 7 → ~90% exon 7 skipping → truncated SMNΔ7",
            "sma_role": "Copy number is primary modifier (2=TypeI, 3=TypeII/III, 4+=mild/asymptomatic)",
        },
    },
    "critical_difference": (
        "Single nucleotide C→T in exon 7 (c.840C>T) disrupts ESE and creates ESS, "
        "causing exon 7 skipping"
    ),
}

# Why copy number doesn't fully predict phenotype
PHENOTYPE_MODIFIERS = [
    {
        "factor": "SMN2 copy number",
        "contribution": "~80% of phenotype variance",
        "mechanism": "More copies → more residual full-length SMN protein",
        "limitation": (
            "2-copy patients range from Type I to Type III — other factors must contribute"
        ),
    },
    {
        "factor": "SMN2 exon 7 inclusion efficiency",
        "contribution": "~5-10% of variance",
        "mechanism": (
            "Some SMN2 copies produce more full-length mRNA due to cis-regulatory variants"
        ),
        "limitation": "Hard to measure directly — requires allele-specific splicing assays",
    },
    {
        "factor": "Modifier genes (PLS3, NCALD, NAIP)",
        "contribution": "~5-10% of variance",
        "mechanism": (
            "PLS3 overexpression in discordant females rescues NMJ. "
            "NCALD reduction restores endocytosis."
        ),
        "limitation": "PLS3 modifier is sex-linked (X chromosome) — primarily protects females",
    },
    {
        "factor": "SMN2 gene conversion/hybrid genes",
        "contribution": "Variable",
        "mechanism": (
            "SMN2 copies with partial SMN1 sequence (c.840C) produce more full-length SMN"
        ),
        "limitation": (
            "Rare — found in ~5% of SMA families. Difficult to detect with standard MLPA."
        ),
    },
    {
        "factor": "Intragenic SMN2 variants",
        "contribution": "Emerging evidence",
        "mechanism": (
            "Variants in SMN2 intron 6/7 (e.g., A-44G, A-549G) affect splicing "
            "regulatory elements"
        ),
        "limitation": "Not routinely tested in clinical diagnostics",
    },
    {
        "factor": "Epigenetic modification",
        "contribution": "Unknown — under investigation",
        "mechanism": (
            "DNA methylation at SMN2 promoter and histones may affect expression levels"
        ),
        "limitation": "No validated epigenetic biomarker yet",
    },
    {
        "factor": "Genetic background / polygenic",
        "contribution": "Unknown",
        "mechanism": (
            "Multiple low-effect variants collectively influence motor neuron vulnerability"
        ),
        "limitation": "Requires large GWAS studies in SMA cohorts",
    },
]

# Key clinical scenarios where copy number fails
DISCORDANT_CASES = [
    {
        "scenario": "Asymptomatic SMN1-deleted individuals",
        "genotype": "0 copies SMN1, 4+ copies SMN2",
        "phenotype": "No SMA symptoms",
        "explanation": (
            "High SMN2 copy number compensates. But not all 4-copy individuals "
            "are asymptomatic."
        ),
    },
    {
        "scenario": "Discordant siblings (same genotype, different severity)",
        "genotype": "Same SMN1 deletion, same SMN2 copies",
        "phenotype": "One sibling Type I, other Type III",
        "explanation": (
            "PLS3 modifier (X-linked), SMN2 exon 7 inclusion efficiency, "
            "or other modifiers differ."
        ),
    },
    {
        "scenario": "Late-onset Type IV with 2 copies",
        "genotype": "0 SMN1, 2 SMN2",
        "phenotype": "Adult-onset mild SMA",
        "explanation": (
            "Extremely rare. Possible SMN2 gene conversion or unknown protective modifiers."
        ),
    },
    {
        "scenario": "Severe Type I with 3 copies",
        "genotype": "0 SMN1, 3 SMN2",
        "phenotype": "Severe infantile onset (expected Type II/III)",
        "explanation": (
            "SMN2 copies may have reduced expression or splicing efficiency. "
            "Point mutations possible."
        ),
    },
]


def get_locus_info() -> dict[str, Any]:
    """Get comprehensive SMN locus information."""
    return {
        "locus": SMN_LOCUS_INFO,
        "phenotype_modifiers": PHENOTYPE_MODIFIERS,
        "discordant_cases": DISCORDANT_CASES,
        "key_message": (
            "SMN2 copy number explains ~80% of phenotype variance, but the remaining ~20% "
            "depends on modifier genes (PLS3, NCALD), SMN2 splicing efficiency variants, "
            "gene conversion events, and potentially epigenetic factors. Understanding these "
            "modifiers is critical for personalized prognosis and treatment stratification."
        ),
    }


def get_modifiers() -> list[dict[str, str]]:
    """Get list of known phenotype modifiers beyond SMN2 copy number."""
    return PHENOTYPE_MODIFIERS


def get_discordant_cases() -> list[dict[str, str]]:
    """Get examples of genotype-phenotype discordance in SMA."""
    return DISCORDANT_CASES
