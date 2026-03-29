# NCATS R21 Grant Application -- Preclinical Proof of Concept for Rare Diseases

**Title**: AI-Guided Dual Kinase Inhibition of the ROCK-LIMK2-Cofilin Axis as SMN-Independent Combination Therapy for Spinal Muscular Atrophy

**PI**: [PI Name, Institution]
**Mechanism**: NIH/NCATS R21 -- Exploratory/Developmental Research Grant
**Total Request**: $275,000 (Year 1: $150,000; Year 2: $125,000)
**Deadline**: June 2, 2026
**FOA**: PAR-XX-XXX (Preclinical Proof of Concept for Rare Diseases)

---

## Specific Aims Page

Spinal muscular atrophy (SMA) is caused by homozygous loss of *SMN1*, leading to SMN protein deficiency and progressive motor neuron degeneration. Three approved therapies -- nusinersen, onasemnogene abeparvovec, and risdiplam -- all function by restoring SMN protein. While transformative, these SMN-dependent approaches do not fully halt disease progression in many patients, particularly those treated after symptom onset (Mercuri et al., 2022; PMID 35101648). This persistent functional decline implicates SMN-independent pathological mechanisms that current therapies do not address. There is a critical unmet need for complementary therapies that target downstream pathology independently of SMN restoration.

We have used an AI-driven computational platform (sma-research.info) to identify the **ROCK-LIMK2-Cofilin-2 signaling axis** as a central, druggable mechanism of motor neuron degeneration in SMA. Our platform integrates 15,874 evidence claims from 9,023 sources with AI-powered structural biology tools (DiffDock v2.2 molecular docking, ESM-2 protein language models, GenMol generative chemistry) to discover and prioritize drug candidates. Three convergent lines of evidence support this axis as the strongest therapeutic target outside of SMN restoration:

**(1) Single-cell transcriptomic validation.** Analysis of scRNA-seq data from SMA mouse spinal cord (GSE208629; 39,136 cells, 208 motor neurons) reveals that 10 of 14 actin pathway genes are coordinately upregulated in SMA motor neurons. LIMK2 is upregulated 7.0-fold (log2FC=+2.81, p=0.002) and CFL2 is upregulated 3.6-fold (log2FC=+1.83, p=0.0002). This pathway-level signature is disease-specific: in ALS motor neurons (GSE287257; 61,664 cells, 240 MNs), CFL2 is downregulated -- the opposite direction -- confirming SMA-specific actin dysregulation.

**(2) In vivo proof of concept for ROCK inhibition.** Fasudil, a ROCK inhibitor, significantly improved survival in Smn2B/- SMA mice without restoring SMN protein (Bowerman et al., 2012; PMID 22397316). The ROCK-ALS Phase 2 trial (n=120) subsequently established fasudil's safety in human motor neuron disease (Lingor et al., 2024; PMID 39424560). However, ROCK inhibition alone is incomplete -- it does not directly address the LIMK2-Cofilin-2 node where pathway dysregulation is most severe in motor neurons.

**(3) AI-driven dual-target drug discovery.** Using DiffDock molecular docking across 501 compound-target combinations (121 positive binders), a stereo-resolved enantiomer panel, and ESM-2 kinase domain analysis (88.2% similarity between LIMK2 and ROCK2 ATP pockets), we identified three lead compounds predicted to inhibit both ROCK2 and LIMK2 simultaneously: **(S,S)-H-1152** (DiffDock LIMK2: +0.957, ROCK2: +0.484), **genmol_119** (LIMK2: +1.058, ROCK2: +0.509), and **sar_analog_053** (a structure-activity optimized analog). All three are BBB-permeable (CNS-MPO >= 4.67) with favorable ADMET profiles. ChEMBL analysis confirms LIMK2 pathway druggability: 301 experimentally validated inhibitors exist (21 sub-nanomolar), and LX-7101, a clinical LIMK inhibitor, reached Phase 1 (pChEMBL 8.8).

**Our central hypothesis is that simultaneous inhibition of ROCK2 and LIMK2 -- dual blockade of the kinase cascade upstream of Cofilin-2 -- will provide superior neuroprotection and functional rescue compared to ROCK inhibition alone, through an SMN-independent mechanism that complements existing therapies.** We propose two aims to bridge our AI-driven discovery to preclinical proof of concept.

---

### Aim 1: Validate Computationally Identified Dual ROCK2/LIMK2 Inhibitors ($100,000, Year 1)

