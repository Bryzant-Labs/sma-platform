# UCM-First Ingestion Specification

Version: 1.0
Date: 2026-03-15
Status: Active

---

## 1. Source Types

The platform ingests from four source categories. Each source record is stored in the `sources` table with a `source_type` discriminator and a globally unique `(source_type, external_id)` pair.

| Source Type       | `source_type` value | External ID format | API                          | Auth required       |
|-------------------|---------------------|--------------------|------------------------------|---------------------|
| PubMed            | `pubmed`            | PMID (e.g. `38291045`) | NCBI E-utilities (Biopython) | NCBI API key (optional, raises rate limit from 3 to 10 req/sec) |
| ClinicalTrials.gov| `clinicaltrials`    | NCT ID (e.g. `NCT05386680`) | CT.gov v2 REST API           | None (5 req/sec limit) |
| GEO               | `geo`               | GSE accession (e.g. `GSE69175`) | NCBI E-utilities (Biopython) | Same as PubMed      |
| Manual            | `manual`            | User-defined slug    | N/A                          | N/A                 |

Additional `source_type` values reserved for future use: `pride`, `knowledgebase`, `preprint`.

---

## 2. Ingestion Pipeline Per Source

### 2.1 PubMed

**Entry point:** `ingestion.adapters.pubmed.search_recent_sma(days_back=7, max_per_query=50)`

**Queries:** Seven predefined SMA-focused queries are executed per run:

```
"spinal muscular atrophy"
"SMN1" OR "SMN2" AND "spinal muscular atrophy"
"STMN2" AND ("motor neuron" OR "SMA")
"nusinersen" OR "Spinraza"
"risdiplam" OR "Evrysdi"
"onasemnogene" OR "Zolgensma"
"spinal muscular atrophy" AND ("gene therapy" OR "antisense oligonucleotide")
```

**Fields extracted per paper:**

| Field      | Source                                      |
|------------|---------------------------------------------|
| `pmid`     | `MedlineCitation.PMID`                      |
| `title`    | `Article.ArticleTitle`                      |
| `authors`  | `AuthorList` -> `LastName ForeName`         |
| `journal`  | `Journal.Title`                             |
| `pub_date` | `JournalIssue.PubDate` (YYYY-MM-DD)        |
| `doi`      | `ELocationID` where `EIdType == "doi"`      |
| `abstract` | `Abstract.AbstractText` (joined parts)      |
| `url`      | `https://pubmed.ncbi.nlm.nih.gov/{pmid}/`  |

**Deduplication:** PMIDs are collected into a `set()` across all seven queries before fetching details, eliminating duplicates at the API level. Database-level dedup uses `UNIQUE (source_type, external_id)` on the `sources` table.

**Pagination:** Single-page per query (controlled by `max_per_query`). No cursor pagination needed at current scale.

### 2.2 ClinicalTrials.gov

**Entry point:** `ingestion.adapters.clinicaltrials.fetch_all_sma_trials()`

**Query:** `"spinal muscular atrophy"` with two status filters:
- Active: `RECRUITING`, `NOT_YET_RECRUITING`, `ENROLLING_BY_INVITATION`, `ACTIVE_NOT_RECRUITING`
- Completed: `COMPLETED`

Max 500 results per status group.

**Fields extracted per trial:**

| Field             | Source path in v2 API                                   |
|-------------------|---------------------------------------------------------|
| `nct_id`          | `protocolSection.identificationModule.nctId`            |
| `title`           | `officialTitle` or `briefTitle`                         |
| `status`          | `statusModule.overallStatus`                            |
| `phase`           | `designModule.phases` (comma-joined)                    |
| `conditions`      | `conditionsModule.conditions`                           |
| `interventions`   | `armsInterventionsModule.interventions`                 |
| `sponsor`         | `sponsorCollaboratorsModule.leadSponsor.name`           |
| `start_date`      | `statusModule.startDateStruct.date`                     |
| `completion_date` | `statusModule.completionDateStruct.date`                |
| `enrollment`      | `designModule.enrollmentInfo.count`                     |
| `brief_summary`   | `descriptionModule.briefSummary`                        |
| `url`             | `https://clinicaltrials.gov/study/{nct_id}`             |

