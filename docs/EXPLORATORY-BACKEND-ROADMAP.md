# Exploratory Sections: Backend Migration Roadmap

> **Goal**: Migrate 13 hardcoded exploratory frontend sections from Python-dataclass-driven reasoning modules to database-driven content with full CRUD APIs.
>
> **Current architecture**: Frontend HTML fetches from FastAPI endpoints -> route files call reasoning module functions -> reasoning modules return hardcoded Python dataclass lists.
>
> **Target architecture**: Frontend HTML fetches from FastAPI endpoints -> route files query PostgreSQL (asyncpg) -> DB tables with seed data from current hardcoded content -> admin CRUD endpoints for ongoing updates.

---

## Architecture Overview

### What Exists Today

| Layer | Status |
|-------|--------|
| **Frontend HTML** (`frontend/index.html`) | Done — all 13 sections have `<table>` structures with `<tbody id="...">` and JS `fetch()` calls to API endpoints |
| **API Routes** (`api/routes/`) | Done — all 13 sections have dedicated route files with GET endpoints |
| **Reasoning Modules** (`reasoning/`) | Done — all 13 sections have Python files with hardcoded dataclass lists (~7,000 lines total) |
| **Database Tables** | Missing — no exploratory tables exist yet |
| **Admin CRUD** | Missing — no POST/PUT/DELETE endpoints for exploratory data |

### Existing DB Tables (for FK references)

```
sources           — PubMed papers, patents, databases
targets           — genes, proteins, pathways (UUID PK, symbol, target_type)
drugs             — therapies (UUID PK, name, drug_type, mechanism)
trials            — clinical trials (UUID PK, nct_id)
datasets          — omics datasets (UUID PK, accession)
claims            — evidence claims (UUID PK, claim_type, subject_id, predicate)
evidence          — claim-source links
graph_edges       — knowledge graph
hypotheses        — generated hypotheses
convergence_scores — evidence convergence
cross_species_targets — comparative biology
drug_outcomes     — success/failure database
```

### Migration Pattern (same for all 13 sections)

```
Step 1: Write SQL migration file (db/migrations/012_*.sql)
Step 2: Seed DB from existing Python dataclass data (one-time script)
Step 3: Add DB query functions to reasoning module (async, pool.acquire, $N params)
Step 4: Update route to call DB query instead of hardcoded function
Step 5: Add POST/PUT/DELETE admin endpoints to route file
Step 6: Frontend unchanged (already fetches from same GET endpoints)
```

### Migration File Naming

Next available: `db/migrations/012_exploratory_tables.sql` (or split per section: 012-028)

---

## Section 1: CRISPR Guide Design (`/crispr`)

### A. Current State

**Route file**: `api/routes/crispr.py` (3 endpoints)
**Reasoning module**: `reasoning/crispr_designer.py` (404 lines)
**Frontend**: Fetches `GET /crispr/guides?max_guides=30`, renders strategies cards + motifs + guides table

**Hardcoded data**:
- `MOTIFS` dict — 6 SMN2 regulatory motifs (ISS-N1, ESE, ESS, Element2, C6T, branch point) with position, sequence, binding proteins
- Guide RNA computation function (`design_smn2_guides`) — scans hardcoded SMN2 exon 7 sequence for NGG PAM sites, computes GC%, on-target/specificity scores
- 3 therapeutic strategies (CRISPRi at ISS-N1, CRISPRi at ESS, CRISPRa at ESE)

**Note**: The guide design is *computational* (scans a reference sequence), not purely static data. The motifs and strategies are the hardcoded part.

### B. Database Tables

```sql
CREATE TABLE crispr_motifs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gene_symbol     TEXT NOT NULL DEFAULT 'SMN2',
    motif_name      TEXT NOT NULL,          -- 'ISS-N1', 'ESE', 'ESS', etc.
    region          TEXT NOT NULL,          -- 'intron7', 'exon7'
    start_pos       INTEGER,
    end_pos         INTEGER,
    sequence        TEXT,
    binding_proteins TEXT[],
    function_desc   TEXT,
    therapeutic_relevance TEXT,
    source_id       UUID REFERENCES sources(id),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (gene_symbol, motif_name)
);

CREATE TABLE crispr_strategies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,          -- 'CRISPRi at ISS-N1'
    approach        TEXT NOT NULL,          -- 'CRISPRi', 'CRISPRa'
    target_motif    TEXT NOT NULL,          -- FK-like to motif_name
    gene_symbol     TEXT NOT NULL DEFAULT 'SMN2',
    mechanism       TEXT,
    expected_outcome TEXT,
    precedent       TEXT,
    feasibility     NUMERIC(3,2),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (name, gene_symbol)
);

CREATE TABLE crispr_guides (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id     UUID REFERENCES crispr_strategies(id),
    gene_symbol     TEXT NOT NULL DEFAULT 'SMN2',
    sequence_20nt   TEXT NOT NULL,          -- 20 nt protospacer
    pam             TEXT DEFAULT 'NGG',
    strand          TEXT CHECK (strand IN ('+', '-')),
    region          TEXT,                   -- 'exon7', 'intron7'
    gc_percent      NUMERIC(4,1),
    on_target_score NUMERIC(4,2),
    specificity     NUMERIC(4,2),
    off_target_count INTEGER,
    computed_at     TIMESTAMPTZ DEFAULT NOW(),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

**FKs to existing tables**: `crispr_motifs.source_id -> sources.id`

**Seed data**: Yes — 6 motifs from `MOTIFS` dict, 3 strategies, ~20-30 pre-computed guides from `design_smn2_guides()`.

### C. API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/crispr/guides` | List guides (existing, keep) |
| GET | `/crispr/motifs` | List motifs (existing, keep) |
| GET | `/crispr/strategies` | List strategies (new) |
| POST | `/crispr/guides` | Design guides for custom sequence (existing, keep computational) |
| POST | `/admin/crispr/motifs` | Add/update motif |
| PUT | `/admin/crispr/motifs/{id}` | Update motif |
| DELETE | `/admin/crispr/motifs/{id}` | Delete motif |
| POST | `/admin/crispr/strategies` | Add strategy |

**Query params**: `gene_symbol` (default SMN2), `strategy` filter, `min_gc`, `max_gc`, `min_specificity`

### D. Data Sources

- **Literature**: PubMed queries for SMN2 exon 7 regulatory elements (PMID: 15548776, 16314491)
- **Databases**: CRISPOR (off-target prediction), CRISPick (on-target scoring), Ensembl (reference sequences)
- **Computational**: Guide scanning is algorithmic — keep as computation, cache results in DB
- **Manual curation**: New motifs from literature review

### E. Migration Strategy

1. Create `crispr_motifs` + `crispr_strategies` tables (migration 012)
2. Write seed script: extract MOTIFS dict + strategies into INSERT statements
3. Keep guide computation algorithmic but cache results in `crispr_guides` table
4. Update `GET /crispr/motifs` to query DB instead of Python dict
5. Add admin CRUD for motifs and strategies

### F. Priority: **HIGH** — core gene editing science, directly actionable

### G. Effort: **M** (3 files: migration SQL, reasoning module update, route update)

---

## Section 2: AAV Capsid Evaluation (`/aav`)

### A. Current State

