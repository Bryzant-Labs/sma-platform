# Evidence Convergence Engine + Prediction Cards — Implementation Plan

**Goal:** Build the convergence scoring engine, prediction card generator, API, MCP tools, frontend, and auto-validation loop.

**Architecture:** Layered on existing claims/evidence/hypotheses tables. New `convergence_scores` + `prediction_cards` tables. New `reasoning/convergence_engine.py` module. New `routes/predictions.py`. Frontend additions to `index.html`.

**Tech Stack:** FastAPI, asyncpg, Claude Sonnet 4.6 (structuring only), vanilla JS

---

### Task 1: Database Migration — New Tables

**Files:**
- Modify: `db/schema.sql` (append new tables)
- Modify: `db/schema_sqlite.sql` (append SQLite equivalents)

**Step 1: Add convergence_scores table to schema.sql**

Append after the `drug_outcomes` table:

```sql
-- ============================================================
-- CONVERGENCE SCORES (Evidence Convergence Engine)
-- ============================================================

CREATE TABLE convergence_scores (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    target_key      TEXT NOT NULL,
    target_label    TEXT,
    target_type     TEXT,
    target_id       UUID,
    volume          NUMERIC(4,3) NOT NULL,
    lab_independence NUMERIC(4,3) NOT NULL,
    method_diversity NUMERIC(4,3) NOT NULL,
    temporal_trend  NUMERIC(4,3) NOT NULL,
    replication     NUMERIC(4,3) NOT NULL,
    composite_score NUMERIC(4,3) NOT NULL,
    confidence_level TEXT NOT NULL CHECK (confidence_level IN ('low', 'medium', 'high', 'very_high')),
    claim_count     INTEGER NOT NULL,
    source_count    INTEGER NOT NULL,
    claim_ids       UUID[] DEFAULT '{}',
    computed_at     TIMESTAMPTZ DEFAULT NOW(),
    weights_version TEXT DEFAULT 'v1',
    UNIQUE (target_key, weights_version)
);

CREATE INDEX idx_convergence_composite ON convergence_scores(composite_score DESC);
CREATE INDEX idx_convergence_target ON convergence_scores(target_id);
```

**Step 2: Add prediction_cards table to schema.sql**

```sql
-- ============================================================
-- PREDICTION CARDS (Evidence-grounded falsifiable predictions)
-- ============================================================

CREATE TABLE prediction_cards (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hypothesis_id       UUID REFERENCES hypotheses(id),
    convergence_score_id UUID REFERENCES convergence_scores(id),
    prediction_text     TEXT NOT NULL,
    target_label        TEXT NOT NULL,
    target_id           UUID,
    convergence_score   NUMERIC(4,3) NOT NULL,
    convergence_breakdown JSONB NOT NULL,
    confidence_level    TEXT NOT NULL,
    supporting_claims   UUID[] DEFAULT '{}',
    contradicting_claims UUID[] DEFAULT '{}',
    neutral_claims      UUID[] DEFAULT '{}',
    evidence_summary    JSONB DEFAULT '{}',
    suggested_experiments JSONB DEFAULT '[]',
    evidence_gaps       TEXT[] DEFAULT '{}',
    linked_patents      UUID[] DEFAULT '{}',
    status              TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'validated', 'monitoring', 'strengthened', 'weakened', 'confirmed', 'refuted')),
    score_history       JSONB DEFAULT '[]',
    last_validated_at   TIMESTAMPTZ,
    validation_notes    TEXT[] DEFAULT '{}',
    generated_by        TEXT DEFAULT 'convergence-prediction-agent',
    weights_version     TEXT DEFAULT 'v1',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_predictions_score ON prediction_cards(convergence_score DESC);
CREATE INDEX idx_predictions_status ON prediction_cards(status);
CREATE INDEX idx_predictions_target ON prediction_cards(target_id);
```

**Step 3: Add SQLite equivalents to schema_sqlite.sql**

Same tables but with `TEXT` instead of `UUID`, no `uuid_generate_v4()`, `DATETIME` instead of `TIMESTAMPTZ`, no array types (use `TEXT` with JSON encoding).

**Step 4: Run migration on moltbot**

