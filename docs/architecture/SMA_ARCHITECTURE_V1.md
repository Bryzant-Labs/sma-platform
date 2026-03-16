# SMA Research Platform -- Architecture v1

Version: 1.0
Date: 2026-03-15
Author: Christian Fischer
Status: Phase A (Evidence Graph) -- operational

---

## 1. Platform Identity

The SMA Research Platform is an open-source, evidence-first drug research system for Spinal Muscular Atrophy (SMA). It ingests published literature, clinical trial data, and omics datasets, extracts structured claims, scores evidence, and generates testable biological hypotheses.

**Who it is for:**

- Researchers working on SMA biology, SMN-dependent and SMN-independent therapeutic targets
- Computational biologists evaluating target prioritization for rare neuromuscular disease
- Anyone who wants structured, traceable access to the SMA evidence base

**What it does:**

- Automated daily ingestion from PubMed, ClinicalTrials.gov, and GEO
- LLM-assisted extraction of structured biological claims from paper abstracts
- Evidence scoring based on method strength, sample size, replication, and p-value
- Hypothesis generation that synthesizes converging claims per target
- A single-page frontend that renders the full evidence graph with no server-side templating

**What it does NOT do:**

- It is not a drug company. There is no marketing, no hype, no fundraising pitch.
- It does not replace wet-lab validation. Every hypothesis is flagged with its evidence gaps.
- GPU compute infrastructure is being built (Phase G — see `docs/plans/2026-03-16-gpu-infrastructure-design.md`).
- It does not store patient data. There is no PII anywhere in the system.

---

## 2. Data Model

### 2.1 Tables

The schema defines 11 tables across two dialects: a canonical PostgreSQL schema (`db/schema.sql`) and a SQLite mirror (`db/schema_sqlite.sql`). The SQLite version replaces UUID with TEXT hex IDs, arrays with JSON strings, JSONB with TEXT, and TIMESTAMPTZ with TEXT.

| Table | Purpose | PK | Key Constraints |
|---|---|---|---|
| `sources` | Papers, preprints, knowledgebase entries | UUID | `UNIQUE (source_type, external_id)`. Types: pubmed, clinicaltrials, geo, pride, knowledgebase, preprint, manual |
| `targets` | Genes, proteins, pathways, phenotypes | UUID | `UNIQUE (symbol, target_type, organism)`. Types: gene, protein, pathway, cell_state, phenotype, other |
| `drugs` | Approved therapies and pipeline candidates | UUID | `drug_type` enum, `approval_status` enum. Targets stored as UUID array (PG) or JSON (SQLite) |
| `trials` | Clinical trials from ClinicalTrials.gov | UUID | `UNIQUE (nct_id)`. Interventions as JSONB |
| `datasets` | Omics datasets (GEO, PRIDE, ArrayExpress) | UUID | `UNIQUE (accession)`. `evidence_tier`: tier1/tier2/tier3. `usage_class`: use_now/use_later/optional |
| `claims` | Factual assertions extracted from sources | UUID | `claim_type` enum (12 types). `confidence` in [0, 1]. `subject_id`/`object_id` are soft FKs |
| `evidence` | Links claims to their supporting sources | UUID | `UNIQUE (claim_id, source_id)`. FK CASCADE to claims and sources. Stores excerpt, method, p_value, effect_size, sample_size |
| `graph_edges` | Knowledge graph relationships between targets | UUID | `UNIQUE (src_id, dst_id, relation)`. FK to targets. Direction: undirected/src_to_dst/dst_to_src. Effect: activates/inhibits/associates/unknown |
| `hypotheses` | LLM-generated testable hypotheses | UUID | `hypothesis_type` enum. `status`: proposed/under_review/validated/refuted/published. `supporting_evidence` and `contradicting_evidence` as UUID arrays |
| `ingestion_log` | Audit trail for every ingestion run | UUID | Tracks source_type, items_found/new/updated, errors, duration_secs |
| `agent_runs` | Execution log for AI agents (planned) | UUID | agent_name, task_type, status, input/output JSONB, duration |

### 2.2 Claim Types

The 12 valid claim types reflect the biology of SMA:

