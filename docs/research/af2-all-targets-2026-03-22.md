# SMA Target Structure Prediction -- All 55 Protein Targets

**Date:** 2026-03-22 18:30 UTC
**Pipeline:** AlphaFold DB v6 + ESMfold NIM (NVIDIA BioNeMo)
**Server:** moltbot (217.154.10.79)
**PDB directory:** `/home/bryzant/sma-platform/data/pdb/`

---

## Summary

| Metric | Value |
|--------|-------|
| Total targets in DB | 63 |
| Pathway entries (skipped) | 8 |
| Protein targets processed | 55 |
| Structures obtained | **55 (100%)** |
| Errors | 0 |
| Already existing | 11 |
| From AlphaFold DB v6 | 42 |
| From ESMfold NIM | 2 (ANK3, LRPN4) |

**Pathways skipped (not proteins):** HDAC_PATHWAY, JNK_PATHWAY, MAPK_PATHWAY, MTOR_PATHWAY, NMJ_MATURATION, NOTCH_PATHWAY, SMN_PROTEIN, WNT_PATHWAY

---

## Complete Structure Table

### High-confidence structures (pLDDT >= 80)

| # | Symbol | UniProt | Source | PDB File | pLDDT | Residues |
|---|--------|---------|--------|----------|-------|----------|
| 1 | LDHA | P00338 | AlphaFold DB v6 | LDHA_P00338.pdb | **96.1** | 332 |
| 2 | PFN1 | P07737 | AlphaFold DB v6 | PFN1_P07737.pdb | **95.7** | 140 |
| 3 | ACTG1 | P63261 | AlphaFold DB v6 | ACTG1_P63261.pdb | **95.4** | 375 |
| 4 | ACTR2 | P61160 | AlphaFold DB v6 | ACTR2_P61160.pdb | **94.0** | 394 |
| 5 | RAPSN | Q13702 | AlphaFold DB v6 | RAPSN_Q13702.pdb | **93.3** | 412 |
| 6 | UBA1 | P22314 | existing | UBA1_P22314.pdb | **92.7** | 1058 |
| 7 | CORO1C | Q9ULV4 | existing | CORO1C_Q9ULV4.pdb | **91.1** | 474 |
| 8 | MAPK14 | Q16539 | existing | MAPK14_Q16539.pdb | **89.9** | 360 |
| 9 | PLS3 | P13797 | existing | PLS3_P13797.pdb | **89.0** | 630 |
| 10 | CFL2 | Q9Y281 | AlphaFold DB v6 | CFL2_Q9Y281.pdb | **88.8** | 166 |
| 11 | GALNT6 | Q8NCL4 | AlphaFold DB v6 | GALNT6_Q8NCL4.pdb | **88.6** | 622 |
| 12 | FST | P19883 | AlphaFold DB v6 | FST_P19883.pdb | **87.8** | 344 |
| 13 | LY96 | Q9Y6Y9 | AlphaFold DB v6 | LY96_Q9Y6Y9.pdb | **87.7** | 160 |
| 14 | LIMK1 | P53667 | existing | LIMK1_kinase_390-638.pdb | **87.6** | 249 |
| 15 | NCALD | P61601 | existing | NCALD_P61601.pdb | **86.9** | 193 |
| 16 | CASP3 | P42574 | AlphaFold DB v6 | CASP3_P42574.pdb | **86.6** | 277 |
| 17 | SARM1 | Q6SZW1 | AlphaFold DB v6 | SARM1_Q6SZW1.pdb | **86.5** | 724 |
| 18 | STMN2 | Q93045 | existing | STMN2_Q93045.pdb | **85.9** | 179 |
| 19 | CNTF | P26441 | AlphaFold DB v6 | CNTF_P26441.pdb | **85.8** | 200 |
| 20 | CHRNA1 | P02708 | AlphaFold DB v6 | CHRNA1_P02708.pdb | **84.3** | 457 |
| 21 | C1QA | P02745 | AlphaFold DB v6 | C1QA_P02745.pdb | **83.7** | 245 |
| 22 | CTNNA1 | P35221 | AlphaFold DB v6 | CTNNA1_P35221.pdb | **83.0** | 906 |
| 23 | ANK3 | Q12955 | ESMfold NIM | ANK3_Q12955.pdb | **82.7** | 1000* |
| 24 | TMEM41B | Q5BJD5 | AlphaFold DB v6 | TMEM41B_Q5BJD5.pdb | **82.8** | 291 |
| 25 | CASP9 | P55211 | AlphaFold DB v6 | CASP9_P55211.pdb | **80.9** | 416 |
| 26 | ZPR1 | O75312 | AlphaFold DB v6 | ZPR1_O75312.pdb | **80.1** | 459 |

*ANK3 truncated to first 1000 of 4377 residues due to ESMfold size limit.

### Medium-confidence structures (pLDDT 60-79.9)

