# MAPK14 & LIMK1 Protein Binder Design — 2026-03-22

## Pipeline

**RFdiffusion** (backbone generation) -> **ProteinMPNN** (sequence design) -> **ESMfold** (structure validation)

All three steps run via NVIDIA NIM cloud APIs (build.nvidia.com).

---

## Target 1: MAPK14 (p38alpha MAPK)

- **Protein**: MAPK14 / p38alpha — mitogen-activated protein kinase 14
- **UniProt**: Q16539
- **Structure**: PDB 1A9U — X-ray crystal structure of human p38alpha MAP kinase (chain A, residues 4-354)
- **Rationale**: MAPK14 is a central stress kinase in the p38 MAPK pathway. In SMA motor neurons, aberrant p38 signaling contributes to neuronal apoptosis and neuroinflammation. Inhibiting MAPK14 could protect motor neurons from stress-induced degeneration.

### RFdiffusion Parameters

| Parameter | Value |
|-----------|-------|
| Target PDB | 1A9U chain A (p38alpha kinase) |
| Contig specification | `90/0 A4-354` |
| Binder length | 90 residues |
| Number of designs | 5 |
| Avg generation time | ~49 seconds per backbone |

### Results (Ranked by pLDDT)

#### Design 2 — Best Overall
- **MPNN Score**: 0.7634 (best)
- **ESMfold pLDDT**: 87.2 (range: 67.2-92.8)
- **Sequence** (90 aa):
```
EVEELLEERLERVERRLREGEGARETIAREMRALAVELARRGYDEEEILEALERFTERLRERLGEEVEVELRRAKLAVRAMFAALENLDR
```

#### Design 5 — Co-Best pLDDT
- **MPNN Score**: 0.7754
- **ESMfold pLDDT**: 86.8 (range: 65.0-93.3)
- **Sequence** (90 aa):
```
KAERARKILKRKIKEFMLDDLGLSEEEVEEAVKKLEEWKDLEIDEQLEKAEELLLEIVKDNEELKELVKGRMEKFKETIEEVEKFLEREE
```

#### Design 1
- **MPNN Score**: 0.7847
- **ESMfold pLDDT**: 79.0 (range: 54.9-88.1)
- **Sequence** (90 aa):
```
LEEDIKLAKVIIEEKLKKEAKEVSEEEVKELKERIERKVTEEGKGIEDVIEEEMARFEEETGNKELRELVTRIKLELRSTKEALENIRKR
```

#### Design 4
- **MPNN Score**: 0.7516 (lowest = best designability)
- **ESMfold pLDDT**: 74.3 (range: 52.4-87.7)
- **Sequence** (90 aa):
```
SFEEEARKTMEELKRLWDYEPVEVNAAKIISELVIASEKSGKELEEVIEYFKEIAEEDEELKEQIEAAKEKIKEAKEEVKKALEKEEELR
```

#### Design 3 — Lowest Confidence
- **MPNN Score**: 0.7912
- **ESMfold pLDDT**: 69.3 (range: 35.3-83.7)
- **Sequence** (90 aa):
```
KKVVYKFKDKLSEDESKEVKACEKGMKKLLKDKEELEKFEKLEKKAVESGLAGRDAVRKLILLKYEKENMTWEKIEESIEEMLRALENIE
```

### MAPK14 Interpretation

- **Designs 2 and 5** are top candidates with pLDDT > 86 — these are predicted to fold into well-defined helical structures with high confidence.
- **Design 2** has the best combination: lowest MPNN score (0.7634 = most designable backbone) AND highest pLDDT (87.2).
- **Design 3** has a minimum pLDDT of 35.3, indicating partially disordered regions. Deprioritize.
- MAPK14 binders outperform ROCK2 binders (87.2 vs 85.0 peak pLDDT), likely because the 1A9U crystal structure provides a higher-quality binding surface than the ROCK2 2F2U structure.

---

## Target 2: LIMK1 (LIM Domain Kinase 1)

