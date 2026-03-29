# PAK1/PAK4 Investigation: Alternative LIMK2 Activators in SMA

**Date**: 2026-03-25
**Trigger**: STRING-DB network expansion revealed PAK1/PAK4 activate LIMK2 independently of ROCK
**Critical implication**: ROCK inhibitors (Fasudil) alone may NOT fully suppress LIMK2

---

## 1. Executive Summary

PAK1 and PAK4 (p21-activated kinases) phosphorylate LIMK2 via a RAC1/Cdc42-dependent pathway that operates **independently of ROCK**. This means our current therapeutic strategy (Fasudil as ROCK inhibitor) has a **bypass vulnerability** -- even with ROCK fully inhibited, PAK-mediated LIMK2 activation could maintain pathological cofilin phosphorylation and actin rod formation.

**Key findings**:
- PAK4 is **upregulated in SMA-resistant ocular motor neurons** as a caspase inhibitor (LCM-seq data)
- PAK4 is **neuroprotective** in ALS motor neurons via CREB signaling (PMID:33615605)
- An existing hypothesis in our database (confidence 0.52) already predicts RAC1-PAK suppression shifts signaling to RhoA-ROCK-LIMK2
- 748 PAK4 and 570 PAK1 bioactive compounds exist in ChEMBL
- KPT-9274 (Padnarsertib) is in Phase 2 clinical trials (the most advanced PAK4 inhibitor)
- NVS-PAK1-1 preserves dendritic spines in Alzheimer's models (2025)
- FRAX486 rescues dendritic spine phenotypes in Fragile X mice

---

## 2. PAK Expression in Our SMA Data

### 2.1 Claims in Database (8 claims found)

| Claim | Confidence | Key Finding |
|-------|-----------|-------------|
| Ocular motor neurons upregulate Pak4 as a caspase inhibitor in SMA | 0.46 | PAK4 = resistance gene |
| PAK4 expression/activation decreased in ALS cell + mouse models | 0.46 | PAK4 loss = vulnerability |
| PAK4 overexpression protected MN from hSOD1^G93A^ degeneration via CREB | 0.36 | Neuroprotection mechanism |
| PAK4 silencing increased MN apoptosis by inhibiting CREB | 0.36 | Loss-of-function = death |
| PAK4 overexpression in hSOD1^G93A^ mice prolonged survival | 0.36 | In vivo efficacy |
| PAK4 overexpression suppressed MN degeneration in mice | 0.36 | In vivo efficacy |
| PAK4 overexpression promoted CREB pathway in mice | 0.30 | Mechanism confirmation |
| PAK4 may be therapeutic target in ALS via CREB anti-apoptosis | 0.26 | Therapeutic hypothesis |

### 2.2 Existing Targets

Both PAK1 and PAK4 are already registered as targets in the database:
- **PAK1** (id: `0a1a4e6e-bbb9-4e76-ac54-789c9631952f`) -- p21-Activated Kinase 1
- **PAK4** (id: `34c9ddab-26b8-4e1b-aff2-e33e42a9f0b8`) -- p21-Activated Kinase 4
- **LIMK2** (id: `52e82c74-8301-45c0-8752-1e1bb3c46211`)
- **RAC1** (id: `cd0a895b-ce34-4cbc-b9ff-600c81cf4393`)
- **RHOA** (id: `6ecbfd6e-3c9e-48f4-8361-368cec7f0fa1`)

### 2.3 Missing Graph Edges (ACTION NEEDED)

**No graph edges exist** connecting PAK1/PAK4 to LIMK2, RAC1, or RHOA. The following edges should be added:

| Source | Target | Relation | Effect | Confidence |
|--------|--------|----------|--------|-----------|
| RAC1 | PAK1 | activates | activates | 0.95 |
| RAC1 | PAK4 | activates | activates | 0.90 |
| PAK1 | LIMK2 | phosphorylates | activates | 0.90 |
| PAK4 | LIMK2 | phosphorylates | activates | 0.90 |
| RHOA | ROCK2 | activates | activates | 0.95 |
| ROCK2 | LIMK2 | phosphorylates | activates | 0.95 |
| PAK4 | CFL2 | indirect_inhibition | inhibits | 0.80 |