```bash
ssh moltbot "cd /home/bryzant/sma-platform && PGPASSWORD=sma-research-2026 psql -h localhost -U sma -d sma_platform -f /dev/stdin" <<'SQL'
-- convergence_scores
CREATE TABLE IF NOT EXISTS convergence_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    target_key TEXT NOT NULL,
    target_label TEXT,
    target_type TEXT,
    target_id UUID,
    volume NUMERIC(4,3) NOT NULL,
    lab_independence NUMERIC(4,3) NOT NULL,
    method_diversity NUMERIC(4,3) NOT NULL,
    temporal_trend NUMERIC(4,3) NOT NULL,
    replication NUMERIC(4,3) NOT NULL,
    composite_score NUMERIC(4,3) NOT NULL,
    confidence_level TEXT NOT NULL CHECK (confidence_level IN ('low','medium','high','very_high')),
    claim_count INTEGER NOT NULL,
    source_count INTEGER NOT NULL,
    claim_ids UUID[] DEFAULT '{}',
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    weights_version TEXT DEFAULT 'v1',
    UNIQUE (target_key, weights_version)
);
CREATE INDEX IF NOT EXISTS idx_convergence_composite ON convergence_scores(composite_score DESC);
CREATE INDEX IF NOT EXISTS idx_convergence_target ON convergence_scores(target_id);

-- prediction_cards
CREATE TABLE IF NOT EXISTS prediction_cards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hypothesis_id UUID REFERENCES hypotheses(id),
    convergence_score_id UUID REFERENCES convergence_scores(id),
    prediction_text TEXT NOT NULL,
    target_label TEXT NOT NULL,
    target_id UUID,
    convergence_score NUMERIC(4,3) NOT NULL,
    convergence_breakdown JSONB NOT NULL,
    confidence_level TEXT NOT NULL,
    supporting_claims UUID[] DEFAULT '{}',
    contradicting_claims UUID[] DEFAULT '{}',
    neutral_claims UUID[] DEFAULT '{}',
    evidence_summary JSONB DEFAULT '{}',
    suggested_experiments JSONB DEFAULT '[]',
    evidence_gaps TEXT[] DEFAULT '{}',
    linked_patents UUID[] DEFAULT '{}',
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft','validated','monitoring','strengthened','weakened','confirmed','refuted')),
    score_history JSONB DEFAULT '[]',
    last_validated_at TIMESTAMPTZ,
    validation_notes TEXT[] DEFAULT '{}',
    generated_by TEXT DEFAULT 'convergence-prediction-agent',
    weights_version TEXT DEFAULT 'v1',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_predictions_score ON prediction_cards(convergence_score DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_status ON prediction_cards(status);
CREATE INDEX IF NOT EXISTS idx_predictions_target ON prediction_cards(target_id);
SQL
```

---

### Task 2: Convergence Engine — Core Scoring Module

**Files:**
- Create: `src/sma_platform/reasoning/convergence_engine.py`

**The module implements all 5 scoring dimensions with fully documented, auditable constants.**

