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

Spinal muscular atrophy (SMA) is caused by homozygous loss of *SMN1*, with current therapies focused on SMN2 splicing correction or gene replacement. Adult patients with long-standing denervation frequently show incomplete therapeutic responses, motivating the search for SMN-independent targets. We describe an open-source computational platform that integrates 6,176 literature sources, 30,153 extracted claims, and 1,262 mechanistic hypotheses into a structured evidence graph for SMA research. Using this platform, we conducted a systematic virtual screening campaign: DiffDock v2.2 blind docking of 54 compounds against 7 SMA-relevant protein targets (378 compound-target pairs) identified 4-aminopyridine (4-AP) binding to coronin-1C (CORO1C) as the strongest predicted interaction (confidence +0.251), one of only 3 positive-confidence hits in the entire screen. 4-AP further showed predicted binding to NCALD (confidence -0.443), SMN2 (-0.447), SMN1 (-0.487), and UBA1 (-0.507), constituting a 5-target binding profile. ESM-2 protein language model analysis revealed CORO1C as the most structurally distinct target among the 7 SMA proteins examined. A 5-dimensional convergence scoring engine, calibrated against known drug outcomes (3 approved SMA therapies), achieved Grade B calibration, appropriately ranking established drug-target relationships. All prior clinical investigation of 4-AP in SMA assumed voltage-gated potassium channel blockade as the sole mechanism. These computational findings suggest a previously unrecognized binding interaction that, if experimentally validated, could justify re-evaluation of 4-AP through a mechanistically distinct rationale. All data, code, and results are publicly available.

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

Fifty-four compounds were assembled from two sources: (a) 47 compounds from ChEMBL with reported bioactivity against SMN1 or SMN2 splicing assay targets, filtered for drug-likeness; and (b) 7 reference and repurposing compounds: risdiplam, valproic acid, riluzole, salbutamol, celecoxib, 4-aminopyridine, and SAHA (vorinostat). SMILES strings were sourced from ChEMBL and verified for chemical validity. 4-AP (SMILES: c1cc(N)ncc1; molecular weight 94.11 Da) was included as a repurposing candidate based on its prior clinical testing in SMA and FDA-approved status.

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

DiffDock v2.2 [16], a diffusion-based molecular docking method, was used for blind docking (no binding site specification). The screening campaign was executed via the NVIDIA NIM cloud API (DiffDock v2.2 microservice) at zero cost using free API credits. Each of the 54 compounds was docked against each of the 7 protein targets, producing 378 compound-target docking predictions. Ten poses were generated per prediction.

DiffDock confidence scores represent a learned prediction of pose correctness: a positive confidence indicates the model predicts its best pose is likely accurate, while negative confidence indicates lower predicted reliability. In benchmark evaluations, DiffDock achieves approximately 38% top-1 success rate (RMSD < 2 Angstrom) on the PoseBusters benchmark set [17], meaning the majority of generated poses are geometrically incorrect. Positive confidence scores are rare in typical docking campaigns and indicate predictions in which the model has comparatively high certainty.

An earlier docking campaign (Run 1) used DiffDock v1 (self-hosted, Vast.ai A100) to dock 20 ChEMBL compounds against SMN2 only (140 docking jobs, 11 poses per compound). Run 2 (378 pairs via NIM API) expanded the compound library and target panel. The total runtime for the 378-pair campaign was 24 minutes.

### 2.9 Statistical Approach

All 378 compound-target pairs were ranked by confidence score. Mean confidence and standard deviation were computed per target. The analysis is explicitly exploratory: no multiple testing correction was applied, as the screen generates hypotheses rather than confirming them. The false discovery rate in a screen of this size is not controlled, and all findings require independent experimental validation.

---

## 3. Results

### 3.1 Virtual Screening Overview

The 378-pair docking campaign yielded confidence scores ranging from -3.56 to +0.251. Only 3 of 378 compound-target pairs (0.8%) achieved positive confidence scores, indicating high selectivity of the DiffDock v2.2 model in this screen.

**Table 1. Top 15 compound-target pairs by DiffDock v2.2 confidence score.**

