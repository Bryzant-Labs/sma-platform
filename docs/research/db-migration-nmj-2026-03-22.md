# DB Migration: NMJ Retrograde Signaling (Phase 7.3)
**Date:** 2026-03-22
**Status:** Complete — live on moltbot sma-api:8090

---

## Summary

Migrated the NMJ Retrograde Signaling module from hardcoded Python dataclasses in
`reasoning/nmj_signaling.py` to three PostgreSQL tables in the sma-platform database.
API routes now query the DB via the shared `core.database` abstraction layer.

---

## Tables Created

### `nmj_signals`
Retrograde signaling molecules at the neuromuscular junction.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PRIMARY KEY | |
| signal_name | TEXT UNIQUE NOT NULL | |
| molecule_type | TEXT | protein / lipid / exosome |
| source | TEXT | muscle fiber / Schwann cell / MN terminal |
| target | TEXT | motor neuron soma / presynaptic terminal |
| sma_status | TEXT CHECK | reduced / absent / increased / normal |
| normal_function | TEXT | Mechanistic description |
| therapeutic_strategy | TEXT | Intervention approach |
| therapeutic_potential | NUMERIC(3,2) | 0.0-1.0 |
| evidence_strength | TEXT CHECK | strong / moderate / emerging |
| created_at | TIMESTAMPTZ | |

**Seeded rows:** 10 signals (BDNF, NT-4/5, GDNF, Gdf5/BMP, LAMB2, Muscle EVs, Agrin, 2-AG, Schwann VEGF, FGF-BP1)
**Key finding in data:** 9/10 signals are reduced in SMA (happy_muscle_score: 0.9)

---

### `nmj_ev_cargo`
Extracellular vesicle cargo for NMJ-targeted therapeutic delivery.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PRIMARY KEY | |
| cargo_name | TEXT UNIQUE NOT NULL | |
| cargo_type | TEXT CHECK | mirna / protein / mrna / lipid |
| function | TEXT | Biological function |
| sma_context | TEXT | SMA-specific relevance |
| delivery_mechanism | TEXT | EV engineering approach |
| feasibility | NUMERIC(3,2) | 0.0-1.0 |
| created_at | TIMESTAMPTZ | |

**Seeded rows:** 7 cargo items (miR-206, miR-1, miR-133a, HSP70, SMN mRNA, BDNF protein, Agrin fragment)
**Top feasible:** miR-206 (0.75), BDNF protein (0.70), miR-1 (0.70)

---

### `nmj_chip_models`
Organ-on-chip NMJ models for validation and drug screening.

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PRIMARY KEY | |
| name | TEXT UNIQUE NOT NULL | |
| cell_types | TEXT[] | Array of cell types used |
| readouts | TEXT[] | Array of measurable outputs |
| trl | SMALLINT CHECK (1-9) | Technology Readiness Level |
| supplier | TEXT | Commercial / academic source |
| validation_assays | TEXT[] | Array of assay names |
| sma_modeling | TEXT | How this model captures SMA |
| cost_per_chip | TEXT | Approximate cost |
| throughput | TEXT | Chips per week |
| created_at | TIMESTAMPTZ | |

**Seeded rows:** 3 models
| Model | TRL | Throughput |
|-------|-----|-----------|
| High-throughput NMJ plate (optogenetic) | 6 | High (96 conditions/plate) |
| NMJ-on-Chip (2-compartment) | 5 | Low (10-20/week) |
| Motor Unit-on-Chip (3-compartment) | 4 | Low (5-10/week) |

**Recommended:** High-throughput optogenetic plate (TRL 6) for drug screening.

---

## API Routes Updated

All routes in `/api/v2/nmj/*` previously called hardcoded Python functions; now query PostgreSQL.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v2/nmj/signals` | GET | All retrograde signals, ordered by therapeutic_potential DESC |
| `/api/v2/nmj/ev-cargo` | GET | EV cargo options, ordered by feasibility DESC |
| `/api/v2/nmj/chip-models` | GET | Chip models, ordered by TRL DESC |
| `/api/v2/nmj/happy-muscle` | GET | Composite analysis assembling all 3 tables + hypothesis scoring |

---

## Implementation Pattern

Follows the same pattern as `news.py`, `splice.py`, and `gpu.py`:

1. **Idempotent DDL** - `CREATE TABLE IF NOT EXISTS` + `CREATE INDEX IF NOT EXISTS`
2. **Idempotent seeding** - `INSERT ... ON CONFLICT (unique_col) DO NOTHING`
3. **Lazy init** - `_ensure_nmj_tables()` called on first request; process-level bool flag prevents repeated DDL
4. **No breaking changes** - Response schema preserved exactly. `happy_muscle_score` is now computed from live DB count.
5. **Phases 7.2, 7.4, 7.5 untouched** - regeneration, multisystem, bioelectric routes still call Python functions.

---

## Files Changed

- `src/sma_platform/api/routes/advanced_analytics.py` - DB-backed NMJ routes, removed import of nmj_signaling Python functions
- `reasoning/nmj_signaling.py` - unchanged (kept as source-of-truth reference; can be cleaned up in a future sprint)

---

## Verification Results (live, 2026-03-22)

```
GET /api/v2/nmj/signals       -> total_signals: 10, happy_muscle_score: 0.9
GET /api/v2/nmj/ev-cargo      -> total_cargo: 7, top: miR-206 (0.75)
GET /api/v2/nmj/chip-models   -> total_models: 3, recommended TRL: 6
GET /api/v2/nmj/happy-muscle  -> hypothesis_score: 0.64, 5 evidence_for, 3 evidence_against
GET /api/v2/regen/genes       -> OK (Phase 7.2 intact)
GET /api/v2/multisystem/organs -> OK (Phase 7.4 intact)
GET /api/v2/bioelectric/channels -> OK (Phase 7.5 intact)
```

PM2 process `sma-api` (id 7): online, startup complete, no import errors.

---

## Next Steps (Optional)

- Add `POST /api/v2/nmj/signals` admin endpoint to update signal data without code deploys
- Add `updated_at` trigger for all three tables
- Remove hardcoded constants from `nmj_signaling.py` in a cleanup commit
- Add `evidence_pmids TEXT[]` column to `nmj_signals` for direct citation tracking
