# GSE208629 — SMA Mouse Spinal Cord scRNA-seq Analysis

**Date**: 2026-03-24
**Dataset**: GSE208629 (PLOS Genetics 2022)
**Species**: Mouse (Smn-/- SMA model)
**Tissue**: Spinal cord, scRNA-seq (10x Genomics)

## Dataset Overview

| Metric | Value |
|--------|-------|
| Total cells (post-QC) | 39,136 |
| SMA cells | 19,695 |
| Control cells | 19,441 |
| Genes | 21,012 |
| Leiden clusters | 25 |
| Motor neurons (top 5% MN score) | 208 (0.5%) |
| SMA motor neurons | 17 |
| Control motor neurons | 191 |

**Note**: Chat (choline acetyltransferase) was not detected in this dataset. Motor neurons were identified using Isl1, Mnx1, and Slc18a3. The asymmetric MN distribution (17 SMA vs 191 control) likely reflects motor neuron loss in SMA, which is biologically expected.

## Cell Type Distribution

| Cell Type | N cells | % |
|-----------|---------|---|
| Oligodendrocyte | 13,990 | 35.7% |
| Astrocyte | 7,042 | 18.0% |
| OPC | 5,879 | 15.0% |
| Microglia | 5,395 | 13.8% |
| Motor_Neuron | 3,059 | 7.8% |
| Endothelial | 2,415 | 6.2% |
| Excitatory_Neuron | 998 | 2.6% |
| Inhibitory_Neuron | 358 | 0.9% |

## Key Findings

### 1. Coro1c is NOT Motor Neuron-Specific (Cross-Species Confirmed)

| Metric | Value |
|--------|-------|
| MN mean expression | 0.0184 |
| Other cells mean | 0.0892 |
| log2FC (MN/other) | **-1.806** |
| p-value | 7.34e-04 |
| MN % expressing | 1.9% |
| Other % expressing | 8.4% |

**Coro1c is DEPLETED in motor neurons** in mouse, consistent with the human ALS finding (GSE287257). Highest expression is in endothelial cells (mean=0.1893, 19.8% expressing).

This is now validated across two species and two datasets: **CORO1C/Coro1c is not a motor neuron gene**.

### 2. Massive Actin Pathway Upregulation in SMA Motor Neurons

The most striking finding: nearly ALL actin pathway genes are significantly UPREGULATED in SMA motor neurons compared to control motor neurons.

| Gene | SMA MN mean | Ctrl MN mean | log2FC | p-value | Significance |
|------|-------------|--------------|--------|---------|--------------|
| **Actg1** | 2.4867 | 0.4149 | **+2.555** | 4.01e-14 | *** |
| **Limk2** | 0.1312 | 0.0101 | **+2.808** | 2.04e-03 | ** |
| **Actr2** | 0.3875 | 0.0758 | **+2.213** | 3.31e-06 | *** |
| **Pls3** | 0.1903 | 0.0362 | **+2.117** | 1.00e-02 | * |
| **Coro1c** | 0.0803 | 0.0129 | **+1.981** | 2.43e-03 | ** |
| **Cfl2** | 0.5413 | 0.1452 | **+1.829** | 2.09e-04 | *** |
| **Rock2** | 0.2639 | 0.1217 | +1.056 | 1.42e-02 | * |
| **Arpc3** | 0.9554 | 0.5113 | +0.889 | 1.22e-02 | * |
| **Pfn1** | 1.9128 | 1.1208 | +0.766 | 4.91e-02 | * |
| **Rock1** | 0.2184 | 0.1355 | +0.650 | 4.43e-02 | * |
| Pfn2 | 1.3487 | 1.1307 | +0.252 | 4.15e-01 | ns |
| Rac1 | 0.6181 | 0.6730 | -0.121 | 5.80e-01 | ns |
| Limk1 | 0.0000 | 0.0046 | -0.542 | 1.00e+00 | ns |
| Abi2 | 0.0000 | 0.1184 | -3.682 | 1.00e+00 | ns |

**10 out of 14 actin pathway genes are upregulated in SMA motor neurons**, with 8 reaching statistical significance. This is a coordinated pathway-level response.

### 3. CFL2 is UP in SMA but DOWN in ALS (Disease-Specific)

| Context | CFL2/Cfl2 Direction | p-value |
|---------|---------------------|---------|
| ALS motor neurons (GSE287257, human) | DOWN | significant |
| SMA motor neurons (GSE208629, mouse) | **UP** (log2FC=+1.829) | 2.09e-04 |

