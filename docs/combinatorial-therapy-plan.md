# Combinatorial Therapy Screen: SMN + CORO1C + UBA1 Triple-Axis Strategy for SMA

**Date**: 2026-03-21
**Status**: Computational Design Phase
**Platform Evidence Base**: 30,789 claims | 6,234 sources | 227 drug outcomes | 451 trials

---

## 1. Scientific Rationale: Why SMN Restoration Alone Is Insufficient

### 1.1 The Residual Disease Problem

All three approved SMN-restoring therapies -- nusinersen (Spinraza), risdiplam (Evrysdi), and onasemnogene abeparvovec (Zolgensma) -- have transformed SMA management. Yet platform evidence reveals persistent deficits even under optimal treatment:

- **Orofacial weakness persists** in nusinersen-treated SMA type 1 patients despite >2.5 years of therapy
- **Skeletal muscle abnormalities remain frequent** in symptomatic patients across all three approved therapies
- **Bulbar function shows limited improvement** in SMA type 1 measured by p-FOIS/CEDAS
- **Renal clearance continues to decline** despite nusinersen/risdiplam treatment (only tubular potassium handling improves)
- **Progressive spinal deformity** develops in treated SMA1 patients despite improved survival
- **Combination of nusinersen + onasemnogene abeparvovec** showed **no additional clinical benefit** versus nusinersen monotherapy alone (platform claim, high confidence)

This last finding is critical: **stacking two SMN-restoring agents on the same axis does not produce additive benefit**. The bottleneck is not SMN protein quantity -- it is downstream pathway restoration.

### 1.2 The Three-Axis Hypothesis

| Axis | Target | Rationale | Platform Convergence Score |
|------|--------|-----------|---------------------------|
| **Axis 1: SMN restoration** | SMN2 splicing / SMN1 replacement | Necessary foundation -- increases full-length SMN protein | 0.630 (high confidence, 2,628 claims) |
| **Axis 2: CORO1C activation** | Coronin 1C / F-actin / endocytosis | Rescues endocytic and cytoskeletal deficits downstream of SMN loss | 0.343 (low evidence volume, but 0.95 hypothesis confidence) |
| **Axis 3: UBA1 modulation** | Ubiquitin homeostasis / UPS | Restores ubiquitin-proteasome function collapsed by SMN depletion | 0.615 (high confidence, 230 claims) |

**Key mechanistic chain**: SMN loss --> UBA1 reduction (36-fold decrease in motor neurons) --> ubiquitin pathway collapse --> cytoskeletal protein degradation failure --> F-actin destabilization --> endocytic and synaptic vesicle recycling defects at NMJ --> motor neuron degeneration.

CORO1C and UBA1 address **different nodes** of this cascade. Combined with SMN restoration, this creates a three-point intervention strategy.

### 1.3 Platform Evidence Supporting Each Axis

**CORO1C (Axis 2) -- 9 platform claims:**
- CORO1C overexpression restores fluid-phase endocytosis in SMN-knockdown cells by elevating F-actin amounts
- CORO1C overexpression rescues axonal truncation and branching phenotype in Smn-depleted zebrafish
- CORO1C is an F-actin binding protein whose direct binding to PLS3 is dependent on calcium
- CORO1C is a protective modifier in SMA identified through PLS3 interactome interrogation
- Protective modifiers like PLS3 and CORO1C have practical therapeutic applications in rescuing SMA phenotypes

**UBA1 (Axis 3) -- 20 platform claims, 7 high-confidence (>0.80):**
- UBA1 was increased 36-fold in the ubiquitome of motor neurons vs. pluripotent stem cells (conf: 0.95)
- The UBA1-specific inhibitor PYR41 significantly decreased motor neuron viability (conf: 0.90)
- UBA1 is a key regulator of motor neuron differentiation through UPS-mediated cytoskeletal control (conf: 0.85)
- Ubiquitination pathway proteins are significantly disrupted in SMA Schwann cells, including reduced Uba1 (conf: 0.92)
- Pharmacological suppression of Uba1 in Schwann cells reproduces defective myelination observed in SMA (conf: 0.85)
- Ubiquitin pathways and Uba1 are key drivers of SMA pathogenesis across a broad range of cells and tissues (conf: 0.82)

