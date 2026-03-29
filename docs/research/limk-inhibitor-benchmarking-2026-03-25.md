# LIMK Inhibitor Benchmarking: AI Candidates vs Real-World Drugs

**Date**: 2026-03-25
**Method**: DiffDock v2.2 (NVIDIA NIM), 20 poses per docking
**Targets**: LIMK2 (P53671), ROCK2 (O75116)

## Motivation

We previously identified two AI-designed candidates with strong DiffDock confidence scores against LIMK2 and ROCK2. To calibrate these results, we docked three real-world LIMK inhibitors as benchmarks:

1. **LX-7101** (CHEMBL3356433) -- Phase 1 clinical, dual LIMK2/ROCK2, pChEMBL 8.8
2. **MDI-114215** -- First CNS-penetrant LIMK1/2 allosteric inhibitor (J Med Chem 2024, Baldwin et al.)
3. **BMS-5** -- Known LIMK1/2 dual inhibitor (Bristol-Myers Squibb)

## Results

### Comparison Table

| Rank | Compound | Type | LIMK2 top | ROCK2 top | Positive poses (LIMK2) |
|------|----------|------|-----------|-----------|------------------------|
| 1 | **(S,S)-H-1152** | AI stereo-optimized | **+0.957** | **+0.484** | 17/20 |
| 2 | **genmol_119** | AI designed (GenMol) | **+0.704** | **+0.400** | 14/20 |
| 3 | BMS-5 | Real-world (BMS) | -0.089 | -1.959 | 0/20 |
| 4 | LX-7101 | Real-world (Phase 1) | -0.314 | -0.433 | 0/20 |
| 5 | MDI-114215 | Real-world (J Med Chem) | -0.840 | -1.580 | 0/20 |

### Key Observations

1. **Both AI candidates outperform all three real drugs** on both targets by a large margin.
2. **Zero positive poses** for any of the three real drugs on either target -- all 120 poses (3 compounds x 2 targets x 20 poses) had negative confidence.
3. **(S,S)-H-1152** scores +0.957 on LIMK2 vs the best real drug (BMS-5) at -0.089 -- a delta of >1.0 confidence units.
4. **LX-7101** (Phase 1 clinical, pChEMBL 8.8 = ~1.6 nM) failed DiffDock with top confidence -0.314. This compound has proven in-vitro and in-vivo activity.

## Critical Interpretation

### Why real drugs scored poorly

DiffDock confidence scores are **not equivalent to binding affinity**. Several factors explain the discrepancy:

1. **DiffDock v2.2 bias toward small, rigid molecules**: Our H-1152 scaffold (MW ~250, 1 rotatable bond) is compact and rigid. The real drugs are larger (MW 424-480) and more flexible, which DiffDock struggles with.

2. **Allosteric vs orthosteric binding**: MDI-114215 is an **allosteric** LIMK inhibitor (binds outside the ATP site). DiffDock docks into the ATP-binding pocket by default. Allosteric inhibitors will inherently score poorly in an orthosteric docking setup.

3. **PDB structure limitations**: Our LIMK2 PDB may not have the appropriate conformation to accommodate these larger ligands. Co-crystal structures with LX-7101 or BMS-5 would likely score much better.

4. **Known DiffDock limitations**: Previous validation (see `learnings-diffdock-validation.md`) showed DiffDock is unreliable for ranking -- only riluzole validated in our prior benchmarks. The method has MW bias and 5-pose runs are unreliable.

### What this means for our AI candidates

- The high DiffDock scores for (S,S)-H-1152 and genmol_119 may reflect **structural complementarity to this specific PDB conformation** rather than true binding superiority over clinical compounds.
- **Do NOT claim our AI candidates are better than Phase 1 drugs.** LX-7101 has pChEMBL 8.8 (~1.6 nM) validated in biochemical assays. DiffDock cannot replicate that measurement.
- The comparison is useful for **relative ranking within the same scaffold class** but not for cross-scaffold comparisons against structurally different real drugs.

### Honest assessment

| Metric | Our AI candidates | Real drugs |
|--------|-------------------|------------|
| DiffDock confidence | High (+0.7 to +0.96) | Low (-0.09 to -1.96) |
| Biochemical IC50 | **Unknown (not tested)** | nM range (validated) |
| In vivo efficacy | **Unknown** | LX-7101: Phase 1; MDI-114215: mouse brain PD |
| Clinical status | Computational only | LX-7101 in human trials |

## Recommendations

1. **Do not over-interpret**: DiffDock is a pose prediction tool, not a binding affinity predictor. High confidence = good geometric fit, not necessarily strong binding.
2. **Next step**: Run FEP (Free Energy Perturbation) or MM-GBSA rescoring to get energy-based binding estimates that are more comparable across scaffolds.
3. **Wet-lab validation needed**: The only way to know if (S,S)-H-1152 truly competes with LX-7101 is a biochemical LIMK2 kinase assay (IC50 determination).
4. **Use benchmarks for calibration**: The fact that known nM inhibitors score negative in DiffDock means our positive-scoring compounds need independent validation before making any efficacy claims.

## Data Files

- Raw results: `data/docking/real_limk_benchmarks_2026-03-25.json`
- Script: `scripts/dock_real_limk_benchmarks.py`
- Previous campaigns: `data/docking/stereoisomer_panel_2026-03-24.json`, `data/docking/limk2_rock2_campaign_2026-03-24.json`

## References

- LX-7101: ChEMBL CHEMBL3356433, Lexicon Pharmaceuticals
- MDI-114215: Baldwin et al., "Discovery of MDI-114215: A Potent and Selective LIMK Inhibitor To Treat Fragile X Syndrome", J Med Chem (2024). DOI: 10.1021/acs.jmedchem.4c02694
- BMS-5: Bristol-Myers Squibb, known LIMK1/2 dual inhibitor
- DiffDock v2.2: Corso et al., NVIDIA NIM cloud API
