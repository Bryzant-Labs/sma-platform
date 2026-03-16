# SMA Research Platform — Scientific Advisory Pack

*For potential PI collaborators | March 2026*

---

## 1. What the Platform Does

The SMA Research Platform is an open-source, AI-driven evidence synthesis system purpose-built for spinal muscular atrophy research. It aggregates, structures, and cross-references the SMA literature at a scale no individual researcher can achieve manually.

### Current Data Scope

| Metric | Count |
|--------|-------|
| Extracted claims | 25,054 |
| Source papers, patents, and trials | 5,216 |
| AI-generated hypotheses (Claude Sonnet 4.6) | 515 |
| Tracked therapeutic targets | 21 |
| Tracked drug candidates | 16 |
| Clinical trials indexed | 449 |

### Core Capabilities

- **Cross-paper synthesis.** The platform identifies connections across papers that no single researcher reads together. Claims from independent sources are linked by target, pathway, and mechanism, surfacing convergent evidence that would otherwise remain siloed across subfields.

- **Bayesian evidence convergence.** Each claim contributes to a posterior probability distribution for its associated hypothesis. The model quantifies how much independent evidence supports or contradicts a given mechanistic relationship, with credible intervals rather than point estimates.

- **Source quality scoring.** Every paper is assessed across five dimensions — methodology rigor, sample size, reproducibility indicators, journal impact, and recency — producing a composite quality weight that modulates its influence on hypothesis scores.

- **Contradiction detection.** The system automatically flags conflicting evidence between papers, surfacing disagreements that might otherwise be missed in narrative reviews.

- **GPU-accelerated structural biology.** Integrated pipelines for DiffDock (molecular docking), Boltz-2 (structure prediction), ESM-2 (protein language model embeddings), and SpliceAI (splice site prediction). These run on-demand via cloud GPU infrastructure (Vast.ai / dstack).

---

## 2. Where the Platform Is Reliable

We want to be specific about what works and how well.

### Claim Extraction

We built an evaluation framework that benchmarks extracted claims against known ground truth (approved drug mechanisms, established pathway relationships). Current calibration is approximately **Grade B** — the system reliably identifies established relationships and rarely fabricates connections, but precision on novel or ambiguous claims has not been fully characterized.

### DiffDock Molecular Docking

- **518 docking predictions** completed across two DiffDock versions (v1 and v2.2).
- **3 positive-confidence binding predictions** confirmed across both model versions, providing cross-validation.
- Docking poses are geometrically plausible and consistent with known binding site residues where crystallographic data exists.

### Evidence Convergence

The Bayesian convergence model produces posterior distributions with credible intervals for each target-mechanism relationship. When multiple independent papers report consistent findings, the model appropriately increases confidence. When evidence conflicts, it appropriately widens uncertainty.

### Contradiction Detection

The system identifies papers that report opposing conclusions about the same target or mechanism. This is particularly valuable in the SMA modifier gene literature, where conflicting results across model organisms are common.

---

## 3. Where the Platform Is Uncertain

These are real limitations. We list them because any collaborator should understand exactly what this system cannot yet do.

- **Claim extraction precision is not fully benchmarked.** We lack gold-standard human-annotated labels for a sufficiently large subset of claims. The Grade B calibration is based on known drug-target pairs, not a comprehensive inter-annotator agreement study.

- **DiffDock confidence scores are not binding affinities.** A positive docking score indicates geometric complementarity, not thermodynamic binding. Confidence values do not correspond to Kd, Ki, or IC50 measurements. Computational prediction only.

- **Protein structures are predominantly AlphaFold-predicted, not experimentally determined.** Docking against predicted structures introduces additional uncertainty, particularly in flexible loop regions and allosteric sites.

- **Cross-paper synthesis is limited by claim-target linking quality.** Currently 29.5% of claims are linked to specific molecular targets. The remaining 70.5% contain useful information but are not yet integrated into the target-level evidence network.

- **No wet-lab validation of any computational prediction exists yet.** Every finding described in this document is computational. None have been confirmed by biochemical or cell-based assay.

- **The digital twin module is rule-based, not data-trained.** It simulates SMN pathway dynamics using published rate constants and logical rules. It has not been trained on or validated against real patient longitudinal data.

- **All hypothesis confidence scores are relative, not absolute probabilities.** A score of 0.72 means "substantially more evidence supports this than opposes it," not "72% chance of being true." These scores are useful for prioritization, not for clinical decision-making.

---

## 4. Three Proposed Collaborations

Each proposal specifies what we found computationally, what wet-lab validation is needed, what we provide, and realistic timelines.

### Collaboration 1: 4-AP Multi-Target Validation

*Relevant for: Wirth lab, Groen lab*

**Computational finding.** 4-Aminopyridine (4-AP), an approved K+ channel blocker, shows predicted binding to CORO1C (DiffDock confidence +0.251), as well as NCALD, SMN2, and SMN1. The CORO1C interaction is novel and potentially significant — CORO1C regulates actin dynamics in the same pathway as the known SMA modifier PLS3.

