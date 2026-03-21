# Fasudil + BDNF Synergy Experiment — Extended Protocol
# Can exercise-mimetic signaling enhance ROCK inhibition in SMA motor neurons?

> **Extension of**: fasudil-sma-experiment-proposal.md
> **Budget**: ~$15K total (includes base Fasudil experiment)
> **Timeline**: 10-14 weeks
> **Statistical design**: 2×2 factorial with Bliss Independence synergy analysis

---

## Rationale

The "Translational Desert" hypothesis predicts that actin-cofilin rods block mRNA
transport to the NMJ. Two interventions could clear these rods:

1. **Fasudil** (ROCK inhibitor) — directly reduces cofilin phosphorylation
2. **Exercise** — promotes actin turnover, increases BDNF (neurotrophic support)

In cell culture, exercise cannot be directly applied. **BDNF treatment** is the
most neuron-relevant exercise mimetic because:
- Exercise increases BDNF in humans (well-established)
- BDNF promotes neurite outgrowth and synaptic plasticity
- BDNF affects actin dynamics through TrkB → Rac1 → cofilin pathway
- BDNF is directly relevant to motor neuron survival

## Experimental Groups (2×2 Factorial)

| Group | Fasudil | BDNF | N | Purpose |
|-------|---------|------|---|---------|
| 1. Control | — | — | 10 | Baseline SMA phenotype |
| 2. Fasudil only | 10 µM | — | 10 | ROCK inhibition alone |
| 3. BDNF only | — | 50 ng/mL | 10 | Exercise-mimetic alone |
| 4. Fasudil + BDNF | 10 µM | 50 ng/mL | 10 | Combination / synergy test |

**Total**: 40 wells (can fit on 2× 24-well plates)
**Treatment duration**: 72 hours
**Positive control**: Y-27632 10 µM (additional 10 wells)

## Primary Readouts

| Readout | Method | Synergy criterion |
|---------|--------|-------------------|
| Phospho-cofilin ratio | Western blot | Combo > sum of individual effects |
| Actin rod count/cell | Phalloidin + cofilin ICC, confocal | Combo reduces rods beyond additivity |
| TDP-43 nuclear ratio | TDP-43 ICC, confocal | Combo improves nuclear retention |
| Motor neuron survival | MTT assay | Combo survival > additive prediction |
| Neurite outgrowth | Phase contrast + image analysis | Combo length > additive prediction |

## Synergy Analysis: Bliss Independence Model

For each readout, calculate:
- E_fasudil = effect of Fasudil alone (normalized to control)
- E_bdnf = effect of BDNF alone (normalized to control)
- E_expected = E_fasudil + E_bdnf - (E_fasudil × E_bdnf)  [Bliss Independence]
- E_observed = actual combination effect

**If E_observed > E_expected → SYNERGY**
**If E_observed ≈ E_expected → ADDITIVE**
**If E_observed < E_expected → ANTAGONISM**

## Statistical Analysis

- **Two-way ANOVA**: Fasudil × BDNF interaction term
  - Significant interaction (p < 0.05) → non-additive effect
- **Post-hoc**: Tukey's HSD for pairwise comparisons
- **Effect size**: Cohen's d for each comparison
- **Power**: 10 replicates provides 80% power for medium effect (d=0.5)

## Timeline

| Week | Activity |
|------|----------|
| 1-3 | iPSC expansion + MN differentiation start |
| 4-6 | MN differentiation complete, QC (HB9/ISL1 >80%) |
| 7 | Plate 2×24-well plates, begin treatment (72h) |
| 8 | Harvest: Western blot (p-cofilin), fix cells for ICC |
| 9 | Confocal imaging: actin rods + TDP-43 |
| 10 | Image analysis + MTT on parallel plates |
| 11-12 | Data analysis, statistics, figure preparation |
| 13-14 | Write-up, interpretation |

## Cost Breakdown

| Item | Cost |
|------|------|
| iPSC lines (from base experiment) | $0 (already purchased) |
| BDNF (50 ng/mL, PeproTech) | ~$200 |
| Additional antibodies (TrkB, p-Rac1) | ~$600 |
| Extra plates + consumables | ~$300 |
| Extended confocal time | ~$500 |
| **Incremental cost over base experiment** | **~$1,600** |
| **Total with base experiment** | **~$8-12K** |

## Why This Matters

If Fasudil + BDNF shows synergy:
1. Supports exercise + ROCK inhibitor as combination for SMA
2. Provides mechanistic rationale for exercise + drug trials
3. Two intervention points on same pathway (upstream BDNF + downstream ROCK)
4. Publishable regardless of outcome (synergy, additive, or antagonism all informative)

## Go/No-Go from Base Experiment

This synergy experiment should ONLY proceed if the base Fasudil experiment (Phase 1)
shows p-cofilin reduction >30%. If Fasudil doesn't reduce p-cofilin, there's no
rationale for testing synergy.
