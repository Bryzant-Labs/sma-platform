# SMA Research Platform — Roadmap

> Last updated: 2026-03-20

## Milestone Tracker

### M1: Evidence Foundation (COMPLETE)

| Deliverable | Status | Date |
|------------|--------|------|
| PubMed ingestion (301 search queries) | DONE | Feb 2026 |
| ClinicalTrials.gov v2 adapter (449 trials) | DONE | Feb 2026 |
| GEO dataset metadata adapter | DONE | Feb 2026 |
| bioRxiv/medRxiv scanner | DONE | Mar 2026 |
| LLM claim extraction (25,054 claims) | DONE | Mar 2026 |
| Evidence scoring (method weights + tier multipliers) | DONE | Feb 2026 |
| Knowledge graph (428 edges, 34 relation types) | DONE | Feb 2026 |
| UCM Parquet pipeline (HuggingFace) | DONE | Mar 2026 |
| REST API (~190 endpoints) | DONE | Mar 2026 |
| Frontend dashboard (vanilla JS) | DONE | Mar 2026 |

### M2: Analytical Intelligence (COMPLETE)

| Deliverable | Status | Date |
|------------|--------|------|
| Mechanistic hypothesis generator (515 cards) | DONE | Mar 2026 |
| Splice Variant Predictor (rule-based + ESM-2) | DONE | Mar 2026 |
| Auto-Discovery pipeline (spikes, confirmations, novel) | DONE | Mar 2026 |
| Computational screening (21,228 molecules) | DONE | Mar 2026 |
| Drug failure/success database | DONE | Mar 2026 |
| Cross-species orthologs (NCBI) | DONE | Mar 2026 |
| STRING-DB protein interactions | DONE | Mar 2026 |
| KEGG pathway mapping | DONE | Mar 2026 |
| ChEMBL bioactivity data | DONE | Mar 2026 |
| UniProt protein annotations | DONE | Mar 2026 |

### M3: Evidence Depth (COMPLETE)

| Deliverable | Status | Date |
|------------|--------|------|
| Full-text analysis (PMC OA) | BUILT | Mar 2026 |
| Clinical trial results parsing (56 with results) | DONE | Mar 2026 |
| Patent literature (578 patents via Google Patents) | DONE | Mar 2026 |
| AlphaFold protein structures (7 proteins, v6) | DONE | Mar 2026 |
| MCP Server (29 tools, REST-based) | DONE | Mar 2026 |
| Claim re-scoring (SMA relevance) | DONE | Mar 2026 |
| Hypothesis upgrade (Sonnet 4.6, 515 hypotheses) | DONE | Mar 2026 |

### MG: GPU Compute Infrastructure (MOSTLY COMPLETE)

| Deliverable | Status | Date |
|------------|--------|------|
| Docker image (csiicf/sma-gpu-toolkit, 14.7GB) | DONE | Mar 2026 |
| SpliceAI scoring (252 variants, 21 high-impact) | DONE | Mar 2026 |
| ESM-2 protein embeddings (15 targets, 1280-dim) | DONE | Mar 2026 |
| Cas-OFFinder off-target scan (2,631 off-targets) | DONE | Mar 2026 |
| DiffDock v1 docking (140 complexes) | DONE | Mar 2026 |
| DiffDock v2.2 NIM batch (378 dockings, $0) | DONE | Mar 2026 |
| Boltz-2 structure prediction (5 proteins on A100) | DONE | Mar 2026 |
| NVIDIA NIMs integration (DiffDock, OpenFold3, GenMol) | DONE | Mar 2026 |
| GenMol de novo molecules (20 4-AP analogs) | DONE | Mar 2026 |
| ESM-2 similarity matrix (105 pairs) | DONE | Mar 2026 |
| ESM-2 contact maps (5 protein pairs) | DONE | Mar 2026 |
| SMN1 variant effect scoring (9 mutations) | DONE | Mar 2026 |
| Protein clustering (15 targets, PCA) | DONE | Mar 2026 |
| OpenMM molecular dynamics | BLOCKED | Needs CUDA OpenMM plugin |
| Virtual screening (630 compounds) | IN PROGRESS | ChEMBL expanded, NIM batch ready |

### M4: Cross-Paper Synthesis (IN PROGRESS — March 2026)

**Differentiator #1** — finding connections no single researcher could see.

| Deliverable | Status | Description |
|------------|--------|-------------|
| Co-occurrence analysis (30 target pairs) | DONE | Targets discussed in same paper |
| Transitive bridges (53 bridges) | DONE | A→B→C chains across papers |
| Shared mechanisms (33 mechanisms) | DONE | Same pathway, different targets |
| Claude synthesis cards (6 cards) | DONE | Mechanistic explanations |
| Temporal evidence analysis | DONE | New evidence retroactively strengthens old findings |
| Contradiction detection | DONE | Conflicting high-confidence claims |
| "Evidence surprise" scoring | DONE | Rank by non-obviousness |
| Claim-target linking enrichment | IN PROGRESS | NER on predicates to link more claims to targets |
| Full-text claim extraction | PLANNED | Claims from body text, not just abstracts |

