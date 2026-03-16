# DiffDock v2.2 NIM — 378 Docking Results Analysis

**Date:** 2026-03-16
**Tool:** DiffDock v2.2 NIM (NVIDIA cloud API)
**Structures:** AlphaFold v6 predicted structures
**Campaign:** 54 compounds x 7 SMA targets = 378 blind dockings
**Runtime:** 24 minutes | **Cost:** $0 (NVIDIA NIM free credits)

---

## Key Findings

### 1. Only 3 positive-confidence hits in 378 dockings

Positive DiffDock confidence is rare and indicates strong predicted binding:

| Rank | Compound | Target | Confidence | Note |
|------|----------|--------|-----------|------|
| **1** | **4-Aminopyridine** | **CORO1C** | **+0.251** | Approved drug, strongest hit |
| 2 | CHEMBL1381595 | NCALD | +0.076 | Thiazole derivative |
| 3 | CHEMBL1328375 | CORO1C | +0.048 | Second CORO1C binder |

### 2. 4-AP is a multi-target binder (4 targets within top 25)

| Target | Confidence | Rank |
|--------|-----------|------|
| CORO1C | +0.251 | #1 |
| NCALD | -0.443 | #18 |
| SMN2 | -0.447 | #19 |
| SMN1 | -0.487 | #20 |
| UBA1 | -0.507 | #21 |
| STMN2 | -1.047 | — |
| PLS3 | -1.281 | — |

### 3. UBA1 is the most druggable target

UBA1 has the most compounds with reasonable binding (5 in top 25):
- CHEMBL1331875 (-0.089)
- CHEMBL1301743 (-0.100)
- CHEMBL1400508 (-0.179)
- CHEMBL1301787 (-0.282)
- CHEMBL1381595 (-0.337)

### 4. SMN2/STMN2 are the hardest targets to dock

- SMN2 average confidence: -2.059 (worst of all targets)
- STMN2 average confidence: -2.380
- These proteins may have less accessible binding pockets in the AlphaFold structures

---

## Per-Target Statistics

| Target | Compounds | Best Conf | Best Compound | Avg Conf | Positive Hits |
|--------|-----------|-----------|---------------|----------|---------------|
| CORO1C | 54 | +0.251 | 4-aminopyridine | -1.520 | 2 |
| NCALD | 54 | +0.076 | CHEMBL1381595 | -1.486 | 1 |
| UBA1 | 54 | -0.089 | CHEMBL1331875 | -1.207 | 0 |
| SMN1 | 54 | -0.067 | CHEMBL1411542 | -1.616 | 0 |
| PLS3 | 54 | -0.216 | CHEMBL1301743 | -1.778 | 0 |
| SMN2 | 54 | -0.447 | 4-aminopyridine | -2.059 | 0 |
| STMN2 | 54 | -1.047 | 4-aminopyridine | -2.380 | 0 |

---

## Multi-Target Binders (conf > -0.5 for 2+ targets)

| Compound | Targets (confidence) | Note |
|----------|---------------------|------|
| **4-aminopyridine** | CORO1C(+0.251), NCALD(-0.443), SMN2(-0.447), SMN1(-0.487) | **4 targets** |
| CHEMBL1381595 | NCALD(+0.076), UBA1(-0.337) | Thiazole |
| CHEMBL1301743 | UBA1(-0.100), PLS3(-0.216) | — |
| CHEMBL1575581 | NCALD(-0.314), CORO1C(-0.407) | Our v1 top hit |

---

## Comparison with DiffDock v1 Results

| Compound | Target | v1 Confidence | v2.2 Confidence | Consistent? |
|----------|--------|--------------|-----------------|-------------|
| 4-AP | SMN2 | +0.100 | -0.447 | Scoring model changed |
| CHEMBL1575581 | SMN2 | -0.090 | not in top | — |
| 4-AP | PLS3 | -0.200 | -1.281 | Both negative |

Note: DiffDock v2.2 was trained on PLINDER dataset with different scoring calibration. Absolute values are not directly comparable across versions.

---

## Implications for Preprint

1. **4-AP→CORO1C (+0.251)** is the strongest single finding — should be the lead result
2. **Multi-target profile** strengthens the drug repurposing hypothesis
3. **CORO1C** connection to actin dynamics links 4-AP to the PLS3 rescue pathway
4. The fact that only 3/378 pairs show positive confidence makes these hits statistically notable
5. UBA1 as a druggable target is a secondary finding worth reporting

---

## Raw Data

Full results: `gpu/results/nim_batch/diffdock_results.json` (378 entries)
Platform API: `GET /api/v2/gpu/jobs?job_type=diffdock_v2_nim`
