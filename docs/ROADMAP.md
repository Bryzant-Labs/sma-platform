# SMA Research Platform — Roadmap

> Last updated: 2026-03-15

## Milestone Tracker

### M1: Evidence Foundation (COMPLETE)

| Deliverable | Status | Date |
|------------|--------|------|
| PubMed ingestion (301 search queries) | DONE | Feb 2026 |
| ClinicalTrials.gov v2 adapter (449 trials) | DONE | Feb 2026 |
| GEO dataset metadata adapter | DONE | Feb 2026 |
| bioRxiv/medRxiv scanner | DONE | Mar 2026 |
| LLM claim extraction (22,607 claims) | DONE | Feb 2026 |
| Evidence scoring (method weights + tier multipliers) | DONE | Feb 2026 |
| Knowledge graph (428 edges, 34 relation types) | DONE | Feb 2026 |
| UCM Parquet pipeline (HuggingFace) | DONE | Mar 2026 |
| REST API (~155 endpoints) | DONE | Feb 2026 |
| Frontend dashboard (vanilla JS) | DONE | Feb 2026 |

### M2: Analytical Intelligence (COMPLETE)

| Deliverable | Status | Date |
|------------|--------|------|
| Mechanistic hypothesis generator (220+ cards) | DONE | Feb 2026 |
| Splice Variant Predictor (rule-based + ESM-2) | DONE | Mar 2026 |
| Auto-Discovery pipeline (spikes, confirmations, novel) | DONE | Mar 2026 |
| Computational screening (21,228 molecules) | DONE | Mar 2026 |
| Drug failure/success database | DONE | Mar 2026 |
| Cross-species orthologs (NCBI) | DONE | Mar 2026 |
| STRING-DB protein interactions | DONE | Mar 2026 |
| KEGG pathway mapping | DONE | Mar 2026 |
| ChEMBL bioactivity data | DONE | Mar 2026 |
| UniProt protein annotations | DONE | Mar 2026 |

### M3: Evidence Depth (IN PROGRESS — March 2026)

| Deliverable | Status | Endpoint | Impact |
|------------|--------|----------|--------|
| Full-text analysis (PMC OA, 3 sources) | BUILT | `POST /ingest/fulltext` | 3-5x more claims per paper |
| Clinical trial results parsing | BUILT | `POST /ingest/trial-results` | Real outcome data (p-values, AEs) |
| Patent literature (PatentsView) | BUILT | `POST /ingest/patents` | IP landscape + novel mechanisms |
| AlphaFold protein structures | BUILT | `POST /ingest/structures` | 3D context for all 7 SMA proteins |
| MCP Server (20 tools, REST-based) | BUILT | npm/pip package | Researcher AI co-pilot |
| Claim re-scoring (SMA relevance) | ~20% | `POST /rescore/claims` | Remove noise, improve signal |
| Hypothesis upgrade (Sonnet 4.6) | PENDING | `POST /generate/hypotheses` | Higher-quality mechanistic cards |

**Gate → M4:** All M3 deliverables deployed and triggered on moltbot. Re-scored claims. Regenerated hypotheses with Sonnet 4.6.

### M4: Cross-Paper Synthesis (Target: April 2026)

This is **Differentiator #1** — finding connections no single researcher could see.

| Deliverable | Status | Description |
|------------|--------|-------------|
| Temporal evidence analysis | PLANNED | Detect when new evidence retroactively strengthens old findings |
| Contradiction detection | PLANNED | Flag conflicting high-confidence claims from independent sources |
| "Evidence surprise" scoring | PLANNED | Rank hypotheses by how non-obvious the connection is |
| Cross-target pathway synthesis | PLANNED | "NCALD + Calcium signaling → new hypothesis about STMN2" |
| Hypothesis quality v2 | PLANNED | Move from descriptive summaries to genuine cross-paper synthesis |
| Full-text claim extraction | PLANNED | Extract claims from full body text, not just abstracts |

**Success metric:** A professor reads a generated hypothesis and says "I never thought of connecting those two."

### M5: Predictive Evidence Layer (Target: May 2026)

This is **Differentiator #2** — quantitative, grounded predictions.