```python
"""Evidence Convergence Engine — quantifies how strongly evidence converges on a target.

All scoring weights and ceiling constants are module-level constants.
Open source, auditable, debatable. If you disagree with a weight,
open a GitHub issue or submit a PR.

Scoring dimensions (sum of weights = 1.0):
1. Volume (0.15)         — how many claims mention this target
2. Lab Independence (0.30) — unique research groups providing evidence
3. Method Diversity (0.20) — variety of experimental methods
4. Temporal Trend (0.15)  — consistency of evidence over time
5. Replication (0.20)     — same finding reproduced by different groups
"""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

from ..core.database import execute, fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

# === CONVERGENCE SCORING WEIGHTS ===
# These determine how different evidence dimensions contribute to
# the overall convergence score. Researchers: if you disagree,
# open a GitHub issue or submit a PR at:
# https://github.com/Bryzant-Labs/sma-platform
#
# Why Lab Independence is highest (0.30):
#   Single-lab findings are the #1 source of irreproducible results.
#   Multi-lab confirmation is the strongest signal of real biology.
#
# Why Volume is lowest (0.15):
#   A target being "well-studied" doesn't mean the evidence converges.
#   100 papers that contradict each other ≠ strong evidence.

CONVERGENCE_WEIGHTS: dict[str, float] = {
    "volume":           0.15,
    "lab_independence":  0.30,
    "method_diversity":  0.20,
    "temporal_trend":    0.15,
    "replication":       0.20,
}

# Normalization ceilings — scores saturate at these values
VOLUME_CEILING = 50        # 50+ claims = max volume score
LAB_CEILING = 10           # 10+ unique labs = max independence
METHOD_CEILING = 6         # 6+ distinct methods = max diversity
YEAR_SPAN_CEILING = 10     # 10+ year span = max temporal credit

# Confidence level thresholds
CONFIDENCE_THRESHOLDS = {
    "very_high": 0.75,
    "high":      0.55,
    "medium":    0.35,
    "low":       0.0,
}

WEIGHTS_VERSION = "v1"


def _clamp(value: float) -> float:
    """Clamp to [0, 1] and round to 3 decimals."""
    return round(max(0.0, min(1.0, value)), 3)


def _extract_lab_proxy(authors: list[str] | None) -> str | None:
    """Extract a proxy for 'lab' from the first author's last name.

    This is an imperfect heuristic — papers from the same lab typically
    share a senior (last) author. First-author last name is used as a
    lightweight proxy without requiring institution parsing.
    """
    if not authors or not isinstance(authors, list):
        return None
    first_author = authors[0] if authors else ""
    if not first_author:
        return None
    # Take last name (last word before any comma or space)
    parts = re.split(r"[,\s]+", first_author.strip())
    return parts[0].lower() if parts else None


def _confidence_level(score: float) -> str:
    """Map composite score to confidence level string."""
    for level, threshold in sorted(
        CONFIDENCE_THRESHOLDS.items(),
        key=lambda x: x[1],
        reverse=True,
    ):
        if score >= threshold:
            return level
    return "low"


async def compute_target_convergence(target_id: str) -> dict | None:
    """Compute convergence score for a single target.

    Returns dict with all 5 dimensions + composite, or None if <3 claims.
    """
    # Get all claims for this target with evidence and source details
    rows = await fetch(
        """
        SELECT
            c.id AS claim_id,
            c.claim_type,
            c.predicate,
            c.confidence AS claim_confidence,
            e.method,
            e.source_id,
            s.authors,
            s.pub_date,
            s.source_type
        FROM claims c
        LEFT JOIN evidence e ON e.claim_id = c.id
        LEFT JOIN sources s ON e.source_id = s.id
        WHERE c.subject_id = $1
        ORDER BY c.created_at
        """,
        target_id,
    )

    if len(rows) < 3:
        return None

    # Collect data for scoring
    claim_ids: list[str] = []
    source_ids: set[str] = set()
    lab_proxies: set[str] = set()
    methods: set[str] = set()
    years: list[int] = []
    predicates: Counter = Counter()
    predicate_sources: defaultdict[str, set[str]] = defaultdict(set)

    for row in rows:
        r = dict(row)
        cid = str(r["claim_id"])
        if cid not in claim_ids:
            claim_ids.append(cid)

        sid = str(r["source_id"]) if r.get("source_id") else None
        if sid:
            source_ids.add(sid)

        # Lab proxy from first author
        lab = _extract_lab_proxy(r.get("authors"))
        if lab:
            lab_proxies.add(lab)

        # Method
        method = (r.get("method") or "").strip().lower()
        if method:
            methods.add(method)

        # Year
        pub_date = r.get("pub_date")
        if pub_date:
            try:
                if hasattr(pub_date, "year"):
                    years.append(pub_date.year)
                else:
                    years.append(int(str(pub_date)[:4]))
            except (ValueError, TypeError):
                pass

        # Predicate tracking for replication
        pred = (r.get("predicate") or "").strip().lower()[:100]
        if pred:
            predicates[pred] += 1
            if sid:
                predicate_sources[pred].add(sid)

    claim_count = len(claim_ids)
    source_count = len(source_ids)

    # --- Dimension 1: Volume ---
    volume = _clamp(claim_count / VOLUME_CEILING)

    # --- Dimension 2: Lab Independence ---
    lab_independence = _clamp(len(lab_proxies) / LAB_CEILING)

    # --- Dimension 3: Method Diversity ---
    method_diversity = _clamp(len(methods) / METHOD_CEILING)

    # --- Dimension 4: Temporal Trend ---
    if len(years) >= 2:
        year_span = max(years) - min(years)
        span_score = _clamp(year_span / YEAR_SPAN_CEILING)

        # Consistency: are claims spread across the span or clustered?
        unique_years = len(set(years))
        consistency = _clamp(unique_years / max(year_span, 1))

        # Recency bonus: more recent = slightly higher
        current_year = datetime.now(timezone.utc).year
        most_recent = max(years)
        recency = _clamp(1.0 - (current_year - most_recent) / 10.0)

        temporal_trend = _clamp((span_score * 0.3 + consistency * 0.4 + recency * 0.3))
    else:
        temporal_trend = 0.1  # Single time point = minimal temporal signal

    # --- Dimension 5: Replication ---
    # A predicate is "replicated" if 2+ different sources assert it
    total_predicates = len(predicates)
    replicated = sum(
        1 for pred, sources in predicate_sources.items()
        if len(sources) >= 2
    )
    replication = _clamp(replicated / max(total_predicates, 1))

    # --- Composite Score ---
    composite = _clamp(
        CONVERGENCE_WEIGHTS["volume"] * volume
        + CONVERGENCE_WEIGHTS["lab_independence"] * lab_independence
        + CONVERGENCE_WEIGHTS["method_diversity"] * method_diversity
        + CONVERGENCE_WEIGHTS["temporal_trend"] * temporal_trend
        + CONVERGENCE_WEIGHTS["replication"] * replication
    )

    return {
        "target_id": target_id,
        "volume": volume,
        "lab_independence": lab_independence,
        "method_diversity": method_diversity,
        "temporal_trend": temporal_trend,
        "replication": replication,
        "composite_score": composite,
        "confidence_level": _confidence_level(composite),
        "claim_count": claim_count,
        "source_count": source_count,
        "claim_ids": claim_ids,
        "methods_found": sorted(methods),
        "labs_found": sorted(lab_proxies),
        "year_range": [min(years), max(years)] if years else [],
    }


async def compute_all_convergence() -> dict:
    """Batch-compute convergence scores for all targets with ≥3 claims.

    Upserts into convergence_scores table.
    """
    targets = await fetch("SELECT id, symbol, target_type FROM targets ORDER BY symbol")

    scored = 0
    skipped = 0
    results = []

    for t in targets:
        t = dict(t)
        tid = str(t["id"])
        result = await compute_target_convergence(tid)

        if result is None:
            skipped += 1
            continue

        target_key = f"target:{tid}"

        # Upsert
        await execute(
            """
            INSERT INTO convergence_scores
                (target_key, target_label, target_type, target_id,
                 volume, lab_independence, method_diversity, temporal_trend, replication,
                 composite_score, confidence_level, claim_count, source_count, claim_ids,
                 computed_at, weights_version)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW(), $15)
            ON CONFLICT (target_key, weights_version)
            DO UPDATE SET
                target_label = EXCLUDED.target_label,
                volume = EXCLUDED.volume,
                lab_independence = EXCLUDED.lab_independence,
                method_diversity = EXCLUDED.method_diversity,
                temporal_trend = EXCLUDED.temporal_trend,
                replication = EXCLUDED.replication,
                composite_score = EXCLUDED.composite_score,
                confidence_level = EXCLUDED.confidence_level,
                claim_count = EXCLUDED.claim_count,
                source_count = EXCLUDED.source_count,
                claim_ids = EXCLUDED.claim_ids,
                computed_at = NOW()
            """,
            target_key,
            t["symbol"],
            t.get("target_type", "target"),
            tid,
            result["volume"],
            result["lab_independence"],
            result["method_diversity"],
            result["temporal_trend"],
            result["replication"],
            result["composite_score"],
            result["confidence_level"],
            result["claim_count"],
            result["source_count"],
            result["claim_ids"],
            WEIGHTS_VERSION,
        )

        results.append({
            "target": t["symbol"],
            "composite_score": result["composite_score"],
            "confidence_level": result["confidence_level"],
            "claim_count": result["claim_count"],
        })
        scored += 1

    logger.info("Convergence scoring complete: %d scored, %d skipped", scored, skipped)
    return {
        "targets_scored": scored,
        "targets_skipped": skipped,
        "results": results,
    }
```

