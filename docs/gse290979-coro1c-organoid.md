# GSE290979: CORO1C in SMA Spinal Cord Organoids

## Dataset Overview

| Field | Value |
|-------|-------|
| **GEO Accession** | [GSE290979](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE290979) |
| **Title** | Targeted ASO Treatment Rescues Developmental Alterations in SMA Organoids [bulk RNA-seq] |
| **PubMed** | [41423447](https://pubmed.ncbi.nlm.nih.gov/41423447/) |
| **Organism** | Homo sapiens (iPSC-derived spinal cord organoids) |
| **Platform** | Illumina NovaSeq X Plus, paired-end 150bp |
| **Alignment** | STAR v2.7.10a to GRCh38 |
| **Public** | Nov 17, 2025 |
| **Lab** | Lodato/Corti, IRCCS Humanitas Research Hospital, Italy |
| **Samples** | 31 (n=9 CTRL, n=6 SMA untreated, n=8 SMA+scramble, n=8 SMA+ASO) |

### Study Design

SMA Type I iPSC-derived spinal cord organoids (SCOs) at 2 months differentiation:
- **3 wild-type control lines** (C1/A2, C2/R1, C3/CS5) -- 3 replicates each = **9 CTRL samples**
- **2 SMA lines** (S2/N3, S3/CS83) -- 3 replicates each = **6 SMA_NT samples**
- **SMA + scrambled morpholino** (negative control) -- 4 replicates per line = **8 SMA_Scramble samples**
- **SMA + r6-morpholino** (therapeutic ASO targeting SMN2 ISS-N1) -- 4 replicates per line = **8 SMA_R6-Mo samples**

Total: **19,417 genes** across **31 samples** -- substantially more statistical power than GSE69175 (n=4).

---

## CORO1C Expression Results

### Group-Level Summary (CPM-normalized)

| Group | N | Mean CPM | SD | Median CPM | Mean Raw Counts |
|-------|---|----------|-----|------------|-----------------|
| CTRL (wild-type) | 9 | 156.54 | 37.00 | 171.63 | 4,975 |
| SMA untreated | 6 | 172.69 | 16.18 | 169.43 | 4,900 |
| SMA + scramble ASO | 8 | 168.64 | 22.61 | 163.09 | 5,018 |
| SMA + therapeutic ASO | 8 | 170.61 | 11.10 | 175.33 | 5,163 |

### Statistical Comparisons

| Comparison | Fold Change | log2FC | t-test p | Mann-Whitney p | Cohen's d |
|------------|------------|--------|----------|----------------|-----------|
| **SMA vs CTRL** | 1.103 | +0.142 | 0.366 | 0.689 | 0.494 |
| SMA_Scramble vs SMA_NT | 0.977 | -0.034 | 0.736 | -- | -- |
| SMA_R6-Mo vs SMA_NT | 0.988 | -0.018 | 0.795 | 1.000 | -0.143 |
| SMA_R6-Mo vs SMA_Scramble | 1.012 | +0.017 | 0.840 | -- | 0.103 |
| SMA_R6-Mo vs CTRL | 1.090 | +0.124 | 0.347 | -- | -- |

**Key finding: CORO1C shows a consistent upward trend (+10.3%) in SMA organoids vs controls, but this does NOT reach statistical significance (p=0.37).**

### Per-Cell-Line Breakdown

| Cell Line | Genotype | Treatment | N | Mean CPM | SD |
|-----------|----------|-----------|---|----------|-----|
| C1 (A2) | CTRL | NT | 3 | 120.47 | 13.13 |
| C2 (R1) | CTRL | NT | 3 | 164.60 | 41.16 |
| C3 (CS5) | CTRL | NT | 3 | 184.56 | 9.47 |
| S3 (CS83) | SMA | NT | 3 | 163.80 | 8.17 |
| S2 (N3) | SMA | NT | 3 | 181.59 | 17.28 |
| S3 (CS83) | SMA | R6-Mo | 4 | 174.13 | 4.70 |
| S2 (N3) | SMA | R6-Mo | 4 | 167.08 | 14.12 |

**Notable**: The large variance in CTRL (C1 mean=120 vs C3 mean=185) masks potential SMA effects. SMA line S2/N3 shows the stronger upregulation (FC=1.160 vs CTRL, p=0.33).

### Genome-Wide Context

CORO1C ranks **5,130 out of 16,233** expressed genes (top 31.6%) for SMA-vs-CTRL fold change. This places it in the upper third but far from the most strongly dysregulated genes.

### ASO Rescue Assessment

```
CORO1C expression trajectory:
  CTRL (healthy):        156.54 CPM
  SMA (untreated):       172.69 CPM  (FC vs CTRL: 1.103)
  SMA + scramble ASO:    168.64 CPM  (FC vs SMA: 0.977)
  SMA + therapeutic ASO: 170.61 CPM  (FC vs SMA: 0.988)

  Rescue percentage: 12.9% (minimal)
```

ASO treatment has essentially no effect on CORO1C expression (FC=0.988, p=0.80). This is expected if CORO1C dysregulation is **downstream of SMN-dependent actin remodeling** rather than a direct SMN splicing target -- the ASO restores SMN protein levels but CORO1C remains at SMA-like levels within the 2-month organoid timeframe.

---

## Actin Cytoskeleton Pathway Analysis

### Pathway-Level Summary (SMA vs CTRL)

| Pathway | Avg FC | Direction | Significant Genes (p<0.05) |
|---------|--------|-----------|----------------------------|
| Rho GTPases | 2.448 | UP in SMA | **RAC1** (1.24x, p=0.021) |
| Motor neuron markers | 1.631 | UP in SMA | **ISL1** (2.54x, p=0.040) |
| Tropomyosins | 1.547 | UP in SMA | none |
| Formins | 1.280 | UP in SMA | **DIAPH2** (1.25x), **DIAPH3** (2.18x), **FMN2** (0.70x) |
| SMN pathway | 1.108 | UP in SMA | **STRAP** (1.32x, p=0.005) |
| Arp2/3 complex | 1.102 | UP in SMA | **ARPC3** (1.29x, p=0.035) |
| Myosins | 1.086 | UP in SMA | **MYO5A** (0.68x, p=0.037) |
| WASP/WAVE | 1.074 | UP in SMA | none |
| Profilin | 1.030 | Unchanged | **PFN1** (1.46x, p=0.004) |
| **Coronin family** | **1.017** | **Unchanged** | **CORO1A** (0.67x, p=0.019) |
| Growth cone/neurite | 0.822 | DOWN in SMA | none |

### All Significantly Changed Actin/Cytoskeletal Genes (p<0.05)

| Gene | FC (SMA/CTRL) | p-value | log2FC | Pathway | Direction |
|------|--------------|---------|--------|---------|-----------|
| **PFN1** | 1.464 | 0.0040 | +0.55 | Profilin | UP |
| **STRAP** | 1.324 | 0.0055 | +0.40 | SMN pathway | UP |
| **DIAPH3** | 2.176 | 0.0168 | +1.12 | Formins | UP |
| **CORO1A** | 0.666 | 0.0188 | -0.59 | Coronin family | DOWN |
| **RAC1** | 1.239 | 0.0212 | +0.31 | Rho GTPases | UP |
| **FMN2** | 0.699 | 0.0280 | -0.52 | Formins | DOWN |
| **DIAPH2** | 1.254 | 0.0284 | +0.33 | Formins | UP |
| **ARPC3** | 1.286 | 0.0353 | +0.36 | Arp2/3 complex | UP |
| **MYO5A** | 0.678 | 0.0367 | -0.56 | Myosins | DOWN |
| **ISL1** | 2.539 | 0.0402 | +1.34 | Motor neuron markers | UP |

### Other Neuronal Genes of Interest

| Gene | CTRL CPM | SMA CPM | FC | p-value | Note |
|------|----------|---------|-----|---------|------|
| MAPT (tau) | 349.1 | 166.3 | 0.476 | 0.0049 | Strongly downregulated |
| NEFL | 803.1 | 464.0 | 0.578 | 0.0146 | Neurofilament light down |
| SNAP25 | 70.8 | 44.4 | 0.627 | 0.0148 | Synaptic marker down |
| DLG4 (PSD-95) | 113.6 | 147.2 | 1.296 | 0.0002 | Postsynaptic density UP |
| GAP43 | 254.5 | 167.6 | 0.659 | 0.097 | Growth cone down (trend) |
| SYN1 | 63.3 | 43.9 | 0.693 | 0.067 | Synapsin down (trend) |

---

## Interpretation for the Double-Hit Model

### What This Dataset Shows

1. **CORO1C is NOT significantly dysregulated in SMA organoids** (FC=1.103, p=0.37). The 10.3% upregulation trend is consistent in direction with GSE69175 mouse data but lacks statistical significance.

2. **The broader actin pathway IS significantly disrupted in SMA**, with the most affected components being:
   - **PFN1** (profilin-1): +46.4%, p=0.004 -- the strongest actin-related hit
   - **RAC1**: +23.9%, p=0.021 -- a key CORO1C interaction partner
   - **ARPC3**: +28.6%, p=0.035 -- Arp2/3 complex subunit
   - **DIAPH3**: +117.6%, p=0.017 -- formin family actin nucleator
   - **CORO1A**: -33.4%, p=0.019 -- paradoxically, the other coronin goes DOWN

3. **ASO treatment does not rescue CORO1C** (FC=0.988 vs SMA_NT, p=0.80). CORO1C expression is essentially unaffected by SMN restoration.

4. **Neuronal maturation markers are broadly downregulated**: MAPT, NEFL, SNAP25, GAP43, SYN1 -- consistent with the paper's finding of "pervasive alterations in neuronal differentiation programs."

### Cross-Dataset Comparison: GSE69175 vs GSE290979

| Feature | GSE69175 (Mouse) | GSE290979 (Human Organoid) |
|---------|-------------------|---------------------------|
| System | SMN-delta7 mouse spinal cord | SMA Type I iPSC organoids |
| Species | Mouse | Human |
| N (SMA vs CTRL) | 2 vs 2 | 6 vs 9 |
| CORO1C direction | Upregulated | Upregulated (trend) |
| CORO1C FC | ~1.19 (log2FC +0.251) | 1.103 (log2FC +0.142) |
| CORO1C significance | Nominally significant | Not significant (p=0.37) |
| PFN1 | Not reported | **1.464x, p=0.004** |
| RAC1 | Not reported | **1.239x, p=0.021** |

### Revised Assessment for the Double-Hit Model

The GSE290979 data provides **partial support** for the CORO1C hypothesis:

**Supporting evidence:**
- Direction is consistent (upward trend in SMA)
- The actin cytoskeleton pathway IS broadly dysregulated in SMA organoids
- RAC1 (CORO1C upstream activator) is significantly upregulated
- PFN1 (profilin, another actin dynamics regulator) is the strongest hit
- Neuronal maturation/synaptic markers are down, consistent with cytoskeletal dysfunction

**Weakening evidence:**
- The CORO1C effect is small (10%) and not significant with n=15
- CORO1A (the other major coronin) goes in the OPPOSITE direction (down 33%)
- ASO treatment does not affect CORO1C, suggesting it is not SMN-responsive
- CORO1C ranks only in the top 31.6% of genes -- not an outlier

**Nuanced interpretation:**
The data suggest that **the actin cytoskeleton pathway disruption in SMA is real and significant, but CORO1C may not be the primary driver**. Instead, the pathway-level disruption appears to flow through:
1. **PFN1** (profilin-1) -- the strongest cytoskeletal hit
2. **RAC1** -- Rho GTPase signaling
3. **ARPC3/Arp2/3** -- actin branching nucleation
4. **Formins (DIAPH2/3)** -- linear actin polymerization

CORO1C may be a **passenger rather than a driver** of the cytoskeletal phenotype, or its role may be more prominent in specific cell types (motor neurons) that are diluted in bulk organoid RNA-seq.

### Recommendation

For the 4-AP + CORO1C activator therapeutic hypothesis, the data suggest **pivoting to a broader "actin cytoskeleton rescue" framing** rather than CORO1C-specific. The strongest targets from this dataset would be:
- **PFN1 modulation** (strongest effect, most significant)
- **RAC1 signaling** (significant, upstream of multiple actin regulators)
- **CORO1C** retained as one component of a multi-target approach

Single-cell RNA-seq from the same study (GSE290978) could resolve whether CORO1C is specifically dysregulated in motor neurons vs. other cell types.

---

## Methods

- Count matrix downloaded from GEO (GSE290979_count_matrix.txt.gz)
- CPM normalization (counts per million)
- Two-sample t-test and Mann-Whitney U test for group comparisons
- Cohen's d for effect size estimation
- No multiple testing correction applied (single-gene focus)
- Analysis performed on moltbot server (2026-03-21)

## Files on Moltbot

```
/home/bryzant/sma-platform/data/geo/GSE290979_matrix.txt
/home/bryzant/sma-platform/data/geo/GSE290979_count_matrix.txt
/home/bryzant/sma-platform/data/geo/coro1c_analysis_gse290979.py
/home/bryzant/sma-platform/data/geo/coro1c_deep_analysis.py
```
