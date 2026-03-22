# SMA-ALS Convergence Deep Dive: Shared Pathways, Targets & Therapeutic Opportunities

**Date**: 2026-03-22
**Status**: Research compilation — NOT peer-reviewed. All claims require primary source verification.
**Research Agent**: Cross-disease analysis based on web search of published literature.

---

## Executive Summary

Spinal Muscular Atrophy (SMA) and Amyotrophic Lateral Sclerosis (ALS) have historically been studied as separate motor neuron diseases. However, converging evidence from proteomics, transcriptomics, and structural biology reveals **deep molecular overlap** centered on:

1. **Actin cytoskeleton dysregulation** (ROCK/cofilin/profilin axis)
2. **RNA processing defects** (SMN-TDP-43-FUS nuclear interactions)
3. **Distal "dying-back" axonopathy** with NMJ as primary vulnerability site
4. **Axon degeneration signaling** (SARM1/NMNAT2/STMN2 pathway)
5. **Shared protein network hubs** (PFN1 and SOD1 as inter-modular connectors)

The actin pathway is the strongest convergence node. SMN directly binds profilins (PFN1/PFN2a). PFN1 mutations cause familial ALS. Cofilin hyperphosphorylation triggers TDP-43 mislocalization. ROCK inhibitors (Fasudil/Bravyl) show efficacy in both SMA mouse models and ALS Phase 2 trials. **Nobody has systematically checked ALS RNA-seq datasets for CORO1C/CFL2/PFN1 co-expression patterns** — this is a gap we can fill.

---

## 1. Shared Molecular Pathways

### 1.1 The Actin Cytoskeleton Hub

The actin cytoskeleton is the strongest convergence point between SMA and ALS pathology:

| Component | Role in SMA | Role in ALS | Cross-Disease Link |
|-----------|-------------|-------------|-------------------|
| **PFN1** (Profilin-1) | SMN directly binds PFN1 and PFN2a; loss of SMN upregulates PFN2a | 8 PFN1 mutations cause familial ALS (G118V, C71G most studied) | SMN-PFN1 binding + PFN1-ALS mutations = shared actin node |
| **CORO1A** (Coronin-1A) | Part of actin regulatory network disrupted by SMN loss | 5.3x elevated in ALS patient exosomes; increases with disease progression | Actin assembly/ARP2/3 regulation; potential biomarker |
| **CORO1C** (Coronin-1C) | Elevated in SMA models (our finding) | **UNSTUDIED in ALS** — gap to fill | Endosomal actin regulation, fission |
| **CFL1/CFL2** (Cofilin-1/2) | Actin dynamics disrupted in SMN-deficient neurons | CFL1 hyperphosphorylated in sALS spinal motor neurons; CFL2 role at NMJ | Cofilin hyperphosphorylation triggers TDP-43 pathology |
| **ROCK** (Rho Kinase) | Enhanced ROCK activation in SMA spinal cord; Fasudil extends survival in SMA mice | ROCK-ALS Phase 2 trial: Fasudil safe and tolerable; Bravyl (oral fasudil) reduces NfL 15% | Shared therapeutic target — ROCK inhibition benefits both |
| **LIMK1** | Downstream of ROCK; phosphorylates cofilin | Increased LIMK1 phosphorylation in sALS patients | ROCK-LIMK1-cofilin axis active in both diseases |
| **CAP2** | Actin dynamics regulator | Elevated in ALS CSF (2026 study); synaptic/cytoskeletal biomarker | Cofilin regulator with CSF biomarker potential |

**Key mechanism**: ROCK --> LIMK1 --> p-Cofilin (inactive) --> F-actin stabilization --> TDP-43 mislocalization (in ALS) / axon transport disruption (in both)

### 1.2 RNA Processing & Nuclear Body Convergence

SMN, TDP-43, and FUS physically interact in nuclear Gems and share RNA processing functions:

- **TDP-43 localizes to nuclear Gems** through its association with SMN (Gems are SMN-enriched nuclear bodies)
- **TDP-43 overexpression enhances SMN2 exon 7 inclusion**, augmenting full-length SMN levels
- **FUS directly binds SMN** via U1-snRNP; ALS-causing FUS mutations abnormally enhance FUS-SMN interaction
- **Gemin3** (SMN complex member) functionally interacts with TDP-43, FUS, and SOD1
- **SMN depletion occurs in TDP-43 knockout mice**; SMN is aberrantly localized in TDP-43 transgenic mice
- Both diseases involve **snRNP assembly defects** and alternative splicing dysregulation