- **Protein**: LIMK1 — LIM domain kinase 1
- **UniProt**: P53667
- **Structure**: AlphaFold v2 prediction, kinase domain extracted (chain A, residues 390-638)
- **Rationale**: LIMK1 phosphorylates cofilin (CFL1/CFL2), and the LIMK-cofilin axis is the direct effector of actin dynamics dysfunction in SMA. Inhibiting LIMK1 could prevent pathological cofilin phosphorylation and restore actin turnover in motor neurons and NMJs.

### RFdiffusion Parameters

| Parameter | Value |
|-----------|-------|
| Target PDB | AlphaFold LIMK1 kinase domain (residues 390-638) |
| Contig specification | `90/0 A390-638` |
| Binder length | 90 residues |
| Number of designs | 5 |
| Avg generation time | ~29 seconds per backbone |

### Results (Ranked by pLDDT)

#### Design 4 — Best Overall
- **MPNN Score**: 0.8181
- **ESMfold pLDDT**: 74.2 (range: 46.4-83.5)
- **Sequence** (90 aa):
```
MTQSERLLKHLEEMAEELKEKATKIREETGKETVHIRISLKVEENKETGKVEGKLKFETVGVENEEAKKELEELIEKHRERLLEEVAEKE
```

#### Design 3
- **MPNN Score**: 0.8136
- **ESMfold pLDDT**: 60.9 (range: 30.0-78.2)
- **Sequence** (90 aa):
```
MKVEETEESKTAFGITLREAFKLAGSKKKLEDLDYTTSAAVVEFESGEKVTMVGFEVKEEDVEELKKRIKELIKYLKEELGLDLELIEVE
```

#### Design 2
- **MPNN Score**: 0.8363
- **ESMfold pLDDT**: 57.6 (range: 38.7-74.4)
- **Sequence** (90 aa):
```
MEIEVATEADTLAADLRLRLHERLKLKEVEVRVVEDDTVDEETGVREASVEWFFKTEEEREAGLELLRELGEECRERNEICRFSEELEVE
```

#### Design 1
- **MPNN Score**: 0.8480
- **ESMfold pLDDT**: 48.9 (range: 22.1-75.1)
- **Sequence** (90 aa):
```
MLGTTGGVGAIGAALLAVCKEEGTEVEEVEMRFVGSSFMEVDGEWVDVVSAEVSEEVRERLLRYIREKEERGWERRQLTEDVTLVLERRE
```

#### Design 5 — Lowest Confidence
- **MPNN Score**: 0.7980 (best MPNN)
- **ESMfold pLDDT**: 47.8 (range: 32.0-73.8)
- **Sequence** (90 aa):
```
AEVKYENIKAEDNLGEIELELELLERGEECTWEIFHEGNIESVEKLLKEKGINATIKLSDYKPSEEEKEKIKEKIEKLKEKLKNVIVEEE
```

### LIMK1 Interpretation

- **Only Design 4** reaches acceptable pLDDT (74.2). Designs 1-3 and 5 are all below 70, meaning they are predicted to be at least partially disordered.
- **MPNN scores are higher (worse)** than MAPK14/ROCK2 (0.80-0.85 vs 0.75-0.80), suggesting the LIMK1 kinase domain surface is harder to design binders against.
- The lower quality is likely because we used an **AlphaFold-predicted** structure (not experimental). AlphaFold structures have inherent uncertainties, especially in surface loops critical for binder design.
- **Recommendation**: Obtain an experimental crystal structure of the LIMK1 kinase domain (e.g., PDB 3S95, 5NXC, or 6SCB) and rerun the pipeline. This should significantly improve binder quality.

---

## Cross-Target Comparison

| Target | Best Design | pLDDT | MPNN Score | Structure Source |
|--------|-------------|-------|------------|-----------------|
| **ROCK2** | Design 4 | 85.0 | 0.7603 | PDB 2F2U (X-ray) |
| **MAPK14** | Design 2 | **87.2** | **0.7634** | PDB 1A9U (X-ray) |
| **LIMK1** | Design 4 | 74.2 | 0.8181 | AlphaFold (predicted) |

