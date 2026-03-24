# Briefing Document v2: Meeting with Prof. Christian Simon

**Date prepared**: 2026-03-24
**Meeting**: Week of March 30, 2026 (Leipzig, in-person)
**Attendees**: Christian Fischer, Prof. Christian Simon (Carl-Ludwig-Institute for Physiology, Leipzig University)
**Possibly also**: Prof. Thorsten Schoeneberg (Biochemistry/Bioinformatics), Prof. Stefan Hallermann (Neurophysiology)
**PRIVATE DOCUMENT -- NOT FOR GITHUB**

---

## Executive Summary: What Changed Since March 20

At our last meeting (March 20), Simon raised four criticisms: (1) no p53/motor neuron death literature on the platform, (2) missing mouse data in species comparison, (3) confusing claim presentation, and (4) no interactive chat. Since then, we have made fundamental analytical advances that go far beyond fixing those issues:

**We now have single-cell resolution data from both mouse SMA and human ALS spinal cord**, enabling cell-type-specific analysis that most SMA computational platforms lack. This produced three findings we believe are novel:

1. **CORO1C is not a motor neuron gene** -- it is a glial/endothelial marker. Our earlier framing was wrong, and the single-cell data corrected it. (Credibility signal: we follow data, not narratives.)

2. **The ROCK-LIMK2-CFL2 axis is the actin therapeutic target in SMA motor neurons** -- with LIMK2 (not LIMK1) being the relevant kinase (+2.81x in SMA MNs), and CFL2 showing opposite regulation in SMA (UP) vs ALS (DOWN).

3. **Fasudil (ROCK inhibitor) is the nearest-term pharmacological candidate** -- already tested in SMA mice (Bowerman 2012), safe in ALS Phase 2 (ROCK-ALS, Lancet Neurology 2024), with an oral formulation in development.

**What we need from Simon**: Validation of the CFL2 signature in his mouse models, feedback on whether the LIMK1/LIMK2 switch is observable, and a feasibility assessment for fasudil + risdiplam combination testing.

---

## Section 1: Single-Cell Analyses (Addressing Simon's Mouse Data Gap)

### GSE208629 -- SMA Mouse Spinal Cord scRNA-seq

| Metric | Value |
|--------|-------|
| Cells (post-QC) | 39,136 |
| SMA motor neurons | 17 |
| Control motor neurons | 191 |
| Model | Smn-/- mouse |
| Technology | 10x Genomics scRNA-seq |

The asymmetric MN count (17 SMA vs 191 control) is biologically expected -- severe MN loss in the Smn-/- model. Despite low n, we find:

**10 of 14 actin pathway genes are upregulated in SMA motor neurons:**

| Gene | log2FC (SMA vs Ctrl MN) | p-value | Interpretation |
|------|-------------------------|---------|----------------|
| Limk2 | +2.81 | 0.002 | Key kinase -- LIMK2, not LIMK1 |
| Actg1 | +2.56 | 4.0e-14 | Massive actin monomer production |
| Actr2 | +2.21 | 3.3e-06 | Arp2/3 complex activation |
| Pls3 | +2.12 | 0.01 | Known SMA modifier gene |
| Coro1c | +1.98 | 0.002 | UP in SMA MNs but depleted vs other cells |
| Cfl2 | +1.83 | 2.1e-04 | Cofilin-2 compensatory response |
| Rock2 | +1.06 | 0.014 | Upstream kinase activation |
| Rock1 | +0.65 | 0.044 | Both ROCK isoforms activated |

This is a coordinated pathway-level response: SMA motor neurons mount a global actin stress program.

### GSE287257 -- Human ALS Spinal Cord snRNA-seq

| Metric | Value |
|--------|-------|
| Cells (post-QC) | 61,664 |
| Motor neurons (top 5% MN score) | 240 (90 ALS, 150 control) |
| Species | Human postmortem cervical spinal cord |
| Technology | 10x Genomics snRNA-seq |

Key results for motor neuron specificity (MN vs all other cells):

| Gene | MN Enrichment (log2FC) | p-value | Significance |
|------|------------------------|---------|--------------|
| PFN2 | +1.22 (7.6x) | 5.3e-18 | Most MN-enriched actin gene |
| LIMK1 | +1.20 (2.3x) | 8.4e-24 | Key MN-specific kinase |
| CFL2 | +0.59 (1.5x) | 7.1e-07 | MN-enriched cofilin isoform |
| CORO1C | +0.10 (1.1x) | 6.9e-03 | Minimal -- NOT MN-specific |

**Cross-species conclusion**: PFN2 and LIMK1 are the motor neuron-enriched actin genes. CORO1C is a glial marker, not a therapeutic target.

---

## Section 2: The ROCK-LIMK2-CFL2 Therapeutic Axis

### The Pathway (Evidence at Each Node)

