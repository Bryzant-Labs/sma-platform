# GPU Compute Sprint — 2026-03-22

## Task 1: Pocket Detection on AlphaFold Structures

**Method**: BioPython PDB parser on all AlphaFold-predicted structures in `/data/pdb/`.
Identified high-confidence (pLDDT >= 85) ordered regions of >= 10 consecutive residues as potential binding pocket candidates.

**Results saved**: `data/pdb/pocket_analysis.json` on moltbot.

### Top 15 Druggable Targets (by largest ordered region)

| Rank | Target | pLDDT | Ordered Regions | Largest Region (aa) | Total Residues |
|------|--------|-------|----------------|---------------------|----------------|
| 1 | ACTG1 | 95.4 | 2 | 324 | 375 |
| 2 | CORO1C | 91.0 | 4 | 298 | 474 |
| 3 | SULF1 | 74.0 | 5 | 276 | 871 |
| 4 | GALNT6 | 88.7 | 8 | 223 | 622 |
| 5 | FST | 88.4 | 3 | 205 | 344 |
| 6 | SARM1 | 85.7 | 7 | 199 | 724 |
| 7 | ANK3 | 84.5 | 14 | 197 | 1000 |
| 8 | UBA1 | 92.4 | 9 | 196 | 1058 |
| 9 | ACTR2 | 93.9 | 4 | 180 | 394 |
| 10 | ABI2 | 65.8 | 2 | 151 | 513 |
| 11 | RAPSN | 93.2 | 6 | 141 | 412 |
| 12 | NEFL | 73.0 | 4 | 134 | 543 |
| 13 | CASP3 | 85.8 | 2 | 131 | 277 |
| 14 | LDHA | 96.2 | 4 | 130 | 332 |
| 15 | C1QA | 82.6 | 2 | 118 | 245 |

### Full Rankings (all 55 targets)

| Target | pLDDT | Regions | Largest (aa) | Residues |
|--------|-------|---------|-------------|----------|
| ACTG1 | 95.4 | 2 | 324 | 375 |
| CORO1C | 91.0 | 4 | 298 | 474 |
| SULF1 | 74.0 | 5 | 276 | 871 |
| GALNT6 | 88.7 | 8 | 223 | 622 |
| FST | 88.4 | 3 | 205 | 344 |
| SARM1 | 85.7 | 7 | 199 | 724 |
| ANK3 | 84.5 | 14 | 197 | 1000 |
| UBA1 | 92.4 | 9 | 196 | 1058 |
| ACTR2 | 93.9 | 4 | 180 | 394 |
| ABI2 | 65.8 | 2 | 151 | 513 |
| RAPSN | 93.2 | 6 | 141 | 412 |
| NEFL | 73.0 | 4 | 134 | 543 |
| CASP3 | 85.8 | 2 | 131 | 277 |
| LDHA | 96.2 | 4 | 130 | 332 |
| C1QA | 82.6 | 2 | 118 | 245 |
| ROCK2 | 76.4 | 8 | 118 | 1388 |
| CTNNA1 | 82.9 | 17 | 116 | 906 |
| PLS3 | 88.8 | 8 | 106 | 630 |
| RIPK1 | 69.7 | 10 | 104 | 671 |
| TP53 | 75.1 | 3 | 103 | 393 |
| MAPK14 | 89.8 | 5 | 97 | 360 |
| STMN2 | 85.6 | 2 | 96 | 179 |
| PFN1 | 95.6 | 2 | 90 | 140 |
| DNMT3B | 72.5 | 14 | 89 | 853 |
| CASP9 | 80.3 | 8 | 88 | 416 |
| CD44 | 53.2 | 3 | 88 | 742 |
| CHRNA1 | 84.0 | 6 | 88 | 457 |
| HTRA2 | 74.5 | 7 | 84 | 458 |
| MDM2 | 62.6 | 4 | 82 | 491 |
| BCL2L1 | 72.5 | 3 | 78 | 233 |
| CFL2 | 88.5 | 4 | 75 | 166 |
| CNTF | 85.1 | 3 | 71 | 200 |
| MUSK | 76.5 | 16 | 71 | 869 |
| MDM4 | 60.1 | 5 | 69 | 490 |
| LIMK1 | 87.5 | 5 | 68 | 249 |
| SPATA18 | 75.4 | 7 | 68 | 538 |
| BCL2 | 72.0 | 4 | 62 | 239 |
| TMEM41B | 82.2 | 5 | 62 | 291 |
| NEDD4L | 68.4 | 13 | 58 | 975 |
| LY96 | 87.7 | 5 | 56 | 160 |
| CAST | 55.9 | 4 | 55 | 510 |
| NEFH | 53.5 | 5 | 54 | 1020 |
| SMN1 | 66.9 | 3 | 54 | 294 |
| SMN2 | 66.9 | 3 | 54 | 294 |
| BDNF | 71.0 | 4 | 50 | 247 |
| SETX | 52.3 | 25 | 46 | 2677 |
| NCALD | 86.3 | 4 | 44 | 193 |
| ZPR1 | 79.5 | 9 | 41 | 459 |
| MSTN | 78.8 | 8 | 38 | 375 |
| GDNF | 75.0 | 3 | 36 | 211 |
| AGRN | 68.8 | 20 | 31 | 2068 |
| LRPN4 | 78.7 | 3 | 30 | 379 |
| FUS | 53.6 | 3 | 25 | 526 |
| TARDBP | 65.2 | 2 | 21 | 414 |
| IGF1 | 59.5 | 0 | 0 | 195 |

