# Slide Outline v4: Simon Meeting -- Week of March 30, 2026

**Presenter**: Christian Fischer
**Audience**: Prof. Christian Simon (+ possibly Prof. Schoeneberg, Prof. Hallermann)
**Duration**: ~30 min presentation + 30 min discussion
**Format**: 20 slides max
**Tone**: Scientific, evidence-first, honest about limitations, collaboration-oriented
**PRIVATE DOCUMENT -- NOT FOR GITHUB**

---

## Slide 1: Title

**Title**: SMA Research Platform: Single-Cell Findings and the ROCK-LIMK2-CFL2 Therapeutic Axis
**Subtitle**: Update for Prof. Simon -- What Changed Since March 20
**Footer**: sma-research.info | Christian Fischer | March 2026
**Key message**: This is an update meeting, not a first introduction.

---

## Slide 2: What Simon Told Us (March 20 Feedback)

**Title**: Your Feedback Shaped Our Analysis
**Content**:
- "Where is the mouse data?" --> We analyzed GSE208629 (SMA mouse scRNA-seq)
- "p53 gap" --> p53/motor neuron death literature ingested
- "Claims are confusing" --> Frontend cleaned, human-readable summaries
- "I want to chat with it" --> Interactive modules improved
- **And beyond**: We went further -- single-cell resolution, cross-species, cross-disease

**Key message**: We listened. And the data took us somewhere unexpected.
**Source**: Meeting notes, March 20 2026

---

## Slide 3: Platform Growth at a Glance

**Title**: Platform Scale: March 20 vs March 24
**Content**: Side-by-side comparison table

| Metric | March 20 | Now |
|--------|----------|-----|
| Evidence claims | ~10,000 | 14,855 |
| Sources | ~4,000 | 7,367 |
| Targets | 48 | 68 |
| Hypotheses | ~800 | 1,476+ |
| Compounds screened | ~5,000 | 21,229 |
| Single-cell datasets | 0 | **2** |

**Key message**: Scale matters, but the single-cell data is the real advance.
**Source**: Platform database stats

---

## Slide 4: Our Original Finding -- The 7-Gene Actin Network

**Title**: Starting Point: Coordinated Actin Pathway Upregulation in SMA
**Content**:
- 7 actin genes co-upregulated in SMA motor neurons (GSE69175, iPSC-derived)
- PLS3 (4.0x), CFL2 (2.9x), ACTR2 (1.8x), ACTG1 (1.6x), CORO1C (1.6x), ABI2 (1.5x), PFN2 (1.5x)
- STRING enrichment: "Actin cytoskeleton organization" FDR = 2.1e-07
- Network density 0.76 (functional module)

**Key message**: This was the bulk RNA-seq finding. But which of these genes actually matter in motor neurons?
**Source**: GSE69175, STRING analysis

---

## Slide 5: Question -- Is This Motor Neuron-Specific?

**Title**: The Question That Changed Everything
**Content**:
- Bulk RNA-seq cannot distinguish cell types
- iPSC cultures are not in vivo tissue
- We needed single-cell data from actual spinal cord
- **Two datasets analyzed**: GSE287257 (human ALS, 61,664 cells) + GSE208629 (mouse SMA, 39,136 cells)

**Key message**: Transition slide -- setting up the single-cell results.
**Source**: N/A (conceptual)

---

## Slide 6: Human Spinal Cord -- Motor Neuron Enrichment (GSE287257)

**Title**: Which Actin Genes Are Motor Neuron-Specific?
**Content**: Bar chart showing MN enrichment (log2FC) for each gene

| Gene | MN Enrichment | p-value |
|------|---------------|---------|
| PFN2 | +1.22 (7.6x) | 5.3e-18 |
| LIMK1 | +1.20 (2.3x) | 8.4e-24 |
| CFL2 | +0.59 (1.5x) | 7.1e-07 |
| ACTG1 | +0.67 | 6.1e-11 |
| CORO1C | +0.10 | 6.9e-03 |

**Key message**: PFN2 and LIMK1 are the MN-enriched actin genes. CORO1C is not.
**Source**: GSE287257, 240 motor neurons, snRNA-seq
**Visual**: Horizontal bar chart, CORO1C bar in grey to emphasize its low enrichment

---

## Slide 7: CORO1C Reinterpretation -- Honesty Slide

**Title**: We Were Wrong About CORO1C
**Content**:
- Previously framed as cross-disease motor neuron target
- Single-cell reality: highest in endothelial (0.60) and microglia (0.57)
- Motor neurons: 0.41 (middle of the pack)
- ALS upregulation is pan-cellular (p=1.0e-30), NOT motor neuron-specific (p=0.52)
- **New framing**: neuroinflammation biomarker, not therapeutic target

