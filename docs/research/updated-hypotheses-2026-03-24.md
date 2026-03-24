# Updated Hypotheses: Post-Single-Cell Analysis (2026-03-24)

**Date**: 2026-03-24
**Based on**: GSE287257 snRNA-seq results + prior convergence synthesis
**Status**: 5 new hypothesis cards reflecting single-cell findings
**Complements**: hypotheses-pfn1-cfl2-rock2.md (2026-03-22)

---

## Hypothesis 1: PFN2 is the Critical Motor Neuron Actin Regulator in SMA

**Evidence Tier**: B (strong mechanistic rationale + transcriptomic data, no direct SMA functional validation yet)

### Biological Rationale

PFN2 (profilin-2) is 7.6x enriched in motor neurons compared to all other spinal cord cell types (GSE287257: log2FC = +1.22, p = 5.3e-18). This makes PFN2 the most motor neuron-specific actin pathway gene in our analysis. SMN directly binds profilin proteins (PFN2a specifically) through a proline-rich domain, and the SMA patient mutation S230L disrupts this interaction (Nolle et al., 2011, PMID 21920940). Schuning et al. (2024, PMID 39305126) further showed that SMN binds actin directly, establishing two functional populations: SMN-PFN2a-actin and SMN-actin.

PFN2 is 1.5x upregulated in SMA motor neurons (GSE69175), likely as a compensatory response to SMN-PFN2a complex disruption. The extreme motor neuron enrichment of PFN2 explains why SMN loss disproportionately affects motor neurons: no other cell type depends on the SMN-PFN2 axis as heavily.

### Testable Prediction

PFN2 knockdown in healthy motor neurons should phenocopy key SMA features (neurite degeneration, growth cone collapse, impaired actin dynamics), while PFN2 knockdown in non-neuronal cells should have minimal effect.

### Experiment

1. **siRNA/shRNA PFN2 knockdown** in iPSC-derived motor neurons (healthy control line)
2. **Readouts**:
   - Neurite length and branching (automated imaging, ImageJ/CellProfiler)
   - Growth cone morphology (phalloidin staining for F-actin)
   - F/G-actin ratio (biochemical fractionation)
   - Actin-cofilin rod formation (immunofluorescence for cofilin + phalloidin)
   - Cell viability at 48h, 96h, 7d (LDH release, calcein-AM)
3. **Controls**: PFN1 knockdown (tests isoform specificity), scrambled siRNA, SMA motor neurons (positive control for phenotype)
4. **Model system**: iPSC-derived motor neurons (human, Maury et al. 2015 protocol or commercial)

### Go/No-Go Criteria

- **GO**: PFN2 knockdown reduces neurite length by >30%, increases actin rods by >2x, and reduces F/G-actin ratio by >20%, all with p<0.05. PFN1 knockdown shows weaker effect (isoform specificity).
- **NO-GO**: PFN2 knockdown has no significant effect on neurite morphology or actin dynamics, or PFN1 knockdown shows equivalent effect (no isoform specificity).

### Cost Estimate

- iPSC motor neuron differentiation: ~4,000 EUR (reagents, 4-6 week protocol)
- siRNA/shRNA constructs: ~500 EUR
- Imaging and analysis: ~1,500 EUR (confocal time, antibodies)
- Total: ~6,000 EUR (1 postdoc, 2-3 months)

### Limitations

- GSE287257 MN-enrichment is from ALS tissue (control samples). PFN2 enrichment in SMA motor neurons has not been directly measured at single-cell level.
- iPSC-derived motor neurons may not fully recapitulate in vivo motor neuron identity.
- PFN2 knockdown tests necessity, not sufficiency. Overexpression/rescue experiments would be needed to demonstrate sufficiency.

---

## Hypothesis 2: The LIMK1-to-LIMK2 Switch Marks the Transition from Compensation to Degeneration

**Evidence Tier**: C (observed in ALS single-cell data, not yet tested in SMA, mechanistic model is speculative)

### Biological Rationale

In GSE287257, ALS motor neurons show a striking kinase switch: LIMK1 is downregulated (log2FC = -0.81, p = 0.004) while LIMK2 is upregulated (log2FC = +1.01, p = 0.009). In healthy motor neurons, LIMK1 is the dominant isoform (2.3x MN-enriched, log2FC = +1.20, p = 8.4e-24), while LIMK2 is more broadly expressed (log2FC = +0.18).

