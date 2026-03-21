# The CORO1C Double-Hit Model of Motor Neuron Vulnerability in SMA

## Summary

This document describes a mechanistic model in which SMN deficiency impairs CORO1C function through two converging mechanisms ("double hit"): (1) loss of splicing fidelity causes CORO1C intron retention, producing less functional mRNA, and (2) compensatory transcriptional upregulation in motor neurons fails to restore sufficient functional CORO1C protein. The net result is reduced F-actin dynamics and impaired endocytosis at motor neuron terminals, contributing to neuromuscular junction degeneration. Each link in this chain is classified below by its evidence status.

---

## 1. The Complete Mechanistic Model

```
SMN1 loss
  |
  v
Reduced SMN protein
  |
  +---> Impaired snRNP biogenesis (especially minor/U12 spliceosome)
  |         |
  |         v
  |     CORO1C intron retention ───────────────────────────── HIT #1
  |         |                                               (less functional
  |         v                                                CORO1C mRNA)
  |     Reduced functional CORO1C protein
  |         |
  +---> Motor neurons sense CORO1C insufficiency
            |
            v
        Compensatory CORO1C transcription increase ────────── HIT #2
            |                                               (insufficient
            v                                                compensation)
        More total CORO1C mRNA, but still intron-retained
            |
            v
        Net deficit of functional CORO1C protein
            |
            +---> Reduced F-actin at cell membrane
            |         |
            |         v
            |     Impaired endocytosis at motor neuron terminals
            |         |
            |         v
            |     Disrupted vesicle recycling at NMJ
            |     Impaired TrkB surface translocation
            |     Defective BDNF signaling
            |
            +---> Impaired growth cone dynamics
            |         |
            |         v
            |     Axonal outgrowth defects
            |     Aberrant axon branching
            |
            v
        Motor neuron degeneration + NMJ loss
```

### Why "double hit"?

Most models of SMA downstream targets describe a single consequence of SMN loss. The CORO1C model is distinct because the same upstream deficiency (low SMN) creates both a post-transcriptional defect (intron retention from impaired splicing) and renders the cell's own compensatory response ineffective (upregulated transcription still feeds through a broken splicing pipeline). The motor neuron is caught in a futile cycle.

---

## 2. Evidence for Each Link

### 2.1 SMN Loss Causes Widespread Intron Retention

**Status: PROVEN**

| Evidence | Source | Confidence |
|----------|--------|------------|
| SMN deficiency causes widespread intron retention, particularly of minor U12 introns, in the spinal cord | PMID:28270613 (Jangi et al.) | 0.95 |
| Widespread intron retention and DNA damage markers observed in SMN-depleted iPSC-derived motor neurons | GSE108094 | 0.93 |
| Same phenotype in human SH-SY5Y neuroblastoma cells | PMID:28270613 | 0.93 |
| Intron retention concomitant with p53 pathway induction and DNA damage response | DB claim | 0.92 |
| Therapeutic ASO rescues intron retention phenotype in SMA model | DB claim | 0.88 |
| U snRNAs belonging to minor spliceosomes are markedly reduced in SMA CNS tissue | DB claim | 0.93 |
| U12 splicing dysfunction contributes to synaptic deafferentation and motor circuit pathology | DB claim | 0.92 |
| Intron retention confirmed in C. elegans SMA model | PMID:41324485 | -- |

**Mechanism**: SMN is a core component of the snRNP assembly complex (confidence 0.98). SMN deficiency reduces assembly of both major (U2-dependent) and minor (U12-dependent) spliceosomal snRNPs (confidence 0.98). Minor introns are preferentially affected because their cognate snRNPs (U11, U12, U4atac, U6atac) are less abundant at baseline.

### 2.2 CORO1C Shows Intron Retention Under SMN Loss

**Status: DEMONSTRATED in transcriptomic data; not yet validated at the individual gene level by targeted assay**

| Evidence | Source | Confidence |
|----------|--------|------------|
| CORO1C intron retention detected in SMN-deficient spinal cord | GSE87281 (inducible SMA mouse, bulk RNA-seq) | FDR = 1.5e-71 |
| Intron retention is a genome-wide effect particularly affecting U12 introns | PMID:28270613 | 0.95 |