**Route file**: `api/routes/aav.py` (3 endpoints)
**Reasoning module**: `reasoning/aav_evaluator.py` (358 lines)
**Frontend**: Fetches `GET /aav/evaluate?cargo=SMN1_cDNA`, renders strategy cards + capsid ranking table

**Hardcoded data**:
- 9 AAV capsid entries (AAV1-AAV9, AAVrh10, AAV-PHP.eB, AAV-MYO, AAV-retro) with tropism, BBB, immunogenicity, manufacturing, packaging scores
- `CARGO_SIZES` dict — 7 therapeutic cargo types with sizes in kb
- Composite scoring function (weighted sum)

### B. Database Tables

```sql
CREATE TABLE aav_capsids (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    serotype        TEXT NOT NULL UNIQUE,    -- 'AAV9', 'AAVrh10', etc.
    full_name       TEXT,
    mn_tropism      NUMERIC(3,2),           -- 0-1 motor neuron tropism
    bbb_crossing    NUMERIC(3,2),           -- 0-1 BBB permeability
    immunogenicity  NUMERIC(3,2),           -- 0-1 (lower = better)
    manufacturing   NUMERIC(3,2),           -- 0-1 manufacturing feasibility
    packaging_kb    NUMERIC(4,1),           -- packaging capacity in kb
    clinical_precedent TEXT,                 -- 'Zolgensma (SMA)', etc.
    clinical_status TEXT,                    -- 'approved', 'phase3', etc.
    notes           TEXT,
    source_id       UUID REFERENCES sources(id),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE aav_cargos (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cargo_name      TEXT NOT NULL UNIQUE,    -- 'SMN1_cDNA'
    cargo_type      TEXT,                    -- 'gene_replacement', 'crispr', 'base_editor'
    size_kb         NUMERIC(4,1) NOT NULL,
    genome_config   TEXT,                    -- 'self_complementary', 'single_stranded'
    description     TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

**FKs**: `aav_capsids.source_id -> sources.id`

**Seed data**: Yes — 9 capsids + 7 cargo types directly from Python constants.

### C. API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/aav/evaluate` | Evaluate capsids for cargo (existing) |
| GET | `/aav/capsid/{serotype}` | Capsid detail (existing) |
| GET | `/aav/cargos` | List cargo types (existing) |
| POST | `/admin/aav/capsids` | Add capsid |
| PUT | `/admin/aav/capsids/{id}` | Update capsid scores |
| POST | `/admin/aav/cargos` | Add cargo type |

**Query params**: `cargo` (existing), `min_tropism`, `min_bbb`

### D. Data Sources

- **Literature**: AAV tropism reviews (PMID: 31142541, 33547423), Zolgensma prescribing info
- **Databases**: ClinicalTrials.gov (AAV trials in SMA/neurodegeneration)
- **Manual curation**: New engineered capsids from literature (AAV-PHP.eB2, MyoAAV)

### E. Migration Strategy

1. Create `aav_capsids` + `aav_cargos` tables
2. Seed from `CAPSIDS` list and `CARGO_SIZES` dict
3. Update `evaluate_capsids()` to query DB, keep scoring computation in Python
4. Add admin CRUD

### F. Priority: **HIGH** — gene therapy delivery is a key SMA research area

### G. Effort: **M** (3 files)

---

## Section 3: Gene Edit Versioning (`/versions`)

### A. Current State

**Route file**: `api/routes/gene_versioning.py` (2 endpoints)
**Reasoning module**: `reasoning/gene_versioning.py` (352 lines)
**Frontend**: Fetches `GET /gene-versions/smn2`, renders version tree table + diffs

**Hardcoded data**:
- SMN2 exon 7 reference sequence (54 nt)
- Version tree with ~8 deterministic "commits" (SMN1 -> SMN2 -> therapeutic edits)
- Each version: SHA-256 hash, parent hash, region, edit description, impact
- Diff computation between parent-child pairs

### B. Database Tables

```sql
CREATE TABLE gene_versions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    commit_hash     TEXT NOT NULL UNIQUE,    -- SHA-256 of sequence
    gene_symbol     TEXT NOT NULL,           -- 'SMN2', 'SMN1'
    version_type    TEXT NOT NULL CHECK (version_type IN ('reference', 'disease', 'therapeutic', 'custom')),
    region          TEXT,                    -- 'exon7', 'intron7'
    sequence        TEXT NOT NULL,           -- full sequence at this version
    parent_hash     TEXT,                    -- FK to commit_hash (NULL for root)
    edit_description TEXT,                   -- 'C6T disease mutation'
    edit_position   INTEGER,
    ref_allele      TEXT,
    alt_allele      TEXT,
    impact          TEXT,                    -- 'Loss of exon 7 inclusion'
    source_id       UUID REFERENCES sources(id),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_gene_versions_hash ON gene_versions(commit_hash);
CREATE INDEX idx_gene_versions_gene ON gene_versions(gene_symbol);
```

**Seed data**: Yes — ~8 versions from `build_smn2_version_tree()`.

### C. API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/gene-versions/smn2` | Get version tree (existing) |
| GET | `/gene-versions/{hash}` | Get single version (new) |
| GET | `/gene-versions/{hash}/diff` | Diff vs parent (new) |
| POST | `/gene-versions/edit` | Create custom edit (existing) |
| POST | `/admin/gene-versions` | Add version manually |
| DELETE | `/admin/gene-versions/{id}` | Remove version |

### D. Data Sources

- **Databases**: Ensembl/NCBI (NG_008728.1 SMN2 reference), ClinVar (pathogenic variants)
- **Computational**: SHA-256 hashing is algorithmic — keep
- **Literature**: Base editing studies (PMID: 33462442, 34912113)

### E. Migration Strategy

1. Create `gene_versions` table
2. Seed from `build_smn2_version_tree()` output
3. Keep diff computation in Python, query versions from DB
4. `POST /gene-versions/edit` writes new versions to DB instead of returning ephemeral

### F. Priority: **MEDIUM** — novel visualization concept, but not core experimental data

### G. Effort: **S** (2 files: migration + reasoning module update)

---

## Section 4: Spatial Multi-Omics (`/spatial`)

### A. Current State

**Route file**: `api/routes/spatial_omics.py` (3 endpoints)
**Reasoning module**: `reasoning/spatial_omics.py` (232 lines)
**Frontend**: Fetches `GET /spatial/penetration`, renders zones table + drug penetration table + silent zones

**Hardcoded data**:
- ~6 spinal cord zones (ventral horn, dorsal horn, lateral column, white matter, CSF, NMJ) with BBB permeability, CSF exposure, vascular density, SMA relevance
- Drug penetration matrix: ~6 drugs x 6 zones
- Silent zone identification logic

### B. Database Tables

