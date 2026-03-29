# SMA Research Platform

Open-source biology-first target discovery platform for Spinal Muscular Atrophy (SMA).
Built with FastAPI + asyncpg/aiosqlite + vanilla JS frontend.

## Architecture

```
src/sma_platform/
  api/           # FastAPI routes (app.py + routes/*.py)
  core/          # Config, database, LLM client
  reasoning/     # Business logic — scorers, generators, predictors
  ingestion/     # External data adapters (PubMed, GEO, ChEMBL, etc.)
  agents/        # AI agent orchestration (drug discovery)
  ucm/           # Unified Context Model builder
```

## Module Categories

| Category    | Description                                                |
|-------------|------------------------------------------------------------|
| `api`       | FastAPI route files in `api/routes/` — thin controllers    |
| `reasoning` | Core logic — hypothesis generation, scoring, prediction    |
| `ingestion` | Adapters for external APIs (PubMed, ClinicalTrials, KEGG)  |
| `core`      | Shared infra — config, database pool, LLM client          |
| `agents`    | AI-driven autonomous agents                                |
| `ucm`       | Unified Context Model for MCP integration                  |

## Key Patterns

### Database
- Dual backend: PostgreSQL (asyncpg) in production, SQLite (aiosqlite) in dev
- All queries use `$N` parameterized syntax (auto-converted for SQLite)
- Helper functions: `fetch()`, `fetchrow()`, `execute()` from `core.database`
- NEVER use string concatenation for SQL — always parameterized

### FastAPI Routes
- Every route file creates `router = APIRouter()`
- All routers registered in `api/app.py` with `include_router(X.router, prefix="/api/v2")`
- Admin/write endpoints use `Depends(require_admin_key)` for auth
- Response format: return dicts/lists directly (FastAPI auto-serializes)
- Use Pydantic models for request body validation

### Reasoning Layer
- Pure business logic — no HTTP concerns
- All DB calls are `async def` using `core.database` helpers
- LLM calls go through `core.llm_client` or direct `httpx` to provider APIs
- Multi-LLM routing: Groq for bulk extraction, Claude for validation

### Ingestion Adapters
- Each adapter in `ingestion/adapters/` handles one external source
- Pattern: fetch raw data → normalize → store via `core.database`
- Adapters: pubmed, clinicaltrials, geo, chembl, uniprot, kegg, biorxiv, alphafold, string_db, nvidia_nims, patents, pmc, orthologs, nanopore_rnaseq, diffdock_local

### Configuration
- All config via `pydantic_settings.BaseSettings` in `core/config.py`
- Environment variables or `.env` file
- Access as `settings.database_url`, `settings.anthropic_api_key`, etc.

## Anti-Patterns (Do NOT)
- Do NOT use `psycopg2` — this is an async codebase (asyncpg/aiosqlite)
- Do NOT hardcode API keys — use `settings.*` from `core/config.py`
- Do NOT add CORS origins beyond `sma-research.info`
- Do NOT skip parameterized queries — SQL injection is a critical risk
- Do NOT return raw exception details to clients — log server-side, return generic messages
- Do NOT create synchronous DB calls — everything is async
- Do NOT modify existing code without understanding the dual-DB abstraction layer

## How to Run

```bash
# Dev (SQLite)
pip install -e ".[dev]"
python main.py

# Production (PostgreSQL)
DATABASE_URL=postgresql://... python main.py

# With auto-reload
DEV_RELOAD=1 python main.py
```

Server runs on port 8100 by default. Swagger docs at `/api/v2/docs`.

## Architecture Intelligence

Auto-generated architecture maps live in `docs/architecture/`:
- `module-map.json` — all modules with imports, classes, functions
- `endpoint-map.json` — all FastAPI endpoints with full paths
- `call-graph.json` — internal cross-module import graph
- `db-table-map.json` — SQL table references per module

Regenerate with: `python scripts/generate_module_map.py`
