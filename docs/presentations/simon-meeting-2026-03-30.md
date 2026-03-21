# Simon Meeting — Week of March 30, 2026
# 30-Minute Presentation Outline

> **Audience**: Christian Simon (PhD student, Leipzig), Prof. Schoeneberg
> **Goal**: Show scientific credibility, get feedback on Fasudil proposal
> **Strategy**: Lead with HIS priorities, then our novel findings

---

## Slide 1: Opening (1 min)
- "We rebuilt the platform based on your feedback"
- Key message: quality over quantity

## Section A: Your Priorities Addressed (8 min)

### Slide 2: Proprioceptive Circuit Support (3 min)
- NEW: Proprioceptive Circuit research direction on platform
- Mentis lab (Columbia) evidence integrated
- Ia afferent synapse loss precedes MN death
- Platform now tracks circuit disease perspective
- **Ask**: Which specific proprioceptive markers should we add?

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

## Section D: Discussion (4 min)

### Slide 10: What We Need
1. iPSC-MN access for Fasudil experiment
2. Proprioceptive circuit data recommendations
3. Feedback on Translational Desert hypothesis
4. Connection to Hallermann lab (electrophysiology)
5. Your list of "what would convince you this is real"

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
