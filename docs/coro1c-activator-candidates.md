# CORO1C Activator Candidates: Compounds to Upregulate CORO1C Expression

*Generated 2026-03-21. Based on SMA Research Platform database (25,054 claims, 515 hypotheses, 142 drug mechanisms), PubMed literature search, and mechanistic inference from the CORO1C Double-Hit Model.*

---

## Executive Summary

**Goal**: Identify compounds that could upregulate CORO1C expression in motor neurons, providing SMN-independent therapeutic benefit in SMA.

**Problem**: No compound has been directly shown to increase CORO1C expression in any published study. The CORO1C promoter, transcriptional regulators, and epigenetic landscape are essentially uncharacterized. This means all candidates below are **inferred from mechanism** rather than demonstrated for CORO1C specifically.

**Key finding from our platform**: A hypothesis (confidence 0.75) already exists in our database linking HDAC inhibitors (LBH589/panobinostat) to potential CORO1C upregulation. The rationale is that HDAC inhibition could de-repress CORO1C transcription while simultaneously boosting SMN levels -- a dual-benefit mechanism.

**Strategy**: We identify candidates through five convergent approaches:
1. Epigenetic de-repression (HDAC inhibitors, BET modulators)
2. Upstream pathway activation (RhoA/ROCK inhibitors, Wnt)
3. miR-133a-3p antagonism (de-repress CORO1C post-transcriptionally)
4. PLS3 co-regulation (CHD4/NuRD pathway activation)
5. Indirect functional rescue (endocytosis/F-actin enhancers)

---

## 1. HDAC Inhibitors (Epigenetic De-repression)

### Rationale

HDAC inhibitors open chromatin broadly, increasing transcription of many genes including SMN2. If the CORO1C promoter contains HDAC-sensitive regulatory elements, HDAC inhibition could increase CORO1C expression. Our platform hypothesis (0.75 confidence) explicitly links this mechanism.

Additionally: miR-133a-3p directly represses CORO1C (see Section 3). HDAC inhibition can alter miRNA expression profiles, potentially reducing miR-133a-3p levels and de-repressing CORO1C post-transcriptionally.

### Candidates

| Compound | Status in SMA | CORO1C Rationale | Priority |
|----------|--------------|------------------|----------|
| **Panobinostat (LBH589)** | Preclinical SMA. Produces ~10-fold SMN increase. Combined with ASO shows enhanced SMN2 splicing (PMID editorial: Poletti & Fischbeck 2020). | Most potent pan-HDAC inhibitor. Strongest candidate for broad transcriptional de-repression including CORO1C. Platform hypothesis (0.75). | **HIGH** |
| **Valproic Acid (VPA)** | In our drug_outcomes: "success" (preclinical). HDAC inhibitor + SMN enhancer. | In our database. Known to increase SMN in cortical neurons. BUT: also blocks voltage-gated Ca2+ channels and reduces growth cone size in SMA motor neurons (PMID:19733665). CORO1C-PLS3 binding is calcium-dependent, so Ca2+ channel blockade could counteract CORO1C function. | **MEDIUM** (calcium concern) |
| **Vorinostat (SAHA)** | Approved for CTCL. Not tested in SMA specifically. | Pan-HDAC inhibitor. Good BBB penetration. No SMA-specific data but well-characterized pharmacology. | **MEDIUM** |
| **Trichostatin A (TSA)** | Research tool only (not clinically viable). | Potent HDAC inhibitor, commonly used as positive control for epigenetic de-repression studies. Useful for in vitro proof-of-concept that HDAC inhibition increases CORO1C. | **HIGH** (for screening) |
| **Sodium butyrate / Phenylbutyrate** | Tested in SMA clinical trials (limited efficacy). | Weak HDAC inhibitor. Less likely to produce meaningful CORO1C upregulation. | **LOW** |
| **Entinostat (MS-275)** | Not tested in SMA. Class I HDAC-selective. | Selective for HDAC1/3. If CORO1C is regulated by class I HDACs specifically, this could be more targeted with fewer side effects. | **MEDIUM** |

### Key Experiment

