# ADMET Predictions: Top LIMK2/ROCK Drug Candidates

**Date**: 2026-03-24
**Method**: RDKit descriptors + SMA Platform `admet_predictor.py` (rule-based ADMET)
**Context**: ROCK-LIMK2-Cofilin therapeutic axis for SMA motor neuron protection

---

## Executive Summary

10 compounds evaluated: 5 literature/tool compounds + 5 AI-generated (GenMol) molecules. The GenMol-derived compounds and Fasudil emerge as the strongest drug candidates, while CHEMBL305177 and BMS-5 should be deprioritized due to serious ADMET liabilities.

**Top 3 to advance**: GenMol-L3/L4/L5 (CNS-MPO 4.85, QED 0.95, BBB+, no flags)
**Promising with caveats**: H-1152 (hERG borderline), Fasudil (approved drug, proven safe)
**Deprioritize**: CHEMBL305177 (no BBB, hERG+), BMS-5 (no BBB, hERG+, hepatotox+)

---

## Full ADMET Table

### Physicochemical Properties

| Compound | MW | LogP | TPSA | HBD | HBA | RotBonds | Aromatic Rings | QED |
|---|---|---|---|---|---|---|---|---|
| **H-1152** | 300.3 | 3.58 | 33.2 | 0 | 2 | 2 | 1 | 0.836 |
| **CHEMBL305177** | 438.4 | 1.45 | 193.6 | 6 | 8 | 9 | 3 | 0.285 |
| **Fasudil** | 291.4 | 1.22 | 62.3 | 1 | 4 | 2 | 2 | 0.904 |
| **Y-27632** | 247.3 | 2.17 | 68.0 | 2 | 3 | 3 | 1 | 0.860 |
| **BMS-5** | 424.5 | 4.13 | 104.0 | 3 | 4 | 5 | 4 | 0.448 |
| **GenMol-L1** | 307.4 | 2.85 | 63.2 | 1 | 3 | 3 | 2 | 0.948 |
| **GenMol-L2** | 307.4 | 2.85 | 63.2 | 1 | 3 | 3 | 2 | 0.948 |
| **GenMol-L3** | 298.3 | 2.71 | 59.1 | 1 | 3 | 3 | 2 | 0.948 |
| **GenMol-L4** | 298.3 | 2.71 | 59.1 | 1 | 3 | 3 | 2 | 0.948 |
| **GenMol-L5** | 298.3 | 2.71 | 59.1 | 1 | 3 | 3 | 2 | 0.948 |
| *CNS drug avg* | *305* | *2.5* | *65* | *1* | *4* | *--* | *--* | *>0.5* |

### Lipinski Rule of 5

| Compound | MW<500 | LogP<5 | HBD<=5 | HBA<=10 | Violations | Pass |
|---|---|---|---|---|---|---|
| H-1152 | YES | YES | YES | YES | 0 | YES |
| CHEMBL305177 | YES | YES | **NO (6)** | YES | 1 | NO |
| Fasudil | YES | YES | YES | YES | 0 | YES |
| Y-27632 | YES | YES | YES | YES | 0 | YES |
| BMS-5 | YES | YES | YES | YES | 0 | YES |
| GenMol-L1 | YES | YES | YES | YES | 0 | YES |
| GenMol-L2 | YES | YES | YES | YES | 0 | YES |
| GenMol-L3 | YES | YES | YES | YES | 0 | YES |
| GenMol-L4 | YES | YES | YES | YES | 0 | YES |
| GenMol-L5 | YES | YES | YES | YES | 0 | YES |

### BBB Permeability & CNS Drug-likeness

Criteria: MW < 450, TPSA < 90, HBD <= 3, LogP 1-4

| Compound | BBB Permeable | CNS-MPO (0-6) | CNS-MPO Verdict |
|---|---|---|---|
| H-1152 | YES | 4.67 | GOOD (>=4) |
| CHEMBL305177 | **NO** (TPSA=194, HBD=6) | 2.44 | POOR (<3) |
| Fasudil | YES | 4.39 | GOOD |
| Y-27632 | YES | 3.85 | ACCEPTABLE (3-4) |
| BMS-5 | **NO** (TPSA=104, LogP=4.1) | 1.14 | POOR |
| GenMol-L1 | YES | 4.69 | GOOD |
| GenMol-L2 | YES | 4.69 | GOOD |
| GenMol-L3 | YES | **4.85** | EXCELLENT |
| GenMol-L4 | YES | **4.85** | EXCELLENT |
| GenMol-L5 | YES | **4.85** | EXCELLENT |

### Safety & Toxicity

