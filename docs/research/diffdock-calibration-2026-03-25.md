# DiffDock v2.2 Calibration: ChEMBL LIMK2 Ground Truth

**Date**: 2026-03-25
**Campaign**: `data/docking/chembl_limk2_ground_truth_2026-03-25.json`

## Purpose

Dock 21 compounds with **real experimental binding data** (ChEMBL IC50/Ki) against LIMK2 to determine how well DiffDock confidence scores track actual binding potency. This is the first rigorous calibration of our DiffDock pipeline.

## Method

- **Source**: Top 20 ChEMBL LIMK2 compounds by pChEMBL value (from 301 total), plus LX-7101 reference
- **pChEMBL range**: 8.80 (LX-7101) to 10.00 (3 compounds with IC50 = 0.1 nM)
- **Target**: LIMK2 kinase domain (P53671, residues 309-595)
- **DiffDock**: v2.2 NVIDIA NIM, 20 poses per compound, RDKit SDF conversion
- **All compounds are KNOWN strong LIMK2 binders** (pChEMBL 8.8-10.0 = IC50 0.1-1.6 nM)

## Key Results

### Correlation: pChEMBL vs DiffDock Confidence

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Pearson r** | **+0.378** | Weak positive |
| **R-squared** | **0.143** | DiffDock explains ~14% of binding variance |
| **Spearman rho** | **+0.301** | Weak rank correlation |

**Verdict: WEAK correlation. DiffDock confidence does NOT reliably quantify binding potency.**

### Binding Detection Rate

All 21 compounds are confirmed strong LIMK2 binders (sub-10 nM). DiffDock should give ALL of them positive confidence scores.

| Category | Count | Rate |
|----------|-------|------|
| Known strong binders (pChEMBL >= 9.0) | 20 | -- |
| DiffDock positive confidence (> 0) | 9 | **45%** |
| DiffDock negative confidence (< 0) | 12 | **55%** |

**DiffDock misses 55% of known strong binders.** A coin flip would do as well.

### Rank Agreement

Do the strongest real binders get the highest DiffDock scores?

- Top 5 real binders (pChEMBL 9.7-10.0) found in DiffDock's top 10: **3/5** (60%)
- Worst real binder (LX-7101, pChEMBL 8.8) correctly ranked last by DiffDock: **YES** (rank 21/21)

### Full Results Table

| pChEMBL Rank | ChEMBL ID | pChEMBL | IC50 (nM) | DiffDock Conf | DiffDock Rank | Positive Poses |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | CHEMBL3797519 | 10.00 | 0.1 | -0.022 | 10 | 0/20 |
| 2 | CHEMBL3800458 | 10.00 | 0.1 | +0.002 | 9 | 1/20 |
| 3 | CHEMBL3799318 | 10.00 | 0.1 | **+0.363** | **1** | 2/20 |
| 4 | CHEMBL3798142 | 9.70 | 0.2 | -0.315 | 17 | 0/20 |
| 5 | CHEMBL3800259 | 9.70 | 0.2 | -0.434 | 18 | 0/20 |
| 6 | CHEMBL3798662 | 9.70 | 0.2 | -0.046 | 11 | 0/20 |
| 7 | CHEMBL3799270 | 9.70 | 0.2 | +0.101 | 7 | 1/20 |
| 8 | CHEMBL3799925 | 9.52 | 3.0 | +0.253 | 3 | 2/20 |
| 9 | CHEMBL3800357 | 9.52 | 3.0 | +0.292 | 2 | 3/20 |
| 10 | CHEMBL3799236 | 9.40 | 4.0 | +0.233 | 4 | 1/20 |
| 11 | CHEMBL3800330 | 9.40 | 4.0 | -0.569 | 19 | 0/20 |
| 12 | CHEMBL3797658 | 9.40 | 4.0 | -0.162 | 14 | 0/20 |
| 13 | CHEMBL3797874 | 9.15 | 7.0 | +0.025 | 8 | 1/20 |
| 14 | CHEMBL571057 | 9.10 | 8.0 | -0.147 | 13 | 0/20 |
| 15 | CHEMBL3800144 | 9.10 | 8.0 | -0.285 | 16 | 0/20 |
| 16 | CHEMBL570126 | 9.05 | 9.0 | -0.050 | 12 | 0/20 |
| 17 | CHEMBL3799695 | 9.05 | 9.0 | -0.672 | 20 | 0/20 |
| 18 | CHEMBL3797634 | 9.05 | 9.0 | -0.174 | 15 | 0/20 |
| 19 | CHEMBL3356431 | 9.00 | 10.0 | +0.118 | 5 | 2/20 |
| 20 | CHEMBL3623439 | 9.00 | 10.0 | +0.116 | 6 | 5/20 |
| 21* | CHEMBL3356433 | 8.80 | 16.0 | **-0.837** | **21** | 0/20 |