LIMK1 and LIMK2 both phosphorylate cofilin at Ser3, but they have different upstream regulators, subcellular localizations, and substrate specificities. LIMK1 is activated by PAK1/PAK4 and ROCK, and is enriched at growth cones and synapses. LIMK2 is activated primarily by ROCK and is more broadly distributed. The switch from LIMK1 to LIMK2 may represent a compensatory response that is ultimately insufficient because LIMK2 lacks LIMK1's synapse-specific functions.

### Testable Prediction

The LIMK1/LIMK2 expression ratio decreases progressively during SMA disease progression. Early-stage SMA motor neurons (presymptomatic) maintain a high LIMK1/LIMK2 ratio, while late-stage (symptomatic) motor neurons show a lower ratio approaching the ALS pattern.

### Experiment

1. **Time-course analysis** in SMA mouse model (SMN-delta-7 or Smn2B/-)
   - Harvest spinal cord at P1, P5, P9, P13 (presymptomatic through endstage)
   - Quantify LIMK1 and LIMK2 mRNA (qRT-PCR, laser-capture microdissected motor neurons)
   - Quantify LIMK1 and LIMK2 protein (IHC with motor neuron co-staining: ChAT or SMI-32)
   - Calculate LIMK1/LIMK2 ratio at each timepoint
2. **Readouts**:
   - LIMK1/LIMK2 mRNA ratio over time
   - LIMK1/LIMK2 protein ratio over time
   - p-cofilin/total cofilin ratio (downstream readout of LIMK activity)
   - Motor neuron counts (to correlate ratio change with degeneration onset)
3. **Model system**: SMA mouse (SMN-delta-7 preferred for well-characterized timepoints)

### Go/No-Go Criteria

- **GO**: LIMK1/LIMK2 ratio decreases by >50% between presymptomatic (P1-P5) and symptomatic (P9-P13) timepoints, correlating with motor neuron loss onset.
- **PARTIAL**: Ratio changes but does not correlate with degeneration timing -- suggests the switch is a consequence, not a driver.
- **NO-GO**: LIMK1/LIMK2 ratio remains stable throughout disease course -- the switch is ALS-specific and not relevant to SMA.

### Cost Estimate

- SMA mouse breeding and timed harvests: ~3,000 EUR (4 timepoints x 4 animals/group)
- Laser-capture microdissection: ~2,000 EUR
- qRT-PCR + IHC: ~2,000 EUR
- Total: ~7,000 EUR (1 technician + 1 postdoc, 3-4 months)

### Limitations

- The LIMK1-to-LIMK2 switch was observed in ALS (GSE287257), not SMA. It may be ALS-specific.
- n=90 ALS motor neurons vs n=150 control motor neurons is modest. The LIMK2 upregulation (p=0.009) is significant but not overwhelming.
- Postmortem tissue captures endstage disease only. The temporal dynamics are inferred, not observed.
- Mouse LIMK1/LIMK2 regulation may differ from human.

---

## Hypothesis 3: CFL2 Upregulation in SMA is a Failed Compensation Mechanism

**Evidence Tier**: B (strong transcriptomic evidence, clear mechanistic logic, no functional SMA validation)

### Biological Rationale

CFL2 (cofilin-2) shows opposite regulation in SMA vs ALS:
- **SMA**: CFL2 is 2.9x upregulated (GSE69175, iPSC-derived motor neurons)
- **ALS**: CFL2 is significantly downregulated (all cells: log2FC = -0.13, p = 9.4e-22; MNs specifically: log2FC = -0.94, p = 0.024, GSE287257)

CFL2 is an actin-depolymerizing factor that severs actin filaments when dephosphorylated (active). In the context of ROCK pathway hyperactivation and actin dynamics disruption caused by SMN loss:

- **In SMA**: Cells upregulate CFL2 to maintain actin turnover. This is a compensatory response -- more cofilin-2 helps process the accumulating F-actin that cannot be properly regulated without the SMN-profilin axis. However, excess active CFL2 also promotes actin-cofilin rod formation (Walter et al., 2021, PMID 33986363), making it a double-edged sword.
- **In ALS**: CFL2 has already collapsed. The compensatory mechanism is exhausted. With both CFL2 down and LIMK1 down, the motor neuron has lost control of actin dynamics entirely. This may contribute to the faster progression seen in ALS compared to most SMA subtypes.

### Testable Prediction

CFL2 knockdown in SMA motor neurons should accelerate degeneration (proving it is compensatory), while CFL2 overexpression in ALS motor neurons should provide partial protection (proving the deficit matters).

### Experiment

**Part A -- CFL2 in SMA** (tests compensation):
1. CFL2 siRNA knockdown in SMA iPSC-derived motor neurons
2. Readouts: neurite length, actin rod count, cell viability, axonal transport velocity (kymography)
3. Prediction: CFL2 knockdown worsens all metrics in SMA MNs

**Part B -- CFL2 in ALS** (tests deficit):
1. CFL2 overexpression (lentiviral) in ALS iPSC-derived motor neurons (e.g., SOD1 or C9orf72 line)
2. Readouts: same as Part A plus TDP-43 localization
3. Prediction: CFL2 overexpression partially rescues actin dynamics

**Model system**: iPSC-derived motor neurons (SMA Type I line + ALS line, commercially available)

### Go/No-Go Criteria

- **GO (Part A)**: CFL2 knockdown in SMA MNs reduces viability by >40% and/or increases actin rods by >3x within 7 days. This confirms compensation.
- **GO (Part B)**: CFL2 overexpression in ALS MNs improves at least 2 of 4 readouts significantly. This confirms the deficit matters.
- **NO-GO**: CFL2 knockdown in SMA has no effect, or CFL2 overexpression in ALS worsens outcomes. In this case, CFL2 changes are a passenger, not a driver.

### Cost Estimate

- iPSC lines (SMA + ALS): ~2,000 EUR (if purchased) or available from collaborators
- Lentiviral CFL2 overexpression construct: ~1,500 EUR
- siRNA + transfection: ~500 EUR
- Motor neuron differentiation (2 lines x 2 conditions): ~6,000 EUR
- Imaging and analysis: ~2,000 EUR
- Total: ~12,000 EUR (1 postdoc, 4-5 months for both parts)

### Limitations

- CFL2 2.9x mRNA upregulation (GSE69175) has not been confirmed at protein level. Protein and phosphorylation status are unknown.
- The ALS CFL2 downregulation is from postmortem tissue (survivorship bias) with modest motor neuron numbers (n=90 ALS MNs).
- "Compensation" vs "pathological response" is difficult to distinguish without temporal data.
- CFL2 has zero dedicated SMA papers -- this is entirely novel territory.

---

## Hypothesis 4: CORO1C Elevation is a Neuroinflammation Marker, Not a Therapeutic Target

**Evidence Tier**: A (most evidence, multi-dataset, single-cell resolution)

### Biological Rationale

CORO1C was initially identified as upregulated in both SMA (GSE69175, 1.6x) and ALS (GSE113924, padj=0.003) motor neuron tissue. This cross-disease convergence was considered potentially novel and therapeutically relevant. However, GSE287257 single-cell analysis reveals:

1. **CORO1C is highest in microglia (0.57) and endothelial cells (0.60)**, not motor neurons (0.41)
2. **CORO1C upregulation in ALS is pan-cellular** (p = 1.03e-30 all cells), not motor neuron-specific (p = 0.52)
3. **CORO1C MN-enrichment is modest** (log2FC = +0.10, p = 0.007) compared to PFN2 (+1.22) or LIMK1 (+1.20)

CORO1C regulates Arp2/3-mediated actin branching and endocytosis. In microglia, these functions are essential for phagocytosis and immune surveillance. In endothelial cells, they regulate blood-brain barrier permeability and leukocyte transmigration. CORO1C upregulation in disease tissue likely reflects microglial activation and vascular remodeling -- hallmarks of neuroinflammation.

### Testable Prediction

CORO1C levels in cerebrospinal fluid (CSF) or blood correlate with neuroinflammatory markers (GFAP, sTREM2, IL-6) but not with motor neuron-specific markers (NfL, STMN2) in SMA and ALS patients.

