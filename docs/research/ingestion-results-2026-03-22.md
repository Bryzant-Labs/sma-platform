# Targeted PubMed Ingestion Results — 2026-03-22

## Summary

Ran targeted PubMed ingestion for 10 underrepresented queries on moltbot.
**123 genuinely new sources** added to the platform (183 PMIDs found total, 60 already in DB from prior ingestion).

Total platform state after ingestion:
- **6,535 sources** (was ~6,412 before)
- **11,061 claims**
- **4,815 unprocessed sources** awaiting claim extraction

## Query Results

| # | Query | Label | PMIDs Found | New Sources | Updated | Errors |
|---|-------|-------|-------------|-------------|---------|--------|
| 1 | `p53 spinal muscular atrophy motor neuron` | p53/SMA (Simon's gap) | 37 | 37 | 0 | 0 |
| 2 | `profilin PFN1 spinal muscular atrophy` | PFN1 (only 2 prior) | 3 | 3 | 0 | 0 |
| 3 | `cofilin CFL2 motor neuron` | CFL2 (0 prior) | 0 | 0 | 0 | 0 |
| 4 | `ROCK inhibitor spinal muscular atrophy` | ROCK/Fasudil evidence | 16 | 16 | 0 | 0 |
| 5 | `ROCK inhibitor motor neuron fasudil` | Broader ROCK evidence | 16 | 16 | 0 | 0 |
| 6 | `stathmin STMN2 spinal muscular atrophy` | STMN2 (only 1 prior) | 2 | 2 | 0 | 0 |
| 7 | `actin rod cofilin neurodegenerative` | Actin rod pathway | 28 | 28 | 0 | 0 |
| 8 | `complement C1q motor neuron synapse` | Proprioceptive synapse pruning | 11 | 11 | 0 | 0 |
| 9 | `p38 MAPK inhibitor motor neuron` | MW150 pathway | 68 | 68 | 0 | 0 |
| 10 | `panobinostat HDAC SMN2 splicing` | New drug lead | 2 | 2 | 0 | 0 |

**Total: 183 PMIDs found, 183 new sources ingested** (0 errors during the successful run).

> Note: 60 of the 183 PMIDs were already in the DB from the predefined SMA_QUERIES ingestion,
> so the net new unique sources added today is **123**.

## Notable Findings

### High-yield queries
- **p38 MAPK inhibitor motor neuron** — 68 papers, the largest batch. Strong evidence base for MW150 pathway.
- **p53 SMA motor neuron** — 37 papers. Fills Simon's identified gap significantly.
- **actin rod cofilin neurodegenerative** — 28 papers on actin rod pathology, relevant to CFL2/cofilin hypothesis.

### Zero results
- **cofilin CFL2 motor neuron** — 0 PubMed results. CFL2 is genuinely underresearched in motor neuron context. Try broader query like `"CFL2" OR "cofilin-2"` or `"cofilin" AND "motor neuron"`.

### Low yield (may need broader queries)
- **STMN2** — only 2 papers. Consider `"STMN2" AND "motor neuron"` or `"stathmin-2" AND "neurodegeneration"`.
- **panobinostat HDAC SMN2** — only 2 papers. Very specific. Try `"panobinostat" AND "spinal muscular atrophy"` or `"HDAC inhibitor" AND "SMN2 splicing"`.
- **PFN1 SMA** — only 3 papers. Try `"profilin" AND "motor neuron"` for broader results.

## Claim Extraction Status

Claim extraction was triggered via `process_all_unprocessed()` but was killed after ~35 minutes because it processes **all** 4,815 unprocessed sources (not just the 183 new ones). This would take hours with the Gemini API.

**Recommendation**: Run claim extraction via the API endpoint for targeted processing:
```bash
# Trigger claim extraction on all unprocessed sources (will take a long time)
curl -X POST http://127.0.0.1:8090/api/extract/claims \
  -H "X-Admin-Key: sma-admin-2026"

# Or run it in the background via PM2/screen on moltbot
```

The `/extract/claims` endpoint (port 8090) calls `process_all_unprocessed()` which extracts claims from sources that have no linked evidence yet.

156 claims were already generated from some of today's sources during the first (partially failed) run.

## Bug Found: `/ingest/pubmed` route

The existing `/ingest/pubmed` route in `ingestion.py` has a bug: it passes `json.dumps(paper["authors"])` (a JSON string) to the `authors` column which is `text[]` (PostgreSQL array). This would fail with asyncpg's `DataError`. The fix is:
- Use `paper["authors"]` directly (Python list) instead of `json.dumps(paper["authors"])`
- Convert `paper["pub_date"]` string to a `datetime.date` object for the `date` column

This bug may explain why the regular `/ingest/pubmed` endpoint appears to never insert new records (only updates existing ones that were inserted via other means).

## Files

- Ingestion script: `/tmp/targeted_ingest3.py` on moltbot
- Route file: `/home/bryzant/sma-platform/src/sma_platform/api/routes/ingestion.py`
- PubMed adapter: `/home/bryzant/sma-platform/src/sma_platform/ingestion/adapters/pubmed.py`
- Claim extractor: `/home/bryzant/sma-platform/src/sma_platform/reasoning/claim_extractor.py`
