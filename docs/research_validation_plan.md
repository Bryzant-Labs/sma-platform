# Experimental Validation Research Plan

## Validating the SMA Research Platform's Top Computational Discoveries

**Version:** 2.0 | **Date:** March 21, 2026
**Author:** Christian Fischer, SMA Research Platform (https://sma-research.info)
**Purpose:** Concrete plan for wet-lab and computational validation of our top findings. Designed for discussion with a collaborating SMA mouse model laboratory, a collaborating SMA genetics laboratory, Prof. Adrian an RNA splicing laboratory (e.g. CSHL), and other potential collaborators.
**Status:** All findings are computational predictions only. No experimental data exists yet.

---

## Executive Summary

The SMA Research Platform's virtual screening campaigns have produced multiple experimentally testable predictions. The initial campaign (378 compound-target dockings via DiffDock v2.2) was expanded to a full 4,116-compound screen across 7 SMA protein targets on March 21, 2026. This expanded campaign confirmed earlier findings and revealed new discoveries, most notably riluzole (an FDA-approved ALS drug) binding to SMN2 protein via a mechanism distinct from its known glutamate inhibition. This document specifies, for each prediction, the minimum viable experiment required to validate or refute it, followed by a phased plan for functional and in vivo studies. Total estimated cost for Phase 1 (biophysical binding confirmation): EUR 18,000-30,000. Total estimated timeline: 12-18 months to complete all validation phases.

The discoveries, ranked by priority:

| # | Discovery | Key Metric | Validation Status |
|---|-----------|-----------|-------------------|
| 1 | 4-AP binds CORO1C protein | DiffDock confidence +0.251 (rank 1 of 378 initial; confirmed in 4,116 screen) | No experimental data |
| 2 | Riluzole binds SMN2 protein | DiffDock confidence +0.201 (4,116-compound screen) | No experimental data |
| 3 | NEDD4L-TP53 protein similarity | ESM-2 cosine similarity 0.973 | No experimental data |
| 4 | SMN1 residues 289-294 interaction hotspot | Contact map overlap for p53 + CORO1C | No experimental data |
| 5 | UBA1 multi-compound druggability | 4-5 positive hits from 1,000+ dockings (most of any target) | No experimental data |
| 6 | CORO1C structural uniqueness | ESM-2 embedding norm 5.259 (lowest of 7 targets) | Computational only |
| 7 | Riluzole multi-target profile | Binds SMN2 (+0.201) AND UBA1 (+0.182) | No experimental data |

---

## Computational Milestones Completed

What the platform has already achieved — providing the foundation for experimental validation.

| # | Milestone | Status | Key Result |
|---|-----------|--------|------------|
| 1 | Evidence ingestion (PubMed + patents + trials + bioRxiv) | DONE | 6,176 sources, 30,668 claims, 578 patents, 449 trials |
| 2 | LLM claim extraction (Claude Sonnet) | DONE | 30,668 structured claims with confidence scoring |
| 3 | Hypothesis generation and prioritization | DONE | 1,263 hypotheses ranked in A/B/C tiers |
| 4 | 5-dimensional convergence scoring | DONE | Volume, lab independence, method diversity, temporal, replication |
| 5 | Bayesian calibration against known outcomes | DONE | **Grade A (89.8%)** — approved drugs score higher than failed |
| 6 | DiffDock v2.2 virtual screening (378 dockings) | DONE | 4-AP→CORO1C (+0.251) discovery |
| 7 | Expanded screening (4,116 dockings) | DONE | 630 compounds x 7 targets, riluzole→SMN2 (+0.201) |
| 8 | GenMol de novo molecule generation | DONE | 1,051 molecules generated, 56 positive hits |
| 9 | ESM-2 protein embeddings (15 proteins) | DONE | 105 similarity pairs, CORO1C structural outlier |
| 10 | ESM-2 contact map predictions | DONE | 5 protein-protein interaction maps |
| 11 | SMN1 pathogenic variant scoring | DONE | 9/9 known mutations correctly classified as deleterious |
| 12 | Cross-paper synthesis | DONE | 30 co-occurrence pairs, 53 transitive bridges |
| 13 | Cross-species comparative biology | DONE | 7 model organisms |
| 14 | AlphaFold DB protein complexes | DONE | 8/8 SMA complexes found |
| 15 | ML docking proxy model | DONE | Random Forest — enables 1M+ molecule screening |
| 16 | Uncertainty quantification (Wilson CI) | DONE | Confidence intervals for all 21 targets |
| 17 | Daily automated pipeline | ACTIVE | Cron 3 AM UTC |
| 18 | Open-source publication | DONE | GitHub (AGPL-3.0), HuggingFace, Docker |

### Experimental Gaps (What Has NOT Been Done)

| Gap | Why It Matters | Required |
|-----|---------------|----------|
| No biophysical binding confirmation | DiffDock predictions are computational only | SPR or MST assay |
| No cellular functional validation | Binding does not equal biological effect | iPSC-MN assays |
| No in vivo testing | Cell culture does not equal animal model | SMA mouse model |
| No orthogonal docking consensus | Single method may produce artifacts | AutoDock Vina + GNINA |
| No clinical PK for CORO1C pathway | 4-AP reaches CNS but motor neuron exposure unquantified | PK modeling |

---

## Part 1: Priority Experiments (Minimum Viable Validation)

### Discovery 1: 4-AP Binds CORO1C (+0.251 DiffDock Confidence)

**Why this matters:** 4-aminopyridine is FDA-approved (Dalfampridine/Fampyra for MS). All prior SMA investigation assumed K+ channel blockade as the sole mechanism. If 4-AP binds CORO1C, this represents a mechanistically distinct rationale for a repurposing candidate that could complement existing SMN-restoring therapies via the actin cytoskeletal pathway (PLS3 rescue network).

#### Experiment 1A: Biophysical Binding Confirmation (GO/NO-GO GATE)

- **Assay:** Surface Plasmon Resonance (SPR) using a Biacore T200 or equivalent
- **Protocol:**
  1. Express and purify recombinant human CORO1C (UniProt Q9ULV4, 474 aa) in E. coli BL21(DE3) or insect cells (baculovirus). His-tag purification via Ni-NTA, followed by SEC (size exclusion chromatography) to confirm monodisperse folded protein.
  2. Immobilize CORO1C on a CM5 sensor chip via amine coupling (target density: 2000-5000 RU).
  3. Flow 4-aminopyridine (Sigma-Aldrich, >99% purity, MW 94.11) at 8 concentrations in 2-fold serial dilution: 0.1, 0.5, 1, 5, 10, 50, 100, 500 micromolar. Running buffer: 10 mM HEPES pH 7.4, 150 mM NaCl, 3 mM EDTA, 0.005% Tween-20, 2% DMSO.
  4. Include negative controls: blank flow cell (no protein), BSA-immobilized flow cell, and buffer-only injections.
  5. Include positive control: if available, a known CORO1C ligand or actin monomer to confirm the protein is properly folded and functional on the chip.
  6. Fit binding curves to 1:1 Langmuir or steady-state affinity models.
- **Model system:** Purified recombinant protein (no cellular context needed for this step)
- **Expected result:**
  - **Positive (validates prediction):** Measurable, dose-dependent binding with Kd < 10 micromolar. Sensorgram shows clear association/dissociation kinetics.
  - **Weakly positive:** Kd between 10-100 micromolar. Binding detectable but low affinity. Proceed with caution; may be pharmacologically irrelevant at physiological 4-AP concentrations.
  - **Negative (refutes prediction):** No detectable binding above baseline at any concentration, or Kd > 100 micromolar. This would definitively refute the DiffDock prediction and terminate this line of investigation.
- **Go/no-go threshold:** Kd < 50 micromolar to proceed to functional studies. Below 10 micromolar = high priority.
- **Alternative assays (if SPR unavailable):**
  - Microscale Thermophoresis (MST): Requires less protein (~50 micrograms), measures binding in solution. Label CORO1C with RED-NHS dye. Same concentration series.
  - Differential Scanning Fluorimetry (DSF/Thermal Shift): Measure 4-AP-induced shift in CORO1C melting temperature. A shift of > 1 degree C at 100 micromolar 4-AP = positive. Low cost, high throughput.
  - Isothermal Titration Calorimetry (ITC): Gold standard for thermodynamic binding parameters (Kd, deltaH, deltaS). Requires more protein (~500 micrograms for full titration) but yields complete thermodynamic profile.
- **Estimated cost:** EUR 3,000-5,000 (protein expression + purification + SPR instrument time)
- **Timeline:** 4-6 weeks (2 weeks protein prep, 2-4 weeks SPR runs + optimization)
- **Collaborator:** a biochemistry core facility with SPR capability (e.g. Leipzig University) or any core facility with SPR capability. Leipzig Biochemistry Institute has Biacore instrumentation. Alternatively, commercial CRO (e.g., Proteros, NovAliX) can run SPR for approximately EUR 5,000-8,000 per target.

#### Experiment 1B: Binding Site Mapping (If 1A positive)

- **Assay:** Hydrogen-Deuterium Exchange Mass Spectrometry (HDX-MS)
- **Protocol:**
  1. Incubate CORO1C (5 micromolar) with and without 4-AP (100 micromolar, 10x Kd if Kd = 10 micromolar) in D2O buffer for 10 s, 1 min, 10 min, 60 min.
  2. Quench with ice-cold low-pH buffer, pepsin digest, LC-MS analysis.
  3. Compare deuterium uptake between apo-CORO1C and 4-AP-bound CORO1C.
  4. Peptides showing > 10% reduction in deuterium uptake indicate 4-AP binding site.
- **Expected result:** Protection from exchange in WD-repeat beta-propeller domain (CORO1C functional region, residues ~40-400). If protection maps to the unique C-terminal tail (residues ~420-474), this would indicate a non-canonical binding site.
- **Estimated cost:** EUR 5,000-8,000 (HDX-MS core facility)
- **Timeline:** 2-4 weeks
- **Collaborator:** Proteros Biostructures (Munich) or Leipzig/Halle HDX-MS core

#### Experiment 1C: Functional Validation in Motor Neurons (If 1A positive, Kd < 10 micromolar)

- **Assay:** Actin dynamics imaging in iPSC-derived motor neurons (iPSC-MNs)
- **Protocol:**
  1. Differentiate iPSC-MNs from SMA patient iPSCs (homozygous SMN1 deletion, 2 copies SMN2) and isogenic corrected controls. Use established directed differentiation protocol (Maury et al., Nat Biotechnol 2015).
  2. Treat with 4-AP at 1x, 5x, and 10x Kd concentrations for 24 h and 72 h.
  3. Fix and stain with Alexa Fluor 488-phalloidin for F-actin visualization. Counterstain with anti-CORO1C antibody (Abcam ab96524 or equivalent) and DAPI.
  4. Image by confocal microscopy (63x oil objective). Quantify: total F-actin intensity, number of actin-rich growth cones, neurite length, CORO1C subcellular localization (cytoplasmic vs. membrane-associated).
  5. Controls: Vehicle (DMSO), tetraethylammonium (TEA, a K+ channel blocker that does NOT bind CORO1C), and jasplakinolide (actin stabilizer, positive control for actin pathway modulation).
  6. Live-cell imaging variant: SiR-Actin probe for real-time actin dynamics (timelapse, 10 min intervals for 12 h).
- **Expected result:**
  - **Positive:** 4-AP alters F-actin organization, growth cone morphology, or CORO1C localization in a dose-dependent manner. TEA does NOT produce the same effect (separating K+ channel from actin pathway mechanism).
  - **Critical negative control:** 4-AP does NOT alter SMN2 exon 7 splicing (run RT-PCR for SMN2 full-length vs. delta7 transcript ratio). If splicing changes, the mechanism is confounded.
- **Estimated cost:** EUR 15,000-25,000 (iPSC differentiation is labor-intensive)
- **Timeline:** 3-5 months (1 month differentiation, 2-4 months treatment + imaging + analysis)
- **Collaborator:** an organoid/NMJ modeling laboratory for iPSC-MN expertise. Alternatively, a collaborating SMA genetics laboratory with iPSC-MN capability has iPSC-MN protocols and deep SMA modifier biology expertise.

#### Experiment 1D: Co-Immunoprecipitation and Proximity Ligation (If 1A positive)

- **Assay:** Co-IP followed by Western blot, and Proximity Ligation Assay (PLA)
- **Protocol:**
  1. Treat HEK293T cells overexpressing FLAG-CORO1C with 4-AP (50 micromolar, 4 h).
  2. Lyse, immunoprecipitate with anti-FLAG beads. Western blot for Arp2/3, cofilin, cortactin — known CORO1C interaction partners.
  3. Compare pulled-down protein amounts +/- 4-AP. If 4-AP disrupts or enhances CORO1C-Arp2/3 interaction, this reveals the functional consequence of binding.
  4. PLA: In situ proximity ligation in iPSC-MNs using anti-CORO1C + anti-Arp2/3 antibody pairs. Count PLA dots/cell +/- 4-AP treatment.
- **Expected result:** 4-AP treatment alters the stoichiometry of CORO1C-Arp2/3 or CORO1C-cofilin complexes (either stabilizing or disrupting the interaction).
- **Estimated cost:** EUR 3,000-5,000
- **Timeline:** 4-6 weeks
- **Collaborator:** Any molecular biology lab with Co-IP capability

---

### Discovery 2: NEDD4L-TP53 Protein Similarity (Cosine 0.973)

**Why this matters:** NEDD4L (an E3 ubiquitin ligase) and TP53 (tumor suppressor) share unexpectedly high sequence-level similarity in ESM-2 embedding space. Both are implicated in motor neuron death in SMA. If NEDD4L functionally compensates for or antagonizes p53 in motor neurons, this could explain the selective vulnerability puzzle (why some motor neurons die while others survive). a collaborating SMA researcher specifically highlighted p53 + motor neuron death as a critical gap on our platform.

#### Experiment 2A: Expression Correlation in SMA Tissue

- **Assay:** Quantitative RT-PCR (qRT-PCR) and Western blot
- **Protocol:**
  1. Obtain spinal cord sections from SMA mouse model (SMN-delta-7, Jackson Lab stock #005025) at P5, P8, and P11 (pre-symptomatic, early symptomatic, late symptomatic).
  2. Laser-capture microdissect ventral horn motor neurons (L1 vs. L5 segments separately — per a collaborating SMA researcher's emphasis on segment-specific analysis).
  3. Measure NEDD4L and TP53 mRNA by qRT-PCR (TaqMan probes). Measure protein by Western blot from pooled microdissected tissue.
  4. Compare expression ratios (NEDD4L/TP53) in L1 (vulnerable) vs. L5 (resistant) motor neurons across timepoints.
  5. Include wild-type littermate controls at each timepoint.
- **Expected result:**
  - **Positive:** NEDD4L and TP53 show anti-correlated expression (high NEDD4L = low TP53 = survival) in resistant L5 motor neurons. Alternatively, NEDD4L expression drops before motor neuron death in L1 segments, mirroring p53 upregulation.
  - **Negative:** No correlation between NEDD4L and TP53 expression across segments or timepoints. The ESM-2 similarity is structural, not functional.
- **Estimated cost:** EUR 8,000-12,000 (mouse colony, LCM, qRT-PCR, Western)
- **Timeline:** 3-4 months
- **Collaborator:** a collaborating SMA mouse model laboratory (e.g. Leipzig University). a collaborating SMA researcher works directly with SMA mouse models and has published on L1 vs. L5 selective vulnerability. He would be the ideal collaborator for segment-specific dissection. His team also has the methodological expertise for proper motor neuron counting that he considers essential for any SMA study.

#### Experiment 2B: Functional Interaction (If 2A shows correlation)

- **Assay:** NEDD4L knockdown in SMA motor neurons + p53 pathway readout
- **Protocol:**
  1. Use iPSC-MNs (SMA patient-derived) or primary mouse MNs from SMA mice.
  2. siRNA knockdown of NEDD4L (ON-TARGETplus SMARTpool, Dharmacon).
  3. Measure: p53 protein levels (Western), p53 target gene activation (p21, PUMA, BAX by qRT-PCR), and motor neuron viability (CellTiter-Glo or TUNEL assay) at 48 h and 96 h post-knockdown.
  4. Reciprocal: overexpress NEDD4L (lentiviral) and measure p53 pathway suppression.
  5. Test if NEDD4L ubiquitinates p53 directly: in vitro ubiquitination assay with recombinant NEDD4L, E1, E2 (UbcH5a), ubiquitin, and His-tagged p53. Detect by anti-ubiquitin Western blot.
- **Expected result:**
  - **Positive:** NEDD4L knockdown increases p53 protein and triggers motor neuron apoptosis. NEDD4L overexpression is protective. In vitro ubiquitination shows direct NEDD4L-mediated p53 ubiquitination.
  - **Note:** MDM2 is the canonical p53 E3 ligase. If NEDD4L also ubiquitinates p53 in motor neurons, this would be a novel mechanism relevant to SMA-specific cell death.
- **Estimated cost:** EUR 10,000-15,000
- **Timeline:** 4-6 months
- **Collaborator:** a collaborating SMA laboratory (Leipzig) for mouse MNs, a collaborating SMA genetics laboratory for iPSC-MNs, or any lab with SMA motor neuron culture capability.

---

### Discovery 3: SMN1 Residues 289-294 as Interaction Hotspot

**Why this matters:** Our protein contact map analysis identified residues 289-294 of SMN1 (C-terminal region) as a shared interaction surface for both p53 and CORO1C. If confirmed, this suggests a competitive binding mechanism: p53 and CORO1C may compete for the same SMN binding site, with implications for motor neuron survival signaling.

#### Experiment 3A: Peptide Binding Competition Assay

- **Assay:** Fluorescence Polarization (FP) competition assay
- **Protocol:**
  1. Synthesize a fluorescein-labeled SMN1(289-294) peptide (FITC-EETNKASK or the exact 6-residue sequence from our contact map).
  2. Measure FP binding of labeled peptide to purified recombinant CORO1C and p53 proteins separately. Determine Kd for each interaction.
  3. Competition: Pre-incubate CORO1C with labeled SMN peptide, then titrate in unlabeled p53. If FP decreases, p53 displaces the SMN peptide from CORO1C, confirming shared binding site.
  4. Reciprocal: Pre-incubate p53 with labeled SMN peptide, titrate in CORO1C.
- **Expected result:**
  - **Positive:** Both CORO1C and p53 bind the SMN1(289-294) peptide with measurable affinity (Kd < 50 micromolar), and they compete for binding (IC50 of competitor within 10-fold of direct Kd).
  - **Negative:** No detectable peptide binding, or no competition. The contact map prediction was artifactual.
- **Estimated cost:** EUR 2,000-4,000 (peptide synthesis + FP plate reader)
- **Timeline:** 4-6 weeks
- **Collaborator:** Any biochemistry lab with fluorescence plate reader

#### Experiment 3B: Mutagenesis Validation

- **Assay:** Site-directed mutagenesis of SMN1 residues 289-294 + binding assay
- **Protocol:**
  1. Generate SMN1 mutants: alanine substitution of residues 289-294 (SMN1-6A mutant) and individual point mutants for each residue.
  2. Express wild-type and mutant SMN1 in HEK293T cells (FLAG-tagged).
  3. Co-IP with endogenous CORO1C and p53.
  4. Compare pull-down efficiency: if 289-294 mutations abolish CORO1C and/or p53 binding, the hotspot prediction is validated.
- **Expected result:** SMN1-6A mutant shows significantly reduced co-immunoprecipitation with CORO1C and p53 compared to wild-type SMN1.
- **Estimated cost:** EUR 3,000-5,000
- **Timeline:** 6-8 weeks
- **Collaborator:** Any molecular biology/structural biology lab

---

### Discovery 4: UBA1 Multi-Compound Druggability

**Why this matters:** UBA1 (ubiquitin-like modifier activating enzyme 1) showed the highest mean docking confidence of all 7 targets (-1.207) in the initial screen. In the expanded 4,116-compound screen (March 2026), UBA1 emerged as the most consistently druggable SMA target, producing 4-5 compounds with positive confidence scores — more than any other target screened. UBA1 dysregulation is an established SMN-independent mechanism in SMA (Wishart et al., JCI 2014). Finding druggable compounds for UBA1 could open a new therapeutic avenue independent of SMN restoration.

**Updated compound list (4,116-compound screen, March 2026):**

| Compound | DiffDock Confidence | Notes |
|----------|-------------------|-------|
| CHEMBL1301743 | +0.314 | Top UBA1 hit across all screens |
| Riluzole | +0.182 | FDA-approved ALS drug; multi-target (also binds SMN2 at +0.201) |
| CHEMBL1400508 | +0.138 | Consistent positive across runs |
| Pemirolast | +0.020 | Anti-allergic drug with existing safety data |
| CHEMBL1331875 | -0.089 | From initial screen, borderline |

The consistency of positive hits against UBA1 across a large and diverse compound library strengthens the case that UBA1 presents genuinely druggable binding pockets. This is not random noise: UBA1 attracted more positive-confidence compounds than targets with similar protein sizes, suggesting a favorable binding site geometry.

#### Experiment 4A: UBA1 Activity Assay with Top Compounds

- **Assay:** UBA1 ubiquitin-activating enzyme activity assay (E1 thioester formation)
- **Protocol:**
  1. Obtain recombinant human UBA1 (R&D Systems or Ubiquigent, catalog UBA1-500).
  2. Test the top DiffDock hits individually. Priority order from expanded screen: CHEMBL1301743 (+0.314), riluzole (+0.182), CHEMBL1400508 (+0.138), pemirolast (+0.020), CHEMBL1331875 (-0.089). Include original hits CHEMBL1301787 (-0.282) and CHEMBL1381595 (-0.337) if budget allows.
  3. E1 thioester assay: Incubate UBA1 (100 nM) + ubiquitin (5 micromolar) + ATP (2 mM) + compound (0.1-100 micromolar) at 37 degrees C for 15 min. Quench with non-reducing SDS-PAGE buffer (to preserve thioester bond). Western blot with anti-UBA1 antibody. Shifted band = UBA1~Ub thioester.
  4. Quantify: Does compound increase (activator) or decrease (inhibitor) thioester formation relative to DMSO control?
  5. Dose-response for any active compounds (8-point curve, 0.01-100 micromolar).
- **Expected result:**
  - **Positive (activator):** Compound increases UBA1~Ub thioester formation. This would be therapeutically desirable in SMA (restoring reduced UBA1 activity).
  - **Positive (inhibitor):** Compound decreases UBA1 activity. May still be informative for understanding UBA1 biology in SMA but less therapeutically relevant unless specific pathway branches benefit from partial inhibition.
  - **Negative:** No effect on UBA1 activity at concentrations up to 100 micromolar for any compound.
- **Estimated cost:** EUR 3,000-6,000 (recombinant enzyme + compounds + Western)
- **Timeline:** 4-6 weeks
- **Collaborator:** a collaborating SMA genetics laboratory — has published on UBA1 in SMA (Wishart et al. 2014). Or any enzymology/biochemistry lab.

#### Experiment 4B: UBA1 Cell-Based Validation (If 4A positive)

- **Assay:** Ubiquitin pathway rescue in SMA motor neurons
- **Protocol:**
  1. Treat SMA iPSC-MNs with active UBA1-modulating compound(s) from 4A.
  2. Measure: global ubiquitination levels (anti-Ub Western), specific ubiquitin substrates (beta-catenin, as identified by Wishart et al.), and motor neuron survival (7-day treatment, CellTiter-Glo).
  3. Compare to nusinersen-treated and untreated SMA iPSC-MNs.
- **Estimated cost:** EUR 10,000-15,000
- **Timeline:** 3-4 months
- **Collaborator:** a collaborating SMA genetics laboratory or an organoid modeling laboratory (Berlin)

---

### Discovery 5: CORO1C Structural Uniqueness Among SMA Targets

**Why this matters:** CORO1C had the lowest ESM-2 embedding norm (5.259) of all 7 SMA targets, indicating it occupies the most distinct position in protein sequence space. This structural uniqueness may explain why it is the only target to produce a strong positive docking hit — its WD-repeat beta-propeller fold presents binding pockets unlike those on the other SMA proteins.

#### Experiment 5A: CORO1C Expression in SMA Patient Tissue

- **Assay:** Immunohistochemistry (IHC) + Western blot on SMA patient or mouse tissue
- **Protocol:**
  1. Obtain spinal cord sections from SMA mouse model (P5, P8, P11) and wild-type controls.
  2. IHC with anti-CORO1C antibody (Abcam ab96524 or Proteintech 14749-1-AP). Co-stain with ChAT (motor neuron marker) and NeuN (pan-neuronal).
  3. Quantify CORO1C expression specifically in motor neurons (L1 vs. L5 segments).
  4. Western blot of lumbar spinal cord lysate for CORO1C protein levels across disease progression.
  5. If accessible: query existing SMA single-cell RNA-seq datasets (GEO, e.g., GSE138120 mouse SMA, GSE161240 human iPSC-MN) for CORO1C expression levels compared to other actin regulators.
- **Expected result:**
  - **Informative:** CORO1C is expressed in motor neurons and its expression changes during SMA disease progression (either up- or down-regulated). Changes would suggest functional relevance.
  - **Critical finding:** If CORO1C is differentially expressed in L1 (vulnerable) vs. L5 (resistant) motor neurons, this connects structural uniqueness to selective vulnerability — a collaborating SMA researcher's core research question.
  - **Negative:** CORO1C is not expressed in motor neurons, or expression does not change in SMA. This would reduce (but not eliminate) the relevance of the 4-AP/CORO1C binding prediction, as 4-AP might act on CORO1C in other cell types.
- **Estimated cost:** EUR 4,000-8,000
- **Timeline:** 2-3 months
- **Collaborator:** a collaborating SMA laboratory (Leipzig) — has SMA mouse tissue, motor neuron expertise, and segment-specific dissection methodology.

---

### Discovery 6: Riluzole Binds SMN2 Protein (+0.201 DiffDock Confidence)

*New finding from 4,116-compound DiffDock screen, March 21, 2026*

**Why this matters:** Riluzole is an FDA-approved drug for ALS (amyotrophic lateral sclerosis), prescribed since 1995 under the brand name Rilutek. It has a well-characterized safety profile with decades of clinical use. Our expanded virtual screening identified riluzole as binding to SMN2 protein with a DiffDock confidence of +0.201 — the second-highest positive score in the entire campaign after 4-AP/CORO1C (+0.251). Riluzole also shows binding to UBA1 (+0.182), suggesting a multi-target profile that could address both the SMN pathway and the SMN-independent ubiquitin pathway simultaneously.

**Critical context — prior clinical data in SMA:** A Phase 1 trial of riluzole in SMA was conducted (Russman et al., J Child Neurol 2003, PMID: 14623733). Key findings:
- Riluzole was safe in SMA patients
- A modest survival benefit was observed
- No motor function improvement was detected
- The hypothesized mechanism was glutamate excitotoxicity inhibition and sodium channel blockade

The critical point: that trial was designed around riluzole's known pharmacology (glutamate/sodium channel modulation), not protein binding. No molecular biomarkers were measured — no SMN protein levels, no SMN2 splicing ratios, no ubiquitin pathway markers. Our finding suggests a completely different mechanism: direct binding to SMN2 protein. If riluzole physically interacts with SMN2, it could potentially stabilize the protein or modulate SMN2 exon 7 splicing — a mechanism that would not have been detectable with the endpoints used in the Phase 1 trial.

**Honest probability estimate:** The a priori probability that riluzole genuinely binds SMN2 protein is approximately **10-25%**. This is lower than for 4-AP/CORO1C because: (a) DiffDock confidence is lower (+0.201 vs. +0.251), (b) riluzole is a moderately small molecule (MW 234.2) that may produce nonspecific docking signals, and (c) no independent evidence currently links riluzole to SMN2 biology. The dual binding to both SMN2 and UBA1 could indicate genuine poly-pharmacology OR nonspecific hydrophobic interactions. Biophysical assays will distinguish between these possibilities.

**Why it is still worth testing:** Riluzole is already FDA-approved, generic, inexpensive (~EUR 50-100/month), and has been administered to SMA patients without safety issues. The experiments required to test this hypothesis (SPR, RT-PCR, Western blot) are among the cheapest in this plan. If even a modest SMN2-stabilizing effect is confirmed, riluzole could be rapidly repurposed — potentially as a combination therapy alongside nusinersen or risdiplam.

#### Experiment 6A: Riluzole-SMN2 Biophysical Binding (GO/NO-GO GATE)

- **Assay:** Surface Plasmon Resonance (SPR) using Biacore T200 or equivalent
- **Protocol:**
  1. Express and purify recombinant human SMN protein (full-length, 294 aa, or Tudor domain + C-terminal region if full-length proves insoluble). His-tag purification via Ni-NTA, followed by SEC.
  2. Immobilize SMN on CM5 sensor chip via amine coupling (target density: 2000-5000 RU).
  3. Flow riluzole (Sigma-Aldrich R116, MW 234.2, >98% purity) at 8 concentrations: 0.1, 0.5, 1, 5, 10, 50, 100, 500 micromolar. Running buffer: 10 mM HEPES pH 7.4, 150 mM NaCl, 3 mM EDTA, 0.005% Tween-20, 2% DMSO.
  4. Negative controls: blank flow cell, BSA-immobilized flow cell, buffer-only injections.
  5. Positive control: if available, a known SMN-binding compound or peptide to confirm the protein is functional on chip.
  6. Fit binding curves to steady-state affinity model.
- **Expected result:**
  - **Positive (validates prediction):** Measurable, dose-dependent binding with Kd < 10 micromolar.
  - **Weakly positive:** Kd between 10-100 micromolar. Potentially pharmacologically relevant given riluzole's plasma Cmax of ~1-2 micromolar at standard 50 mg BID dosing.
  - **Negative (refutes prediction):** No detectable binding at any concentration tested. This would definitively refute the DiffDock prediction.
- **Go/no-go threshold:** Kd < 50 micromolar to proceed to functional studies.
- **Estimated cost:** EUR 3,000-5,000 (can share infrastructure with CORO1C SPR in Experiment 1A if both proteins are purified simultaneously)
- **Timeline:** 4-6 weeks (can run in parallel with Experiment 1A)

#### Experiment 6B: Riluzole Effect on SMN2 Exon 7 Splicing (If 6A positive)

- **Assay:** RT-PCR for SMN2 full-length vs. delta-7 transcript ratio
- **Protocol:**
  1. Treat SMA patient fibroblasts (homozygous SMN1 deletion, 2-3 copies SMN2) with riluzole at 0.1, 1, 10, 50 micromolar for 24 h and 72 h.
  2. Extract total RNA (TRIzol), reverse transcribe, PCR with primers spanning exon 6-8 junction.
  3. Quantify FL-SMN2 (exon 7 included) vs. delta7-SMN2 (exon 7 skipped) by capillary electrophoresis or qRT-PCR.
  4. Positive control: risdiplam (1 micromolar, known to increase exon 7 inclusion ~2-3-fold in fibroblasts).
  5. Negative control: DMSO vehicle.
- **Expected result:**
  - **Positive:** Riluzole increases the FL/delta7 ratio by > 1.5-fold at achievable plasma concentrations (< 10 micromolar). This would be a significant finding — identifying a potential second oral SMN2 splicing modifier alongside risdiplam.
  - **Negative:** No change in splicing ratio. Riluzole may still bind SMN2 protein without affecting splicing (e.g., by stabilizing full-length protein post-translationally rather than modulating mRNA processing).
- **Estimated cost:** EUR 500-1,500 (fibroblasts are widely available, RT-PCR is routine)
- **Timeline:** 2-3 weeks
- **Note:** This is one of the cheapest and fastest experiments in the entire plan. Any SMA laboratory with patient fibroblasts can perform this.

#### Experiment 6C: Riluzole Effect on Full-Length SMN Protein Levels (If 6A or 6B positive)

- **Assay:** Western blot for SMN protein levels
- **Protocol:**
  1. Treat SMA patient fibroblasts with riluzole (dose range as in 6B) for 24 h, 48 h, 72 h.
  2. Lyse, run Western blot with anti-SMN antibody (BD Transduction 610646 or equivalent).
  3. Quantify full-length SMN protein by densitometry, normalized to beta-actin loading control.
  4. Positive control: risdiplam-treated or nusinersen-treated cells (if available).
- **Expected result:**
  - **Positive:** Riluzole increases full-length SMN protein by > 1.3-fold. Even a modest increase could be clinically meaningful, particularly in combination with existing SMN-restoring therapies.
  - **Negative:** No change in SMN protein levels. Combined with a negative splicing result, this would indicate that riluzole-SMN2 binding (if biophysically real) does not translate to functional consequences for SMN biology.
- **Estimated cost:** EUR 1,000-2,000
- **Timeline:** 2-3 weeks (can run in parallel with 6B)

#### Experiment 6D: Riluzole-UBA1 Binding and Activity (Parallel with Experiment 4A)

- **Assay:** UBA1 E1 thioester assay (shared with Experiment 4A compound panel)
- **Protocol:** Include riluzole in the UBA1 activity assay described in Experiment 4A. If riluzole modulates UBA1 enzymatic activity, this confirms the dual-target prediction from DiffDock.
- **Expected result:** If riluzole both binds SMN2 and modulates UBA1 activity, this would represent a dual-mechanism drug: SMN pathway restoration + SMN-independent pathway modulation. Such a profile would be unique among SMA therapeutics.
- **Estimated cost:** Minimal incremental cost (riluzole added to existing UBA1 compound panel)

#### Clinical Considerations for Riluzole Repurposing

| Property | Detail |
|----------|--------|
| **Generic name** | Riluzole (2-amino-6-(trifluoromethoxy)benzothiazole) |
| **Brand names** | Rilutek (oral tablet), Exservan (oral film), Tiglutik (oral suspension) |
| **FDA approval** | 1995, for ALS |
| **Approved dose** | 50 mg BID |
| **Plasma Cmax** | ~1-2 micromolar at standard dosing |
| **Half-life** | ~12 hours |
| **BBB penetration** | Yes (CNS-active drug, established BBB crossing) |
| **Safety in SMA** | Phase 1 tested (Russman et al. 2003) — safe, well-tolerated |
| **Generic availability** | Yes. Approximate cost: EUR 50-100/month |
| **Key advantage** | Already tested in SMA patients (safety data exists). If SMN2 binding mechanism confirmed, could enter Phase 2 rapidly with molecular biomarkers (SMN protein, SMN2 splicing) as endpoints. |

**Limitation stated transparently:** The Phase 1 trial (Russman et al. 2003) found no motor improvement, which may discourage clinicians and funders from reinvestigating riluzole for SMA. The counter-argument is that the trial tested the wrong mechanism (glutamate inhibition) with endpoints insensitive to protein-level effects (motor function rather than SMN biomarkers). If riluzole acts via SMN2 protein interaction, the appropriate endpoints would be SMN protein levels in blood or CSF and SMN2 splicing ratios — neither of which were measured in the original trial.

---

## Part 2: Computational Validation (Actionable Now — Zero Cost)

These analyses can be performed immediately using existing tools and public databases. They should be completed BEFORE any wet-lab experiments begin, as they may strengthen or weaken the rationale for specific experiments.

### 2.1 Cross-Reference 4-AP/CORO1C in Interaction Databases

| Database | Query | Expected |
|----------|-------|----------|
| **STRING-DB** | CORO1C protein interactions | Check if any known 4-AP targets (KCNA1-6, K+ channels) interact with CORO1C |
| **BioGRID** | CORO1C (human, 23603) | Full interaction list — look for SMA-relevant partners |
| **IntAct** | CORO1C OR Q9ULV4 | Experimentally validated PPIs |
| **ChEMBL** | 4-aminopyridine (CHEMBL1138) | All known bioactivities — any actin/cytoskeletal targets? |
| **DrugBank** | Dalfampridine (DB06637) | Comprehensive target list beyond K+ channels |
| **PDB** | CORO1C | Any experimental structures? (Likely none; coronin family has some structures) |

**Action:** Run these queries and document results. If STRING-DB shows CORO1C interacting with known 4-AP targets, this suggests a pathway-level connection even if direct binding is not catalogued.

### 2.2 CORO1C Expression in SMA Datasets

| Dataset | Source | Analysis |
|---------|--------|----------|
| GSE138120 | Mouse SMA spinal cord (Nichterwitz et al.) | CORO1C expression in MN vs. non-MN cells |
| GSE161240 | Human iPSC-MN SMA vs. control | CORO1C differential expression |
| GSE150831 | SMA mouse NMJ transcriptomics | CORO1C at NMJ |
| Allen Brain Atlas | Human spinal cord | CORO1C spatial expression pattern |

**Action:** Download raw counts or use GEO2R for differential expression. If CORO1C is significantly down-regulated in SMA motor neurons, this strengthens the rationale for 4-AP/CORO1C as a compensatory mechanism.

### 2.3 Verify NEDD4L-TP53 Link

| Database | Query | Expected |
|----------|-------|----------|
| **STRING-DB** | NEDD4L + TP53 co-expression/interaction | Known functional connection? |
| **BioGRID** | NEDD4L (23327) | Does NEDD4L interact with p53 or MDM2? |
| **PhosphoSitePlus** | NEDD4L substrates | Is p53 a known or predicted NEDD4L substrate? |
| **UbiNet** | NEDD4L E3 ligase targets | Published ubiquitination targets |
| **PubMed** | "NEDD4L" AND "p53" | Any published connection? |

**Note:** NEDD4L is known to ubiquitinate various substrates (ENaC, SMAD2/3, PTEN). If p53 is NOT a known NEDD4L substrate, our ESM-2 similarity finding would be genuinely novel and worth investigating.

### 2.4 Orthogonal Docking with Alternative Scoring

Run 4-AP vs. CORO1C docking using at least 2 additional methods to assess consensus:

| Method | Tool | Access |
|--------|------|--------|
| **AutoDock Vina** | Open-source, local GPU | Self-hosted (Vast.ai or local) |
| **GNINA** | CNN-scored docking, open-source | Self-hosted |
| **GOLD** | Genetic optimization, commercial | Academic license via CCDC |
| **Glide (Schrodinger)** | Industry standard | Academic license or free trial |

**Consensus threshold:** If 3 of 4 methods predict 4-AP binding to CORO1C with favorable scores, this substantially increases confidence. If DiffDock is the only method predicting binding, the result is likely an artifact.

### 2.5 Molecular Dynamics Simulation

- **System:** CORO1C (AlphaFold structure) + 4-AP in best DiffDock pose
- **Protocol:** 100-500 ns explicit solvent MD using OpenMM or GROMACS on A100 GPU
- **Metrics:** RMSD of 4-AP from initial pose over time, binding free energy (MM-GBSA or MM-PBSA), hydrogen bond persistence, contact frequency
- **Go/no-go:** If 4-AP dissociates within < 10 ns, the binding pose is unstable. If stable for > 50 ns with consistent H-bonds, the prediction is reinforced.
- **Cost:** < EUR 5 (Vast.ai A100, ~2 hours for 100 ns)
- **Note:** We already have the OpenMM script (`gpu/scripts/run_md_4ap_smn2.py`) — adapt for CORO1C target.

### 2.6 Expanded Screening (Statistical Context)

**STATUS: PARTIALLY COMPLETED (March 21, 2026)**

The initial 54-compound library was expanded to a 4,116-compound screen across all 7 SMA protein targets. Key findings from the expanded screen:

- **4-AP/CORO1C:** The +0.251 confidence score from the initial screen was confirmed. 4-AP remains among the top-ranked compounds for CORO1C in the larger library, strengthening the signal.
- **New discovery — riluzole:** Identified as binding SMN2 (+0.201) and UBA1 (+0.182). Not detected in the initial 54-compound screen because riluzole was not in that library.
- **UBA1 druggability confirmed:** UBA1 attracted the most positive-confidence compounds of any target (4-5 hits), consistent across the expanded library.

**Next step:** Screen a still-larger library to further contextualize these hits:

- **Source:** ZINC20 or Enamine REAL (50,000-100,000 drug-like compounds, diverse scaffolds)
- **Method:** DiffDock v2.2 NIM API or self-hosted GNINA
- **Question:** Where do 4-AP and riluzole rank among 50,000+ compounds against their respective targets? If top 1% = strong signal. If top 10% = weak signal.
- **Cost:** DiffDock NIM API free credits may cover 10,000 dockings. Full 100K screen ~EUR 20-50 on Vast.ai.

---

## Part 3: Clinical Context

### 3.1 4-AP Regulatory Status

| Property | Detail |
|----------|--------|
| **Generic name** | 4-aminopyridine (fampridine, dalfampridine) |
| **Brand names** | Fampyra (EU), Ampyra (US) |
| **FDA approval** | 2010, for walking improvement in MS |
| **EMA approval** | 2011 |
| **Approved dose** | 10 mg BID (extended-release) |
| **Safety profile** | Well-characterized. Seizure risk at supratherapeutic doses. Therapeutic window: plasma 15-40 ng/mL. |
| **Generic availability** | Yes (off-patent). Very low cost. |
| **Repurposing advantage** | Phase 1 safety data exists. Could proceed directly to Phase 2 proof-of-concept with CORO1C-specific biomarkers. |

### 3.2 Prior 4-AP Clinical Data in SMA

| Trial | NCT01645787 |
|-------|------------|
| **Phase** | 2/3 |
| **Sponsor** | Columbia University |
| **Population** | 11 adult SMA Type 3 (ambulatory) |
| **Duration** | 8 weeks |
| **Drug** | Dalfampridine-ER 10 mg BID |
| **Primary endpoints** | 6MWT, HFMSE |
| **Result** | Negative (no significant improvement) |
| **Hypothesized mechanism** | K+ channel blockade improving NMJ transmission |
| **What was NOT measured** | CORO1C expression, actin dynamics, SMN protein, any molecular biomarker |
| **Interpretation** | Disproves K+ channel hypothesis for functional improvement in ambulatory Type 3 adults over 8 weeks. Does NOT address protein-binding hypothesis. |

### 3.3 Key Question: Does 4-AP Reach CORO1C In Vivo?

Before any new clinical trial, pharmacokinetic considerations must be addressed:

1. **Blood-brain barrier penetration:** 4-AP crosses the BBB (established in MS literature, CSF/plasma ratio ~0.8).
2. **Motor neuron exposure:** CNS penetration is confirmed, but spinal motor neuron exposure specifically has not been quantified. MS pharmacology assumes diffuse CNS distribution.
3. **Required concentration:** If SPR shows Kd = 10 micromolar for CORO1C, is this achievable at approved doses? At 10 mg BID, plasma Cmax is ~35 ng/mL = ~0.37 micromolar. This is 27-fold below a 10 micromolar Kd. Higher doses or local delivery may be needed, but seizure risk limits systemic dosing.
4. **Implication:** Even if binding is confirmed biophysically, the clinically achievable 4-AP concentration may be insufficient for meaningful CORO1C modulation at standard doses. This is a critical go/no-go consideration that must be discussed transparently with collaborators.

### 3.4 Repurposing Path (If All Validation Positive)

| Step | Activity | Timeline |
|------|----------|----------|
| 1 | SPR binding confirmation | Month 1-2 |
| 2 | Orthogonal docking consensus | Month 1-2 (parallel) |
| 3 | iPSC-MN functional studies with CORO1C readouts | Month 3-6 |
| 4 | PK modeling: Can therapeutic CORO1C-binding concentrations be achieved? | Month 4-5 |
| 5 | SMA mouse model: 4-AP treatment with CORO1C-specific endpoints | Month 6-12 |
| 6 | If positive: IND-enabling studies or investigator-initiated trial design | Month 12-18 |
| 7 | Phase 2 proof-of-concept (existing safety data accelerates timeline) | Month 18-30 |

### 3.5 Riluzole Clinical Context

| Property | Detail |
|----------|--------|
| **Generic name** | Riluzole (2-amino-6-(trifluoromethoxy)benzothiazole) |
| **Brand names** | Rilutek (EU/US), Exservan (oral film), Tiglutik (oral suspension) |
| **FDA approval** | 1995, for ALS |
| **EMA approval** | 1996 |
| **Approved dose** | 50 mg BID |
| **Safety profile** | Well-characterized over 30+ years. Hepatotoxicity (monitor ALT/AST). Neutropenia (rare). GI side effects (nausea). Overall well-tolerated. |
| **Generic availability** | Yes (off-patent since 2013). Very low cost (~EUR 50-100/month). |
| **BBB penetration** | Yes (CNS-active drug, designed to reach motor neurons) |
| **Plasma Cmax** | ~1-2 micromolar at standard 50 mg BID dosing |

### 3.6 Prior Riluzole Clinical Data in SMA

| Trial | Russman et al. 2003 (PMID: 14623733) |
|-------|--------------------------------------|
| **Phase** | 1 (safety/tolerability) |
| **Population** | SMA patients (mixed types) |
| **Duration** | 9 months |
| **Drug** | Riluzole (dose adjusted by weight) |
| **Result** | Safe, modest survival benefit, no motor function improvement |
| **Hypothesized mechanism** | Glutamate excitotoxicity reduction + sodium channel modulation |
| **What was NOT measured** | SMN protein levels, SMN2 splicing, UBA1 activity, any molecular biomarker |
| **Our interpretation** | The trial tested glutamate inhibition, NOT protein binding. Our DiffDock prediction suggests riluzole may bind SMN2 directly — a completely distinct mechanism that would require different endpoints (SMN protein, splicing ratio) to detect. The negative motor outcome does not address this hypothesis. |

### 3.7 Key Question: Does Riluzole Reach SMN2 at Therapeutic Concentrations?

1. **BBB penetration:** Confirmed (riluzole is designed for CNS activity in ALS).
2. **Plasma Cmax:** ~1-2 micromolar at 50 mg BID. If SPR shows Kd = 10 micromolar for SMN2, the drug would need higher dosing or local delivery. However, if Kd < 5 micromolar, standard oral dosing may achieve pharmacologically meaningful occupancy.
3. **Advantage over 4-AP:** Riluzole achieves ~3-5x higher CNS concentrations than 4-AP at standard doses, making it more likely to reach a protein-binding threshold even if Kd is in the low micromolar range.
4. **Combination potential:** Riluzole could theoretically be combined with nusinersen or risdiplam. If riluzole stabilizes SMN protein (post-translational) while risdiplam increases SMN2 exon 7 inclusion (pre-translational), the combination could be additive.

---

## Part 4: Grant Application Opportunities

### 4.1 Cure SMA Research Grant

| Field | Detail |
|-------|--------|
| **Funder** | Cure SMA (US-based, largest SMA patient organization) |
| **Amount** | $100,000-$250,000 |
| **Duration** | 1-2 years |
| **Cycle** | Annual (LOI typically due March-May) |
| **Fit** | Strong. Cure SMA funds both basic and translational SMA research. Drug repurposing with novel mechanism is exactly their target. Patient-researcher angle is compelling. |
| **PI requirement** | Must be affiliated with a research institution. Leipzig or Cologne affiliation required. Christian Fischer as co-investigator or consultant. |
| **URL** | https://www.curesma.org/research/for-researchers/ |

### 4.2 NIH R21 (Exploratory/Developmental Research)

| Field | Detail |
|-------|--------|
| **Funder** | NIH / NINDS (National Institute of Neurological Disorders and Stroke) |
| **Amount** | $275,000 over 2 years (direct costs) |
| **Mechanism** | R21 — explicitly for "exploratory and developmental research" |
| **Fit** | Good. Computational prediction + biophysical validation is classic R21 scope. Novel target (CORO1C) for existing disease (SMA) with existing drug (4-AP). |
| **PI requirement** | US institution or foreign institution with NIH-eligible status. an RNA splicing laboratory (e.g. CSHL) or a US collaborator needed. |
| **Relevant FOA** | PAR-XX-XXX "Novel Approaches to Drug Repurposing for Neurological Disorders" (check current NINDS FOAs) |
| **Advantage** | Preliminary data = DiffDock screen + evidence graph. No need for extensive prior results for R21. |

### 4.3 DFG (Deutsche Forschungsgemeinschaft)

| Field | Detail |
|-------|--------|
| **Funder** | German Research Foundation |
| **Amount** | Variable (typically EUR 150,000-400,000 for individual grants, Sachbeihilfe) |
| **Mechanism** | Sachbeihilfe (research grant) or SPP (Priority Programme) if relevant call exists |
| **Fit** | Excellent for Leipzig collaboration. DFG favors German-institution PIs with defined projects. |
| **PI requirement** | German institution (Leipzig University qualifies). a collaborating laboratory as PI, Fischer as project partner. |
| **Advantage** | No strict deadlines for Sachbeihilfe (submit anytime). Peer review within 6 months. |
| **Note** | DFG increasingly values open science and reproducibility — our open-source platform and data availability align well. |

### 4.4 SMA Europe Research Grant

| Field | Detail |
|-------|--------|
| **Funder** | SMA Europe (patient organization, EU-based) |
| **Amount** | EUR 50,000-150,000 |
| **Cycle** | Annual call (typically autumn) |
| **Fit** | Good. European patient organization funding European research. Patient-researcher PI is unique. |
| **URL** | https://www.sma-europe.eu/research/ |

### 4.5 BMBF (German Federal Ministry of Education and Research)

| Field | Detail |
|-------|--------|
| **Funder** | BMBF, often via DLR Projekttraeger |
| **Mechanism** | Targeted calls for rare disease research, AI in medicine, or drug repurposing |
| **Amount** | EUR 200,000-1,000,000 (collaborative projects) |
| **Fit** | Strong if a relevant call is open. BMBF funds translational rare disease projects. Leipzig-Cologne-Berlin consortium would be competitive. |
| **Note** | Calls are not continuous — must watch for relevant announcements. |

### 4.6 Suggested Grant Strategy

**Phase 1 (immediate):** Apply for Cure SMA Research Grant (highest probability of success, fastest timeline, $100-250K covers all Phase 1 experiments). a collaborating SMA researcher/a biochemistry collaborator as Leipzig PI, Fischer as co-PI or consultant.

**Phase 2 (if Phase 1 experiments positive):** DFG Sachbeihilfe for expanded mechanistic studies (EUR 200-300K, 3-year project). Leipzig-based, leveraging Phase 1 results as preliminary data.

**Phase 3 (if mouse model positive):** NIH R21 via US collaborator (an RNA splicing laboratory (US)) for translational studies + IND-enabling work.

---

## Part 5: Timeline

### Phase 1: Computational Cross-Validation + Biophysical Binding (Month 1-3)

| Month | Activity | Responsible | Cost |
|-------|----------|-------------|------|
| 1 | Orthogonal docking (AutoDock Vina, GNINA) for 4-AP/CORO1C AND riluzole/SMN2 | Fischer (computational) | < EUR 10 |
| 1 | MD simulation: 100 ns pose stability for 4-AP/CORO1C, riluzole/SMN2, riluzole/UBA1 | Fischer (Vast.ai GPU) | < EUR 15 |
| 1 | Database queries: STRING-DB, BioGRID, ChEMBL, DrugBank for all targets | Fischer (computational) | EUR 0 |
| 1 | GEO expression analysis: CORO1C + UBA1 in SMA scRNA-seq datasets | Fischer (computational) | EUR 0 |
| 1 | Riluzole literature mining: PubMed/bioRxiv for any riluzole-SMN connection | Fischer (computational) | EUR 0 |
| 1 | ML proxy screen: 100K ZINC compounds vs. CORO1C, SMN2, UBA1 | Fischer (computational) | EUR 0 |
| 1-2 | **FAST-TRACK:** Riluzole effect on SMN2 splicing (RT-PCR in SMA fibroblasts) | Any collaborating SMA lab | EUR 500-1,500 |
| 1 | CORO1C + SMN2 protein expression + purification | Leipzig collaborator | EUR 3,000-5,000 |
| 2-3 | SPR binding assay: 4-AP vs. CORO1C | Leipzig collaborator | EUR 2,000-3,000 |
| 2-3 | SPR binding assay: riluzole vs. SMN2 (parallel with CORO1C SPR) | Leipzig collaborator | EUR 2,000-3,000 |
| 2-3 | Riluzole effect on SMN protein levels (Western blot in SMA fibroblasts) | Any collaborating SMA lab | EUR 1,000-2,000 |
| 3 | **GO/NO-GO DECISION** based on SPR Kd values and functional results | All | — |

**Phase 1 total: EUR 8,500-14,500 + computational (< EUR 50)**

### Phase 2: Functional Studies in Motor Neurons (Month 3-6)

*Proceed only if SPR shows Kd < 50 micromolar*

| Month | Activity | Responsible | Cost |
|-------|----------|-------------|------|
| 3-4 | HDX-MS binding site mapping on CORO1C | CRO or core facility | EUR 5,000-8,000 |
| 3-5 | iPSC-MN differentiation (SMA + isogenic control) | an organoid modeling laboratory (Berlin) or a collaborating SMA genetics laboratory | EUR 10,000-15,000 |
| 4-6 | Actin dynamics imaging: 4-AP effect on F-actin in iPSC-MNs | Same lab | Included above |
| 4-5 | Co-IP: 4-AP effect on CORO1C-Arp2/3 interaction | Leipzig or Cologne | EUR 3,000-5,000 |
| 4-5 | NEDD4L-TP53 expression correlation in SMA mouse (L1 vs. L5) | a collaborating SMA laboratory (Leipzig) | EUR 8,000-12,000 |
| 4-6 | UBA1 enzyme activity assay with top 5 compounds | a collaborating SMA genetics laboratory | EUR 3,000-6,000 |
| 5-6 | SMN1(289-294) peptide competition assay | Leipzig biochemistry | EUR 2,000-4,000 |
| 6 | **GO/NO-GO DECISION** based on functional results | All | — |

**Phase 2 total: EUR 31,000-50,000**

### Phase 3: In Vivo Validation in SMA Mouse Model (Month 6-12)

*Proceed only if Phase 2 shows functional effects in motor neurons*

| Month | Activity | Responsible | Cost |
|-------|----------|-------------|------|
| 6-7 | Design mouse study: SMA-delta-7 model, 4-AP dosing, CORO1C-specific endpoints | Platform team + collaborating laboratory | EUR 0 |
| 7-10 | Mouse treatment study: 4-AP (5 mg/kg daily IP, based on Bhatt et al.) from P1-P11 | a collaborating SMA laboratory (Leipzig) | EUR 15,000-25,000 |
| 7-10 | Endpoints: CORO1C expression (IHC + Western), actin dynamics (phalloidin), motor neuron counts (L1 vs. L5), NMJ morphology, grip strength, righting reflex, survival | a collaborating SMA researcher | Included |
| 10-11 | Spinal cord histology: CORO1C + ChAT co-staining across segments | a collaborating SMA researcher | EUR 3,000-5,000 |
| 10-11 | Ubiquitin pathway markers: UBA1 activity, beta-catenin levels | Leipzig/Cologne | EUR 2,000-4,000 |
| 11-12 | Data analysis + manuscript preparation | All | EUR 0 |
| 12 | **PUBLICATION DECISION** | All | — |

**Phase 3 total: EUR 20,000-34,000**

### Total Budget Summary

| Phase | Timeline | Cost (EUR) | Go/No-Go Gate |
|-------|----------|-----------|---------------|
| Computational validation | Month 1 | < 50 | Consensus docking + stable MD + expression data |
| Phase 1: Biophysical binding | Month 1-3 | 8,000-15,000 | SPR Kd < 50 micromolar (CORO1C + SMN2 + UBA1) |
| Phase 1 fast-track: Riluzole/SMN2 splicing | Month 1-2 | 500-1,500 | FL/delta7 ratio change > 1.5-fold |
| Phase 2: Functional studies | Month 3-6 | 31,000-50,000 | Functional effect in iPSC-MNs |
| Phase 3: In vivo validation | Month 6-12 | 20,000-34,000 | Mouse model efficacy |
| **Total** | **12-18 months** | **EUR 60,000-100,000** | |

---

## Part 6: Risk Assessment and Failure Modes

### What Could Go Wrong

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| SPR shows no 4-AP/CORO1C binding | 40-60% | Fatal for Discovery 1 | Run orthogonal docking first; if all methods disagree with DiffDock, deprioritize SPR |
| 4-AP binds CORO1C but Kd > 100 micromolar | 20-30% | Weakly positive; pharmacologically irrelevant | Explore 4-AP analogs with higher affinity (GenMol pipeline) |
| CORO1C not expressed in motor neurons | 15-25% | Reduces relevance | Check GEO datasets first (zero cost); could still act on glial cells |
| Achievable 4-AP plasma concentration too low for CORO1C binding | High if Kd > 5 micromolar | Blocks clinical translation | Model early; consider intrathecal delivery or higher-affinity analogs |
| DiffDock result is a false positive (small molecule artifact) | 30-50% | Wastes Phase 1 resources | Expanded screening (10K compounds) will contextualize the signal before wet-lab starts |
| NEDD4L does not interact with p53 in motor neurons | 50% | Terminates Discovery 2 | Independent of Discovery 1; failure here does not affect 4-AP/CORO1C work |
| iPSC-MN differentiation fails or is inconsistent | 10-20% | Delays Phase 2 | Use established protocol (Maury et al.); bank differentiated neurons; collaborate with experienced lab |
| SPR shows no riluzole/SMN2 binding | 50-70% | Terminates Discovery 6 | Run orthogonal docking first; low cost to test (shared SPR infrastructure) |
| Riluzole binds SMN2 but does not affect splicing or protein levels | 30-40% (if binding confirmed) | Limits therapeutic relevance | Binding without function is still publishable and informative for SMN2 structural biology |
| Prior negative Phase 1 data discourages collaborators | 30-40% | Slows progress | Explain mechanism distinction clearly; the Phase 1 tested glutamate inhibition, not protein binding |
| Riluzole multi-target binding is nonspecific (hydrophobic artifact) | 40-50% | Invalidates both SMN2 and UBA1 predictions | SPR with proper controls (BSA, unrelated protein) will distinguish specific from nonspecific binding |

### Honest Assessment of Overall Probability

Based on DiffDock's ~38% top-1 accuracy on PoseBusters, the small size of 4-AP (prone to nonspecific docking), and the use of predicted (not experimental) structures, the a priori probability that the 4-AP/CORO1C binding prediction is correct is approximately **15-30%**. For riluzole/SMN2, the probability is estimated at **10-25%** (lower DiffDock confidence, no prior literature support). For UBA1 druggability, the probability is somewhat higher at **25-40%**, given the consistency of positive hits across a large compound library and the established biological role of UBA1 in SMA. These are consistent with typical computational drug discovery hit rates and are stated transparently.

However, the investment required to test these hypotheses is modest (EUR 8,500-14,500 for expanded Phase 1 covering all three predictions), the compounds are already FDA-approved (removing years of safety testing), and the potential payoff (new therapeutic mechanisms for SMA) is high. The riluzole/SMN2 splicing experiment in particular (EUR 500, 2 weeks) may be the single highest-value experiment available in SMA drug repurposing research today. The expected value calculation favors proceeding for all three top predictions.

---

## Part 7: Deliverables for a collaborating SMA researcher Meeting (Week of March 30)

To prepare for the collaborator meeting, the following should be completed:

1. **Computational validation results** (Part 2 items 2.1-2.6 + Part 8): Database queries, GEO expression data, orthogonal docking results, riluzole literature mining. These are zero-cost and can be done this week.
2. **One-page summary** of Discovery 1 (4-AP/CORO1C) with honest probability assessment.
3. **NEW: One-page summary** of Discovery 6 (riluzole/SMN2) including the critical distinction from the prior Phase 1 trial mechanism.
4. **Specific ask for collaborating SMA laboratory:** SMA mouse tissue for CORO1C IHC (L1 vs. L5 segments). This directly aligns with expertise in segment-specific analysis.
5. **Specific ask — lowest-cost experiment:** Can a collaborating laboratory test riluzole effect on SMN2 splicing in SMA fibroblasts? This requires only fibroblasts + riluzole + RT-PCR (EUR 500, 2 weeks). A positive or negative result would be immediately informative.
6. **Discussion of NEDD4L-TP53:** This connects to p53 + motor neuron death research. Frame as: "Our ESM-2 analysis found unexpectedly high similarity between NEDD4L and TP53. Is there published evidence for NEDD4L involvement in SMA motor neuron death?"
7. **Updated grant opportunity brief:** Cure SMA annual grant + DFG Sachbeihilfe options. Now with expanded scope covering riluzole/SMN2 and UBA1 druggability in addition to 4-AP/CORO1C.
8. **4,116-compound screening summary:** Present the expanded campaign results, emphasizing UBA1 as the most consistently druggable target and riluzole as a multi-target hit.

---

## Part 8: Computational Validations We Can Run Immediately (Cost: < EUR 50 Total)

These analyses require no wet-lab access, no collaborators, and minimal compute cost. They should be completed before any experimental investment to strengthen or weaken the rationale for each prediction. All can be run from the SMA Research Platform infrastructure.

### 8.1 AutoDock Vina Consensus Docking

- **What:** Re-dock 4-AP vs. CORO1C, and riluzole vs. SMN2 and UBA1, using AutoDock Vina as an orthogonal scoring function to DiffDock.
- **Why:** DiffDock uses a diffusion model for scoring; AutoDock Vina uses a physics-based force field. Agreement between fundamentally different methods substantially increases confidence. Disagreement flags potential DiffDock artifacts.
- **How:** Download AlphaFold structures for CORO1C (AF-Q9ULV4), SMN (AF-Q16637), UBA1 (AF-P22314). Prepare receptor with MGLTools. Run Vina with exhaustiveness=32, 20 modes per run.
- **Interpretation:** Vina score < -5.0 kcal/mol = plausible binding. Score < -7.0 = strong binding. Compare binding poses between DiffDock and Vina — if poses overlap (RMSD < 3 angstrom), the prediction is reinforced.
- **Cost:** < EUR 1 (Vast.ai GPU, ~15 minutes per target)
- **Timeline:** 1-2 days

### 8.2 Molecular Dynamics Pose Stability

- **What:** Run 100 ns explicit-solvent MD simulations for: (a) 4-AP in CORO1C binding site, (b) riluzole in SMN2 binding site, (c) riluzole in UBA1 binding site.
- **Why:** DiffDock provides a static pose. MD tests whether the small molecule remains stably bound under physiological conditions. If the compound leaves the binding pocket within the first 10 ns, the DiffDock pose is unstable.
- **How:** Use OpenMM or GROMACS on Vast.ai A100. Start from best DiffDock pose. TIP3P water model, PME electrostatics, 2 fs timestep, NVT + NPT equilibration, 100 ns production run.
- **Metrics:** Ligand RMSD over time (stable < 3 angstrom), hydrogen bond occupancy (>30% = stable H-bond), binding free energy (MM-GBSA, negative = favorable).
- **Go/no-go:** Dissociation within < 10 ns = unstable pose. Stable for > 50 ns with consistent interactions = reinforced prediction.
- **Cost:** < EUR 5 per simulation (A100 ~2 hours for 100 ns). Total for 3 simulations: < EUR 15.
- **Timeline:** 2-3 days
- **Note:** We already have the OpenMM script template (`gpu/scripts/run_md_4ap_smn2.py`). Adapt receptor and ligand inputs.

### 8.3 GEO Dataset Expression Analysis

- **What:** Query existing SMA transcriptomic datasets for CORO1C, UBA1, and NEDD4L expression patterns.
- **Datasets:**
  - GSE138120 (mouse SMA spinal cord, single-cell RNA-seq)
  - GSE161240 (human iPSC-MN, SMA vs. control)
  - GSE150831 (SMA mouse NMJ transcriptomics)
  - GSE3307 (human SMA carrier/patient spinal cord, microarray)
- **Questions:**
  1. Is CORO1C expressed in motor neurons? At what level relative to other actin regulators?
  2. Is CORO1C differentially expressed in SMA vs. wild-type motor neurons?
  3. Does UBA1 expression correlate with disease severity across samples?
  4. Are NEDD4L and TP53 anti-correlated in motor neuron-enriched samples?
- **How:** Use GEO2R (web-based, instant) or download raw counts for reanalysis in R/Python.
- **Cost:** EUR 0
- **Timeline:** 1-2 days

### 8.4 STRING-DB and BioGRID Cross-Referencing

- **What:** Map interaction networks for all key targets (CORO1C, UBA1, SMN1/2, NEDD4L, TP53) to identify shared pathways and unexpected connections.
- **Specific queries:**
  1. Does CORO1C interact with any known 4-AP target (K+ channels KCNA1-6)?
  2. Does UBA1 interact with SMN or CORO1C directly?
  3. Is there a NEDD4L-TP53 interaction in any experimental database?
  4. Does riluzole's known target network (sodium channels, glutamate receptors) overlap with any SMA target network?
- **How:** STRING-DB web API, BioGRID REST API, DrugBank search for riluzole (DB00740).
- **Cost:** EUR 0
- **Timeline:** 1 day

### 8.5 ML Docking Proxy Screen (100,000 Compounds)

- **What:** Use our trained Random Forest docking proxy model to screen 100,000 ZINC drug-like compounds against CORO1C, SMN2, and UBA1.
- **Why:** This provides statistical context. If 4-AP and riluzole remain in the top 1% after a 100K screen, the signal is robust. If they fall to the top 10-20%, the signal may be noise.
- **How:** Generate Morgan fingerprints for ZINC compounds, run through trained RF model, rank by predicted DiffDock confidence.
- **Top hits:** Any compound predicted to score higher than 4-AP (+0.251) or riluzole (+0.201) should be validated with actual DiffDock to check proxy accuracy.
- **Cost:** EUR 0 (runs on CPU, ~10 minutes for 100K compounds)
- **Timeline:** 1 day

### 8.6 Riluzole Literature Mining

- **What:** Systematic PubMed/bioRxiv search for any evidence linking riluzole to SMN biology, ubiquitin pathways, or SMA beyond the Russman 2003 trial.
- **Specific searches:**
  - "riluzole" AND ("SMN" OR "survival motor neuron")
  - "riluzole" AND ("ubiquitin" OR "UBA1" OR "proteasome")
  - "riluzole" AND "spinal muscular atrophy"
  - "riluzole" AND ("protein binding" OR "off-target" OR "polypharmacology")
- **Why:** If there is ANY published evidence connecting riluzole to SMN biology, this dramatically changes the prior probability of our DiffDock prediction being correct. If there is none, the prediction is genuinely novel.
- **Cost:** EUR 0
- **Timeline:** 2-4 hours

### Summary: Computational Validation Checklist

| # | Analysis | Cost | Time | Status |
|---|----------|------|------|--------|
| 8.1 | AutoDock Vina consensus docking | < EUR 1 | 1-2 days | Not started |
| 8.2 | MD pose stability (3 simulations) | < EUR 15 | 2-3 days | Not started |
| 8.3 | GEO expression analysis | EUR 0 | 1-2 days | Not started |
| 8.4 | STRING-DB/BioGRID cross-referencing | EUR 0 | 1 day | Not started |
| 8.5 | ML proxy screen (100K compounds) | EUR 0 | 1 day | Not started |
| 8.6 | Riluzole literature mining | EUR 0 | 2-4 hours | Not started |
| **Total** | | **< EUR 20** | **~1 week** | |

**Recommendation:** Complete all items in Part 8 BEFORE requesting any wet-lab time from collaborators. If computational cross-validation fails (no consensus docking, unstable MD poses, no expression in motor neurons), wet-lab experiments should be deprioritized. If computational validation succeeds, the combined evidence package (DiffDock + Vina consensus + stable MD + expression data) makes a substantially stronger case for grant applications and collaborator engagement.

---

## Part 9: The Path to Curing SMA — What It Would Take

### 9.1 Current Therapeutic Landscape

Three drugs are currently approved for SMA, all targeting the SMN pathway:

| Drug | Mechanism | Route | Approval | Limitation |
|------|-----------|-------|----------|------------|
| **Nusinersen** (Spinraza) | ASO, promotes SMN2 exon 7 inclusion | Intrathecal injection (every 4 months) | 2016 | Invasive delivery, does not reach peripheral tissues, ~$750K/year |
| **Risdiplam** (Evrysdi) | Small molecule, promotes SMN2 exon 7 inclusion | Oral (daily) | 2020 | Systemic exposure (off-target splicing effects possible), long-term safety ongoing |
| **Onasemnogene abeparvovec** (Zolgensma) | AAV9 gene therapy delivering SMN1 cDNA | Single IV infusion | 2019 | One-time dosing (no redosing possible), immune response to AAV, ~$2.1M, liver toxicity risk, diminishing effect over years |

**What these drugs share:** All three restore SMN protein — either by modulating SMN2 splicing or by delivering a functional SMN1 gene. This is a validated strategy that has transformed SMA outcomes, particularly when treatment begins early (pre-symptomatic).

**What these drugs do not address:**
- Irreversible motor neuron loss that has already occurred before treatment initiation
- SMN-independent pathological pathways (UBA1 dysregulation, synaptic vesicle defects, mitochondrial dysfunction)
- The continued vulnerability of motor neurons to degeneration despite SMN restoration
- Peripheral organ involvement (heart, liver, pancreas) in severe SMA types

No cure exists. Current therapies are disease-modifying, not curative. Patients on treatment still experience motor neuron decline, albeit more slowly. The unmet need is clear.

### 9.2 What Is Missing for a Cure

A true cure for SMA would likely require a combinatorial approach addressing multiple biological deficits simultaneously:

**1. Complete and sustained SMN restoration**
Current therapies restore SMN partially and require ongoing treatment (except Zolgensma, which may lose efficacy over years due to episomal AAV dilution in dividing cells). A cure would need either permanent genetic correction (e.g., CRISPR-based SMN2-to-SMN1 conversion) or a combination of therapies maintaining SMN above a critical threshold indefinitely.

**2. SMN-independent neuroprotection**
Even with full SMN restoration, motor neurons already damaged may continue to deteriorate. SMN-independent pathways — including UBA1-mediated ubiquitin signaling, actin cytoskeletal dynamics (CORO1C/PLS3 pathway), and mitochondrial function — are disrupted in SMA and may need separate therapeutic intervention. This is where our platform's novel targets (CORO1C, UBA1) become relevant: they represent the first computationally identified candidates for SMN-independent SMA therapy.

**3. Earlier treatment (newborn screening)**
The most impactful intervention for SMA is early diagnosis. Newborn screening programs, now implemented in many countries, identify SMA before symptom onset. Pre-symptomatic treatment with nusinersen or onasemnogene abeparvovec produces near-normal motor outcomes. Expanding newborn screening globally remains a critical public health priority.

**4. Muscle preservation and regeneration**
In patients diagnosed after symptom onset, muscle atrophy is already present. Current therapies protect remaining motor neurons but do not regenerate lost muscle tissue. Future approaches may include muscle-directed therapies (myostatin inhibitors, follistatin) alongside SMN restoration.

**5. Peripheral organ protection**
Severe SMA (Type 0, Type 1 without early treatment) involves cardiac, hepatic, and pancreatic dysfunction. These are not addressed by current CNS-focused therapies. Systemic gene therapy (Zolgensma) or oral drugs (risdiplam) have partial peripheral coverage, but dedicated organ-protective strategies may be needed.

### 9.3 How the SMA Research Platform Contributes

Our platform's contributions are computational. We do not generate experimental data. Our value lies in four areas:

**1. Identifying novel therapeutic targets**
CORO1C and UBA1 are, to our knowledge, the first SMA drug targets identified through AI-driven computational screening rather than traditional hypothesis-driven biology. Whether these predictions survive experimental validation remains to be determined (estimated probability: 15-30% for CORO1C, higher for UBA1 given established literature). If validated, they would represent the first SMN-independent targets amenable to drug repurposing.

**2. Repurposing existing approved drugs**
4-aminopyridine and riluzole are both FDA-approved, generic, and inexpensive. If our binding predictions are correct, these drugs could potentially enter clinical trials for SMA within 2-3 years rather than the 10-15 years required for de novo drug development. This is the fastest possible path to new SMA treatments.

**3. Evidence-based hypothesis ranking**
The platform's 1,263 hypotheses are ranked using a 5-dimensional convergence score calibrated against known outcomes (89.8% concordance with approved drug performance). This means researchers can prioritize the most promising avenues rather than pursuing targets based on intuition alone. The calibration is imperfect — a 10.2% error rate means approximately 1 in 10 highly ranked hypotheses will be wrong — but it is substantially better than the uncalibrated literature review that typically drives research prioritization.

**4. Open-source infrastructure**
The platform is fully open-source (AGPL-3.0), available on GitHub, HuggingFace, and Docker Hub. Any SMA researcher can query our API (174 endpoints), download our datasets, or extend the platform with their own data. This is a deliberate design choice: SMA affects ~1 in 10,000 births, and the research community is small. Open collaboration is not optional — it is necessary for progress.

### 9.4 Realistic Timeline to Impact

The following timeline assumes our computational predictions survive initial validation. Each phase is gated by the previous one.

| Period | Milestone | Prerequisite | Estimated Probability of Reaching This Stage |
|--------|-----------|-------------|---------------------------------------------|
| **2026 Q2-Q3** | Complete computational validation (Part 8) | None | 95% (these are computational analyses we control) |
| **2026 Q3-Q4** | SPR binding confirmation for top 3 predictions (4-AP/CORO1C, riluzole/SMN2, top UBA1 compound) | Collaborator engagement, EUR 10-15K funding | 70% (dependent on collaborator timeline) |
| **2026 Q4 - 2027 Q2** | Functional validation in iPSC-MNs (if SPR positive) | Positive SPR result for at least 1 target | 15-30% (dependent on binding confirmation) |
| **2027 Q2 - 2028 Q2** | SMA mouse model studies (if iPSC-MN effects confirmed) | Positive functional data, EUR 20-35K grant | 10-20% (compound probability of all prior gates) |
| **2028 - 2030** | Investigator-initiated clinical trial design (if mouse model positive) | Positive mouse data, grant funding, regulatory consultation | 5-10% |
| **2030+** | Combinatorial therapy trials: SMN restoration + CORO1C/UBA1 modulation | All prior stages validated, IND approval | 2-5% |

**Interpretation of probabilities:** The overall probability that our computational predictions lead to a clinical trial is low (estimated 2-10%). This is not unusual in computational drug discovery — the vast majority of in silico predictions do not survive experimental validation. The probabilities above are honest and are stated to prevent overinterpretation of computational results.

**What makes this worthwhile despite low probability:** The investment required for initial validation is small (EUR 4,000-15,000 for SPR, EUR 500-1,500 for riluzole/SMN2 splicing RT-PCR), the drugs are already approved (eliminating years of safety testing), and SMA currently has no cure. The expected value calculation — (probability of success) x (magnitude of impact) / (cost to test) — favors proceeding for all three top predictions.

### 9.5 What Researchers Can Do Today

Concrete, low-cost experiments that any SMA laboratory can perform immediately:

| Experiment | What It Tests | Cost | Time | Required Expertise |
|-----------|---------------|------|------|--------------------|
| SPR: 4-AP vs. CORO1C | Does 4-AP physically bind CORO1C? | EUR 3-5K | 4-6 weeks | Protein biochemistry, SPR facility |
| IHC: CORO1C in SMA mouse spinal cord | Is CORO1C expressed in motor neurons? Does expression change in SMA? | EUR 1-2K | 2-3 weeks | SMA mouse model, histology |
| RT-PCR: riluzole effect on SMN2 splicing | Does riluzole alter SMN2 exon 7 inclusion in SMA fibroblasts? | EUR 500 | 2 weeks | Cell culture, RT-PCR (routine) |
| Western: riluzole effect on SMN protein | Does riluzole increase full-length SMN protein? | EUR 1K | 2 weeks | Cell culture, Western blot (routine) |
| UBA1 activity: riluzole + CHEMBL1301743 | Do the top UBA1 hits modulate E1 enzyme activity? | EUR 3-5K | 4-6 weeks | Enzymology |
| API query | Search our platform for any target of interest | EUR 0 | Minutes | API access (public) |

**The riluzole/SMN2 splicing experiment (EUR 500, 2 weeks) is the single highest-value experiment in this plan** on a cost-per-information basis. It requires only SMA patient fibroblasts (available from Coriell Institute), riluzole (Sigma-Aldrich, ~EUR 30), and standard RT-PCR — reagents and equipment available in virtually any molecular biology laboratory. A positive result would be immediately publishable and would justify a larger investigation.

### 9.6 Limitations of This Analysis

This section would be incomplete without stating what we cannot do and what we do not know:

1. **Computational predictions are not evidence.** DiffDock confidence scores are not binding affinities. Until SPR or equivalent biophysical data exists, all predictions in this document are hypotheses.

2. **The platform has no experimental capability.** We generate hypotheses; others must test them. This creates a dependency on collaborator engagement and funding that we do not control.

3. **DiffDock's accuracy on small molecules is limited.** The PoseBusters benchmark shows ~38% top-1 accuracy for DiffDock v2. Small molecules like 4-AP (MW 94) are particularly prone to false positives due to limited interaction surfaces.

4. **We have not yet validated any prediction experimentally.** Zero of our computational findings have been confirmed in the lab. The track record of this specific platform is therefore unknown.

5. **Repurposing approved drugs for rare diseases is commercially unattractive.** 4-AP and riluzole are generic drugs with no patent protection for SMA use. Pharmaceutical companies have little financial incentive to fund SMA trials for these drugs. Progress will depend on academic grants, patient organizations, and investigator-initiated trials.

6. **SMA pathobiology is complex and not fully understood.** Our platform models known biology. Unknown mechanisms — including those not represented in PubMed or bioRxiv — are invisible to our analysis. The most important therapeutic mechanism for SMA may not yet have been published.

---

## Appendix A: Reagent and Resource List

| Resource | Catalog/Source | Estimated Cost |
|----------|---------------|---------------|
| Recombinant CORO1C (human, His-tag) | Custom expression (E. coli or insect cell) | EUR 1,500-2,500 |
| 4-aminopyridine, >99% | Sigma-Aldrich A78403 | EUR 30 |
| SPR CM5 sensor chip | Cytiva (GE Healthcare) BR100530 | EUR 300-500 |
| Anti-CORO1C antibody | Abcam ab96524 or Proteintech 14749-1-AP | EUR 350-400 |
| Anti-ChAT antibody | Millipore AB144P | EUR 350 |
| Alexa Fluor 488-phalloidin | Thermo Fisher A12379 | EUR 200 |
| SMA patient iPSCs | Coriell Institute (GM03813 or similar) | EUR 500-1,000 |
| SMN-delta-7 mice | Jackson Lab #005025 | EUR 2,000-4,000 (breeding colony) |
| CHEMBL1331875 (UBA1 compound) | Custom synthesis or Mcule | EUR 200-500 |
| Recombinant UBA1 | R&D Systems E-305 or Ubiquigent | EUR 500-800 |
| FITC-SMN1(289-294) peptide | Custom synthesis (GenScript or Thermo) | EUR 300-500 |
| Riluzole, >98% | Sigma-Aldrich R116 (MW 234.2) | EUR 30-50 |
| Recombinant SMN protein (human, His-tag) | Custom expression (E. coli or insect cell) | EUR 1,500-2,500 |
| Anti-SMN antibody | BD Transduction 610646 | EUR 350-400 |
| SMA patient fibroblasts | Coriell Institute (GM03813) | EUR 300-500 |
| CHEMBL1301743 (UBA1 compound) | Custom synthesis or Mcule | EUR 200-500 |
| Pemirolast (UBA1 compound) | Sigma-Aldrich or Cayman Chemical | EUR 50-100 |
| Risdiplam (positive control) | MedChemExpress or Selleck Chemicals | EUR 200-400 |

## Appendix B: Key Collaborator Contact Points

| Collaborator | Institution | Expertise | Relevance |
|-------------|-------------|-----------|-----------|
| Prof. a collaborating SMA researcher | Leipzig, Carl-Ludwig-Institute | SMA mouse models, selective vulnerability, proprioception | Discoveries 2, 3, 5; mouse tissue access |
| Prof. Thorsten a biochemistry collaborator | Leipzig University | Bioinformatics, biochemistry | SPR facility, computational cross-validation |
| Prof. Stefan Hallermann | Leipzig, Carl-Ludwig-Institute | Neurophysiology, institute director | Institute resources, funding support |
| Prof. a collaborating SMA genetics group | Cologne, Institute of Human Genetics | SMA genetics, modifier biology, UBA1 | Discoveries 2, 4; iPSC-MN expertise |
| an organoid/NMJ modeling laboratory | MDC Berlin | Organoid/NMJ models, iPSC differentiation | Discovery 1C (functional validation) |
| Prof. an RNA splicing expert | CSHL, New York | RNA splicing, ASO therapeutics | US grant partner (NIH R21) |
| Dr. Ewout Groen | Netherlands SMA Center | Translational SMA, biomarkers | Clinical endpoint design |

---

*This document is version 2.0 (March 21, 2026). Version 1.0 covered the initial 378-compound screen. Version 2.0 incorporates the expanded 4,116-compound campaign results (riluzole/SMN2 discovery, UBA1 druggability confirmation), adds computational validation protocols (Part 8), and includes a strategic assessment of the path toward SMA treatment (Part 9). It will be updated as computational validation results become available and after the collaborator meeting (week of March 30, 2026).*

*All computational predictions described herein are hypotheses, not conclusions. No therapeutic claims are made. The author has SMA and discloses this positionality transparently. This document is intended for scientific discussion with potential collaborators and is not a promotional or clinical document.*
