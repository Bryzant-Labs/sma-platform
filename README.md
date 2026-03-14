# SMA Research Platform

Open-source, evidence-first research platform for Spinal Muscular Atrophy (SMA).

**Mission**: Aggregate, structure, and analyze all available SMA research data to accelerate therapeutic development. Every claim traces back to its source. No marketing — only evidence.

## Architecture

```
Phase A: Evidence Graph (current)
  → Ingest papers, trials, datasets from PubMed, ClinicalTrials.gov, GEO
  → Build knowledge graph: targets, drugs, pathways, claims, evidence
  → UCM format: nodes/edges/evidence in TSV → Parquet pipeline

Phase B: Reasoning (next)
  → Score and rank targets by evidence strength
  → Generate testable hypotheses
  → Identify gaps in the evidence

Phase C: Compute (future)
  → Molecule screening against validated targets
  → CRISPR guide design
  → AAV capsid optimization
  → GPU workloads for molecular dynamics

Phase D: Publication (future)
  → Open research site with all structured data
  → API for pharma and academic researchers
```

## Quick Start

```bash
# 1. Create venv
python -m venv venv
source venv/bin/activate

# 2. Install
pip install -e ".[dev]"

# 3. Configure
cp .env.example .env
# Edit .env with your DATABASE_URL and API keys

# 4. Initialize database
python scripts/init_db.py

# 5. Seed reference data
python scripts/seed_targets.py
python scripts/seed_drugs.py
python scripts/seed_datasets.py

# 6. Run API
python main.py
# → http://localhost:8100/docs
```

## Project Structure

```
sma-platform/
├── src/sma_platform/
│   ├── core/           # Config, database pool, shared types
│   ├── ucm/            # Unified Computational Model (TSV → Parquet)
│   ├── api/            # FastAPI endpoints
│   │   └── routes/     # stats, targets, trials, evidence, ingestion
│   ├── ingestion/      # Source adapters
│   │   └── adapters/   # pubmed, clinicaltrials, geo
│   ├── reasoning/      # Evidence scoring, hypothesis generation
│   └── agents/         # Autonomous research agents (planned)
├── db/
│   ├── schema.sql      # Canonical PostgreSQL schema
│   └── migrations/     # Future migration files
├── data/
│   ├── raw/            # UCM input files (nodes.tsv, edges.tsv, evidence.tsv)
│   ├── processed/      # Built artifacts (parquet, bundles)
│   └── datasets/       # Downloaded omics data
├── scripts/            # DB init, seed data, utilities
├── tests/              # Unit and integration tests
└── docs/               # Plans, ADRs, research notes
```

## Key Tables

| Table | Purpose |
|-------|---------|
| `sources` | PubMed papers, trial records, dataset entries |
| `targets` | Genes (SMN1, SMN2, STMN2, PLS3), proteins, pathways |
| `drugs` | Approved (Spinraza, Evrysdi, Zolgensma) + pipeline therapies |
| `trials` | Clinical trials from ClinicalTrials.gov |
| `datasets` | Omics datasets (GEO, PRIDE) with evidence tiers |
| `claims` | Factual assertions extracted from sources |
| `evidence` | Links claims to their supporting sources |
| `graph_edges` | Knowledge graph: target-target relationships |
| `hypotheses` | Generated and validated research hypotheses |

## API Endpoints

- `GET /health` — Health check
- `GET /api/v2/stats` — Platform-wide counts
- `GET /api/v2/targets` — List targets (genes, proteins, pathways)
- `GET /api/v2/trials` — List clinical trials
- `GET /api/v2/claims` — List evidence-backed claims
- `GET /api/v2/sources` — List ingested sources
- `GET /api/v2/hypotheses` — List generated hypotheses
- `POST /api/v2/ingest/pubmed` — Trigger PubMed ingestion
- `POST /api/v2/ingest/trials` — Trigger ClinicalTrials.gov ingestion

## Data Sources

| Source | Adapter | Status |
|--------|---------|--------|
| PubMed (NCBI E-utilities) | `pubmed.py` | Built |
| ClinicalTrials.gov v2 API | `clinicaltrials.py` | Built |
| GEO (Gene Expression Omnibus) | `geo.py` | Built |
| PRIDE (Proteomics) | planned | - |
| UniProt | planned | - |
| KEGG/Reactome | planned | - |

## Core SMA Biology

The platform focuses on the SMN pathway and emerging targets:

- **SMN1/SMN2**: The primary SMA genes. SMN1 deletion causes SMA; SMN2 copy number modifies severity.
- **STMN2**: Microtubule regulator, neuroprotective target. Downregulated when SMN is low.
- **PLS3/NCALD**: Natural protective modifiers identified in discordant SMA families.
- **NMJ dysfunction**: Earliest pathological feature, precedes motor neuron loss.
- **mTOR dysregulation**: Hyperactivation in SMA motor neurons.

## License

MIT — All research data is open source.
