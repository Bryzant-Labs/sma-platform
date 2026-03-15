# SMA Research Platform — Security Audit

**Date:** 2026-03-15
**Auditor:** Claude Security Audit (automated + manual code review)
**Target:** https://sma-research.info
**Stack:** FastAPI (Python) + SQLite + Nginx/1.24.0 (Ubuntu) + Let's Encrypt TLS

---

## Summary

| Severity | Count | Issues |
|----------|-------|--------|
| CRITICAL | 1 | Unprotected admin write endpoints |
| HIGH | 3 | No rate limiting on admin/contact, CORS wildcard + cookie reflection, pagination DoS |
| MEDIUM | 3 | Missing security headers, nginx version disclosure, Swagger docs fully public |
| LOW | 2 | No pagination upper bound, /api/v2/targets POST unprotected |

---

## CRITICAL

### C-1: Admin write endpoints are publicly callable with no authentication

**Severity:** CRITICAL

**Confirmed live:**
```
POST /api/v2/ingest/pubmed  → HTTP 200 (actually fetched 51 papers from NCBI)
POST /api/v2/ingest/trials  → HTTP 200
POST /api/v2/scores/refresh → HTTP 200
POST /api/v2/relink/claims  → HTTP 200
```

The following endpoints perform expensive, stateful, or data-modifying operations and are reachable by **any anonymous internet user** with zero authentication:

| Endpoint | What it does |
|---|---|
| `POST /api/v2/ingest/pubmed?days_back=N` | Fetches from NCBI PubMed and writes to DB. `days_back` is uncapped — `days_back=3650` would pull 10 years of papers. |
| `POST /api/v2/ingest/trials` | Fetches all SMA trials from ClinicalTrials.gov and writes to DB. |
| `POST /api/v2/extract/claims` | Runs LLM (Anthropic Claude) on all unprocessed abstracts — **burns API credits on demand**. |
| `POST /api/v2/relink/claims` | Rewrites all claim-target associations. |
| `POST /api/v2/generate/hypotheses` | Runs LLM on all targets — **burns API credits on demand**. Confirmed: `DELETE FROM hypotheses` then regenerates. |
| `POST /api/v2/scores/refresh` | Re-scores all targets. |
| `POST /api/v2/generate/hypothesis/{target_id}` | LLM call per target. |

**Impact:** An attacker can (a) corrupt the database by triggering ingest loops, (b) exhaust Anthropic API credits by repeatedly calling `/extract/claims` and `/generate/hypotheses`, (c) delete and regenerate hypotheses at will.

**Fix:** Protect all admin POST endpoints with an API key or IP allowlist. Fastest safe approach: shared secret via request header.

In `src/sma_platform/api/app.py` — add a dependency:

```python
# In src/sma_platform/api/app.py
import os
from fastapi import Depends, HTTPException, Header

ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "")

async def require_admin_key(x_admin_key: str = Header(default="")):
    if not ADMIN_API_KEY:
        raise HTTPException(503, "Admin key not configured on server")
    if x_admin_key != ADMIN_API_KEY:
        raise HTTPException(403, "Forbidden")
```

Then in `src/sma_platform/api/routes/ingestion.py` and `scoring.py`, add the dependency:

```python
from fastapi import APIRouter, Depends
from ..app import require_admin_key

router = APIRouter(dependencies=[Depends(require_admin_key)])
```

Set `ADMIN_API_KEY` as an environment variable on moltbot (never hardcode). Call from cron with `-H "x-admin-key: $ADMIN_API_KEY"`.

---

## HIGH

### H-1: No rate limiting on any API endpoint

**Severity:** HIGH

**Confirmed:** 5 consecutive POST requests to `/contact` all returned HTTP 200. No `Retry-After` or `429` response.

There is no rate limiting anywhere in the application — not in Nginx, not in FastAPI. This affects:
- `/contact` — unlimited form submissions (spam database)
- `/ingest/pubmed` — can be triggered repeatedly to abuse NCBI (get the platform IP banned)
- All GET endpoints — scraping/DoS possible

**Fix (Nginx level — apply immediately, no code deploy needed):**

```nginx
# In /etc/nginx/nginx.conf or site config
limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;
limit_req_zone $binary_remote_addr zone=contact:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=admin:10m rate=2r/m;

# In server block:
location /api/v2/contact {
    limit_req zone=contact burst=2 nodelay;
    proxy_pass http://localhost:8090;
}

location ~ ^/api/v2/(ingest|extract|relink|generate|scores/refresh) {
    limit_req zone=admin burst=1 nodelay;
    proxy_pass http://localhost:8090;
    # Also restrict to localhost/known IPs only:
    # allow 127.0.0.1;
    # deny all;
}

location /api/v2/ {
    limit_req zone=api burst=10 nodelay;
    proxy_pass http://localhost:8090;
}
```