**Existing synergy evidence from platform:**
- ML372 + ASO synergistically increases SMN production in SMA cells and model mice (conf: 0.92)
- Combination of treatment modalities targeting different pathways synergistically increases SMN levels more than individual treatments (conf: 0.90)
- Myostatin inhibition acts synergistically with SMN-restoring antisense therapy (conf: 0.90)
- Bortezomib + trichostatin A synergistically increases SMN protein levels in mouse tissue (conf: 0.93)
- Combined drugs that decrease SMN protein degradation and increase SMN gene transcription synergistically improve SMA disease phenotype (conf: 0.91)

---

## 2. Drug Selection for Combinatorial Screen

### 2.1 Axis 1: SMN-Restoring Agents (Backbone Therapy)

| Drug | Type | Status | Mechanism | Combination Suitability |
|------|------|--------|-----------|------------------------|
| **Risdiplam (Evrysdi)** | Small molecule splicing modifier | **FDA-approved** | Promotes SMN2 exon 7 inclusion; oral, crosses BBB | **Preferred backbone** -- oral, systemic, stable PK |
| **Nusinersen (Spinraza)** | ASO | **FDA-approved** | Targets ISS-N1 to promote SMN2 splicing; intrathecal | CNS-restricted; intrathecal route limits combination |
| **Onasemnogene abeparvovec (Zolgensma)** | AAV9 gene therapy | **FDA-approved** | Delivers functional SMN1 gene; single IV dose | One-time administration; ideal pre-combination foundation |

**Recommendation**: Use **risdiplam** as the SMN backbone for combination studies due to:
1. Oral bioavailability enabling easy co-administration
2. Systemic distribution (not CNS-restricted like nusinersen)
3. Continuous dosing allows steady-state SMN protein levels
4. Well-characterized safety profile in >2,000 patients
5. Predictable PK across age groups (platform: "reliable CNS penetration and predictable pharmacokinetics")
6. Mild AE profile (primarily GI, photosensitivity, liver enzyme elevations -- all transient)

### 2.2 Axis 2: CORO1C Activators / F-Actin-Endocytosis Pathway Modulators

CORO1C cannot be directly drugged with existing compounds. However, the pathway can be activated indirectly through several strategies:

| Compound | Mechanism Relevant to CORO1C Axis | Status | Key Considerations |
|----------|-----------------------------------|--------|-------------------|
| **Valproic acid (VPA)** | HDAC inhibitor; increases CORO1C/PLS3 expression via chromatin remodeling; also increases SMN protein | **Approved** (epilepsy, bipolar) | Extensive safety data; teratogenic; hepatotoxic at high doses; 5 completed SMA trials |
| **4-Aminopyridine (4-AP, dalfampridine)** | Potassium channel blocker; rescued SMA cortical neurons (conf: 0.88); improves motor behavior in SMA mice (conf: 0.92); **platform synergy score with CORO1C: +0.251** | **FDA-approved** (MS, walking improvement) | Seizure risk at supratherapeutic doses; narrow therapeutic index; well-characterized PK |
| **Panobinostat (Farydak)** | Pan-HDAC inhibitor; potent epigenetic reactivation | **FDA-approved** (multiple myeloma) | Serious AEs: cardiac (QTc prolongation), myelosuppression, GI; too toxic for chronic SMA use at oncology doses |
| **Vorinostat (Zolinza)** | HDAC inhibitor; Class I/II | **FDA-approved** (CTCL) | Pulmonary embolism, thrombocytopenia risk; less data in neurodegenerative context |
| **Trichostatin A (TSA)** | HDAC inhibitor; synergistically increases SMN with bortezomib (platform, conf: 0.93) | **Research tool** | Not clinically viable -- poor PK, toxicity; but validates the HDAC mechanism |

**Recommended candidates for screen:**
1. **VPA** (low-dose, 10-15 mg/kg/day) -- safest HDAC inhibitor with existing SMA clinical data
2. **4-AP** (10 mg BID, extended-release) -- independent mechanism; proven motor neuron rescue; unique CORO1C synergy signal
3. **Entinostat (MS-275)** -- Class I-selective HDAC inhibitor in Phase 3 for breast cancer; better selectivity than pan-HDAC inhibitors; oral; explored in combination oncology

### 2.3 Axis 3: UBA1 / Ubiquitin Pathway Modulators

