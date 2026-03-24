# Ingestion Layer

Adapters for external biomedical data sources. Each adapter handles one API,
normalizes the response, and provides async functions for the API/reasoning layers.

## Structure

```
ingestion/
  __init__.py
  adapters/
    pubmed.py           # NCBI PubMed via Biopython Entrez
    clinicaltrials.py   # ClinicalTrials.gov v2 API
    geo.py              # NCBI GEO (Gene Expression Omnibus)
    chembl.py           # ChEMBL bioactivity data
    uniprot.py          # UniProt protein data
    kegg.py             # KEGG pathway data
    biorxiv.py          # bioRxiv preprint monitoring
    alphafold.py        # AlphaFold structure predictions
    string_db.py        # STRING protein interactions
    nvidia_nims.py      # NVIDIA NIM APIs (DiffDock, GenMol)
    patents.py          # Patent landscape data
    pmc.py              # PubMed Central full-text
    orthologs.py        # Cross-species ortholog data
    nanopore_rnaseq.py  # Nanopore RNA-seq processing
    diffdock_local.py   # Local DiffDock GPU docking
```

## Adapter Pattern

```python
"""Source adapter docstring with API docs link."""

from __future__ import annotations
import logging
import httpx
from ...core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.example.com/v1"

async def search(query: str, max_results: int = 100) -> list[dict]:
    """Fetch and normalize data from external source."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{BASE_URL}/search", params={"q": query})
        resp.raise_for_status()
        raw = resp.json()
    return [_normalize(item) for item in raw["results"]]

def _normalize(raw: dict) -> dict:
    """Convert API-specific format to platform schema."""
    return { ... }
```

## Key Rules

- All external calls are `async` using `httpx.AsyncClient`
- Biopython Entrez calls (PubMed, GEO) run in thread via `asyncio.to_thread()`
- Always set timeouts on HTTP clients (default: 30s)
- Handle rate limits gracefully — external APIs have quotas
- Config (API keys, emails) from `core.config.settings`
- Log failures with context: `logger.error(f"Failed to fetch {source}: {e}")`
- Normalize external data into platform-standard dicts before returning

## Anti-Patterns

- Do NOT store data directly — return normalized dicts, let the caller decide
- Do NOT block the event loop with synchronous I/O
- Do NOT hardcode API keys — use `settings.*`
- Do NOT retry infinitely — fail fast with clear error messages