```
gene_expression       -- e.g. "SMN2 copy number correlates with disease severity"
protein_interaction   -- e.g. "SMN protein interacts with Gemin2 in snRNP assembly"
pathway_membership    -- e.g. "PLS3 acts in the actin cytoskeleton pathway"
drug_target           -- e.g. "Nusinersen targets SMN2 pre-mRNA"
drug_efficacy         -- e.g. "Risdiplam improves motor function in Type 2 SMA"
biomarker             -- e.g. "Neurofilament light chain is elevated in SMA patients"
splicing_event        -- e.g. "SMN2 exon 7 skipping produces truncated SMN protein"
neuroprotection       -- e.g. "STMN2 maintains axonal integrity in motor neurons"
motor_function        -- e.g. "HFMSE scores improve after 12 months on nusinersen"
survival              -- e.g. "Event-free survival at 14 months was 66% with onasemnogene"
safety                -- e.g. "Thrombocytopenia observed in risdiplam Phase 3 trial"
other                 -- Catch-all for claims that do not fit the above
```

### 2.3 Entity Relationship Diagram

```
                              +-------------+
                              |   targets   |
                              |-------------|
                              | id (PK)     |
                              | symbol      |
                              | target_type |
                              | organism    |
                              +------+------+
                                     |
                      +--------------+--------------+
                      |              |              |
               subject_id     src_id/dst_id    object_id
                      |              |              |
               +------+------+  +---+--------+  +--+--+
               |   claims    |  |graph_edges  |  |     |
               |-------------|  |-------------|  |     |
               | id (PK)     |  | id (PK)     |  |     |
               | claim_type  |  | relation    |  |     |
               | predicate   |  | direction   |  +-----+
               | confidence  |  | effect      |
               +------+------+  | confidence  |
                      |         +-------------+
                      |
               +------+------+
               |  evidence   |
               |-------------|
               | id (PK)     |
               | claim_id FK-+--------> claims.id  (CASCADE)
               | source_id FK+--------> sources.id (CASCADE)
               | excerpt     |
               | method      |
               | p_value     |
               | effect_size |
               | sample_size |
               +-------------+

  +-------------+    +-------------+    +-------------+    +--------------+
  |   sources   |    |    drugs    |    |   trials    |    |   datasets   |
  |-------------|    |-------------|    |-------------|    |--------------|
  | id (PK)     |    | id (PK)     |    | id (PK)     |    | id (PK)      |
  | source_type |    | drug_type   |    | nct_id (UQ) |    | accession(UQ)|
  | external_id |    | mechanism   |    | status      |    | modality     |
  | title       |    | approval_   |    | phase       |    | evidence_    |
  | abstract    |    |   status    |    | enrollment  |    |   tier       |
  | pub_date    |    | targets[]   |    | sponsor     |    | tissue       |
  +-------------+    +-------------+    +-------------+    +--------------+

  +---------------+    +--------------+
  | hypotheses    |    |ingestion_log |
  |---------------|    |--------------|
  | id (PK)       |    | id (PK)      |
  | hypothesis_   |    | source_type  |
  |   type        |    | items_found  |
  | title         |    | items_new    |
  | description   |    | duration_secs|
  | confidence    |    | run_at       |
  | status        |    +--------------+
  | supporting_   |
  |   evidence[]  |
  +---------------+
```

### 2.4 Data Flow

```
PubMed/ClinicalTrials/GEO  -->  sources / trials / datasets  (ingestion)
                                        |
                                        v
                                     claims     (LLM extraction from abstracts)
                                        |
                                        v
                                    evidence    (links claim <-> source with excerpt/method)
                                        |
                                        v
                                   hypotheses   (LLM synthesis across targets)
```

### 2.5 Current Data Volumes

| Table | Count | Notes |
|---|---|---|
| sources | ~180 | PubMed papers with abstracts |
| targets | 10 | SMN1, SMN2, STMN2, PLS3, NCALD, UBA1, SMN Protein, mTOR, + phenotypes |
| drugs | 7 | 3 approved (nusinersen, risdiplam, onasemnogene) + 4 pipeline |
| trials | ~449 | All SMA trials from ClinicalTrials.gov |
| datasets | 7 | Curated GEO datasets (GSE69175, GSE108094, GSE208629, etc.) |
| claims | 700+ | LLM-extracted from paper abstracts |
| evidence | 700+ | One evidence link per claim-source pair |
| hypotheses | ~10 | One per target with sufficient claims |

---