**Rationale.** Our computational pipeline predicts that (S,S)-H-1152, genmol_119, and sar_analog_053 bind both ROCK2 and LIMK2, but these predictions require experimental confirmation. The racemic parent compound H-1152 is the most potent known ROCK inhibitor (Ki = 1.6 nM for ROCK2; 390-fold over PKA, 5,800-fold over PKC) but its activity against LIMK2 has never been tested. ESM-2 embedding analysis reveals 88.2% kinase domain similarity and 79.7% P-loop conservation between LIMK2 and ROCK2, providing a structural rationale for cross-target activity. No LIMK2-selective inhibitor has ever been tested in any SMA model -- this represents a critical pharmacological gap despite LIMK2 being the most upregulated kinase in SMA motor neurons.

**Approach.**

**(1a) Enantiopure synthesis of lead compounds.** We will synthesize (S,S)-H-1152 at >99% enantiomeric excess (ee) via chiral HPLC resolution of commercially available racemic H-1152 dihydrochloride (CAS 871543-07-6). Genmol_119, the (R,S)-enantiomer identified by GenMol as optimal for LIMK2, will be synthesized in parallel. The opposite enantiomers and racemic mixtures will serve as controls, enabling a complete stereoisomer structure-activity study. A third compound, sar_analog_053, will be synthesized by custom CRO. **Deliverables**: 500 mg each of three lead compounds + analytical certificates (chiral HPLC, NMR, MS). **Estimated cost**: $25,000.

**(1b) Binding kinetics by surface plasmon resonance (SPR).** Biacore SPR will measure true binding affinity (Kd), on-rate (ka), and off-rate (kd) for all three leads against ROCK2, LIMK2, ROCK1, and LIMK1. Fasudil and LX-7101 will serve as reference compounds. We predict Kd < 10 nM for ROCK2 (based on parent compound data) and Kd < 500 nM for LIMK2 (novel prediction). **Estimated cost**: $20,000.

**(1c) Enzymatic IC50 determination.** Radiometric kinase assays (10-point dose-response) will quantify inhibitory potency against ROCK2, LIMK2, ROCK1, and LIMK1 for all compounds. This will define the selectivity window and determine whether any lead achieves meaningful dual inhibition. **Estimated cost**: $15,000.

**(1d) Kinome-wide selectivity profiling.** DiscoverX scanMAX profiling across 468 kinases at 1 uM will establish the off-target liability profile for the top-performing lead. S-score < 0.10 is the threshold for a selective compound. Follow-up Kd determination for the top 10-20 hits will define the true selectivity window. Computational predictions identify ABL1 as the primary off-target concern (DiffDock +0.416 for genmol_119), but with a > 2.5x selectivity margin over the LIMK2 on-target score. **Estimated cost**: $20,000.

**(1e) ADMET confirmation panel.** Microsomal stability (human/mouse), CYP inhibition (5-isoform panel including CYP3A4 to assess risdiplam interaction potential), Caco-2 permeability, plasma protein binding, and hERG channel liability (patch clamp) for the lead compound. Our computational ADMET predictions (CNS-MPO 4.67-4.90, QED 0.836-0.948, no PAINS or Brenk alerts) will be experimentally validated. **Estimated cost**: $20,000.

**Go/No-Go Decision (Month 6):** Proceed to Aim 2 if at least one lead achieves LIMK2 IC50 < 1 uM AND ROCK2 IC50 < 50 nM with acceptable selectivity (S-score < 0.15) and no critical ADMET flags. If all three leads fail LIMK2 binding, we will pivot to the top-ranked pyrimido-indole LIMK2 inhibitor from ChEMBL (Harrison et al., 2016; IC50 = 0.1 nM) tested in combination with fasudil.

---

### Aim 2: Demonstrate Combination Efficacy in SMA Disease Models ($175,000, Years 1-2)

**Rationale.** Biochemical target engagement (Aim 1) must translate to functional rescue in disease-relevant cells and organisms. Our Bliss independence modeling predicts that dual ROCK2/LIMK2 blockade achieves 67% pathway correction (vs. 45% for fasudil alone), and that triple combination with risdiplam achieves 77% correction with near-normalization of the CFL2 phosphorylation biomarker (predicted p-CFL2 ratio: 0.33 vs. healthy 0.30). These computational predictions generate specific, testable hypotheses for the in vitro and in vivo experiments below.

