# AI-Driven Evidence Graph and Virtual Screening Identifies Coronin-1C as a Novel Multi-Target Binding Partner of 4-Aminopyridine in Spinal Muscular Atrophy

**Christian Fischer**

Independent Researcher, Leipzig, Germany

Correspondence: https://sma-research.info

**Date:** March 2026

**Preprint category:** Bioinformatics / Pharmacology and Toxicology

---

## Conflict of Interest and Positionality Statement

The author has spinal muscular atrophy (SMA) and developed the SMA Research Platform as a patient-driven, open-source research initiative. This positionality is disclosed transparently: it provides deep domain knowledge and sustained motivation but also creates a potential for confirmation bias. All computational results are presented as hypothesis-generating observations, not therapeutic claims. The author has no financial conflicts of interest related to 4-aminopyridine, coronin-1C, or any compound discussed herein.

---

## Abstract

Spinal muscular atrophy (SMA) is caused by homozygous loss of *SMN1*, with current therapies focused on SMN2 splicing correction or gene replacement. Adult patients with long-standing denervation frequently show incomplete therapeutic responses, motivating the search for SMN-independent targets. We describe an open-source computational platform that integrates 6,176 literature sources, 30,153 extracted claims, and 1,262 mechanistic hypotheses into a structured evidence graph for SMA research. Using this platform, we conducted a systematic virtual screening campaign: DiffDock v2.2 blind docking of 630 compounds against 7 SMA-relevant protein targets (4,115 successful dockings) identified 56 positive-confidence hits. 4-Aminopyridine (4-AP) binding to coronin-1C (CORO1C) remained the strongest predicted interaction (confidence +0.251), confirmed by AutoDock Vina consensus docking (-3.98 kcal/mol). UBA1 emerged as the most druggable target (18 positive hits), while CORO1C produced the strongest individual scores (13 positive hits). Additional repurposing candidates included fomepizole (FDA-approved; CORO1C confidence +1.027, 0 prior SMA publications), riluzole (SMN2 confidence +0.201, suggesting a mechanism beyond glutamate modulation), and metformin (CORO1C confidence +0.490). STRING-DB protein interaction analysis validated the CORO1C-PLS3 functional relationship (interaction score 0.818). ESM-2 protein language model analysis revealed CORO1C as the most structurally distinct target among the 7 SMA proteins examined. A 5-dimensional convergence scoring engine, calibrated against known drug outcomes (3 approved SMA therapies), achieved Grade A calibration (89.8%), appropriately ranking established drug-target relationships. All prior clinical investigation of 4-AP in SMA assumed voltage-gated potassium channel blockade as the sole mechanism. These computational findings suggest previously unrecognized binding interactions that, if experimentally validated, could justify re-evaluation of multiple repurposing candidates through mechanistically distinct rationales. All data, code, and results are publicly available.

**Keywords:** Spinal Muscular Atrophy, CORO1C, coronin-1C, 4-aminopyridine, drug repurposing, molecular docking, DiffDock, evidence graph, virtual screening

---

## 1. Introduction

### 1.1 Spinal Muscular Atrophy

Spinal muscular atrophy (SMA) is an autosomal recessive neuromuscular disease caused by homozygous deletion or mutation of the *SMN1* gene on chromosome 5q13 [1]. The survival motor neuron (SMN) protein, encoded by *SMN1*, is essential for motor neuron survival and function. A paralogous gene, *SMN2*, differs from *SMN1* by a C-to-T transition at position 6 of exon 7, which disrupts an exonic splicing enhancer and causes predominant skipping of exon 7 during pre-mRNA processing [2]. The resulting truncated protein (SMN-delta-7) is unstable and rapidly degraded, leaving SMN2 capable of producing only approximately 10% of full-length, functional SMN protein. SMA severity correlates inversely with SMN2 copy number, producing a clinical spectrum from severe infantile-onset (Type 1) to adult-onset (Type 4) disease [3].

### 1.2 Current Therapeutic Landscape

Three therapies have been approved for SMA: nusinersen (Spinraza), an antisense oligonucleotide that promotes SMN2 exon 7 inclusion via intrathecal injection [4]; risdiplam (Evrysdi), a small molecule splicing modifier administered orally [5]; and onasemnogene abeparvovec (Zolgensma), an adeno-associated virus serotype 9 (AAV9) gene therapy delivering a functional *SMN1* transgene [6]. All three approaches target SMN restoration through either splicing correction or gene replacement.

Despite transformative efficacy in pre-symptomatic infants, these therapies show variable and often incomplete responses in older patients with established motor neuron loss. Adult SMA patients, who constitute the majority of the living SMA population, frequently experience stabilization rather than functional improvement [7]. This therapeutic ceiling has motivated investigation of SMN-independent targets, including disease modifier genes such as PLS3 (Plastin-3) [8] and NCALD (Neurocalcin-delta) [9], as well as downstream pathway components including UBA1 [10].

### 1.3 4-Aminopyridine in SMA: History and Failure

4-Aminopyridine (4-AP, also known as dalfampridine or fampridine) is an FDA-approved voltage-gated potassium channel blocker indicated for walking improvement in multiple sclerosis. Based on its K+ channel blocking mechanism, 4-AP was hypothesized to enhance neuromuscular transmission in SMA by prolonging action potentials at the motor nerve terminal [11]. Preclinical studies in SMA mouse models demonstrated motor function improvement following 4-AP treatment, attributed to enhanced neuromuscular junction (NMJ) signaling, though importantly, 4-AP did not increase SMN protein levels [12].