**Validation needed.**
- Surface plasmon resonance (SPR) binding assay for 4-AP against recombinant CORO1C
- Functional actin dynamics assay (phalloidin staining or live-cell actin imaging) in motor neurons with and without 4-AP treatment

**What we provide.**
- Complete computational docking data with predicted binding poses and residue contacts
- Full evidence synthesis linking CORO1C to the PLS3/actin modifier pathway
- Compound library recommendations for structure-activity follow-up

**Expected timeline.** 3-6 months for binding confirmation (SPR). An additional 2-3 months for functional assay if binding is confirmed.

---

### Collaboration 2: ASO Design Optimization

*Relevant for: Krainer lab*

**Computational finding.** The platform's ASO generator module designs antisense oligonucleotide candidates targeting established SMA splice regulatory elements — ISS-N1, ISS-N2, and the exon 7 ESS. Candidates are ranked by predicted melting temperature (Tm), GC content, blood-brain barrier permeability scores, and off-target hybridization risk.

**Validation needed.**
- Splicing reporter assay (SMN2 minigene) for the top 5 ranked ASO candidates
- RT-qPCR quantification of exon 7 inclusion efficiency

**What we provide.**
- Ranked ASO sequences with full predicted physicochemical properties
- Splice site predictions (SpliceAI) for each target region
- Comparative analysis against published nusinersen binding parameters

**Expected timeline.** 2-4 months for initial splicing screen. Reporter assay results would directly inform whether the computational ranking has predictive value.

---

### Collaboration 3: Organoid and NMJ Validation

*Relevant for: Gouti lab*

**Computational finding.** Cross-paper synthesis identified a mechanistic bridge between SMN1 function and NCALD-mediated calcium signaling. Five independent papers link NCALD to SMN2 modifier activity, converging on calcium-dependent endocytosis at the neuromuscular junction. The platform predicts that NCALD knockdown combined with partial SMN restoration (e.g., risdiplam) may produce synergistic rescue.

**Validation needed.**
- Test NCALD-ASO + nusinersen (or risdiplam) combination in NMJ-on-chip or organoid model
- Quantify NMJ formation, synaptic vesicle cycling, and motor neuron survival independently and in combination

**What we provide.**
- Full evidence synthesis with all source papers and claim lineage
- Hypothesis cards with Bayesian confidence scores and credible intervals
- Assay-ready experimental design with pre-specified go/no-go decision criteria

**Expected timeline.** 6-12 months for combination study in organoid or NMJ-on-chip system.

---

## 5. Three Ready-to-Test Hypotheses

Each hypothesis below includes the supporting evidence, a concrete experimental test, and a pre-specified go/no-go criterion.

### Hypothesis 1

**"4-AP rescues motor neuron function through CORO1C-mediated actin remodeling, independent of K+ channel blockade."**

| | |
|---|---|
| **Evidence** | DiffDock binding confidence +0.251 for 4-AP/CORO1C. CORO1C and PLS3 co-occur in 3 independent papers discussing actin dynamics in SMA. Actin pathway convergence across modifier gene literature. |
| **Experimental test** | SPR binding assay (4-AP vs. recombinant CORO1C) + phalloidin staining in iPSC-derived motor neurons +/- 4-AP treatment. |
| **Go/No-Go** | Kd < 10 uM = proceed to functional actin dynamics assay. Kd > 100 uM or no detectable binding = reject hypothesis. |

### Hypothesis 2

**"Combined NCALD knockdown + SMN restoration provides synergistic motor neuron rescue via calcium-dependent endocytosis."**

| | |
|---|---|
| **Evidence** | 5 papers linking NCALD to SMN2 modifier activity. Bayesian posterior probability 0.72 (credible interval 0.58-0.84). Convergent evidence on calcium-dependent endocytosis at the NMJ. |
| **Experimental test** | NCALD-ASO + risdiplam in SMA iPSC-derived motor neurons. Measure NMJ formation rate, synaptic vesicle recycling, and cell survival at 14 and 28 days. |
| **Go/No-Go** | >30% improvement in NMJ formation over risdiplam alone = proceed to in vivo combination study. <10% improvement = reject synergy hypothesis. |

### Hypothesis 3

**"UBA1 represents a druggable SMN-independent target with 5 candidate compounds identified."**

| | |
|---|---|
| **Evidence** | 7 papers linking UBA1 dysregulation to SMN pathway disruption. UBA1 activity is reduced in SMA motor neurons independent of SMN levels. 5 compounds show predicted binding to UBA1 active site via DiffDock. |
| **Experimental test** | UBA1 ubiquitin-conjugating activity assay with top candidate compound (CHEMBL1331875). Dose-response curve (0.01-100 uM). |
| **Go/No-Go** | IC50 < 1 uM = proceed to cell-based validation in SMA motor neurons. IC50 > 10 uM = deprioritize compound, test remaining 4 candidates. |

---

## Contact and Access

| | |
|---|---|
| **Platform** | [sma-platform.org](https://sma-platform.org) |
| **Source code** | GitHub (open source, MIT license) |
| **Contact** | Christian Fischer |

*Built by a researcher with SMA. Evidence-first. Open source.*