| Compound | hERG Risk | Ames Risk | Hepatotox Risk | PAINS | Brenk Alerts | Flags |
|---|---|---|---|---|---|---|
| H-1152 | MODERATE (0.60) | LOW | LOW | None | None | hERG borderline |
| CHEMBL305177 | **HIGH (0.70)** | MODERATE | MODERATE | None | None | hERG_liability |
| Fasudil | MODERATE (0.50) | LOW | LOW | None | None | -- |
| Y-27632 | LOW (0.30) | LOW | LOW | None | None | -- |
| BMS-5 | **HIGH (1.00)** | MODERATE | **HIGH** | None | None | hERG_liability, hepatotoxicity_risk |
| GenMol-L1 | MODERATE (0.50) | LOW | LOW | None | None | -- |
| GenMol-L2 | MODERATE (0.50) | LOW | LOW | None | None | -- |
| GenMol-L3 | MODERATE (0.50) | LOW | LOW | None | None | -- |
| GenMol-L4 | MODERATE (0.50) | LOW | LOW | None | None | -- |
| GenMol-L5 | MODERATE (0.50) | LOW | LOW | None | None | -- |

### Metabolism & Pharmacokinetics

| Compound | CYP Risk | CYP Motifs | PPB Est. | Soft Spots | Clearance | Half-life |
|---|---|---|---|---|---|---|
| H-1152 | MODERATE | CYP3A4, CYP2D6 | 0.86 | 0 | Low (hepatic) | Medium |
| CHEMBL305177 | **HIGH** | CYP2D6, CYP2C9 | 0.65 | 4 | Moderate | Medium |
| Fasudil | LOW | CYP2D6 | 0.62 | 1 | Moderate | Short |
| Y-27632 | LOW | CYP2D6 | 0.72 | 3 | Moderate | Medium |
| BMS-5 | **HIGH** | CYP3A4, CYP2D6 | **0.91** | 2 | Low (hepatic) | Long |
| GenMol-L1 | LOW | CYP2D6 | 0.79 | 1 | Moderate | Medium |
| GenMol-L2 | LOW | CYP2D6 | 0.79 | 1 | Moderate | Medium |
| GenMol-L3 | LOW | CYP2D6 | 0.77 | 1 | Moderate | Medium |
| GenMol-L4 | LOW | CYP2D6 | 0.77 | 1 | Moderate | Medium |
| GenMol-L5 | LOW | CYP2D6 | 0.77 | 1 | Moderate | Medium |

---

## Traffic Light Summary

| Compound | Category | Overall ADMET Score | Lipinski | BBB | CNS-MPO | hERG | Ames | Hepatotox | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **GenMol-L3** | AI-generated | 0.716 | GREEN | GREEN | GREEN | AMBER | GREEN | GREEN | **ADVANCE** |
| **GenMol-L4** | AI-generated | 0.716 | GREEN | GREEN | GREEN | AMBER | GREEN | GREEN | **ADVANCE** |
| **GenMol-L5** | AI-generated | 0.716 | GREEN | GREEN | GREEN | AMBER | GREEN | GREEN | **ADVANCE** |
| **GenMol-L1** | AI-generated | 0.736 | GREEN | GREEN | GREEN | AMBER | GREEN | GREEN | **ADVANCE** |
| **GenMol-L2** | AI-generated | 0.736 | GREEN | GREEN | GREEN | AMBER | GREEN | GREEN | **ADVANCE** |
| **Y-27632** | ROCK tool | 0.702 | GREEN | GREEN | GREEN | GREEN | GREEN | GREEN | **ADVANCE** (tool compound) |
| **H-1152** | ROCK/LIMK | 0.674 | GREEN | GREEN | GREEN | AMBER | GREEN | GREEN | **ADVANCE with monitoring** |
| **Fasudil** | ROCK (approved) | 0.665 | GREEN | GREEN | GREEN | AMBER | GREEN | GREEN | **ADVANCE** (clinical precedent) |
| **CHEMBL305177** | Diaminopteridine | 0.308 | AMBER | RED | RED | RED | AMBER | AMBER | **DEPRIORITIZE** |
| **BMS-5** | LIMK inhibitor | 0.270 | GREEN | RED | RED | RED | AMBER | RED | **DEPRIORITIZE** |

---

## Comparison with Approved CNS Drugs

| Property | CNS Drug Mean | GenMol-L3/L4/L5 | H-1152 | Fasudil | CHEMBL305177 | BMS-5 |
|---|---|---|---|---|---|---|
| MW | 305 | 298 | 300 | 291 | 438 (high) | 425 (high) |
| LogP | 2.5 | 2.71 | 3.58 (high) | 1.22 (low) | 1.45 | 4.13 (high) |
| TPSA | 65 | 59 | 33 (low) | 62 | 194 (very high) | 104 (high) |
| HBD | 1 | 1 | 0 | 1 | 6 (very high) | 3 |

The GenMol series matches approved CNS drug profiles almost exactly. H-1152 has slightly high LogP and low TPSA (possible non-specific binding). Fasudil is already approved and proven BBB-penetrant.

---

## Recommendations

### Tier 1 -- Advance to DiffDock Validation
1. **GenMol-L3/L4/L5** (pyridine-sulfonamide scaffold, QED=0.948, CNS-MPO=4.85): Best overall ADMET profile of all candidates. MW and LogP in the sweet spot for CNS. No PAINS, no Brenk alerts, no toxicity flags. Three positional isomers -- test all three in DiffDock against LIMK2 kinase domain.
2. **GenMol-L1/L2** (acetanilide-methylsulfonyl scaffold, QED=0.948, CNS-MPO=4.69): Slightly higher TPSA than L3-L5 but still excellent. Verify binding mode vs BMS-5 parent.

