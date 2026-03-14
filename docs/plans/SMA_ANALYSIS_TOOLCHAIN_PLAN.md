# SMA Analysis Toolchain Plan

## Objective

Set up the SMA research toolchain in the correct order:

1. robust target and fragility hypotheses
2. prioritization
3. molecule / CRISPR / AAV compute bursts

The central rule is simple:
- no expensive generation or screening before the biological hypothesis layer is stable

## Why This Order Matters

If the order is wrong:
- the system will generate huge candidate volumes against weak biology
- compute will amplify noise
- outputs will look impressive but remain unusable

If the order is correct:
- bad biological ideas are eliminated early
- compute is focused on narrowed, defensible target sets
- outputs become fundable, reviewable, and testable

## Phase 1: Robust Target And Fragility Hypotheses

### Goal

Build a biologically grounded, reproducible system that identifies:
- candidate leverage points
- fragile couplings
- pathway collapse patterns
- non-obvious but defensible target hypotheses

### Core Questions

- Which genes, proteins, and modules repeatedly converge across SMA-relevant evidence?
- Which signals survive context changes and dataset removal?
- Which findings are likely causal levers versus downstream markers?

### Required Tools

#### Data And Workflow

- Python 3.11+
- Postgres
- `SMA-UCM` bundle tooling
- DVC or equivalent artifact versioning
- Snakemake or Nextflow

#### Analysis

- pandas
- polars
- numpy
- scipy
- scikit-learn
- networkx
- igraph or graph-tool
- statsmodels
- pyarrow

#### Omics / Biology

- scanpy
- anndata
- seaborn / matplotlib / plotly
- gseapy
- Biopython

#### Source Connectors

- PubMed / Europe PMC ingestion
- ClinicalTrials.gov ingestion
- OpenAlex / Crossref metadata ingestion
- curated GEO / proteomics dataset importers

### Recommended Setup

#### Environment

- `sma-core` Python environment
- one Postgres database for canonical data
- one object/artifact store for raw and derived files

Suggested environment split:
- `env-core`
- `env-omics`
- `env-site`

#### Data Model

Use the canonical entities already defined:
- papers
- datasets
- trials
- genes
- proteins
- pathways
- targets
- claims
- evidence
- hypotheses

#### Pipelines To Implement First

1. source ingestion
2. canonical normalization
3. evidence scoring
4. signal extraction by dataset
5. fixed biological network projection
6. robustness tests
7. hypothesis card generation

### Inputs

- publicly available SMA RNA-seq / splicing / proteomics datasets
- disease modifier literature
- pathway / interaction references
- treatment-response and longitudinal data when available

### Outputs

- target candidates
- fragility modules
- pathway instability reports
- hypothesis cards with supporting evidence
- rejected hypotheses list

### Review Gates

Do not move to Phase 2 until:
- at least 20 to 50 serious hypothesis cards exist
- each card has explicit supporting evidence
- robustness tests are defined and reproducible
- obvious stratifiers are separated from intervention candidates

### Stop Criteria

Stop and fix the pipeline if:
- two runs on same inputs produce materially different rankings
- evidence links are missing
- dataset context is unclear
- pathway mappings are being learned from the same signals they explain

## Phase 2: Prioritization

### Goal

Reduce the Phase 1 hypothesis set to a small, defensible shortlist for downstream compute.

Target output:
- 5 to 15 high-conviction targets or intervention modules

### Core Questions

- Which candidates have the strongest cross-evidence convergence?
- Which candidates are mechanistically meaningful?
- Which candidates are plausible for drug, ASO, CRISPR, or AAV intervention?
- Which candidates have acceptable translational risk?

### Required Tools

#### Ranking And Scoring

- scikit-learn
- xgboost or lightgbm
- network scoring utilities
- multi-criteria ranking framework

#### Scientific Enrichment

- OpenTargets
- ChEMBL
- PubChem
- DrugBank if licensed/access available
- patent search source
- safety / adverse event sources

#### Review And Reporting

- Jupyter for analysis review
- markdown / static report generation
- dashboards for side-by-side comparison

### Scoring Dimensions

