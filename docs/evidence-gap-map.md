# Evidence Gap Map — SMA Research Platform

**Generated**: 2026-03-22
**After cleanup**: 25,135 non-SMA claims removed (confidence < 0.2)
**Clean dataset**: 5,973 claims, 58 targets, 5,962 evidence links

## Summary

After removing non-SMA contamination (breast cancer, HCC, glioblastoma, prostate cancer claims that leaked in via shared gene names), the evidence landscape is much clearer.

## Tier 1: Well-Evidenced (>50 claims)

| Target | Type | Claims | Strongest Evidence Types | Key Gaps |
|--------|------|--------|--------------------------|----------|
| SMN1 | gene | 1,091 | biomarker (254), gene_expr (178), pathway (109) | None — comprehensive |
| SMN_PROTEIN | protein | 993 | neuroprot (155), gene_expr (138), pathway (105) | None — comprehensive |
| SMN2 | gene | 320 | biomarker (107), splicing (30), drug_eff (34) | Low protein_interaction (4) |
| BCL2 | gene | 221 | gene_expr (71), neuroprot (69), pathway (29) | Zero safety, low drug_target (7) |
| HTRA2 | gene | 200 | gene_expr (72), biomarker (21), neuroprot (17) | Zero splicing, zero safety |
| TP53 | gene | 190 | pathway (64), gene_expr (30), prot_int (21) | Zero survival, zero safety |
| CASP3 | gene | 162 | gene_expr (43), neuroprot (40), drug_target (22) | Zero biomarker, low survival |
| NEFL | gene | 160 | pathway (40), drug_eff (27), gene_expr (23) | Zero safety, zero splicing |
| NMJ_MATURATION | pathway | 92 | pathway (17), neuroprot (13) | Low drug evidence, zero safety |
| MTOR_PATHWAY | pathway | 81 | pathway (38), neuroprot (15) | Zero safety, zero splicing |
| TARDBP | gene | 68 | prot_int (12), neuroprot (12), motor (9) | Low drug_target (2), low survival (1) |
| UBA1 | gene | 53 | prot_int (11), pathway (12) | Zero safety, zero survival |

## Tier 2: Moderate Evidence (10-50 claims)

| Target | Claims | Key Gaps |
|--------|--------|----------|
| IGF1 | 46 | Zero safety, zero biomarker, zero splicing |
| MAPK_PATHWAY | 44 | Zero biomarker, zero safety, zero splicing |
| CORO1C | 37 | Zero survival, zero safety, low gene_expr (2) |
| HDAC_PATHWAY | 33 | Zero biomarker, zero safety |
| JNK_PATHWAY | 31 | Balanced but small across all types |
| FUS | 31 | Zero safety, zero biomarker (7), zero drug_target (0) |
| MSTN | 29 | Zero safety, zero gene_expr (2) |
| BCL2L1 | 26 | Zero safety, zero splicing, zero biomarker |
| CASP9 | 21 | Zero safety, zero biomarker, zero survival |
| BDNF | 19 | Zero safety, zero splicing, zero biomarker |
| NOTCH_PATHWAY | 16 | Most types missing — very sparse |
| TMEM41B | 15 | Zero gene_expr, zero safety, zero biomarker |
| RIPK1 | 14 | Zero neuroprot, motor, survival — new target, needs evidence |
| CAST | 14 | Zero gene_expr, zero biomarker |
| CNTF | 14 | Zero safety, zero biomarker, zero survival |
| WNT_PATHWAY | 12 | 8/12 pathway — almost nothing else |
| ROCK2 | 11 | Zero prot_int, zero safety — critical gap for Fasudil target |

## Tier 3: Sparse Evidence (<10 claims)

These targets need urgent evidence enrichment:

| Target | Claims | Notes |
|--------|--------|-------|
| GDNF | 9 | Neurotrophic factor, mostly neuroprotection |
| ANK3 | 9 | Mostly protein_interaction (4) |
| MUSK | 8 | NMJ receptor — important but underlinked |
| CTNNA1 | 8 | Mostly neuroprot (4) |
| ZPR1 | 8 | Underexplored modifier — needs claims |
| FST | 7 | Follistatin — myostatin antagonist |
| **STMN2** | **6** | **CRITICAL: core SMA target, only 6 linked claims!** |
| **NCALD** | **6** | **CRITICAL: known SMA modifier, only 6 linked claims!** |
| ACTR2 | 5 | Actin pathway — novel, expected sparse |
| **PLS3** | **5** | **CRITICAL: validated SMA modifier, only 5 linked claims!** |
| PFN1 | 3 | New target from sprint — needs enrichment |
| CFL2 | 3 | New target from sprint — needs enrichment |
| ACTG1 | 2 | Novel — no prior SMA papers |
| LY96 | 1 | Almost zero evidence |

## Critical Gaps

### 1. Core SMA targets with too few linked claims
**STMN2 (6), PLS3 (5), NCALD (6)** — these are well-established SMA modifier genes with hundreds of papers, but our claim-linking is broken for them. The claims exist but aren't linked to the target UUIDs. **This is a data quality bug, not a literature gap.**

### 2. Evidence type deserts
- **Safety data**: Almost no target has safety claims. This is critical for translational work.
- **Survival data**: Very sparse outside SMN1/SMN2.
- **Splicing events**: Only SMN1 (47), SMN2 (30), STMN2 (2), TARDBP (3) have any. Most targets: zero.

### 3. New targets need evidence
ROCK2, PFN1, CFL2, RIPK1, SARM1 — all added during the sprint but have <15 claims each. Need targeted PubMed ingestion for these genes.

## Action Items

1. **Fix claim-target linking** for STMN2, PLS3, NCALD — many claims mention these but aren't linked via subject_id/object_id
2. **Run targeted PubMed queries** for ROCK2, PFN1, CFL2, RIPK1, SARM1
3. **Add safety evidence** — search for adverse events, toxicity, contraindications for all drug targets
4. **Re-link claims to targets** using alias patterns (229 patterns exist but may not cover all)
