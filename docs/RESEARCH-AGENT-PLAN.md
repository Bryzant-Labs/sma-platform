# SMA Research Agent Plan

**Date**: 2026-03-22
**Platform**: SMA Research Platform (moltbot, ~210 API endpoints, 32 MCP tools)
**Compute**: Claude Max plan (Opus lead, Sonnet agents, Haiku research), NVIDIA NIMs (12 cloud endpoints), Vast.ai GPU on-demand

---

## Overview

Six autonomous research tracks designed to run as background agents on the Max plan. Each track is self-contained with clear inputs, outputs, and dependencies. Tracks A-B can start immediately. Tracks C-D depend on the new NIM integrations (deployed 2026-03-22). Tracks E-F are LLM-only and can run anytime.

**Total estimated effort**: ~40-60 agent-hours across all tracks.

---

## Track A: Cross-Disease Transcriptomics

### What (Deliverables)
- DEG overlap table: CORO1C, CFL2, PFN1, ROCK2, LIMK1 expression across SMA, ALS, CMT, and other motor neuron diseases
- DESeq2 differential expression results for our 24-gene actin panel across 3 GEO datasets
- Single-cell motor neuron-specific expression profiles for key targets
- Summary report: which targets are SMA-specific vs. shared across neuromuscular diseases

### How (Tools, APIs, Compute)
- **GEO datasets**:
  - `GSE113924`: SMA vs. control motor neurons (bulk RNA-seq). Download supplementary DEG tables from GEO.
  - `GSE153960`: SMA mouse model time course (count matrices available). Run DESeq2 locally.
  - `GSE287257`: SMA iPSC-derived motor neurons (single-cell). Use scanpy/Seurat for MN-specific analysis.
- **Tools**: Python (pandas, DESeq2 via pydeseq2, scanpy), GEOquery, NCBI Entrez API
- **Compute**: CPU-only (no GPU needed). Runs in the sma-platform venv on moltbot.
- **LLM**: Haiku for data parsing/exploration, Sonnet for analysis code, Opus for interpretation

### Agent Spec
```
Agent: researcher (Haiku) + implementer (Sonnet)
Step 1: Download GSE113924 supplementary files via GEO FTP
Step 2: Parse DEG tables, extract fold-change + p-value for 24-gene panel
Step 3: Download GSE153960 count matrices
Step 4: Run pydeseq2 on count matrices (SMA vs. control, per timepoint)
Step 5: Download GSE287257, run scanpy clustering, identify MN cluster
Step 6: Extract MN-specific expression for 24-gene panel
Step 7: Cross-reference all 3 datasets, build overlap matrix
Output: JSON + markdown report -> ingest into platform claims
```

### Priority: HIGH
### Effort: 8-12 hours
### Can run as background agent: Yes
### Dependencies: None (all data is public on GEO)

---

## Track B: Extended DiffDock Campaign

### What (Deliverables)
- DiffDock v2.2 docking results for convergence synthesis drugs against all 63 targets with AlphaFold structures
- Re-docking of original campaign hits with v2.2 (our campaign used v2.0)
- Ranked hit list: compound-target pairs sorted by confidence score
- Comparison report: v2.0 vs. v2.2 confidence score changes

### How (Tools, APIs, Compute)
- **SMILES sources**: Platform DB (`/api/v2/screen/molecules`), DrugBank (FDA-approved CNS drugs), convergence synthesis hits (Fasudil, MW150, 4-AP analogs from GenMol)
- **PDB sources**: AlphaFold DB for all 63 targets (auto-download via UniProt ID mapping)
- **API**: DiffDock v2.2 NIM (`/api/v2/nims/dock`), batch endpoint for efficiency
- **Compute**: NVIDIA cloud credits (rate-limited). For large campaigns: Vast.ai self-hosted DiffDock.

### Agent Spec
```
Agent: implementer (Sonnet)
Step 1: Query platform API for all 63 targets with UniProt IDs
Step 2: Query platform API for convergence synthesis drugs (SMILES)
Step 3: Add new compounds: Fasudil (C14H17N3O2S), MW150, p38 MAPK inhibitors
Step 4: For each target: download AlphaFold PDB, batch-dock all compounds (3 poses each)
Step 5: Parse results, rank by confidence score
Step 6: Compare with original v2.0 results from platform DB
Step 7: Identify top 20 novel hits (not in original campaign)
Output: CSV ranked list + platform ingestion via /api/v2/ingest/docking
```

### Batching Strategy
- Group compounds in batches of 10-20 per DiffDock call (batch endpoint)
- Process targets in priority order: ROCK2, MAPK14, LIMK1, CFL2, PFN1 first
- Rate limit: ~100 dockings per hour on cloud NIM, unlimited on self-hosted

