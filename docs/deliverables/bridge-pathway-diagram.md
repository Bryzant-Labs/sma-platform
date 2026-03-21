# Proprioception ↔ Actin Pathway Bridge
# The connection nobody has made yet

```
                    ┌─────────────────────────────────────────┐
                    │        SMN PROTEIN (CORE DEFECT)        │
                    │   Lost in SMA → cascade of dysfunction  │
                    └──────────┬───────────────┬──────────────┘
                               │               │
                    ┌──────────▼───────┐  ┌────▼──────────────┐
                    │  snRNP Assembly  │  │  Actin Dynamics    │
                    │  (canonical)     │  │  (non-canonical)   │
                    └──────────┬───────┘  └────┬──────────────┘
                               │               │
                    ┌──────────▼───────┐  ┌────▼──────────────┐
                    │  Splicing        │  │  SMN → Profilin    │
                    │  Defects         │  │  (PMID 21920940)   │
                    └──────────┬───────┘  └────┬──────────────┘
                               │               │
              ┌────────────────▼───┐      ┌────▼──────────────┐
              │  U12 Minor         │      │  RhoA/ROCK        │
              │  Spliceosome?      │      │  Activation       │
              │  (hypothesis)      │      │  (elevated in SMA)│
              └────────────────┬───┘      └────┬──────────────┘
                               │               │
                               │          ┌────▼──────────────┐
                               │          │  LIMK → CFL2      │
                               │          │  Hyperphosphoryl.  │
                               │          │  (p-cofilin ↑)     │
                               │          └────┬──────────────┘
                               │               │
                               │          ┌────▼──────────────┐
                               │          │  ACTIN-COFILIN     │
                               │          │  ROD FORMATION     │
                               │          │  (PMID 33986363)   │
                               │          └────┬──────────────┘
                               │               │
              ┌────────────────▼───────────────▼──────────────┐
              │         AXONAL TRANSPORT BLOCKADE              │
              │  Rods physically obstruct cargo movement       │
              │  mRNA granules + mitochondria can't reach NMJ  │
              └──────────┬──────────────────┬─────────────────┘
                         │                  │
              ┌──────────▼──────┐  ┌────────▼─────────────────┐
              │  "TRANSLATIONAL  │  │  "METABOLIC              │
              │   DESERT"        │  │   STARVATION"            │
              │  No local        │  │  No ATP at              │
              │  protein synth.  │  │  distal synapse          │
              └──────────┬──────┘  └────────┬─────────────────┘
                         │                  │
              ┌──────────▼──────────────────▼─────────────────┐
              │         SYNAPSE FAILURE (length-dependent)      │
              │                                                │
              │  1st: Ia afferent lumbar (1000µm) — 99.9%      │
              │  2nd: α-MN leg (800µm) — 99.7%                │
              │  3rd: γ-MN (600µm) — 98.6%                    │
              │  Last: local interneuron (50µm) — 30.1%        │
              │                                                │
              │  = Simon Brain 2025: proprioception fails FIRST│
              └──────────────────────┬────────────────────────┘
                                     │
              ┌──────────────────────▼────────────────────────┐
              │                   TDP-43                        │
              │  Actin rods → stress granules → TDP-43 aggr.   │
              │  = SMA-ALS convergence mechanism                │
              └──────────────────────┬────────────────────────┘
                                     │
              ┌──────────────────────▼────────────────────────┐
              │              THERAPEUTIC TARGETS                │
              │                                                │
              │  ● Fasudil (ROCK inhibitor) — crosses BBB      │
              │    Proposed 2014 (Coque), our addition: p-CFL2 │
              │                                                │
              │  ● 4-AP (K+ channel blocker) — prevents        │
              │    deafferentation (Martinez-Espana 2026)       │
              │                                                │
              │  ● Risdiplam + Fasudil combination              │
              │    = SMN restoration + rod clearance            │
              └────────────────────────────────────────────────┘
```

## Evidence Quality per Node

| Node | Evidence | Verified PMIDs | Status |
|------|----------|---------------|--------|
| SMN → Profilin | PMID 21920940 (Nölle 2011) | Verified ✅ | Established |
| ROCK elevated in SMA | Published studies | Multiple | Established |
| p-cofilin elevated | Mouse + patient fibroblasts | Multiple | Established |
| Actin-cofilin rods | PMID 33986363 (Walter 2021) | Verified ✅ | Established |
| Transport blockade by rods | Neurodegeneration literature | Multiple | Strong |
| Length-dependent failure | Transport model (this sprint) | Computed | Novel prediction |
| Proprioception fails first | PMID 39982868 (Simon 2025) | Verified ✅ | Experimentally confirmed |
| TDP-43 connection | Cofilin-P → TDP-43 (ALS lit.) | Multiple | Cross-disease |
| Fasudil proposed | PMID 25221469 (Coque 2014) | Verified ✅ | Prior art exists |
| 4-AP deafferentation | SMA Europe Congress 2026 | Conference only | Not peer-reviewed |
| U12 spliceosome | Hypothesis from platform | None specific | Unproven |

## What's Novel (Our Contribution)

1. The COMPLETE pathway from SMN → actin rods → proprioceptive failure
2. The "Translational Desert" concept (mRNA transport blockade)
3. The "Metabolic Starvation" extension (mitochondrial transport)
4. The quantitative transport model predicting failure order
5. The connection to TDP-43 (SMA-ALS convergence)
6. The Fasudil + p-cofilin + TDP-43 specific mechanism
7. The computational cross-paper synthesis identifying the gap
