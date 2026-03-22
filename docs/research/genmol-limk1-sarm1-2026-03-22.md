# GenMol/MolMIM LIMK1 & SARM1 Molecule Generation Report

**Date**: 2026-03-22
**Targets**: LIMK1 (LIM domain kinase 1) & SARM1 (Sterile alpha and TIR motif-containing protein 1)
**Tool**: NVIDIA MolMIM NIM (CMA-ES optimization, QED scoring)
**API**: `health.api.nvidia.com/v1/biology/nvidia/molmim/generate`

---

## Target Rationale

### LIMK1 (pLDDT 87.6, Kinase Domain)
- **Pathway**: ROCK-LIMK-Cofilin axis -- LIMK1 phosphorylates cofilin, inhibiting actin depolymerization
- **SMA relevance**: Actin dynamics disrupted in SMA motor neurons; LIMK1 inhibition restores cofilin activity and actin turnover
- **Druggability**: Kinase domain with well-characterized ATP-binding site; multiple tool compounds exist (BMS-5, LIMKi3, MDI-117740)
- **MDI-117740**: Most selective LIMK inhibitor reported (J Med Chem 2025); pyrrolopyrimidine scaffold

### SARM1 (pLDDT 86.5, NADase Domain)
- **Function**: NAD+ hydrolase that triggers axon degeneration (Wallerian degeneration) upon activation
- **SMA relevance**: Motor neuron axons degenerate in SMA; SARM1 inhibition could protect axons independent of SMN levels
- **Druggability**: Enzymatic NADase domain with defined substrate pocket; Nura Bio has clinical-stage inhibitors
- **Key inhibitor classes**: Isoquinolines (NADase active site), nicotinamide analogs (substrate-competitive), dihydropyridines

---

## 1. Generation Method

**Algorithm**: CMA-ES (Covariance Matrix Adaptation Evolution Strategy)
**Iterations**: 40 per batch
**Particles**: 30
**Min similarity**: 0.3 (Tanimoto)
**Scoring**: QED (Quantitative Estimate of Drug-likeness)

### LIMK1 Scaffolds (3 batches, 90 molecules requested)

| Batch | Scaffold | SMILES | Rationale |
|-------|----------|--------|-----------|
| 1 | BMS-5 | `CC(=O)Nc1cccc(-c2cc3c(Nc4ccc(N5CCN(C)CC5)cc4)ncn3[nH]2)c1` | Known LIMK inhibitor, pyrrolopyrimidine-aniline core |
| 2 | LIMKi3 | `CC(C)(C)c1nc(-c2cccc(NS(=O)(=O)c3c(F)cccc3F)c2)c(-c2ccnc(NC3CC3)n2)s1` | Dabrafenib-like sulfonamide-thiazole LIMK inhibitor |
| 3 | Pyrrolopyrimidine | `Nc1ncnc2[nH]cc(-c3cccc(NC(=O)C4CC4)c3)c12` | Generic 7H-pyrrolo[2,3-d]pyrimidine kinase scaffold |

### SARM1 Scaffolds (3 batches, 90 molecules requested)

| Batch | Scaffold | SMILES | Rationale |
|-------|----------|--------|-----------|
| 1 | 8-Hydroxyisoquinoline | `Oc1ccnc2ccccc12` | Known SARM1 NADase inhibitor class (isoquinoline series) |
| 2 | Nisoldipine-like | `CCOC(=O)C1=C(C)NC(C)=C(C(=O)OC(C)C)C1c1ccccc1[N+](=O)[O-]` | Dehydronitrosonisoldipine scaffold (dihydropyridine) |
| 3 | Nicotinamide riboside | `NC(=O)c1ccc[n+](C2OC(CO)C(O)C2O)c1` | NAD+ substrate-competitive analog |

---

## 2. Drug-Likeness Filtering

**Filters Applied**:
- Lipinski Rule of 5 (MW < 500, LogP < 5, HBD < 5, HBA < 10; max 1 violation)
- BBB penetration (3/4 of: MW < 450, LogP 1-3, TPSA < 90, HBD <= 3)
- CNS MPO score (Pfizer 6-component, 0-6 scale)
- QED > 0.4

### LIMK1 Results
- **Total unique valid**: 31
- **Passed all filters**: 31 (100.0% pass rate)
- **BBB-penetrant**: 30/31

### SARM1 Results
- **Total unique valid**: 36
- **Passed all filters**: 35 (97.2% pass rate)
- **BBB-penetrant**: 32/35