```sql
CREATE TABLE spatial_zones (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zone_name       TEXT NOT NULL UNIQUE,
    region          TEXT NOT NULL,           -- 'spinal_cord', 'brain', 'peripheral'
    bbb_permeability NUMERIC(3,2),
    csf_exposure    NUMERIC(3,2),
    vascular_density NUMERIC(3,2),
    sma_relevance   TEXT,
    cell_types      TEXT[],
    description     TEXT,
    source_id       UUID REFERENCES sources(id),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE spatial_drug_penetration (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drug_id         UUID REFERENCES drugs(id),
    drug_name       TEXT NOT NULL,           -- denormalized for speed
    zone_id         UUID REFERENCES spatial_zones(id),
    penetration_score NUMERIC(3,2),         -- 0-1
    route           TEXT,                    -- 'intrathecal', 'oral', 'IV'
    drug_type       TEXT,                    -- 'ASO', 'small_molecule', 'gene_therapy'
    evidence_level  TEXT,                    -- 'clinical', 'preclinical', 'modeled'
    source_id       UUID REFERENCES sources(id),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (drug_name, zone_id)
);
```

**FKs**: `spatial_drug_penetration.drug_id -> drugs.id`, `.zone_id -> spatial_zones.id`, `.source_id -> sources.id`

**Seed data**: Yes — zones and drug-zone matrix from Python constants.

### C. API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/spatial/penetration` | Drug penetration analysis (existing) |
| GET | `/spatial/expression` | Expression map (existing) |
| GET | `/spatial/silent-zones` | Silent zones (existing) |
| GET | `/spatial/zones` | List all zones (new) |
| POST | `/admin/spatial/zones` | Add zone |
| PUT | `/admin/spatial/zones/{id}` | Update zone |
| POST | `/admin/spatial/penetration` | Add drug-zone penetration entry |

**Query params**: `drug_name`, `zone`, `min_penetration`, `route`

### D. Data Sources

- **Literature**: Spatial transcriptomics studies (10x Visium spinal cord), drug distribution studies
- **Databases**: Allen Brain Atlas (spatial expression), DrugBank (BBB permeability data)
- **Computational**: Penetration modeling from molecular properties (MW, logP, PSA)
- **Manual curation**: Most data is literature-derived

### E. Migration Strategy

1. Create `spatial_zones` + `spatial_drug_penetration` tables
2. Seed from Python dataclasses
3. Link `drug_name` entries to existing `drugs` table where possible
4. Silent zone computation stays in Python (logic over DB data)

### F. Priority: **HIGH** — directly answers "which drugs reach which tissues" for SMA

### G. Effort: **M** (3 files)

---

## Section 5: Regeneration Signatures (`/regen`)

### A. Current State

**Route file**: `api/routes/advanced_analytics.py` (3 endpoints under `/regen/`)
**Reasoning module**: `reasoning/regeneration_signatures.py` (300 lines)
**Frontend**: Fetches `GET /regen/genes` + `GET /regen/pathways`, renders genes table + pathway comparison table

**Hardcoded data**:
- `REGENERATION_GENES` list — ~10 genes with organism (axolotl/zebrafish), human ortholog, pathway, SMA status, reactivation potential score
- `PATHWAY_COMPARISONS` — ~6 pathway comparisons (MAPK/ERK, Wnt, Notch, etc.) with regen state vs SMA state and gap score

### B. Database Tables

```sql
CREATE TABLE regeneration_genes (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol                  TEXT NOT NULL,
    name                    TEXT,
    organism                TEXT NOT NULL,       -- 'axolotl', 'zebrafish', 'both'
    human_ortholog          TEXT,                -- human gene symbol
    human_target_id         UUID REFERENCES targets(id),
    regeneration_role       TEXT,
    sma_status              TEXT CHECK (sma_status IN ('upregulated', 'downregulated', 'unchanged', 'unknown')),
    reactivation_potential  NUMERIC(3,2),       -- 0-1
    pathway                 TEXT,
    evidence_source         TEXT,
    source_id               UUID REFERENCES sources(id),
    metadata                JSONB DEFAULT '{}',
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (symbol, organism)
);

CREATE TABLE regeneration_pathways (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pathway_name    TEXT NOT NULL UNIQUE,
    regen_state     TEXT,                    -- 'highly active', 'transiently activated'
    sma_state       TEXT,                    -- 'suppressed', 'reduced'
    gap_score       NUMERIC(3,2),           -- 0-1 difference magnitude
    strategy        TEXT,                    -- therapeutic reactivation strategy
    key_genes       TEXT[],
    source_id       UUID REFERENCES sources(id),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

**FKs**: `regeneration_genes.human_target_id -> targets.id`, `.source_id -> sources.id`

**Seed data**: Yes — ~10 genes + ~6 pathways from Python dataclasses.

### C. API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/regen/genes` | List regen genes (existing) |
| GET | `/regen/pathways` | Pathway comparisons (existing) |
| GET | `/regen/silenced` | Silenced programs (existing) |
| POST | `/admin/regen/genes` | Add gene |
| PUT | `/admin/regen/genes/{id}` | Update gene |
| POST | `/admin/regen/pathways` | Add pathway comparison |

**Query params**: `organism`, `pathway`, `min_reactivation`, `sma_status`

### D. Data Sources

- **Literature**: Gerber et al. Science 2018 (axolotl), Mokalled et al. Science 2016 (zebrafish), Nichterwitz et al. Cell Reports 2016
- **Databases**: Ensembl ortholog mappings, KEGG pathways, STRING (protein interactions)
- **Manual curation**: SMA status annotations require literature review

### E. Migration Strategy

1. Create `regeneration_genes` + `regeneration_pathways` tables
2. Seed from `REGENERATION_GENES` + `PATHWAY_COMPARISONS`
3. Link `human_ortholog` to existing `targets` table where symbol matches
4. Keep silenced program identification as computation over DB data

### F. Priority: **MEDIUM** — novel cross-species angle, but speculative

### G. Effort: **M** (3 files)

---

## Section 6: NMJ Retrograde Signaling (`/nmj`)

### A. Current State

**Route file**: `api/routes/advanced_analytics.py` (4 endpoints under `/nmj/`)
**Reasoning module**: `reasoning/nmj_signaling.py` (320 lines)
**Frontend**: Fetches `GET /nmj/signals` + `GET /nmj/ev-cargo` + `GET /nmj/chip-models`, renders 3 sub-sections

**Hardcoded data**:
- `RETROGRADE_SIGNALS` list — ~8 molecules (BDNF, GDNF, NT-3, BMP, Wnt, EVs, NO, endocannabinoids) with type, source, target, SMA status, therapeutic potential
- `EV_CARGO` list — ~6 cargo types for extracellular vesicle delivery
- `CHIP_MODELS` list — ~3 organ-on-chip models (NMJ-on-chip, muscle-nerve co-culture, microfluidic)

### B. Database Tables

