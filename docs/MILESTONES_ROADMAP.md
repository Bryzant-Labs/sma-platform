# SMA Research Platform — Milestones Roadmap

> Living document tracking research directions and implementation milestones.
> Last updated: 2026-03-20

---

## 2030 Strategic Tracks (Scientific Advisory)

> Restructured based on scientific advisory feedback. Priority: calibration > features, depth > breadth.

### Track 1: Trustworthy Evidence Engine (HIGHEST PRIORITY)
Before building more features, calibrate what we have.

| Deliverable | Status | Why It Matters |
|------------|--------|----------------|
| Gold-standard claim extraction evaluation set | PLANNED | Inter-annotator agreement benchmark |
| Claim confidence calibration curves | PARTIAL | confidence_calibrator.py built, grade B |
| Contradiction detection benchmark | DONE | find_contradictions() live |
| Source quality weighting | DONE | Not all PubMed papers are equal |
| Retrospective validation against known outcomes | DONE | Calibration report with approved drugs |
| Extraction precision/recall benchmark | PLANNED | How many claims are wrong? |
| Score reproducibility testing | DONE | Same input → same scores? |
| Evidence uncertainty intervals | DONE | Every prediction needs error bars |

### Track 2: SMA Mechanism Engine (CORE SCIENCE)
Go deeper on SMA-specific biology, not broader.

| Deliverable | Status | Why It Matters |
|------------|--------|----------------|
| SMN locus resolution (long-read haplotypes) | PLANNED | Copy number alone doesn't explain phenotype |
| SMN2 splicing regulatory grammar model | PLANNED | Fine-tune Evo/ESM-2 on SMA splice data (~$100 GPU) |
| Modifier-aware phenotype prediction | DONE | modifier_predictor.py — SMN2 copies + PLS3/NCALD/NAIP |
| Off-target splice impact prediction | PLANNED | ASO safety beyond primary target |
| Cross-disease transfer (mechanistically grounded only) | DONE | ALS/DMD overlap where biologically justified |
| Spatial/single-cell integration | PLANNED | When Slide-seq/MERFISH data available |
| RNA structure-informed ligand ranking | PLANNED | Via OpenFold3/RNAPro NIMs |
| **RNAPro SMN2 pre-mRNA 3D structure** | IN PROGRESS | GTC 2026 — RNA structure at ISS-N1 nusinersen binding site |
| **Proteina-Complexa protein binders** | PLANNED | GTC 2026 — new therapeutic modality: designed protein binders for SMA targets |
| **ESM-2 fine-tuning via BioNeMo Recipes** | PLANNED | GTC 2026 — SMA-specific protein embeddings |
| **ASO Sequence Generator** | BUILDING | Design novel ASOs targeting SMN2 ISS-N1/ISS-N2/ESS regions |
| **Nanopore RNA-seq Data Catalog** | BUILDING | Search SRA/ENA for public SMA direct RNA datasets |
| **Generative RNA Therapeutics** | PLANNED | Diffusion models for ASO design with BBB penetration |
| **Bio-LLM for Splicing Grammar** | PLANNED | Fine-tune on 762 SMA splice variants + SpliceAI data |

### Track 3: Functional Translation Engine (BRIDGE TO WET LAB)
Prioritize experiments, not just ideas.

| Deliverable | Status | Why It Matters |
|------------|--------|----------------|
| Organoid/NMJ validation scorecard | DONE | Which predictions are testable in organoids? |
| Expected Value of Experiment score | DONE | Cost/time/likelihood ranking per hypothesis |
| Assay-ready output format | DONE | 3 hypotheses with assay + model + readouts + go/no-go |
| Biomarker atlas (molecular/imaging/fluid) | DONE | Treatment response stratification |
| Compound/ASO/CRISPR comparison engine | DONE | Dual-target + CRISPR + AAV modules exist |
| Therapy combination ranking | DONE | Digital twin has basic combo scoring |
| **Generative Virtual Screening Blueprint** | IN PROGRESS | GTC 2026 — NVIDIA open-source pipeline: GenMol → Filter → DiffDock → Rank |
| **nvMolKit GPU cheminformatics** | PLANNED | GTC 2026 — faster Lipinski/BBB/PAINS filtering |
| **AlphaFold DB protein complexes** | IN PROGRESS | GTC 2026 — 1.7M new complexes for SMA structural biology |
| **Agentic Drug Discovery** | PLANNED | GTC 2026 — autonomous BioNeMo NIM orchestration |
| IP/freedom-to-operate signal | DONE | Patent landscape integration |

