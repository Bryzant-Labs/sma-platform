# Meeting Prep: Simon / Schoeneberg — Week of March 30, 2026

**PRIVATE DOCUMENT — NOT FOR GITHUB**

**Attendees**: Christian Fischer, Prof. Christian Simon (Carl-Ludwig-Institute for Physiology, Leipzig), possibly Prof. Thorsten Schoeneberg (Biochemistry/Bioinformatics, Leipzig)

**Location**: Leipzig (in-person) | **Duration**: 45 min

---

## Agenda (3 items, 45 min)

### 1. Platform Demo (15 min)
Walk through sma-research.info live. Show the evidence engine, not the feature count.

**Demo flow:**
- Start with search: type "CORO1C" to show instant cross-paper results
- Evidence tiers: explain VALIDATED vs COMPUTATIONAL vs HYPOTHESIS
- Calibration gauge: Grade A, 89.8% — back-tested against 227 drug outcomes
- Knowledge graph: dark-theme, show CORO1C neighborhood
- MCP natural language query (if Schoeneberg is present — he has AI interest)

**Key stat to state casually:** "6,176 sources, about 30,000 claims extracted and scored."

**Do NOT** list module counts or endpoint numbers. Simon cares about data quality, not architecture.

### 2. CORO1C IHC Proposal (15 min)
Simon's core expertise is selective motor neuron vulnerability: L1 (proximal, vulnerable) vs L5 (distal, resistant). CORO1C fits directly into his research.

**The pitch:**
- Wirth Lab (PMID 27499521): CORO1C overexpression rescues SMA phenotype in zebrafish
- PLS3-CORO1C interaction: STRING-DB score 0.818 (high confidence)
- Our ESM-2 analysis: CORO1C is a structural outlier among SMA targets (similarity 0.64-0.73 to other targets)
- Nobody has measured CORO1C expression differentially in L1 vs L5 motor neurons
- This is a straightforward IHC experiment on tissue Simon already has (SMN-delta-7 mouse)

**What makes this compelling for Simon:** It connects his L1/L5 vulnerability work to the modifier biology field. If CORO1C is differentially expressed in resistant L5 neurons, it would explain part of the selective vulnerability puzzle — his main research question.

### 3. HDAC to CORO1C Hypothesis (15 min)
The untested experiment that could be a quick win.

**The logic chain:**
1. HDAC inhibitors (valproic acid, vorinostat) are known to increase SMN2 expression in SMA
2. miR-133a-3p suppresses CORO1C expression (PMID 39278098)
3. HDAC inhibitors are known to modulate miRNA expression
4. **Nobody has measured CORO1C expression after HDAC inhibitor treatment**
5. If HDAC inhibitors also upregulate CORO1C, that is a dual therapeutic mechanism (SMN2 + modifier)

**The experiment:** Treat SMA fibroblasts with vorinostat/valproic acid, measure CORO1C by qRT-PCR. One week, one student, minimal cost.

**GEO dataset available:** GSE69175 — SMA iPSC-derived motor neuron RNA-seq. Could check CORO1C levels computationally before committing to wet lab.

---

## Key Data Points to Show

| Data Point | Value | Source |
|------------|-------|--------|
| Total sources | 6,176 | Platform stats |
| Total claims | ~30,700 | Platform stats |
| Calibration grade | A (89.8%) | Bayesian back-test vs 227 outcomes |
| Riluzole to SMN2 binding | +0.082 confidence (20-pose validated) | DiffDock campaign |
| CORO1C-PLS3 interaction | STRING-DB 0.818 | STRING database |
| 4-AP to CORO1C binding | DiffDock +0.251, Vina -3.98 kcal/mol | Consensus docking |
| CORO1C rescue | Overexpression rescues SMA in zebrafish | Wirth Lab, PMID 27499521 |
| CORO1C after HDAC treatment | UNKNOWN — nobody has measured this | Literature gap |
| Available RNA-seq | GSE69175 (SMA iPSC motor neurons) | GEO |

---

## Questions to ASK Simon

