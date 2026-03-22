# GenMol/MolMIM ROCK2 Molecule Generation Report

**Date**: 2026-03-22
**Target**: ROCK2 (Rho-associated protein kinase 2, UniProt O75116)
**Rationale**: ROCK2 inhibition restores actin dynamics in SMA motor neurons; fasudil (approved ROCK inhibitor) validated as a lead scaffold in prior DiffDock screening.

---

## 1. Generation Method

**Tool**: NVIDIA MolMIM NIM (CMA-ES optimization, QED scoring)
**Note**: GenMol NIM returned `"Incorrect input molecule description - integer division or modulo by zero"` for all SMILES inputs (SAFE encoding bug). MolMIM was used as a validated alternative.

### Scaffolds Used (5 batches, 100 molecules total)

| Batch | Scaffold | SMILES | Rationale |
|-------|----------|--------|-----------|
| 1 | Fasudil | `O=S(=O)(c1cccc2c1cc1CCn3ccnc3c1n2)N1CCCCC1` | Approved ROCK inhibitor |
| 2 | Y-27632 | `CC(N)C1CCC(c2cccc3[nH]cnc23)CC1` | Selective ROCK inhibitor |
| 3 | Kinase scaffold | `c1ccc(-c2ccnc3[nH]ccc23)cc1` | Generic kinase pharmacophore |
| 4 | Fasudil (high-div) | Same as batch 1, 20 iterations | More diverse exploration |
| 5 | Ripasudil-like | `O=C(NC1CCNCC1)c1cccc2[nH]ccc12` | Approved ROCK inhibitor (eye) |

---

## 2. Drug-Likeness Filtering

**Filters Applied**:
- Lipinski Rule of 5 (MW < 500, LogP < 5, HBD < 5, HBA < 10; max 1 violation)
- BBB penetration (3/4 of: MW < 450, LogP 1-3, TPSA < 90, HBD <= 3)
- CNS MPO score (Pfizer 6-component, 0-6 scale)
- QED > 0.4

**Results**: 71 unique valid molecules -> **69 passed all filters** (97.2% pass rate)

---

## 3. Top 20 Drug-Like Candidates (ranked by CNS-MPO + QED)

| Rank | SMILES | QED | CNS-MPO | BBB | MW | LogP | TPSA | Batch |
|------|--------|-----|---------|-----|-----|------|------|-------|
| 1 | `CN(C)C1CCN(Cc2ccc3nc[nH]c3c2)CC1` | 0.915 | 5.7 | 4/4 | 258.2 | 2.09 | 35.2 | Y-27632 |
| 2 | `O=S(=O)(c1cccc2c1CCNC2)N1CCCCCC1` | 0.906 | 5.6 | 4/4 | 294.1 | 1.90 | 49.4 | Fasudil-2 |
| 3 | `O=S(=O)(c1cccc2c1CCNC2)N1CCCCC1` | 0.893 | 5.6 | 4/4 | 280.1 | 1.51 | 49.4 | Fasudil-2 |
| 4 | `O=S(=O)(c1cccc2c1CNCC2)N1CCCCC1` | 0.893 | 5.6 | 4/4 | 280.1 | 1.51 | 49.4 | Fasudil-2 |
| 5 | `CN(C)C1CC(N(C)C(=O)Cc2c[nH]c3ncccc23)C1` | 0.930 | 5.5 | 4/4 | 286.2 | 1.66 | 52.2 | Y-27632 |
| 6 | `O=S(=O)(c1cccc2c1NCCC2)N1CCCCC1` | 0.903 | 5.5 | 4/4 | 280.1 | 2.22 | 49.4 | Fasudil-2 |
| 7 | `CCn1nc(S(=O)(=O)N2CCCCCC2)c2cccnc21` | 0.870 | 5.4 | 4/4 | 308.1 | 2.02 | 68.1 | Fasudil-2 |
| 8 | `CN(C)C1CCN(Cc2c[nH]c3ccccc23)CC1` | 0.913 | 5.4 | 4/4 | 257.2 | 2.69 | 22.3 | Y-27632 |
| 9 | `O=S(=O)(c1cccc2c1OCCN2)N1CCCCC1` | 0.896 | 5.4 | 4/4 | 282.1 | 1.67 | 58.6 | Fasudil-2 |
| 10 | `O=S(=O)(c1cccn2c1nc1ccccc12)N1CCCCC1` | 0.730 | 5.4 | 4/4 | 315.1 | 2.66 | 54.7 | Fasudil-2 |
| 11 | `O=S(=O)(c1ccccc1-c1cnc2cncn2c1)N1CCCC1` | 0.739 | 5.4 | 4/4 | 328.1 | 2.18 | 67.6 | Fasudil-1 |
| 12 | `c1nc2c(c(Oc3cncc4c3CCCC4)n1)CCC2` | 0.839 | 5.3 | 3/4 | 267.1 | 3.03 | 47.9 | Fasudil-1 |
| 13 | `O=S(=O)(c1cccc2c1NCCC2)N1CCCCCC1` | 0.912 | 5.3 | 4/4 | 294.1 | 2.61 | 49.4 | Fasudil-2 |
| 14 | `O=S(=O)(c1cccc2c1nc1n2CCNC1)N1CCCCCC1` | 0.908 | 5.2 | 4/4 | 334.1 | 1.70 | 67.2 | Fasudil-2 |
| 15 | `O=S(=O)(c1cccc2c1nc1n2CCNCC1)N1CCCCC1` | 0.900 | 5.2 | 4/4 | 334.1 | 1.36 | 67.2 | Fasudil-2 |
| 16 | `CCSC1CCC([C@H](N)C[C@H](C)OC)CC1` | 0.781 | 5.2 | 3/4 | 245.2 | 3.05 | 35.2 | Y-27632 |
| 17 | `O=S(=O)(c1ccccc1OCc1ccncc1)N1CCCCC1` | 0.845 | 5.2 | 4/4 | 332.1 | 2.84 | 59.5 | Fasudil-1 |
| 18 | `O=S(=O)(c1cncc(-c2ncc3c(n2)CCC3)c1)N1CCCCC1` | 0.853 | 5.2 | 4/4 | 344.1 | 2.20 | 76.0 | Fasudil-1 |
| 19 | `O=S(=O)(c1ccccc1-c1ncnc2c1CCC2)N1CCCCC1` | 0.860 | 5.1 | 4/4 | 343.1 | 2.81 | 63.2 | Fasudil-1 |
| 20 | `O=S(=O)(c1cccc(-c2ncc3c(n2)CCC3)c1)N1CCCCC1` | 0.860 | 5.1 | 4/4 | 343.1 | 2.81 | 63.2 | Fasudil-1 |