---

### Task 3: API Routes — Convergence + Predictions

**Files:**
- Create: `src/sma_platform/api/routes/predictions.py`
- Modify: `src/sma_platform/api/app.py` (register new router)

```python
"""Convergence scoring and prediction card endpoints."""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from ...core.database import execute, fetch, fetchrow
from ..dependencies import require_admin_key

router = APIRouter()


# --- Convergence Scores ---

@router.get("/convergence")
async def list_convergence_scores(
    min_score: float = Query(default=0.0, ge=0, le=1),
    limit: int = Query(default=50, ge=1, le=200),
):
    """List convergence scores for all scored targets."""
    rows = await fetch(
        """SELECT * FROM convergence_scores
           WHERE composite_score >= $1
           ORDER BY composite_score DESC
           LIMIT $2""",
        min_score, limit,
    )
    return [dict(r) for r in rows]


@router.get("/convergence/{target_id}")
async def get_convergence_score(target_id: UUID):
    """Get convergence score breakdown for a specific target."""
    row = await fetchrow(
        "SELECT * FROM convergence_scores WHERE target_id = $1",
        target_id,
    )
    if not row:
        raise HTTPException(404, "No convergence score for this target")
    return dict(row)


@router.post("/convergence/compute", dependencies=[Depends(require_admin_key)])
async def compute_convergence():
    """Trigger batch convergence score computation for all targets."""
    from ...reasoning.convergence_engine import compute_all_convergence
    result = await compute_all_convergence()
    return result


# --- Prediction Cards ---

@router.get("/predictions")
async def list_predictions(
    target: str | None = None,
    status: str | None = None,
    min_score: float = Query(default=0.0, ge=0, le=1),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List prediction cards with optional filters."""
    wheres = ["convergence_score >= $1"]
    params: list = [min_score]
    idx = 2

    if target:
        wheres.append(f"LOWER(target_label) = ${idx}")
        params.append(target.lower())
        idx += 1
    if status:
        wheres.append(f"status = ${idx}")
        params.append(status)
        idx += 1

    where_clause = " WHERE " + " AND ".join(wheres)

    params.append(limit)
    limit_idx = idx
    idx += 1
    params.append(offset)
    offset_idx = idx

    rows = await fetch(
        f"SELECT * FROM prediction_cards{where_clause} ORDER BY convergence_score DESC LIMIT ${limit_idx} OFFSET ${offset_idx}",
        *params,
    )
    return [dict(r) for r in rows]


@router.get("/predictions/{prediction_id}")
async def get_prediction(prediction_id: UUID):
    """Get a single prediction card with full detail."""
    row = await fetchrow(
        "SELECT * FROM prediction_cards WHERE id = $1",
        prediction_id,
    )
    if not row:
        raise HTTPException(404, "Prediction not found")
    return dict(row)


@router.get("/predictions/{prediction_id}/export")
async def export_prediction(prediction_id: UUID, format: str = "markdown"):
    """Export prediction card as Markdown (for grant applications)."""
    row = await fetchrow(
        "SELECT * FROM prediction_cards WHERE id = $1",
        prediction_id,
    )
    if not row:
        raise HTTPException(404, "Prediction not found")

    card = dict(row)

    if format != "markdown":
        raise HTTPException(400, "Only 'markdown' format supported")

    # Build markdown
    breakdown = card.get("convergence_breakdown") or {}
    if isinstance(breakdown, str):
        breakdown = json.loads(breakdown)

    experiments = card.get("suggested_experiments") or []
    if isinstance(experiments, str):
        experiments = json.loads(experiments)

    gaps = card.get("evidence_gaps") or []

    md_lines = [
        f"# Prediction Card: {card['target_label']}",
        "",
        f"**Status:** {card['status']}  ",
        f"**Convergence Score:** {card['convergence_score']:.3f} ({card['confidence_level'].upper()})  ",
        f"**Generated:** {card['created_at']}  ",
        f"**Weights Version:** {card.get('weights_version', 'v1')}",
        "",
        "---",
        "",
        "## Prediction",
        "",
        f"> {card['prediction_text']}",
        "",
        "## Convergence Score Breakdown",
        "",
        "| Dimension | Score | Weight |",
        "|-----------|-------|--------|",
        f"| Volume | {breakdown.get('volume', 0):.3f} | 0.15 |",
        f"| Lab Independence | {breakdown.get('lab_independence', 0):.3f} | 0.30 |",
        f"| Method Diversity | {breakdown.get('method_diversity', 0):.3f} | 0.20 |",
        f"| Temporal Trend | {breakdown.get('temporal_trend', 0):.3f} | 0.15 |",
        f"| Replication | {breakdown.get('replication', 0):.3f} | 0.20 |",
        "",
    ]

    # Evidence summary
    summary = card.get("evidence_summary") or {}
    if isinstance(summary, str):
        summary = json.loads(summary)

    if summary:
        md_lines.extend([
            "## Evidence Summary",
            "",
        ])
        for category in ["supporting", "contradicting", "neutral"]:
            items = summary.get(category, [])
            if items:
                md_lines.append(f"### {category.title()} ({len(items)} claims)")
                md_lines.append("")
                for item in items:
                    if isinstance(item, dict):
                        md_lines.append(f"- {item.get('text', str(item))}")
                    else:
                        md_lines.append(f"- {item}")
                md_lines.append("")

    # Experiments
    if experiments:
        md_lines.extend(["## Suggested Experiments", ""])
        for i, exp in enumerate(experiments, 1):
            if isinstance(exp, dict):
                md_lines.append(f"### {i}. {exp.get('title', 'Experiment')}")
                if exp.get("protocol"):
                    md_lines.append(f"**Protocol:** {exp['protocol']}")
                if exp.get("readout"):
                    md_lines.append(f"**Readout:** {exp['readout']}")
                if exp.get("timeline"):
                    md_lines.append(f"**Timeline:** {exp['timeline']}")
                if exp.get("priority"):
                    md_lines.append(f"**Priority:** {exp['priority']}")
                md_lines.append("")
            else:
                md_lines.append(f"{i}. {exp}")

    # Gaps
    if gaps:
        md_lines.extend(["## Evidence Gaps", ""])
        for gap in gaps:
            md_lines.append(f"- {gap}")
        md_lines.append("")

    md_lines.extend([
        "---",
        f"*Generated by SMA Research Platform (sma-research.info) | Weights version: {card.get('weights_version', 'v1')}*",
    ])

    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content="\n".join(md_lines),
        media_type="text/markdown",
    )


@router.post("/predictions/generate", dependencies=[Depends(require_admin_key)])
async def generate_predictions():
    """Generate prediction cards from convergence scores ≥ 0.5."""
    from ...reasoning.prediction_generator import generate_all_predictions
    result = await generate_all_predictions()
    return result


@router.patch("/predictions/{prediction_id}/status", dependencies=[Depends(require_admin_key)])
async def update_prediction_status(prediction_id: UUID, status: str = Query(...)):
    """Update prediction card status."""
    valid = {"draft", "validated", "monitoring", "strengthened", "weakened", "confirmed", "refuted"}
    if status not in valid:
        raise HTTPException(400, f"Invalid status. Must be one of: {valid}")

    row = await fetchrow("SELECT id FROM prediction_cards WHERE id = $1", prediction_id)
    if not row:
        raise HTTPException(404, "Prediction not found")

    await execute(
        "UPDATE prediction_cards SET status = $1, updated_at = NOW() WHERE id = $2",
        status, prediction_id,
    )
    return {"id": str(prediction_id), "status": status}
```

