# SMA Research Platform — Next 24h Sprint Plan
# Date: 2026-03-22
# Prerequisites: Complete the current sprint items first

> **Focus**: Execute what's ready, fix what's broken, deepen what works.
> **Rule**: No Gemini for factual claims. Verify EVERYTHING. Quality > Speed.

---

## Blocker Fixes (Hours 0-2)

### 1. Fix DiffDock v2.2 NIM API Format
- Current: 400 Bad Request — API format changed since our last successful run
- Action: Check NVIDIA NIM docs for current DiffDock request schema
- Test with Fasudil SMILES against SMN2 AlphaFold PDB
- If fixed → run Fasudil batch docking (5 compounds × 7 targets)
- Deliverable: Fasudil docking results with confidence scores

### 2. Fix OpenFold3 + RNAPro NIM URLs
- Current: 404 — URLs changed
- Action: Check build.nvidia.com for current BioNeMo NIM endpoints
- Priority: RNAPro for SMN2 pre-mRNA 3D structure prediction

### 3. GSEA Data Preprocessing
- Current: Gene sets ready (57 genes), no processable expression matrix
- Action: Download ARCHS4 human gene v2.2 HDF5 (~15GB) OR
  find processed count matrix from a specific SMA publication
- Run ssGSEA with our 6 proprioceptive gene sets
- Deliverable: GSEA enrichment scores for SMA vs control

---

## Deep Research (Hours 2-8)

### 4. U12 Vulnerability Map Execution
- Gene sets: Build U12 intron list from GENCODE v44
- Cross-reference with proprioceptive gene list (Pvalb, Piezo2, EphA4, Ret, Etv1)
- Identify which proprioceptive genes have U12-type introns
- Run IRFinder on GSE152717 (human spinal MN, 80M reads) if FASTQ accessible
- Deliverable: List of U12-vulnerable proprioceptive genes

### 5. PFN1/CFL2 Deep Literature Ingestion
- Current: PFN1 has 4 claims, CFL2 has 4 claims (too thin)
- Action: Targeted PubMed queries for profilin + motor neuron, cofilin + neurodegeneration
- Ingest 50+ papers specifically about actin dynamics in motor neurons
- Extract claims, relink to targets
- Deliverable: PFN1 and CFL2 each at 20+ claims

### 6. Simon's Brain 2025 Paper Deep Analysis
- Download supplementary data from PMID 39982868
- Extract all gene lists, fold changes, statistical tests
- Cross-reference with our 60 targets
- Find which of our targets appear in his data
- Deliverable: Table showing overlap between Simon's genes and our targets

