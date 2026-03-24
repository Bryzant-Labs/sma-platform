# STRING-DB Network Expansion: ROCK-LIMK2-CFL2 Pathway

**Date**: 2026-03-25
**Source**: STRING-DB v12.0 (Homo sapiens, species 9606)
**Query proteins**: LIMK2, ROCK2, CFL2, ROCK1, PFN2, RAC1
**Parameters**: required_score >= 700, limit 50 per query

---

## Network Statistics

| Metric | Value |
|--------|-------|
| Total unique interaction partners | 148 |
| Total unique edges | 216 |
| Hub nodes (2+ connections) | 52 |
| Hub nodes already in our 68 targets | 2 |
| NEW hub discoveries | 50 |
| New druggable hubs | 19 |
| Existing targets validated by network | 6 |
| Total new interaction partners | 142 |

---

## Major Hub Nodes (connected to 3+ query proteins)

These proteins sit at the center of the ROCK-LIMK-CFL pathway and represent the highest-priority new candidates.

| Gene | Connections | Connected To | Score | Druggability | In DB? |
|------|------------|-------------|-------|--------------|--------|
| RHOA | 4 | CFL2, LIMK2, ROCK1, ROCK2 | 0.999 | GTPase/GPCR | **No** |
| LIMK1 | 4 | CFL2, LIMK2, ROCK1, ROCK2 | 0.998 | kinase | Yes |
| CFL1 | 4 | CFL2, LIMK2, ROCK1, ROCK2 | 0.995 | unknown | **No** |
| RHOC | 4 | CFL2, LIMK2, ROCK1, ROCK2 | 0.954 | GTPase/GPCR | **No** |
| RND3 | 3 | CFL2, ROCK1, ROCK2 | 0.999 | GTPase/GPCR | **No** |
| CDC42 | 3 | CFL2, RAC1, ROCK1 | 0.935 | GTPase/GPCR | **No** |

### Key Findings - Major Hubs

1. **RHOA** (score 0.999, 4 connections): Master GTPase upstream of ROCK1/ROCK2. Activated RHOA signals through ROCK kinases to phosphorylate LIMK2, which then inactivates CFL2. This is THE upstream activator of the entire pathway. Not directly druggable but targetable via GEF/GAP modulators.

2. **CFL1** (score 0.995, 4 connections): Cofilin-1, the ubiquitously expressed paralog of CFL2. Both are LIMK substrates. CFL1 is the dominant form in most cells; CFL2 is muscle-enriched. Their shared regulation by LIMK1/2 suggests CFL1 status may compensate for CFL2 changes in SMA.

3. **RHOC** (score 0.954, 4 connections): Another Rho GTPase that activates ROCK kinases. RHOC is particularly relevant in neuronal contexts and cell migration.

4. **RND3/RhoE** (score 0.999, 3 connections): Atypical Rho GTPase that INHIBITS ROCK1. This is a natural brake on ROCK signaling. If RND3 is downregulated in SMA motor neurons, it could explain ROCK pathway overactivation.

5. **CDC42** (score 0.935, 3 connections): Key regulator of actin polymerization and cell polarity. Works with RAC1 to control filopodia and neuronal growth cones. CDC42 deficiency causes axon guidance defects similar to SMA phenotypes.

---

## New Druggable Hub Targets

These are proteins NOT in our 68 targets that are both hub nodes AND have known drug classes.

