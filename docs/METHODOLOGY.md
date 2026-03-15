# Methodology

## Research Approach

The SMA Research Platform uses a systematic, computational biology pipeline to aggregate, structure, analyze, and prioritize evidence from public biomedical databases. The methodology follows established principles of evidence-based medicine and bioinformatics, adapted for automated knowledge synthesis.

This document describes the scientific methods behind the platform's outputs so that researchers can evaluate the rigor and limitations of the results.

---

## 1. Data Collection

### 1.1 Literature Ingestion

**Source**: NCBI PubMed via E-utilities API (Entrez)

**Method**: We maintain 107+ curated search queries spanning:
- Core SMA biology (SMN1, SMN2, spinal muscular atrophy)
- Established molecular targets (STMN2, PLS3, NCALD, UBA1, mTOR)
- Discovery targets identified through omics convergence (LY96, NEDD4L, SPATA18, LDHA, CAST, SULF1, ANK3, DNMT3B, CD44, CTNNA1, GALNT6)
- Cross-species comparative biology (axolotl, zebrafish, naked mole rat, C. elegans, Drosophila)

Queries are executed daily via cron (06:00 UTC). Each paper is stored with full metadata: PMID, title, authors, journal, publication date, DOI, and abstract. Deduplication is by PMID with ON CONFLICT UPSERT.

**Current corpus**: 1,773 PubMed sources with abstracts.

### 1.2 Clinical Trials

**Source**: ClinicalTrials.gov v2 REST API

**Method**: All trials matching "spinal muscular atrophy" are retrieved with structured fields: NCT ID, title, status, phase, conditions, interventions, sponsor, enrollment, dates.

**Current data**: 449 clinical trials.

### 1.3 Protein Interactions

**Source**: STRING-DB v12 API

**Method**: Protein-protein interactions are queried for all gene targets at medium confidence (combined score >= 400). Interaction scores include neighborhood, fusion, co-expression, experimental, database, text-mining, and co-occurrence sub-scores.

### 1.4 Bioactivity Data

**Source**: ChEMBL REST API (EMBL-EBI)

**Method**: For each gene target, we search ChEMBL for matching targets and retrieve bioactivity records. Compound-target edges are stored with pChEMBL values (negative log of IC50/EC50/Ki/Kd in M) as confidence metrics. pChEMBL >= 6 indicates moderate activity; >= 8 indicates high activity.

**Current data**: 188 unique compounds with 191 bioactivity measurements.

### 1.5 Protein Annotations

**Source**: UniProt REST API (Swiss-Prot reviewed entries)

**Method**: Each gene symbol is mapped to its reviewed UniProt accession. Full annotations are retrieved: protein name, function description, Gene Ontology (GO) terms, Reactome/KEGG pathways, and keyword annotations. Shared GO biological process terms and shared pathways between targets create network edges.

### 1.6 Pathway Data

**Source**: KEGG REST API

**Method**: The SMA pathway (hsa05033) is queried for member genes. Overlaps between KEGG pathway members and our target list create co-pathway edges in the knowledge graph.

---

## 2. Claim Extraction

### 2.1 LLM-Based Structured Extraction

**Model**: Claude 3 Haiku (Anthropic)

**Method**: Each PubMed abstract is processed by the LLM with a structured prompt that extracts factual claims. The model outputs JSON with typed claims:

| Claim Type | Description |
|------------|-------------|
| gene_expression | Expression changes in specific conditions |
| protein_interaction | Physical or functional protein interactions |
| pathway_membership | Gene/protein belongs to a biological pathway |
| drug_target | A compound acts on a specific molecular target |
| drug_efficacy | Evidence of therapeutic effect |
| biomarker | Potential diagnostic or prognostic marker |
| splicing_event | Splicing regulation relevant to SMA |
| neuroprotection | Neuroprotective mechanisms |
| motor_function | Effects on motor function |
| survival | Survival outcomes |
| safety | Safety/toxicity data |
| other | Claims not fitting above categories |