**Fix (FastAPI level — for defense in depth):**
Add `slowapi` or `fastapi-limiter` package.

```python
# pyproject.toml: add "slowapi>=0.1.9"
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# In contact.py:
@router.post("/contact")
@limiter.limit("5/minute")
async def submit_contact(request: Request, msg: ContactMessage):
    ...
```

### H-2: CORS wildcard + cookie reflection

**Severity:** HIGH

**Confirmed behavior:**

```
# Without cookie:
Origin: https://evil.com → Access-Control-Allow-Origin: *

# With cookie (any cookie):
Origin: https://evil.com + Cookie: x=1 → Access-Control-Allow-Origin: https://evil.com
                                          Vary: Origin
```

This is Starlette's intentional behavior: when `allow_origins=["*"]` and a request includes a `Cookie` header, the wildcard is replaced with the specific requesting origin. This is correct per the CORS spec (wildcards cannot be used with credentials), but it means **any site that sends a cross-origin request with cookies gets its origin explicitly reflected**, bypassing the intent of using a wildcard.

More critically: the CORS preflight allows **ALL methods** (`DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT`) from **any origin**. This means a malicious site can direct a victim's browser to call the admin endpoints if the victim has any cookie set.

**Impact:** If the admin POST endpoints ever gain session-based auth, this CORS configuration would make them fully CSRF-exploitable from any origin.

**Fix:** Restrict CORS to the actual frontend domain. Since the frontend is on the same domain, CORS is only needed if the API will be consumed by external sites.

```python
# In src/sma_platform/api/app.py
ALLOWED_ORIGINS = [
    "https://sma-research.info",
    "https://www.sma-research.info",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],       # Only what's actually needed
    allow_headers=["Content-Type"],
    allow_credentials=False,             # No cookies needed
)
```

### H-3: Unbounded pagination enables memory/CPU exhaustion

**Severity:** HIGH

**Confirmed:** `GET /api/v2/claims?limit=999999` and `GET /api/v2/sources?limit=999999` return HTTP 200. The `limit` and `offset` parameters across all listing endpoints (`/claims`, `/sources`, `/targets`, `/trials`, `/drugs`, `/datasets`, `/hypotheses`) accept arbitrarily large integers with no validation.

For a small dataset this is currently low risk, but as the database grows, a single request with `limit=1000000` could read the entire database into memory.

**Fix:** Cap the limit using FastAPI's `Query` validator in every listing endpoint:

```python
# Example for evidence.py (apply same pattern to all listing endpoints)
from fastapi import Query

async def list_claims(
    claim_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
```

---

## MEDIUM

### M-1: Missing HTTP security headers

**Severity:** MEDIUM

**Confirmed:** None of the following headers are present on any response:

```
X-Frame-Options: SAMEORIGIN          — missing → clickjacking possible
X-Content-Type-Options: nosniff      — missing → MIME sniffing attacks
Strict-Transport-Security: ...       — missing → SSL stripping possible
Content-Security-Policy: ...         — missing → XSS amplification
X-XSS-Protection: 1; mode=block     — missing (legacy browsers)
Referrer-Policy: strict-origin-when-cross-origin — missing
Permissions-Policy: ...             — missing
```

The only security-relevant header present is `Cache-Control: public, max-age=3600` on the frontend HTML.

**Fix:** Add to Nginx site config:

```nginx
# In the server {} block for sma-research.info
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; connect-src 'self' https://sma-research.info; img-src 'self' data:;" always;
```

Note: `'unsafe-inline'` is required because the frontend uses inline `<style>` and `<script>` blocks. Long-term, move JS/CSS to separate files and use nonces/hashes.

### M-2: Nginx server version disclosed

**Severity:** MEDIUM

Every response includes:
```
server: nginx/1.24.0 (Ubuntu)
```

This tells attackers the exact Nginx version, making targeted exploit selection easier.

**Fix:**
```nginx
# In nginx.conf, http {} block:
server_tokens off;
```

### M-3: Swagger UI and full OpenAPI schema publicly accessible

**Severity:** MEDIUM

The following are accessible with no authentication:
- `GET /api/v2/docs` — Interactive Swagger UI (HTTP 200)
- `GET /api/v2/redoc` — ReDoc UI
- `GET /api/v2/openapi.json` — Full OpenAPI schema listing all 29 endpoints with parameters and request bodies