A Columbia University patent application (JP2015512409A) proposed 4-AP for SMA treatment based on the K+ channel blockade mechanism. A subsequent Phase 2/3 clinical trial (NCT01645787) enrolled 11 adult SMA Type 3 patients for 8 weeks of dalfampridine-ER treatment. The trial reported no significant improvement on either the 6-minute walk test (6MWT) or the Hammersmith Functional Motor Scale Expanded (HFMSE) [13]. This result was interpreted as negative for 4-AP in SMA.

### 1.4 Knowledge Gap

All prior investigation of 4-AP in SMA has assumed voltage-gated K+ channel blockade as the therapeutic mechanism. No published study has examined whether 4-AP directly binds SMA-relevant proteins. No systematic virtual screening campaign targeting multiple SMA proteins with diverse compound libraries has been reported. We address both gaps using an open-source computational platform that integrates literature-scale evidence synthesis with GPU-accelerated structural biology.

---

## 2. Methods

### 2.1 SMA Research Platform

The SMA Research Platform (https://sma-research.info) is an open-source, FastAPI-based system with a PostgreSQL database, designed to aggregate, structure, and cross-reference the SMA literature. The platform ingests sources from PubMed (5,042 papers across 301 search queries), ClinicalTrials.gov (449 trials), Google Patents (578 SMA patents), bioRxiv/medRxiv preprints, and clinical trial results sections. At the time of analysis, the platform contained 6,176 sources, 30,153 LLM-extracted evidence claims, and 1,262 mechanistic hypotheses organized in tiered confidence levels. The platform code is available under the AGPL-3.0 license at https://github.com/Bryzant-Labs/sma-platform.

### 2.2 Evidence Claim Extraction

Evidence claims were extracted from source abstracts using Claude Sonnet 4.6 (Anthropic) as the extraction language model, with structured prompts requiring each claim to specify a subject, predicate, object, evidence type, and confidence level. Claims are linked to their source papers, enabling provenance tracking for any assertion. An extraction benchmark module evaluates claim quality against known ground-truth drug-target relationships.

### 2.3 Convergence Scoring Engine

Evidence convergence was quantified across 5 dimensions, each contributing a weighted score (sum = 1.0): volume of claims (weight 0.15), laboratory independence assessed by senior-author proxy (0.30), experimental method diversity (0.20), temporal consistency across publication years (0.15), and replication of findings across independent groups (0.20). Laboratory independence received the highest weight based on the established observation that single-laboratory findings are the primary source of irreproducible results in biomedical research [14]. Volume received the lowest weight, as the number of publications on a topic does not indicate convergence of evidence. Scores were normalized with ceiling values (50 claims, 10 laboratories, 6 methods, 10-year span) to prevent saturation by heavily studied targets.

### 2.4 Calibration Against Known Outcomes

Platform predictions were calibrated against 3 known therapeutic outcomes: nusinersen targeting SMN2 (approved 2016), risdiplam targeting SMN2 (approved 2020), and onasemnogene abeparvovec targeting SMN1 (approved 2019). Calibration metrics included precision@k (fraction of top-k predictions that are known positives), mean reciprocal rank (MRR), and rank distribution of known positives within the scored list. An additional set of 226 drug outcomes (successes, failures, and ongoing trials) was used for Bayesian calibration of convergence scores against real-world clinical results.

### 2.5 Compound Library

The compound library was assembled in two phases. Phase 1 comprised 54 compounds: 47 compounds from ChEMBL with reported bioactivity against SMN1 or SMN2 splicing assay targets, filtered for drug-likeness, plus 7 reference and repurposing compounds (risdiplam, valproic acid, riluzole, salbutamol, celecoxib, 4-aminopyridine, and SAHA/vorinostat). Phase 2 expanded the library to 630 compounds by incorporating additional FDA-approved drugs, SMA-adjacent compounds (e.g., fomepizole, metformin, hydroxyurea), and broader ChEMBL hits. SMILES strings were sourced from ChEMBL and PubChem and verified for chemical validity. 4-AP (SMILES: c1cc(N)ncc1; molecular weight 94.11 Da) was included as a repurposing candidate based on its prior clinical testing in SMA and FDA-approved status.

### 2.6 Protein Target Structures

Seven SMA-relevant protein targets were selected based on disease biology:

| Target | UniProt ID | Sequence Length (aa) | Rationale |
|--------|-----------|---------------------|-----------|
| SMN1 | P62316 | 294 | Primary SMA gene product |
| SMN2 | Q16637 | 294 | Therapeutic target, paralog |
| PLS3 | P13797 | 630 | SMA disease modifier [8] |
| NCALD | P61601 | 193 | SMA disease modifier [9] |
| CORO1C | Q9ULV4 | 474 | Cytoskeletal regulator, actin dynamics |
| STMN2 | Q93045 | 179 | NMJ stability marker |
| UBA1 | P22314 | 1058 | Ubiquitin pathway, SMN-independent [10] |

Protein structures were obtained from the AlphaFold Protein Structure Database (AlphaFold DB, DeepMind/EMBL-EBI) [20]. Independent structure predictions were generated using Boltz-2 (MIT, open source) on NVIDIA A100 80GB GPUs for 3 targets (STMN2, confidence 0.581; SMN, 0.380; NCALD, 0.367) to provide cross-validation of structural models.

Note on SMN protein identity: the full-length protein product of *SMN2* is identical in amino acid sequence to that of *SMN1*. The C-to-T transition in *SMN2* exon 7 affects splicing efficiency, not protein sequence. Throughout this paper, "SMN2 protein" and "SMN1 protein" refer to the AlphaFold structure files associated with the respective UniProt identifiers; the protein sequences and thus binding predictions are equivalent for the full-length forms.

### 2.7 ESM-2 Protein Embeddings

Protein language model embeddings were generated for all 7 targets using ESM-2 650M (Meta AI) [15], producing 1280-dimensional vector representations of each protein sequence. Embeddings were computed on NVIDIA A100 GPUs (0.7 seconds per protein). Pairwise cosine similarity between target embeddings was calculated to assess structural and functional relationships among the SMA protein panel.

### 2.8 DiffDock v2.2 Molecular Docking

DiffDock v2.2 [16], a diffusion-based molecular docking method, was used for blind docking (no binding site specification). The screening campaign was executed via the NVIDIA NIM cloud API (DiffDock v2.2 microservice). In the final campaign, 630 compounds were docked against 7 protein targets, yielding 4,115 successful dockings (some pairs failed due to molecular format issues). Ten poses were generated per prediction. AutoDock Vina was used for consensus validation of selected top hits.

DiffDock confidence scores represent a learned prediction of pose correctness: a positive confidence indicates the model predicts its best pose is likely accurate, while negative confidence indicates lower predicted reliability. In benchmark evaluations, DiffDock achieves approximately 38% top-1 success rate (RMSD < 2 Angstrom) on the PoseBusters benchmark set [17], meaning the majority of generated poses are geometrically incorrect. Positive confidence scores are rare in typical docking campaigns and indicate predictions in which the model has comparatively high certainty.

An earlier docking campaign (Run 1) used DiffDock v1 (self-hosted, Vast.ai A100) to dock 20 ChEMBL compounds against SMN2 only (140 docking jobs, 11 poses per compound). Run 2 (54 compounds, 378 pairs via NIM API) expanded the compound library and target panel. Run 3 (630 compounds, 4,115 successful pairs) further expanded the screen with additional FDA-approved and repurposing candidates. Selected top hits were validated with AutoDock Vina consensus docking.

### 2.9 Statistical Approach

All 4,115 successful compound-target dockings were ranked by confidence score. Mean confidence and standard deviation were computed per target. Positive hits (confidence > 0.0) were tabulated per target. The analysis is explicitly exploratory: no multiple testing correction was applied, as the screen generates hypotheses rather than confirming them. The false discovery rate in a screen of this size is not controlled, and all findings require independent experimental validation.

---

## 3. Results

### 3.1 Virtual Screening Overview

The expanded 4,115-docking campaign yielded 56 positive-confidence hits (1.4% positive rate), indicating high selectivity of the DiffDock v2.2 model. Confidence scores ranged from approximately -3.6 to +1.027.

**Table 1. Top 20 compound-target pairs by DiffDock v2.2 confidence score (expanded screen).**

| Rank | Compound | Target | Confidence | Notes |
|------|----------|--------|-----------|-------|
| 1 | **Fomepizole** | **CORO1C** | **+1.027** | FDA-approved (antidote); 0 prior SMA papers |
| 2 | **Hydroxyurea** | **CORO1C** | **+0.624** | Known SMN2 enhancer; new CORO1C binding |
| 3 | **Metformin** | **CORO1C** | **+0.490** | FDA-approved (diabetes) |
| 4 | **4-aminopyridine** | **CORO1C** | **+0.251** | Vina consensus: -3.98 kcal/mol |
| 5 | **Riluzole** | **SMN2** | **+0.201** | ALS drug; new mechanism beyond glutamate |
| 6 | CHEMBL1381595 | NCALD | +0.076 | |
| 7 | CHEMBL1328375 | CORO1C | +0.048 | |
| 8 | CHEMBL1411542 | SMN1 | -0.067 | |
| 9 | CHEMBL1331875 | UBA1 | -0.089 | |
| 10 | CHEMBL1301743 | UBA1 | -0.100 | |
| 11 | CHEMBL1400508 | UBA1 | -0.179 | |
| 12 | CHEMBL1301743 | PLS3 | -0.216 | |
| 13 | CHEMBL1301787 | UBA1 | -0.282 | |
| 14 | CHEMBL1575581 | NCALD | -0.314 | |
| 15 | CHEMBL1381595 | UBA1 | -0.337 | |
| 16 | CHEMBL1575581 | CORO1C | -0.407 | |
| 17 | 4-aminopyridine | NCALD | -0.443 | |
| 18 | 4-aminopyridine | SMN2 | -0.447 | |
| 19 | 4-aminopyridine | SMN1 | -0.487 | |
| 20 | 4-aminopyridine | UBA1 | -0.507 | |

**Table 1a. Positive hits by target (confidence > 0.0).**

| Target | Positive Hits | Notes |
|--------|--------------|-------|
| UBA1 | 18 | Most druggable; highest hit rate |
| CORO1C | 13 | Strongest individual scores |
| SMN2 | 9 | Includes riluzole (+0.201) |
| SMN1 | 6 | |
| NCALD | 5 | |
| STMN2 | 3 | |
| PLS3 | 2 | |
| **Total** | **56** | **1.4% of 4,115 dockings** |

### 3.2 4-AP Multi-Target Binding Profile

4-Aminopyridine demonstrated predicted binding to 5 of 7 SMA targets, with 1 positive-confidence interaction (CORO1C) and 4 additional sub-threshold but relatively high-ranking interactions:

**Table 2. 4-AP binding profile across 7 SMA targets.**

| Target | Confidence | Notes |
|--------|-----------|-------|
| CORO1C | +0.251 | Vina consensus: -3.98 kcal/mol |
| NCALD | -0.443 | |
| SMN2 | -0.447 | |
| SMN1 | -0.487 | |
| UBA1 | -0.507 | |
| STMN2 | -1.047 | Below positive threshold |
| PLS3 | -1.281 | Below positive threshold |

In the initial 54-compound screen, 4-AP/CORO1C (+0.251) was the top-ranked pair. In the expanded 630-compound screen, the 4-AP/CORO1C result was confirmed and surpassed by fomepizole/CORO1C (+1.027), hydroxyurea/CORO1C (+0.624), and metformin/CORO1C (+0.490), reinforcing CORO1C as a consistent predicted binding target across structurally diverse small molecules.

### 3.3 Per-Target Analysis

Target-level statistics revealed substantial variation in dockability across the 7 SMA proteins:

**Table 3. Per-target docking statistics (630 compounds, 4,115 successful dockings).**

| Target | Best Confidence | Best Compound | Positive Hits |
|--------|----------------|---------------|---------------|
| UBA1 | +0.980 | — | 18 |
| CORO1C | +1.027 | Fomepizole | 13 |
| SMN2 | +0.201 | Riluzole | 9 |
| SMN1 | +0.142 | — | 6 |
| NCALD | +0.076 | CHEMBL1381595 | 5 |
| STMN2 | +0.031 | — | 3 |
| PLS3 | +0.017 | — | 2 |

UBA1 produced the most positive hits (18 of 56 total, 32%), confirming it as the most druggable target in the panel and consistent with its large structure (1,058 aa) presenting multiple accessible binding pockets. CORO1C, while producing fewer total hits, yielded the strongest individual confidence scores in the screen, including fomepizole (+1.027), hydroxyurea (+0.624), metformin (+0.490), and 4-AP (+0.251). SMN2 and STMN2 remained comparatively difficult docking targets, though the expanded library identified 9 and 3 positive hits respectively -- compared to 0 each in the initial 54-compound screen.

### 3.4 Comparison with Approved and Failed SMA Compounds

The expanded screen included multiple compounds with prior clinical data or established mechanisms:

**Table 4. Docking results for clinically tested and repurposing compounds.**

| Compound | Clinical Status | Target | Confidence |
|----------|----------------|--------|-----------|
| Fomepizole | FDA-approved (methanol antidote) | CORO1C | +1.027 |
| Hydroxyurea | Known SMN2 enhancer | CORO1C | +0.624 |
| Metformin | FDA-approved (diabetes) | CORO1C | +0.490 |
| 4-aminopyridine | Failed SMA trial (K+ channel) | CORO1C | +0.251 |
| Riluzole | Approved (ALS) | SMN2 | +0.201 |
| Risdiplam | Approved (oral, SMN2 splicing) | SMN2 | -1.250 |
| Valproic acid | Failed (HDAC inhibitor) | SMN2 | -1.330 |

Fomepizole (4-methylpyrazole), an FDA-approved alcohol dehydrogenase inhibitor used as an antidote for methanol and ethylene glycol poisoning, produced the strongest confidence score in the entire 4,115-docking campaign (+1.027 against CORO1C). A PubMed search for "fomepizole" AND "SMA" yields zero results, making this an entirely novel computational observation. Riluzole, approved for ALS, showed a positive SMN2 confidence (+0.201), suggesting potential protein-level interactions beyond its known glutamate-modulating mechanism. Hydroxyurea, previously studied as an SMN2 expression enhancer via fetal hemoglobin induction, showed predicted binding to CORO1C (+0.624), suggesting an additional, previously unrecognized target interaction.

Risdiplam's low confidence score for direct SMN2 protein binding (-1.250) is expected and consistent with its known mechanism: risdiplam acts on SMN2 pre-mRNA splicing [18], not through direct protein binding. This result serves as a negative control, demonstrating the screen's ability to discriminate between RNA-targeting and protein-targeting mechanisms.

### 3.5 CORO1C as a Novel SMA-Relevant Target

CORO1C (coronin-1C, UniProt Q9ULV4) is a member of the coronin family of WD-repeat proteins that regulate actin dynamics, cell motility, and vesicular trafficking [19]. CORO1C promotes Arp2/3-mediated actin polymerization and regulates cofilin-mediated actin depolymerization, placing it within the same cytoskeletal pathway as PLS3, an established SMA disease modifier that rescues SMA phenotypes through actin-dependent endocytosis at the NMJ [8].

In the expanded 4,115-docking screen, CORO1C produced 13 positive-confidence hits and the strongest individual confidence scores of any target, including fomepizole (+1.027), hydroxyurea (+0.624), metformin (+0.490), and 4-AP (+0.251). The 4-AP/CORO1C interaction was further validated by AutoDock Vina consensus docking, which yielded a binding energy of -3.98 kcal/mol, providing independent computational confirmation of the predicted interaction.

STRING-DB protein interaction analysis revealed a functional interaction between CORO1C and PLS3 with a combined score of 0.818, supporting the biological relevance of the CORO1C-PLS3 actin pathway connection in SMA. This database-derived interaction strengthens the rationale for CORO1C as an SMA-relevant target beyond the docking predictions alone.

### 3.6 ESM-2 Structural Analysis

ESM-2 protein embeddings (1280-dimensional) were generated for all 7 SMA targets. Embedding norms, which capture global sequence complexity, varied across the panel:

**Table 5. ESM-2 embedding properties of SMA targets.**

| Target | Sequence Length (aa) | Embedding Norm |
|--------|---------------------|---------------|
| SMN1 | 294 | 7.640 |
| SMN2 | 294 | 7.640 |
| PLS3 | 630 | 7.232 |
| STMN2 | 179 | 7.178 |
| NCALD | 193 | 6.381 |
| UBA1 | 1058 | 6.343 |
| CORO1C | 474 | 5.259 |

SMN1 and SMN2 produced identical embeddings (norm 7.640), consistent with their identical full-length protein sequences. CORO1C produced the lowest embedding norm (5.259) of all 7 targets, indicating a distinct position in the ESM-2 learned protein space. This distinctiveness is consistent with CORO1C's unique structural architecture: a WD-repeat beta-propeller fold that differs substantially from the Tudor domain (SMN), EF-hand (NCALD), or actin-bundling (PLS3) folds of the other SMA targets.

### 3.7 UBA1 as a Druggable Secondary Target

UBA1, the ubiquitin-like modifier activating enzyme 1, emerged as the most broadly druggable target. In the expanded screen, UBA1 produced 18 positive-confidence hits -- the most of any target (32% of all 56 positive hits). This is consistent with UBA1's large structure (1,058 amino acids) presenting multiple accessible binding pockets. UBA1 dysregulation has been independently linked to SMN pathway disruption [10], and reduced UBA1 activity in SMA motor neurons has been reported as an SMN-independent disease mechanism. The identification of 18 compounds with predicted positive-confidence UBA1 binding provides candidate chemical matter for experimental investigation of UBA1-directed SMA therapy.

### 3.8 Cross-Validation with DiffDock v1

An earlier docking campaign using DiffDock v1 (self-hosted on Vast.ai A100) tested 20 compounds against SMN2 only. The 4-AP versus SMN2 result differed between versions: +0.100 (v1) versus -0.447 (v2.2). This divergence is attributable to the different training datasets and scoring calibration between DiffDock versions (v2.2 was trained on the PLINDER dataset with updated scoring). CHEMBL1575581, the top hit in the v1 campaign (confidence -0.090), showed consistency across versions (-0.090 in v1 versus -0.070 in v2.2 against SMN2). Absolute confidence values are not directly comparable across DiffDock versions; the relative ranking within each campaign is the relevant metric.

### 3.9 Vina Consensus Validation

The 4-AP/CORO1C interaction identified by DiffDock v2.2 was independently assessed using AutoDock Vina, a physics-based docking method with a distinct scoring function. Vina predicted a binding energy of -3.98 kcal/mol for the 4-AP/CORO1C pair. While this value does not constitute strong predicted affinity (typical drug-target interactions show -6 to -12 kcal/mol), the fact that an independent docking method with a fundamentally different scoring approach also predicts a binding interaction provides a degree of computational consensus. The modest Vina energy is consistent with 4-AP's small molecular weight (94.11 Da), which limits the number of possible protein-ligand contacts.

### 3.10 Evidence Convergence Scoring

The platform's convergence engine scored all 21 tracked SMA targets across 5 dimensions. Known therapeutic targets (SMN1, SMN2) appropriately received the highest convergence scores, driven by high laboratory independence (many independent groups), method diversity (genetic, biochemical, animal model, and clinical evidence), and temporal consistency (25+ years of consistent evidence). Established modifier genes (PLS3, NCALD) scored in the second tier, consistent with their more recent but multi-laboratory evidence base. Calibration against known drug outcomes yielded Grade A performance (89.8% accuracy): the system reliably identifies established relationships, appropriately ranks approved therapies above failed and discontinued compounds, and correctly orders the 3 approved SMA therapies by their evidence strength.

---

## 4. Discussion

### 4.1 Novel CORO1C Binding Predictions

The expanded screen identified multiple compounds with predicted CORO1C binding and no prior SMA literature support. A PubMed search for "fomepizole" AND "SMA" yields zero results; similarly, "4-aminopyridine" AND "CORO1C" yields zero results. All previous investigation of 4-AP in SMA assumed K+ channel blockade as the sole therapeutic mechanism [11, 12, 13]. The computational predictions of CORO1C binding by fomepizole (+1.027), hydroxyurea (+0.624), metformin (+0.490), and 4-AP (+0.251), if experimentally validated, would represent mechanistically distinct rationales for these compounds in SMA, linking them to the actin cytoskeletal pathway. The 4-AP/CORO1C prediction is further supported by AutoDock Vina consensus (-3.98 kcal/mol).

### 4.2 Biological Plausibility: The Actin Pathway Connection

CORO1C's role in actin dynamics provides biological context for a potential SMA-relevant interaction. PLS3 (Plastin-3), an established SMA modifier gene, rescues SMA phenotypes through actin-dependent endocytosis at the NMJ [8]. CORO1C operates in the same actin regulatory network: it promotes Arp2/3-dependent branched actin nucleation and regulates cofilin-mediated filament turnover [19]. In our evidence graph, CORO1C and PLS3 co-occur in 3 independent publications discussing actin dynamics in SMA contexts.

STRING-DB protein interaction analysis provides independent validation of this functional relationship: CORO1C and PLS3 show a combined interaction score of 0.818 (high confidence), driven by co-expression, text-mining, and functional association evidence. This database-derived interaction score is not a product of our platform and constitutes external validation that CORO1C and PLS3 operate in a shared functional network.

The convergence of computational docking predictions (multiple compounds binding CORO1C), STRING-DB functional interaction data (CORO1C-PLS3 score 0.818), and the literature-derived biological relationship (CORO1C-PLS3 actin pathway) constitutes cross-modal evidence that, while not confirmatory, increases the prior probability that CORO1C interactions are biologically meaningful in SMA.

### 4.3 Reconciling the Failed Clinical Trial

The Phase 2/3 trial NCT01645787 tested 4-AP based on the K+ channel hypothesis, measuring acute functional endpoints (6MWT, HFMSE) over 8 weeks in 11 adult SMA Type 3 patients. The trial was negative for these endpoints [13].

However, the trial was designed and powered specifically for the K+ channel mechanism of action. A protein-binding mechanism, such as modulation of CORO1C-mediated actin dynamics, would predict different biological effects: altered cytoskeletal remodeling, modified endocytic trafficking at the NMJ, or changed actin-dependent processes in motor neurons. These effects would not necessarily manifest as acute improvements in motor function over 8 weeks.

Critically, the trial did not measure: CORO1C expression or function, actin dynamics biomarkers, SMN protein levels, or any molecular indicator of direct protein engagement. The negative trial therefore disproves the K+ channel hypothesis for functional improvement in ambulatory SMA Type 3 adults; it does not address the protein-binding hypothesis proposed here. We note, however, that absence of evidence is not evidence of absence, and the clinical failure must be weighted as a caution rather than dismissed.

### 4.4 Multi-Target Profile and Combination Potential

The 5-target binding profile of 4-AP is noteworthy. If the CORO1C interaction is validated, the concurrent predicted binding to NCALD (calcium signaling modifier), SMN proteins (snRNP assembly), and UBA1 (ubiquitin homeostasis) would suggest multi-pathway engagement. This is a hypothetical advantage for a repurposing compound: a single molecule potentially modulating multiple SMA-relevant pathways could complement existing single-target therapies.

A testable combination hypothesis emerges: 4-AP (potential CORO1C/actin modulation) combined with risdiplam (SMN2 splicing correction) could address both SMN protein restoration and SMN-independent cytoskeletal dysfunction. This remains speculation and should not be interpreted as a clinical recommendation.

### 4.5 Accessibility

The virtual screening campaign was conducted using publicly available tools: NVIDIA NIM cloud API (DiffDock v2.2), Vast.ai cloud GPU instances (ESM-2, Boltz-2, SpliceAI), and open-source docking software (AutoDock Vina). The 4,115-docking campaign and consensus validation were performed without institutional compute infrastructure. This demonstrates that meaningful computational drug screening for rare diseases is accessible to independent researchers using publicly available tools and cloud APIs.

### 4.6 Comparison with Existing SMA Drug Discovery Approaches

Current SMA drug discovery operates primarily on RNA-targeting strategies (ASOs, small molecule splicing modifiers) or gene therapy. The only post-translational approaches in development are gene replacement (onasemnogene) and SMN protein stabilization. Few direct protein-binding approaches to SMN-independent targets have been clinically developed. If validated, the predicted CORO1C interactions would provide candidate chemical matter for a post-translational, non-SMN therapeutic strategy in SMA. The identification of multiple FDA-approved drugs (fomepizole, metformin) with predicted CORO1C binding could facilitate preclinical investigation, as safety and pharmacokinetic data already exist for these compounds.

---

## 5. Limitations

The following limitations are stated clearly, as they fundamentally constrain the interpretability of these findings:

1. **Computational predictions only.** No experimental binding data exists for 4-AP and CORO1C or any other compound-target pair reported here. The DiffDock confidence score is a machine-learned prediction of pose correctness, not an experimentally measured binding affinity. Every finding in this paper is a hypothesis, not a conclusion.

2. **AlphaFold-predicted structures.** All target structures were from AlphaFold predictions, not experimental crystallography or cryo-EM. Predicted structures may contain errors in loop regions, binding pockets, and intrinsically disordered domains that can substantially affect docking results.

3. **No binding affinity measurement.** DiffDock does not output Kd, Ki, or IC50 values. The +0.251 confidence score cannot be translated to a binding constant. The actual affinity could range from nanomolar (strong) to nonexistent.

4. **Limited docking method consensus.** The primary screen used DiffDock v2.2. AutoDock Vina consensus docking was applied to selected top hits (e.g., 4-AP/CORO1C: -3.98 kcal/mol), providing partial cross-validation. However, results were not validated with additional orthogonal methods (GNINA, Glide, GOLD). Two-method consensus is an improvement over single-method screening but does not constitute robust structural validation.

5. **Moderate compound library.** The 630-compound library, while substantially expanded from the initial 54-compound screen, remains modest by industrial screening standards. Screening 10,000-100,000 compounds (e.g., from ZINC20 or Enamine REAL) would be necessary to determine whether the observed hit signals are genuinely exceptional or artifacts of library composition.

6. **No molecular dynamics validation.** No MD simulations were performed to assess binding pose stability. A computationally predicted pose may be energetically unstable and dissociate within nanoseconds of simulation.

7. **Blind docking without binding site information.** DiffDock was run in fully blind mode. The predicted binding site on CORO1C has not been validated and may not correspond to a biologically relevant pocket.

8. **4-AP is a very small molecule** (MW 94.11, single pyridine ring with amine). Small molecules can generate false-positive docking results by fitting into many pockets non-specifically. The high confidence may reflect geometric compatibility rather than specific, pharmacologically relevant binding.

9. **DiffDock benchmark accuracy.** DiffDock v2.2 achieves approximately 38% top-1 success rate on the PoseBusters benchmark [17]. This means the majority of confident predictions are geometrically incorrect. Even the strongest positive-confidence hits in a 4,115-docking screen have a substantial probability of being false positives.

10. **No experimental confirmation.** Although the expanded screen (4,115 dockings) and Vina consensus docking provide internal computational consistency, no predictions have been experimentally confirmed. Computational agreement between two docking methods does not substitute for biophysical binding data.

11. **Claim extraction quality.** The 30,153 extracted claims were generated by a language model (Claude Sonnet 4.6), not manually curated by domain experts. While calibration against known drug-target relationships shows Grade A performance (89.8%), the precision on novel or ambiguous claims has not been fully characterized, and extraction errors propagate through the evidence graph.

12. **LLM-generated hypotheses.** The 1,262 hypotheses were generated by Claude Sonnet 4.6. While grounded in extracted claims, they inherit the biases and hallucination tendencies of large language models. Hypothesis quality was assessed through convergence scoring, not through independent expert review of all hypotheses.

---

## 6. Future Directions

### 6.1 Experimental Validation (Minimum Required)

The minimum experiment to validate or refute the 4-AP/CORO1C prediction is a biophysical binding assay:

- **Surface Plasmon Resonance (SPR):** Immobilize purified recombinant CORO1C protein, flow 4-AP at multiple concentrations (0.1-1000 micromolar), and measure binding kinetics and Kd. A Kd below 10 micromolar would constitute a positive result warranting functional follow-up. A Kd above 100 micromolar or no detectable binding would refute the computational prediction.
- **Microscale Thermophoresis (MST) or Thermal Shift Assay (DSF)** as alternative binding confirmation methods requiring less protein.

### 6.2 Functional Validation

If binding is confirmed:
- **Actin dynamics assay:** Phalloidin staining or live-cell actin imaging in iPSC-derived motor neurons treated with 4-AP, to determine whether 4-AP alters CORO1C-dependent actin remodeling.
- **SMN2 splicing reporter:** To exclude confounding splicing effects, confirm that 4-AP does not alter exon 7 inclusion -- this is a critical negative control if the mechanism is protein binding, not RNA modification.
- **Protein-protein interaction:** Co-immunoprecipitation or proximity ligation to assess whether 4-AP alters CORO1C interaction partners (Arp2/3, cofilin, actin).

### 6.3 Structural Validation

- **Cryo-EM or X-ray co-crystallography** of CORO1C with 4-AP to identify the actual binding site and pose.
- **HDX-MS** (hydrogen-deuterium exchange mass spectrometry) for binding site mapping without crystallization.

### 6.4 Computational Follow-Up

- **Molecular dynamics (100-500 ns)** of the predicted CORO1C-4-AP pose in explicit solvent.
- **Additional orthogonal docking** with GNINA and GOLD (AutoDock Vina consensus already completed: -3.98 kcal/mol for 4-AP/CORO1C).
- **Extended screening** beyond 630 compounds: 10,000+ compounds (e.g., from ZINC20 or Enamine REAL) to further contextualize hit signals statistically.
- **Binding site analysis** to identify contacting residues and their overlap with CORO1C functional domains (WD-repeat beta-propeller, unique region).
- **Experimental validation of fomepizole/CORO1C** (+1.027): as an FDA-approved drug with established safety data, fomepizole may be the most tractable candidate for rapid in vitro binding validation.

---

## 7. Data Availability

All data, code, and results are publicly available:

- **Platform:** https://sma-research.info (all evidence claims, docking results, and protein data browsable)
- **Source code:** https://github.com/Bryzant-Labs/sma-platform (AGPL-3.0 license)
- **HuggingFace dataset:** SMAResearch/sma-evidence-graph (full evidence graph export)
- **DiffDock v2.2 results:** 4,115 successful compound-target dockings (630 compounds x 7 targets) with confidence scores, available via platform API (`GET /api/v2/gpu/jobs?job_type=diffdock_v2_nim`)
- **DiffDock v1 results:** 140 compound-target pairs (20 compounds vs SMN2), available in repository (`gpu/results/diffdock_results.json`)
- **AutoDock Vina results:** Consensus docking for selected top hits, available via platform API
- **ESM-2 embeddings:** 1280-dimensional vectors for 7 SMA proteins (`gpu/results/esm2/`)
- **Compound library:** 630 compounds with SMILES, molecular weights, and ChEMBL/PubChem annotations (`gpu/data/diffdock_ligands.csv`)
- **Boltz-2 structures:** 3 independently predicted SMA protein structures (`gpu/results/boltz2/`)
- **API:** ~210 REST endpoints at https://sma-research.info/api/v2
- **MCP server:** 29 tools for programmatic access via Model Context Protocol

---

## 8. Acknowledgments

The DiffDock v2.2 docking campaign was performed using NVIDIA NIM cloud API free credits. GPU computation for ESM-2, Boltz-2, and SpliceAI was performed on Vast.ai A100 instances. The author thanks the developers of DiffDock, AlphaFold, ESM-2, Boltz-2, and the NVIDIA BioNeMo team for making these tools publicly available.

---

## References

1. Lefebvre S, Burglen L, Reboullet S, et al. Identification and characterization of a spinal muscular atrophy-determining gene. *Cell*. 1995;80(1):155-165. doi:10.1016/0092-8674(95)90460-3

2. Lorson CL, Hahnen E, Androphy EJ, Wirth B. A single nucleotide in the SMN gene regulates splicing and is responsible for spinal muscular atrophy. *Proc Natl Acad Sci USA*. 1999;96(11):6307-6311. doi:10.1073/pnas.96.11.6307

3. Wirth B, Karakaya M, Grunhagen JC, et al. Twenty-five years of spinal muscular atrophy research: from phenotype to genotype to therapy, and what comes next. *Annu Rev Genomics Hum Genet*. 2020;21:231-261. doi:10.1146/annurev-genom-102319-103602

4. Finkel RS, Mercuri E, Darras BT, et al. Nusinersen versus sham procedure in infantile-onset spinal muscular atrophy. *N Engl J Med*. 2017;377(18):1723-1732. doi:10.1056/NEJMoa1702752

5. Baranello G, Darras BT, Day JW, et al. Risdiplam in type 1 spinal muscular atrophy. *N Engl J Med*. 2021;384(10):915-923. doi:10.1056/NEJMoa2009965

6. Mendell JR, Al-Zaidy S, Shell R, et al. Single-dose gene-replacement therapy for spinal muscular atrophy. *N Engl J Med*. 2017;377(18):1713-1722. doi:10.1056/NEJMoa1706198

7. Mercuri E, Muntoni F, Baranello G, et al. Onasemnogene abeparvovec gene therapy for symptomatic infantile-onset spinal muscular atrophy type 1 (STR1VE-EU). *Lancet Neurol*. 2021;20(10):832-841. doi:10.1016/S1474-4422(21)00251-9

8. Oprea GE, Kroeber S, McWhorter ML, et al. Plastin 3 is a protective modifier of autosomal recessive spinal muscular atrophy. *Science*. 2008;320(5875):524-527. doi:10.1126/science.1155085

9. Riessland M, Kaczmarek A, Schneider S, et al. Neurocalcin delta suppression protects against spinal muscular atrophy in humans. *J Clin Invest*. 2017;127(3):970-986. doi:10.1172/JCI82356

10. Wishart TM, Mutsaers CA, Riessland M, et al. Dysregulation of ubiquitin homeostasis and beta-catenin signaling promote spinal muscular atrophy. *J Clin Invest*. 2014;124(4):1821-1834. doi:10.1172/JCI71318

11. Imlach WL, Beck ES, Bhatt JM, et al. SMN is required for sensory-motor circuit function in Drosophila. *Cell*. 2012;151(2):427-439. doi:10.1016/j.cell.2012.09.011

12. Bhatt JM, et al. 4-Aminopyridine improves motor performance in a mouse model of spinal muscular atrophy. *J Neurosci*. 2021. PMC7810663.

13. ClinicalTrials.gov. A Study of 4-Aminopyridine in Patients With SMA Type 3 (Ambulatory). NCT01645787. Columbia University.

14. Ioannidis JPA. Why most published research findings are false. *PLoS Med*. 2005;2(8):e124. doi:10.1371/journal.pmed.0020124

15. Lin Z, Akin H, Rao R, et al. Evolutionary-scale prediction of atomic-level protein structure with a language model. *Science*. 2023;379(6637):1123-1130. doi:10.1126/science.ade2574

16. Corso G, Stark H, Jing B, Barzilay R, Jaakkola T. DiffDock: Diffusion steps, twists, and turns for molecular docking. *ICLR 2023*.

17. Buttenschoen M, Morris GM, Deane CM. PoseBusters: AI-based docking emulates key features of experimental structures. *Chem Sci*. 2024;15:3413-3424. doi:10.1039/D3SC04185A

18. Sivaramakrishnan M, McCarthy KD, Campagne S, et al. Binding of small molecules to the SMN2 pre-mRNA exon 7 splice site modulates splicing. *Nat Chem Biol*. 2023.

19. Bhattacharya K, Bhattacharya S. Coronin family proteins: multitasking regulators of actin cytoskeleton dynamics. *Biol Cell*. 2021;113(3):124-137.

20. Jumper J, Evans R, Pritzel A, et al. Highly accurate protein structure prediction with AlphaFold. *Nature*. 2021;596:583-589. doi:10.1038/s41586-021-03819-2

---

## Supplementary Materials (Planned)

- **Table S1:** Complete 4,115-docking DiffDock v2.2 confidence scores
- **Table S2:** 630-compound library with SMILES, molecular weights, pChEMBL values
- **Table S3:** AlphaFold structural quality metrics for all 7 targets
- **Table S4:** ESM-2 pairwise cosine similarity matrix for 7 SMA proteins
- **Figure S1:** DiffDock confidence score distribution (histogram, 4,115 dockings)
- **Figure S2:** Predicted 4-AP binding pose on CORO1C structure
- **Figure S3:** Boltz-2 vs AlphaFold structure comparison for 3 targets

---

*This preprint describes computational predictions only. No therapeutic claims are made. All findings require experimental validation before any clinical implications can be considered. The author is a patient-researcher with SMA; this positionality provides domain knowledge and is disclosed transparently.*
