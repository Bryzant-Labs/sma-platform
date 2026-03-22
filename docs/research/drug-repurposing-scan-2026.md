# SMA Drug Repurposing Scan -- March 2026

**Generated**: 2026-03-22
**Scope**: Novel drug repurposing candidates for SMA beyond current pipeline
**Focus**: Actin dynamics, neuroprotection, SMN enhancement, combination strategies

---

## Executive Summary

This scan identifies **18 drug repurposing candidates** across 7 therapeutic axes for SMA. The highest-priority additions to the platform are:

1. **MW150** (p38 MAPK inhibitor) -- direct SMA synergy data with SMN-inducing drugs (EMBO Mol Med 2025)
2. **Panobinostat** (pan-HDAC inhibitor) -- most potent SMN2 exon 7 splicing corrector, BBB-penetrant, synergy with nusinersen
3. **MS023** (Type I PRMT inhibitor) -- promotes SMN2 exon 7 inclusion, synergizes with nusinersen in SMA mice
4. **Apitegromab** (anti-myostatin) -- Phase 3 SAPPHIRE met primary endpoint, FDA BLA under review
5. **MDI-117740** (LIMK inhibitor) -- most selective LIMK inhibitor to date, directly targets actin-rod pathway

---

## 1. ROCK Inhibitors Beyond Fasudil

### 1a. Y-27632

| Field | Detail |
|-------|--------|
| **Mechanism** | Pan-ROCK1/2 inhibitor (research tool compound) |
| **Current indication** | Research use only (not clinically approved) |
| **Evidence for SMA** | **Indirect**: Protects against excitotoxicity-induced neuronal death in vivo/in vitro. Increases dendritic protrusion density in hippocampal neurons. Reduces p-LIMK and p-cofilin (same pathway as fasudil in SMA). Protects dopaminergic neurons. Enhances HK2 mitochondrial localization, improving bioenergetics. |
| **BBB penetration** | Yes (demonstrated in preclinical models) |
| **Clinical trial status** | None (research tool only, no GMP formulation) |
| **Feasibility for SMA** | **Low** -- Not a drug candidate; serves as proof-of-concept for ROCK inhibition class |
| **Key references** | PMID: 22810835, PMC11965611 |

### 1b. Ripasudil (Glanatec)

| Field | Detail |
|-------|--------|
| **Mechanism** | Pan-ROCK1/2 inhibitor (Ki = 51 nM ROCK1, 19 nM ROCK2) |
| **Current indication** | Approved (ophthalmic) for glaucoma/ocular hypertension (Japan 2014) |
| **Evidence for SMA** | **Indirect**: Same ROCK pathway as fasudil. ROCK inhibition reduces p-LIMK/p-cofilin in SMA mice, corrects actin polymerization imbalance. Ripasudil has higher ROCK2 selectivity than fasudil, potentially more relevant for CNS (ROCK2 predominates in neurons). |
| **BBB penetration** | Unknown for systemic use (only approved as eye drops; would need oral reformulation) |
| **Clinical trial status** | Approved for glaucoma (topical). No CNS trials. |
| **Feasibility for SMA** | **Medium** -- Approved safety profile (topical), but systemic/oral formulation and BBB penetration data needed. Could leapfrog fasudil if oral BBB-penetrant formulation developed. |
| **Key references** | PMC10640453 |

### 1c. Netarsudil (Rhopressa)

| Field | Detail |
|-------|--------|
| **Mechanism** | Dual ROCK + norepinephrine transporter (NET) inhibitor |
| **Current indication** | FDA-approved (ophthalmic, 0.02%) for glaucoma (2017) |
| **Evidence for SMA** | **Very indirect**: ROCK inhibition pathway relevant, but NET inhibition adds complexity. Minimal systemic absorption after topical use -- plasma levels generally undetectable. |
| **BBB penetration** | No systemic formulation exists. Highly protein-bound. Not viable for CNS delivery in current form. |
| **Clinical trial status** | Ophthalmic only. No oral/systemic development. |
| **Feasibility for SMA** | **Low** -- No systemic bioavailability, no oral formulation, dual mechanism (NET) may be unwanted. Fasudil remains the better ROCK inhibitor for SMA. |
| **Key references** | DrugBank DB13931 |

