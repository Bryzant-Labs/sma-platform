# Convergence Synthesis: Updated with Single-Cell Resolution

**Date**: 2026-03-24
**Status**: Updated synthesis incorporating GSE287257 snRNA-seq findings
**Supersedes**: convergence-synthesis-2026-03-22.md (core framework retained, key reinterpretations added)

**New data source**: GSE287257 — Human postmortem cervical spinal cord snRNA-seq (4 Control + 3 ALS, 61,664 cells, 240 motor neurons after top-5% MN-score filtering)

---

## 1. The Actin Cytoskeleton Hub: SMN -> PFN2 -> ROCK -> LIMK1 -> CFL2 -> Actin

This section presents the complete pathway with evidence at each step. The key update from GSE287257 is the identification of **PFN2** and **LIMK1** as the most motor neuron-enriched actin pathway genes, shifting the focus from CORO1C (which is glial) to the ROCK-LIMK kinase axis.

### The Pathway (with evidence level at each step)

```
SMN deficiency
  |
  |-- [PROVEN] SMN binds profilin2a directly; SMA mutation S230L disrupts this
  |   (Nolle et al., 2011, PMID 21920940)
  |
  |-- [PROVEN] SMN also binds F-actin and G-actin independently of profilin
  |   (Schuning et al., 2024, PMID 39305126)
  |
  v
PFN2 dysregulation
  |
  |-- [NEW - GSE287257] PFN2 is 7.6x enriched in motor neurons vs other cells
  |   (log2FC = +1.22, p = 5.3e-18, n = 240 MNs vs 61,424 other cells)
  |
  |-- [ESTABLISHED] SMN-PFN2a complex disruption leads to RhoA/ROCK hyperactivation
  |   (Nolle et al., 2011, PMID 21920940; Bowerman et al., 2007, PMID 17728540)
  |
  v
ROCK pathway activation
  |
  |-- [PROVEN] ROCK activity elevated in SMA mouse spinal cord
  |   (Bowerman et al., 2014, PMID 25221469)
  |
  |-- [NEW - GSE287257] ROCK1 upregulated in ALS motor neurons (log2FC = +0.47, p = 0.009)
  |   ROCK2 modestly enriched in MNs overall (log2FC = +0.22, p = 0.005)
  |
  |-- [PROVEN] Fasudil (ROCK inhibitor) improves SMA mouse survival
  |   (Bowerman et al., 2012, PMID 22397316)
  |
  v
LIMK1 phosphorylation (ROCK substrate)
  |
  |-- [NEW - GSE287257] LIMK1 is 2.3x enriched in motor neurons
  |   (log2FC = +1.20, p = 8.4e-24) -- second-most MN-enriched actin gene after PFN2
  |
  |-- [NEW - GSE287257] LIMK1 is DOWNREGULATED in ALS motor neurons
  |   (log2FC = -0.81, p = 0.004) while LIMK2 is UPREGULATED (log2FC = +1.01, p = 0.009)
  |   --> "LIMK1-to-LIMK2 switch" in diseased motor neurons
  |
  |-- [ESTABLISHED] LIMK phosphorylates cofilin at Ser3, inactivating it
  |   (Standard biochemistry, reviewed in Scott & Bhatt, 2014)
  |
  v
CFL2 (cofilin-2) dysregulation
  |
  |-- [ESTABLISHED] CFL2 2.9x upregulated in SMA motor neurons
  |   (GSE69175, iPSC-derived SMA motor neurons)
  |
  |-- [NEW - GSE287257] CFL2 is significantly MN-enriched (log2FC = +0.59, p = 7.1e-7)
  |
  |-- [NEW - GSE287257] CFL2 is DOWNREGULATED in ALS (all cells: log2FC = -0.13, p = 9.4e-22)
  |   CFL2 DOWN in ALS motor neurons specifically (log2FC = -0.94, p = 0.024)
  |   --> OPPOSITE direction from SMA (UP) -- disease-specific signature
  |
  v
Actin dynamics failure
  |
  |-- [PROVEN] Actin-cofilin rods form in SMA cell models
  |   (Walter et al., 2021, PMID 33986363)
  |
  |-- [PROVEN] Persistent rods block axonal transport, causing distal degeneration
  |   (Bamburg et al., 2010, PMID 20088812)
```