## 3. API Layer

### 3.1 Application Factory

The API is built with FastAPI via `create_app()` in `src/sma_platform/api/app.py`. The lifespan context manager initializes the database pool on startup and closes it on shutdown. CORS is permissive (`allow_origins=["*"]`) for the public research use case.

### 3.2 Endpoints

All API routes are mounted under the `/api/v2` prefix.

**Stats**

| Method | Path | Description |
|---|---|---|
| GET | `/api/v2/stats` | Row counts for all major tables |

**Targets**

| Method | Path | Description |
|---|---|---|
| GET | `/api/v2/targets` | List targets. Filters: `target_type`, `limit`, `offset` |
| GET | `/api/v2/targets/{target_id}` | Get target by UUID |
| GET | `/api/v2/targets/symbol/{symbol}` | Get target by gene symbol (case-insensitive) |
| POST | `/api/v2/targets` | Create or upsert target |

**Clinical Trials**

| Method | Path | Description |
|---|---|---|
| GET | `/api/v2/trials` | List trials. Filters: `status`, `phase`, `limit`, `offset` |
| GET | `/api/v2/trials/{trial_id}` | Get trial by UUID |
| GET | `/api/v2/trials/nct/{nct_id}` | Get trial by NCT number |

**Drugs**

| Method | Path | Description |
|---|---|---|
| GET | `/api/v2/drugs` | List drugs. Filters: `approval_status`, `drug_type`, `limit`, `offset` |
| GET | `/api/v2/drugs/{drug_id}` | Get drug by UUID |
| GET | `/api/v2/drugs/name/{name}` | Get drug by generic name |

**Datasets**

| Method | Path | Description |
|---|---|---|
| GET | `/api/v2/datasets` | List datasets. Filters: `evidence_tier`, `modality`, `organism`, `limit`, `offset` |
| GET | `/api/v2/datasets/{dataset_id}` | Get dataset by UUID |
| GET | `/api/v2/datasets/accession/{accession}` | Get dataset by GEO/PRIDE accession |

**Evidence & Claims**

| Method | Path | Description |
|---|---|---|
| GET | `/api/v2/claims` | List claims. Filters: `claim_type`, `limit`, `offset`. Ordered by confidence DESC |
| GET | `/api/v2/claims/{claim_id}` | Get single claim |
| GET | `/api/v2/claims/{claim_id}/evidence` | Get all evidence rows supporting a claim, joined with source metadata |
| GET | `/api/v2/sources` | List source papers. Filters: `source_type`, `limit`, `offset` |
| GET | `/api/v2/hypotheses` | List hypotheses. Filters: `status`, `limit`, `offset`. Ordered by confidence DESC |

**Ingestion & Reasoning Triggers**

| Method | Path | Description |
|---|---|---|
| POST | `/api/v2/ingest/pubmed` | Pull recent SMA papers. Param: `days_back` (default 7) |
| POST | `/api/v2/ingest/trials` | Pull all SMA trials from ClinicalTrials.gov |
| POST | `/api/v2/extract/claims` | Extract claims from all unprocessed paper abstracts using Claude Haiku |
| POST | `/api/v2/generate/hypotheses` | Generate hypothesis cards for all targets |
| POST | `/api/v2/generate/hypothesis/{target_id}` | Generate hypothesis for a single target |

**Utility**

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check. Returns `{"status": "ok", "version": "0.1.0"}` |
| GET | `/docs` | Auto-generated FastAPI/Swagger documentation |

---

## 4. Ingestion Pipeline

### 4.1 PubMed Adapter

**File:** `src/sma_platform/ingestion/adapters/pubmed.py`
**Library:** Biopython `Bio.Entrez`
**Rate limit:** 3 req/sec without API key, 10 req/sec with NCBI API key

**Search queries** (7 queries, deduplicated by PMID):

```
"spinal muscular atrophy"
"SMN1" OR "SMN2" AND "spinal muscular atrophy"
"STMN2" AND ("motor neuron" OR "SMA")
"nusinersen" OR "Spinraza"
"risdiplam" OR "Evrysdi"
"onasemnogene" OR "Zolgensma"
"spinal muscular atrophy" AND ("gene therapy" OR "antisense oligonucleotide")
```

**Flow:**

