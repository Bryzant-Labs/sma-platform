# SMA Research Platform — Milestones Roadmap

> Living document tracking research directions and implementation milestones.
> Last updated: 2026-03-15

---

## Phase 1: Evidence Foundation (COMPLETE)

- [x] PubMed ingestion pipeline (Biopython Entrez)
- [x] ClinicalTrials.gov v2 adapter (449 trials)
- [x] GEO dataset metadata adapter
- [x] LLM claim extraction (Claude Haiku) from abstracts
- [x] Evidence scoring (method weights, tier multipliers)
- [x] Knowledge graph: nodes, edges, evidence linking
- [x] Hypothesis generation from evidence convergence
- [x] Target identification: 10 established + 11 discovery targets

## Phase 2: Multi-Criteria Scoring & Prioritization (COMPLETE)

- [x] 7-dimension scoring: genetic evidence, biological coherence, clinical validation, druggability, network centrality, publication density, biomarker potential
- [x] Hypothesis prioritization: 102 hypotheses ranked in A/B/C tiers
- [x] Score persistence in `target_scores` table
- [x] Composite score calculation with dimension weighting

## Phase 3: Data Source Expansion (COMPLETE)

- [x] ChEMBL bioactivity data (188 compounds with pChEMBL values)
- [x] UniProt protein annotations (18 proteins, GO terms, pathways)
- [x] STRING-DB protein-protein interactions (10 PPI edges)
- [x] KEGG pathway membership (41 pathway genes)
- [x] SMA MCP Server (12 tools for AI agent integration)

## Phase 4: Cross-Species Comparative Biology (IN PROGRESS)

### 4.1 Ortholog Mapping (COMPLETE)
- [x] NCBI Datasets API adapter with multi-species search
- [x] 5 model organisms: axolotl, zebrafish, naked mole rat, C. elegans, Drosophila
- [x] Conservation breadth scoring (0-1)
- [x] `cross_species_targets` database table
- [x] Comparative API endpoints (`/api/v2/comparative/`)
- [x] Gene symbol case-variant handling per species

### 4.2 Cross-Species PubMed Literature (COMPLETE)
- [x] 16 cross-species search queries (axolotl, zebrafish, naked mole rat, C. elegans, Drosophila)
- [x] Cross-species regeneration queries

### 4.3 Cross-Disease Learning (COMPLETE)
- [x] ALS / motor neuron disease overlap (SMN, STMN2, TDP-43, SOD1)
- [x] DMD / Duchenne (NMJ, exon skipping, gene therapy)
- [x] SBMA / Kennedy disease (lower motor neuron, androgen receptor)
- [x] Myasthenia Gravis (NMJ, complement, acetylcholine receptor)
- [x] Charcot-Marie-Tooth (axonal degeneration, neuropathy)
- [x] Friedreich Ataxia (mitochondrial, frataxin)
- [x] General cross-disease drug repurposing queries

### 4.4 Frontend Comparative Tab (COMPLETE)
- [x] Cross-species visualization in frontend (Species tab)
- [x] Ortholog mapping display (species cards with counts)
- [x] Conservation heatmap (target × species matrix with % scores)

## Phase 5: Querdenker Research Directions (IN PROGRESS)

### 5.1 Gemini Querdenker-Ansaetze (COMPLETE — queries added)
- [x] Bear Hibernation / Muscle Preservation (myosin ATPase, torpor, SUMOylation)
- [x] Bioelectricity / Michael Levin (bioelectric regeneration, Vmem, gap junctions)
- [x] Epigenetic Dimming / dCas9 (CRISPRi, FSHD/DUX4, chromatin remodeling)
- [x] ECM / Matrix Engineering (fibrosis reversal, decellularized matrix, MMP)
- [x] Cross-Species Proteomics (axolotl proteomics, alternative splicing, spatial transcriptomics)

### 5.2 Harvard-Level Cutting-Edge (COMPLETE — queries added)
- [x] Spatial Multi-Omics / "Google Maps of Muscle" (Slide-seq, MERFISH, niche-specific drug discovery)
- [x] NMJ-on-a-Chip / Organ-on-Chip (microphysiological systems, extracellular vesicles, retrograde signaling)
- [x] Bioelectric Patches / Electroceuticals (functional electrical stimulation, satellite cell activation)
- [x] Atrofish / NDRG1 / Survivorship Bias (cell dormancy, quiescence, stress response)
- [x] SMA as Multisystem Disease (liver metabolism, systemic effects, energy metabolism)