### 7. Necroptosis Pathway Deep Dive
- Martinez-Espana showed 4-AP prevents deafferentation via necroptosis
- Search for: RIPK1/RIPK3/MLKL expression data in SMA
- Check if necrostatin-1 has been tested in SMA (verify, don't trust Gemini)
- Deliverable: Verified necroptosis evidence table

---

## Platform Improvements (Hours 8-14)

### 8. Frontend: Make ALL Advanced Sections Interactive
- Current: Most Advanced pages are static (CRISPR, AAV, Docking, etc.)
- Pattern: Follow GPU Results upgrade (expandable rows, detail panels, external links)
- Priority order:
  1. Docking section (pharmacophore scores)
  2. CRISPR section (guide details)
  3. Screening section (compound details)
  4. Directions section (already clickable, improve depth)

### 9. Frontend: Improve Targets Deep-Dive
- Each target should have a deep-dive page showing:
  - All linked claims (with source links)
  - All hypotheses mentioning this target
  - Evidence gap analysis (which claim types missing)
  - External links (UniProt, NCBI Gene, STRING-DB, AlphaFold)
  - If available: ESM-2 embedding, DiffDock results, CRISPR guides

### 10. API: Add Clinical Scoring Endpoint
- New endpoint: GET /scores?mode=clinical
- Already implemented in code but needs frontend toggle
- Add dropdown on Scores page to switch between Discovery/Clinical mode

### 11. MCP: Improve verify_pmid Tool
- Current: checks single PMID
- Add: batch verification (list of PMIDs)
- Add: auto-verify on claim extraction (flag claims with unverifiable PMIDs)

---

## Hypothesis Refinement (Hours 14-18)

### 12. Generate Hypotheses for New Targets
- Trigger hypothesis generation for PFN1, CFL2, ROCK2, RIPK1, SARM1
- Requires Claude Sonnet API on moltbot
- Target: 5-10 new mechanistic hypotheses
- Quality check: GPT-4o professor-readiness scoring on each

### 13. Run Convergence Analysis
- Check which existing hypotheses are CONFIRMED by the 308 new claims
- Run convergence scoring on all 1,271 hypotheses
- Identify hypotheses that gained or lost evidence
- Deliverable: "Evidence movement" report

### 14. Validate Top 3 Hypotheses Further
- H2 (Cofilin-P → TDP-43 + Fasudil): search for experimental validation
- H4 (Translational Desert): find transport measurement studies in SMA
- H6 (4-AP deafferentation): get Martinez-Espana poster abstract

---

## Documentation & Outreach (Hours 18-24)

### 15. Create Simon Email (Final Version)
- Incorporate feedback on PPTX v3
- Attach: PPTX + platform access info
- Tone: collegial, data-focused, no marketing
- Ask: which analyses would help his next paper?

### 16. Write Platform Blog Post
- "How Computational Cross-Paper Synthesis Revealed a Connection Between
  Actin Dynamics and Proprioceptive Synapse Failure in SMA"
- Target audience: SMA researchers at Cure SMA conference
- Include: pathway diagram, transport model, 4-AP validation
- Peer-level writing, no marketing

### 17. Prepare for Git Push
- Squash/rebase Simon-related commits (private docs were added then removed)
- Clean commit history for public GitHub
- Push to origin/master
- Verify: no private data in any commit

### 18. Update All Memory Files
- Session recap with all new findings
- Update SMA biology learnings
- Update platform state
- Update feedback rules (Gemini hallucination count: 3)

---

## Success Criteria

At the end of this sprint:
- [ ] DiffDock works again with Fasudil docking results
- [ ] GSEA executed on at least one dataset
- [ ] U12 vulnerability map has initial results
- [ ] PFN1 and CFL2 each have 20+ claims
- [ ] 3+ frontend sections upgraded to interactive
- [ ] Simon email ready to send
- [ ] All findings verified (0% PMID hallucination)
- [ ] Git pushed to GitHub (clean history)

---

## Extended Blocks (10 additional research sprints — Prof Level)

### Block 5: SMA Patient Stratification Engine
- Build computational model: SMN2 copy number + modifier genes → predicted severity
- Input: SMN2 copies (2-4), PLS3 status, NCALD, NAIP, age of onset
- Output: predicted trajectory, recommended monitoring interval
- Cross-validate against published natural history cohorts (Mercuri, De Vivo)
- Deliverable: stratification algorithm with calibration metrics

### Block 6: Drug Combination Optimizer
- Systematic scoring of all 21 drugs × 21 drugs for combination potential
- Criteria: mechanism complementarity, BBB penetration, safety overlap, clinical feasibility
- Special focus: Risdiplam + Fasudil, Nusinersen + 4-AP, Gene therapy + ROCK inhibitor
- Model drug-drug interactions from ChEMBL bioactivity overlap
- Deliverable: ranked combination table with mechanistic rationale per pair

### Block 7: Automated Literature Monitor
- Build daily alert system: new PubMed papers matching our 60 targets
- Auto-classify: which target, which claim type, SMA relevance score
- Auto-ingest papers above threshold
- Weekly digest email/notification for key findings
- Deliverable: automated pipeline replacing manual ingestion

### Block 8: Wet Lab Experiment Registry
- Create structured database of proposed experiments from our platform
- Track: hypothesis → proposed experiment → status → result → conclusion
- Link back to platform hypotheses and claims
- Fasudil iPSC-MN is experiment #1, BDNF synergy is #2
- Deliverable: experiment tracking system with Go/No-Go gates

### Block 9: Patient-Facing Evidence Summaries
- Write lay-language summaries of top 10 targets
- Explain: what this gene does, why it matters for SMA, what therapies exist
- Tone: accurate but accessible to SMA families
- Multilingual: English + German (for SMA Europe community)
- Deliverable: patient-facing section on sma-research.info

### Block 10: Bayesian Model Upgrade
- Current: Grade A (89.8%) calibrated against 227 drug outcomes
- Upgrade: incorporate new drug outcomes from 2025-2026 clinical trials
- Add: time-to-event modeling (not just success/failure)
- Add: uncertainty intervals on every prediction
- Deliverable: Grade A+ model with temporal predictions

### Block 11: Protein Structure Analysis Pipeline
- When OpenFold3/RNAPro come back online:
  - Predict SMN2 pre-mRNA 3D structure (ISS-N1 site)
  - Predict SMN-Gemin complex structure
  - Predict PFN1-actin interaction structure
  - Dock Fasudil into ROCK2 crystal structure (PDB available)
- Deliverable: structural biology section on platform

### Block 12: HuggingFace Dataset V2
- Update SMAResearch/sma-evidence-graph with sprint data
- Add: new targets (PFN1, CFL2, ROCK2, RIPK1, SARM1)
- Add: new hypotheses (Fasudil, Translational Desert, 4-AP validation)
- Add: transport vulnerability model results
- Add: GSEA gene sets as separate dataset
- Deliverable: published HuggingFace dataset update

### Block 13: SMA News Aggregator
- Build RSS/API aggregator for:
  - PubMed new SMA papers (daily)
  - ClinicalTrials.gov new/updated SMA trials (weekly)
  - bioRxiv/medRxiv SMA preprints (daily)
  - FDA/EMA regulatory decisions on SMA drugs (monthly)
- Auto-post summaries to platform news section
- Deliverable: always-current news feed

### Block 14: Collaboration Network Map
- Build visual network of SMA researchers and their connections
- Data: co-authorship from our 6,325 sources
- Show: who collaborates with whom, which labs work on which targets
- Identify: potential collaboration partners for specific hypotheses
- Special: map Simon's network (Mentis, Capogrosso, Pellizzoni, Wirth, Hallermann)
- Deliverable: interactive collaboration graph on platform

---

## Anti-Patterns
- NO Gemini for factual claims (use ONLY for broad synthesis)
- NO costs/pricing in any document
- NO celebrating before verification
- NO "first-in-field" claims without prior art check
- NO pushing to GitHub without history review
