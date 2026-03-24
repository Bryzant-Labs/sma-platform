# Proprioceptive Pathway Hypothesis Cards

**Date**: 2026-03-24
**Context**: Prepared for Simon meeting (week of March 30, 2026)
**Status**: Draft -- to be refined with Simon's input before database entry

---

## Hypothesis 1: ROCK/LIMK Pathway Inhibition Rescues Proprioceptive Synapse Maintenance in SMA

### Biological Rationale
Proprioceptive Ia synapses on motor neurons are lost early in SMA, before motor neuron death (Mentis et al., 2011, PMID 21315257; Simon et al., 2025, PMID 39982868). The ROCK-LIMK-cofilin axis regulates presynaptic actin dynamics critical for synaptic vesicle cycling and postsynaptic receptor clustering. ROCK pathway activation is documented in SMA motor neurons (Nolle et al., 2011, PMID 21920940), and fasudil (ROCK inhibitor) improves NMJ postsynaptic endplate size in SMA mice (Bowerman et al., 2012, PMID 22397316), but its effect on proprioceptive synapses has never been tested.

### Testable Prediction
Treatment with fasudil will increase the number of VGLUT1+ proprioceptive synaptic boutons on motor neuron somata and dendrites in SMA mice, and will improve H-reflex amplitude.

### Feasible Assay / Experiment
1. Treat SMN-delta-7 or Smn2B/- mice with fasudil (30 mg/kg/day IP, from P1) vs. vehicle
2. At P10-P14, quantify VGLUT1+ synaptic boutons on ChAT+ motor neurons in L1 and L5 segments by confocal immunohistochemistry
3. Measure H-reflex amplitude and latency at P10-P14 (electrophysiology)
4. Quantify phospho-cofilin (Ser3) levels in spinal cord by Western blot

### Model System
SMN-delta-7 mouse (to match Bowerman 2012 fasudil data) AND Smn2B/- mouse (to match Simon lab expertise)

### Readouts
- Primary: VGLUT1+ bouton count per motor neuron (L1 vs. L5)
- Secondary: H-reflex amplitude (mV)
- Mechanistic: phospho-cofilin/total cofilin ratio in spinal cord
- Functional: righting reflex time, grip strength

### Go/No-Go Criteria
- GO: Fasudil increases VGLUT1+ bouton count by >=20% AND improves H-reflex amplitude by >=15% in at least one spinal segment
- NO-GO: No change in VGLUT1+ bouton count despite confirmed ROCK inhibition (reduced p-cofilin)
- PIVOT: If H-reflex improves but bouton count does not change, the effect may be on synaptic function (glutamate release) rather than synapse number -- redesign with paired-pulse facilitation electrophysiology

### Estimated Cost
EUR 15,000-25,000 (mouse cohorts, IHC reagents, electrophysiology time). Lower if Simon lab has existing tissue.

### Evidence Tier
**B** -- Strong mechanistic rationale from convergent evidence (ROCK activation in SMA + proprioceptive synapse loss + fasudil preclinical efficacy), but the specific connection between ROCK inhibition and proprioceptive synapses has not been tested. Upgradeable to A upon positive result.

---

## Hypothesis 2: Actin-Cofilin Rod Formation Occurs Preferentially in Vulnerable (L1) Motor Neurons

### Biological Rationale
Actin-cofilin rods form in SMA neuronal cultures through a ROCK/profilin2-dependent mechanism (Walter et al., 2021, PMID 33986363). Motor neurons innervating proximal muscles (L1 spinal segment) are selectively vulnerable in SMA, while those innervating distal muscles (L5) are relatively resistant (Murray et al., 2013, PMID 24324819). If actin-cofilin rods contribute to motor neuron dysfunction by disrupting axonal transport and depleting the actin pool, they should be more abundant in vulnerable motor neurons. CFL2 is 2.9x upregulated in SMA motor neurons (GSE69175), but nobody has examined whether this upregulation differs between vulnerable and resistant motor neuron pools.

### Testable Prediction
Actin-cofilin rods (detected by cofilin/actin co-staining) will be more abundant in L1 motor neurons than in L5 motor neurons in SMA mice at pre-symptomatic stages (P5-P7). CFL2 immunoreactivity will be higher in L1 than L5 motor neurons.

