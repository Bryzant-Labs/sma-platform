# DB Migration: Spatial Multi-Omics — 2026-03-22

## Summary

Migrated the Spatial Multi-Omics section from hardcoded Python dicts to PostgreSQL.
All zone metadata and drug penetration scores are now stored in the DB and served live.

---

## What Changed

### Before
- `reasoning/spatial_omics.py` contained hardcoded `SPINAL_ZONES` dataclass dict and `drugs` list in `analyze_drug_penetration()`
- All three API routes called pure Python functions with no DB
- No way to add/update zones or drugs without a code deploy

### After
- Two new PostgreSQL tables hold all spatial data
- `reasoning/spatial_omics.py` functions are `async` and query DB via `..core.database`
- `TARGET_EXPRESSION` matrix kept in-memory (static literature values, no DB needed yet)
- `_zone_accessibility()` compute function kept for dynamic/novel compound queries
- New POST endpoint `/api/v2/spatial/penetration/predict` for novel compound scoring

---

## Migration: 012_spatial_multiomics.sql

Location: `db/migrations/012_spatial_multiomics.sql`

### Tables Created

#### `spatial_zones`
| Column | Type | Description |
|---|---|---|
| id | UUID PK | |
| zone_key | TEXT UNIQUE | Machine key (e.g. `ventral_horn`) |
| zone_name | TEXT | Human display name |
| anatomical_region | TEXT | |
| cell_types | TEXT[] | Array of cell types |
| bbb_score | FLOAT 0-1 | BBB permeability |
| csf_score | FLOAT 0-1 | CSF exposure (intrathecal access) |
| vascular_score | FLOAT 0-1 | Relative vascular density |
| sma_relevance | FLOAT 0-1 | Importance for SMA pathology |
| drug_access | TEXT | Qualitative access summary |
| clinical_relevance | TEXT | Description / clinical note |

#### `spatial_drug_penetration`
| Column | Type | Description |
|---|---|---|
| id | UUID PK | |
| drug_name | TEXT | |
| route | TEXT | intrathecal / oral / iv / aav / other |
| molecular_weight | FLOAT | |
| logp | FLOAT | |
| drug_type | TEXT | ASO / small_molecule / gene_therapy |
| zone_scores | JSONB | {zone_key: 0.0-1.0} |
| best_zone | TEXT | Zone key with highest score |
| worst_zone | TEXT | Zone key with lowest score |
| mechanism | TEXT | MOA description |
| bbb_crossing | BOOLEAN GENERATED | True if ventral_horn score > 0.4 |
| notes | TEXT | |

### Seeded Data

6 zones: ventral_horn, dorsal_horn, central_canal, white_matter, drg, nmj

3 drugs:
- Nusinersen (Spinraza) — intrathecal — best: central_canal — bbb_crossing: true
- Risdiplam (Evrysdi) — oral — best: nmj — bbb_crossing: false
- Zolgensma (AAV9-SMN1) — aav — best: nmj — bbb_crossing: true

---

## API Endpoints

### Existing (unchanged contract, now DB-backed)
- GET /api/v2/spatial/penetration
- GET /api/v2/spatial/expression
- GET /api/v2/spatial/silent-zones

### New Endpoints
- GET /api/v2/spatial/zones
- GET /api/v2/spatial/zones/{zone_key}
- GET /api/v2/spatial/drugs?route=oral
- POST /api/v2/spatial/penetration/predict

POST predict payload: {"drug_name":"...","molecular_weight":291,"logp":0.8,"route":"oral","drug_type":"small_molecule","persist":false}
Set persist:true to upsert result to spatial_drug_penetration table.

---

## Files Modified

- db/migrations/012_spatial_multiomics.sql — NEW
- src/sma_platform/reasoning/spatial_omics.py — Rewritten async
- src/sma_platform/api/routes/spatial_omics.py — Updated + 4 new endpoints

---

## Test Results (moltbot localhost:8090)

GET /spatial/penetration   — 200, drugs_analyzed: 3, source: postgresql
GET /spatial/expression    — 200, 6 zones, 10 targets, source: postgresql_zones+in_memory_expression
GET /spatial/silent-zones  — 200, total: 0 (white_matter nusinersen=0.54 > 0.5 threshold, correct)
GET /spatial/zones         — 200, 6 rows ordered by sma_relevance
GET /spatial/drugs         — 200, 3 rows with bbb_crossing computed column
POST /spatial/penetration/predict (Fasudil) — 200, zone scores computed on-the-fly

No PM2 errors. No frontend contract breakage.

---

## Notes

- TARGET_EXPRESSION matrix stays in-memory — static literature data. A spatial_target_expression
  table can be added when real Slide-seq/MERFISH data is integrated.
- bbb_crossing is a PostgreSQL GENERATED STORED column from zone_scores->>'ventral_horn' > 0.4
- _zone_accessibility() is retained for the predict endpoint