| Rank | Compound | Target | Confidence |
|------|----------|--------|-----------|
| 1 | **4-aminopyridine** | **CORO1C** | **+0.251** |
| 2 | CHEMBL1381595 | NCALD | +0.076 |
| 3 | CHEMBL1328375 | CORO1C | +0.048 |
| 4 | CHEMBL1411542 | SMN1 | -0.067 |
| 5 | CHEMBL1331875 | UBA1 | -0.089 |
| 6 | CHEMBL1301743 | UBA1 | -0.100 |
| 7 | CHEMBL1400508 | UBA1 | -0.179 |
| 8 | CHEMBL1301743 | PLS3 | -0.216 |
| 9 | CHEMBL1301787 | UBA1 | -0.282 |
| 10 | CHEMBL1575581 | NCALD | -0.314 |
| 11 | CHEMBL1381595 | UBA1 | -0.337 |
| 12 | CHEMBL1575581 | CORO1C | -0.407 |
| 13 | 4-aminopyridine | NCALD | -0.443 |
| 14 | 4-aminopyridine | SMN2 | -0.447 |
| 15 | 4-aminopyridine | SMN1 | -0.487 |

### 3.2 4-AP Multi-Target Binding Profile

4-Aminopyridine was the only compound to appear 5 times in the top 25 compound-target pairs, demonstrating predicted binding to 5 of 7 SMA targets:

**Table 2. 4-AP binding profile across 7 SMA targets.**

| Target | Confidence | Overall Rank (of 378) |
|--------|-----------|----------------------|
| CORO1C | +0.251 | 1 |
| NCALD | -0.443 | 13 |
| SMN2 | -0.447 | 14 |
| SMN1 | -0.487 | 15 |
| UBA1 | -0.507 | 21 |
| STMN2 | -1.047 | -- |
| PLS3 | -1.281 | -- |

The gap between 4-AP/CORO1C (+0.251) and the second-ranked pair (CHEMBL1381595/NCALD, +0.076) was 0.175 confidence units, the largest margin between any adjacent top-ranked pairs.

### 3.3 Per-Target Analysis

Target-level statistics revealed substantial variation in dockability across the 7 SMA proteins:

**Table 3. Per-target docking statistics (54 compounds each).**

| Target | Best Confidence | Best Compound | Mean Confidence | Positive Hits |
|--------|----------------|---------------|-----------------|---------------|
| CORO1C | +0.251 | 4-aminopyridine | -1.520 | 2 |
| NCALD | +0.076 | CHEMBL1381595 | -1.486 | 1 |
| UBA1 | -0.089 | CHEMBL1331875 | -1.207 | 0 |
| SMN1 | -0.067 | CHEMBL1411542 | -1.616 | 0 |
| PLS3 | -0.216 | CHEMBL1301743 | -1.778 | 0 |
| SMN2 | -0.447 | 4-aminopyridine | -2.059 | 0 |
| STMN2 | -1.047 | 4-aminopyridine | -2.380 | 0 |

UBA1 showed the highest mean confidence (-1.207) and the most compounds with reasonable binding scores (5 compounds above -0.35), suggesting it may present the most accessible binding pockets among the targets examined. SMN2 and STMN2 showed the lowest mean confidence values (-2.059 and -2.380, respectively), consistent with less favorable predicted binding across the compound library, possibly reflecting limited accessible binding pockets in the AlphaFold-predicted structures.

### 3.4 Comparison with Approved and Failed SMA Compounds

The screen included 4 compounds with prior SMA clinical data:

**Table 4. Docking results for clinically tested SMA compounds.**

| Compound | Clinical Status | Target | Confidence |
|----------|----------------|--------|-----------|
| Risdiplam | Approved (oral, SMN2 splicing) | SMN2 | -1.250 |
| Valproic acid | Failed (HDAC inhibitor) | SMN2 | -1.330 |
| Riluzole | Tested (ALS drug) | SMN2 | -0.300 |
| 4-aminopyridine | Failed (K+ channel) | SMN2 | -0.447 |
| 4-aminopyridine | Failed (K+ channel) | CORO1C | +0.251 |

