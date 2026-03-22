# Full Relink & Convergence Recomputation - 2026-03-22

## Summary

Full relink cycle and convergence recomputation run on the SMA Research Platform
to incorporate all new data from today's session (AF2 structures, GenMol molecules,
ESM2 embeddings, GEO analyses, hypothesis generation, claim extractions).

---

## Step 1: Relink Orphaned Claims

| Metric | Value |
|--------|-------|
| Claims checked | 5,031 |
| Claims updated (relinked) | 76 |
| Duration | 13.09 seconds |

76 previously orphaned claims were linked back to their respective targets.

---

## Step 2: Convergence Scores (Top 15)

| Target | Score | Confidence | Claims |
|--------|-------|------------|--------|
| SMN1 | 0.6350 | high | 2,895 |
| BCL2 | 0.6330 | high | 199 |
| SMN_PROTEIN | 0.6330 | high | 980 |
| SMN2 | 0.6310 | high | 1,759 |
| TP53 | 0.6290 | high | 190 |
| CASP3 | 0.6270 | high | 159 |
| PLS3 | 0.6240 | high | 117 |
| TARDBP | 0.6200 | high | 355 |
| UBA1 | 0.6190 | high | 171 |
| HDAC_PATHWAY | 0.6170 | high | 75 |
| NMJ_MATURATION | 0.6150 | high | 378 |
| HTRA2 | 0.6130 | high | 379 |
| MAPK_PATHWAY | 0.6130 | high | 107 |
| MSTN | 0.6130 | high | 98 |
| MTOR_PATHWAY | 0.6130 | high | 155 |

51 targets scored, 12 skipped (insufficient data).

---

## Step 3: Target Priority v2 (Top 10)

| Target | Composite Score | Tier |
|--------|----------------|------|
| SMN1 | 0.4731 | tier_2_promising |
| SMN2 | 0.4676 | tier_2_promising |
| NEDD4L | 0.4357 | tier_2_promising |
| CD44 | 0.4045 | tier_2_promising |
| LY96 | 0.4030 | tier_2_promising |
| STMN2 | 0.4014 | tier_2_promising |
| UBA1 | 0.4004 | tier_2_promising |
| CORO1C | 0.3744 | tier_3_exploratory |
| ANK3 | 0.3732 | tier_3_exploratory |
| GALNT6 | 0.3565 | tier_3_exploratory |

Note: No targets reached tier_1 yet. SMN1/SMN2 lead at ~0.47. NEDD4L is the
highest non-SMN target at 0.4357. CORO1C (our double-hit model) sits at 0.3744
in tier_3_exploratory.

---

## Step 4: Cross-Paper Synthesis

| Metric | Value |
|--------|-------|
| Co-occurrences found | 189 |
| Bridges found | 200 |
| Shared mechanisms | 34 |
| New cards created | 0 |

Top co-occurrence pairs:
1. SMN1 <-> SMN2: 292 shared papers (score 276.17)
2. SMN1 <-> SMN_PROTEIN: 124 shared papers (score 114.22)
3. SMN2 <-> SMN_PROTEIN: 59 shared papers (score 54.84)
4. NEFL <-> SMN2: 34 shared papers (score 30.71)
5. HTRA2 <-> NEFL: 32 shared papers (score 29.12)
6. BCL2 <-> CASP3: 28 shared papers (score 25.38)
7. NMJ_MATURATION <-> SMN2: 23 shared papers (score 21.64)

---

## Step 5: Platform Stats (Post-Recomputation)

| Entity | Count |
|--------|-------|
| Sources | 6,778 |
| Targets | 63 |
| Drugs | 21 |
| Clinical Trials | 451 |
| Datasets | 7 |
| Claims | 14,187 |
| Evidence entries | 14,176 |
| Hypotheses | 1,472 |

---

## Changes vs. Previous Session (2026-03-21)

| Metric | Previous | Current | Delta |
|--------|----------|---------|-------|
| Claims | ~30,789* | 14,187 | deduplicated |
| Hypotheses | 1,264 | 1,472 | +208 |
| Targets | 50 | 63 | +13 |

*Note: Previous claim count was before deduplication cleanup.