```sql
CREATE TABLE nmj_retrograde_signals (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_name         TEXT NOT NULL UNIQUE,
    molecule_type       TEXT,                -- 'protein', 'lipid', 'rna', 'exosome'
    source_tissue       TEXT,                -- 'muscle fiber', 'Schwann cell'
    target_tissue       TEXT,                -- 'motor neuron soma', 'axon terminal'
    sma_status          TEXT,                -- 'reduced', 'absent', 'normal'
    therapeutic_potential NUMERIC(3,2),
    mechanism           TEXT,
    evidence_strength   TEXT CHECK (evidence_strength IN ('strong', 'moderate', 'emerging')),
    drug_id             UUID REFERENCES drugs(id),
    source_id           UUID REFERENCES sources(id),
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE nmj_ev_cargo (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cargo_name      TEXT NOT NULL UNIQUE,
    cargo_type      TEXT,                    -- 'miRNA', 'protein', 'mRNA'
    function_desc   TEXT,
    sma_relevance   TEXT,
    feasibility     NUMERIC(3,2),
    delivery_method TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE nmj_chip_models (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name      TEXT NOT NULL UNIQUE,
    platform        TEXT,                    -- 'microfluidic', 'organ-on-chip'
    cell_types      TEXT[],
    readouts        TEXT[],
    timeline_days   INTEGER,
    cost_estimate   TEXT,
    advantages      TEXT[],
    limitations     TEXT[],
    reference       TEXT,
    source_id       UUID REFERENCES sources(id),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

**FKs**: `nmj_retrograde_signals.drug_id -> drugs.id`, `.source_id -> sources.id`

**Seed data**: Yes — all three lists from Python dataclasses.

### C. API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/nmj/signals` | Retrograde signals (existing) |
| GET | `/nmj/ev-cargo` | EV cargo (existing) |
| GET | `/nmj/chip-models` | Chip models (existing) |
| GET | `/nmj/happy-muscle` | Full analysis (existing) |
| POST | `/admin/nmj/signals` | Add signal |
| PUT | `/admin/nmj/signals/{id}` | Update signal |
| POST | `/admin/nmj/ev-cargo` | Add EV cargo |
| POST | `/admin/nmj/chip-models` | Add chip model |

**Query params**: `molecule_type`, `evidence_strength`, `min_therapeutic_potential`

### D. Data Sources

- **Literature**: Bhatt et al. J Cell Sci 2019, Feng & Ko Curr Opin Neurobiol 2008, Kariya et al. Hum Mol Genet 2008
- **Databases**: UniProt (signal proteins), GeneOntology (NMJ terms)
- **Manual curation**: NMJ biology is specialized; needs expert annotation

### E. Migration Strategy

1. Create 3 tables
2. Seed from dataclass lists
3. Update route endpoints to query DB
4. Add admin CRUD

### F. Priority: **MEDIUM** — important biology, but limited actionable therapeutics

### G. Effort: **M** (3 files)

---

## Section 7: Multisystem SMA (`/multisystem`)

### A. Current State

**Route file**: `api/routes/advanced_analytics.py` (4 endpoints under `/multisystem/`)
**Reasoning module**: `reasoning/multisystem_sma.py` (355 lines)
**Frontend**: Fetches `GET /multisystem/organs` + `GET /multisystem/combinations` + `GET /multisystem/energy`, renders organs table + combination cards + energy budget

**Hardcoded data**:
- `ORGAN_SYSTEMS` list — ~8 organ systems (hepatic, cardiac, metabolic, pancreatic, vascular, skeletal, GI, autonomic) with SMA type, prevalence, severity, biomarkers
- `COMBINATION_THERAPIES` — multi-drug strategies
- `ENERGY_BUDGET` — metabolic energy analysis for SMA motor neurons

### B. Database Tables

```sql
CREATE TABLE multisystem_organs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    system_name         TEXT NOT NULL,       -- 'Hepatic Dysfunction'
    organ               TEXT NOT NULL,       -- 'Liver'
    sma_types_affected  TEXT[],             -- ['SMA1', 'SMA1-2']
    prevalence          NUMERIC(3,2),       -- 0-1 fraction
    severity            NUMERIC(3,2),       -- 0-1
    smn_dependent       BOOLEAN DEFAULT TRUE,
    biomarkers          TEXT[],
    mechanisms          TEXT[],
    clinical_features   TEXT[],
    therapeutic_implications TEXT,
    source_id           UUID REFERENCES sources(id),
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (system_name, organ)
);

CREATE TABLE multisystem_combinations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    combo_name      TEXT NOT NULL UNIQUE,
    target_organs   TEXT[],
    drugs           TEXT[],                  -- drug names
    drug_ids        UUID[],                  -- FK refs to drugs table
    rationale       TEXT,
    expected_benefit TEXT,
    risk_level      TEXT CHECK (risk_level IN ('low', 'moderate', 'high')),
    evidence_level  TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE multisystem_energy_budget (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    compartment     TEXT NOT NULL UNIQUE,    -- 'soma', 'axon', 'synapse'
    atp_demand      NUMERIC(5,2),           -- relative units
    atp_supply      NUMERIC(5,2),
    deficit         NUMERIC(5,2),
    rate_limiting   TEXT,                    -- bottleneck process
    therapeutic_target TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

**FKs**: `multisystem_organs.source_id -> sources.id`, `multisystem_combinations.drug_ids -> drugs.id[]`

**Seed data**: Yes — all lists from Python dataclasses.

### C. API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/multisystem/organs` | Organ systems (existing) |
| GET | `/multisystem/combinations` | Combo therapies (existing) |
| GET | `/multisystem/energy` | Energy budget (existing) |
| GET | `/multisystem/full` | Full analysis (existing) |
| POST | `/admin/multisystem/organs` | Add organ system |
| PUT | `/admin/multisystem/organs/{id}` | Update organ entry |
| POST | `/admin/multisystem/combinations` | Add combination |

**Query params**: `sma_type`, `min_severity`, `organ`

### D. Data Sources

- **Literature**: Hamilton & Bhatt Front Biosci 2013, Deguise & Bhatt Rare Diseases 2021, Nery et al. Eur J Paed Neurol 2021
- **Databases**: OMIM (SMA phenotype spectrum), HPO (phenotype ontology)
- **Manual curation**: Clinical data from case reports

### E. Migration Strategy

1. Create 3 tables
2. Seed from dataclass lists
3. Link `drug_ids` in combinations to existing `drugs` table
4. Update routes, add admin CRUD

### F. Priority: **HIGH** — clinically important for patient management

### G. Effort: **M** (3 files)

---

## Section 8: Bioelectric Reprogramming (`/bioelectric`)

### A. Current State

**Route file**: `api/routes/advanced_analytics.py` (4 endpoints under `/bioelectric/`)
**Reasoning module**: `reasoning/bioelectric_module.py` (324 lines)
**Frontend**: Fetches `GET /bioelectric/channels` + `GET /bioelectric/vmem` + `GET /bioelectric/electroceuticals`, renders channels table + Vmem state cards + electroceuticals table

**Hardcoded data**:
- `ION_CHANNELS` list — ~8 channels (SCN1A, KCNQ2, CACNA1A, GABRA1, HCN1, etc.) with type, Vmem role, SMA expression, drug candidates
- `VMEM_STATES` — ~4 membrane potential states (healthy, depolarized, dormant, apoptotic)
- `ELECTROCEUTICALS` — ~5 intervention modalities (spinal stim, TMS, optogenetics, channel openers, etc.)

### B. Database Tables