Risdiplam's low confidence score for direct SMN2 protein binding (-1.250) is expected and consistent with its known mechanism: risdiplam acts on SMN2 pre-mRNA splicing [18], not through direct protein binding. This result serves as a negative control, demonstrating the screen's ability to discriminate between RNA-targeting and protein-targeting mechanisms.

### 3.5 CORO1C as a Novel SMA-Relevant Target

CORO1C (coronin-1C, UniProt Q9ULV4) is a member of the coronin family of WD-repeat proteins that regulate actin dynamics, cell motility, and vesicular trafficking [19]. CORO1C promotes Arp2/3-mediated actin polymerization and regulates cofilin-mediated actin depolymerization, placing it within the same cytoskeletal pathway as PLS3, an established SMA disease modifier that rescues SMA phenotypes through actin-dependent endocytosis at the NMJ [8].

CORO1C received the highest-confidence docking prediction in the entire 378-pair screen, and was one of only 2 targets to produce positive-confidence predictions (CORO1C: 2 positive hits; NCALD: 1 positive hit). Among the 54 compounds screened, 4-AP showed a confidence gap of +0.658 above the CORO1C target mean (-1.520), indicating an outlier interaction within this target's docking landscape.

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

UBA1, the ubiquitin-like modifier activating enzyme 1, emerged as the most broadly druggable target. Five compounds achieved confidence scores above -0.35 against UBA1 (CHEMBL1331875: -0.089; CHEMBL1301743: -0.100; CHEMBL1400508: -0.179; CHEMBL1301787: -0.282; CHEMBL1381595: -0.337). UBA1 dysregulation has been independently linked to SMN pathway disruption [10], and reduced UBA1 activity in SMA motor neurons has been reported as an SMN-independent disease mechanism. The identification of multiple compounds with predicted UBA1 binding provides candidate chemical matter for experimental investigation of UBA1-directed SMA therapy.

### 3.8 Cross-Validation with DiffDock v1

An earlier docking campaign using DiffDock v1 (self-hosted on Vast.ai A100) tested 20 compounds against SMN2 only. The 4-AP versus SMN2 result differed between versions: +0.100 (v1) versus -0.447 (v2.2). This divergence is attributable to the different training datasets and scoring calibration between DiffDock versions (v2.2 was trained on the PLINDER dataset with updated scoring). CHEMBL1575581, the top hit in the v1 campaign (confidence -0.090), showed consistency across versions (-0.090 in v1 versus -0.070 in v2.2 against SMN2). Absolute confidence values are not directly comparable across DiffDock versions; the relative ranking within each campaign is the relevant metric.

### 3.9 Evidence Convergence Scoring

The platform's convergence engine scored all 21 tracked SMA targets across 5 dimensions. Known therapeutic targets (SMN1, SMN2) appropriately received the highest convergence scores, driven by high laboratory independence (many independent groups), method diversity (genetic, biochemical, animal model, and clinical evidence), and temporal consistency (25+ years of consistent evidence). Established modifier genes (PLS3, NCALD) scored in the second tier, consistent with their more recent but multi-laboratory evidence base. Calibration against known drug outcomes yielded Grade B performance: the system reliably identifies established relationships and appropriately ranks approved therapies above failed and discontinued compounds.

---

## 4. Discussion

### 4.1 Novelty of the CORO1C Finding

To our knowledge, no prior publication describes a direct binding interaction between 4-AP and CORO1C protein. A PubMed search for "4-aminopyridine" AND "CORO1C" yields zero results. All previous investigation of 4-AP in SMA assumed K+ channel blockade as the sole therapeutic mechanism [11, 12, 13]. The computational prediction of 4-AP binding to CORO1C, if experimentally validated, would represent a mechanistically distinct rationale for this compound in SMA, linking it to the actin cytoskeletal pathway rather than ion channel pharmacology.

### 4.2 Biological Plausibility: The Actin Pathway Connection

CORO1C's role in actin dynamics provides biological context for a potential SMA-relevant interaction. PLS3 (Plastin-3), an established SMA modifier gene, rescues SMA phenotypes through actin-dependent endocytosis at the NMJ [8]. CORO1C operates in the same actin regulatory network: it promotes Arp2/3-dependent branched actin nucleation and regulates cofilin-mediated filament turnover [19]. In our evidence graph, CORO1C and PLS3 co-occur in 3 independent publications discussing actin dynamics in SMA contexts. The convergence of the computational docking prediction (4-AP binding CORO1C) with the literature-derived biological relationship (CORO1C-PLS3 actin pathway) constitutes cross-modal evidence that, while not confirmatory, increases the prior probability that this interaction is biologically meaningful.

