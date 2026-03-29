# API Layer

FastAPI route handlers. Thin controllers that delegate to `reasoning/` for logic
and `core/database` for data access.

## Structure

- `app.py` — Application factory (`create_app()`), lifespan management, middleware, router registration
- `auth.py` — Admin key authentication via `require_admin_key` dependency
- `routes/` — ~100 route modules, each with `router = APIRouter()`

## Route Patterns

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from ...core.database import execute, fetch, fetchrow
from ..auth import require_admin_key

router = APIRouter()

# Read endpoint — no auth required
@router.get("/things")
async def list_things(limit: int = Query(default=100, ge=1, le=2000)):
    rows = await fetch("SELECT * FROM things LIMIT $1", limit)
    return [dict(r) for r in rows]

# Write endpoint — admin auth required
@router.post("/things")
async def create_thing(body: ThingCreate, _key: str = Depends(require_admin_key)):
    await execute("INSERT INTO things (...) VALUES ($1, $2)", body.name, body.value)
    return {"status": "created"}
```

## Key Rules

- ALL routers mount at `/api/v2` prefix (set in `app.py`, not in route files)
- Auth: `X-Admin-Key` header checked via `require_admin_key` dependency
- Use `Query()` with `ge`/`le` constraints for pagination params
- Use `HTTPException(404, "...")` for not-found, `HTTPException(400, "...")` for bad input
- Return dicts directly — FastAPI handles JSON serialization
- Use Pydantic `BaseModel` subclasses for POST/PUT request bodies
- Always use `$N` parameterized queries via `fetch()` / `fetchrow()` / `execute()`

## CORS

Only `https://sma-research.info` is allowed. Do not add `*` or localhost origins.

## Security Headers

Applied via middleware in `app.py`: CSP, X-Frame-Options DENY, HSTS, etc.
Swagger UI paths get a relaxed CSP to allow cdn.jsdelivr.net.

## Docs

Swagger UI at `/api/v2/docs`, ReDoc at `/api/v2/redoc`.
Controlled by `settings.enable_docs` (default: True).