### Track 4: Researcher Distribution (ACCESS + TRUST)
Make the platform usable AND credible.

| Deliverable | Status | Why It Matters |
|------------|--------|----------------|
| MCP Server (29 tools) | DONE | Natural language query access |
| Reproducible benchmarks | PLANNED | Others can verify our claims |
| Scientific Advisory Pack (5 pages) | DONE | What it does, where reliable, where uncertain |
| Grant-ready hypothesis exports | DONE | Translation module has grant templates |
| Citation-grade evidence summaries | PARTIAL | Literature review module built |
| External lab collaboration hooks | PLANNED | API for result sharing |
| DREAM/CACHE challenge participation | PLANNED | Industry-standard validation |

### Key Researchers to Engage
| Name | Institution | Expertise | Why |
|------|------------|-----------|-----|
| Adrian Krainer | CSHL | RNA splicing, ASO therapeutics | Nusinersen co-inventor, splicing authority |
| Mina Gouti | MDC Berlin | Organoid/NMJ models | Advanced human NMJ models for drug testing |
| Ewout Groen | UMC Utrecht | Translational SMA, biomarkers | Clinical translation + patient stratification |
| Brunhilde Wirth | U Cologne | SMA genetics, modifiers | PLS3/NCALD discovery, genetic plausibility |

### What to Deprioritize
These are interesting but not essential for scientific credibility:
- Agentic swarm "autonomy" narrative → keep simple, calibrated agents
- Gene edit versioning as showcase → useful internal tool, not a selling point
- Excessive frontend tabs → focus on data quality, not visualization breadth
- Generic Digital Twin without mechanistic backbone → only if validated
- "Pharmaceutical Superintelligence" framing → evidence-first, not hype

---

## Phase 1: Evidence Foundation (COMPLETE)

- [x] PubMed ingestion pipeline (Biopython Entrez)
- [x] ClinicalTrials.gov v2 adapter (449 trials)
- [x] GEO dataset metadata adapter
- [x] LLM claim extraction (Claude Haiku) from abstracts
- [x] Evidence scoring (method weights, tier multipliers)
- [x] Knowledge graph: nodes, edges, evidence linking
- [x] Hypothesis generation from evidence convergence (515 hypotheses, Sonnet 4.6)
- [x] Target identification: 10 established + 11 discovery targets
- [x] 25,054 LLM-extracted claims (growing daily)

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
- [x] SMA MCP Server (29 tools for AI agent integration, including synthesis + NIMs)

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

### 6.1 Small Molecule Design (IN PROGRESS)
- [x] RDKit molecular descriptor calculation (Lipinski, BBB, CNS MPO, QED, PAINS)
- [x] Drug screening dashboard (188 compounds screened, 100 drug-like, 18 BBB-permeable)
- [x] SMILES-based single compound screening API
- [x] ADMET prediction pipeline (absorption, distribution, metabolism, excretion, toxicity)
- [x] Drug repurposing candidate identification (57 candidates from cross-disease + ChEMBL)
- [x] Knowledge graph auto-expansion (claim-based + drug-outcome + conservation edges)
- [x] 13-stage daily pipeline (PubMed → Trials → Claims → Hypotheses → Full-text → Drug Outcomes → Relinking → Graph Expansion → Scoring → FAISS Reindex → Blackboard Cleanup → Hypothesis Convergence → Molecule Screening)
- [x] Molecular docking score prediction (pharmacophore-based, 7 binding pockets — ISS-N1, splice site, HDAC, mTOR, NCALD, PLS3, UBA1)
- [x] Virtual screening against SMN2 splicing targets (`GET /dock/score?pocket=SMN2_SPLICE_SITE`)
- [ ] Full AutoDock Vina docking (requires vina + meeko installation on GPU server)
- [x] In silico screening for dual-target molecules (SMN2 splicing + ion channels — 8 candidates, risdiplam+4-AP top combo)
- [x] Dual-target API (GET /screen/dual-target, /channels, /synergy)
- [x] Frontend Dual Target tab with ranked candidates

