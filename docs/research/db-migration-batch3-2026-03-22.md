# DB Migration Batch 3 — Exploratory Sections to PostgreSQL

**Date:** 2026-03-22
**Server:** moltbot (217.154.10.79)
**Status:** COMPLETE — all 3 sections migrated and verified

---

## Summary

Migrated 3 more EXPLORATORY analytical sections from hardcoded Python dataclasses to PostgreSQL, following the same pattern established in Batch 1 (bioelectric, NMJ, spatial, CRISPR) and Batch 2 (AAV, regeneration, multisystem, organoids).

---

## 1. Cross-Species Splicing Map

**Migration:** `db/migrations/024_splicing_map_events.sql`
**Seed:** `db/seeds/seed_splicing_map.py`
**Route file:** `api/routes/splicing_map.py` (full rewrite)
**Table:** `splicing_map_events`
**Rows seeded:** 10

### Schema

```sql
CREATE TABLE splicing_map_events (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gene_axolotl                TEXT NOT NULL,
    gene_human                  TEXT NOT NULL,
    event_type                  TEXT CHECK (IN: exon_skip, alt_5ss, alt_3ss, intron_retention, alt_promoter),
    exon_region                 TEXT,
    axolotl_state               TEXT CHECK (IN: included, skipped, retained, switched),
    human_sma_state             TEXT CHECK (IN: included, skipped, retained, silenced, unknown),
    regeneration_function       TEXT,
    conservation_score          NUMERIC(4,3),
    reactivation_feasibility    NUMERIC(4,3),
    therapeutic_approach        TEXT,
    source_id                   UUID REFERENCES sources(id),
    metadata                    JSONB DEFAULT '{}',
    created_at                  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (gene_human, event_type, exon_region)
);
```

### Seeded Genes

FGF8, CTNNB1, TP53, SOX2, LIN28A, MARCKS, VIM, CIRBP, NRG1, MSI1

### Verification

- `GET /api/v2/splice/cross-species` → 10 events | 6 silenced | avg_conservation: 0.74
- `GET /api/v2/splice/cross-species/actionable` → top 5 | 3 ASO candidates (CTNNB1, MARCKS, NRG1)
- `GET /api/v2/splice/cross-species/compare` → 7 regen_active | 6 human_silenced | 6 overlap
- `GET /api/v2/splice/cross-species?event_type=exon_skip` → 3 events (NRG1, MARCKS, CTNNB1)
- `GET /api/v2/splice/cross-species/{gene_human}` → by-gene lookup (e.g., NRG1)

### New Filters Added

All filters are query params: `event_type`, `human_state`, `min_conservation`, `min_feasibility`

---

## 2. Gene Edit Versioning

**Migration:** `db/migrations/025_gene_versions.sql`
**Seed:** `db/seeds/seed_gene_versions.py`
**Route file:** `api/routes/gene_versioning.py` (DB-first with fallback)
**Table:** `gene_versions`
**Rows seeded:** 4 (2 skipped due to biologically identical sequences — expected)

### Schema

```sql
CREATE TABLE gene_versions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gene_symbol         TEXT NOT NULL,
    variant_name        TEXT NOT NULL,
    sequence_hash       TEXT NOT NULL,     -- Short SHA-256 (12 chars, like git)
    full_hash           TEXT NOT NULL,     -- Full SHA-256
    sequence            TEXT NOT NULL,
    region              TEXT NOT NULL,
    parent_hash         TEXT,              -- Hash of parent version
    base_change         TEXT,
    ref_allele          TEXT,
    alt_allele          TEXT,
    position            INTEGER,
    edit_type           TEXT CHECK (IN: reference, snv, deletion, insertion, base_edit, crispr_ko, prime_edit),
    clinical_significance TEXT,
    population_frequency  NUMERIC(8,6),
    functional_impact     TEXT,
    source_id             UUID REFERENCES sources(id),
    metadata              JSONB DEFAULT '{}',
    created_at            TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (gene_symbol, sequence_hash)
);
```

### Seeded Versions

| edit_type | variant_name | sequence_hash |
|-----------|-------------|---------------|
| reference | SMN1 exon 7 reference (healthy) | b6502e948020 |
| snv | C→T at position 6 (SMN2 disease mutation) | 41ae769ac7fb |
| snv | G→T at position 49 (ESS disruption) | 9ee1a9be7387 |
| reference | SMN2 full region 255 nt | d47ea234eb05 |

