# Cure SMA Basic Research Grant -- Specific Aims

**Title**: Dual ROCK/LIMK2 Inhibition as SMN-Independent Complementary Therapy for SMA: Computational Drug Discovery and Preclinical Validation

**PI**: [PI Name, Institution]
**Mechanism**: Cure SMA Basic Research Grant ($140K/year, 2 years)
**Total Request**: $190K (Year 1: $110K; Year 2: $80K)

---

## Specific Aims

Spinal muscular atrophy (SMA) is caused by homozygous loss of *SMN1*, leading to SMN protein deficiency and progressive motor neuron degeneration. Three approved therapies -- nusinersen, onasemnogene abeparvovec, and risdiplam -- all function by restoring SMN protein. While transformative, these SMN-dependent approaches do not fully halt disease progression in many patients, particularly those treated after symptom onset (Mercuri et al., 2022; PMID 35101648). This persistent functional decline implicates SMN-independent pathological mechanisms that current therapies do not address. There is a critical unmet need for complementary therapies that target downstream pathology independently of SMN restoration.

We and others have identified the **ROCK-LIMK2-Cofilin-2 signaling axis** as a central, druggable mechanism of motor neuron degeneration in SMA. Our computational analysis of single-cell RNA-seq data from SMA mouse spinal cord (GSE208629) reveals that LIMK2 is upregulated 2.81-fold in SMA motor neurons (p=0.002), and that 10 of 14 actin pathway genes are coordinately dysregulated -- a pathway-level signature not seen in ALS motor neurons (GSE287257). Critically, Cofilin-2 (CFL2) shows a disease-specific expression pattern: upregulated +1.83-fold in SMA motor neurons but downregulated in ALS, making it both a potential biomarker and a functional readout of pathway rescue. Fasudil, a ROCK inhibitor, already demonstrated significant survival improvement in SMA mice without restoring SMN protein (Bowerman et al., 2012; PMID 22397316), providing direct in vivo proof of concept for this axis. Using AI-driven drug discovery (DiffDock molecular docking, ESM-2 protein language models, GenMol generative chemistry), we identified a stereo-resolved enantiomer of H-1152 -- designated (S,S)-H-1152 -- as a candidate dual ROCK2/LIMK2 inhibitor. ESM-2 embedding analysis confirms 88% kinase domain similarity between LIMK2 and ROCK2, providing a structural rationale for dual inhibition. ChEMBL contains 301 experimentally validated LIMK2 compounds (21 with sub-nanomolar potency), and LX-7101, a LIMK inhibitor, has entered Phase 1 clinical trials, establishing pathway druggability.

**Our central hypothesis is that dual inhibition of ROCK2 and LIMK2 by (S,S)-H-1152 will rescue actin dynamics and protect motor neurons through an SMN-independent mechanism, complementing existing therapies.** We propose three aims to bridge our computational findings to preclinical validation.

---

### Aim 1: Validate (S,S)-H-1152 as a Dual ROCK2/LIMK2 Inhibitor ($60K, Year 1)

**Rationale.** Our computational pipeline predicts that (S,S)-H-1152 binds both ROCK2 and LIMK2, but this has never been tested experimentally. The racemic parent compound H-1152 is a well-characterized ROCK inhibitor (Ki ~1.6 nM for ROCK2; Sasaki et al., 2002; PMID 12408861), yet its activity against LIMK2 is unknown. DiffDock docking scores the (S,S)-enantiomer at +0.957 for LIMK2 and +0.484 for ROCK2, suggesting preferential LIMK2 engagement -- a desirable profile given that LIMK2 is the rate-limiting kinase in SMA motor neurons (GSE208629). We will rigorously test this prediction using industry-standard biochemical assays.

**Approach.**
**(1a) Enantiopure synthesis.** We will synthesize (S,S)-H-1152 at >99% enantiomeric excess (ee) via chiral HPLC resolution of commercially available racemic H-1152 dihydrochloride (CAS 871543-07-6). The opposite enantiomer and racemic mixture will serve as controls. Deliverables: 500 mg (S,S)-H-1152, 100 mg opposite enantiomer, analytical certificates (chiral HPLC, NMR, MS). Estimated cost: $8K-15K.

**(1b) Binding kinetics by surface plasmon resonance (SPR).** Biacore SPR will measure true binding affinity (Kd), on-rate (ka), and off-rate (kd) for (S,S)-H-1152 against ROCK2, LIMK2, ROCK1, and LIMK1. Fasudil will serve as a reference compound. We predict Kd <10 nM for ROCK2 (based on parent compound) and Kd <500 nM for LIMK2 (novel). Estimated cost: $12K-18K.

**(1c) Enzymatic IC50 determination.** Radiometric kinase assays (10-point dose-response) will quantify inhibitory potency against ROCK2, LIMK2, ROCK1, and LIMK1 for all four test compounds. This will define the selectivity window and confirm whether (S,S)-H-1152 achieves meaningful dual inhibition. Estimated cost: $4K-8K.

