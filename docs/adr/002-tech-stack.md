# ADR-002: Technology Stack

**Status**: Accepted
**Date**: 2025-03-14

## Decision

- **API**: FastAPI (async, auto-docs, Pydantic validation)
- **Database**: PostgreSQL with asyncpg (same pattern as Bryzant CMS)
- **Data format**: UCM (TSV → Parquet pipeline, from sma_ucm)
- **Ingestion**: Biopython (PubMed/GEO), httpx (ClinicalTrials.gov REST API)
- **LLM**: Anthropic Claude (claim extraction, hypothesis generation)
- **Testing**: pytest + pytest-asyncio

## Rationale

- FastAPI over Flask: native async, better for I/O-heavy biomedical API calls
- PostgreSQL: proven at Bryzant CMS scale, JSONB for flexible metadata, UUID PKs
- asyncpg: same driver used in CMS, familiar patterns
- Biopython: battle-tested NCBI API wrapper, handles rate limiting
- UCM format preserved from existing sma_ucm codebase

## Consequences

- Can reuse database patterns from Bryzant CMS
- FastAPI's auto-generated docs make the API self-documenting
- No ORM for now — raw SQL with asyncpg for performance
