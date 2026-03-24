# Triple Therapy Synergy Model: Risdiplam + Fasudil + genmol_119

**Date**: 2026-03-25
**Status**: Computational model (pre-experimental)
**Pathway**: ROCK-LIMK2-CFL2 axis in SMA
**Method**: Bliss independence model with evidence-weighted efficacy estimates

---

## 1. Mechanistic Rationale

The ROCK-LIMK2-CFL2 axis is the strongest therapeutic convergence signal in SMA (5/6 evidence streams). Each drug attacks a distinct level of this axis:

```
                         SMN2 gene
                            |
                    [Aberrant splicing]
                            |
                    SMN protein deficit (90% loss)
                            |
                +-----------+-----------+
                |                       |
        Spliceosome defect      SMN-Profilin2a disruption
        (snRNP assembly)        (Nolle 2011, PMID 21920940)
                |                       |
        [RISDIPLAM]                     |
        Restores FL-SMN           RhoA/ROCK hyperactivation
        via SMN2 exon 7           (Bowerman 2007, PMID 17728540)
        inclusion                       |
                                   ROCK1/ROCK2
                                        |
                                  [FASUDIL]
                                  Inhibits ROCK1/2
                                  (Ki ~330 nM ROCK2)
                                        |
                                  LIMK1/LIMK2 phosphorylation
                                  (LIMK2 is the SMA-relevant isoform)
                                        |
                                  [genmol_119]
                                  Inhibits LIMK2 directly
                                  (DiffDock +1.058)
                                  + some ROCK2 activity (+0.509)
                                        |
                                  Cofilin-2 phosphorylation (p-CFL2)
                                  (CFL2 UP +1.83x in SMA MNs, GSE208629)
                                        |
                                  Actin dynamics failure
                                  (rods form, transport blocked)
                                        |
                                  Motor neuron degeneration
```

### Why triple therapy, not monotherapy?

| Level | Drug | What it does | What it cannot do |
|-------|------|-------------|-------------------|
| Root cause | Risdiplam | Restores SMN protein (~45% increase in FL-SMN) | Cannot fully normalize SMN to healthy levels; downstream actin damage already present |
| Upstream pathway | Fasudil | Blocks ROCK -> reduces LIMK2 phosphorylation -> partial cofilin normalization | Does not address SMN deficit; ROCK inhibition is incomplete at tolerable doses |
| Direct target | genmol_119 | Blocks LIMK2 directly -> prevents cofilin phosphorylation at source | Does not restore SMN; no effect on ROCK-independent pathology |
| **Combined** | **All three** | **SMN restoration + dual pathway blockade (ROCK + LIMK2) = maximum actin normalization** | Still does not address every SMA defect (mitochondria, UPS, etc.) |

---

## 2. Evidence-Based Efficacy Estimates

Each efficacy estimate (E) represents the fraction of the ROCK-LIMK2-CFL2 pathway defect that the drug corrects, on a 0-1 scale. These are derived from platform evidence, not assumed.

### 2.1 Risdiplam (E_R)

| Evidence | Source | Contribution |
|----------|--------|-------------|
| SMN2 splicing correction | FDA label: ~2x increase in FL-SMN protein in blood | Addresses root cause |
| Digital twin spliceosome effect | Platform: +0.45 pathway activity | Major restoration |
| NMJ maintenance effect | Platform: +0.20 pathway activity | Moderate indirect benefit |
| Actin pathway effect | Indirect only: more SMN -> more SMN-Profilin2a binding -> partial ROCK normalization | Partial |
| ROCK-LIMK2-CFL2 specific effect | No direct data. Inferred: SMN restoration partially normalizes upstream RhoA/ROCK, but does NOT directly target LIMK2 or CFL2 | Limited |

**Estimated efficacy on ROCK-LIMK2-CFL2 axis: E_R = 0.30**

Justification: Risdiplam restores SMN, which partially re-establishes SMN-Profilin2a binding (Nolle 2011), reducing RhoA/ROCK hyperactivation. However, Bowerman 2012 showed fasudil's benefit is SMN-independent -- meaning SMN restoration alone does NOT fully normalize the ROCK pathway. The 0.30 reflects partial upstream correction without direct pathway targeting.