| # | Symbol | UniProt | Source | PDB File | pLDDT | Residues |
|---|--------|---------|--------|----------|-------|----------|
| 27 | MSTN | O14793 | AlphaFold DB v6 | MSTN_O14793.pdb | 78.8 | 375 |
| 28 | MUSK | O15146 | AlphaFold DB v6 | MUSK_O15146.pdb | 76.6 | 869 |
| 29 | TP53 | P04637 | existing | TP53_P04637.pdb | 75.8 | 393 |
| 30 | SPATA18 | Q8TC71 | AlphaFold DB v6 | SPATA18_Q8TC71.pdb | 75.5 | 538 |
| 31 | LRPN4 | Q6UXI1 | ESMfold NIM | LRPN4_Q6UXI1.pdb | 75.4 | 379 |
| 32 | GDNF | P39905 | AlphaFold DB v6 | GDNF_P39905.pdb | 75.3 | 211 |
| 33 | HTRA2 | O43464 | AlphaFold DB v6 | HTRA2_O43464.pdb | 74.8 | 458 |
| 34 | SULF1 | Q8IWU6 | AlphaFold DB v6 | SULF1_Q8IWU6.pdb | 74.3 | 871 |
| 35 | BCL2 | P10415 | AlphaFold DB v6 | BCL2_P10415.pdb | 74.2 | 239 |
| 36 | NEFL | P07196 | AlphaFold DB v6 | NEFL_P07196.pdb | 73.7 | 543 |
| 37 | BCL2L1 | Q07817 | AlphaFold DB v6 | BCL2L1_Q07817.pdb | 73.3 | 233 |
| 38 | DNMT3B | Q9UBC3 | AlphaFold DB v6 | DNMT3B_Q9UBC3.pdb | 73.2 | 853 |
| 39 | BDNF | P23560 | AlphaFold DB v6 | BDNF_P23560.pdb | 71.4 | 247 |
| 40 | RIPK1 | Q13546 | AlphaFold DB v6 | RIPK1_Q13546.pdb | 70.4 | 671 |
| 41 | AGRN | O00468 | AlphaFold DB v6 | AGRN_O00468.pdb | 69.8 | 2068 |
| 42 | NEDD4L | Q96PU5 | AlphaFold DB v6 | NEDD4L_Q96PU5.pdb | 69.8 | 975 |
| 43 | SMN1 | Q16637 | AlphaFold DB v6 | SMN1_Q16637.pdb | 67.4 | 294 |
| 44 | SMN2 | Q16637 | existing | SMN2_Q16637.pdb | 67.4 | 294 |
| 45 | ABI2 | Q9NYB9 | AlphaFold DB v6 | ABI2_Q9NYB9.pdb | 67.1 | 513 |
| 46 | TARDBP | Q13148 | AlphaFold DB v6 | TARDBP_Q13148.pdb | 66.5 | 414 |
| 47 | MDM2 | Q00987 | existing | MDM2_Q00987.pdb | 63.2 | 491 |
| 48 | MDM4 | O15151 | AlphaFold DB v6 | MDM4_O15151.pdb | 60.8 | 490 |

### Low-confidence structures (pLDDT < 60)

| # | Symbol | UniProt | Source | PDB File | pLDDT | Residues | Notes |
|---|--------|---------|--------|----------|-------|----------|-------|
| 49 | IGF1 | P05019 | AlphaFold DB v6 | IGF1_P05019.pdb | 59.7 | 195 | Signal peptide + propeptide regions poorly predicted |
| 50 | CAST | O15446 | AlphaFold DB v6 | CAST_O15446.pdb | 55.7 | 510 | Intrinsically disordered regions |
| 51 | FUS | P35637 | AlphaFold DB v6 | FUS_P35637.pdb | 55.0 | 526 | Large low-complexity / disordered regions |
| 52 | NEFH | P12036 | AlphaFold DB v6 | NEFH_P12036.pdb | 54.3 | 1020 | Long tail domain is intrinsically disordered |
| 53 | CD44 | P16070 | AlphaFold DB v6 | CD44_P16070.pdb | 53.3 | 742 | Mucin-like stem region poorly predicted |
| 54 | SETX | Q7Z333 | AlphaFold DB v6 | SETX_Q7Z333.pdb | 52.9 | 2677 | Very large; many disordered linkers |
| 55 | ROCK2 | O75116 | existing | ROCK2_2F2U.pdb | 47.5 | 769 | Experimental PDB (X-ray), B-factors not pLDDT |

---

## Druggability Ranking

Scoring criteria:
- **Structure quality:** pLDDT >= 80 (+3), 70-79 (+2), 60-69 (+1)
- **Protein size:** 100-800 residues (+2, ideal for small-molecule pockets), >800 (+1)
- **Known druggable target** with established binding pockets (+2)