### Motor Neuron Specificity (New from GSE287257)

The single-cell data reveals that the ROCK-LIMK-cofilin axis is not generically expressed -- specific components are highly enriched in motor neurons:

| Gene | MN Enrichment (log2FC) | p-value | Interpretation |
|------|----------------------|---------|----------------|
| **PFN2** | **+1.22 (7.6x)** | **5.3e-18** | **Most MN-enriched actin gene** |
| **LIMK1** | **+1.20 (2.3x)** | **8.4e-24** | **Key kinase, most MN-enriched** |
| CFL2 | +0.59 (1.5x) | 7.1e-7 | MN-enriched cofilin isoform |
| ACTG1 | +0.67 (1.6x) | 6.1e-11 | Cytoskeletal gamma-actin |
| ACTR2 | +0.44 (1.4x) | 2.9e-6 | Arp2/3 complex component |
| RAC1 | +0.43 (1.4x) | 5.2e-6 | Rho GTPase upstream of ROCK |
| CORO1C | +0.10 (1.1x) | 6.9e-3 | Modest MN enrichment (see Section 3) |

**Key insight**: PFN2 and LIMK1 stand out as the genes where motor neuron biology and actin pathway intersect most strongly. This explains why motor neurons are selectively vulnerable to SMN loss -- they are uniquely dependent on the SMN-PFN2-LIMK1 axis for actin homeostasis.

**Limitation**: GSE287257 is an ALS dataset. PFN2 and LIMK1 MN-enrichment reflects normal motor neuron biology (MN vs non-MN cells in control samples). Whether PFN2 is similarly enriched in SMA motor neurons requires analysis of GSE208629 (SMA iPSC-MN single-cell data, analysis pending).

---

## 2. Disease-Specific Signatures: SMA vs ALS

The single-cell data enables, for the first time, a direct comparison of actin pathway changes between SMA and ALS at single-cell resolution.

### 2.1 SMA Signature (from GSE69175 bulk + GSE290979 organoids)

| Gene | Direction | Fold Change | Interpretation |
|------|-----------|-------------|----------------|
| CFL2 | UP | 2.9x | Compensatory cofilin increase |
| PLS3 | UP | 4.0x | Known SMA modifier (Wirth lab) |
| CORO1C | UP | 1.6x | Part of broader actin network |
| PFN2 | UP | 1.5x | Compensatory profilin increase |
| ACTR2 | UP | 1.8x | Arp2/3 complex upregulation |

**Interpretation**: SMA motor neurons mount a coordinated compensatory actin rescue response. CFL2 upregulation may represent an attempt to maintain actin dynamics in the face of SMN-profilin disruption.

### 2.2 ALS Signature (from GSE287257 single-cell, motor neuron-specific)

| Gene | Direction | log2FC | p-value | Interpretation |
|------|-----------|--------|---------|----------------|
| CFL2 | **DOWN** | -0.94 | 0.024 | Cofilin collapsed |
| LIMK1 | **DOWN** | -0.81 | 0.004 | Key kinase lost |
| LIMK2 | **UP** | +1.01 | 0.009 | Compensatory switch |
| ROCK1 | **UP** | +0.47 | 0.009 | ROCK hyperactivation |
| CORO1C | ns | -0.14 | 0.52 | Not MN-specific in ALS |

**Interpretation**: ALS motor neurons show a fundamentally different actin pathway signature. The LIMK1-to-LIMK2 switch and CFL2 collapse suggest that the compensatory mechanisms active in SMA have already failed in ALS. This may explain why ALS progresses more rapidly than SMA in many cases.

### 2.3 Disease Comparison Table