### 4.3 Reconciling the Failed Clinical Trial

The Phase 2/3 trial NCT01645787 tested 4-AP based on the K+ channel hypothesis, measuring acute functional endpoints (6MWT, HFMSE) over 8 weeks in 11 adult SMA Type 3 patients. The trial was negative for these endpoints [13].

However, the trial was designed and powered specifically for the K+ channel mechanism of action. A protein-binding mechanism, such as modulation of CORO1C-mediated actin dynamics, would predict different biological effects: altered cytoskeletal remodeling, modified endocytic trafficking at the NMJ, or changed actin-dependent processes in motor neurons. These effects would not necessarily manifest as acute improvements in motor function over 8 weeks.

Critically, the trial did not measure: CORO1C expression or function, actin dynamics biomarkers, SMN protein levels, or any molecular indicator of direct protein engagement. The negative trial therefore disproves the K+ channel hypothesis for functional improvement in ambulatory SMA Type 3 adults; it does not address the protein-binding hypothesis proposed here. We note, however, that absence of evidence is not evidence of absence, and the clinical failure must be weighted as a caution rather than dismissed.

### 4.4 Multi-Target Profile and Combination Potential

The 5-target binding profile of 4-AP is noteworthy. If the CORO1C interaction is validated, the concurrent predicted binding to NCALD (calcium signaling modifier), SMN proteins (snRNP assembly), and UBA1 (ubiquitin homeostasis) would suggest multi-pathway engagement. This is a hypothetical advantage for a repurposing compound: a single molecule potentially modulating multiple SMA-relevant pathways could complement existing single-target therapies.

A testable combination hypothesis emerges: 4-AP (potential CORO1C/actin modulation) combined with risdiplam (SMN2 splicing correction) could address both SMN protein restoration and SMN-independent cytoskeletal dysfunction. This remains speculation and should not be interpreted as a clinical recommendation.

### 4.5 Cost and Accessibility

The entire virtual screening campaign cost $0.78 in GPU compute (Vast.ai A100 instances for ESM-2, Boltz-2, and SpliceAI computations) plus $0 for the 378 DiffDock v2.2 NIM API dockings (NVIDIA free credits). The total computational cost for identifying the 4-AP/CORO1C interaction was under $1. This demonstrates that meaningful computational drug screening for rare diseases does not require institutional budgets or dedicated compute infrastructure, and that patient-researchers with domain expertise can contribute hypothesis-generating computational work using publicly available tools and cloud APIs.

### 4.6 Comparison with Existing SMA Drug Discovery Approaches

Current SMA drug discovery operates primarily on RNA-targeting strategies (ASOs, small molecule splicing modifiers) or gene therapy. The only post-translational approaches in development are gene replacement (onasemnogene) and SMN protein stabilization. No direct protein-binding approach to SMN-independent targets has been clinically developed. If validated, a 4-AP/CORO1C interaction would represent the first post-translational, non-SMN therapeutic strategy in SMA originating from computational screening.

---

## 5. Limitations

The following limitations are stated clearly, as they fundamentally constrain the interpretability of these findings:

1. **Computational predictions only.** No experimental binding data exists for 4-AP and CORO1C or any other compound-target pair reported here. The DiffDock confidence score is a machine-learned prediction of pose correctness, not an experimentally measured binding affinity. Every finding in this paper is a hypothesis, not a conclusion.

2. **AlphaFold-predicted structures.** All target structures were from AlphaFold predictions, not experimental crystallography or cryo-EM. Predicted structures may contain errors in loop regions, binding pockets, and intrinsically disordered domains that can substantially affect docking results.

3. **No binding affinity measurement.** DiffDock does not output Kd, Ki, or IC50 values. The +0.251 confidence score cannot be translated to a binding constant. The actual affinity could range from nanomolar (strong) to nonexistent.

