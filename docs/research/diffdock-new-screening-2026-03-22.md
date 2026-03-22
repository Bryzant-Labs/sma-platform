# DiffDock Virtual Screening — New Compounds & Targets (2026-03-22)

## Overview

Ran 36 DiffDock v2.2 docking simulations via NVIDIA NIM cloud API:
- **6 compounds** (4 new + 1 existing + 1 control) against **6 targets** (3 new + 3 existing)
- All 36 dockings completed successfully
- **3 positive-confidence hits** identified

## NVIDIA NIM Status

| NIM Service | Status | Endpoint | Notes |
|------------|--------|----------|-------|
| DiffDock v2.2 | **HEALTHY** | `health.api.nvidia.com/v1/biology/mit/diffdock` | 36/36 dockings succeeded |
| GenMol v1.0 | **HEALTHY** | `health.api.nvidia.com/v1/biology/nvidia/genmol/generate` | Returns 400 on bad input (working) |
| MolMIM | **HEALTHY** | `health.api.nvidia.com/v1/biology/nvidia/molmim/generate` | Molecule optimization working |
| OpenFold3 | **OFFLINE** | 404 | Endpoint not found — may be deprecated or renamed |
| RNAPro | **OFFLINE** | 404 | Endpoint not found — may be deprecated or renamed |

**Important**: DiffDock requires `ligand_file_type: "txt"` for SMILES input (not `"sdf"`). Using `"sdf"` with SMILES causes silent failures (status: "failed", null confidences).

## New Targets Added

| Target | UniProt | AlphaFold PDB | Atoms | SMA Relevance |
|--------|---------|---------------|-------|---------------|
| LIMK1 | P53667 | AF-P53667-F1-model_v6 | 5,087 | LIM kinase 1 — phosphorylates cofilin, controls actin dynamics downstream of ROCK |
| MAPK14/p38 | Q16539 | AF-Q16539-F1-model_v6 | 2,907 | p38 MAPK — neuroinflammation, stress signaling in motor neurons |
| MDM2 | Q00987 | AF-Q00987-F1-model_v6 | 3,859 | p53 negative regulator — SMN stability, apoptosis control |

PDB files saved to: `/home/bryzant/sma-platform/data/pdb/`

## Compounds Screened

| Compound | SMILES | Description | Rationale |
|----------|--------|-------------|-----------|
| MW150 | `Cc1cc(C)c(Nc2nccc(-c3ccc(F)cc3)n2)c(C)c1` | p38 MAPK alpha/beta inhibitor | BBB-permeable, anti-neuroinflammatory, designed for CNS |
| Panobinostat | `O=C(/C=C/c1cccc(Cc2ccc(N)cc2)c1)NO` | Pan-HDAC inhibitor (FDA-approved) | Epigenetic modulator, tested in SMA context for SMN2 upregulation |
| Belumosudil | `CC(NC(=O)c1cc(F)c(-c2ccnc(Nc3ccc(N4CCC(F)(F)C4)cc3)n2)cc1F)c1ccc(F)cc1` | ROCK2-selective inhibitor (FDA-approved) | Actin cytoskeleton modulator, directly relevant to CORO1C/CFL pathway |
| Palbociclib | `CC(=O)c1c(C)c2cnc(Nc3ccc(N4CCNCC4)cn3)nc2n(C2CCCC2)c1=O` | CDK4/6 inhibitor (FDA-approved) | Cell cycle control, potentially relevant to motor neuron survival |
| MS023 | `CC(C)NCC(O)COc1ccc2[nH]c(-c3ccc(N(C)C)cc3)nc2c1` | Type I PRMT inhibitor | Epigenetic modulator, potential SMN2 upregulator |
| 4-Aminopyridine | `Nc1ccncc1` | K+ channel blocker (control) | Baseline comparison compound from previous screening |

**Note**: MDI-117740 (LIMK inhibitor) was excluded — no public SMILES available.