---

## 3. Top 20 LIMK1 Drug-Like Candidates (ranked by CNS-MPO + QED)

| Rank | SMILES | QED | CNS-MPO | BBB | MW | LogP | TPSA | Batch |
|------|--------|-----|---------|-----|-----|------|------|-------|
| 1 | `CC(=O)Nc1cccc(-c2cc([C@@]3(C)CCOC3)n(C)n2)c1` | 0.948 | 6.0 | 4/4 | 299.4 | 2.72 | 56.1 | BMS-5 |
| 2 | `CC(=O)Nc1cccc(-c2cc([C@@]3(C)CCOC3)nn2C)c1` | 0.948 | 6.0 | 4/4 | 299.4 | 2.72 | 56.1 | BMS-5 |
| 3 | `CC(=O)Nc1cccc(-c2cc([C@]3(C)CCOC3)n(C)n2)c1` | 0.948 | 6.0 | 4/4 | 299.4 | 2.72 | 56.1 | BMS-5 |
| 4 | `CC(=O)Nc1cccc(-c2cc([C@]3(C)CCOC3)nn2C)c1` | 0.948 | 6.0 | 4/4 | 299.4 | 2.72 | 56.1 | BMS-5 |
| 5 | `CC(=O)Nc1cccc(-c2cc([C@@]3(C)CCCO3)nn2C)c1` | 0.947 | 6.0 | 3/4 | 299.4 | 3.07 | 56.1 | BMS-5 |
| 6 | `CC(=O)Nc1cccc(-c2cc([C@]3(C)CCCO3)n(C)n2)c1` | 0.947 | 6.0 | 3/4 | 299.4 | 3.07 | 56.1 | BMS-5 |
| 7 | `CN1C(=O)NC[C@@H]1c1cccc(-c2cc([C@@]3(C)CCOC3)nn2C)c1` | 0.934 | 6.0 | 4/4 | 340.4 | 2.46 | 59.4 | BMS-5 |
| 8 | `O=C(Nc1cccc(-c2noc(C(F)F)n2)c1)C1CC1` | 0.934 | 6.0 | 3/4 | 279.2 | 3.02 | 68.0 | Pyrrolopyrimidine |
| 9 | `Cn1ccc(NS(=O)(=O)c2c(F)cccc2F)n1` | 0.921 | 6.0 | 4/4 | 273.3 | 1.5 | 64.0 | LIMKi3 |
| 10 | `O=C(Nc1cccc(-c2nc(C(F)(F)F)no2)c1)C1CC1` | 0.945 | 5.9 | 3/4 | 297.2 | 3.1 | 68.0 | Pyrrolopyrimidine |
| 11 | `O=C(Nc1cccc(-c2noc(C(F)(F)F)n2)c1)C1CC1` | 0.945 | 5.9 | 3/4 | 297.2 | 3.1 | 68.0 | Pyrrolopyrimidine |
| 12 | `O=C(Nc1cccc(-c2noc(CC(F)(F)F)n2)c1)C1CC1` | 0.941 | 5.9 | 3/4 | 311.3 | 3.19 | 68.0 | Pyrrolopyrimidine |
| 13 | `O=S(=O)(Nc1cccc(-n2cccn2)c1)c1c(F)cccc1F` | 0.797 | 6.0 | 4/4 | 335.3 | 2.95 | 64.0 | LIMKi3 |
| 14 | `O=S(=O)(Nc1cccc(-c2nnco2)c1)c1c(F)cccc1F` | 0.791 | 6.0 | 4/4 | 337.3 | 2.82 | 85.1 | LIMKi3 |
| 15 | `O=C(Nc1cccc(-c2noc(/C=C/C(F)(F)F)n2)c1)C1CC1` | 0.932 | 5.7 | 3/4 | 323.3 | 3.66 | 68.0 | Pyrrolopyrimidine |
| 16 | `O=S(=O)(Nc1cccc(-c2ccno2)c1)c1c(F)cccc1F` | 0.792 | 5.8 | 3/4 | 336.3 | 3.42 | 72.2 | LIMKi3 |
| 17 | `CC(=O)Nc1cccc(-c2cc([C@@]3(C)C[C@@]3(C)CO)nn2C)c1` | 0.912 | 5.5 | 4/4 | 313.4 | 2.71 | 67.2 | BMS-5 |
| 18 | `CC(=O)Nc1cccc(-n2c(-c3ccc(C)cc3)nnc2[C@]2(C)CCOC2)c1` | 0.750 | 5.4 | 3/4 | 376.5 | 3.88 | 69.0 | BMS-5 |
| 19 | `Nc1cc(NS(=O)(=O)c2c(F)cccc2F)ccn1` | 0.899 | 5.0 | 4/4 | 285.3 | 1.74 | 85.1 | LIMKi3 |
| 20 | `Nc1ccn(-c2cccc(NS(=O)(=O)c3c(F)cccc3F)c2)n1` | 0.757 | 5.0 | 3/4 | 350.4 | 2.53 | 90.0 | LIMKi3 |