```sql
CREATE TABLE bioelectric_channels (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gene                TEXT NOT NULL,       -- 'SCN1A'
    channel_name        TEXT NOT NULL,       -- 'Nav1.1'
    channel_type        TEXT,                -- 'Na', 'K', 'Ca', 'Cl', 'HCN'
    vmem_role           TEXT,                -- 'depolarizing', 'repolarizing', 'resting'
    sma_expression      TEXT,                -- 'downregulated', 'upregulated'
    sma_impact          TEXT,
    therapeutic_target  BOOLEAN DEFAULT FALSE,
    drug_candidates     TEXT[],
    target_id           UUID REFERENCES targets(id),
    source_id           UUID REFERENCES sources(id),
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (gene, channel_name)
);

CREATE TABLE bioelectric_vmem_states (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    state_name      TEXT NOT NULL UNIQUE,    -- 'healthy', 'dormant'
    vmem_mv         NUMERIC(5,1),           -- membrane potential in mV
    vmem_range      TEXT,                    -- '-65 to -55 mV'
    description     TEXT,
    prevalence_sma  NUMERIC(3,2),           -- fraction of MNs in this state
    reversible      BOOLEAN,
    therapeutic_window TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bioelectric_interventions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    intervention_name TEXT NOT NULL UNIQUE,
    modality        TEXT,                    -- 'electrical', 'pharmacological', 'optogenetic'
    target_state    TEXT,                    -- which Vmem state it targets
    mechanism       TEXT,
    evidence_level  TEXT,
    feasibility     NUMERIC(3,2),
    risks           TEXT[],
    current_trials  TEXT[],                  -- NCT numbers
    source_id       UUID REFERENCES sources(id),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

**FKs**: `bioelectric_channels.target_id -> targets.id`, `.source_id -> sources.id`

**Seed data**: Yes — all lists from Python dataclasses.

### C. API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/bioelectric/channels` | Ion channels (existing) |
| GET | `/bioelectric/vmem` | Vmem states (existing) |
| GET | `/bioelectric/electroceuticals` | Interventions (existing) |
| GET | `/bioelectric/profile` | Full analysis (existing) |
| POST | `/admin/bioelectric/channels` | Add channel |
| PUT | `/admin/bioelectric/channels/{id}` | Update channel |
| POST | `/admin/bioelectric/interventions` | Add intervention |

**Query params**: `channel_type`, `vmem_role`, `sma_expression`, `modality`

### D. Data Sources

- **Literature**: Levin BioSystems 2012, Adams & Bhatt Neural Regen Res 2020, Gill et al. Nature Medicine 2024
- **Databases**: IUPHAR/BPS Guide to Pharmacology (ion channel data), ChEMBL (channel modulators)
- **Manual curation**: Vmem states are largely conceptual/modeled

### E. Migration Strategy

1. Create 3 tables
2. Seed from Python dataclasses
3. Link channels to `targets` table via gene symbol
4. Update routes, add admin CRUD

### F. Priority: **MEDIUM** — innovative concept (Levin framework), but early-stage science

### G. Effort: **M** (3 files)

---

## Section 9: Cross-Species Splicing Map (`/splicemap`)

### A. Current State

**Route file**: `api/routes/splicing_map.py` (3 endpoints)
**Reasoning module**: `reasoning/splicing_map.py` (253 lines)
**Frontend**: Fetches `GET /splice/cross-species`, renders single table (8 columns: axolotl gene, human ortholog, event type, exon, axolotl state, human SMA, conservation, feasibility)

**Hardcoded data**:
- `SPLICE_EVENTS` list — ~10 cross-species splice events mapping axolotl regeneration isoforms to human orthologs
- Conservation scores, feasibility ratings, and therapeutic strategies

### B. Database Tables

```sql
CREATE TABLE splicing_map_events (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    axolotl_gene        TEXT NOT NULL,
    human_ortholog      TEXT NOT NULL,
    human_target_id     UUID REFERENCES targets(id),
    event_type          TEXT,                -- 'exon_inclusion', 'exon_skipping', 'alt_5ss'
    exon                TEXT,                -- 'exon 3', 'exon 7'
    axolotl_state       TEXT,                -- 'included during regeneration'
    human_sma_state     TEXT,                -- 'constitutively skipped'
    conservation_score  NUMERIC(3,2),       -- 0-1
    feasibility         NUMERIC(3,2),       -- 0-1
    therapeutic_strategy TEXT,
    evidence_source     TEXT,
    source_id           UUID REFERENCES sources(id),
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (axolotl_gene, human_ortholog, event_type)
);
```

**FKs**: `splicing_map_events.human_target_id -> targets.id`, `.source_id -> sources.id`

**Seed data**: Yes — ~10 events from Python list.

### C. API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/splice/cross-species` | Full map (existing) |
| GET | `/splice/cross-species/actionable` | High-feasibility targets (existing) |
| GET | `/splice/cross-species/compare` | Regen vs degen comparison (existing) |
| POST | `/admin/splice/events` | Add splice event |
| PUT | `/admin/splice/events/{id}` | Update event |

**Query params**: `event_type`, `min_conservation`, `min_feasibility`, `organism`

### D. Data Sources

- **Literature**: Axolotl genome studies (Nowoshilow et al. Nature 2018), zebrafish splicing (Burge lab)
- **Databases**: Ensembl Compara (ortholog mappings), VAST-DB (alternative splicing), SpliceAI
- **Computational**: Conservation scoring from multi-species alignment

### E. Migration Strategy

1. Create `splicing_map_events` table
2. Seed from `SPLICE_EVENTS` list
3. Link `human_ortholog` to `targets` table
4. Update route, add admin CRUD

### F. Priority: **LOW** — creative cross-species concept, but speculative

### G. Effort: **S** (2 files)

---

## Section 10: Digital Twin (`/twin`)

### A. Current State

**Route file**: `api/routes/digital_twin.py` (6 endpoints)
**Reasoning module**: `reasoning/digital_twin.py` (671 lines — largest module)
**Frontend**: Fetches `GET /twin/compartments` + `GET /twin/pathways` + `GET /twin/optimize`, renders compartment cards + pathways table + optimal combos

**Hardcoded data**:
- `COMPARTMENTS` — 5 motor neuron compartments (soma, axon, NMJ, dendrites, nucleus) with properties
- `PATHWAYS` — ~8 signaling pathways with SMA state, activity level, compartment mapping
- `DRUGS` — drug-pathway interaction matrix
- Simulation engine (ODE-like weighted computation of drug effects across compartments)
- GPU-validated drug list

### B. Database Tables

```sql
CREATE TABLE twin_compartments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    compartment_name TEXT NOT NULL UNIQUE,   -- 'soma', 'axon', 'NMJ'
    description     TEXT,
    volume_fraction NUMERIC(4,3),
    key_processes   TEXT[],
    sma_deficits    TEXT[],
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE twin_pathways (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pathway_name    TEXT NOT NULL UNIQUE,
    sma_state       TEXT,                    -- 'reduced', 'hyperactive'
    activity_level  NUMERIC(3,2),           -- 0-1
    compartments    TEXT[],                  -- which compartments this pathway is in
    therapeutic_targets TEXT[],
    key_genes       TEXT[],
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE twin_drug_effects (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drug_name       TEXT NOT NULL,
    drug_id         UUID REFERENCES drugs(id),
    pathway_id      UUID REFERENCES twin_pathways(id),
    compartment_id  UUID REFERENCES twin_compartments(id),
    effect_magnitude NUMERIC(4,3),          -- -1 to +1
    effect_type     TEXT,                    -- 'activation', 'inhibition'
    evidence_level  TEXT,
    source_id       UUID REFERENCES sources(id),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (drug_name, pathway_id, compartment_id)
);

CREATE TABLE twin_simulations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drug_combination TEXT[] NOT NULL,
    result          JSONB NOT NULL,          -- full simulation output
    overall_score   NUMERIC(4,3),
    compartment_scores JSONB,
    computed_at     TIMESTAMPTZ DEFAULT NOW(),
    metadata        JSONB DEFAULT '{}'
);
```