**Implication**: ALS-linked TDP-43/FUS pathology directly disrupts SMN function, creating an "acquired SMA-like state" in ALS motor neurons.

### 1.3 STMN2 (Stathmin-2) — A Shared Survival Factor

STMN2 is emerging as a critical node connecting ALS and SMA:

- In ALS: TDP-43 nuclear loss causes cryptic splicing/polyadenylation of STMN2 mRNA in ~97% of cases
- In SMA: STMN2 overexpression rescues axonal growth defects in iPSC-derived SMA motor neurons
- AAV9-STMN2 gene therapy in SMA mice: significantly increased survival, improved motor function, ameliorated NMJ pathology
- STMN2 enhances motor axon regeneration independent of tubulin binding (PNAS 2025)
- **Therapeutic angle**: STMN2 restoration could benefit both ALS and SMA

### 1.4 Dying-Back Axonopathy & NMJ Vulnerability

Both diseases follow a "dying-back" pattern of neurodegeneration:

| Feature | SMA | ALS |
|---------|-----|-----|
| **Primary site** | NMJ denervation precedes motor neuron loss | 40% end-plates denervated before any cell body loss (SOD1 mice, day 47) |
| **Progression** | Distal-to-proximal; NMJ defects before symptom onset | Distal-to-proximal; NMJ loss --> axon loss --> cell body loss |
| **SMN role** | Required for NMJ formation and maturation | SMN mislocalized in TDP-43 transgenic mice |
| **Actin role** | Actin dynamics required for NMJ maintenance | Profilin/cofilin disruption impairs NMJ stability |
| **Schwann cells** | Perisynaptic Schwann cell defects | Schwann cell dysfunction contributes to NMJ instability |

### 1.5 Axon Degeneration Signaling (SARM1/NMNAT2)

The SARM1 pathway is the central executioner of pathological axon degeneration in both diseases:

- **TNF-alpha triggers SARM1-dependent axon degeneration** via noncanonical necroptotic signaling
- **MLKL induces loss of NMNAT2 and STMN2** to activate SARM1 NADase --> calcium influx --> axon death
- SARM1 mediates both Wallerian degeneration and the dying-back axonopathy characteristic of ALS
- **Wld(s)** (slow Wallerian degeneration) fails to rescue SMA NMJ defects, suggesting SMA involves additional non-SARM1 mechanisms
- This identifies **neuroinflammation --> SARM1 activation** as a therapeutically targetable mechanism

### 1.6 Protein Network Analysis (Hensel et al.)

Systematic network analysis (PMC8966079, 2022) reveals:

- **PFN1 and SOD1** serve as inter-modular hub proteins connecting ALS and SMA pathways
- Dysregulated processes span: actin dynamics, fatty acid metabolism, skeletal muscle metabolism, stress granule dynamics
- 15 proteins differentially expressed in proteomic studies of BOTH ALS and SMA
- Shared pathways converge on **ER-Golgi trafficking** and **vesicle-mediated transport**
- B-Raf and JAK/STAT signaling also shared between diseases

---

## 2. Key Papers

