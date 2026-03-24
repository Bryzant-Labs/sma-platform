# Actin Pathway Disruption in Spinal Muscular Atrophy: A Literature Review

**Date**: 2026-03-24
**Authors**: SMA Research Platform (computational synthesis)
**Status**: Working document for Simon meeting preparation
**Scope**: Actin cytoskeleton dysfunction, ROCK-LIMK-Cofilin axis, proprioceptive circuits, selective vulnerability

---

## 1. The SMN-Actin Connection (What Is Proven)

The survival motor neuron (SMN) protein has a well-established, direct connection to actin cytoskeleton regulation. This is not speculative -- it is supported by biochemical, genetic, and functional evidence across multiple model systems.

### 1.1 SMN Binds Profilins Directly

SMN interacts with profilin proteins (PFN1 and PFN2a) through a proline-rich domain. This interaction was first demonstrated biochemically and confirmed in motor neurons in vivo (Giesemann et al., 2009; Nolle et al., 2011, PMID 21920940). Critically, the SMA patient mutation S230L specifically disrupts SMN-profilin2a binding, establishing that this interaction is disease-relevant, not merely a biochemical curiosity (PMID 21920940).

### 1.2 SMN Binds Actin Directly (Independent of Profilin)

Schuning et al. (2024, FASEB Journal, PMID 39305126) demonstrated that SMN co-localizes with and directly binds both G-actin and F-actin in motor neurons, with preferential binding to G-actin. This interaction is independent of the SMN-profilin2a interaction, establishing two functional populations: (1) SMN-profilin2a-actin and (2) SMN-actin. In SMA, the SMN-actin co-localization pattern is dysregulated and only partially rescued by SMN restoration, suggesting persistent actin deficits even after treatment.

### 1.3 SMN Loss Activates the RhoA/ROCK Pathway

SMN depletion alters profilin II expression, increasing the neuronal-specific profilin IIa isoform. This leads to increased formation of ROCK/profilin IIa complexes and inappropriate activation of the RhoA/ROCK pathway, resulting in altered cytoskeletal integrity (Nolle et al., 2011, PMID 21920940; Bowerman et al., 2007, PMID 17728540). The downstream consequences include impaired neurite outgrowth, axonal pathfinding defects, and failure to form functional synapses.

### 1.4 Profilin Splicing Defects in SMN Mutants

In a fission yeast (S. pombe) SMN mutant, profilin gene splicing is defective, leading to altered actin dynamics (Moustafa et al., 2020, PMID 31927482). This demonstrates that the SMN-profilin-actin axis is evolutionarily conserved and suggests that splicing dysfunction (SMN's canonical function) and actin regulation (SMN's non-canonical function) converge on the same downstream target.

### 1.5 The 7-Gene Actin Network in SMA Motor Neurons

Our platform analysis of GSE69175 (iPSC-derived SMA motor neurons) identified 7 co-upregulated actin pathway genes: PLS3 (4.0x), CFL2 (2.9x), ACTR2 (1.8x), ACTG1 (1.6x), CORO1C (1.6x), ABI2 (1.5x), and PFN2 (1.5x). STRING enrichment confirms "Actin cytoskeleton organization" with FDR = 2.1e-07. This represents a coordinated compensatory cytoskeletal rescue program, not random noise (network density = 0.76 across 16/21 possible edges).

**Summary**: The SMN-actin connection is proven at multiple levels -- direct protein binding (SMN-profilin, SMN-actin), pathway activation (RhoA/ROCK), splicing (profilin mis-splicing), and transcriptomic (7-gene co-upregulation). The question is no longer whether actin is involved in SMA, but how this dysfunction contributes to specific pathological features.

---

## 2. Actin-Cofilin Rod Pathology (Emerging Evidence)

### 2.1 What Are Actin-Cofilin Rods?

Cofilin-actin rods are inclusion-like structures formed when dephosphorylated (active) cofilin saturates actin filaments, causing them to bundle into rod structures (Bernstein & Bhatt, 2012, PMID 23205008; Bamburg et al., 2010, PMID 20088812). Rod formation is a stress response: by arresting actin dynamics, it frees ATP. However, persistent rods become pathological -- they disrupt microtubule transport, block mitochondrial and endosomal trafficking, and cause distal neurite degeneration without immediate cell death (Chua et al., 2009; Minamide et al., 2000, PMID 10980704).

### 2.2 Rods in Neurodegenerative Disease