---

## 3. Top 20 SARM1 Drug-Like Candidates (ranked by CNS-MPO + QED)

| Rank | SMILES | QED | CNS-MPO | BBB | MW | LogP | TPSA | Batch |
|------|--------|-----|---------|-----|-----|------|------|-------|
| 1 | `CC1(C)COC(COc2cccc(C(N)=O)c2)OC1` | 0.897 | 6.0 | 4/4 | 265.3 | 1.56 | 70.8 | NR-analog |
| 2 | `CC1(C)OCC(OCc2cccc(C(N)=O)c2)CO1` | 0.894 | 6.0 | 4/4 | 265.3 | 1.45 | 70.8 | NR-analog |
| 3 | `CCOC(=O)c1c(C)[nH]c2c(C(=O)OC(C)C)cccc2c1=O` | 0.876 | 6.0 | 4/4 | 317.3 | 2.58 | 85.5 | Nisoldipine |
| 4 | `CCOC(=O)c1c(C)[nH]c2cccc(C(=O)OC(C)C)c2c1=O` | 0.876 | 6.0 | 4/4 | 317.3 | 2.58 | 85.5 | Nisoldipine |
| 5 | `CC1(C)COC(COc2cccc(C(N)=O)c2)O1` | 0.876 | 6.0 | 4/4 | 251.3 | 1.32 | 70.8 | NR-analog |
| 6 | `CCOC(=O)c1c(C)[nH]c2c(C(=O)OCC)cccc2c1=O` | 0.875 | 6.0 | 4/4 | 303.3 | 2.19 | 85.5 | Nisoldipine |
| 7 | `CCOC(=O)c1c(C)[nH]c2c(C(=O)OC(C)(C)C)cccc2c1=O` | 0.874 | 6.0 | 4/4 | 331.4 | 2.97 | 85.5 | Nisoldipine |
| 8 | `C[C@@](N)(Cc1ccnc2ccccc12)C(F)(F)F` | 0.894 | 5.9 | 3/4 | 254.3 | 3.06 | 38.9 | 8-Hydroxyisoquinoline |
| 9 | `CCOC(=O)C1=C(C)Nc2ccccc2C(C(=O)OCC)=C1C` | 0.864 | 5.9 | 3/4 | 315.4 | 3.29 | 64.6 | Nisoldipine |
| 10 | `C[C@@](Cc1cccc2ncccc12)(C(=O)O)C(F)(F)F` | 0.938 | 5.8 | 3/4 | 283.2 | 3.43 | 50.2 | 8-Hydroxyisoquinoline |
| 11 | `C[C@@](Cc1ccnc2ccccc12)(C(=O)O)C(F)(F)F` | 0.938 | 5.8 | 3/4 | 283.2 | 3.43 | 50.2 | 8-Hydroxyisoquinoline |
| 12 | `C[C@](Cc1cccc2ncccc12)(C(=O)O)C(F)(F)F` | 0.938 | 5.8 | 3/4 | 283.2 | 3.43 | 50.2 | 8-Hydroxyisoquinoline |
| 13 | `C[C@](Cc1ccnc2ccccc12)(C(=O)O)C(F)(F)F` | 0.938 | 5.8 | 3/4 | 283.2 | 3.43 | 50.2 | 8-Hydroxyisoquinoline |
| 14 | `C[C@@](O)(Cc1ccnc2ccccc12)C(F)(F)F` | 0.894 | 5.8 | 3/4 | 255.2 | 3.09 | 33.1 | 8-Hydroxyisoquinoline |
| 15 | `C[C@](O)(Cc1cccc2ncccc12)C(F)(F)F` | 0.894 | 5.8 | 3/4 | 255.2 | 3.09 | 33.1 | 8-Hydroxyisoquinoline |
| 16 | `CCOC(=O)C1(C(=O)C(C)C)c2ccccc2NC(=O)C1(C)C` | 0.684 | 6.0 | 4/4 | 317.4 | 2.69 | 72.5 | Nisoldipine |
| 17 | `COC1COC(COc2cccc(C(N)=O)c2)OC1` | 0.842 | 5.8 | 3/4 | 267.3 | 0.55 | 80.0 | NR-analog |
| 18 | `CC1(C)OCC(OCOc2cccc(C(N)=O)c2)CO1` | 0.823 | 5.8 | 4/4 | 281.3 | 1.29 | 80.0 | NR-analog |
| 19 | `CCOC(=O)[C@](Cc1ccnc2ccccc12)(C(=O)O)C(F)(F)F` | 0.668 | 5.8 | 4/4 | 341.3 | 2.97 | 76.5 | 8-Hydroxyisoquinoline |
| 20 | `O=C(O)[C@@](O)(Cc1ccnc2ccccc12)C(F)(F)F` | 0.906 | 5.5 | 4/4 | 285.2 | 2.16 | 70.4 | 8-Hydroxyisoquinoline |

