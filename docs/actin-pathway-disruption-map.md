# Actin Pathway Disruption Map in SMA

**Source**: GSE69175 — iPSC-derived motor neurons from SMA patients vs. controls
**Date**: 2026-03-21
**Status**: Complete pathway reconstruction from transcriptomic + network + literature evidence

---

## Executive Summary

Analysis of GSE69175 reveals **7 co-upregulated actin pathway genes** in SMA motor neurons, forming a densely interconnected network (16/21 possible edges at STRING score > 0.4). This is not random noise — STRING enrichment confirms "Actin cytoskeleton organization" with FDR = 2.1e-07 (all 7/7 genes). The co-upregulation pattern suggests a **coordinated compensatory cytoskeletal rescue program** activated in SMA motor neurons, centered on the Arp2/3 branching pathway, actin dynamics, and endocytosis.

Combined with the landmark finding that PLS3 and CORO1C rescue endocytosis and SMA phenotype in animal models (Hosseinibarkooie et al., 2016), this network represents **the most promising multi-target therapeutic axis** beyond SMN restoration.

---

## The 7-Gene Actin Network

| Gene | Fold Change | FDR (q) | Function | In Platform DB | Claims | PubMed (SMA) |
|------|------------|---------|----------|---------------|--------|-------------|
| **PLS3** | 4.0x | 0.002 | Actin bundling, SMA modifier | YES | 83 | 35 papers |
| **CFL2** | 2.9x | 0.0009 | Actin depolymerization (cofilin-2) | NO | 0 | 1 paper |
| **ACTR2** | 1.8x | 0.002 | Arp2/3 complex subunit (ARP2) | NO | 2 | 0 papers |
| **ACTG1** | 1.6x | 0.0009 | Cytoskeletal gamma-actin | NO | 7 | 0 papers |
| **CORO1C** | 1.6x | 0.027 | Arp2/3 regulator, endocytosis | YES | 14 | 4 papers |
| **ABI2** | 1.5x | 0.014 | Arp2/3 regulator (Abl-interactor 2) | NO | 0 | 0 papers |
| **PFN2** | 1.5x | 0.034 | Actin polymerization (profilin-2) | NO | 4 | 4 papers |

**Key observation**: PLS3 (4.0x) is the most strongly upregulated, consistent with its known role as an SMA protective modifier. CFL2 (2.9x) is second highest and almost unstudied in SMA context.

---

## Protein-Protein Interaction Network (STRING-DB)

### Network Density
- **16 out of 21 possible edges** at combined score > 0.4
- Network density = 0.76 (extremely high for a 7-node network)
- This is a functional module, not a random gene list

### All Pairwise Interactions (Human, score > 0.4)

```
                CORO1C    CFL2    ACTG1    ACTR2    ABI2    PFN2    PLS3
CORO1C            --     0.507   0.451    0.899     -      -      0.818
CFL2            0.507      --    0.996    0.936     -     0.573   0.523
ACTG1           0.451    0.996     --     0.949   0.608   0.753   0.528
ACTR2           0.899    0.936   0.949      --    0.688   0.474   0.511
ABI2              -        -     0.608    0.688     --      -       -
PFN2              -      0.573   0.753    0.474     -       --    0.473
PLS3            0.818    0.523   0.528    0.511     -     0.473     --
```

### Strongest Interactions (Top 5)
1. **CFL2 -- ACTG1**: 0.996 (experimental=0.854, database=0.9) — Direct binding
2. **ACTG1 -- ACTR2**: 0.949 (experimental=0.402, database=0.9) — Arp2/3 complex
3. **CFL2 -- ACTR2**: 0.936 (experimental=0.24, textmining=0.916)
4. **ACTR2 -- CORO1C**: 0.899 (experimental=0.69, textmining=0.65)
5. **CORO1C -- PLS3**: 0.818 (textmining=0.795) — The SMA modifier axis

### Network Hub Analysis
- **ACTG1** = Most connected (6/6 possible edges) — central structural hub
- **ACTR2** = Second hub (6/6 edges) — Arp2/3 enzymatic hub
- **CFL2** = Third hub (5/6 edges) — actin dynamics regulator
- **ABI2** = Most isolated (2 edges) — upstream signaling node

---

## Functional Pathway Map

### Pathway Architecture (5 functional layers)