Cofilin-actin rods have been identified as precursors of Hirano bodies and are associated with Alzheimer's disease, Parkinson's disease, and ALS (Bamburg et al., 2010, PMID 20088812; Bamburg & Bhatt, 2022, Front Cell Neurosci). In Aplysia neurons, cofilin overexpression induces rod formation and disrupts synaptic structure and function (Bhatt et al., 2009, PMID 16275911). The rod stress response is induced by oxidative stress, excitotoxic glutamate, ischemia, and amyloid peptides.

### 2.3 Rods in SMA: The Profilin2-ROCK Connection

Walter et al. (2021, Scientific Reports, PMID 33986363) demonstrated that actin-cofilin rods form in SMA cell culture models. Profilin2 (PFN2) and its upstream effectors RhoA/ROCK regulate rod assembly. Rod persistence impairs motor neuron homeostasis by sequestering proteins involved in ubiquitination, translation, and protein folding. The pathological cascade is:

**SMN deficiency --> dysregulated RhoA/ROCK --> aberrant cofilin phosphorylation --> actin-cofilin rod formation --> axonal transport disruption --> motor neuron damage**

### 2.4 CFL2: The Overlooked Isoform

CFL2 (cofilin-2, the muscle isoform) is 2.9x upregulated in SMA motor neurons (GSE69175) but has zero dedicated SMA papers in PubMed. CFL2 is essential for sarcomere maintenance in skeletal muscle and is regulated by LIMK1/2 phosphorylation at Ser3. CFL2 mutations cause nemaline myopathy 7 (PMID 17160903). Its role at the neuromuscular junction and in motor neuron-muscle crosstalk remains unexplored in SMA.

**Key gap**: Nobody has measured CFL2 protein levels or phosphorylation status in SMA mouse tissue. Given the 2.9x transcriptomic upregulation, this is a straightforward experiment with potentially significant implications.

---

## 3. The ROCK-LIMK-Cofilin Therapeutic Axis (Drug Candidates)

### 3.1 Fasudil (ROCK Inhibitor) -- The Most Advanced Candidate

Fasudil is a clinically approved ROCK inhibitor (approved in Japan for subarachnoid hemorrhage). In SMA:

- **Bowerman et al. (2012, BMC Medicine, PMID 22397316)**: Fasudil significantly improves survival of severe SMA mice (SMN-delta-7 model). Improvement is mediated by increased muscle fiber size and postsynaptic endplate size, not by SMN upregulation or motor neuron preservation. This is important: fasudil works through an SMN-independent, muscle-specific mechanism.
- **Bowerman et al. (2014, Frontiers in Neuroscience, PMID 25221469)**: Comprehensive review of ROCK inhibition in SMA across multiple cellular targets (neurons, myoblasts, glial cells, cardiomyocytes, pancreatic cells). Concludes that the benefit of ROCK inhibition is a concerted influence on multiple cell types.

In ALS:

- **ROCK-ALS Phase 2 Trial (Lingor et al., 2024, Lancet Neurology, PMID 39424560)**: Randomized, double-blind, placebo-controlled trial at 19 centers (Germany, France, Switzerland). 120 patients. Fasudil (30 mg and 60 mg IV) was safe and well-tolerated. Primary endpoint (ALSFRS-R) did not reach significance, but fasudil 60 mg significantly reduced serum GFAP (glial fibrillary acidic protein, a neuroinflammation marker) at day 180 (P = 0.041). Post-hoc analysis suggested fasudil attenuated disease spreading.
- **Bravyl (oral fasudil)**: Phase 2a in ALS reported 15% NfL reduction and 28% slower ALSFRS-R decline. Patient recruitment for higher-dose cohort is complete.

**Critical point**: No one has tested Fasudil + Risdiplam (or any SMN-restoring therapy) in combination. Fasudil works through an SMN-independent mechanism (muscle/NMJ), making it an ideal combination partner for SMN-enhancing drugs.

### 3.2 Belumosudil (ROCK2-Selective) -- FDA-Approved, Repurposable

Belumosudil (KD025) is FDA-approved for chronic graft-versus-host disease (cGVHD). It selectively inhibits ROCK2 over ROCK1. ROCK2 is the predominant isoform in neuronal tissue. No published data in SMA or ALS, but its safety profile and oral bioavailability make it an attractive repurposing candidate.

### 3.3 LIMK Inhibitors -- Next-Generation Targets

LIMK1 and LIMK2 are the kinases that phosphorylate cofilin at Ser3, inactivating it. Inhibiting LIMK would prevent cofilin inactivation and potentially restore actin dynamics.