### 2.4 Existing Related Hypothesis

**RAC1-PAK pathway is suppressed in SMA motor neurons, shifting signaling to RhoA-ROCK-LIMK2** (confidence: 0.52)

This hypothesis partially addresses the PAK question but frames PAK suppression as a contributor to the problem. The STRING-DB data adds a new dimension: even with partial RAC1-PAK activity remaining, PAK-mediated LIMK2 activation could be a Fasudil-resistance mechanism.

---

## 3. Literature Evidence

### 3.1 PAK4 in Motor Neuron Disease

**Key paper**: Yeon et al. (2021) "PAK4 suppresses motor neuron degeneration in hSOD1^G93A^-linked ALS cell and rat models" (PMID: 33615605)
- PAK4 expression/activation decreases as ALS progresses (miR-9-5p mediated)
- PAK4 overexpression protects MN via CREB anti-apoptotic signaling
- PAK4 overexpression in spinal neurons prolongs survival in SOD1 mice
- **Paradox**: PAK4 is neuroprotective, but it also activates LIMK2 which phosphorylates cofilin

### 3.2 PAK4 in SMA-Resistant Neurons

**Key paper**: Nichterwitz et al. (2020) "LCM-seq reveals unique transcriptional adaptation mechanisms of resistant neurons" (PMID: 32820007)
- Ocular motor neurons (resistant to SMA) upregulate PAK4
- PAK4 acts as a caspase inhibitor in these resistant neurons
- Other resistance genes: Syt1, Syt5, Cplx2, Gdf15, Chl1, Lif

### 3.3 PAK-LIMK-Cofilin Signaling

The pathway operates as two parallel arms converging on LIMK:
```
RAC1/Cdc42 --> PAK1/PAK4 --> LIMK1/LIMK2 --> phospho-Cofilin (inactive) --> actin stabilization
     |
RhoA --> ROCK1/ROCK2 --> LIMK1/LIMK2 --> phospho-Cofilin (inactive) --> actin stabilization
```

Both arms phosphorylate LIMK at Thr508 (LIMK2) / Thr505 (LIMK1), rendering them active kinases that inactivate cofilin.

### 3.4 Cofilin-Actin Rods in Neurodegeneration

- Dysregulation of actin dynamics is associated with overexpression of phosphorylated LIMK and phosphorylated cofilin in sporadic ALS patients
- Cofilin-actin rods block intracellular trafficking of mitochondria --> ATP depletion --> synaptic failure
- ALS and FTD showcase cofilin's association with C9ORF72, affecting actin dynamics

---

## 4. PAK Inhibitor Landscape

### 4.1 Clinical-Stage Compounds

| Compound | Target | Phase | Status | Notes |
|----------|--------|-------|--------|-------|
| **KPT-9274 (Padnarsertib)** | PAK4 + NAMPT (dual) | Phase 2 | Active (pediatric sarcoma) | RPD designation 2024; Phase 1 in solid tumors terminated |
| **PF-3758309** | Pan-PAK (Group I + II) | Phase 1 | Withdrawn | Poor oral bioavailability in humans |
| **NVS-PAK1-1** | PAK1 | Preclinical | Active (AD research) | Preserves dendritic spines; 2025 Alzheimer's data |

### 4.2 Preclinical Neuroscience Compounds

| Compound | Target | IC50 | Neuro Evidence | ChEMBL |
|----------|--------|------|----------------|--------|
| **FRAX486** | PAK1 (14 nM), PAK2 (33 nM), PAK3 (39 nM), PAK4 (575 nM) | 14 nM PAK1 | Rescues dendritic spine phenotypes in Fmr1 KO (Fragile X) mice. Single dose sufficient. | CHEMBL3609326 |
| **FRAX597** | PAK1 (8 nM), PAK2 (13 nM), PAK3 (19 nM) | 8 nM PAK1 | Inhibits NF2-associated schwannomas; orally available | CHEMBL5661936 |