**Deduplication:** In-memory dedup by NCT ID across active + completed result sets. Database-level dedup via `UNIQUE` on `trials.nct_id`.

**Pagination:** Token-based (`nextPageToken`), page size capped at 100 per request, loop until exhausted or `max_results` reached.

### 2.3 GEO (Gene Expression Omnibus)

**Entry point:** `ingestion.adapters.geo.fetch_known_datasets()`

**Strategy:** Two-tier approach:
1. **Known datasets** -- A curated inventory of SMA-relevant datasets with pre-assigned evidence tiers and modality labels.
2. **Search** -- `Entrez.esearch(db="gds", term="spinal muscular atrophy")` for discovery of new datasets.

**Known dataset inventory:**

| Accession   | Tier  | Modality    | Tissue         |
|-------------|-------|-------------|----------------|
| GSE69175    | tier1 | rna-seq     | motor neurons  |
| GSE108094   | tier1 | rna-seq     | motor neurons  |
| GSE208629   | tier1 | scrna-seq   | spinal cord    |
| GSE87281    | tier2 | rna-seq     | spinal cord    |
| GSE65470    | tier3 | transcriptomics | nmj        |

**Fields extracted per dataset:**

| Field          | Source                    |
|----------------|---------------------------|
| `accession`    | Input accession           |
| `title`        | `esummary.title`          |
| `summary`      | `esummary.summary`        |
| `organism`     | `esummary.taxon`          |
| `platform`     | `esummary.GPL`            |
| `sample_count` | `esummary.n_samples`      |
| `series_type`  | `esummary.gdsType`        |
| `pub_date`     | `esummary.PDAT`           |
| `evidence_tier`| From known inventory      |
| `modality`     | From known inventory      |
| `tissue`       | From known inventory      |

**Deduplication:** `UNIQUE` on `datasets.accession`.

### 2.4 Manual Sources

Manual sources are inserted directly via the API or database with `source_type = 'manual'`. They follow the same schema as other sources but require the user to provide all fields. External ID is a user-defined slug.

---

## 3. UCM Normalization -- Raw Data to Canonical Nodes/Edges

The UCM (Unified Canonical Model) layer transforms raw ingestion data into a graph representation. The `UCMBuilder` class (`ucm/builder.py`) processes TSV files into validated Parquet/TSV artifacts.

### 3.1 Artifact Types

| Artifact   | Required columns                          | Optional columns                          | Output format |
|------------|-------------------------------------------|-------------------------------------------|---------------|
| Nodes      | `node_id`, `node_type`, `label`           | `synonyms`, `namespace`, `metadata_json`  | Parquet       |
| Edges      | `src`, `dst`, `relation`, `confidence`    | `direction`, `effect`, `evidence_ids`, `metadata_json` | Parquet |
| Evidence   | `evidence_id`, `source_type`, `source_ref`| `notes`, `date`, `checksum`               | TSV           |

### 3.2 Normalization Rules

1. **Node IDs** -- Stable deterministic IDs generated via `stable_id(prefix, *parts)`. Uses SHA-256 of pipe-delimited parts, truncated to 12 hex characters, prefixed (e.g., `gene_a1b2c3d4e5f6`).
2. **Confidence clamping** -- All confidence values pass through `normalize_confidence()`: cast to float, clamp to [0.0, 1.0]. Non-numeric values default to 0.0.
3. **Date auto-fill** -- Evidence rows without a `date` value receive `now_iso()` (UTC ISO 8601 timestamp).
4. **Checksum** -- `sha256_file()` computes a SHA-256 checksum for file-level integrity verification.
5. **Missing optional columns** -- Automatically added with empty string defaults during build.

### 3.3 Database-Level Normalization

Raw ingestion data maps to PostgreSQL tables as follows:

| Raw source      | Target table | Normalization steps                                                |
|-----------------|--------------|--------------------------------------------------------------------|
| PubMed papers   | `sources`    | `source_type='pubmed'`, `external_id=pmid`, authors as `TEXT[]`    |
| CT.gov trials   | `trials`     | `nct_id` as unique key, interventions stored as JSONB              |
| GEO datasets    | `datasets`   | `accession` as unique key, tier/modality from known inventory      |
| Gene symbols    | `targets`    | Unique on `(symbol, target_type, organism)`, cross-ref identifiers in JSONB |
| Relationships   | `graph_edges`| `src_id`/`dst_id` reference `targets.id`, unique on `(src_id, dst_id, relation)` |

---

## 4. Claim Extraction Pipeline

### 4.1 LLM Configuration

- **Model:** `claude-haiku-4-5-20251001` (Claude Haiku 4.5)
- **Max tokens:** 2,000 per extraction
- **Timeout:** 60 seconds
- **API:** Anthropic Messages API v1 (`2023-06-01`)
- **Auth:** `ANTHROPIC_API_KEY` environment variable (required; extraction is skipped if missing)

### 4.2 Input Requirements

- Source must have an `abstract` field with length >= 50 characters.
- Sources without evidence rows are considered "unprocessed" and queued for extraction.
- Identification query: `SELECT s.id FROM sources s LEFT JOIN evidence e ON e.source_id = s.id WHERE e.id IS NULL AND s.abstract IS NOT NULL AND length(s.abstract) > 50`

### 4.3 Extraction Prompt Schema

The LLM receives a structured prompt with `{title}`, `{journal}`, and `{abstract}` and returns a JSON array. Each claim object contains:

| Field             | Type          | Description                                           |
|-------------------|---------------|-------------------------------------------------------|
| `predicate`       | string        | Factual assertion (1-2 sentences)                     |
| `claim_type`      | string        | One of the 12 valid claim types (see Section 4.4)     |
| `confidence`      | float         | LLM's confidence the abstract supports this claim     |
| `subject`         | string        | Primary entity (gene symbol, drug name, pathway, or "SMA") |
| `subject_type`    | string        | One of: gene, drug, pathway, disease, cell_type       |
| `object`          | string/null   | Secondary entity, if applicable                       |
| `object_type`     | string/null   | Same options as subject_type                          |
| `related_targets` | string[]      | Gene/protein symbols mentioned (e.g., SMN1, SMN2)    |
| `excerpt`         | string        | Supporting sentence from the abstract                 |

### 4.4 Type Mapping

The LLM may return non-canonical type strings. These are mapped to valid database values:

| LLM output         | Mapped to              |
|---------------------|------------------------|
| `mechanism`         | `pathway_membership`   |
| `efficacy`          | `drug_efficacy`        |
| `epidemiology`      | `other`                |
| `methodology`       | `other`                |
| `drug_mechanism`    | `drug_target`          |
| `gene_regulation`   | `gene_expression`      |
| `splicing`          | `splicing_event`       |
| `neuroprotective`   | `neuroprotection`      |
| `motor`             | `motor_function`       |

Any unmapped type not in the 12 valid types defaults to `other`.

### 4.5 Response Parsing