### 5.3 Unconventional Querdenker (COMPLETE — queries added)
- [x] RNA Decoy / Sponge Strategy (hnRNP A1 sequestration, splicing factor decoys)
- [x] Mitochondrial Overdrive / PGC-1alpha (bioenergetic rescuing, NAD+)
- [x] DUBTACs — Protein Stabilization via deubiquitination (reverse PROTACs for SMN)
- [x] Mechanotransduction (vibration therapy, HSP activation, chaperone-mediated protection)
- [x] Engineered Probiotics / Microbiome-Logic (gut-brain axis, butyrate/HDAC, living therapeutics)
- [x] Naked Mole Rat / HMM-HA (high-MW hyaluronic acid, HAS2, CD44-mediated cytoprotection)
- [x] Axolotl c-Fos/JunB switch (regeneration vs scar molecular switch, miR-200a, sustained ERK)
- [x] Spinal Cord Stimulation in SMA (epidural stimulation, Nature Medicine 2024)

### 5.4 Evidence Integration (IN PROGRESS)
- [x] Run claim extraction on all Querdenker papers (12,900+ claims and growing)
- [x] Link Querdenker claims to existing targets (DNMT3B, SULF1, ANK3, CD44, CTNNA1)
- [x] Generate Querdenker-specific hypotheses (189 hypotheses across all targets)
- [x] Score new hypotheses against established targets
- [x] Research Directions API with deep-dive (16 directions, connected targets/claims/hypotheses)
- [x] Research Directions frontend tab with interactive deep-dive

## Phase 6: Computational Drug Discovery (IN PROGRESS)

### 6.1 Small Molecule Design
- [x] RDKit molecular descriptor calculation (Lipinski, BBB, CNS MPO, QED, PAINS)
- [x] Drug screening dashboard (188 compounds screened, 100 drug-like, 18 BBB-permeable)
- [x] SMILES-based single compound screening API
- [x] ADMET prediction pipeline (absorption, distribution, metabolism, excretion, toxicity)
- [x] Drug repurposing candidate identification (57 candidates from cross-disease + ChEMBL)
- [x] Knowledge graph auto-expansion (claim-based + drug-outcome + conservation edges)
- [x] 9-stage daily pipeline (PubMed → Trials → Claims → Hypotheses → Full-text → Drug Outcomes → Relinking → Graph Expansion → Scoring)
- [ ] Molecular docking (AutoDock Vina / DiffDock)
- [ ] Virtual screening against SMN2 splicing targets
- [ ] In silico screening for dual-target molecules (SMN2 + ion channels — bioelectricity intersection)

### 6.2 CRISPR / Prime Editing
- [ ] Guide RNA design for SMA targets
- [ ] Off-target prediction
- [ ] CRISPRi/dCas9 guide design for epigenetic dimming approach
- [ ] Prime editing feasibility assessment

### 6.3 AAV Capsid Evaluation
- [ ] Capsid tropism scoring for motor neurons
- [ ] Immunogenicity assessment
- [ ] Delivery efficiency modeling

## Phase 7: Advanced Analytics (PLANNED)

### 7.1 Spatial Multi-Omics Analysis
- [ ] Integrate Slide-seq / MERFISH data when available
- [ ] Niche-specific expression mapping
- [ ] Drug penetration zone analysis
- [ ] Identify "silent zones" resistant to current therapies

### 7.2 Cross-Species Regeneration Signatures
- [ ] RNA splicing pattern comparison: axolotl (regeneration) vs human SMA (degeneration)
- [ ] Identify conserved regeneration programs absent in SMA
- [ ] Salamander → human translation scoring

### 7.3 NMJ Retrograde Signaling Module
- [ ] Map muscle-to-nerve retrograde signals
- [ ] Model "happy muscle → surviving neuron" hypothesis
- [ ] EV/exosome cargo analysis for NMJ delivery
- [ ] Organ-on-Chip validation pathway

### 7.4 Multisystem SMA Module
- [ ] Liver function biomarkers in SMA
- [ ] Metabolic pathway analysis (fatty acid, lipid)
- [ ] Systemic energy budget modeling
- [ ] Combination therapy scoring (neuro + hepatic)

### 7.5 Bioelectric Reprogramming Module
- [ ] Ion channel expression profiling in SMA motor neurons
- [ ] Vmem state classification
- [ ] Electroceutical target identification
- [ ] Bioelectric patch feasibility scoring

## Phase 8: Knowledge Infrastructure (PLANNED)