**What is proven**: The GSE87281 dataset (bulk RNA-seq of inducible SMA mouse spinal cord) shows CORO1C intron retention at FDR = 1.5e-71, a statistically strong signal. This is consistent with the established genome-wide intron retention phenotype.

**What remains hypothesized**: Whether CORO1C intron retention specifically occurs in motor neurons (vs. other spinal cord cell types), whether the retained intron triggers nonsense-mediated decay or produces a truncated protein, and whether the degree of intron retention is sufficient to meaningfully reduce functional CORO1C protein below a critical threshold.

### 2.3 Motor Neurons Upregulate CORO1C Transcription (Compensation)

**Status: OBSERVED in two independent datasets; mechanism hypothesized**

| Evidence | Source | Confidence |
|----------|--------|------------|
| Increased CORO1C mRNA levels in SMA iPSC-derived motor neurons | GSE69175 (patient-derived iPSC motor neurons, RNA-seq) | -- |
| Increased CORO1C expression in SMA mouse model | Mouse model data (cross-referenced) | -- |
| General compensatory sprouting occurs in SMA motor units | DB claim (Smn+/- mice) | 0.93-0.98 |
| CNTF is necessary for motor axon sprouting in Smn+/- mice | DB claim | 0.97 |

**What is proven**: Two independent datasets (one human iPSC-derived, one mouse) show elevated CORO1C transcript levels in SMA motor neurons compared to controls.

**What remains hypothesized**: Whether this represents a directed compensatory response to CORO1C protein insufficiency (e.g., via a feedback loop sensing F-actin or endocytic flux), or whether it is a non-specific consequence of the broader transcriptional dysregulation in SMA motor neurons. The transcription factor(s) driving upregulation are unknown.

### 2.4 Compensation Is Insufficient: Net Deficit of Functional CORO1C

**Status: HYPOTHESIZED, consistent with available data but not directly measured**

The core logic: if CORO1C mRNA is upregulated (2.3) but much of it carries retained introns (2.2), the net output of functional protein could still be reduced. This is the defining feature of the double-hit model.

**Supporting indirect evidence**:
- CORO1C overexpression rescues SMA phenotypes (section 2.5), implying endogenous levels are insufficient
- PLS3 overexpression restores endocytosis in SMA cells (PMID:27499521), suggesting the endocytic pathway is genuinely impaired despite any compensation
- SMN loss causes measurable F-actin organizational defects in neurons (DB claim, 0.15)
- Smn deficiency impairs F-actin-dependent translocation of TrkB to cell surface (DB claim, 0.15)

**What has not been measured**: Functional CORO1C protein levels (Western blot) in SMA motor neurons vs. controls. The ratio of intron-retained to correctly spliced CORO1C transcripts specifically in motor neurons. Whether the intron-retained CORO1C transcript undergoes NMD or produces a dominant-negative product.

### 2.5 CORO1C Overexpression Rescues SMA Phenotypes

**Status: PROVEN in zebrafish and cell models**

| Evidence | Source | Confidence |
|----------|--------|------------|
| CORO1C overexpression rescues axonal truncation and branching phenotype in Smn-depleted zebrafish | PMID:27499521 | 0.15 (DB) |
| CORO1C overexpression restores fluid-phase endocytosis in SMN-knockdown cells by elevating F-actin amounts | PMID:27499521 | 0.15 (DB) |
| Overexpression of PLS3 and CORO1C rescues endocytosis in SMA models | PMID:27499521 | 0.15 (DB) |
| CORO1C is a protective modifier identified through PLS3 interactome interrogation | PMID:27499521 | 0.15 (DB) |

Note: The low confidence scores (0.15) in our database reflect that these claims come from a single publication. The experimental data within that publication are robust (zebrafish rescue is a direct functional demonstration), but independent replication by other groups has not been published.

### 2.6 CORO1C Functions in the PLS3-Endocytosis Axis

**Status: PROVEN biochemically and functionally**

