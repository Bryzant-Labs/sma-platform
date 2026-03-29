# Experimental Validation Pipeline: genmol_119 -> Drug Candidate

**Date**: 2026-03-24
**Compound**: genmol_119 = (R,S)-H-1152 enantiomer (stereo-resolved)
**Targets**: ROCK2 (Ki ~1.6 nM for racemic H-1152) + LIMK2 (DiffDock score +1.058)
**Key Properties**: MW 300.32, cLogP 3.58, TPSA 33.2, BBB-permeable, CNS-MPO 4.90, QED 0.836
**SMILES Stereocenters**: C8(R), C14(S) -- the specific enantiomer that GenMol identified as optimal

---

## Executive Summary

genmol_119 is a computationally identified stereo-resolved enantiomer of H-1152, an established
ROCK inhibitor (CAS 451462-58-1 for racemic). Our DiffDock analysis shows the (R,S)-enantiomer
binds LIMK2 with a higher confidence score (+1.058) than the racemic mixture (+0.90), making it
a potential dual ROCK2/LIMK2 inhibitor -- exactly the therapeutic profile needed for the
ROCK-LIMK2-Cofilin axis in SMA.

This document outlines the complete wet-lab validation pipeline from computational hit to
Investigational New Drug (IND) filing, with realistic costs, timelines, and recommended
service providers.

---

## Stage 1: Chemical Synthesis & Characterization (Month 1-2)

### Objective
Synthesize the specific (R,S)-enantiomer of H-1152 with >99% enantiomeric excess (ee), and
produce sufficient material for all in vitro assays (~500 mg).

### Approach Options

**Option A: Chiral Resolution (Lower risk, faster)**
- Purchase racemic H-1152 dihydrochloride (commercially available, CAS 871543-07-6)
- Separate enantiomers via chiral HPLC (preparative scale)
- Advantage: H-1152 is a known compound with established synthesis
- Disadvantage: Maximum 50% theoretical yield

**Option B: Enantioselective Synthesis (Higher value, slower)**
- Asymmetric synthesis targeting (R,S)-configuration specifically
- Provides scalable route for later manufacturing
- Required eventually for IND-enabling CMC work

### Recommended CROs

| CRO | Location | Specialty | Est. Cost | Timeline |
|-----|----------|-----------|-----------|----------|
| **Enamine** | Kyiv, Ukraine | Custom synthesis, large catalog | $3,000-8,000 (resolution) | 4-6 weeks |
| **BOC Sciences** | New York, USA | Chiral resolution specialists | $5,000-15,000 | 4-8 weeks |
| **Chiroblock** | Wolfen, Germany | Chiral synthesis, academic rates | $8,000-20,000 (de novo) | 6-10 weeks |
| **WuXi AppTec** | Shanghai, China | Scale-up capable, FTE model | $5,000-12,000 | 4-6 weeks |
| **Symeres** | Netherlands/Czech | Med chem + chiral synthesis | $10,000-25,000 (full route) | 6-12 weeks |

### Deliverables
- [ ] 500 mg (R,S)-H-1152, >99% ee
- [ ] 100 mg (S,R)-H-1152 (opposite enantiomer, as negative control)
- [ ] 100 mg racemic H-1152 (reference)
- [ ] Analytical certificate: chiral HPLC, NMR, MS, elemental analysis
- [ ] HPLC method for ee determination

### Estimated Cost: $8,000-25,000
### Timeline: 4-10 weeks

---

## Stage 2: In Vitro Binding & Potency (Month 2-3)

### 2A: Surface Plasmon Resonance (SPR) -- Binding Kinetics

**Purpose**: Measure true binding affinity (Kd), on-rate (ka), and off-rate (kd) for both
targets to confirm computational predictions.

| Assay | Target | Metric | Expected Range |
|-------|--------|--------|----------------|
| SPR (Biacore) | ROCK2 | Kd, ka, kd | Kd < 10 nM (based on H-1152 Ki = 1.6 nM) |
| SPR (Biacore) | LIMK2 | Kd, ka, kd | Kd < 500 nM (novel, DiffDock predicted) |
| SPR (Biacore) | ROCK1 | Kd, ka, kd | Selectivity reference |

