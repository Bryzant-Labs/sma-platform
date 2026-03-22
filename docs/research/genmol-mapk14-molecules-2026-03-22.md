# GenMol/MolMIM: Novel Drug-Like Molecules Targeting MAPK14/p38

**Date**: 2026-03-22
**Target**: MAPK14 (p38 MAP kinase, UniProt Q16539)
**Tool**: NVIDIA MolMIM NIM (CMA-ES algorithm, QED-optimized)
**Docking**: DiffDock v2.2 NIM against PDB 1A9U (MAPK14 crystal structure)

## Summary

Generated 150 molecules from 3 scaffold sources using NVIDIA MolMIM NIM.
After deduplication and drug-likeness filtering:
- **118 unique** molecules generated
- **113 passed** Lipinski Rule of Five + QED > 0.5
- **112 BBB-permeable** (TPSA <= 90, MW <= 400)
- **Top 10 docked** against MAPK14 via DiffDock v2.2

## Generation Parameters

| Source | Scaffold SMILES | Raw | Unique | QED Range | Median QED |
|--------|----------------|-----|--------|-----------|------------|
| MW150 scaffold | `Nc1cc(N)nc(-c2ccccc2)c1` | 50 | 37 | 0.697-0.946 | 0.884 |
| SB203580 scaffold | `CS(=O)c1ccc2[nH]c(-c3ccccc3)nc2c1-c1ccc(F)cc1` | 50 | 41 | 0.528-0.827 | 0.768 |
| De novo (pyridine) | `c1ccc2[nH]c(-c3ccncc3)nc2c1` | 50 | 40 | 0.855-0.946 | 0.939 |

**MolMIM Settings**: algorithm=CMA-ES, property_name=QED, particles=60, iterations=10-15, min_similarity=0.1-0.3

## DiffDock Docking Results (Top 10 vs MAPK14)

Docked against PDB 1A9U (MAPK14 experimental crystal structure), 5 poses each.
DiffDock confidence: higher = better binding prediction (positive = strong binder).

| Rank | Best Conf. | Avg Conf. | QED | MW | LogP | TPSA | BBB | Source | SMILES |
|------|-----------|-----------|-----|-----|------|------|-----|--------|--------|
| **1** | **+0.433** | -0.465 | 0.942 | 285.4 | 3.19 | 54.9 | Y | de novo | `O=C(Nc1nnc(-c2ccccc2)s1)[C@H]1[C@@H]2CCC[C@@H]21` |
| 2 | -0.124 | -0.907 | 0.942 | 297.4 | 2.96 | 68.0 | Y | de novo | `C[C@H](NC(=O)[C@H]1[C@@H]2CCC[C@@H]21)c1noc(-c2ccccc2)n1` |
| 3 | -0.245 | -1.223 | 0.941 | 281.4 | 2.85 | 54.9 | Y | de novo | `C[C@H](NC(=O)[C@H]1[C@@H]2CCC[C@@H]21)c1ncc2ccccc2n1` |
| 4 | -0.246 | -1.039 | 0.941 | 281.4 | 2.85 | 54.9 | Y | de novo | `C[C@H](NC(=O)[C@H]1[C@@H]2CCC[C@@H]21)c1ncnc2ccccc12` |
| 5 | -0.285 | -0.877 | 0.942 | 307.4 | 3.37 | 54.9 | Y | de novo | `C[C@H](NC(=O)[C@H]1[C@@H]2CCC[C@@H]21)c1ncc(-c2ccccc2)cn1` |
| 6 | -0.629 | -1.340 | 0.941 | 281.4 | 2.85 | 54.9 | Y | de novo | `C[C@H](NC(=O)[C@H]1[C@@H]2CCC[C@@H]21)c1cnc2ccccc2n1` |
| 7 | -0.761 | -1.312 | 0.942 | 297.4 | 2.96 | 68.0 | Y | de novo | `C[C@H](NC(=O)[C@H]1[C@@H]2CCC[C@@H]21)c1nc(-c2ccccc2)no1` |
| 8 | -0.809 | -1.322 | 0.942 | 307.4 | 3.37 | 54.9 | Y | de novo | `C[C@H](NC(=O)[C@H]1[C@@H]2CCC[C@@H]21)c1cnc(-c2ccccc2)nc1` |
| 9 | -0.866 | -1.592 | 0.946 | 300.4 | 2.29 | 51.2 | Y | de novo | `O=C(NC1(c2nc3ccccc3s2)CC1)[C@H]1[C@@H]2COC[C@@H]21` |
| 10 | -1.712 | -2.824 | 0.946 | 296.4 | 2.68 | 45.4 | Y | MW150 | `Cc1cc(N)cc(N2CCCN(Cc3ccccc3)CC2)n1` |