### Summary: ROCK Inhibitor Landscape for SMA

Fasudil remains the lead ROCK inhibitor for SMA (PMID: 22397316 -- improves survival in SMA mice, increases muscle fiber size, restores NMJ maturation). Ripasudil is the most interesting second-generation candidate due to higher ROCK2 selectivity, but requires systemic reformulation. **Recommendation**: Keep fasudil as primary, monitor ripasudil oral development.

---

## 2. LIMK Inhibitors

### 2a. MDI-117740

| Field | Detail |
|-------|--------|
| **Mechanism** | Highly potent dual LIMK1/2 inhibitor; most selective LIMK inhibitor reported to date (minimal kinome promiscuity, including no RIPK1 off-target) |
| **Current indication** | Preclinical (lead optimization stage) |
| **Evidence for SMA** | **Strong mechanistic rationale**: LIMK is directly downstream of ROCK in the RhoA/ROCK/LIMK/cofilin pathway. In SMA, ROCK inhibition with fasudil reduces p-LIMK and p-cofilin, correcting actin dynamics. Direct LIMK inhibition could achieve the same effect more selectively, avoiding ROCK's broader signaling roles. LIMK overactivation implicated in neurodegeneration (ALS, AD, schizophrenia). |
| **BBB penetration** | Improved DMPK properties reported; suitable for in vivo evaluation. CNS penetration not yet confirmed in published data. |
| **Clinical trial status** | Preclinical. Related compound MDI-114215 published Dec 2024 (PMID: 39711116) for Fragile X Syndrome, demonstrating the class is progressing toward clinic. |
| **Feasibility for SMA** | **Medium-High** -- Most selective LIMK inhibitor available. Directly targets the actin-rod pathway. However, still preclinical with no SMA-specific data yet. |
| **Key references** | J Med Chem 2025 (DOI: 10.1021/acs.jmedchem.5c00974), PMID: 39711116 (MDI-114215) |

### 2b. BMS-5 (LIMKi 3)

| Field | Detail |
|-------|--------|
| **Mechanism** | Potent LIMK1/2 inhibitor (IC50: 7 nM LIMK1, 8 nM LIMK2) |
| **Current indication** | Research tool compound (Bristol-Myers Squibb) |
| **Evidence for SMA** | **Indirect**: Same pathway rationale as MDI-117740. Less selective than MDI-117740 (more off-targets). Originally developed for oncology (cytoskeletal disruption). |
| **BBB penetration** | Unknown; likely poor (designed for oncology, not CNS) |
| **Clinical trial status** | None (tool compound only) |
| **Feasibility for SMA** | **Low** -- Tool compound, less selective, no CNS optimization. MDI-117740 is the better LIMK candidate. |
| **Key references** | MedChemExpress product data |

### Summary: LIMK Inhibitors for SMA

LIMK inhibition is a compelling SMN-independent strategy directly addressing the actin-rod phenotype. MDI-117740 is the lead candidate -- most selective LIMK inhibitor to date, with DMPK properties suitable for in vivo work. **Recommendation**: Add MDI-117740 to the platform as a high-priority preclinical candidate. The MDI series (Fragile X program) may provide clinical path data.

---

## 3. HDAC Inhibitors (Beyond VPA)

### 3a. Panobinostat (Farydak/LBH589)

