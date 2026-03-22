# bioRxiv/medRxiv Targeted Preprint Monitor

**Date**: 2026-03-22
**Location**: moltbot (`/home/bryzant/sma-platform/scripts/monitor_biorxiv.py`)
**Schedule**: Daily at 04:00 UTC (after main pipeline at 03:00 UTC)

## Purpose

Extends the daily pipeline's general bioRxiv scan (Stage 2, which uses basic SMA keywords) with focused monitoring on our specific therapeutic targets and mechanistic pathways.

## Architecture

### Two-phase search strategy

**Phase 1 — Europe PMC targeted searches**
- Uses Europe PMC API (`europepmc.org`), which indexes bioRxiv and medRxiv preprints
- Supports keyword search (unlike the bioRxiv API which only has date-range browsing)
- Runs 8 targeted queries with exact-phrase matching
- Rate-limited to 0.5s between queries

**Phase 2 — bioRxiv date-range scan with extended keywords**
- Pages through all bioRxiv/medRxiv papers in the last 7 days
- Filters locally against 22 extended keywords (vs 8 in the default adapter)
- Catches papers that Europe PMC might not yet have indexed
- Deduplicates against Phase 1 results by DOI

**Phase 3 — Database ingestion**
- Inserts new preprints into `sources` table (type: `biorxiv`)
- Uses `ON CONFLICT` for idempotent upserts
- Logs results to `ingestion_log` table

**Phase 4 — Claim extraction**
- Triggers `/api/v2/extract/claims` for new sources only
- Skipped if no new papers found

## Monitored Queries

| # | Query | Rationale |
|---|-------|-----------|
| 1 | "spinal muscular atrophy" | Core disease |
| 2 | "SMN protein motor neuron" | Core biology |
| 3 | "ROCK inhibitor motor neuron" | Therapeutic target (fasudil, ROCK2) |
| 4 | "actin cofilin rod neurodegeneration" | Mechanistic pathway (CFL2, cofilin rods) |
| 5 | "fasudil neuroprotection" | Lead compound |
| 6 | "p38 MAPK motor neuron" | Therapeutic target (MAPK14) |
| 7 | "complement synapse elimination" | Synapse loss mechanism (C1q) |
| 8 | "profilin actin motor neuron" | Actin pathway (PFN1, PFN2) |

## Extended Keywords (Phase 2 filter)

Core SMA: spinal muscular atrophy, smn1, smn2, motor neuron, nusinersen, risdiplam, onasemnogene

Therapeutic targets: rock inhibitor, fasudil, rock2 kinase, p38 mapk, p38 alpha

Mechanistic pathways: actin cofilin, cofilin rod, profilin actin, pfn1, pfn2, complement synapse, complement c1q

Related diseases: motor neuron disease, amyotrophic lateral sclerosis, neuromuscular junction

## Crontab

```
# --- bioRxiv Targeted Monitor (extended queries) ---
# Daily at 04:00 UTC (05:00 CET) — after main pipeline at 03:00 UTC
0 4 * * * cd /home/bryzant/sma-platform && /home/bryzant/sma-platform/venv/bin/python scripts/monitor_biorxiv.py >> /home/bryzant/sma-platform/logs/biorxiv_monitor_$(date +%Y-%m-%d).log 2>&1
```

## Usage

```bash
# Dry run (search only, no database changes)
python scripts/monitor_biorxiv.py --dry-run

# Custom lookback period
python scripts/monitor_biorxiv.py --days-back 14

# Normal run (ingest + claim extraction)
python scripts/monitor_biorxiv.py
```

## First Dry Run Results (2026-03-22)

- Europe PMC: 1 preprint (SMA lumbar puncture technique)
- bioRxiv scan: 1,471 papers checked, 15 relevant
- medRxiv scan: additional papers checked
- **Total: 19 unique relevant preprints in last 7 days**
- Notable: "Anti-inflammatory and pro-proliferative effects of fasudil in human trisomy 21" — directly relevant to our fasudil research track

## Relationship to Daily Pipeline

```
03:00 UTC — daily_pipeline.sh (9 stages including basic bioRxiv scan)
04:00 UTC — monitor_biorxiv.py (extended queries, catches what Stage 2 misses)
```

The monitor complements rather than replaces Stage 2. Stage 2 uses the 8 basic SMA keywords from `biorxiv.py` adapter. The monitor adds 14 more keywords covering therapeutic targets and mechanistic pathways specific to our research directions.

## Log Location

`/home/bryzant/sma-platform/logs/biorxiv_monitor_YYYY-MM-DD.log`
