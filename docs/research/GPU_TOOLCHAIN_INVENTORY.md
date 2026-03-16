# SMA Drug Discovery — GPU Toolchain Inventory

**Date:** 2026-03-16
**Source:** GitHub + HuggingFace research
**Purpose:** Complete inventory of open-source tools for AI-driven SMA drug discovery

---

## TIER 1: Critical Path Tools (Must Have)

### Splicing Prediction (SMA Core Target)

| Tool | GitHub | License | SMA Relevance |
|------|--------|---------|---------------|
| **SpliceAI** | [Illumina/SpliceAI](https://github.com/Illumina/SpliceAI) | Apache 2.0 | Gold standard splice variant scoring. 96% AUC-PR. |
| **SpliceTransformer** | [ShenLab-Genomics/SpliceTransformer](https://github.com/ShenLab-Genomics/SpliceTransformer) | Open | Tissue-specific splicing — predicts motor neuron-specific effects. Nature Comms 2024. |
| **Pangolin** | [tkzeng/Pangolin](https://github.com/tkzeng/Pangolin) | Open | Splice site strength prediction. Complements SpliceAI. |

**Ensemble strategy:** Run all 3 on SMN2 variants → consensus scoring = highest confidence.

### ASO Design (Next-Gen Nusinersen)

| Tool | GitHub | License | SMA Relevance |
|------|--------|---------|---------------|
| **openASO** | [lackeylela/openASO](https://github.com/lackeylela/openASO) | Open | Design antisense oligonucleotides targeting SMN2 regulatory regions. Direct path to next-gen Spinraza. |

### Protein Structure + Binding

| Tool | GitHub | License | SMA Relevance |
|------|--------|---------|---------------|
| **Boltz-1/2** | [jwohlwend/boltz](https://github.com/jwohlwend/boltz) | MIT | Structure + binding affinity in one pass. Open training code. AF3-level. |
| **OpenFold3** | [aqlaboratory/openfold-3](https://github.com/aqlaboratory/openfold-3) | Apache 2.0 | Proteins + RNA + small molecules. Can model SMN + ASO + drug together. |
| **ESM-2/3** | [facebookresearch/esm](https://github.com/facebookresearch/esm) | MIT | Protein language model. Variant effect prediction. 60x faster than AF2. |

### Molecular Docking

| Tool | GitHub | License | SMA Relevance |
|------|--------|---------|---------------|
| **DiffDock-L** | [gcorso/DiffDock](https://github.com/gcorso/DiffDock) | MIT | Diffusion-based. 38% top-1 (RMSD<2Å). 100x faster than traditional. |
| **GNINA** | [gnina/gnina](https://github.com/gnina/gnina) | Open | CNN scoring. 73% top-1 redocking (vs 58% Vina). Ensemble approach. |
| **AutoDock Vina** | [ccsb-scripps/AutoDock-Vina](https://github.com/ccsb-scripps/AutoDock-Vina) | Apache 2.0 | Industry standard baseline. |

### Molecular Dynamics

| Tool | GitHub | License | SMA Relevance |
|------|--------|---------|---------------|
| **OpenMM** | [openmm/openmm](https://github.com/openmm/openmm) | MIT | GPU-accelerated MD. 250 ns/day on A100. Drug-protein interaction validation. |

---

## TIER 2: High-Value Additions

### Generative Drug Design

| Tool | GitHub | License | SMA Relevance |
|------|--------|---------|---------------|
| **REINVENT 4** | [MolecularAI/REINVENT4](https://github.com/MolecularAI/REINVENT4) | Apache 2.0 | RL-based de novo drug design. Generate novel SMN2-targeting molecules. |
| **RFDiffusion3** | [RosettaCommons/RFdiffusion](https://github.com/RosettaCommons/RFdiffusion) | Open | Design SMN protein binders. Experimentally validated (cryo-EM). |
| **ProteinMPNN** | [dauparas/ProteinMPNN](https://github.com/dauparas/ProteinMPNN) | MIT | Inverse folding. 52% sequence recovery (vs 33% Rosetta). |

### DNA/Genome Models

| Tool | GitHub | License | SMA Relevance |
|------|--------|---------|---------------|
| **Evo 2** | [ArcInstitute/evo2](https://github.com/ArcInstitute/evo2) | Open | Largest biology AI (9.3T nucleotides). 1M bp context. Can model entire SMN2 locus. |
| **GENA-LM** | [AIRI-Institute/GENA_LM](https://github.com/AIRI-Institute/GENA_LM) | Open | 36,000 bp human DNA context. Variant impact prediction. |
| **Nucleotide Transformer** | HuggingFace: InstaDeepAI | Open | 3,200+ genomes. Cross-species SMN analysis. |

### Virtual Screening Pipelines

| Tool | GitHub | License | SMA Relevance |
|------|--------|---------|---------------|
| **DrugPipe** | [HySonLab/DrugPipe](https://github.com/HySonLab/DrugPipe) | Open | End-to-end: generative AI + pocket prediction + database retrieval. Blind screening. |
| **OpenVS** | [gfzhou/OpenVS](https://github.com/gfzhou/OpenVS) | Open | AI-accelerated virtual screening. Nature Comms 2024. |
| **BioNeMo Blueprint** | [NVIDIA-BioNeMo-blueprints/generative-virtual-screening](https://github.com/NVIDIA-BioNeMo-blueprints/generative-virtual-screening) | Open | NVIDIA industry-grade pipeline. |

### Drug Discovery ML

| Tool | GitHub | License | SMA Relevance |
|------|--------|---------|---------------|
| **DeepChem** | [deepchem/deepchem](https://github.com/deepchem/deepchem) | MIT | Unified ML toolkit. Molecular property prediction, binding affinity, ADMET. |
| **TorchDrug** | [DeepGraphLearning/torchdrug](https://github.com/DeepGraphLearning/torchdrug) | Apache 2.0 | Graph neural networks. De novo design + retrosynthesis. |
| **RDKit** | [rdkit/rdkit](https://github.com/rdkit/rdkit) | BSD | Foundation cheminformatics. Already in our platform. |
| **ADMETlab 3.0** | [ifyoungnet/ADMETlab](https://github.com/ifyoungnet/ADMETlab) | Open | Best ADMET prediction tool (2024 eval). |

### CRISPR Tools

| Tool | GitHub | License | SMA Relevance |
|------|--------|---------|---------------|
| **Cas-OFFinder** | [snugel/cas-offinder](https://github.com/snugel/cas-offinder) | GPL-3.0 | GPU off-target scanning. hg38 genome-wide. |
| **CRISPResso2** | [pinellolab/CRISPResso2](https://github.com/pinellolab/CRISPResso2) | Open | Quantify editing outcomes. |

---

## TIER 3: Infrastructure & NLP

### GPU Orchestration

| Tool | GitHub | Stars | Purpose |
|------|--------|-------|---------|
| **dstack** | [dstackai/dstack](https://github.com/dstackai/dstack) | 7.5k | GPU router across 14+ providers |
| **SkyPilot** | [skypilot-org/skypilot](https://github.com/skypilot-org/skypilot) | 6.1k | Multi-cloud GPU orchestration |
| **Nextflow** | [nextflow-io/nextflow](https://github.com/nextflow-io/nextflow) | 2.7k | Bioinformatics pipeline standard |
| **nf-core** | [nf-core](https://github.com/nf-core) | — | 145+ peer-reviewed pipelines |

### Biomedical NLP

| Tool | HuggingFace | Purpose |
|------|-------------|---------|
| **BioGPT** | microsoft/biogpt | Generative biomedical text (15M PubMed abstracts) |
| **PubMedBERT** | microsoft/BiomedNLP-BiomedBERT | SOTA biomedical language understanding |
| **SciBERT** | allenai/scibert_scivocab_uncased | Scientific paper analysis |

### HuggingFace Datasets

| Dataset | URL | SMA Relevance |
|---------|-----|---------------|
| **MISATO** | huggingface.co/MISATO-dataset | 30K+ protein-ligand structures with MD sims |
| **PDB Complexes** | jglaser/pdb_protein_ligand_complexes | 36K protein-ligand pairs for training |
| **Approved Drugs** | alimotahharynia/approved_drug_target | 1,660 drugs + 2,093 targets for repurposing |

---

## Key Insight

**No one has done this for SMA.** The tools exist. The data exists. The compute is cheap ($0.78/hr). But no published computational campaign has combined these tools for systematic SMA drug discovery. We are building the first one.