**Register in app.py:**

Add to imports: `from .routes import predictions`

Add to router registrations:
```python
app.include_router(predictions.router, prefix="/api/v2", tags=["predictions"])
```

---

### Task 4: Prediction Card Generator

**Files:**
- Create: `src/sma_platform/reasoning/prediction_generator.py`

This module uses Sonnet 4.6 to structure existing claims into falsifiable prediction cards. The LLM classifies claims (supporting/contradicting/neutral) and formulates the prediction — it does NOT invent evidence.

```python
"""Prediction Card Generator — structures evidence into falsifiable predictions.

Uses Claude Sonnet 4.6 for structuring only. All evidence comes from the claims
table. The LLM's job is to:
1. Classify claims as supporting/contradicting/neutral
2. Formulate a falsifiable prediction statement
3. Suggest experiments based on evidence gaps
4. Identify what's missing (evidence gaps)

It does NOT invent evidence or make up citations.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

import anthropic

from ..core.config import settings
from ..core.database import execute, fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
AGENT_NAME = "convergence-prediction-agent"

PREDICTION_SYSTEM_PROMPT = """You are a senior SMA researcher writing a prediction card for a grant review panel.

You are given a target name, its convergence score, and a list of evidence claims from the published literature. Your job is to:

1. CLASSIFY each claim as "supporting", "contradicting", or "neutral" for the overall research direction
2. Write ONE precise, falsifiable prediction statement (not vague — it must be testable in a lab)
3. Suggest 2-3 concrete experiments to test this prediction (model system, readout, timeline)
4. Identify 2-4 evidence gaps (what's missing that would strengthen or refute the prediction)

CRITICAL RULES:
- Every claim you reference MUST come from the provided list — do NOT invent citations
- The prediction must be falsifiable — a clear yes/no experiment could confirm or refute it
- Experiments should be practical (iPSC, mouse model, cell culture — not "launch clinical trial")

Return ONLY valid JSON with this structure:
{
    "prediction_text": "One sentence falsifiable prediction",
    "evidence_summary": {
        "supporting": [{"claim_id": "uuid", "text": "brief summary"}],
        "contradicting": [{"claim_id": "uuid", "text": "brief summary"}],
        "neutral": [{"claim_id": "uuid", "text": "brief summary"}]
    },
    "suggested_experiments": [
        {
            "title": "Short title",
            "protocol": "Model system + intervention",
            "readout": "What to measure",
            "timeline": "Estimated weeks",
            "priority": "HIGH/MEDIUM/LOW"
        }
    ],
    "evidence_gaps": ["Gap 1", "Gap 2"]
}

No markdown fences. No explanation outside JSON."""


async def generate_prediction_for_target(convergence_row: dict) -> dict | None:
    """Generate a prediction card for a target with a convergence score."""
    target_id = convergence_row.get("target_id")
    target_label = convergence_row.get("target_label", "Unknown")

    if not target_id:
        return None

    # Get claims for this target
    claims = await fetch(
        """SELECT c.id, c.claim_type, c.predicate, c.confidence, c.value,
                  e.source_id, e.method, e.excerpt,
                  s.title AS source_title, s.external_id AS pmid, s.source_type
           FROM claims c
           LEFT JOIN evidence e ON e.claim_id = c.id
           LEFT JOIN sources s ON e.source_id = s.id
           WHERE c.subject_id = $1
           ORDER BY c.confidence DESC""",
        target_id,
    )

    if not claims:
        return None

    # Format claims for LLM
    claims_text_lines = []
    for i, c in enumerate(claims[:30], 1):  # Cap at 30
        c = dict(c)
        source_info = ""
        if c.get("pmid"):
            source_info = f" (PMID: {c['pmid']})"
        elif c.get("source_title"):
            source_info = f" ({c['source_title'][:50]})"
        method_info = f" [method: {c['method']}]" if c.get("method") else ""
        conf = f" [confidence: {c['confidence']:.2f}]" if c.get("confidence") else ""

        claims_text_lines.append(
            f"{i}. [ID: {c['id']}] [{c['claim_type']}] {c['predicate']}{source_info}{method_info}{conf}"
        )

    claims_text = "\n".join(claims_text_lines)

    # Find linked patents
    patent_rows = await fetch(
        """SELECT id FROM sources
           WHERE source_type = 'patent'
             AND (LOWER(title) LIKE $1 OR LOWER(abstract) LIKE $1)
           LIMIT 10""",
        f"%{target_label.lower()}%",
    )
    linked_patent_ids = [str(r["id"]) for r in patent_rows]

    user_prompt = (
        f"Target: {target_label}\n"
        f"Convergence Score: {convergence_row['composite_score']:.3f} "
        f"({convergence_row['confidence_level']})\n"
        f"Claims: {convergence_row['claim_count']} from "
        f"{convergence_row['source_count']} sources\n\n"
        f"Evidence Claims:\n{claims_text}"
    )

    api_key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("No ANTHROPIC_API_KEY — generating fallback prediction")
        return _fallback_prediction(convergence_row, claims, linked_patent_ids)

    try:
        client = anthropic.AsyncAnthropic(api_key=api_key)
        message = await client.messages.create(
            model=MODEL,
            max_tokens=3000,
            system=PREDICTION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        content = message.content[0].text.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [ln for ln in lines if not ln.strip().startswith("```")]
            content = "\n".join(lines).strip()

        result = json.loads(content)

    except (json.JSONDecodeError, KeyError) as e:
        logger.error("Failed to parse prediction JSON for %s: %s", target_label, e)
        return _fallback_prediction(convergence_row, claims, linked_patent_ids)
    except anthropic.APIError as e:
        logger.error("Anthropic API error for %s: %s", target_label, e)
        return _fallback_prediction(convergence_row, claims, linked_patent_ids)

    # Extract claim IDs from LLM classification
    summary = result.get("evidence_summary", {})
    supporting_ids = [
        item["claim_id"] for item in summary.get("supporting", [])
        if isinstance(item, dict) and "claim_id" in item
    ]
    contradicting_ids = [
        item["claim_id"] for item in summary.get("contradicting", [])
        if isinstance(item, dict) and "claim_id" in item
    ]
    neutral_ids = [
        item["claim_id"] for item in summary.get("neutral", [])
        if isinstance(item, dict) and "claim_id" in item
    ]

    return {
        "prediction_text": result.get("prediction_text", ""),
        "target_label": target_label,
        "target_id": target_id,
        "convergence_score": convergence_row["composite_score"],
        "convergence_breakdown": json.dumps({
            "volume": convergence_row["volume"],
            "lab_independence": convergence_row["lab_independence"],
            "method_diversity": convergence_row["method_diversity"],
            "temporal_trend": convergence_row["temporal_trend"],
            "replication": convergence_row["replication"],
        }),
        "confidence_level": convergence_row["confidence_level"],
        "supporting_claims": supporting_ids,
        "contradicting_claims": contradicting_ids,
        "neutral_claims": neutral_ids,
        "evidence_summary": json.dumps(summary),
        "suggested_experiments": json.dumps(result.get("suggested_experiments", [])),
        "evidence_gaps": result.get("evidence_gaps", []),
        "linked_patents": linked_patent_ids,
        "convergence_score_id": convergence_row.get("id"),
    }