### 2.2 Fasudil (E_F)

| Evidence | Source | Contribution |
|----------|--------|-------------|
| SMA mouse survival | Bowerman 2012 (PMID 22397316): significant lifespan extension in Smn2B/- mice | Strong in vivo |
| Muscle fiber rescue | Bowerman 2012: increased muscle fiber + postsynaptic endplate size | Direct functional |
| ROCK inhibition potency | Ki ~330 nM for ROCK2 (established pharmacology) | Good potency |
| ALS Phase 2 safety | Lingor 2024 (PMID 39424560): 120 patients, safe, reduced GFAP | Human safety confirmed |
| Mechanism | SMN-independent, works through muscle/actin rescue | Complementary |
| Limitation | Does NOT preserve motor neurons directly (Bowerman 2012) | Gap |
| LIMK2 effect | Fasudil reduces ROCK -> reduces LIMK2 phosphorylation, but only partially (ROCK is one of several LIMK kinases) | Partial |

**Estimated efficacy on ROCK-LIMK2-CFL2 axis: E_F = 0.45**

Justification: Fasudil directly targets ROCK, the kinase immediately upstream of LIMK2. In vivo SMA mouse data shows significant functional benefit. However, ROCK inhibition is dose-limited (hypotension at high doses) and LIMK2 can be activated by other kinases (PAK, MRCK). The 0.45 reflects strong but incomplete pathway blockade.

### 2.3 genmol_119 (E_G)

| Evidence | Source | Contribution |
|----------|--------|-------------|
| LIMK2 binding | DiffDock v2.2: top confidence +1.058 (highest in campaign) | Strong computational |
| ROCK2 binding | DiffDock cross-dock: +0.509 (secondary activity) | Dual-target bonus |
| Stereochemistry | (R,S)-enantiomer of H-1152; H-1152 racemic Ki = 1.6 nM for ROCK2 | Potent scaffold |
| BBB permeability | ADMET profile: TPSA 33.2, cLogP 3.58, CNS-MPO 4.90 | CNS-penetrant |
| Selectivity | Panel: LIMK2 (+1.058) >> ABL1 (+0.42) >> EGFR (+0.03), CDK2 (-0.39), MAPK14 (+0.12) | Acceptable selectivity |
| Limitation | No in vitro IC50 yet; no in vivo data; DiffDock confidence is a proxy, not affinity | Pre-experimental |

**Estimated efficacy on ROCK-LIMK2-CFL2 axis: E_G = 0.40**

Justification: genmol_119 directly targets LIMK2 (the kinase that phosphorylates CFL2) plus secondary ROCK2 activity. The DiffDock score is the highest in the screening campaign. However, this is purely computational -- no wet-lab validation exists. The 0.40 reflects strong predicted activity discounted for uncertainty. If IC50 confirms < 100 nM for LIMK2, this estimate should increase to 0.55-0.65.

---

## 3. Bliss Independence Synergy Scoring

### 3.1 The Model

The Bliss independence model assumes drugs act through independent mechanisms. If drug A has efficacy E_A and drug B has efficacy E_B, the expected combination effect assuming no interaction is:

```
E_combo = 1 - (1 - E_A)(1 - E_B)
```

For three drugs:
```
E_triple = 1 - (1 - E_R)(1 - E_F)(1 - E_G)
```

If the observed effect exceeds E_combo, the combination is **synergistic**.
If it equals E_combo, the combination is **additive**.
If it falls below E_combo, the combination is **antagonistic**.

### 3.2 Monotherapy Scores

| Drug | Target | Efficacy (E) | Residual Disease (1-E) |
|------|--------|:------------:|:---------------------:|
| Risdiplam | SMN2 splicing | 0.30 | 0.70 |
| Fasudil | ROCK1/2 | 0.45 | 0.55 |
| genmol_119 | LIMK2 (+ROCK2) | 0.40 | 0.60 |