Treat SMA iPSC-derived motor neurons with panobinostat (10-100 nM) and TSA (100-500 nM) for 24-72h. Measure CORO1C mRNA (qRT-PCR) and protein (Western blot). Compare to SMN2 upregulation as positive control.

### VPA Caveat (Critical)

Our database contains a high-confidence claim (0.92): "Valproic acid inhibits voltage-gated calcium channels in motor neurons." Since CORO1C-PLS3 binding is calcium-dependent (PMID:27499521), VPA could paradoxically impair CORO1C function even if it increases CORO1C expression. A separate claim (0.15) notes: "Valproic acid inhibits HDAC activity to reduce RhoA expression" -- which is actually favorable for actin dynamics (see Section 2). Net effect is unpredictable without experimental testing.

---

## 2. RhoA/ROCK Pathway Inhibitors (Upstream Actin Regulation)

### Rationale

The RhoA/ROCK pathway is hyperactivated in SMA (confidence 0.90). ROCK phosphorylates LIMK, which phosphorylates cofilin, causing actin depolymerization. ROCK inhibition should:
- Reduce actin stress fibers and increase G-actin availability
- Shift actin dynamics toward the polymerized state that CORO1C and PLS3 operate on
- Potentially upregulate compensatory actin-binding proteins including CORO1C

Our database claims (high confidence):
- "LWDH-WE inhibits activation of the RhoA/ROCK2/p-LIMK/p-cofilin pathway induced by SMN deficiency" (0.90)
- "Phosphorylated myosin light chain expression is increased in synaptic afferents on motoneurons in SMNΔ7 mice, implicating RhoA/ROCK pathway activation" (0.90)
- "RhoA/ROCK pathway is involved in mediating DNA damage-dependent cell death in SMA" (0.80)
- "Profilin2 regulates actin rod assembly in neuronal cells" via RhoA/ROCK (PMID:33986363)

Key review: "ROCK inhibition as a therapy for spinal muscular atrophy" (PMID:25221469) -- Coque et al. 2014. Fasudil improves survival in SMA mice.

### Candidates

| Compound | Status in SMA | CORO1C Rationale | Priority |
|----------|--------------|------------------|----------|
| **Fasudil** | Preclinical SMA: improves survival and skeletal muscle in SMA mouse model (PMID:22436459, Bowerman et al. 2012). Already approved in Japan/China for cerebral vasospasm. | ROCK inhibitor. Directly opposes RhoA/ROCK pathway hyperactivation in SMA. Increases G-actin/F-actin ratio. May functionally synergize with CORO1C by improving the actin substrate CORO1C acts on. Does NOT directly upregulate CORO1C but creates conditions where existing CORO1C is more effective. | **HIGH** |
| **Y-27632** | Research tool ROCK inhibitor. | More selective than fasudil. Demonstrated effects on astrocyte morphology and actin dynamics (PMID:25221469). Useful for in vitro studies. | **HIGH** (for screening) |
| **LWDH-WE (Liu Wei Di Huang water extract)** | Preclinical SMA. 10 high-confidence claims (0.90-0.93) in our database. Increases SMN protein in brain, spinal cord, and muscle. Improves muscle strength. Increases cell viability. Inhibits RhoA/ROCK2/p-LIMK/p-cofilin. | Traditional Chinese medicine formula. Dual mechanism: increases SMN AND inhibits RhoA/ROCK. Unique among candidates. Inhibits the exact pathway (RhoA/ROCK2/p-LIMK/p-cofilin) that causes actin disassembly in SMA. | **HIGH** (mechanistically compelling but complex mixture) |
| **Ripasudil** | Approved for glaucoma (topical). Not tested in SMA. | ROCK1/2 inhibitor. Could be repurposed if systemic formulation developed. | **LOW** |

### LWDH-WE Detail (from our database)