| Field | Detail |
|-------|--------|
| **Mechanism** | Pan-HDAC inhibitor (Class I, II, IV) |
| **Current indication** | FDA-approved for multiple myeloma (2015) |
| **Evidence for SMA** | **Direct and strong**: Most potent HDAC inhibitor for SMN2 exon 7 splicing correction at 25 nM (more active than all other tested HDAC inhibitors). Enhances SMN2 gene expression via histone acetylation and chromatin relaxation at SMN2 locus. **Synergy with nusinersen**: Combined treatment in SMA cell models showed panobinostat increases SMN2 transcript availability, allowing ASO (nusinersen) to work at otherwise subtherapeutic doses (20 nM). This could enable lower/less frequent intrathecal nusinersen dosing. |
| **BBB penetration** | **Yes** -- Confirmed in murine model (PMC8896403). Achieves effective brain concentrations. Clinically tested in glioma at relevant CNS concentrations. |
| **Clinical trial status** | Approved for myeloma. No SMA trials yet. Tested in glioma (CNS). |
| **Feasibility for SMA** | **High** -- FDA-approved, oral, BBB-penetrant, direct SMN2 splicing data, synergy with nusinersen demonstrated in vitro. Key concern: toxicity profile in cancer (cytopenias, diarrhea, cardiac) may limit chronic use at oncology doses. Needs dose-finding for SMA (effective at much lower concentrations). |
| **Key references** | PMC8896403 (BBB), Poletti 2020 (PMID: 32056234), SMA News Today 2019 |

### 3b. Vorinostat (Zolinza/SAHA)

| Field | Detail |
|-------|--------|
| **Mechanism** | Pan-HDAC inhibitor (Class I, II) |
| **Current indication** | FDA-approved for cutaneous T-cell lymphoma (2006) |
| **Evidence for SMA** | **Direct**: Evaluated in SMA cell models; increases SMN protein levels. Less potent than panobinostat for SMN2 exon 7 correction. Broader repurposing evidence for brain disorders. |
| **BBB penetration** | **Partial** -- Crosses BBB but with limited CNS exposure. Brain-to-plasma ratio suboptimal for chronic neurological use. |
| **Clinical trial status** | Approved for CTCL. Phase 2 trials in glioblastoma (limited CNS efficacy). No SMA trials. |
| **Feasibility for SMA** | **Medium** -- Less potent than panobinostat for SMN2, inferior BBB penetration. Panobinostat is the better candidate in this class. |
| **Key references** | Springer s12017-021-08660-4, ResearchGate pub/6978497 |

### 3c. Valproic Acid (VPA) -- Status Update

| Field | Detail |
|-------|--------|
| **Mechanism** | Weak HDAC inhibitor (Class I/IIa); multiple mechanisms (GABA, sodium channels) |
| **Current indication** | FDA-approved for epilepsy, bipolar disorder, migraine |
| **Evidence for SMA** | **Direct but disappointing**: Multiple clinical trials completed. Meta-analysis of 5 trials (n=126): no significant improvement in gross motor function. No significant change in full-length SMN or exon 7-lacking SMN. VALIANT trial: no change in primary/secondary outcomes at 6 or 12 months. Benefit may be limited to children <5 years with SMA type II. |
| **BBB penetration** | **Yes** -- Excellent CNS penetration |
| **Clinical trial status** | Multiple completed Phase 2/3 trials. Failed to show efficacy. |
| **Feasibility for SMA** | **Low as monotherapy** -- Clinical evidence negative. May retain value only as part of combination (Risdiplam + VPA + 4-AP) where it contributes modest HDAC inhibition alongside stronger SMN-restoring agents. |
| **Key references** | PMID: 30796634 (meta-analysis), PMID: 23681940 (VALIANT) |

### Summary: HDAC Inhibitors for SMA

Panobinostat is the standout candidate -- most potent SMN2 splicing corrector, BBB-penetrant, synergy with nusinersen. **Recommendation**: Add panobinostat to platform as HIGH priority. Consider replacing VPA with panobinostat in combination strategies (much more potent HDAC inhibition at lower doses).

---

## 4. Autophagy Modulators

### 4a. Rapamycin (Sirolimus)