**Test compounds**: (R,S)-genmol_119, (S,R)-enantiomer, racemic H-1152, fasudil (reference)

### Recommended CROs

| CRO | Location | Platform | Est. Cost | Timeline |
|-----|----------|----------|-----------|----------|
| **Reaction Biology** | Malvern, PA / Freiburg, DE | Biacore 8K+ | $3,000-8,000/target | 2-4 weeks |
| **Charles River** | Multiple | Biacore T200/8K | $5,000-10,000/target | 3-4 weeks |
| **Gifford Bioscience** | Birmingham, UK | Biacore 8K | $3,500-7,000/target | 2-3 weeks |
| **BioAscent** | Newhouse, UK | Biacore 8K | $4,000-8,000/target | 2-4 weeks |

### 2B: Kinase Enzymatic Assays -- IC50 Determination

**Purpose**: Determine inhibitory potency against ROCK2 and LIMK2 with IC50 dose-response curves.

| Assay | Target | Format | Concentrations |
|-------|--------|--------|----------------|
| Radiometric HotSpot | ROCK2 | 10-point IC50 | 0.1 nM - 10 uM |
| Radiometric HotSpot | LIMK2 | 10-point IC50 | 0.1 nM - 10 uM |
| Radiometric HotSpot | ROCK1 | 10-point IC50 | Selectivity |
| Radiometric HotSpot | LIMK1 | 10-point IC50 | Selectivity |

**Test compounds**: (R,S)-genmol_119, (S,R)-enantiomer, racemic H-1152, fasudil

### Recommended CROs

| CRO | Location | Assay Format | Est. Cost | Timeline |
|-----|----------|-------------|-----------|----------|
| **Reaction Biology** | Malvern, PA / Freiburg, DE | HotSpot radiometric | $150-300/compound/kinase | 10 business days |
| **Eurofins (DiscoverX)** | San Diego, CA | KINOMEscan binding | $200-400/compound/kinase | 2-3 weeks |
| **AssayQuant** | Marlborough, MA | PhosphoSens real-time | $200-350/compound/kinase | 2 weeks |
| **Pharmaron** | Beijing/USA | Activity-based | $100-250/compound/kinase | 2-3 weeks |

**Note**: Reaction Biology specifically lists LIMK2 in their kinase catalog -- confirmed available.

### Estimated Cost (Stage 2 total): $15,000-35,000
- SPR for 3 targets x 4 compounds: $9,000-24,000
- IC50 for 4 kinases x 4 compounds: $6,000-11,000

### Timeline: 2-4 weeks (can run parallel with SPR)

---

## Stage 3: Selectivity & Safety Profiling (Month 3-4)

### 3A: Kinome-Wide Selectivity -- KINOMEscan

**Purpose**: Determine selectivity across the human kinome. A "clean" selectivity profile
(S-score < 0.1) is critical for a CNS drug.

| Panel | Kinases | Test | Compounds |
|-------|---------|------|-----------|
| **scanMAX** | 468 kinases | Single concentration (1 uM) | (R,S)-genmol_119 |
| **KdELECT** | Top 10-20 hits from scanMAX | Full Kd determination | (R,S)-genmol_119 |

### Recommended Provider
- **Eurofins DiscoverX** (San Diego, CA) -- industry standard, most published
  - scanMAX panel (468 kinases, single compound): **$7,000-12,000**
  - KdELECT follow-up (20 kinases): **$4,000-6,000**
  - Turnaround: 2-3 weeks (scanMAX), 5 days (KdELECT)

### 3B: Cardiac Safety -- hERG

**Purpose**: The ADMET profile flagged AMBER for hERG risk. This MUST be resolved before
any in vivo work.

| Assay | Method | Go/No-Go Threshold |
|-------|--------|-------------------|
| hERG binding (initial) | Fluorescence polarization | IC50 > 10 uM = GREEN |
| hERG patch-clamp (if needed) | Automated (QPatch/SyncroPatch) | IC50 > 30x therapeutic dose |

### Recommended CROs