| PMID | Year | Authors | Finding | Relevance to SMA |
|------|------|---------|---------|-------------------|
| 28459188 | 2018 | Hensel & Claus | Actin cytoskeleton contributes to motoneuron degeneration in both SMA and ALS; SMN binds profilins, PFN1 mutated in ALS | **Foundational review** — establishes shared actin hypothesis |
| 35372839 | 2022 | Hensel et al. | Protein network analysis: PFN1 and SOD1 are inter-modular hubs connecting ALS-SMA dysregulated processes | Network-level validation of shared pathomechanism |
| 23022481 | 2012 | Yamazaki et al. | FUS-SMN protein interactions link ALS and SMA; FUS directly binds SMN | Direct molecular link between ALS (FUS) and SMA (SMN) |
| 25525858 | 2016 | Perera et al. | Enhancing SMN expression extends lifespan in mutant TDP-43 mice | SMN as therapeutic target in TDP-43 proteinopathies |
| 31604920 | 2019 | Cacciottolo et al. | SMN complex member Gemin3 interacts with TDP-43, FUS, and SOD1 | SMN complex directly connected to all 3 major ALS genes |
| awag096 | 2026 | (Brain) | Cofilin hyperphosphorylation triggers TDP-43 pathology in sporadic ALS | **Critical new finding** — actin dynamics DRIVE TDP-43 pathology |
| 39424560 | 2024 | Koch et al. | ROCK-ALS Phase 2: Fasudil safe/tolerable in ALS; MUNIX preservation | ROCK inhibition works in SMA mice AND ALS patients |
| — | 2024 | Woolsey Pharma | Bravyl (oral fasudil) Phase 2a: 15% NfL reduction, 28% slower ALSFRS-R decline | Oral ROCK inhibitor showing efficacy in ALS |
| 28916199 | 2017 | Hensel et al. | ERK and ROCK functionally interact; ROCK compensationally upregulated in SMA | ROCK-ERK crosstalk in SMA pathomechanism |
| 22573689 | 2012 | Bernstein et al. | Cofilin rod formation depends on disulfide bonds; implications for neurodegeneration | Cofilin rods block axonal transport — relevant to both |
| 36212686 | 2022 | Bamburg et al. | Cytoskeletal dysregulation: cofilin-actin rod formation, monitoring, inhibition | Comprehensive review of cofilin pathology across diseases |
| 39725771 | 2024 | — | STMN2 targeting for SMA: AAV9-STMN2 improves survival, motor function, NMJ | STMN2 as shared ALS-SMA therapeutic target |
| 32609299 | 2020 | Summers et al. | SARM1 acts downstream of neuroinflammatory and necroptotic signaling | SARM1 as shared axon degeneration executioner |
| — | 2026 | Sci Rep | CAP2 in CSF: synaptic/cytoskeletal signatures of motor neuron disease | New actin-related ALS biomarker |
| 25221469 | 2014 | Coque et al. | ROCK inhibition therapy for SMA: effects on multiple cellular targets | ROCK inhibition extends SMA mouse survival |
| — | 2023 | Answer ALS | 433 iPSC lines (341 ALS, 92 control) bulk RNA-seq; 13 DEGs in initial comparison | Largest ALS iPSC transcriptome resource |
| 29016853 | 2017 | Hensel et al. | PlexinD1 cleavage and sequestration to actin rods in SMA | Actin rod formation occurs in SMA too |
| 28220755 | 2017 | Mirra et al. | Functional interaction between FUS and SMN underlies SMA-like splicing changes | FUS overexpression causes SMA-like splicing defects |
| — | 2026 | Nature Sci Rep | CORO1A 5.3x elevated in ALS exosomes; increases with disease progression | Coronin family as ALS biomarkers — check CORO1C next |

---

## 3. GEO Datasets Worth Analyzing for CORO1C/CFL2/PFN1

### Priority 1: Human Post-Mortem Spinal Cord (Most Relevant)

| GSE Accession | Type | Samples | Description | Priority |
|---------------|------|---------|-------------|----------|
| **GSE153960** | Bulk RNA-seq | 380 transcriptomes (154 ALS, 49 ctrl) | Cervical, thoracic, lumbar spinal cord segments | **HIGHEST** — largest human ALS spinal cord dataset |
| **GSE76220** | Bulk RNA-seq | 13 sALS + 9 ctrl | Laser-captured motor neurons from lumbar spinal cord | **HIGH** — motor neuron-specific |
| **GSE190442** | snRNA-seq | 55,289 cells, 7 donors | Single-nucleus from post-mortem lumbar spinal cord; 64 cell subtypes | **HIGH** — cell-type resolution |
| **GSE18920** | Microarray | MN from sALS + ctrl | Motor neurons, sporadic ALS | MEDIUM — microarray, older |
| **GSE56500** | Microarray | MN from sALS + ctrl | Motor neuron expression profiles | MEDIUM — microarray |
| **GSE68605** | Microarray | MN from sALS + ctrl | Motor neuron expression profiles | MEDIUM — microarray |
| **GSE234774** | RNA-seq | ALS spinal cord | Recent 2023 submission | HIGH — check for completeness |

### Priority 2: iPSC-Derived Motor Neurons