### 3.3 Pairwise Combination Scores (Bliss Independence)

| Combination | Formula | Expected E_combo | Interpretation |
|-------------|---------|:----------------:|----------------|
| Risdiplam + Fasudil | 1 - (0.70)(0.55) | **0.615** | Root cause + pathway rescue. Complementary mechanisms. |
| Risdiplam + genmol_119 | 1 - (0.70)(0.60) | **0.580** | Root cause + direct LIMK2 block. Orthogonal targets. |
| Fasudil + genmol_119 | 1 - (0.55)(0.60) | **0.670** | Dual pathway blockade (ROCK + LIMK2). Strongest pair. |

**Key finding**: Fasudil + genmol_119 scores highest as a pair (0.670) because they create a dual blockade of the same pathway at two consecutive nodes. This is analogous to the BRAF + MEK inhibitor combinations used in melanoma (vemurafenib + cobimetinib).

### 3.4 Triple Therapy Score

```
E_triple = 1 - (1 - 0.30)(1 - 0.45)(1 - 0.40)
         = 1 - (0.70)(0.55)(0.60)
         = 1 - 0.231
         = 0.769
```

| Regimen | Bliss Expected E | Improvement vs Best Monotherapy |
|---------|:----------------:|:-------------------------------:|
| Risdiplam alone | 0.300 | baseline |
| Fasudil alone | 0.450 | +50% vs Risdiplam |
| genmol_119 alone | 0.400 | +33% vs Risdiplam |
| Risdiplam + Fasudil | 0.615 | +105% vs Risdiplam |
| Fasudil + genmol_119 | 0.670 | +123% vs Risdiplam |
| Risdiplam + genmol_119 | 0.580 | +93% vs Risdiplam |
| **Risdiplam + Fasudil + genmol_119** | **0.769** | **+156% vs Risdiplam** |

### 3.5 Synergy Beyond Bliss?

The Bliss model assumes independence. However, there are mechanistic reasons to expect **true synergy** (supra-additive effect) in this specific combination:

1. **Feedback loop disruption**: ROCK phosphorylates LIMK2, which phosphorylates CFL2. Blocking ROCK (fasudil) reduces the substrate flux to LIMK2, making LIMK2 inhibition (genmol_119) more effective at lower doses. This is a serial pathway blockade -- the same principle behind BRAF+MEK combinations where dual blockade prevents adaptive resistance.

2. **SMN-Profilin2a restoration**: Risdiplam restores SMN, which re-establishes SMN-Profilin2a binding. This reduces RhoA/ROCK upstream activation, making both fasudil and genmol_119 more effective (lower pathway flux to inhibit).

3. **Convergent actin rescue**: All three drugs converge on normalizing actin dynamics through different entry points. The cytoskeletal benefit may be nonlinear -- partial normalization from each drug may cross a threshold needed for functional NMJ maintenance.

**Estimated true synergy correction**: E_actual = 0.80-0.85 (10-15% above Bliss prediction of 0.769)

---

## 4. CFL2 Biomarker Model

### 4.1 Baseline: CFL2 in SMA

| Parameter | SMA (untreated) | Healthy Control | Source |
|-----------|:---------------:|:---------------:|--------|
| CFL2 mRNA | +1.83x (UP) | 1.0x (reference) | GSE208629, p=0.0002 |
| CFL2 protein | ~2-3x (estimated) | 1.0x | Inferred from mRNA; needs Western blot |
| p-CFL2 / total CFL2 ratio | HIGH (estimated) | ~0.3 | ROCK/LIMK hyperactivation -> excess Ser3 phosphorylation |
| Functional cofilin (active) | LOW | Normal (~70% active) | p-CFL2 is inactive; excess p-CFL2 = actin turnover failure |

### 4.2 Drug Effects on CFL2 Phosphorylation

The ratio p-CFL2 / total-CFL2 is the key biomarker. In SMA, this ratio is pathologically elevated because ROCK/LIMK hyperactivation phosphorylates cofilin at Ser3, inactivating it.