### Experiment

1. **Retrospective biomarker correlation** in existing SMA/ALS patient CSF biobanks
   - Measure CORO1C protein (ELISA or Olink panel) in CSF
   - Correlate with GFAP (astrogliosis), sTREM2 (microglial activation), NfL (neuronal damage), STMN2 (if available)
   - Test: does CORO1C correlate more strongly with glial markers than neuronal markers?
2. **Spatial transcriptomics** (MERFISH or Visium) on SMA/ALS spinal cord sections
   - Map CORO1C expression to specific cell types in situ
   - Co-stain with Iba1 (microglia), CD31 (endothelial), ChAT (motor neurons)
   - Quantify cell-type contribution to total CORO1C signal
3. **Model system**: Patient CSF (biobank) + postmortem tissue (if available)

### Go/No-Go Criteria

- **GO (biomarker)**: CORO1C correlates with GFAP/sTREM2 (r > 0.5) but not with NfL (r < 0.2). This confirms neuroinflammation marker status.
- **GO (spatial)**: >70% of CORO1C+ cells in disease tissue are microglia or endothelial. This confirms the single-cell finding in situ.
- **REVISE**: CORO1C correlates with both glial and neuronal markers -- it may be a general disease activity marker, not specifically neuroinflammatory.
- **NO-GO**: CORO1C shows no correlation with any biomarker -- it is not useful diagnostically.

### Cost Estimate

- CSF ELISA (CORO1C + correlate markers, 50 samples): ~5,000 EUR
- Spatial transcriptomics (3 tissue sections): ~15,000 EUR (if MERFISH; ~5,000 if Visium)
- Total: ~10,000-20,000 EUR depending on platform
- Timeline: 3-6 months (mainly limited by tissue/CSF access)

### What Remains Novel

- CORO1C upregulation in ALS spinal cord has never been reported (GSE113924 analysis is ours)
- The cell-type resolution showing glial rather than neuronal origin is novel
- If validated as a CSF biomarker for neuroinflammation in motor neuron diseases, this would be clinically useful
- The reinterpretation itself (from target to biomarker) demonstrates rigorous self-correction

### Limitations

- CORO1C in SMA has only been measured in bulk tissue (GSE69175) and organoids (GSE290979). Cell-type resolution in SMA is not yet available.
- CSF CORO1C may not reflect CNS tissue levels.
- GSE287257 has only 3 ALS and 4 control individuals -- individual variation is substantial.

---

## Hypothesis 5: Fasudil + Risdiplam Dual Therapy Achieves Synergistic Motor Function Improvement

**Evidence Tier**: B (strong individual drug evidence, no combination data)

### Biological Rationale

Fasudil and Risdiplam address distinct pathological mechanisms in SMA:

**Fasudil** (ROCK inhibitor):
- Improves survival of SMA mice via SMN-independent mechanism (Bowerman et al., 2012, PMID 22397316)
- Increases muscle fiber size and postsynaptic endplate size
- Does NOT increase SMN protein or preserve motor neurons directly
- Mechanism: normalizes ROCK-mediated actin/muscle pathology
- Human safety established: Phase 2 ALS trial (n=120, well-tolerated, PMID 39424560)

**Risdiplam** (SMN2 splicing modifier):
- FDA-approved for SMA (all types, all ages)
- Increases functional SMN protein from SMN2 gene
- Oral, CNS-penetrant
- Addresses the root cause (SMN deficiency)

**Why combination should be synergistic, not merely additive**:
1. Fasudil rescues muscle-intrinsic pathology that persists even after SMN restoration (Schuning et al., 2024, PMID 39305126 showed SMN-actin co-localization is only partially rescued by SMN restoration)
2. SMN restoration (Risdiplam) would repair the SMN-PFN2a complex, reducing ROCK hyperactivation upstream
3. Fasudil would simultaneously address the downstream consequences (actin rods, NMJ pathology, muscle fiber degeneration) that SMN restoration alone cannot fully reverse
4. The ROCK-ALS trial (PMID 39424560) showed fasudil reduces GFAP, suggesting anti-neuroinflammatory effects that would complement SMN restoration