def _fallback_prediction(convergence_row: dict, claims: list, patent_ids: list) -> dict:
    """Generate a basic prediction without LLM."""
    target_label = convergence_row.get("target_label", "Unknown")
    claim_ids = [str(dict(c)["id"]) for c in claims]

    return {
        "prediction_text": (
            f"Modulating {target_label} activity will affect SMN-dependent motor neuron "
            f"survival pathways, based on {convergence_row['claim_count']} converging claims "
            f"from {convergence_row['source_count']} independent sources."
        ),
        "target_label": target_label,
        "target_id": convergence_row.get("target_id"),
        "convergence_score": convergence_row["composite_score"],
        "convergence_breakdown": json.dumps({
            "volume": convergence_row["volume"],
            "lab_independence": convergence_row["lab_independence"],
            "method_diversity": convergence_row["method_diversity"],
            "temporal_trend": convergence_row["temporal_trend"],
            "replication": convergence_row["replication"],
        }),
        "confidence_level": convergence_row["confidence_level"],
        "supporting_claims": claim_ids,
        "contradicting_claims": [],
        "neutral_claims": [],
        "evidence_summary": json.dumps({"supporting": [], "contradicting": [], "neutral": []}),
        "suggested_experiments": json.dumps([]),
        "evidence_gaps": ["LLM unavailable — manual review needed"],
        "linked_patents": patent_ids,
        "convergence_score_id": convergence_row.get("id"),
    }