1. `search_recent_sma(days_back=7)` runs all 7 queries via `Entrez.esearch`
2. Collects unique PMIDs across queries
3. `fetch_paper_details(pmids)` via `Entrez.efetch` (XML) extracts: PMID, title, authors, journal, pub_date, DOI, abstract, URL
4. Ingestion route upserts into `sources` table (`ON CONFLICT ... DO UPDATE`)
5. Logs result to `ingestion_log`

### 4.2 ClinicalTrials.gov Adapter

**File:** `src/sma_platform/ingestion/adapters/clinicaltrials.py`
**API:** ClinicalTrials.gov v2 REST API (`https://clinicaltrials.gov/api/v2`)
**Library:** httpx (async)
**Rate limit:** 5 req/sec (no API key required)

**Flow:**

1. `fetch_all_sma_trials()` makes two paginated searches:
   - Active trials (RECRUITING, NOT_YET_RECRUITING, ENROLLING_BY_INVITATION, ACTIVE_NOT_RECRUITING), up to 500
   - Completed trials, up to 500
2. Deduplicates by NCT ID
3. Extracts from `protocolSection`: identification, status, design, description, arms/interventions, sponsors
4. Ingestion route upserts into `trials` table (`ON CONFLICT (nct_id) DO UPDATE`)

### 4.3 GEO Adapter

**File:** `src/sma_platform/ingestion/adapters/geo.py`
**Library:** Biopython `Bio.Entrez` (database: `gds`)

**Curated dataset inventory** (5 known SMA datasets):

| Accession | Tier | Modality | Tissue |
|---|---|---|---|
| GSE69175 | tier1 | rna-seq | motor neurons |
| GSE108094 | tier1 | rna-seq | motor neurons |
| GSE208629 | tier1 | scrna-seq | spinal cord |
| GSE87281 | tier2 | rna-seq | spinal cord |
| GSE65470 | tier3 | transcriptomics | nmj |

**Flow:**

1. `fetch_known_datasets()` iterates the curated list
2. For each accession: `Entrez.esearch` then `Entrez.esummary` to get title, summary, organism, platform, sample count, pub date
3. Enriches with tier/modality/tissue from the curated inventory
4. Stored in `datasets` table

### 4.4 Ingestion Audit

Every ingestion run writes a row to `ingestion_log` with:
- `source_type` (pubmed, clinicaltrials, geo)
- `query` description
- `items_found`, `items_new`, `items_updated`
- `errors` (capped at first 10)
- `duration_secs`

---

## 5. Reasoning Pipeline

### 5.1 Claim Extraction

**File:** `src/sma_platform/reasoning/claim_extractor.py`
**Model:** Claude Haiku 4.5 (`claude-haiku-4-5-20251001`)
**API:** Direct httpx POST to `https://api.anthropic.com/v1/messages`

**Process:**

1. `process_all_unprocessed()` finds sources with no evidence rows (LEFT JOIN WHERE NULL)
2. For each source, sends the abstract to Claude with a structured extraction prompt
3. Claude returns a JSON array of claims, each with:
   - `predicate`: the factual assertion
   - `claim_type`: mapped to the 12 valid types (with fallback mapping for LLM-generated variants)
   - `confidence`: 0.0-1.0
   - `subject`/`subject_type`/`object`/`object_type`: entities
   - `related_targets`: gene symbols
   - `excerpt`: supporting sentence from the abstract
4. Each claim is inserted into `claims` table
5. Subject/object are resolved to target IDs via symbol lookup
6. An `evidence` row is created linking claim to source with method `llm_abstract_extraction`

**Type normalization:** The extractor maps LLM-generated types to valid DB types:
```python
"mechanism"       -> "pathway_membership"
"efficacy"        -> "drug_efficacy"
"drug_mechanism"  -> "drug_target"
"gene_regulation" -> "gene_expression"
"splicing"        -> "splicing_event"
"neuroprotective" -> "neuroprotection"
"motor"           -> "motor_function"
```

### 5.2 Evidence Scoring

**File:** `src/sma_platform/reasoning/scorer.py`

Computes a confidence score for each claim based on its evidence rows. The score is a weighted average incorporating:

**Method strength weights:**

| Method | Weight |
|---|---|
| randomized_controlled_trial | 1.0 |
| meta_analysis | 0.95 |
| cohort_study | 0.8 |
| case_control | 0.7 |
| in_vivo | 0.7 |
| in_vitro | 0.6 |
| case_report | 0.5 |
| in_silico | 0.4 |
| expert_opinion | 0.3 |