| Field | Detail |
|-------|--------|
| **Mechanism** | mTOR inhibitor; induces autophagy |
| **Current indication** | FDA-approved for organ transplant rejection, LAM |
| **Evidence for SMA** | **Direct but CONTRADICTORY**: (1) In wild-type motor neurons, rapamycin elevated Smn and LC3-II levels. (2) In SMA mice, rapamycin DECREASED SMN/SMN-delta7 levels, caused failure in autophagosome-lysosome fusion, and REDUCED lifespan. (3) Autophagy INHIBITION (3-methyladenine) actually increased lifespan and motor neuron count in SMA pups. This suggests autophagy is pathologically overactivated in SMA, and further induction is harmful. |
| **BBB penetration** | **Yes** (lipophilic, crosses BBB) |
| **Clinical trial status** | Extensive trials for other indications. No SMA trials. |
| **Feasibility for SMA** | **Low -- potentially HARMFUL** -- Evidence suggests rapamycin worsens SMA phenotype. Autophagy induction appears contraindicated in SMA (opposite of ALS where it may help). |
| **Key references** | PMID: 24983518, PMID: 29259166, PMC10801191 |

### 4b. Trehalose

| Field | Detail |
|-------|--------|
| **Mechanism** | mTOR-independent autophagy inducer (activates TFEB); also a chemical chaperone |
| **Current indication** | GRAS food additive; investigational for neurodegeneration |
| **Evidence for SMA** | **Indirect**: Delayed disease onset, reduced motor neuron degeneration, improved lifespan in SOD1-G93A mice (ALS model). TFEB activation emerging as therapeutic target for motor neuron axon degeneration. However, given the autophagy overactivation concern in SMA (see rapamycin above), trehalose may face the same paradox. Tissue-dependent autophagy regulation in SMA complicates the picture. |
| **BBB penetration** | **Poor** -- Very hydrophilic disaccharide. Low oral bioavailability. Rapidly degraded by intestinal trehalase. Requires high doses or novel delivery. |
| **Clinical trial status** | Phase 2 for ALS (NCT05490381). No SMA trials. |
| **Feasibility for SMA** | **Low** -- BBB penetration is poor. Autophagy induction may be harmful in SMA. The tissue-specific autophagy dysregulation (muscle vs. motor neurons) makes this a risky candidate. |
| **Key references** | PMC10801191 (SMA autophagy review), PMID: 38259504 |

### Summary: Autophagy Modulators for SMA

**Critical insight**: Autophagy is dysregulated in SMA in a tissue-dependent manner, and evidence suggests it is OVERACTIVATED in motor neurons. Autophagy induction (rapamycin, trehalose) may be harmful. Autophagy INHIBITION showed survival benefit in SMA mice. **Recommendation**: Do NOT pursue autophagy inducers for SMA. Instead, investigate selective autophagy inhibitors or TFEB modulators with tissue specificity. This is a key finding that contradicts naive pathway extrapolation from ALS.

---

## 5. miRNA Therapeutics

### 5a. Anti-miR-133a-3p (for CORO1C Activation)

| Field | Detail |
|-------|--------|
| **Mechanism** | LNA (locked nucleic acid) antisense oligonucleotide targeting miR-133a-3p to de-repress CORO1C expression |
| **Current indication** | Preclinical concept (no drug candidate exists) |
| **Evidence for SMA** | **Platform-specific hypothesis**: miR-133a-3p suppresses CORO1C (coronin-1C), which is involved in actin dynamics. In the platform's CORO1C double-hit model, restoring CORO1C could improve actin-rod dissolution. miR-133a-3p is upregulated in ALS patient serum, suggesting neuromuscular relevance. LNA knockdown of miR-133a has been demonstrated in muscle cells (80 nM transfection). |
| **BBB penetration** | N/A -- ASOs for CNS require intrathecal delivery (like nusinersen) or conjugation. CNS-targeted miRNA therapeutics remain a major delivery challenge. |
| **Clinical trial status** | No clinical candidates. AI-driven ASO design platforms (eSkipFinder, ASOptimizer) advancing the field. Exosome-mediated delivery being explored for CNS miRNA therapeutics. |
| **Feasibility for SMA** | **Low (currently)** -- Compelling biology (CORO1C/actin connection), but: (1) No drug candidate, (2) CNS delivery unsolved for miRNA therapeutics, (3) CORO1C may be a "passenger" not "driver" (per platform learnings). Would require intrathecal delivery like nusinersen. |
| **Key references** | MDPI Genes 2025 (16/12/1468), PMC10277317, Platform internal: CORO1C double-hit model |

