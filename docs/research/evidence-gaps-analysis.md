# Evidence Gaps Analysis — SMA Research Platform

**Date**: 2026-03-22
**Platform**: moltbot (localhost:8090)
**Pipeline run**: 2026-03-22 03:00 UTC (633s, 0 errors)

---

## Platform Overview

| Metric | Count |
|--------|------:|
| Sources | 6,412 |
| Targets | 60 |
| Claims | 31,108 |
| Evidence links | 31,097 |
| Hypotheses | 1,272 |
| Drugs | 21 |
| Clinical Trials | 451 |
| Datasets | 7 |

### Claim Linking Health (from enrichment/stats)

- **Total claims analyzed**: 6,772
- **Subject-linked**: 4,477 (66.1%)
- **Subject-unlinked**: 2,295 (33.9%)
- **985 unlinked gene-type claims** — these are the primary relinking opportunity

---

## Target Evidence Gap Rankings

### Priority 1: Zero Claims (16 targets)

These targets exist in the database but have NO linked claims. They need both **source ingestion** and **claim extraction**.

| Target | Description | Gap Score |
|--------|-------------|-----------|
| ABI2 | Arp2/3 regulator, 1.5x up in SMA MNs | 1.00 |
| CD44 | Cell adhesion glycoprotein, ECM receptor | 1.00 |
| CTNNA1 | Alpha-catenin, convergence score in SMA | 1.00 |
| DNMT3B | De novo DNA methyltransferase | 1.00 |
| GALNT6 | Golgi-resident glycosyltransferase | 1.00 |
| LDHA | Key glycolytic enzyme, convergence score 28 | 1.00 |
| LRPN4 | Agrin co-receptor at NMJ | 1.00 |
| LY96 | TLR4 coreceptor, discovery score 0.5 | 1.00 |
| NEDD4L | E3 ubiquitin ligase, convergence score 22 | 1.00 |
| NEFH | pNfH biomarker for axonal damage | 1.00 |
| NMJ_MATURATION | NMJ defects pathway | 1.00 |
| RAPSN | AChR clustering scaffolding protein | 1.00 |
| SARM1 | Axon degeneration master regulator | 1.00 |
| SMN_PROTEIN | Core SMA protein | 1.00 |
| SPATA18 | Mitochondrial quality control | 1.00 |
| SULF1 | Extracellular sulfatase | 1.00 |

**Note**: Relink stage DID find matches for some "zero-claim" targets today: LRPN4 (12), CD44 (6), NEDD4L (12), SARM1 (8), ANK3 (5), DNMT3B (5), LDHA (6), SPATA18 (1), SMN_PROTEIN (20). The evidence/gaps endpoint may be stale — these counts need verification after today's relink completes its write-back.

### Priority 2: Critically Underlinked (flagged targets)

| Target | Linked Claims | Sources | Gap Score | Evidence Types Present | Missing Types |
|--------|------------:|--------:|-----------|----------------------|---------------|
| **STMN2** | 4 | 3 | 0.91 | splicing_event (3), other (1) | gene_expression, protein_interaction, pathway, drug_target, drug_efficacy, biomarker, neuroprotection, motor_function, survival, safety |
| **CFL2** | 2 | 0 | 0.82 | drug_target (1), gene_expression (1) | protein_interaction, pathway, drug_efficacy, biomarker, splicing, neuroprotection, motor_function, survival, safety |
| **NCALD** | 6 | 3 | 0.73 | neuroprotection (3), drug_target (1), gene_expression (1), other (1) | protein_interaction, pathway, drug_efficacy, biomarker, splicing, motor_function, survival, safety |
| **ROCK2** | 5 | 2 | 0.64 | pathway (2), gene_expression (1), motor_function (1), neuroprotection (1) | protein_interaction, drug_target, drug_efficacy, biomarker, splicing, survival, safety |
| **PLS3** | 10 | 4 | 0.64 | other (4), pathway (2), protein_interaction (2), drug_efficacy (1), neuroprotection (1) | gene_expression, drug_target, biomarker, splicing, motor_function, survival, safety |
| **PFN1** | 18 | 5 | 0.64 | other (6), protein_interaction (5), gene_expression (3), neuroprotection (3), pathway (1) | drug_target, drug_efficacy, biomarker, splicing, motor_function, survival, safety |
| **CORO1C** | 14 | 3 | 0.36 | pathway (5), drug_target (2), gene_expression (2), protein_interaction (2), drug_efficacy (1), neuroprotection (1), splicing (1) | biomarker, motor_function, survival, safety |

### For Comparison: Well-Linked Targets

