# GSE287257 snRNA-seq Analysis Results (2026-03-24)

## Dataset
- **GEO**: GSE287257
- **Tissue**: Human postmortem cervical spinal cord
- **Samples**: 4 Control + 3 ALS (1 ALS sample truncated during download, GSM8742370)
- **Technology**: 10x Genomics snRNA-seq

## QC Summary
| Metric | Value |
|--------|-------|
| Total cells (post-QC) | 61,664 |
| Genes | 33,500 |
| Median genes/cell | 2,650 |
| Median counts/cell | 6,241 |
| Median MT% | 0.2% |
| Leiden clusters | 25 |

## Cell Type Distribution
| Cell Type | N Cells | % |
|-----------|---------|---|
| Oligodendrocyte | 35,379 | 57.4% |
| Astrocyte | 10,335 | 16.8% |
| Microglia | 6,044 | 9.8% |
| OPC | 4,728 | 7.7% |
| Endothelial | 2,485 | 4.0% |
| Excitatory Neuron | 986 | 1.6% |
| Motor Neuron (marker-scored) | 977 | 1.6% |
| Inhibitory Neuron | 730 | 1.2% |
| **Motor Neurons (top 5% MN score)** | **240** | **0.4%** |
| ALS Motor Neurons | 90 | - |
| Control Motor Neurons | 150 | - |

## Key Finding: CORO1C

### 1. CORO1C is upregulated in ALS (all cells, p=1.03e-30)
- ALS mean: 0.4130, Control mean: 0.3461
- log2FC = +0.248 (ALS > Control)
- **Highly significant** (Mann-Whitney U, p = 1.03e-30)
- This CONFIRMS the bulk RNA-seq finding from GSE113924

### 2. CORO1C is modestly enriched in motor neurons (p=0.007)
- MN mean: 0.4050 (49.6% expressing), Other mean: 0.3773 (35.6% expressing)
- log2FC = +0.100
- Significant but small effect size
- Highest expression in Endothelial (0.6013) and Microglia (0.5704)

### 3. CORO1C is NOT specifically upregulated in ALS motor neurons (p=0.52)
- ALS-MN mean: 0.3794, Control-MN mean: 0.4203
- log2FC = -0.144 (trend OPPOSITE to bulk finding)
- Not significant (p = 0.52)
- **Caveat**: Only 90 ALS MNs vs 150 Control MNs - underpowered. Also, damaged/dying MNs may be lost during sample prep (survivorship bias).

### Interpretation
CORO1C upregulation in ALS appears to be a **pan-cellular phenomenon** rather than motor neuron-specific. The bulk RNA-seq signal (GSE113924, padj=0.003) likely reflects tissue-level changes across multiple cell types, particularly microglia and endothelial cells. The absence of MN-specific upregulation could also reflect survivorship bias (the most affected MNs are dead/absent in postmortem tissue).

## Actin Pathway: Motor Neurons vs Other Cells

All genes enriched in motor neurons (MN vs Other, top 5% MN-score threshold):

| Gene | MN Mean | Other Mean | log2FC | p-value | Significant |
|------|---------|------------|--------|---------|-------------|
| CORO1C | 0.4050 | 0.3773 | +0.100 | 6.94e-03 | ** |
| **CFL2** | **0.3389** | **0.2221** | **+0.588** | **7.09e-07** | **\*\*\*** |
| PFN1 | 0.2035 | 0.1575 | +0.350 | 7.00e-04 | *** |
| PLS3 | 0.3480 | 0.3031 | +0.193 | 8.66e-02 | ns |
| **ACTG1** | **0.9271** | **0.5779** | **+0.673** | **6.06e-11** | **\*\*\*** |
| ACTR2 | 0.6009 | 0.4400 | +0.441 | 2.85e-06 | *** |
| ABI2 | 0.7387 | 0.5746 | +0.357 | 2.28e-05 | *** |
| **PFN2** | **0.2746** | **0.1122** | **+1.220** | **5.33e-18** | **\*\*\*** |
| **LIMK1** | **0.1659** | **0.0668** | **+1.195** | **8.44e-24** | **\*\*\*** |
| LIMK2 | 0.2667 | 0.2338 | +0.183 | 4.63e-04 | *** |
| ROCK1 | 0.7170 | 0.8174 | -0.187 | 4.68e-02 | * (DOWN) |
| ROCK2 | 0.6115 | 0.5231 | +0.221 | 5.25e-03 | ** |
| RAC1 | 0.5037 | 0.3707 | +0.432 | 5.23e-06 | *** |
| ARPC3 | 0.2990 | 0.2461 | +0.271 | 1.71e-04 | *** |

