# SMA Research Platform — 24h Autonomous Research Sprint
# =====================================================
# Reusable prompt for deep autonomous research work.
# Created: 2026-03-21
# Usage: Feed this to Claude Code as initial prompt, then let it run.

> **Mission**: Maximize scientific output for the SMA Research Platform over 24 hours.
> Use all 4 LLMs (Claude Opus, GPT-4o, Gemini Flash, Groq Llama), NVIDIA NIMs,
> GPU compute, and the full MCP toolchain. Evidence-first. No marketing. Prof-level.

---

## Rules

1. **Never ask "weiter?" or "soll ich...?"** — work autonomously, plan 5-10 steps ahead
2. **Never publish, email, or deploy to moltbot** unless explicitly told
3. **Never show costs/pricing** on any output
4. **Validate every finding** — no celebrating before verification
5. **Save all findings** to memory + git commits as you go
6. **Use parallel agents** for independent work streams
7. **Evidence > Features** — one validated discovery > ten unverified modules
8. **Critical thinking always** — if it sounds too good, it probably is

## LLM Routing Strategy

| LLM | Role | Via |
|-----|------|-----|
| Claude Opus (self) | Lead architect, scientific reasoning, complex synthesis | Direct |
| GPT-4o | Code generation, data analysis, structured output | Codex MCP `dev_write_code` / `dev_analyze` |
| Gemini Flash | Research synthesis, large-context literature review | Codex MCP `dev_research` |
| Groq Llama | Fast iteration, bulk processing, quick checks | Codex MCP `dev_fast` |

## Phase 1: Fresh Evidence Ingestion (Hours 0-2)

### 1.1 Run Full Ingestion Pipeline
```
# On moltbot via SSH:
ssh moltbot "cd /home/bryzant/sma-platform && source venv/bin/activate && python scripts/daily_ingest.py"
```
- PubMed: new papers since last run
- bioRxiv/medRxiv: new SMA preprints
- ClinicalTrials.gov: new/updated trials
- Log: how many new sources, claims, trials

### 1.2 Targeted PubMed Deep Dives (via API)
Focus on gaps identified by Simon and scientific advisory:
- "SMA proprioceptive" — Simon's #1 priority, largely ignored by field
- "SMA motor neuron counting methodology" — Simon showed 0-80% variation
- "SMN protein complex structure" — for Proteina-Complexa integration
- "SMA bioelectric" — electroceutical approach evidence
- "SMA actin dynamics" — CORO1C/PLS3/CFL2 pathway
- "SMA intron retention" — CORO1C double-hit model evidence
- "SMA organoid NMJ" — validation platform evidence
- "SMN2 splicing modifier" — beyond nusinersen/risdiplam

### 1.3 Extract Claims from All New Sources
```
POST /api/v2/extract/claims
```
- Run claim extraction on all unprocessed sources
- Track: precision, false positive rate
- Link new claims to existing targets

## Phase 2: Deep Research with Multi-LLM (Hours 2-6)

### 2.1 Gemini Flash Deep Research (via Codex `dev_research`)

Run 6 deep research queries, each returning structured markdown:

1. **"What are all known protein-protein interaction partners of SMN beyond the canonical Gemin complex? Focus on cytoplasmic functions, axonal transport, and actin dynamics."**

2. **"Comprehensive review of intron retention as a disease mechanism in neurodegenerative diseases. Which genes show pathological intron retention? Is there evidence that SMN loss causes widespread intron retention beyond SMN2?"**

3. **"What experimental evidence exists for proprioceptive synaptic dysfunction in SMA? What do motor neuron counting studies actually show — is the 0-80% variation across labs a methodology problem or biology?"**

4. **"State of the art in SMN2 splicing regulatory grammar. What is known about the ISS-N1, ISS-N2, ESE, ESS elements? What new regulatory elements have been discovered since nusinersen approval?"**

5. **"Bioelectric approaches to neurodegeneration — what evidence exists for electrical stimulation, ion channel modulation, or voltage-mediated programs activating repair in motor neuron diseases?"**

6. **"What are the most promising non-SMN therapeutic targets for SMA? Evidence for PLS3, NCALD, UBA1, STMN2, CORO1C — which has the strongest human genetic evidence?"**

### 2.2 GPT-4o Code Analysis (via Codex `dev_analyze`)

1. Analyze our CORO1C double-hit hypothesis against all available evidence
2. Analyze the actin pathway convergence (CORO1C-PLS3-CFL2-PFN1)
3. Analyze our DiffDock results — which hits are methodologically sound?
4. Analyze our claim extraction quality — systematic error patterns

### 2.3 Groq Fast Processing (via Codex `dev_fast`)