### Priority: HIGH
### Effort: 12-20 hours (depends on rate limits)
### Can run as background agent: Yes
### Dependencies: DiffDock v2.2 NIM (live, confirmed working)

---

## Track C: Protein Structure + Binder Design Pipeline

### What (Deliverables)
- AlphaFold2 NIM structures for top 20 targets (cross-validate with AlphaFold DB)
- ESMfold rapid structures for all 63 targets (screening pass)
- RFdiffusion binder designs for 3 priority targets: ROCK2, MAPK14, LIMK1
- ProteinMPNN-optimized sequences for top binder designs
- ESMfold validation of designed sequences (do they fold correctly?)
- Structural analysis report: binding site identification, druggability assessment

### How (Tools, APIs, Compute)
- **APIs** (all NVIDIA NIMs, deployed 2026-03-22):
  - AlphaFold2 NIM: `/api/v2/nims/alphafold2` (high-accuracy, slower)
  - ESMfold NIM: `/api/v2/nims/esmfold` (fast screening, no MSA)
  - RFdiffusion NIM: `/api/v2/nims/design-binder`
  - ProteinMPNN NIM: `/api/v2/nims/design-sequence`
  - MSA Search NIM: `/api/v2/nims/msa-search` (for AF2 pipeline)
- **Target sequences**: UniProt (auto-fetch via platform target DB)
- **Hotspot identification**: From DiffDock results (Track B) and literature active sites

### Agent Spec
```
Agent: implementer (Sonnet)
Phase 1 -- Screening (ESMfold, all 63 targets):
  Step 1: Get all target UniProt sequences from platform API
  Step 2: Run ESMfold for each (fast, ~30s per protein)
  Step 3: Compute pLDDT scores, flag low-confidence regions
  Step 4: Compare with existing AlphaFold DB structures

Phase 2 -- High-accuracy (AlphaFold2, top 20 targets):
  Step 5: Run MSA Search for each target
  Step 6: Run AlphaFold2 with MSA input
  Step 7: Compare with ESMfold results (pLDDT correlation)

Phase 3 -- Binder Design (ROCK2, MAPK14, LIMK1):
  Step 8: Identify hotspot residues from Track B docking results + literature
  Step 9: RFdiffusion: generate 10 binder backbones per target (80-120 residues)
  Step 10: ProteinMPNN: design 5 sequences per backbone
  Step 11: ESMfold: validate top sequences fold correctly
  Step 12: Score designs by pLDDT, select top 3 per target

Output: PDB files, sequence FASTA, ranking table, structural analysis report
```

### Priority: HIGH (novel computational biology, publishable)
### Effort: 15-25 hours
### Can run as background agent: Yes (Phases 1-2 fully autonomous; Phase 3 needs Track B hotspots)
### Dependencies:
- New NIM integrations (deployed 2026-03-22)
- Track B results for hotspot identification (Phase 3 only)
- NVIDIA API credits (monitor usage)

---

## Track D: Molecule Generation Pipeline

### What (Deliverables)
- 500+ novel molecules generated for ROCK2, MAPK14, LIMK1 scaffolds
- RDKit-filtered candidates (Lipinski Rule of 5, BBB permeability, CNS MPO > 4.0)
- DiffDock docking of top 50 filtered candidates per target
- Ranked drug candidate list with predicted binding + drug-likeness scores
- ADMET property predictions for top 10 candidates

### How (Tools, APIs, Compute)
- **Generation**: GenMol NIM (`/api/v2/nims/generate-molecules`)
  - Scaffolds: Fasudil, MW150, known ROCK2 inhibitors, known p38 inhibitors
  - 100-200 molecules per scaffold, QED scoring
- **Filtering**: RDKit (local Python)
  - Lipinski Rule of 5 (MW < 500, HBD <= 5, HBA <= 10, LogP <= 5)
  - BBB permeability (PSA < 90, MW < 450)
  - CNS MPO score > 4.0 (multiparameter optimization)
  - PAINS filter (pan-assay interference compounds)
- **Docking**: DiffDock v2.2 NIM (from Track B infrastructure)
- **ADMET**: SwissADME API or pkCSM (free, web-based)