| Target | Linked Claims | Sources | Gap Score |
|--------|------------:|--------:|-----------|
| SMN1 | 1,198 | 328 | 0.00 |
| SMN2 | 655 | 220 | 0.00 |
| BCL2 | 193 | 99 | 0.00 |
| TP53 | 170 | 75 | 0.00 |

---

## Relink Pipeline Analysis (2026-03-22 run)

Today's relink checked **18,514 claims** and updated **4,414 claims** across all targets.

### Relink results for key targets:

| Target | Claims Relinked Today | Currently Linked (evidence/gaps) | Delta |
|--------|---------------------:|--------------------------------:|-------|
| STMN2 | 6 | 4 | Relink found more than currently shown |
| PLS3 | 17 | 10 | +7 potential unlinked |
| NCALD | 32 | 6 | **+26 potential unlinked** |
| ROCK2 | 5 | 5 | Stable |
| PFN1 | 1 | 18 | Already well-linked from prior runs |
| CORO1C | 16 | 14 | +2 |
| CFL2 | 0 | 2 | Not picked up by relinker |
| SMN_PROTEIN | 20 | 0 | **Evidence gaps endpoint is stale** |

**Key finding**: The relink stage IS running and finding matches, but the evidence/gaps endpoint appears to report stale data. NCALD had 32 relinks today but only shows 6 in the gaps API. This suggests either:
1. The relink results are not persisting to the claims table, or
2. The evidence/gaps endpoint caches old data and needs a refresh trigger

---

## Semantic Search: Unlinked Claims Found

Using `/api/v2/search?q=<TARGET>`, I found claims that semantically match but may not be formally linked:

| Target | Claims in Search | Explicitly Mention Gene | Sources Found | Key Finding |
|--------|----------------:|----------------------:|-------------:|-------------|
| STMN2 | 19 | 0 | 1 | Only 1 source paper — needs PubMed ingestion for stathmin-2/STMN2 specifically |
| PLS3 | 10 | 6 | 10 | Good source coverage (10 papers); 6 claims mention PLS3 explicitly |
| NCALD | 13 | 0 | 7 | 7 sources exist but claims use "neurocalcin delta" / "calcium sensor" — alias matching needed |
| PFN1 | 18 | 18 | 2 | Claims mention PFN1 well; only 2 source papers — needs more ingestion |
| CFL2 | 17 | 2 | 3 | Only 2 claims mention CFL2 explicitly; rest are semantic matches for cofilin/actin |
| ROCK2 | 9 | 3 | 11 | Good source coverage (11 papers); claims use "ROCK2" and "RhoA/ROCK2" |
| CORO1C | 16 | 5 | 4 | Moderate; many claims reference coronin pathway indirectly |

---

## Root Cause Analysis

### Problem 1: Alias Matching Gap
The relinker matches gene symbols but misses synonyms:
- STMN2 = "stathmin-2", "SCG10", "superior cervical ganglion-10"
- NCALD = "neurocalcin delta", "NCALD", "neurocalcin-delta"
- CFL2 = "cofilin-2", "CFL2", "muscle cofilin"
- ROCK2 = "Rho-associated kinase 2", "ROCK-II"

**Action**: The relink algorithm should include an alias map for these targets.

### Problem 2: Insufficient Source Papers
Some targets simply lack ingested literature:
- **STMN2**: Only 1 source paper found. There are dozens of STMN2+SMA papers in PubMed (Klim et al. 2019, Melamed et al. 2019, etc.)
- **CFL2**: 3 sources. Literature exists for cofilin in motor neuron context but not ingested.
- **PFN1**: 2 sources. PFN1-ALS convergence papers exist (Wu et al. 2012, etc.)

**Action**: Targeted PubMed queries needed (see below).

### Problem 3: Evidence/Gaps Endpoint Staleness
The `/api/v2/evidence/gaps` counts do not match the relink output from today's pipeline. NCALD shows 6 linked but 32 were relinked today. SMN_PROTEIN shows 0 but 20 were relinked.

**Action**: Investigate whether relink write-back is failing silently, or if the gaps endpoint needs a cache-bust.

---

## Daily Pipeline Status

### Cron Schedule
```
0 3 * * * /home/bryzant/sma-platform/scripts/daily_pipeline.sh
```
Runs daily at 03:00 UTC with 9 stages:
1. PubMed ingestion (7 days)
2. bioRxiv/medRxiv preprints (7 days)
3. ClinicalTrials.gov update
4. Claim extraction on unprocessed sources
5. Claim relinking to targets
6. Convergence score recomputation
7. Evidence score refresh
8. HuggingFace dataset publish
9. Stats snapshot

### Latest Run (2026-03-22)
- **Duration**: 633 seconds (10.5 min)
- **Errors**: 0
- **Claims relinked**: 4,414 / 18,514 checked
- **HuggingFace**: Published (no new data changes)

