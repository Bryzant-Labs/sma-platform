# Research Publication Standard

Version: 1.0
Date: 2026-03-15
Status: Active

---

## 1. Provenance Rule

Every claim in the platform MUST link to at least one source record with a verifiable external identifier. No claim may exist without provenance.

### 1.1 Required Provenance Fields

| Field           | Description                                      | Example                              |
|-----------------|--------------------------------------------------|--------------------------------------|
| `source_type`   | Origin database                                  | `pubmed`, `clinicaltrials`, `geo`, `manual` |
| `external_id`   | Identifier in the origin database                | `38291045` (PMID), `NCT05386680`, `GSE69175` |
| `pub_date`      | Publication or registration date                 | `2025-11-14`                         |
| `url`           | Direct link to the source                        | `https://pubmed.ncbi.nlm.nih.gov/38291045/` |
| `method`        | How the claim was extracted                      | `llm_abstract_extraction`, `manual_review` |

### 1.2 Provenance Chain

Every claim is connected to its source through the `evidence` table:

```
source (PMID/NCT/GSE) --[evidence.source_id]--> evidence --[evidence.claim_id]--> claim
```

The `evidence` row stores the specific excerpt, statistical data, and experimental method that substantiate the claim. The `UNIQUE (claim_id, source_id)` constraint prevents duplicate claim-source links.

### 1.3 Extraction Metadata

Claims extracted by LLM carry additional provenance in `claims.metadata`:

| Key                 | Value                                    |
|---------------------|------------------------------------------|
| `extraction_model`  | `claude-haiku-4-5-20251001`              |
| `extracted_at`      | UTC ISO 8601 timestamp                   |
| `source_paper_id`   | UUID of the source record                |
| `subject_label`     | Raw subject string from extraction       |
| `object_label`      | Raw object string from extraction        |
| `related_targets`   | Array of gene/protein symbols mentioned  |

### 1.4 Manual Source Requirements

Sources with `source_type = 'manual'` must include:
- A descriptive `external_id` (slug)
- A `title`
- Either an `abstract` or `full_text` field with substantive content
- The `pub_date` of the original material

---

## 2. Evidence Classes

All evidence is classified into three tiers based on the strength of the underlying methodology. Tier assignment affects confidence scoring via multipliers.

### 2.1 Tier 1 -- Experimental Evidence

**Multiplier: 1.0**

Direct experimental data from controlled studies. This is the strongest class of evidence.

| Method                         | Description                                                  |
|--------------------------------|--------------------------------------------------------------|
| Randomized controlled trial    | Phase 1-3 clinical trials with control arms                  |
| Meta-analysis                  | Systematic quantitative synthesis of multiple studies         |
| In vivo (disease model)        | Animal model experiments with SMA-relevant endpoints         |
| In vitro (motor neuron)        | Cell-based assays using motor neurons or iPSC-derived models |
| RNA-seq / scRNA-seq            | Transcriptomic profiling of SMA-relevant tissues             |
| Proteomics                     | Protein-level quantification in SMA-relevant tissues         |

**GEO datasets at Tier 1:** GSE69175 (motor neuron RNA-seq), GSE108094 (motor neuron RNA-seq), GSE208629 (spinal cord scRNA-seq).

### 2.2 Tier 2 -- Observational Evidence

**Multiplier: 0.7**

Observational and correlational studies. Informative but cannot establish causation.

| Method              | Description                                              |
|---------------------|----------------------------------------------------------|
| Cohort study        | Longitudinal observation of SMA patient cohorts          |
| Case-control study  | Comparison of SMA patients vs. matched controls          |
| Natural history     | Registry-based longitudinal SMA outcome data             |
| Model organism      | Non-disease-model animal studies with SMA gene homologs  |

**GEO datasets at Tier 2:** GSE87281 (spinal cord RNA-seq).

### 2.3 Tier 3 -- Opinion and Indirect Evidence

**Multiplier: 0.4**

Expert interpretation, case reports, and computational predictions. Useful for hypothesis generation but insufficient for standalone conclusions.

| Method              | Description                                              |
|---------------------|----------------------------------------------------------|
| Case report         | Single-patient or small-series clinical observations     |
| Expert opinion      | Review articles, editorials, commentary                  |
| In silico           | Computational predictions, network analysis, docking     |
| Pathway inference   | Claims derived from known pathway membership             |

**GEO datasets at Tier 3:** GSE65470 (NMJ transcriptomics).

---

## 3. Confidence Scoring

Every claim carries a confidence score in the range [0.0, 1.0]. The score is computed, not assigned subjectively.

### 3.1 Score Formula

For a single evidence row:

```
evidence_score = (method_weight + p_value_bonus) * sample_size_factor
```

For a claim with multiple evidence rows:

```
claim_confidence = sum(evidence_score_i * weight_i) / sum(weight_i)
```

Result is clamped to [0.0, 1.0] and rounded to 3 decimal places.

### 3.2 Scoring Factors

**Method weight** (base score for experimental approach):