### 8.1 RAG Knowledge Base (IN PROGRESS)
- [x] FAISS vector index over 22,607 claims + 4,582 source abstracts
- [x] sentence-transformers `all-mpnet-base-v2` (768-dim PRO model)
- [x] Hybrid search API: semantic (vector) + keyword (ILIKE) combined
- [x] Search API: `GET /api/v2/search?q=...&mode=hybrid`
- [x] Auto-reindex in daily pipeline
- [ ] Conversational research assistant
- [ ] Context-aware hypothesis refinement

### 8.2 HuggingFace Dataset Publishing (COMPLETE)
- [x] Curated SMA evidence dataset (claims + scores) — 9 tables as Parquet
- [x] Cross-species ortholog mapping dataset
- [x] Drug-target interaction dataset
- [x] Drug outcomes (failure/success) dataset
- [x] Results only — no raw PubMed content
- [x] Repo: `Bryzant-Labs/sma-evidence-graph`

### 8.3 Full-Text Paper Access (COMPLETE)
- [x] PubMed Central OA subset integration (Europe PMC REST API)
- [x] NCBI PMC fallback via ID converter + E-utilities
- [x] Unpaywall OA DOI resolver
- [x] Full-text stored in `sources.full_text` column
- [x] Daily pipeline stage for incremental fetching
- [x] Full-text claim extraction — extractor uses full_text when available, falls back to abstract

## Phase 9: SMA Open Data Commons (PLANNED)

### 9.1 SMA Failure & Success Database (COMPLETE)
- [x] LLM-based outcome extraction from literature (6 outcome types, 8 failure reasons)
- [x] Structured output: Molecule → Target → Mechanism → Outcome → Failure Reason → Key Finding
- [x] `drug_outcomes` table with UPSERT and source paper linking
- [x] API: `GET /drug-outcomes`, `GET /drug-outcomes/summary`, `POST /extract/drug-outcomes`
- [x] Frontend: Drug Outcome Database tab with filters and summary stats
- [x] Included in HuggingFace dataset export
- [x] Daily pipeline integration (Stage 6)
- [ ] Train models to predict "known dead ends" and avoid them

### 9.2 SMN2 Splice Variant Benchmark (IN PROGRESS)
- [x] Generate all ~762 SNVs across exon 7 + flanking introns (254bp region)
- [x] Knowledge-based splice impact scoring (4 dimensions: splice site proximity, motif disruption, conservation, therapeutic relevance)
- [x] Known motif annotation: ISS-N1 (nusinersen target), ESE, ESS, Tra2-beta, branch point
- [x] Splice benchmark API: `GET /splice/benchmark`, position/region queries
- [ ] Run through SpliceAI for delta splice scores (requires GPU)
- [ ] Publish as HuggingFace dataset + GitHub CSV

### 9.3 Cross-Species Splicing Map (Axolotl vs Human)
- [ ] Map regeneration-active genes in axolotl to human orthologs (extends Phase 4)
- [ ] Compare splicing patterns: regeneration (axolotl) vs degeneration (human SMA)
- [ ] Conservation scores for regeneration-specific splice variants
- [ ] Identify "silenced regeneration programs" in human motor neurons
- [ ] Publish as comparative genomics dataset

### 9.4 RDKit Drug-Likeness Filter for SMA
- [ ] Filter PubChem/ChEMBL compounds by SMA-specific criteria
- [ ] BBB penetration prediction (for CNS-targeted compounds)
- [ ] RNA-binding prediction (for SMN2 splicing modulators)
- [ ] Lipinski + Veber + CNS MPO filters
- [ ] Curated "Top 1000 SMA Drug Candidates" list
- [ ] Molecular descriptors + ADMET predictions for each candidate

## Phase 10: Warp-Speed Infrastructure (VISIONARY)

> "Weg von isolierten Einzellösungen, hin zu einem autonomen, KI-getriebenen Forschungs-Ökosystem."

### 10.1 "GitHub for Life" — Gene Edit Versioning
- [ ] Build platform treating DNA sequences and splice modifications like code
- [ ] SMN2 splice variants get "commit hashes" — version-controlled gene edits
- [ ] CRISPR/Prime Editing simulation tool: predict edit outcomes before lab testing
- [ ] Host "Biological Embeddings" on HuggingFace (ProtT5, ESM-2)
- [ ] Fine-tune protein language models on SMA-specific sequences
- [ ] DNA change → protein folding impact prediction (10-step cascade modeling)
- [ ] Open repo: `OpenSMA-Engine` with cleaned datasets