**Notable**: LIMK1 (log2FC=+1.20, p=8.4e-24) and PFN2 (log2FC=+1.22, p=5.3e-18) are the most motor neuron-enriched actin pathway genes. CFL2 is also significantly MN-enriched (log2FC=+0.59). This is consistent with the ROCK-LIMK-Cofilin pathway being particularly active in motor neurons.

## Actin Pathway: ALS vs Control (All Cells)

| Gene | ALS Mean | Control Mean | log2FC | p-value |
|------|----------|--------------|--------|---------|
| **CORO1C** | **0.4130** | **0.3461** | **+0.248** | **1.03e-30** |
| CFL2 | 0.2113 | 0.2325 | -0.132 | 9.42e-22 (DOWN) |
| ACTG1 | 0.5909 | 0.5690 | +0.054 | 2.22e-03 |
| **LIMK2** | **0.2745** | **0.1983** | **+0.450** | **<1e-300** |
| ROCK1 | 0.8324 | 0.8036 | +0.050 | 7.14e-05 |

**Key**: CORO1C and LIMK2 are the most upregulated actin pathway genes in ALS at the single-cell level. CFL2 is significantly DOWNregulated in ALS, which is the OPPOSITE of what we see in SMA -- supporting the "CFL2 as SMA-specific" hypothesis.

## ALS Motor Neurons vs Control Motor Neurons

| Gene | ALS-MN | Ctrl-MN | log2FC | p-value |
|------|--------|---------|--------|---------|
| CORO1C | 0.3794 | 0.4203 | -0.144 | 0.52 (ns) |
| CFL2 | 0.2121 | 0.4150 | -0.936 | 0.024 * |
| LIMK1 | 0.1098 | 0.1996 | -0.806 | 0.004 ** |
| LIMK2 | 0.3943 | 0.1902 | +1.014 | 0.009 ** |
| ROCK1 | 0.8682 | 0.6263 | +0.465 | 0.009 ** |

**Striking**: In ALS motor neurons specifically, CFL2 and LIMK1 are DOWNregulated while LIMK2 and ROCK1 are UPregulated. This suggests a LIMK1-to-LIMK2 switch in ALS motor neurons, with compensatory ROCK1 upregulation. Very different from SMA where CFL2 is the key signal.

## SMA/MN Markers
| Gene | Overall Mean (%) | MN Mean (%) |
|------|-----------------|-------------|
| SMN1 | 0.0257 (3.6%) | 0.0391 (9.6%) |
| SMN2 | 0.0159 (2.1%) | 0.0114 (4.2%) |
| STMN2 | 0.0857 (5.0%) | 0.8617 (35.4%) |
| NCALD | 0.2011 (15.7%) | 0.2623 (24.2%) |
| CHAT | 0.0008 (0.1%) | 0.2017 (29.2%) |
| MNX1 | 0.0014 (0.2%) | 0.3698 (47.9%) |

Motor neuron identification validated: CHAT (29.2% in MN vs 0.1% overall), MNX1 (47.9% vs 0.2%), STMN2 (35.4% vs 5.0%).

## Limitations
1. **Truncated download**: Only 7 of 12 samples loaded (1 ALS file corrupt, 4 ALS samples missing from tar)
2. **Survivorship bias**: Postmortem snRNA-seq misses dead/dying motor neurons
3. **Small MN numbers**: 90 ALS MNs, 150 Control MNs limits statistical power for MN-specific comparisons
4. **No batch correction**: Samples from different individuals without integration (Harmony/scVI)
5. **Cell type annotation**: Marker gene scoring, not reference-based annotation

## Files
- Script: `scripts/analyze_gse287257.py`
- Results JSON: `data/geo/GSE287257/results/gse287257_analysis_results.json`
- Raw data: `data/geo/GSE287257/*.h5`