async def generate_all_predictions(min_score: float = 0.5) -> dict:
    """Generate prediction cards for all targets with convergence score ≥ min_score."""
    convergence_rows = await fetch(
        "SELECT * FROM convergence_scores WHERE composite_score >= $1 ORDER BY composite_score DESC",
        min_score,
    )

    generated = 0
    skipped = 0

    for conv in convergence_rows:
        conv = dict(conv)
        target_key = conv["target_key"]

        # Check if prediction already exists
        existing = await fetchval(
            "SELECT COUNT(*) FROM prediction_cards WHERE target_id = $1 AND weights_version = $2",
            conv.get("target_id"),
            conv.get("weights_version", "v1"),
        )
        if existing and existing > 0:
            skipped += 1
            continue

        result = await generate_prediction_for_target(conv)
        if not result:
            skipped += 1
            continue

        # Insert prediction card
        await execute(
            """INSERT INTO prediction_cards
                (convergence_score_id, prediction_text, target_label, target_id,
                 convergence_score, convergence_breakdown, confidence_level,
                 supporting_claims, contradicting_claims, neutral_claims,
                 evidence_summary, suggested_experiments, evidence_gaps,
                 linked_patents, status, score_history, weights_version)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                       'draft', $15, $16)""",
            result["convergence_score_id"],
            result["prediction_text"],
            result["target_label"],
            result["target_id"],
            result["convergence_score"],
            result["convergence_breakdown"],
            result["confidence_level"],
            result["supporting_claims"],
            result["contradicting_claims"],
            result["neutral_claims"],
            result["evidence_summary"],
            result["suggested_experiments"],
            result["evidence_gaps"],
            result["linked_patents"],
            json.dumps([{
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "score": float(result["convergence_score"]),
                "delta": 0.0,
                "new_claims": 0,
                "note": "Initial generation",
            }]),
            conv.get("weights_version", "v1"),
        )
        generated += 1

    logger.info("Prediction generation complete: %d generated, %d skipped", generated, skipped)
    return {
        "predictions_generated": generated,
        "predictions_skipped": skipped,
        "min_score_threshold": min_score,
    }
```

---

### Task 5: MCP Tools — 2 New Tools

**Files:**
- Modify: `mcp_server/server.py`

Add 2 new tools after existing tools:

```python
@mcp.tool()
async def get_predictions(target: str = "", min_score: float = 0.0, limit: int = 10) -> dict:
    """Get prediction cards — falsifiable, evidence-grounded predictions for SMA targets.

    Each prediction card contains:
    - A falsifiable prediction statement
    - Convergence score (0-1) with 5-dimension breakdown
    - Supporting, contradicting, and neutral evidence
    - Suggested experiments and evidence gaps
    """
    params = {"min_score": min_score, "limit": min(limit, 50)}
    if target:
        params["target"] = target
    cards = await _get("/predictions", params=params)
    return {
        "predictions": cards,
        "count": len(cards),
        "filter": {"target": target, "min_score": min_score},
    }


@mcp.tool()
async def get_convergence_score(target: str) -> dict:
    """Get the evidence convergence score breakdown for a specific SMA target.

    Shows 5 scoring dimensions:
    - Volume (0.15): claim count
    - Lab Independence (0.30): unique research groups
    - Method Diversity (0.20): experimental method variety
    - Temporal Trend (0.15): evidence consistency over time
    - Replication (0.20): findings reproduced by different groups

    All weights are open source at github.com/Bryzant-Labs/sma-platform
    """
    # First resolve target name to ID
    targets = await _get("/targets", params={"limit": 100})
    target_lower = target.lower()
    matched = [t for t in targets if target_lower in (t.get("symbol") or "").lower()
               or target_lower in (t.get("name") or "").lower()]

    if not matched:
        return {"error": f"Target '{target}' not found", "available_targets": [t["symbol"] for t in targets]}

    target_id = matched[0]["id"]
    try:
        score = await _get(f"/convergence/{target_id}")
        return score
    except Exception:
        return {"error": f"No convergence score computed for {matched[0]['symbol']}. Run computation first."}