## Lead Compound Analysis

### #1: Thiadiazole-bicyclopentane amide (BEST DOCKING)

```
O=C(Nc1nnc(-c2ccccc2)s1)[C@H]1[C@@H]2CCC[C@@H]21
```

- **DiffDock confidence: +0.433** (only positive-confidence hit = predicted binder)
- QED: 0.942 | MW: 285.4 | LogP: 3.19 | TPSA: 54.9 | BBB: Yes
- HBD: 1 | HBA: 4 | Rotatable bonds: 3 | Rings: 4
- **Scaffold**: 1,3,4-thiadiazole linked to phenyl, with bicyclo[2.1.0]pentane carboxamide
- **Key features**: Compact, rigid bicyclic constraint, thiadiazole hinge-binder motif

### #2: Oxadiazole-bicyclopentane (second best)

```
C[C@H](NC(=O)[C@H]1[C@@H]2CCC[C@@H]21)c1noc(-c2ccccc2)n1
```

- DiffDock confidence: -0.124 | QED: 0.942 | MW: 297.4 | BBB: Yes
- 1,2,4-oxadiazole with phenyl and methylamine-bicyclopentane

### #3-4: Quinazoline/quinoxaline variants

```
C[C@H](NC(=O)[C@H]1[C@@H]2CCC[C@@H]21)c1ncc2ccccc2n1   (naphthyridine)
C[C@H](NC(=O)[C@H]1[C@@H]2CCC[C@@H]21)c1ncnc2ccccc12   (quinazoline)
```

- Both: confidence ~-0.25, QED 0.941, MW 281.4, excellent drug-likeness

## Structural Themes

1. **Bicyclo[2.1.0]pentane carboxamide** is the dominant warhead across 8/10 top compounds - highly rigid, conformationally constrained, favorable for kinase binding
2. **N-heterocyclic aromatic** heads (thiadiazole, oxadiazole, pyrimidine, quinazoline, naphthyridine) serve as hinge-binding motifs for kinase ATP pocket
3. **Phenyl appendage** provides hydrophobic pocket engagement
4. All compounds are **BBB-permeable** and **drug-like** (QED > 0.94)

## Drug-Likeness Summary (All 113 Filtered)

| Property | Range | Median |
|----------|-------|--------|
| QED | 0.503 - 0.946 | 0.903 |
| MW | 185.2 - 499.6 | 293.4 |
| LogP | -0.42 - 4.98 | 2.85 |
| TPSA | 20.3 - 89.7 | 54.9 |
| HBD | 0 - 4 | 1 |
| HBA | 1 - 10 | 4 |
| Rotatable bonds | 1 - 9 | 3 |
| BBB-permeable | 112/113 (99%) | - |

## Additional Filtered Molecules (Ranked 11-30)

