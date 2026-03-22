# Claim Relink Results — 2026-03-22

## Summary

After updating the claim extractor with fixed aliases and word-boundary matching,
the relinker was triggered via `POST /api/v2/relink/claims`.

### Relink API Response

| Metric | Value |
|--------|-------|
| Claims checked | 3,928 |
| Claims updated | 80 |
| Duration | 10.33 seconds |

### Targets that gained claims (from relinker)

| Target | New Links |
|--------|-----------|
| CFL2 | 5 |
| ROCK2 | 4 |
| RIPK1 | 3 |
| PLS3 | 2 |
| MAPK_PATHWAY | 2 |
| TP53 | 2 |
| SETX | 2 |
| UBA1 | 1 |

**Note:** The relinker changed `subject_type` from other categories (gene, drug, etc.)
to `target` for 80 claims where the subject/object UUID already pointed to a target record.

---

## Current Platform Stats

| Entity | Count |
|--------|-------|
| Sources | 6,412 |
| Targets | 58 |
| Drugs | 21 |
| Trials | 451 |
| Datasets | 7 |
| Claims | 10,905 |
| Evidence | 10,894 |
| Hypotheses | 1,272 |

---

## Top 25 Targets by Total Linked Claims (all subject_types)

| Rank | Target | Claims |
|------|--------|--------|
| 1 | SMN1 | 2,094 |
| 2 | SMN2 | 1,045 |
| 3 | SMN_PROTEIN | 1,025 |
| 4 | HTRA2 | 389 |
| 5 | TARDBP | 355 |
| 6 | NMJ_MATURATION | 331 |
| 7 | NEFL | 287 |
| 8 | BCL2 | 228 |
| 9 | TP53 | 193 |
| 10 | MTOR_PATHWAY | 162 |
| 11 | CASP3 | 157 |
| 12 | UBA1 | 151 |
| 13 | PLS3 | 89 |
| 14 | MAPK_PATHWAY | 70 |
| 15 | MSTN | 69 |
| 16 | HDAC_PATHWAY | 67 |
| 17 | CORO1C | 54 |
| 18 | IGF1 | 54 |
| 19 | FUS | 53 |
| 20 | BDNF | 45 |
| 21 | JNK_PATHWAY | 38 |
| 22 | CHRNA1 | 29 |
| 23 | MUSK | 29 |
| 24 | NCALD | 26 |
| 25 | BCL2L1 | 26 |

---

## Specific Targets of Interest

| Target | Total Claims | Breakdown |
|--------|-------------|-----------|
| STMN2 | 22 | gene:20, other:2 |
| PLS3 | 89 | gene:65, pathway:4, disease:4, target:3, cell_component:1, protein:1, other:1 |
| NCALD | 26 | gene:9, drug:7, target:6, pathway:1 |
| PFN1 | 21 | gene:15, target:3, protein:1 |
| CFL2 | 12 | gene:7, drug:3, target:2 |
| ROCK2 | 15 | drug:11, gene:3, pathway:1 |

### Observations

1. **STMN2** has 22 claims but none with `subject_type=target` -- all classified as `gene` or `other`.
   The relinker did not touch these because they were already linked by UUID to the target record.

2. **PLS3** is the strongest of the specific targets with 89 total claims (13th overall).

3. **ROCK2** has 15 claims but most (11) are classified as `drug` type -- likely claims about
   ROCK inhibitors (fasudil, etc.) that reference the ROCK2 target.

4. **CFL2** gained 5 new target-typed links from the relinker (now 12 total across all types).

5. **NCALD** has 26 claims with good diversity across gene, drug, and target types.

6. **PFN1** has 21 claims, mostly classified as `gene` type.

### Next Steps

- Consider normalizing `subject_type` so that all claims linked to a target UUID
  have `subject_type=target` (currently many are `gene`, `drug`, `pathway`).
- STMN2 and ROCK2 would benefit from re-classification.
- Run a second pass to convert `gene`-typed claims that point to target UUIDs into `target` type.