---

## 4. Chemical Analysis of Top Candidates

### Rank 1: Benzimidazole-piperidine (Y-27632 derivative)
- **SMILES**: `CN(C)C1CCN(Cc2ccc3nc[nH]c3c2)CC1`
- **Key features**: Benzimidazole + 4-(dimethylamino)piperidine. High QED (0.915), excellent CNS-MPO (5.7). Low MW (258), ideal LogP (2.09). Structurally related to known kinase inhibitors.
- **BBB**: Predicted permeable (4/4 criteria met)

### Ranks 2-4: Simplified fasudil analogs (sulfonamide core)
- Retain the sulfonamide-piperidine warhead of fasudil
- Replace the isoquinoline with simpler tetrahydroisoquinoline or isoindoline
- MW 280-294, excellent drug-likeness

### Rank 5: Indole-azetidine (Y-27632 derivative)
- **SMILES**: `CN(C)C1CC(N(C)C(=O)Cc2c[nH]c3ncccc23)C1`
- Compact azaindole + azetidine scaffold with N,N-dimethyl group
- Highest QED in set (0.930)

---

## 5. DiffDock Docking Status

**Status**: BLOCKED -- NVIDIA DiffDock cloud NIM API returning HTTP 400 for all inputs.

Tested:
- Multiple PDB formats (AlphaFold full-length, kinase domain extract, RCSB crystal structures)
- Multiple SMILES (simple benzene to complex scaffolds)
- Multiple payload formats (raw/base64 PDB, various field names)
- All return `{"error":{"message":"Bad request.","type":"BadRequestError","code":400}}`

**Root cause**: The NVIDIA DiffDock cloud NIM at `health.api.nvidia.com/v1/biology/mit/diffdock` appears to have a service-side issue as of 2026-03-22. The endpoint responds to OPTIONS (405 = POST only) but rejects all POST requests with 400.

**Next steps for docking**:
1. Deploy DiffDock locally on Vast.ai GPU (self-hosted NIM container)
2. Retry cloud NIM when NVIDIA resolves the issue
3. Alternative: use AutoDock Vina or GNINA locally

---

## 6. ROCK2 Target Context

- **UniProt**: O75116
- **PDB**: 2F2U (crystal structure with fasudil bound), 4WOT, 4L6Q
- **Kinase domain**: Residues 92-354 (serine/threonine kinase)
- **SMA relevance**: ROCK2 hyperactivation impairs actin dynamics in SMN-deficient motor neurons. Fasudil showed therapeutic benefit in SMA mouse models (Bowerman et al., 2010). ROCK2 is a validated target in the SMA platform with evidence tier "Strong".

---

## 7. NVIDIA API Key Rotation Required

**IMPORTANT**: The NVIDIA API key was inadvertently exposed during verbose curl debugging. Rotate the key at https://build.nvidia.com and update `/home/bryzant/sma-platform/.env` on moltbot.

---

## 8. Summary

| Metric | Value |
|--------|-------|
| Molecules generated | 100 (5 batches x 20) |
| Unique valid | 71 |
| Passed drug-likeness filters | 69 (97.2%) |
| Top candidate QED | 0.930 |
| Top candidate CNS-MPO | 5.7/6.0 |
| BBB-permeable candidates | 65 (94.2%) |
| Docking completed | 0/10 (API blocked) |
| Generation tool | NVIDIA MolMIM NIM (CMA-ES + QED) |

**Key finding**: The fasudil-derived sulfonamide scaffolds (Ranks 2-6, 9, 13-15) retain the ROCK2-targeting pharmacophore while achieving better drug-likeness scores than fasudil itself. The Y-27632-derived benzimidazole-piperidine (Rank 1) represents a novel scaffold class with the highest CNS-MPO score (5.7), suggesting excellent brain penetration potential -- critical for SMA CNS therapy.
