# Bugfix: Synergy 500 + Drugs Missing Clinical Trials

**Date**: 2026-03-22
**Status**: FIXED and deployed

---

## Bug 1: Synergy endpoint returns 500

**Endpoint**: `GET /api/v2/synergy/predictions`

**Root cause**: The `drugs.targets` column stores a PostgreSQL UUID array (`uuid[]`), but `synergy_predictor.py` treated the values as strings and called `.lower()` on them. `asyncpg` returns these as `asyncpg.pgproto.pgproto.UUID` objects, which have no `.lower()` method.

**Error**:
```
File "synergy_predictor.py", line 326, in predict_drug_target_synergy
    drug_targets_map[name] = [t.lower() for t in raw_targets if t]
AttributeError: 'asyncpg.pgproto.pgproto.UUID' object has no attribute 'lower'
```

**Fix** (`src/sma_platform/reasoning/synergy_predictor.py`):
1. Convert UUID objects to strings with `str(t).lower()` when building `drug_targets_map`
2. After building `target_ids` (symbol -> id mapping), resolve the UUID strings back to target symbols using a reverse lookup (`target_id_to_symbol`)
3. This ensures downstream functions (`_get_pathway_overlap`, etc.) receive symbols, not UUIDs

**Verification**:
```
GET /api/v2/synergy/predictions?limit=3 -> HTTP 200
Returns: fasudil-ROCK2 pair with pathway_score=1.0, synergy_score=0.2
```

---

## Bug 2: Drugs show 0 clinical trials

**Endpoint**: `GET /api/v2/drugs` (list) and `GET /api/v2/drugs/{id}` (detail)

**Root cause**: The list and detail endpoints returned raw drug rows without any trial linkage. The separate `/drugs/{id}/trials` endpoint existed and worked correctly, but the main drug listing had no `clinical_trials` field. The frontend expected this field on each drug object.

The `trials` table uses a `interventions` column (jsonb), not `intervention` (text). The correct query casts jsonb to text for LIKE matching.

**Fix** (`src/sma_platform/api/routes/drugs.py`):
1. Added trial count enrichment to `list_drugs()` -- for each drug, searches trials by drug name + brand names against `LOWER(CAST(interventions AS TEXT))` and `LOWER(title)`
2. Added same enrichment to `get_drug()` (single drug detail)
3. Uses NCT ID deduplication to avoid double-counting when both drug name and brand name match

**Verification**:
```
GET /api/v2/drugs?limit=5 -> HTTP 200
nusinersen:                   clinical_trials: 36
onasemnogene abeparvovec:     clinical_trials: 18
risdiplam:                    clinical_trials: 24
riluzole:                     clinical_trials: 1
salbutamol:                   clinical_trials: 0
```

Total trials in DB: 451

---

## Files Changed

| File | Change |
|------|--------|
| `src/sma_platform/reasoning/synergy_predictor.py` | UUID-to-symbol resolution for drug targets |
| `src/sma_platform/api/routes/drugs.py` | Added `clinical_trials` count to list + detail endpoints |

## Deployment

- Applied directly on moltbot server
- `pm2 restart sma-api` -- clean startup, no errors
- Both endpoints verified with curl
- Local files synced via scp