### 6.2 CRISPR / Prime Editing (IN PROGRESS)
- [x] Guide RNA design for SMA targets (20nt + NGG PAM scanning, both strands)
- [x] CRISPRi/dCas9 guide design for epigenetic dimming approach (3 strategies: ISS-N1, ESS, ESE)
- [x] Motif overlap detection (ISS-N1, ESE Tra2-beta, ESS hnRNP A1, Element2, C6T, branch point)
- [x] On-target scoring (Doench 2016-inspired) and specificity scoring (sequence complexity)
- [x] CRISPR API endpoints (`GET/POST /crispr/guides`, `GET /crispr/motifs`)
- [x] Frontend CRISPR tab with strategies, motifs, and guide table
- [x] Off-target prediction (Cas-OFFinder on A100: 2,631 off-targets for 19 guides, 75 exact matches)
- [x] Prime editing feasibility assessment (PE2/PE3/PEmax for C6T correction, ISS-N1 disruption, ESE strengthening)
- [x] Comparison with approved therapies (nusinersen, risdiplam, Zolgensma, CRISPRi)
- [x] Frontend Prime Editing tab with design cards and therapy comparison table

### 6.3 AAV Capsid Evaluation (COMPLETE)
- [x] Capsid tropism scoring for motor neurons (9 serotypes evaluated)
- [x] Immunogenicity assessment (NAb seroprevalence data)
- [x] Delivery efficiency modeling (BBB crossing, manufacturing feasibility)
- [x] Packaging capacity vs cargo size analysis (7 cargo types)
- [x] Composite suitability scoring (weighted: 30% MN tropism, 20% BBB, 20% immunogenicity, 15% manufacturing, 15% packaging)
- [x] 5 SMA-specific delivery strategies (neonatal IV, intrathecal, AAV9-seropositive rescue, dual-vector CRISPRi, muscle+CNS dual targeting)
- [x] AAV API endpoints (`GET /aav/evaluate`, `/aav/capsid/{serotype}`, `/aav/cargos`)
- [x] Frontend AAV tab with strategy cards and capsid ranking table

## Phase 7: Advanced Analytics (COMPLETE)

### 7.1 Spatial Multi-Omics Analysis (COMPLETE)
- [x] 6 spinal cord zones modeled (ventral horn, dorsal horn, central canal, white matter, DRG, NMJ)
- [x] Target × zone expression matrix (10 targets × 6 zones)
- [x] Drug penetration zone analysis (BBB permeability, CSF exposure, vascular density)
- [x] 4 delivery route models (intrathecal, oral, IV, AAV)
- [x] Identify "silent zones" resistant to current therapies
- [x] Spatial API endpoints (GET /spatial/penetration, /expression, /silent-zones)
- [x] Frontend Spatial tab with zone table, drug penetration, silent zones
- [ ] Integrate Slide-seq / MERFISH data when available

### 7.2 Cross-Species Regeneration Signatures (COMPLETE)
- [x] 12 regeneration genes mapped (axolotl + zebrafish → human orthologs)
- [x] 7 pathway comparisons: regeneration state vs SMA state with gap scores
- [x] Silenced regeneration programs identification (reactivation potential scoring)
- [x] Regeneration API endpoints (GET /regen/genes, /pathways, /silenced)
- [x] Frontend Regeneration tab with gene table and pathway comparisons

### 7.3 NMJ Retrograde Signaling Module (COMPLETE)
- [x] 10 retrograde signaling molecules mapped (BDNF, GDNF, agrin, EVs, etc.)
- [x] "Happy muscle → surviving neuron" hypothesis analysis
- [x] 7 EV therapeutic cargo components for NMJ delivery
- [x] 3 organ-on-chip models (NMJ-on-Chip, Motor Unit-on-Chip, high-throughput optogenetic)
- [x] NMJ API endpoints (GET /nmj/signals, /ev-cargo, /chip-models, /happy-muscle)
- [x] Frontend NMJ Signals tab with signals, EV cargo, and chip model cards