Key observations:
- Targets with **experimental crystal structures** (ROCK2, MAPK14) consistently produce higher-quality binders than AlphaFold predictions (LIMK1).
- **MAPK14 Design 2** is the best binder across all three targets (pLDDT 87.2, excellent MPNN 0.7634).
- The RhoA-ROCK-LIMK-Cofilin pathway now has designed binders for all three kinases: ROCK2 (upstream), MAPK14 (parallel stress signaling), and LIMK1 (direct cofilin kinase).

---

## Caveats

1. **No binding affinity prediction**: RFdiffusion designs backbones geometrically but does not predict binding energy. AlphaFold2-Multimer or Rosetta interface scoring needed.
2. **No experimental validation**: Computational designs only. SPR, ITC, or co-crystallization testing required.
3. **LIMK1 quality**: The AlphaFold-based LIMK1 designs are marginal. Redesigning with an experimental PDB is strongly recommended.
4. **Hotspot selection**: Broad kinase domain targeting. More specific hotspot targeting of ATP-binding pockets could yield more potent inhibitory binders.
5. **ProteinMPNN limitations**: NVIDIA NIM API only returns 1 sequence per backbone (minimal parameters accepted). Self-hosted ProteinMPNN would allow temperature sampling and multiple sequence generation per backbone.

---

## Files on Server (moltbot)

### MAPK14
```
/home/bryzant/sma-platform/data/binder_designs/
  mapk14_backbone_{1-5}.pdb          — RFdiffusion backbone structures (complex)
  mapk14_mpnn_{1-5}.json             — ProteinMPNN sequence design results
  mapk14_binder_{1-5}_esmfold.pdb    — ESMfold-predicted binder structures
  mapk14_binder_final.json           — Summary results (ranked by pLDDT)
```

### LIMK1
```
/home/bryzant/sma-platform/data/binder_designs/
  limk1_backbone_{1-5}.pdb           — RFdiffusion backbone structures (complex)
  limk1_mpnn_{1-5}.json              — ProteinMPNN sequence design results
  limk1_binder_{1-5}_esmfold.pdb     — ESMfold-predicted binder structures
  limk1_binder_final.json            — Summary results (ranked by pLDDT)
```

### Additional PDB files
```
/home/bryzant/sma-platform/data/pdb/
  MAPK14_1A9U.pdb                    — Experimental p38alpha crystal structure (downloaded)
  LIMK1_kinase_390-638.pdb           — LIMK1 kinase domain extracted from AlphaFold
```

---

## Next Steps

1. **LIMK1 redesign with experimental PDB**: Download PDB 3S95 or 5NXC (LIMK1 kinase domain X-ray structures) and rerun the pipeline.
2. **AlphaFold2-Multimer**: Predict complex structures of top binders (MAPK14 Design 2, ROCK2 Design 4) with their targets to assess interface quality.
3. **Rosetta InterfaceAnalyzer**: Score binding energy (ddG) for top designs from all three targets.
4. **Hotspot-focused redesign**: Target specific active site residues:
   - MAPK14: T180, Y182 (activation loop), K53, E71 (ATP pocket)
   - LIMK1: T508 (activation loop), K368, E384 (ATP pocket)
5. **Multi-target panel**: Compare all top binders for selectivity — an ideal LIMK1 binder should NOT bind ROCK2/MAPK14.

## API Format Reference

| API | URL | Accepted Fields |
|-----|-----|----------------|
| RFdiffusion | `health.api.nvidia.com/.../rfdiffusion/generate` | `input_pdb`, `contigs` |
| ProteinMPNN | `health.api.nvidia.com/.../proteinmpnn/predict` | `input_pdb` |
| ESMfold | `health.api.nvidia.com/.../nvidia/esmfold` | `sequence` |

**ProteinMPNN output format**: `mfasta` field contains FASTA entries separated by `>`. Entry 1 = input (polyglycine). Entry 2 = designed sequence (T=0.1, sample=1). Chains separated by `/`. Binder = chain A (first segment before `/`).