**P-value bonus:** +0.10 if p < 0.01, +0.05 if p < 0.05.
**Sample size factor:** `min(1.0, n / 100)`. Default 0.5 if unknown.
**Final score:** `(method_weight + p_bonus) * sample_factor`, clamped to [0, 1].

**Evidence tier multipliers** (defined but not yet applied in scoring):

| Tier | Multiplier |
|---|---|
| tier1 | 1.0 |
| tier2 | 0.7 |
| tier3 | 0.4 |

### 5.3 Hypothesis Generation

**File:** `src/sma_platform/reasoning/hypothesis_generator.py`
**Model:** Claude Haiku 4.5 (`claude-haiku-4-5-20251001`)

**Process:**

1. `generate_all_hypotheses()` clears existing hypotheses (full regeneration) and iterates all targets
2. For each target, `get_target_claims(target_id)` collects:
   - Direct claims (subject_id = target_id)
   - Metadata matches (target symbol appears in claim metadata JSON)
   - Deduplicated by claim ID
3. Claims are formatted (max 20) with PMID and confidence, sent to Claude
4. Claude returns a hypothesis card with:
   - `title`: one-sentence hypothesis statement
   - `description`: 2-3 paragraph scientific rationale
   - `confidence`: 0.0-1.0
   - `status`: proposed / needs_validation / strong_candidate
   - `modality_suggestion`: small_molecule / aso / gene_therapy / crispr / antibody / combination / unclear
   - `key_questions`: 2-3 validation questions
5. Stored in `hypotheses` table with metadata (target symbol, claim count, source count, model, timestamp)

**Fallback:** If no API key is available, `_generate_basic_hypothesis()` creates a statistical summary without LLM reasoning: average confidence, claim type distribution, source count.

---

## 6. UCM Layer

**Unified Canonical Model** -- a flat-file data pipeline for offline analysis and interoperability.

### 6.1 Architecture

**Files:** `src/sma_platform/ucm/builder.py`, `src/sma_platform/ucm/utils.py`

The UCM layer reads TSV files from a raw data directory and produces validated, normalized artifacts:

```
data/raw/              data/processed/
  nodes.tsv      -->     nodes.parquet
  edges.tsv      -->     edges.parquet
  evidence.tsv   -->     evidence.tsv (validated)
```

### 6.2 Schemas

**Nodes** (required: `node_id`, `node_type`, `label`; optional: `synonyms`, `namespace`, `metadata_json`):
Represent biological entities -- genes, proteins, pathways, phenotypes.

**Edges** (required: `src`, `dst`, `relation`, `confidence`; optional: `direction`, `effect`, `evidence_ids`, `metadata_json`):
Represent relationships. Confidence is clamped to [0.0, 1.0].

**Evidence** (required: `evidence_id`, `source_type`, `source_ref`; optional: `notes`, `date`, `checksum`):
Provenance records linking edges to their source publications.

### 6.3 Utilities

| Function | Purpose |
|---|---|
| `sha256_file(path)` | Content-addressable checksums for data lineage |
| `read_tsv(path)` | Safe TSV read with `dtype=str`, returns None if missing |
| `normalize_confidence(x)` | Clamps to [0.0, 1.0] |
| `now_iso()` | UTC timestamp |
| `stable_id(prefix, *parts)` | Deterministic SHA-256 IDs for non-biological entities |

---

## 7. Site Layer

**File:** `frontend/index.html`

A single-page application served as static HTML. Zero build step. No framework.

### 7.1 Design

- Inter font, monochrome light theme, no rounded corners
- CSS variables for theming: `--bg: #fafafa`, `--panel: #ffffff`, `--text: #1a1a1a`, `--accent: #1a56db`
- JetBrains Mono for data cells, IDs, and accession numbers
- Color-coded badges: green (active/approved/tier1), blue (gene/phase3), amber (phase2/tier2), gray (default), red (terminated/discontinued)

### 7.2 Sections