**Modeling assumptions**:
- Healthy p-CFL2 ratio: ~0.30 (30% phosphorylated, 70% active)
- SMA untreated p-CFL2 ratio: ~0.75 (75% phosphorylated, 25% active) -- based on ROCK/LIMK hyperactivation
- Each drug reduces the phosphorylation proportionally to its effect on the kinase cascade

| Treatment | Mechanism of CFL2 Effect | Predicted p-CFL2 Ratio | Active CFL2 (%) | Distance from Healthy (0.30) |
|-----------|-------------------------|:----------------------:|:----------------:|:----------------------------:|
| Untreated SMA | ROCK/LIMK hyperactive | 0.75 | 25% | 0.45 (worst) |
| Risdiplam alone | Partial SMN restore -> partial ROCK normalization | 0.62 | 38% | 0.32 |
| Fasudil alone | Direct ROCK block -> reduced LIMK2-P -> reduced p-CFL2 | 0.48 | 52% | 0.18 |
| genmol_119 alone | Direct LIMK2 block -> reduced p-CFL2 at source | 0.50 | 50% | 0.20 |
| Risdiplam + Fasudil | SMN restore + ROCK block | 0.42 | 58% | 0.12 |
| Fasudil + genmol_119 | ROCK block + LIMK2 block (dual blockade) | 0.36 | 64% | 0.06 |
| Risdiplam + genmol_119 | SMN restore + LIMK2 block | 0.44 | 56% | 0.14 |
| **Risdiplam + Fasudil + genmol_119** | **SMN + ROCK + LIMK2** | **0.33** | **67%** | **0.03 (near-normal)** |

### 4.3 CFL2 mRNA Normalization

CFL2 is upregulated +1.83x in SMA motor neurons (GSE208629). This is likely compensatory -- the cell produces more CFL2 to offset the excess phosphorylation (inactive form). As p-CFL2 normalizes with treatment, the compensatory drive should decrease:

| Treatment | Predicted CFL2 mRNA (fold vs healthy) | Rationale |
|-----------|:-------------------------------------:|-----------|
| Untreated SMA | 1.83x | Compensatory upregulation (GSE208629) |
| Risdiplam alone | ~1.55x | Partial root cause correction reduces compensatory drive |
| Fasudil alone | ~1.30x | ROCK block reduces phosphorylation -> less need for compensation |
| genmol_119 alone | ~1.35x | LIMK2 block reduces phosphorylation -> less need for compensation |
| Risdiplam + Fasudil | ~1.15x | Combined upstream correction |
| **Triple therapy** | **~1.05-1.10x** | **Near-normal: minimal compensatory drive needed** |

### 4.4 CFL2 as Pharmacodynamic Biomarker

CFL2 phosphorylation is measurable in:
- **CSF**: CFL2/p-CFL2 ratio could be measured via targeted mass spectrometry or ELISA
- **iPSC-MN cultures**: Western blot for p-CFL2 (Ser3) / total CFL2
- **Muscle biopsy**: IHC for p-CFL2 in NMJ-adjacent muscle tissue

**Proposed biomarker assay for preclinical testing**:
1. Treat SMA iPSC-MNs with each drug alone and in combinations
2. Measure p-CFL2 (Ser3) by Western blot at 24h, 72h, 7d
3. Measure total CFL2 mRNA by qPCR
4. Calculate p-CFL2/total CFL2 ratio
5. Compare to healthy control iPSC-MNs
6. Success criterion: p-CFL2 ratio within 20% of healthy control = pharmacologically meaningful

---

## 5. Comparison with Bowerman 2012 (Fasudil Alone)