### Tier 2 -- Advance with Caveats
3. **Fasudil** (ADMET=0.665, CNS-MPO=4.39): Already approved in Japan/China for cerebral vasospasm. Known BBB penetrant. Short half-life may require frequent dosing but safety is established. **Best candidate for repurposing.**
4. **H-1152** (ADMET=0.674, CNS-MPO=4.67): Best DiffDock score (+0.90 vs LIMK2). Borderline hERG (0.60) needs experimental hERG patch-clamp validation. Zero HBD is unusual -- check solubility.
5. **Y-27632** (ADMET=0.702): Cleanest safety profile (hERG LOW), but it is primarily a tool compound, not developed for clinical use.

### Tier 3 -- Deprioritize
6. **CHEMBL305177** (ADMET=0.308): Despite pChEMBL=11.0 potency, this is essentially a folate analog (diaminopteridine + glutamate). TPSA=194 means zero BBB penetration. 6 HBDs and 9 rotatable bonds. High hERG risk. Not viable as a CNS drug without major scaffold redesign.
7. **BMS-5** (ADMET=0.270): The parent LIMK inhibitor has the worst ADMET profile in this set -- hERG=1.0, hepatotox=HIGH, no BBB, PPB=0.91, CYP=HIGH. However, the GenMol derivatives of BMS-5 (GenMol-L1-L5) have dramatically improved profiles, validating the AI-driven optimization approach.

---

## Platform API Endpoint

The SMA platform has an existing ADMET API:
- **POST** `/api/v2/screen/admet` -- Single compound ADMET prediction (accepts `{"smiles": "..."}`)
- **GET** `/api/v2/screen/admet/batch` -- Batch ADMET for all ChEMBL compounds (admin key required)
- **GET** `/api/v2/admet/summary` -- Aggregate ADMET statistics
- **GET** `/api/v2/admet/compounds` -- Filter compounds by ADMET properties
- **GET** `/api/v2/admet/top` -- Top N compounds by QED, CNS-MPO, etc.

Results from this analysis can be POSTed individually via `/api/v2/screen/admet` or integrated into the batch pipeline via `data/admet_predictions.json`.

---

## SMILES Reference

| Compound | SMILES |
|---|---|
| H-1152 | `CC(C)C(=O)N1CCC(C(F)(F)F)CC1c1ccncc1` |
| CHEMBL305177 | `Nc1nc(N)c2cc(CNc3ccc(C(=O)NC(CCC(=O)O)C(=O)O)cc3)ccc2n1` |
| Fasudil | `O=S(=O)(c1cccc2cnccc12)N1CCCNCC1` |
| Y-27632 | `CC(N)C1CCC(C(=O)Nc2ccncc2)CC1` |
| BMS-5 | `CC(=O)Nc1ccc(-c2nc3cc(NS(=O)(=O)c4ccc(F)cc4)ccc3[nH]2)cc1` |
| GenMol-L1 | `CC(=O)Nc1ccc(-c2ccc(S(C)(=O)=O)cc2)c(F)c1` |
| GenMol-L2 | `CC(=O)Nc1ccc(-c2ccc(S(C)(=O)=O)cc2)cc1F` |
| GenMol-L3 | `Cc1cc(-c2ccc(NS(C)(=O)=O)cn2)c(F)cc1F` |
| GenMol-L4 | `Cc1cc(F)c(-c2ccc(NS(C)(=O)=O)cn2)cc1F` |
| GenMol-L5 | `Cc1cc(F)c(-c2ccc(NS(C)(=O)=O)nc2)cc1F` |

---

## Methodology Notes

- **Lipinski**: Standard Rule of 5 (MW<500, LogP<5, HBD<=5, HBA<=10)
- **BBB**: Clark's rules (MW<450, TPSA<90, HBD<=3, LogP 1-4)
- **CNS-MPO**: Wager et al. 2010 six-parameter model (CLogP, CLogD, MW, TPSA, HBD, pKa), score 0-6, >=4 is CNS-favorable
- **QED**: Bickerton et al. 2012 quantitative estimate of drug-likeness
- **PAINS**: RDKit FilterCatalog (Baell & Holloway 2010)
- **Brenk**: RDKit FilterCatalog (Brenk et al. 2008 structural alerts)
- **hERG**: Rule-based (LogP, basic nitrogen, MW, aromatic rings) -- Aronov 2005
- **Ames**: Structural alert-based (nitro groups, aromatic amines) -- Hansen et al. 2009
- **CYP**: Motif-based substrate prediction (CYP3A4: large lipophilic; CYP2D6: basic N + aromatic; CYP2C9: acidic + lipophilic)
- **PPB**: LogP-dependent estimate (ppb = 0.5 + LogP*0.1)

**Limitation**: All predictions are rule-based/descriptor-based. Experimental validation (hERG patch-clamp, Caco-2 assay, microsomal stability) is required before advancing any compound.