Every candidate should be scored on:
- evidence strength
- biological coherence
- fragility relevance
- interventionability
- translational feasibility
- novelty without absurdity
- contradiction risk

### Setup

Implement a target prioritization pipeline that:
- consumes canonical targets, claims, evidence, pathways
- computes component scores separately
- stores score traces
- never emits a single opaque score without decomposition

### Inputs

- Phase 1 hypothesis cards
- druggability and targetability data
- pathway involvement
- literature density
- trial and competitive context

### Outputs

- ranked target shortlist
- confidence bands
- rationale traces
- exclusion reasons for rejected targets
- target-to-modality suggestions

### Review Gates

Do not move to Phase 3 until:
- the shortlist is reviewable by humans
- each shortlisted target has a rationale trace
- excluded candidates are documented
- one can explain why each target is suitable for molecule, CRISPR, AAV, or not

### Stop Criteria

Stop if:
- ranking is dominated by literature volume instead of convergence
- the shortlist changes wildly after small data perturbations
- there is no explicit uncertainty model

## Phase 3: Molecule / CRISPR / AAV Bursts

### Goal

Run targeted compute against a narrowed, biologically justified shortlist.

This phase is not discovery from zero.
It is structured option elimination.

### Core Questions

- For which targets is small-molecule intervention plausible?
- Where does CRISPR or epigenetic editing make more sense than molecules?
- Which problems are delivery problems and therefore AAV-centric?

### Sub-Phase 3A: Molecule Bursts

Use when:
- target is chemically tractable
- a binding pocket or mechanism is plausible
- drug-likeness and CNS relevance can be screened

Required tools:
- RDKit
- molecular property filters
- docking stack
- ADMET prediction stack
- protein structure access

Output:
- ranked candidate set
- property filters
- rationale for rejection

### Sub-Phase 3B: CRISPR / Prime Editing Bursts

Use when:
- correction or regulation is more realistic than small molecules
- editability and context are biologically justified

Required tools:
- guide design tools
- off-target prediction
- sequence handling
- locus-specific annotation

Output:
- ranked edit strategies
- off-target profiles
- feasibility notes

### Sub-Phase 3C: AAV Bursts

Use when:
- delivery dominates the risk profile
- gene payload / tissue targeting questions are central

Required tools:
- capsid sequence evaluation
- tropism scoring
- immunogenicity heuristics
- payload and re-dosing constraints

Output:
- ranked AAV design set
- delivery rationale
- risk flags

### Required Infrastructure

- Ray or similar orchestration
- job queue
- GPU scheduling
- run tracking
- artifact logging

### Compute Policy

Start with small validation bursts:
- proof-of-pipeline runs
- profile cost and throughput
- verify ranking sanity

Only then:
- medium bursts
- finally large bursts

### Review Gates

Before any serious GPU spend:
- shortlisted targets approved
- data and provenance frozen
- run objective explicit
- success/failure definition explicit
- cost ceiling explicit

### Stop Criteria

Abort burst planning if:
- targets are not convergent
- modalities are chosen by fashion instead of mechanism
- no benchmark set exists
- no downstream review workflow exists

## Tooling By Order Of Installation

### Install First

- Python core environment
- Postgres
- DVC or artifact versioning
- pipeline runner
- `SMA-UCM` tooling
- ingestion connectors

### Install Second

- omics and network analysis stack
- target prioritization and enrichment stack
- OpenTargets / ChEMBL / PubChem connectors

### Install Third

- RDKit and docking stack
- CRISPR design stack
- AAV evaluation stack
- cluster orchestration for GPU bursts

## Team By Phase

### Phase 1

- bioinformatics lead
- data engineer
- systems biology reviewer

### Phase 2

- target ranking / translational analyst
- literature and evidence reviewer

### Phase 3

- computational chemist
- genome editing specialist
- delivery / vector specialist
- HPC engineer

## Minimal Deliverables Before Big Compute

The minimum acceptable pre-burst package is:
- canonical data store
- reproducible ingestion
- reviewed hypothesis cards
- ranked target shortlist
- modality rationale
- runbook for compute

## The Practical Rule

If you cannot explain in one page why a target should be screened, edited, or packaged into a vector, you are not ready to spend GPU money on it.