### 7.4 Multisystem SMA Module (COMPLETE)
- [x] 7 organ systems (liver, cardiac, metabolic, pancreatic, vascular, skeletal, GI)
- [x] SMN-dependent vs independent pathology classification
- [x] 4 combination therapy strategies (risdiplam+metformin, dual SMN, SMN+apitegromab, Zolgensma+metabolic)
- [x] Energy budget modeling (normal vs SMA vs treated MN supply/demand ratios)
- [x] 5 actionable mitochondrial support compounds
- [x] Multisystem API endpoints (GET /multisystem/organs, /combinations, /energy, /full)
- [x] Frontend Multisystem tab with organ table, combo cards, energy budget

### 7.5 Bioelectric Reprogramming Module (COMPLETE)
- [x] 9 ion channels profiled (Na, K, Ca, HCN, Cl — expression + SMA impact)
- [x] 4 Vmem state classifications (healthy, hyperpolarized/silenced, depolarized/stressed, committed)
- [x] 55% rescuable MN fraction identified (40% silenced = prime bioelectric target)
- [x] 5 electroceutical interventions (epidural SCS, transcutaneous, bioelectric patch, FES, optogenetic)
- [x] Bioelectric API endpoints (GET /bioelectric/channels, /vmem, /electroceuticals, /profile)
- [x] Frontend Bioelectric tab with channel table, Vmem state cards, electroceutical table

## Phase 8: Knowledge Infrastructure (PLANNED)

### 8.1 RAG Knowledge Base (COMPLETE)
- [x] FAISS vector index over 22,607 claims + 4,582 source abstracts
- [x] sentence-transformers `all-mpnet-base-v2` (768-dim PRO model)
- [x] Hybrid search API: semantic (vector) + keyword (ILIKE) combined
- [x] Search API: `GET /api/v2/search?q=...&mode=hybrid`
- [x] Auto-reindex in daily pipeline (Stage 10)
- [x] Conversational research assistant (`GET /api/v2/ask?q=...` — Claude Sonnet RAG)
- [x] Context-aware hypothesis refinement (via convergence hypothesis agent)

### 8.2 HuggingFace Dataset Publishing (COMPLETE)
- [x] Curated SMA evidence dataset (claims + scores) — 9 tables as Parquet
- [x] Cross-species ortholog mapping dataset
- [x] Drug-target interaction dataset
- [x] Drug outcomes (failure/success) dataset
- [x] Results only — no raw PubMed content
- [x] Repo: `SMAResearch/sma-evidence-graph`

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
- [x] Convergence hypothesis agent auto-generates new hypotheses from evidence (daily pipeline Stage 12)
- [ ] Train models to predict "known dead ends" and avoid them

### 9.2 SMN2 Splice Variant Benchmark (IN PROGRESS)
- [x] Generate all ~762 SNVs across exon 7 + flanking introns (254bp region)
- [x] Knowledge-based splice impact scoring (4 dimensions: splice site proximity, motif disruption, conservation, therapeutic relevance)
- [x] Known motif annotation: ISS-N1 (nusinersen target), ESE, ESS, Tra2-beta, branch point
- [x] Splice benchmark API: `GET /splice/benchmark`, position/region queries
- [x] Run through SpliceAI for delta splice scores (252 variants scored on A100, 21 high-impact)
- [x] Publish as HuggingFace dataset (splice_variants added to HF export script)

### 9.3 Cross-Species Splicing Map (COMPLETE)
- [x] 10 regeneration-active splice events mapped from axolotl/zebrafish to human orthologs
- [x] 5 event types: exon skipping, alternative promoter, intron retention, alt 5'ss, alt 3'ss
- [x] Conservation scores (avg 0.73) for regeneration-specific splice variants
- [x] 6 silenced regeneration programs identified in human motor neurons
- [x] Actionable ASO candidates (MARCKS exon 4, NRG1 exon 5 — nusinersen-like approach)
- [x] Splicing map API endpoints (GET /splice/cross-species, /actionable, /compare)
- [x] Frontend Splice Map tab with event table and insights
- [ ] Publish as comparative genomics dataset