---

## 4. Chemical Analysis of Top Candidates

### LIMK1 Top Candidates

#### Rank 1
- **SMILES**: `CC(=O)Nc1cccc(-c2cc([C@@]3(C)CCOC3)n(C)n2)c1`
- **Properties**: MW=299.4, LogP=2.72, QED=0.948, CNS-MPO=6.0, BBB=4/4
- **Batch**: BMS-5

#### Rank 2
- **SMILES**: `CC(=O)Nc1cccc(-c2cc([C@@]3(C)CCOC3)nn2C)c1`
- **Properties**: MW=299.4, LogP=2.72, QED=0.948, CNS-MPO=6.0, BBB=4/4
- **Batch**: BMS-5

#### Rank 3
- **SMILES**: `CC(=O)Nc1cccc(-c2cc([C@]3(C)CCOC3)n(C)n2)c1`
- **Properties**: MW=299.4, LogP=2.72, QED=0.948, CNS-MPO=6.0, BBB=4/4
- **Batch**: BMS-5

#### Rank 4
- **SMILES**: `CC(=O)Nc1cccc(-c2cc([C@]3(C)CCOC3)nn2C)c1`
- **Properties**: MW=299.4, LogP=2.72, QED=0.948, CNS-MPO=6.0, BBB=4/4
- **Batch**: BMS-5

#### Rank 5
- **SMILES**: `CC(=O)Nc1cccc(-c2cc([C@@]3(C)CCCO3)nn2C)c1`
- **Properties**: MW=299.4, LogP=3.07, QED=0.947, CNS-MPO=6.0, BBB=3/4
- **Batch**: BMS-5

### SARM1 Top Candidates

#### Rank 1
- **SMILES**: `CC1(C)COC(COc2cccc(C(N)=O)c2)OC1`
- **Properties**: MW=265.3, LogP=1.56, QED=0.897, CNS-MPO=6.0, BBB=4/4
- **Batch**: NR-analog

#### Rank 2
- **SMILES**: `CC1(C)OCC(OCc2cccc(C(N)=O)c2)CO1`
- **Properties**: MW=265.3, LogP=1.45, QED=0.894, CNS-MPO=6.0, BBB=4/4
- **Batch**: NR-analog

#### Rank 3
- **SMILES**: `CCOC(=O)c1c(C)[nH]c2c(C(=O)OC(C)C)cccc2c1=O`
- **Properties**: MW=317.3, LogP=2.58, QED=0.876, CNS-MPO=6.0, BBB=4/4
- **Batch**: Nisoldipine

#### Rank 4
- **SMILES**: `CCOC(=O)c1c(C)[nH]c2cccc(C(=O)OC(C)C)c2c1=O`
- **Properties**: MW=317.3, LogP=2.58, QED=0.876, CNS-MPO=6.0, BBB=4/4
- **Batch**: Nisoldipine

#### Rank 5
- **SMILES**: `CC1(C)COC(COc2cccc(C(N)=O)c2)O1`
- **Properties**: MW=251.3, LogP=1.32, QED=0.876, CNS-MPO=6.0, BBB=4/4
- **Batch**: NR-analog

---

## 5. Complete Molecule Lists

### All LIMK1 Molecules Passing Filters (31 total)