1. **Stats bar** -- live counts for all 8 entity types
2. **Targets** -- gene/protein/pathway table with identifiers and descriptions
3. **Clinical Trials** -- filterable (All / Recruiting / Phase 3 / Completed) with NCT links
4. **Drugs & Therapies** -- approval status, mechanism, brand names
5. **Literature** -- PMID-linked papers with journal and date
6. **Omics Datasets** -- accession links, modality, tissue, evidence tier
7. **Extracted Claims** -- predicate text, type badge, confidence score, related targets
8. **Hypotheses** -- cards with title, confidence bar, target badge, modality, key questions
9. **Evidence Graph** -- summary description (visual graph planned)

### 7.3 Security

- **No `innerHTML` usage.** All DOM manipulation uses `createElement`, `textContent`, and `appendChild`
- External links use `target="_blank" rel="noopener"`
- All data comes from the same-origin API (`/api/v2/*`)

### 7.4 Scroll Navigation

Sticky nav bar with scroll-tracking. Click-to-scroll with smooth behavior. Active section highlights based on scroll position with 120px offset.

---

## 8. Infrastructure

### 8.1 Server

| Property | Value |
|---|---|
| Host | moltbot (217.154.10.79) |
| Domain | sma-research.info |
| SSH | `ssh moltbot` (user: bryzant) |
| Process manager | PM2 |
| PM2 app name | sma-api |
| Port | 8090 |
| Reverse proxy | Nginx |
| Python | 3.11+ |

### 8.2 Database

**Current:** SQLite with WAL mode and foreign keys enabled.

The database layer (`src/sma_platform/core/database.py`) is dual-dialect:

- Auto-detects from `DATABASE_URL`: `postgresql://` activates asyncpg, `sqlite:///` activates sqlite3
- All queries are written in PostgreSQL syntax (`$1`, `$2` parameters, `::type` casts)
- `_pg_to_sqlite_query()` converts at runtime: strips type casts (`::jsonb`, `::text`, `::int[]`), replaces `$N` with `?`
- SQLite uses synchronous `sqlite3.connect()` wrapped in async function signatures
- PostgreSQL uses asyncpg connection pool with configurable `min_size`/`max_size`

**Query helpers:**

| Function | PostgreSQL | SQLite |
|---|---|---|
| `fetch()` | `conn.fetch()` | `conn.execute().fetchall()` |
| `fetchrow()` | `conn.fetchrow()` | `conn.execute().fetchone()` |
| `fetchval()` | `conn.fetchval()` | `conn.execute().fetchone()[0]` |
| `execute()` | `conn.execute()` | `conn.execute()` + `conn.commit()` |
| `execute_script()` | `conn.execute()` | `conn.executescript()` |

`DictRow` provides both dict-style (`row["key"]`) and attribute-style (`row.key`) access, unifying asyncpg.Record and sqlite3.Row behavior.

**PostgreSQL upgrade path:**
1. Set `DATABASE_URL=postgresql://user:pass@host/sma_platform`
2. Run `db/schema.sql` (has UUID extensions, proper types, arrays)
3. No application code changes required

### 8.3 Deployment

```
git pull on moltbot
pm2 restart sma-api --update-env
```

PM2 runs uvicorn with the FastAPI app on port 8090. Nginx proxies `sma-research.info` to `localhost:8090`.

### 8.4 Cron

Daily ingestion at 06:00 UTC (planned):

```
POST /api/v2/ingest/pubmed    -- pull last 7 days of papers
POST /api/v2/ingest/trials    -- refresh all SMA trials
POST /api/v2/extract/claims   -- extract claims from new papers
POST /api/v2/generate/hypotheses  -- regenerate all hypotheses
```

### 8.5 Configuration

