# Fasudil in SMA iPSC-Motor Neurons — Experiment Proposal
# First-in-Field: ROCK Inhibition as Combination Therapy for SMA

> **Generated**: 2026-03-21 (Autonomous Research Sprint)
> **Scoring**: GPT-4o — Novelty 9/10, Impact 9/10, Probability 8/10
> **Status**: Proposed for Simon collaboration (Leipzig)

---

## Hypothesis

**Cofilin hyperphosphorylation links SMA actin pathway disruption to TDP-43
aggregation, and Fasudil (ROCK inhibitor) can break this pathological cycle.**

Pathway: SMN loss → impaired PFN1 → RhoA/ROCK activation → LIMK activation →
CFL2 hyperphosphorylation → actin-cofilin rod formation → TDP-43 aggregation

## Supporting Evidence

| Evidence | Source | Type |
|----------|--------|------|
| SMN interacts directly with PFN1 in motor neurons | PMID 21920940 | Co-IP, MN validated |
| ROCK1/ROCK2 elevated in SMNΔ7 mouse muscle | Published studies | Animal model |
| Phospho-cofilin elevated in SMA models + patient fibroblasts | Published studies | Human + animal |
| CFL2 2.9x upregulated in SMA iPSC-MN | GSE69175 | Transcriptomic |
| Actin-cofilin rods form in SMA cell models | PMID 33986363 (Walter 2021) | Cell model |
| Cofilin-P triggers TDP-43 pathology in ALS | Brain, March 2026 | Cross-disease |
| Fasudil crosses blood-brain barrier | Stroke studies | Pharmacology |
| Fasudil Phase 2 completed in ALS | NCT03792490 | Clinical safety |
| PFN1 mutations cause familial ALS type 20 | 62 papers | Human genetics |
| Nobody has tested ROCK inhibitors in SMA | Literature search | Gap |

## Experiment Design

### Phase 1: Baseline Characterization (Weeks 1-6)

1. **Obtain SMA iPSC lines** — Coriell Institute or Reprocell
   - SMA Type I (severe): homozygous SMN1 deletion, 2 copies SMN2
   - Isogenic control: CRISPR-corrected or healthy donor
2. **Differentiate to motor neurons** — Svendsen or Wichterle protocol
   - 2-4 weeks differentiation, confirm by HB9/ISL1/ChAT markers
   - QC: >80% MN purity by ICC

### Phase 2: Fasudil Treatment (Weeks 7-8)

3. **Treatment groups** (n=3 biological replicates each):
   - Vehicle control (DMSO)
   - Fasudil 10 µM (low dose)
   - Fasudil 30 µM (high dose)
   - Y-27632 10 µM (positive control, common ROCK inhibitor)
   - Treatment duration: 48-72 hours

### Phase 3: Readouts (Weeks 8-10)

4. **Primary readouts**:
   - **Phospho-cofilin / total cofilin ratio** — Western blot
     - Prediction: Fasudil reduces p-cofilin by >50%
   - **Actin-cofilin rod count** — Phalloidin + cofilin ICC, confocal
     - Prediction: Fasudil reduces rod count by >30%
   - **TDP-43 nuclear/cytoplasmic ratio** — TDP-43 ICC, confocal
     - Prediction: Fasudil increases nuclear TDP-43 (less mislocalization)

5. **Secondary readouts**:
   - Motor neuron survival (cell counting, MTT assay)
   - Neurite outgrowth (image analysis)
   - SMN protein levels (to confirm no interference)

### Phase 4: Validation (Weeks 10-12, if Phase 3 positive)

6. **MDI-117740** (LIMK inhibitor) at 1-10 µM — more specific than Fasudil
7. **Dose-response curve** for the most effective compound
8. **Time course** — when do effects appear (24h, 48h, 72h)?

## Expected Results

**If hypothesis is correct:**
- p-cofilin decreases dose-dependently with Fasudil
- Actin-cofilin rods decrease
- TDP-43 returns to nuclear localization
- Motor neuron survival improves

**If hypothesis is wrong:**
- p-cofilin decreases but TDP-43 unchanged → pathway disconnected
- No p-cofilin change → ROCK not the relevant kinase in SMA MNs
- Cell death increases → ROCK inhibition is detrimental (toxicity)

## Cost Estimate

| Item | Cost |
|------|------|
| iPSC lines (SMA + isogenic control) | ~$2,000-3,000 |
| Cell culture reagents + differentiation | ~$1,500-2,000 |
| Fasudil, Y-27632, MDI-117740 | ~$500 |
| Antibodies (p-cofilin, cofilin, TDP-43, phalloidin) | ~$1,000-1,500 |
| Western blot + ICC consumables | ~$500 |
| Core facility (confocal microscopy) | ~$500-1,000 |
| **Total** | **~$6,000-10,000** |

## Timeline

| Phase | Duration | Milestone |
|-------|----------|-----------|
| iPSC expansion | 2-3 weeks | Cells banked |
| MN differentiation | 2-4 weeks | >80% MN purity |
| Fasudil treatment | 1 week | Treatment complete |
| Readouts | 1-2 weeks | Data collected |
| Analysis | 1-2 weeks | Results interpreted |
| **Total** | **7-12 weeks** | Go/no-go decision |

## Why This Matters

1. **First-in-field**: Nobody has tested ROCK inhibitors in SMA
2. **Drug exists**: Fasudil is approved (Japan/China), Phase 2 data in ALS
3. **Cross-disease**: If positive, applies to both SMA AND ALS
4. **Combination potential**: Risdiplam (SMN) + Fasudil (actin) addresses both cause and downstream damage
5. **Publication potential**: Novel mechanism + repurposed drug = high-impact paper

## Go/No-Go Criteria

- **GO**: p-cofilin reduced >30% AND TDP-43 nuclear ratio increased >20%
- **PIVOT**: p-cofilin reduced but TDP-43 unchanged → test other downstream targets
- **STOP**: No p-cofilin reduction → ROCK pathway not relevant in SMA MNs

## References

- PMID 21920940 — SMN-PFN1 interaction in motor neurons
- PMID 33986363 — Actin-cofilin rods in SMA (Walter 2021)
- NCT03792490 — Fasudil Phase 2 in ALS
- GSE69175 — CFL2 2.9x up in SMA iPSC-MN
- GSE290979 — PFN1 +46% in SMA organoids