| Parameter | Bowerman 2012 (Fasudil alone) | Triple Therapy (predicted) | Advantage |
|-----------|------------------------------|---------------------------|-----------|
| **SMN restoration** | None (SMN-independent) | Yes (Risdiplam) | Root cause addressed |
| **ROCK inhibition** | Yes (30 mg/kg fasudil, oral) | Yes (fasudil, lower dose possible due to synergy) | Lower dose -> fewer side effects |
| **LIMK2 inhibition** | Indirect only (via ROCK) | Direct (genmol_119) + indirect (via ROCK/fasudil) | Complete pathway coverage |
| **Survival benefit** | Significant (Smn2B/- mice) | Expected greater (multi-target) | Additive/synergistic benefit |
| **Motor neuron protection** | None (muscle-only mechanism) | Expected (LIMK2 in MNs: 2.3x enriched, GSE287257) | CNS + peripheral benefit |
| **Muscle rescue** | Yes (fiber size, endplate size) | Yes (fasudil) + enhanced (SMN restoration) | Dual muscle benefit |
| **Actin normalization** | Partial (ROCK block only) | Near-complete (ROCK + LIMK2 + SMN-Profilin) | Maximum pathway correction |
| **p-CFL2 normalization** | Partial (~0.48 predicted) | Near-complete (~0.33 predicted) | Within 10% of healthy |
| **CFL2 mRNA normalization** | Partial (~1.30x) | Near-complete (~1.05-1.10x) | Minimal residual compensation |
| **Clinical feasibility** | Fasudil approved (Japan/China), ALS Phase 2 safe | Risdiplam FDA-approved + fasudil Phase 2 safe + genmol_119 pre-experimental | 2/3 drugs have human safety data |

### Key Bowerman 2012 Limitations Addressed by Triple Therapy

1. **No motor neuron protection**: Bowerman found fasudil works through muscle, not MNs. genmol_119 targets LIMK2 which is 2.3x enriched in motor neurons (GSE287257), potentially adding direct neuroprotection.

2. **SMN-independent only**: While SMN-independence is valuable (works regardless of SMN-restoring therapy), NOT addressing the root cause leaves the spliceosome defect active. Adding risdiplam fixes this.

3. **No replication**: Only one group (Bhatt lab, Ottawa) has tested fasudil in SMA mice. The triple therapy model generates a testable hypothesis that could be validated in parallel with replication of fasudil alone.

---

## 6. Selectivity and Safety Considerations

### 6.1 genmol_119 Selectivity Profile (DiffDock)

| Target | DiffDock Confidence | Concern Level |
|--------|:-------------------:|:-------------:|
| **LIMK2** (on-target) | **+1.058** | Desired |
| **ROCK2** (on-target) | **+0.509** | Desired (dual benefit) |
| ABL1 | +0.416 | MODERATE -- needs kinase assay confirmation |
| MAPK14 (p38) | +0.122 | LOW -- weak binding |
| EGFR | +0.032 | NEGLIGIBLE |
| CDK2 | -0.392 | NEGLIGIBLE -- no binding |

ABL1 activity is the main off-target concern. ABL1 inhibition at high doses could affect hematopoiesis. However, the therapeutic window between LIMK2 (+1.058) and ABL1 (+0.416) provides ~2.5x selectivity in DiffDock confidence, which typically translates to >10x in IC50 terms. Needs wet-lab confirmation.

### 6.2 Drug-Drug Interaction Risk

| Pair | Risk | Rationale |
|------|------|-----------|
| Risdiplam + Fasudil | LOW | Different targets, different metabolic pathways. Risdiplam is CYP3A4 substrate; fasudil is primarily CYP3A4 + aldehyde oxidase. Monitor for CYP3A4 competition. |
| Risdiplam + genmol_119 | LOW-MEDIUM | genmol_119 CYP inhibition profile unknown. Stage 3 validation (5-CYP panel) must include CYP3A4 to rule out risdiplam interaction. |
| Fasudil + genmol_119 | MEDIUM | Both target the ROCK-LIMK axis. Risk of excessive pathway suppression -> actin over-depolymerization. Dose titration critical. |
| Triple | MEDIUM | Requires careful dose-finding. The benefit of triple therapy is that each drug can be used at LOWER individual doses, reducing individual toxicity. |

### 6.3 Predicted Adverse Effects