| Gene | Type | Connections | Score | Connected To | Therapeutic Relevance |
|------|------|------------|-------|-------------|----------------------|
| RHOA | GTPase/GPCR | 4 | 0.999 | CFL2, LIMK2, ROCK1, ROCK2 | Master switch upstream of ROCK. RhoA inhibitors (C3 transferase, rhosin) exist |
| RHOC | GTPase/GPCR | 4 | 0.954 | CFL2, LIMK2, ROCK1, ROCK2 | ROCK activator. Same druggability class as RHOA |
| RND3 | GTPase/GPCR | 3 | 0.999 | CFL2, ROCK1, ROCK2 | Natural ROCK inhibitor. Activating RND3 = inhibiting ROCK (novel strategy) |
| CDC42 | GTPase/GPCR | 3 | 0.935 | CFL2, RAC1, ROCK1 | Growth cone regulator. CDC42 activators could restore axon growth |
| PAK1 | kinase | 2 | 0.999 | LIMK2, RAC1 | p21-activated kinase 1. PAK inhibitors (FRAX597, PF-3758309) in clinical trials |
| PPP1R12A | phosphatase | 2 | 0.996 | ROCK1, ROCK2 | MYPT1 (myosin phosphatase). ROCK substrate. Phospho-MYPT1 = ROCK activity biomarker |
| PAK2 | kinase | 2 | 0.983 | LIMK2, RAC1 | PAK family kinase. Same inhibitors as PAK1. Role in neuronal survival |
| PTEN | phosphatase | 2 | 0.954 | ROCK1, ROCK2 | Tumor suppressor phosphatase. PTEN inhibitors (bpV, SF1670) enhance PI3K/AKT/mTOR |
| RHOB | GTPase/GPCR | 2 | 0.946 | ROCK1, ROCK2 | Rho GTPase with unique endosomal localization. May affect SMN trafficking |
| PAK4 | kinase | 2 | 0.943 | CFL2, LIMK2 | Activates LIMK2 directly. PAK4 inhibitors could reduce LIMK2 activity in SMA |
| PAK6 | kinase | 2 | 0.934 | LIMK2, RAC1 | Brain-enriched PAK. Potential role in motor neuron LIMK regulation |
| PAK3 | kinase | 2 | 0.931 | LIMK2, RAC1 | Neuron-enriched PAK. X-linked intellectual disability gene. PAK3 mutations cause MN defects |
| PPP1CB | phosphatase | 2 | 0.928 | ROCK1, ROCK2 | PP1-beta catalytic subunit. Counteracts ROCK phosphorylation. Activators = ROCK-like effect |
| MAPK3 | kinase | 2 | 0.927 | ROCK1, ROCK2 | ERK1. Cross-talks with ROCK pathway. MEK inhibitors well-characterized |
| PPP1CC | phosphatase | 2 | 0.926 | ROCK1, ROCK2 | PP1-gamma catalytic subunit. Highly expressed in neurons |
| PPP1CA | phosphatase | 2 | 0.923 | ROCK1, ROCK2 | PP1-alpha catalytic subunit. Dephosphorylates cofilin (activates it) |
| MAPK1 | kinase | 2 | 0.922 | ROCK1, ROCK2 | ERK2. Major MAPK/ERK pathway effector. Cross-regulates ROCK signaling |
| SRC | kinase | 2 | 0.856 | CFL2, RAC1 | Non-receptor tyrosine kinase. Dasatinib, bosutinib FDA-approved. Regulates actin dynamics |
| RND1 | GTPase/GPCR | 2 | 0.796 | ROCK1, ROCK2 | Atypical GTPase. Inhibits RhoA signaling. Axon guidance roles |

---

## Existing Targets Validated by STRING Network

These targets from our 68 are confirmed to directly interact with ROCK-LIMK2-CFL2 pathway members, strengthening their inclusion.

| Gene | Connections | Score | Connected To |
|------|------------|-------|-------------|
| LIMK1 | 4 | 0.998 | CFL2, LIMK2, ROCK1, ROCK2 |
| ACTG1 | 2 | 0.996 | CFL2, PFN2 |
| PFN1 | 1 | 0.967 | CFL2 |
| ABI2 | 1 | 0.966 | RAC1 |
| CASP3 | 1 | 0.959 | ROCK1 |
| ACTR2 | 1 | 0.936 | CFL2 |

LIMK1 is the strongest validation: it connects to 4 of 6 query proteins (score 0.998), confirming the ROCK-LIMK-CFL axis is tightly coupled.

---

## Pathway Clusters Identified

### Cluster 1: RhoA-ROCK-LIMK-Cofilin Core (the actin dynamics axis)
RHOA -> ROCK1/ROCK2 -> LIMK1/LIMK2 -> CFL1/CFL2

This is the canonical signaling cascade. ROCK phosphorylates LIMK, LIMK phosphorylates cofilin (inactivating it), leading to actin stabilization. In SMA, this pathway appears overactivated, causing rigid actin networks that impair motor neuron function.

**Therapeutic strategy**: Inhibit at ROCK (fasudil, ripasudil) or LIMK (LIMKi3, BMS-5) level.