**Note:** base_edit (T→C restoring SMN1-like sequence) and ESE snv produce sequences with identical hashes to existing entries — biologically correct (base edit restores SMN1; ESE mutation at pos 21 produces same sequence as SMN2 in this data).

### Verification

- `GET /api/v2/gene-versions/smn2` → 4 versions | DB-backed with reasoning fallback
- `GET /api/v2/gene-versions/list` → all versions with filters (gene_symbol, edit_type, region)
- `GET /api/v2/gene-versions/{gene}/{hash}` → version by hash
- `POST /api/v2/gene-versions/edit` → compute-only custom edit simulation (unchanged)

---

## 3. Dual-Target Molecules

**Migration:** `db/migrations/026_dual_target_molecules.sql`
**Seed:** `db/seeds/seed_dual_target.py`
**Route file:** `api/routes/dual_target.py` (full rewrite)
**Table:** `dual_target_molecules`
**Rows seeded:** 8

### Schema

```sql
CREATE TABLE dual_target_molecules (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                    TEXT NOT NULL UNIQUE,
    target_a                TEXT NOT NULL,
    target_b                TEXT NOT NULL,
    mechanism               TEXT,
    smiles                  TEXT,
    mw                      NUMERIC(8,2),
    logp                    NUMERIC(5,2),
    smn2_activity           TEXT,
    smn2_score              NUMERIC(4,3),
    ion_channel_activity    TEXT,
    ion_channel_score       NUMERIC(4,3),
    synergy_rationale       TEXT,
    drug_likeness           NUMERIC(4,3),
    bbb_penetration         NUMERIC(4,3),
    evidence_level          TEXT CHECK (IN: clinical, preclinical, theoretical, combination),
    development_stage       TEXT,
    clinical_status         TEXT,
    source                  TEXT,
    source_id               UUID REFERENCES sources(id),
    metadata                JSONB DEFAULT '{}',
    created_at              TIMESTAMPTZ DEFAULT NOW()
);
```

### Seeded Molecules

| name | smn2_score | ion_score | evidence_level |
|------|-----------|-----------|----------------|
| Risdiplam + 4-AP combination | 0.95 | 0.80 | combination |
| Valproic acid (VPA) | 0.45 | 0.50 | clinical |
| Riluzole | 0.35 | 0.70 | clinical |
| Roscovitine (Seliciclib) | 0.30 | 0.60 | preclinical |
| Lamotrigine | 0.25 | 0.65 | clinical |
| Retigabine (ezogabine) | 0.20 | 0.75 | preclinical |
| 4-Aminopyridine (Dalfampridine) | 0.15 | 0.80 | clinical |
| GV-58 | 0.10 | 0.85 | preclinical |

### Composite Score (DB-computed in SQL)

```sql
ROUND(smn2_score * 0.25 + ion_channel_score * 0.20 + drug_likeness * 0.15
      + bbb_penetration * 0.15 + LEAST(smn2_score, ion_channel_score) * 0.25, 3)
```

### Verification

- `GET /api/v2/screen/dual-target` → 8 candidates | top: Risdiplam + 4-AP combination
- `GET /api/v2/screen/dual-target/channels` → 5 channels | most_targeted: CACNA1A
- `GET /api/v2/screen/dual-target/synergy` → 8 total | 5 synergistic
- `GET /api/v2/screen/dual-target/{name}` → by-name lookup
- `POST /api/v2/admin/screen/dual-target` → admin-only CRUD (new)

### New Filters Added

All filters are query params: `min_smn2_score`, `min_ion_score`, `evidence_level`, `target_a`, `target_b`

---

## Migration Summary

| # | Table | Rows | Migration | Source File |
|---|-------|------|-----------|-------------|
| 024 | splicing_map_events | 10 | 024_splicing_map_events.sql | reasoning/splicing_map.py |
| 025 | gene_versions | 4 | 025_gene_versions.sql | reasoning/gene_versioning.py |
| 026 | dual_target_molecules | 8 | 026_dual_target_molecules.sql | reasoning/dual_target.py |

**Total new rows:** 22
**Total migrations to date:** 026 (counting from 009)

---

## Pattern Notes

All three routes now:
- Query PostgreSQL via `fetch`/`fetchrow` from `...core.database`
- Support filtering query params
- Return structured JSON with computed stats
- Include `insight` text synthesized from DB data
- Admin CRUD endpoints (where applicable) with `require_admin_key`

Gene versioning uses DB-first with fallback to `build_smn2_version_tree()` from the reasoning module if no DB rows exist — this preserves the computed simulation capability (custom edit POST endpoint remains compute-only).