LWDH-WE is the strongest non-SMN-restoring compound in our database by claim count and confidence:
- Up-regulates SMN protein in spinal cord (0.93), brain (0.93), gastrocnemius muscle (0.93)
- Increases cell viability of SMN-deficient NSC34 cells (0.93)
- Improves muscle strength in SMAΔ7 mice (0.93)
- Increases body weight in SMAΔ7 mice (0.92)
- Prevents SMN deficiency-induced inhibition of neurite outgrowth (0.92)
- Increases mitochondrial membrane potential (0.92)
- Inhibits RhoA/ROCK2/p-LIMK/p-cofilin pathway (0.90)
- Attenuates Bcl-2 downregulation (0.91)

**Limitation**: LWDH-WE is a multi-component herbal extract. The active compound(s) responsible for ROCK inhibition are not isolated. Not directly druggable without fractionation and lead identification.

---

## 3. miR-133a-3p Antagonism (Post-transcriptional De-repression)

### Rationale

Our platform hypothesis (0.75) states: "miR-133a-3p directly represses CORO1C, and HDAC inhibition could de-repress CORO1C transcription." If miR-133a-3p is a direct negative regulator of CORO1C mRNA, then:
- Anti-miR-133a-3p (antagomir) would directly increase CORO1C protein
- Compounds that reduce miR-133a-3p expression would indirectly increase CORO1C

### Database evidence on miR-133a

- "miR-206, miR-133a, miR-133b, and miR-1 are dysregulated in SMA mouse muscle during disease progression" (0.15)
- "NMES upregulates muscle-specific miR-1, miR-133a/b, and miR-206 in myogenic precursor cells" (0.15)
- miR-133a is classified as a myomiR (muscle-specific microRNA)

### Candidates

| Compound | Mechanism | CORO1C Rationale | Priority |
|----------|-----------|------------------|----------|
| **Anti-miR-133a-3p ASO** | Antisense oligonucleotide targeting miR-133a-3p | Most direct approach. Would specifically de-repress CORO1C (and other miR-133a targets). Requires validation that miR-133a-3p actually binds CORO1C 3'UTR. | **HIGH** (if target validated) |
| **miR-133a sponge** | Competitive endogenous RNA containing miR-133a binding sites | Gene therapy approach (AAV-delivered). Sequesters miR-133a away from CORO1C mRNA. | **MEDIUM** |

### Critical gap

The miR-133a-3p --> CORO1C repression link is stated in our hypothesis but needs experimental validation:
1. Check TargetScan/miRDB for predicted miR-133a-3p binding sites in CORO1C 3'UTR
2. Luciferase reporter assay with CORO1C 3'UTR +/- miR-133a-3p mimic
3. Anti-miR-133a-3p treatment in motor neurons, measure CORO1C protein

**Note**: miR-133a is a myomiR primarily expressed in muscle. Its expression in motor neurons is less clear. If miR-133a-3p is not expressed in motor neurons, this approach is irrelevant for CNS-targeted therapy but could be relevant for NMJ/muscle-side effects.

---

## 4. CHD4/NuRD Pathway Activation (PLS3 Co-regulation)

### Rationale

Strathmann et al. 2023 (PMID:36812914, Wirth lab) demonstrated that CHD4 (Chromodomain Helicase DNA Binding Protein 4) is an epigenetic transcriptional activator of PLS3. CHD4 is the catalytic subunit of the NuRD (Nucleosome Remodeling and Deacetylase) complex.

Since CORO1C and PLS3 are:
- Direct binding partners (calcium-dependent, PMID:27499521)
- Co-functional in endocytosis rescue
- Both protective SMA modifiers
- Both F-actin binding proteins

It is plausible that CHD4/NuRD also regulates CORO1C transcription, or that compounds activating PLS3 co-activate CORO1C through shared regulatory elements.

### Candidates

| Compound | Mechanism | CORO1C Rationale | Priority |
|----------|-----------|------------------|----------|
| **CHD4 overexpression** (gene therapy) | Increase CHD4/NuRD complex activity | Proven to upregulate PLS3 (PMID:36812914). Test whether it also upregulates CORO1C. | **HIGH** (for proof-of-concept) |
| **DXZ4 macrosatellite expansion** | Epigenetic regulation via X-chromosome architecture | PLS3 expression correlates with DXZ4 monomer copy number. Only relevant if CORO1C is also X-linked (it is NOT -- CORO1C is on chromosome 12). | **NOT APPLICABLE** |

