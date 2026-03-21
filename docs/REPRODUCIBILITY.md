# Reproducibility Guide

## Purpose

Every claim, score, and ranking produced by the SMA Research Platform must be
independently verifiable. This document explains how to reproduce our key findings
from scratch and how to run automated verification checks.

## Quick Check

Run the automated reproducibility script to verify the current deployment:

```bash
export DATABASE_URL='postgresql://user:pass@host:5432/sma'
export SMA_API_BASE='http://localhost:8090'  # optional, defaults to localhost:8090

bash scripts/reproduce.sh
```

This checks:
1. **Database schema integrity** -- all 14 required tables exist
2. **Data consistency** -- DB row counts match API `/stats` responses
3. **Claim type distribution** -- at least 5 claim types, 1000+ claims
4. **Convergence scoring** -- 5-dimension scores in valid range [0, 1]
5. **Bayesian calibration** -- calibration grade A or B
6. **Hypothesis prioritization** -- tier A hypotheses present with scores

## Full Reproduction (from scratch)

### 1. Environment Setup

```bash
git clone https://github.com/Bryzant-Labs/sma-platform.git
cd sma-platform
python3.11 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### 2. Database Setup

```bash
createdb sma
export DATABASE_URL='postgresql://localhost:5432/sma'
psql -d sma -f db/schema.sql
```

Apply any pending migrations:

```bash
for f in db/migrations/*.sql; do psql -d sma -f "$f"; done
```

### 3. Seed Reference Data

```bash
python scripts/seed_targets.py    # ~70 SMA-relevant targets
python scripts/seed_drugs.py      # approved + investigational drugs
python scripts/seed_datasets.py   # GEO/PRIDE dataset catalog
```

### 4. Ingest Literature

```bash
python scripts/daily_ingest.py    # PubMed + ClinicalTrials.gov
```

This creates `sources` records and links them via `ingestion_log`. For a full
reproduction, run ingestion repeatedly (or use `--days-back=3650` for a 10-year
backfill).

### 5. Extract Claims

Claims are extracted from source abstracts by the reasoning layer:

```bash
# Via API (requires running server):
curl -X POST http://localhost:8090/api/v2/extract/claims \
     -H "X-Admin-Key: $ADMIN_KEY"

# Or directly:
python -c "
import asyncio
from src.sma_platform.reasoning.claim_extractor import extract_all_claims
asyncio.run(extract_all_claims())
"
```

### 6. Compute Convergence Scores

```bash
curl -X POST http://localhost:8090/api/v2/convergence/compute \
     -H "X-Admin-Key: $ADMIN_KEY"
```

This computes 5-dimension convergence scores (volume, lab independence, method
diversity, temporal trend, replication) for every target and stores them in
`convergence_scores`.

### 7. Run Calibration

```bash
curl http://localhost:8090/api/v2/calibration/bayesian/report
```

Back-tests convergence scores against known drug outcomes (approved vs failed)
from the `drug_outcomes` table.

### 8. Compare With Gold Standard

```bash
python tests/gold_standard/evaluate.py
```

Compares LLM-extracted claims against manually verified samples.

## Key Claims and Their Evidence

| Claim | Method | Evidence Location | Reproducible? |
|-------|--------|-------------------|---------------|
| 4-AP binds SMN2 pre-mRNA (+0.251 confidence) | DiffDock v2, 20-pose ensemble | `gpu/results/diffdock_v2_4ap_smn2.json` | Yes -- re-run DiffDock with same PDB + SMILES |
| Multi-target docking (378 poses) | DiffDock batch, 6 targets x 63 compounds | `gpu/results/diffdock_multi_results.json` | Yes -- re-run `POST /api/v2/dock/local/batch` |
| Calibration Grade A | Bayesian back-test vs drug_outcomes table | `GET /api/v2/calibration/bayesian/report` | Yes -- deterministic given same DB state |
| CORO1C-PLS3 interaction (STRING score 0.818) | STRING-DB API query | STRING-DB public API (v12.0) | Yes -- public API, same query parameters |
| ESM-2 embeddings for 7 SMA proteins | ESM-2 (650M), per-residue embeddings | `gpu/results/esm2/*.npy` + `metadata.json` | Yes -- re-run ESM-2 with same sequences |
| Boltz-2 structure predictions | Boltz-2 structure prediction | `gpu/results/boltz2/` | Yes -- re-run with same FASTA inputs |
| GenMol 4-AP analogs | GenMol de novo generation | `gpu/results/genmol_4ap_analogs.json` | Stochastic -- seed-dependent, similar distribution |
| Top convergence target ranking | 5-dimension convergence engine | `GET /api/v2/convergence/scores` | Yes -- deterministic given same claims |

## Scoring Algorithm Transparency

All scoring weights are defined in:
- **Convergence engine**: `src/sma_platform/reasoning/convergence_engine.py`
- **Prioritizer**: `src/sma_platform/reasoning/prioritizer.py`
- **Calibration**: `src/sma_platform/reasoning/bayesian_calibration.py`
- **Uncertainty**: `src/sma_platform/reasoning/uncertainty_engine.py`

Weights version is tracked in `convergence_scores.weights_version` (currently `v1`).
Any weight change increments the version and triggers re-computation.

## API Reproducibility Endpoints

The platform includes built-in reproducibility testing via API:

| Endpoint | Description |
|----------|-------------|
| `GET /api/v2/reproducibility/test` | Run all reproducibility tests |
| `GET /api/v2/reproducibility/test/convergence` | Test convergence score determinism (run twice, compare) |
| `GET /api/v2/reproducibility/test/ranking` | Test ranking order stability |
| `GET /api/v2/reproducibility/test/claims` | Test claim count consistency |

## Data Availability

| Resource | Location |
|----------|----------|
| Source code | https://github.com/Bryzant-Labs/sma-platform |
| HuggingFace dataset | https://huggingface.co/SMAResearch/sma-evidence-graph |
| Live API | https://sma-research.info/api/v2 |
| Database schema | `db/schema.sql` |
| GPU computation results | `gpu/results/` |
| Gold standard test set | `tests/gold_standard/` |

## Determinism Notes

- **Deterministic**: Schema checks, data counts, convergence scoring, calibration
  back-tests, claim type distribution, hypothesis ranking. These produce identical
  results given the same database state.
- **Stochastic**: LLM-based claim extraction (temperature-dependent), GenMol
  molecule generation (seed-dependent), DiffDock pose sampling (stochastic component).
  For these, we verify distributional consistency rather than exact output matching.
- **External dependencies**: STRING-DB scores, ClinicalTrials.gov data, PubMed
  abstracts may change over time. Pin to specific API versions and dates for exact
  reproduction.
