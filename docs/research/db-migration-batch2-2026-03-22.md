# DB Migration Batch 2 — Exploratory Sections to PostgreSQL

**Date:** 2026-03-22
**Server:** moltbot (217.154.10.79)
**Status:** COMPLETE — all 4 sections migrated and verified

---

## Summary

Migrated 4 more EXPLORATORY analytical sections from hardcoded Python dataclasses to PostgreSQL, following the same pattern established in Batch 1 (bioelectric, NMJ, spatial, CRISPR).

---

## 1. AAV Capsid Evaluation

**Table:** `aav_capsids`
**Rows seeded:** 9
**Route file:** `api/routes/aav.py` (full rewrite)

### Schema
```sql
CREATE TABLE aav_capsids (
    id SERIAL PRIMARY KEY,
    serotype TEXT NOT NULL UNIQUE,
    common_name TEXT,
    tropism_mn NUMERIC(4,3),
    bbb_crossing NUMERIC(4,3),
    immunogenicity NUMERIC(4,3),
    manufacturing NUMERIC(4,3),
    cargo_capacity_kb NUMERIC(5,2),
    clinical_precedent TEXT,
    sma_relevance TEXT,
    route TEXT, species_data TEXT, key_reference TEXT, notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Serotypes:** AAV9, AAVrh10, PHP.eB, AAV5, AAVhu68, AAV-PHP.S, AAV1, AAV-DJ, MyoAAV

**Endpoints:**
- `GET /api/v2/aav/evaluate?cargo=SMN1_cDNA` — ranked evaluation with composite scoring
- `GET /api/v2/aav/capsid/{serotype}` — detailed capsid info + per-cargo packaging scores
- `GET /api/v2/aav/capsids` — list all capsids from DB

---

## 2. Regeneration Signatures

**Tables:** `regen_genes` (12 rows), `regen_pathways` (7 rows)
**Route section:** `advanced_analytics.py` — regen section replaced (was hardcoded)

### regen_genes schema
```sql
CREATE TABLE regen_genes (
    id SERIAL PRIMARY KEY,
    gene_symbol TEXT NOT NULL UNIQUE,
    gene_name TEXT, organism TEXT, human_ortholog TEXT,
    conservation_score NUMERIC(4,3),
    expression_status TEXT,    -- downregulated, upregulated, unchanged, unknown
    reactivation_potential NUMERIC(4,3),
    pathway TEXT, regeneration_role TEXT, evidence_source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### regen_pathways schema
```sql
CREATE TABLE regen_pathways (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    regen_state TEXT, sma_state TEXT,
    gap_score NUMERIC(4,3),
    drug_candidates TEXT[],
    reactivation_strategy TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Genes:** c-Fos, JunB, ctgfa, miR-200a, sox2, shha, mstn, pgc1a, nrg1, wnt, hmga2, bdnf

**Pathways:** MAPK/ERK, TGF-beta/anti-fibrotic, Wnt/beta-catenin, Mitochondrial biogenesis, ErbB/Neuregulin, Neurotrophic support, Chromatin accessibility

**Endpoints:**
- `GET /api/v2/regen/genes` — filterable by organism, sma_status, min_reactivation
- `GET /api/v2/regen/pathways` — filterable by regen_state, sma_state, min_gap
- `GET /api/v2/regen/silenced` — downregulated genes with high reactivation potential

---

## 3. Digital Twin — Compartments & Pathways

**Tables:** `twin_compartments` (5 rows), `twin_pathways` (8 rows)
**Route file:** `api/routes/digital_twin.py` (updated)

### twin_compartments schema
```sql
CREATE TABLE twin_compartments (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    volume_um3 INTEGER,
    key_processes TEXT[], sma_defects TEXT[],
    druggable BOOLEAN DEFAULT FALSE,
    health_baseline NUMERIC(4,3),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### twin_pathways schema
```sql
CREATE TABLE twin_pathways (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    activity_level NUMERIC(4,3),
    sma_state TEXT,
    target_genes TEXT[], compartments TEXT[],
    inputs TEXT[], outputs TEXT[], therapeutic_targets TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Compartments:** Soma, Axon, Presynaptic terminal (NMJ), Dendrites, Nucleus

**Pathways:** PI3K/Akt/mTOR, MAPK/ERK, Calcium/CaMKII, Ubiquitin-proteasome, Mitochondrial bioenergetics, Spliceosome/snRNP, NMJ maintenance, Autophagy/mitophagy

**Endpoints:**
- `GET /api/v2/twin/compartments` — now DB-backed (fallback to Python if DB empty)
- `GET /api/v2/twin/pathways` — now DB-backed (fallback to Python if DB empty)
- Simulation endpoints (`/simulate`, `/optimize`, `/temporal`) remain Python-only

**Architecture note:** Simulation engine still uses Python COMPARTMENTS/PATHWAYS dataclasses for drug combination math. DB serves display/retrieval only — simulation correctness preserved.

---

## 4. Multisystem SMA

**Table:** `multisystem_organs` (7 rows)
**Route section:** `advanced_analytics.py` — multisystem section replaced (was hardcoded)

### Schema
```sql
CREATE TABLE multisystem_organs (
    id SERIAL PRIMARY KEY,
    organ_name TEXT NOT NULL UNIQUE,
    prevalence_pct NUMERIC(5,2),
    severity NUMERIC(4,3),
    sma_types_affected TEXT,
    smn_dependent BOOLEAN DEFAULT TRUE,
    clinical_manifestations TEXT[],
    biomarkers TEXT[], mechanisms TEXT[],
    therapeutic_approaches TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Organs:** Liver (70%), Heart (60%), Systemic metabolism (55%), Pancreas (40%), Vasculature (35%), Skeleton (80%), GI tract (65%)

**Endpoints:**
- `GET /api/v2/multisystem/organs` — filterable by sma_type, smn_dependent, min_prevalence
- `GET /api/v2/multisystem/combinations` — combination therapy strategies (Python, unchanged)
- `GET /api/v2/multisystem/energy` — energy budget analysis (Python, unchanged)
- `GET /api/v2/multisystem/full` — full analysis (organs from DB, combos+energy from Python)

---

## Verification Results

All endpoints tested after deployment (sma-api PM2 restart confirmed):

| Endpoint | Status | Records | Source |
|----------|--------|---------|--------|
| `/api/v2/aav/evaluate` | OK | 9 capsids | postgresql |
| `/api/v2/regen/genes` | OK | 12 genes | postgresql |
| `/api/v2/regen/pathways` | OK | 7 pathways | postgresql |
| `/api/v2/regen/silenced` | OK | 7 silenced, 5 high-potential | postgresql |
| `/api/v2/twin/compartments` | OK | 5 compartments | postgresql |
| `/api/v2/twin/pathways` | OK | 8 pathways | postgresql |
| `/api/v2/twin/simulate` (POST) | OK | functional_score: 0.55 | python |
| `/api/v2/multisystem/organs` | OK | 7 organs | postgresql |

Key findings:
- Most impaired compartment: **Presynaptic terminal (NMJ)** (health_baseline 0.25)
- Most impaired pathway: **Spliceosome/snRNP assembly** (activity 0.15)
- Largest regen-SMA gap: **MAPK/ERK sustained signaling** (gap_score 0.75)
- Most prevalent non-MN organ: **Skeleton** (80%)

---

## New Tables Added (DB total: 47)

| # | Table | Rows |
|---|-------|------|
| 42 | `aav_capsids` | 9 |
| 43 | `regen_genes` | 12 |
| 44 | `regen_pathways` | 7 |
| 45 | `twin_compartments` | 5 |
| 46 | `twin_pathways` | 8 |
| 47 | `multisystem_organs` | 7 |

---

## Files Modified on Server

| File | Change |
|------|--------|
| `api/routes/aav.py` | Full rewrite — DB-backed with Python scoring |
| `api/routes/digital_twin.py` | Compartments + pathways now DB-backed |
| `api/routes/advanced_analytics.py` | Regen (7.2) and Multisystem (7.4) sections DB-backed |
| `api/routes/advanced_analytics.py.bak` | Backup of previous version |