```

---

### Task 6: Frontend — Predictions Tab

**Files:**
- Modify: `frontend/index.html`

Add "Predictions" to navigation tabs and build the Predictions page with:

1. **Card grid** — each card shows: target, prediction text (truncated), score bar, confidence badge
2. **Detail view** — full prediction with evidence breakdown, stacked bar chart for dimensions, experiments, gaps
3. **Filters** — by target, confidence level, status
4. **Markdown export button** — opens `/predictions/{id}/export?format=markdown`
5. **Trend indicator** — ↗ ↘ → based on score_history

The frontend follows existing patterns: `createElement + textContent` (no innerHTML), `el()` helper, fetch from `/api/v2/predictions`.

Key functions to add:
- `renderPredictionsPage()` — main page with card grid
- `renderPredictionDetail(id)` — full detail view
- `renderConvergenceBar(breakdown)` — horizontal stacked bar for 5 dimensions
- `confidenceBadge(level)` — colored badge (low=gray, medium=blue, high=green, very_high=gold)

---

### Task 7: Auto-Validation Script

**Files:**
- Create: `scripts/validate_predictions.py`

```python
"""Daily auto-validation of prediction cards against new evidence.

Run after daily PubMed ingestion (e.g. 06:30 UTC via cron).
Re-computes convergence scores and updates prediction card status.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.sma_platform.core.database import init_pool, close_pool, execute, fetch, fetchrow
from src.sma_platform.reasoning.convergence_engine import compute_target_convergence

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SCORE_CHANGE_THRESHOLD = 0.1  # Trigger status change at ±0.1


async def validate_predictions():
    """Re-validate all active prediction cards."""
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        logger.error("DATABASE_URL not set")
        return

    await init_pool(dsn)

    try:
        # Get active predictions
        cards = await fetch(
            """SELECT * FROM prediction_cards
               WHERE status IN ('validated', 'monitoring')
               ORDER BY convergence_score DESC"""
        )

        if not cards:
            logger.info("No active predictions to validate")
            return

        updated = 0
        for card in cards:
            card = dict(card)
            target_id = str(card["target_id"])

            # Re-compute convergence
            result = await compute_target_convergence(target_id)
            if not result:
                continue

            new_score = result["composite_score"]
            old_score = float(card["convergence_score"])
            delta = round(new_score - old_score, 3)

            if abs(delta) < 0.001:
                continue  # No change

            # Count new claims since last validation
            last_validated = card.get("last_validated_at") or card["created_at"]
            new_claims_row = await fetchrow(
                """SELECT COUNT(*) AS cnt FROM claims
                   WHERE subject_id = $1 AND created_at > $2""",
                target_id, last_validated,
            )
            new_claims = new_claims_row["cnt"] if new_claims_row else 0

            # Build history entry
            history = card.get("score_history") or []
            if isinstance(history, str):
                history = json.loads(history)

            history.append({
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "score": new_score,
                "previous_score": old_score,
                "delta": delta,
                "new_claims_count": new_claims,
            })

            # Determine new status
            new_status = card["status"]
            if delta > SCORE_CHANGE_THRESHOLD:
                new_status = "strengthened"
            elif delta < -SCORE_CHANGE_THRESHOLD:
                new_status = "weakened"

            # Update card
            await execute(
                """UPDATE prediction_cards SET
                    convergence_score = $1,
                    confidence_level = $2,
                    score_history = $3,
                    status = $4,
                    last_validated_at = NOW(),
                    updated_at = NOW()
                   WHERE id = $5""",
                new_score,
                result["confidence_level"],
                json.dumps(history),
                new_status,
                card["id"],
            )
            updated += 1
            logger.info(
                "Updated %s: %.3f → %.3f (Δ%.3f) → %s",
                card["target_label"], old_score, new_score, delta, new_status,
            )

        logger.info("Validation complete: %d/%d cards updated", updated, len(cards))

    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(validate_predictions())
```

---

### Task 8: Deploy + Initial Run

**Step 1: Deploy code to moltbot**

```bash
rsync -av src/ moltbot:/home/bryzant/sma-platform/src/
rsync -av scripts/ moltbot:/home/bryzant/sma-platform/scripts/
rsync -av mcp_server/ moltbot:/home/bryzant/sma-platform/mcp_server/
rsync -av db/ moltbot:/home/bryzant/sma-platform/db/
rsync -av frontend/index.html moltbot:/var/www/sma-research.info/index.html
```

**Step 2: Run database migration (Task 1 SQL)**

**Step 3: Restart API**

```bash
ssh moltbot "pm2 restart sma-api"
```

**Step 4: Trigger convergence computation**

```bash
curl -X POST https://sma-research.info/api/v2/convergence/compute -H "x-admin-key: sma-admin-2026"
```

**Step 5: Trigger prediction generation**

```bash
curl -X POST https://sma-research.info/api/v2/predictions/generate -H "x-admin-key: sma-admin-2026"
```

**Step 6: Verify**

```bash
curl https://sma-research.info/api/v2/convergence | python3 -m json.tool | head -30
curl https://sma-research.info/api/v2/predictions | python3 -m json.tool | head -30
```