| Rank | Symbol | pLDDT | Residues | Score | Rationale |
|------|--------|-------|----------|-------|-----------|
| **1** | **LDHA** | 96.1 | 332 | **7** | Excellent structure, known enzymatic pocket (NADH/pyruvate site), metabolic target |
| **2** | **MAPK14** (p38-alpha) | 89.9 | 360 | **7** | High-quality structure, ATP-binding pocket, multiple approved inhibitors exist |
| **3** | **LIMK1** | 87.6 | 249 | **7** | Well-defined kinase domain, known inhibitors (BMS-5, LIMKi3) |
| **4** | **CASP3** | 86.6 | 277 | **7** | High confidence, active site well-defined, caspase inhibitors exist |
| **5** | **SARM1** | 86.5 | 724 | **7** | NADase domain is highly druggable, recent drug discovery interest |
| **6** | **CASP9** | 80.9 | 416 | **7** | Good structure, known catalytic site, initiator caspase |
| **7** | TP53 | 75.8 | 393 | 6 | DNA-binding domain well-predicted; MDM2 interaction surface targetable |
| **8** | HTRA2 | 74.8 | 458 | 6 | Serine protease with defined pocket; mitochondrial target |
| **9** | BCL2 | 74.2 | 239 | 6 | BH3 groove is druggable (venetoclax-class); anti-apoptotic |
| **10** | BCL2L1 | 73.3 | 233 | 6 | Same BH3 groove as BCL2; navitoclax target |
| **11** | RIPK1 | 70.4 | 671 | 6 | Kinase domain druggable; necrostatin-1 is a known inhibitor |
| **12** | DNMT3B | 73.2 | 853 | 5 | SAM-binding pocket in methyltransferase domain |
| **13** | PFN1 | 95.7 | 140 | 5 | Excellent structure but small; actin-binding interface |
| **14** | ACTG1 | 95.4 | 375 | 5 | Excellent structure, ATP-binding cleft |
| **15** | ACTR2 | 94.0 | 394 | 5 | High quality; Arp2/3 complex component |

---

## Key Findings

### Best Structural Coverage (pLDDT >= 90)
Seven targets have near-experimental quality structures:
- **LDHA** (96.1), **PFN1** (95.7), **ACTG1** (95.4), **ACTR2** (94.0), **RAPSN** (93.3), **UBA1** (92.7), **CORO1C** (91.1)

### Intrinsically Disordered Proteins (pLDDT < 60)
These targets have significant disordered regions that cannot form well-defined 3D structures. Structure-based drug design is less applicable; consider alternative approaches (peptide mimetics, PROTACs, RNA-targeting):
- **FUS** (55.0) -- RNA-binding protein with prion-like domain
- **CAST** (55.7) -- Calpastatin, intrinsically disordered inhibitor
- **CD44** (53.3) -- Mucin-like stem region
- **SETX** (52.9) -- Very large (2677 res), many unstructured linkers
- **NEFH** (54.3) -- Neurofilament heavy chain, long disordered tail

### SMA-Core Targets
- **SMN1/SMN2** (pLDDT=67.4): Moderate confidence. The Tudor domain and oligomerization regions are better predicted than the N-terminal region.
- **PLS3** (pLDDT=89.0): High quality. Actin-bundling protein, potential modifier gene target.
- **NCALD** (pLDDT=86.9): Good quality calcium sensor. Known SMA modifier.
- **STMN2** (pLDDT=85.9): Stathmin-like domain well-predicted. Axonal maintenance.

### Actin Pathway Cluster (SMA-Relevant)
All actin pathway components have excellent structures:
- **ACTG1** (95.4), **PFN1** (95.7), **CFL2** (88.8), **CORO1C** (91.1), **PLS3** (89.0), **LIMK1** (87.6), **ACTR2** (94.0)

### Recommended for DiffDock Virtual Screening
Top candidates based on structure quality + druggability:
1. **LDHA** -- metabolic reprogramming in SMA motor neurons
2. **MAPK14** -- neuroinflammation target, existing drugs
3. **LIMK1** -- actin dynamics, ROCK2-LIMK1-CFL2 axis
4. **CASP3/CASP9** -- apoptosis cascade in motor neuron death
5. **SARM1** -- axon degeneration (NADase activity)
6. **BCL2/BCL2L1** -- anti-apoptotic, venetoclax analogs
7. **ROCK2** -- existing structure (2F2U), kinase domain druggable (note: pLDDT=47.5 because this is an X-ray structure with crystallographic B-factors, not AlphaFold pLDDT)

---

## Technical Notes

- **AlphaFold2 NIM** was attempted but returns 504 Gateway Timeout for all proteins (NVIDIA cloud endpoint overloaded on 2026-03-22). AlphaFold DB pre-computed structures were used instead.
- **ESMfold NIM** was used for 2 proteins not in AlphaFold DB (ANK3, LRPN4). ANK3 was truncated to 1000 residues (full length: 4377 aa).
- **ROCK2** uses experimental crystal structure (PDB: 2F2U), not AlphaFold. The low "pLDDT" is actually a crystallographic B-factor average, not a prediction confidence score.
- **SMN1 and SMN2** encode the same protein (Q16637) -- structures are identical.
- All structures are stored as PDB files in `/home/bryzant/sma-platform/data/pdb/` on moltbot.
- Full JSON results: `/home/bryzant/sma-platform/data/pdb/structure_prediction_results.json`