| CRO | Location | Platform | Est. Cost | Timeline |
|-----|----------|----------|-----------|----------|
| **Metrion Biosciences** | Cambridge, UK | QPatch HTX | $3,000-5,000/compound | 2 weeks |
| **Reaction Biology** | Malvern, PA | SyncroPatch 384PE | $2,500-5,000/compound | 2 weeks |
| **Cyprotex (Evotec)** | Macclesfield, UK | QPatch/Predictor | $2,000-4,000/compound | 2 weeks |

### 3C: CYP450 Inhibition Panel

**Purpose**: Assess drug-drug interaction risk. Critical for combination with risdiplam
(which is CYP3A4 substrate).

| CYP Isoform | Importance | Go/No-Go |
|-------------|-----------|----------|
| CYP3A4 | Risdiplam interaction | IC50 > 10 uM |
| CYP2D6 | Polymorphic, CNS drugs | IC50 > 10 uM |
| CYP2C9 | Common interaction | IC50 > 10 uM |
| CYP2C19 | Polymorphic | IC50 > 10 uM |
| CYP1A2 | CNS relevance | IC50 > 10 uM |

**CRO**: Cyprotex (Evotec) or Pharmaron -- standard 5-CYP panel: **$1,500-3,000/compound**

### Estimated Cost (Stage 3 total): $18,000-35,000
- KINOMEscan: $11,000-18,000
- hERG: $3,000-5,000
- CYP450 panel: $1,500-3,000
- Buffer for follow-up: $2,500-9,000

### Timeline: 3-4 weeks

---

## Stage 4: Cell-Based Functional Assays (Month 4-6)

### 4A: SMA Motor Neuron iPSC Assays

**Purpose**: Demonstrate that genmol_119 rescues the ROCK-LIMK2-Cofilin pathway defect
in disease-relevant human cells.

| Assay | Readout | Expected Effect | Reference |
|-------|---------|-----------------|-----------|
| **p-Cofilin rescue** | Western blot / ELISA | Reduced p-CFL2 in SMA MNs | Bowerman 2012 |
| **Neurite outgrowth** | IncuCyte/ImageXpress | Increased neurite length/branching | Key SMA phenotype |
| **NMJ formation** | Co-culture MN + myotubes, AChR clustering | Improved NMJ maturation | Yoshida 2015 |
| **Cell viability** | CellTiter-Glo | No toxicity at therapeutic dose | Safety |
| **SMN level** | ELISA | Expected: no change (pathway-independent) | Bowerman 2012 |

**iPSC lines needed**:
- SMA Type I patient iPSC-derived motor neurons (e.g., from Coriell, GM09677)
- Isogenic corrected control line
- Healthy control motor neurons

### Recommended CROs / Collaborators

| Provider | Location | Capability | Est. Cost |
|----------|----------|-----------|-----------|
| **iPS Academia Japan** | Kyoto, Japan | iPSC-MN differentiation | Collaboration |
| **Ncardia** | Leiden, Netherlands | iPSC disease models, HTS | $30,000-60,000 |
| **Charles River (Cellero)** | Cleveland, OH | iPSC-MN characterization | $25,000-50,000 |
| **AxoL Biosciences** | Cambridge, UK | iPSC-derived motor neurons | $15,000-30,000 (cells only) |
| **Academic collaboration** | e.g., Leipzig / Hallermann lab | Custom NMJ assay | $10,000-25,000 (materials) |

**Note**: An academic collaboration with the Hallermann lab (Leipzig) or a similar SMA-focused
neuroscience group would significantly reduce costs and add scientific credibility.

### 4B: Combination Studies

| Combination | Rationale | Readout |
|------------|-----------|---------|
| genmol_119 + risdiplam | SMN restoration + actin rescue | Synergy (Bliss/Loewe) |
| genmol_119 + nusinersen (ASO) | Alternative SMN + actin | Synergy |
| genmol_119 alone vs fasudil alone | Enantiomer advantage | Head-to-head comparison |

### Estimated Cost (Stage 4 total): $40,000-90,000
- iPSC-MN generation and differentiation: $15,000-30,000
- Functional assays (3-4 assays): $15,000-35,000
- Combination studies: $10,000-25,000

### Timeline: 6-10 weeks (iPSC differentiation takes 4-6 weeks alone)

---

## Stage 5: In Vivo Efficacy & Pharmacokinetics (Month 6-12)

### 5A: Mouse Pharmacokinetics (Month 6-7)