| Deliverable | Status | Description |
|------------|--------|-------------|
| Bayesian evidence convergence model | PLANNED | Probability model over claim types, source quality, replication |
| Drug-target synergy prediction | PLANNED | Combine screening + pathway overlap + literature co-occurrence |
| Confidence calibration | PLANNED | Back-test predictions against known outcomes (approved therapies) |
| Uncertainty quantification | PLANNED | Every prediction carries explicit confidence intervals |
| Target prioritization engine | PLANNED | Multi-criteria scoring: evidence + biology + interventionability |

**Success metric:** A predicted drug-target interaction scores >70% confidence and is later confirmed experimentally.

### M6: Researcher Tools (Target: June 2026)

This is **Differentiator #3** — making the platform accessible to every SMA researcher.

| Deliverable | Status | Description |
|------------|--------|-------------|
| MCP Server distribution (npm + pip) | PLANNED | One-command install for Claude Desktop / Claude Code |
| Researcher documentation | PLANNED | Example queries, use cases, getting started guide |
| Embedding-based semantic search | PLANNED | FAISS + sentence-transformers for nuanced queries |
| Automated literature review | PLANNED | Per-target review generation from all evidence |
| Experiment design suggestions | PLANNED | Grounded in evidence gaps, actionable next steps |
| BibTeX/CSV/JSON export expansion | PLANNED | Full data portability for researchers |

**Success metric:** A researcher installs the MCP server, asks a complex question, and trusts the answer enough to cite in a grant application.

### M7: Warp-Speed (Target: Q3-Q4 2026)

| Deliverable | Status | Description |
|------------|--------|-------------|
| Agentic Research Swarm | PLANNED | Multi-agent hypothesis exploration and validation |
| Digital Twin (in silico SMA model) | PLANNED | Pathway simulation for testing interventions computationally |
| Lab-OS Integration | PLANNED | LIMS/ELN connectivity to bridge computational → wet lab |
| Zero-Knowledge Data Sharing | PLANNED | Federated analytics for multi-site collaboration |
| GitHub for Life (Versioned biology) | PLANNED | Git-like versioning for biological knowledge |

---

## Current Sprint (March 15-31, 2026)

### Priority Actions

1. **Deploy M3 to moltbot** — rsync all new adapters + ingestion routes, restart PM2
2. **Trigger full-text ingestion** — `POST /ingest/fulltext?batch_size=200` (infrastructure ready)
3. **Trigger trial results ingestion** — `POST /ingest/trial-results` (adapter ready)
4. **Trigger patent ingestion** — `POST /ingest/patents` (adapter ready)
5. **Trigger AlphaFold ingestion** — `POST /ingest/structures` (adapter ready)
6. **Complete claim re-scoring** — currently at ~20%, needs to finish
7. **Regenerate hypotheses** — `POST /generate/hypotheses` after re-scoring completes
8. **Update HuggingFace dataset** — with new claims, full-text, trial results

### Blocked On

- Claim re-scoring completion (~80% remaining)
- Professor feedback (email sent, awaiting response)

---

## Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| PatentsView over Lens.org | Free, no API key, US patents cover most SMA IP |
| AlphaFold DB over ESMFold | Pre-computed structures are faster and more reliable; missense scores available |
| MCP via REST API (not SQLite) | Live data, no sync needed, works from any machine |
| 3-source full-text fallback | Europe PMC → NCBI PMC → Unpaywall maximizes OA coverage |
| Plain-text summaries for LLM | Uniform format lets claim_extractor treat all sources the same |

---

## Adapter Inventory

| Adapter | File | Source | Records |
|---------|------|--------|---------|
| PubMed | `pubmed.py` | NCBI Entrez | 4,582 papers |
| ClinicalTrials.gov | `clinicaltrials.py` | v2 REST API | 449 trials + results |
| bioRxiv/medRxiv | `biorxiv.py` | bioRxiv API | ~50 preprints/scan |
| GEO | `geo.py` | NCBI Entrez | 7 datasets |
| PMC Full-Text | `pmc.py` | Europe PMC + NCBI + Unpaywall | OA papers |
| STRING-DB | `string_db.py` | STRING API | Protein interactions |
| KEGG | `kegg.py` | KEGG REST | Pathway genes |
| ChEMBL | `chembl.py` | ChEMBL API | Bioactivities |
| UniProt | `uniprot.py` | UniProt REST | Protein annotations |
| Orthologs | `orthologs.py` | NCBI Gene | Cross-species data |
| **Patents** | `patents.py` | PatentsView | SMA patents (NEW) |
| **AlphaFold** | `alphafold.py` | AlphaFold DB + Missense | Protein structures (NEW) |