### Key Observations

- **ACTG1** (gamma-actin) has the largest single ordered region (324 aa / 86% of protein) — extremely well-folded, high confidence. Central to the actin pathway disruption in SMA.
- **CORO1C** has 298 aa ordered region — our novel double-hit model target. Highly druggable structure.
- **SARM1** (NADase, axon protection) has 7 ordered regions with largest at 199 aa — good pocket diversity for drug design.
- **UBA1** shows 9 ordered regions (largest 196 aa) — multiple potential binding sites.
- **SMN1/SMN2** only have 54 aa ordered regions out of 294 total — largely disordered, confirming why direct SMN targeting is difficult.
- **IGF1** has ZERO ordered regions — entirely disordered at this confidence threshold, not directly druggable by small molecules.

---

## Task 2: MolMIM Molecule Generation

Generated 20 molecules per target using NVIDIA MolMIM (CMA-ES algorithm, QED optimization, 10 iterations).

### SARM1 — NADase Inhibitor Scaffold

Seed SMILES: `O=c1[nH]c(=O)c2ccccc21` (isatin-like scaffold)

| # | SMILES | QED Score |
|---|--------|-----------|
| 1 | `O=c1ccc(O[C@@H]2CN(c3ccccc3)C[C@H]2F)c[nH]1` | 0.931 |
| 2 | `C[C@@H]1CN(c2ccc(C(=O)O)cc2)C[C@H]1Sc1ccccc1` | 0.926 |
| 3 | `C[C@@H](c1ccccc1)N1CCN(C(=O)CCCC(=O)O)CC1` | 0.875 |
| 4 | `C[C@@H]1CN(C(=O)c2cc(=O)[nH][nH]2)C[C@H]1c1ccccc1` | 0.870 |
| 5 | `C[C@@H](Oc1cc[nH]c(=O)c1)c1ccccc1` | 0.854 |
| 6 | `O=c1cc(N2CC[C@H](c3ccccc3)C2)[nH]c(=O)[nH]1` | 0.845 |
| 7 | `COC(=O)c1cc(NC(=O)N2CC[C@@H](c3ccccc3)[C@H](C)C2)c[nH]1` | 0.840 |
| 8 | `O=C1O[C@@H](c2ccccc2)CN1c1cc(F)cc(F)c1` | 0.837 |

**Best hit**: QED 0.931 — fluorinated pyrrolidine with pyridinone. Drug-like, chiral centers suggest good selectivity potential.

### ROCK2 — Kinase Inhibitor Scaffold