| Evidence | Source | Confidence |
|----------|--------|------------|
| CORO1C is an F-actin binding protein whose direct binding to PLS3 is calcium-dependent | PMID:27499521 | 0.15 (DB) |
| PLS3 counteracts reduced F-actin levels in SMA by restoring impaired endocytosis and calcium homeostasis | DB claim | 0.15 |
| Endocytic pathways are perturbed at motor neuron synapses in SMN-deficient organisms | DB claim | 0.97 |
| Decreased SMN levels reduce endocytosis-dependent infection by JCPyV | DB claim | 0.93 |
| Conserved cellular pathways of endocytosis are critical genetic modifiers of SMN loss across species | DB claim | 0.85 |
| PLS3 overexpression restores endocytosis to normal levels in SMA cells | DB claim | 0.15 |
| CHP1 reduction ameliorates SMA by restoring calcineurin activity and endocytosis | PMID:29961886 | -- |
| NCALD suppression restores impaired endocytosis across species | PMID:28132687 | -- |

**CORO1C function (UniProt Q9ULV4)**: 474 amino acids. Regulates activation and subcellular location of RAC1. Increases activated RAC1 at the leading edge of migrating cells. Involved in directed cell migration, cell proliferation, and endocytosis. Keywords: actin-binding, cell membrane, cytoskeleton, endosome.

### 2.7 The Endocytosis-NMJ Connection

**Status: PROVEN that endocytic defects contribute to NMJ pathology; HYPOTHESIZED that CORO1C specifically mediates this in SMA**

| Evidence | Source | Confidence |
|----------|--------|------------|
| Loss of NMJs represents an early and significant event in SMA pathogenesis | DB claim | 0.98 |
| Synaptic dysfunction of NMJs precedes motor neuron cell death | DB claim | 0.95 |
| Decreased SMN levels result in changes in synaptic endocytic proteins | DB claim | 0.94 |
| Increased SMN expression in motor neurons prevents synaptic dysfunction at NMJ | DB claim | 0.96 |
| F-actin bundling is required for proper translocation of transmembrane proteins at the cell surface in motoneurons | DB claim | 0.15 |
| F-actin-dependent TrkB translocation to cell surface is disturbed in Smn-deficient motor axon terminals | DB claim | 0.15 |
| PLS3 rescues TrkB cell surface translocation and activation in SMA | PMID:36607273 | -- |
| PLS3 rescues BDNF-TrkB signaling in SMA | PMID:36786833 | -- |

---

## 3. Relationship to Other SMA Modifiers

The CORO1C double-hit model does not stand alone. It fits within a broader network of actin-endocytosis modifiers:

| Modifier | Mechanism | Interaction with CORO1C |
|----------|-----------|------------------------|
| **PLS3** (Plastin 3) | F-actin bundling, endocytosis restoration | Direct binding partner (calcium-dependent). PLS3 interactome screen identified CORO1C. Both rescue endocytosis independently. |
| **NCALD** (Neurocalcin Delta) | Calcium sensor; reduction restores endocytic flux | Convergent pathway. NCALD and CORO1C both modulate calcium-dependent actin dynamics. Reduction of NCALD ameliorates SMA across species (PMID:28132687). |
| **CHP1** (Calcineurin-like EF-hand Protein 1) | Calcineurin regulation; reduction restores endocytosis | Parallel pathway. CHP1 reduction restores endocytosis via calcineurin (PMID:29961886). |
| **PFN2** (Profilin 2) | Actin monomer binding, cytoskeleton modulation | Both PFN2 and CORO1C modulate actin dynamics in motor neurons. PFN2 listed as SMA modifier gene. Profilin-1 is elevated in SMA type 3 CSF. |
| **4-AP** (4-aminopyridine) | K+ channel blocker, increases neuronal activity | 4-AP restores synaptic connectivity and NMJ function (confidence 0.90-0.92). 4-AP's mechanism (neuronal activity) is upstream of endocytosis; increased activity drives synaptic vesicle cycling. Potential synergy with CORO1C pathway. |
| **HDAC inhibitors** (e.g., valproic acid) | Chromatin remodeling, SMN2 expression increase | HDAC inhibitors ameliorate SMA in mouse models (confidence 0.95). Could potentially increase CORO1C transcription. No direct CORO1C connection published. |

---

## 4. Therapeutic Intervention Points

The double-hit model identifies five distinct points where intervention could restore CORO1C function or bypass its deficiency:

### 4.1 Restore Splicing (Fix Hit #1)

**Target**: The intron retention defect upstream of CORO1C.

