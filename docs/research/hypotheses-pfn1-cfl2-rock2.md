# Hypotheses: PFN1, CFL2, and ROCK2 in SMA

**Generated**: 2026-03-22
**Status**: Draft for platform integration
**Confidence calibration**: Scores reflect strength of direct SMA evidence + mechanistic plausibility + cross-disease validation

---

## Table of Contents

1. [PFN1 (Profilin 1) Hypotheses](#1-pfn1-profilin-1)
2. [CFL2 (Cofilin 2) Hypotheses](#2-cfl2-cofilin-2)
3. [ROCK2 (Rho-associated kinase 2) Hypotheses](#3-rock2-rho-associated-kinase-2)
4. [Cross-Target Convergence Hypotheses](#4-cross-target-convergence)
5. [Drug Candidates Summary](#5-drug-candidates-summary)
6. [Cross-Disease Connections](#6-cross-disease-connections)
7. [Recent Literature (2024-2026)](#7-recent-literature-2024-2026)
8. [Sources](#8-sources)

---

## 1. PFN1 (Profilin 1)

**Context**: PFN1 is +46% upregulated in SMA organoids (strongest actin signal in the dataset). PFN1 mutations cause familial ALS (PMID 22801503). SMN directly interacts with Profilin2a (PMID 21920940). AAV-delivered PFN1 promotes CNS axon regeneration (PMID 31945017).

### Hypothesis 1.1: PFN1 Upregulation as Compensatory Rescue Attempt

**Title**: PFN1 overexpression in SMA is a compensatory response to SMN-profilin2a axis disruption

**Mechanism**: In healthy motor neurons, SMN binds profilin2a (PFN2) to regulate actin polymerization at growth cones and synapses. When SMN levels drop in SMA, the SMN-PFN2 complex is disrupted, leading to defective actin dynamics (Schuning et al. 2024, FASEB). The cell upregulates PFN1 (+46%) as a partial compensatory mechanism, since PFN1 shares actin-binding capacity but lacks the neuron-specific PFN2 regulatory context. This compensation is incomplete because PFN1 cannot fully substitute for PFN2 in SMN-dependent complexes.

**Supporting evidence**:
- SMN directly binds profilin2a and regulates actin dynamics (PMID 21920940, PMID 19497369)
- Schuning 2024: SMN regulates two actin populations -- SMN-PFN2a-actin and SMN-actin; SMA disrupts both (DOI: 10.1096/fj.202300183R)
- PFN1 and PFN2 share ~60% sequence identity but have distinct regulatory roles in neurons (PMID 34571959)
- PFN1 +46% upregulation in SMA organoids (platform dataset)

**Confidence**: 0.72

**Required experiment**: siRNA knockdown of PFN1 in SMA motor neuron cultures. If compensatory, PFN1 knockdown should accelerate neurite degeneration and worsen actin dynamics. Measure F/G-actin ratios, neurite length, and growth cone morphology with/without PFN1 suppression.

**SMA therapeutic connection**: If confirmed, this argues AGAINST PFN1 inhibition and FOR PFN1 augmentation as a therapeutic strategy -- potentially via AAV-PFN1 delivery analogous to Bhatt et al. 2020.

---

### Hypothesis 1.2: AAV-PFN1 Gene Therapy as SMN-Independent Axon Rescue

**Title**: AAV-delivered constitutively active PFN1 can rescue motor neuron axonal defects independently of SMN restoration

**Mechanism**: Bhatt et al. (2020) demonstrated that AAV-delivered constitutively active PFN1 promotes axon regeneration, NMJ maturation, and functional recovery in spinal cord injury models by coordinating actin retrograde flow and microtubule dynamics in growth cones. In SMA, motor neuron axons degenerate due to disrupted actin dynamics downstream of SMN loss. Delivering active PFN1 could bypass the broken SMN-PFN2a axis and directly restore cytoskeletal function needed for axon maintenance and NMJ integrity.

**Supporting evidence**:
- AAV-PFN1 promotes axon regeneration and NMJ maturation in rodent spinal cord injury (PMID 31945017)
- SMA motor neurons show axonal defects and NMJ degeneration as primary pathology
- PFN1 already upregulated in SMA (+46%), suggesting the pathway is active but insufficient -- a stronger/constitutively active form may cross the threshold
- SMN-independent therapies are an identified unmet need (Hensel & Claus 2020, Frontiers)

**Confidence**: 0.55

**Required experiment**: AAV9-PFN1(CA) delivery to SMA delta7 mice (intrathecal). Primary endpoints: motor neuron survival, NMJ morphology (pretzel-like vs. denervated), survival extension. Compare to nusinersen alone and combination.

**SMA therapeutic connection**: This would be an SMN-independent combinatorial therapy -- could complement nusinersen/risdiplam in patients who respond suboptimally to SMN restoration alone.

**SPECULATIVE FLAG**: No AAV-PFN1 has been tested in any SMA model. The leap from spinal cord injury to SMA is mechanistically plausible but unvalidated.

---

### Hypothesis 1.3: PFN1-ALS/SMA Convergence on Actin Toxicity

**Title**: PFN1 gain-of-function (ALS) and SMN loss-of-function (SMA) converge on the same actin-rod toxicity pathway

**Mechanism**: ALS-causing PFN1 mutations (C71G, M114T, A20T, G118V) cause protein aggregation and TDP-43 pathology (PMID 22801503, PMID 26929031). In SMA, SMN loss dysregulates actin dynamics through the profilin axis (Schuning 2024). Both diseases show actin-cofilin rod formation, motor neuron degeneration, and NMJ pathology. The convergence point is likely the actin polymerization/depolymerization equilibrium: mutant PFN1 aggregates and loses actin-binding function (loss of polymerization), while SMN loss causes excess free profilin2 driving aberrant ROCK-mediated signaling. Both endpoints produce toxic actin rods and sequester essential cellular machinery.

**Supporting evidence**:
- PFN1 mutations cause fALS (PMID 22801503)
- Protein network analysis reveals functional connectivity between ALS and SMA (PMID 35406253)
- Actin-cofilin rods form in SMA cell models (Walter et al. 2021, PMID 33986363)
- Both diseases show NMJ pathology and motor neuron selectivity
- Hensel & Claus 2018: actin cytoskeleton is the convergence point for SMA and ALS (PMID 28459182)

**Confidence**: 0.68

**Required experiment**: Compare actin rod composition (proteomics) between PFN1-C71G ALS iPSC motor neurons and SMA iPSC motor neurons. If the rod proteome is similar, this confirms shared toxicity mechanism and validates cross-disease drug repurposing.

**SMA therapeutic connection**: Drugs developed for PFN1-ALS could be repurposed for SMA. Conversely, SMA-specific actin modulators could benefit ALS patients.

---

### Hypothesis 1.4: PFN1 as SMA Treatment Response Biomarker

**Title**: Serum PFN1 levels track treatment response in SMA patients on nusinersen/risdiplam

**Mechanism**: Profilin-1 concentrations are elevated in untreated SMA type 3 patients compared to healthy controls and decrease during nusinersen treatment, reaching control levels at the maintenance phase (Wurster et al. 2024, PMID: PMC11414805). This suggests PFN1 is released from stressed/degenerating motor neurons and decreases as SMN restoration reduces cellular stress. PFN1 could serve as a pharmacodynamic biomarker complementing neurofilament light chain (NfL).

**Supporting evidence**:
- PFN1 elevated at baseline in SMA type 3, normalizes with nusinersen (PMC11414805)
- NfL is established but imperfect SMA biomarker
- PFN1 is mechanistically linked to SMA pathology (not just a nonspecific damage marker)

**Confidence**: 0.78

**Required experiment**: Longitudinal cohort study measuring serum PFN1 in SMA types 1-3 on risdiplam/nusinersen. Correlate PFN1 trajectories with motor function scores (HFMSE, RULM). Determine if PFN1 adds predictive value beyond NfL alone.

**SMA therapeutic connection**: A validated biomarker would enable faster clinical trials and better patient stratification for combination therapies.

---

## 2. CFL2 (Cofilin 2)

**Context**: CFL2 is 2.9x upregulated in SMA. ZERO SMA-specific publications. Actin-cofilin rods form in SMA cell models (Walter 2021, PMID 33986363). ROCK phosphorylates LIMK, which phosphorylates cofilin, inactivating it. Dephosphorylated (active) cofilin severs actin and participates in rod formation. CFL2 mutations cause congenital myopathy (PMID 22025600).

### Hypothesis 2.1: CFL2 Overactivation Drives Actin Rod Toxicity in SMA Motor Neurons

**Title**: Excess active (dephosphorylated) CFL2 drives actin-cofilin rod formation in SMA motor neurons, sequestering essential proteins

**Mechanism**: In SMA, the ROCK-LIMK-cofilin signaling axis is dysregulated. Walter et al. (2021) showed that actin rods in SMA cell models contain cofilin proteins and sequester proteins involved in ubiquitination, translation, and protein folding. CFL2 at 2.9x overexpression provides excess substrate for rod formation. When the ratio of active (dephosphorylated) cofilin to actin exceeds a threshold, cofilin-actin rods nucleate and grow, blocking axonal transport and trapping essential cellular machinery. This is particularly damaging in long motor neuron axons where transport blockade leads to distal degeneration.

**Supporting evidence**:
- CFL2 2.9x upregulated in SMA organoids (platform dataset)
- Actin rods in SMA contain cofilin and sequester critical proteins (PMID 33986363)
- Cofilin-actin rods block neurite transport and cause synaptic loss in Alzheimer models (PMID 20088812, PMC4458070)
- CFL2 knockout mice show progressive sarcomeric disruption and muscle wasting (PMID 22025600)
- Cytoplasmic rod formation triggered by metabolic stress (PMC: 10.3389/fcell.2021.742310)

**Confidence**: 0.65

**Required experiment**: Quantify phospho-CFL2 vs. total CFL2 ratio in SMA vs. control motor neurons (Western blot + immunofluorescence). Image actin rod formation with live-cell microscopy. Test whether CFL2 knockdown (shRNA) reduces rod burden and rescues axonal transport.

**SMA therapeutic connection**: If CFL2 is the primary cofilin driving rods in motor neurons, it becomes a specific therapeutic target -- more precise than pan-ROCK inhibition.

---

### Hypothesis 2.2: Fasudil Dissolves CFL2-Actin Rods via ROCK-LIMK-Cofilin Pathway

**Title**: ROCK inhibition by fasudil reduces CFL2-actin rod burden in SMA motor neurons by modulating the phosphorylation balance

**Mechanism**: This is mechanistically counterintuitive and requires careful consideration. ROCK phosphorylates LIMK, which phosphorylates cofilin (inactivating it). ROCK inhibition by fasudil should REDUCE cofilin phosphorylation, producing MORE active cofilin -- which could INCREASE rod formation. However, Walter et al. (2021) showed that ROCK/profilin2 signaling regulates rod assembly, and fasudil improved SMA mouse survival (Bowerman et al. 2012, PMID 22397316). The resolution may be that ROCK inhibition primarily acts by: (a) reducing excess profilin2 phosphorylation that drives aberrant actin dynamics, (b) normalizing the overall RhoA-ROCK hyperactivation in SMA, or (c) the survival benefit is mediated through non-cofilin ROCK targets (myosin, ERM proteins, NMJ maturation).

**Supporting evidence**:
- Fasudil improves survival + muscle development in SMA mice (PMID 22397316)
- ROCK inhibition rescues NMJ morphology in SMA (Bowerman et al. 2012)
- Walter 2021: ROCK/profilin2 involvement in rod assembly (PMID 33986363)
- ROCK activity enhanced in SMA mouse spinal cord (PMID 25221469)

**Confidence**: 0.58

**IMPORTANT CAVEAT**: The relationship between ROCK inhibition and cofilin-actin rods is paradoxical. ROCK inhibition reduces p-cofilin, increasing active cofilin. It is unclear whether the net effect on rods is positive or negative. This requires direct experimental testing.

**Required experiment**: Treat SMA motor neuron cultures with fasudil (1-30 uM). Quantify: (a) rod count per neurite, (b) p-CFL2/CFL2 ratio, (c) axonal transport velocity, (d) NMJ formation in co-culture. This will determine whether fasudil's benefit in SMA is mediated through or independent of the cofilin-rod pathway.

**SMA therapeutic connection**: Fasudil is already in ALS Phase 2 (ROCK-ALS trial, Lancet Neurology 2024). If it works via actin rod dissolution in SMA, it could be rapidly repurposed.

---

### Hypothesis 2.3: CFL2 as a Muscle-Specific Contributor to SMA Peripheral Pathology

**Title**: CFL2 overexpression in SMA drives skeletal muscle pathology independently of motor neuron degeneration

**Mechanism**: CFL2 is the predominant cofilin isoform in skeletal muscle. CFL2 knockout mice develop progressive sarcomeric disruption with actin accumulations (PMID 22025600). In SMA, skeletal muscle shows intrinsic defects beyond denervation. The 2.9x CFL2 upregulation could directly impair sarcomeric actin turnover, contributing to the muscle-intrinsic pathology seen in SMA. This would represent a peripheral, SMN-independent disease mechanism that persists even after motor neuron rescue.

**Supporting evidence**:
- CFL2 is the muscle-specific cofilin isoform
- CFL2 knockout causes myopathy with actin accumulation (PMID 22025600)
- CFL2 mutations cause nemaline myopathy in humans (PMID 22025600)
- SMA has intrinsic skeletal muscle defects beyond denervation
- Fasudil improves muscle fiber size in SMA mice independently of motor neuron preservation (PMID 22397316)

**Confidence**: 0.60

**Required experiment**: Conditional CFL2 knockdown specifically in skeletal muscle of SMA mice (Cre-lox under muscle promoter). Measure muscle fiber size, NMJ morphology, and motor function. If muscle-specific CFL2 normalization improves phenotype, this validates a peripheral therapeutic target.

**SMA therapeutic connection**: Muscle-targeted therapies (like apitegromab/anti-myostatin) are gaining traction. CFL2 modulation in muscle could be a complementary peripheral target.

---

### Hypothesis 2.4: CFL2 Phosphorylation Status as Diagnostic Marker for Actin Pathway Activation in SMA

**Title**: The p-CFL2/CFL2 ratio in patient-derived cells predicts actin pathway dysregulation severity and treatment response

**Mechanism**: The balance between phosphorylated (inactive) and dephosphorylated (active) CFL2 reflects the net activity of the ROCK-LIMK-cofilin axis. In SMA patients, this ratio may vary based on SMN2 copy number, disease severity, and treatment status. Measuring this ratio in accessible cells (fibroblasts, iPSC-derived motor neurons, or potentially PBMCs) could provide a functional readout of actin pathway health.

**Confidence**: 0.45

**SPECULATIVE FLAG**: No data exist on CFL2 phosphorylation status in SMA patient samples. This is a hypothesis-generating proposal.

**Required experiment**: Measure p-CFL2/total CFL2 in fibroblasts from SMA type 1, 2, and 3 patients vs. carriers vs. controls. Correlate with SMN2 copy number and motor function scores.

**SMA therapeutic connection**: Would enable patient stratification for ROCK/LIMK inhibitor trials.

---

## 3. ROCK2 (Rho-associated kinase 2)

**Context**: Central kinase in the RhoA-ROCK-LIMK-cofilin pathway. ROCK activity elevated in SMA mouse spinal cord. Fasudil (pan-ROCK inhibitor) extends SMA mouse survival. Fasudil Phase 2 in ALS (ROCK-ALS, Lancet Neurology 2024) showed safety and dose-dependent efficacy signals. ROCK2 is the predominant isoform in brain/spinal cord. MDI-117740 is a next-generation LIMK inhibitor (J Med Chem 2025).

### Hypothesis 3.1: ROCK2-Selective Inhibition is Superior to Pan-ROCK Inhibition in SMA

**Title**: ROCK2-selective inhibitors provide better motor neuron protection with fewer peripheral side effects than pan-ROCK inhibitors in SMA

**Mechanism**: ROCK1 is ubiquitously expressed and regulates smooth muscle contraction, blood pressure, and cardiac function. ROCK2 is enriched in brain and spinal cord. Fasudil inhibits both ROCK1 and ROCK2, causing dose-limiting hypotension. A ROCK2-selective inhibitor would specifically target the CNS-relevant isoform, allowing higher effective doses in the nervous system with reduced cardiovascular side effects. In SMA, ROCK2 hyperactivation in motor neurons drives: (a) LIMK-cofilin axis dysregulation, (b) aberrant profilin2 phosphorylation, (c) actin rod formation, and (d) impaired axonal transport.

**Supporting evidence**:
- ROCK2 is the predominant CNS isoform
- ROCK activity elevated in SMA spinal cord (PMID 25221469)
- Fasudil (pan-ROCK) improves SMA mouse survival but with systemic effects (PMID 22397316)
- ROCK-ALS Phase 2: fasudil safe but dose-dependent efficacy suggests higher doses needed (Lancet Neurology 2024, PMID 39424560)
- ROCK2-selective inhibitors (e.g., KD025/belumosudil) exist and are FDA-approved for cGVHD

**Confidence**: 0.62

**Required experiment**: Compare fasudil (pan-ROCK) vs. belumosudil (ROCK2-selective) in SMA delta7 mice. Endpoints: survival, motor function, NMJ morphology, blood pressure, cardiac function. If ROCK2-selective shows equal efficacy with better tolerability, this de-risks clinical translation.

**SMA therapeutic connection**: Belumosudil (Rezurock) is already FDA-approved for chronic graft-versus-host disease. Repurposing for SMA would be a rapid path to clinical testing.

---

### Hypothesis 3.2: Fasudil as First Combinatorial SMN-Independent Therapy for SMA

**Title**: Fasudil combined with nusinersen/risdiplam provides additive benefit in SMA by rescuing actin dynamics that SMN restoration alone cannot fully normalize

**Mechanism**: Schuning et al. (2024) showed that SMN restoration in SMA cells only partially rescues the SMN-actin co-localization pattern and F/G-actin ratios. This means that even optimal SMN-enhancing therapy leaves residual actin dysfunction. Fasudil, by inhibiting the hyperactivated ROCK pathway downstream of SMN, could normalize the actin dynamics that persist after SMN restoration. The combination addresses both the root cause (SMN deficiency) and a downstream consequence (ROCK hyperactivation) that becomes partially autonomous.

**Supporting evidence**:
- Schuning 2024: SMN restoration only partially rescues actin dynamics (DOI: 10.1096/fj.202300183R)
- Fasudil improves SMA mouse survival independently of SMN upregulation (PMID 22397316)
- ROCK-ALS Phase 2: fasudil safe and tolerable, dose-dependent efficacy (PMID 39424560)
- Oral fasudil (Bravyl) in Phase 2a for ALS, 300mg dose under investigation
- Need for SMN-independent combination therapies is recognized (Hensel & Claus 2020)

**Confidence**: 0.70

**Required experiment**: SMA delta7 mice treated with: (a) risdiplam alone, (b) fasudil alone, (c) risdiplam + fasudil, (d) vehicle. Primary endpoints: survival, motor function (rotarod, grip strength), NMJ innervation, motor neuron counts. If combination > either alone, this supports clinical combination trials.

**SMA therapeutic connection**: This is the most immediately translatable hypothesis. Fasudil has human safety data (ROCK-ALS). Nusinersen/risdiplam are approved. A combination trial could be designed within 1-2 years.

---

### Hypothesis 3.3: LIMK Inhibition Downstream of ROCK is More Precise for Actin Rod Prevention

**Title**: LIMK1/2 inhibition with MDI-117740 prevents actin-cofilin rod formation more precisely than ROCK inhibition by targeting the rod-forming branch while sparing other ROCK functions

**Mechanism**: ROCK has many substrates beyond LIMK: myosin light chain (MLC), ERM proteins, PTEN, tau. Pan-ROCK inhibition affects all these pathways, causing diverse effects (some beneficial, some not). LIMK is specifically upstream of cofilin phosphorylation, which directly controls actin rod dynamics. Inhibiting LIMK with MDI-117740 (the most selective LIMK inhibitor reported, J Med Chem 2025) would specifically modulate the cofilin-actin rod pathway while leaving other ROCK-dependent signaling intact.

**Supporting evidence**:
- MDI-117740: potent dual LIMK1/2 inhibitor, highly selective, suitable for in vivo (J Med Chem 2025, DOI: 10.1021/acs.jmedchem.5c00974)
- LIMK to cofilin phosphorylation is the direct upstream regulator of rod dynamics
- MDI-114215 (related LIMK inhibitor) developed for Fragile X Syndrome, a neurodevelopmental disorder (J Med Chem 2025, DOI: 10.1021/acs.jmedchem.4c02694)
- ROCK has >20 substrates; LIMK inhibition is more targeted

**Confidence**: 0.50

**SPECULATIVE FLAG**: MDI-117740 has not been tested in any motor neuron disease model. Its selectivity is based on kinome profiling, not disease-specific validation. The relationship between LIMK inhibition and rod prevention is inferred, not demonstrated.

**Required experiment**: Test MDI-117740 in SMA motor neuron cultures. Measure: (a) p-cofilin/cofilin ratio, (b) actin rod count, (c) neurite integrity, (d) compare to fasudil at equi-effective concentrations for cofilin dephosphorylation. If LIMK inhibition shows better rod reduction with fewer off-target effects, this justifies in vivo testing.

**SMA therapeutic connection**: MDI-117740 represents a next-generation approach to the same pathway targeted by fasudil, with potentially better specificity. Also connects to Fragile X Syndrome, broadening the neurodevelopmental disease overlap.

---

### Hypothesis 3.4: ROCK2 Hyperactivation Mediates NMJ Degeneration via Postsynaptic Actin Collapse

**Title**: Elevated ROCK2 activity in SMA causes postsynaptic endplate degeneration by disrupting the actin scaffold that maintains acetylcholine receptor clusters

**Mechanism**: NMJ postsynaptic endplates depend on an actin scaffold to maintain the characteristic "pretzel-like" AChR cluster morphology. ROCK2 hyperactivation in SMA muscle cells could destabilize this scaffold through excess actomyosin contractility and cofilin-mediated actin severing. Fasudil treatment in SMA mice increases endplate size (PMID 22397316), consistent with ROCK inhibition allowing the actin scaffold to reform. The NMJ defect may be a direct consequence of ROCK2 hyperactivation in the postsynaptic muscle cell, not just secondary to presynaptic motor neuron degeneration.

**Supporting evidence**:
- Fasudil increases postsynaptic endplate size in SMA mice (PMID 22397316)
- ROCK inhibition rescues NMJ morphology in SMA (Bowerman et al. 2012)
- AChR clustering depends on actin cytoskeleton (established biology)
- SMA NMJ defects include endplate denervation and size reduction

**Confidence**: 0.60

**Required experiment**: Muscle-specific ROCK2 knockdown (or muscle-targeted fasudil delivery via nanoparticle) in SMA mice. Assess NMJ morphology specifically. If postsynaptic endplate rescue occurs without motor neuron rescue, this proves a muscle-autonomous ROCK2 mechanism.

**SMA therapeutic connection**: Supports the growing evidence for peripheral/muscle-directed SMA therapies as combination approaches.

---

## 4. Cross-Target Convergence

### Hypothesis 4.1: The PFN1-ROCK2-CFL2 Axis is a Single Druggable Pathway in SMA

**Title**: PFN1 upregulation, ROCK2 hyperactivation, and CFL2 overexpression represent a coherent actin-rod toxicity pathway that can be targeted at multiple nodes

**Mechanism**: In SMA motor neurons, SMN loss disrupts the SMN-profilin2a complex, freeing excess profilin2 that is phosphorylated by hyperactivated ROCK2. This triggers a cascade: ROCK2 also activates LIMK, which phosphorylates cofilin. Simultaneously, CFL2 is upregulated 2.9x, flooding the system with cofilin substrate. PFN1 is upregulated +46% as a compensatory attempt. The net result is oscillation between states: too much actin polymerization (from PFN1) and too much severing (from active CFL2), with the debris nucleating into toxic actin-cofilin rods. The optimal therapeutic strategy may be multi-node intervention: ROCK2 inhibition (fasudil/belumosudil) + PFN1 augmentation (AAV) + rod dissolution (LIMK inhibitor).

**Supporting evidence**:
- All three targets upregulated/hyperactivated in SMA
- Walter 2021 confirmed ROCK/profilin2/cofilin involvement in SMA rod formation (PMID 33986363)
- Schuning 2024 confirmed SMN-profilin-actin axis disruption (DOI: 10.1096/fj.202300183R)
- Individual pathway components validated by separate studies

**Confidence**: 0.55

**SPECULATIVE FLAG**: The integrated model connecting all three targets has not been tested as a unified pathway. Each component has individual evidence, but the systems-level interaction is inferred.

**Required experiment**: Multi-omics profiling (phosphoproteomics + live actin imaging) of SMA motor neurons treated with: (a) ROCK inhibitor alone, (b) LIMK inhibitor alone, (c) PFN1 overexpression alone, (d) combinations. Map the signaling network to identify the optimal intervention point(s).

---

## 5. Drug Candidates Summary

| Drug | Target | Status | SMA Evidence | Source |
|------|--------|--------|-------------|--------|
| **Fasudil** (IV) | ROCK1/2 (pan) | ALS Phase 2 complete (ROCK-ALS) | Extends SMA mouse survival, improves NMJ + muscle | PMID 22397316, PMID 39424560 |
| **Bravyl** (oral fasudil) | ROCK1/2 (pan) | ALS Phase 2a (Woolsey Pharma) | None (oral formulation untested in SMA) | alsnewstoday.com |
| **Belumosudil** (Rezurock) | ROCK2-selective | FDA-approved (cGVHD) | None in SMA | FDA label |
| **MDI-117740** | LIMK1/2 (dual) | Preclinical (J Med Chem 2025) | None | DOI: 10.1021/acs.jmedchem.5c00974 |
| **MDI-114215** | LIMK (selective) | Preclinical (Fragile X) | None | DOI: 10.1021/acs.jmedchem.4c02694 |
| **Y-27632** | ROCK1/2 (pan) | Research tool compound | SMA mouse survival benefit | PMID 25221469 |
| **Apitegromab** | Anti-myostatin (muscle) | Phase 3 / BLA resubmission 2026 | Muscle function improvement in SMA | Scholar Rock 2025 |

**Nearest to SMA clinical testing**: Fasudil (has human safety data from ROCK-ALS + SMA preclinical efficacy). Belumosudil (FDA-approved, ROCK2-selective, no SMA data but mechanistically compelling).

---

## 6. Cross-Disease Connections

### ALS
- **PFN1**: Mutations (C71G, M114T, A20T, G118V) CAUSE familial ALS (PMID 22801503). Mutant PFN1 causes TDP-43 aggregation and motor neuron death in mice (PMID 27681617). Actin cytoskeleton is convergence point for SMA and ALS (PMID 28459182).
- **ROCK2/Fasudil**: ROCK-ALS Phase 2 showed safety and dose-dependent efficacy signal (PMID 39424560, Lancet Neurology 2024). Post-hoc analysis (2025 preprint) suggests fasudil attenuates disease spreading in ALS.
- **Shared mechanism**: Both diseases show motor neuron selectivity, NMJ pathology, actin dynamics disruption, and cytoskeletal collapse.

### Alzheimer's Disease
- **Cofilin-actin rods**: Rods accumulate in AD brain, contain phospho-tau, block neurite transport, and may mediate synapse loss and Abeta secretion (PMID 20088812, PMC4458070).
- **ROCK inhibitors**: Under investigation for AD (tau phosphorylation reduction).
- **Relevance to SMA**: Same rod toxicity mechanism but in different neuronal subtypes.

### Huntington's Disease
- **Nuclear actin rods**: Cofilin-actin rods form in heat-shocked neurons; wild-type huntingtin clears them but mutant huntingtin does not (PMC4458070). Rod clearance failure may contribute to HD pathology.
- **ROCK pathway**: RhoA-ROCK signaling implicated in HD striatal neuron vulnerability.

### Fragile X Syndrome
- **LIMK pathway**: MDI-114215 LIMK inhibitor developed specifically for Fragile X (J Med Chem 2025). LIMK overactivation is a core mechanism in Fragile X.
- **Overlap**: Both SMA and Fragile X involve synaptic dysfunction and actin dysregulation.

### Congenital Myopathy
- **CFL2**: Recessive CFL2 mutations cause nemaline myopathy with rods and minicores (PMID 22025600). CFL2 knockout mice show progressive sarcomeric disruption. Direct evidence that CFL2 dysfunction causes muscle disease.

---

## 7. Recent Literature (2024-2026)

### Key Papers

1. **Schuning et al. 2024** - "The spinal muscular atrophy gene product regulates actin dynamics" - FASEB Journal. Demonstrated that SMN regulates two distinct actin populations (SMN-PFN2a-actin and SMN-actin directly). SMN restoration only partially rescues the phenotype. DOI: 10.1096/fj.202300183R

2. **ROCK-ALS Trial 2024** - "Safety, tolerability, and efficacy of fasudil in amyotrophic lateral sclerosis" - Lancet Neurology. Phase 2 RCT: fasudil safe, dose-dependent efficacy on MUNIX. PMID 39424560.

3. **Fasudil Disease Spreading 2025** (preprint) - Post-hoc analysis of ROCK-ALS suggesting fasudil attenuates disease spreading in ALS. DOI: 10.1101/2025.09.02.25334770

4. **MDI-117740 2025** - Tetrahydropyrazolopyridinones as novel selective LIMK inhibitors. J Med Chem. DOI: 10.1021/acs.jmedchem.5c00974

5. **MDI-114215 2025** - LIMK inhibitor for Fragile X Syndrome. J Med Chem. DOI: 10.1021/acs.jmedchem.4c02694

6. **LIMK1 Isoform-Selective 2025** - Covalent targeting for LIMK1 selectivity. J Med Chem. DOI: 10.1021/acs.jmedchem.5c01204

7. **Actin Mutant Phenotypes 2025** - Identification of actin mutants with neurodegenerative disease-like phenotypes. Frontiers Cell Neurosci. DOI: 10.3389/fncel.2025.1543199

8. **Cytoskeleton Dysfunction in SMA 2024** - "Cytoskeleton dysfunction of motor neuron in spinal muscular atrophy" - J Neurology. Reviews the complete cytoskeletal pathology in SMA including profilin-ROCK-cofilin axis. DOI: 10.1007/s00415-024-12724-3

9. **PFN1 Biomarker 2024** - "Neurofilament light chain and profilin-1 dynamics in 30 SMA type 3 patients treated with nusinersen" - PMC11414805

### Not Found / Gaps
- No 2024-2026 papers specifically on CFL2 in SMA (confirming ZERO SMA publications for CFL2)
- No fasudil/ROCK inhibitor trials in SMA patients
- No LIMK inhibitor testing in any motor neuron disease model

---

## 8. Sources

### Primary Research
- [Schuning et al. 2024 - SMN regulates actin dynamics (FASEB)](https://faseb.onlinelibrary.wiley.com/doi/full/10.1096/fj.202300183R)
- [Walter et al. 2021 - Profilin2 regulates actin rod assembly in SMA (PMID 33986363)](https://www.nature.com/articles/s41598-021-89397-9)
- [Bowerman et al. 2012 - Fasudil in SMA mice (PMID 22397316)](https://link.springer.com/article/10.1186/1741-7015-10-24)
- [Wu et al. 2012 - PFN1 mutations cause fALS (PMID 22801503)](https://www.nature.com/articles/nature11280)
- [Bhatt et al. 2020 - PFN1 delivery for axon regeneration (PMID 31945017)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7108904/)
- [Abers et al. 2012 - CFL2 knockout muscle pathology (PMID 22025600)](https://academic.oup.com/hmg/article-abstract/21/10/2341/2900775)

### Clinical Trials
- [ROCK-ALS Phase 2 - Lancet Neurology 2024 (PMID 39424560)](https://www.thelancet.com/journals/laneur/article/PIIS1474-4422(24)00373-9/fulltext)
- [Fasudil disease spreading post-hoc 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12424921/)
- [Bravyl (oral fasudil) Phase 2a for ALS](https://alsnewstoday.com/news/phase-2-trial-rock-inhibitor-bravyl-now-fully-enrolled/)

### Drug Development
- [MDI-117740 LIMK inhibitor (J Med Chem 2025)](https://pubs.acs.org/doi/10.1021/acs.jmedchem.5c00974)
- [MDI-114215 LIMK inhibitor for Fragile X (J Med Chem 2025)](https://pubs.acs.org/doi/10.1021/acs.jmedchem.4c02694)
- [LIMK1 isoform-selective inhibitor (J Med Chem 2025)](https://pubs.acs.org/doi/10.1021/acs.jmedchem.5c01204)

### Reviews
- [Hensel & Claus 2018 - Actin cytoskeleton in SMA and ALS (PMID 28459182)](https://journals.sagepub.com/doi/abs/10.1177/1073858417705059)
- [ROCK inhibition for SMA review (PMID 25221469)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4148024/)
- [Cytoskeleton dysfunction in SMA 2024](https://link.springer.com/article/10.1007/s00415-024-12724-3)
- [Cofilin-actin rods in neurodegeneration (PMC9535683)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9535683/)
- [ADF/cofilin-actin rods review (PMID 20088812)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4458070/)
- [Protein network ALS-SMA connectivity (PMID 35406253)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8966079/)
- [SMN-independent SMA therapies (Hensel & Claus 2020)](https://www.frontiersin.org/journals/neurology/articles/10.3389/fneur.2020.00045/full)
- [PFN1 biomarker in SMA (PMC11414805)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11414805/)