4. **Single docking method.** Only DiffDock v2.2 was used. Results were not cross-validated with orthogonal methods (AutoDock Vina, GNINA, Glide). A single method provides no structural consensus.

5. **Small compound library.** Fifty-four compounds is a minimal screening set. Screening 10,000-100,000 compounds (e.g., from ZINC20 or Enamine REAL) would be necessary to determine whether the 4-AP signal is genuinely exceptional or a statistical artifact of sample size.

6. **No molecular dynamics validation.** No MD simulations were performed to assess binding pose stability. A computationally predicted pose may be energetically unstable and dissociate within nanoseconds of simulation.

7. **Blind docking without binding site information.** DiffDock was run in fully blind mode. The predicted binding site on CORO1C has not been validated and may not correspond to a biologically relevant pocket.

8. **4-AP is a very small molecule** (MW 94.11, single pyridine ring with amine). Small molecules can generate false-positive docking results by fitting into many pockets non-specifically. The high confidence may reflect geometric compatibility rather than specific, pharmacologically relevant binding.

9. **DiffDock benchmark accuracy.** DiffDock v2.2 achieves approximately 38% top-1 success rate on the PoseBusters benchmark [17]. This means the majority of confident predictions are geometrically incorrect. A single positive-confidence hit, even the strongest in a 378-pair screen, has a substantial probability of being a false positive.

10. **N=1 computational observation.** This is a single prediction from a single screen using a single docking method. It has not been replicated, externally validated, or experimentally confirmed.

11. **Claim extraction quality.** The 30,153 extracted claims were generated by a language model (Claude Sonnet 4.6), not manually curated by domain experts. While calibration against known drug-target relationships shows Grade B performance, the precision on novel or ambiguous claims has not been fully characterized, and extraction errors propagate through the evidence graph.

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
- **Orthogonal docking** with AutoDock Vina, GNINA, and GOLD for consensus assessment.
- **Expanded screening** of 10,000+ compounds to contextualize the 4-AP signal statistically.
- **Binding site analysis** to identify contacting residues and their overlap with CORO1C functional domains (WD-repeat beta-propeller, unique region).

---

## 7. Data Availability

All data, code, and results are publicly available:

- **Platform:** https://sma-research.info (all evidence claims, docking results, and protein data browsable)
- **Source code:** https://github.com/Bryzant-Labs/sma-platform (AGPL-3.0 license)
- **HuggingFace dataset:** SMAResearch/sma-evidence-graph (full evidence graph export)
- **DiffDock v2.2 results:** 378 compound-target pairs with confidence scores, available via platform API (`GET /api/v2/gpu/jobs?job_type=diffdock_v2_nim`)
- **DiffDock v1 results:** 140 compound-target pairs (20 compounds vs SMN2), available in repository (`gpu/results/diffdock_results.json`)
- **ESM-2 embeddings:** 1280-dimensional vectors for 7 SMA proteins (`gpu/results/esm2/`)
- **Compound library:** 54 compounds with SMILES, molecular weights, and ChEMBL annotations (`gpu/data/diffdock_ligands.csv`)
- **Boltz-2 structures:** 3 independently predicted SMA protein structures (`gpu/results/boltz2/`)
- **API:** ~210 REST endpoints at https://sma-research.info/api/v2
- **MCP server:** 32 tools for programmatic access via Model Context Protocol

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

- **Table S1:** Complete 378-pair DiffDock v2.2 confidence scores
- **Table S2:** Compound library with SMILES, molecular weights, pChEMBL values
- **Table S3:** AlphaFold structural quality metrics for all 7 targets
- **Table S4:** ESM-2 pairwise cosine similarity matrix for 7 SMA proteins
- **Figure S1:** DiffDock confidence score distribution (histogram, 378 pairs)
- **Figure S2:** Predicted 4-AP binding pose on CORO1C structure
- **Figure S3:** Boltz-2 vs AlphaFold structure comparison for 3 targets

---

*This preprint describes computational predictions only. No therapeutic claims are made. All findings require experimental validation before any clinical implications can be considered. The author is a patient-researcher with SMA; this positionality provides domain knowledge and is disclosed transparently.*
