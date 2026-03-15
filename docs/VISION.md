# SMA Research Platform — Vision & Differentiators

## Leitfaden

We don't replace researchers. We can't build a drug. But we can make every SMA researcher 10x faster by finding connections they'd never see, making predictions they can test, and giving them instant access to structured knowledge across 4,582+ sources.

---

## Three Core Differentiators

### 1. Non-Obvious Connections (Cross-Think)

**The Promise:** "Paper X from 2019 about NCALD and Paper Y from 2025 about Calcium Signaling together say something NEW that neither author saw."

**Why this matters:** No single researcher reads all 4,582 SMA publications. Our platform cross-references 22,607 claims simultaneously and surfaces connections across targets, pathways, and timepoints that are invisible to any individual.

**Current State:** Infrastructure exists — claims are extracted and linked to targets. The hypothesis engine generates mechanistic cards from evidence convergence.

**What's Needed:**
- Improve hypothesis quality: move from descriptive summaries to genuine cross-paper synthesis
- Add temporal analysis: detect when new evidence from 2025 retroactively strengthens a 2019 finding
- Build contradiction detection: flag when two high-confidence claims from independent sources conflict
- Implement "evidence surprise" scoring: rank hypotheses by how non-obvious the connection is

**Success Metric:** A professor reads a generated hypothesis and says "I never thought of connecting these two" — then designs an experiment to test it.

---

### 2. Predictive Statements (Evidence Convergence Scoring)

**The Promise:** "Based on evidence convergence of 47 claims from 23 sources, Target X has a 73% probability of synergistic effect with Drug Y."

**Why this matters:** Researchers make intuitive prioritization decisions every day. We can quantify what the evidence actually supports — grounded in data, not opinion.

**Current State:** Basic confidence scoring exists per claim. Evidence strength scores per target (0-100 composite). No cross-target predictive modeling yet.

**What's Needed:**
- Probabilistic convergence model: Bayesian network over claim types, source quality, replication count
- Drug-target synergy prediction: combine screening data + pathway overlap + literature co-occurrence
- Confidence calibration: back-test predictions against known outcomes (e.g., trial results for approved therapies)
- Uncertainty quantification: every prediction must carry explicit confidence intervals

**Success Metric:** A predicted drug-target interaction scores >70% confidence, and a subsequent wet-lab experiment confirms it.

---

### 3. MCP Server — The Game-Changer

**The Promise:** "What do we know about PLS3 as a severity modifier in Type 2 patients?" → Instant structured answer from 4,582 papers.

**Why this matters:** No other tool in existence lets a researcher query the entire SMA evidence base in natural language and get a grounded, citation-backed response in seconds.

**Current State:** 20 MCP tools built and functional. REST API-backed, live data. Tools cover targets, claims, hypotheses, trials, drugs, discovery signals, splice prediction, screening, knowledge graph, BibTeX export, and cross-target comparison.

**What's Needed:**
- Distribution: package as installable MCP server for Claude Desktop / Claude Code
- Documentation: researcher-friendly guide with example queries and use cases
- Semantic search: add embedding-based search across claims and full-text for nuanced queries
- Response synthesis: pre-assemble context so the LLM can give richer, more grounded answers

**Success Metric:** A researcher installs the MCP server, asks a complex question, and gets an answer they trust enough to cite in a grant application.

---

## Implementation Roadmap

### Phase A: Evidence Depth (Current Sprint — March 2026)

| Feature | Status | Impact |
|---------|--------|--------|
| Full-Text Analysis (PMC OA) | Built, needs trigger | 3-5x more evidence per paper |
| Clinical Trial Results Parsing | Built | Real outcome data for claim extraction |
| Patent Literature Integration | Building | IP landscape + novel mechanisms |
| AlphaFold/ESMFold Integration | Building | Protein structure context for targets |
| MCP Server (20 tools) | Built | Researcher-facing query interface |

### Phase B: Intelligence Layer (April 2026)

| Feature | Target | Impact |
|---------|--------|--------|
| Cross-paper synthesis hypotheses | Improved hypothesis engine | Differentiator #1 |
| Temporal evidence analysis | New analytical module | Detect emerging trends before publication spikes |
| Contradiction detection | New analytical module | Flag conflicting evidence for resolution |
| Evidence convergence scoring | Bayesian model | Differentiator #2 |

### Phase C: Researcher Tools (May 2026)

| Feature | Target | Impact |
|---------|--------|--------|
| MCP Server distribution (npm/pip) | Packaged installer | Differentiator #3 |
| Embedding-based semantic search | FAISS + sentence-transformers | Nuanced query understanding |
| Automated literature review | Per-target review generation | Save weeks of manual review |
| Experiment design suggestions | Grounded in evidence gaps | Actionable next steps |

### Phase D: Warp-Speed (Q3 2026)

| Feature | Target | Impact |
|---------|--------|--------|
| Agentic Research Swarm | Multi-agent hypothesis exploration | Autonomous discovery |
| Digital Twin (in silico SMA model) | Pathway simulation | Test interventions computationally |
| Lab-OS Integration | LIMS/ELN connectivity | Bridge computational → wet lab |
| Zero-Knowledge Data Sharing | Federated analytics | Multi-site collaboration without data exposure |

---

## Inspiration

A non-biologist designed a functional mRNA cancer vaccine using only AI tools (LinkedIn, March 2025). This proves that AI + structured data + the right tooling can dramatically accelerate research. Our platform aims to do the same for SMA — not by replacing domain expertise, but by amplifying it.

---

## Key Numbers (as of March 2026)

- **4,582** indexed sources (PubMed + bioRxiv/medRxiv + ClinicalTrials.gov)
- **22,607** LLM-extracted scientific claims
- **220+** mechanistic hypothesis cards
- **21** molecular targets (10 established + 11 discovery)
- **16** drugs/therapies tracked
- **449** clinical trials indexed
- **21,228** computationally screened molecules
- **~155** REST API endpoints
- **20** MCP tools for AI-assisted research
- **MIT License** — fully open source
