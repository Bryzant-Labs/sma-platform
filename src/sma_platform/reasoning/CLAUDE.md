# Reasoning Layer

Core business logic for the SMA Research Platform. Each module encapsulates
a specific analytical capability — scoring, hypothesis generation, prediction,
drug discovery, etc.

## Structure

~55 modules organized by function:

- **Scoring & Prioritization**: `scorer.py`, `prioritizer.py`, `target_prioritizer.py`, `target_prioritizer_v2.py`, `source_quality.py`, `source_weigher.py`
- **Hypothesis Generation**: `hypothesis_generator.py`, `hypothesis_prioritizer.py`
- **Drug Discovery**: `repurposing.py`, `molecule_screener.py`, `virtual_screening.py`, `synergy_predictor.py`
- **Structural Biology**: `protein_binder_design.py`, `ml_docking_proxy.py`, `md_generator.py`
- **Genomics/Splicing**: `splice_predictor.py`, `splice_benchmark.py`, `splice_offtarget.py`, `splicing_map.py`, `rna_binding.py`, `smn_locus.py`
- **Analytics**: `enrichment_analyzer.py`, `convergence.py`, `graph_expander.py`, `mutation_cascade.py`, `uncertainty.py`, `uncertainty_engine.py`, `bayesian.py`
- **Translational**: `translation.py`, `experiment_designer.py`, `prediction_generator.py`, `patent_landscape.py`, `patent_fto.py`
- **Advanced**: `bioelectric.py`, `spatial_omics.py`, `regeneration_signatures.py`, `nmj_signaling.py`, `multisystem_sma.py`, `proprioception.py`

## Patterns

```python
"""Module docstring explaining the analysis."""

from __future__ import annotations

import logging
from ..core.database import fetch, fetchrow, execute
from ..core.config import settings

logger = logging.getLogger(__name__)

# Constants at module level (weights, thresholds, prompts)
SCORING_WEIGHTS = { ... }

async def compute_something(target_id: str) -> dict:
    """Pure async function — fetches data, runs logic, returns result."""
    rows = await fetch("SELECT ... FROM ... WHERE id = $1", target_id)
    # Business logic here
    return {"score": computed_value}
```

## Key Rules

- All functions are `async def` — database calls are async
- Use `$N` parameterized queries via `fetch()`, `fetchrow()`, `execute()`
- Access config via `settings.*` from `core.config`
- LLM calls use `httpx` with proper error handling and timeout
- Return plain dicts — the API layer handles JSON serialization
- Log with context: `logger.error(f"Failed to {action}: {e}", exc_info=True)`
- Multi-LLM routing: Groq/Gemini for bulk, Claude for reasoning, OpenAI for embeddings

## Anti-Patterns

- Do NOT import from `api/` — reasoning is independent of HTTP layer
- Do NOT catch exceptions silently — always log
- Do NOT make synchronous DB calls
- Do NOT hardcode API keys — use `settings.*`
- Do NOT return HTTP status codes — that is the API layer's job