### Testable Prediction

Fasudil + Risdiplam combination in SMA mice improves survival, motor function, and NMJ morphology significantly more than either drug alone.

### Experiment

1. **SMA mouse study** (Smn2B/- model, matching Bowerman 2012)
   - Groups (n=15 per group, both sexes):
     - Vehicle control
     - Risdiplam alone (5 mg/kg/day oral, per published dosing)
     - Fasudil alone (30 mg/kg twice daily oral, per Bowerman 2012)
     - Risdiplam + Fasudil combination
   - Treatment: P3 to endstage (or P21 for fasudil window)
2. **Primary endpoints**:
   - Survival (Kaplan-Meier)
   - Motor function (righting reflex latency, grip strength)
   - Body weight trajectory
3. **Secondary endpoints**:
   - Motor neuron counts (lumbar spinal cord, ChAT+ cells)
   - NMJ morphology (pretzel vs denervated, alpha-bungarotoxin + neurofilament)
   - Muscle fiber cross-sectional area (H&E, tibialis anterior)
   - SMN protein levels (Western blot, spinal cord + muscle)
   - p-cofilin/cofilin ratio (downstream pathway marker)
   - GFAP levels (neuroinflammation, per ROCK-ALS finding)
4. **Model system**: Smn2B/- mice (C57BL/6 background)

### Go/No-Go Criteria

- **GO (synergy)**: Combination extends survival >20% beyond the better single agent AND improves at least 2 secondary endpoints significantly beyond either alone. Interaction term significant in two-way ANOVA.
- **GO (additive)**: Combination improves outcomes beyond either single agent but without significant interaction. Still clinically valuable but mechanistically less interesting.
- **NO-GO**: Combination shows no benefit over the better single agent, or combination produces toxicity (e.g., excessive hypotension from fasudil + risdiplam interaction).

### Cost Estimate

- SMA mice (60 pups + breeders): ~8,000 EUR
- Drug costs (risdiplam synthesis or purchase, fasudil): ~3,000 EUR
- Behavioral testing + tissue processing: ~4,000 EUR
- Histology + Western blots + imaging: ~5,000 EUR
- Total: ~20,000 EUR (1 postdoc + 1 technician, 6-8 months)

### Limitations

- Smn2B/- is a severe SMA model. Results may not translate to milder (Type 2/3) disease.
- Fasudil dosing in Bowerman 2012 was in the SMN-delta-7 model, not Smn2B/-. Cross-model dose optimization may be needed.
- Mouse pharmacokinetics differ from human. Fasudil IV (ROCK-ALS trial) vs oral (Bowerman) complicates dosing translation.
- No PK interaction data between fasudil and risdiplam exists. Potential drug-drug interactions need to be assessed.
- The "synergy" threshold is high. Additive benefit would still be clinically meaningful but harder to publish.

---

## Summary Table

| # | Hypothesis | Tier | Key Evidence | Critical Gap |
|---|-----------|------|-------------|-------------|
| 1 | PFN2 is the critical MN actin regulator | B | 7.6x MN-enriched (GSE287257), SMN-profilin binding (PMID 21920940) | No PFN2 knockdown in MNs tested |
| 2 | LIMK1-to-LIMK2 switch marks degeneration | C | LIMK1 down + LIMK2 up in ALS MNs (GSE287257) | Not measured in SMA at all |
| 3 | CFL2 UP in SMA is failed compensation | B | 2.9x UP in SMA, DOWN in ALS (opposite), rod connection (PMID 33986363) | No protein-level data in SMA tissue |
| 4 | CORO1C is neuroinflammation marker | A | Highest in microglia/endothelial (GSE287257), pan-cellular ALS signal | No CSF/blood correlation data |
| 5 | Fasudil + Risdiplam synergy | B | Fasudil SMA efficacy (PMID 22397316), Phase 2 ALS safety (PMID 39424560), Risdiplam approved | No combination study exists |

---

*These hypotheses should be reviewed with Prof. Simon during the March 30 meeting. His proprioceptive circuit expertise is particularly relevant for Hypotheses 1 (PFN2 in synaptic actin), 2 (LIMK kinase switch timing), and 5 (fasudil effects on circuit function).*