### Important distinction

PLS3 is X-linked (Xq23) and regulated by DXZ4/CHD4 in a sex-specific manner. CORO1C is on chromosome 12q24.11 -- completely different chromosomal context. Therefore:
- The DXZ4 mechanism does NOT apply to CORO1C
- CHD4/NuRD may still regulate CORO1C if it binds the CORO1C promoter (this needs ChIP-seq validation)
- The Strathmann paper provides methodology (ChIP, dual-luciferase assays) that should be applied to the CORO1C promoter

---

## 5. Indirect Functional Rescue (Endocytosis/F-Actin Enhancers)

These compounds do not upregulate CORO1C expression but functionally compensate for CORO1C deficiency by restoring the downstream pathway (F-actin dynamics and endocytosis).

### Candidates

| Compound | Mechanism | SMA Evidence | Priority |
|----------|-----------|-------------|----------|
| **NCALD-ASO** | Antisense knockdown of Neurocalcin Delta | NCALD reduction restores endocytosis across species (PMID:28132687). Combined NCALD-ASO + SMN-ASO shows additive benefit at 3 months in severe SMA mice. 10 claims in our DB. | **HIGH** |
| **CHP1-ASO** | Antisense knockdown of Calcineurin-like EF-hand Protein 1 | CHP1 reduction restores calcineurin activity and endocytosis (PMID:29961886). | **MEDIUM** |
| **AAV9-PLS3** | Gene therapy delivering PLS3 | Extends survival in pharmacologically induced SMA model. "AAV9-PLS3 extends survival in a pharmacologically induced SMA model" (DB claim 0.15). | **HIGH** |
| **Bis-T-23** | Direct F-actin stabilizer (formin agonist) | Stabilizes existing F-actin filaments. Would bypass both CORO1C and PLS3 deficiency. Not tested in SMA. | **MEDIUM** |
| **4-AP (4-aminopyridine)** | K+ channel blocker, increases neuronal activity | Restores synaptic connectivity (0.90-0.92). Increases vesicle cycling demand. Our platform identified 4-AP-->CORO1C synergy score +0.251 -- the strongest drug-target synergy discovered. | **HIGH** (as combination partner) |
| **GV-58** | Calcium channel gating modifier | "GV-58 is a calcium channel gating modifier that acts as a drug target for SMA treatment" (DB claim 0.88). Could improve calcium-dependent CORO1C-PLS3 binding. | **MEDIUM** |

---

## 6. Novel Screening Approaches

### 6.1 CORO1C Promoter Reporter Screen

**Design**: Clone the CORO1C promoter (2-5 kb upstream of TSS) into a luciferase reporter. Transfect into motor neuron-like cells (NSC34 or iPSC-MNs). Screen compound libraries.

**Libraries to screen**:
- Epigenetics Compound Library (Selleckchem, ~180 compounds)
- FDA-approved drug library (repurposing)
- Natural products library (given LWDH-WE activity)
- Our own drug_outcomes compounds (16 drugs in our database)

### 6.2 ChEMBL/ZINC Database Mining

**CORO1C does not appear as a target in ChEMBL** (no known ligands or modulators). This confirms that CORO1C is an undrugged target.

**Alternative ChEMBL strategy**:
- Search for HDAC inhibitors with known CNS penetrance
- Search for ROCK inhibitors in clinical use
- Search for miR-133a-3p modulators
- Cross-reference with our drug_outcomes to find compounds already tested in SMA

### 6.3 Connectivity Map (CMap) Approach

Query the Broad Institute Connectivity Map with the gene signature: CORO1C_UP + PLS3_UP + NCALD_DOWN. Identify compounds that produce this expression pattern in L1000 data. This is the most unbiased approach to finding CORO1C activators.

### 6.4 CRISPR Activation Screen

**Design**: dCas9-VPR + sgRNA library targeting the CORO1C locus. Screen for guides that maximally activate CORO1C transcription, identifying regulatory elements. Then identify compounds that mimic the effect of activating those elements.