**(1d) Kinome-wide selectivity (KINOMEscan).** DiscoverX scanMAX profiling across 468 kinases at 1 uM will establish the off-target liability profile. S-score <0.10 is the threshold for a selective compound. Follow-up Kd determination for the top 10-20 hits will define the true selectivity window. Estimated cost: $11K-18K.

**Milestones.** Go/no-go decision at Month 4: proceed to Aim 2 if LIMK2 IC50 <1 uM and ROCK2 IC50 <50 nM with acceptable selectivity (S-score <0.15). If (S,S)-H-1152 fails LIMK2 binding, we will pivot to the top-ranked LIMK2-selective compound from the pyrimido-indole series (Harrison et al., 2016; IC50 = 0.1 nM for LIMK2) and test it in combination with fasudil.

---

### Aim 2: Demonstrate Neuroprotection in SMA Motor Neurons ($50K, Year 1)

**Rationale.** Biochemical target engagement (Aim 1) must translate to functional rescue in disease-relevant cells. SMA iPSC-derived motor neurons recapitulate key pathological features including reduced neurite outgrowth, impaired NMJ formation, and altered actin dynamics (Nizzardo et al., 2015; PMID 26056268). Our single-cell data (GSE208629) predicts that ROCK-LIMK2 inhibition should reduce phospho-CFL2 levels and restore actin turnover. Bowerman et al. (2012) showed that fasudil's benefit in SMA mice was independent of SMN levels -- we will test whether dual ROCK2/LIMK2 inhibition provides greater rescue than ROCK inhibition alone, and whether it combines additively or synergistically with risdiplam.

**Approach.**
**(2a) iPSC-derived SMA motor neurons.** We will obtain SMA Type I patient iPSC-derived motor neurons (e.g., Coriell GM09677) with isogenic corrected and healthy controls. Motor neuron differentiation will follow established protocols (Du et al., 2015; PMID 25936564). We will characterize cultures for ISL1+/MNX1+ motor neuron identity (>60% purity target).

**(2b) Phospho-CFL2 rescue assay (primary endpoint).** Western blot and quantitative ELISA will measure the ratio of phospho-CFL2 to total CFL2 in SMA versus control motor neurons, treated with (S,S)-H-1152 (0.1-10 uM), fasudil (10-100 uM), or vehicle. A reduction of p-CFL2/CFL2 ratio toward control levels constitutes pathway rescue. This is a direct readout of on-target pharmacology for the ROCK-LIMK2-Cofilin axis.

**(2c) Neurite outgrowth and NMJ formation.** Automated high-content imaging (IncuCyte or ImageXpress) will quantify neurite length, branching, and complexity. For NMJ assessment, motor neurons will be co-cultured with C2C12 myotubes, and AChR clustering at synaptic contacts will be quantified by alpha-bungarotoxin staining. Both assays have been used to measure ROCK inhibitor effects in SMA models (Bowerman et al., 2012).

**(2d) Combination with risdiplam.** A 4x4 dose matrix of (S,S)-H-1152 and risdiplam will assess combination effects using the Bliss independence model. The mechanistic prediction is additivity or synergy, since risdiplam restores SMN protein (upstream) while (S,S)-H-1152 rescues actin dynamics (downstream). SMN protein levels will be measured by ELISA to confirm that (S,S)-H-1152 does not interfere with risdiplam's mechanism.

**Milestones.** Go/no-go at Month 9: proceed to Aim 3 if (S,S)-H-1152 significantly reduces p-CFL2/CFL2 ratio (p<0.05, n>=3 biological replicates) and improves at least one of neurite outgrowth or NMJ formation versus vehicle. Combination benefit over risdiplam alone would strongly support the translational hypothesis.

---

### Aim 3: In Vivo Proof of Concept in SMA Mouse Model ($80K, Year 2)

**Rationale.** Fasudil (a ROCK-only inhibitor) improved survival by ~25% in Smn2B/- mice at 30 mg/kg BID oral gavage (Bowerman et al., 2012; PMID 22397316). We hypothesize that dual ROCK2/LIMK2 inhibition with (S,S)-H-1152 will provide superior efficacy by blocking the pathway at two nodes simultaneously. The Smn2B/- model is well-characterized (median survival ~21 days), has a short study duration, and was used in the foundational fasudil study, enabling direct comparison. We will also test combination with low-dose risdiplam to model the clinical scenario of add-on therapy for patients already on SMN-restoring treatment.