```
Layer 1: UPSTREAM SIGNALING
  ABI2 (Abl-interactor 2)
    |-- Receives: RHO GTPase signals (CDC42, RAC1)
    |-- Activates: WAVE regulatory complex (WASF1/2/3, CYFIP1/2, BRK1, NCKAP1)
    |-- Feeds into: Arp2/3 activation
    v

Layer 2: ACTIN NUCLEATION (Arp2/3 complex)
  ACTR2 (ARP2) + CORO1C (coronin)
    |-- ACTR2 = core Arp2/3 subunit, nucleates branched actin
    |-- CORO1C = Arp2/3 regulator, controls branch timing
    |-- Together: generate branched actin networks at leading edge
    v

Layer 3: ACTIN DYNAMICS
  CFL2 (cofilin-2) + PFN2 (profilin-2)
    |-- CFL2 = depolymerizes old actin filaments (recycles monomers)
    |-- PFN2 = promotes polymerization of new filaments
    |-- Together: maintain actin treadmilling essential for motility
    v

Layer 4: STRUCTURAL ACTIN
  ACTG1 (gamma-actin)
    |-- The actin monomer itself (cytoplasmic gamma isoform)
    |-- Substrate for all above regulators
    |-- Upregulation = more raw material for cytoskeletal rescue
    v

Layer 5: ACTIN BUNDLING & STABILIZATION
  PLS3 (plastin 3)
    |-- Bundles parallel actin filaments
    |-- Stabilizes mature structures (growth cones, NMJ)
    |-- Direct SMN1/SMN2 interactor (STRING: 0.86/0.83)
    |-- THE proven SMA protective modifier
```

### Critical Functional Enrichments (STRING-DB)

| Category | Term | FDR | Genes |
|----------|------|-----|-------|
| GO Process | Actin cytoskeleton organization | 2.1e-07 | ALL 7/7 |
| GO Process | Supramolecular fiber organization | 1.96e-05 | 6/7 |
| GO Process | Actin filament organization | 3.53e-05 | 5/7 |
| GO Process | Positive regulation of lamellipodium | 0.0007 | ABI2, ACTR2, CORO1C |
| GO Component | Synapse | 0.019 | PFN2, ABI2, ACTR2, CORO1C, ACTG1 |
| GO Component | Postsynapse | 0.019 | PFN2, ABI2, ACTR2, ACTG1 |
| Reactome | RHO GTPases Activate WASPs/WAVEs | 0.00057 | ABI2, ACTR2, ACTG1 |
| Reactome | Regulation of phagocytic cup formation | 0.0014 | ABI2, ACTR2, ACTG1 |
| KEGG | Regulation of actin cytoskeleton | 0.014 | ABI2, CFL2, ACTG1 |
| PMID | SMA modifying genes study | 0.048 | PFN2, PLS3, CORO1C |

**5 of 7 genes localize to synapses** -- directly relevant to NMJ dysfunction in SMA.

---

## SMA Mechanistic Model

### The SMN-Actin-Endocytosis Axis

```
SMN1 loss
    |
    v
Reduced SMN protein
    |
    |--> Impaired beta-actin mRNA transport to growth cones (direct SMN function)
    |--> Profilin-2 (PFN2) increase --> RhoA/ROCK pathway activation (Bowerman 2009)
    |--> Cofilin (CFL2) dysregulation --> aberrant actin dynamics
    |
    v
ACTIN CYTOSKELETON COLLAPSE
    |
    |--> Failed growth cone motility
    |--> Impaired endocytosis (synaptic vesicle recycling)
    |--> NMJ destabilization
    |--> Motor neuron degeneration
    |
    v
COMPENSATORY RESCUE PROGRAM (GSE69175 upregulation)
    |
    |--> PLS3 (4.0x) -- bundles/stabilizes actin, rescues endocytosis
    |--> CFL2 (2.9x) -- recycles actin, maintains treadmilling
    |--> ACTR2 (1.8x) -- more Arp2/3-mediated branching
    |--> ACTG1 (1.6x) -- more actin monomer supply
    |--> CORO1C (1.6x) -- regulates Arp2/3, rescues endocytosis
    |--> ABI2 (1.5x) -- WAVE complex signaling for actin nucleation
    |--> PFN2 (1.5x) -- polymerization fuel (despite RhoA dysregulation)
```

### Why This Matters for SMA

1. **SMN directly translocates beta-actin to axonal growth cones** (confirmed claim, confidence 0.90 in platform)
2. **SMN loss = actin transport failure** at the most vulnerable cellular compartment
3. **The 7-gene upregulation = motor neurons trying to compensate** by increasing actin pathway capacity
4. **PLS3 and CORO1C overexpression RESCUES endocytosis** in SMA models (Wirth lab, PMID: 27499521)
5. **Profilin-2 increase + Plastin-3 decrease** observed in SMA mice (Bowerman 2009, PMID: 19497369)

---

## Literature Evidence

### Key Papers

| PMID | Year | Key Finding | Genes |
|------|------|-------------|-------|
| 27499521 | 2016 | PLS3+CORO1C overexpression rescues endocytosis in SMA, extends survival from 14 to >250 days | PLS3, CORO1C |
| 19497369 | 2009 | PFN2 increase + PLS3 decrease in SMA mice; RhoA/ROCK pathway dysregulation | PFN2, PLS3 |
| 36071912 | 2022 | First expression study of PFN2, CORO1C, ZPR1 in SMA patients | PFN2, PLS3, CORO1C |
| 28684086 | 2017 | PLS3 and CORO1C as protective modifiers; SMA modifier therapy concept | PLS3, CORO1C |