### 9.4 RDKit Drug-Likeness Filter for SMA
- [x] Filter PubChem/ChEMBL compounds by SMA-specific criteria (via molecule_screener)
- [x] BBB penetration prediction (for CNS-targeted compounds) — via ADMET predictor
- [x] RNA-binding prediction for SMN2 splicing modulators (6 RNA target sites, 5 known modulator benchmarks)
- [x] RNA binding API (GET /rna/targets, /modulators, POST /rna/predict, /benchmark)
- [x] Frontend RNA Binding tab with target sites and known modulators
- [x] Lipinski + Veber + CNS MPO filters — via drug_screener + ADMET
- [x] Curated "Top 1000 SMA Drug Candidates" list — `GET /screen/top1000` endpoint
- [x] Molecular descriptors + ADMET predictions for each candidate — integrated in candidate_ranker

## Phase 10: Warp-Speed Infrastructure (VISIONARY)

> "Weg von isolierten Einzellösungen, hin zu einem autonomen, KI-getriebenen Forschungs-Ökosystem."

### 10.1 "GitHub for Life" — Gene Edit Versioning (IN PROGRESS)
- [x] Build platform treating DNA sequences and splice modifications like code
- [x] SMN2 splice variants get "commit hashes" — version-controlled gene edits (SHA-256)
- [x] CRISPR/Base Editing simulation tool: SNV, base edit (ABE/CBE), CRISPR KO simulation
- [x] Version tree: SMN1 (healthy) → SMN2 (disease) → therapeutic edits (base edit, ESE, ESS)
- [x] Sequence diffs with change detection (substitutions, insertions, deletions)
- [x] Gene versioning API endpoints (`GET /gene-versions/smn2`, `POST /gene-versions/edit`)
- [x] Frontend Gene Versions tab with lineage hashes, version tree, and diffs
- [ ] Host "Biological Embeddings" on HuggingFace (ProtT5, ESM-2)
- [ ] Fine-tune protein language models on SMA-specific sequences
- [ ] DNA change → protein folding impact prediction (10-step cascade modeling)
- [ ] Open repo: `OpenSMA-Engine` with cleaned datasets

### 10.2 Agentic Research Swarm — Blackboard Architecture (IN PROGRESS)
- [x] Agent A: bioRxiv/medRxiv pre-print scanner (keyword relevance scoring, 2 servers)
- [x] Blackboard Architecture: agents share discoveries via structured message bus (PostgreSQL, JSONB metadata, TEXT[] arrays)
- [x] Blackboard API: GET/POST /blackboard, stats, read tracking, expiry cleanup
- [x] Agent D: Hypothesis auto-generator from new evidence convergence (Claude Haiku, convergence detection, daily pipeline Stage 12)
- [x] Research Assistant: Conversational RAG (`GET /api/v2/ask` — Claude Sonnet over evidence base)
- [x] Agent B: ChEMBL/PubChem molecule screener (`GET/POST /screen/molecules` — auto-screen targets, drug-likeness filter, blackboard posting, daily pipeline Stage 13)
- [x] Agent E: Evidence summary writer (`GET /write/summary`, `/write/compare` — NIH grant sections, paper intros, briefings, hypothesis rationales via Claude Sonnet)
- [x] Agent C: Molecular dynamics simulation code generator (Python/OpenMM — 6 SMA simulations, 52 GPU hours total)
- [x] MD simulation API (`GET /md/simulations`, `GET /md/generate/{sim_key}`) — generates complete setup/production/analysis scripts
- [ ] Speed target: compress years of research into weeks

### 10.3 Digital Twin of the Motor Neuron (IN PROGRESS)
- [x] 5-compartment motor neuron model (soma, axon, NMJ terminal, dendrites, nucleus)
- [x] 8 signaling pathways modeled (PI3K/Akt, MAPK/ERK, Ca/CaMKII, UPS, mitochondria, spliceosome, NMJ, autophagy)
- [x] 6 drugs with quantified pathway and compartment effects (nusinersen, risdiplam, 4-AP, apitegromab, NMN, GV-58)
- [x] Drug combination simulator with synergy detection
- [x] Exhaustive pair + triple optimization (top combinations ranked)
- [x] Digital twin API (GET /twin/compartments, /pathways, /drugs, /optimize, POST /twin/simulate)
- [x] Frontend Digital Twin tab with compartment cards, pathway table, optimal combinations
- [ ] ML model simulating entire SMA motor neuron metabolism
- [ ] Integrate Spatial Transcriptomics + Proteomics into real-time simulation
- [ ] In silico drug combination screening: 1M combinations/night
- [ ] Top-3 candidates → lab validation pipeline