---

## 7. Combination Strategies (Highest Therapeutic Potential)

Based on the double-hit model, the most promising approach is combining SMN restoration with CORO1C pathway activation.

| Combination | Rationale | Evidence Level |
|-------------|-----------|----------------|
| **Risdiplam + Panobinostat** | Risdiplam fixes SMN2 splicing (fixes Hit #1 for all genes). Panobinostat could upregulate CORO1C transcription (amplifies Hit #2 compensation). Dual SMN + CORO1C benefit. | Hypothesis (no data) |
| **Nusinersen + NCALD-ASO** | Nusinersen restores SMN and partially fixes splicing. NCALD-ASO restores endocytosis directly. | Preclinical data: additive benefit at 3 months in severe SMA mice |
| **Risdiplam + Fasudil** | Risdiplam restores SMN. Fasudil inhibits RhoA/ROCK, improving actin dynamics and creating a permissive environment for CORO1C/PLS3 function. | Fasudil alone: improved survival in SMA mice. Combination: untested. |
| **Risdiplam + 4-AP** | Risdiplam restores SMN. 4-AP increases synaptic activity. CORO1C synergy score +0.251. | Our platform prediction. Both individually beneficial. Combination untested. |
| **Risdiplam + LWDH-WE** | Risdiplam restores SMN. LWDH-WE provides SMN-independent RhoA/ROCK inhibition. | LWDH-WE: 10 high-confidence claims. Combination: untested. Active compounds unknown. |

---

## 8. Priority Ranking Summary

### Tier 1: Test Immediately (in vitro, using iPSC-derived motor neurons)

1. **Panobinostat (LBH589)** -- HDAC inhibitor, ~10x SMN increase, potential CORO1C upregulation
2. **Trichostatin A (TSA)** -- HDAC inhibitor positive control for screening
3. **Y-27632** -- ROCK inhibitor, actin dynamics improvement
4. **Anti-miR-133a-3p** -- Direct CORO1C de-repression (after target validation)

**Experiment**: Treat SMA iPSC-MNs with each compound. Measure CORO1C mRNA + protein, PLS3 mRNA + protein, F-actin levels, and endocytosis (FM1-43 uptake). 48-72h treatment. Include risdiplam as SMN-restoration control.

### Tier 2: Validate Mechanism

5. **LWDH-WE** -- RhoA/ROCK inhibitor + SMN enhancer (needs fractionation)
6. **Fasudil** -- ROCK inhibitor with SMA preclinical data
7. **CHD4 overexpression** -- Test if PLS3 epigenetic regulator also controls CORO1C
8. **CMap query** -- Unbiased compound discovery

### Tier 3: Combination Testing

9. **Panobinostat + Risdiplam** -- Dual SMN + epigenetic CORO1C benefit
10. **4-AP + Fasudil** -- Synaptic activity + actin dynamics
11. **NCALD-ASO + SMN-ASO** -- Already has preclinical data; add CORO1C measurement

---

## 9. What Our Database Contains vs. What Is Missing

### In our database
- 9 CORO1C claims (all from PMID:27499521)
- 1 HDAC inhibitor in drug_outcomes (VPA, preclinical success)
- 10 LWDH-WE claims (0.90-0.93 confidence)
- 10 NCALD claims (including combination with SMN-ASO)
- 10 RhoA/ROCK claims (0.80-0.93 confidence)
- 1 hypothesis linking HDAC inhibitors to CORO1C (0.75 confidence)
- CORO1C target entry with 2 associated hypotheses
- 4 actin-related targets (CORO1C, PLS3, CTNNA1, ZPR1)
- 16 drugs total, 142 distinct mechanisms

### NOT in our database (gaps to fill)
- No panobinostat/LBH589 in drug_outcomes (only referenced in hypothesis)
- No ROCK inhibitors (fasudil, Y-27632) in drug_outcomes
- No miR-133a-3p validation data
- No CORO1C promoter/epigenetic regulation data
- No ChEMBL compound-CORO1C links
- No CMap signatures for CORO1C upregulation
- No CORO1C protein-level measurements in SMA models
- No identified transcription factors for CORO1C in motor neurons

### Key PubMed gaps
- "increase CORO1C expression compound" -- 1 result (CDC42/afatinib in cancer, not SMA-relevant)
- "coronin 1C upregulation drug" -- 1 result (McCabe review, no specific drug)
- "CORO1C promoter CpG methylation" -- 0 results
- "coronin 1C transcription regulation promoter" -- 0 results
- "risdiplam CORO1C" -- 0 results
- "nusinersen actin cytoskeleton expression" -- 0 results
- "valproic acid coronin expression" -- 0 results

This confirms that **CORO1C transcriptional regulation is essentially unstudied**. The field is wide open.

---

## 10. Recommended Next Steps

### Immediate (this week)
1. Run CMap query: CORO1C_UP signature against L1000 database
2. Check TargetScan for miR-133a-3p binding sites in CORO1C 3'UTR
3. Add panobinostat and fasudil to our drug_outcomes database
4. Design CORO1C promoter-luciferase construct

### Short-term (1-2 months)
5. In vitro screen: panobinostat, TSA, Y-27632, VPA on SMA iPSC-MNs
6. Measure CORO1C protein levels (Western blot) in SMA vs. control iPSC-MNs (Experiment 2 from double-hit model)
7. CHD4 overexpression in motor neurons: does it upregulate CORO1C?

### Medium-term (3-6 months)
8. CORO1C promoter reporter screen (epigenetics compound library)
9. ATAC-seq of CORO1C locus in SMA vs. control motor neurons
10. Test top compound(s) in SMA mouse model for CORO1C expression

---

## Key References

### CORO1C in SMA
- PMID:27499521 -- Hosseinibarkooie et al. 2016. "PLS3 and CORO1C Unravel Impaired Endocytosis in SMA." *Am J Hum Genet.*
- PMID:28684086 -- McCabe 2017. "Modifier genes: Moving from pathogenesis to therapy." *Mol Genet Metab.*
- PMID:36071912 -- Zhuri et al. 2022. "Investigation on the Effects of Modifying Genes on the SMA Phenotype." *Glob Med Genet.*

### PLS3 Epigenetic Regulation (CHD4/DXZ4)
- PMID:36812914 -- Strathmann et al. 2023. "Epigenetic regulation of PLS3 by DXZ4 and CHD4." *Am J Hum Genet.*

### HDAC Inhibitors in SMA
- Poletti & Fischbeck 2020. "Combinatorial treatment for SMA: LBH589 and splice-switch ASO." *J Neurochem.* (editorial)
- PMID:19733665 -- Rak et al. 2009. "Valproic acid blocks excitability in SMA type I mouse motor neurons." *Neurobiol Dis.*

### ROCK Inhibitors in SMA
- PMID:25221469 -- Coque et al. 2014. "ROCK inhibition as a therapy for SMA." *Front Neurosci.*
- PMID:22436459 -- Bowerman et al. 2012. "Fasudil improves survival in SMA mouse model." *BMC Med.*
- PMID:33986363 -- Walter et al. 2021. "Profilin2 regulates actin rod assembly via RhoA/ROCK in SMA." *Sci Rep.*
- PMID:21705428 -- Nolle et al. 2011. "SMN is linked to the Rho-kinase pathway via profilin." *Hum Mol Genet.*

### Endocytosis Modifiers in SMA
- PMID:28132687 -- Riessland et al. 2017. "NCALD Suppression Protects against SMA by Restoring Endocytosis." *Am J Hum Genet.*
- PMID:29961886 -- CHP1 reduction ameliorates SMA via calcineurin and endocytosis.

### Actin Dynamics in SMA
- PMID:39305126 -- "The SMA gene product regulates actin dynamics."
- PMID:39666039 -- "Cytoskeleton dysfunction of motor neuron in SMA." Review.

---

*This document should be updated after in vitro screening results are available. The most impactful experiment is treating SMA iPSC-derived motor neurons with panobinostat and measuring CORO1C expression -- if positive, this immediately validates a repurposable clinical compound for CORO1C upregulation.*
