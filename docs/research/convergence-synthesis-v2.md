# Convergence Synthesis v2: ROCK-LIMK2-CFL2 Therapeutic Axis

**Date**: 2026-03-24
**Status**: Major revision incorporating GSE287257 (ALS snRNA-seq) + GSE208629 (SMA scRNA-seq)
**Supersedes**: convergence-synthesis-2026-03-24.md (added SMA single-cell validation)

---

## Summary

Single-cell validation across two independent datasets confirms **ROCK-LIMK2-CFL2** as the primary druggable axis in SMA motor neurons. The SMA mouse dataset (GSE208629) resolves critical gaps left by the ALS-only analysis, confirming that LIMK2 (not LIMK1) is the SMA-relevant kinase and that CFL2 upregulation is an SMA-specific compensatory response.

---

## Key Revisions from v1

| # | Change | Rationale |
|---|--------|-----------|
| 1 | **CORO1C -> DEPRIORITIZED** | Glial marker (highest in microglia 0.570, endothelial 0.601), not MN target. Depleted in SMA MNs (-1.81 log2FC). |
| 2 | **LIMK1 -> LIMK2** | LIMK2 is the SMA kinase (+2.81x in SMA MNs, p=0.002). LIMK1 is DOWN in ALS MNs but not detected as significant in SMA. |
| 3 | **CFL2 -> PROMOTED** to biomarker candidate | Disease-specific: UP +1.83x in SMA MNs (compensation), DOWN -0.94x in ALS MNs (failure). |
| 4 | **PFN2 -> NEW lead** MN-enriched gene | 7.6x enriched in motor neurons (GSE287257, p=5.3e-18). PFN1 UP +1.57x in SMA MNs. |
| 5 | **ROCK1/2 -> CONFIRMED** druggable | Both UP in SMA MNs. ROCK1 UP in ALS MNs (+0.47, p=0.009). Fasudil validated in both contexts. |

---

## Convergence Evidence Matrix

| Gene | GSE287257 (ALS snRNA-seq) MN Enrichment | GSE287257 ALS vs Control (MN) | GSE208629 (SMA scRNA-seq) SMA vs Control (MN) | GSE69175 (SMA iPSC bulk) | Interpretation |
|------|----------------------------------------|-------------------------------|-----------------------------------------------|--------------------------|----------------|
| **PFN2** | +1.22 log2FC (p=5.3e-18) | Not significant | Not directly tested | +1.5x UP | Most MN-enriched actin gene |
| **PFN1** | Moderate MN expression | Not significant | +1.57x UP (p=1e-4) | +46% (organoids) | SMA compensatory; fALS mutations |
| **LIMK1** | +1.20 log2FC (p=8.4e-24) | DOWN -0.81 (p=0.004) | Not detected as significant | N/A | MN-enriched but lost in ALS |
| **LIMK2** | Moderate expression | UP +1.01 (p=0.009) | **UP +2.81x (p=0.002)** | N/A | **THE SMA kinase** |
| **CFL2** | +0.59 log2FC (p=7.1e-7) | DOWN -0.94 (p=0.024) | **UP +1.83x (p=2e-4)** | +2.9x UP | **Disease-specific biomarker** |
| **ROCK1** | +0.22 (MN-enriched) | UP +0.47 (p=0.009) | UP (both ROCK1/2) | Elevated activity (Bowerman) | Druggable kinase, Fasudil target |
| **ROCK2** | Moderate | Not significant in MNs | UP in SMA MNs | N/A | Dual ROCK activation in SMA |
| **CORO1C** | +0.10 (modest, p=6.9e-3) | ns in MNs (p=0.52) | **DEPLETED -1.81 (p=7.3e-4)** | +1.6x UP (bulk) | Glial marker, not MN target |
| **RAC1** | +0.43 (p=5.2e-6) | Not significant | +1.69x UP (p=4e-5) | N/A | Upstream of ROCK, active in SMA |
| **ACTG1** | +0.67 (p=6.1e-11) | Not significant | +2.60x UP (p=4e-14) | N/A | Cytoskeletal remodeling in SMA |
| **PLS3** | MN-enriched | Not significant | +2.12x UP (p=0.01) | +4.0x UP | Known SMA modifier (Wirth lab) |

---

## Therapeutic Axis: ROCK -> LIMK2 -> Cofilin