### Feasible Assay / Experiment
1. Harvest spinal cords from SMN-delta-7 mice at P5, P7, P10, and P14 (n=4-6 per timepoint)
2. Prepare 20-um cryosections at L1 and L5 levels
3. Triple immunostaining: ChAT (motor neuron marker), CFL2 or phospho-cofilin (Ser3), phalloidin (F-actin)
4. Confocal imaging: quantify rod-like structures (elongated cofilin/actin co-positive aggregates) per motor neuron
5. Compare L1 vs. L5 at each timepoint
6. Optional: co-stain with VGLUT1 to correlate rod burden with proprioceptive synapse loss

### Model System
SMN-delta-7 mouse (standard severe SMA model). Age-matched wild-type controls required.

### Readouts
- Primary: Number and size of actin-cofilin rods per motor neuron at L1 vs. L5
- Secondary: CFL2 immunofluorescence intensity (L1 vs. L5)
- Tertiary: Correlation between rod burden and VGLUT1+ bouton count (within-animal, within-section)

### Go/No-Go Criteria
- GO: Rod density is >=2-fold higher in L1 than L5 motor neurons at any timepoint, AND rod formation precedes or coincides with VGLUT1 synapse loss
- NO-GO: No rods detected in spinal motor neurons in vivo (possible -- rods have only been shown in culture). If so, the rod hypothesis for in vivo SMA pathology would need revision.
- PIVOT: If rods are equal between L1 and L5, rods may contribute to pathology but do not explain selective vulnerability. Focus would shift to other mechanisms (proprioceptive input density, metabolic demand).

### Estimated Cost
EUR 8,000-12,000 (mouse tissue, cryosectioning, antibodies, confocal time). Significantly cheaper if using archived tissue.

### Evidence Tier
**C** -- Rod formation is demonstrated in SMA cell culture (PMID 33986363) but not in vivo. The hypothesis linking rod burden to selective vulnerability is novel and untested. Upgradeable to B upon demonstration of rods in vivo, to A upon demonstration of differential rod burden between L1/L5.

---

## Hypothesis 3: Combinatorial Fasudil + Risdiplam Therapy Improves Motor Function Beyond Either Alone

### Biological Rationale
Fasudil (ROCK inhibitor) improves SMA mouse survival through muscle-specific mechanisms without increasing SMN protein (Bowerman et al., 2012, PMID 22397316). Risdiplam increases SMN2 full-length mRNA and protein levels (the approved mechanism of action for SMA treatment). These two drugs target non-overlapping pathological axes: Risdiplam addresses SMN deficiency (the root cause), while fasudil addresses downstream cytoskeletal/muscle pathology (a consequence that may persist even after partial SMN restoration). In treated SMA patients, residual motor deficits persist despite SMN restoration, suggesting SMN-independent pathology requires separate intervention.

### Testable Prediction
SMA mice treated with fasudil + risdiplam will show greater improvement in motor function (righting reflex, grip strength, survival) compared to either drug alone. The combination will also show greater proprioceptive synapse preservation (VGLUT1+ bouton count) and H-reflex improvement compared to monotherapy.

### Feasible Assay / Experiment
1. Four-arm study in SMN-delta-7 mice (n=12-15 per arm): vehicle, fasudil alone (30 mg/kg/day), risdiplam alone (dose TBD based on published mouse PK), fasudil + risdiplam
2. Treatment from P1 (or P3 for risdiplam, based on published protocols)
3. Motor function testing: righting reflex (daily P2-P14), grip strength (P10-P14), survival (Kaplan-Meier)
4. Terminal endpoints at P14: VGLUT1+ bouton count (L1, L5), NMJ endplate size, motor neuron count, SMN protein levels (Western blot), phospho-cofilin levels
5. H-reflex recording at P10-P14

### Model System
SMN-delta-7 mouse. Alternative: Smn2B/- (longer-lived, allows later timepoints but different drug dosing may be needed).

### Readouts
- Primary: Survival (days) and motor function composite score
- Secondary: VGLUT1+ bouton count, NMJ endplate size, motor neuron count
- Mechanistic: SMN protein (Western), phospho-cofilin (Western), H-reflex amplitude
- Safety: body weight, gross organ pathology

### Go/No-Go Criteria
- GO: Combination shows >=30% improvement in survival AND >=25% improvement in motor function composite vs. best monotherapy
- PARTIAL GO: Combination shows improvement in one measure but not both -- proceed with modified dose optimization
- NO-GO: Combination is no better than best monotherapy on any endpoint, or shows toxicity (weight loss >20%, mortality)

### Estimated Cost
EUR 40,000-60,000 (large mouse cohort, two drugs, comprehensive endpoint panel, electrophysiology). This is a significant study that would likely require external funding.