## Results

### Hits (confidence > 0)

| Rank | Compound | Target | Best Confidence | Avg Confidence | Assessment |
|------|----------|--------|-----------------|----------------|------------|
| 1 | **Palbociclib** | **MAPK14** | **+0.3313** | +0.0110 | Best hit — CDK4/6 inhibitor binds p38 MAPK |
| 2 | **4-Aminopyridine** | **MAPK14** | **+0.1674** | -1.3036 | Weak hit — small molecule, likely nonspecific |
| 3 | **Palbociclib** | **LIMK1** | **+0.0717** | -0.0710 | Marginal hit — kinase cross-reactivity expected |

### Near-misses (confidence -0.5 to 0)

| Compound | Target | Best Confidence | Avg Confidence |
|----------|--------|-----------------|----------------|
| Panobinostat | MAPK14 | -0.1542 | -0.8404 |
| MW150 | LIMK1 | -0.2031 | -1.2913 |
| 4-Aminopyridine | MDM2 | -0.3517 | -0.8720 |
| Belumosudil | LIMK1 | -0.4996 | -1.5926 |

### Full Results Table (sorted by best confidence)

| Compound | Target | Best Conf | Avg Conf | Status |
|----------|--------|-----------|----------|--------|
| Palbociclib | MAPK14 | +0.3313 | +0.0110 | HIT |
| 4-Aminopyridine | MAPK14 | +0.1674 | -1.3036 | HIT |
| Palbociclib | LIMK1 | +0.0717 | -0.0710 | HIT |
| Panobinostat | MAPK14 | -0.1542 | -0.8404 | near-miss |
| MW150 | LIMK1 | -0.2031 | -1.2913 | near-miss |
| 4-Aminopyridine | MDM2 | -0.3517 | -0.8720 | near-miss |
| Belumosudil | LIMK1 | -0.4996 | -1.5926 | weak |
| Panobinostat | MDM2 | -0.5348 | -1.9774 | weak |
| 4-Aminopyridine | CORO1C | -0.5836 | -1.2779 | weak |
| 4-Aminopyridine | SMN2 | -0.6189 | -1.5749 | weak |
| 4-Aminopyridine | PLS3 | -0.7621 | -1.4655 | weak |
| Panobinostat | CORO1C | -0.7740 | -2.1483 | no bind |
| 4-Aminopyridine | LIMK1 | -0.7773 | -2.0436 | no bind |
| MW150 | MDM2 | -0.8241 | -2.0688 | no bind |
| MW150 | CORO1C | -0.8476 | -2.6669 | no bind |
| MS023 | MAPK14 | -0.9826 | -1.2859 | no bind |
| MW150 | MAPK14 | -1.0292 | -1.3955 | no bind |
| MS023 | LIMK1 | -1.2408 | -1.9824 | no bind |
| Palbociclib | MDM2 | -1.3370 | -2.8396 | no bind |
| Panobinostat | PLS3 | -1.3673 | -3.0161 | no bind |
| Palbociclib | PLS3 | -1.3871 | -2.9557 | no bind |
| MW150 | SMN2 | -1.5528 | -3.1131 | no bind |
| MS023 | PLS3 | -1.6207 | -3.4995 | no bind |
| Belumosudil | SMN2 | -1.6653 | -3.2344 | no bind |
| Panobinostat | SMN2 | -1.7021 | -3.2099 | no bind |
| Palbociclib | CORO1C | -1.7279 | -2.8191 | no bind |
| MS023 | MDM2 | -1.7868 | -3.1246 | no bind |
| Belumosudil | CORO1C | -1.8353 | -3.2478 | no bind |
| MW150 | PLS3 | -1.9343 | -3.3187 | no bind |
| Belumosudil | MAPK14 | -1.9386 | -2.7353 | no bind |
| MS023 | CORO1C | -2.0124 | -3.3592 | no bind |
| Belumosudil | PLS3 | -2.3564 | -3.4399 | no bind |
| Panobinostat | LIMK1 | -2.5286 | -3.1506 | no bind |
| Belumosudil | MDM2 | -2.6388 | -3.1637 | no bind |
| Palbociclib | SMN2 | -2.6824 | -3.6428 | no bind |
| MS023 | SMN2 | -3.2266 | -3.7430 | no bind |

