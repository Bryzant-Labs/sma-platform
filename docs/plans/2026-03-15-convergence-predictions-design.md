# Evidence Convergence Engine + Prediction Cards — Design Document

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the SMA platform from evidence aggregation into a research instrument that generates falsifiable, quantified predictions grounded in 23,000+ claims from 5,216+ sources.

**Architecture:** Three new components layered on top of existing claims/evidence/hypotheses infrastructure. (1) Convergence Engine scores evidence clusters across 5 transparent dimensions, (2) Prediction Cards generate actionable, grant-ready outputs with LLM structuring, (3) Auto-Validation Loop monitors new papers against active predictions.

**Tech Stack:** FastAPI routes, asyncpg, Claude Sonnet 4.6 (LLM structuring only — all scoring is deterministic), vanilla JS frontend.

**Open Source Principle:** ALL scoring weights, formulas, and dimension calculations are hardcoded constants in source code — no hidden models, no black boxes. Every number on a Prediction Card traces back to claims, which trace back to sources. Researchers can inspect and challenge every score on GitHub.

---

## 1. Evidence Convergence Engine

### 1.1 Scoring Dimensions (all weights visible in code)

```python
# File: src/sma_platform/reasoning/convergence_engine.py
# These weights are the platform's "opinion" — open source, auditable, debatable.

CONVERGENCE_WEIGHTS = {
    "volume":           0.15,  # Raw claim count, normalized
    "lab_independence":  0.30,  # Unique author groups / labs
    "method_diversity":  0.20,  # Distinct experimental methods
    "temporal_trend":    0.15,  # Evidence consistency over time
    "replication":       0.20,  # Same finding reproduced
}
# Sum = 1.0 — weighted average produces final score [0, 1]
```

**Dimension Details:**

| Dimension | Input | Formula | Rationale |
|-----------|-------|---------|-----------|
| Volume | claim count for target | `min(1.0, count / VOLUME_CEILING)` where `VOLUME_CEILING = 50` | More claims = more studied, but diminishing returns |
| Lab Independence | unique first-author last names from linked sources | `min(1.0, unique_labs / LAB_CEILING)` where `LAB_CEILING = 10` | Single-lab findings are fragile; multi-lab = robust |
| Method Diversity | unique `evidence.method` values | `min(1.0, unique_methods / METHOD_CEILING)` where `METHOD_CEILING = 6` | in_vivo + in_vitro + omics + clinical > any single method |
| Temporal Trend | year span + consistency | `consistency_ratio * recency_bonus` | Findings confirmed across years > single-year burst |
| Replication | same predicate from ≥2 sources | `replicated_predicates / total_predicates` | Replication crisis is real — reward reproduced findings |

All ceiling constants are module-level `SCREAMING_SNAKE_CASE` — easy to find, easy to challenge.

### 1.2 Database

```sql
CREATE TABLE convergence_scores (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    target_key      TEXT NOT NULL,          -- "target:{uuid}" or "drug:{uuid}"
    target_label    TEXT,                   -- "SMN2", "NCALD", etc.
    target_type     TEXT,                   -- "target", "drug"
    target_id       UUID,                   -- FK to targets or drugs

    -- The 5 dimensions (all 0.0–1.0)
    volume          NUMERIC(4,3) NOT NULL,
    lab_independence NUMERIC(4,3) NOT NULL,
    method_diversity NUMERIC(4,3) NOT NULL,
    temporal_trend  NUMERIC(4,3) NOT NULL,
    replication     NUMERIC(4,3) NOT NULL,

    -- Composite
    composite_score NUMERIC(4,3) NOT NULL,
    confidence_level TEXT NOT NULL CHECK (confidence_level IN ('low', 'medium', 'high', 'very_high')),

    -- Metadata
    claim_count     INTEGER NOT NULL,
    source_count    INTEGER NOT NULL,
    claim_ids       UUID[] DEFAULT '{}',

    computed_at     TIMESTAMPTZ DEFAULT NOW(),
    weights_version TEXT DEFAULT 'v1',      -- tracks which weight set was used

    UNIQUE (target_key, weights_version)
);

CREATE INDEX idx_convergence_composite ON convergence_scores(composite_score DESC);
CREATE INDEX idx_convergence_target ON convergence_scores(target_id);
```

### 1.3 Confidence Level Mapping

```python
CONFIDENCE_THRESHOLDS = {
    "very_high": 0.75,  # Strong multi-lab, multi-method convergence
    "high":      0.55,  # Solid evidence from multiple sources
    "medium":    0.35,  # Some convergence, gaps remain
    "low":       0.0,   # Preliminary or single-source
}
```

### 1.4 Computation Flow

```
POST /api/v2/convergence/compute (admin)
  → For each target with ≥3 claims:
    1. Gather all claims (subject_id = target.id)
    2. Join evidence → sources for author/method/date data
    3. Compute 5 dimensions
    4. Weighted average → composite_score
    5. Map to confidence_level
    6. UPSERT into convergence_scores
  → Return: {targets_scored, avg_score, distribution}
```

---

## 2. Prediction Cards

### 2.1 Database

