# MolMIM Molecule Generation for High-Druggability SMA Targets

**Date**: 2026-03-22
**Method**: NVIDIA MolMIM NIM (CMA-ES optimization)
**Server**: moltbot (217.154.10.79)
**Results**: `/home/bryzant/sma-platform/gpu/results/molmim_druggable_targets_2026-03-22.json`

## Summary

| Target | pLDDT | Raw Generated | Unique Valid | Drug-like (QED>0.5 + Lipinski) | BBB-Permeable | Best QED |
|--------|-------|---------------|--------------|-------------------------------|---------------|----------|
| LDHA   | 96.1  | 120           | 19           | 18                            | 18            | 0.948    |
| CASP3  | 86.6  | 120           | 34           | 34                            | 34            | 0.947    |
| CASP9  | 80.9  | 120           | 23           | 23                            | 23            | 0.948    |
| MDM2   | --    | 120           | 17           | 17                            | 17            | 0.948    |
| **Total** | | **480**       | **93**       | **92**                        | **92**        |          |

**Note**: SARM1 was skipped (already done in prior session).

## Method Details

- **Model**: MolMIM (Molecular Masked Inverse-folding Model) via NVIDIA NIM cloud API
- **Why MolMIM**: GenMol has a SAFE encoding bug that produces invalid molecules. MolMIM uses CMA-ES optimization directly in latent space.
- **Settings per scaffold**: 3 rounds with varying diversity (min_similarity 0.2/0.3/0.4, scaled_radius 0.8/1.0/1.5), 50 iterations, 50 particles, QED-optimized
- **Filter criteria**: QED > 0.5, Lipinski Rule of 5 pass, BBB permeability (TPSA < 90, MW < 450, 0 < LogP < 5)
- **Scaffolds**: 4 known inhibitor scaffolds per target (16 total), chosen from published literature

---

## 1. LDHA (Lactate Dehydrogenase A)

**AF2 pLDDT**: 96.1 (highest confidence among all targets)
**SMA Relevance**: Motor neurons show metabolic stress; LDHA inhibition may redirect pyruvate to mitochondrial oxidation, reducing lactate-driven acidosis in SMA motor neurons.

### Scaffolds Used
| Scaffold | Description | SMILES |
|----------|-------------|--------|
| NHI-1 | Naphthohydroxamic acid LDHA inhibitor | `O=C(O)c1cc2c(cc1O)C(=O)c1ccccc1C2=O` |
| FX-11 | Gossypol-derivative LDHA inhibitor | `O=C(O)c1cc(O)c2c(c1)C(=O)c1ccccc1C2=O` |
| Oxamate | Pyruvate-competitive LDHA inhibitor | `NC(=O)C(=O)O` |
| Gossypol | Natural LDHA inhibitor | `Cc1cc2c(C=O)c(O)c(O)c(C(C)C)c2c(O)c1-c1c(C)cc2c(C=O)c(O)c(O)c(C(C)C)c2c1O` |

### Top 10 Candidates

| Rank | QED | MW | LogP | TPSA | BBB | Scaffold | SMILES |
|------|-----|-----|------|------|-----|----------|--------|
| 1 | 0.948 | 309.4 | 3.09 | 57.6 | Yes | FX-11 | `Cc1cc(C(=O)O)cc(C)c1CN1Cc2ccccc2CC1=O` |
| 2 | 0.947 | 309.4 | 3.17 | 57.6 | Yes | NHI-1 | `CCN1C[C@@](C)(c2ccccc2C(=O)O)c2ccccc2C1=O` |
| 3 | 0.947 | 309.4 | 3.17 | 57.6 | Yes | NHI-1 | `CCN1C[C@](C)(c2ccc(C(=O)O)cc2)c2ccccc2C1=O` |
| 4 | 0.947 | 295.3 | 2.99 | 57.6 | Yes | NHI-1 | `CCN1C[C@@H](c2ccc(C(=O)O)cc2)c2ccccc2C1=O` |
| 5 | 0.946 | 300.3 | 3.10 | 63.6 | Yes | NHI-1 | `O=C(O)c1cc(O[C@@H]2CC(=O)c3ccccc3C2)ccc1F` |
| 6 | 0.945 | 303.4 | 3.38 | 60.2 | Yes | Gossypol | `Cc1cccc(C)c1-c1c(C)cc(CS(N)(=O)=O)cc1C` |
| 7 | 0.944 | 296.3 | 3.31 | 63.6 | Yes | FX-11 | `COc1cc(C(=O)O)cc([C@@H]2CC(=O)c3ccccc3C2)c1` |
| 8 | 0.905 | 283.3 | 2.25 | 77.8 | Yes | NHI-1 | `O=C(O)c1cc(CN2Cc3ccccc3C2=O)ccc1O` |
| 9 | 0.904 | 308.4 | 3.77 | 87.1 | Yes | Gossypol | `Cc1cc(C)c(C(C)C)c(O)c1-c1cc(C#N)cc(C(N)=O)c1` |
| 10 | 0.894 | 295.3 | 4.06 | 81.3 | Yes | Gossypol | `Cc1ccc(-c2cc(C#N)cc(C(=O)O)c2)c(O)c1C(C)C` |