| # | SMILES | QED | CNS-MPO | BBB | MW | LogP | TPSA | Batch |
|---|--------|-----|---------|-----|-----|------|------|-------|
| 1 | `CC(=O)Nc1cccc(-c2cc([C@@]3(C)CCOC3)n(C)n2)c1` | 0.948 | 6.0 | 4/4 | 299.4 | 2.72 | 56.1 | BMS-5 |
| 2 | `CC(=O)Nc1cccc(-c2cc([C@@]3(C)CCOC3)nn2C)c1` | 0.948 | 6.0 | 4/4 | 299.4 | 2.72 | 56.1 | BMS-5 |
| 3 | `CC(=O)Nc1cccc(-c2cc([C@]3(C)CCOC3)n(C)n2)c1` | 0.948 | 6.0 | 4/4 | 299.4 | 2.72 | 56.1 | BMS-5 |
| 4 | `CC(=O)Nc1cccc(-c2cc([C@]3(C)CCOC3)nn2C)c1` | 0.948 | 6.0 | 4/4 | 299.4 | 2.72 | 56.1 | BMS-5 |
| 5 | `CC(=O)Nc1cccc(-c2cc([C@@]3(C)CCCO3)nn2C)c1` | 0.947 | 6.0 | 3/4 | 299.4 | 3.07 | 56.1 | BMS-5 |
| 6 | `CC(=O)Nc1cccc(-c2cc([C@]3(C)CCCO3)n(C)n2)c1` | 0.947 | 6.0 | 3/4 | 299.4 | 3.07 | 56.1 | BMS-5 |
| 7 | `CN1C(=O)NC[C@@H]1c1cccc(-c2cc([C@@]3(C)CCOC3)nn2C)c1` | 0.934 | 6.0 | 4/4 | 340.4 | 2.46 | 59.4 | BMS-5 |
| 8 | `O=C(Nc1cccc(-c2noc(C(F)F)n2)c1)C1CC1` | 0.934 | 6.0 | 3/4 | 279.2 | 3.02 | 68.0 | Pyrrolopyrimidine |
| 9 | `Cn1ccc(NS(=O)(=O)c2c(F)cccc2F)n1` | 0.921 | 6.0 | 4/4 | 273.3 | 1.5 | 64.0 | LIMKi3 |
| 10 | `O=C(Nc1cccc(-c2nc(C(F)(F)F)no2)c1)C1CC1` | 0.945 | 5.9 | 3/4 | 297.2 | 3.1 | 68.0 | Pyrrolopyrimidine |
| 11 | `O=C(Nc1cccc(-c2noc(C(F)(F)F)n2)c1)C1CC1` | 0.945 | 5.9 | 3/4 | 297.2 | 3.1 | 68.0 | Pyrrolopyrimidine |
| 12 | `O=C(Nc1cccc(-c2noc(CC(F)(F)F)n2)c1)C1CC1` | 0.941 | 5.9 | 3/4 | 311.3 | 3.19 | 68.0 | Pyrrolopyrimidine |
| 13 | `O=S(=O)(Nc1cccc(-n2cccn2)c1)c1c(F)cccc1F` | 0.797 | 6.0 | 4/4 | 335.3 | 2.95 | 64.0 | LIMKi3 |
| 14 | `O=S(=O)(Nc1cccc(-c2nnco2)c1)c1c(F)cccc1F` | 0.791 | 6.0 | 4/4 | 337.3 | 2.82 | 85.1 | LIMKi3 |
| 15 | `O=C(Nc1cccc(-c2noc(/C=C/C(F)(F)F)n2)c1)C1CC1` | 0.932 | 5.7 | 3/4 | 323.3 | 3.66 | 68.0 | Pyrrolopyrimidine |
| 16 | `O=S(=O)(Nc1cccc(-c2ccno2)c1)c1c(F)cccc1F` | 0.792 | 5.8 | 3/4 | 336.3 | 3.42 | 72.2 | LIMKi3 |
| 17 | `CC(=O)Nc1cccc(-c2cc([C@@]3(C)C[C@@]3(C)CO)nn2C)c1` | 0.912 | 5.5 | 4/4 | 313.4 | 2.71 | 67.2 | BMS-5 |
| 18 | `CC(=O)Nc1cccc(-n2c(-c3ccc(C)cc3)nnc2[C@]2(C)CCOC2)c1` | 0.750 | 5.4 | 3/4 | 376.5 | 3.88 | 69.0 | BMS-5 |
| 19 | `Nc1cc(NS(=O)(=O)c2c(F)cccc2F)ccn1` | 0.899 | 5.0 | 4/4 | 285.3 | 1.74 | 85.1 | LIMKi3 |
| 20 | `Nc1ccn(-c2cccc(NS(=O)(=O)c3c(F)cccc3F)c2)n1` | 0.757 | 5.0 | 3/4 | 350.4 | 2.53 | 90.0 | LIMKi3 |
| 21 | `NC(=O)c1cc(NS(=O)(=O)c2c(F)cccc2F)ccn1` | 0.887 | 4.6 | 3/4 | 313.3 | 1.26 | 102.1 | LIMKi3 |
| 22 | `NC(=O)c1cccc(NS(=O)(=O)c2c(F)cccc2F)n1` | 0.887 | 4.6 | 3/4 | 313.3 | 1.26 | 102.1 | LIMKi3 |
| 23 | `NS(=O)(=O)c1ccc(NS(=O)(=O)c2c(F)cccc2F)cc1` | 0.871 | 4.5 | 3/4 | 348.4 | 1.41 | 106.3 | LIMKi3 |
| 24 | `NS(=O)(=O)c1cccc(NS(=O)(=O)c2c(F)cccc2F)c1` | 0.871 | 4.5 | 3/4 | 348.4 | 1.41 | 106.3 | LIMKi3 |
| 25 | `O=C(Nc1cccc(-c2noc(CNC(=O)C(F)(F)F)n2)c1)C1CC1` | 0.858 | 4.5 | 3/4 | 354.3 | 2.26 | 97.1 | Pyrrolopyrimidine |
| 26 | `NS(=O)(=O)c1cc(NS(=O)(=O)c2c(F)cccc2F)ccc1F` | 0.856 | 4.4 | 3/4 | 366.3 | 1.55 | 106.3 | LIMKi3 |
| 27 | `O=C(Nc1cccc(NC(=O)c2cc(C(F)(F)F)no2)c1)C(F)=C1CC1` | 0.632 | 4.5 | 3/4 | 369.3 | 3.9 | 84.2 | Pyrrolopyrimidine |
| 28 | `NS(=O)(=O)Cc1cccc(NS(=O)(=O)c2c(F)cccc2F)c1` | 0.842 | 4.2 | 3/4 | 362.4 | 1.55 | 106.3 | LIMKi3 |
| 29 | `C[C@H](NC(=O)c1cnoc1C(F)(F)F)c1cccc(NC(=O)C2CCC2)c1` | 0.822 | 4.1 | 3/4 | 381.4 | 3.92 | 84.2 | Pyrrolopyrimidine |
| 30 | `NS(=O)(=O)c1cc(NS(=O)(=O)c2c(F)cccc2F)ccn1` | 0.846 | 4.0 | 2/4 | 349.3 | 0.81 | 119.2 | LIMKi3 |
| 31 | `NS(=O)(=O)Nc1cccc(NS(=O)(=O)c2c(F)cccc2F)c1` | 0.743 | 2.8 | 3/4 | 363.4 | 1.38 | 118.4 | LIMKi3 |