## Key Observations

### 1. Palbociclib shows kinase cross-reactivity
- Best hit: **Palbociclib vs MAPK14** (confidence +0.33) — a CDK4/6 inhibitor showing binding to p38 MAPK
- Also marginal binding to LIMK1 (+0.07) — both are kinases, so cross-reactivity is structurally plausible
- **Caveat**: DiffDock confidence > 0 is a weak signal. Previous validation showed only riluzole was a true validated hit from our prior screening. Confidence thresholds should be > +0.5 for higher confidence.

### 2. MW150 does NOT strongly bind its intended target (p38/MAPK14)
- MW150 vs MAPK14: confidence -1.03 (no binding predicted)
- MW150 is designed as a p38 MAPK inhibitor, but DiffDock does not predict strong binding to the AlphaFold structure
- This may reflect: (a) AlphaFold structure vs crystal structure differences, (b) DiffDock limitations with this target conformation, or (c) the need for active-site-specific docking

### 3. Belumosudil disappoints against actin pathway targets
- Despite being a ROCK2 inhibitor (directly upstream of LIMK1 in the actin pathway), Belumosudil shows weak binding to LIMK1 (-0.50) and poor binding to CORO1C (-1.84) and PLS3 (-2.36)
- This is expected — Belumosudil targets ROCK2 specifically, not downstream kinases

### 4. No compounds bind well to SMN2, PLS3, or CORO1C
- All compounds scored < -0.5 against these SMA-specific targets
- Consistent with previous screening: these protein targets may not have conventional druggable binding pockets
- SMN2 as an RNA-based target is better addressed by splicing modifiers (risdiplam approach)

### 5. MAPK14 is the most "druggable" new target
- Best binding across multiple compounds
- 2 out of 3 hits were against MAPK14
- Makes sense — p38 MAPK has a well-defined ATP binding pocket

## DiffDock Confidence Interpretation

| Confidence Range | Interpretation | Action |
|-----------------|----------------|--------|
| > +0.5 | Strong binding predicted | Priority for experimental validation |
| +0.0 to +0.5 | Weak/marginal binding | Interesting but unreliable without validation |
| -0.5 to 0.0 | Very weak binding | Likely noise |
| < -0.5 | No binding | Reject |

**Per our validation study**: Only riluzole (conf ~+0.15) was validated as a true DiffDock hit out of 518 prior dockings. DiffDock has known MW bias (favors larger molecules) and 5-pose runs are unreliable. These results should be treated as computational hypotheses, not predictions.

## Files

- Results JSON: `/home/bryzant/sma-platform/gpu/results/nim_batch/diffdock_new_screening_2026-03-22.json`
- New PDB structures: `/home/bryzant/sma-platform/data/pdb/{LIMK1_P53667,MAPK14_Q16539,MDM2_Q00987}.pdb`
- Docking script: `/tmp/run_docking2.py` (on moltbot, ephemeral)

## Next Steps

1. **Add LIMK1, MAPK14, MDM2 to platform's `_TARGET_PDB_MAP`** in `virtual_screening.py`
2. **Validate Palbociclib-MAPK14 hit** with literature search — is CDK4/6-p38 cross-reactivity known?
3. **Try 20-pose runs** for the 3 hits to improve confidence estimates
4. **Consider adding ROCK2 (O75116)** as a docking target — it is Belumosudil's actual target and highly SMA-relevant
5. **MDI-117740 SMILES**: Contact vendor or search patents for the LIMK inhibitor structure