### 10.2 Agentic Research Swarm — Blackboard Architecture (IN PROGRESS)
- [x] Agent A: bioRxiv/medRxiv pre-print scanner (keyword relevance scoring, 2 servers)
- [x] Blackboard Architecture: agents share discoveries via structured message bus (PostgreSQL, JSONB metadata, TEXT[] arrays)
- [x] Blackboard API: GET/POST /blackboard, stats, read tracking, expiry cleanup
- [ ] Agent B: ChEMBL/PubChem molecule screener (auto-match new findings to compounds)
- [ ] Agent C: Molecular dynamics simulation code generator (Python/OpenMM)
- [ ] Agent D: Hypothesis auto-generator from new evidence convergence
- [ ] Agent E: Grant/paper writing assistant (auto-generate evidence summaries)
- [ ] Speed target: compress years of research into weeks

### 10.3 Digital Twin of the Motor Neuron
- [ ] ML model simulating entire SMA motor neuron metabolism
- [ ] Integrate Spatial Transcriptomics + Proteomics into real-time simulation
- [ ] In silico drug combination screening: 1M combinations/night
- [ ] Top-3 candidates → lab validation pipeline
- [ ] Multi-scale: molecular (protein interactions) → cellular (signaling) → tissue (NMJ)
- [ ] Training data: GEO datasets + Human Cell Atlas motor neuron profiles

### 10.4 Open-Source Lab-OS
- [ ] Connect AI pipeline to cloud lab synthesis (Emerald Cloud Lab, Strateos)
- [ ] Automated loop: Hypothesis → Experiment Design → Robotic Synthesis → Data → New Hypothesis
- [ ] Eliminate human delay from discovery-to-experiment cycle
- [ ] API integration with Opentrons/Hamilton liquid handlers
- [ ] Experiment result auto-ingestion into evidence graph

### 10.5 Zero-Knowledge Data Sharing
- [ ] Federated Learning framework: train on pharma private data without data leaving the building
- [ ] Differential privacy guarantees for patient data
- [ ] Cross-institutional model aggregation (FedAvg/FedProx)
- [ ] Patent-preserving knowledge extraction
- [ ] Integration with OHDSI/OMOP common data model for clinical data

## Phase 11: Translation & Impact (FUTURE)

- [ ] Expert validation pipeline (crowdsource hypothesis review)
- [ ] Collaboration portal for SMA researchers
- [ ] Integration with patient registries (with ethics approval)
- [ ] Drug repurposing candidates report
- [ ] Grant application support (auto-generated evidence summaries)
- [ ] Regulatory pathway mapping (FDA/EMA)

---

## Key Research Hypotheses to Validate

These emerged from Querdenker and Harvard-level thinking:

1. **Retrograde Muscle→Nerve Signaling**: "Heal the muscle to save the neuron" — muscle-derived trophic factors may be more important than direct neuronal intervention
2. **NDRG1 / Hibernation Mode**: Temporarily putting motor neurons into quiescence (like bear muscles) could protect them during the therapeutic window
3. **Bioelectric Reprogramming**: Ion channel modulation could activate endogenous regeneration programs, bypassing the need for gene therapy
4. **Spatial Drug Resistance**: Current SMA therapies may fail in specific tissue niches — spatial transcriptomics could reveal why
5. **SMA as Multisystem**: Hepatic metabolism optimization may amplify neuronal therapy efficacy
6. **Epigenetic Dimming via dCas9**: CRISPRi approach could silence disease-causing genes without DNA cuts (applicable from FSHD/DUX4 experience)
7. **Dual-Target Molecules**: Compounds that modify SMN2 splicing AND influence ion channels simultaneously

---

## Current Platform Stats (2026-03-15)

| Metric | Count |
|--------|-------|
| PubMed Sources | 4,582 |
| LLM-Extracted Claims | 22,607 (complete) |
| Prioritized Hypotheses | 189 (A/B/C tiers) |
| Knowledge Graph Edges | 397 |
| Drug Outcomes | 226 |
| Drug Repurposing Candidates | 57 |
| Clinical Trials | 449 |
| Molecular Targets | 21 (10 established + 11 discovery) |
| Drugs Tracked | 16 (3 approved + 13 pipeline) |
| PubMed Search Queries | 250+ across 14 categories |
| Data Sources | PubMed, ClinicalTrials.gov, GEO, ChEMBL, UniProt, STRING-DB, KEGG |
| Model Organisms | 5 (axolotl, zebrafish, naked mole rat, C. elegans, Drosophila) |
| Cutting-Edge Research Directions | 16 |
| Warp-Speed Phases | 5 (Gene Versioning, Agentic Swarm, Digital Twin, Lab-OS, Zero-Knowledge) |