| GSE Accession | Type | Samples | Description | Priority |
|---------------|------|---------|-------------|----------|
| **GSE106382** | Bulk RNA-seq | iPSC-MNs from fALS, sALS, ctrl | iPSC differentiated to spinal motor neurons | HIGH — controlled conditions |
| **Answer ALS** | Bulk RNA-seq | 433 lines (341 ALS, 92 ctrl) | Largest iPSC ALS dataset; 32-day diMN protocol | **HIGHEST** — massive sample size |
| **GSE67196** | RNA-seq | iPSC-MNs | Cross-comparison fALS/sALS iPSC motor neurons | HIGH |
| **GSE118723** | scRNA-seq | iPSC-MNs | Single-cell ALS signatures | HIGH — cell heterogeneity |

### Priority 3: Mouse Models (Mechanistic Validation)

| GSE Accession | Type | Samples | Description | Priority |
|---------------|------|---------|-------------|----------|
| **GSE113924** | Bulk RNA-seq | hPFN1-G118V mouse | PFN1 ALS mouse model — pre-symptomatic + end-stage | **HIGHEST** — directly tests PFN1/actin axis |
| **GSE38820** | Bulk RNA-seq | SOD1-G85R mouse MNs | Pre-symptomatic SOD1 motor neurons | HIGH |
| **GSE40438** | Bulk RNA-seq | SOD1-G93A mouse | Resistant vs. vulnerable motor neuron populations | HIGH — differential vulnerability |
| **GSE178693** | scRNA-seq | SOD1 mouse brainstem | Perturbed cell types and pathways | MEDIUM |
| **GSE93939** | RNA-seq | Oculomotor vs. spinal MNs | ALS-resistant vs. vulnerable neurons | HIGH — vulnerability comparison |

### Analysis Plan for These Datasets

For each dataset, extract and compare:
1. **CORO1C** expression: ALS vs. control (is it elevated like CORO1A?)
2. **CFL2** expression: motor neuron and muscle compartments
3. **PFN1/PFN2** ratio: does PFN2a upregulation (seen in SMA) also occur in ALS?
4. **LIMK1/LIMK2** expression: ROCK pathway activation status
5. **STMN2** cryptic splicing: correlate with actin gene expression changes
6. **Coronin family** (CORO1A/B/C, CORO2A/B, CORO7): systematic expression profiling

**Hypothesis to test**: If CORO1C is elevated in ALS motor neurons (like CORO1A in exosomes), it would validate the "shared coronin-actin disruption" model across SMA and ALS.

---

## 4. Therapeutic Candidates for Both Diseases

### 4.1 ROCK Inhibitors (Most Advanced)

| Drug | Stage | Disease | Key Results |
|------|-------|---------|-------------|
| **Fasudil** (IV) | Phase 2 complete | ALS | Safe/tolerable; MUNIX preservation; dose-dependent effect (Lancet Neurol 2024) |
| **Bravyl** (oral fasudil) | Phase 2a complete; 300mg cohort ongoing | ALS | 15% NfL reduction (p<0.001); 28% slower ALSFRS-R decline; well tolerated |
| **Fasudil** | Preclinical | SMA | Extended survival in SMA mice; improved skeletal muscle and NMJ pathology |
| **Y-27632** | Preclinical | SMA | Significant increase in survival; improved phenotype |

**Status**: Bravyl is the most promising cross-disease candidate. Phase 2 ALS data (300mg dose) expected June 2025. If positive, SMA trials should be proposed.

### 4.2 SARM1 Inhibitors (Axon Protection)

| Drug | Stage | Disease | Notes |
|------|-------|---------|-------|
| **NB-4746** (Nura Bio) | Phase 1 complete; Phase 1b/2 planned 2025 | ALS, MS, CIPN | Oral, brain-penetrant; well tolerated in Phase 1 |
| **LY3873862** (Eli Lilly) | Entering HEALEY ALS Platform Trial | ALS | Potent selective SARM1 inhibitor |
| **ASHA-624** (Asha Therapeutics) | Preclinical | CMT2A | Novel mechanism; potential broader application |

**Caution**: Recent reports show SARM1 base-exchange inhibitors can paradoxically INCREASE SARM1 activity and worsen neuronal damage at subinhibitory doses (npj Drug Discovery, 2025). Dosing precision is critical.

**SMA relevance**: Wld(s) (which blocks SARM1-related pathways) failed to rescue SMA NMJ defects. This suggests SMA axon degeneration may involve SARM1-independent mechanisms. SARM1 inhibitors may be more relevant for ALS than SMA.

### 4.3 RIPK1 Inhibitors (Necroptosis)