1. Strip markdown code fences if present (lines starting with `` ``` ``).
2. Parse as JSON.
3. If the result is a single object (not an array), wrap in a list.
4. On parse failure, log the first 300 characters of raw response and return empty list.

---

## 5. Target Linking

After claim extraction, each claim's `subject` and `object` fields are resolved to database target IDs.

### 5.1 Resolution Process

```
subject (e.g., "SMN2")
  -> uppercase -> "SMN2"
  -> SELECT id FROM targets WHERE symbol = 'SMN2'
  -> if found: subject_id = target.id
  -> if not found: subject_id = NULL (unresolved)
```

The same process applies to `object`.

### 5.2 Metadata Search

Claims that cannot be resolved via `subject_id` are still discoverable through metadata. The `hypothesis_generator` searches `claims.metadata` for target symbol strings using `LIKE '%"SYMBOL"%'`, enabling cross-referencing even when direct foreign keys are absent.

### 5.3 Unresolved Targets

When a claim references a gene/protein not yet in the `targets` table, the claim is stored with `subject_id = NULL` but the subject label is preserved in `claims.metadata.subject_label`. A future enrichment step can backfill target IDs as new targets are added.

---

## 6. Evidence Chain -- Full Traceability

Every assertion in the platform follows a strict evidence chain:

```
Source (PMID / NCT ID / GSE accession)
  |
  v
Claim (factual assertion extracted from source)
  |
  v
Evidence (link between claim and source, with excerpt + method + stats)
  |
  v
Hypothesis (synthesized from multiple claims about a target)
```

### 6.1 Database Relationships

```
sources.id <-- evidence.source_id
claims.id  <-- evidence.claim_id
claims.subject_id --> targets.id
claims.object_id  --> targets.id
graph_edges.src_id --> targets.id
graph_edges.dst_id --> targets.id
graph_edges.evidence_ids[] --> evidence.id
hypotheses.supporting_evidence[] --> evidence.id (or claim.id)
hypotheses.contradicting_evidence[] --> evidence.id
```

### 6.2 Traceability Guarantees

1. **No orphan claims.** Every claim stored via `process_source()` immediately creates an `evidence` row linking `claim_id` to `source_id`.
2. **Method tagging.** All LLM-extracted claims have `evidence.method = 'llm_abstract_extraction'`.
3. **Extraction metadata.** Each claim's `metadata` JSONB field records: `extraction_model`, `extracted_at` (UTC ISO), `source_paper_id`, `subject_label`, `object_label`, `related_targets`.
4. **Hypothesis provenance.** Each hypothesis records: `claim_count`, `source_count`, `generated_at`, `model` in its `metadata` JSONB.

### 6.3 Audit Path

For any hypothesis, the full provenance chain can be reconstructed:

```sql
-- From hypothesis to claims
SELECT * FROM claims WHERE id = ANY(hypothesis.supporting_evidence);

-- From claims to sources
SELECT s.* FROM evidence e
JOIN sources s ON e.source_id = s.id
WHERE e.claim_id = $1;

-- From source to external database
SELECT source_type, external_id, url FROM sources WHERE id = $1;
```

---

## 7. Deduplication

### 7.1 Database-Level Constraints

| Table         | Unique constraint                      | Conflict behavior          |
|---------------|----------------------------------------|----------------------------|
| `sources`     | `(source_type, external_id)`           | `ON CONFLICT` -- reject    |
| `targets`     | `(symbol, target_type, organism)`      | `ON CONFLICT` -- reject    |
| `trials`      | `nct_id`                               | `ON CONFLICT` -- reject    |
| `datasets`    | `accession`                            | `ON CONFLICT` -- reject    |
| `evidence`    | `(claim_id, source_id)`               | `ON CONFLICT` -- reject    |
| `graph_edges` | `(src_id, dst_id, relation)`          | `ON CONFLICT` -- reject    |

### 7.2 Application-Level Deduplication

- **PubMed:** PMIDs are deduplicated via `set()` before calling `fetch_paper_details()`. Seven queries may return overlapping results; only unique PMIDs proceed.
- **ClinicalTrials.gov:** NCT IDs are deduplicated via `set()` across active + completed result sets.
- **Claims:** Claims are matched by `predicate` text for post-insert lookup (`ORDER BY created_at DESC LIMIT 1`). Semantic deduplication (same meaning, different wording) is not yet implemented.
- **Hypothesis generation:** The `generate_all_hypotheses()` function deletes all existing hypotheses before regeneration (`DELETE FROM hypotheses`), preventing stale duplicates.

---

## 8. Daily Automation

### 8.1 Schedule

**Cron:** `0 6 * * *` (06:00 UTC daily)

### 8.2 Pipeline Steps (Sequential)

| Step | Function                                 | Description                                    | Expected duration |
|------|------------------------------------------|------------------------------------------------|-------------------|
| 1    | `pubmed.search_recent_sma(days_back=7)`  | Fetch papers from last 7 days across 7 queries | ~15 sec           |
| 2    | `clinicaltrials.fetch_all_sma_trials()`  | Fetch all active + completed SMA trials        | ~30 sec           |
| 3    | `geo.fetch_known_datasets()`             | Fetch metadata for curated GEO datasets        | ~10 sec           |
| 4    | Upsert raw data into `sources`, `trials`, `datasets` | Normalize + store                  | ~5 sec            |
| 5    | `claim_extractor.process_all_unprocessed()` | LLM extraction on new sources               | ~2-10 min (API-bound) |
| 6    | `scorer.score_all_claims()`              | Recompute confidence for all claims            | ~10 sec           |
| 7    | `hypothesis_generator.generate_all_hypotheses()` | Regenerate all hypothesis cards         | ~1-5 min (API-bound) |
| 8    | Log run to `ingestion_log`               | Record counts, errors, duration                | <1 sec            |

### 8.3 Ingestion Log

Each run writes to `ingestion_log`:

| Field           | Value                                   |
|-----------------|-----------------------------------------|
| `source_type`   | `"daily_pipeline"`                      |
| `query`         | `"daily_automation"`                    |
| `items_found`   | Total items from all sources            |
| `items_new`     | Items not previously in database        |
| `items_updated` | Items with updated metadata             |
| `errors`        | Array of error messages                 |
| `run_at`        | UTC timestamp                           |
| `duration_secs` | Wall-clock time                         |

### 8.4 Failure Handling

- API failures (PubMed, CT.gov, Claude) are logged but do not halt the pipeline. Each source adapter operates independently.
- Partial failures are recorded in `ingestion_log.errors[]`.
- Missing `ANTHROPIC_API_KEY` skips claim extraction and hypothesis generation silently (logged at WARNING level).

---

## 9. Quality Gates -- Confidence Scoring

### 9.1 Score Computation

The `scorer.score_claim()` function computes a weighted confidence score per claim:

```
score = (method_weight + p_value_bonus) * sample_size_factor
```

Aggregated across all evidence rows for a claim, then normalized to [0.0, 1.0].

### 9.2 Method Strength Weights

| Method                       | Weight |
|------------------------------|--------|
| `randomized_controlled_trial`| 1.00   |
| `meta_analysis`              | 0.95   |
| `cohort_study`               | 0.80   |
| `case_control`               | 0.70   |
| `in_vivo`                    | 0.70   |
| `in_vitro`                   | 0.60   |
| `case_report`                | 0.50   |
| `in_silico`                  | 0.40   |
| `expert_opinion`             | 0.30   |
| (unrecognized)               | 0.50   |

### 9.3 Evidence Tier Multipliers

| Tier   | Multiplier | Description                                              |
|--------|------------|----------------------------------------------------------|
| `tier1`| 1.0        | Direct experimental evidence (RCT, motor neuron RNA-seq) |
| `tier2`| 0.7        | Observational or model-organism evidence                 |
| `tier3`| 0.4        | Expert opinion, case reports, computational predictions  |

### 9.4 P-Value Bonus

| Condition      | Bonus  |
|----------------|--------|
| p < 0.01       | +0.10  |
| 0.01 <= p < 0.05 | +0.05 |
| p >= 0.05 or null | +0.00 |

### 9.5 Sample Size Factor

```
n_factor = min(1.0, sample_size / 100)  if sample_size > 0
n_factor = 0.5                          if sample_size is null or 0
```

### 9.6 Hypothesis Confidence

Hypothesis-level confidence is determined by the LLM synthesizer, informed by:
- Number of converging claims for a target
- Average claim confidence
- Number of independent sources
- Status classification: `proposed` | `needs_validation` | `strong_candidate`

A fallback (no LLM) computes hypothesis confidence as the arithmetic mean of its supporting claims' confidence scores.