| Rank | QED | MW | LogP | BBB | Source | SMILES |
|------|-----|-----|------|-----|--------|--------|
| 11 | 0.941 | 313.4 | 3.43 | Y | de novo | `C[C@H](NC(=O)[C@H]1[C@@H]2CCC[C@@H]21)c1nc(-c2ccccc2)ns1` |
| 12 | 0.939 | 279.3 | 2.67 | Y | de novo | `O=C(NC1[C@H]2CCC[C@H]12)c1cnc(-c2ccccc2)nc1` |
| 13 | 0.939 | 279.3 | 2.67 | Y | de novo | `O=C(N[C@H]1[C@@H]2CCC[C@@H]21)c1cnc(-c2ccccc2)nc1` |
| 14 | 0.939 | 324.4 | 2.77 | Y | de novo | `O=C(NCC1(N2CCCC2)CCCC1)c1cnc2ccccc2n1` |
| 15 | 0.939 | 279.3 | 3.13 | Y | de novo | `O=C(Nc1cnc(-c2ccccc2)nc1)C1[C@@H]2CCC[C@@H]12` |
| 16 | 0.939 | 279.3 | 3.13 | Y | de novo | `O=C(Nc1cnc(-c2ccccc2)nc1)[C@H]1[C@@H]2CCC[C@@H]21` |
| 17 | 0.939 | 279.3 | 3.13 | Y | de novo | `O=C(Nc1nccc(-c2ccccc2)n1)[C@H]1[C@@H]2CCC[C@@H]21` |
| 18 | 0.938 | 311.4 | 1.95 | Y | de novo | `C[C@H](Cn1cnc2ccccc2c1=O)NC(=O)[C@H]1[C@@H]2CCC[C@@H]21` |
| 19 | 0.938 | 282.4 | 2.29 | Y | MW150 | `Cc1cc(N)cc(CN2CCN(c3ccccc3)CC2)n1` |
| 20 | 0.938 | 282.4 | 2.29 | Y | MW150 | `Cc1cc(N)cc(N2CCN(Cc3ccccc3)CC2)n1` |
| 21 | 0.938 | 286.4 | 3.52 | Y | de novo | `C[C@H](NC(=O)C1[C@H]2CCC[C@H]12)c1nc2ccccc2s1` |
| 22 | 0.938 | 286.4 | 3.52 | Y | de novo | `C[C@H](NC(=O)[C@H]1[C@@H]2CCC[C@@H]21)c1nc2ccccc2s1` |
| 23 | 0.937 | 299.4 | 3.73 | Y | MW150 | `Cc1cc(N)cc(N2CCC(Sc3ccccc3)CC2)n1` |
| 24 | 0.937 | 281.4 | 2.98 | Y | de novo | `C[C@H](NC(=O)[C@@H]1C[C@H]1C)c1ncc(-c2ccccc2)cn1` |
| 25 | 0.937 | 281.4 | 2.98 | Y | de novo | `C[C@H](NC(=O)[C@H]1C[C@H]1C)c1ncc(-c2ccccc2)cn1` |
| 26 | 0.937 | 281.4 | 3.06 | Y | de novo | `O=C(NCC1CCCC1)c1cnc(-c2ccccc2)nc1` |
| 27 | 0.937 | 281.4 | 2.51 | Y | de novo | `C[C@@H]1C[C@H]1CNC(=O)[C@@H]1C[C@H]1c1cnc2ccccc2n1` |
| 28 | 0.935 | 293.4 | 1.86 | Y | MW150 | `N#Cc1cc(N)nc(N2CCN(Cc3ccccc3)CC2)c1` |
| 29 | 0.934 | 289.4 | 1.97 | Y | de novo | `O=S(=O)(NC1CCC1)c1cnc(-c2ccccc2)nc1` |
| 30 | 0.933 | 275.4 | 3.00 | Y | de novo | `CCC1(CNC(=O)c2nc3cccnc3s2)CCC1` |

## Technical Notes

- **GenMol vs MolMIM**: The GenMol NIM `/generate` endpoint requires SAFE format input which has a bug with most SMILES. MolMIM (`/v1/biology/nvidia/molmim/generate`) works correctly with the `smi` parameter and CMA-ES optimization.
- **DiffDock**: Requires SDF format (not SMILES) for ligand input. Protein must be ATOM-only PDB lines.
- **Confidence interpretation**: DiffDock confidence > 0 indicates predicted binding. Only compound #1 achieved positive confidence (+0.433).
- **Limitation**: DiffDock is a pose predictor, not an affinity predictor. Positive confidence suggests reasonable binding geometry but does not quantify binding energy.

## Next Steps

1. Validate lead #1 (thiadiazole-bicyclopentane) with molecular dynamics simulation
2. Dock against known p38 inhibitor co-crystal structures (3GCP, 1OUK) for comparison
3. Compare DiffDock confidence to known p38 inhibitors (SB203580, BIRB-796, VX-745)
4. Run selectivity screening against other kinases (ERK2, JNK1, CDK2)
5. Consider SAR expansion around the thiadiazole-bicyclopentane scaffold
