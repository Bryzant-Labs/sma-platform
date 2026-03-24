# SMA Drug Discovery Competitive Landscape

**Date**: 2026-03-22
**Purpose**: Understand who else is working on computational SMA drug discovery, where the pipeline stands, and how our platform differentiates.

---

## 1. Computational SMA Drug Discovery: Who Else Is Doing It?

### Academic Groups

| Group / Institution | Focus | Key Publications |
|---------------------|-------|-----------------|
| **Monash University** (Rai et al.) | Comprehensive computational review of SMA drug discovery (molecular docking, QSAR, pharmacophore modeling) | [Drug Discovery of SMA from the Computational Perspective (2021)](https://www.mdpi.com/1422-0067/22/16/8962) |
| **Oxford / Talbot Lab** | AI-guided analysis of disease-relevant molecules in SMA using machine learning on transcriptomic data | [From data to discovery: AI-guided analysis (2024, Human Molecular Genetics)](https://doi.org/10.1093/hmg/ddae076) |
| **Bowerman Lab** (formerly Ottawa, now Keele/Aix-Marseille) | ROCK inhibition therapy for SMA; fasudil preclinical work | [Fasudil improves survival in SMA mice (2012)](https://pubmed.ncbi.nlm.nih.gov/22397316/); [ROCK inhibition review (2014)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4148024/) |
| **Li / Zhang groups (China)** | Cytoskeleton dysfunction in SMA motor neurons; actin dynamics and SMN | [Cytoskeleton dysfunction of motor neuron in SMA (2024, J Neurol)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11638312/) |
| **Bhatt Lab (Columbia)** | SMN protein regulates actin dynamics directly | [The SMA gene product regulates actin dynamics (2024)](https://pubmed.ncbi.nlm.nih.gov/39305126/) |

### Companies

| Company | Approach | SMA Relevance |
|---------|----------|---------------|
| **Cure SMA (nonprofit)** | Funds basic research and drug discovery programs | Pipeline tracker, not computational platform |
| **Scholar Rock** | Anti-myostatin antibody (apitegromab) -- biology-driven, not computational | Direct SMA pipeline (Phase 3 complete) |
| **NMD Pharma** | ClC-1 inhibitor (NMD670) -- pharmacology-driven | Phase 2 SMA trial |
| **Biogen / Ionis** | ASO chemistry (salanersen) -- medicinal chemistry | Phase 3 initiating |

### Key Finding: NO Integrated Computational SMA Platform Exists

**No company or academic group has built a dedicated computational drug discovery platform for SMA** that integrates:
- Evidence knowledge graph (claims, sources, targets)
- Virtual screening (DiffDock, GenMol)
- Protein structure prediction (AlphaFold2, ESM2)
- Protein binder design (RFdiffusion)
- Hypothesis generation and scoring
- Cross-disease convergence analysis (SMA-ALS)

**This is our unique position.** The closest analogs are general-purpose rare disease platforms (see Section 3).

---

## 2. SMA Drug Pipeline (2025-2026)

### Approved Therapies (Standard of Care)

| Drug | Company | Mechanism | Route | Approved |
|------|---------|-----------|-------|----------|
| **Nusinersen (Spinraza)** | Biogen/Ionis | ASO, SMN2 splicing | Intrathecal (3x/year) | 2016 |
| **Onasemnogene (Zolgensma)** | Novartis | Gene therapy, SMN1 replacement | IV (one-time) | 2019 |
| **Risdiplam (Evrysdi)** | Roche | Small molecule, SMN2 splicing | Oral (daily) | 2020 |

### Late-Stage Pipeline (Phase 2-3)

#### Apitegromab (Scholar Rock) -- MOST ADVANCED NON-SMN THERAPY
- **Mechanism**: Anti-myostatin antibody (targets latent myostatin via proMyostatin)
- **Phase 3 SAPPHIRE results** (published in Lancet Neurology, Aug 2025):
  - Primary endpoint MET: +1.8 points HFMSE vs placebo (p=0.019)
  - 30.4% of patients achieved clinically meaningful >=3-point improvement vs 12.5% placebo
  - 48-month data: +5.3 HFMSE points with nusinersen combination
  - Used as ADD-ON to existing SMN therapy (nusinersen or risdiplam)
- **Regulatory**: BLA under FDA review; PDUFA date September 22, 2025
- **Commercial**: US launch expected 2025, EU 2026
- **Significance**: First approved muscle-targeting SMA therapy (SMN-independent mechanism)

#### Salanersen / BIIB115 (Biogen/Ionis) -- NEXT-GEN ASO
- **Mechanism**: ASO with novel backbone chemistry, corrects SMN2 splicing
- **Advantage**: Once-yearly intrathecal dosing (vs 3x/year for nusinersen)
- **Phase 1b results**: Motor milestones achieved in gene-therapy-pretreated children
- **Phase 3 program** (3 studies):
  - STELLAR-1: Screening initiated (Q1 2026)
  - SOLAR: Planned Q2 2026
  - STELLAR-2: Planned Q3 2026
- **Significance**: Could replace nusinersen with better dosing schedule

#### NMD670 (NMD Pharma) -- NEUROMUSCULAR JUNCTION ENHANCER
- **Mechanism**: First-in-class ClC-1 chloride channel inhibitor; increases muscle excitability
- **Phase 2** (SYNAPSE-SMA, NCT05794139):
  - Randomized, double-blind, placebo-controlled crossover
  - 50 ambulatory SMA Type 3 adults (18-75 years)
  - Primary endpoint: 6-minute walk test improvement
  - Trial expected to conclude January 2026
- **Significance**: Purely symptomatic muscle therapy; targets NMJ transmission, not SMN

### ROCK Inhibitor Trials for SMA

**No active clinical trials of ROCK inhibitors specifically for SMA as of March 2026.**

Preclinical evidence is strong:
- Fasudil dramatically improved lifespan in Smn2B/- mice (Bowerman et al., 2012)
- Y-27632 significantly increased SMA mouse lifespan
- Mechanism is SMN-independent: works through cytoskeletal rescue and muscle development
- Fasudil is in clinical trials for ALS (separate indication), which may pave the way for SMA

**This is a gap we identified early. Our fasudil-for-SMA hypothesis and DiffDock validation of fasudil binding to ROCK2 is ahead of the field.**

### Pipeline Summary Diagram

```
APPROVED (3):     Nusinersen --- Zolgensma --- Risdiplam
                      |
PHASE 3:         Salanersen (Biogen) -- next-gen ASO, once/year
                 Apitegromab (Scholar Rock) -- anti-myostatin, BLA filed
                      |
PHASE 2:         NMD670 (NMD Pharma) -- ClC-1 inhibitor, NMJ
                      |
PRECLINICAL:     Fasudil/ROCK inhibitors (academic only)
                 Anti-miR-133a-3p concepts (OUR WORK)
                 Multi-kinase approaches (OUR WORK)
                 CORO1C activators (OUR WORK)
```

---

## 3. Computational Biology Platforms for Rare Diseases

### Major Competitors (General Rare Disease, Not SMA-Specific)

| Platform | Focus | Technology | Strengths | Weaknesses |
|----------|-------|-----------|-----------|------------|
| **Healx** | Rare disease drug repurposing | Biomedical knowledge graph, ML | 20+ programs, Sanofi partnership, fast (24mo to preclinical for Fragile X) | Repurposing only -- no de novo design, no structural biology |
| **BenevolentAI** | Knowledge graph drug discovery | NLP on literature, graph ML, expert-augmented | COVID baricitinib success, strong publication record | General-purpose, not disease-specialized, commercially struggling |
| **Insilico Medicine** | End-to-end AI drug discovery | PandaOmics (targets), Chemistry42 (molecules), InClinico (trial prediction) | First AI-designed drug in Phase 2 (INS018_055 for fibrosis), comprehensive suite | Expensive, steep learning curve, focused on aging/fibrosis not neuro |
| **Recursion** | Phenotypic drug discovery | Massive cell imaging dataset, Recursion OS | Scale (millions of images), strong rare disease programs | Black-box phenotypic approach, less mechanistic insight |
| **Valo Health** | Human data integration | Opal platform, EHR + genomics + ML | Real-world data integration | Early-stage pipeline, less academic validation |

### How Our SMA Platform Compares

| Feature | Healx | BenevolentAI | Insilico | Recursion | **Our Platform** |
|---------|-------|-------------|----------|-----------|-----------------|
| Disease-specific knowledge graph | No | No | No | No | **YES (14k+ claims, 63 targets, 6.7k sources)** |
| Evidence-based claim scoring | No | Partial | No | No | **YES (calibrated, grade A: 89.8%)** |
| Hypothesis generation + validation | No | Manual | Partial | No | **YES (1,472 hypotheses, scored)** |
| Virtual screening (DiffDock) | No | No | Chemistry42 | No | **YES (378+ dockings, validated)** |
| De novo molecule generation (GenMol) | No | No | Chemistry42 | No | **YES (ROCK2, MAPK14 campaigns)** |
| Protein structure (AlphaFold2) | No | No | No | No | **YES (63 targets predicted)** |
| Protein binder design (RFdiffusion) | No | No | No | No | **YES (ROCK2, MAPK14, LIMK1)** |
| Cross-disease convergence | No | Partial | No | No | **YES (SMA-ALS, PFN1 convergence)** |
| GEO transcriptomics integration | No | No | No | Partial | **YES (7 datasets, DEG analysis)** |
| Clinical trial tracking | No | No | InClinico | No | **YES (451 trials)** |
| MCP API (32 tools) | No | No | API | No | **YES** |
| Open/academic | No | No | No | No | **YES (non-commercial research)** |

### Our Unique Differentiators

1. **Disease specialization**: Only platform 100% focused on SMA with deep biological knowledge
2. **Full-stack computational**: From literature mining to protein binder design in one platform
3. **Cross-disease convergence**: SMA-ALS overlap via actin pathway (PFN1, CORO1C, CFL2) -- no one else does this
4. **Novel therapeutic hypotheses**: CORO1C double-hit model (0 prior papers), fasudil for SMA, anti-miR-133a-3p
5. **Reproducibility package**: Evidence tiers, calibration scores, gold-standard validation

---

## 4. ROCK-LIMK-Cofilin Axis: Who Is Working On It?

### Key Groups

| Researcher | Institution | Focus | Latest |
|-----------|------------|-------|--------|
| **Melissa Bowerman** | Keele University / Aix-Marseille | ROCK inhibition for SMA; fasudil preclinical | Foundational work (2012-2014); no new SMA-specific ROCK papers since ~2015 |
| **Bhatt group** | Columbia | SMN directly regulates actin dynamics | 2024 paper on SMN-actin regulation |
| **Li / Zhang** | China (multiple institutions) | Cytoskeleton dysfunction review in SMA | 2024 comprehensive review (J Neurol) -- covers ROCK/LIMK/cofilin/profilin |
| **C9ORF72-ALS groups** | Multiple | Cofilin modulates actin in C9ORF72 motor neurons | [Bhatt et al., 2016](https://pubmed.ncbi.nlm.nih.gov/27723745/) -- ALS, not SMA |

### Fasudil for SMA: Current State

- **Preclinical only**. No clinical trials exist or are planned for fasudil in SMA.
- Bowerman (2012) showed dramatic lifespan improvement in SMA mice
- Mechanism is SMN-independent: works via cytoskeletal rescue + muscle development
- Fasudil is in ALS clinical trials (separate), which could generate safety data transferable to SMA
- **Our platform identified fasudil as top validated hit via DiffDock** -- we are computationally ahead

### Actin Dynamics in SMA: Recent Publications (2024-2025)

1. **"Cytoskeleton dysfunction of motor neuron in spinal muscular atrophy"** (J Neurol, 2024)
   - Comprehensive review of actin/microtubule/neurofilament dysfunction
   - Covers profilin-2, plastin-3, stathmin-1, MAP1B
   - Confirms: SMN loss -> free profilin-2 -> ROCK phosphorylation -> F/G-actin imbalance
   - [PMC11638312](https://pmc.ncbi.nlm.nih.gov/articles/PMC11638312/)

2. **"The SMA gene product regulates actin dynamics"** (2024)
   - Direct evidence that SMN protein controls actin polymerization
   - F-actin organizational defect quantified
   - [PMID 39305126](https://pubmed.ncbi.nlm.nih.gov/39305126/)

3. **"Whole-blood dysregulation of actin-cytoskeleton pathway in adult SMA patients"** (2020)
   - Systemic actin pathway disruption, not just motor neurons
   - Supports our "actin pathway is the real finding" thesis
   - [PMC7359125](https://pmc.ncbi.nlm.nih.gov/articles/PMC7359125/)

### Our Position

We are the only group that has:
- Mapped the full ROCK-LIMK-Cofilin-Profilin-CORO1C axis computationally
- Generated de novo molecules targeting ROCK2 (via GenMol)
- Designed protein binders for ROCK2, MAPK14, and LIMK1 (via RFdiffusion)
- Proposed a multi-kinase inhibitor strategy targeting the axis
- Connected the actin pathway to SMA-ALS convergence via PFN1

---

## 5. Protein Binder Design for Neurological Targets

### State of the Field (2025-2026)

**RFdiffusion** (Baker Lab, Institute for Protein Design, UW):
- RFdiffusion3 released December 2025: 10x faster than v2, handles any biomolecule
- Beta-pairing targeted RFdiffusion achieves pM-nM affinities for edge-strand targets
- Demonstrated binders for KIT, PDGFRa, ALK-2, ALK-3, FCRL5, NRP1
- **No published applications to ROCK2, MAPK14, or SMA-related targets**

**PepMLM** (peptide binder design):
- Can generate peptides targeting neurodegeneration-related proteins
- Works without structural information (sequence-based)
- Not yet applied to SMA targets specifically

**ProteinDJ Pipeline** (2025 preprint):
- Modular protein design pipeline combining multiple tools
- No SMA applications published

### Who Has Designed Binders for Our Targets?

| Target | Published Binder Designs | Our Status |
|--------|------------------------|------------|
| ROCK2 | **None found** | RFdiffusion binders designed, documented |
| MAPK14 (p38a) | Small molecule inhibitors extensively studied; **no protein binders** | RFdiffusion binders designed |
| LIMK1 | **None found** | RFdiffusion binders designed |
| SARM1 | **None found** for binders | GenMol molecules generated |

### Our Advantage

**We appear to be the first to apply RFdiffusion protein binder design to SMA-relevant kinase targets (ROCK2, MAPK14, LIMK1).** This is a genuinely novel application. No academic group or company has published binder designs for these neurodegeneration-relevant kinases.

---

## 6. Strategic Assessment

### Threats

| Threat | Severity | Mitigation |
|--------|----------|------------|
| Apitegromab approval (Sep 2025) changes treatment paradigm | **Medium** | Our targets are complementary (cytoskeletal, not myostatin) |
| Salanersen Phase 3 success would dominate SMN space | **Low** | We focus on SMN-independent mechanisms |
| Large pharma enters computational SMA | **Low** (SMA too small a market) | Speed advantage; first-mover on actin axis |
| Recursion/Insilico pivots to SMA | **Very Low** | Our disease-specific depth is years ahead |

### Opportunities

| Opportunity | Impact | Action Required |
|-------------|--------|----------------|
| **No ROCK inhibitor clinical trial for SMA exists** | HIGH | Fasudil repurposing proposal; seek academic collaborator for preclinical validation |
| **Actin pathway gaining recognition (2024 papers)** | HIGH | Publish our computational findings before wet-lab groups catch up |
| **RFdiffusion binders for ROCK2 are first-in-field** | HIGH | Validate computationally (binding energy); seek wet-lab partner |
| **Cross-disease SMA-ALS convergence is underexplored** | MEDIUM | PFN1 and CFL2 convergence paper; attract ALS funding |
| **Apitegromab + cytoskeletal therapy combination** | MEDIUM | Model combination approach; propose synergy hypothesis |

### What Competitors Have That We Don't

| Capability | Who Has It | Priority for Us |
|-----------|-----------|----------------|
| Wet-lab validation | Scholar Rock, NMD Pharma, Biogen | **CRITICAL** -- need academic partner |
| Clinical trial infrastructure | Biogen, Roche, Novartis | Not needed yet |
| Phenotypic screening at scale | Recursion | Low priority -- we use structure-based |
| Real-world patient data (EHR) | Valo Health | Medium -- could enhance clinical relevance |
| FDA-approved drug in portfolio | Biogen (nusinersen) | N/A -- we are research platform |
| Commercial AI platform | Insilico (Pharma.AI) | Low -- our value is disease expertise |

---

## 7. Summary

### Our Platform by the Numbers

| Metric | Count |
|--------|-------|
| Sources (literature) | 6,778 |
| Molecular targets | 63 |
| Drugs tracked | 21 |
| Clinical trials | 451 |
| Evidence claims | 14,187 |
| Hypotheses | 1,472 |
| GEO datasets | 7 |
| MCP tools | 32 |
| API endpoints | ~210 |

### Bottom Line

1. **No direct competitor exists** -- no one has built a dedicated computational SMA drug discovery platform
2. **The closest analogs** (Healx, BenevolentAI, Insilico) are general-purpose and lack SMA-specific depth
3. **Our actin pathway / ROCK-LIMK-Cofilin work is ahead of the field** -- 2024 publications confirm the biology but no one is doing computational drug design against these targets
4. **Fasudil for SMA is an open opportunity** -- strong preclinical evidence (2012), no clinical trials, we have DiffDock validation
5. **RFdiffusion binders for ROCK2/MAPK14/LIMK1 appear to be first-in-field** -- no published precedent found
6. **Critical gap: wet-lab validation** -- computational predictions without experimental confirmation limit credibility
7. **Timing is favorable**: actin dynamics in SMA is gaining recognition (2024 review papers), apitegromab is proving non-SMN approaches work, and ROCK inhibitor clinical data from ALS trials will generate transferable safety evidence

---

## Sources

- [Drug Discovery of SMA from the Computational Perspective (Rai et al., 2021)](https://www.mdpi.com/1422-0067/22/16/8962)
- [AI-guided analysis of disease-relevant molecules in SMA (2024)](https://doi.org/10.1093/hmg/ddae076)
- [Cure SMA Drug Pipeline](https://www.curesma.org/sma-drug-pipeline/)
- [SAPPHIRE Phase 3 Results -- Lancet Neurology (2025)](https://www.thelancet.com/journals/laneur/article/PIIS1474-4422(25)00225-X/abstract)
- [Scholar Rock SAPPHIRE Primary Endpoint](https://investors.scholarrock.com/news-releases/news-release-details/scholar-rock-reports-apitegromab-meets-primary-endpoint-phase-3)
- [Salanersen Phase 3 STELLAR Studies](https://www.neurologylive.com/view/phase-3-stellar-studies-test-efficacy-salanersen-presymptomatic-newborns-sma)
- [Biogen Salanersen Data (March 2026)](https://investors.biogen.com/news-releases/news-release-details/biogen-presents-additional-salanersen-data-showing-new-motor)
- [NMD670 Phase 2 Trial (NCT05794139)](https://clinicaltrials.gov/study/NCT05794139)
- [ROCK inhibition as therapy for SMA (Bowerman, 2014)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4148024/)
- [Fasudil improves survival in SMA mice (Bowerman, 2012)](https://pubmed.ncbi.nlm.nih.gov/22397316/)
- [Cytoskeleton dysfunction of motor neuron in SMA (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11638312/)
- [SMN regulates actin dynamics (2024)](https://pubmed.ncbi.nlm.nih.gov/39305126/)
- [Healx AI Drug Discovery](https://healx.ai/)
- [BenevolentAI Expert-Augmented Drug Discovery](https://www.benevolent.com/news-and-media/blog-and-videos/expert-augmented-computational-drug-discovery-rare-diseases/)
- [Insilico Medicine Phase 2 AI Drug](https://insilico.com/blog/first_phase2)
- [RFdiffusion3 (IPD, Dec 2025)](https://www.ipd.uw.edu/2025/12/rfdiffusion3-now-available/)
- [Beta-pairing targeted RFdiffusion binders (Nature Comms, 2025)](https://www.nature.com/articles/s41467-025-67866-3)
- [AI in Rare Disease Drug Discovery (The Medicine Maker, 2026)](https://themedicinemaker.com/issues/2026/articles/february/the-role-of-ai-in-rare-disease-drug-discovery/)
- [Leading AI Drug Discovery Platforms: 2025 Landscape](https://www.sciencedirect.com/science/article/abs/pii/S0031699725075118)
- [AI Drug Discovery Trends 2026 (Ardigen)](https://ardigen.com/ai-in-biotech-lessons-from-2025-and-the-trends-shaping-drug-discovery-in-2026/)