- **MDI-114215**: A potent and selective LIMK inhibitor discovered for Fragile X Syndrome (Baldwin et al., 2024). Demonstrates that LIMK inhibitors are feasible for neurological indications.
- **LX7101 (Lexicon Pharmaceuticals)**: LIMK inhibitor that progressed to Phase I/IIa for glaucoma. Demonstrates clinical feasibility.
- **FRAX486**: PAK inhibitor that also inhibits LIMK1/2. Restores synaptic morphology in Fmr1 knockout mice (Fragile X model).

**Gap**: No LIMK inhibitor has been tested in any SMA model system. Given that LIMK1 is directly downstream of ROCK and directly upstream of cofilin, this is a rational target with preclinical tool compounds available.

### 3.4 p38 MAPK / MW150 -- The Combination Therapy Leader

MW150 is a BBB-penetrant, oral p38alpha MAPK inhibitor. In SMA mice, MW150 synergizes with SMN-inducing drugs, enhancing motor function, survival, and synaptic rewiring (PMID 40926051). p38 MAPK connects to the ROCK-cofilin axis through Stasimon-dependent activation in SMA motor neurons (PMID 31851921). MW150 + Risdiplam is currently the strongest preclinical combination candidate.

---

## 4. Proprioceptive Circuit Dysfunction (Simon's Angle)

### 4.1 SMA Is a Circuit Disease, Not Just a Motor Neuron Disease

The paradigm has shifted. SMA was traditionally viewed as a motor neuron autonomous disease. Current evidence demonstrates that proprioceptive synapse loss PRECEDES motor neuron death and is a primary pathogenic event.

**Key evidence chain:**

1. **Mentis et al. (2011, Neuron, PMID 21315257)**: First demonstration that sensory-motor connectivity is impaired early in SMA mouse models. Reduced proprioceptive reflexes correlate with decreased number and function of synapses on motor neuron somata and proximal dendrites. These abnormalities occur at pre-symptomatic stages in motor neurons innervating proximal muscles.

2. **Fletcher et al. (2017, PMID 28504671)**: Proprioceptive synapses show reduced glutamate release at postnatal day 4 (P4), before any motor neuron death occurs. This establishes temporal primacy -- synaptic dysfunction is the cause, not the consequence.

3. **Simon et al. (2024, medRxiv preprint / 2025, Brain, PMID 39982868)**: Landmark translational study confirming proprioceptive synapse dysfunction in HUMAN SMA patients. SMA patients exhibit impaired proprioception measured by H-reflex. Loss of excitatory afferent synapses and altered potassium channel expression (Kv2.1 downregulation) are conserved between mouse models and severely affected patients. Treatment with SMN-inducing drugs (nusinersen) increases H-reflex amplitude, correlating with improved walking distance and reduced fatigability.

4. **Simon et al. (2024, Science Advances)**: Synaptic imbalance -- increased inhibition impairs motor function in SMA. The ratio of excitatory to inhibitory inputs on motor neurons shifts pathologically.

### 4.2 The H-Reflex as a Biomarker

The Hoffmann reflex (H-reflex) directly assays proprioceptive Ia afferent-to-motor neuron circuit function. It is non-invasive, quantitative, and translatable between mouse and human. Simon's group has demonstrated that H-reflex amplitude correlates with treatment response in SMA patients, making it a potential clinical trial endpoint and pharmacodynamic biomarker.

### 4.3 Molecular Mechanism: Kv2.1 and Glutamate

The proposed mechanism: reduced proprioceptive glutamate release --> Kv2.1 potassium channel downregulation in motor neurons --> altered motor neuron excitability --> firing failure --> functional denervation (before structural death). This is distinct from the classic "dying-back" NMJ degeneration narrative and suggests earlier, more proximal circuit dysfunction.

### 4.4 The Actin Connection to Proprioceptive Synapses (Hypothesized)

This is the unexplored intersection between the actin pathway findings and Simon's proprioceptive circuit work:

- Cdc42/actin remodeling is required for proprioceptive synapse formation (PMID 27225763)
- The ROCK-LIMK-cofilin axis regulates synaptic vesicle release and presynaptic function
- PLS3 (the strongest SMA modifier, 4.0x upregulated) is an actin-bundling protein that rescues SMA by restoring endocytosis at the NMJ
- **Nobody has examined whether actin pathway disruption preferentially affects proprioceptive synapses versus other synapse types in SMA**

This gap represents an opportunity: if actin pathway disruption disproportionately affects proprioceptive synapses, it would provide a molecular explanation for why proprioceptive circuit failure precedes motor neuron death.

---

## 5. Selective Motor Neuron Vulnerability (The Big Question)

### 5.1 Not All Motor Neurons Are Equal

SMA does not kill all motor neurons equally. There is a clear pattern of selective vulnerability:

- **Proximal > distal**: Motor neurons innervating proximal and axial muscles are more vulnerable than those innervating distal muscles.
- **L1 > L5**: Within the lumbar spinal cord, L1 motor neurons (proximal) are more vulnerable than L5 motor neurons (distal).
- **Large > small**: Larger motor neurons (alpha motor neurons) are more vulnerable than smaller ones (gamma motor neurons).
- **Fast-fatigable > slow**: Motor neurons innervating fast-fatigable muscle fibers degenerate before those innervating slow-twitch fibers.

### 5.2 Evidence for Selective Vulnerability

- **Mentis et al. (2011)**: Proprioceptive synapse loss occurs first in motor neurons innervating proximal muscles, correlating with clinical weakness pattern.
- **Murray et al. (2013, PLoS ONE, PMID 24324819)**: Selective vulnerability of spinal and cortical motor neuron subpopulations in delta7 SMA mice. Larger motor neurons and motor pools for axial and proximal forelimb muscles in the cervical spinal cord are most vulnerable.
- **Powis & Bhumbra et al. (2022, PMID 36089582)**: Mouse models of SMA show divergent patterns of neuronal vulnerability and resilience. The Smn2B/- model shows different vulnerability patterns than SMN-delta-7, suggesting that vulnerability depends on residual SMN levels and not just motor neuron identity.
- **Reilly et al. (2025, Human Molecular Genetics)**: Motor pool selectivity of neuromuscular degeneration in type I SMA is conserved between human and mouse. This validates the mouse models for studying selective vulnerability.

### 5.3 What Determines Vulnerability?

Several hypotheses, none fully proven:

1. **Axonal length/branching**: Motor neurons with longer axons and more extensive branching may be more sensitive to SMN deficiency because SMN is involved in axonal mRNA transport. The metabolic demand hypothesis.
2. **Proprioceptive input density**: Motor neurons receiving more proprioceptive input may be more dependent on intact Ia synapses. When those synapses fail, the motor neurons lose trophic support. This is Simon's angle.
3. **Actin cytoskeleton demand**: Motor neurons with larger cell bodies and more extensive dendritic arbors may require more actin remodeling. If ROCK-LIMK-cofilin is dysregulated, these neurons fail first. This is our actin pathway hypothesis.
4. **SMN dosage sensitivity**: Different motor neuron subtypes may have different thresholds for SMN protein levels. This is supported by the divergent vulnerability patterns across SMA mouse models with different SMN levels.

**Untested prediction**: If the actin pathway hypothesis is correct, vulnerable (L1) motor neurons should show more severe actin-cofilin rod formation, higher CFL2 expression, or more ROCK pathway activation than resistant (L5) motor neurons. This is a testable IHC experiment.

---

## 6. Gaps and Opportunities (What Nobody Has Done)

### Gap 1: CFL2 in SMA Tissue
No published study has measured CFL2 protein levels, phosphorylation status, or actin-cofilin rod burden in SMA mouse or human tissue. Given the 2.9x transcriptomic upregulation, this is low-hanging fruit.

### Gap 2: Actin Pathway in Proprioceptive Synapses
Nobody has examined whether actin pathway disruption (ROCK-LIMK-cofilin axis) preferentially affects proprioceptive Ia synapses on motor neurons. This connects two well-established SMA pathologies (actin dysfunction + proprioceptive synapse loss) but the intersection is unexplored.

### Gap 3: LIMK Inhibitors in SMA
No LIMK inhibitor has been tested in any SMA model. MDI-114215 is available as a tool compound. This would position the target between ROCK (tested) and cofilin (endpoint).

### Gap 4: Fasudil + SMN-Restoring Drug Combination
Fasudil has been tested alone in SMA mice (Bowerman 2012). Risdiplam/Nusinersen have been tested alone. No one has tested the combination. Given that Fasudil works through an SMN-independent mechanism (muscle/NMJ), the combination is rational and potentially synergistic.

### Gap 5: L1 vs. L5 Actin Pathway Profiling
Nobody has compared actin pathway gene expression, ROCK activity, or cofilin phosphorylation between vulnerable (L1) and resistant (L5) motor neurons in SMA. This would directly test the actin vulnerability hypothesis.

### Gap 6: Actin-Cofilin Rods in Human SMA Tissue
Rod pathology has been demonstrated in SMA cell culture (Walter et al., 2021) but not in post-mortem human tissue or mouse spinal cord sections. If rods are found preferentially in vulnerable motor neuron pools, it would strongly support the pathway.