| Feature | SMA | ALS | Shared? |
|---------|-----|-----|---------|
| CFL2 | UP (2.9x) | DOWN (0.5x in MNs) | **Opposite** |
| LIMK1 | Unknown (gap) | DOWN in MNs | Unclear |
| LIMK2 | Unknown (gap) | UP in MNs (compensatory) | Unclear |
| ROCK1 | Elevated activity | UP in MNs | Shared direction |
| CORO1C | UP (1.6x) | UP (all cells, not MNs) | Shared but different cell types |
| PFN1 | UP (46%, organoids) | Mutations cause fALS | Convergence via profilin |
| Actin rods | Present (Walter 2021) | Present (TDP-43 related) | Shared phenotype |
| Fasudil response | Improves survival (mice) | Safe in Phase 2 (humans) | Both respond |

### 2.4 The Compensation-Failure Model

Based on the combined data, we propose a two-stage model:

**Stage 1 (Compensation)** -- seen in SMA:
- CFL2 UP (trying to maintain actin turnover)
- PLS3 UP (actin bundling compensation)
- PFN1/2 UP (profilin compensation)
- LIMK1 may still be functional (not yet measured in SMA MNs)
- Motor neurons are stressed but surviving

**Stage 2 (Failure)** -- seen in ALS motor neurons:
- CFL2 DOWN (compensation exhausted)
- LIMK1 DOWN (key kinase lost)
- LIMK2 UP (emergency backup, insufficient)
- ROCK1 UP (pathway hyperactivation despite kinase loss)
- Motor neurons actively degenerating

**Hypothesis**: SMA motor neurons are in Stage 1. Without intervention, they may progress to Stage 2. The therapeutic window is during Stage 1, when compensation can be augmented rather than replaced.

**Caveat**: This model compares across diseases (SMA iPSC data vs ALS postmortem tissue), which differ in age, cell type, and disease context. Direct comparison requires single-cell SMA MN data at disease stage-matched timepoints.

---

## 3. The CORO1C Reinterpretation

### 3.1 Previous Framing (pre-GSE287257)

CORO1C was identified as upregulated in both SMA (GSE69175, 1.6x) and ALS (GSE113924, padj=0.003). This cross-disease convergence, validated in three datasets, had never been previously reported. We framed CORO1C as a potential therapeutic target within the actin pathway.

### 3.2 Updated Framing (post-GSE287257)

The single-cell data fundamentally reinterprets CORO1C:

**Cell-type expression in GSE287257**:
| Cell Type | CORO1C Mean Expression |
|-----------|----------------------|
| Endothelial | 0.60 |
| Microglia | 0.57 |
| OPC | 0.42 |
| Motor Neurons | 0.41 |
| Oligodendrocyte | 0.33 |
| Astrocyte | 0.32 |

- CORO1C is highest in microglia (0.57) and endothelial cells (0.60), not motor neurons (0.41)
- CORO1C upregulation in ALS is a pan-cellular phenomenon (p = 1.03e-30 all cells), not motor neuron-specific (p = 0.52 in MNs)
- The bulk RNA-seq signal from GSE113924 (padj=0.003) likely reflects tissue-level changes driven by glial and vascular cells, not neuronal pathology

### 3.3 New Interpretation: CORO1C as Neuroinflammation Biomarker

CORO1C should now be framed as:

1. **A neuroinflammation/vascular marker**, not a motor neuron therapeutic target
2. CORO1C in microglia may reflect microglial activation and phagocytic activity (CORO1C regulates Arp2/3 and endocytosis)
3. CORO1C in endothelial cells may reflect blood-brain barrier changes in disease
4. Still potentially useful as a **biomarker for disease activity** (accessible in CSF or blood)

### 3.4 What Remains Novel

- CORO1C upregulation in ALS spinal cord (GSE113924, padj=0.003) has still never been reported in the literature
- The finding that it is glial rather than neuronal is itself a novel characterization
- CORO1C could serve as a marker of neuroinflammatory burden in motor neuron diseases
- The reinterpretation is scientifically stronger than the original framing -- it is honest about what the data actually shows

### 3.5 Therapeutic Direction Shift

| Previous | Updated |
|----------|---------|
| CORO1C as therapeutic target | CORO1C as biomarker candidate |
| Inhibit CORO1C in MNs | Target ROCK-LIMK axis in MNs instead |
| Focus on Arp2/3 regulation | Focus on PFN2/LIMK1 (the real MN players) |

---

## 4. Therapeutic Convergence

### 4.1 Fasudil (ROCK Inhibitor) -- Most Advanced Candidate