### Known Issues in Pipeline Logs
1. **bioRxiv author parsing bug**: 6 DOIs failed with `a sized iterable container expected (got type 'str')` — authors stored as JSON string instead of list
2. **ClinicalTrials conditions parsing**: Same bug pattern — conditions field stored as string not list
3. **PubMed date parsing**: 10 PMIDs failed with `'str' object has no attribute 'toordinal'` — date strings not converted to date objects
4. **Gemini API 503s**: Intermittent service unavailability errors in sma-api logs

### Data Freshness
- Last PubMed ingestion: 2026-03-21 09:29 UTC (81 items)
- Last source added: 2026-03-21 22:33 UTC
- Last claim added: 2026-03-22 08:25 UTC

---

## Priority Actions

### Immediate (fix today)

1. **Investigate relink persistence**: Check if the 4,414 relinked claims from today's pipeline actually persisted. Run:
   ```
   curl -s -X POST "http://localhost:8090/api/v2/relink/claims" -H "x-admin-key: sma-admin-2026" -d '{"dry_run": true}'
   ```
   Compare dry_run counts with post-relink evidence/gaps.

2. **Fix the evidence/gaps cache**: If relink IS persisting, the gaps endpoint needs a refresh. Check if `scores/refresh` triggers a gaps recalculation.

### Short-term (this week)

3. **Targeted PubMed ingestion for underlinked targets**:
   ```
   # STMN2 — axonal regulator, TDP-43/SMA connection
   POST /api/v2/ingest/pubmed with query: "STMN2 OR stathmin-2 AND spinal muscular atrophy"

   # CFL2 — cofilin-2, actin dynamics in MN
   POST /api/v2/ingest/pubmed with query: "cofilin-2 OR CFL2 AND motor neuron"

   # PFN1 — profilin, ALS-SMA convergence
   POST /api/v2/ingest/pubmed with query: "profilin-1 OR PFN1 AND motor neuron disease"

   # ROCK2 — Rho kinase, fasudil
   POST /api/v2/ingest/pubmed with query: "ROCK2 OR Rho-kinase AND spinal muscular atrophy"

   # NCALD — neurocalcin delta, SMA modifier
   POST /api/v2/ingest/pubmed with query: "neurocalcin delta OR NCALD AND SMA"
   ```

4. **Add alias map to relinker**: The relink algorithm should map gene symbols to their common synonyms/aliases. At minimum:
   - STMN2 -> ["stathmin-2", "SCG10"]
   - NCALD -> ["neurocalcin delta", "neurocalcin-delta"]
   - CFL2 -> ["cofilin-2", "muscle cofilin"]
   - ROCK2 -> ["Rho-associated kinase 2", "ROCK-II", "Rho kinase 2"]
   - PLS3 -> ["plastin-3", "T-plastin", "fimbrin"]
   - PFN1 -> ["profilin-1", "profilin 1"]
   - CORO1C -> ["coronin-1C", "coronin 1C"]

### Medium-term (next 2 weeks)

5. **Fix pipeline bugs**:
   - bioRxiv/ClinicalTrials author/conditions parsing (JSON string vs list)
   - PubMed date parsing (str vs date object)

6. **Fill evidence type gaps**: Even well-linked targets like PFN1 (18 claims) are missing drug_target, drug_efficacy, biomarker, splicing, motor_function, survival, and safety evidence types. Consider:
   - Running claim extraction with prompts that specifically ask for these evidence types
   - Adding ChEMBL/DrugBank integration for drug_target claims
   - Adding ClinVar/OMIM integration for biomarker claims

7. **Address the 985 unlinked gene-type claims**: These are claims with subject_type="gene" but no target match. Run analysis to identify which gene symbols appear most frequently and whether new targets should be created or aliases added.

---

## Summary Table: Diagnosis per Target

| Target | Claims | Diagnosis | Action |
|--------|-------:|-----------|--------|
| STMN2 | 4 | Too few source papers (1) + no aliases | Ingest + add aliases |
| CFL2 | 2 | Few sources (3) + not picked up by relinker | Ingest + fix relinker |
| NCALD | 6 | Relinker found 32 but only 6 show — persistence bug? | Fix persistence + add aliases |
| ROCK2 | 5 | Moderate sources (11) but claims not linking | Add aliases (RhoA/ROCK2) |
| PLS3 | 10 | Good sources (10), decent explicit mentions (6) | Add aliases (plastin-3) |
| PFN1 | 18 | Good claims but few sources (2) | Ingest more papers |
| CORO1C | 14 | Best of the underlinked, 7 evidence types | Mostly OK — fill biomarker/motor gaps |
