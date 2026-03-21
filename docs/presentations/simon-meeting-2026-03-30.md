# Simon Meeting — Week of March 30, 2026
# 30-Minute Presentation Outline

> **Audience**: Christian Simon (Carl-Ludwig-Institute, Leipzig) — rising PI, first author in Brain 2025
> **His network**: Mentis (Columbia), Capogrosso (Pittsburgh), Pellizzoni, Sumner, Wirth, Hallermann
> **Goal**: Establish collaboration, propose joint Fasudil experiment
> **Strategy**: Show we understand HIS proprioceptive work (PMID 39982868), then connect to our actin pathway

---

## Slide 1: Opening (1 min)
- "We rebuilt the platform based on your feedback"
- Key message: quality over quantity

## Section A: Your Priorities Addressed (8 min)

### Slide 2: Your Brain 2025 Paper — Computational Extensions (4 min)
- Reference HIS paper: PMID 39982868 "Proprioceptive synaptic dysfunction in mice AND humans"
- Show: we ingested this work, built proprioceptive circuit research direction
- Platform can computationally extend his findings:
  - Which genes are co-dysregulated with proprioceptive markers?
  - Cross-paper synthesis: what other targets connect to Ia afferents?
  - Evidence gap: what's missing to translate from mouse to therapy?
- **Ask**: What computational analysis would be most useful for his next paper?

### Slide 3: Motor Neuron Counting Problem (2 min)
- Literature confirms: 0-80% variation across labs
- Our platform flags methodology limitations in claims
- Evidence Gap Map shows which targets lack motor_function data
- **Ask**: What counting methodology do you trust most?

### Slide 4: Data Quality Improvements (3 min)
- Gold-standard: 60 claims validated (98.3% lenient, 28.3% strict)
- Found non-SMA claims in DB → cleaning pipeline built
- PMID verification: caught 1 hallucinated reference (11% rate)
- Dual-mode scoring: Discovery vs Clinical target ranking
- TP53 added (155 claims) as requested

## Section B: Novel Scientific Findings (12 min)

### Slide 5: The Actin Pathway Story (4 min)
- SMN → Profilin → ROCK → LIMK → Cofilin → Actin Rods (PMID 21920940)
- NOT just CORO1C (we downgraded it — it's a passenger)
- The PATHWAY is the finding, not a single gene
- PFN1: only MN-validated non-Gemin SMN interaction
- CFL2: 2.9x up in SMA, ZERO publications → first-in-field

### Slide 6: Cofilin-P → TDP-43 Convergence (3 min)
- p-cofilin elevated in SMA models + patient fibroblasts
- Actin-cofilin rods form in SMA (Walter 2021, PMID 33986363)
- Cofilin-P triggers TDP-43 aggregation in ALS
- SMA-ALS convergence at the actin level
- Implication: shared therapeutic target

### Slide 7: Fasudil Experiment Proposal (3 min)
- ROCK inhibitor, approved (Japan/China), crosses BBB
- Phase 2 in ALS (NCT03792490), NOBODY tested in SMA
- Proposed: SMA iPSC-MN + Fasudil 10-30µM
- Readouts: p-cofilin, actin rods, TDP-43 localization
- Cost: $6-10K, Timeline: 7-12 weeks
- **Ask**: Would Hallermann lab have iPSC-MN capacity?

### Slide 8: "Translational Desert" Hypothesis (2 min)
- Actin rods block mRNA transport → NMJ starves
- Explains: why NMJ fails first, why early treatment works better
- Testable: fluorescent mRNA + live imaging after Fasudil
- GPT-4o: Publishable (High plausibility, High testability)

## Section C: Platform Demo (5 min)

### Slide 9: Live Demo
- Show: https://sma-research.info
- Demo: Scores page (Clinical mode → PLS3 ranks higher)
- Demo: New targets (PFN1, CFL2, ROCK2)
- Demo: Research Directions (21 total)
- Demo: /ask endpoint (conversational search)
- Demo: GPU Results (DiffDock, now clickable)

## Section D: Collaboration Proposal (4 min)

### Slide 10: Joint Research Opportunities
1. **Fasudil in your iPSC-MN** — does actin rod clearance improve proprioceptive synapse function?
2. **Computational support for your next paper** — we can run analysis pipelines, literature synthesis
3. **Hallermann electrophysiology** — can we measure bioelectric changes after Fasudil?
4. **Connection to Capogrosso** — spinal cord stimulation + ROCK inhibition as combination?
5. **Sowoidnich's MN counting** — integrate her automated method as platform gold standard?
6. Your Wirth connection — could validate CORO1C/PLS3 pathway findings in her lab

---

## Backup Slides (if asked)

- Evidence Gap Map (which targets need what data)
- TDP-43 as novel target (445 claims, 0 hypotheses → now 3)
- Querdenker directions (aging, epigenetic editing, gut-brain)
- DiffDock validation story (fomepizole artifact, MW bias)
- PMID verification methodology

## Do NOT Present
- Cost/pricing of anything
- Marketing language
- Unvalidated claims
- Features that don't work yet (NVIDIA NIMs are down)
- The 12 commits or "24h sprint" narrative (they don't care about our process)