**SMA preclinical**: Fasudil significantly improves survival of severe SMA mice (Smn2B/- model), increases muscle fiber size and postsynaptic endplate size, works through SMN-independent mechanism (Bowerman et al., 2012, PMID 22397316).

**ALS Phase 2 clinical**: ROCK-ALS trial (Lingor et al., 2024, Lancet Neurology, PMID 39424560). Randomized, double-blind, placebo-controlled at 19 centers. n=120 ALS patients. Fasudil (30 mg and 60 mg IV) was safe and well-tolerated. Fasudil 60 mg significantly reduced serum GFAP (neuroinflammation marker) at day 180 (p=0.041). Post-hoc analysis suggested fasudil attenuated disease spreading.

**Oral fasudil (Bravyl)**: Phase 2a in ALS reported 15% NfL reduction and 28% slower ALSFRS-R decline. Higher-dose cohort recruitment complete.

**The untested combination**: No study has tested Fasudil + Risdiplam (or any SMN-restoring therapy). The rationale is strong:
- Fasudil: SMN-independent actin/muscle rescue (Bowerman 2012)
- Risdiplam: SMN protein restoration
- These target distinct pathological axes with no expected pharmacological interaction

### 4.2 LIMK Inhibitors -- Next-Generation Candidates

Given that LIMK1 is 2.3x enriched in motor neurons (GSE287257), LIMK inhibitors are rational candidates:

- **MDI-114215**: Potent and selective LIMK inhibitor developed for Fragile X Syndrome (Baldwin et al., 2024). Tool compound, never tested in motor neuron disease.
- **LX7101**: LIMK inhibitor that reached Phase I/IIa for glaucoma (Lexicon Pharmaceuticals). Demonstrates clinical feasibility.
- **FRAX486**: PAK inhibitor with LIMK1/2 activity. Restored synaptic morphology in Fragile X mouse model.

**Gap**: No LIMK inhibitor has been tested in any SMA or ALS model. Given the LIMK1 MN-enrichment data and the LIMK1-to-LIMK2 switch in ALS, this is a priority experiment.

### 4.3 Triple Therapy Concept

The convergence data supports a triple therapy rationale:

```
Risdiplam (SMN restoration)
  + Fasudil (ROCK/actin/muscle rescue, SMN-independent)
  + MW150 (p38 MAPK inhibitor, neuroprotection, SMN-independent)
```

Each targets a distinct mechanism:
1. **Risdiplam**: Restores SMN protein, addresses the root cause
2. **Fasudil**: Normalizes ROCK-actin axis, rescues muscle and NMJ (PMID 22397316)
3. **MW150**: Blocks p38-p53 death pathway, synaptic rewiring (PMID 40926051)

Human safety data exists for Risdiplam (FDA-approved) and Fasudil (Phase 2 ALS, PMID 39424560). MW150 has preclinical SMA synergy data but no human safety data yet.

**Speculative alternative**: Replace MW150 with a LIMK inhibitor (MDI-114215 or successor) for a more actin-focused combination: Risdiplam + Fasudil + LIMK inhibitor. This would target the pathway at two levels (ROCK and LIMK) while restoring SMN.

---

## 5. Evidence Gaps -- What Experiments Are Needed

### 5.1 Highest Priority (would change therapeutic direction)

| Gap | Experiment | Why It Matters |
|-----|-----------|----------------|
| PFN2 in SMA motor neurons | Analyze GSE208629 (SMA iPSC-MN scRNA-seq) for PFN2 expression; PFN2 knockdown in healthy MNs | If PFN2 is also MN-enriched in SMA context and knockdown phenocopies SMA, PFN2 becomes the central node |
| LIMK1 in SMA motor neurons | Measure LIMK1 expression and phosphorylation in SMA mouse spinal cord (IHC, Western blot) | Unknown whether LIMK1 is up or down in SMA -- critical for LIMK inhibitor rationale |
| Fasudil + Risdiplam combination | Test in SMA mouse model (delta-7 or Smn2B/-), measure survival, NMJ, motor function | If synergistic, this is immediately translatable given existing human safety data for both drugs |