### Summary: miRNA Therapeutics for SMA

The anti-miR-133a-3p concept is scientifically interesting but practically distant. CNS delivery of miRNA therapeutics remains the bottleneck. **Recommendation**: Monitor exosome delivery and GalNAc-like conjugation advances. Do not prioritize as near-term repurposing candidate. The biology is better served by upstream ROCK/LIMK inhibition (fasudil, MDI-117740) which achieves similar actin-pathway effects with existing drug-like molecules.

---

## 6. Neuroprotective Agents

### 6a. Riluzole (Rilutek)

| Field | Detail |
|-------|--------|
| **Mechanism** | Glutamate release inhibitor; sodium channel blocker; neuroprotective |
| **Current indication** | FDA-approved for ALS (1995) |
| **Evidence for SMA** | **Direct**: Tested in SMA patients (ASIRI trial, ages 6-20, SMA types 2/3). Failed to demonstrate significant efficacy in clinical endpoints. Platform note: Only validated DiffDock hit. PK studied in young SMA patients (PMID: 21284699). |
| **BBB penetration** | **Yes** -- Excellent CNS penetration |
| **Clinical trial status** | ASIRI trial completed -- negative results for SMA. |
| **Feasibility for SMA** | **Low as monotherapy** -- Clinical trial failed. May retain modest neuroprotective value in combination, but evidence is weak. |
| **Key references** | PMID: 21284699, PMC11549153 |

### 6b. Edaravone (Radicava)

| Field | Detail |
|-------|--------|
| **Mechanism** | Free radical scavenger; antioxidant neuroprotectant |
| **Current indication** | FDA-approved for ALS (2017); approved for stroke in Japan |
| **Evidence for SMA** | **Indirect**: Listed as promising repurposed drug for SMA (PMC11549153). Reduces oxidative stress in motor neurons. No direct SMA preclinical or clinical data. Oxidative stress is documented in SMA but is likely secondary to SMN deficiency. |
| **BBB penetration** | **Yes** (oral formulation available -- Radicava ORS) |
| **Clinical trial status** | Approved for ALS. No SMA trials. |
| **Feasibility for SMA** | **Low** -- No SMA-specific data. Addresses secondary pathology (oxidative stress), not primary mechanism. Would only make sense as adjunct to SMN-restoring therapy. |
| **Key references** | PMC11549153 |

### 6c. AMX0035 (Relyvrio -- sodium phenylbutyrate + taurursodiol)

| Field | Detail |
|-------|--------|
| **Mechanism** | Dual mechanism: sodium phenylbutyrate (reduces ER stress, also weak HDAC inhibitor) + taurursodiol (mitochondrial protectant, inhibits apoptosis) |
| **Current indication** | Was FDA-approved for ALS (2022); **VOLUNTARILY WITHDRAWN** from US and Canadian markets after Phase 3 PHOENIX trial failed. |
| **Evidence for SMA** | **None direct**. Sodium phenylbutyrate has been studied for SMN2 upregulation (as an HDAC inhibitor) with modest effects. The taurursodiol component has no SMA data. |
| **BBB penetration** | **Yes** (oral, both components cross BBB) |
| **Clinical trial status** | WITHDRAWN from market. Phase 3 PHOENIX failed for ALS. |
| **Feasibility for SMA** | **Very Low** -- Market withdrawal, failed Phase 3 in its primary indication. Would not pass regulatory or investor scrutiny for SMA repurposing. |
| **Key references** | PMC10387989 |

### Summary: Neuroprotective Agents for SMA

None of the classical neuroprotectants (riluzole, edaravone, AMX0035) show strong SMA-specific potential. They address secondary pathology (glutamate excitotoxicity, oxidative stress, ER stress) rather than the primary SMN/actin defect. **Recommendation**: Deprioritize this axis. The neuroprotection angle is better served by p38 MAPK inhibition (MW150), which has direct SMA combination data.