Each claim includes: subject (entity), predicate (relationship), object (entity), confidence score, and the originating source_id for full traceability.

### 2.2 Target Linking

Claims are linked to molecular targets using fuzzy symbol matching against the targets table. This enables per-target evidence aggregation. Claims are re-linked when new targets are added (retroactive linking).

### 2.3 Limitations of LLM Extraction

- Claims are only as reliable as the LLM's interpretation of abstracts
- Full-text analysis is not yet performed (abstracts only)
- Confidence scores are model-assigned, not statistically derived
- Extraction errors are possible — all claims should be verified against the source paper

---

## 3. Evidence Scoring & Target Prioritization

### 3.1 Seven-Dimension Scoring

Each molecular target is scored across 7 orthogonal dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Genetic Evidence | 0.25 | Strength of genetic association with SMA |
| Biological Coherence | 0.20 | Mechanistic plausibility (pathway relevance, protein interactions) |
| Clinical Validation | 0.15 | Evidence from clinical trials or approved therapies |
| Druggability | 0.15 | Known compounds, binding sites, drug-like properties |
| Network Centrality | 0.10 | Position in the protein interaction network |
| Publication Density | 0.10 | Volume and recency of research literature |
| Biomarker Potential | 0.05 | Measurability as a disease or response biomarker |

Each dimension is scored 0.0–1.0 based on available evidence. The composite score is a weighted sum.

### 3.2 Scoring Methodology

- **Genetic Evidence**: Based on claim count and type (gene_expression, splicing_event claims weighted higher)
- **Biological Coherence**: Pathway membership, GO term overlap, STRING interaction count
- **Clinical Validation**: Presence in clinical trial interventions, approved drug targets
- **Druggability**: ChEMBL bioactivity data (pChEMBL values), known drug-target edges
- **Network Centrality**: Degree centrality in STRING interaction + shared pathway network
- **Publication Density**: Claim count normalized by corpus size, weighted by recency
- **Biomarker Potential**: Biomarker-type claims, expression measurability

### 3.3 Limitations

- Weights are expert-assigned, not statistically optimized
- Scoring reflects currently ingested evidence (expanding corpus changes scores)
- Discovery targets with fewer publications will score lower due to data sparsity, not lack of therapeutic potential

---

## 4. Hypothesis Generation

### 4.1 Method

For each target with sufficient claims (>= 3), the system generates research hypotheses by:

1. Aggregating all claims linked to the target
2. Identifying evidence patterns (e.g., multiple papers reporting similar findings)
3. Cross-referencing with known SMA biology and approved therapies
4. Using Claude 3 Haiku to synthesize claims into structured hypothesis cards

Each hypothesis includes: title, description, supporting claims (with source IDs), confidence level, and suggested next experiments.

### 4.2 Prioritization (Tier System)

Hypotheses are ranked by a multi-criteria score and assigned to tiers:

- **Tier A** (top 5): High-conviction, ready for experimental validation
- **Tier B** (6-15): Medium priority, need more evidence
- **Tier C** (rest): Lower priority or insufficient data

---

## 5. Knowledge Graph

### 5.1 Structure

The knowledge graph connects molecular targets through multiple edge types:

| Edge Type | Source | Meaning |
|-----------|--------|---------|
| protein_interaction | STRING-DB | Physical/functional protein interaction |
| shared_go_process | UniProt | Shared Gene Ontology biological process |
| shared_pathway | KEGG | Co-membership in KEGG pathway |
| shared_pathway_uniprot | UniProt/Reactome | Co-membership in Reactome pathway |
| compound_bioactivity | ChEMBL | Compound has measured activity against target |

### 5.2 Network Analysis

Network centrality metrics (degree, betweenness) inform the Network Centrality scoring dimension. Highly connected targets in the SMA network are flagged as potential pathway hubs.

---

## 6. Cross-Species Comparative Biology (Querdenker Module)

### 6.1 Rationale

Certain organisms possess natural mechanisms for motor neuron regeneration or neuroprotection that SMA patients lack:

- **Axolotl** (*Ambystoma mexicanum*): Full spinal cord regeneration
- **Zebrafish** (*Danio rerio*): Motor neuron regeneration
- **Naked Mole Rat** (*Heterocephalus glaber*): Extreme resistance to neurodegeneration
- **C. elegans**: Conserved SMN ortholog (smn-1) with motor neuron models
- **Drosophila**: Well-characterized SMN loss-of-function phenotypes

### 6.2 Method

1. **Ortholog mapping**: NCBI Datasets API maps human SMA gene targets to orthologs across 5 model organisms
2. **Conservation scoring**: Fraction of model organisms with a detectable ortholog (0.0–1.0)
3. **Literature mining**: 16 cross-species PubMed queries retrieve regeneration-relevant papers
4. **Divergence analysis**: Comparison of expression patterns, pathway regulation, and regeneration involvement between human and model organism orthologs

---

## 7. Data Quality & Validation

### 7.1 Source Provenance

Every claim in the database traces back to a specific PubMed paper (via source_id → evidence → claim chain). This full traceability ensures that no assertion exists without a verifiable origin.

### 7.2 Automated Quality Checks

- Duplicate detection by external ID (PMID, NCT ID)
- Claim type validation via database CHECK constraint (12 valid types)
- Confidence score range enforcement (0.0–1.0)
- Ingestion logging with error tracking and duration metrics

### 7.3 Known Limitations

1. **Abstract-only analysis**: Full-text papers are not yet processed. Some claims may be incomplete or miss context from methods/results sections.
2. **LLM extraction errors**: Automated claim extraction can produce false positives or miss relevant claims. Estimated error rate: 5-15% based on manual spot-checks.
3. **Publication bias**: PubMed queries favor published, English-language research. Negative results and non-English literature are underrepresented.
4. **Temporal bias**: Discovery targets have fewer publications, creating an inherent scoring disadvantage vs. well-studied targets like SMN1/SMN2.
5. **No experimental validation**: This is a computational platform. All hypotheses require independent experimental validation before clinical application.

---

## 8. Reproducibility

### 8.1 Data Sources

All data is derived from public, freely accessible databases:
- PubMed (NCBI): https://pubmed.ncbi.nlm.nih.gov/
- ClinicalTrials.gov: https://clinicaltrials.gov/
- STRING-DB: https://string-db.org/
- ChEMBL: https://www.ebi.ac.uk/chembl/
- UniProt: https://www.uniprot.org/
- KEGG: https://www.kegg.jp/
- NCBI Gene: https://www.ncbi.nlm.nih.gov/gene/

### 8.2 API Access

All platform data is accessible via REST API at `https://sma-research.info/api/v2/`. API documentation is available at `/api/v2/docs` (Swagger UI).

### 8.3 Machine-Readable Metadata

- `llms.txt` provides structured platform overview for AI systems
- `sitemap.xml` lists all public pages
- `robots.txt` allows research-focused crawlers

---

## 9. Ethical Considerations

- This platform is a research tool, not a clinical decision-making system
- No patient data is collected or processed
- All source data comes from publicly available databases
- The platform is open-source to enable independent verification
- Hypotheses are computational predictions, not medical advice

---

## References

1. Lefebvre S, et al. (1995). Identification and characterization of a spinal muscular atrophy-determining gene. *Cell*, 80(1), 155-165.
2. Szklarczyk D, et al. (2023). The STRING database in 2023. *Nucleic Acids Research*, 51(D1), D99-D106.
3. Mendez D, et al. (2019). ChEMBL: towards direct deposition of bioassay data. *Nucleic Acids Research*, 47(D1), D930-D940.
4. The UniProt Consortium (2023). UniProt: the Universal Protein Knowledgebase in 2023. *Nucleic Acids Research*, 51(D1), D523-D531.
5. Kanehisa M, et al. (2023). KEGG for taxonomy-based analysis of pathways and genomes. *Nucleic Acids Research*, 51(D1), D587-D592.

---

*Last updated: 2026-03-15*
*Contact: Christian Fischer — christian@bryzant.com*