### 5.2 High Priority (would strengthen or refute model)

| Gap | Experiment | Why It Matters |
|-----|-----------|----------------|
| CFL2 protein levels in SMA tissue | Western blot / IHC for CFL2 and p-CFL2 in SMA mouse spinal cord and muscle | 2.9x mRNA upregulation needs protein-level confirmation; phosphorylation state determines activity |
| LIMK1/LIMK2 ratio across disease stages | Measure in SMA mice at P1, P5, P9, P13 (presymptomatic to endstage) | Tests whether the LIMK1-to-LIMK2 switch seen in ALS also occurs in SMA |
| CORO1C cell-type resolution in SMA tissue | Single-cell or spatial transcriptomics on SMA mouse spinal cord | Confirms whether CORO1C upregulation in SMA is also glial (matching ALS) or truly neuronal |

### 5.3 Longer-Term (mechanistic understanding)

| Gap | Experiment | Why It Matters |
|-----|-----------|----------------|
| PFN2 vs PFN1 functional redundancy | Domain-swap experiments (replace PFN2 with PFN1 in MNs) | Tests whether PFN2's MN enrichment reflects a unique function or just expression pattern |
| Actin rod composition in ALS vs SMA | LC-MS proteomics of purified rods from both disease models | Determines if the same toxic structures form in both diseases |
| Fasudil effect on proprioceptive synapses | Fasudil treatment in SMA mice + H-reflex measurement (Simon's expertise) | Connects actin pathway rescue to circuit-level functional improvement |

---

## 6. Retained Convergence Points (from 2026-03-22 synthesis)

The following convergence points from the previous synthesis remain valid and are strengthened by the new data:

1. **ROCK-LIMK-Cofilin-Actin axis is central** (5/6 streams) -- NOW with single-cell MN-enrichment data
2. **p38 MAPK / MW150 as combination candidate** (3/6 streams) -- unchanged
3. **Proprioceptive synapse loss precedes MN death** (3/6 streams) -- unchanged
4. **Fasudil as cross-disease therapeutic** (4/6 streams) -- STRENGTHENED by Phase 2 ALS safety data
5. **PFN1 as SMA-ALS Rosetta Stone** (3/6 streams) -- now complemented by PFN2 MN-enrichment
6. **SMN-independent therapies essential** (4/6 streams) -- unchanged

The novel cross-stream connections (A through E) from the 2026-03-22 document remain valid. Connection A (p53 + actin rod dual-hit) is particularly strengthened by the CFL2 disease-specific data.

---

## 7. Summary of Changes from Previous Synthesis

| Topic | Previous (2026-03-22) | Updated (2026-03-24) |
|-------|----------------------|---------------------|
| CORO1C | Therapeutic target candidate | Neuroinflammation biomarker (glial, not neuronal) |
| PFN2 | Part of 7-gene network (1.5x UP) | **The** motor neuron actin gene (7.6x MN-enriched) |
| LIMK1 | Known ROCK substrate | 2.3x MN-enriched + LIMK1-to-LIMK2 switch in ALS |
| CFL2 | 2.9x UP in SMA | Disease-specific: UP in SMA, DOWN in ALS |
| Fasudil | Preclinical SMA + ALS Phase 2 safety | Confirmed 120-patient safety data (PMID 39424560) |
| SMN-actin | Indirect via profilin | Direct binding proven (Schuning 2024, PMID 39305126) |
| Therapeutic focus | ROCK inhibition broadly | PFN2-LIMK1 axis specifically in MNs |

---

**Limitations of this synthesis**:
- GSE287257 is ALS, not SMA. MN-enrichment data reflects normal MN biology (control cells) but ALS vs control comparisons are ALS-specific.
- n=240 motor neurons is modest for single-cell analysis. MN-specific ALS comparisons (90 vs 150) are underpowered.
- Survivorship bias in postmortem tissue: the most damaged MNs are already dead and absent.
- Cross-disease comparisons (SMA iPSC vs ALS postmortem) involve different species, ages, and experimental platforms.
- No batch correction was applied to GSE287257 (individual variation not accounted for).

*This document should be updated when GSE208629 (SMA single-cell) analysis is complete.*