**Key message**: The data corrected us. This is how science should work.
**Source**: GSE287257, cell-type expression analysis

---

## Slide 8: Mouse SMA -- Massive Actin Stress Response (GSE208629)

**Title**: 10 of 14 Actin Genes Upregulated in SMA Motor Neurons
**Content**: Heatmap or table showing SMA vs Control MNs

| Gene | log2FC | p-value |
|------|--------|---------|
| Limk2 | +2.81 | 0.002 |
| Actg1 | +2.56 | 4.0e-14 |
| Actr2 | +2.21 | 3.3e-06 |
| Pls3 | +2.12 | 0.01 |
| Cfl2 | +1.83 | 2.1e-04 |
| Rock2 | +1.06 | 0.014 |
| Rock1 | +0.65 | 0.044 |

**Key message**: SMA motor neurons mount a coordinated actin stress program. This is pathway-level, not single-gene noise.
**Source**: GSE208629, 17 SMA MNs vs 191 control MNs (Smn-/- mouse)
**Caveat on slide**: "n=17 SMA MNs -- low n, but 10/14 genes in same direction is robust"

---

## Slide 9: The ROCK-LIMK2-CFL2 Pathway Diagram

**Title**: The Therapeutic Axis: From SMN to Actin Failure
**Content**: Pathway diagram (vertical flow):

```
SMN loss --> PFN2 dysregulation --> ROCK activation --> LIMK2 phosphorylation
  --> CFL2 inactivation --> Actin rod formation --> Axonal transport failure
```

Each node annotated with evidence level: [PROVEN], [NEW], [ESTABLISHED]
Drug intervention points shown as red arrows: Fasudil at ROCK, "?" at LIMK2

**Key message**: Complete mechanistic pathway from gene to phenotype with drug intervention points.
**Source**: Nolle 2011, Bowerman 2007/2012/2014, Walter 2021, GSE208629/GSE287257

---

## Slide 10: LIMK2, Not LIMK1 -- The SMA-Specific Kinase

**Title**: The LIMK Switch: Different Kinases for Different Diseases
**Content**: Comparison table

| Kinase | Healthy MNs | SMA MNs | ALS MNs |
|--------|-----------|---------|---------|
| LIMK1 | High (2.3x enriched) | Not detected | DOWN (-0.81) |
| LIMK2 | Moderate | UP +2.81x | UP +1.01x |

- In SMA: LIMK2 takes over (LIMK1 absent)
- In ALS: LIMK1 lost, LIMK2 compensates
- Drug implication: LIMK2-selective inhibitors needed for SMA

**Key message**: LIMK2 is the drug target for SMA. No LIMK2-selective inhibitor exists -- this is a gap.
**Source**: GSE208629 (SMA), GSE287257 (ALS)
**Question for Simon**: "Has anyone measured LIMK1 vs LIMK2 protein in SMA mouse spinal cord?"

---

## Slide 11: CFL2 -- A Disease-Specific Biomarker

**Title**: CFL2 Goes Opposite in SMA vs ALS
**Content**: Divergence diagram or table

| Disease | CFL2 | Interpretation |
|---------|------|----------------|
| SMA (mouse MNs) | UP +1.83x | Active compensation |
| SMA (iPSC MNs) | UP +2.9x | Replicated |
| ALS (human MNs) | DOWN -0.94x | Compensation failed |
| ALS (all cells) | DOWN | Pan-cellular |

- Zero dedicated CFL2-SMA papers exist
- Simple IHC/Western blot could validate this computationally

**Key message**: CFL2 is unexplored territory in SMA. Potential differential biomarker.
**Source**: GSE208629, GSE69175, GSE287257
**Question for Simon**: "Do you have SMA tissue where CFL2 protein could be measured?"

---

## Slide 12: Fasudil -- The Lead Compound

**Title**: Fasudil: From SMA Mice to ALS Phase 2
**Content**: Timeline/evidence ladder

1. **2007**: ROCK pathway linked to SMA (Bowerman, PMID 17728540)
2. **2012**: Fasudil improves SMA mouse survival (Bowerman, PMID 22397316)
   - NMJ and muscle improvement without SMN restoration
3. **2014**: ROCK activity elevated in SMA spinal cord (Bowerman, PMID 25221469)
4. **2024**: ROCK-ALS Phase 2 -- Fasudil safe in motor neuron disease patients
   - n=120, reduced GFAP (neuroinflammation), signals of motor unit preservation
