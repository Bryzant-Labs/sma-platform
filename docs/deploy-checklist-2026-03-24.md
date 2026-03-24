# Deployment Checklist — 2026-03-24

## Files Changed Since Last Deploy (HEAD~10)

```
.gitignore
frontend/index.html
src/sma_platform/ingestion/adapters/pubmed.py
src/sma_platform/reasoning/target_prioritizer_v2.py
```

### Uncommitted / New Files
```
M  .gitignore
M  frontend/index.html
M  src/sma_platform/ingestion/adapters/pubmed.py
?? data/geo/
?? data/pocket_results.json
?? docs/plans/2026-03-24-24h-sprint.md
?? docs/research/competitive-landscape-2026-03-22.md
?? docs/research/gpu-compute-sprint-2026-03-22.md
?? src/sma_platform/api/routes/pockets.py
?? scripts/audit_claims.py (new — claim dedup audit)
```

## Frontend Fixes Applied (This Session)
1. Fixed `showSection('ask')` -> `showSection('search')` (dead section reference)
2. Fixed `getElementById('ask-query')` -> `getElementById('chat-input')` (wrong element ID)
3. Replaced `innerHTML` with `textContent` on 3D view buttons (security)
4. Removed marketing language: "cutting-edge", "Querdenker thinking", "Harvard-level insights"

## Database Migrations Needed
- None (no schema changes in this batch)
- OPTIONAL: Run `scripts/dedup_claims.sql` after review to remove duplicate claims

## New pip Dependencies
- None

## Server Issues Found (PM2 Logs)
1. **Gemini 429 (rate limited)** — 9 occurrences in last 100 error lines. Need to add backoff/retry or reduce batch size.
2. **DiffDock 403 Forbidden** — NVIDIA NIM API key expired or quota exhausted. Renew at build.nvidia.com.
3. **bioRxiv API failures** — Connection retries for daily ingestion. Transient, has retry logic.
4. **Gemini JSON parse error** — Truncated JSON response from Gemini, claim extraction failed for 1 paper.
5. **Duplicate Operation ID warning** — `compute_convergence` route registered twice in FastAPI.

## API Status (Verified)
- Health: OK
- Stats: 14,662 claims, 7,367 sources, 63 targets, 1,472 hypotheses, 451 trials
- All tested endpoints returning 200: /targets, /claims, /sources, /hypotheses, /drugs, /screen/compounds/results

## Rsync Commands

```bash
# Sync frontend
rsync -avz --progress \
  "frontend/index.html" \
  moltbot:/home/bryzant/sma-platform/frontend/index.html

# Sync backend changes
rsync -avz --progress \
  "src/sma_platform/ingestion/adapters/pubmed.py" \
  moltbot:/home/bryzant/sma-platform/src/sma_platform/ingestion/adapters/pubmed.py

rsync -avz --progress \
  "src/sma_platform/reasoning/target_prioritizer_v2.py" \
  moltbot:/home/bryzant/sma-platform/src/sma_platform/reasoning/target_prioritizer_v2.py

# Sync audit script (optional)
rsync -avz --progress \
  "scripts/audit_claims.py" \
  moltbot:/home/bryzant/sma-platform/scripts/audit_claims.py

# After rsync, restart:
# ssh moltbot "cd /home/bryzant/sma-platform && pm2 restart sma-api"
# ssh moltbot "curl -s http://localhost:8090/api/v2/health"
```

## Pre-Deploy Verification
- [ ] Review all diffs: `git diff frontend/index.html`
- [ ] Verify no credentials in changed files
- [ ] Run audit_claims.py (optional, needs SSH tunnel)
- [ ] Confirm Gemini API quota status
- [ ] Confirm NVIDIA NIM API key is active

## Post-Deploy Verification
- [ ] `curl -s http://localhost:8090/api/v2/health` returns OK
- [ ] `pm2 logs sma-api --lines 10 --nostream --err` shows no new errors
- [ ] Frontend loads, section navigation works
- [ ] 3D structure viewer buttons visible on Structures page
- [ ] Search section accessible from homepage hero