### 10.4 Open-Source Lab-OS (COMPLETE)
- [x] 8 standardized SMA assays (RT-qPCR, Western blot, splicing reporter, iPSC-MN survival, NMJ formation, electrophysiology, mouse survival, behavioral)
- [x] 3 cloud lab integration specs (Emerald Cloud Lab, Strateos, Opentrons)
- [x] Experiment design generator from hypothesis text (budget-aware: low/medium/high)
- [x] Lab-OS API endpoints (GET /lab/assays, /cloud-labs, /design)
- [x] Frontend Lab-OS tab with assay library and cloud lab cards
- [ ] Robotic synthesis loop: Experiment → Data → New Hypothesis
- [ ] Experiment result auto-ingestion into evidence graph

### 10.5 Zero-Knowledge Data Sharing (COMPLETE)
- [x] 4 federated learning protocols for SMA (FedAvg, FedProx, SCAFFOLD — phenotype, drug response, biomarker, natural history)
- [x] 14 OMOP/OHDSI concept mappings (SNOMED, LOINC, RxNorm for SMA)
- [x] Privacy budget calculator (basic, advanced, RDP composition theorems)
- [x] 4-tier data sharing framework (aggregate → federated → synthetic → trusted environment)
- [x] Federated API endpoints (GET /federated/protocols, /omop, /privacy-budget, /data-tiers)
- [x] Frontend Federated tab with protocols, data tiers, OMOP mappings
- [ ] Actual FedAvg/FedProx implementation (requires multi-site deployment)
- [ ] Integration with real OHDSI network

## Phase 11: Translation & Impact (COMPLETE)

- [x] 6 regulatory pathways (Orphan Drug, Breakthrough Therapy, PRIME, Accelerated Approval, PRV, RMAT)
- [x] 4 grant application templates (NIH R01, NIH R21, Cure SMA, ERC Starting Grant)
- [x] 5-level hypothesis validation pipeline (computational → biochemical → cell-based → animal → clinical/IND)
- [x] Hypothesis gate checker (evidence score + digital twin improvement thresholds)
- [x] Translation API endpoints (GET /translate/regulatory, /grants, /validation, /validate)
- [x] Frontend Translation tab with regulatory table, grant cards, validation pipeline
- [ ] Expert validation crowdsourcing
- [ ] Integration with patient registries (ethics approval required)

---

## Phase 12: NVIDIA GTC 2026 Integration (IN PROGRESS)

> Integrating 7 new tools and models announced at NVIDIA GTC 2026 (March 17-21).
> Design doc: `docs/plans/2026-03-20-nvidia-gtc-integration.md`

### 12.1 RNAPro NIM — RNA 3D Structure Prediction (PRIORITY)
- [ ] Add RNAPro API function to nvidia_nims adapter
- [ ] Add POST /nims/rna-structure endpoint
- [ ] Predict SMN2 ISS-N1 pre-mRNA 3D structure (nusinersen binding site)
- [ ] Predict full SMN2 intron 7 structure
- [ ] Store results + add to GPU Results section
- [ ] Compare with existing ASO binding predictions

### 12.2 AlphaFold DB Complex Expansion
- [ ] Query AlphaFold DB for SMA protein complexes (1.7M new structures added)
- [ ] Check: SMN+Gemin2/3/4/5, SMN+p53, PLS3+actin, NCALD+calcium channel
- [ ] Store complex structures in targets.metadata.alphafold_complexes
- [ ] Display on Targets deep-dive pages

### 12.3 Generative Virtual Screening Blueprint (PRIORITY)
- [ ] Study NVIDIA Blueprint architecture (github.com/NVIDIA-BioNeMo-blueprints/generative-virtual-screening)
- [ ] Create virtual_screening.py orchestrator (GenMol → Filter → DiffDock → Rank)
- [ ] Add POST /screening/virtual endpoint
- [ ] Run first campaign: 100 molecules from 4-AP scaffold vs 7 SMA targets
- [ ] Scale to 1000+ molecules
- [ ] Compare with our existing 378 DiffDock v2.2 results