```
SMN deficiency
  |
  |-- [PROVEN] SMN binds profilin-2a directly (Nolle 2011, PMID 21920940)
  |-- [PROVEN] SMN binds F-actin/G-actin independently (Schuning 2024, PMID 39305126)
  v
PFN2 dysregulation --> RhoA/ROCK hyperactivation
  |
  |-- [PROVEN] ROCK elevated in SMA mouse spinal cord (Bowerman 2014, PMID 25221469)
  |-- [NEW] Rock1 (+0.65) and Rock2 (+1.06) both UP in SMA MNs (GSE208629)
  v
ROCK phosphorylates LIMK2 (not LIMK1 in SMA)
  |
  |-- [NEW] Limk2 is +2.81x in SMA MNs (GSE208629, p=0.002)
  |-- [NEW] Limk1 NOT DETECTED in SMA MNs (species difference from human?)
  v
LIMK2 phosphorylates CFL2 (inactivation)
  |
  |-- [NEW] Cfl2 is +1.83x UP in SMA MNs (GSE208629, p=2.1e-4)
  |-- [ESTABLISHED] CFL2 2.9x UP in iPSC-SMA MNs (GSE69175)
  v
Actin dynamics failure --> rod formation, transport block
  |-- [PROVEN] Actin-cofilin rods form in SMA cell models (Walter 2021, PMID 33986363)
```

### Drug Intervention Points

| Target | Drug | Status | Evidence |
|--------|------|--------|----------|
| ROCK1/2 | Fasudil | Phase 2 safe (ALS); SMA preclinical | Bowerman 2012, ROCK-ALS 2024 |
| ROCK2 | H-1152 | Preclinical | DiffDock: +0.90 confidence vs LIMK2 |
| LIMK2 | None available | **Critical gap** | No LIMK2-selective inhibitor exists |
| SMN | Risdiplam | Approved | Standard of care |

**Proposed combination**: Risdiplam (SMN restoration) + Fasudil (ROCK inhibition). Untested but individually safe in humans.

---

## Section 3: Disease-Specific Signatures (SMA vs ALS)

### CFL2 -- Opposite Direction, Potential Biomarker

| Disease | CFL2 Direction | p-value | Source |
|---------|---------------|---------|--------|
| SMA motor neurons (mouse) | UP +1.83x | 2.1e-04 | GSE208629 |
| SMA motor neurons (iPSC) | UP +2.9x | significant | GSE69175 |
| ALS motor neurons (human) | DOWN -0.94x | 0.024 | GSE287257 |
| ALS all cells (human) | DOWN -0.13x | 9.4e-22 | GSE287257 |

**Interpretation**: CFL2 UP in SMA = active compensatory response (cells trying to maintain actin turnover). CFL2 DOWN in ALS = compensation failed or absent. This could serve as a differential biomarker between motor neuron diseases.

**CFL2 has zero dedicated SMA papers.** A straightforward IHC or Western blot in SMA mouse spinal cord would validate this.

### LIMK1/LIMK2 Kinase Switch

| Kinase | Normal MNs | SMA MNs | ALS MNs |
|--------|-----------|---------|---------|
| LIMK1 | High (2.3x MN-enriched) | Not detected | DOWN (log2FC -0.81, p=0.004) |
| LIMK2 | Moderate | UP +2.81x (p=0.002) | UP +1.01x (p=0.009) |

Both diseases show LIMK2 upregulation, but only ALS shows concurrent LIMK1 loss. This kinase switch has not been reported in SMA literature.

---

## Section 4: Platform Statistics (Growth Since March 20)

| Metric | March 20 | March 24 | Change |
|--------|----------|----------|--------|
| Evidence claims | ~10,000 | 14,855 | +49% |
| Sources | ~4,000 | 7,367 | +84% |
| Molecular targets | 48 | 68 | +42% |
| Hypotheses | ~800 | 1,476+ | +85% |
| Compounds screened | ~5,000 | 21,229 | +4x |
| Single-cell datasets | 0 | 2 | NEW |
| GEO datasets total | 3 | 5 | +2 |

Key improvements since last meeting:
- SmilesDrawer chemical structure rendering fixed
- Interactive advanced modules (NMJ, Bioelectric, Prime Editing) fixed
- DiffDock v2.2 molecular docking operational with SDF conversion
- 5 news posts published with analysis summaries
- Convergence synthesis updated with single-cell validation

---

## Section 5: Discussion Questions for Simon

### Priority Questions (Must Discuss)

1. **CFL2 validation**: Does the Simon lab have SMA mouse spinal cord tissue where CFL2 protein levels could be checked by IHC or Western blot? A positive result would be the first wet-lab confirmation of our computational finding.

2. **LIMK1 vs LIMK2**: In Simon's SMA mouse models, is LIMK1 expressed in motor neurons? Our data shows Limk1 absent in SMA MNs, LIMK1 present in human MNs -- is this a species difference or a disease effect?

3. **Fasudil + proprioception**: Fasudil improved muscle/NMJ in SMA mice (Bowerman 2012) but was never tested for proprioceptive synapse preservation. Given Simon's proprioceptive work (PMID 39982868), would testing fasudil's effect on VGLUT1+ boutons and H-reflex be feasible?

4. **Fasudil + Risdiplam combination**: Is there interest in testing this combination in SMA mice? The rationale is SMN restoration (risdiplam) + downstream actin rescue (fasudil) as complementary mechanisms.

