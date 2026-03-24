---
license: cc-by-4.0
language:
- en
tags:
- biology
- spinal-muscular-atrophy
- sma
- drug-discovery
- evidence-graph
- biomedical
- clinical-trials
- gene-targets
- ai-drug-design
- molecular-docking
- diffdock
size_categories:
- 10K<n<100K
task_categories:
- text-classification
- question-answering
pretty_name: SMA Evidence Graph
---

# SMA Evidence Graph

An open-source, evidence-first dataset for Spinal Muscular Atrophy (SMA) drug research.

## Description

This dataset contains structured evidence extracted from PubMed papers, clinical trials
from ClinicalTrials.gov, computationally generated hypotheses, AI-designed molecules,
and DiffDock molecular docking results — all linking gene targets to potential
therapeutic interventions for SMA.

**Built by a researcher who has SMA**, this dataset aims to accelerate drug discovery
by making the evidence landscape machine-readable and openly accessible.

### What's New (March 2026 Sprint)

- **Quality-gated claims**: 15,874 claims with recalibrated confidence scores (up from ~14K)
- **9,023 sources**: Expanded PubMed coverage including actin pathway and ROCK-LIMK literature
- **1,535 hypotheses**: Including convergence analysis of ROCK-LIMK2-CFL2 therapeutic axis
- **1,122 AI-designed molecules**: Generated via MolMIM/GenMol with BBB permeability, CNS-MPO, and Lipinski scoring
- **501 DiffDock dockings**: Molecular docking confidence scores across stereoisomer and selectivity panels
- **21,229 molecule screenings**: ChEMBL/PubChem bioactive compounds for LIMK2, ROCK2, and other targets
- **68 targets**: Including new actin-cytoskeleton pathway targets (ROCK1/2, LIMK1/2, CFL1/2, PFN1/2)

## Dataset Structure

| Split | Description | Records |
|-------|-------------|---------|
| `targets` | Gene/protein/pathway targets relevant to SMA | 68 |
| `drugs` | Approved and investigational therapies | 21 |
| `trials` | Clinical trials from ClinicalTrials.gov | 451 |
| `sources` | PubMed papers with abstracts | 9023 |
| `claims` | Structured claims extracted from abstracts (LLM) | 15874 |
| `evidence` | Links between claims and source papers | 15863 |
| `hypotheses` | Generated hypothesis cards per target | 1535 |
| `graph_edges` | Knowledge graph edges (STRING, KEGG, ChEMBL) | 582 |
| `drug_outcomes` | Structured drug success/failure database | 227 |
| `molecule_screenings` | ChEMBL/PubChem bioactive compounds screened | 21229 |
| `splice_variants` | SMN2 splice variant benchmark (SNVs scored) | 726 |
| `designed_molecules` | AI-designed molecules (MolMIM/GenMol) with ADMET | 1122 |
| `diffdock_extended` | DiffDock v2 molecular docking results | 501 |

## Key Features

- **Evidence-first**: Every claim traces back to a PubMed source with excerpt and method
- **Multi-modal**: Combines literature, clinical trials, protein interactions, and pathway data
- **Scored**: Claims and hypotheses have computed confidence scores
- **Typed claims**: gene_expression, drug_efficacy, splicing_event, biomarker, etc.
- **Knowledge graph**: Protein-protein interactions (STRING), pathway co-membership (KEGG), compound bioactivity (ChEMBL)
- **AI drug design**: De novo molecules with BBB permeability, QED, CNS-MPO, and Lipinski properties
- **Molecular docking**: DiffDock v2 docking confidence scores for drug-target pairs
- **ROCK-LIMK2-CFL2 convergence**: Cross-species validated therapeutic axis data (SMA + ALS)

## Core SMA Targets

| Symbol | Role |
|--------|------|
| SMN1 | Primary SMA gene (absent in patients) |
| SMN2 | Paralog, copy number = severity modifier |
| STMN2 | Axonal growth regulator |
| PLS3 | Actin-bundling, natural severity modifier |
| NCALD | Calcium sensor, knockdown rescues SMA |
| UBA1 | Ubiquitin homeostasis, dysregulated in SMA |
| ROCK1/2 | Rho kinase, actin regulation, upstream of LIMK |
| LIMK1/2 | LIM kinase, phosphorylates cofilin, actin dynamics |
| CFL1/2 | Cofilin, actin depolymerization, dysregulated in SMA |

## Approved Therapies

1. **Nusinersen** (Spinraza) — ASO targeting SMN2 ISS-N1
2. **Risdiplam** (Evrysdi) — Small molecule SMN2 splicing modifier
3. **Onasemnogene** (Zolgensma) — AAV9 gene replacement

## Usage

```python
from datasets import load_dataset

ds = load_dataset("SMAResearch/sma-evidence-graph")

# Access claims
claims = ds["claims"]
high_confidence = claims.filter(lambda x: x["confidence"] and x["confidence"] > 0.7)

# Access AI-designed molecules
molecules = ds["designed_molecules"]
bbb_permeable = molecules.filter(lambda x: x["bbb_permeable"] == True)

# Access DiffDock docking results
docking = ds["diffdock_extended"]

# Access knowledge graph
edges = ds["graph_edges"]
```

## Citation

If you use this dataset, please cite:

```bibtex
@misc{sma-evidence-graph-2026,
  title={SMA Evidence Graph: An Open Dataset for Spinal Muscular Atrophy Drug Discovery},
  author={Christian Fischer},
  year={2026},
  publisher={HuggingFace},
  url={https://huggingface.co/datasets/SMAResearch/sma-evidence-graph}
}
```

## Updates

This dataset is updated regularly via an automated pipeline that pulls new PubMed papers,
clinical trials, re-extracts claims, and runs computational drug design campaigns.

Last updated: 2026-03-24

## License

CC-BY-4.0 — free to use for research, attribution required.

## Links

- Platform: [sma-research.info](https://sma-research.info)
- GitHub: [Bryzant-Labs/sma-platform](https://github.com/Bryzant-Labs/sma-platform)