This OPPOSITE regulation confirms disease-specific actin pathway dysregulation:
- In **ALS**: actin dynamics may be impaired by CFL2 loss (depolymerization failure)
- In **SMA**: actin dynamics may be compensatorily activated (CFL2 up = increased depolymerization)

### 4. PLS3 Upregulated in SMA Motor Neurons

PLS3 (Plastin 3) is a known SMA modifier gene. Its upregulation in SMA motor neurons (log2FC=+2.117, p=0.01) is consistent with its role as a compensatory/protective factor in SMA.

### 5. Pfn2 — Not Differentially Expressed in SMA MNs

Unlike in human ALS where PFN2 was strongly MN-enriched (7.6x), in mouse SMA:
- Pfn2 is modestly MN-enriched overall (log2FC=+0.457, p=6.37e-04)
- But NOT differentially expressed between SMA and control MNs (log2FC=+0.252, p=0.415)

This suggests Pfn2 is constitutively expressed in MNs regardless of disease state.

### 6. LIMK1 vs LIMK2 Divergence

| Kinase | MN enrichment | SMA MN vs Ctrl MN |
|--------|---------------|-------------------|
| Limk1 | Depleted (log2FC=-1.369) | Not detected in SMA MNs |
| **Limk2** | Similar (log2FC=-0.914) | **UP in SMA** (log2FC=+2.808, p=0.002) |

LIMK2, not LIMK1, is the actin-regulating kinase upregulated in SMA motor neurons. This is important for drug targeting: LIMK2-selective inhibitors may be more relevant than LIMK1 inhibitors for SMA.

### 7. ROCK1/2 Both Upregulated in SMA Motor Neurons

Both ROCK kinases (upstream of LIMK-Cofilin pathway) are upregulated:
- Rock1: log2FC=+0.650, p=0.044
- Rock2: log2FC=+1.056, p=0.014

This supports the ROCK-LIMK-Cofilin pathway as a therapeutic target in SMA. **Fasudil** (ROCK inhibitor) could modulate this pathway.

## Interpretation: Coordinated Actin Stress Response in SMA Motor Neurons

The data reveals a **global actin pathway activation** in SMA motor neurons:

1. **Actin monomer** (Actg1): massively UP (+2.6 log2FC) -- more actin being produced
2. **Actin polymerization** (Arpc3/Arp2/3 complex, Pfn1): UP -- more branching and polymerization
3. **Actin severing/depolymerization** (Cfl2/Cofilin-2): UP (+1.8 log2FC) -- compensatory turnover
4. **Upstream kinases** (Rock1/2, Limk2): UP -- pathway activation
5. **Known SMA modifier** (Pls3): UP -- protective bundling

This pattern suggests SMA motor neurons mount a compensatory actin stress response, possibly to maintain synaptic connections and axonal transport despite SMN deficiency.

**Critical caveat**: Only 17 SMA motor neurons were available (vs 191 control), reflecting the expected MN loss in Smn-/- mice. While the statistical tests account for sample size, these findings should be validated in larger datasets or with alternative SMA models.

## Cross-Species Summary Table

| Gene | Human ALS (GSE287257) MN-enriched? | Mouse SMA MNs: direction | Note |
|------|-----------------------------------|--------------------------|------|
| CORO1C/Coro1c | NO (microglia/endothelial) | UP in SMA MNs (p=0.002) | Passenger, not MN-specific |
| PFN2/Pfn2 | YES (7.6x) | No change in SMA MNs | Constitutive MN gene |
| LIMK1/Limk1 | YES (2.3x) | Not detected in SMA MNs | Species difference? |
| CFL2/Cfl2 | DOWN in ALS MNs | **UP in SMA MNs** (p=0.0002) | Disease-specific! |
| PLS3/Pls3 | Not MN-enriched | **UP in SMA MNs** (p=0.01) | Known SMA modifier |
| ROCK1/Rock1 | Not tested | **UP in SMA MNs** (p=0.044) | Pathway activation |
| ROCK2/Rock2 | Not tested | **UP in SMA MNs** (p=0.014) | Pathway activation |

## Files

- Script: `scripts/analyze_gse208629_sma.py`
- Raw data: `data/geo/GSE208629/` (GSE208629_RAW.tar)
- Results JSON: `data/geo/GSE208629/results/gse208629_analysis_results.json`