---

## 7. Novel Combination Strategies

### 7a. MW150 (p38 MAPK inhibitor) + SMN-Inducing Drug

| Field | Detail |
|-------|--------|
| **Mechanism** | p38alpha MAPK selective inhibitor; BBB-penetrant; neuroprotective |
| **Current indication** | Investigational (clinical development for neurodegeneration) |
| **Evidence for SMA** | **DIRECT AND STRONG** (EMBO Mol Med, Oct 2025): SMN deficiency induces p38 MAPK activation. MW150 alone improves SMA phenotype. Combined with SMN-inducing drug: **synergistic** enhancement -- increased motor function, weight gain, survival. Mechanism: promotes motor neuron survival + enables synaptic rewiring of sensory-motor spinal circuits. Also shown effective in AD mouse models. |
| **BBB penetration** | **Yes** -- Specifically designed as BBB-permeable CNS compound |
| **Clinical trial status** | Under clinical development (CNS). No SMA-specific trial yet. |
| **Feasibility for SMA** | **HIGH** -- Direct SMA synergy data. BBB-penetrant. Oral. Addresses SMN-independent neuroprotection. Perfect combination partner for risdiplam or nusinersen. |
| **Key references** | PMID: 40236193, PMID: 40926051, EMBO Mol Med 2025 (DOI: 10.1038/s44321-025-00303-6) |

### 7b. MS023 (Type I PRMT Inhibitor) + Nusinersen

| Field | Detail |
|-------|--------|
| **Mechanism** | Selective Type I PRMT inhibitor; modulates HNRNPA1 methylation to promote SMN2 exon 7 inclusion |
| **Current indication** | Preclinical |
| **Evidence for SMA** | **DIRECT**: MS023 promotes SMN2 exon 7 inclusion by altering HNRNPA1 binding. In SMA mice, MS023 alone improves phenotype. Combined with nusinersen: **strong synergistic amplification**. Transcriptomics shows minimal off-targets; added benefit from reducing neuroinflammation. |
| **BBB penetration** | Not explicitly reported; likely requires optimization for CNS |
| **Clinical trial status** | Preclinical only. Published EMBO Mol Med 2023 (PMID: 37724723). |
| **Feasibility for SMA** | **Medium-High** -- Direct SMA data with synergy. Concerns: PRMT inhibitors are being developed for oncology (toxicity at high doses), and CNS penetration needs confirmation. |
| **Key references** | PMID: 37724723, PMC10630883 |

### 7c. Panobinostat + Nusinersen (or Risdiplam)

| Field | Detail |
|-------|--------|
| **Mechanism** | Pan-HDAC inhibitor (chromatin opening at SMN2 locus) + ASO splice-switching |
| **Evidence for SMA** | **DIRECT**: Panobinostat enhances SMN2 expression, increasing substrate for nusinersen-mediated splicing correction. Allows nusinersen to work at subtherapeutic doses (20 nM). Proof of concept in SMA cell models. |
| **Feasibility** | **High** -- Both drugs exist (one FDA-approved). Panobinostat is oral + BBB-penetrant. Could reduce nusinersen dosing frequency. |
| **Key references** | PMID: 32056234 (Poletti 2020) |

### 7d. Apitegromab + SMN Therapy (Standard of Care)

| Field | Detail |
|-------|--------|
| **Mechanism** | Anti-myostatin antibody (targets latent myostatin activation) + SMN restoration |
| **Evidence for SMA** | **DIRECT Phase 3**: SAPPHIRE trial met primary endpoint. HFMSE improvement of 1.8 points (P=0.019). 30.4% achieved >=3-point gain (vs 12.5% placebo). Published Lancet Neurology Aug 2025. FDA BLA accepted, PDUFA date Sept 2025. |
| **Feasibility** | **Very High** -- Phase 3 positive, FDA under review. First muscle-targeted SMA therapy. |
| **Key references** | PMID: 40818473, Lancet Neurology 2025 |

---

## Proposed Priority Combinations (Novel)