**Purpose**: Confirm BBB penetration and establish PK parameters in vivo.

| Study | Design | Endpoints |
|-------|--------|-----------|
| **Single-dose PK** | 3 dose levels (10, 30, 100 mg/kg), oral gavage, n=3/group | Plasma + brain Cmax, AUC, t1/2, brain:plasma ratio |
| **Multi-dose PK** | 30 mg/kg BID x 7 days, oral gavage | Steady-state levels, accumulation |
| **PAMPA-BBB confirmation** | In vitro parallel | Pe values, correlation with in vivo |

**Key metrics for go/no-go**:
- Brain:plasma ratio > 0.3 (target for CNS drug)
- Oral bioavailability > 20%
- t1/2 > 2 hours (twice-daily dosing feasible)

### Recommended CROs for PK

| CRO | Location | Est. Cost | Timeline |
|-----|----------|-----------|----------|
| **Pharmaron** | Beijing / Baltimore | $15,000-25,000 | 3-4 weeks |
| **Charles River** | Multiple global | $20,000-35,000 | 3-4 weeks |
| **Labcorp Drug Development** | Multiple | $18,000-30,000 | 3-4 weeks |
| **Cyprotex (Evotec)** | UK | $8,000-15,000 (PAMPA only) | 1-2 weeks |

### 5B: SMA Mouse Model Efficacy (Month 7-12)

**Purpose**: Demonstrate therapeutic benefit in a validated SMA animal model.
**Study design modeled on Bowerman et al. 2012 (PMID 22397316).**

#### Mouse Model Selection

