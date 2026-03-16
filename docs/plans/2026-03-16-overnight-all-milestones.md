# Overnight All-Milestones Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement ALL remaining PLANNED milestone items that are pure code (no external data dependencies) in one overnight session.

**Architecture:** Each task creates a reasoning module + API routes + registers in app.py. Tasks are independent and can be dispatched as parallel agents. All follow existing patterns: asyncpg queries, FastAPI routes, httpx for external APIs.

**Tech Stack:** Python, FastAPI, asyncpg, Claude API (optional), NVIDIA NIM API, RDKit

---

## Wave 1: Track 1 — Trustworthy Evidence Engine (6 tasks)

### Task 1: Source Quality Weighting
**Files:** Create `src/sma_platform/reasoning/source_quality.py` + `src/sma_platform/api/routes/source_quality.py`

Score each source paper by: journal impact (known SMA journals get bonus), study type (RCT > observational > review > case report), sample size (from metadata), recency (newer = higher), citation proxy (claim count as proxy).

Endpoints: `GET /source-quality/scores`, `GET /source-quality/distribution`

### Task 2: Extraction Benchmark
**Files:** Create `src/sma_platform/reasoning/extraction_benchmark.py` + `src/sma_platform/api/routes/benchmark.py`

Build a gold-standard evaluation set: take 50 random claims, store them with manual labels (correct/incorrect/partial). Compare LLM extraction against these. Calculate precision, recall, F1. Also test reproducibility: extract same abstract twice, compare outputs.

Endpoints: `GET /benchmark/extraction`, `GET /benchmark/reproducibility`, `POST /benchmark/evaluate` (admin)

### Task 3: Evidence Uncertainty Intervals
**Files:** Create `src/sma_platform/reasoning/uncertainty.py` + `src/sma_platform/api/routes/uncertainty.py`

For each target's convergence score, compute bootstrap confidence intervals (resample claims with replacement N=1000 times, compute score distribution). Return mean, std, 95% CI for each scoring dimension.

Endpoints: `GET /uncertainty/target/{symbol}`, `GET /uncertainty/all`

### Task 4: Full-Text Claim Extraction Trigger
**Files:** Modify `src/sma_platform/reasoning/claim_extractor.py`

Add logic: when extracting claims, prefer `sources.full_text` over `sources.abstract` if available. Track extraction source (abstract vs full_text) in claim metadata.

Endpoint: existing `POST /extract/claims` gets enhanced

### Task 5: Bayesian Evidence Convergence Model
**Files:** Create `src/sma_platform/reasoning/bayesian_convergence.py` + `src/sma_platform/api/routes/bayesian.py`

Replace simple weighted average with Bayesian posterior: P(target_valid | evidence) using claim types as features, source quality as prior weight, replication as likelihood multiplier. Use conjugate Beta-Binomial for tractability.

Endpoints: `GET /bayesian/target/{symbol}`, `GET /bayesian/all`, `GET /bayesian/compare`

### Task 6: Target Prioritization Engine
**Files:** Create `src/sma_platform/reasoning/target_prioritizer.py` + `src/sma_platform/api/routes/prioritization.py`

Multi-criteria ranking combining: evidence convergence (30%), biological plausibility (20%), interventionability/druggability (20%), network centrality from graph (15%), novelty/recency (15%). Return ranked target list with per-dimension scores.

Endpoints: `GET /prioritize/targets`, `GET /prioritize/target/{symbol}`

---

## Wave 2: Track 2 — SMA Mechanism Engine (3 tasks)

### Task 7: Modifier-Aware Phenotype Prediction
**Files:** Create `src/sma_platform/reasoning/modifier_predictor.py` + `src/sma_platform/api/routes/modifier.py`

Given SMN2 copy number + modifier gene status (PLS3 overexpression, NCALD knockdown, NAIP deletion), predict phenotype severity. Use evidence-based rules from literature claims. Output: predicted SMA type, confidence, supporting evidence.

Endpoints: `GET /modifier/predict?smn2_copies=3&pls3=high&ncald=low`, `GET /modifier/factors`

### Task 8: Off-Target Splice Impact Prediction
**Files:** Create `src/sma_platform/reasoning/offtarget_splice.py` + `src/sma_platform/api/routes/offtarget.py`

For a given ASO or small molecule targeting SMN2, predict potential off-target splice effects on other genes. Use SpliceAI-style motif analysis + known splice regulatory elements. Cross-reference with safety claims in evidence.