| Compound | Mechanism Relevant to UBA1 Axis | Status | Key Considerations |
|----------|--------------------------------|--------|-------------------|
| **ML372** | Inhibits SMN ubiquitination, slowing degradation; synergistic with ASO (platform, conf: 0.92) | **Preclinical** | Not yet in clinical trials; strong SMA-specific data; directly relevant to UPS axis |
| **Bortezomib (Velcade)** | Proteasome inhibitor; with TSA, synergistically increases SMN (conf: 0.93) | **FDA-approved** (myeloma) | Peripheral neuropathy (dose-limiting); probably too toxic for chronic use in SMA |
| **Ixazomib (Ninlaro)** | Oral proteasome inhibitor | **FDA-approved** (myeloma) | Better tolerability than bortezomib; oral; still neuropathy risk |
| **Ubiquitin E1 activators** | Direct UBA1 activity enhancement | **Research stage** | No clinical candidates yet; target biology well-validated in SMA |
| **SAHA (vorinostat)** | HDAC inhibitor that also modulates ubiquitin pathway gene expression | **FDA-approved** | Dual HDAC/ubiquitin pathway modulation; toxicity concerns |
| **Bardoxolone methyl** | NRF2 activator; upregulates proteasome subunits and UBA1 expression | **Phase 3** (CKD) | Cardiac safety signal (BEACON trial); may be manageable at low doses |

**Recommended candidates for screen:**
1. **ML372** (preclinical combination with risdiplam) -- most direct UBA1-axis mechanism
2. **Low-dose ixazomib** (modulate proteasome flux without complete inhibition)
3. **Bardoxolone methyl** at sub-therapeutic doses (NRF2-mediated UBA1 upregulation)

---

## 3. Combinatorial Screening Matrix

### 3.1 Computational Phase (Tier 1)

**Objective**: Predict drug-drug interactions, pharmacokinetic conflicts, and synergy scores for all pairwise and triple combinations.

#### 3.1.1 Drug-Drug Interaction Predictions

| Combination | Metabolic Interaction Risk | Known DDI Concerns |
|-------------|---------------------------|-------------------|
| Risdiplam + VPA | **MODERATE** -- VPA inhibits CYP2C9, CYP2C19, UGT; risdiplam metabolized by FMO1/3 and CYP3A4. Minimal direct CYP overlap, but VPA glucuronidation competition possible. | Monitor liver function; VPA may slightly increase risdiplam exposure via UGT inhibition |
| Risdiplam + 4-AP | **LOW** -- 4-AP primarily renally eliminated (>90%); risdiplam hepatically metabolized. Orthogonal clearance routes. | Seizure threshold: both lower it (risdiplam: mild; 4-AP: known dose-dependent). Additive seizure risk. |
| Risdiplam + Ixazomib | **MODERATE** -- Ixazomib metabolized by CYP3A4 and multiple CYPs. Risdiplam is CYP3A4 substrate. Potential bidirectional interaction. | GI toxicity overlap (nausea, diarrhea); peripheral neuropathy from ixazomib |
| VPA + 4-AP | **LOW** -- VPA hepatic, 4-AP renal. No direct metabolic interaction. | VPA lowers seizure threshold (anticonvulsant paradox at certain doses); 4-AP raises it. Opposing effects on CNS excitability need careful titration. |
| VPA + Ixazomib | **MODERATE** -- VPA UGT/CYP inhibition may increase ixazomib exposure. | Hepatotoxicity overlap; both can cause thrombocytopenia |
| Triple: Risdiplam + VPA + 4-AP | **Preferred triple** -- lowest DDI risk; orthogonal mechanisms; all oral; all with human safety data | Seizure monitoring essential; liver function monitoring for VPA+risdiplam |
| Triple: Risdiplam + 4-AP + ML372 | **Unknown** -- ML372 PK not yet characterized in humans | Requires preclinical ADME before human combination |

#### 3.1.2 Computational Synergy Prediction Method

**Approach**: Bliss Independence Model + Network Pharmacology

1. **Single-agent effect estimation**: For each drug, estimate fractional effect on motor neuron survival using platform dose-response data and published EC50/IC50 values
2. **Bliss independence threshold**: E_combination_predicted = 1 - (1-E_A)(1-E_B)(1-E_C) for the triple
3. **Network analysis**: Score pathway overlap using platform knowledge graph (30,789 claims, graph edges)
4. **If observed > predicted**: Synergy (interaction term > 0)