**Approaches**:
- **SMN restoration** (nusinersen, risdiplam, onasemnogene): Already approved. Restoring SMN should restore snRNP assembly, reduce intron retention, and thereby increase correctly spliced CORO1C. This is the most validated approach but addresses all downstream effects, not CORO1C specifically.
- **Minor snRNA gene delivery**: Virus-mediated delivery of minor snRNA genes improves U12 splicing defects in SMA cells and spinal cord (DB claim, 0.95). Could specifically rescue CORO1C intron retention.
- **CORO1C-specific splice-switching ASO**: A targeted antisense oligonucleotide designed to mask the cryptic splice site or promote correct splicing of CORO1C introns.

### 4.2 Boost Compensation (Amplify Hit #2 Response)

**Target**: The transcriptional upregulation machinery for CORO1C.

**Approaches**:
- **HDAC inhibitors**: Could potentially increase CORO1C transcription (as they increase SMN2 transcription). Untested for CORO1C specifically.
- **Transcription factor identification**: Once the TF(s) driving CORO1C upregulation are identified, these could be targeted to amplify the compensatory response.
- **mRNA stabilization**: Small molecules or ASOs that stabilize correctly spliced CORO1C mRNA, increasing the fraction of functional transcript.

### 4.3 Direct CORO1C Supplementation (Bypass Both Hits)

**Target**: CORO1C protein levels directly.

**Approaches**:
- **AAV-mediated CORO1C gene therapy**: Deliver a codon-optimized, intronless CORO1C cDNA under a motor neuron-specific promoter. Bypasses both the splicing defect and transcriptional regulation entirely.
- **CORO1C protein delivery**: Challenging due to protein size (474 aa) and intracellular target. Less feasible than gene delivery.

### 4.4 Restore F-Actin / Endocytosis Downstream (Bypass CORO1C Entirely)

**Target**: The functional consequences of CORO1C deficiency.

**Approaches**:
- **PLS3 overexpression**: Proven to restore endocytosis and F-actin in SMA models. ASO-mediated PLS3 upregulation combined with low-dose SMN-ASO shows benefit (PMID:35724821).
- **NCALD reduction**: ASO-mediated NCALD knockdown restores endocytic flux (PMID:28132687). Combined NCALD-ASO + SMN-ASO shows additive benefit in severe SMA mice.
- **CHP1 reduction**: Restores calcineurin activity and endocytosis (PMID:29961886).
- **F-actin stabilizers**: Compounds like Bis-T-23 that directly stabilize F-actin filaments.

### 4.5 Combination Strategies