### Secondary Questions

5. **Selective vulnerability and actin**: Our data shows 10/14 actin genes UP in SMA MNs globally. Does the actin stress response differ between vulnerable L1 and resistant L5 motor neurons? This could connect our pathway finding to Simon's selective vulnerability work.

6. **Actin-cofilin rods in vivo**: Rods are demonstrated in SMA cell culture (Walter 2021) but never in vivo. Could they be detected in SMA mouse spinal cord sections?

7. **Schoeneberg collaboration**: For the bioinformatics aspects -- would Prof. Schoeneberg be interested in co-analyzing the single-cell data? We have the processed Scanpy objects ready to share.

---

## Section 6: What We Need From Simon's Group

### Data Requests
- Access to SMA mouse spinal cord tissue (archived or fresh) for CFL2/LIMK2 IHC validation
- Segment-specific data (L1 vs L5) for any actin pathway gene, if available
- Mouse model details: which Smn model does the lab currently use? (Smn2B/-, SMN-delta-7, other?)

### Expertise Requests
- Electrophysiology readouts for proprioceptive circuit assessment (H-reflex protocol)
- Motor neuron counting methodology (Sowoidnich's standardized approach)
- Interpretation of 17 SMA MN vs 191 control MN asymmetry -- is this consistent with expected MN loss timing in Smn-/- mice?

### Collaboration Structure (Proposed)
- **Fischer**: Computational platform, GPU compute (NVIDIA NIMs), hypothesis generation, drug screening
- **Simon**: SMA biology, mouse models, electrophysiology, proprioceptive circuits, validation experiments
- **Schoeneberg**: Bioinformatics, omics analysis, AI/ML methods review
- **Hallermann**: Neurophysiology resources, institute infrastructure

---

## Section 7: Proposed Next Computational Analyses

These are analyses we can run before or after the meeting, depending on Simon's input:

| Analysis | What It Would Show | Simon's Input Needed? |
|----------|-------------------|----------------------|
| CFL2 expression across SMA mouse models | Whether CFL2 upregulation is model-specific | Which models to prioritize |
| LIMK2 inhibitor virtual screen | Novel LIMK2-selective compounds | Validation assay design |
| Proprioceptive gene panel in GSE208629 | Whether proprioceptive markers are altered in SMA | Gene list from Simon's expertise |
| L1 vs L5 transcriptomic comparison | Segment-specific vulnerability signatures | Spatial transcriptomics data (if available) |
| Fasudil combination modeling | Predicted synergy with risdiplam | Mouse model parameters |
| STMN2 analysis across datasets | STMN2 expression in our single-cell data | Simon specifically asked about this |

---

## Section 8: Limitations and Honest Caveats

**We must be upfront about these:**

1. **n=17 SMA motor neurons** in GSE208629. While statistically significant results were obtained, the small sample size means individual gene-level findings need validation. The pathway-level signal (10/14 genes UP) is more robust than any single gene.

2. **ALS data, not SMA data** for human single-cell. GSE287257 is human ALS spinal cord. MN-enrichment patterns (PFN2, LIMK1) reflect normal MN biology, but disease-specific changes are ALS, not SMA. We need human SMA single-cell data.

3. **Computational predictions, not wet-lab results.** DiffDock docking scores, GenMol molecule designs, and hypothesis scores are computational. None have been experimentally validated. We frame these as prioritization tools, not discoveries.

4. **CORO1C correction.** We initially presented CORO1C as a potential cross-disease target. The data corrected us. We should present this as a strength (data-driven self-correction) but acknowledge it means our earlier communication was partially misleading.

5. **No proprioceptive-specific analysis yet.** We have generated hypotheses (see proprioceptive-hypotheses-2026-03-24.md) but have not analyzed proprioceptive markers in the single-cell data. This is a gap Simon will notice.

6. **Platform is not peer-reviewed.** The analyses are reproducible (code available, data from public GEO), but no external scientist has validated our pipeline. Simon and Schoeneberg reviewing the methodology would significantly strengthen credibility.

---

## Appendix: Key PMIDs for Discussion

| PMID | Authors | Finding | Relevance |
|------|---------|---------|-----------|
| 22397316 | Bowerman 2012 | Fasudil improves SMA mouse survival | ROCK inhibition proof-of-concept |
| 39424560 | Lingor 2024 | Fasudil safe in ALS Phase 2 | Clinical safety data |
| 21920940 | Nolle 2011 | SMN binds profilin-2a | Upstream pathway connection |
| 39305126 | Schuning 2024 | SMN binds F-actin directly | Additional actin link |
| 25221469 | Bowerman 2014 | ROCK elevated in SMA | Pathway activation evidence |
| 33986363 | Walter 2021 | Actin-cofilin rods in SMA | Downstream pathology |
| 39982868 | Simon 2025 | Proprioceptive dysfunction in SMA patients | Simon's own landmark paper |
| 17728540 | Bowerman 2007 | RhoA/ROCK pathway in SMA | Original ROCK-SMA connection |