### Evidence Tier
**B** -- Both drugs have independent SMA preclinical efficacy data. The combination is mechanistically rational (non-overlapping targets). No combination data exists. Upgradeable to A upon positive preclinical result, which would support a clinical translation proposal.

---

## Hypothesis 4: Proprioceptive Neuron-Specific Actin Vulnerability Drives Early Circuit Failure in SMA

### Biological Rationale
Proprioceptive (Ia afferent) neurons express specific actin-regulatory programs for maintaining their elaborate synaptic terminals on motor neurons. Cdc42/actin remodeling is required for proprioceptive synapse formation (PMID 27225763). If SMN deficiency disrupts actin dynamics systemically (via ROCK pathway activation), proprioceptive neurons may be disproportionately affected because their synaptic terminals require high rates of actin turnover for synaptic vesicle cycling and active zone maintenance. This would explain why proprioceptive synapse loss precedes motor neuron death -- the presynaptic (proprioceptive) compartment fails first due to its higher actin demand.

### Testable Prediction
ROCK pathway activation (measured by phospho-cofilin) and actin dynamics disruption (F/G-actin ratio) will be more severe in proprioceptive DRG neurons and their central synaptic terminals than in motor neuron cell bodies in early-stage SMA mice (P4-P7).

### Feasible Assay / Experiment
1. Harvest DRGs and spinal cords from SMA mice at P4, P7, P10 (pre-symptomatic to early symptomatic)
2. FACS-sort PVALB+ proprioceptive neurons from DRGs (or use PVALB-Cre reporter mice)
3. Measure phospho-cofilin/total cofilin ratio by Western blot in sorted proprioceptive neurons vs. motor neuron-enriched spinal cord fractions
4. In parallel, image F/G-actin ratio in VGLUT1+ proprioceptive terminals on motor neurons using phalloidin/DNaseI staining and confocal microscopy
5. Compare with glutamatergic corticospinal terminals (VGLUT2+) as control synapse population

### Model System
SMN-delta-7 mouse crossed with PVALB-Cre;Rosa26-tdTomato (for proprioceptive neuron identification). Alternative: use PVALB antibody staining on standard SMA mice.

### Readouts
- Primary: phospho-cofilin/total cofilin ratio in PVALB+ DRG neurons vs. motor neurons
- Secondary: F/G-actin ratio in VGLUT1+ vs. VGLUT2+ synaptic terminals
- Tertiary: temporal correlation -- does actin disruption in proprioceptive terminals precede VGLUT1+ bouton loss?

### Go/No-Go Criteria
- GO: Proprioceptive neurons show >=50% higher phospho-cofilin ratio than motor neurons at P4-P7, AND VGLUT1+ terminals show lower F/G-actin ratio than VGLUT2+ terminals
- NO-GO: No difference in actin pathway activation between proprioceptive neurons and motor neurons -- actin dysfunction is cell-autonomous in motor neurons, not circuit-driven
- PIVOT: If both cell types show equal actin disruption, the selective vulnerability of proprioceptive synapses may be due to structural features (terminal morphology, branching complexity) rather than differential pathway activation

### Estimated Cost
EUR 20,000-35,000 (transgenic mice or antibodies, FACS, confocal, Westerns). Requires access to PVALB-Cre mice or high-quality PVALB antibodies validated for IHC in mouse DRG.

### Evidence Tier
**C** -- Novel hypothesis connecting two established observations (actin disruption in SMA + proprioceptive synapse loss) through a specific mechanism (differential actin vulnerability). No direct evidence exists. High-risk, high-reward. Upgradeable to B upon demonstration of differential actin pathway activation in proprioceptive neurons.

---

## Hypothesis 5: CFL2 Upregulation Is a Failed Compensatory Response That Accelerates Actin-Cofilin Rod Pathology

### Biological Rationale
CFL2 is 2.9x upregulated in SMA motor neurons (GSE69175), the second-highest fold change among the 7-gene actin network. CFL2 (cofilin-2) is the muscle-predominant cofilin isoform that severs and depolymerizes F-actin. In a healthy context, CFL2 upregulation might be compensatory -- increasing actin turnover to counteract the excessive F-actin accumulation caused by ROCK pathway activation. However, excess cofilin can paradoxically promote actin-cofilin rod formation by saturating actin filaments (Bamburg et al., 2010, PMID 20088812). The prediction is that CFL2 upregulation begins as compensation but, in the context of dysregulated ROCK/LIMK signaling (which fails to properly phosphorylate and inactivate the excess cofilin), leads to increased rod formation -- a vicious cycle.