5. **2025**: Oral fasudil (RT1968) Phase 1 complete, ~69% bioavailability

**Key message**: Fasudil has 17 years of ROCK-SMA evidence and is now clinically safe.
**Source**: Listed PMIDs

---

## Slide 13: The Untested Combination -- Risdiplam + Fasudil

**Title**: Why Nobody Has Tested This (And Why They Should)
**Content**:
- Risdiplam: restores SMN protein (addresses root cause)
- Fasudil: inhibits ROCK pathway (addresses downstream actin pathology)
- Schuning 2024: SMN-actin co-localization only PARTIALLY rescued by SMN restoration
  --> Persistent actin deficits remain even after treatment
- Both drugs have human safety data
- **Never tested in combination**

**Key message**: The rationale for combination is mechanistically sound and both drugs are individually safe.
**Source**: Schuning 2024 (PMID 39305126), Bowerman 2012
**Question for Simon**: "Would a fasudil + risdiplam combination study be feasible in your mouse models?"

---

## Slide 14: Connection to Simon's Proprioceptive Work

**Title**: Where Our Data Meets Your Research
**Content**:
- Simon 2025 (PMID 39982868): Proprioceptive synaptic dysfunction is a key feature in SMA mice AND humans
- Proprioceptive Ia synapses lost early, before motor neuron death
- ROCK-LIMK-cofilin axis regulates presynaptic actin dynamics critical for synaptic vesicle cycling
- Fasudil improved NMJ/muscle (Bowerman 2012) but **proprioceptive synapses were never examined**

**Testable prediction**: Fasudil treatment will increase VGLUT1+ proprioceptive boutons on SMA motor neurons and improve H-reflex amplitude

**Key message**: Direct bridge between our computational finding and Simon's experimental expertise.
**Source**: Simon 2025, Bowerman 2012, proprioceptive-hypotheses-2026-03-24.md

---

## Slide 15: Hypothesis -- Actin Rods and Selective Vulnerability

**Title**: Do Actin-Cofilin Rods Explain Why L1 Motor Neurons Die?
**Content**:
- Rods form in SMA cell culture (Walter 2021, PMID 33986363)
- L1 motor neurons (proximal, vulnerable) vs L5 (distal, resistant) -- Simon's expertise
- **Prediction**: Rod density will be higher in L1 than L5 motor neurons
- CFL2 immunoreactivity may differ by segment

**Experiment**: Triple IHC (ChAT + CFL2/p-cofilin + phalloidin) at L1 vs L5 in SMA mice
**Estimated cost**: EUR 8,000-12,000 (lower if archived tissue available)

**Key message**: A concrete, affordable experiment that connects our pathway to Simon's selective vulnerability question.
**Source**: Walter 2021, Murray 2013 (PMID 24324819)

---

## Slide 16: ROCK Inhibitor Landscape

**Title**: 13 Compounds Mapped -- One Clear Leader
**Content**: Summary table of ROCK/LIMK inhibitor landscape

| Category | Compounds | Status |
|----------|-----------|--------|
| ROCK inhibitors | Fasudil, Y-27632, H-1152, Ripasudil, Netarsudil, Belumosudil, GSK429286A | Fasudil = leader |
| ROCK2-selective | KD025 (Belumosudil) | FDA-approved (GVHD), not tested in SMA |
| LIMK inhibitors | BMS-5, LIMKi 3, T56-LIMKi | All LIMK1-biased; T56 failed validation |
| LIMK2-selective | **None exist** | **Critical gap** |

DiffDock result: H-1152 docks to LIMK2 pocket (+0.90 confidence, 14/20 poses) -- potential dual-target compound

**Key message**: Fasudil is the near-term candidate; LIMK2-selective inhibitor development is a medium-term opportunity.
**Source**: rock-inhibitor-landscape.md, DiffDock v2.2 results

---

## Slide 17: H-1152 -- An Unexpected Dual-Target Hit

**Title**: H-1152: ROCK Inhibitor That Also Docks LIMK2
**Content**:
- H-1152 is a potent ROCK2 inhibitor (IC50 ~12 nM)
- Our DiffDock screening found it docks LIMK2 with high confidence
- 14 of 20 poses show pocket binding
- If confirmed: would be a dual ROCK2/LIMK2 inhibitor
- **Needs enzymatic assay validation** (Ki/IC50 against LIMK2)

**Key message**: Computational prediction only -- needs wet lab confirmation. But if real, addresses both targets in one molecule.
**Source**: DiffDock v2.2, diffdock-extended-campaign-2026-03-22.md
**Caveat**: "This is a docking prediction. DiffDock has known biases toward larger molecules."

