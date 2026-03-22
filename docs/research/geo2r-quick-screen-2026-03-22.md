# GEO2R Quick Screen: Actin Pathway Genes in ALS Datasets
## Phase 1 Results -- CORO1C, CFL2, PFN1 Cross-Disease Screen

**Date**: 2026-03-22
**Status**: Phase 1 complete -- literature and database screen
**Prerequisite**: [GEO Analysis Plan](geo-analysis-plan-als-sma.md) | [SMA-ALS Convergence Deep Dive](sma-als-convergence-deep-dive.md)

---

## Executive Summary

**Bottom line**: No one has systematically checked CORO1C/CFL2/PFN1 co-expression in ALS RNA-seq datasets. However, the surrounding evidence is strong enough to justify moving to Phase 2 (computational analysis). Key findings:

1. **CORO1A** (sister gene to CORO1C) is **5.3-fold upregulated** in ALS patient plasma exosomes -- first coronin family member linked to ALS
2. **Cofilin phosphorylation** (CFL1, likely also CFL2) is **enhanced** in C9ORF72-ALS motor neurons, iPSC-MNs, and post-mortem brain
3. **PFN1** mutations cause both familial AND sporadic ALS; the G118V mouse model has 890 DEGs with actin/inflammation pathways upregulated
4. **STMN2** is the most downregulated transcript in TDP-43-depleted motor neurons -- strong positive control for our analysis
5. **Hensel & Claus 2018** explicitly proposed SMA-ALS convergence on actin cytoskeleton -- but never tested it with transcriptomics
6. All three priority datasets have raw data available and are amenable to GEO2R or custom analysis

**Verdict**: The actin convergence hypothesis has strong mechanistic support but **zero transcriptomic validation**. This is a genuine gap we can fill.

---

## Dataset-by-Dataset Results

### 1. GSE153960 -- Human ALS Spinal Cord (380 transcriptomes)