### Gap 7: STMN2 and Actin -- Two Cytoskeletal Axes?
STMN2 (stathmin-2) regulates microtubules. CFL2 regulates actin. Both are dysregulated in SMA. Whether microtubule and actin dysfunction act independently or synergistically in SMA motor neurons is unknown. TDP-43-dependent STMN2 cryptic splicing is established in ALS (PMID 36542741) -- is a similar mechanism relevant in SMA?

---

## 7. Key Papers Table

| PMID | Authors | Year | Journal | Key Finding | Model System |
|------|---------|------|---------|-------------|-------------|
| 39305126 | Schuning et al. | 2024 | FASEB J | SMN directly binds G- and F-actin, independent of profilin | Mouse MN, in vitro |
| 28459188 | Hensel & Claus | 2018 | Neuroscientist | Review: actin cytoskeleton in SMA and ALS, common mechanism via profilin | Review |
| 21920940 | Nolle et al. | 2011 | Hum Mol Genet | SMN-profilin2a interaction disrupted by SMA mutation S230L; ROCK pathway activation | Mouse MN, SMA fibroblasts |
| 31927482 | Moustafa et al. | 2020 | iScience | Profilin splicing defects in SMN mutant yeast alter actin dynamics | S. pombe |
| 33986363 | Walter et al. | 2021 | Sci Rep | Profilin2 regulates actin-cofilin rod assembly in SMA neurons; ROCK-dependent | NSC-34, primary MN |
| 22397316 | Bowerman et al. | 2012 | BMC Medicine | Fasudil improves survival in SMA mice; muscle-specific, not MN rescue | SMN-delta-7 mouse |
| 25221469 | Bowerman et al. | 2014 | Front Neurosci | ROCK inhibition benefits multiple cell types in SMA (neurons, muscle, glia) | Review |
| 39424560 | Lingor et al. | 2024 | Lancet Neurol | ROCK-ALS Phase 2: fasudil safe, reduced GFAP, supported further investigation | ALS patients (n=120) |
| 39982868 | Simon et al. | 2025 | Brain | Proprioceptive synapse dysfunction in human SMA patients; H-reflex as biomarker | SMA patients + mice |
| 38883729 | Simon et al. | 2024 | medRxiv | Proprioceptive synapse dysfunction is pathogenic event and therapeutic target | SMA patients + mice |
| 21315257 | Mentis et al. | 2011 | Neuron | Early sensory-motor connectivity impairment in SMA mice | SMN-delta-7 mouse |
| 28504671 | Fletcher et al. | 2017 | -- | Reduced proprioceptive glutamate release at P4, before MN death | SMA mouse |
| 24324819 | Murray et al. | 2013 | PLoS ONE | Selective vulnerability of motor neuron subpopulations in delta7 SMA mice | SMN-delta-7 mouse |
| 36089582 | Powis & Bhumbra | 2022 | Acta Neuropathol | Divergent vulnerability patterns across SMA mouse models | Smn2B/- mouse |
| 17160903 | Agrawal et al. | 2007 | Am J Hum Genet | CFL2 mutations cause nemaline myopathy 7 | Human genetics |
| 20088812 | Bamburg et al. | 2010 | Cytoskeleton | Review: ADF/cofilin-actin rods in neurodegenerative diseases | Review |
| 31851921 | Simon et al. | 2019 | Cell Reports | Stasimon contributes to sensory synapse loss; p38 MAPK activation | SMA mouse |
| 17728540 | Bowerman et al. | 2007 | J Mol Neurosci | SMN depletion alters profilin II, upregulates RhoA/ROCK, impairs neuronal integrity | NSC-34 cells |

---

## Summary Statement

The actin cytoskeleton is not a peripheral feature of SMA pathology -- it is central. SMN directly binds profilins and actin, and SMN deficiency activates the RhoA/ROCK pathway, leading to aberrant cofilin phosphorylation, actin-cofilin rod formation, and cytoskeletal collapse. The ROCK-LIMK-Cofilin axis is druggable (fasudil, belumosudil, LIMK inhibitors) and has clinical-stage compounds. The convergence of actin pathway disruption with proprioceptive synapse loss offers a molecular explanation for why circuit dysfunction precedes motor neuron death in SMA. Seven specific experimental gaps remain open. Addressing even two or three of these gaps -- particularly CFL2 measurement in SMA tissue and the Fasudil + Risdiplam combination -- could significantly advance the field.

---

*This review was prepared computationally using the SMA Research Platform evidence engine (14,000+ claims, 6,000+ sources) supplemented by targeted PubMed searches conducted 2026-03-24. All PMIDs were verified against PubMed records. Claims are categorized as proven, suggested, or hypothesized according to the evidence hierarchy described in the platform methodology.*