---

## Slide 18: Limitations -- What We Cannot Claim

**Title**: Honest Assessment: What Needs Validation
**Content** (bullet list):
1. **n=17 SMA motor neurons** -- statistically significant but needs replication
2. **Human data is ALS, not SMA** -- MN enrichment is normal biology, disease changes are ALS-specific
3. **All computational** -- no wet-lab validation of any finding
4. **CORO1C was wrong initially** -- we corrected, but earlier framing was misleading
5. **No proprioceptive marker analysis yet** -- hypotheses exist but not tested against single-cell data
6. **Not peer-reviewed** -- reproducible code, public data, but no external validation

**Key message**: We know what we do not know. Validation requires collaboration with experimental labs.
**Source**: Internal assessment

---

## Slide 19: Proposed Collaboration

**Title**: What We Bring / What We Need
**Content**: Two-column layout

**We bring:**
- Computational platform (14,855 claims, 68 targets, 21K compounds)
- GPU compute (NVIDIA NIMs: DiffDock, ESM-2, GenMol)
- Hypothesis generation and prioritization
- Cross-disease analysis (SMA/ALS convergence)

**We need from Simon's group:**
- CFL2/LIMK2 validation in SMA mouse tissue (IHC/Western)
- Proprioceptive circuit electrophysiology (H-reflex)
- Motor neuron counting expertise (Sowoidnich methodology)
- Mouse model access and experimental design
- Scientific credibility review of our analysis pipeline

**From Schoeneberg:** Bioinformatics validation, omics co-analysis, AI/ML review

**Key message**: Computation generates hypotheses; experiments validate them. We need each other.
**Source**: N/A (proposal)

---

## Slide 20: Next Steps

**Title**: What Happens After This Meeting
**Content** (numbered list):

**Immediate (this week):**
1. Share processed Scanpy objects (GSE208629 + GSE287257) with Schoeneberg if interested
2. Run STMN2 analysis across all datasets (Simon asked about this)
3. Analyze proprioceptive gene panel in single-cell data

**Short-term (1-3 months):**
4. CFL2 IHC validation in SMA mouse spinal cord (Simon lab)
5. LIMK1/LIMK2 protein validation (Western blot)
6. Fasudil + proprioceptive synapse pilot (VGLUT1 counting)

**Medium-term (3-6 months):**
7. Fasudil + Risdiplam combination study design
8. LIMK2-selective inhibitor virtual screen + medicinal chemistry collaboration
9. Segment-specific analysis (L1 vs L5) if spatial data becomes available

**Key message**: Concrete next steps, not vague promises. Each has a clear owner and timeline.
**Source**: Proposed timeline

---

## Notes for Presenter

### Opening (2 min)
- Thank Simon for the March 20 feedback
- Frame: "Your questions pushed us to do single-cell analysis, and it changed everything"
- Set expectations: 20 min presentation, then open discussion

### Pacing
- Slides 1-3: Context (3 min)
- Slides 4-7: From bulk to single-cell, CORO1C correction (5 min)
- Slides 8-11: Key findings -- ROCK-LIMK2-CFL2, disease signatures (7 min)
- Slides 12-15: Therapeutic implications, connection to Simon's work (5 min)
- Slides 16-18: Drug landscape, limitations (3 min)
- Slides 19-20: Collaboration, next steps (3 min)
- Discussion: 30 min

### Key Points to Emphasize
- We corrected our own mistake (CORO1C) -- builds trust
- CFL2 has zero SMA papers -- genuine novelty, low-hanging fruit for validation
- Fasudil + proprioception is the direct bridge to Simon's research
- Frame everything as "computational evidence requiring experimental validation"
- Never say "we discovered" -- say "the data suggests" or "our analysis indicates"

### Questions to Expect from Simon
- "How did you identify motor neurons in the single-cell data?" (Answer: Isl1/Mnx1/Slc18a3 scoring, top 5% threshold; Chat not detected in GSE208629)
- "17 motor neurons is very few -- how do you trust these results?" (Answer: pathway-level signal is robust even if individual genes are underpowered; 10/14 in same direction)
- "What about the Smn model -- Smn-/- is very severe" (Answer: acknowledged; need replication in milder models like Smn2B/-)
- "Why ALS data for motor neuron enrichment?" (Answer: no human SMA single-cell available; ALS gives us healthy human MNs from control samples)
- "Did you look at proprioceptive neurons?" (Answer: not yet -- this is a gap, and we want his input on which markers to use)
