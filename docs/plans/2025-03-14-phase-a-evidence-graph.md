# Phase A: Evidence Graph — Implementation Plan

> Biology-first target discovery for SMA. No marketing, no hype — evidence only.

**Goal**: Build a structured, queryable evidence graph connecting all known SMA biology (genes, proteins, pathways, drugs, trials, datasets) backed by traceable sources.

## Phase A Milestones

### A1: Core Infrastructure (Week 1)
- [x] PostgreSQL schema with 10 core tables
- [x] FastAPI skeleton with /api/v2 endpoints
- [x] asyncpg connection pool
- [x] UCM builder (nodes/edges/evidence → Parquet)
- [x] Seed data: 10 targets, 7 drugs, 7 datasets
- [x] Unit tests for UCM layer

### A2: Ingestion Pipeline (Week 2)
- [x] PubMed adapter (NCBI E-utilities via Biopython)
- [x] ClinicalTrials.gov v2 API adapter
- [x] GEO dataset metadata adapter
- [ ] Daily cron job for PubMed ingestion
- [ ] Deduplication and conflict resolution
- [ ] PRIDE proteomics adapter
- [ ] UniProt protein metadata adapter

### A3: Evidence Extraction (Week 3)
- [ ] LLM-powered claim extraction from paper abstracts
- [ ] Structured claim types (gene_expression, drug_efficacy, etc.)
- [ ] Confidence scoring based on evidence quality
- [ ] Evidence linking: claims ↔ sources
- [ ] Manual curation interface (admin only)

### A4: Knowledge Graph (Week 4)
- [ ] Build graph_edges from claims
- [ ] Target-target relationship inference
- [ ] Pathway membership propagation
- [ ] Graph visualization endpoint
- [ ] Export to UCM bundle format

## Data Inventory (Tier 1 — Use Now)

| Accession | Modality | Tissue | Why |
|-----------|----------|--------|-----|
| GSE69175 | RNA-seq | Human iPSC MNs | Direct human motor neuron data |
| GSE108094 | RNA-seq | Human MNs | Splicing analysis in SMA MNs |
| GSE208629 | scRNA-seq | Mouse spinal cord | Single-cell atlas, cell-type specificity |

## Key Targets

| Symbol | Type | Role | Confidence |
|--------|------|------|------------|
| SMN1 | gene | Primary SMA gene | 1.0 |
| SMN2 | gene | Copy number modifier | 0.9 |
| STMN2 | gene | Neuroprotective target | 0.8 |
| PLS3 | gene | Protective modifier | 0.7 |
| NCALD | gene | Protective modifier | 0.65 |

## Next: Phase B (Reasoning)
Once the evidence graph has sufficient data (~500+ sources, ~100+ claims):
- Target ranking by aggregate evidence score
- Hypothesis generation for novel targets
- Gap analysis: what evidence is missing