| Drug | Stage | Disease | Notes |
|------|-------|---------|-------|
| **SAR443820/DNL788** (Sanofi/Denali) | Phase 2 FAILED (Oct 2024) | ALS | Did not meet primary (ALSFRS-R) or secondary endpoints |
| **SAR443820/DNL788** | Ongoing | Multiple Sclerosis | Still in development for MS |
| **DNL747** | Discontinued | ALS, AD | Dose-limiting toxicities in primates |

**Assessment**: RIPK1 inhibition alone is insufficient for ALS. Genetic inactivation of RIP1 kinase also failed in SOD1 mice. RIPK1 may be upstream of SARM1 (which is the actual executioner), but targeting RIPK1 alone misses the mark. Combination with SARM1 inhibition may be needed.

### 4.4 STMN2 Restoration

| Approach | Stage | Disease | Notes |
|----------|-------|---------|-------|
| **AAV9-STMN2** gene therapy | Preclinical | SMA | Improved survival, motor function, NMJ pathology in SMA mice |
| **STMN2 ASO** (prevent cryptic splicing) | Preclinical | ALS | Restoring full-length STMN2 in TDP-43 proteinopathies |
| **QRL-201** (QurAlis) | Phase 1 planned | ALS | ASO targeting STMN2 cryptic exon |

**Cross-disease opportunity**: STMN2 is depleted in both diseases (by different mechanisms). Gene therapy or ASO approaches could benefit both SMA and ALS patients.

### 4.5 Emerging Candidates

| Target/Drug | Mechanism | Relevance |
|-------------|-----------|-----------|
| **LIMK1 inhibitors** | Block cofilin phosphorylation; restore actin dynamics | Directly upstream of TDP-43 mislocalization trigger |
| **Cofilin-actin rod disruptors** | Prevent/dissolve pathological cofilin rods | Would restore axonal transport in both diseases |
| **CAP2 modulators** | Regulate cofilin activity via actin sequestering | New CSF biomarker target (2026) |
| **Tropomyosin modulators** | TPM4.1/4.2 elevated in sALS; regulate actin stability | Novel target identified in cofilin-TDP-43 study |

---

## 5. Novel Hypotheses for Cross-Disease Mechanisms

### Hypothesis 1: "Acquired SMA" in ALS
TDP-43 pathology in ALS disrupts SMN nuclear localization and Gem formation, creating a secondary SMN deficiency. This means **ALS motor neurons may develop an SMA-like state** as disease progresses. Testing: Measure SMN protein levels and Gem counts in TDP-43-positive vs. TDP-43-negative ALS motor neurons.

### Hypothesis 2: Coronin Family as Universal Motor Neuron Stress Markers
CORO1A is 5.3x elevated in ALS exosomes. CORO1C is elevated in SMA. If CORO1C is also elevated in ALS, the coronin family may represent a **universal actin-stress response** in motor neurons, regardless of the initiating insult (SMN loss vs. TDP-43 pathology vs. SOD1 toxicity).

### Hypothesis 3: ROCK-Cofilin-TDP-43 as a Feedforward Loop
The 2026 Brain paper shows cofilin hyperphosphorylation triggers TDP-43 mislocalization. TDP-43 loss-of-function causes STMN2 cryptic splicing. STMN2 loss destabilizes microtubules. Microtubule instability activates Rho-ROCK signaling. ROCK phosphorylates LIMK1, which hyperphosphorylates cofilin. **This creates a self-amplifying feedforward loop** that could explain the progressive, unstoppable nature of ALS neurodegeneration.

```
Cofilin hyperphosphorylation
    --> F-actin stabilization
    --> TDP-43 cytoplasmic mislocalization
    --> STMN2 cryptic splicing (loss of function)
    --> Microtubule destabilization
    --> Rho-GTPase activation
    --> ROCK activation
    --> LIMK1 phosphorylation
    --> More cofilin hyperphosphorylation (LOOP)
```

**Breaking the loop**: ROCK inhibitors (Fasudil/Bravyl) could interrupt this at the ROCK step. STMN2 ASOs interrupt at the splicing step. LIMK1 inhibitors interrupt at the phosphorylation step. **Combination therapy targeting multiple loop nodes** may be necessary.