### Cluster 2: PAK-LIMK Branch
PAK1/PAK2/PAK3/PAK4/PAK6 -> LIMK2

PAK kinases provide an alternative activation route for LIMK, independent of ROCK. This means ROCK inhibitors alone may not fully suppress LIMK2 activity. PAK inhibitors could be needed as combination therapy.

**Therapeutic implication**: Dual ROCK+PAK inhibition may be needed to fully suppress LIMK2.

### Cluster 3: RAC1-CDC42-WASL Actin Polymerization
RAC1/CDC42 -> WASL/WAS -> Arp2/3 -> actin branching

This branch promotes actin polymerization (opposite of cofilin's severing). In SMA, both actin stabilization (via ROCK-LIMK-CFL) and actin branching (via RAC1-WASL) may be dysregulated.

### Cluster 4: Myosin Light Chain / Contractility
ROCK1/ROCK2 -> MYL2/MYL9/MYL12A/MYL12B -> actomyosin contractility

ROCK directly phosphorylates myosin light chains, increasing contractility. This is separate from the cofilin branch but equally important for motor neuron axon retraction and NMJ maintenance.

### Cluster 5: Phosphatase Counter-Regulation
PPP1R12A (MYPT1), PPP1CA/PPP1CB/PPP1CC, PTEN

These phosphatases oppose ROCK signaling. ROCK inhibits MYPT1 (PPP1R12A), creating a positive feedback loop. PTEN loss activates PI3K/AKT which cross-inhibits ROCK. Phosphatase activators could be a novel therapeutic angle.

---

## Priority New Targets for Addition to Platform

Based on hub connectivity, druggability, and SMA relevance:

### Tier 1 - Immediate Addition (strong evidence, directly druggable)
1. **RHOA** - Master upstream GTPase. Required to understand pathway regulation.
2. **CFL1** - Cofilin-1 paralog. Essential for interpreting CFL2 data.
3. **PAK1** - Alternative LIMK activator. Clinical inhibitors exist (FRAX597).
4. **PAK4** - Direct LIMK2 activator. PAK4-selective inhibitors in development.
5. **CDC42** - Growth cone regulator. Key for axon dynamics.
6. **PTEN** - Phosphatase, PI3K/AKT/mTOR cross-talk. Clinical compounds available.

### Tier 2 - Strong Candidates (pathway context)
7. **PPP1R12A** (MYPT1) - ROCK activity biomarker. Essential for reading ROCK inhibitor efficacy.
8. **RND3** - Natural ROCK brake. Potential endogenous therapeutic.
9. **SRC** - Tyrosine kinase hub. FDA-approved inhibitors (dasatinib).
10. **CTNNB1** (beta-catenin) - WNT pathway effector, ROCK substrate.

### Tier 3 - Worth Monitoring
11. **RHOB** - Endosomal Rho. May affect SMN protein trafficking.
12. **PAK2/PAK3/PAK6** - Other PAK family members.
13. **MAPK1/MAPK3** (ERK1/2) - MAPK cross-talk with ROCK.
14. **WASL** (N-WASP) - Actin nucleation.

---

## Network Data Files

- Raw STRING-DB responses: `data/string_db/raw_interaction_partners.json`
- Full analysis: `data/string_db/network_analysis.json`
- Graph visualization data: `data/string_db/limk2_rock2_cfl2_network.json` (154 nodes, 216 edges)

---

## Methodological Notes

- STRING-DB v12.0 combines 7 evidence channels: neighborhood, gene fusion, cooccurrence, coexpression, experimental, database, textmining
- Score >= 700 = "high confidence" (STRING definition)
- Limit of 50 partners per query protein to focus on strongest interactors
- Species: Homo sapiens (9606)
- Hub analysis counts how many of our 6 query proteins each partner interacts with
- Druggability classification based on protein family (kinase, phosphatase, GTPase, enzyme)

## Next Steps

1. Add Tier 1 targets to the platform database
2. Query claims DB for any existing SMA evidence on new targets (esp. RHOA, CFL1, PAK1, CDC42)
3. Run DiffDock on PAK1/PAK4 inhibitors against LIMK2 structure
4. Check single-cell expression of RHOA, CFL1, PAK1 in motor neurons (GSE208629, GSE287257)
5. Import STRING edges into graph_edges table for platform visualization