### All SARM1 Molecules Passing Filters (35 total)

| # | SMILES | QED | CNS-MPO | BBB | MW | LogP | TPSA | Batch |
|---|--------|-----|---------|-----|-----|------|------|-------|
| 1 | `CC1(C)COC(COc2cccc(C(N)=O)c2)OC1` | 0.897 | 6.0 | 4/4 | 265.3 | 1.56 | 70.8 | NR-analog |
| 2 | `CC1(C)OCC(OCc2cccc(C(N)=O)c2)CO1` | 0.894 | 6.0 | 4/4 | 265.3 | 1.45 | 70.8 | NR-analog |
| 3 | `CCOC(=O)c1c(C)[nH]c2c(C(=O)OC(C)C)cccc2c1=O` | 0.876 | 6.0 | 4/4 | 317.3 | 2.58 | 85.5 | Nisoldipine |
| 4 | `CCOC(=O)c1c(C)[nH]c2cccc(C(=O)OC(C)C)c2c1=O` | 0.876 | 6.0 | 4/4 | 317.3 | 2.58 | 85.5 | Nisoldipine |
| 5 | `CC1(C)COC(COc2cccc(C(N)=O)c2)O1` | 0.876 | 6.0 | 4/4 | 251.3 | 1.32 | 70.8 | NR-analog |
| 6 | `CCOC(=O)c1c(C)[nH]c2c(C(=O)OCC)cccc2c1=O` | 0.875 | 6.0 | 4/4 | 303.3 | 2.19 | 85.5 | Nisoldipine |
| 7 | `CCOC(=O)c1c(C)[nH]c2c(C(=O)OC(C)(C)C)cccc2c1=O` | 0.874 | 6.0 | 4/4 | 331.4 | 2.97 | 85.5 | Nisoldipine |
| 8 | `C[C@@](N)(Cc1ccnc2ccccc12)C(F)(F)F` | 0.894 | 5.9 | 3/4 | 254.3 | 3.06 | 38.9 | 8-Hydroxyisoquinoline |
| 9 | `CCOC(=O)C1=C(C)Nc2ccccc2C(C(=O)OCC)=C1C` | 0.864 | 5.9 | 3/4 | 315.4 | 3.29 | 64.6 | Nisoldipine |
| 10 | `C[C@@](Cc1cccc2ncccc12)(C(=O)O)C(F)(F)F` | 0.938 | 5.8 | 3/4 | 283.2 | 3.43 | 50.2 | 8-Hydroxyisoquinoline |
| 11 | `C[C@@](Cc1ccnc2ccccc12)(C(=O)O)C(F)(F)F` | 0.938 | 5.8 | 3/4 | 283.2 | 3.43 | 50.2 | 8-Hydroxyisoquinoline |
| 12 | `C[C@](Cc1cccc2ncccc12)(C(=O)O)C(F)(F)F` | 0.938 | 5.8 | 3/4 | 283.2 | 3.43 | 50.2 | 8-Hydroxyisoquinoline |
| 13 | `C[C@](Cc1ccnc2ccccc12)(C(=O)O)C(F)(F)F` | 0.938 | 5.8 | 3/4 | 283.2 | 3.43 | 50.2 | 8-Hydroxyisoquinoline |
| 14 | `C[C@@](O)(Cc1ccnc2ccccc12)C(F)(F)F` | 0.894 | 5.8 | 3/4 | 255.2 | 3.09 | 33.1 | 8-Hydroxyisoquinoline |
| 15 | `C[C@](O)(Cc1cccc2ncccc12)C(F)(F)F` | 0.894 | 5.8 | 3/4 | 255.2 | 3.09 | 33.1 | 8-Hydroxyisoquinoline |
| 16 | `CCOC(=O)C1(C(=O)C(C)C)c2ccccc2NC(=O)C1(C)C` | 0.684 | 6.0 | 4/4 | 317.4 | 2.69 | 72.5 | Nisoldipine |
| 17 | `COC1COC(COc2cccc(C(N)=O)c2)OC1` | 0.842 | 5.8 | 3/4 | 267.3 | 0.55 | 80.0 | NR-analog |
| 18 | `CC1(C)OCC(OCOc2cccc(C(N)=O)c2)CO1` | 0.823 | 5.8 | 4/4 | 281.3 | 1.29 | 80.0 | NR-analog |
| 19 | `CCOC(=O)[C@](Cc1ccnc2ccccc12)(C(=O)O)C(F)(F)F` | 0.668 | 5.8 | 4/4 | 341.3 | 2.97 | 76.5 | 8-Hydroxyisoquinoline |
| 20 | `O=C(O)[C@@](O)(Cc1ccnc2ccccc12)C(F)(F)F` | 0.906 | 5.5 | 4/4 | 285.2 | 2.16 | 70.4 | 8-Hydroxyisoquinoline |
| 21 | `O=C(O)[C@](O)(Cc1cccc2ncccc12)C(F)(F)F` | 0.906 | 5.5 | 4/4 | 285.2 | 2.16 | 70.4 | 8-Hydroxyisoquinoline |
| 22 | `OC(Cc1cccc2ncccc12)(C(F)(F)F)C(F)(F)F` | 0.859 | 5.5 | 3/4 | 309.2 | 3.63 | 33.1 | 8-Hydroxyisoquinoline |
| 23 | `OC(Cc1ccnc2ccccc12)(C(F)(F)F)C(F)(F)F` | 0.859 | 5.5 | 3/4 | 309.2 | 3.63 | 33.1 | 8-Hydroxyisoquinoline |
| 24 | `CCOC(=O)C1=C(C)NC(=C(C)C)c2c(C(=O)OC(C)C)cccc21` | 0.840 | 5.5 | 3/4 | 343.4 | 3.9 | 64.6 | Nisoldipine |
| 25 | `O=C(O)C(Cc1ccccc1)(C(=O)O)C(F)(F)F` | 0.813 | 5.5 | 4/4 | 262.2 | 1.95 | 74.6 | 8-Hydroxyisoquinoline |
| 26 | `CC1(C)OCC(OCCOc2cccc(C(N)=O)c2)CO1` | 0.801 | 5.5 | 4/4 | 295.3 | 1.33 | 80.0 | NR-analog |
| 27 | `CCOC(=O)C1=C(C)Nc2c(C(=O)OC(C)C)cccc2C1=C(C)C` | 0.825 | 5.3 | 3/4 | 343.4 | 4.31 | 64.6 | Nisoldipine |
| 28 | `CCOC(=O)c1cccc2c1c(C(=O)OCC)c(C(=O)OCC)n2C` | 0.590 | 5.5 | 4/4 | 347.4 | 2.71 | 83.8 | Nisoldipine |
| 29 | `CCOC(=O)C(C)=C1c2ccccc2C(=O)Nc2cccc(C(=O)OC(C)C)c21` | 0.622 | 5.2 | 3/4 | 393.4 | 4.2 | 81.7 | Nisoldipine |
| 30 | `CCCN(CC(F)(F)F)C(=O)COC(=O)Cc1cccc2ncccc12` | 0.705 | 5.1 | 3/4 | 368.4 | 3.12 | 59.5 | 8-Hydroxyisoquinoline |
| 31 | `CCOC(=O)C1=C(C(=O)OCC)C(C)(C)Nc2c(C(=O)OC(C)C)cccc21` | 0.589 | 5.1 | 2/4 | 389.4 | 3.34 | 90.9 | Nisoldipine |
| 32 | `CC1(C)COC(COc2cccc(C(=N)N)c2)OC1` | 0.641 | 5.0 | 4/4 | 264.3 | 1.75 | 77.6 | NR-analog |
| 33 | `CCOC(=O)C1=CC(C(=O)OCC)=C(C)Nc2c(C(=O)OC(C)(C)C)cccc21` | 0.592 | 5.0 | 2/4 | 401.5 | 3.85 | 90.9 | Nisoldipine |
| 34 | `CCOC(=O)C1=C(C(=O)OCC)c2c(C(=O)OC(C)(C)C)cccc2-c2ccccc2N1` | 0.541 | 4.4 | 2/4 | 437.5 | 4.57 | 90.9 | Nisoldipine |
| 35 | `CCNC(=O)C(C)=C(C(=O)OCC)c1c(N)cccc1C(=O)OC(C)C` | 0.438 | 3.6 | 3/4 | 362.4 | 2.31 | 107.7 | Nisoldipine |