The model suggests that combining SMN restoration (partially fixing Hit #1) with an endocytosis-pathway modifier (compensating for residual Hit #2) could produce additive or synergistic benefit. Specific combinations to consider:

- **Low-dose nusinersen/risdiplam + PLS3 upregulation**: Addresses both splicing defect and downstream actin dynamics.
- **SMN-ASO + NCALD-ASO**: Already shown additive benefit at 3 months in severe SMA mice.
- **4-AP + SMN restoration**: 4-AP restores synaptic connectivity (confidence 0.92); SMN restoration fixes the splicing defect. Combined 4-AP + p53 inhibition already shows additive effects.

---

## 5. Proposed Experiments to Test Each Link

### Experiment 1: Quantify CORO1C intron retention specifically in motor neurons

**Tests link**: 2.2 (CORO1C intron retention under SMN loss) and 2.3 (cell-type specificity)

**Approach**: Single-cell or single-nucleus RNA-seq of SMA mouse spinal cord (GSE208629 may already contain this data), computationally isolating motor neurons. Alternatively, TRAP (Translating Ribosome Affinity Purification) using ChAT-Cre;TRAP mice crossed with SMA mice to isolate motor neuron-specific transcripts, followed by RT-PCR with primers flanking CORO1C introns.

**Readout**: Fraction of intron-retained vs. correctly spliced CORO1C transcripts in motor neurons vs. other cell types.

**Expected result if model is correct**: Motor neurons show higher intron-retained fraction of CORO1C than astrocytes or interneurons, despite higher total CORO1C transcript levels.

### Experiment 2: Measure functional CORO1C protein in SMA motor neurons

**Tests link**: 2.4 (net functional protein deficit)

**Approach**: Western blot of CORO1C in iPSC-derived motor neurons from SMA patients vs. controls (isogenic corrected lines preferred). Include both total CORO1C antibody and phospho-CORO1C (active form) if antibody available. Complement with immunofluorescence showing subcellular localization at growth cones and synapses.

**Readout**: Total CORO1C protein level, ratio of full-length to truncated forms (if intron retention produces truncated protein), and subcellular localization pattern.

**Expected result if model is correct**: Reduced functional CORO1C protein despite elevated mRNA. Possible truncated forms detectable.

### Experiment 3: Determine fate of intron-retained CORO1C transcript

**Tests link**: 2.2 and 2.4 (mechanism of protein reduction)

**Approach**:
- Cycloheximide chase + qRT-PCR: If intron-retained transcript undergoes NMD, cycloheximide (NMD inhibitor) treatment should increase intron-retained CORO1C mRNA levels in SMA cells.
- Ribosome profiling (Ribo-seq): Determine whether intron-retained CORO1C mRNA is translated at all.
- Minigene reporter: Clone CORO1C with and without the retained intron(s) into a reporter construct. Measure protein output.

**Readout**: Whether intron-retained CORO1C is degraded by NMD, translated into truncated protein, or sequestered in the nucleus.

### Experiment 4: Identify the compensatory transcription mechanism

**Tests link**: 2.3 (compensation mechanism)

**Approach**:
- ATAC-seq of CORO1C locus in SMA vs. control motor neurons to identify differential chromatin accessibility.
- CUT&RUN or ChIP-seq for candidate transcription factors at the CORO1C promoter.
- CRISPR interference screen of transcription factors in SMA motor neurons, measuring CORO1C mRNA as readout.

**Readout**: Identification of the transcription factor(s) and enhancer(s) driving CORO1C upregulation in SMA motor neurons.

### Experiment 5: Test CORO1C rescue in mammalian SMA model

**Tests link**: 2.5 (therapeutic potential in mammals, extending zebrafish data)

**Approach**: AAV9-mediated delivery of codon-optimized CORO1C cDNA (no introns) under Synapsin or ChAT promoter, injected IV at P1 into severe SMA mice (SMNΔ7 or Smn2B/-). Compare to GFP control and to sub-therapeutic dose of SMN-ASO.

**Readout**: Survival, motor function (righting reflex, grip strength), NMJ innervation (whole-mount NMJ staining), motor neuron counts.

**Expected result if model is correct**: CORO1C delivery alone provides partial rescue (not as complete as full SMN restoration, because CORO1C is one of many SMN-dependent targets). CORO1C delivery + low-dose SMN-ASO provides additive benefit.

### Experiment 6: Test whether intron retention is the causal mechanism

**Tests link**: 2.2 (causality, not just correlation)

**Approach**: CRISPR-mediate removal of the specific intron(s) that show retention in CORO1C from iPSC-derived SMA motor neurons (creating an "intron-deleted" CORO1C allele that cannot undergo intron retention). Alternatively, design a splice-switching ASO targeting the CORO1C retained intron.

**Readout**: Does preventing CORO1C intron retention (without restoring SMN) rescue F-actin dynamics and endocytosis in motor neurons?

**Expected result if model is correct**: Partial rescue of endocytic defects, demonstrating that CORO1C intron retention is a functionally significant downstream consequence of SMN loss.

### Experiment 7: Test CORO1C in the 4-AP synergy model

**Tests link**: Section 3 (relationship to other modifiers)

**Approach**: Combine 4-AP treatment (which restores neuronal activity and synaptic connectivity) with CORO1C delivery in SMA mice. 4-AP increases vesicle cycling demand; CORO1C restores the endocytic machinery needed to meet that demand.

**Readout**: NMJ function (electrophysiology), proprioceptive synapse number, motor behavior.

**Expected result if model is correct**: Synergistic rather than merely additive benefit, because 4-AP and CORO1C target complementary bottlenecks in the same synaptic recycling pathway.

### Experiment 8: Temporal dynamics of the double hit

**Tests link**: 2.2 and 2.3 (timing of intron retention vs. compensatory upregulation)

**Approach**: Time-course RNA-seq in the inducible SMA mouse model (GSE87281 source), sampling spinal cord at days 1, 3, 5, 7, and 10 after SMN depletion. Quantify CORO1C total expression and intron retention index at each time point.

**Readout**: Does intron retention precede compensatory upregulation? Is there a window where compensation is effective before intron retention overwhelms it?

**Expected result if model is correct**: Intron retention appears first (within 1-3 days), compensatory upregulation follows (3-5 days), and the ratio of functional/total CORO1C declines progressively despite rising total mRNA.

---

## 6. What Is Proven vs. Hypothesized

### Proven

1. SMN deficiency causes widespread intron retention, particularly of U12 introns, in the spinal cord (multiple labs, multiple species).
2. CORO1C shows intron retention in SMN-deficient spinal cord at FDR = 1.5e-71 (GSE87281).
3. CORO1C transcript levels are elevated in SMA motor neurons relative to controls (GSE69175, mouse model).
4. CORO1C overexpression rescues axon morphology in Smn-depleted zebrafish (PMID:27499521).
5. CORO1C overexpression restores endocytosis in SMN-knockdown cells (PMID:27499521).
6. CORO1C binds PLS3 in a calcium-dependent manner (PMID:27499521).
7. Endocytosis is impaired at motor neuron synapses in SMA (multiple lines of evidence, confidence 0.85-0.97).
8. NMJ degeneration is an early event in SMA, preceding motor neuron death (confidence 0.95-0.98).
9. PLS3, NCALD, and CHP1 modulate endocytosis and modify SMA severity (multiple publications).

### Hypothesized (constituting the "double-hit" model)

1. CORO1C intron retention reduces functional CORO1C protein specifically in motor neurons (not directly measured at protein level).
2. The transcriptional upregulation of CORO1C is a directed compensatory response (could be non-specific dysregulation).
3. The compensatory upregulation is insufficient because new transcripts also undergo intron retention (logical inference, not experimentally tested).
4. The CORO1C protein deficit is a functionally significant contributor to motor neuron vulnerability (as opposed to one of many minor downstream effects of splicing disruption).
5. The double-hit mechanism (futile compensation cycle) distinguishes CORO1C from other intron-retention targets that do not show compensatory upregulation.
6. CORO1C supplementation would provide therapeutic benefit in mammalian SMA models (only demonstrated in zebrafish and cell culture so far).

### Unknown

1. Which specific CORO1C intron(s) are retained and whether they contain U12-type splice sites.
2. Whether intron-retained CORO1C mRNA undergoes NMD, nuclear retention, or aberrant translation.
3. The transcription factor(s) driving CORO1C compensatory upregulation.
4. CORO1C protein levels in SMA motor neurons (no published Western blot data).
5. Whether CORO1C intron retention is cell-type specific within the spinal cord.
6. Whether the double-hit pattern (intron retention + compensatory upregulation) applies to other actin-binding proteins in SMA.
7. The therapeutic window for CORO1C intervention relative to disease onset.

---

## 7. Key References

### Primary CORO1C-SMA paper
- **PMID:27499521** — "The Power of Human Protective Modifiers: PLS3 and CORO1C Unravel Impaired Endocytosis in Spinal Muscular Atrophy and Rescue SMA Phenotype." Source of zebrafish rescue, endocytosis restoration, and PLS3-CORO1C interaction data.

### Intron retention in SMA
- **PMID:28270613** — "SMN deficiency in severe models of spinal muscular atrophy causes widespread intron retention and DNA damage." Established the link between SMN loss and genome-wide intron retention.
- **PMID:27557711** — "RNA-sequencing of a mouse-model of spinal muscular atrophy reveals tissue-wide changes in splicing." Tissue-specific splicing changes including U12 intron retention.
- **PMID:41324485** — Intron retention and exon skipping in C. elegans SMA model. Cross-species conservation.

### Endocytosis pathway in SMA
- **PMID:28132687** — NCALD suppression protects against SMA by restoring endocytosis across species.
- **PMID:29961886** — CHP1 reduction ameliorates SMA by restoring calcineurin activity and endocytosis.
- **PMID:32938453** — Genetic modifiers ameliorate endocytic and neuromuscular defects in SMA model.
- **PMID:38249130** — PLS3 targets cell membrane-associated proteins in motoneurons.
- **PMID:35724821** — Combinatorial ASO-mediated therapy with low dose SMN and PLS3.

### PLS3-actin-SMA axis
- **PMID:36607273** — PLS3 rescues TrkB cell surface translocation and activation in SMA.
- **PMID:36786833** — PLS3 rescues BDNF-TrkB signaling in SMA.
- **PMID:29552580** — PLS3 promotes motor neuron axonal growth and extends survival in SMA mouse model.
- **PMID:34023917** — "Plastin 3 in health and disease: a matter of balance." Review.

### Actin dynamics in SMA
- **PMID:39305126** — "The spinal muscular atrophy gene product regulates actin dynamics."
- **PMID:31927482** — "Splicing Defects of the Profilin Gene Alter Actin Dynamics in an S. pombe SMN Mutant."
- **PMID:39666039** — "Cytoskeleton dysfunction of motor neuron in spinal muscular atrophy." Review.

### SMA modifier genes
- **PMID:28684086** — "Modifier genes: Moving from pathogenesis to therapy." Review covering CORO1C, PLS3, NCALD, and others.

### Datasets in our platform
- **GSE87281** — Bulk RNA-seq of inducible SMA mouse spinal cord. Source of CORO1C intron retention signal (FDR = 1.5e-71).
- **GSE69175** — RNA-seq of patient-derived iPSC motor neurons. Source of CORO1C transcriptional upregulation signal.
- **GSE108094** — Deep RNA-seq of SMA motor neurons with altered splicing data.
- **GSE208629** — Single-cell RNA-seq of severe SMA mouse spinal cord. Potential source for cell-type resolution.
- **GSE65470** — NMJ-focused transcriptomics in SMA context.

---

## 8. Platform Database Evidence Summary

Our SMA Research Platform contains:
- **9 direct CORO1C claims** (all from PMID:27499521, the only dedicated CORO1C-SMA publication)
- **10 intron retention claims** (confidence 0.88-0.95)
- **10 endocytosis claims** (confidence 0.85-0.97)
- **10 F-actin claims** (confidence 0.15-0.95)
- **10 NMJ claims** (confidence 0.95-0.99)
- **10 growth cone claims** (confidence 0.80-0.96)
- **8 NCALD claims** (confidence 0.15)
- **10 U12/minor spliceosome claims** (confidence 0.15-0.98)
- **2 platform hypotheses for CORO1C**: Protein Interaction (confidence 0.95) and Neuroprotection (confidence 0.93)
- **5 GEO datasets** relevant to the model

The model synthesizes across all of these evidence categories. No single category alone establishes the double-hit mechanism; the model emerges from the convergence of splicing biology, transcriptomics, and functional rescue data.

---

## 9. Limitations and Alternative Interpretations

1. **Single-source CORO1C data**: All direct CORO1C-SMA evidence comes from one group (PMID:27499521). Independent replication is needed.

2. **Correlation vs. causation for intron retention**: CORO1C intron retention in GSE87281 is correlative. Many genes show intron retention in SMA; CORO1C may not be functionally significant among them.

3. **Transcriptional upregulation may not be compensatory**: The elevated CORO1C mRNA in GSE69175 could reflect a stress response, cell-type composition change (surviving motor neurons may express more CORO1C at baseline), or a technical artifact of comparing iPSC-derived cells.

4. **Zebrafish rescue does not prove the double-hit mechanism**: CORO1C overexpression rescuing zebrafish SMA proves CORO1C is sufficient to ameliorate symptoms, not that endogenous CORO1C deficit is the cause. The rescue could work by compensating for a different pathway entirely.

5. **The model assumes motor neuron cell-autonomy**: CORO1C deficiency in surrounding cells (astrocytes, Schwann cells, muscle) could also contribute. The current data do not distinguish cell-autonomous from non-cell-autonomous effects.

6. **Therapeutic relevance is uncertain**: Even if the model is correct, CORO1C may be one of many targets with individually small effect sizes. The practical question is whether CORO1C-targeted intervention provides meaningful benefit beyond existing SMN-restoring therapies.

---

*Document generated 2026-03-21. Based on SMA Research Platform database (25,054 claims, 515 hypotheses) and PubMed literature search.*