Environment variables loaded via `pydantic-settings` with `.env` file support:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///sma_platform.db` | Database connection string |
| `NCBI_API_KEY` | (empty) | NCBI/PubMed rate limit increase (3 -> 10 req/sec) |
| `NCBI_EMAIL` | `christian@bryzant.com` | Required by NCBI Entrez |
| `NCBI_TOOL` | `sma-platform` | Tool identifier for NCBI |
| `ANTHROPIC_API_KEY` | (empty) | Claude API for claim extraction and hypothesis generation |
| `OPENAI_API_KEY` | (empty) | Reserved for future use |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8100` | Server port (overridden to 8090 in PM2) |
| `LOG_LEVEL` | `info` | Uvicorn log level |

---

## 9. Technology Stack

### 9.1 Core

| Component | Technology | Version | Purpose |
|---|---|---|---|
| Language | Python | >=3.11 | Type hints, match statements, ExceptionGroup |
| Web framework | FastAPI | >=0.115 | Async API with auto-generated OpenAPI docs |
| ASGI server | Uvicorn | >=0.34 | Production server with lifespan support |
| HTTP client | httpx | >=0.28 | Async HTTP for external APIs |
| Validation | Pydantic | >=2.10 | Request/response models, settings |
| Settings | pydantic-settings | >=2.7 | .env loading, type coercion |

### 9.2 Data

| Component | Technology | Version | Purpose |
|---|---|---|---|
| DB (current) | SQLite | (stdlib) | WAL mode, foreign keys, zero-config |
| DB (upgrade) | PostgreSQL + asyncpg | >=0.30 | Connection pooling, JSONB, UUID, arrays |
| Data frames | pandas | >=2.2 | UCM builder, TSV processing |
| Columnar format | PyArrow | >=18 | Parquet output for UCM |
| YAML | PyYAML | >=6.0 | Configuration files |

### 9.3 Biology

| Component | Technology | Version | Purpose |
|---|---|---|---|
| NCBI access | Biopython | >=1.84 | Entrez (PubMed, GEO) with rate limiting |
| LLM reasoning | Anthropic Claude Haiku 4.5 | claude-haiku-4-5-20251001 | Claim extraction, hypothesis generation |

### 9.4 Development

| Component | Technology | Version | Purpose |
|---|---|---|---|
| Testing | pytest + pytest-asyncio | >=8.0, >=0.25 | Async test support |
| HTTP mocking | pytest-httpx | >=0.35 | Mock external API calls in tests |
| Linting | Ruff | >=0.9 | Fast Python linter (E, F, I, UP, B, SIM rules) |
| Type checking | mypy | >=1.14 | Strict mode |
| Build | Hatchling | - | PEP 517 build backend |

### 9.5 Optional (ML)

| Component | Technology | Version | Purpose |
|---|---|---|---|
| ML | scikit-learn | >=1.6 | Target prioritization models (Phase 2) |
| Graphs | NetworkX | >=3.4 | Knowledge graph analysis (Phase 2) |
| Statistics | SciPy | >=1.15 | Statistical tests for evidence scoring |

---

## 10. Phase Roadmap

### Phase A: Evidence Graph (CURRENT)

**Status:** Operational. Deployed on moltbot.

**Scope:**
- Automated ingestion from PubMed, ClinicalTrials.gov, GEO
- LLM-assisted claim extraction from paper abstracts
- Evidence scoring based on method strength and statistical significance
- Hypothesis card generation per target
- Single-page frontend with full evidence graph visualization
- SQLite database with PostgreSQL-compatible query layer
- Seed data: 10 targets, 7 drugs, 7 datasets

**Delivered:**
- 3 ingestion adapters (PubMed, ClinicalTrials.gov, GEO)
- 7 API route modules with 20+ endpoints
- Claim extraction pipeline with 12 claim types
- Evidence scorer with method weights and p-value bonuses
- Hypothesis generator with LLM synthesis and fallback mode
- UCM builder (TSV -> Parquet)
- Frontend with 8 data sections, filters, scroll navigation
- 9 unit tests (UCM layer)

### Phase B: Prioritization

**Status:** Planned.

**Scope:**
- Target prioritization scoring using NetworkX graph centrality
- Cross-target hypothesis generation (combination therapies, repurposing)
- Evidence tier multipliers applied in scoring
- Druggability assessment integration
- Full-text paper processing (beyond abstracts)
- PostgreSQL migration for production workloads
- Agent system: 8 specialized agents (literature scanner, trial monitor, target evaluator, hypothesis critic, data curator, report writer, alert system, coordinator)

### Phase C: Compute Bursts

**Status:** Planned.

**Scope:**
- GPU-accelerated molecular docking
- Protein structure prediction (AlphaFold integration)
- Differential expression analysis on Tier 1 GEO datasets
- Network pharmacology simulations
- Cost-controlled compute: burst on demand, not always-on

### Phase D: Publication

**Status:** Planned.

**Scope:**
- Automated research report generation
- Open data publication (evidence graph as downloadable dataset)
- Integration with preprint servers
- Community contribution workflow

---

## Appendix A: Project File Structure

```
sma-platform/
  pyproject.toml                  -- Package metadata, dependencies, tool config
  db/
    schema.sql                    -- Canonical PostgreSQL schema (11 tables)
    schema_sqlite.sql             -- SQLite-compatible mirror
  scripts/
    seed_targets.py               -- Seed 10 SMA targets
    seed_drugs.py                 -- Seed 7 SMA drugs
    seed_datasets.py              -- Seed 7 GEO datasets
  frontend/
    index.html                    -- Single-page application (no build step)
  src/sma_platform/
    __init__.py
    core/
      __init__.py
      config.py                   -- pydantic-settings (env vars + .env)
      database.py                 -- Dual-dialect DB layer (SQLite + PostgreSQL)
    api/
      __init__.py
      app.py                      -- FastAPI factory, lifespan, CORS, router registration
      routes/
        __init__.py
        stats.py                  -- GET /stats
        targets.py                -- CRUD targets
        trials.py                 -- List/get trials
        drugs.py                  -- List/get drugs
        datasets.py               -- List/get datasets
        evidence.py               -- Claims, evidence, sources, hypotheses
        ingestion.py              -- POST triggers for ingestion + reasoning
    ingestion/
      __init__.py
      adapters/
        __init__.py
        pubmed.py                 -- Biopython Entrez, 7 search queries
        clinicaltrials.py         -- httpx, v2 API, paginated
        geo.py                    -- Biopython Entrez, curated inventory
    reasoning/
      __init__.py
      claim_extractor.py          -- Claude Haiku, structured claim extraction
      hypothesis_generator.py     -- Claude Haiku, hypothesis synthesis
      scorer.py                   -- Method-weighted evidence scoring
    ucm/
      __init__.py
      builder.py                  -- TSV -> Parquet pipeline
      utils.py                    -- sha256, normalize, stable_id
    agents/
      __init__.py                 -- Planned: 8 specialized agents
  tests/
    (9 tests for UCM layer)