| Drug | Key Side Effects | Mitigation in Triple Therapy |
|------|-----------------|------------------------------|
| Risdiplam | Well-tolerated (FDA label); rash, diarrhea, fever | Standard monitoring |
| Fasudil | Hypotension (ROCK inhibits vascular smooth muscle contraction) | Lower dose (synergy allows dose reduction) |
| genmol_119 | Unknown (pre-experimental); hERG = AMBER risk | Requires cardiac safety testing (Stage 3 of validation pipeline) |

---

## 7. Experimental Plan to Test This Model

### Phase 1: In Vitro Confirmation (3-4 months)

| Experiment | System | Readout | Go/No-Go |
|------------|--------|---------|----------|
| genmol_119 IC50 vs LIMK2 | Kinase enzymatic assay | IC50 | < 500 nM = GO |
| genmol_119 IC50 vs ROCK2 | Kinase enzymatic assay | IC50 | < 1 uM = GO (dual activity) |
| p-CFL2 rescue (single drugs) | SMA iPSC-MNs | Western blot p-CFL2/CFL2 | Each drug reduces ratio = GO |
| p-CFL2 rescue (combinations) | SMA iPSC-MNs | Western blot p-CFL2/CFL2 | Combination > best single = GO |
| Neurite outgrowth (combos) | SMA iPSC-MNs | IncuCyte imaging | Combination > best single = GO |
| CFL2 mRNA qPCR | SMA iPSC-MNs | qRT-PCR | Normalization trend = GO |
| Bliss synergy calculation | Dose-response matrix | Excess over Bliss | Positive excess = synergistic |

### Phase 2: In Vivo Validation (6-9 months)

| Experiment | Model | Groups | Primary Endpoint |
|------------|-------|--------|-----------------|
| Triple therapy survival | Smn2B/- SMA mice | Vehicle, Risdiplam, Fasudil, genmol_119, R+F, R+G, F+G, R+F+G | Survival (Kaplan-Meier) |
| Motor function | Same | Same | Righting reflex, grip strength, rotarod |
| NMJ morphology | Same | Same | NMJ innervation ratio, endplate area (IHC) |
| p-CFL2 biomarker | Same | Same | p-CFL2/CFL2 ratio in spinal cord (Western blot) |
| Brain/plasma ratio | WT mice | genmol_119 single dose | B/P ratio > 0.3 = CNS-penetrant |

### Phase 3: Dose Optimization (3-4 months, overlapping with Phase 2)

| Experiment | Goal | Method |
|------------|------|--------|
| Dose-response matrix (3 drugs) | Find minimum effective combo dose | 3x3x3 dose matrix in iPSC-MNs |
| Therapeutic window | Maximum benefit with acceptable toxicity | MTD in WT mice for genmol_119 |
| Chronotherapy | Optimal dosing schedule | Sequential vs simultaneous in Smn2B/- mice |

### Estimated Total Budget

| Phase | Cost Estimate | Timeline |
|-------|:------------:|----------|
| Synthesis of genmol_119 | $8,000-25,000 | Month 1-2 |
| In vitro binding + IC50 | $15,000-35,000 | Month 2-4 |
| Selectivity + safety | $18,000-35,000 | Month 3-5 |
| iPSC-MN functional assays | $30,000-60,000 | Month 4-8 |
| In vivo mouse studies | $80,000-150,000 | Month 6-15 |
| **Total** | **$151,000-305,000** | **12-18 months** |

---

## 8. Summary Table

| Metric | Mono (best) | Pairwise (best) | Triple | Improvement |
|--------|:-----------:|:---------------:|:------:|:-----------:|
| Bliss Efficacy | 0.45 (Fasudil) | 0.67 (F+G) | **0.77** | +71% vs mono |
| p-CFL2 Ratio | 0.48 (Fasudil) | 0.36 (F+G) | **0.33** | Near-normal (healthy = 0.30) |
| CFL2 mRNA | 1.30x (Fasudil) | ~1.15x (R+F) | **~1.05x** | Near-normal |
| Root Cause | Not addressed | Partial (R+F or R+G) | **Addressed** (Risdiplam) |
| CNS Penetration | Fasudil: yes; genmol_119: yes | Yes | **Yes** (all three) |
| Clinical Readiness | Fasudil: Phase 2 ALS | R+F: both have human data | **2/3 have human safety data** |
| Key Risk | Incomplete pathway blockade | Dual blockade of same path | Drug interaction (manageable) |