**Success metric:** A professor reads a generated hypothesis and says "I never thought of connecting those two." *(SMN1-NCALD calcium bridge = first example)*

### M5: Predictive Evidence Layer (Target: April 2026)

**Differentiator #2** — quantitative, grounded predictions.

| Deliverable | Status | Description |
|------------|--------|-------------|
| Convergence scoring engine (5 dimensions) | DONE | Volume, lab independence, method diversity, temporal, replication |
| Prediction cards (falsifiable predictions) | DONE | Structured from convergence scores |
| Bayesian evidence convergence model | DONE | Grade A (89.8%) — back-tested against 227 drug outcomes |
| Drug-target synergy prediction | DONE | Synergy module live with search + sort |
| Confidence calibration | DONE | Approved drugs score higher than failed — validated |
| Uncertainty quantification | PLANNED | Explicit confidence intervals |
| Target prioritization engine | PLANNED | Multi-criteria: evidence + biology + interventionability |

### M6: Researcher Tools (Target: May 2026)

**Differentiator #3** — making the platform accessible to every SMA researcher.

| Deliverable | Status | Description |
|------------|--------|-------------|
| MCP Server (29 tools) | DONE | REST-based, works with Claude Desktop/Code |
| Embedding-based semantic search (FAISS) | DONE | Claims + sources indexed |
| English presentation (21 slides) | DONE | PPTX + HTML versions |
| German presentation (20 slides) | DONE | HTML version |
| News & Discoveries section | DONE | 4 posts, comments, RSS feed |
| bioRxiv preprint outline | DONE | 395-line detailed outline |
| Researcher outreach emails | DONE | 3 drafts (not in repo) |
| Researcher documentation | PLANNED | Example queries, use cases, getting started |
| Automated literature review | PLANNED | Per-target review from all evidence |
| Experiment design suggestions | PLANNED | From evidence gaps |

### M7: Publication & Outreach (Target: April 2026)

| Deliverable | Status | Description |
|------------|--------|-------------|
| bioRxiv preprint (multi-target 4-AP) | IN PROGRESS | Full draft being written (4000 words) |
| Researcher outreach (Simon, Cure SMA, Krainer) | DONE | 3 polished emails in docs/emails/ |
| HuggingFace dataset (updated) | DONE | SMAResearch/sma-evidence-graph |
| GitHub repository (public) | DONE | Bryzant-Labs/sma-platform |
| Docker Hub image | DONE | csiicf/sma-gpu-toolkit |

### M8: Warp-Speed (Target: Q3-Q4 2026)

| Deliverable | Status | Description |
|------------|--------|-------------|
| Digital Twin (pathway simulation) | PARTIAL | Basic temporal simulation built |
| Agentic Research Swarm | PLANNED | Multi-agent hypothesis exploration |
| Lab-OS Integration | PLANNED | LIMS/ELN connectivity |
| Federated analytics | PLANNED | Multi-site collaboration |

---

## Key Discoveries (2026-03-16)

1. **4-AP → CORO1C (+0.251)** — strongest binding of 378 compound-target pairs
2. **4-AP is a multi-target binder** — engages CORO1C, NCALD, SMN2, SMN1
3. **SMN1-NCALD calcium signaling bridge** — cross-paper synthesis discovery
4. **4-AP scaffold is optimal** — GenMol analogs don't improve CORO1C binding
5. **UBA1 is highly druggable** — 5 compounds in top 25

---

## Current Numbers

| Metric | Count |
|--------|-------|
| Claims | 30,153 |
| Hypotheses | 1,262 |
| Sources | 6,176 |
| Trials | 449 |
| Targets | 21 |
| Drugs | 16 |
| Screening compounds | 630 |
| MCP tools | 32 |
| API endpoints | ~210 |
| Synthesis cards | 6 |
| GPU dockings | 1,429 (140 v1 + 378 v2.2 + 957 GenMol screen) |
| Protein structures | 8 (AlphaFold DB complexes) |
| Protein embeddings | 15 (ESM-2) |
| Similarity pairs | 105 (cosine matrix) |
| Contact maps | 5 (protein-protein interaction) |
| Variant scores | 9 (SMN1 pathogenic mutations) |
| Calibration grade | A (89.8%) |
| Daily pipeline | Active (cron 6 UTC) |

---

## Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| Google Patents over PatentsView | PatentsView is US-only; Google Patents has global coverage |
| AlphaFold v6 structures | Latest version, most accurate |
| NVIDIA NIM API over self-hosted DiffDock | Free credits, no GPU cost, 16% more accurate (v2.2) |
| pip OpenMM over conda | Single Python environment, simpler Docker |
| Cross-Paper Synthesis without confidence filter | 97% of claims have confidence 0.1-0.3 (LLM extraction default) |
| Docker Hub (csiicf) | Public image for Vast.ai pull |