### Combo 1: Risdiplam + MW150 + Panobinostat
**Rationale**: Triple-axis attack
- Risdiplam: SMN2 splicing correction (oral, FDA-approved)
- Panobinostat: Enhances SMN2 transcription (oral, FDA-approved, BBB-penetrant)
- MW150: p38 MAPK neuroprotection + synaptic rewiring (oral, BBB-penetrant)

**Why this works**: Panobinostat opens chromatin at SMN2 locus (more transcript) -> Risdiplam corrects splicing (more full-length SMN) -> MW150 protects surviving motor neurons and enables circuit repair. All three are oral and BBB-penetrant.

**Feasibility**: HIGH -- All components are drug-like with human safety data (2/3 FDA-approved).

### Combo 2: Nusinersen + Panobinostat + Apitegromab
**Rationale**: Maximize SMN + muscle protection
- Nusinersen: ASO splice-switching (intrathecal)
- Panobinostat: Increases SMN2 transcript availability, allowing lower nusinersen doses
- Apitegromab: Muscle preservation (IV, Phase 3 positive)

**Why this works**: Panobinostat + nusinersen synergy is demonstrated. Apitegromab adds muscle-directed benefit independent of SMN pathway.

**Feasibility**: HIGH -- Panobinostat is the only component needing SMA trial.

### Combo 3: Risdiplam + Fasudil + MW150
**Rationale**: SMN restoration + actin pathway repair + neuroprotection
- Risdiplam: SMN protein restoration
- Fasudil: ROCK inhibition -> corrects actin dynamics, improves NMJ/muscle
- MW150: p38 MAPK inhibition -> motor neuron survival + circuit rewiring

**Why this works**: Addresses both upstream (SMN) and downstream (actin, neuroprotection) pathology. All three are oral and BBB-penetrant. Fasudil has direct SMA mouse survival data.

**Feasibility**: MEDIUM-HIGH -- Fasudil ALS Phase 2 provides safety data. MW150 under clinical development.

---

## Additional Pipeline Candidates to Monitor

| Drug | Mechanism | Stage | SMA Relevance |
|------|-----------|-------|---------------|
| **Apitegromab** | Anti-myostatin | Phase 3 / BLA review | SAPPHIRE positive; first muscle-directed therapy |
| **NMD670** | NMJ enhancer (CIV inhibitor) | Phase 2 (results Jan 2026) | Directly targets NMJ transmission defect |
| **Salanersen** | Next-gen ASO | Phase 1 (STELLAR-1) | Successor to nusinersen (Biogen) |
| **BIIB115** | Gene therapy (next-gen) | Phase 1 (results Nov 2026) | Post-Zolgensma gene therapy |
| **Taldefgrobep** | Anti-myostatin (dual mechanism) | Phase 3 | Muscle mass/strength |
| **OAV101 IT** | Intrathecal gene therapy | Regulatory filing 2025 | Zolgensma via spinal injection |

---

## Summary Ranking: New Candidates for Platform Addition

| Rank | Drug | Axis | Feasibility | Priority |
|------|------|------|-------------|----------|
| 1 | **MW150** | p38 MAPK / neuroprotection | High | **ADD IMMEDIATELY** |
| 2 | **Panobinostat** | HDAC / SMN2 enhancement | High | **ADD IMMEDIATELY** |
| 3 | **MS023** | PRMT / SMN2 splicing | Medium-High | **ADD -- preclinical** |
| 4 | **Apitegromab** | Myostatin / muscle | Very High | **ADD -- Phase 3** |
| 5 | **MDI-117740** | LIMK / actin dynamics | Medium-High | **ADD -- preclinical** |
| 6 | **Ripasudil** | ROCK / actin | Medium | Monitor |
| 7 | **Vorinostat** | HDAC / SMN2 | Medium | Lower priority vs panobinostat |
| 8 | **NMD670** | NMJ / transmission | Medium | Monitor Phase 2 results |

### Deprioritized