**FKs**: `twin_drug_effects.drug_id -> drugs.id`, `.source_id -> sources.id`

**Seed data**: Yes — compartments, pathways, and drug-effect matrix.

### C. API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/twin/compartments` | Compartment model (existing) |
| GET | `/twin/pathways` | Pathway model (existing) |
| GET | `/twin/drugs` | Available drugs (existing) |
| POST | `/twin/simulate` | Run simulation (existing, keep computational) |
| GET | `/twin/optimize` | Optimal combos (existing) |
| POST | `/twin/simulate/temporal` | Time-series simulation (existing) |
| POST | `/admin/twin/drug-effects` | Add drug-pathway effect |
| PUT | `/admin/twin/drug-effects/{id}` | Update effect magnitude |
| POST | `/admin/twin/pathways` | Add pathway |

**Query params**: `drug` filter, `compartment`, `pathway`

### D. Data Sources

- **Literature**: Systems biology SMA models, drug mechanism papers
- **Databases**: KEGG (pathway data), Reactome, PharmGKB (drug-pathway interactions)
- **Computational**: Simulation engine is algorithmic — keep in Python, parameterize from DB

### E. Migration Strategy

1. Create 4 tables
2. Seed compartments, pathways, drug effects from Python constants
3. Keep simulation engine in Python but read parameters from DB
4. Cache simulation results in `twin_simulations` table
5. Add admin CRUD for drug effects (most frequently updated)

### F. Priority: **HIGH** — core computational tool, drug combination predictions

### G. Effort: **L** (5 files: migration, 3 table queries, route update)

---

## Section 11: Lab-OS (`/labos`)

### A. Current State

**Route file**: `api/routes/lab_os.py` (3 endpoints)
**Reasoning module**: `reasoning/lab_os.py` (436 lines)
**Frontend**: Fetches `GET /lab/assays` + `GET /lab/cloud-labs`, renders assay table + cloud lab cards

**Hardcoded data**:
- `ASSAY_LIBRARY` — 8 SMA assays with category, readout, timeline, cost, throughput
- `CLOUD_LABS` — 3 cloud lab integrations (Emerald, Strateos, Opentrons)
- `generate_experiment()` function — LLM-like experiment design from hypothesis text

### B. Database Tables

```sql
CREATE TABLE lab_assays (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assay_name      TEXT NOT NULL UNIQUE,
    category        TEXT,                    -- 'splicing', 'cell_viability', 'motor_function'
    readout         TEXT,                    -- 'RT-qPCR', 'Western blot'
    timeline        TEXT,                    -- '3-5 days'
    timeline_days   INTEGER,                -- numeric for sorting
    cost_estimate   TEXT,                    -- '$500-2000'
    cost_min        NUMERIC,                -- for filtering
    cost_max        NUMERIC,
    throughput      TEXT,                    -- 'medium', 'high'
    protocol_url    TEXT,
    required_equipment TEXT[],
    cell_types      TEXT[],
    description     TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE lab_cloud_integrations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lab_name        TEXT NOT NULL UNIQUE,    -- 'Emerald Cloud Lab'
    platform_type   TEXT,                    -- 'full_service', 'robotic', 'open_source'
    supported_assays TEXT[],
    api_available   BOOLEAN DEFAULT FALSE,
    pricing_model   TEXT,
    turnaround_time TEXT,
    capabilities    TEXT[],
    limitations     TEXT[],
    url             TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

**Seed data**: Yes — 8 assays + 3 cloud labs from Python constants.

### C. API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/lab/assays` | Assay library (existing) |
| GET | `/lab/cloud-labs` | Cloud lab integrations (existing) |
| GET | `/lab/design` | Generate experiment from hypothesis (existing, keep) |
| POST | `/admin/lab/assays` | Add assay |
| PUT | `/admin/lab/assays/{id}` | Update assay |
| POST | `/admin/lab/cloud-labs` | Add cloud lab |

**Query params**: `category`, `max_cost`, `max_timeline_days`, `throughput`

### D. Data Sources

- **Manual curation**: Assay protocols from lab experience and literature
- **Vendor data**: Cloud lab capabilities from Emerald, Strateos, Opentrons websites
- **Literature**: SMA assay optimization papers

### E. Migration Strategy

1. Create 2 tables
2. Seed from Python constants
3. Keep `generate_experiment()` as computational logic (references DB assays)
4. Update routes, add admin CRUD

### F. Priority: **MEDIUM** — useful for experiment planning but mostly static reference

### G. Effort: **S** (2 files)

---

## Section 12: Federated Learning (`/federated`)

### A. Current State

**Route file**: `api/routes/federated.py` (4 endpoints)
**Reasoning module**: `reasoning/federated.py` (333 lines)
**Frontend**: Fetches `GET /federated/protocols` + `GET /federated/data-tiers` + `GET /federated/omop`, renders protocols table + tier cards + OMOP mapping table

**Hardcoded data**:
- `FL_PROTOCOLS` — ~5 federated learning protocols with algorithm, use case, utility/privacy scores
- `DATA_SHARING_TIERS` — 4 tiers (open, controlled, federated, secure enclave)
- `OMOP_MAPPINGS` — ~10 SMA concept-to-OMOP vocabulary mappings
- Privacy budget calculator (mathematical formula — not data)

### B. Database Tables

```sql
CREATE TABLE federated_protocols (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    protocol_name   TEXT NOT NULL UNIQUE,
    algorithm       TEXT,                    -- 'FedAvg', 'SCAFFOLD', 'FedProx'
    use_case        TEXT,
    min_participants INTEGER,
    utility_score   NUMERIC(3,2),           -- 0-1
    privacy_score   NUMERIC(3,2),           -- 0-1
    communication_rounds INTEGER,
    description     TEXT,
    reference       TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE federated_data_tiers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tier_level      INTEGER NOT NULL UNIQUE, -- 1-4
    tier_name       TEXT NOT NULL,            -- 'Open', 'Controlled'
    description     TEXT,
    data_types      TEXT[],
    privacy_level   TEXT,
    access_requirements TEXT[],
    examples        TEXT[],
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE federated_omop_mappings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sma_concept     TEXT NOT NULL,
    omop_domain     TEXT,                    -- 'Condition', 'Measurement', 'Drug'
    concept_name    TEXT,
    vocabulary      TEXT,                    -- 'SNOMED', 'LOINC', 'RxNorm'
    concept_id      TEXT,                    -- OMOP concept ID
    notes           TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (sma_concept, omop_domain)
);
```

**Seed data**: Yes — protocols + tiers + OMOP mappings from Python constants.

### C. API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/federated/protocols` | FL protocols (existing) |
| GET | `/federated/omop` | OMOP mappings (existing) |
| GET | `/federated/privacy-budget` | Privacy calculator (existing, keep computational) |
| GET | `/federated/data-tiers` | Data sharing tiers (existing) |
| POST | `/admin/federated/protocols` | Add protocol |
| POST | `/admin/federated/omop` | Add OMOP mapping |
| PUT | `/admin/federated/omop/{id}` | Update mapping |