**Approach.**

**(2a) iPSC-derived SMA motor neuron assays ($55,000, Months 7-12).** We will obtain SMA Type I patient iPSC-derived motor neurons (e.g., Coriell GM09677) with isogenic corrected and healthy controls. Using the lead compound from Aim 1:

- **p-CFL2 rescue assay (primary endpoint):** Western blot and quantitative ELISA will measure the ratio of phospho-CFL2 (Ser3) to total CFL2 in SMA versus control motor neurons, treated with lead compound, fasudil, or vehicle. A reduction of p-CFL2/CFL2 ratio toward control levels constitutes direct evidence of on-target pharmacology for the ROCK-LIMK2-Cofilin axis. This assay has never been performed in SMA motor neurons -- CFL2 phosphorylation state in SMA cells is unknown, despite CFL2 mRNA being among the most significantly upregulated transcripts in SMA motor neurons.

- **Neurite outgrowth and NMJ formation:** Automated high-content imaging (IncuCyte or ImageXpress) will quantify neurite length, branching, and complexity. For NMJ assessment, motor neurons will be co-cultured with C2C12 myotubes, and AChR clustering at synaptic contacts will be quantified by alpha-bungarotoxin staining.

- **Combination matrix with risdiplam:** A 4x4 dose matrix of lead compound and risdiplam will assess combination effects using the Bliss independence model. The mechanistic prediction is additivity or synergy, since risdiplam restores SMN protein (upstream) while the lead compound rescues actin dynamics (downstream). SMN protein levels will be measured by ELISA to confirm no interference with risdiplam's mechanism.

- **CFL2 biomarker validation:** p-CFL2/CFL2 ratio will be measured across all 7 treatment conditions (3 monotherapies + 3 pairs + 1 triple) at 24h, 72h, and 7d to establish CFL2 phosphorylation as a pharmacodynamic biomarker for pathway engagement.

**(2b) In vivo proof of concept in Smn2B/- mice ($100,000, Months 10-20).** The Smn2B/- model (median survival ~21 days) was used in the foundational fasudil study (Bowerman et al., 2012), enabling direct comparison. Treatment groups (n=15 per group, both sexes):

| Group | Treatment | Rationale |
|-------|-----------|-----------|
| 1 | Vehicle | Negative control |
| 2 | Fasudil 30 mg/kg BID | Positive control (replicates Bowerman 2012) |
| 3 | Lead compound 10 mg/kg BID | Low dose monotherapy |
| 4 | Lead compound 30 mg/kg BID | High dose monotherapy |
| 5 | Lead compound 30 mg/kg BID + fasudil 30 mg/kg BID | Dual ROCK/LIMK2 blockade |
| 6 | Sub-therapeutic risdiplam (~0.3 mg/kg/day) | SMN-restoring monotherapy (suboptimal) |
| 7 | Lead compound 30 mg/kg + sub-therapeutic risdiplam | Combination: SMN-independent + SMN-dependent |

- **Primary endpoints:** Survival (Kaplan-Meier, log-rank test), body weight, motor function (righting reflex, grip strength, open field locomotion). All assessments blinded.

- **Pathology and biomarkers at endpoint:** (i) Spinal cord motor neuron counts (ChAT+ cells, lumbar ventral horn); (ii) NMJ maturation (AChR cluster area, innervation ratio, TVA muscle); (iii) muscle fiber cross-sectional area (tibialis anterior, H&E); (iv) **phospho-CFL2 in spinal cord lysate** (Western blot) as pharmacodynamic biomarker linking in vitro to in vivo; (v) serum neurofilament light (NfL) by Simoa as translational neurodegeneration biomarker; (vi) GFAP as astrogliosis marker (shown to respond to fasudil in ROCK-ALS trial).

- **Statistical plan:** Power analysis: n=15/group provides 80% power to detect a 25% survival improvement (alpha=0.05, two-sided), based on Bowerman 2012 effect size. Multiple comparison correction (Holm-Bonferroni) for secondary endpoints. Pre-registered analysis plan deposited on OSF before study initiation.