| Model | Genotype | Severity | Lifespan | Advantage |
|-------|----------|----------|----------|-----------|
| **Smn2B/-** | Smn2B knock-in | Intermediate | ~28 days | Used by Bowerman; longer window for intervention |
| **SMNDELTA7** (JAX #005025) | SMN2+/+;SMNdelta7+/+;mSmn-/- | Intermediate-severe | ~14 days | Most published SMA model |
| **Smn-/-;SMN2+/+** (JAX #005024) | Severe Type I | Severe | ~5 days | Too short for chronic dosing |

**Recommended**: **Smn2B/-** (same as Bowerman 2012) for direct comparison with fasudil data.

#### Efficacy Study Design (Based on Bowerman 2012)

| Parameter | Design |
|-----------|--------|
| **Groups** | (1) WT untreated (n=10), (2) Smn2B/+ vehicle (n=10), (3) Smn2B/- vehicle (n=15), (4) Smn2B/- genmol_119 30mg/kg BID (n=15), (5) Smn2B/- genmol_119 + risdiplam (n=15), (6) Smn2B/- fasudil 30mg/kg BID (n=10, positive control) |
| **Route** | Oral gavage |
| **Dosing** | P3-P21 (postnatal day 3 to 21), 30 mg/kg twice daily |
| **Primary endpoint** | Survival (Kaplan-Meier, log-rank test) |
| **Secondary endpoints** | Body weight, righting reflex, muscle fiber cross-section area, NMJ maturation (AChR clustering), motor neuron counts (spinal cord L1-L5), SMN protein levels (ELISA) |
| **Electrophysiology** | CMAP (compound muscle action potential), MUNE if available |
| **Tissue collection** | Spinal cord, gastrocnemius, quadriceps, heart, brain at endpoint |
| **Histology** | H&E, immunofluorescence (ChAT, SMN, p-cofilin, bungarotoxin) |

#### Go/No-Go Criteria for Efficacy

| Endpoint | Minimum for "Go" | Ideal |
|----------|------------------|-------|
| Survival extension | >20% increase vs vehicle | >40% (fasudil achieved ~30%) |
| Body weight | Significant improvement at P14 | Normalized growth curve |
| Motor neuron preservation | Trend toward preservation | Significant preservation |
| NMJ maturation | Improved AChR clustering | Near-WT endplate size |
| Combination synergy | Additive with risdiplam | Synergistic (survival) |

### Recommended CROs for SMA Mouse Studies

| CRO | Location | SMA Experience | Est. Cost | Timeline |
|-----|----------|---------------|-----------|----------|
| **Jackson Laboratory (JAX)** | Bar Harbor, ME | Gold standard for SMA mice, breeding colony, full phenotyping | $80,000-150,000 | 4-6 months |
| **Charles River** | Multiple | Neuroscience CRO, SOD1/TDP-43 experience | $60,000-120,000 | 3-5 months |
| **Psychogenics** | Paramus, NJ | CNS phenotyping, SmartCube | $50,000-100,000 | 3-5 months |
| **Academic collaboration** | Leipzig (Hallermann) / Ottawa (Bhatt, Bhattacharya) | SMA mouse colony, published expertise | $30,000-60,000 | 4-6 months |

**Strong recommendation**: Jackson Laboratory (JAX) In Vivo Services. They maintain SMA mouse
colonies, have published SMA efficacy study protocols, and offer full phenotyping including
survival, motor function, NMJ analysis, and electrophysiology. JAX is the source of both the
SMNDELTA7 (005025) and Smn2B models used in SMA research.

### Estimated Cost (Stage 5 total): $100,000-250,000
- PK study: $20,000-35,000
- SMA mouse efficacy study: $80,000-200,000
- Histology & analysis: $10,000-15,000

### Timeline: 4-6 months

---

## Stage 6: IND-Enabling Studies (Month 12-24)

### 6A: GLP Toxicology (Month 12-18)

| Study | Species | Duration | Design |
|-------|---------|----------|--------|
| **28-day repeat-dose** | Rat | 28 days + 14-day recovery | 3 dose levels + control, n=10/sex/group |
| **28-day repeat-dose** | Dog or NHP | 28 days + 14-day recovery | 3 dose levels + control, n=3/sex/group |
| **Genetic toxicology** | In vitro/in vivo | Ames, chromosomal aberration, micronucleus | Standard battery |
| **Safety pharmacology** | Rat + dog | CNS (Irwin), cardiovascular (telemetry), respiratory | ICH S7A compliant |
| **Reproductive toxicology** | Rat | Segment II (embryo-fetal) | If pediatric indication |

### Recommended CROs for GLP Tox

| CRO | Location | Specialty | Est. Cost |
|-----|----------|-----------|-----------|
| **Labcorp Drug Development** | Multiple global | Full IND-enabling package | $1.5M-2.5M |
| **Charles River** | Multiple global | Integrated tox + PK | $1.2M-2.0M |
| **Inotiv (Bioanalytical Systems)** | West Lafayette, IN | Rodent GLP tox | $800K-1.5M |
| **WuXi AppTec** | Suzhou, China | Cost-effective GLP | $600K-1.2M |

### 6B: CMC (Chemistry, Manufacturing, Controls) (Month 12-20)

| Activity | Description | Est. Cost |
|----------|-------------|-----------|
| Process development | Scalable synthesis route, >99% ee | $100,000-200,000 |
| Analytical method development | HPLC, stability-indicating methods | $50,000-100,000 |
| Formulation development | Oral dosage form (capsule/tablet) | $80,000-150,000 |
| Stability studies | ICH conditions, 6-month accelerated | $30,000-60,000 |
| GMP batch manufacturing | Drug substance (1-5 kg) | $200,000-500,000 |
| Drug product manufacture | GMP capsules/tablets for Phase 1 | $100,000-250,000 |

### 6C: IND Filing (Month 20-24)

| Component | Description |
|-----------|-------------|
| Module 1 | Administrative (cover letter, FDA Form 1571/1572) |
| Module 2 | Summaries (quality, nonclinical, clinical overview) |
| Module 3 | Quality (CMC data, drug substance/product specs) |
| Module 4 | Nonclinical (pharmacology, PK, toxicology reports) |
| Module 5 | Clinical (Phase 1 protocol, Investigator's Brochure) |

**Regulatory consultant cost**: $100,000-200,000
**IND preparation & filing**: $50,000-100,000

### Estimated Cost (Stage 6 total): $2,500,000-5,000,000
- GLP toxicology: $1,200,000-2,500,000
- CMC: $560,000-1,260,000
- Regulatory: $150,000-300,000

### Timeline: 12-18 months

---

## Estimated Total Budget

| Stage | Activity | Low Estimate | High Estimate | Timeline |
|-------|----------|-------------|---------------|----------|
| **1** | Chemical synthesis | $8,000 | $25,000 | Month 1-2 |
| **2** | In vitro binding (SPR + IC50) | $15,000 | $35,000 | Month 2-3 |
| **3** | Selectivity & safety | $18,000 | $35,000 | Month 3-4 |
| **4** | Cell-based functional | $40,000 | $90,000 | Month 4-6 |
| **5** | In vivo PK + efficacy | $100,000 | $250,000 | Month 6-12 |
| **6** | IND-enabling | $2,500,000 | $5,000,000 | Month 12-24 |
| | | | | |
| **TOTAL** | **Hit to IND** | **$2,681,000** | **$5,435,000** | **24 months** |

### Cost by Decision Gate

| Gate | Cumulative Spend | Decision |
|------|-----------------|----------|
| **Gate 1: Binding confirmed** | ~$50,000 | Does (R,S) bind LIMK2 with Kd < 500 nM? |
| **Gate 2: Selectivity clean** | ~$85,000 | S-score < 0.1, hERG clear, CYP clear? |
| **Gate 3: Cells work** | ~$175,000 | p-Cofilin rescue + neurite outgrowth in SMA iPSC-MNs? |
| **Gate 4: Mice respond** | ~$400,000 | Survival extension + BBB penetration confirmed? |
| **Gate 5: IND filed** | ~$3-5M | GLP tox clean, GMP material ready? |

**Critical insight**: You spend only ~$175,000 before knowing if the compound works in
disease-relevant cells. If it fails at Gate 1-3, losses are manageable. The major
investment ($2.5-5M) only triggers after in vivo proof-of-concept.

---

## Available Grants & Funding Sources

### Tier 1: SMA-Specific (Highest Relevance)

| Funder | Program | Amount | Deadline | Notes |
|--------|---------|--------|----------|-------|
| **Cure SMA** | Basic Research Grant | Up to $140,000/year | **October 3, 2025** | Specifically funds "non-SMN approaches with combination potential." Our ROCK/LIMK2 approach fits perfectly. Contact: Jackie Glascock, PhD (jglascock@curesma.org) |
| **Cure SMA** | Drug Discovery Program | $250,000-500,000 | Rolling | Preclinical drug programs towards IND. $20M invested in 12 programs to date. |
| **SMA Foundation** | Translational Research | $500,000-2,000,000 | Rolling | Leading SMA funder ($150M total). Focus on late translational and clinical. Would fund Stages 4-6. |

### Tier 2: NIH/FDA Rare Disease

| Funder | Program | Amount | Deadline | Notes |
|--------|---------|--------|----------|-------|
| **NCATS** | Preclinical Proof of Concept for Rare Diseases (R21) | $275,000/2 years | **June 2, 2026** | RFA-TR-25-002. Funds efficacy in established preclinical model. Perfect for Stages 2-5. |
| **NCATS** | TRND (Therapeutics for Rare and Neglected Diseases) | IND-enabling support | Rolling | Full preclinical-to-IND partnership. NCATS provides resources, expertise, and funding. |
| **FDA** | Orphan Products Clinical Studies (R01) | $500K-1.5M/4 years | **May 19, 2026** | RFA-FD-25-020. For clinical trials of orphan products. Relevant post-IND. |
| **NIH/NINDS** | R01/R21 | Standard R01/R21 | Standard cycles | SMA is NINDS priority; ROCK pathway is novel angle |
| **NCATS** | New Therapeutic Uses (Drug Repurposing) | Variable | Rolling | H-1152 is a known compound with safety data -- repurposing argument is strong |

### Tier 3: European Funding

| Funder | Program | Amount | Deadline | Notes |
|--------|---------|--------|----------|-------|
| **EMA** | Orphan Designation | Fee waivers + 10yr exclusivity | Any time | SMA qualifies (prevalence <5/10,000). Free protocol assistance. |
| **ERDERA** | European Rare Disease Research Partnership | Up to EUR 380M total pool | 2024-2031 | Horizon Europe co-funded, 180 partners from 37 countries |
| **DFG** | German Research Foundation | Standard funding | Standard cycles | German academic labs (Leipzig collaboration) |
| **BMBF** | German Ministry of Education and Research | Project-dependent | Various | Rare disease drug development programs |

### Tier 4: Private / Venture

| Source | Type | Amount | Notes |
|--------|------|--------|-------|
| **SBIR/STTR** | NIH Phase I/II | $275K (Phase I), $1.5M (Phase II) | Requires small business entity |
| **Orphan drug investors** | Venture capital | $2-10M seed | BioVenture Hub, LifeSci Venture Partners |
| **Patient advocacy** | Philanthropic | Variable | Families of SMA patients (high engagement community) |

### Recommended Funding Strategy

1. **Immediate (Stages 1-3, ~$85K)**: Self-fund or small institutional grant. Low enough for academic startup budget.
2. **Near-term (Stage 4, ~$90K)**: Apply to **Cure SMA Basic Research Grant** (deadline Oct 2025) and **NCATS R21** (deadline Jun 2026).
3. **Medium-term (Stage 5, ~$250K)**: **SMA Foundation** translational grant or NCATS TRND partnership.
4. **Long-term (Stage 6, ~$3-5M)**: **TRND IND-enabling partnership** + venture funding or pharma licensing deal.

---

## Recommended CROs -- Summary by Capability

### One-Stop-Shop Options (Multiple Stages)

| CRO | Stages Covered | Location | Advantage |
|-----|---------------|----------|-----------|
| **Charles River** | 2, 3, 4, 5, 6 | Global | Full discovery-to-IND, neuroscience expertise |
| **WuXi AppTec** | 1, 2, 3, 5, 6 | China + USA | Cost-effective, GLP capable |
| **Pharmaron** | 1, 2, 3, 5, 6 | China + USA + UK | Integrated, kinase profiling expertise |
| **Labcorp Drug Development** | 3, 5, 6 | Global | GLP toxicology leader |

### Specialist Options (Best-in-Class per Stage)

| Stage | Recommended CRO | Why |
|-------|-----------------|-----|
| **1: Synthesis** | **Enamine** (resolution) or **Chiroblock** (de novo) | European, academic-friendly, chiral expertise |
| **2: SPR** | **Reaction Biology** | Biacore 8K+, LIMK2 in catalog, fast turnaround |
| **2: IC50** | **Reaction Biology** | HotSpot radiometric, 10 business day turnaround |
| **3: KINOMEscan** | **Eurofins DiscoverX** | Industry standard, 468 kinases, most published |
| **3: hERG** | **Metrion Biosciences** | Cardiac safety specialists, QPatch HTX |
| **3: ADME** | **Cyprotex (Evotec)** | PAMPA, CYP, permeability panels |
| **4: iPSC-MN** | **Ncardia** or **academic collab** | SMA iPSC disease models |
| **5: SMA mice** | **Jackson Laboratory (JAX)** | SMA mouse colony, published protocols, gold standard |
| **6: GLP tox** | **Charles River** or **WuXi** | Cost vs. quality trade-off |

---

## Timeline Gantt Chart (Text Format)

```
Month:  1    2    3    4    5    6    7    8    9    10   11   12   ...  18   24
        |----|----|----|----|----|----|----|----|----|----|----|----|    |----|
STAGE 1 [====]                                                    Synthesis
STAGE 2      [========]                                           SPR + IC50
STAGE 3           [========]                                      Selectivity
  Gate 1     *                                                    Binding?
  Gate 2               *                                          Clean profile?
STAGE 4                [================]                         Cell assays
  Gate 3                         *                                iPSC rescue?
STAGE 5                              [==========================] In vivo
  5A PK                              [====]                       PK study
  5B Efficacy                              [====================] SMA mice
  Gate 4                                              *           Efficacy?
STAGE 6                                                    [===============]
  6A GLP tox                                               [=========]
  6B CMC                                               [============]
  6C IND                                                         [====]
  Gate 5                                                              * IND!
```

---

## Risk Assessment & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| (R,S)-enantiomer does NOT bind LIMK2 | Medium | FATAL | Test at Gate 1 (only $50K invested). Fall back to ROCK2-only rationale. |
| hERG inhibition (flagged AMBER) | Medium | HIGH | Test early (Stage 3). If fails, medicinal chemistry to reduce basicity. |
| Poor oral bioavailability | Low | HIGH | H-1152 parent has good oral PK. PK study (Stage 5A) will confirm. |
| SMA mouse model shows no benefit | Medium | HIGH | Fasudil showed benefit at same dose -- genmol_119 should be at least equivalent. Include fasudil as positive control. |
| CYP3A4 inhibition (risdiplam DDI) | Medium | MODERATE | CYP panel (Stage 3). If interaction, adjust combination dosing. |
| Synthesis fails to achieve >99% ee | Low | MODERATE | Multiple chiral resolution methods available (HPLC, crystallization). |
| Funding not secured | Medium | HIGH | Stage-gated approach allows incremental funding. Stages 1-3 are self-fundable. |

---

## Key References

1. **Bowerman M, et al.** (2012) "Fasudil improves survival and promotes skeletal muscle development in a mouse model of spinal muscular atrophy." *BMC Medicine* 10:24. PMID: 22397316
   - *The foundational study for ROCK inhibition in SMA. Used Smn2B/- mice, 30 mg/kg BID fasudil from P3-P21. Our study design directly mirrors this.*

2. **Bowerman M, et al.** (2014) "ROCK inhibition as a therapy for spinal muscular atrophy: understanding the repercussions on multiple cellular targets." *Front Neurosci* 8:271.
   - *Review of ROCK pathway in SMA, including LIMK and cofilin downstream effects.*

3. **Koch JC, et al.** (2024) "Fasudil in amyotrophic lateral sclerosis (ROCK-ALS): a phase 2, randomized, double-blind, placebo-controlled trial." *Lancet Neurology*.
   - *Phase 2 safety data for fasudil in motor neuron disease. n=120, well-tolerated, signals of motor unit preservation.*

4. **GSE208629** -- SMA single-cell RNA-seq (Smn2B/- mouse motor neurons)
   - *Our analysis showing LIMK2 (not LIMK1) is the relevant kinase, CFL2 upregulated +1.83x.*

5. **genmol_119 ADMET profile** -- This repository, `docs/research/admet-genmol119-deep-profile-2026-03-24.md`
   - *Full computational ADMET characterization of the (R,S)-enantiomer.*

---

## Appendix: Regulatory Pathway Considerations

### Orphan Drug Designation (ODD)
- **FDA**: SMA affects ~1 in 10,000 births (<200,000 US prevalence). genmol_119 qualifies.
- **EMA**: SMA prevalence <5 in 10,000. Qualifies for EU orphan designation.
- **Benefits**: Tax credits (25% US, reduced fees EU), market exclusivity (7yr US, 10yr EU), protocol assistance.
- **Timing**: Apply after Stage 2 (binding data confirms mechanism).

### Rare Pediatric Disease (RPD) Designation
- SMA is predominantly pediatric onset.
- **Priority Review Voucher (PRV)** upon approval -- transferable, worth $100M+.

### Fast Track / Breakthrough Therapy
- If Stage 5 shows significant survival benefit, apply for Breakthrough Therapy Designation.
- Grants rolling review and intensive FDA guidance.

### 505(b)(2) Pathway
- genmol_119 is a specific enantiomer of H-1152, which has extensive published safety data.
- May reference existing pharmacology/toxicology data, reducing IND-enabling burden.
- **This could save 6-12 months and $500K-1M in GLP studies.**

---

## Next Steps (Immediate Actions)

1. **Contact Enamine or BOC Sciences** for chiral resolution quote on racemic H-1152 (1 week)
2. **Contact Reaction Biology** for LIMK2 + ROCK2 IC50 quote and SPR quote (1 week)
3. **Draft Cure SMA Basic Research Grant** application (deadline October 3, 2025)
4. **Prepare NCATS R21 application** for Preclinical Proof of Concept (deadline June 2, 2026)
5. **Reach out to Bowerman lab** (University of Ottawa) for potential academic collaboration
6. **File provisional patent** on (R,S)-H-1152 as LIMK2 inhibitor for SMA (before any publication)

---

*This pipeline document is a living plan. Costs are estimates based on 2024-2026 CRO pricing
research and industry benchmarks. Actual quotes should be obtained before committing to each stage.
All costs exclude overhead, personnel, and indirect costs that would apply in an academic setting.*