### Agent Spec
```
Agent: implementer (Sonnet)
Step 1: Define scaffolds from convergence synthesis drugs
  - Fasudil: OC(=O)c1cccc2CCN(S(=O)=O)c12
  - MW150: from literature SMILES
  - 4-AP: Nc1ccncc1
  - Y-27632 (ROCK inhibitor): CC(N)C1CCC(CC1)c1ccncc1
Step 2: GenMol: generate 150 molecules per scaffold (4 scaffolds = 600 total)
Step 3: RDKit filtering pipeline:
  - Lipinski -> BBB -> CNS MPO -> PAINS -> uniqueness check
  - Expected yield: ~30-40% pass all filters
Step 4: DiffDock: dock top 50 per target (ROCK2, MAPK14, LIMK1)
Step 5: Rank by: DiffDock confidence * QED * CNS_MPO
Step 6: ADMET prediction for top 10 candidates
Output: Candidate table (SMILES, scores, properties) -> platform ingestion
```

### Priority: MEDIUM
### Effort: 8-12 hours
### Can run as background agent: Yes
### Dependencies:
- GenMol NIM (live, confirmed)
- DiffDock NIM (live, confirmed)
- RDKit installed in sma-platform venv (verify: `pip show rdkit-pypi`)

---

## Track E: Hypothesis Mining

### What (Deliverables)
- Hypotheses generated for all 63 targets using full claim corpus (14,176 claims)
- Cross-referenced hypotheses with convergence synthesis findings
- Prioritized hypothesis list focusing on MW150/Fasudil/p53 axis connections
- Novel therapeutic angle identification (like CORO1C double-hit model)
- Confidence-calibrated hypotheses (using Grade A calibration system, 89.8%)

### How (Tools, APIs, Compute)
- **LLM Strategy** (multi-model, cost-optimized):
  - Gemini 2.0 Flash: Bulk hypothesis generation (cheap, fast, good for structured extraction)
  - Sonnet 4: Quality filtering and scoring
  - Opus 4: Final review of top hypotheses, novel angle identification
- **Data**: Platform API (`/api/v2/hypotheses`, `/api/v2/claims`, `/api/v2/targets`)
- **MCP tools**: `validate_sma_hypothesis`, `search_sma_claims`, `get_sma_hypotheses`

### Agent Spec
```
Agent: researcher (Haiku for exploration) + implementer (Sonnet for generation)

Phase 1 -- Bulk Generation (Gemini):
  Step 1: Export all claims per target from platform API
  Step 2: For each target: prompt Gemini with claims + convergence context
  Step 3: Generate 5-10 hypotheses per target (63 * 7 = ~440 hypotheses)
  Step 4: Store raw hypotheses in platform DB

Phase 2 -- Quality Filter (Sonnet):
  Step 5: Score each hypothesis on novelty, testability, evidence support
  Step 6: Cross-reference with convergence synthesis (MW150/Fasudil/p53 axis)
  Step 7: Flag hypotheses connecting multiple targets (systems-level)
  Step 8: Remove duplicates and near-duplicates

Phase 3 -- Expert Review (Opus):
  Step 9: Review top 50 hypotheses for scientific rigor
  Step 10: Identify novel therapeutic angles (like CORO1C double-hit)
  Step 11: Calibrate confidence using Grade A system
  Step 12: Write summary report with actionable next steps

Output: Ranked hypothesis table, novel angles report, suggested experiments
```

### Priority: MEDIUM
### Effort: 6-10 hours
### Can run as background agent: Yes (Phase 1-2 fully autonomous)
### Dependencies:
- Gemini API key configured (check: `GOOGLE_API_KEY` in env)
- Platform API accessible (confirmed)
- Existing hypotheses in DB for deduplication (1,264 currently)

---

## Track F: Literature Expansion

### What (Deliverables)
- 500+ new PubMed abstracts ingested for underrepresented targets
- bioRxiv preprint monitoring set up for SMA/ALS/actin dynamics
- Patent literature scan (Google Patents) for ROCK2/MAPK14 inhibitors
- Updated claim count per target (currently 14,176 total)
- Literature gap report: which targets need more evidence

### How (Tools, APIs, Compute)
- **PubMed**: Entrez API (NCBI), batch download, rate-limited (10 req/sec with API key)
- **bioRxiv**: bioRxiv API (medrxiv.org/api), search for recent preprints
- **Patents**: Google Patents Public Datasets (BigQuery) or SerpAPI
- **Ingestion**: Platform API (`/api/v2/ingest/pubmed`, `/api/v2/ingest/abstracts`)
- **LLM**: Haiku for relevance screening, Sonnet for claim extraction