**Key observations**: LDHA candidates retain the carboxylic acid moiety critical for pyruvate-competitive binding. The top compounds feature isochromanone/tetralone scaffolds with excellent drug-likeness (QED 0.83-0.95).

---

## 2. CASP3 (Caspase-3)

**AF2 pLDDT**: 86.6
**SMA Relevance**: CASP3 drives motor neuron death in SMA; inhibition could delay apoptosis and extend the motor neuron survival window for SMN restoration.

### Scaffolds Used
| Scaffold | Description | SMILES |
|----------|-------------|--------|
| Isatin-core | Caspase-3 small molecule scaffold | `O=C1Nc2ccccc2C1=O` |
| 5-Nitroisatin | Potent caspase-3 inhibitor | `O=C1Nc2ccc([N+](=O)[O-])cc2C1=O` |
| Nicotinamide | Weak caspase-3 modulator, CNS-penetrant | `NC(=O)c1cccnc1` |
| Quinoline-amide | Quinoline carboxamide scaffold | `O=C(Nc1ccccc1)c1ccc2ccccc2n1` |

### Top 10 Candidates

| Rank | QED | MW | LogP | TPSA | BBB | Scaffold | SMILES |
|------|-----|-----|------|------|-----|----------|--------|
| 1 | 0.947 | 302.4 | 2.62 | 66.5 | Yes | Isatin | `Cc1cc(C)cc(NS(=O)(=O)N2C(=O)c3ccccc32)c1` |
| 2 | 0.947 | 296.4 | 2.78 | 51.2 | Yes | Quinoline | `O=C(NC[C@@H]1CC12CCOCC2)c1ccc2ccccc2n1` |
| 3 | 0.947 | 296.4 | 2.78 | 51.2 | Yes | Quinoline | `O=C(NC1CC([C@H]2CCOC2)C1)c1ccc2ccccc2n1` |
| 4 | 0.945 | 307.2 | 3.10 | 75.0 | Yes | Quinoline | `N#Cc1ccccc1NC(=O)c1cccc(OC(F)(F)F)n1` |
| 5 | 0.944 | 309.4 | 2.11 | 62.3 | Yes | Nicotinamide | `C[C@@H]1C[C@@H](NC(=O)c2ccccc2)CN1C(=O)c1cccnc1` |
| 6 | 0.944 | 309.4 | 2.11 | 62.3 | Yes | Nicotinamide | `C[C@@H]1[C@@H](NC(=O)c2ccccc2)CCN1C(=O)c1cccnc1` |
| 7 | 0.944 | 315.4 | 2.18 | 62.3 | Yes | Nicotinamide | `C[C@@H]1C[C@H](NC(=O)c2ccsc2)CN1C(=O)c1cccnc1` |
| 8 | 0.944 | 323.4 | 2.50 | 62.3 | Yes | Nicotinamide | `C[C@@H]1CC[C@@H](NC(=O)c2ccccc2)CN1C(=O)c1cccnc1` |
| 9 | 0.942 | 287.3 | 2.29 | 63.2 | Yes | Isatin | `O=C1Nc2ccccc2[C@@H]1S(=O)(=O)Cc1ccccc1` |
| 10 | 0.942 | 317.8 | 2.89 | 76.3 | Yes | Nicotinamide | `CC(C)N(C(=O)c1cccnc1)c1cc(Cl)ccc1C(N)=O` |