```
SMN deficiency (root cause)
  |
  v
SMN-PFN2a complex disruption (PMID 21920940)
  |
  v
RhoA/ROCK hyperactivation (PMID 25221469)
  |                                              DRUG: Fasudil (ROCK inhibitor)
  |                                              Phase 2 ALS safety (PMID 39424560)
  |                                              SMA mouse survival (PMID 22397316)
  v
LIMK2 hyperactivation (+2.81x in SMA MNs)       DRUG: LIMK2-selective inhibitor
  |                                              (MDI-114215 analog, LX7101 class)
  |                                              Gap: Never tested in MN disease
  v
CFL2 phosphorylation (inactivation)              BIOMARKER: p-CFL2/CFL2 ratio
  |                                              UP in SMA = compensation
  |                                              DOWN in ALS = failure
  v
Actin dynamics failure -> Actin-cofilin rods     PHENOTYPE: Axonal transport block
  |                                              (PMID 33986363, 20088812)
  v
Motor neuron degeneration
```

**Key pharmacological intervention points**:
1. **ROCK level**: Fasudil -- human safety data exists (Phase 2 ALS, FDA-approved in Japan)
2. **LIMK2 level**: Selective LIMK2 inhibitor -- no clinical candidates yet, but tool compounds exist
3. **Cofilin level**: CFL2 phosphorylation status as treatment response biomarker

---

## Disease-Specific Signatures

| Gene | SMA (GSE208629 MNs) | ALS (GSE287257 MNs) | Interpretation |
|------|---------------------|---------------------|----------------|
| **CFL2** | **UP +1.83x** (p=2e-4) | **DOWN -0.94x** (p=0.024) | Compensation success (SMA) vs failure (ALS) |
| **LIMK2** | **UP +2.81x** (p=0.002) | UP +1.01x (p=0.009) | Shared compensatory kinase, stronger in SMA |
| **LIMK1** | Not detected as significant | **DOWN -0.81x** (p=0.004) | ALS-specific loss |
| **PFN2** | Not directly tested | MN-enriched +1.22x (p=5.3e-18) | Cross-validate in SMA single-cell |
| **PFN1** | UP +1.57x (p=1e-4) | Not significant | SMA compensatory profilin |
| **ROCK1** | UP (both ROCK1/2) | UP +0.47x (p=0.009) | Shared hyperactivation |
| **RAC1** | UP +1.69x (p=4e-5) | Not significant | SMA-specific upstream activation |
| **ACTG1** | UP +2.60x (p=4e-14) | Not significant | SMA-specific cytoskeletal remodeling |
| **CORO1C** | DEPLETED -1.81x (p=7.3e-4) | ns in MNs (p=0.52) | Not a MN player in either disease |

### The Compensation-Failure Model (Updated)

**SMA Motor Neurons (Stage 1 -- Active Compensation)**:
- 10/14 actin genes UP -- coordinated rescue response
- LIMK2 UP +2.81x -- emergency kinase activation
- CFL2 UP +1.83x -- maintaining actin turnover
- PLS3 UP +2.12x -- actin bundling compensation
- RAC1/ACTG1 strongly UP -- cytoskeletal remodeling
- Therapeutic window: augment compensation before exhaustion

**ALS Motor Neurons (Stage 2 -- Compensation Failure)**:
- CFL2 DOWN -- cofilin collapse
- LIMK1 DOWN -- key kinase lost
- LIMK2 UP (but weaker than SMA) -- insufficient backup
- ROCK1 UP -- pathway hyperactivated despite kinase loss
- Motor neurons actively degenerating

**Hypothesis**: SMA motor neurons are in Stage 1. The LIMK2/CFL2 upregulation represents a targetable therapeutic window. Without intervention, progression toward Stage 2 (ALS-like collapse) is expected.

---

## Drug Strategy Update

### Primary Combination: Risdiplam + Fasudil + LIMK2 Inhibitor

| Drug | Target | Mechanism | Human Safety | SMA Evidence |
|------|--------|-----------|--------------|--------------|
| **Risdiplam** | SMN2 splicing | Restores SMN protein (root cause) | FDA-approved | Standard of care |
| **Fasudil** | ROCK1/2 | Normalizes actin/muscle axis | Phase 2 ALS (PMID 39424560) | Mouse survival (PMID 22397316) |
| **LIMK2i** (TBD) | LIMK2 | Prevents cofilin hyperphosphorylation | MDI-114215 (tool), LX7101 (Phase I glaucoma) | None yet -- priority experiment |