### Testable Prediction
1. CFL2 protein is elevated in SMA motor neurons at early timepoints (P4-P7, compensatory phase)
2. Actin-cofilin rod burden increases between P7 and P14 (pathological phase)
3. Phospho-CFL2 (Ser3, inactive form) is DECREASED despite total CFL2 being increased, indicating that the excess cofilin is predominantly in the active (dephosphorylated) form
4. LIMK inhibition (which would further decrease cofilin phosphorylation) should WORSEN rod pathology, while ROCK inhibition (fasudil, which reduces upstream signaling) should REDUCE rods by normalizing the cofilin activation/inactivation cycle

### Feasible Assay / Experiment
1. Western blot time-course: total CFL2 and phospho-CFL2 (Ser3) in spinal cord from SMA mice at P1, P4, P7, P10, P14 vs. controls
2. IHC: CFL2 and phospho-CFL2 in motor neurons, co-stained with ChAT
3. Cell culture validation: treat SMA motor neurons with (a) fasudil (ROCK inhibitor), (b) BMS-5 (LIMK inhibitor), (c) vehicle
4. Quantify rod formation under each condition

### Model System
SMN-delta-7 mouse (in vivo time course). iPSC-derived SMA motor neurons (for drug treatment experiments).

### Readouts
- Primary: total CFL2 protein level (Western blot, time course)
- Secondary: phospho-CFL2/total CFL2 ratio (time course)
- Tertiary: rod count per motor neuron under fasudil vs. LIMK inhibitor vs. vehicle (cell culture)
- Confirmatory: correlation of CFL2 levels with motor neuron degeneration markers

### Go/No-Go Criteria
- GO: CFL2 protein is elevated at P4-P7 AND phospho-CFL2 ratio is decreased AND fasudil reduces rod formation in culture
- PARTIAL: CFL2 protein elevated but phospho-CFL2 ratio unchanged -- compensation is occurring but regulation is intact. Revise model.
- NO-GO: CFL2 protein not elevated at protein level despite 2.9x mRNA upregulation -- post-transcriptional regulation prevents translation. Shift focus to CFL1 (neuronal isoform) or other pathway members.

### Estimated Cost
EUR 12,000-18,000 (Western blot time course, IHC, cell culture drug experiments). Antibody availability for phospho-CFL2 (Ser3) should be confirmed -- most commercial antibodies detect phospho-CFL1 and phospho-CFL2 without isoform specificity.

### Evidence Tier
**C** -- This is a mechanistic hypothesis based on transcriptomic data (CFL2 2.9x upregulated) and known cofilin biology (excess cofilin promotes rods). The "failed compensation" model is speculative but testable. Upgradeable to B upon protein-level validation, to A upon demonstration of the fasudil/LIMK inhibitor differential effect on rods.

---

## Summary Table

| # | Hypothesis | Evidence Tier | Cost (EUR) | Timeline | Key Dependency |
|---|-----------|--------------|-----------|----------|---------------|
| 1 | ROCK inhibition rescues proprioceptive synapses | B | 15-25K | 3-4 months | Simon lab electrophysiology |
| 2 | Actin-cofilin rods in L1 > L5 motor neurons | C | 8-12K | 2-3 months | SMA mouse tissue access |
| 3 | Fasudil + Risdiplam combination | B | 40-60K | 6-9 months | External funding needed |
| 4 | Proprioceptive neuron actin vulnerability | C | 20-35K | 4-6 months | PVALB-Cre mice or Ab |
| 5 | CFL2 failed compensation --> rod pathology | C | 12-18K | 3-4 months | phospho-CFL2 antibody validation |

**Recommended priority order** (based on feasibility, cost, and information value):
1. **Hypothesis 2** (rods in L1 vs L5) -- cheapest, can use archived tissue, directly tests selective vulnerability
2. **Hypothesis 5** (CFL2 protein validation) -- straightforward Western blot, validates transcriptomic finding
3. **Hypothesis 1** (ROCK inhibition + proprioceptive synapses) -- highest clinical translation potential, needs Simon collaboration
4. **Hypothesis 4** (proprioceptive neuron actin vulnerability) -- most novel, highest risk
5. **Hypothesis 3** (combination therapy) -- most expensive, pursue only after Hypotheses 1-2 are positive

---

*These hypothesis cards will be entered into the SMA Research Platform hypothesis database after review and refinement with Prof. Simon. Each card is designed to include explicit go/no-go criteria to prevent confirmation bias and ensure honest evaluation of results.*