Seed SMILES: `c1ccc2c(c1)[nH]c(=O)c(=O)[nH]2` (quinoxalinedione)

| # | SMILES | QED Score |
|---|--------|-----------|
| 1 | `N#Cc1ccc2[nH]c(=O)c(C(F)(F)F)cc2c1` | 0.766 |
| 2 | `O=c1[nH]c2ccccc2cc1CBr` | 0.760 |
| 3 | `C[S@@](=O)CCNC(=O)NCc1cc2ccccc2[nH]c1=O` | 0.759 |
| 4 | `O=c1[nH]c2ccccc2[nH]c1=Nc1ccc(F)cc1` | 0.688 |
| 5 | `CCN=c1[nH]c2ccccc2[nH]c1=O` | 0.684 |

**Note**: Lower QED diversity — many molecules collapsed to the seed scaffold. The quinoxalinedione core is quite rigid. Future runs should use different seed scaffolds (e.g., fasudil-derived).

### LIMK1 — Quinazoline Scaffold

Seed SMILES: `c1ccc(-c2cnc3ccccc3n2)cc1` (2-phenylquinazoline)

| # | SMILES | QED Score |
|---|--------|-----------|
| 1 | `O=C(O)c1cc(F)c(-c2ccccn2)cc1F` | 0.870 |
| 2 | `O=C(O)[C@]1(c2ccc(Cl)cc2)C[C@@H]1F` | 0.821 |
| 3 | `O=C(O)c1csc(-c2ncccc2O)c1` | 0.815 |
| 4 | `O=C(O)c1ccc(-c2ccccc2)nc1` | 0.808 |
| 5 | `O=C(O)c1cnc(-c2ccccc2)nc1` | 0.803 |
| 6 | `O=C(O)c1ccc(-c2ccccn2)nc1` | 0.803 |
| 7 | `O=C(O)c1ccc(-c2ncc3ccccc3n2)cc1` | 0.759 |
| 8 | `CC(=O)c1ccc(C(=O)c2ccccn2)cc1` | 0.754 |

**Best hit**: QED 0.870 — difluorophenyl-pyridine carboxylic acid. Good drug-likeness, pyridine nitrogen provides H-bond acceptor for kinase hinge binding.

### Summary: Total Molecules Generated

| Target | Seed Scaffold | Molecules | Best QED | Unique (non-empty) |
|--------|---------------|-----------|----------|---------------------|
| SARM1 | Isatin-like | 20 | 0.931 | 19 |
| ROCK2 | Quinoxalinedione | 20 | 0.766 | 19 |
| LIMK1 | 2-Phenylquinazoline | 20 | 0.870 | 19 |
| **Total** | | **60** | | **57** |

---

## Task 3: DiffDock NIM Status

**Status: OFFLINE (HTTP 404)**

The DiffDock NIM endpoint (`https://health.api.nvidia.com/v1/biology/mit/diffdock/generate`) returned `404 page not found`. This is consistent with previous observations — the endpoint has been deprecated in favor of DiffDock v2.2 on BioNeMo.

**Docking of MAPK14 champion was NOT performed** (DiffDock unavailable).

### Alternatives for Docking
1. **NVIDIA BioNeMo DiffDock v2.2** — check if new endpoint is available
2. **Local AutoDock Vina** — can run on moltbot CPU (slower but reliable)
3. **Vast.ai GPU instance** — spin up for batch docking

---

## Next Steps

1. **Prioritize pocket candidates**: Cross-reference pocket analysis with SMA relevance scores to identify the best drug discovery targets
2. **Dock MolMIM molecules**: Once DiffDock is back or using AutoDock Vina, dock the top QED molecules against their respective targets
3. **SARM1 deep dive**: The QED 0.931 hit warrants further characterization — check for PAINS alerts, synthetic accessibility
4. **ROCK2 scaffold hopping**: Use fasudil as seed instead of quinoxalinedione for better diversity
5. **ACTG1/CORO1C structures**: These have the largest ordered regions — investigate allosteric pocket sites