**(2c) Open platform deliverable ($20,000, concurrent).** All computational methods, screening results, docking poses, single-cell analyses, and experimental data will be deposited on the SMA Research Platform (https://sma-research.info) -- an open-access resource currently hosting 15,874 evidence claims, 1,535 hypotheses, 68 molecular targets, and 451 clinical trial records. Raw data and analysis pipelines will be available on GitHub under a permissive license. This ensures full reproducibility and enables the SMA research community to build on our findings.

**Milestones.** In vitro go/no-go at Month 12: proceed to in vivo if lead compound significantly reduces p-CFL2/CFL2 ratio (p<0.05, n>=3 biological replicates) and improves at least one of neurite outgrowth or NMJ formation versus vehicle. In vivo study completion by Month 20. Success criteria: lead compound shows significant survival improvement over vehicle (p<0.05), and at least one combination group shows benefit over the best monotherapy.

---

## Innovation and Significance

This proposal is innovative in four respects:

**First, it applies AI-driven drug discovery to rare disease.** Our platform integrates DiffDock molecular docking, ESM-2 protein language models, and GenMol generative chemistry with systematic literature mining (15,874 claims from 9,023 sources) to identify drug candidates that would be invisible to conventional approaches. The stereo-resolved enantiomer panel and kinase domain similarity analysis represent novel computational methods for dual-target inhibitor design.

**Second, it targets the ROCK-LIMK2-Cofilin-2 axis as an SMN-independent mechanism.** While all three approved SMA therapies restore SMN protein, no approved or clinical-stage therapy addresses the downstream actin cytoskeletal pathology. Our single-cell data reveals a coordinated, pathway-level response (10/14 genes dysregulated) that is specific to SMA motor neurons and absent in ALS -- a distinction not previously reported. Dual ROCK2/LIMK2 blockade would be the first pharmacological strategy to target this axis at two nodes simultaneously, analogous to BRAF+MEK combinations in melanoma.

**Third, it introduces CFL2 phosphorylation as a disease-specific, pathway-specific biomarker.** CFL2 is upregulated in SMA motor neurons (+1.83-fold, p=0.0002) but downregulated in ALS motor neurons -- making it uniquely informative for SMA. The p-CFL2/total-CFL2 ratio provides a direct readout of on-target pharmacology that can be measured in iPSC-MN cultures, mouse tissue, and potentially in patient CSF. No current SMA clinical trial uses a pathway-level pharmacodynamic biomarker.

**Fourth, it delivers an open computational platform as a public resource.** The SMA Research Platform (sma-research.info) provides the entire SMA research community with searchable evidence, prioritized targets, drug candidates, and analytical tools. All data generated in this project will be immediately available, accelerating the field beyond the specific compounds tested here.

---

## Timeline and Budget Summary

| Period | Activity | Budget | Go/No-Go |
|--------|----------|--------|----------|
| Months 1-3 | Aim 1a: Synthesis of 3 lead compounds | $25,000 | Compounds in hand |
| Months 3-6 | Aim 1b-e: SPR, IC50, KINOMEscan, ADMET | $75,000 | LIMK2 IC50 < 1 uM, ROCK2 IC50 < 50 nM |
| Months 7-12 | Aim 2a: iPSC-MN assays, p-CFL2, combinations | $55,000 | p-CFL2 rescue + neurite/NMJ improvement |
| Months 10-20 | Aim 2b: Smn2B/- mouse study (7 groups x 15 mice) | $100,000 | Survival benefit + combination superiority |
| Months 1-24 | Aim 2c: Open platform data deposition | $20,000 | Data publicly available |
| Months 21-24 | Analysis, manuscript, IND-enabling data package | -- | -- |

**Total: $275,000 over 2 years**

---

## Evidence Summary

This proposal is grounded in a comprehensive AI-driven analysis of the SMA disease landscape. Our platform has aggregated 15,874 evidence claims from 9,023 peer-reviewed sources, generated 1,535 ranked hypotheses across 68 molecular targets, and cataloged 21 drugs and 451 clinical trials. For drug discovery, we performed 501 molecular dockings using DiffDock v2.2 (NVIDIA NIM), identifying 121 positive binders across 8 SMA-relevant target proteins. A complete stereoisomer panel of the H-1152 scaffold was evaluated, revealing stereospecific binding preferences for both ROCK2 and LIMK2. ESM-2 protein language model analysis of 683 kinase domain residues confirmed 88.2% structural similarity between LIMK2 and ROCK2 at the ATP-binding pocket, providing a biophysical rationale for dual inhibition. Single-cell transcriptomic analysis of 100,800 cells across two datasets (GSE208629: SMA mouse, 39,136 cells; GSE287257: ALS human, 61,664 cells) identified the ROCK-LIMK2-CFL2 axis as the most consistently dysregulated pathway in SMA motor neurons and revealed disease-specific signatures distinguishing SMA from ALS at single-cell resolution. LIMK2 emerged as the rate-limiting kinase in SMA motor neurons (7.0-fold upregulated, p=0.002), while LIMK1 -- the isoform targeted by most existing LIMK inhibitors -- is undetectable in SMA motor neurons, redirecting therapeutic strategy toward LIMK2-selective approaches. ChEMBL analysis confirmed pathway druggability with 301 experimentally validated LIMK2 compounds (21 sub-nanomolar) and one clinical-stage inhibitor (LX-7101, Phase 1). Bliss independence modeling of the triple combination (risdiplam + fasudil + dual ROCK/LIMK2 inhibitor) predicts 77% pathway correction with near-normalization of the CFL2 phosphorylation biomarker, generating testable hypotheses for the proposed experiments.

---

## Key References

1. Bowerman M et al. (2012) Fasudil improves survival and promotes skeletal muscle development in a mouse model of spinal muscular atrophy. *BMC Medicine* 10:24. **PMID 22397316**
2. Bowerman M et al. (2007) Rho-kinase inactivation prolongs survival of an intermediate SMA mouse model. *Hum Mol Genet* 16:3539. **PMID 17728540**
3. Nolle A et al. (2011) The spinal muscular atrophy disease protein SMN is linked to the Rho-pathway via profilin. *Hum Mol Genet* 20:4865. **PMID 21920940**
4. Schuning T et al. (2024) SMN binds F-actin and G-actin directly. *J Biol Chem*. **PMID 39305126**
5. Lingor P et al. (2024) ROCK-ALS: Fasudil Phase 2 trial in ALS (n=120). *Lancet Neurology*. **PMID 39424560**
6. Bowerman M et al. (2014) ROCK activity is elevated in SMA mouse spinal cord. *Neurobiol Dis*. **PMID 25221469**
7. Hensel N et al. (2017) ROCK-ERK signaling network in SMA. *Neurobiol Dis* 108:304. **PMID 28916199**
8. Walter LM et al. (2021) Actin-cofilin rods form in SMA cell models. *Cell Mol Life Sci*. **PMID 33986363**
9. Harrison BA et al. (2016) Tetrahydro-pyrimido-indoles as selective LIMK inhibitors. *MedChemComm* 7:1012. **DOI 10.1039/C5MD00473J**
10. Wirth B (2021) PLS3 as a protective modifier in SMA. *Front Mol Neurosci*. **PMID 33071755**
11. Mercuri E et al. (2022) SMA treatment landscape. *Nat Rev Neurol*. **PMID 35101648**
12. Koch JC et al. (2024) Fasudil oral formulation (Bravyl) Phase 2a in ALS: 15% NfL reduction, 28% slower ALSFRS-R decline.
13. Baldwin MK et al. (2024) MDI-114215: First CNS-penetrant LIMK1/2 allosteric inhibitor. *J Med Chem*.

---

## Distinction from Cure SMA Basic Research Grant

This NCATS R21 application differs from our parallel Cure SMA submission in four key respects:

| Dimension | Cure SMA Grant ($190K) | NCATS R21 ($275K) |
|-----------|----------------------|-------------------|
| **Emphasis** | Target validation (single lead compound) | AI methodology + dual-target mechanism |
| **Compounds** | (S,S)-H-1152 only | 3 leads: (S,S)-H-1152, genmol_119, sar_analog_053 |
| **In vivo scope** | 5 groups (75 mice) | 7 groups (105 mice), including dual blockade arm |
| **Platform deliverable** | Data sharing | Open platform (sma-research.info) as explicit deliverable |
| **ADMET** | Not included | Full ADMET panel with CYP interaction assessment |
| **Biomarker depth** | p-CFL2 as secondary readout | p-CFL2 as validated PD biomarker (7 conditions, 3 timepoints) |

The larger NCATS budget enables testing of three compounds (vs. one), a dual-blockade treatment arm that is central to the innovation, comprehensive ADMET characterization, and rigorous biomarker validation -- all elements that strengthen the translational path from computational prediction to IND-enabling data.

---

*Draft prepared 2026-03-24 | SMA Research Platform (sma-research.info)*
*All computational data and methods available at: https://sma-research.info*