```sql
CREATE TABLE prediction_cards (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hypothesis_id       UUID REFERENCES hypotheses(id),
    convergence_score_id UUID REFERENCES convergence_scores(id),

    -- The prediction
    prediction_text     TEXT NOT NULL,       -- Falsifiable statement
    target_label        TEXT NOT NULL,       -- e.g. "NCALD"
    target_id           UUID,

    -- Scores (copied from convergence at generation time)
    convergence_score   NUMERIC(4,3) NOT NULL,
    convergence_breakdown JSONB NOT NULL,    -- {volume: 0.78, lab_independence: 0.82, ...}
    confidence_level    TEXT NOT NULL,

    -- Evidence links
    supporting_claims   UUID[] DEFAULT '{}',
    contradicting_claims UUID[] DEFAULT '{}',
    neutral_claims      UUID[] DEFAULT '{}',

    -- LLM-structured content
    evidence_summary    JSONB DEFAULT '{}',  -- {supporting: [...], contradicting: [...], neutral: [...]}
    suggested_experiments JSONB DEFAULT '[]', -- [{title, protocol, readout, timeline, priority}]
    evidence_gaps       TEXT[] DEFAULT '{}',
    linked_patents      UUID[] DEFAULT '{}',

    -- Lifecycle
    status              TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'validated', 'monitoring', 'strengthened', 'weakened', 'confirmed', 'refuted')),
    score_history       JSONB DEFAULT '[]',  -- [{date, score, delta, new_claims}]
    last_validated_at   TIMESTAMPTZ,
    validation_notes    TEXT[] DEFAULT '{}',

    -- Meta
    generated_by        TEXT DEFAULT 'convergence-prediction-agent',
    weights_version     TEXT DEFAULT 'v1',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_predictions_score ON prediction_cards(convergence_score DESC);
CREATE INDEX idx_predictions_status ON prediction_cards(status);
CREATE INDEX idx_predictions_target ON prediction_cards(target_id);
```

### 2.2 Generation Pipeline

```
POST /api/v2/predictions/generate (admin)
  → For each convergence_score where composite_score ≥ 0.5:
    1. Gather all claims for this target
    2. Classify into supporting/contradicting/neutral (LLM)
    3. Generate falsifiable prediction text (LLM)
    4. Suggest experiments based on evidence gaps (LLM)
    5. Find linked patents (text match on target symbol)
    6. Store as draft prediction_card
```

**LLM Usage:** Sonnet 4.6 for structuring ONLY. The LLM does not invent evidence — it classifies existing claims and formulates the prediction statement. Every claim in the card links to a real source.

### 2.3 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/predictions` | List prediction cards (filter by target, status, min_score) |
| GET | `/predictions/{id}` | Single card with full detail |
| GET | `/predictions/{id}/export` | Markdown export (format=markdown) |
| POST | `/predictions/generate` | Trigger generation (admin) |
| PATCH | `/predictions/{id}/status` | Update status (admin) |
| GET | `/convergence` | List convergence scores |
| GET | `/convergence/{target_id}` | Single target convergence detail |
| POST | `/convergence/compute` | Trigger batch computation (admin) |

### 2.4 MCP Tools (2 new)

```python
@mcp.tool()
async def get_predictions(target: str = "", min_score: float = 0.0, limit: int = 10) -> dict:
    """Get prediction cards — falsifiable, evidence-grounded predictions for SMA targets."""

@mcp.tool()
async def get_convergence_score(target: str) -> dict:
    """Get the evidence convergence score breakdown for a specific SMA target."""
```

### 2.5 Frontend

New "Predictions" tab in navigation (between Hypotheses and Sources):
- Card grid layout showing prediction cards
- Each card: target label, prediction text, convergence score bar, confidence badge
- Click → full detail view with evidence breakdown, experiments, gaps
- Filter by: target, confidence level, status
- Score breakdown visualization (horizontal stacked bar)

---

## 3. Auto-Validation Loop

### 3.1 Daily Cron (`scripts/validate_predictions.py`)

Runs after daily PubMed ingestion (06:30 UTC):

```
1. Get all prediction_cards WHERE status IN ('validated', 'monitoring')
2. For each card:
   a. Find new claims (created since last_validated_at) mentioning the same target
   b. If new claims found:
      - Re-query all claims for target
      - Re-compute convergence score
      - Calculate delta from previous score
      - Append to score_history
      - If delta > +0.1: status → 'strengthened'
      - If delta < -0.1: status → 'weakened'
      - Update last_validated_at
3. Log results to ingestion_log
```

### 3.2 Score History Entry

```json
{
    "date": "2026-03-16",
    "score": 0.76,
    "previous_score": 0.71,
    "delta": 0.05,
    "new_claims_count": 3,
    "note": "3 new claims from 2 sources (PMID: 39851234, 39851567)"
}
```

### 3.3 Frontend: Trend Indicator

Next to each prediction score: ↗ (rising), → (stable), ↘ (falling) based on most recent delta.

---

## 4. Open Source Transparency

All scoring constants live in well-documented module-level blocks:

```python
# === CONVERGENCE SCORING WEIGHTS ===
# These determine how different evidence dimensions contribute to
# the overall convergence score. Researchers: if you disagree with
# these weights, open a GitHub issue or submit a PR.
#
# Why Lab Independence is highest (0.30):
#   Single-lab findings are the #1 source of irreproducible results.
#   Multi-lab confirmation is the strongest signal of real biology.
#
# Why Volume is lowest (0.15):
#   A target being "well-studied" doesn't mean the evidence converges.
#   100 papers that contradict each other ≠ strong evidence.
```

Every prediction card includes a `weights_version` field so cards can be re-scored when weights change.

---

## Implementation Order

1. **Task 1**: Database migration — `convergence_scores` + `prediction_cards` tables
2. **Task 2**: `reasoning/convergence_engine.py` — the 5-dimension scoring engine
3. **Task 3**: API routes — `routes/predictions.py` (convergence + predictions endpoints)
4. **Task 4**: Prediction card generator — LLM structuring of claims into cards
5. **Task 5**: MCP tools — `get_predictions` + `get_convergence_score`
6. **Task 6**: Frontend — Predictions tab with card grid + detail view
7. **Task 7**: Auto-validation script — `scripts/validate_predictions.py`
8. **Task 8**: Deploy to moltbot + run initial computation