### PubMed Coverage (gene + "spinal muscular atrophy")
- **PLS3**: 35 papers (well-studied SMA modifier)
- **PFN2**: 4 papers (emerging, linked to RhoA/ROCK)
- **CORO1C**: 4 papers (established via PLS3 interactome)
- **CFL2**: 1 paper (almost entirely unstudied in SMA)
- **ACTG1**: 0 papers (NOVEL — no SMA literature)
- **ACTR2**: 0 papers (NOVEL — no SMA literature)
- **ABI2**: 0 papers (NOVEL — no SMA literature)

---

## Novel Targets: Research Opportunities

### Priority 1: CFL2 (Cofilin-2) — Highest Novelty-Impact Score

- **FC = 2.9x** (second highest upregulation)
- **q = 0.0009** (most significant after ACTG1)
- **Only 1 SMA paper** (included in an NMD gene panel, not functionally studied)
- **STRING hub**: 5/6 edges, including direct interaction with ACTG1 (0.996)
- **Known biology**: Actin depolymerizing factor; regulated by LIMK1/2 and SSH1/3 phosphatases
- **Therapeutic angle**: LIMK inhibitors (e.g., LIMKi 3) could modulate CFL2 activity
- **First-shell interactors**: LIMK1 (1.0), LIMK2 (0.99), SSH1 (0.99), CTTN (1.0)
- **Hypothesis**: CFL2 upregulation maintains actin treadmilling at growth cones; pharmacological enhancement of CFL2 activity via SSH1 activation or LIMK inhibition could augment the compensatory program

### Priority 2: ACTG1 (Gamma-Actin) — Structural Foundation

- **FC = 1.6x, q = 0.0009** (highest statistical significance in the set)
- **0 SMA papers** (completely novel)
- **Network hub**: 6/6 edges (most connected node)
- **First-shell**: CFL1 (1.0), PFN1 (0.99), MYH14 (0.99), VCL (0.99)
- **Known**: Mutations cause Baraitser-Winter syndrome (cortical malformations), DFNA20 deafness
- **Hypothesis**: ACTG1 upregulation increases raw actin monomer pool; may be the rate-limiting supply for the entire compensatory program

### Priority 3: ACTR2 (Arp2/3 Complex Subunit) — Branching Engine

- **FC = 1.8x, q = 0.002**
- **0 SMA papers** (novel)
- **Network hub**: 6/6 edges
- **First-shell**: All Arp2/3 subunits (ARPC2, ARPC3, ARPC4, ARPC5, etc.) at score 1.0
- **Known**: Core catalytic subunit of Arp2/3 complex; essential for branched actin
- **Therapeutic angle**: Arp2/3 activators (e.g., N-WASP-derived peptides) could amplify compensatory branching
- **Hypothesis**: ACTR2 upregulation increases Arp2/3 capacity for branched actin at growth cones and NMJ

### Priority 4: ABI2 — Upstream Signaling Amplifier

- **FC = 1.5x, q = 0.014**
- **0 SMA papers** (novel)
- **Only 2 edges** (most isolated in the network)
- **First-shell**: WAVE complex members all at score 1.0 (WASF1, CYFIP1, BRK1, NCKAP1)
- **Known**: Adaptor protein linking Rac1/Cdc42 signaling to WAVE complex and Arp2/3 activation
- **Hypothesis**: ABI2 upregulation amplifies upstream Rho GTPase signaling to compensate for impaired actin nucleation

---

## Broader Actin Pathway Context in the Platform

The SMA Research Platform contains extensive actin-related evidence:

| Term | Claims |
|------|--------|
| actin | 149 |
| cytoskeleton | 69 |
| myosin | 48 |
| profilin | 33 |
| ROCK | 29 |
| plastin | 24 |
| Rac1 | 7 |
| cofilin | 5 |
| Cdc42 | 5 |
| Rho GTPase | 2 |
| Arp2/3 | 1 |

**Total actin-related claims: ~370** across the platform, representing one of the most evidence-rich pathways in the entire SMA research corpus.

---

## First-Shell Network Extensions

Key genes that bridge the 7-gene network to broader SMA biology:

| Gene | Connections to 7-Gene Set | Score | SMA Relevance |
|------|--------------------------|-------|---------------|
| **ACTB** (beta-actin) | PFN2, CFL2, ACTG1 | 0.78-1.0 | SMN directly translocates ACTB mRNA to growth cones |
| **WASL** (N-WASP) | CFL2, ACTR2, ACTG1 | 0.98-1.0 | Arp2/3 activator at growth cones |
| **SMN1** | PLS3 | 0.86 | THE SMA gene — direct PLS3 interaction |
| **SMN2** | PLS3 | 0.83 | SMA copy gene — PLS3 modifies its phenotype |
| **LIMK1** | CFL2 | 1.0 | Phosphorylates/inactivates cofilin; drug target |
| **CORO1B** | CORO1C | 0.92 | Coronin family member, growth cone enriched |
| **ACTA1** | PLS3 | 0.94 | Skeletal muscle actin; linked to myopathies |

---

## Therapeutic Implications

### Multi-Target Strategies

1. **Combinatorial SMN + Actin Pathway Enhancement**
   - Nusinersen/risdiplam (SMN2 splicing) + PLS3/CORO1C upregulation
   - Already proven in mice: extends survival from 14 to >250 days (PMID: 27499521)

2. **LIMK Inhibition (CFL2 pathway)**
   - LIMK inhibitors increase active (dephosphorylated) cofilin
   - Would enhance actin treadmilling at growth cones
   - Small molecule candidates exist (LIMKi 3, BMS-5)

3. **Arp2/3 Pathway Activation (ACTR2/CORO1C/ABI2)**
   - N-WASP-derived peptides activate Arp2/3
   - Would increase branched actin network formation at NMJ

4. **ROCK Inhibition (PFN2 pathway)**
   - Already explored in SMA: RhoA/ROCK overactivation from PFN2 increase
   - Y-27632 (ROCK inhibitor) rescues neurite outgrowth in SMA models
   - Fasudil (approved ROCK inhibitor) could be repurposed

5. **miR-133a-3p Axis (CORO1C regulation)**
   - MALAT1/miR-133a-3p/CORO1C regulatory axis identified
   - Anti-miR-133a-3p would de-repress CORO1C expression
   - Platform claim confidence: 0.90

### Experimental Validation Plan

| Priority | Experiment | Expected Outcome |
|----------|-----------|-----------------|
| 1 | RT-qPCR validation of all 7 genes in SMA patient fibroblasts/iPSC-MNs | Confirm GSE69175 co-upregulation |
| 2 | CFL2 knockdown/overexpression in SMN-depleted cells | Test CFL2 role in actin rescue |
| 3 | CFL2 + PLS3 double overexpression in SMA zebrafish | Test combinatorial actin rescue |
| 4 | LIMK inhibitor treatment in SMA motor neurons | Test pharmacological CFL2 activation |
| 5 | Arp2/3 activity assay (pyrene-actin) in SMN-depleted vs control neurons | Confirm Arp2/3 pathway disruption |

---

## Platform Integration Status

### Currently in Database
- **CORO1C**: Full target entry, 14 claims, ESM2 embeddings, hypothesis (0.95 confidence)
- **PLS3**: Full target entry, 83 claims, ESM2 embeddings, hypothesis (0.94 confidence)

### Candidates for Addition (5 new targets)
- **CFL2**: 0 claims, not in targets table — HIGHEST PRIORITY for addition
- **ACTG1**: 7 claims (OTUD6A axis), not in targets table
- **ACTR2**: 2 claims, not in targets table
- **ABI2**: 0 claims, not in targets table
- **PFN2**: 4 claims (known SMA modifier gene), not in targets table

### Recommended Actions
1. Add CFL2, ACTG1, ACTR2, ABI2, PFN2 as targets in the platform
2. Create "Actin Pathway Disruption" hypothesis linking all 7 genes
3. Run cross-paper synthesis (M4) for CFL2 and ACTG1
4. Generate ESM2 embeddings for all 5 new targets
5. Run DiffDock virtual screening: LIMK inhibitors against CFL2

---

## Conclusion

The GSE69175 actin pathway analysis reveals that SMA motor neurons mount a **coordinated, multi-level cytoskeletal compensatory response** spanning every major actin regulatory layer: signaling (ABI2), nucleation (ACTR2, CORO1C), dynamics (CFL2, PFN2), structure (ACTG1), and stabilization (PLS3). This is not a single-gene effect but an entire pathway activation program.

Three of the seven genes (ACTG1, ACTR2, ABI2) have **zero SMA publications**, representing completely novel therapeutic target candidates. CFL2 has only one tangential mention. This network, centered on the proven PLS3-CORO1C endocytosis rescue mechanism, provides the most complete map of the actin disruption axis in SMA to date.

The therapeutic implication is clear: **targeting the entire actin pathway, not just individual genes, could produce synergistic rescue effects** beyond what SMN restoration alone achieves. This is especially relevant for SMA patients who respond suboptimally to nusinersen or risdiplam.

---

*Generated from SMA Research Platform analysis (30,794 claims, 50 targets, 1,264 hypotheses)*
*STRING-DB v12.0, PubMed via Entrez, GSE69175 differential expression data*