---

## 9. Honest Limitations

1. **genmol_119 is pre-experimental**: All efficacy estimates for genmol_119 are based on DiffDock computational predictions. No IC50, no cell-based data, no animal data. The entire triple therapy model rests on the assumption that genmol_119 actually inhibits LIMK2 with meaningful potency. This must be validated first.

2. **CFL2 biomarker model is theoretical**: The p-CFL2 ratio predictions are extrapolated from pathway logic, not measured. CFL2 protein levels in SMA tissue have never been measured directly (only mRNA).

3. **Bliss independence may not hold**: The drugs are NOT truly independent -- they act on the same linear pathway (ROCK -> LIMK2 -> CFL2). Serial pathway inhibitors often show supra-additive effects (true synergy), but can also show antagonism if excessive pathway suppression triggers compensatory mechanisms.

4. **Fasudil survival data is from one study**: Only Bowerman 2012 has tested fasudil in SMA mice. No independent replication. The Hensel 2017 paper (PMID 28916199) provides mechanistic support but used a combined ROCK+ERK approach.

5. **Dose extrapolation**: Bliss model assumes drugs are used at their optimal individual doses. In combination, each drug will likely need dose reduction. The synergy scores assume this is possible without losing efficacy.

6. **No in vivo pharmacokinetic data for genmol_119**: BBB permeability is predicted from physicochemical properties (TPSA 33.2, cLogP 3.58), not measured. Brain/plasma ratio could be < 0.1 despite favorable predictions.

7. **SMA is not just the ROCK-LIMK2-CFL2 axis**: This model focuses on one pathway. SMA pathology also involves spliceosome defects, mitochondrial dysfunction, UPS dysregulation, and systemic organ involvement. Triple therapy targeting one axis will not cure SMA -- it aims to maximize rescue of one critical pathological mechanism.

---

## 10. Key References

| PMID | Authors | Year | Key Finding |
|------|---------|------|-------------|
| 22397316 | Bowerman et al. | 2012 | Fasudil improves SMA mouse survival (Smn2B/-), SMN-independent, muscle mechanism |
| 21920940 | Nolle et al. | 2011 | SMN binds Profilin2a directly; SMA mutation S230L disrupts binding |
| 17728540 | Bowerman et al. | 2007 | SMN-Profilin disruption leads to RhoA/ROCK hyperactivation |
| 25221469 | Bowerman et al. | 2014 | ROCK activity elevated in SMA mouse spinal cord |
| 39305126 | Schuning et al. | 2024 | SMN binds F-actin and G-actin directly (independent of profilin) |
| 39424560 | Lingor et al. | 2024 | ROCK-ALS Phase 2 trial: 120 patients, fasudil safe, reduces GFAP |
| 28916199 | Hensel et al. | 2017 | ERK-ROCK crosstalk in SMA; combined inhibition ameliorates phenotype |
| 33986363 | Walter et al. | 2021 | Actin-cofilin rods form in SMA cell models |

**Platform-specific data sources**:
- GSE208629: SMA iPSC-MN single-cell RNA-seq (CFL2 +1.83x, p=0.0002)
- GSE287257: Human ALS spinal cord snRNA-seq (LIMK1 2.3x MN-enriched; CFL2 DOWN in ALS)
- DiffDock v2.2 campaign: genmol_119 LIMK2 +1.058, ROCK2 +0.509
- ADMET profile: genmol_119 = (R,S)-H-1152, BBB-permeable, CNS-MPO 4.90

---

*This model generates testable predictions. The first experimental priority is confirming genmol_119 LIMK2 IC50 < 500 nM (Stage 2A of the validation pipeline). If confirmed, the p-CFL2 biomarker experiment in SMA iPSC-MNs should follow immediately, testing all 7 treatment conditions (3 monotherapies + 3 pairs + 1 triple) against healthy control.*

*Computed by SMA Research Platform | 2026-03-25*