### 4.3 ChEMBL Bioactivity Data

- **PAK4**: 748 bioactive compounds (top: pChEMBL 9.03, CHEMBL3669583)
- **PAK1**: 570 bioactive compounds (top: pChEMBL 9.67, staurosporine -- non-selective)
- **PF-3758309** (CHEMBL3128043): pChEMBL 8.89 for PAK4, Phase 1 compound

### 4.4 Top 3 PAK Inhibitors for Potential LIMK2 Docking

| Rank | Compound | Rationale | ChEMBL |
|------|----------|-----------|--------|
| 1 | **FRAX486** | Best neuro data (Fragile X rescue), Group I selectivity | CHEMBL3609326 |
| 2 | **NVS-PAK1-1** | Most recent neuro data (AD 2025), PAK1-selective | CHEMBL5091324 |
| 3 | **PF-3758309** | Pan-PAK, most clinical data (Phase 1), MW 490.6 | CHEMBL3128043 |

---

## 5. The PAK Paradox in SMA

### 5.1 Dual Role of PAK4

PAK4 has a **paradoxical role** in SMA/motor neuron disease:

**Protective function (pro-survival)**:
- Inhibits caspase activation --> prevents apoptosis
- Activates CREB signaling --> neuroprotection
- Upregulated in SMA-resistant ocular motor neurons
- PAK4 loss correlates with ALS progression

**Potentially harmful function (pro-pathology)**:
- Activates LIMK2 --> phosphorylates cofilin --> disrupts actin dynamics
- Creates Fasudil resistance by maintaining LIMK2 activation via non-ROCK pathway
- May contribute to cofilin-actin rod formation

### 5.2 Therapeutic Implications

**Option A: Dual ROCK + PAK inhibition (aggressive)**
- Pro: Complete LIMK2 suppression
- Con: Lose PAK4-CREB neuroprotection; may accelerate MN death
- Risk: HIGH

**Option B: LIMK2-specific inhibition (bypass both upstream kinases)** -- RECOMMENDED
- Pro: Blocks pathological cofilin phosphorylation regardless of source (ROCK or PAK)
- Pro: Preserves PAK4-CREB neuroprotection (CREB activation is independent of LIMK2)
- Con: LIMK2 inhibitors are less developed than ROCK inhibitors
- Risk: MODERATE -- most elegant solution

**Option C: Fasudil + PAK-activating strategy (paradox exploitation)**
- Pro: Inhibit ROCK-LIMK2 axis while boosting PAK4-CREB neuroprotection
- Con: PAK4 activation would also activate LIMK2, partially counteracting Fasudil
- Risk: Complex

**Option D: Sequential/conditional therapy**
- Early SMA: PAK4 agonism to delay apoptosis
- Late SMA: LIMK2 inhibition to restore actin dynamics
- Risk: Requires biomarker-guided switching

### 5.3 Recommendation

**Option B (LIMK2-specific inhibition) is the strongest strategy.** It:
1. Bypasses the PAK paradox entirely
2. Blocks cofilin phosphorylation from both ROCK and PAK pathways
3. Preserves PAK4-CREB neuroprotection
4. Aligns with our existing genmol_119 hypothesis (AI-designed LIMK2 binder)
5. Validates our existing triple therapy model (Risdiplam + Fasudil + LIMK2i)

The triple therapy now has additional mechanistic rationale: LIMK2i catches what Fasudil misses via the PAK bypass.

---

## 6. Proposed New Hypotheses

### Hypothesis 1: PAK4-CREB Neuroprotection as SMA Resistance Biomarker
- PAK4 expression level in motor neurons predicts vulnerability to SMA-induced degeneration
- Type: `biomarker` | Confidence: 0.55

### Hypothesis 2: PAK-Mediated LIMK2 Activation as Fasudil Resistance Mechanism
- Residual PAK-mediated LIMK2 phosphorylation maintains pathological cofilin inactivation during ROCK inhibitor therapy
- Type: `mechanism` | Confidence: 0.50