- Quick classification of all unlinked claims to targets
- Batch NER extraction of gene names from claim text
- Quick consistency check: do our hypothesis scores match the evidence?

## Phase 3: Hypothesis Generation & Validation (Hours 6-10)

### 3.1 Generate New Hypotheses from Fresh Evidence
```
POST /api/v2/generate/hypotheses
```
- Focus on claims from last 30 days
- Look for NEW convergence patterns
- Specifically target cross-paper bridges

### 3.2 Run Discovery Pipeline
```
POST /api/v2/discovery/run
```
- Claim volume spikes (new hot targets?)
- Hypothesis confirmations (old predictions now validated?)
- Novel targets (claims mentioning genes not in our target list)

### 3.3 Critical Validation Loop

For each TOP finding:
1. Check: Is this actually novel? (PubMed search for exact claim)
2. Check: Is the evidence base solid? (n > 5 papers? Independent labs?)
3. Check: Does it survive critical questioning? (What would disprove this?)
4. Check: Is it biologically plausible? (Known pathway? Mechanism?)
5. If survives all 4 → save to memory as validated finding
6. If fails any → document WHY it failed (anti-finding is also knowledge)

## Phase 4: Computational Predictions (Hours 10-16)

### 4.1 NVIDIA NIM Structural Biology
- RNAPro: Predict SMN2 ISS-N1 3D structure (if NIM is back up)
- OpenFold3: Predict SMN-CORO1C complex structure
- DiffDock v2.2: Re-dock top 10 hits with 20-pose validation
- GenMol: Generate novel compounds for validated targets

### 4.2 Cross-Paper Synthesis Upgrade
- Run co-occurrence analysis on expanded evidence base
- Find NEW transitive bridges (A→B→C where A and C never co-cited)
- Generate synthesis cards for top 3 novel connections
- Compare: which connections are truly novel vs already known?

### 4.3 Proteina-Complexa Dataset Integration
- Query AlphaFold DB for new SMA protein complexes
- Check: SMN+Gemin2/3/4/5, SMN+CORO1C, PLS3+actin, SMN+p53
- Store complex confidence scores
- Use for hypothesis ranking

## Phase 5: Platform Quality & Data Integrity (Hours 16-20)

### 5.1 Claim Quality Audit
- Sample 100 random claims, check extraction accuracy
- Identify systematic errors (gene name confusion, negation errors)
- Fix extraction prompts if error patterns found
- Re-extract claims with known errors

### 5.2 Score Calibration Check
- Re-run Bayesian calibration with latest data
- Check: do approved drugs still score higher than failed?
- Check: does new evidence change any target rankings?
- Document calibration grade

### 5.3 Evidence Gap Map
- For each of 50 targets: what evidence type is MISSING?
- Which targets have claims but zero human genetics?
- Which have genetics but zero functional data?
- This becomes the "what to study next" guide

## Phase 6: Documentation & Memory (Hours 20-24)

### 6.1 Update All Memory Files
- `sma-research-platform.md` — latest numbers, new findings
- `gpu-infrastructure.md` — any new GPU work
- `learnings-sma-biology.md` — new biology knowledge
- Create new memory files for major discoveries

### 6.2 Git Commit All Work
- One commit per logical unit of work
- Descriptive commit messages with `feat:`, `fix:`, `docs:`
- Never commit credentials

### 6.3 Scientific Summary Document
- Write `docs/FINDINGS-2026-03-21.md`
- Structure: Abstract, Key Findings, Evidence Quality, Limitations, Next Steps
- This becomes the "what we learned today" artifact
- Prof-level scientific writing, not marketing

### 6.4 MCP Server Updates
- Add any new tools needed for new data types
- Update existing tool descriptions if capabilities changed
- Verify all 32 tools still return correct data

## Success Criteria

At the end of 24 hours, the sprint is successful if:

1. [ ] Evidence base grew (new sources, claims, linked claims)
2. [ ] At least 1 genuinely novel finding that survives validation
3. [ ] Calibration grade maintained or improved
4. [ ] No data quality regressions
5. [ ] All findings saved to memory + git
6. [ ] Gap map produced (what's missing for each target)
7. [ ] Scientific summary written at professor level
8. [ ] Platform numbers updated in ROADMAP.md

## Anti-Patterns to Avoid

- Building new UI features (this is a research sprint, not a feature sprint)
- Adding modules nobody asked for
- Generating hypotheses without validating them
- Treating LLM output as evidence (it's synthesis, not data)
- Ignoring negative results (document what DIDN'T work)
- Over-engineering infrastructure (use what exists)
- Spending GPU money without expected value calculation