**Platform data for single-agent estimates:**
- Risdiplam: SMN2 splicing increase ~2-4 fold; motor function improvement in >60% of patients
- VPA: Rescued cortical neuron vitality in SMNΔ7 model (preclinical success)
- 4-AP: Rescued neuronal survival and morphology in SMNΔ7 cortical neurons (conf: 0.88)
- ML372: Synergistic with ASO (nusinersen-class) in increasing SMN production

#### 3.1.3 Recommended Computational Tools

| Tool | Purpose | Application |
|------|---------|-------------|
| **SynergyFinder** (Ianevski et al.) | ZIP/Bliss/HSA/Loewe synergy models | Score all pairwise combinations from dose-response matrices |
| **DrugComb** (He et al.) | Drug combination database + prediction | Cross-reference existing combination data for our drug pairs |
| **DeepSynergy** (Preuer et al.) | Deep learning DDI prediction | Predict novel synergies using chemical + genomic features |
| **STITCH** (Kuhn et al.) | Protein-chemical interaction network | Map off-target interactions between all candidate drugs |
| **CYPReact / DDI-Pred** | CYP450 interaction prediction | Quantify metabolic DDI risk for all pairs |
| **Platform digital twin** | Multi-scale SMA simulation | Simulate motor neuron response to combinatorial perturbation |

### 3.2 In Vitro Screening Phase (Tier 2)

#### 3.2.1 Cell Models

| Model | Source | Relevance | Readouts |
|-------|--------|-----------|----------|
| **SMA patient iPSC-derived motor neurons** | Coriell (GM03813) or commercial (Axol) | Gold standard; human; disease-relevant | SMN protein, neurite length, survival, CORO1C/UBA1 levels |
| **SMNΔ7 primary cortical neurons (mouse)** | In-house from SMNΔ7 mice | Platform-validated model (VPA and 4-AP both succeeded here) | Same as above, cross-species validation |
| **SMA patient iPSC-derived Schwann cells** | Differentiation protocol | UBA1 dysregulation confirmed in this cell type (conf: 0.92) | Myelination, UBA1 levels, ubiquitin flux |
| **NMJ co-culture** (motor neuron + myotube) | iPSC-MN + C2C12 or patient myotubes | Models the NMJ synapse where endocytic defects manifest | NMJ formation, synaptic vesicle recycling, CMAP-like readouts |

#### 3.2.2 Screening Design: 6x6x6 Dose Matrix

**Axis 1 (risdiplam)**: 0, 10 nM, 30 nM, 100 nM, 300 nM, 1 uM
**Axis 2 (VPA)**: 0, 0.1 mM, 0.3 mM, 1 mM, 3 mM, 10 mM
**Axis 2-alt (4-AP)**: 0, 1 uM, 3 uM, 10 uM, 30 uM, 100 uM
**Axis 3 (ML372)**: 0, 0.1 uM, 0.3 uM, 1 uM, 3 uM, 10 uM

Total conditions: 6 x 6 x 6 = 216 per triple combination, in triplicate = 648 wells per matrix.

**Primary readouts (72h exposure)**:
1. **Motor neuron survival** (CellTiter-Glo)
2. **SMN protein levels** (HTRF/AlphaLISA)
3. **Neurite length** (high-content imaging, InCell 6500)
4. **CORO1C protein levels** (Western blot or MSD)
5. **UBA1 protein levels** (Western blot or MSD)
6. **Ubiquitin flux** (Ub-luc reporter or total mono/poly-Ub Western)

**Secondary readouts (selected hits)**:
7. **F-actin quantification** (phalloidin staining, high-content)
8. **Endocytosis rate** (FM4-64 dye uptake or transferrin uptake assay)
9. **Transcriptome** (bulk RNA-seq of top 3 combinations vs. single agents)
10. **Proteomics** (TMT-labeled quantitative proteomics of ubiquitinome)

#### 3.2.3 Analysis Pipeline

```
Raw dose-response data
  --> Normalize to DMSO control
  --> Fit Hill curves per single agent
  --> Calculate Bliss/Loewe expected additivity
  --> Score excess-over-Bliss (synergy) or deficit (antagonism)
  --> Identify synergistic dose windows
  --> Confirm with Chou-Talalay Combination Index (CI < 1 = synergy)
  --> Validate top combinations in NMJ co-culture
```

---