**Query params**: `algorithm`, `min_utility`, `min_privacy`, `omop_domain`

### D. Data Sources

- **Literature**: FL in healthcare surveys (PMID: 34907070, 35084367)
- **Databases**: OMOP CDM v5.4 documentation, OHDSI Atlas
- **Manual curation**: SMA-specific OMOP mappings

### E. Migration Strategy

1. Create 3 tables
2. Seed from Python constants
3. Keep privacy budget calculator as pure math in Python
4. Update routes, add admin CRUD

### F. Priority: **LOW** — infrastructure concept, not directly science-producing

### G. Effort: **S** (2 files)

---

## Section 13: Translation & Impact (`/translate`)

### A. Current State

**Route file**: `api/routes/translation.py` (6 endpoints)
**Reasoning module**: `reasoning/translation.py` (1,096 lines — second largest)
**Frontend**: Fetches `GET /translate/regulatory` + `GET /translate/grants` + `GET /translate/validation`, renders regulatory table + grant cards + validation pipeline table

**Hardcoded data**:
- `REGULATORY_PATHWAYS` — ~6 FDA/EMA pathways with timeline, SMA drugs using each, relevance
- `GRANT_TEMPLATES` — ~4 templates (NIH R01, NIH R21, ERC StG, CURE SMA) with format, budget, structure
- `VALIDATION_PIPELINE` — 5-level pipeline (computational -> in vitro -> in vivo -> preclinical -> IND)
- `GRANT_FORMATS` dict — detailed export specifications per funder
- Grant text generation functions (use convergence scores, claims, etc.)

### B. Database Tables

```sql
CREATE TABLE translation_regulatory (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pathway_name    TEXT NOT NULL UNIQUE,    -- 'Orphan Drug Designation'
    agency          TEXT NOT NULL,           -- 'FDA', 'EMA', 'Both'
    designation     TEXT,                    -- 'Orphan', 'Breakthrough', 'Fast Track'
    typical_timeline TEXT,
    sma_drugs_using TEXT[],                  -- which approved SMA drugs used this
    relevance_score NUMERIC(3,2),
    requirements    TEXT[],
    benefits        TEXT[],
    url             TEXT,
    source_id       UUID REFERENCES sources(id),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE translation_grant_templates (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_key    TEXT NOT NULL UNIQUE,    -- 'NIH_R01'
    funder          TEXT NOT NULL,           -- 'NIH', 'ERC', 'CURE SMA'
    mechanism       TEXT,                    -- 'R01', 'R21', 'StG'
    budget_range    TEXT,
    duration_years  INTEGER,
    page_limit      INTEGER,
    sections        JSONB,                   -- section specs as JSON
    description     TEXT,
    url             TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE translation_validation_levels (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    level_number    INTEGER NOT NULL UNIQUE,
    level_name      TEXT NOT NULL,           -- 'Computational Validation'
    assays          TEXT[],
    timeline        TEXT,
    cost_estimate   TEXT,
    go_nogo_criteria TEXT[],
    success_rate    NUMERIC(3,2),            -- historical success rate
    description     TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

**FKs**: `translation_regulatory.source_id -> sources.id`

**Seed data**: Yes — all three lists + GRANT_FORMATS from Python constants.

### C. API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/translate/regulatory` | Regulatory pathways (existing) |
| GET | `/translate/grants` | Grant templates (existing) |
| GET | `/translate/grants/formats` | Format specs (existing) |
| GET | `/translate/grants/export/{symbol}` | Generate grant text (existing, keep computational) |
| GET | `/translate/validation` | Validation pipeline (existing) |
| POST | `/translate/validate` | Validate hypothesis through pipeline (existing) |
| POST | `/admin/translate/regulatory` | Add regulatory pathway |
| PUT | `/admin/translate/regulatory/{id}` | Update pathway |
| POST | `/admin/translate/grants` | Add grant template |
| POST | `/admin/translate/validation` | Add validation level |

**Query params**: `agency`, `designation`, `funder`

### D. Data Sources

- **Manual curation**: FDA/EMA guidelines, grant program announcements
- **Databases**: FDA Orange Book, EMA public assessment reports
- **Literature**: Regulatory science papers for rare diseases

### E. Migration Strategy

1. Create 3 tables
2. Seed from Python constants
3. Keep grant text generation as computational (reads from DB + convergence scores)
4. Keep hypothesis validation logic in Python
5. Update routes, add admin CRUD

### F. Priority: **MEDIUM** — useful reference for grant writing and regulatory strategy

### G. Effort: **M** (3 files — translation.py is large and complex)

---

## Dead-Link Sections (Already Have Backend Code)

These 4 sections appear in the frontend HTML with full data tables and JS fetch calls. They are NOT dead links — they already work end-to-end just like the 13 sections above.

### Section A: Prime Editing Feasibility (`/prime`)

**HTML section id**: `prime` (line 2061)
**Route**: `api/routes/prime_edit.py` — `GET /prime-editing/feasibility`
**Reasoning**: `reasoning/prime_editor.py` (405 lines)
**Frontend fetch**: `fetch(API + '/prime-editing/feasibility')` (line 7483)
**Displays**: Prime editing designs (PE2/PE3/PEmax for SMN2 C6T, ISS-N1, ESE) + therapy comparison cards

**DB migration needed**:
```sql
CREATE TABLE prime_editing_designs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    edit_name       TEXT NOT NULL,           -- 'SMN2 C6T Correction'
    pe_system       TEXT,                    -- 'PE2', 'PE3', 'PEmax'
    target_gene     TEXT DEFAULT 'SMN2',
    target_region   TEXT,
    pegrna_spacer   TEXT,
    pbs_length      INTEGER,
    rt_template     TEXT,
    nick_distance   INTEGER,
    efficiency_estimate NUMERIC(4,2),
    off_target_risk TEXT,
    delivery_vector TEXT,
    comparison_with TEXT[],                  -- existing therapy names
    source_id       UUID REFERENCES sources(id),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (edit_name, pe_system)
);
```
**Priority**: HIGH | **Effort**: S

### Section B: MD Simulations (`/mdsim`)

**HTML section id**: `mdsim` (line 2069)
**Route**: `api/routes/md_simulation.py` — `GET /md/simulations`, `GET /md/generate/{sim_key}`
**Reasoning**: `reasoning/md_generator.py` (576 lines)
**Frontend fetch**: `fetch(API + '/md/simulations')` (line 7542)
**Displays**: 6 simulation templates (SMN oligomerization, hnRNP A1-ISS-N1, risdiplam, NCALD, PLS3, SMN-Gemin2)

**DB migration needed**:
```sql
CREATE TABLE md_simulations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sim_key         TEXT NOT NULL UNIQUE,    -- 'smn_oligomerization'
    sim_name        TEXT NOT NULL,
    target          TEXT,
    simulation_type TEXT,                    -- 'protein-protein', 'ligand-binding'
    pdb_id          TEXT,
    atom_count      INTEGER,
    sim_time_ns     NUMERIC(6,1),
    gpu_hours       NUMERIC(5,1),
    forcefield      TEXT DEFAULT 'AMBER ff14SB',
    water_model     TEXT DEFAULT 'TIP3P',
    description     TEXT,
    scripts         JSONB DEFAULT '{}',      -- generated Python scripts
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```
**Priority**: MEDIUM | **Effort**: S

