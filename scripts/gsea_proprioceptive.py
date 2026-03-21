#!/usr/bin/env python3
"""GSEA for proprioceptive gene sets on SMA RNA-seq data.

Deliverable #1 from Simon collaboration proposal.
Runs Gene Set Enrichment Analysis on GSE87281 with proprioceptive markers.

Requirements:
    pip install gseapy pandas numpy

Usage:
    python scripts/gsea_proprioceptive.py

Note: This script prepares the gene sets and analysis framework.
      The actual GSEA run requires downloading the GEO dataset first.
"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Proprioceptive Gene Sets (curated from literature)
# ============================================================================

GENE_SETS = {
    "PROPRIOCEPTIVE_MARKERS": {
        "description": "Core proprioceptive neuron markers",
        "genes": [
            "PVALB",      # Parvalbumin — canonical proprioceptor marker
            "PIEZO2",     # Mechanosensitive ion channel — essential for proprioception
            "EPHA4",      # Ephrin receptor — synapse specificity
            "RET",        # GDNF receptor — DRG neuron survival
            "ETV1",       # Transcription factor — proprioceptor specification
            "RUNX3",      # Transcription factor — proprioceptor development
            "NTRK3",      # TrkC receptor — NT-3 signaling
            "MAB21L2",    # Proprioceptor differentiation
            "WNT7A",      # Proprioceptor circuit formation
        ],
    },

    "IA_AFFERENT_SYNAPSE": {
        "description": "Genes enriched at Ia afferent synapses on motor neurons",
        "genes": [
            "VGLUT1",     # SLC17A7 — glutamatergic marker of Ia afferents
            "SLC17A7",    # Same as VGLUT1
            "BASSOON",    # BSN — presynaptic active zone
            "HOMER1",     # Postsynaptic scaffold
            "SHANK2",     # Postsynaptic scaffold
            "GRIA1",      # AMPA receptor subunit
            "GRIA2",      # AMPA receptor subunit
            "NRXN1",      # Neurexin — synapse formation
            "NLGN1",      # Neuroligin — synapse formation
            "SYNGAP1",    # Synaptic GTPase
        ],
    },

    "ACTIN_DYNAMICS_SMA": {
        "description": "Actin cytoskeleton genes dysregulated in SMA",
        "genes": [
            "PFN1",       # Profilin 1 — SMN interaction partner
            "PFN2",       # Profilin 2 — SMN interaction partner
            "CFL1",       # Cofilin 1 — actin depolymerization
            "CFL2",       # Cofilin 2 — 2.9x up in SMA
            "PLS3",       # Plastin 3 — known SMA modifier
            "CORO1C",     # Coronin 1C — actin regulator
            "ACTG1",      # Gamma actin
            "ACTR2",      # Arp2/3 complex
            "ABI2",       # Arp2/3 regulator
            "ROCK1",      # Rho kinase 1
            "ROCK2",      # Rho kinase 2
            "LIMK1",      # LIM kinase 1
            "LIMK2",      # LIM kinase 2
        ],
    },

    "PROPRIOCEPTIVE_CIRCUIT": {
        "description": "Genes involved in proprioceptive circuit formation and maintenance",
        "genes": [
            "PVALB", "PIEZO2", "EPHA4", "RET", "ETV1", "RUNX3",
            "NTRK3", "GDNF", "NTF3",  # NT-3
            "ERBB3",      # ErbB3 — muscle spindle development
            "NRG1",       # Neuregulin — muscle spindle maturation
            "CHRNA1",     # Acetylcholine receptor
            "MUSK",       # MuSK — NMJ formation
            "AGRN",       # Agrin — NMJ formation
            "RAPSN",      # Rapsyn — AChR clustering
        ],
    },

    "NECROPTOSIS_PATHWAY": {
        "description": "Necroptosis pathway genes (Martinez-Espana SMA Europe 2026)",
        "genes": [
            "RIPK1",      # RIPK1 — necroptosis initiator
            "RIPK3",      # RIPK3 — necroptosis mediator
            "MLKL",       # MLKL — necroptosis executor
            "CASP8",      # Caspase-8 — necroptosis/apoptosis switch
            "FADD",       # FADD — death receptor adaptor
            "TNFRSF1A",   # TNF receptor 1
            "CYLD",       # Deubiquitinase — RIPK1 regulation
        ],
    },

    "MITOCHONDRIAL_TRANSPORT": {
        "description": "Mitochondrial transport and dynamics genes",
        "genes": [
            "KIF5A",      # Kinesin — anterograde transport
            "KIF5B",      # Kinesin — anterograde transport
            "DYNC1H1",    # Dynein — retrograde transport
            "MFN1",       # Mitofusin 1 — fusion
            "MFN2",       # Mitofusin 2 — fusion
            "OPA1",       # OPA1 — inner membrane fusion
            "DNM1L",      # DRP1 — fission
            "RHOT1",      # MIRO1 — mitochondrial motility
            "RHOT2",      # MIRO2 — mitochondrial motility
            "TRAK1",      # TRAK1 — mito-kinesin adaptor
        ],
    },
}


def save_gmt_file(gene_sets: dict, output_path: str):
    """Save gene sets in GMT format for GSEA tools."""
    with open(output_path, "w") as f:
        for name, data in gene_sets.items():
            genes = "\t".join(data["genes"])
            f.write(f"{name}\t{data['description']}\t{genes}\n")
    logger.info(f"Saved {len(gene_sets)} gene sets to {output_path}")


def main():
    output_dir = Path("data/gsea")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save gene sets as GMT file
    gmt_path = output_dir / "sma_proprioceptive_gene_sets.gmt"
    save_gmt_file(GENE_SETS, str(gmt_path))

    # Save as JSON for platform integration
    json_path = output_dir / "sma_proprioceptive_gene_sets.json"
    with open(json_path, "w") as f:
        json.dump(GENE_SETS, f, indent=2)
    logger.info(f"Saved JSON to {json_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("PROPRIOCEPTIVE GENE SETS FOR GSEA")
    print("=" * 60)
    for name, data in GENE_SETS.items():
        print(f"\n{name} ({len(data['genes'])} genes)")
        print(f"  {data['description']}")
        print(f"  Genes: {', '.join(data['genes'][:8])}...")

    print(f"\n\nGMT file: {gmt_path}")
    print(f"JSON file: {json_path}")
    print("\nNext steps:")
    print("  1. Download GSE87281 expression matrix from GEO")
    print("  2. Run: gseapy.prerank() with ranked gene list")
    print("  3. Or use gseapy.ssgsea() for single-sample enrichment")
    print("  4. Compare enrichment between SMA and control groups")


if __name__ == "__main__":
    main()