## 4. Specific Combination Regimens to Prioritize

### 4.1 Regimen A: Risdiplam + VPA + 4-AP (All Approved -- Fastest to Clinic)

**Rationale**: All three drugs are FDA-approved for other indications. This enables off-label combination studies or rapid investigator-initiated trials without IND requirements for each component.

| Parameter | Risdiplam | Valproic Acid | 4-Aminopyridine |
|-----------|-----------|---------------|-----------------|
| **Target axis** | SMN2 splicing | HDAC inhibition / CORO1C upregulation | K+ channel block / motor neuron rescue |
| **Dose (adult)** | 5 mg/day oral | 10-15 mg/kg/day oral (target trough: 50-75 ug/mL) | 10 mg BID extended-release (Ampyra) |
| **Dose (pediatric)** | 0.2 mg/kg/day oral | 10-15 mg/kg/day oral | Not yet established; 0.5-1 mg/kg/day proposed |
| **Route** | Oral (liquid or tablet) | Oral (liquid, sprinkles, or EC tablet) | Oral (tablet) |
| **Metabolism** | FMO1/3, CYP3A4 | Hepatic glucuronidation, CYP2C9/19 | Renal (>90%) |
| **Half-life** | ~50 hours | 8-20 hours | ~6 hours (ER: ~12 hours) |
| **Key AE** | Photosensitivity, diarrhea | Hepatotoxicity, teratogenicity, tremor | Seizures (dose-dependent), insomnia |
| **Monitoring** | LFTs, CBC | VPA trough levels, LFTs, ammonia, CBC | Renal function (CrCl >50 required), EEG if concerns |

**DDI management**:
- VPA may slightly increase risdiplam AUC via UGT inhibition --> start risdiplam at standard dose, monitor
- VPA + 4-AP: opposing CNS excitability effects may partially cancel seizure risk, but monitor with EEG
- No shared renal/hepatic clearance pathway between 4-AP and risdiplam/VPA

**Expected synergy basis**:
- Risdiplam increases SMN protein (necessary foundation)
- VPA: (a) increases SMN independently via HDAC inhibition, (b) upregulates CORO1C/PLS3 axis via chromatin remodeling, (c) neuroprotective via BDNF upregulation
- 4-AP: (a) improves neuronal excitability at NMJ, (b) rescued SMA cortical neurons (confirmed in platform), (c) platform synergy signal with CORO1C pathway (+0.251)

### 4.2 Regimen B: Risdiplam + VPA + ML372 (SMN + Epigenetic + Ubiquitin)

**Rationale**: ML372 directly addresses the UBA1/ubiquitin axis by inhibiting SMN ubiquitination. Platform shows synergistic SMN increase when ML372 combined with ASO (conf: 0.92). Combining with risdiplam (different SMN mechanism) + VPA (HDAC/CORO1C) covers all three axes.

**Status**: ML372 is preclinical. Requires ADME characterization and IND-enabling toxicology before clinical combination. Timeline: 3-5 years to first-in-human combination.

**Priority**: High for preclinical proof-of-concept. If ML372 + risdiplam + VPA shows >3x synergy in motor neuron survival assay, this justifies accelerated clinical development.

### 4.3 Regimen C: Zolgensma (foundation) --> Risdiplam + 4-AP (maintenance combination)

**Rationale**: Onasemnogene abeparvovec provides one-time SMN1 gene delivery as the foundation. After ~6 months stabilization, add risdiplam (SMN2 backup) + 4-AP (motor function enhancement). This represents a "hit hard, maintain broadly" strategy.

**Precedent**: Platform data shows patients already receiving sequential therapies (Zolgensma --> risdiplam) with continued positive outcomes. Adding 4-AP is pharmacologically rational.

---

## 5. Drug-Drug Interaction Risk Assessment

### 5.1 Pharmacokinetic Interactions

| Drug Pair | CYP Overlap | Transporter Overlap | Predicted Exposure Change | Clinical Significance |
|-----------|-------------|--------------------|--------------------------|-----------------------|
| Risdiplam + VPA | Low (FMO vs. CYP2C) | VPA inhibits OAT1/3 | Risdiplam AUC may increase 10-20% | Low -- within normal variability |
| Risdiplam + 4-AP | None | None (renal vs. hepatic) | No change expected | Negligible |
| VPA + 4-AP | None | VPA inhibits OAT; 4-AP partly OAT substrate | 4-AP AUC may increase 15-25% | **Moderate** -- monitor 4-AP trough; may need dose reduction to 5mg BID |
| Risdiplam + ML372 | Unknown | Unknown | Cannot predict | Requires in vitro DDI study |
| Risdiplam + Ixazomib | CYP3A4 overlap | P-gp substrate (both) | Bidirectional increase possible | **Moderate** -- therapeutic drug monitoring needed |