1. **Mouse tissue**: Does he have SMN-delta-7 mouse spinal cord tissue suitable for CORO1C immunohistochemistry, comparing L1 vs L5 segments?
2. **SMA fibroblasts**: Does his lab (or a Leipzig collaborator) have access to SMA patient fibroblasts for the HDAC inhibitor to CORO1C qRT-PCR experiment?
3. **Schoeneberg SPR**: Would Prof. Schoeneberg's biochemistry group be able to run surface plasmon resonance (SPR) for riluzole/SMN2 binding validation? This is the one biophysically confirmed hit from our 4,116-compound screen.
4. **Co-authorship**: Would he be interested in co-authoring the bioRxiv preprint? (Draft exists: 5,186 words, 5 tables, 20 references, 12 limitations section)
5. **Proprioceptive angle**: Does he see a connection between CORO1C/actin dynamics and proprioceptive synapse maintenance? (This maps to his primary research interest)

---

## What NOT to Say

- **No superlatives**: Do not say "largest", "first-ever", "revolutionary", "groundbreaking"
- **No cost/budget talk**: Never mention costs, GPU pricing, or compute expenses on the platform or in conversation
- **No overselling DiffDock**: Always frame as "computational prediction that needs SPR/ITC validation" — not as proof of binding
- **No Fomepizole**: This was a molecular-weight-bias artifact (MW 82.1, score +1.027 was false positive). Mentioning it would undermine credibility. It has been publicly corrected on the platform already.
- **No CORO1C inhibitors**: We know CORO1C overexpression is protective (PMID 27499521). Inhibiting it would be counterproductive. Our DiffDock hits against CORO1C are binders/blockers, which is the wrong direction. The correct strategy is upregulation via HDAC/epigenetic mechanisms.
- **No module counting**: Simon does not care about 210 endpoints or 32 MCP tools. He cares about whether the data is reliable.
- **No AI hype**: Simon wants to know which model (Claude Sonnet) and how it is validated. Be transparent, not promotional.

---

## Backup Slides to Prepare

1. **Platform architecture diagram** — simple: Sources in, Claims extracted, Evidence scored, Hypotheses generated. Not the full technical stack.
2. **Evidence tier explanation** — VALIDATED (wet lab confirmed), COMPUTATIONAL (DiffDock/ESM-2), HYPOTHESIS (AI-generated, needs testing). One slide.
3. **Riluzole binding data** — table comparing 1-pose vs 5-pose vs 20-pose DiffDock scores for SMN2 and UBA1. Show that only riluzole survived validation.
4. **CORO1C to PLS3 to Actin pathway diagram** — CORO1C (actin dynamics) interacts with PLS3 (STRING 0.818), both modify actin cytoskeleton, critical for axon/synapse maintenance. Link to selective vulnerability.
5. **HDAC to miR-133a to CORO1C regulation model** — HDAC inhibitor suppresses miR-133a-3p, which normally suppresses CORO1C. Net effect: CORO1C upregulation. Show this as a testable mechanism.

---

## Simon's Known Priorities (from transcript analysis)

Keep these in mind during the meeting — align everything to his interests:

- **Data quality over quantity** — he spent 20 min in the first call explaining how 50% of SMA papers have methodological problems
- **Selective vulnerability (L1 vs L5)** — this is his main research question
- **Proprioceptive synaptic dysfunction** — his published landmark work, largely ignored by the field
- **Mouse model specifics** — he knows SMN-delta-7 intimately, do not generalize across models
- **Skepticism of astrocyte/microglia claims** — avoid citing those papers uncritically
- **Motor neuron counting methodology** — his 5-year study on proper counting. Our platform's source quality scoring speaks to this concern.

---

## Pre-Meeting Checklist

- [ ] Verify sma-research.info is live and responsive
- [ ] Test CORO1C search on the platform (should return Wirth Lab paper + DiffDock results)
- [ ] Check that p53/SMA papers (134 ingested for Simon) appear in search
- [ ] Confirm mouse (Mus musculus) is in species comparison section
- [ ] Ensure claim display uses human-readable format (not UUIDs)
- [ ] Have the bioRxiv preprint draft printed or on tablet
- [ ] Check GSE69175 dataset page loads
- [ ] Prepare laptop with platform open + backup screenshots in case of WiFi issues

---

## Desired Outcomes

1. Simon agrees to check CORO1C expression in L1 vs L5 tissue (IHC) — this is low-effort for him and high-value for us
2. A path to SPR validation via Schoeneberg's group for riluzole/SMN2
3. Agreement on the HDAC to CORO1C experiment as a joint project
4. Simon and/or Schoeneberg interested in co-authorship on bioRxiv preprint
5. Continued access to feedback on platform — Simon is our first real validator