| Method                         | Weight |
|--------------------------------|--------|
| Randomized controlled trial    | 1.00   |
| Meta-analysis                  | 0.95   |
| Cohort study                   | 0.80   |
| Case-control                   | 0.70   |
| In vivo                        | 0.70   |
| In vitro                       | 0.60   |
| Case report                    | 0.50   |
| In silico                      | 0.40   |
| Expert opinion                 | 0.30   |
| Unrecognized / missing         | 0.50   |

**P-value bonus:**

| Condition             | Bonus   |
|-----------------------|---------|
| p < 0.01              | +0.10   |
| 0.01 <= p < 0.05      | +0.05   |
| p >= 0.05 or unknown  | +0.00   |

**Sample size factor:**

```
if sample_size > 0:  factor = min(1.0, sample_size / 100)
if sample_size is null or 0:  factor = 0.5
```

### 3.3 Score Persistence

- Claim confidence is stored in `claims.confidence` (NUMERIC(3,2)).
- Scores are recomputed in batch by `scorer.score_all_claims()` during daily ingestion.
- The `update_claim_confidence()` function writes the new score directly to the claim row.

### 3.4 Initial LLM Confidence

During extraction, the LLM assigns an initial confidence reflecting how well the abstract supports the claim. This value is stored on insert but is overwritten by the evidence-based scorer when evidence rows are complete. If no statistical data is available, the LLM's initial confidence persists as a fallback.

---

## 4. Review Status Lifecycle

Claims and hypotheses progress through defined status states. Status transitions are logged implicitly via `updated_at` timestamps.

### 4.1 Claim Lifecycle

Claims do not have an explicit `status` column in the current schema. Their lifecycle is tracked through the evidence chain:

| Stage       | Definition                                                        | Indicator                                  |
|-------------|-------------------------------------------------------------------|--------------------------------------------|
| **raw**     | Source ingested, no claims extracted yet                           | Source exists; no evidence rows point to it |
| **extracted** | Claims extracted by LLM, evidence rows created                  | `evidence.method = 'llm_abstract_extraction'` |
| **validated** | Human or secondary LLM review confirms the claim                | `claims.metadata.validated = true` (future) |
| **contested** | Contradicting evidence found from independent source            | Claim appears in `hypotheses.contradicting_evidence[]` |
| **retracted** | Source paper retracted or claim proven false                    | `claims.metadata.retracted = true` (future), confidence set to 0.0 |

### 4.2 Hypothesis Lifecycle

Hypotheses have an explicit `status` column:

| Status            | Definition                                                     |
|-------------------|----------------------------------------------------------------|
| `proposed`        | Generated by LLM or fallback, awaiting review                  |
| `under_review`    | Being actively evaluated by researchers                        |
| `validated`       | Sufficient converging evidence supports the hypothesis         |
| `refuted`         | Contradicting evidence disproves the hypothesis                |
| `published`       | Hypothesis has been published or shared externally              |

The `generate_hypothesis_for_target()` function sets initial status based on LLM assessment: `proposed`, `needs_validation`, or `strong_candidate`. (Note: `needs_validation` maps to `under_review` in the database constraint.)

### 4.3 Transition Rules

1. No status may be skipped. A hypothesis cannot go from `proposed` directly to `published`.
2. `refuted` is a terminal state. To re-open, a new hypothesis must be created.
3. `retracted` claims (future) trigger automatic re-scoring of all hypotheses referencing them.
4. Status changes must be accompanied by an `updated_at` timestamp update.

---

## 5. Claim Type Taxonomy

The platform defines exactly 12 valid claim types. These are enforced by a `CHECK` constraint on `claims.claim_type`.

| Claim type              | Definition                                                          | Example predicate                                              |
|-------------------------|---------------------------------------------------------------------|----------------------------------------------------------------|
| `gene_expression`       | A gene's expression level changes in SMA context                    | "SMN2 expression is reduced in SMA type I motor neurons"       |
| `protein_interaction`   | Two proteins physically or functionally interact                    | "SMN protein interacts with Gemin2 in the SMN complex"         |
| `pathway_membership`    | An entity participates in a biological pathway                      | "PLS3 is part of the actin dynamics pathway in motor neurons"  |
| `drug_target`           | A drug acts on a specific biological target                         | "Nusinersen targets SMN2 pre-mRNA exon 7 inclusion"            |
| `drug_efficacy`         | A drug produces a measurable therapeutic effect                     | "Risdiplam improves HFMSE scores in SMA type 2 patients"      |
| `biomarker`             | A measurable indicator of disease state or treatment response       | "Plasma pNfH levels correlate with motor function decline"     |
| `splicing_event`        | A specific RNA splicing pattern relevant to SMA                     | "SMN2 exon 7 skipping is the primary molecular defect in SMA"  |
| `neuroprotection`       | An intervention protects neurons from degeneration                  | "STMN2 restoration prevents motor neuron axonal dieback"       |
| `motor_function`        | An observation about motor function in SMA patients or models       | "Early treatment preserves motor milestone acquisition"        |
| `survival`              | Data about patient or model organism survival outcomes              | "Onasemnogene-treated SMA1 patients show improved event-free survival" |
| `safety`                | Adverse events, toxicity, or safety signals                         | "Thrombocytopenia observed in risdiplam-treated patients"      |
| `other`                 | Claims not fitting the above categories                             | "SMA prevalence is approximately 1 in 10,000 live births"      |

