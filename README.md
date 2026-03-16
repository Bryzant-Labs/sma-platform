# SMA Research Platform

**An evidence-first computational biology platform for Spinal Muscular Atrophy drug target discovery.**

[![Live](https://img.shields.io/badge/Live-sma--research.info-blue)](https://sma-research.info)
[![API](https://img.shields.io/badge/API-REST%20v2-green)](https://sma-research.info/api/v2/docs)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue)](LICENSE)

## What This Does

The platform systematically aggregates SMA research from public biomedical databases, extracts structured claims from the literature using NLP, builds a molecular knowledge graph, and prioritizes drug targets through multi-dimensional scoring.

Every assertion traces back to its source. No marketing — only evidence.

## Platform Statistics

| Metric | Count |
|--------|-------|
| PubMed sources ingested | 1,773 |
| LLM-extracted evidence claims | 7,400+ |
| Clinical trials (ClinicalTrials.gov) | 449 |
| Molecular targets scored | 21 |
| Prioritized hypotheses (A/B/C tiers) | 102 |
| Knowledge graph edges | 214 |
| Unique compounds (ChEMBL) | 188 |
| Curated research links | 53 |

## Scientific Methodology

**Full methodology documentation**: [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md)

The pipeline follows a six-stage process:

```
1. COLLECT    PubMed, ClinicalTrials.gov, STRING-DB, ChEMBL, UniProt, KEGG
              107+ curated queries across SMA biology, discovery targets,
              and cross-species comparative biology
                  ↓
2. EXTRACT    NLP-based claim extraction from 1,773 paper abstracts
              12 typed claim categories (gene_expression, drug_efficacy, etc.)
              Each claim → source paper traceability chain
                  ↓
3. LINK       Claims linked to 21 molecular targets via fuzzy symbol matching
              Evidence chains: source → evidence → claim → target
                  ↓
4. GRAPH      Knowledge graph from 6 data sources:
              STRING-DB protein interactions, UniProt GO processes,
              KEGG/Reactome pathways, ChEMBL compound bioactivities
                  ↓
5. SCORE      7-dimension composite scoring per target:
              Genetic evidence, biological coherence, clinical validation,
              druggability, network centrality, publication density,
              biomarker potential (weighted sum → 0.0-1.0)
                  ↓
6. HYPOTHESIZE  Multi-criteria hypothesis ranking into action tiers:
                Tier A (top 5) → ready for experimental validation
                Tier B (6-15) → needs more evidence
                Tier C (rest) → lower priority
```

## Data Sources

| Source | Type | What We Extract |
|--------|------|-----------------|
| [PubMed](https://pubmed.ncbi.nlm.nih.gov/) | Literature | Abstracts, metadata from 107+ queries |
| [ClinicalTrials.gov](https://clinicaltrials.gov/) | Clinical | Trial status, phase, interventions, enrollment |
| [STRING-DB](https://string-db.org/) | Protein interactions | PPI scores (experimental, co-expression, text-mining) |
| [ChEMBL](https://www.ebi.ac.uk/chembl/) | Bioactivity | Compound-target IC50/EC50/Ki, pChEMBL values |
| [UniProt](https://www.uniprot.org/) | Protein annotations | GO terms, Reactome/KEGG pathways, function |
| [KEGG](https://www.kegg.jp/) | Pathways | SMA pathway (hsa05033) gene membership |
| [NCBI Gene](https://www.ncbi.nlm.nih.gov/gene/) | Orthologs | Cross-species ortholog mapping |

All data is derived from public, freely accessible databases.

## Molecular Targets

### Established Targets

| Rank | Symbol | Score | Role |
|------|--------|-------|------|
| 1 | SMN2 | 0.891 | Primary therapeutic target, severity modifier |
| 2 | SMN1 | 0.735 | Primary disease gene, absent in patients |
| 3 | SMN Protein | 0.603 | Essential for snRNP biogenesis |
| 4 | UBA1 | 0.456 | Ubiquitin homeostasis, dysregulated in SMA |
| 5 | NCALD | 0.389 | Calcium sensor, knockdown rescues SMA |
| 6 | STMN2 | 0.382 | Neuroprotective, axonal growth |
| 7 | PLS3 | 0.377 | Natural severity modifier |

### Discovery Targets (from omics convergence analysis)

| Symbol | Score | Mechanism |
|--------|-------|-----------|
| LY96 | 0.434 | TLR4 coreceptor, neuroinflammation |
| DNMT3B | 0.405 | Epigenetic regulation, SMN2 exon 7 modifier |
| NEDD4L | 0.391 | Ubiquitin pathway, related to UBA1 |
| CAST | 0.372 | Calpain inhibitor, neuroprotection |
| SPATA18 | 0.325 | Mitochondrial quality control |
| ANK3 | 0.295 | Nodes of Ranvier integrity |

## Cross-Species Comparative Biology (Querdenker)

A novel module analyzing how regenerative organisms solve motor neuron problems that SMA patients cannot:

| Organism | Key Trait | Why It Matters |
|----------|-----------|----------------|
| Axolotl | Full spinal cord regeneration | Understanding regeneration pathways |
| Zebrafish | Motor neuron regeneration | SMN ortholog expression in regeneration |
| Naked Mole Rat | Neurodegeneration resistance | Neuroprotective mechanisms |
| C. elegans | Conserved smn-1 ortholog | Genetic models of motor neuron function |
| Drosophila | SMN loss-of-function models | Well-characterized SMA phenotypes |

## API

All data is freely accessible via REST API:

```
GET /api/v2/stats                    Platform statistics
GET /api/v2/targets                  Molecular targets (21 entries)
GET /api/v2/scores                   7-dimension composite scores
GET /api/v2/hypotheses/prioritized   Ranked hypotheses (A/B/C tiers)
GET /api/v2/trials                   Clinical trials (449 entries)
GET /api/v2/drugs                    Drugs/therapies (16 entries)
GET /api/v2/sources                  PubMed literature (1,773 papers)
GET /api/v2/claims                   Evidence claims (7,400+ entries)
GET /api/v2/datasets                 Curated omics datasets
GET /api/v2/comparative/species      Model organisms for cross-species analysis
```

Interactive documentation: https://sma-research.info/api/v2/docs

## Limitations & Transparency

We believe in honest science. Known limitations:

1. **Abstract-only analysis** — Full-text papers are not yet processed. Context from methods/results sections may be missed.
2. **LLM extraction errors** — Automated claim extraction has an estimated 5-15% error rate. All claims should be verified against the source paper.
3. **Publication bias** — PubMed queries favor published, English-language research.
4. **No experimental validation** — This is a computational platform. All hypotheses require independent experimental validation.
5. **Scoring weights are expert-assigned** — Not statistically optimized. The expanding corpus changes scores over time.

See [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) for full details on methods, validation, and reproducibility.

## Technology

- **Backend**: Python / FastAPI / SQLite
- **NLP**: Claude 3 Haiku (structured claim extraction)
- **Data**: httpx (REST APIs), Biopython (NCBI)
- **Frontend**: Vanilla JS (no framework dependencies)
- **Updates**: Daily automated ingestion (06:00 UTC)

## Contact

**Christian Fischer** — christian@bryzant.com
SMA Research Platform — https://sma-research.info

## License

AGPL-3.0 — Platform code is open source. Research data under CC-BY-SA 4.0.