### 5.2 Pharmacodynamic Interactions

| Drug Pair | PD Interaction | Risk Level | Mitigation |
|-----------|---------------|------------|------------|
| Risdiplam + VPA | Both increase SMN protein (different mechanisms) | **Beneficial** -- additive/synergistic | Monitor for excessive SMN (theoretical; no known toxicity of SMN overexpression) |
| VPA + 4-AP | VPA anticonvulsant + 4-AP proconvulsant | **Moderate risk** | Start 4-AP at low dose (5 mg BID); titrate with EEG monitoring; VPA may be protective |
| Risdiplam + 4-AP | Risdiplam mild seizure risk + 4-AP seizure risk | **Low-moderate** | Baseline and periodic EEG; seizure diary |
| Triple combination | Additive hepatic stress (risdiplam + VPA) | **Moderate** | Monthly LFTs for first 6 months, then quarterly |

### 5.3 Cardiac Safety

- **VPA**: QTc neutral at therapeutic doses
- **4-AP**: QTc neutral at 10 mg BID; prolongation only at supratherapeutic (>15 mg BID)
- **Risdiplam**: No QTc signal in clinical program
- **Triple risk**: LOW -- no additive cardiac concern expected
- **Panobinostat** (excluded from primary screen): QTc prolongation is why it was not recommended

---

## 6. Preclinical Testing Pathway

### Phase 1: Computational Modeling (Months 1-3)

**Deliverables**:
1. Network pharmacology analysis of all pairwise and triple combinations using platform knowledge graph
2. PBPK modeling of triple combination (risdiplam + VPA + 4-AP) in pediatric and adult virtual populations
3. DDI simulation using SimCYP or GastroPlus
4. Synergy prediction using DeepSynergy trained on SMA platform data
5. Digital twin simulation of motor neuron response to triple perturbation

**Go/no-go**: Predicted synergy score >1.5 (Bliss excess) for at least one combination; no predicted severe PK interaction

### Phase 2: In Vitro Screening (Months 3-9)

**Deliverables**:
1. 6x6x6 dose matrix in SMA iPSC-motor neurons for Regimen A
2. Pairwise dose matrices for Regimens B and C
3. Synergy quantification (Chou-Talalay CI)
4. Target engagement confirmation: SMN protein (HTRF), CORO1C (Western), UBA1 (Western), F-actin (phalloidin), endocytosis (FM4-64)
5. Transcriptomic profiling of top 3 synergistic combinations

**Go/no-go**: CI < 0.7 (synergy) in motor neuron survival AND evidence of multi-axis target engagement (SMN + CORO1C + UBA1 all modulated)

### Phase 3: In Vivo Validation (Months 9-18)

**Model**: SMNΔ7 mice (severe SMA model; survival ~13 days untreated)

**Study design**:
- Group 1: Vehicle control (n=15)
- Group 2: Risdiplam alone (0.3 mg/kg/day oral, n=15)
- Group 3: Risdiplam + VPA (100 mg/kg/day, n=15)
- Group 4: Risdiplam + 4-AP (1 mg/kg BID, n=15)
- Group 5: Risdiplam + VPA + 4-AP (triple, n=15)
- Group 6: Risdiplam + ML372 (if available, n=15)

**Primary endpoints**:
- Survival (Kaplan-Meier)
- Body weight trajectory
- Righting reflex time

**Secondary endpoints**:
- Motor neuron counts (spinal cord L1-L5, NeuN/ChAT immunostaining)
- NMJ innervation (bungarotoxin + neurofilament)
- SMN protein (Western, spinal cord + brain + muscle)
- CORO1C protein levels (Western, spinal cord)
- UBA1 protein levels (Western, spinal cord + muscle)
- Ubiquitin conjugate profiling
- CMAP (compound muscle action potential) electrophysiology

**Go/no-go**: Triple combination significantly extends survival over risdiplam alone (p<0.05) AND shows superior NMJ innervation