**Key observations**: CASP3 candidates show strong diversity. The isatin-sulfonamide (#1) retains the critical isatin warhead. Nicotinamide-derived compounds (#5-8) are promising due to their CNS-penetrant scaffolds. Quinoline amides (#2-4) are novel scaffolds with excellent QED.

---

## 3. CASP9 (Caspase-9)

**AF2 pLDDT**: 80.9
**SMA Relevance**: CASP9 initiates the intrinsic apoptosis cascade in SMN-deficient motor neurons; blocking upstream initiation may be more effective than blocking downstream executioners.

### Scaffolds Used
| Scaffold | Description | SMILES |
|----------|-------------|--------|
| Isatin-5-sulfonamide | Selective caspase-9 scaffold | `NS(=O)(=O)c1ccc2c(c1)C(=O)C(=O)N2` |
| Anilinoquinazoline | 4-anilinoquinazoline kinase/caspase scaffold | `Nc1ccc(Nc2ncnc3ccccc23)cc1` |
| Pyrrolidine-dione | N-phenyl succinimide caspase modulator | `O=C1CCC(=O)N1c1ccccc1` |
| XIAP-mimic | Benzoxazole XIAP-BIR3 mimic | `CC(NC(=O)c1cccc(F)c1)c1nc2ccccc2o1` |

### Top 10 Candidates

| Rank | QED | MW | LogP | TPSA | BBB | Scaffold | SMILES |
|------|-----|-----|------|------|-----|----------|--------|
| 1 | 0.948 | 309.4 | 2.89 | 62.3 | Yes | Pyrrolidine | `O=C1CCCCN1C(=O)N[C@@H](c1ccccc1)c1ccccn1` |
| 2 | 0.947 | 309.8 | 3.10 | 60.2 | Yes | Isatin-sulfonamide | `Cc1ccc([C@@H](N)c2cc(S(C)(=O)=O)ccc2Cl)cc1` |
| 3 | 0.947 | 303.4 | 3.13 | 65.8 | Yes | XIAP-mimic | `Cc1nc(C(C)(C)NC(=O)c2cccc(F)c2)sc1C#N` |
| 4 | 0.946 | 310.3 | 2.84 | 75.7 | Yes | Pyrrolidine | `O=C1CCC(=O)N(c2ccc(Oc3ccccc3)cc2)C(=O)N1` |
| 5 | 0.946 | 306.3 | 3.17 | 42.0 | Yes | XIAP-mimic | `O=C(NC1CC(c2ccc(F)cn2)C1)c1ccc(F)c(F)c1` |
| 6 | 0.945 | 296.3 | 3.31 | 58.6 | Yes | Pyrrolidine | `C[C@H]1CC(=O)N(c2ccc(Oc3ccccc3)cc2)C(=O)N1` |
| 7 | 0.944 | 289.3 | 2.82 | 65.8 | Yes | XIAP-mimic | `CC(C)(NC(=O)c1cccc(F)c1)c1nc(C#N)cs1` |
| 8 | 0.943 | 307.4 | 2.12 | 77.2 | Yes | Isatin-sulfonamide | `NS(=O)(=O)c1ccc(Cc2cc3c(s2)CCC3=O)cc1` |
| 9 | 0.943 | 317.4 | 2.65 | 86.5 | Yes | Isatin-sulfonamide | `NS(=O)(=O)c1ccc(Oc2ccc3c(c2)C(=O)CCC3)cc1` |
| 10 | 0.942 | 312.4 | 3.35 | 50.3 | Yes | Anilinoquinazoline | `CC(C)(C)c1ccc(Nc2cc(N3CCOCC3)ncn2)cc1` |

**Key observations**: CASP9 candidates feature diverse chemotypes. The XIAP-mimics (#3, #5, #7) are particularly interesting as they could inhibit both CASP9 activation and XIAP-mediated apoptosis regulation. Sulfonamide derivatives retain the key pharmacophore.

---

## 4. MDM2 (p53 Negative Regulator)

**SMA Relevance**: p53 pathway is hyperactivated in SMA motor neurons; MDM2 inhibition restores p53-mediated transcription including SMN2 upregulation. This addresses the "p53 gap" identified by Simon Schiaffino.

### Scaffolds Used
| Scaffold | Description | SMILES |
|----------|-------------|--------|
| Nutlin-core | Nutlin-3a imidazoline MDM2-p53 inhibitor | `c1ccc(C2=NC(c3ccc(Cl)cc3)C(c3ccc(Cl)cc3)N2)cc1` |
| Spiro-oxindole | MI-series MDM2 inhibitor | `O=C1Nc2ccccc2C11CCNCC1` |
| Piperidinone | AMG-232 class MDM2 inhibitor | `O=C1CC(c2ccc(Cl)cc2)CN1c1ccc(Cl)cc1` |
| Benzodiazepinedione | Benzodiazepinedione scaffold | `O=C1NC(=O)c2ccccc2N1Cc1ccccc1` |

### Top 10 Candidates

| Rank | QED | MW | LogP | TPSA | BBB | Scaffold | SMILES |
|------|-----|-----|------|------|-----|----------|--------|
| 1 | 0.948 | 304.7 | 2.92 | 62.6 | Yes | Piperidinone | `O=C(Nc1ccco1)[C@@H]1CC(=O)N(c2ccc(Cl)cc2)C1` |
| 2 | 0.947 | 304.8 | 2.72 | 46.3 | Yes | Piperidinone | `NC(=O)C1(c2ccc(Cl)cc2)CN(c2ccc(F)cc2)C1` |
| 3 | 0.947 | 302.4 | 2.49 | 49.4 | Yes | Benzodiazepinedione | `O=S1(=O)CCN(CCc2ccccc2)c2ccccc2N1` |
| 4 | 0.946 | 304.7 | 2.55 | 76.5 | Yes | Piperidinone | `NC(=O)c1ccc(N2CC(c3ccc(Cl)o3)CC2=O)cc1` |
| 5 | 0.946 | 314.8 | 2.96 | 63.4 | Yes | Piperidinone | `NC(=O)c1ccc(N2CC(c3ccc(Cl)cc3)CC2=O)cc1` |
| 6 | 0.946 | 295.3 | 2.55 | 52.7 | Yes | Benzodiazepinedione | `C[C@@H]1NN(Cc2ccccc2)C(=O)N(c2ccccc2)C1=O` |
| 7 | 0.945 | 312.8 | 2.84 | 32.3 | Yes | Spiro-oxindole | `O=C1NC2(CN(CCc3ccc(Cl)cc3)C2)c2ccccc21` |
| 8 | 0.945 | 306.4 | 2.90 | 32.3 | Yes | Spiro-oxindole | `O=C1N(CCc2ccccc2)c2ccccc2C12CCNCC2` |
| 9 | 0.942 | 314.8 | 3.52 | 49.4 | Yes | Nutlin-core | `O=C1C[C@@H](c2ccc(Cl)cc2)NC(=O)N1Cc1ccccc1` |
| 10 | 0.939 | 286.8 | 3.32 | 32.3 | Yes | Nutlin-core | `O=C1C[C@@H](c2ccc(Cl)cc2)NN1Cc1ccccc1` |

**Key observations**: MDM2 candidates are highly diverse. The piperidinone derivatives (#1, #2, #4, #5) retain the chloro-aryl pharmacophore essential for MDM2 pocket binding. Compound #5 (QED 0.946, Sim 0.763 to AMG-232 scaffold) is a close analog of the clinical candidate AMG-232. Spiro-oxindoles (#7, #8) maintain the MI-series core.

---

## Drug-likeness Filter Details

All 92 drug-like candidates passed:
- **Lipinski Rule of 5**: MW <= 500, LogP <= 5, HBD <= 5, HBA <= 10
- **QED > 0.5**: Quantitative Estimate of Drug-likeness (Bickerton et al. 2012)
- **BBB permeability estimate**: TPSA < 90, MW < 450, 0 < LogP < 5

All 92 candidates are BBB-permeable by computational estimate, critical for SMA where CNS penetration is required for motor neuron targets.

## Next Steps

1. **DiffDock docking**: Dock top 5 candidates per target against AF2-predicted structures to estimate binding affinity
2. **ADMET prediction**: Run SwissADME or ADMETlab for full ADMET profiling
3. **Selectivity check**: Ensure CASP3 inhibitors don't block CASP9 (and vice versa) unless dual inhibition is desired
4. **MDM2 priority**: Compound #5 (`NC(=O)c1ccc(N2CC(c3ccc(Cl)cc3)CC2=O)cc1`, Sim=0.763 to piperidinone scaffold) is closest to clinical MDM2 inhibitors and should be prioritized
5. **Combination strategy**: LDHA (metabolic) + CASP3/9 (anti-apoptotic) + MDM2 (p53/SMN2) could form a triple combination approach for SMA

## Files

- Results JSON: `moltbot:/home/bryzant/sma-platform/gpu/results/molmim_druggable_targets_2026-03-22.json`
- Generation script: `moltbot:/home/bryzant/sma-platform/scripts/molmim_druggable_targets.py`
- This report: `docs/research/genmol-druggable-targets-2026-03-22.md`