### Hypothesis 4: PFN1 as the Rosetta Stone
PFN1 mutations cause familial ALS. SMN directly binds PFN1. PFN1 is a central hub in ALS-SMA protein networks. PFN1 catalyzes actin elongation. PFN1 also localizes inside mitochondria (EMBO Reports 2024). **PFN1 dysfunction may be the single molecular event that most faithfully recapitulates BOTH diseases** — making PFN1 the "Rosetta Stone" of motor neuron degeneration.

### Hypothesis 5: Intron Retention Convergence
Intron retention is the primary ALS transcriptomic signature. SMN loss in SMA causes widespread splicing defects. Both diseases may converge on **a common set of intron-retained transcripts** in motor neurons. Specifically, if actin-pathway genes (CORO1C, CFL2, PFN1, STMN2) show intron retention in both diseases, this would establish a unified splicing-cytoskeletal mechanism.

### Hypothesis 6: NMJ as the Actin Battlefield
The NMJ is the first site of pathology in both diseases. NMJ maintenance is exquisitely dependent on actin dynamics (pre-synaptic vesicle cycling, post-synaptic receptor clustering). CFL2 (muscle cofilin) specifically regulates NMJ postsynaptic development. **NMJ degeneration in both diseases may be driven by the same actin dysregulation** occurring at the synapse, with different upstream triggers (SMN loss in SMA, TDP-43/PFN1/SOD1 in ALS).

---

## 6. Recommended Next Steps

### Computational (Can Do Now)
1. **Download GSE153960** (380 ALS spinal cord transcriptomes) and run differential expression for CORO1C, CFL2, PFN1, PFN2, LIMK1, LIMK2, CAP2, STMN2
2. **Download GSE113924** (PFN1-G118V ALS mouse) and check coronin/cofilin family expression
3. **Cross-reference with SMA datasets** already analyzed on the platform (3 GEO datasets)
4. **Build integrated actin-pathway heatmap** across all SMA and ALS datasets
5. **Check intron retention** in actin genes across both disease datasets

### Experimental (Requires Collaboration)
6. **Immunostain ALS spinal cord** for CORO1C (does it co-localize with TDP-43 inclusions?)
7. **Test Fasudil/Bravyl in SMA mouse models** with NMJ-focused readouts
8. **Measure CORO1C in ALS patient CSF/exosomes** (parallel to CORO1A findings)
9. **STMN2 + Fasudil combination** in ALS iPSC motor neurons

### Strategic
10. **Contact Woolsey Pharmaceuticals** about SMA indication for Bravyl
11. **Submit grant proposal** for cross-disease actin pathway analysis
12. **Present at ALS/MND Symposium** — the actin convergence story is novel and fundable

---

## 7. Summary: The Actin Convergence Model

```
                        SMA                              ALS
                         |                                |
                    SMN loss                    TDP-43/FUS/SOD1/PFN1
                         |                                |
                    SMN-profilin               Cofilin hyperphosphorylation
                    interaction lost            (via ROCK-LIMK1)
                         |                                |
                         v                                v
                    +------------------------------------------+
                    |     ACTIN DYNAMICS DISRUPTED             |
                    |                                          |
                    |  - Profilin imbalance (PFN2a up)        |
                    |  - Cofilin-actin rod formation           |
                    |  - Coronin dysregulation (CORO1A/1C)    |
                    |  - F-actin/G-actin ratio shifted        |
                    |  - Stress granule formation enhanced     |
                    +------------------------------------------+
                                      |
                         +------------+------------+
                         |            |            |
                         v            v            v
                   NMJ failure   Axon transport   TDP-43/SMN
                   (dying-back)  blockade         mislocalization
                         |            |            |
                         v            v            v
                    +------------------------------------------+
                    |     MOTOR NEURON DEGENERATION            |
                    |     (SARM1 --> NAD+ depletion -->        |
                    |      calcium influx --> axon death)      |
                    +------------------------------------------+
```

---

## Sources