### Phase 4: IND-Enabling Studies (Months 18-30)

Applicable only to Regimen A (all components already approved), enabling a faster regulatory path:

1. **28-day repeat-dose toxicology** of triple combination in rats and non-human primates
2. **ADME interaction study**: Confirm PK predictions from Phase 1 in vivo
3. **Genotoxicity battery** for the combination (individual components already cleared)
4. **Reproductive toxicology**: VPA is Category X -- this combination is contraindicated in pregnancy. Study design must reflect this.
5. **Safety pharmacology**: hERG, Irwin (CNS), respiratory -- focused on combination effects

### Phase 5: Clinical Development (Months 30-48)

**Proposed trial: Investigator-Initiated, Open-Label, Phase 1b/2a**

- **Population**: Adult SMA type 2/3 patients already on risdiplam (stable >12 months) with residual motor deficits
- **Design**: Sequential addition -- add VPA (Month 0), then add 4-AP (Month 3)
- **Primary endpoint**: Safety, tolerability, PK of triple combination
- **Secondary endpoints**: HFMSE, RULM, 6-MWT (motor function); SMN protein (blood); CORO1C/UBA1 levels (skin biopsy fibroblasts as surrogate)
- **n**: 20-30 patients
- **Duration**: 12 months treatment + 6 months follow-up
- **Regulatory path**: Since all three drugs are FDA-approved, an IND may not be required for an investigator-initiated study using approved drugs at approved doses for a new combination. Consult FDA Pre-IND meeting.

---

## 7. Safety Guardrails for the Triple Combination

### 7.1 Absolute Contraindications
- Pregnancy or planned pregnancy (VPA is teratogenic)
- Hepatic impairment (Child-Pugh B or C) -- VPA + risdiplam hepatic metabolism
- Renal impairment CrCl <50 mL/min (4-AP accumulation risk)
- History of seizures on 4-AP
- Urea cycle disorders (VPA-induced hyperammonemia)

### 7.2 Required Monitoring Protocol
| Time Point | Tests |
|------------|-------|
| Baseline | CBC, LFTs, ammonia, renal function, pregnancy test, EEG, ECG |
| Week 2, 4 | LFTs, VPA trough level, ammonia |
| Monthly (months 2-6) | CBC, LFTs, VPA trough, renal function |
| Quarterly (months 7+) | CBC, LFTs, VPA trough, renal function, ECG |
| As needed | EEG (if seizure concern), ammonia (if lethargy/confusion) |

### 7.3 Dose Modification Rules
- **LFT >3x ULN**: Hold VPA; continue risdiplam + 4-AP; recheck in 1 week
- **VPA trough >100 ug/mL**: Reduce VPA dose by 25%
- **Seizure on 4-AP**: Discontinue 4-AP permanently; continue risdiplam + VPA
- **Thrombocytopenia (<100k)**: Hold VPA; recheck in 1 week
- **Hyperammonemia (>50 umol/L) with symptoms**: Hold VPA; add L-carnitine 50 mg/kg/day

---

## 8. Computational Predictions from Platform Data

### 8.1 Network Pharmacology: Pathway Coverage

The triple combination (risdiplam + VPA + 4-AP) covers the following SMA-relevant pathways:

| Pathway | Risdiplam | VPA | 4-AP | Coverage |
|---------|-----------|-----|------|----------|
| SMN2 splicing | +++ | + | - | Primary |
| SMN protein stability | + | ++ (HDAC) | - | Dual |
| F-actin / endocytosis (CORO1C) | - | ++ (epigenetic) | + (indirect) | Addressed |
| Ubiquitin homeostasis (UBA1) | - | + (HDAC modulates UPS) | - | Partial |
| NMJ synaptic transmission | + | - | +++ | Dual |
| Neuronal excitability | - | +/- (complex) | +++ | Primary |
| Neuroprotection (BDNF) | - | ++ | - | Single |
| Myelination | + (SMN restoration) | + | - | Dual |

**Gap identified**: Axis 3 (UBA1/ubiquitin) is only partially addressed by VPA. This is why ML372 or an alternative UBA1-directed agent would strengthen the combination.

### 8.2 Platform Synergy Score Estimate

Based on the existing platform synergy data:

