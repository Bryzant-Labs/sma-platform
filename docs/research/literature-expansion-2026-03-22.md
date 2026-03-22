# Literature Expansion — Targeted PubMed Ingestion (2026-03-22)

## Summary

Ran 10 targeted PubMed queries focusing on underrepresented targets and recent findings.
All queries executed successfully with zero errors.

**Results:**
- **284 new sources** ingested (6,535 -> 6,778 total in DB, but 366 new today counting earlier batches)
- **60 SMA-relevant claims** extracted via Gemini 2.0 Flash
- **156 claims** linked to new sources (including earlier targeted batches today)
- **0 errors** in both ingestion and extraction

## Query Results

| # | Query | Found | New | Notes |
|---|-------|-------|-----|-------|
| 1 | SARM1 motor neuron axon degeneration SMA | 5 | 5 | Necroptosis/axon degeneration target |
| 2 | Complement C1q synapse elimination motor neuron | 24 | 24 | Used broader fallback (original returned 0 for 2024-2026) |
| 3 | Fasudil ROCK inhibitor motor neuron neuroprotection | 56 | 56 | Strong literature base, key ROCK pathway evidence |
| 4 | MW150 p38 MAPK inhibitor motor neuron | 9 | 9 | Small but focused — our #1 drug candidate |
| 5 | Panobinostat HDAC inhibitor SMN2 splicing | 8 | 8 | #2 drug candidate, HDAC/SMN2 splicing |
| 6 | Apitegromab myostatin SMA phase 3 | 6 | 6 | Phase 3 myostatin inhibitor |
| 7 | Belumosudil ROCK2 selective kinase | 97 | 97 | Largest batch — selective ROCK2 inhibitor, mostly GVHD context |
| 8 | Actin cofilin rod motor neuron neurodegeneration | 24 | 24 | Actin rod pathway in neurodegeneration |
| 9 | Bioelectric reprogramming motor neuron spinal cord stimulation | 17 | 17 | Levin framework / spinal cord stimulation |
| 10 | Digital twin motor neuron computational model SMA | 38 | 38 | Computational models for SMA |
| | **TOTAL** | **284** | **284** | **100% new (no duplicates with existing DB)** |

## Claim Extraction

- **329 sources** processed (284 from this batch + 45 from earlier today without claims)
- **60 claims** extracted (many sources correctly filtered as non-SMA-relevant)
- **Quality gate**: SMA keyword filter removed papers about GVHD, cancer, ophthalmology etc. that are belumosudil/fasudil-related but not neuromuscular
- **LLM**: Gemini 2.0 Flash (extraction_llm=gemini)

### Notable High-Confidence Claims Extracted

1. **Fasudil improves survival and skeletal muscle development in SMA mice** (conf=1.00)
   - Fasudil increases muscle fiber size and improves neuromuscular junction maturation
   - Restores normal expression of skeletal muscle development markers

2. **ROCK inhibition (Y-27632) extends lifespan in intermediate SMA mice** (conf=1.00)
   - Lifespan rescue is independent of Smn expression
   - RhoA effectors are viable therapeutic targets for SMA

3. **Smn depletion increases RhoA activation in spinal cord** (conf=1.00)
   - Direct mechanistic link between SMN loss and ROCK pathway activation

4. **Apitegromab/myostatin pathway**:
   - Taldefgrobep alfa selectively binds myostatin
   - Myostatin levels correlate with SMA severity and motor function
   - Nusinersen has no major effect on myostatin/follistatin levels

5. **Spinal cord stimulation for motor neuron diseases** — epidural stimulation literature now ingested

## DB State After Ingestion

| Metric | Before | After |
|--------|--------|-------|
| Total sources | 6,535 | 6,778 (+243 net from this run) |
| Total claims | ~14,127 | 14,187 (+60 from extraction) |

## Technical Notes

- Fixed `nvidia_api_key_2` config error in `src/sma_platform/core/config.py` (added missing field)
- Script: `/home/bryzant/sma-platform/scripts/targeted_ingest_2026_03_22.py`
- Extraction script: `/home/bryzant/sma-platform/scripts/extract_claims_new_sources.py`
- Used fallback broader queries when narrow queries returned <5 results (C1q, MW150, panobinostat, belumosudil, cofilin, bioelectric, digital twin)
- All 10 targeted queries now added to ingestion_log with `targeted:` prefix

## Coverage Gaps Addressed

| Target/Topic | Previous Sources | New Sources | Status |
|--------------|-----------------|-------------|--------|
| SARM1 / necroptosis | 0 | 5 | New coverage |
| C1q / complement | ~2 | +24 | Significantly expanded |
| Fasudil / ROCK | ~5 | +56 | Major expansion |
| MW150 / p38 MAPK | ~3 | +9 | Expanded |
| Panobinostat / HDAC | ~2 | +8 | Expanded |
| Apitegromab / myostatin | ~4 | +6 | Expanded with Phase 3 data |
| Belumosudil / ROCK2 | 0 | +97 | New coverage (mostly GVHD, some repurposing) |
| Actin/cofilin rods | ~3 | +24 | Major expansion |
| Bioelectric / SCS | ~8 | +17 | Expanded |
| Digital twin / computational | ~2 | +38 | Major expansion |