### 5.1 Type Enforcement

- Database: `CHECK` constraint rejects rows with invalid types.
- Application: `VALID_CLAIM_TYPES` set validates before insert.
- LLM fallback: `TYPE_MAP` dictionary normalizes common LLM variations (see UCM Ingestion Spec, Section 4.4). Unmapped values default to `other`.

---

## 6. Contradiction Handling

### 6.1 Definition

A contradiction exists when two claims with overlapping subjects make incompatible assertions. Examples:
- Claim A: "Drug X improves motor function in SMA type 2" (confidence 0.8)
- Claim B: "Drug X shows no significant effect on motor function in SMA type 2" (confidence 0.7)

### 6.2 Detection

Contradictions are currently identified at the hypothesis generation stage. The `generate_hypothesis_for_target()` function receives all claims about a target and passes them to the LLM, which is prompted to assess the evidence including gaps and conflicts. The LLM may classify a hypothesis as `needs_validation` when contradictions are present.

### 6.3 Storage

The `hypotheses` table has two evidence arrays:
- `supporting_evidence UUID[]` -- Evidence rows that support the hypothesis
- `contradicting_evidence UUID[]` -- Evidence rows that contradict it

### 6.4 Resolution Rules

1. **Higher-tier evidence takes precedence.** A Tier 1 RCT result overrides a Tier 3 expert opinion.
2. **Larger sample sizes take precedence.** An n=200 cohort study is weighted more heavily than an n=5 case series.
3. **Recency is a tiebreaker.** When evidence quality is equal, more recent publications are preferred.
4. **Contradictions are preserved, not deleted.** Both supporting and contradicting claims remain in the database. Resolution is recorded in hypothesis metadata, not by removing data.
5. **Confidence reduction.** A claim with strong contradicting evidence should have its confidence reduced through the scoring pipeline (lower aggregate when conflicting evidence is included).

### 6.5 Future Enhancements

- Automated contradiction detection via semantic similarity of predicates for claims sharing a subject.
- Explicit `contradiction_pairs` table linking claim IDs with a `resolution_status` column.
- Notification system when new evidence contradicts a `validated` hypothesis.

---

## 7. Update Policy

### 7.1 Source Updates

| Event                            | Action                                                         |
|----------------------------------|----------------------------------------------------------------|
| New paper published              | Ingested during next daily run if it matches SMA queries       |
| Paper retracted                  | Mark source `metadata.retracted = true`; set linked claims to confidence 0.0; re-score all affected hypotheses |
| Trial status changes             | Re-ingest trial metadata; update `trials.status`               |
| GEO dataset updated              | Re-fetch metadata; update `datasets` row                       |
| New target gene identified       | Add to `targets` table; backfill unresolved claims             |

### 7.2 Claim Updates

- Claims are immutable after extraction. If a claim needs correction, a new claim is extracted and the old one is marked (future: `metadata.superseded_by`).
- Confidence scores are mutable and recomputed on every daily run via `score_all_claims()`.
- Claim type is set at extraction time and does not change.

### 7.3 Hypothesis Updates

- Hypotheses are regenerated from scratch on each daily run (`DELETE FROM hypotheses` followed by `generate_all_hypotheses()`).
- This ensures hypotheses reflect the latest claim set and confidence scores.
- Previously validated hypotheses (status `validated` or `published`) should be preserved in a future version rather than deleted and regenerated.

### 7.4 Data Retention

- No source, claim, or evidence record is ever hard-deleted outside of hypothesis regeneration.
- The `ingestion_log` table provides a full audit trail of all ingestion runs.
- Database-level `ON DELETE CASCADE` on `evidence` ensures that if a claim is removed, its evidence links are cleaned up. If a source is removed, its evidence links are cleaned up.

### 7.5 Ingestion Frequency

| Source           | Frequency     | Window        |
|------------------|---------------|---------------|
| PubMed           | Daily 06:00 UTC | Last 7 days  |
| ClinicalTrials.gov | Daily 06:00 UTC | All active + completed |
| GEO              | Daily 06:00 UTC | Known inventory + search |
| Manual           | On demand     | N/A           |
| Claim extraction | Daily (after ingestion) | Unprocessed sources only |
| Scoring          | Daily (after extraction) | All claims |
| Hypotheses       | Daily (after scoring) | All targets with claims |

### 7.6 Schema Versioning

- The canonical schema is `db/schema.sql` (PostgreSQL) with a SQLite variant at `db/schema_sqlite.sql`.
- Schema changes require a new version number in this document and a corresponding migration script.
- The database layer (`core/database.py`) auto-detects PostgreSQL vs. SQLite and translates `$N` parameters to `?` for SQLite compatibility.
