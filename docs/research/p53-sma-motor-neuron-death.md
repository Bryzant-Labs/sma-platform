# p53-Mediated Motor Neuron Death in Spinal Muscular Atrophy

**Research compiled: 2026-03-22**
**Requested by: Christian Simon (Leipzig University, Carl-Ludwig-Institute for Physiology)**
**Status: GAP ON PLATFORM -- ~15 publications exist, ZERO claims indexed**

---

## Executive Summary

p53 is a **central executor of motor neuron death in SMA**. SMN deficiency activates p53 through at least two converging mechanisms: (1) mis-splicing of Mdm2/Mdm4 (the two non-redundant p53 repressors) due to snRNP dysfunction, and (2) Stasimon/Tmem41b deficiency activating p38 MAPK, which phosphorylates p53. Cell-autonomous p53 activation occurs selectively in **vulnerable** motor neurons at pre-symptomatic stages, marked by phosphorylation of p53-Ser18. Pharmacological inhibition (pifithrin-alpha) or genetic ablation of p53 fully rescues motor neuron survival in severe SMA mouse models.

Critically, recent work (2025) shows p53 also drives **Purkinje cell death in the cerebellum** of SMA mice and patients, expanding the p53 story beyond spinal motor neurons.

This represents one of the most mechanistically well-characterized pathways in SMA neurodegeneration and is a **major gap** on the platform.

---

## The p53-SMA Pathway: Mechanistic Model

```
SMN Deficiency
    |
    v
snRNP Assembly Defects
    |
    +---> Mdm2 exon skipping ----+
    |                             |
    +---> Mdm4 exon skipping ----+--> Loss of p53 repression
    |                             |
    +---> Stasimon/Tmem41b -------+--> p38 MAPK activation
          mis-splicing                  |
                                        v
                                  p53 phosphorylation (Ser18)
                                        |
                                        v
                              p53 transcriptional activation
                                   /         \
                                  v           v
                           c-Fos           Bax/Bak
                          (marker)        (apoptosis)
                                              |
                                              v
                                  Caspase activation
                                              |
                                              v
                              MOTOR NEURON DEATH (selective)
```

### Why Only Vulnerable Motor Neurons?

- p53-Ser18 phosphorylation occurs **exclusively** in vulnerable (not resistant) motor neurons
- Mdm2/Mdm4 exon skipping is most prominent in motor neurons (correlating with snRNP reduction)
- Resistant motor neurons and spinal interneurons do NOT show p53 activation
- This provides a molecular explanation for the selective vulnerability puzzle in SMA

### Additional Convergent Pathways (p53-adjacent)

- **JNK3**: ASK1/MKK4/JNK3 and MEKK1/MKK7/JNK3 modules phosphorylate c-Jun; JNK3 knockout is neuroprotective
- **CDK5/Tau**: Non-aggregating tau phosphorylation (S202, T205) via CDK5; contributes to motor neuron degeneration
- **ER stress**: Endoplasmic reticulum stress also implicated in SMA motor neurons
- **p38 MAPK**: Stasimon deficiency activates p38 MAPK, which phosphorylates p53; p38 inhibition (MW150) is neuroprotective and synergizes with SMN-inducing therapies

---

## Complete Literature Table

### Core p53-SMA Papers