### Agent Spec
```
Agent: researcher (Haiku) + implementer (Sonnet)

Phase 1 -- Gap Analysis:
  Step 1: Query platform for claim count per target
  Step 2: Identify targets with < 50 claims (underrepresented)
  Step 3: Generate PubMed search queries for each underrepresented target
  Expected underrepresented: ~20-30 of 63 targets

Phase 2 -- Targeted PubMed Ingestion:
  Step 4: For each underrepresented target: PubMed search (2020-2026)
  Step 5: Download abstracts (max 50 per target)
  Step 6: Screen for relevance with Haiku (fast, cheap)
  Step 7: Extract claims from relevant abstracts with Sonnet
  Step 8: Ingest claims via platform API

Phase 3 -- Preprint Monitoring:
  Step 9: bioRxiv API: search "spinal muscular atrophy" (last 90 days)
  Step 10: bioRxiv API: search "actin dynamics motor neuron" (last 90 days)
  Step 11: bioRxiv API: search "ROCK2 inhibitor" OR "p38 MAPK neurodegeneration"
  Step 12: Screen + ingest relevant preprints

Phase 4 -- Patent Literature:
  Step 13: Google Patents: "ROCK2 inhibitor" filed 2023-2026
  Step 14: Google Patents: "SMN2 splicing modifier" filed 2023-2026
  Step 15: Extract patent claims, map to our targets
  Step 16: Identify commercial interest signals

Output: Ingested claims, gap report, monitoring schedule
```

### Monitoring Schedule (Recurring)
- PubMed: Weekly (every Monday, automated via cron or n8n)
- bioRxiv: Weekly (same schedule)
- Patents: Monthly

### Priority: LOW (incremental improvement, not urgent)
### Effort: 10-15 hours (initial), 1-2 hours/week (ongoing)
### Can run as background agent: Yes (fully autonomous)
### Dependencies:
- NCBI API key for higher rate limits (check: `NCBI_API_KEY` in env)
- Platform ingestion endpoints working (confirmed)

---

## Execution Order

```
Week 1 (Immediate):
  [A] Cross-Disease Transcriptomics  <- START (no dependencies)
  [B] Extended DiffDock Campaign      <- START (no dependencies)
  [E] Hypothesis Mining Phase 1       <- START (Gemini bulk, no dependencies)

Week 2:
  [C] Protein Structure Phase 1-2     <- START (ESMfold + AF2 screening)
  [D] Molecule Generation             <- START (GenMol + RDKit)
  [F] Literature Expansion Phase 1-2  <- START (gap analysis + PubMed)

Week 3:
  [C] Phase 3: Binder Design          <- DEPENDS ON Track B hotspots
  [E] Phase 2-3: Quality + Expert     <- DEPENDS ON Phase 1 completion
  [F] Phase 3-4: Preprints + Patents  <- Can run in parallel

Week 4:
  Integration: Cross-reference all track results
  Report: Comprehensive findings document for Simon meeting
```

---

## Resource Budget

| Resource | Tracks | Estimated Usage |
|----------|--------|----------------|
| NVIDIA NIM credits | B, C, D | ~500-800 credits (monitor at build.nvidia.com) |
| Gemini API (bulk) | E, F | ~$2-5 (Flash is cheap) |
| Claude Opus (review) | E | ~$10-15 (top hypotheses only) |
| Claude Sonnet (agents) | All | ~$20-30 (main workhorse) |
| Claude Haiku (research) | A, F | ~$1-3 (fast/cheap) |
| Vast.ai GPU | B (optional) | $0 if using cloud NIM; ~$5-10/hr if self-hosted |
| Compute (moltbot CPU) | A, D | Included (server already running) |

**Total estimated cost**: $35-65 for all six tracks.

---

## Risk Mitigation

1. **NVIDIA rate limits**: Batch operations, priority ordering, optional Vast.ai fallback
2. **ESM-2 degradation**: Retry logic deployed (3 attempts, exponential backoff). Monitor.
3. **RNAPro unavailable**: Marked as container-only. Plan Vast.ai deployment if needed.
4. **GEO data quality**: Validate sample counts, check for batch effects before DESeq2
5. **GenMol output quality**: RDKit filtering catches bad molecules. PAINS filter removes false positives.
6. **Credit exhaustion**: Start with priority targets (ROCK2, MAPK14, LIMK1), expand if credits allow
7. **Hypothesis hallucination**: Multi-model validation (generate with Gemini, validate with Opus)

---

## Integration with Existing Platform

All track outputs feed into the platform via existing API endpoints:
- Claims: `POST /api/v2/ingest/abstracts` or `POST /api/v2/ingest/claims`
- Docking results: `POST /api/v2/ingest/docking`
- Structures: stored as PDB files in `/data/structures/`
- Hypotheses: `POST /api/v2/hypotheses`
- Molecules: `POST /api/v2/screen/molecules`

MCP tools available for agent self-service:
- `search_sma_claims`, `search_sma_targets`, `search_sma_drugs`
- `validate_sma_hypothesis`, `get_sma_hypotheses`
- `simulate_sma_digital_twin`