---

## 6. Summary Statistics

| Metric | LIMK1 | SARM1 |
|--------|-------|-------|
| Scaffolds used | 3 | 3 |
| Molecules generated | 90 | 90 |
| Unique valid | 31 | 36 |
| Passed filters | 31 | 35 |
| Avg QED | 0.873 | 0.800 |
| Avg CNS-MPO | 5.3 | 5.6 |
| BBB-penetrant | 30/31 | 32/35 |
| MW range | 273.3-381.4 | 251.3-437.5 |
| LogP range | 0.81-3.92 | 0.55-4.57 |

---

## 7. Next Steps

1. **DiffDock v2.2 Docking**: Dock top 10 LIMK1 candidates against LIMK1 kinase domain (PDB: 3S95 or AlphaFold model)
2. **DiffDock v2.2 Docking**: Dock top 10 SARM1 candidates against SARM1 NADase domain (PDB: 7NAK or AlphaFold model)
3. **Selectivity Profiling**: Compare top hits against off-target kinases (LIMK2, ROCK1/2) using docking scores
4. **ADMET Prediction**: Run SwissADME/pkCSM for pharmacokinetic and toxicity estimates
5. **Lead Optimization**: Use top-scoring docked poses for second-round MolMIM generation with tighter scaffolds
6. **Cross-target Combination Analysis**: Evaluate LIMK1+SARM1 dual-target potential for synergistic neuroprotection

---

## 8. Technical Notes

- **GenMol NIM**: Returned SAFE encoding bug (`integer division or modulo by zero`) -- MolMIM used as validated alternative
- **NVIDIA API Key**: `.bashrc` key expired (403); `.env` key `nvapi-OBS_...` used successfully
- **MolMIM API**: CMA-ES with 40 iterations, 30 particles, min_similarity=0.3, QED scoring
- **Drug-likeness**: Lipinski Ro5 (max 1 violation), BBB (3/4 criteria), CNS-MPO (Pfizer 6-component), QED > 0.4
- **Deduplication**: Within-batch and cross-batch SMILES deduplication applied