Endpoints: `GET /offtarget/predict?drug=nusinersen`, `GET /offtarget/genes`

### Task 9: RNA Structure-Informed Ligand Ranking
**Files:** Create `src/sma_platform/reasoning/rna_structure_ranker.py` + `src/sma_platform/api/routes/rna_ranking.py`

Rank compounds by predicted RNA binding using: NVIDIA RNAPro NIM for SMN2 RNA structure, OpenFold3 for protein-RNA complex, compound properties (MW, LogP, RNA-binding pharmacophore features). Integrate with existing screening data.

Endpoints: `GET /rna-ranking/compounds`, `GET /rna-ranking/predict?smiles=...`

---

## Wave 3: Track 3 — Functional Translation Engine (4 tasks)

### Task 10: Expected Value of Experiment Score
**Files:** Create `src/sma_platform/reasoning/experiment_value.py` + `src/sma_platform/api/routes/experiment_value.py`

For each hypothesis, calculate EVE = P(success) * Impact / (Cost + Time). Use: evidence convergence as P(success), therapeutic relevance as Impact, estimated assay costs from Lab-OS module, estimated timeline. Return ranked hypothesis list.

Endpoints: `GET /experiment-value/hypotheses`, `GET /experiment-value/hypothesis/{id}`

### Task 11: Assay-Ready Hypothesis Output
**Files:** Create `src/sma_platform/reasoning/assay_ready.py` + `src/sma_platform/api/routes/assay_ready.py`

Convert top hypotheses into assay-ready format: biological rationale (from evidence), recommended assay (from Lab-OS module), model system, readouts, go/no-go criteria, estimated cost/time, clinical translatability score. Use Claude to synthesize.

Endpoints: `GET /assay-ready/top3`, `GET /assay-ready/hypothesis/{id}`

### Task 12: Biomarker Atlas
**Files:** Create `src/sma_platform/reasoning/biomarker_atlas.py` + `src/sma_platform/api/routes/biomarker.py`

Aggregate all biomarker-type claims across: molecular (NfL, SMN protein levels), imaging (MRI, CMAP), functional (HFMSE, CHOP INTEND), fluid (CSF, blood). Map to treatment response. Cross-reference with clinical trial outcomes.

Endpoints: `GET /biomarker/atlas`, `GET /biomarker/treatment-response`, `GET /biomarker/target/{symbol}`

### Task 13: Patent Landscape / IP Signal
**Files:** Create `src/sma_platform/reasoning/patent_landscape.py` + `src/sma_platform/api/routes/patent_landscape.py`

Analyze 578 SMA patents: cluster by target/mechanism, identify freedom-to-operate for each drug candidate, flag recent patent filings as competitive intelligence. Cross-reference with our docking hits.

Endpoints: `GET /patents/landscape`, `GET /patents/freedom-to-operate?compound=...`, `GET /patents/recent`

---

## Wave 4: Track 4 — Researcher Distribution (2 tasks)

### Task 14: Experiment Design Suggestions
**Files:** Create `src/sma_platform/reasoning/experiment_designer.py` + `src/sma_platform/api/routes/experiment_design.py`

From evidence gaps per target, suggest experiments: if target has drug_efficacy but no protein_interaction claims, suggest binding assay. If has gene_expression but no motor_function, suggest functional assay. Use Lab-OS assay catalog.

Endpoints: `GET /experiment/suggest/{target_symbol}`, `GET /experiment/gaps`

### Task 15: Dead-End Predictor
**Files:** Create `src/sma_platform/reasoning/dead_end_predictor.py` + `src/sma_platform/api/routes/dead_ends.py`

From drug_outcomes data, learn patterns of failure: which target types, mechanisms, claim profiles correlate with clinical failure. Flag new hypotheses that match failure patterns. Simple logistic regression on features.

Endpoints: `GET /dead-ends/risks`, `GET /dead-ends/hypothesis/{id}`, `GET /dead-ends/patterns`

---

## Execution Strategy

15 tasks, all independent. Deploy in 3-4 waves of parallel agents:
- Wave 1: Tasks 1-6 (Track 1 — highest priority)
- Wave 2: Tasks 7-9 (Track 2)
- Wave 3: Tasks 10-13 (Track 3)
- Wave 4: Tasks 14-15 (Track 4)

Each task: ~300-600 lines of code. Total: ~6,000-9,000 new lines.
After each wave: deploy to moltbot, test endpoints, commit + push.
