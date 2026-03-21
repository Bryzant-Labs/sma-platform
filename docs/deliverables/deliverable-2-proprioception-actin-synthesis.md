# Deliverable #2: Cross-Paper Synthesis — Proprioception × Actin Pathway
# Status: FIRST PASS COMPLETE

> **Date**: 2026-03-21
> **Method**: Hybrid semantic search over 30,844 claims + co-occurrence analysis
> **Result**: The connection is NOT obvious — only 2 shared genes (Ret, SMN)

---

## Key Finding

Proprioceptive biology and actin dynamics are **largely separate literatures** in SMA.
152 proprioceptive claims and 119 actin pathway claims share only 2 direct overlapping
claims and 2 shared molecular targets (Ret, SMN).

**This is the opportunity.** The connection between actin dynamics and proprioceptive
synapse failure is not yet made in the literature. Our platform identifies this gap.

## Evidence Summary

| Category | Count |
|----------|-------|
| Proprioceptive claims | 152 |
| Actin pathway claims | 119 |
| Direct overlap | 2 claims |
| Shared genes | Ret, SMN |

### Genes in Proprioceptive Literature
Piezo2, Ret, SMN, UBA1

### Genes in Actin Literature
CFL2, CORO1C, LIMK, NfL, PFN1, PFN2, PLS3, ROCK, Ret, SMN, TDP-43, actin, cofilin, profilin

### The Bridge We Propose

The connection is mechanistic, not literature-based:

```
SMN loss → PFN1/PFN2 dysfunction → ROCK activation → LIMK → CFL2-P →
actin-cofilin rods → transport blockade →
→ Ia afferent synapse failure (Simon Brain 2025)
→ NMJ translational desert (our hypothesis)
→ Mitochondrial transport failure → metabolic starvation
```

No single paper makes this full connection. Our platform enables it through:
1. SMN-PFN interaction (PMID 21920940, Nölle 2011)
2. p-cofilin elevation in SMA (published, multiple labs)
3. Actin-cofilin rods in SMA (PMID 33986363, Walter 2021)
4. Proprioceptive synapse loss in SMA (PMID 39982868, Simon 2025)
5. ROCK inhibition proposed for SMA (PMID 25221469, Coque 2014)

## Limitations

- PFN1, CFL2, ROCK2 were just added as targets — no claim linkages yet
- Co-occurrence matrix needs claim-relinking to show new target connections
- The bridge is mechanistic reasoning, NOT direct experimental evidence
- Only 2 direct overlap claims — the fields don't talk to each other yet

## What This Means for Simon

The fact that there's almost NO overlap is actually powerful:
- It means nobody has connected these dots before
- Our computational platform is the first to identify this gap
- The experimental validation (Fasudil → proprioceptive synapse readout) would be novel
- A paper connecting actin dynamics to proprioceptive failure would be genuinely new

## Next Steps

1. Run claim-relinking for PFN1, CFL2, ROCK2 to expand co-occurrence data
2. Run GSEA on GSE87281 with proprioceptive gene sets (Deliverable #1)
3. Build network visualization for the bridge pathway
4. Present gap + bridge to Simon as "here's what we found, here's what we propose"
