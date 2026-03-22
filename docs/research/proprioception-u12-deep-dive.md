# Deep Dive: Proprioceptive Synapse Dysfunction & U12 Minor Intron Splicing in SMA

**Date**: 2026-03-22
**Status**: Research synthesis from literature (2011-2025)

---

## Table of Contents

1. [Proprioceptive Synapse Dysfunction in SMA](#1-proprioceptive-synapse-dysfunction-in-sma)
   - 1.1 The Circuit Disease Hypothesis
   - 1.2 Key Evidence: Mentis Lab (Columbia)
   - 1.3 Molecular Mechanism: Kv2.1 and Glutamate
   - 1.4 Complement-Mediated Synapse Elimination
   - 1.5 Actin Cytoskeleton in Proprioceptive Synapses
   - 1.6 Could Fasudil Protect Proprioceptive Synapses?
   - 1.7 Biomarkers for Proprioceptive Synapse Health
   - 1.8 NT3 Trophic Support
2. [U12 Minor Intron Splicing Vulnerability](#2-u12-minor-intron-splicing-vulnerability)
   - 2.1 SMN and the Minor Spliceosome
   - 2.2 STASIMON/TMEM41B: The Keystone U12 Gene
   - 2.3 The p38 MAPK-p53 Death Pathway
   - 2.4 Minor snRNA Gene Delivery Rescues Proprioceptive Synapses
   - 2.5 U12 Intron-Containing Genes Critical for Motor Neurons
   - 2.6 Is CORO1C Related to U12 Splicing?
   - 2.7 Tissue-Specific Vulnerability
3. [Convergence: Proprioception Meets U12 Splicing](#3-convergence-proprioception-meets-u12-splicing)
4. [Therapeutic Implications](#4-therapeutic-implications)
5. [Open Questions & Next Steps](#5-open-questions--next-steps)

---

## 1. Proprioceptive Synapse Dysfunction in SMA

### 1.1 The Circuit Disease Hypothesis

SMA has traditionally been viewed as a motor neuron disease. A paradigm shift is underway: **proprioceptive synapse loss PRECEDES motor neuron death**, reframing SMA as a **circuit disease** where sensory-motor connectivity breaks down before the motor neuron itself degenerates.

Key timeline in SMA mouse models:
- **P4**: Proprioceptive synapses already show reduced glutamate release (PMID: 28504671)
- **P4-P11**: Progressive loss of vGluT1+ proprioceptive synapses from motor neuron soma and proximal dendrites (PMID: 38883729)
- **P11-P13**: Significant synapse stripping, especially on proximal dendrites (PMID: 31801075)
- **Later**: Motor neuron death follows synapse loss

This means that **protecting the synapse may be more important than protecting the motor neuron directly**.

### 1.2 Key Evidence: Mentis Lab (Columbia)

George Z. Mentis at Columbia University's Center for Motor Neuron Biology and Disease has built a sustained research program (2011-2025) establishing proprioceptive synapse dysfunction as central to SMA:

**Landmark Paper 1 (2011)**: "Early functional impairment of sensory-motor connectivity in a mouse model of spinal muscular atrophy"
- First demonstration that sensory-motor synaptic dysfunction precedes motor neuron loss
- PMID: 21315257 (Neuron, 2011)

**Landmark Paper 2 (2017)**: "Reduced sensory synaptic excitation impairs motor neuron function via Kv2.1 in spinal muscular atrophy"
- Established the Kv2.1 mechanism (see 1.3)
- PMID: 28504671 (Nature Neuroscience, 2017)

**Landmark Paper 3 (2024)**: "Dysfunction of proprioceptive sensory synapses is a pathogenic event and therapeutic target in mice and humans with spinal muscular atrophy"
- Extended findings to HUMAN SMA patients
- Demonstrated H-reflex as clinical biomarker
- PMID: 38883729

**Landmark Paper 4 (2025)**: "Proprioceptive synaptic dysfunction is a key feature in mice and humans with spinal muscular atrophy"
- Published in Brain (2025)
- Confirmed conserved pathology across mice and humans
- H-reflex correlates with treatment response (nusinersen, risdiplam)
- PMID: 39982868

### 1.3 Molecular Mechanism: Kv2.1 and Glutamate

The mechanistic chain from synapse dysfunction to motor neuron failure (PMID: 28504671):

1. **Proprioceptive synapses release less glutamate** at physiological frequencies
2. **Reduced glutamatergic drive** causes downregulation of Kv2.1 potassium channels on motor neuron surface
3. **Kv2.1 reduction** impairs action potential repolarization, leading to longer action potentials
4. **Sustained depolarization** between spikes inactivates voltage-gated sodium channels
5. **Motor neuron firing frequency decreases** -- functional motor neuron failure before death

Critical insight: **The Kv2.1 reduction is caused by reduced glutamate release, NOT by synapse loss itself.** Kv2.1 was already reduced in animals that had not yet lost synapses but had impaired neurotransmission. This means the dysfunction precedes the structural loss.

Therapeutic angle: Pharmacologically increasing neuronal activity *in vivo* normalized Kv2.1 expression and improved motor function, and led to healthier nerve circuits. Kv2.1 has been identified as a potential treatment target (reported at MDA 2025 conference).

### 1.4 Complement-Mediated Synapse Elimination

The classical complement pathway actively drives synapse elimination in SMA (PMID: 31801075):

- **C1q tags vulnerable SMA proprioceptive synapses**: ~25% of SMA proprioceptive synapses on proximal dendrites of L1 motor neurons were C1q-tagged vs. ~4% in wild-type
- **Microglia engulf tagged synapses**: Classical complement cascade (C1q -> C3 -> CR3 on microglia) mediates phagocytic removal
- **Dual intervention rescues synapses**:
  - Pharmacological inhibition of C1q rescues synapse number and function
  - Depletion of microglia similarly rescues synapses
  - Both confer significant behavioral benefit in SMA mice

This represents a **druggable pathway**: complement inhibitors or microglial modulators could preserve proprioceptive synapses.

### 1.5 Actin Cytoskeleton in Proprioceptive Synapses

The actin cytoskeleton is critical for proprioceptive synapse formation and maintenance:

**Cdc42 (Rho GTPase) controls synapse formation** (PMID: 27225763):
- Cdc42 regulates actin cytoskeleton rearrangements necessary for synapse formation
- In mice lacking Cdc42 in presynaptic sensory neurons, proprioceptive axons reach the ventral spinal cord but **significantly fewer synapses form** with motor neurons
- Cdc42 acts in presynaptic (sensory), NOT postsynaptic (motor), neurons
- Interesting: temporally targeted Cdc42 deletion AFTER circuit establishment does NOT affect synaptic transmission -- Cdc42/actin is critical for formation, not maintenance

**Profilin splicing defect in SMN mutants** (PMID: 31927482):
- In S. pombe SMN mutants, profilin gene shows strong splicing defects with accumulation of pre-mRNAs
- Profilin is a key actin monomer-binding protein that promotes F-actin assembly
- Splicing defects reduce profilin levels, leading to decreased F-actin and altered actin dynamics
- This provides a direct link: SMN deficiency -> splicing defect -> reduced profilin -> actin dysfunction -> synapse vulnerability

**The actin cytoskeleton provides the structural scaffold** for presynaptic terminals, from elaboration of terminal arbors to recruitment of presynaptic vesicles and active zone components.

### 1.6 Could Fasudil Protect Proprioceptive Synapses?

**Direct evidence in SMA** (PMID: 22397316):
- Fasudil significantly improves survival of SMA mice
- Dramatically increases myofiber and postsynaptic endplate (EP) size
- Improvement in post-synaptic parameters stabilizes synaptic connections
- **Does NOT increase SMN protein** -- works via SMN-independent mechanism
- Has little impact on initial motor neuron loss but protects remaining motor neurons via synapse stabilization

**Mechanism relevant to proprioceptive synapses**:
- ROCK (Rho-associated kinase) is a major regulator of actin cytoskeleton dynamics
- ROCK inactivates cofilin (via LIMK phosphorylation), preventing F-actin severing
- ROCK phosphorylates profilin, reducing G-actin recycling and F-actin turnover
- Fasudil, by inhibiting ROCK, promotes actin turnover and axonal regeneration
- In DRG neurons (proprioceptive neurons reside in DRG), ROCK inhibitor Y-27632 substantially promotes axonal regeneration (multiple studies)

**Fasudil and synaptic vesicle dynamics** (PMID: 33341946):
- Fasudil alters chronic dynamics of synaptic vesicles
- Does not affect basic synaptic function or key synaptic protein levels
- May modulate vesicle recycling relevant to glutamate release at proprioceptive terminals

**Assessment**: There is **no direct study** testing Fasudil's effect specifically on proprioceptive synapse preservation in SMA. However, the convergence of evidence is compelling:
- Fasudil improves SMA phenotype via synapse stabilization (not SMN induction)
- ROCK inhibition promotes DRG neuron axon regeneration
- Actin dynamics are critical for proprioceptive synapse formation (Cdc42 data)
- Profilin (ROCK substrate) is mis-spliced in SMN deficiency

**This is a strong hypothesis for experimental testing.**

### 1.7 Biomarkers for Proprioceptive Synapse Health

**H-reflex (Hoffmann reflex)** -- the most validated biomarker:

The H-reflex is an electrophysiological measure of the monosynaptic reflex arc (Ia afferent -> motor neuron -> muscle). It directly assesses proprioceptive sensory-motor circuit function.

Evidence from Mentis lab (PMID: 38883729, 39982868):
- **SMA patients exhibit impaired H-reflex** consistent with proprioceptive synapse dysfunction
- **H-reflex amplitude correlates with treatment response**: increased amplitudes in nusinersen-treated patients correlated with improved walking distance and reduced fatigability
- **Risdiplam analog treatment** in mice: improved motor function associated with increased H-reflex amplitude
- **Suitable for monitoring disease progression AND treatment efficacy**
- Can be performed non-invasively in ambulatory patients

**Kv2.1 expression** -- a molecular biomarker (currently preclinical only):
- Reduced Kv2.1 on motor neuron surface reflects impaired proprioceptive drive
- Normalized by activity-enhancing treatments
- Not yet measurable in patients

**vGluT1+ synapse counts** -- gold standard in preclinical models:
- Quantifies proprioceptive synaptic boutons on motor neurons
- Progressive loss from P4 to P13 in SMA mice, especially on proximal dendrites
- Standard outcome measure in mouse studies

**Neurofilament light chain (NfL)** -- complementary biomarker:
- Reflects axonal damage broadly (not proprioception-specific)
- Shows promise for monitoring treatment response in SMA patients (PMID studies 2024)
- Could be combined with H-reflex for comprehensive circuit assessment

### 1.8 NT3 Trophic Support

Neurotrophin-3 (NT3) is a critical trophic factor for proprioceptive sensory-motor connectivity:

- **Muscle spindle-derived NT3** regulates synaptic connectivity between Ia afferents and motor neurons (PMID: 11978828)
- NT3 expression becomes selectively restricted to intrafusal muscle fibers (muscle spindles) after birth
- In neonatal mice lacking spindle NT3, synaptic connections can be rescued by intramuscular NT3 injection during the first two postnatal weeks
- **Spindle-derived NT3 strengthens homonymous Ia-motor neuron connections** during the second postnatal week (PMID: 11978828)
- In adults, axotomy reduces Ia-motor neuron synaptic strength, and NT3 administration prevents this loss

**SMA relevance**: If SMA impairs muscle spindle function or NT3 production, this would create a vicious cycle:
Reduced SMN -> spindle dysfunction -> less NT3 -> weaker Ia synapses -> less glutamate -> Kv2.1 reduction -> motor neuron failure

---

## 2. U12 Minor Intron Splicing Vulnerability

### 2.1 SMN and the Minor Spliceosome

SMN (Survival Motor Neuron) protein is a core component of the spliceosome assembly machinery. It is essential for biogenesis of snRNPs (small nuclear ribonucleoproteins), including both major (U1, U2, U4, U5, U6) and minor (U11, U12, U4atac, U6atac) spliceosomal components.

Key facts:
- **U12-type introns** represent ~0.5% of all introns (~700-800 genes in the human genome)
- SMN deficiency **preferentially reduces minor snRNP levels** (PMID: 17934057, Gabanella et al. 2007)
- Nearly **one-third of all U12 introns** in the spinal cord of SMA mice showed significantly increased retention (PMID: 27557711)
- U12-type introns are more sensitive to SMN mutations because a larger proportion of U12 introns are retained compared to U2 introns

**Why the minor spliceosome is more vulnerable**: Minor snRNPs are present at lower abundance than major snRNPs. When SMN is reduced, their biogenesis drops below a functional threshold earlier, creating a bottleneck specifically for U12 intron splicing.

### 2.2 STASIMON/TMEM41B: The Keystone U12 Gene

Stasimon (named "stymied in smn") was identified as a critical SMN-dependent U12 splicing target (PMID: 23063131, Cell 2012):

**Identity and function**:
- Gene: *TMEM41B* (also called CG8408 in Drosophila)
- Encodes a transmembrane ER-resident protein
- Localizes to mitochondria-associated ER membranes (MAMs)
- Essential for mouse embryonic development (PMID: 30352685)
- Interactome includes ER, mitochondria, and COPI vesicle trafficking components
- Involved in autophagy/lipid metabolism

**Evidence for role in SMA across species**:

| Organism | Finding | PMID |
|----------|---------|------|
| Drosophila | Restoration of Stasimon in motor circuit corrects NMJ transmission defects and muscle growth | 23063131 |
| Zebrafish | Stasimon restoration rescues aberrant motor neuron development in SMN-deficient fish | 23063131 |
| Mouse (SMA) | AAV9-Stasimon improves motor function, prevents proprioceptive synapse loss, reduces motor neuron death | 31851921 |
| Mouse (SMA) | Stasimon overexpression in proprioceptive neurons prevents loss of afferent synapses and enhances sensory-motor neurotransmission | 31851921 |
| Mouse (SMA) | In motor neurons, Stasimon suppresses neurodegeneration by reducing p53 phosphorylation | 31851921 |

**Dual mechanism**: Stasimon acts in BOTH proprioceptive (sensory) neurons AND motor neurons -- a rare example of a single gene with cell-autonomous protective functions in both halves of the circuit.

### 2.3 The p38 MAPK-p53 Death Pathway

Stasimon deficiency activates a specific death signaling cascade (PMID: 31851921):

1. SMN deficiency -> reduced Stasimon expression (via U12 splicing defect)
2. Stasimon deficiency -> activation of p38 MAPK
3. p38 MAPK -> phosphorylation of tumor suppressor p53
4. Phosphorylated p53 -> motor neuron apoptosis

**Therapeutic validation** -- a breakthrough 2025 paper:

"Identification of p38 MAPK inhibition as a neuroprotective strategy for combinatorial SMA therapy" (EMBO Molecular Medicine, 2025; PMID: 40926051)

Key findings:
- Cell-based screen identified p38 MAPK inhibitors as suppressors of SMN deficiency-induced defects
- **MW150** (a highly optimized p38 MAPK inhibitor) improves motor function in SMA mice
- MW150 promotes motor neuron survival through an **SMN-independent** mechanism
- **Combinatorial treatment** (MW150 + SMN-inducing drug): **synergistic enhancement** beyond either alone
- p38 MAPK inhibition enables enhanced **synaptic rewiring** of motor neurons within sensory-motor spinal circuits
- MW150 identified as a candidate for **clinical combination therapy** in SMA

This is extremely significant: it provides a pharmacological approach to block the Stasimon deficiency death pathway WITHOUT needing to fix SMN levels.

### 2.4 Minor snRNA Gene Delivery Rescues Proprioceptive Synapses

A direct experimental link between U12 splicing and proprioceptive synapses (PMID: 32516136, JCI Insight 2020):

**Experiment**: AAV9-mediated delivery of minor snRNA genes (U11, U12, U4atac) to SMA mice

**Results**:
- Improved aberrant splicing of the U12 intron-containing gene Stasimon in spinal cord and DRG
- **Robust rescue of proprioceptive synapse numbers** on motor neurons
- AAV9-U11/U12 was equally effective as AAV9-U11/U12/U4atac in preventing proprioceptive synapse stripping
- Moderate improvement in survival, weight gain, and motor function
- **Did NOT increase SMN expression** -- pure splicing correction

**Significance**: This proves that U12 splicing dysfunction is a **direct pathogenic driver** of proprioceptive synapse loss in SMA. Correcting U12 splicing alone (without fixing SMN) is sufficient to rescue proprioceptive synapses.

### 2.5 U12 Intron-Containing Genes Critical for Motor Neurons

Beyond Stasimon, several U12 intron-containing genes are critical for neuronal function:

**Voltage-gated ion channels** (highly enriched for U12 introns):
- Nav (SCN) family: voltage-gated sodium channels -- U12 introns conserved in Domain 1, Segment 1
- Cav1, Cav2, Cav3 families: voltage-gated calcium channels -- U12 introns conserved
- These channels are essential for action potential generation and synaptic transmission in motor neurons

**Signal transduction**:
- Ras-Raf-MAPK pathway genes: over-represented among U12 intron-containing genes
- Phospholipase C family
- cAMP-binding guanine nucleotide exchange factor family

**Drosophila SMA-relevant U12 genes** identified by functional screen (PMID: 33159053, Nature Communications 2020):
- **Pcyt2**: phosphoethanolamine cytidylyltransferase -- when restored, rescues muscle development phenotypes
- **Zmynd10**: zinc finger MYND domain -- contributes to NMJ defects
- **Fas3**: fasciclin 3 -- contributes to locomotion defects
- All three directly contribute to SMA-associated phenotypes when their splicing is disrupted

**Mouse spinal cord U12 genes affected in SMA** (PMID: 27557711):
- RNA-sequencing of SMA mouse model revealed tissue-wide changes in U12-dependent intron splicing
- Nearly 1/3 of all U12 introns showed significantly increased retention in spinal cord
- Enrichment in genes involved in **adherens junction organization**, **actin cytoskeleton dynamics**, and **muscle morphology**

### 2.6 Is CORO1C Related to U12 Splicing?

**Short answer: CORO1C is NOT a U12 intron-containing gene, and its role in SMA is not through U12 splicing but through a separate actin/endocytosis pathway.**

**CORO1C's actual role in SMA** (PMID: 27499521, Wirth Lab 2016):
- CORO1C (Coronin 1C) is an F-actin binding protein
- Identified as a **protective modifier** of SMA alongside PLS3 (Plastin 3)
- CORO1C binds directly to PLS3 in a calcium-dependent manner
- SMN deficiency dramatically reduces endocytosis
- CORO1C overexpression restores endocytosis by elevating F-actin levels
- Rescues axonal truncation and branching in Smn-depleted zebrafish

**Why CORO1C was thought to involve splicing**:
- SMN deficiency causes widespread intron retention (both U2 and U12 types)
- Profilin (an actin regulator) shows strong splicing defects in SMN mutants (PMID: 31927482)
- But **no significant splicing defects were found for coronin genes themselves**
- CORO1C acts as a downstream compensatory factor, not a direct splicing victim

**Connection to actin pathway**: CORO1C harbors a second actin-binding site conferring cooperative binding to F-actin. Together with PLS3, it maintains F-actin levels needed for endocytosis at presynaptic terminals and NMJ maintenance. This is parallel to, but distinct from, the U12 splicing pathway.

### 2.7 Tissue-Specific Vulnerability

U12 splicing defects are tissue-specific, explaining selective vulnerability (PMID: 27557711):

- Different tissues show distinct patterns of U12 intron retention
- Spinal cord shows particularly high retention of U12 introns in SMA
- DRG (where proprioceptive neurons reside) also shows U12 splicing defects
- The branchpoint sequence (BPS) is a key element controlling splicing efficiency of minor introns (PMID: 35166596)
- A subset of minor introns can use BOTH minor and major spliceosome components, adding complexity

This tissue specificity may explain why motor circuits are selectively affected: the combination of low SMN, high demand for U12 splicing in neural genes (especially ion channels and actin regulators), and limited compensatory capacity creates a perfect storm in spinal motor circuits.

---

## 3. Convergence: Proprioception Meets U12 Splicing

The two research threads converge in a compelling mechanistic model:

```
SMN deficiency
    |
    v
Reduced minor spliceosome assembly (U11, U12, U4atac snRNPs)
    |
    v
U12 intron retention in critical genes
    |
    +---> Stasimon/TMEM41B reduced expression
    |         |
    |         +---> In proprioceptive neurons: synapse loss from motor neurons
    |         +---> In motor neurons: p38 MAPK -> p53 phosphorylation -> apoptosis
    |
    +---> Voltage-gated ion channels (SCN, CACN) mis-spliced
    |         |
    |         +---> Impaired action potential generation
    |         +---> Reduced synaptic transmission
    |
    +---> Actin regulators (profilin) mis-spliced
    |         |
    |         +---> Reduced F-actin dynamics
    |         +---> Impaired synapse formation and endocytosis
    |         +---> Compensated partially by PLS3/CORO1C in some individuals
    |
    v
Proprioceptive synapses: reduced glutamate release (functional before structural)
    |
    v
Motor neurons: Kv2.1 downregulation -> firing impairment
    |
    v
C1q tagging of dysfunctional synapses -> complement cascade -> microglia engulf synapses
    |
    v
Motor neuron denervation and death
```

**Key insight**: The U12 splicing defect is an UPSTREAM driver of the proprioceptive synapse dysfunction. Correcting U12 splicing (even without fixing SMN) rescues proprioceptive synapses (PMID: 32516136). The complement-mediated elimination is a DOWNSTREAM effector that could be independently blocked.

---

## 4. Therapeutic Implications

### Combination Strategy (evidence-based):

| Target | Drug/Approach | Mechanism | Evidence Level |
|--------|--------------|-----------|----------------|
| SMN induction | Nusinersen / Risdiplam / Onasemnogene | Addresses root cause | FDA approved |
| p38 MAPK | MW150 | Blocks Stasimon-deficiency death pathway, SMN-independent | Preclinical, synergistic with SMN drugs (PMID: 40926051) |
| Complement (C1q) | Anti-C1q antibodies | Prevents microglia-mediated synapse stripping | Preclinical (PMID: 31801075) |
| ROCK pathway | Fasudil | Stabilizes synapses via actin/endplate effects, SMN-independent | Preclinical in SMA; Phase 2 in ALS |
| U12 splicing | AAV9-U11/U12 snRNA delivery | Directly corrects splicing defect, rescues proprioceptive synapses | Preclinical (PMID: 32516136) |
| Kv2.1/Activity | Activity-enhancing drugs | Normalizes motor neuron firing | Preclinical (PMID: 28504671) |
| Endocytosis | PLS3/CORO1C pathway enhancement | Restores presynaptic endocytosis at NMJ | Genetic modifier data |

### Most Promising Combination:
**SMN induction + MW150 (p38 MAPK inhibitor)** -- already shown to be synergistic in SMA mice (PMID: 40926051). MW150 is a well-characterized, brain-penetrant compound.

---

## 5. Open Questions & Next Steps

### For the SMA Research Platform:

1. **Map U12 intron-containing genes to existing platform targets**: Which of our ~50 targets have U12 introns? Cross-reference with U12DB database.

2. **Stasimon as a platform target**: Should Stasimon/TMEM41B be added as a high-priority target with dual evidence (proprioceptive + motor neuron protection)?

3. **p38 MAPK/MW150 scoring**: The 2025 EMBO paper (PMID: 40926051) provides strong combination therapy evidence. Score MW150 in drug screening module.

4. **Complement pathway targets**: C1q inhibition data (PMID: 31801075) suggests adding complement components as therapeutic targets.

5. **Fasudil + proprioception experiment**: No one has specifically tested Fasudil's effect on proprioceptive synapse numbers in SMA mice. This is a gap in the literature and a concrete experimental proposal.

6. **NT3 in SMA muscle spindles**: Is NT3 production reduced in SMA muscle spindles? This would explain the progressive proprioceptive synapse loss and represents a potential therapeutic target.

7. **H-reflex as clinical endpoint**: The H-reflex should be highlighted as the leading biomarker for proprioceptive circuit health in clinical trials.

### Unanswered Questions in the Field:

- Why are proprioceptive synapses on **proximal** motor neurons more vulnerable than distal ones?
- Does U12 splicing dysfunction affect proprioceptive (DRG) neurons cell-autonomously, or only through their central synapses?
- Can complement inhibitors and p38 MAPK inhibitors be combined with SMN-inducing drugs for triple therapy?
- What is the therapeutic window for proprioceptive synapse rescue in human patients?
- Are there U12 intron-containing genes in proprioceptive neurons specifically that have not been identified yet?

---

## Key References

### Proprioceptive Synapse Dysfunction
| PMID | Year | Title | Journal |
|------|------|-------|---------|
| 21315257 | 2011 | Early functional impairment of sensory-motor connectivity in a mouse model of SMA | Neuron |
| 28504671 | 2017 | Reduced sensory synaptic excitation impairs motor neuron function via Kv2.1 in SMA | Nature Neuroscience |
| 31801075 | 2019 | The classical complement pathway mediates microglia-dependent remodeling of spinal motor circuits during development and in SMA | Cell Reports |
| 38883729 | 2024 | Dysfunction of proprioceptive sensory synapses is a pathogenic event and therapeutic target in mice and humans with SMA | (Preprint/medRxiv) |
| 39982868 | 2025 | Proprioceptive synaptic dysfunction is a key feature in mice and humans with SMA | Brain |

### U12 Minor Intron Splicing
| PMID | Year | Title | Journal |
|------|------|-------|---------|
| 23063131 | 2012 | An SMN-dependent U12 splicing event essential for motor circuit function | Cell |
| 27557711 | 2016 | RNA-sequencing of a mouse model of SMA reveals tissue-wide changes in splicing of U12-dependent introns | Nucleic Acids Research |
| 31851921 | 2020 | Stasimon contributes to the loss of sensory synapses and motor neuron death in a mouse model of SMA | Cell Reports |
| 32516136 | 2020 | Minor snRNA gene delivery improves the loss of proprioceptive synapses on SMA motor neurons | JCI Insight |
| 33159053 | 2020 | Defective minor spliceosomes induce SMA-associated phenotypes through sensitive intron-containing neural genes in Drosophila | Nature Communications |
| 35166596 | 2022 | Splicing efficiency of minor introns in a mouse model of SMA predominantly depends on their branchpoint sequence | RNA |

### Therapeutic Targets
| PMID | Year | Title | Journal |
|------|------|-------|---------|
| 22397316 | 2012 | Fasudil improves survival and promotes skeletal muscle development in a mouse model of SMA | BMC Medicine |
| 27499521 | 2016 | PLS3 and CORO1C unravel impaired endocytosis in SMA and rescue SMA phenotype | American Journal of Human Genetics |
| 40926051 | 2025 | Identification of p38 MAPK inhibition as a neuroprotective strategy for combinatorial SMA therapy | EMBO Molecular Medicine |

### Actin and Synapse Biology
| PMID | Year | Title | Journal |
|------|------|-------|---------|
| 11978828 | 2002 | Muscle spindle-derived NT3 regulates synaptic connectivity between muscle sensory and motor neurons | J Neuroscience |
| 27225763 | 2016 | Synapse formation in monosynaptic sensory-motor connections is regulated by presynaptic Rho GTPase Cdc42 | J Neuroscience |
| 31927482 | 2020 | Splicing defects of the profilin gene alter actin dynamics in an S. pombe SMN mutant | iScience |
| 33341946 | 2020 | Rho-kinase inhibition by fasudil modulates pre-synaptic vesicle dynamics | (Journal) |
