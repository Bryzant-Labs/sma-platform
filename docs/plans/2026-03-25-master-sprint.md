# Master Sprint 2026-03-25 — From Computation to Cure

**Goal:** Turn 3 dual-target drug candidates into a fundable research program with reproducible evidence, a grant application, and a preprint.

---

## Wave 1: Complete Yesterday's Blockers (Hours 0-2)

| Task | What | Depends On |
|------|------|------------|
| 1A | Stereoisomer panel — dock all 4 H-1152 enantiomers vs LIMK2 + ROCK2 | NVIDIA API reset |
| 1B | ABL1 selectivity optimization — generate analogs that reduce ABL1 while keeping LIMK2/ROCK2 | NVIDIA API |
| 1C | Import ALL remaining docking/screening results to DB | Nothing |
| 1D | Run claim extraction on remaining unprocessed sources | Nothing |

## Wave 2: Evidence Expansion (Hours 2-6)

| Task | What | Why |
|------|------|-----|
| 2A | bioRxiv deep scan — SMA + ROCK + LIMK + actin preprints (last 2 years) | Preprints have the freshest findings |
| 2B | ClinicalTrials.gov refresh — pull all new SMA trials + ROCK inhibitor trials | Fasudil ROCK-ALS trial results |
| 2C | STRING-DB network expansion — LIMK2/ROCK2/CFL2 protein interaction partners | Discover new nodes in the pathway |
| 2D | ChEMBL LIMK2 bioactivity query (target CHEMBL3286) — real LIMK2 inhibitor data | True LIMK2 binders, not just repurposing |
| 2E | Claim-target relinking — 15K+ claims, many not linked to specific targets | Strengthen evidence per target |

## Wave 3: Combination Therapy Modeling (Hours 6-10)

| Task | What | Why |
|------|------|-----|
| 3A | Synergy prediction: genmol_119 + risdiplam | SMN restoration + LIMK2 inhibition |
| 3B | Synergy prediction: genmol_119 + fasudil | Dual LIMK2 + ROCK coverage |
| 3C | Triple therapy model: risdiplam + fasudil + genmol_119 | The full ROCK-LIMK2-CFL2 axis intervention |
| 3D | CFL2 biomarker integration — predict treatment response by CFL2 levels | Personalized medicine angle |
| 3E | Digital Twin update — simulate genmol_119 effect on personal SMA profile | N=1 treatment prediction |

## Wave 4: Grant Application Foundation (Hours 10-14)

| Task | What | Why |
|------|------|-----|
| 4A | Cure SMA Basic Research Grant draft — Specific Aims page | Deadline Oct 3, $140K/year |
| 4B | NCATS R21 concept — Preclinical Proof of Concept for Rare Diseases | Deadline Jun 2, $275K/2yr |
| 4C | Scientific Advisory Pack v2 — updated with all sprint findings | For collaborator recruitment |
| 4D | Budget justification — synthesis + SPR + kinase assay costs | Stage 1-2 of validation pipeline |
| 4E | Collaboration letters — draft outreach to Wirth, Gouti, Hallermann labs | SMA iPSC motor neurons needed |

## Wave 5: Preprint Draft (Hours 14-18)

| Task | What | Why |
|------|------|-----|
| 5A | Preprint outline: "AI-designed dual ROCK/LIMK2 inhibitors for SMA" | The computational story is complete |
| 5B | Figure generation — convergence matrix, DiffDock heatmaps, SAR plots | Publication-quality figures |
| 5C | Methods section — DiffDock, MolMIM, ESM-2, RDKit pipeline | Reproducibility |
| 5D | Supplementary tables — all 501 dockings, 1,122 molecules, ADMET | Complete data |
| 5E | bioRxiv submission prep — LaTeX/Word, author info, abstract | Ready to submit |

## Wave 6: Platform Enhancement (Hours 18-22)

| Task | What | Why |
|------|------|-----|
| 6A | Drug Pipeline Visualization — interactive Sankey diagram showing screening funnel | Show the path from 23K → 1,122 → 76 → 3 candidates |
| 6B | Compound Comparison Tool — side-by-side ADMET/docking for any 2 molecules | Researcher tool |
| 6C | Evidence Graph Visualization — force-directed graph of target-claim-source network | See connections |
| 6D | HuggingFace dataset update — publish all new data (claims, dockings, molecules) | Open science |
| 6E | API documentation polish — Swagger examples for all 100+ endpoints | External researchers |

## Wave 7: Scale & Future (Hours 22-24)

| Task | What | Why |
|------|------|-----|
| 7A | ML Docking Proxy retrain — add 306 new DiffDock results to training data | Better predictions for next round |
| 7B | CRISPR guide design for LIMK2 knockdown — validation via gene silencing | Alternative validation approach |
| 7C | Boltz-2 structure prediction for genmol_119-LIMK2 complex | Predicted binding pose |
| 7D | Schedule automated pipelines — daily PubMed + weekly claim extraction + monthly DiffDock | Platform runs itself |
| 7E | Plan: 1B molecule screening pipeline ($400 on Vast.ai) | Scale from 1K to 1B molecules |

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Claims | 15,874 | 20,000+ |
| Sources | 9,023 | 10,000+ |
| Dockings | 501 | 1,000+ |
| Drug Candidates | 3 | 5+ with full ADMET |
| Grant Drafts | 0 | 2 (Cure SMA + NCATS) |
| Preprint | 0 | 1 (bioRxiv-ready) |
| Figures | 0 | 10+ publication-quality |
| Combination Models | 0 | 3 (mono, dual, triple) |

---

## Execution Strategy
- Waves 1-2: Parallel agents (data expansion, no dependencies)
- Wave 3: Depends on Wave 2 evidence
- Wave 4: Can start in parallel with Wave 3
- Waves 5-6: Depend on Waves 1-4 results
- Wave 7: Independent, can start anytime
- All git handled by lead (Opus)
- Max Plan burning throughout
