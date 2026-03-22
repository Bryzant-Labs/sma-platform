# Frontend Render Audit — 2026-03-22

## Summary

Comprehensive audit of all data-rendering sections in the SMA Research Platform frontend (`index.html`). Each section's JavaScript was compared against the actual API response field names by querying the live backend via SSH.

**Bugs found and fixed: 9**
**Sections verified working: 20+**
**Deployment: Completed via rsync to moltbot**

---

## Bugs Found & Fixed

### 1. Screening: `target_symbol` vs `target`
- **Section**: Drug Screening (`/screening`)
- **API endpoint**: `/api/v2/screen/compounds/results`
- **Problem**: API returns `target_symbol` for each compound, but JS reads `c.target` in search filter, target dropdown filter, and target dropdown population.
- **Impact**: Target filter dropdown was empty; search by target returned no results.
- **Fix**: Changed all `c.target` references in screening to `c.target || c.target_symbol`.

### 2. Synthesis Contradictions: nested objects vs flat numbers
- **Section**: Cross-Paper Synthesis > Contradictions tab (`/synthesis`)
- **API endpoint**: `/api/v2/synthesis/contradictions`
- **Problem**: API returns `positive_claims` and `negative_claims` as nested objects (`{count: 1, example_predicate: "...", example_source: "..."}`), but JS read them as flat numbers. This rendered as `[object Object]`.
- **Impact**: Positive/negative claim counts showed "[object Object]" instead of numbers.
- **Fix**: Added type checking — if value is an object, extract `.count`; otherwise use as-is.

### 3. Synthesis Contradictions: `contradiction_score` vs `score`
- **Section**: Cross-Paper Synthesis > Contradictions tab
- **Problem**: API returns `contradiction_score` but JS read `c.score`.
- **Impact**: Score column showed "-" for all rows.
- **Fix**: Changed to read `c.contradiction_score` with fallback to `c.score`.

### 4. Synthesis Surprise: `surprises` vs `surprise` response key
- **Section**: Cross-Paper Synthesis > Surprise tab
- **API endpoint**: `/api/v2/synthesis/surprise`
- **Problem**: API wraps results in `data.surprises` array, but JS tried `data.surprise`. Missing the plural form.
- **Impact**: Entire surprise tab showed "No surprise connection data available yet."
- **Fix**: Added `data.surprises` as first fallback option.

### 5. Synthesis Surprise: `paper_overlap` vs `papers`
- **Section**: Cross-Paper Synthesis > Surprise tab
- **Problem**: API returns `paper_overlap` but JS read `s.papers || s.paper_count`.
- **Impact**: Papers column showed "0" for all rows.
- **Fix**: Added `s.paper_overlap` as first fallback.

### 6. Synthesis Surprise: `claim_diversity` vs `diversity`
- **Section**: Cross-Paper Synthesis > Surprise tab
- **Problem**: API returns `claim_diversity` but JS read `s.diversity`.
- **Impact**: Diversity column showed "-" for all rows.
- **Fix**: Added `s.claim_diversity` as first fallback.

### 7. Synthesis Surprise: `source_independence` vs `independence`
- **Section**: Cross-Paper Synthesis > Surprise tab
- **Problem**: API returns `source_independence` but JS read `s.independence`.
- **Impact**: Independence column showed "-" for all rows.
- **Fix**: Added `s.source_independence` as first fallback.

### 8. Synthesis Shared Mechanisms: `num_claims` vs `claims`
- **Section**: Cross-Paper Synthesis > Shared Mechanisms tab
- **API endpoint**: `/api/v2/synthesis/shared-mechanisms`
- **Problem**: API returns `num_claims` but JS read `m.claims || m.claim_count`.
- **Impact**: Claims column showed "0" for all mechanisms.
- **Fix**: Added `m.num_claims` as first fallback.

### 9. Comparative Biology: `ortholog_id` vs `ortholog_gene_id`
- **Section**: Cross-Species Comparative (`/comparative`)
- **API endpoint**: `/api/v2/comparative/orthologs`
- **Problem**: API returns `ortholog_id` but JS read `o.ortholog_gene_id` for gene ID display, NCBI links, and detail panel.
- **Impact**: Gene ID column showed "-"; NCBI Gene links were broken/missing.
- **Fix**: Changed all 6 occurrences to `o.ortholog_id || o.ortholog_gene_id`.

---

## Sections Verified Working (No Bugs)

| Section | URL | API Endpoint | Status |
|---------|-----|-------------|--------|
| Targets | `/targets` | `/api/v2/targets` | 58 targets, all fields match |
| Trials | `/trials` | `/api/v2/trials` | 451 trials, filters work |
| Drugs | `/drugs` | `/api/v2/drugs` | 21 drugs, expand trials works |
| Sources | `/sources` | `/api/v2/sources` + `/evidence` | 6,535 sources with claim counts |
| Claims | `/claims` | `/api/v2/claims` (enriched) | 11,061 claims, server-side pagination |
| Hypotheses | `/hypotheses` | `/api/v2/hypotheses/prioritized` | 1,272 hypotheses across 3 tiers |
| Predictions | `/predictions` | `/api/v2/predictions` | Prediction cards render |
| Convergence | `/convergence` | `/api/v2/convergence/scores` | Scores table + prediction cards |
| Scores | `/scores` | `/api/v2/scores` | 60 targets with 8 dimensions |
| Repurposing | `/repurposing` | `/api/v2/screen/repurposing` | 75 candidates |
| Candidates | `/candidates` | `/api/v2/screen/candidates` | 795 screened, tiered |
| Graph | `/graph` | `/api/v2/graph` | Nodes + edges render |
| Outcomes | `/outcomes` | `/api/v2/drug-outcomes` | 227 outcomes |
| Datasets | `/datasets` | `/api/v2/datasets` | 7 datasets |
| Evidence | `/evidence` | `/api/v2/evidence` | Evidence links by source |
| Calibration | `/calibration` | `/api/v2/calibration/bayesian/report` | Grade A (89.8%) |
| News | `/news` | `/api/v2/news` | Posts with categories, tags |
| Synthesis Co-occurrences | `/synthesis` | `/api/v2/synthesis/cooccurrences` | 20 rows |
| Synthesis Temporal | `/synthesis` | `/api/v2/synthesis/temporal` | 20 rows |

## Backend Issues (Not Frontend Bugs)

1. **Priority v2** (`/api/v2/prioritize/v2/targets`): Returns HTTP 500. Backend issue.
2. **Synergy** (`/api/v2/nim-batch/synergy`): Returns 404. Not deployed yet.
3. **Comparative Matrix** (`/api/v2/comparative/matrix`): Returns 404. Endpoint removed or renamed.

## Files Modified

- `/mnt/c/Users/bryza/Dropbox/Christian fischer/SMA/sma-platform/frontend/index.html` (9 fixes)