```

## Appendix B: SMA Biology Reference

For context on the biological domain this platform models:

**Spinal Muscular Atrophy (SMA)** is a genetic neuromuscular disease caused by homozygous deletion or mutation of the *SMN1* gene on chromosome 5q13. The paralog *SMN2* produces primarily truncated SMN protein due to exon 7 skipping, with only ~10% full-length transcript. SMN2 copy number (typically 1-4) is the primary modifier of disease severity.

**SMA types by severity:**
- Type 0: prenatal onset, fatal
- Type 1 (Werdnig-Hoffmann): onset <6 months, never sit, most common
- Type 2 (Dubowitz): onset 6-18 months, sit but never stand
- Type 3 (Kugelberg-Welander): onset >18 months, walk but progressive weakness
- Type 4: adult onset, mild

**Approved therapies (as of 2026):**
- **Nusinersen (Spinraza)**: Antisense oligonucleotide. Intrathecal injection. Modifies SMN2 splicing to increase full-length SMN protein. FDA approved 2016.
- **Onasemnogene abeparvovec (Zolgensma)**: AAV9 gene therapy. Single IV dose. Delivers functional SMN1 gene copy. FDA approved 2019.
- **Risdiplam (Evrysdi)**: Small molecule SMN2 splicing modifier. Oral daily. FDA approved 2020.

**Key targets in this platform:**
- **SMN1/SMN2**: Primary disease and modifier genes
- **STMN2 (Stathmin-2)**: Neuroprotective. Downregulated when SMN is low. Critical for axonal maintenance in motor neurons.
- **PLS3 (Plastin-3)**: Natural protective modifier discovered in discordant families. Involved in actin cytoskeleton dynamics.
- **NCALD (Neurocalcin Delta)**: Calcium sensor. Another natural modifier from discordant families.
- **UBA1**: Ubiquitin-activating enzyme. Dysregulated in severe SMA. Links to ubiquitin-proteasome pathway.
- **mTOR**: Mechanistic target of rapamycin. Autophagy regulation implicated in motor neuron survival.

**Pathological cascade:**
SMN1 deletion -> SMN protein deficiency -> snRNP assembly disruption -> widespread splicing dysregulation -> motor neuron-selective vulnerability -> NMJ defects (earliest feature) -> motor neuron degeneration -> progressive muscle weakness -> respiratory failure.