| Drug | Reason |
|------|--------|
| Rapamycin | Autophagy induction HARMFUL in SMA -- reduces lifespan in SMA mice |
| Trehalose | Same autophagy concern + poor BBB penetration |
| AMX0035 | Withdrawn from market, Phase 3 failed |
| Riluzole | SMA clinical trial (ASIRI) negative |
| Edaravone | No SMA data, addresses secondary pathology only |
| Netarsudil | No systemic formulation, no BBB penetration |
| Y-27632 | Research tool only, not a drug candidate |
| BMS-5 | Research tool, less selective than MDI-117740 |
| VPA (monotherapy) | Meta-analysis negative; only viable in combination |

---

## Key Insight: The Autophagy Paradox in SMA

A critical finding from this scan: **autophagy is pathologically overactivated in SMA motor neurons**, unlike in ALS where autophagy induction may be beneficial. Rapamycin (mTOR inhibitor) REDUCED lifespan in SMA mice, while autophagy INHIBITION (3-methyladenine) INCREASED lifespan and motor neuron count. This means:

- Do NOT naively extrapolate ALS autophagy strategies to SMA
- Trehalose, rapamycin, and other autophagy inducers are likely CONTRAINDICATED
- Selective autophagy inhibition or TFEB tissue-specific modulation may warrant investigation
- SMA autophagy is tissue-dependent (muscle vs. motor neuron profiles differ)

This contradicts initial assumptions and should be prominently noted in the platform.

---

## Sources

- [ROCK inhibitors in Alzheimer's disease (Frontiers 2025)](https://www.frontiersin.org/journals/aging/articles/10.3389/fragi.2025.1547883/full)
- [Fasudil inhibits alpha-synuclein aggregation (2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12014416/)
- [Fasudil improves survival in SMA mice](https://pubmed.ncbi.nlm.nih.gov/22397316/)
- [ROCK inhibition as SMA therapy](https://pmc.ncbi.nlm.nih.gov/articles/PMC4148024/)
- [MDI-114215 LIMK inhibitor for Fragile X](https://pubmed.ncbi.nlm.nih.gov/39711116/)
- [Tetrahydropyrazolopyridinones as LIMK inhibitors (J Med Chem 2025)](https://pubs.acs.org/doi/10.1021/acs.jmedchem.5c00974)
- [Panobinostat BBB penetration](https://pmc.ncbi.nlm.nih.gov/articles/PMC8896403/)
- [Panobinostat + nusinersen combination (Poletti 2020)](https://onlinelibrary.wiley.com/doi/10.1111/jnc.14974)
- [Vorinostat for brain disorders](https://link.springer.com/article/10.1007/s12017-021-08660-4)
- [VPA meta-analysis for SMA](https://pubmed.ncbi.nlm.nih.gov/30796634/)
- [Autophagy in SMA (Frontiers 2024)](https://www.frontiersin.org/journals/cellular-neuroscience/articles/10.3389/fncel.2023.1307636/full)
- [Autophagy inhibition extends SMA lifespan](https://pubmed.ncbi.nlm.nih.gov/29259166/)
- [p38 MAPK inhibition as SMA combinatorial therapy (EMBO Mol Med 2025)](https://www.embopress.org/doi/full/10.1038/s44321-025-00303-6)
- [PRMT inhibitor synergizes with nusinersen (EMBO Mol Med 2023)](https://pubmed.ncbi.nlm.nih.gov/37724723/)
- [SAPPHIRE Phase 3 results (Lancet Neurology 2025)](https://pubmed.ncbi.nlm.nih.gov/40818473/)
- [SMA drug repurposing review (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11549153/)
- [Riluzole PK in SMA patients](https://pubmed.ncbi.nlm.nih.gov/21284699/)
- [Cure SMA Drug Pipeline](https://www.curesma.org/sma-drug-pipeline/)
- [FDA kinase inhibitors for neurological disorders (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12288644/)
- [Apitegromab SAPPHIRE (Lancet Neurology)](https://pubmed.ncbi.nlm.nih.gov/40818473/)
- [SMA skeletal muscle autophagy (2025)](https://pubmed.ncbi.nlm.nih.gov/39901351/)
