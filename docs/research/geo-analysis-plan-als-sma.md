# GEO Dataset Mining Plan: Actin Pathway Genes in ALS
## Cross-Disease Analysis for CORO1C / CFL2 / PFN1 / Actin Signature

**Date**: 2026-03-22
**Status**: Computational analysis plan -- ready for execution
**Prerequisite**: [SMA-ALS Convergence Deep Dive](sma-als-convergence-deep-dive.md)
**Key insight**: Nobody has systematically checked ALS RNA-seq datasets for CORO1C/CFL2/PFN1 co-expression. This plan fills that gap.

---

## 1. Priority GEO Datasets

### Tier 1: Highest Priority (Large human cohorts, RNA-seq, raw data available)

#### 1.1 GSE153960 -- Human ALS Spinal Cord Transcriptome Atlas
| Field | Value |
|-------|-------|
| **GEO Accession** | [GSE153960](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE153960) |
| **Samples** | 380 transcriptomes (154 ALS, 49 non-neurological controls, + other conditions) |
| **Species** | Human |
| **Tissue** | Post-mortem spinal cord (cervical, thoracic, lumbar segments) |
| **Data type** | Bulk RNA-seq |
| **Raw data** | Yes -- FASTQ on SRA |
| **Publication** | [Humphrey et al. 2023, Nature Communications](https://www.nature.com/articles/s41467-023-37630-6) |
| **Comparison groups** | ALS vs. control; C9orf72 vs. sporadic; cervical vs. lumbar; early vs. late stage |
| **Why highest priority** | Largest human ALS spinal cord RNA-seq dataset. Segment-level resolution allows testing whether actin gene dysregulation varies along the neuraxis. |

#### 1.2 Answer ALS Project -- iPSC Motor Neurons at Scale
| Field | Value |
|-------|-------|
| **Accession** | [Answer ALS / LINCS Portal](https://www.answerals.org/) + dbGAP for raw data |
| **Samples** | 433 iPSC lines (341 ALS, 92 controls); differentiated to spinal motor neurons (day 32) |
| **Species** | Human |
| **Tissue** | iPSC-derived motor neurons (diMN protocol) |
| **Data type** | Bulk RNA-seq + ATAC-seq |
| **Raw data** | Yes -- dbGAP (controlled access) + processed counts on LINCS |
| **Publication** | [Baxi et al. 2023, Neuron](https://www.cell.com/neuron/fulltext/S0896-6273(23)00034-X) |
| **Comparison groups** | ALS (C9orf72, SOD1, FUS, TARDBP, sporadic) vs. healthy controls |
| **Why highest priority** | Largest iPSC ALS resource. Controlled cell culture conditions eliminate tissue heterogeneity. Genetic subtype comparisons possible. |

#### 1.3 GSE113924 -- PFN1-G118V ALS Mouse Model
| Field | Value |
|-------|-------|
| **GEO Accession** | [GSE113924](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE113924) |
| **Samples** | hPFN1-G118V transgenic mouse spinal cord (pre-symptomatic + end-stage + wild-type) |
| **Species** | Mouse |
| **Tissue** | Spinal cord |
| **Data type** | Bulk RNA-seq |
| **Raw data** | Yes -- SRA |
| **Comparison groups** | PFN1-G118V vs. WT; pre-symptomatic vs. end-stage |
| **Why highest priority** | Directly tests the PFN1-actin axis. If CORO1C/CFL2 are dysregulated in a PFN1 mutant background, it validates the shared actin pathway model. Pre-symptomatic timepoint reveals early/causal changes. |

### Tier 2: High Priority (Motor neuron-specific or single-cell resolution)

#### 2.1 GSE287257 -- ALS Spinal Cord snRNA-seq (2025)
| Field | Value |
|-------|-------|
| **GEO Accession** | [GSE287257](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE287257) |
| **Samples** | 8 ALS (6 sporadic, 2 familial) + 4 age-matched controls |
| **Species** | Human |
| **Tissue** | Cervical spinal cord, post-mortem |
| **Data type** | Single-nucleus RNA-seq (snRNA-seq) |
| **Raw data** | Yes -- SRA |
| **Publication** | [Bhargava et al. 2025, Immunity](https://www.cell.com/immunity/fulltext/S1074-7613(25)00091-3) |
| **Comparison groups** | ALS vs. control; cell-type-resolved (motor neurons, astrocytes, microglia, oligodendrocytes) |
| **Why high priority** | Cell-type resolution. Can determine whether actin gene dysregulation is motor neuron-specific or pan-cellular. RIPK1 signaling data adds SARM1/necroptosis context. |

#### 2.2 GSE190442 -- Human Spinal Cord Cellular Taxonomy
| Field | Value |
|-------|-------|
| **GEO Accession** | [GSE190442](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE190442) |
| **Samples** | ~55,289 nuclei from 7 human donors |
| **Species** | Human |
| **Tissue** | Post-mortem lumbar spinal cord |
| **Data type** | Single-nucleus RNA-seq |
| **Raw data** | Yes |
| **Publication** | [Yadav et al. 2023, Neuron](https://www.cell.com/neuron/fulltext/S0896-6273(23)00031-4) |
| **Comparison groups** | 64 cell subtypes identified; healthy reference atlas |
| **Why high priority** | Baseline reference atlas. Establishes normal actin gene expression per cell type. Essential for interpreting disease datasets. |

#### 2.3 GSE76220 -- Laser-Captured ALS Motor Neurons
| Field | Value |
|-------|-------|
| **GEO Accession** | [GSE76220](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE76220) |
| **Samples** | 13 sporadic ALS + 9 controls |
| **Species** | Human |
| **Tissue** | Laser-capture microdissected motor neurons, lumbar spinal cord |
| **Data type** | Bulk RNA-seq |
| **Raw data** | Yes |
| **Comparison groups** | sALS motor neurons vs. control motor neurons |
| **Why high priority** | Pure motor neuron populations (no glial contamination). Small n but gold-standard enrichment method. |

#### 2.4 GSE106382 -- iPSC Motor Neurons (fALS + sALS)
| Field | Value |
|-------|-------|
| **GEO Accession** | [GSE106382](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE106382) |
| **Samples** | iPSC-derived motor neurons from fALS (SOD1, FUS, C9orf72), sALS, and healthy controls |
| **Species** | Human |
| **Tissue** | iPSC-derived spinal motor neurons |
| **Data type** | Bulk RNA-seq |
| **Raw data** | Yes |
| **Publication** | [Melamed et al. 2019, Cell Reports](https://pmc.ncbi.nlm.nih.gov/articles/PMC7897311/) |
| **Comparison groups** | fALS vs. sALS vs. control; per-genotype (SOD1, FUS, C9orf72) |
| **Why high priority** | Tests whether actin signature appears across ALL genetic forms of ALS. Cross-comparison with SMA iPSC data possible. |

#### 2.5 GSE52202 -- C9orf72 iPSC Motor Neurons
| Field | Value |
|-------|-------|
| **GEO Accession** | [GSE52202](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE52202) |
| **Samples** | iPSC-derived motor neurons from C9orf72 ALS carriers + controls |
| **Species** | Human |
| **Tissue** | iPSC-derived motor neurons |
| **Data type** | RNA-seq |
| **Raw data** | Yes |
| **Comparison groups** | C9orf72 ALS vs. healthy control motor neurons |
| **Why high priority** | C9orf72 is the most common genetic cause of ALS. Integrated multi-omic (DNA + RNA + epigenetics + protein) analysis available. |

### Tier 3: Medium Priority (Mouse models, microarray, or specialized)

#### 3.1 GSE40438 -- SOD1-G93A Mouse: Vulnerable vs. Resistant Motor Neurons
| Field | Value |
|-------|-------|
| **GEO Accession** | [GSE40438](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE40438) |
| **Samples** | SOD1-G93A mouse motor neuron populations |
| **Species** | Mouse |
| **Tissue** | Spinal cord motor neurons |
| **Data type** | Bulk RNA-seq |
| **Raw data** | Yes |
| **Comparison groups** | ALS-vulnerable (limb) vs. ALS-resistant (oculomotor) motor neurons |
| **Why medium priority** | Tests differential vulnerability hypothesis: do vulnerable motor neurons show worse actin dysregulation? |

#### 3.2 GSE93939 -- Oculomotor vs. Spinal Motor Neurons
| Field | Value |
|-------|-------|
| **GEO Accession** | [GSE93939](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE93939) |
| **Samples** | Oculomotor and spinal motor neurons |
| **Species** | Mouse |
| **Tissue** | Brainstem + spinal cord |
| **Data type** | RNA-seq |
| **Raw data** | Yes |
| **Comparison groups** | ALS-resistant (oculomotor) vs. ALS-vulnerable (spinal) |
| **Why medium priority** | If ALS-resistant motor neurons have HIGHER baseline CORO1C/PFN1 or LOWER CFL2, it supports a protective actin dynamics model. |

#### 3.3 GSE38820 -- Pre-symptomatic SOD1-G85R Motor Neurons
| Field | Value |
|-------|-------|
| **GEO Accession** | [GSE38820](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE38820) |
| **Samples** | SOD1-G85R mouse motor neurons, pre-symptomatic stage |
| **Species** | Mouse |
| **Tissue** | Spinal motor neurons |
| **Data type** | Bulk RNA-seq |
| **Raw data** | Yes |
| **Comparison groups** | SOD1-G85R pre-symptomatic vs. wild-type |
| **Why medium priority** | Pre-symptomatic timepoint reveals early/causal changes before neurodegeneration confounds. |

#### 3.4 GSE178693 -- SOD1 Mouse Brainstem Single-Cell
| Field | Value |
|-------|-------|
| **GEO Accession** | [GSE178693](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE178693) |
| **Samples** | SOD1 transgenic mouse brainstem |
| **Species** | Mouse |
| **Tissue** | Brainstem |
| **Data type** | Single-cell RNA-seq |
| **Raw data** | Yes |
| **Comparison groups** | SOD1 mutant vs. wild-type; multiple cell types |
| **Why medium priority** | Cell-type resolution in mouse model. Brainstem complements spinal cord data. |

#### 3.5 GSE118723 -- iPSC Motor Neuron Single-Cell ALS
| Field | Value |
|-------|-------|
| **GEO Accession** | [GSE118723](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE118723) |
| **Samples** | iPSC-derived motor neurons |
| **Species** | Human |
| **Tissue** | iPSC-derived motor neurons |
| **Data type** | Single-cell RNA-seq |
| **Raw data** | Yes |
| **Publication** | [Ho et al. 2021, Cell Stem Cell](https://www.biorxiv.org/content/10.1101/2020.04.27.064584v1) |
| **Comparison groups** | ALS (C9orf72, sporadic) vs. control; culture vs. experiment variability |
| **Why medium priority** | Single-cell resolution in iPSC motor neurons. Can identify motor neuron subpopulations most affected by actin dysregulation. |

### Tier 4: Supplementary (Microarray, older, specialized tissue)

| GEO Accession | Type | Samples | Tissue | Notes |
|---------------|------|---------|--------|-------|
| GSE18920 | Microarray | sALS + ctrl | LCM motor neurons | Older but motor neuron-pure |
| GSE56500 | Microarray | sALS + ctrl | Motor neurons | Motor neuron expression profiles |
| GSE68605 | Microarray | sALS + ctrl | Motor neurons | Motor neuron expression profiles |
| GSE67196 | RNA-seq | iPSC-MNs | iPSC motor neurons | fALS/sALS cross-comparison |
| GSE243076 | snRNA-seq + Spatial | 9 donors | Spinal cord | Healthy reference; spatial context |

---

## 2. Gene Panel

### Primary targets (our novel hypotheses)

| Gene | Symbol | Why |
|------|--------|-----|
| Coronin-1C | **CORO1C** | Elevated in SMA; UNSTUDIED in ALS. Central hypothesis. |
| Cofilin-2 | **CFL2** | Muscle-specific cofilin; NMJ regulator. Actin rod hypothesis. |
| Profilin-1 | **PFN1** | Mutated in fALS; SMN binding partner; +46% in SMA organoids. |

### Extended actin pathway panel

| Gene | Symbol | Why |
|------|--------|-----|
| Profilin-2 | **PFN2** | Neuron-specific; SMN binding partner; PFN1/PFN2 ratio matters. |
| Plastin-3 | **PLS3** | SMA modifier gene; actin bundler. |
| Neurocalcin delta | **NCALD** | SMA modifier gene; calcium-actin crosstalk. |
| Stathmin-2 | **STMN2** | Cryptic splicing in ALS; rescues SMA axons. Correlate with actin genes. |
| Rho kinase 2 | **ROCK2** | Kinase upstream of cofilin phosphorylation. Fasudil target. |
| Gamma-actin | **ACTG1** | Cytoplasmic actin isoform; structural component. |
| ARP2/3 complex | **ACTR2** | Actin nucleation; coronin-regulated. |
| Abi-2 | **ABI2** | WAVE/WASP complex; actin signaling. |

### Contextual markers (for correlation analysis)

| Gene | Symbol | Why |
|------|--------|-----|
| Cofilin-1 | **CFL1** | Hyperphosphorylated in sALS; compare with CFL2. |
| LIMK1 | **LIMK1** | Cofilin kinase; ROCK pathway readout. |
| LIMK2 | **LIMK2** | Second cofilin kinase. |
| CAP2 | **CAP2** | Elevated in ALS CSF; cofilin regulator. |
| Coronin-1A | **CORO1A** | 5.3x elevated in ALS exosomes; compare with CORO1C. |
| Coronin-1B | **CORO1B** | Complete coronin family profiling. |
| Coronin-2A | **CORO2A** | Complete coronin family profiling. |
| Coronin-7 | **CORO7** | Complete coronin family profiling. |
| Tropomyosin 4 | **TPM4** | Elevated in sALS (cofilin-TDP-43 study). |
| TDP-43 | **TARDBP** | ALS hallmark; correlate with actin genes. |
| SMN1/SMN2 | **SMN1/SMN2** | SMA gene; "acquired SMA" hypothesis in ALS. |

**Total: 24 genes** -- small enough to query rapidly across all datasets.

---

## 3. Analysis Pipeline Design

### 3.1 Bulk RNA-seq Pipeline (Datasets: GSE153960, GSE113924, GSE76220, GSE106382, GSE52202, Answer ALS, others)

```
Step 1: Download
    GEOquery (R) or ffq/fasterq-dump (command line) to pull FASTQ or count matrices
    For Answer ALS: apply for dbGAP access or use processed counts from LINCS portal

Step 2: Quality Control
    FastQC --> MultiQC for read quality
    Trim adapters with Trim Galore or fastp
    Check for rRNA contamination, GC bias

Step 3: Alignment (if starting from FASTQ)
    STAR aligner (human: GRCh38/hg38; mouse: GRCm39/mm39)
    GENCODE v44 (human) or vM33 (mouse) annotation
    featureCounts (Subread) for gene-level quantification
    Alternative: Salmon pseudo-alignment (faster, adequate for gene-level)

Step 4: Normalization & Differential Expression
    Tool: DESeq2 (primary) + edgeR (validation)
    Design formula: ~ condition + covariates (sex, age, site, batch)
    For 24 target genes: extract log2FC + padj from full DE results
    Shrunken log2FC (apeglm) for effect size ranking

Step 5: Targeted Gene Analysis
    Extract normalized counts (VST or rlog) for 24-gene panel
    Heatmap: genes x samples, clustered by condition
    Volcano plot: highlight actin pathway genes
    Correlation matrix: pairwise Pearson/Spearman across 24 genes
    PCA of 24-gene panel only: do ALS and SMA cluster together?

Step 6: Cross-Dataset Meta-Analysis
    Combat-seq (sva package) for batch correction across datasets
    Random-effects meta-analysis (metafor R package) for combined effect sizes
    Forest plots per gene across all datasets
    I-squared heterogeneity statistic
```

### 3.2 Single-Cell / Single-Nucleus Pipeline (Datasets: GSE287257, GSE190442, GSE178693, GSE118723)

```
Step 1: Download
    Pull processed count matrices from GEO (CellRanger output or h5ad)
    If only raw FASTQ: run CellRanger count locally (requires ~32GB RAM)

Step 2: QC & Preprocessing (Scanpy)
    Filter: min_genes=200, min_cells=3, mito% < 20%
    Doublet removal: Scrublet
    Normalize: scran or total-count normalization
    Log-transform, HVG selection (2000-3000 genes)

Step 3: Integration (if combining datasets)
    scVI or Harmony for batch integration
    Benchmark: LISI score to verify mixing

Step 4: Cell Type Annotation
    Leiden clustering at multiple resolutions
    Marker genes: MNX1/CHAT (motor neurons), GFAP/AQP4 (astrocytes),
                  CX3CR1/CSF1R (microglia), MBP/MOG (oligodendrocytes)
    Transfer labels from GSE190442 reference atlas if available

Step 5: Targeted Analysis
    DotPlot: 24 genes x cell types
    Violin plots: each gene, motor neurons only, ALS vs. control
    Differential expression: Wilcoxon rank-sum per cell type
    Cell-type-specific fold changes for CORO1C, CFL2, PFN1
    Key question: Is dysregulation motor neuron-AUTONOMOUS or non-cell-autonomous?

Step 6: Trajectory / Pseudotime (if motor neuron subtypes vary)
    Monocle3 or diffusion pseudotime
    Plot actin gene expression along disease pseudotime
    Identify tipping points where actin signature shifts
```

### 3.3 Microarray Pipeline (Datasets: GSE18920, GSE56500, GSE68605)

```
Step 1: Download processed expression matrices from GEO (GEO2R or GEOquery)
Step 2: Normalize (RMA for Affymetrix; quantile normalization for Illumina)
Step 3: Probe-to-gene mapping (use platform annotation file)
Step 4: limma for differential expression
Step 5: Extract 24-gene panel results
Note: Microarray has lower dynamic range -- use for directional validation only,
      not for quantitative comparisons with RNA-seq.
```

### 3.4 Handling Batch Effects Across Datasets

This is the hardest part of the analysis. Strategy:

1. **Never merge raw counts across datasets.** Run DE within each dataset independently first.
2. **Meta-analysis approach (primary)**: Combine summary statistics (log2FC, SE) using random-effects meta-analysis (DerSimonian-Laird). This avoids all batch effect issues.
3. **Integrated analysis (secondary)**: For exploratory PCA/UMAP across datasets, use ComBat-seq (for bulk) or scVI (for single-cell) to remove batch while preserving biological signal.
4. **Validation rule**: A finding must be significant (padj < 0.05) in at least 2 independent datasets to be reported. Direction of change must be consistent.

### 3.5 Statistical Tests

| Analysis | Test | Multiple testing correction |
|----------|------|-----------------------------|
| Differential expression (bulk) | DESeq2 Wald test | Benjamini-Hochberg FDR |
| Differential expression (single-cell) | Wilcoxon rank-sum | Bonferroni per cell type |
| Cross-gene correlation | Spearman rho | Bonferroni for 24x24 matrix |
| Meta-analysis | Random-effects (DerSimonian-Laird) | FDR across genes |
| Enrichment | GSEA (fgsea) for actin/cytoskeleton gene sets | FDR |
| Survival correlation (if clinical data) | Cox proportional hazards | FDR |

**Significance thresholds**:
- Discovery: padj < 0.05, |log2FC| > 0.5
- Replication: padj < 0.1, same direction
- Cross-disease "shared signature": significant in >= 1 ALS dataset AND >= 1 SMA dataset, same direction

---

## 4. Hypotheses to Test

### Hypothesis A: CORO1C is dysregulated in ALS motor neurons
- **Prediction**: CORO1C upregulated in ALS spinal cord (like CORO1A in exosomes)
- **Datasets**: GSE153960 (bulk), GSE287257 (snRNA-seq), GSE76220 (LCM motor neurons)
- **Strong positive**: log2FC > 0.5, padj < 0.05 in >= 2 datasets
- **Impact if confirmed**: Validates coronin family as universal motor neuron stress markers. CORO1C becomes a candidate ALS biomarker.
- **Impact if negative**: CORO1C is SMA-specific, ruling out shared coronin mechanism. Still informative.

### Hypothesis B: CFL2 is upregulated in ALS (actin rod hypothesis)
- **Prediction**: CFL2 (muscle cofilin) upregulated in ALS spinal cord or NMJ-adjacent tissue
- **Context**: CFL1 is known to be hyperphosphorylated in sALS motor neurons (Brain 2026). CFL2 role at NMJ is established but its expression in ALS tissue is unknown.
- **Datasets**: GSE153960, GSE113924, GSE287257
- **Key distinction**: CFL1 (neuronal) vs. CFL2 (muscle) expression -- bulk RNA-seq cannot distinguish motor neuron vs. muscle contribution. snRNA-seq is critical for this.

### Hypothesis C: PFN1 is dysregulated in sporadic ALS (not just familial)
- **Prediction**: PFN1 expression altered in sporadic ALS, not just in PFN1-mutant familial ALS
- **Logic**: If PFN1 is only disrupted by its own mutations, the actin convergence is limited to rare fALS. If PFN1 expression changes in sporadic ALS (98% of cases), the convergence is disease-wide.
- **Datasets**: GSE153960 (sALS subset), Answer ALS (sALS lines), GSE76220 (all sALS)
- **Critical test**: PFN1/PFN2 ratio in sALS vs. controls. In SMA, PFN2a is upregulated while PFN1 is +46%.

### Hypothesis D: Shared "actin signature" across SMA and ALS
- **Prediction**: A subset of the 24-gene actin panel shows concordant dysregulation in both diseases
- **Method**: For each gene, compare direction and magnitude of change in SMA datasets (already analyzed on platform) vs. ALS datasets (this plan)
- **Visualization**: Scatter plot of log2FC(SMA) vs. log2FC(ALS) for all 24 genes. Genes in the same quadrant (both up or both down) are the shared signature.
- **Impact**: If >= 5 genes share direction, propose "actin motor neuron degeneration signature." If < 3, the diseases diverge at the actin level despite sharing individual targets.

### Hypothesis E: PFN1-G118V mouse recapitulates the SMA actin profile
- **Prediction**: The PFN1-G118V ALS mouse (GSE113924) shows similar actin pathway gene changes as SMA mice
- **Specific test**: Compare CORO1C, CFL2, PLS3, NCALD, ROCK2 expression between GSE113924 and existing SMA mouse RNA-seq
- **Impact**: If the PFN1 mutant mimics SMA at the actin level, PFN1 is truly the "Rosetta Stone" connecting both diseases.

### Hypothesis F: Actin gene dysregulation predicts motor neuron vulnerability
- **Prediction**: ALS-vulnerable motor neuron populations (spinal) show worse actin dysregulation than ALS-resistant populations (oculomotor)
- **Datasets**: GSE40438 (vulnerable vs. resistant MNs), GSE93939 (oculomotor vs. spinal)
- **Impact**: Establishes actin dynamics as a vulnerability factor, not just a disease marker.

---

## 5. Execution Plan

### 5.1 Compute Requirements

| Task | CPU/GPU | RAM | Disk | Time estimate |
|------|---------|-----|------|---------------|
| Download FASTQs (all datasets) | CPU | 8 GB | ~500 GB | 4-8 hours |
| STAR alignment (380 samples, GSE153960) | CPU (16 cores) | 32 GB | 200 GB | 12-24 hours |
| DESeq2 on count matrices (all bulk datasets) | CPU | 16 GB | 5 GB | 30 min total |
| CellRanger (if needed for snRNA-seq) | CPU (16 cores) | 64 GB | 100 GB | 6-12 hours |
| Scanpy pipeline (snRNA-seq) | CPU | 32 GB | 20 GB | 2-4 hours |
| Meta-analysis + visualization | CPU | 8 GB | 1 GB | 30 min |
| **Total** | **CPU only** | **32-64 GB** | **~800 GB** | **~24-48 hours** |

**GPU NOT required.** This entire analysis is CPU-based. RNA-seq alignment and differential expression do not benefit from GPU acceleration. Single-cell analysis (Scanpy) is CPU-only.

### 5.2 Where to Run

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **Local WSL** | Free, immediate, persistent | 16 GB RAM limit (likely); disk space on Dropbox | Only for processed count matrices |
| **Prestaging server** (85.215.32.196) | Linux, always on, PM2 | No sudo, limited disk, shared | Good for lightweight analysis |
| **Google Colab Pro** | Free GPU, 25 GB RAM | Session timeouts, disk limits | Good for single-dataset prototyping |
| **Vast.ai GPU instance** | Cheap ($0.20-0.50/hr), scalable | Setup overhead | Not needed (CPU-only) |
| **HPC/Cloud (AWS/GCP)** | Unlimited, reproducible | Cost ($50-100 for full run) | Best for full STAR alignment pipeline |

**Recommended approach**:

1. **Phase 1 (free, immediate)**: Download processed count matrices (GEO2R or supplementary tables) for GSE153960, GSE113924, GSE76220. Run DESeq2 locally. This answers the primary hypotheses within hours.
2. **Phase 2 (if Phase 1 positive)**: Full FASTQ alignment on a cloud instance for datasets where processed counts are unavailable or insufficient.
3. **Phase 3**: Single-cell analysis (GSE287257, GSE190442) on a 64 GB RAM instance.

### 5.3 Shortcut: GEO2R for Instant Results

For many datasets, GEO provides the **GEO2R** web tool that runs limma on processed expression data directly in the browser. We can get preliminary results for our 24-gene panel in minutes:

1. Go to each GSE page on GEO
2. Click "Analyze with GEO2R"
3. Define groups (ALS vs. control)
4. Run analysis
5. Search results table for our 24 genes
6. Record log2FC, p-value, adj.p.value

**Limitation**: GEO2R uses limma (not DESeq2) and may not have optimal normalization. Use for screening; confirm with full pipeline.

### 5.4 Phased Execution Timeline

```
Week 1: Quick Screen (GEO2R + processed counts)
  Day 1-2: GEO2R screen of GSE153960, GSE76220, GSE113924
           Extract 24-gene panel results from each
  Day 3:   Download processed count matrices where available
           Run DESeq2 locally for GSE153960 (if counts available)
  Day 4-5: Compile results table: gene x dataset x log2FC x padj
           Generate initial heatmap and forest plots
  DECISION POINT: Do >= 2 genes show consistent dysregulation?

Week 2: Deep Analysis (full pipeline, conditional on Week 1 results)
  Day 6-7:  Apply for Answer ALS dbGAP access (2-4 week turnaround)
  Day 8-9:  Full DESeq2 pipeline on all Tier 1 + Tier 2 bulk datasets
            ComBat-seq batch correction for meta-analysis
  Day 10:   Random-effects meta-analysis across all datasets
            Forest plots, funnel plots, I-squared

Week 3: Single-Cell Analysis
  Day 11-12: Download and process GSE287257 (snRNA-seq)
  Day 13-14: Scanpy pipeline: clustering, annotation, cell-type DE
  Day 15:    Cell-type-specific actin gene expression plots

Week 4: Integration and Write-Up
  Day 16-17: Cross-disease comparison (ALS results vs. SMA platform data)
  Day 18-19: Shared actin signature analysis
  Day 20:    Figures, tables, manuscript-ready results
```

### 5.5 Software Dependencies

```
# R packages (for bulk RNA-seq)
BiocManager::install(c("DESeq2", "edgeR", "limma", "sva",  # DE + batch
                        "GEOquery", "SummarizedExperiment",  # data access
                        "apeglm", "ashr",                    # shrinkage
                        "ComplexHeatmap", "EnhancedVolcano", # visualization
                        "metafor", "meta",                   # meta-analysis
                        "fgsea", "msigdbr",                  # pathway analysis
                        "org.Hs.eg.db", "org.Mm.eg.db"))    # annotation

# Python packages (for single-cell)
pip install scanpy anndata scvi-tools scrublet harmonypy
pip install leidenalg igraph louvain
pip install matplotlib seaborn plotly

# Command-line tools (for FASTQ processing)
# STAR, Salmon, featureCounts (Subread), FastQC, MultiQC, Trim Galore
# CellRanger (10x Genomics, for snRNA-seq if needed)
```

---

## 6. Expected Outcomes and Impact

### If CORO1C is upregulated in ALS:
- Validates the "shared coronin-actin disruption" model
- CORO1C becomes a candidate cross-disease biomarker (measurable in CSF/exosomes)
- Justifies CORO1C functional studies in ALS motor neurons
- Strengthens the SMA platform's novelty (we identified this connection first)

### If CFL2 is dysregulated at ALS NMJs:
- Confirms the NMJ as the "actin battlefield" in both diseases
- CFL2 becomes a therapeutic target for NMJ stabilization
- Links to ROCK inhibitor mechanism (Fasudil/Bravyl)

### If a shared actin signature exists (>= 5 concordant genes):
- Defines a new molecular subtype: "actin motor neuron degeneration"
- Enables drug repurposing between SMA and ALS pipelines
- Publishable as a research paper (no one has done this systematic comparison)
- Foundation for grant applications (cross-disease funding is attractive to NIH/ERC)

### If PFN1 is dysregulated in sporadic ALS:
- Extends PFN1 relevance from rare fALS to all ALS
- Validates PFN1 as the "Rosetta Stone" connecting both diseases
- Supports PFN1-targeting therapies for broader patient populations

---

## 7. Risk Assessment

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Processed count matrices not available for some datasets | Medium | Use GEO supplementary files; fall back to FASTQ alignment |
| Answer ALS dbGAP access denied or slow | Medium | Use other iPSC datasets (GSE106382, GSE52202) as alternatives |
| Actin genes not detected in single-cell (dropout) | Medium | Use imputation (MAGIC) or aggregate to pseudo-bulk |
| Batch effects dominate cross-dataset signal | Low | Use meta-analysis approach (never merge raw counts) |
| All hypotheses null (no actin dysregulation in ALS) | Low | Still publishable as a negative result; narrows the field |
| Species differences (mouse vs. human) confound results | Medium | Analyze human and mouse separately; only compare directions |

---

## 8. References

Key papers underpinning this analysis plan (full references in [sma-als-convergence-deep-dive.md](sma-als-convergence-deep-dive.md)):

- Humphrey et al. 2023 -- GSE153960, 380 ALS spinal cord transcriptomes ([Nature Comms](https://www.nature.com/articles/s41467-023-37630-6))
- Baxi et al. 2023 -- Answer ALS, 433 iPSC lines ([Neuron](https://www.cell.com/neuron/fulltext/S0896-6273(23)00034-X))
- Bhargava et al. 2025 -- GSE287257, ALS snRNA-seq + RIPK1 ([Immunity](https://www.cell.com/immunity/fulltext/S1074-7613(25)00091-3))
- Yadav et al. 2023 -- GSE190442, human spinal cord atlas ([Neuron](https://www.cell.com/neuron/fulltext/S0896-6273(23)00031-4))
- Melamed et al. 2019 -- GSE106382, iPSC ALS cross-comparison ([Cell Reports](https://pmc.ncbi.nlm.nih.gov/articles/PMC7897311/))
- Hensel & Claus 2018 -- Actin cytoskeleton in SMA and ALS ([Neuroscientist](https://journals.sagepub.com/doi/abs/10.1177/1073858417705059))
- Hensel et al. 2022 -- Protein network ALS-SMA ([PMC8966079](https://pmc.ncbi.nlm.nih.gov/articles/PMC8966079/))
- Cofilin-TDP-43 2026 -- Actin drives TDP-43 pathology ([Brain](https://academic.oup.com/brain/advance-article/doi/10.1093/brain/awag096/8512674))
- Koch et al. 2024 -- ROCK-ALS Fasudil trial ([Lancet Neurol](https://www.thelancet.com/journals/laneur/article/PIIS1474-4422(24)00373-9/fulltext))
- Frontiers 2024 -- Meta-analysis ALS motor neurons ([Frontiers Genetics](https://www.frontiersin.org/journals/genetics/articles/10.3389/fgene.2024.1385114/full))
- Multi-region ALS brain transcriptome 2025 ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12023386/))

---

*Generated 2026-03-22. This is a computational analysis plan, not results. All dataset descriptions are based on GEO metadata and published papers. Execute Phase 1 (GEO2R quick screen) before committing to full pipeline.*