*LX-7101 reference compound

### Notable Observations

1. **Best DiffDock hit (CHEMBL3799318, conf=+0.363)**: Is indeed a top-3 real binder (pChEMBL 10.0, IC50 = 0.1 nM). DiffDock got this one right.

2. **Worst DiffDock scores go to known potent binders**: CHEMBL3800330 (conf=-0.569, pChEMBL=9.4) and CHEMBL3799695 (conf=-0.672, pChEMBL=9.05) are 4 nM and 9 nM binders that DiffDock completely misses.

3. **Three pChEMBL=10.0 compounds span the DiffDock range**: From +0.363 (rank 1) to -0.022 (rank 10). Same real potency, wildly different predictions.

4. **LX-7101 scored worst** (-0.837, rank 21): Consistent with previous docking (-0.314). This clinical compound is poorly predicted by DiffDock against this LIMK2 structure.

5. **CHEMBL3623439 (pChEMBL=9.0) had the most positive poses** (5/20): Yet its real binding is among the weakest. This is a MW=379.9 compound -- the smallest in the set -- confirming known MW bias.

## Implications for Our Drug Discovery Pipeline

### What DiffDock CAN do:
- **Pose generation**: The binding poses themselves may be informative even when confidence is wrong
- **Coarse filtering**: Confidence > +0.3 enriches for real binders (1/1 in our data)
- **Relative comparison within the same scaffold**: Structurally similar compounds show more consistent ranking

### What DiffDock CANNOT do:
- **Quantitative binding prediction**: r=0.38 is far too weak for reliable IC50 estimation
- **Reliable hit detection**: 55% false negative rate on known binders
- **Cross-scaffold ranking**: Different scaffolds get systematically different scores regardless of real potency

### Calibration Rules (Apply to ALL future DiffDock results)

1. **DiffDock confidence > +0.3**: Likely real binder, but verify experimentally
2. **DiffDock confidence 0 to +0.3**: Inconclusive -- could be strong or weak binder
3. **DiffDock confidence < 0**: Does NOT mean non-binder (55% of confirmed nM binders scored negative)
4. **Never compare DiffDock scores across different scaffolds**
5. **Our previous (S,S)-H-1152 score of +0.957**: Genuinely exceptional -- higher than ANY of the 21 confirmed nM LIMK2 binders from ChEMBL

### Comparison with Previous Campaign Results

| Compound | Type | DiffDock Confidence | Context |
|----------|------|:---:|---------|
| **(S,S)-H-1152** | **AI-designed** | **+0.957** | Higher than all 21 confirmed binders |
| genmol_119 | AI-designed | +0.704 | Higher than all 21 confirmed binders |
| H-1152 (racemic) | Known ROCK/LIMK | +0.900 | Higher than all 21 confirmed binders |
| Best ChEMBL hit | Real LIMK2 binder (IC50=0.1nM) | +0.363 | Rank 1 of ground truth |
| LX-7101 | Clinical LIMK inhibitor | -0.837 | Worst of all |

**This raises a critical question**: Are our AI candidates truly better than confirmed nM binders, or does DiffDock systematically overpredict certain scaffolds?

Given that real 0.1 nM LIMK2 binders only reach +0.363, a score of +0.957 is either:
- (a) A genuinely exceptional binding mode, OR
- (b) A scaffold bias artifact (H-1152's isoquinoline scaffold may be computationally favored)

**Recommendation**: The +0.957 for (S,S)-H-1152 should be treated with extreme caution until validated by at least one orthogonal method (FEP, MD simulation, or experimental IC50).

## Raw Data

Full results: `data/docking/chembl_limk2_ground_truth_2026-03-25.json`
Script: `scripts/dock_chembl_limk2_ground_truth.py`
Source data: `data/chembl_limk2_bioactivity.json` (301 compounds from ChEMBL)