**Approach.**
**(3a) Dosing and treatment groups.** Based on Bowerman et al. (2012) and H-1152's favorable ADMET profile (MW 300.3, cLogP 3.58, TPSA 33.2 -- BBB-permeable), we will use the Smn2B/- mouse model with the following groups (n=15 per group, both sexes): (i) Vehicle; (ii) Fasudil 30 mg/kg BID (positive control, replicating Bowerman 2012); (iii) (S,S)-H-1152 at two doses (10 and 30 mg/kg BID); (iv) Low-dose risdiplam (sub-therapeutic, ~0.3 mg/kg/day); (v) (S,S)-H-1152 30 mg/kg BID + low-dose risdiplam. Treatment from P3 to endpoint. Estimated cost: $45K-55K.

**(3b) Primary endpoints.** Survival (Kaplan-Meier analysis with log-rank test), body weight, and motor function (righting reflex, grip strength, open field locomotion) will be assessed daily/bi-weekly. These match the Bowerman 2012 protocol for direct comparability. A blinded observer will score all motor assessments.

**(3c) Pathology and biomarkers.** At endpoint, we will assess: (i) spinal cord motor neuron counts (ChAT+ cells in lumbar ventral horn); (ii) NMJ maturation (AChR cluster area, innervation ratio in the TVA muscle); (iii) muscle fiber cross-sectional area (tibialis anterior, H&E); (iv) phospho-CFL2 in spinal cord lysate (Western blot) as a pharmacodynamic biomarker; (v) serum NfL (neurofilament light) by Simoa as a translational neurodegeneration biomarker; (vi) GFAP as an astrogliosis marker (shown to respond to ROCK inhibition in the ROCK-ALS trial). Estimated cost: $20K-25K.

**(3d) Statistical plan.** Power analysis: n=15/group provides 80% power to detect a 25% survival improvement (alpha=0.05, two-sided), based on the effect size observed with fasudil (Bowerman 2012). Multiple comparison correction (Holm-Bonferroni) for secondary endpoints. Pre-registered analysis plan will be deposited on OSF before study initiation.

**Milestones.** Study completion by Month 20. Success criteria: (S,S)-H-1152 shows significant survival improvement over vehicle (p<0.05), and combination with risdiplam shows a trend or significant improvement over either monotherapy.

---

## Innovation and Significance

This proposal is innovative in three respects. **First**, it targets the ROCK-LIMK2-Cofilin-2 axis as an SMN-independent mechanism -- complementary to, not competing with, all three approved SMA therapies. **Second**, it leverages AI-driven drug discovery (DiffDock, ESM-2, GenMol) to identify a stereo-resolved dual-kinase inhibitor from an established pharmacophore, substantially reducing development risk. **Third**, it introduces CFL2 as a disease-specific biomarker (upregulated in SMA but downregulated in ALS), providing both a mechanistic readout and a potential clinical biomarker.

All computational methods, raw data, and analysis pipelines are publicly available on the SMA Research Platform (https://sma-research.info), an open-access resource supporting collaborative SMA drug discovery.

---

## Timeline Summary

| Period | Activity | Budget | Go/No-Go |
|--------|----------|--------|----------|
| Months 1-4 | Aim 1: Synthesis, SPR, IC50, KINOMEscan | $60K | LIMK2 IC50 <1 uM |
| Months 4-9 | Aim 2: iPSC-MN assays, p-CFL2 rescue, combinations | $50K | p-CFL2 rescue + neurite/NMJ improvement |
| Months 10-20 | Aim 3: Smn2B/- mouse study, pathology, biomarkers | $80K | Survival benefit |
| Months 21-24 | Analysis, manuscript, IND-enabling data package | -- | -- |

**Total: $190K over 2 years**

---

## Key References

- Bowerman M et al. (2012) Fasudil improves survival and promotes skeletal muscle development in a mouse model of spinal muscular atrophy. *BMC Medicine* 10:24. **PMID 22397316**
- Bowerman M et al. (2007) Rho-kinase inactivation prolongs survival of an intermediate SMA mouse model. *Hum Mol Genet* 16:3539. **PMID 17728540**
- Nolle A et al. (2011) The spinal muscular atrophy disease protein SMN is linked to the Rho-pathway via profilin. *Hum Mol Genet* 20:4865. **PMID 21920940**
- Koch JC et al. (2024) ROCK-ALS Phase 2 trial of fasudil in ALS. *Lancet Neurology*. **PMID 39424560**
- Bowerman M et al. (2017) ROCK-ERK signaling network in SMA. *Neurobiol Dis* 108:304. **PMID 28916199**
- Harrison BA et al. (2016) Tetrahydro-pyrimido-indoles as selective LIMK inhibitors. *MedChemComm* 7:1012. **DOI 10.1039/C5MD00473J**
- Wirth B (2021) PLS3 as a protective modifier in SMA. *Front Mol Neurosci*. **PMID 33071755**
- Mercuri E et al. (2022) SMA treatment landscape. *Nat Rev Neurol*. **PMID 35101648**