| Field | Detail |
|-------|--------|
| **Publication** | Humphrey et al. 2023, *Nature Neuroscience* 26:150-162 (PMID: [36482247](https://pubmed.ncbi.nlm.nih.gov/36482247/)) |
| **Samples** | 380 post-mortem spinal cord RNA-seq (154 ALS, 49 controls, cervical/thoracic/lumbar) |
| **Platform** | Bulk RNA-seq (Illumina) |
| **Data portal** | [jackhump.github.io/ALS_SpinalCord_QTLs](https://jackhump.github.io/ALS_SpinalCord_QTLs/) |
| **Processed data** | Count matrices on Zenodo; DE vignette available; Shiny app for browsing |
| **GEO2R** | Not directly (bulk RNA-seq needs custom pipeline), but DE vignette replicates results |

#### Expression data for our genes?

**Not yet checked computationally.** The study focused on:
- Glial activation (microglia/astrocyte increase, oligodendrocyte decrease)
- Gene co-expression networks (WGCNA)
- Molecular QTLs (eQTLs, sQTLs)
- TWAS risk genes

The paper does NOT mention CORO1C, CFL2, or PFN1 in text or figures. However:
- Full DE results are available via the [DE Vignette](https://jackhump.github.io/ALS_SpinalCord_QTLs/html/DE_Vignette.html) on GitHub
- Count matrices are downloadable from Zenodo
- The data portal may allow gene-level browsing

#### What we need to do:
1. Download processed count matrices from Zenodo
2. Run DE analysis for CORO1C, CFL2, PFN1 + extended gene set (PLS3, NCALD, STMN2, ROCK2, ACTG1, ACTR2, ABI2)
3. Check ALS vs. control, C9orf72 vs. sporadic, and segment-level differences
4. Use STMN2 as positive control (should be strongly downregulated)

#### Existing publications that checked our genes?
- **None found** that specifically examined CORO1C/CFL2/PFN1 in this dataset
- A separate study using this dataset examined RNA editing (GSE153960 was used for editome analysis in ALS-Ox subtype, but focused on glutamatergic synapses, not actin)

---

### 2. GSE113924 -- PFN1-G118V ALS Mouse Model

| Field | Detail |
|-------|--------|
| **Publication** | Fil et al. 2018, *Scientific Reports* 8:13737 (PMID: [30213953](https://pubmed.ncbi.nlm.nih.gov/30213953/)) |
| **Samples** | hPFN1-G118V transgenic mice vs. hPFN1-WT controls, spinal cord, pre-symptomatic (day 50) + end-stage (~day 202) |
| **Platform** | Bulk RNA-seq (Illumina) |
| **DEG counts** | End-stage vs. pre-symptomatic: 890 DEGs (747 up, 143 down); End-stage G118V vs. age-matched WT: 836 DEGs (742 up, 94 down) |
| **GEO2R** | Applicable for basic analysis; raw data on SRA |

#### Expression data for our genes?

**Partially available from published results, but our specific genes are NOT reported:**

The paper reports pathway-level results:
- **Upregulated at end-stage**: NF-kB signaling, nitric oxide/ROS, interleukin signaling, inflammasome, astrocyte/microglia markers
- **Downregulated**: Neuronal markers, cholinergic signaling (ChAT reduced)
- **Pre-symptomatic**: Only 1 DEG (Prnp) -- remarkably stable early transcriptome

The paper does NOT specifically report fold-change/p-values for:
- Coro1c, Cfl2, Pfn1 (the transgene itself), Pls3, Ncald, Stmn2, Rock2, Actg1, Actr2, Abi2

However, with 890 DEGs at end-stage, there is a HIGH probability that actin pathway genes appear in the full supplementary tables.

#### What we need to do:
1. Download supplementary tables from the Scientific Reports paper (should contain full DEG list with fold-changes)
2. Search for Coro1c, Cfl2, Pls3, Ncald, Stmn2, Rock2, Actg1, Actr2, Abi2 in the DEG list
3. Note: Pfn1 itself is the transgene, so its expression will be artificially elevated -- but downstream actin targets are the real prize
4. Compare pre-symptomatic vs. end-stage to distinguish early (causal) from late (reactive) changes
5. If our genes are NOT in the published DEG list, download raw counts from GEO and run targeted analysis

#### Key insight:
If CORO1C/CFL2 are dysregulated in a PFN1-mutant background, it validates the shared actin pathway model and suggests these genes respond to upstream profilin dysfunction regardless of the specific disease (SMA or ALS).

#### Existing publications that checked our genes?
- **None found** that specifically checked CORO1C or CFL2 in this dataset
- The original paper focused on inflammation and glia, not actin dynamics per se (ironic given PFN1 is an actin-binding protein)

---

### 3. GSE287257 -- ALS Spinal Cord snRNA-seq (2025)

| Field | Detail |
|-------|--------|
| **Publication** | Bhargava et al. 2025, *Immunity* (PMID: [40132594](https://pubmed.ncbi.nlm.nih.gov/40132594/)) |
| **Samples** | 8 ALS (6 sporadic, 2 familial) + 4 age-matched controls, cervical spinal cord |
| **Platform** | Single-nucleus RNA-seq (10x Genomics) |
| **Key finding** | RIPK1/necroptosis pathway activated; 21/34 necroptosis genes significantly changed |
| **GEO2R** | Not applicable (snRNA-seq requires Seurat/Scanpy pipeline) |

#### Expression data for our genes?

**Not reported for our specific genes.** The study focused on:
- Glial cell state changes (disease-associated astrocytes, microglia)
- RIPK1/RIPK3/MLKL necroptosis pathway upregulation
- SOD1-G93A mouse validation with RIPK1 inhibition
- iPSC tri-culture biomarker discovery

The paper does NOT mention CORO1C, CFL2, PFN1, or actin pathway analysis.

#### What we need to do:
1. Download processed snRNA-seq data (likely Seurat object or h5ad) from GEO
2. Subset motor neuron cluster
3. Compare CORO1C/CFL2/PFN1 expression: ALS motor neurons vs. control motor neurons
4. Check cell-type specificity: are actin genes dysregulated in motor neurons specifically, or pan-cellular?
5. Use STMN2 as positive control (should be motor neuron-specific and reduced in ALS nuclei)

#### Key advantage:
This is the ONLY dataset that can tell us if actin gene changes are **motor neuron-specific** vs. driven by glial contamination in bulk data.

#### Existing publications that checked our genes?
- **None found**

---

## Gene-by-Gene Evidence Summary

### Primary Targets

| Gene | Known ALS Connection | Expression Data Available? | Direction | Key Reference |
|------|---------------------|---------------------------|-----------|---------------|
| **CORO1C** | None direct; sister gene CORO1A is 5.3x upregulated in ALS plasma exosomes | NO transcriptomic data in ALS | Unknown | [Springer 2022 (CORO1A)](https://link.springer.com/article/10.1007/s11684-021-0905-y) |
| **CFL2** | Cofilin phosphorylation enhanced in C9ORF72-ALS motor neurons | Phospho-proteomics only, NO RNA-seq expression data | p-CFL increased (protein level) | [Sivadasan et al. 2016, Nat Neurosci](https://www.nature.com/articles/nn.4407) |
| **PFN1** | Causal mutations in fALS AND sporadic ALS; G118V mouse model exists | YES (GSE113924 is the PFN1 mouse); spatial transcriptomics shows altered expression | Mutant = loss + gain of function | [Fil et al. 2018](https://www.nature.com/articles/s41598-018-31132-y) |

### Extended Targets

| Gene | Known ALS Connection | Expression Data Available? | Key Reference |
|------|---------------------|---------------------------|---------------|
| **PLS3** | SMA protective modifier; proposed for "other MN diseases" | NOT tested in ALS RNA-seq | [Oprea et al. 2008, Science](https://pubmed.ncbi.nlm.nih.gov/18440926/) |
| **NCALD** | SMA protective modifier (endocytosis); no ALS data | NOT tested in ALS | [Riessland et al. 2017, AJHG](https://pubmed.ncbi.nlm.nih.gov/28132687/) |
| **STMN2** | Most downregulated in TDP-43-depleted MNs; hallmark of ALS | YES -- extensively validated | [Klim et al. 2019, Nat Neurosci](https://www.nature.com/articles/s41593-018-0300-4) |
| **ROCK2** | Major regulator of axonal degeneration; Rho/ROCK pathway in SMA | Expression in ALS spinal cord not specifically reported | [Koch et al. 2014, Cell Death Dis](https://www.nature.com/articles/cddis2014191) |
| **ACTG1** | Gamma-actin; structural component | NOT specifically tested in ALS RNA-seq | GeneCards |
| **ACTR2** | Arp2/3 complex (CORO1C interactor) | NOT specifically tested in ALS RNA-seq | GeneCards |
| **ABI2** | Arp2/3 regulator, actin dynamics | NOT specifically tested in ALS RNA-seq | GeneCards |

---

## Critical Supporting Evidence

### 1. CORO1A Upregulation in ALS (Novel Finding)
- **CORO1A** (coronin-1A, same family as CORO1C) is **5.3-fold elevated** in plasma exosomes of ALS patients vs. healthy controls
- CORO1A increases with disease progression in both plasma and mouse spinal cord
- CORO1A overexpression causes: increased apoptosis, oxidative stress, overactivated autophagy, blocked autophagosome-lysosome fusion
- **Implication**: If CORO1A is elevated in ALS, CORO1C may also be dysregulated -- they share actin-binding and endocytic functions
- Source: [Springer/MedScience 2022](https://link.springer.com/article/10.1007/s11684-021-0905-y)

### 2. C9ORF72-Cofilin Axis in ALS Motor Neurons
- C9ORF72 forms a complex with cofilin and actin-binding proteins
- C9ORF72 depletion enhances cofilin phosphorylation (inactivation) via LIMK1/2
- This reduces axonal actin dynamics in motor neurons
- Validated in: C9orf72-depleted MNs, patient iPSC-MNs, post-mortem brain
- **Implication**: CFL2 expression changes may accompany the phosphorylation changes -- no one has checked RNA levels
- Source: [Sivadasan et al. 2016, Nature Neuroscience](https://www.nature.com/articles/nn.4407)

### 3. SMA-ALS Actin Convergence (Review)
- Hensel & Claus 2018 explicitly proposed that SMA and ALS converge on actin cytoskeleton dysfunction
- SMN binds profilins; PFN1 mutations cause ALS; both lead to actin dysregulation
- The review noted: "a common molecular mechanism involving the actin cytoskeleton" for MN degeneration
- **Critical gap**: This was a hypothesis paper -- NO transcriptomic validation was performed
- Source: [Hensel & Claus 2018, Neuroscientist 24:54-72](https://journals.sagepub.com/doi/abs/10.1177/1073858417705059)

### 4. Actin Modulation Rescues Nucleocytoplasmic Transport in ALS
- Modulation of actin polymerization rescues nuclear pore dysfunction caused by both PFN1 mutations AND C9ORF72 repeat expansion
- This connects actin dynamics to a central ALS mechanism (TDP-43 mislocalization, nuclear pore damage)
- Source: [Giampetruzzi et al. 2019, Nature Communications](https://www.nature.com/articles/s41467-019-11837-y)

---

## Actionable Next Steps (Phase 2)

### Quick Wins (1-2 hours each)
1. **Download GSE113924 supplementary DEG tables** -- search for Coro1c, Cfl2, Pls3, Ncald, Stmn2, Rock2 in the full gene list
2. **Browse Humphrey lab data portal** at [jackhump.github.io](https://jackhump.github.io/ALS_SpinalCord_QTLs/) -- try gene-level lookup for CORO1C, CFL2, PFN1
3. **Check Expression Atlas** at [EBI](https://www.ebi.ac.uk/gxa/home) for pre-computed expression of our genes across ALS datasets

### Computational Analysis (4-8 hours)
4. **GSE153960 DE analysis**: Download Zenodo counts, run DESeq2 for our 11 genes, generate volcano plot
5. **GSE113924 reanalysis**: If genes not in published DEG list, download raw counts, run targeted DE
6. **GSE287257 snRNA-seq**: Download, process with Scanpy/Seurat, extract motor neuron cluster, test actin genes

### Validation & Publication
7. **Cross-dataset comparison**: Are the same actin genes consistently dysregulated across all 3 datasets?
8. **Direction consistency**: Do CORO1C/CFL2/PFN1 change in the same direction in ALS as in SMA?
9. **Positive controls**: STMN2 should be down in all ALS datasets; GFAP/AIF1 should be up (glia)

---

## Prediction: What We Expect to Find

Based on the mechanistic evidence, here are testable predictions:

| Prediction | Rationale | Confidence |
|------------|-----------|------------|
| CORO1C will be dysregulated in ALS motor neurons | CORO1A (same family) is 5.3x up in ALS; CORO1C is an SMA modifier | Medium |
| CFL2 RNA levels may NOT change, but p-CFL will | Cofilin regulation in ALS is post-translational (LIMK phosphorylation) | Medium-High |
| PFN1 expression may be unchanged in sporadic ALS | PFN1 mutations are rare; sporadic ALS may not alter PFN1 transcription | Medium |
| PLS3 may be reduced in ALS motor neurons | PLS3 is protective in SMA; loss would worsen both diseases | Low (speculative) |
| STMN2 will be strongly downregulated | Established hallmark of TDP-43 ALS | Very High (positive control) |
| ROCK2 may be upregulated | Rho/ROCK pathway activated in SMA; ROCK2 is a major CNS neurodegeneration regulator | Medium |
| Actin pathway changes will be motor neuron-enriched | MN vulnerability in ALS; actin dynamics critical for axonal maintenance | Medium |

---

## Key Literature References

1. Humphrey et al. (2023) "Integrative transcriptomic analysis of the ALS spinal cord" -- *Nature Neuroscience* 26:150-162. [PubMed](https://pubmed.ncbi.nlm.nih.gov/36482247/) | [Data Portal](https://jackhump.github.io/ALS_SpinalCord_QTLs/)
2. Fil et al. (2018) "RNA-Seq of hPFN1-G118V mouse spinal cord" -- *Scientific Reports* 8:13737. [PubMed](https://pubmed.ncbi.nlm.nih.gov/30213953/)
3. Bhargava et al. (2025) "RIPK1 signaling in ALS pathogenesis" -- *Immunity*. [PubMed](https://pubmed.ncbi.nlm.nih.gov/40132594/)
4. Sivadasan et al. (2016) "C9ORF72-cofilin actin dynamics in motor neurons" -- *Nature Neuroscience* 19:1610-1618. [PubMed](https://pubmed.ncbi.nlm.nih.gov/27723745/)
5. Hensel & Claus (2018) "The actin cytoskeleton in SMA and ALS" -- *Neuroscientist* 24:54-72. [PubMed](https://pubmed.ncbi.nlm.nih.gov/28459188/)
6. CORO1A in ALS (2022) "Increased expression of coronin-1a in ALS" -- *MedScience/Frontiers of Medicine*. [Springer](https://link.springer.com/article/10.1007/s11684-021-0905-y)
7. Giampetruzzi et al. (2019) "Actin polymerization and nucleocytoplasmic transport in ALS" -- *Nature Communications*. [Nature](https://www.nature.com/articles/s41467-019-11837-y)
8. Klim et al. (2019) "TDP-43 sustains STMN2 in motor neurons" -- *Nature Neuroscience* 22:167-179. [PubMed](https://pubmed.ncbi.nlm.nih.gov/30643292/)
9. Oprea et al. (2008) "PLS3 as protective SMA modifier" -- *Science*. [PubMed](https://pubmed.ncbi.nlm.nih.gov/18440926/)
10. Riessland et al. (2017) "NCALD suppression protects in SMA" -- *AJHG*. [PubMed](https://pubmed.ncbi.nlm.nih.gov/28132687/)