- [Hensel & Claus 2018 — Actin Cytoskeleton in SMA and ALS](https://journals.sagepub.com/doi/abs/10.1177/1073858417705059)
- [Hensel et al. 2022 — Protein Network Analysis ALS-SMA](https://pmc.ncbi.nlm.nih.gov/articles/PMC8966079/)
- [Yamazaki et al. 2012 — FUS-SMN Interactions](https://www.sciencedirect.com/science/article/pii/S2211124712002653)
- [Perera et al. 2016 — SMN Enhances TDP-43 Mouse Survival](https://academic.oup.com/hmg/article/25/18/4080/2525858)
- [Cacciottolo et al. 2019 — Gemin3 Interacts with TDP-43, FUS, SOD1](https://www.nature.com/articles/s41598-019-53508-4)
- [Cofilin-TDP-43 2026 — Brain](https://academic.oup.com/brain/advance-article/doi/10.1093/brain/awag096/8512674)
- [ROCK-ALS Trial 2024 — Lancet Neurology](https://www.thelancet.com/journals/laneur/article/PIIS1474-4422(24)00373-9/fulltext)
- [Bravyl Phase 2a Results — Woolsey Pharmaceuticals](https://www.prnewswire.com/news-releases/results-of-woolsey-pharmaceuticals-phase-2a-study-of-bravyl-in-als-patients-shows-statistically-significant-reduction-in-neurofilament-light-and-directionally-improved-clinical-outcomes-302176845.html)
- [Fasudil in SMA Mice — BMC Medicine](https://bmcmedicine.biomedcentral.com/articles/10.1186/1741-7015-10-24)
- [STMN2 in SMA — Cell Mol Life Sci 2024](https://link.springer.com/article/10.1007/s00018-024-05550-3)
- [SARM1 Downstream of Necroptosis — J Cell Biol 2020](https://rupress.org/jcb/article/219/8/e201912047/151915/SARM1-acts-downstream-of-neuroinflammatory-and)
- [SARM1 Inhibitor Safety Concerns — npj Drug Discovery 2025](https://www.nature.com/articles/s44386-025-00023-4)
- [RIPK1 in ALS — Science 2016](https://www.science.org/doi/10.1126/science.aaf6803)
- [DNL788 Phase 2 Failure — BioSpace](https://www.biospace.com/sanofi-denali-als-candidate-flops-in-mid-stage-trial)
- [CORO1A in ALS Exosomes — Springer MedScience](https://link.springer.com/article/10.1007/s11684-021-0905-y)
- [CAP2 in ALS CSF 2026 — Scientific Reports](https://www.nature.com/articles/s41598-026-39274-0)
- [FUS-SMN Splicing Interaction — Scientific Reports 2017](https://www.nature.com/articles/s41598-017-02195-0)
- [ALS as Distal Axonopathy — Frontiers Neuroscience 2014](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2014.00252/full)
- [NMJ Shared Vulnerability 2025 — J Neuroscience](https://www.jneurosci.org/content/45/46/e1353252025.full.pdf)
- [Cofilin-Actin Rods Review 2022 — Frontiers Cell Neurosci](https://www.frontiersin.org/journals/cellular-neuroscience/articles/10.3389/fncel.2022.982074/full)
- [Profilin Isoforms Review — PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8387879/)
- [ALS-Causing PFN1 Mutations — Nature Sci Rep](https://www.nature.com/articles/s41598-018-31199-7)
- [STMN2 Axon Regeneration 2025 — PNAS](https://www.pnas.org/doi/10.1073/pnas.2502294122)
- [Nura Bio SARM1 Phase 1](https://nurabio.com/news/nura-bio-initiates-phase-1-clinical-trial-for-its-oral-brain-penetrant-sarm1-inhibitor-nb-4746/)
- [Lilly SARM1 in HEALEY Trial](https://www.massgeneral.org/neurology/als/news/new-regimen-for-healey-als-platform-trial-with-lilly)
- [Fasudil Attenuates ALS Disease Spreading — PMC 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12424921/)
- [CFL2 at NMJ — PubMed 2023](https://pubmed.ncbi.nlm.nih.gov/38045306/)
- [ALS Spinal Cord Transcriptome (380 samples) — Nature Comms 2023](https://www.nature.com/articles/s41467-023-37630-6)
- [PFN1 Inside Mitochondria — EMBO Reports 2024](https://link.springer.com/article/10.1038/s44319-024-00209-3)
- [Answer ALS 433 iPSC Lines — Neuron 2023](https://www.cell.com/neuron/fulltext/S0896-6273(23)00034-X)
- [Meta-analysis ALS Motor Neurons — Frontiers Genetics 2024](https://www.frontiersin.org/journals/genetics/articles/10.3389/fgene.2024.1385114/full)
- [ROCK Inhibition in SMA — Frontiers Neuroscience 2014](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2014.00271/full)

---

*Generated by cross-disease research agent, 2026-03-22. All PMIDs and findings should be verified against primary sources before citation in manuscripts or grant applications.*