### 12.4 Proteina-Complexa — Protein Binder Design (NEW MODALITY)
- [ ] Assess availability (NIM API vs self-hosted on Vast.ai)
- [ ] Create protein_binder_design.py module
- [ ] Add POST /binder/design endpoint
- [ ] Design first binders: SMN2 protein, SMN-p53 interface
- [ ] Add "Protein Binder Design" as new Research Direction
- [ ] Validate top designs with structural analysis

### 12.5 BioNeMo Recipes — ESM-2 Fine-Tuning
- [ ] Install BioNeMo Recipes
- [ ] Prepare SMA protein dataset (21 targets → UniProt sequences)
- [ ] Write BioNeMo Recipe config for ESM-2 fine-tuning
- [ ] Create Vast.ai launch script
- [ ] Run fine-tuning on SMA-specific protein embeddings

### 12.6 nvMolKit — GPU-Accelerated Cheminformatics
- [ ] Check nvMolKit availability (pip or BioNeMo container only)
- [ ] Integrate as optional backend in screening_funnel.py
- [ ] Benchmark: RDKit vs nvMolKit on 1000 molecules
- [ ] Use for Lipinski/BBB/PAINS filtering in virtual screening

### 12.7 Agentic Drug Discovery
- [ ] Design autonomous pipeline: generate → filter → dock → rank → store
- [ ] Create DrugDiscoveryAgent class
- [ ] Orchestrate BioNeMo NIMs (GenMol + DiffDock + RNAPro + OpenFold3)
- [ ] Add POST /agent/drug-discovery endpoint
- [ ] Auto-create news posts for significant findings
- [ ] Connect to MCP server for external AI agent access

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

## Current Platform Stats (2026-03-20)

| Metric | Count |
|--------|-------|
| Sources (PubMed + Patents + Trial Results) | 6,042 (+987 p53/apoptosis/glial papers) |
| LLM-Extracted Claims | 30,145 (growing — claim extraction running) |
| Prioritized Hypotheses | 1,252 (A/B/C tiers, Sonnet 4.6) |
| Knowledge Graph Edges | 428 (34 relation types) |
| Cross-Paper Synthesis Cards | 6 (Claude-generated) |
| Co-occurrence Pairs | 30 target pairs |
| Transitive Bridges | 53 cross-paper connections |
| Drug Outcomes | 226 |
| Molecule Screenings (ChEMBL/PubChem) | 21,228 compounds |
| DiffDock Dockings | 518 (140 v1 + 378 v2.2 NIM) |
| Boltz-2 Protein Structures | 5 (A100 GPU) |
| ESM-2 Protein Embeddings | 6 (1280-dim) |
| GenMol Novel Molecules | 20 (4-AP analogs) |
| Drug Repurposing Candidates | 57 |
| Clinical Trials | 449 |
| SMA Patents | 578 |
| Molecular Targets | 21 (10 established + 11 discovery) |
| Drugs Tracked | 16 (3 approved + 13 pipeline) |
| API Endpoints | ~190 |
| MCP Tools | 29 |
| PubMed Search Queries | 301 across 14 categories |
| Data Sources | PubMed, ClinicalTrials.gov, GEO, ChEMBL, UniProt, STRING-DB, KEGG, Google Patents, AlphaFold, bioRxiv |
| NVIDIA NIMs | DiffDock v2.2, OpenFold3, GenMol |
| Docker Image | csiicf/sma-gpu-toolkit (14.7GB) |
| Total GPU Cost | $0.78 |
| Total NIM Cost | $0 |

## Key Discoveries (2026-03-16)

1. **4-AP → CORO1C (+0.251)** — strongest predicted binding of ALL 378 compound-target pairs
2. **4-AP multi-target profile** — binds CORO1C, NCALD, SMN2, SMN1 (4 SMA targets)
3. **SMN1-NCALD calcium signaling bridge** — cross-paper synthesis discovery
4. **4-AP scaffold is optimal** — GenMol analogs don't improve CORO1C binding
5. **UBA1 is highly druggable** — 5 compounds in top 25 docking hits
6. **CHEMBL1381595 → NCALD (+0.076)** — novel calcium sensor binder