- ML372 + ASO: synergy confirmed (conf: 0.92)
- Bortezomib + TSA: synergy confirmed (conf: 0.93)
- Myostatin inhibitor + SMN-ASO: synergy confirmed (conf: 0.90)
- Multi-pathway combination: synergistic improvement > individual (conf: 0.91)
- 4-AP + CORO1C pathway: +0.251 synergy signal (platform discovery)

**Extrapolated triple synergy estimate**: Based on the pattern that orthogonal-mechanism combinations consistently show synergy in the platform (4/4 tested pairs), and the independent pathway coverage of risdiplam/VPA/4-AP, we estimate a **Bliss excess of 0.15-0.35** for the triple combination in motor neuron survival assays.

This would translate to an estimated **25-50% improvement in motor neuron survival** beyond risdiplam monotherapy.

---

## 9. Alternative and Emerging Candidates

### 9.1 Pipeline Drugs Worth Monitoring for Future Combinations

| Drug | Company | Phase | Mechanism | Combination Rationale |
|------|---------|-------|-----------|----------------------|
| **NMD-670** | NMD Pharma | Phase 1 | CaV2.1 calcium channel modulator (NMJ) | Direct NMJ enhancement; synergy with SMN restoration |
| **Apitegromab** | Scholar Rock | Phase 3 | Anti-myostatin | Muscle-targeted; addresses peripheral weakness; synergy with SMN confirmed |
| **Taldefgrobep alfa** | Biohaven | Phase 2 | Anti-myostatin | Alternative myostatin approach |
| **CinnatraRx p38α inhibitor** | CinnatraRx | Phase 1 | p38α MAPK inhibitor (neuroinflammation) | Addresses inflammatory component; orthogonal to SMN/CORO1C/UBA1 |
| **Reldesemtiv** | Cytokinetics | Phase 2 | Fast skeletal muscle troponin activator | Directly enhances muscle contractility; complementary to central therapies |

### 9.2 Gene Therapy Combinations

For the next generation (2028+):
1. **AAV-CORO1C**: Direct overexpression of CORO1C in motor neurons via AAV9 vector
2. **AAV-UBA1**: Restore UBA1 levels in motor neurons via gene therapy
3. **Dual-payload AAV**: SMN1 + CORO1C in a single vector (size limit: ~4.7 kb; both genes fit)

---

## 10. Summary: Recommended Screening Priorities

| Priority | Combination | Rationale | Timeline to Clinic |
|----------|-------------|-----------|-------------------|
| **1 (Highest)** | Risdiplam + VPA + 4-AP | All FDA-approved; fastest path; covers Axis 1 + partial Axis 2 + Axis 2-alt | 2-3 years (investigator-initiated) |
| **2 (High)** | Risdiplam + VPA + ML372 | Best mechanistic coverage of all 3 axes; ML372 preclinical | 4-6 years (IND required for ML372) |
| **3 (Medium)** | Zolgensma foundation + Risdiplam + 4-AP maintenance | Maximal SMN restoration + functional enhancement | 3-4 years |
| **4 (Medium)** | Risdiplam + NMD-670 + VPA | If NMD-670 Phase 1 succeeds; NMJ + SMN + epigenetic | 4-5 years |
| **5 (Exploratory)** | Risdiplam + low-dose ixazomib + 4-AP | Direct proteasome modulation; higher risk | 5-7 years |

---

## 11. Key References and Platform Sources

- Platform convergence scores: SMN2 (0.630), UBA1 (0.615), PLS3 (0.624), CORO1C (0.343), NCALD (0.330)
- ML372 + ASO synergy: platform claim conf 0.92, from published preclinical data
- Bortezomib + TSA synergy: platform claim conf 0.93
- 4-AP motor neuron rescue: platform claim conf 0.88 (SMNΔ7 model)
- 4-AP + CORO1C synergy signal: platform discovery score +0.251
- UBA1 36-fold increase in motor neuron ubiquitome: platform claim conf 0.95
- UBA1 disruption in SMA Schwann cells: platform claim conf 0.92
- Valproic acid SMA trials: NCT01033331, NCT00661453, NCT00374075, NCT00227266, NCT00481013 (all completed)
- Nusinersen + onasemnogene showed no additional benefit: platform post-market evidence

---

*Generated from SMA Research Platform analysis (30,789 claims, 6,234 sources, 451 clinical trials). This document is a computational screening design -- all combinations require experimental validation before clinical use.*