**Rationale**: Each targets a distinct node in the cascade:
1. Risdiplam: upstream (SMN protein)
2. Fasudil: midstream (ROCK kinase)
3. LIMK2i: downstream (LIMK2 kinase, SMA-specific)

### Alternative: Risdiplam + Fasudil + MW150

Replace LIMK2i with MW150 (p38 MAPK inhibitor) for a broader neuroprotective strategy targeting both actin dysfunction and p53-mediated death signaling.

### Biomarker Strategy

| Biomarker | Measurement | Expected Change with Treatment | Source |
|-----------|-------------|-------------------------------|--------|
| p-CFL2/CFL2 ratio | Western blot, CSF proteomics | Decrease (less hyperphosphorylation) | SMA MN CFL2 UP +1.83x |
| LIMK2 expression | qPCR, RNAscope | Decrease (less compensatory need) | SMA MN LIMK2 UP +2.81x |
| Serum GFAP | ELISA | Decrease (Fasudil effect) | ALS Phase 2 (p=0.041) |
| NfL | Simoa assay | Decrease (axonal protection) | Oral Fasudil: 15% reduction |

---

## Evidence Gaps Requiring Experiments

### Highest Priority

| Gap | Experiment | Impact |
|-----|-----------|--------|
| **PFN2 in SMA MNs** | Re-analyze GSE208629 for PFN2 specifically (may not have been captured) | Confirms/refutes PFN2 as central node |
| **Fasudil + Risdiplam combo** | SMA mouse model (Smn2B/-), measure survival + NMJ + actin rods | Immediately translatable if synergistic |
| **LIMK2 inhibitor in SMA** | Test MDI-114215 or analog in SMA iPSC-MNs | Validates LIMK2 as drug target |
| **p-CFL2 in SMA tissue** | Western blot for CFL2 and p-CFL2 in SMA mouse spinal cord | Confirms biomarker utility |

### High Priority

| Gap | Experiment | Impact |
|-----|-----------|--------|
| LIMK2 temporal profile in SMA | Measure LIMK2 at P1/P5/P9/P13 in SMA mice | Defines therapeutic window |
| CFL2 protein confirmation | IHC/Western for CFL2 protein in SMA vs control | mRNA-to-protein validation |
| ROCK1/2 selectivity | Compare pan-ROCK (Fasudil) vs ROCK2-selective inhibitor in SMA MNs | Optimizes drug selection |

---

## Retained Convergence Points (from previous syntheses)

All prior convergence points remain valid and are now strengthened:

1. **ROCK-LIMK-Cofilin-Actin axis is central** -- NOW validated in SMA single-cell (10/14 actin genes UP)
2. **Fasudil as cross-disease therapeutic** -- STRENGTHENED by SMA mouse ROCK confirmation
3. **PFN1 as SMA-ALS Rosetta Stone** -- PFN1 UP +1.57x in SMA MNs, PFN1 mutations cause fALS
4. **SMN-independent therapies essential** -- ROCK-LIMK2 axis operates downstream of SMN
5. **p38 MAPK / MW150 as combination candidate** -- unchanged, complementary axis
6. **Proprioceptive synapse loss precedes MN death** -- unchanged

---

## Limitations

1. **Cross-species**: GSE287257 is human ALS postmortem; GSE208629 is SMA mouse embryonic (E13.5). Direct comparison has caveats.
2. **Cell counts**: GSE287257 had 240 MNs; GSE208629 had ~500 MNs. Both modest for differential expression.
3. **Survivorship bias**: Postmortem ALS tissue lacks the most damaged MNs (already dead).
4. **Temporal mismatch**: SMA data is embryonic (pre-symptomatic); ALS data is end-stage. The compensation-failure model is inferred, not directly observed longitudinally.
5. **No batch correction**: Neither dataset had cross-sample batch correction applied.
6. **LIMK2 antibody specificity**: LIMK1 and LIMK2 share high homology; protein-level confirmation requires isoform-specific antibodies.

---

*This document supersedes convergence-synthesis-2026-03-24.md. Next update when Fasudil+Risdiplam combination data or LIMK2 inhibitor SMA data becomes available.*