### Section C: RNA-Binding Prediction (`/rnabind`)

**HTML section id**: `rnabind` (line 2171)
**Route**: `api/routes/rna_binding.py` — `GET /rna/targets`, `GET /rna/modulators`, `POST /rna/predict`, `POST /rna/benchmark`
**Reasoning**: `reasoning/rna_binding.py` (313 lines)
**Frontend fetch**: `fetch(API + '/rna/targets')` (line 8238), `fetch(API + '/rna/modulators')` (line 8288)
**Displays**: RNA target sites table (6 sites: ISS-N1, 5'ss, ESE2, ESS, branch point, TSL2) + known modulators table (risdiplam, branaplam, etc.)

**DB migration needed**:
```sql
CREATE TABLE rna_target_sites (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    site_name       TEXT NOT NULL UNIQUE,    -- 'ISS-N1'
    gene_symbol     TEXT DEFAULT 'SMN2',
    location        TEXT,                    -- 'intron 7, pos 10-24'
    sequence_motif  TEXT,
    binding_proteins TEXT[],
    druggability    NUMERIC(3,2),
    approved_drug   TEXT,
    structure_known BOOLEAN DEFAULT FALSE,
    source_id       UUID REFERENCES sources(id),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE rna_known_modulators (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    compound_name   TEXT NOT NULL,
    drug_id         UUID REFERENCES drugs(id),
    mw              NUMERIC(6,1),
    logp            NUMERIC(4,2),
    target_site     TEXT,                    -- 'ISS-N1', '5ss/U1'
    ec50_nm         NUMERIC(8,2),
    status          TEXT,                    -- 'approved', 'phase3', 'discontinued'
    mechanism       TEXT,
    source_id       UUID REFERENCES sources(id),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (compound_name, target_site)
);
```
**Priority**: HIGH | **Effort**: M

### Section D: Dual-Target Molecules (`/dualtarget`)

**HTML section id**: `dualtarget` (line 2187)
**Route**: `api/routes/dual_target.py` — `GET /screen/dual-target`, `GET /screen/dual-target/channels`, `GET /screen/dual-target/synergy`
**Reasoning**: `reasoning/dual_target.py` (283 lines)
**Frontend fetch**: `fetch(API + '/screen/dual-target')` (line 8334)
**Displays**: Dual-target candidates table (compound, SMN2 score, ion channel, channel score, BBB, composite, status)

**DB migration needed**:
```sql
CREATE TABLE dual_target_candidates (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    compound_name   TEXT NOT NULL,
    drug_id         UUID REFERENCES drugs(id),
    smn2_score      NUMERIC(3,2),
    ion_channel     TEXT,
    channel_gene    TEXT,
    channel_score   NUMERIC(3,2),
    bbb_score       NUMERIC(3,2),
    composite_score NUMERIC(3,2),
    status          TEXT,                    -- 'preclinical', 'clinical', 'approved'
    mechanism       TEXT,
    synergy_potential NUMERIC(3,2),
    source_id       UUID REFERENCES sources(id),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (compound_name, ion_channel)
);

CREATE TABLE dual_target_channel_map (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel_gene    TEXT NOT NULL UNIQUE,
    channel_name    TEXT,
    channel_type    TEXT,
    available_drugs TEXT[],
    sma_relevance   TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```
**Priority**: HIGH | **Effort**: M

---

## Implementation Plan

### Phase 1: Core Science (Sprint 1, ~3 sessions)

| # | Section | Priority | Effort | Migration File |
|---|---------|----------|--------|----------------|
| 1 | CRISPR Guide Design | HIGH | M | `012_crispr_tables.sql` |
| 2 | AAV Capsid Evaluation | HIGH | M | `013_aav_tables.sql` |
| 4 | Spatial Multi-Omics | HIGH | M | `014_spatial_tables.sql` |
| 7 | Multisystem SMA | HIGH | M | `015_multisystem_tables.sql` |
| 10 | Digital Twin | HIGH | L | `016_twin_tables.sql` |
| A | Prime Editing | HIGH | S | `017_prime_editing_tables.sql` |
| C | RNA-Binding | HIGH | M | `018_rna_binding_tables.sql` |
| D | Dual-Target | HIGH | M | `019_dual_target_tables.sql` |

### Phase 2: Advanced Modules (Sprint 2, ~2 sessions)

| # | Section | Priority | Effort | Migration File |
|---|---------|----------|--------|----------------|
| 3 | Gene Edit Versioning | MEDIUM | S | `020_gene_versions_table.sql` |
| 5 | Regeneration Signatures | MEDIUM | M | `021_regeneration_tables.sql` |
| 6 | NMJ Retrograde Signaling | MEDIUM | M | `022_nmj_tables.sql` |
| 8 | Bioelectric Reprogramming | MEDIUM | M | `023_bioelectric_tables.sql` |
| 13 | Translation & Impact | MEDIUM | M | `024_translation_tables.sql` |
| B | MD Simulations | MEDIUM | S | `025_md_simulations_table.sql` |

### Phase 3: Infrastructure (Sprint 3, ~1 session)

| # | Section | Priority | Effort | Migration File |
|---|---------|----------|--------|----------------|
| 9 | Cross-Species Splicing | LOW | S | `026_splicing_map_table.sql` |
| 11 | Lab-OS | MEDIUM | S | `027_lab_os_tables.sql` |
| 12 | Federated Learning | LOW | S | `028_federated_tables.sql` |

### Shared Work (before Phase 1)

1. **Admin auth middleware**: Add API key check for all `/admin/*` routes
2. **Migration runner**: Script to apply SQL migrations in order (check `db/migrations/` naming)
3. **Seed script template**: Generic `seed_from_module.py` that extracts Python dataclass lists into INSERT statements

### Per-Section Agent Instructions

Each section can be implemented by a single agent in one session. The agent should:

1. Read the reasoning module (e.g., `reasoning/crispr_designer.py`)
2. Write the migration SQL file
3. Write a seed script (or add seed data as SQL INSERTs in migration)
4. Add async DB query functions to the reasoning module (keep existing functions as fallback)
5. Update the route file to try DB first, fall back to hardcoded
6. Add admin POST/PUT/DELETE endpoints to the route file
7. Test: start server, verify GET endpoints return same data as before

### Fallback Pattern (use in all routes)

```python
@router.get("/section/data")
async def get_data():
    """Try DB first, fall back to hardcoded."""
    from ...core.database import fetch
    try:
        rows = await fetch("SELECT * FROM section_table ORDER BY created_at")
        if rows:
            return {"data": [dict(r) for r in rows], "source": "database"}
    except Exception:
        pass
    # Fallback to hardcoded
    return get_hardcoded_data()
```

This ensures zero downtime during migration — sections keep working with hardcoded data until DB is populated.

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Sections to migrate | 17 (13 listed + 4 "dead links" that are actually working) |
| New DB tables needed | ~35 |
| Reasoning modules affected | 17 files (~7,000 lines) |
| Route files affected | ~10 files (some share `advanced_analytics.py`) |
| Total estimated effort | ~6 agent sessions |
| HIGH priority sections | 8 |
| MEDIUM priority sections | 7 |
| LOW priority sections | 2 |