| PMID | Year | Journal | First Author | Title | Key Finding |
|------|------|---------|-------------|-------|-------------|
| [11704667](https://pubmed.ncbi.nlm.nih.gov/11704667/) | 2002 | J Biol Chem | Young PJ | A direct interaction between the survival motor neuron protein and p53 and its relationship to SMA | SMN directly binds p53; pathogenic SMN mutations reduce p53 binding; SMN and p53 co-localize in Cajal bodies; interaction loss may explain motor neuron death |
| [29281826](https://pubmed.ncbi.nlm.nih.gov/29281826/) | 2017 | Cell Reports | **Simon CM** | Converging mechanisms of p53 activation drive motor neuron degeneration in SMA | **LANDMARK PAPER.** Cell-autonomous p53 activation in vulnerable (not resistant) MNs; p53-Ser18 phosphorylation as death marker; pifithrin-alpha fully rescues MN survival; genetic p53 ablation prevents degeneration |
| [30012555](https://pubmed.ncbi.nlm.nih.gov/30012555/) | 2018 | Genes Dev | Van Alstyne M | Dysregulation of Mdm2 and Mdm4 alternative splicing underlies motor neuron death in SMA | snRNP dysfunction causes Mdm2/Mdm4 exon skipping; this de-represses p53; AAV-mediated Mdm2/Mdm4 restoration suppresses p53 and rescues MNs; causal link: splicing defect -> p53 -> death |
| [31851921](https://pubmed.ncbi.nlm.nih.gov/31851921/) | 2020 | Cell Reports | **Simon CM** | Stasimon contributes to the loss of sensory synapses and motor neuron death in a mouse model of SMA | Stasimon/Tmem41b deficiency activates p38 MAPK -> p53 phosphorylation -> MN death; AAV-Stasimon delivery rescues both sensory synapses and motor neurons; dual contribution to motor circuit pathology |
| [36419936](https://pubmed.ncbi.nlm.nih.gov/36419936/) | 2022 | Front Cell Neurosci | Buettner JM | p53-dependent c-Fos expression is a marker but not executor for motor neuron death in SMA mouse models | c-Fos is induced downstream of p53 in dying MNs but is NOT required for death; c-Fos is a biomarker, not a therapeutic target |
| [33382987](https://pubmed.ncbi.nlm.nih.gov/33382987/) | 2021 | Exp Neurol | Rindt H | Spinal motor neuron loss occurs through a p53-and-p21-independent mechanism in the Smn2B/- mouse model of SMA | **IMPORTANT NUANCE:** In the milder Smn2B/- model, p53/p21 ablation does NOT prevent MN loss; suggests p53-independent death pathways in milder disease |
| [31273192](https://pubmed.ncbi.nlm.nih.gov/31273192/) | 2019 | Cell Death Dis | Courtney NL | Reduced P53 levels ameliorate NMJ loss without affecting motor neuron pathology in Smn2B/- mice | Post-natal p53 reduction reduces NMJ loss but NOT MN death or phenotype in Smn2B/-; p53 role is model-severity dependent |
| [40585211](https://pubmed.ncbi.nlm.nih.gov/40585211/) | 2025 | Brain | **Simon CM** | Cerebellar pathology contributes to neurodevelopmental deficits in SMA | **NEWEST.** p53-dependent Purkinje cell death in SMA cerebellum (non-apoptotic); lobule-specific; confirmed in human Type I SMA tissue; cerebellar pathology contributes to motor + social communication deficits |

### p53-Adjacent / Convergent Pathway Papers

| PMID | Year | Journal | First Author | Title | Key Finding |
|------|------|---------|-------------|-------|-------------|
| [23063131](https://pubmed.ncbi.nlm.nih.gov/23063131/) | 2012 | Cell | Lotti F | An SMN-dependent U12 splicing event essential for motor circuit function | Identified Stasimon as SMN-dependent U12 splicing target critical for motor circuit function (upstream of p53 pathway) |
| [25878277](https://pubmed.ncbi.nlm.nih.gov/25878277/) | 2015 | J Neurosci | Miller N | Non-aggregating tau phosphorylation by CDK5 contributes to motor neuron degeneration in SMA | Tau hyperphosphorylation (S202/T205) via CDK5 in SMA MNs; does NOT aggregate (unlike AD); phospho-mimetic tau promotes MN defects |
| [26423457](https://pubmed.ncbi.nlm.nih.gov/26423457/) | 2015 | Hum Mol Genet | Genabai NK | Genetic inhibition of JNK3 ameliorates spinal muscular atrophy | JNK3 knockout is neuroprotective in SMA mice; ASK1/MKK4/JNK3 pathway phosphorylates c-Jun driving neurodegeneration |
| [30368521](https://pubmed.ncbi.nlm.nih.gov/30368521/) | 2018 | Cell Death Dis | Soh BSE | Cell cycle inhibitors protect motor neurons in an organoid model of SMA | SMN-deficient MNs aberrantly reactivate cell cycle (consistent with p53 activation); CDK4/6 inhibitor rescues MN survival in spinal organoids |
| [22723941](https://pubmed.ncbi.nlm.nih.gov/22723941/) | 2012 | PLoS One | Sareen D | Inhibition of apoptosis blocks human motor neuron cell death in a stem cell model of SMA | iPSC-derived SMA MNs show Fas ligand-mediated apoptosis; caspase-3/caspase-8 activation; Fas blocking antibody rescues survival |
| [40926051](https://pubmed.ncbi.nlm.nih.gov/40926051/) | 2025 | EMBO Mol Med | Carlini MJ | Identification of p38 MAPK inhibition as a neuroprotective strategy for combinatorial SMA therapy | **NEWEST.** p38 MAPK inhibitor MW150 is neuroprotective; synergizes with SMN-inducing drugs; enables synaptic rewiring; candidate for combination therapy |

### Simon CM Additional SMA Papers (Motor Circuit Context)

| PMID | Year | Journal | Title | Key Finding |
|------|------|---------|-------|-------------|
| [33219005](https://pubmed.ncbi.nlm.nih.gov/33219005/) | 2021 | J Neurosci | Chronic pharmacological increase of neuronal activity improves sensory-motor dysfunction in SMA mice | 4-aminopyridine (4-AP) restores proprioceptive synapses and NMJs; FDA-approved drug |
| [34825141](https://pubmed.ncbi.nlm.nih.gov/34825141/) | 2021 | iScience | Central synaptopathy is the most conserved feature of motor circuit pathology across SMA mouse models | Central excitatory synaptopathy precedes MN death across all models; more conserved than p53-dependent MN death |

---

## Papers Authored by Christian M. Simon (Leipzig)

Simon is a **key figure** in this field. He was first/corresponding author on the landmark p53-SMA paper and continues to publish on this topic from Leipzig:

1. **PMID 29281826 (2017)** -- "Converging mechanisms of p53 activation..." (Cell Reports) -- First author, Columbia
2. **PMID 31851921 (2020)** -- "Stasimon contributes to..." (Cell Reports) -- Author, Columbia/Leipzig
3. **PMID 33219005 (2021)** -- "Chronic pharmacological increase..." (J Neurosci) -- First author, Columbia/Leipzig
4. **PMID 34825141 (2021)** -- "Central synaptopathy..." (iScience) -- Author, Leipzig
5. **PMID 36419936 (2022)** -- "p53-dependent c-Fos..." (Front Cell Neurosci) -- **Senior/corresponding author, Leipzig** (Buettner JM first author from his lab)
6. **PMID 40585211 (2025)** -- "Cerebellar pathology..." (Brain) -- **Corresponding author, Leipzig**
7. **PMID 40926051 (2025)** -- "p38 MAPK inhibition..." (EMBO Mol Med) -- Collaborator (Pellizzoni lab lead, Simon involved)

Simon's group at Leipzig is the **world leader** on p53 in SMA motor neurons. Not having his work on the platform is a significant omission.

---

## Connection to Existing Platform Targets

### SMN1 / SMN2

- **Direct**: SMN protein physically binds p53 (Young et al., 2002). SMN deficiency -> snRNP assembly defects -> Mdm2/Mdm4 mis-splicing -> p53 de-repression. This is the **mechanistic chain from SMN loss to motor neuron death**.
- p53 pathway is the most direct explanation for WHY SMN deficiency kills motor neurons selectively.

### CORO1C (Actin Dynamics)

- CORO1C is involved in actin cytoskeleton regulation. p53 activation in SMA motor neurons is upstream and mechanistically distinct, but both are consequences of SMN deficiency.
- Potential interaction: p53-induced cell death may be exacerbated by cytoskeletal dysfunction (CORO1C, PFN1, CFL2).

### PFN1 (Profilin 1)

- PFN1 mutations cause ALS. In SMA, actin dynamics disruption (PFN1-related) and p53 activation may represent parallel pathological cascades.
- The CDK5/tau phosphorylation pathway (Miller et al., 2015) could bridge actin dysfunction and p53, since CDK5 regulates both cytoskeletal proteins and apoptotic pathways.

### CFL2 (Cofilin 2)

- CFL2 regulates actin depolymerization. p53 activation and actin cytoskeleton collapse may synergize to drive motor neuron death.
- No direct published link between CFL2 and p53 in SMA, but both are downstream of SMN deficiency.

---

## Suggested New Claims to Extract

### High-Priority Claims (from core papers)

1. "SMN protein directly interacts with p53 tumor suppressor protein; pathogenic SMN mutations reduce this interaction proportional to disease severity" (PMID 11704667)
2. "Cell-autonomous activation of p53 occurs selectively in vulnerable but not resistant motor neurons at pre-symptomatic stages in SMA mice" (PMID 29281826)
3. "Phosphorylation of p53-Ser18 exclusively marks vulnerable SMA motor neurons and is required for the neurodegenerative process" (PMID 29281826)
4. "Pharmacological inhibition of p53 by pifithrin-alpha fully rescues survival of vulnerable motor neurons in severe SMA mouse models" (PMID 29281826)
5. "SMN deficiency causes exon skipping in Mdm2 and Mdm4, the two non-redundant p53 repressors, leading to p53 de-repression in motor neurons" (PMID 30012555)
6. "AAV-mediated restoration of full-length Mdm2 and Mdm4 suppresses p53 induction and prevents motor neuron degeneration in SMA mice" (PMID 30012555)
7. "Stasimon/Tmem41b deficiency activates p38 MAPK, which phosphorylates p53 to drive motor neuron death in SMA" (PMID 31851921)
8. "p53-dependent c-Fos expression is a biomarker but NOT an executor of motor neuron death in SMA" (PMID 36419936)
9. "Motor neuron death in the milder Smn2B/- model occurs through a p53-and-p21-INDEPENDENT mechanism" (PMID 33382987)
10. "Post-natal p53 reduction ameliorates NMJ loss but does not prevent motor neuron death in the Smn2B/- model" (PMID 31273192)
11. "p53-dependent non-apoptotic Purkinje cell death occurs in SMA cerebellum, confirmed in human Type I SMA tissue" (PMID 40585211)
12. "p38 MAPK inhibitor MW150 synergizes with SMN-inducing drugs to enhance motor function, weight gain, and survival in SMA mice" (PMID 40926051)

### Medium-Priority Claims (convergent pathways)

13. "JNK3 genetic knockout is neuroprotective in SMA mice via suppression of c-Jun phosphorylation" (PMID 26423457)
14. "Non-aggregating tau phosphorylation at S202/T205 by CDK5 contributes to motor neuron degeneration in SMA" (PMID 25878277)
15. "CDK4/6 inhibition rescues motor neuron survival in SMA spinal organoids by blocking aberrant cell cycle reactivation" (PMID 30368521)
16. "Fas ligand-mediated apoptosis with caspase-8 and caspase-3 activation drives human iPSC-derived SMA motor neuron death" (PMID 22723941)

---

## Therapeutic Implications

### Direct p53 Inhibition

| Compound | Mechanism | Evidence in SMA | Status |
|----------|-----------|-----------------|--------|
| **Pifithrin-alpha** | p53 transcriptional activity inhibitor | Fully rescues MN survival in severe SMA mice (PMID 29281826) | Preclinical tool compound; not drug-like for clinical use |
| **Pifithrin-mu** | p53 mitochondrial pathway inhibitor | Used in TBI neuroprotection; not tested in SMA | Could complement pifithrin-alpha |
| **Nutlin-3** | Mdm2-p53 interaction (opposite effect -- activates p53) | Negative control in SMA studies | Avoid in SMA context |

### Upstream Pathway Targets (More Druggable)

| Target | Compound | Mechanism | Evidence | Clinical Potential |
|--------|----------|-----------|----------|-------------------|
| **p38 MAPK** | **MW150** | p38 MAPK inhibitor | Synergizes with SMN induction; neuroprotective in SMA mice (PMID 40926051) | **HIGH -- candidate for combination therapy with nusinersen/risdiplam** |
| **JNK3** | SP600125, JNK-IN-8 | JNK pathway inhibitor | Genetic JNK3 KO ameliorates SMA (PMID 26423457) | Moderate -- isoform selectivity challenge |
| **CDK5** | Roscovitine | CDK inhibitor | Tau phosphorylation by CDK5 drives MN degeneration (PMID 25878277) | Moderate -- broad CDK inhibition concerns |
| **CDK4/6** | Palbociclib (FDA-approved) | Cell cycle inhibitor | Rescues MNs in SMA organoids (PMID 30368521) | **HIGH -- repurposing opportunity; already FDA-approved for cancer** |
| **Mdm2/Mdm4** | AAV gene therapy | Restore full-length splicing | Suppresses p53 and rescues MNs (PMID 30012555) | Gene therapy approach; complex delivery |

### Combination Therapy Concept (2025 State-of-Art)

The most promising therapeutic strategy emerging from this literature:

**SMN-inducing drug (risdiplam/nusinersen) + p38 MAPK inhibitor (MW150)**

This was demonstrated in Simon/Pellizzoni's 2025 EMBO Mol Med paper to produce synergistic benefits:
- Enhanced synaptic rewiring of motor neurons
- Increased motor function beyond either drug alone
- Improved survival
- MW150 provides SMN-independent neuroprotection

This is directly relevant to the clinical challenge of **incomplete benefit** from current SMN-targeting therapies.

---

## Model-Dependent Complexity

A critical nuance that must be captured on the platform:

| SMA Mouse Model | Severity | p53 Role | Evidence |
|----------------|----------|----------|----------|
| **SMN-delta7** (severe) | Severe; death ~P13 | p53 is REQUIRED for MN death; pifithrin-alpha fully protective | PMID 29281826 |
| **Smn2B/-** (intermediate) | Intermediate; death ~P25 | p53/p21 ablation does NOT prevent MN death | PMID 33382987, 31273192 |
| **Taiwanese** (mild) | Mild | Central synaptopathy precedes MN loss; p53 role unclear | PMID 34825141 |

**Interpretation**: p53 may drive acute MN death in severe SMN depletion, while milder/chronic SMN deficiency engages additional/alternative death pathways. This has implications for therapeutic targeting -- p53 inhibition alone may be insufficient for milder SMA forms.

---

## Platform Action Items

1. **Add TP53 as a molecular target** (gene type) with evidence tier GOLD (multiple mouse model studies + human tissue confirmation)
2. **Add MDM2, MDM4 as molecular targets** (gene type) -- silver tier (single key paper but mechanistically compelling)
3. **Add TMEM41B/Stasimon as molecular target** (gene type) -- silver tier
4. **Add p38 MAPK (MAPK14) as molecular target** (gene/pathway type) -- gold tier (therapeutic candidate)
5. **Add JNK3 (MAPK10) as molecular target** (gene type) -- silver tier
6. **Add CDK5 as molecular target** (gene type) -- bronze/silver tier
7. **Extract all 16 claims listed above** with proper source attribution
8. **Create hypothesis**: "p53 inhibition combined with SMN induction provides superior neuroprotection compared to SMN-targeting monotherapy"
9. **Create hypothesis**: "p53-Ser18 phosphorylation status could serve as a pharmacodynamic biomarker for SMA motor neuron vulnerability"
10. **Link Simon's papers as sources** -- at minimum PMIDs 29281826, 31851921, 36419936, 40585211

---

## References (All PMIDs Verified via PubMed)

1. Young PJ et al. (2002) J Biol Chem. PMID: [11704667](https://pubmed.ncbi.nlm.nih.gov/11704667/)
2. Lotti F et al. (2012) Cell. PMID: [23063131](https://pubmed.ncbi.nlm.nih.gov/23063131/)
3. Sareen D et al. (2012) PLoS One. PMID: [22723941](https://pubmed.ncbi.nlm.nih.gov/22723941/)
4. Miller N et al. (2015) J Neurosci. PMID: [25878277](https://pubmed.ncbi.nlm.nih.gov/25878277/)
5. Genabai NK et al. (2015) Hum Mol Genet. PMID: [26423457](https://pubmed.ncbi.nlm.nih.gov/26423457/)
6. Simon CM et al. (2017) Cell Reports. PMID: [29281826](https://pubmed.ncbi.nlm.nih.gov/29281826/)
7. Van Alstyne M et al. (2018) Genes Dev. PMID: [30012555](https://pubmed.ncbi.nlm.nih.gov/30012555/)
8. Soh BSE et al. (2018) Cell Death Dis. PMID: [30368521](https://pubmed.ncbi.nlm.nih.gov/30368521/)
9. Courtney NL et al. (2019) Cell Death Dis. PMID: [31273192](https://pubmed.ncbi.nlm.nih.gov/31273192/)
10. Simon CM et al. (2020) Cell Reports. PMID: [31851921](https://pubmed.ncbi.nlm.nih.gov/31851921/)
11. Rindt H et al. (2021) Exp Neurol. PMID: [33382987](https://pubmed.ncbi.nlm.nih.gov/33382987/)
12. Simon CM et al. (2021) J Neurosci. PMID: [33219005](https://pubmed.ncbi.nlm.nih.gov/33219005/)
13. Simon CM et al. (2021) iScience. PMID: [34825141](https://pubmed.ncbi.nlm.nih.gov/34825141/)
14. Buettner JM, Simon CM et al. (2022) Front Cell Neurosci. PMID: [36419936](https://pubmed.ncbi.nlm.nih.gov/36419936/)
15. Simon CM et al. (2025) Brain. PMID: [40585211](https://pubmed.ncbi.nlm.nih.gov/40585211/)
16. Carlini MJ, Pellizzoni L et al. (2025) EMBO Mol Med. PMID: [40926051](https://pubmed.ncbi.nlm.nih.gov/40926051/)