### Hypothesis 3: LIMK2-Specific Inhibition Outperforms ROCK Inhibition
- Direct LIMK2 inhibition blocks both ROCK-mediated and PAK-mediated cofilin phosphorylation
- Type: `therapeutic` | Confidence: 0.60

### Hypothesis 4: PAK4 Agonism + LIMK2 Inhibition as Optimal SMA Combination
- Combining PAK4 activation (neuroprotection via CREB) with LIMK2 inhibition (actin restoration) separates beneficial and harmful PAK signaling arms
- Type: `combinatorial` | Confidence: 0.45

---

## 7. Database Actions Needed

### 7.1 Graph Edges to Add
Add the PAK-LIMK2-ROCK signaling edges listed in Section 2.3.

### 7.2 Hypotheses to Create
Add the 4 hypotheses from Section 6.

### 7.3 Drugs to Add
- FRAX486 (PAK1/2/3 inhibitor, neuro-validated)
- NVS-PAK1-1 (PAK1 inhibitor, AD-validated)
- KPT-9274/Padnarsertib (PAK4+NAMPT dual inhibitor, Phase 2)

### 7.4 Docking Candidates
Dock FRAX486, NVS-PAK1-1, and PF-3758309 against LIMK2 to check cross-reactivity.

---

## 8. Impact on Existing Hypotheses

| Existing Hypothesis | Impact |
|---------------------|--------|
| Triple therapy (Risdiplam + Fasudil + LIMK2i) | **STRENGTHENED** -- PAK bypass justifies why LIMK2i is needed on top of Fasudil |
| ROCK-LIMK2-CFL2 axis inhibition rescues NMJ defects | **STILL VALID** -- but incomplete without considering PAK input |
| Dual ROCK1/ROCK2 + LIMK2 inhibition prevents resistance | **STRENGTHENED** -- PAK bypass = molecular resistance mechanism |
| RAC1-PAK suppression shifts to RhoA-ROCK-LIMK2 | **REFINED** -- suppressed but not absent PAK still feeds LIMK2 |
| genmol_059: dual ROCK2/LIMK2 inhibitor | **MORE IMPORTANT** -- dual inhibition captures both upstream arms |
| genmol_119: AI-designed LIMK2 binder | **HIGHEST PRIORITY** -- pure LIMK2 inhibition is the cleanest solution |

---

## Sources

- [PAK4 suppresses MN degeneration in ALS](https://pubmed.ncbi.nlm.nih.gov/33615605/)
- [LCM-seq: resistant neurons in SMA](https://pubmed.ncbi.nlm.nih.gov/32820007/)
- [NVS-PAK1-1 preserves dendritic spines in AD](https://alz-journals.onlinelibrary.wiley.com/doi/10.1002/alz.71033)
- [FRAX486 rescues Fragile X phenotypes](https://pmc.ncbi.nlm.nih.gov/articles/PMC3619302/)
- [Cofilin-actin rods in neurodegeneration](https://pmc.ncbi.nlm.nih.gov/articles/PMC9535683/)
- [LIMK1-cofilin-actin axis in AD dendritic spines](https://www.nature.com/articles/s41419-025-07741-7)
- [PAK inhibitor clinical development review](https://pmc.ncbi.nlm.nih.gov/articles/PMC5973817/)
- [PAK4 inhibitors as anti-tumor agents](https://pmc.ncbi.nlm.nih.gov/articles/PMC9465411/)
- [KPT-9274 Phase I](https://www.annalsofoncology.org/article/S0923-7534(20)37794-2/fulltext)
- [FRAX597 inhibits NF2-associated schwannomas](https://pmc.ncbi.nlm.nih.gov/articles/PMC3790009/)
- [PAK inhibition restores neurite outgrowth in Down Syndrome](https://link.springer.com/article/10.1007/s12640-023-00638-3)
- [KPT-9274 pipeline (Karyopharm)](https://www.karyopharm.com/science/pipeline/oral-dual-inhibitor-of-pak4-and-nampt-kpt-9274/)
- [FDA kinase inhibitors for neurological disorders (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12288644/)