The OpenAPI schema explicitly documents the admin write endpoints (`/ingest/pubmed`, `/extract/claims`, etc.) with full parameter descriptions, effectively serving as an attack manual.

**Fix:** Restrict the docs URLs, or disable them in production:

```python
# In src/sma_platform/api/app.py
import os
ENABLE_DOCS = os.environ.get("ENABLE_DOCS", "false").lower() == "true"

app = FastAPI(
    ...
    docs_url="/api/v2/docs" if ENABLE_DOCS else None,
    redoc_url="/api/v2/redoc" if ENABLE_DOCS else None,
    openapi_url="/api/v2/openapi.json" if ENABLE_DOCS else None,
)
```

Or restrict via Nginx:
```nginx
location ~ ^/api/v2/(docs|redoc|openapi\.json) {
    allow 127.0.0.1;   # Allow only local/SSH tunnel access
    deny all;
}
```

---

## LOW

### L-1: POST /api/v2/targets is unauthenticated

**Severity:** LOW

`POST /api/v2/targets` is a write endpoint (creates or upserts gene/protein targets) with no authentication. A test call returned `Internal Server Error` (likely because the SQLite schema doesn't support the `::jsonb` PostgreSQL cast used in the INSERT query), but the endpoint is exposed and callable.

Once the `::jsonb` SQLite bug is resolved (the `_pg_to_sqlite_query` function in `database.py` strips the cast but the INSERT query uses `RETURNING *` which SQLite doesn't support), this endpoint would allow anyone to inject arbitrary targets into the knowledge graph.

**Fix:** Apply the same `require_admin_key` dependency from C-1 to the targets POST endpoint.

### L-2: TLS 1.2 disabled — TLS 1.3 only

**Severity:** LOW (informational — this is actually good practice, noted for compatibility awareness)

**Confirmed:** The server rejects TLS 1.0, TLS 1.1, and TLS 1.2 connections. Only TLS 1.3 with `TLS_AES_256_GCM_SHA384` cipher is accepted.

This is a strong TLS configuration. However, some older research institution networks or automated monitoring tools may require TLS 1.2. If compatibility issues arise with legitimate users, adding TLS 1.2 with modern ciphers only is acceptable.

**Certificate:** Let's Encrypt `E8` CA, valid until **2026-05-05** (51 days remaining). Ensure auto-renewal is configured.

---

## What Is NOT Vulnerable

The following areas were reviewed and found to be correctly implemented:

**SQL Injection:** All database queries use parameterized `$N` placeholders. The dynamic query builder in `trials.py` and `datasets.py` correctly only interpolates `$N` parameter indices (not user input) into the SQL string — the actual filter values (status, phase, organism, etc.) are passed as bound parameters. No f-string SQL injection vulnerabilities found.

**Frontend XSS:** The frontend uses a safe DOM helper pattern throughout (`el()` function, `textContent` assignments, `document.createTextNode()`). No `innerHTML` assignments were found. External links use `rel="noopener"` to prevent reverse tainting. LLM-generated hypothesis content (`h.title`, `h.description`, `questions[q]`) is rendered via `textContent` / `{text: ...}` helper, not innerHTML — this is correct.

**HTTP to HTTPS redirect:** `http://sma-research.info/` correctly returns `301 Moved Permanently` to HTTPS.

**Input validation on contact form:** Pydantic validators enforce email format, name/message length limits, and required fields. This is properly implemented.

**No hardcoded secrets:** Reviewed `config.py`, `claim_extractor.py`, `hypothesis_generator.py`, `daily_ingest.py`. API keys are loaded from environment variables or `settings` object. `.env.example` contains only placeholder values.

**Certificate validity:** Let's Encrypt cert is valid (issued 2026-02-04, expires 2026-05-05).

---

## Priority Fix Order

1. **[CRITICAL — C-1]** Add admin API key authentication to all write endpoints before the next LLM-triggering deployment.
2. **[HIGH — H-1]** Add Nginx rate limiting (server config change, no redeploy of Python code needed).
3. **[MEDIUM — M-1]** Add security headers to Nginx config (alongside rate limiting, one config edit).
4. **[MEDIUM — M-2]** Add `server_tokens off` to Nginx.
5. **[HIGH — H-2]** Restrict CORS to `https://sma-research.info` only.
6. **[MEDIUM — M-3]** Disable or restrict Swagger UI in production.
7. **[HIGH — H-3]** Cap pagination `limit` parameter at 500 across all listing endpoints.
8. **[LOW — L-1]** Add auth to `POST /targets`.

Items 2, 3, 4 can be done in a single Nginx config edit with `nginx -s reload` — no application restart required.
