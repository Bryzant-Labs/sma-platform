# Cross-Species Comparative Biology Module — "Querdenker"

**Goal**: Discover novel SMA therapeutic approaches by analyzing how regenerative organisms solve motor neuron problems that SMA patients cannot.

**Architecture**: New `comparative` module that ingests cross-species data from PubMed, OrthoDB, STRING, and model organism databases. Maps orthologous genes across species, identifies divergent pathway regulation, and generates cross-species hypotheses.

**Why this matters**: No other SMA research platform does systematic cross-species analysis. Salamanders regenerate entire spinal cords. Zebrafish regenerate motor neurons. Naked mole rats resist neurodegeneration. Understanding WHY their motor neurons survive when human SMA neurons die could reveal entirely new therapeutic targets.

---

## Phase 1: Cross-Species Evidence Ingestion

### Task 1: PubMed Cross-Species Queries

Add targeted PubMed queries for motor neuron regeneration across species:

```python
CROSS_SPECIES_QUERIES = [
    # Axolotl / Salamander
    '"axolotl" AND ("motor neuron" OR "spinal cord regeneration")',
    '"axolotl" AND ("SMN" OR "survival motor neuron")',
    '"salamander" AND "neural regeneration" AND "motor"',
    '"ambystoma mexicanum" AND ("neuron" OR "regeneration")',

    # Zebrafish
    '"zebrafish" AND ("motor neuron regeneration" OR "spinal cord repair")',
    '"zebrafish" AND ("SMN" OR "smn1" OR "smn2")',
    '"danio rerio" AND "motor neuron" AND ("regeneration" OR "development")',

    # Naked mole rat
    '"naked mole rat" AND ("neurodegeneration" OR "neuroprotection")',
    '"heterocephalus glaber" AND "neuron"',

    # C. elegans
    '"C. elegans" AND ("smn-1" OR "SMN" OR "motor neuron")',
    '"caenorhabditis elegans" AND "motor neuron" AND "degeneration"',

    # Drosophila
    '"drosophila" AND ("SMN" OR "Smn" OR "motor neuron")',
    '"drosophila" AND "spinal muscular atrophy"',

    # General comparative
    '"motor neuron regeneration" AND "model organism"',
    '"neural regeneration" AND ("comparative" OR "cross-species")',
    '"axon regeneration" AND "motor neuron" AND ("zebrafish" OR "axolotl")',
]
```

**Files**: `src/sma_platform/ingestion/adapters/pubmed.py` (add to SMA_QUERIES)

### Task 2: Ortholog Database Integration

Build adapter for OrthoDB or NCBI Orthologs:

```python
# src/sma_platform/ingestion/adapters/orthologs.py

async def find_orthologs(gene_symbol: str, species_ids: list[str]) -> list[dict]:
    """Find orthologous genes across species.

    species_ids: NCBI taxonomy IDs
    - 9606: Homo sapiens
    - 8296: Ambystoma mexicanum (axolotl)
    - 7955: Danio rerio (zebrafish)
    - 10181: Heterocephalus glaber (naked mole rat)
    - 6239: C. elegans
    - 7227: Drosophila melanogaster
    """
    pass

async def get_ortholog_conservation(human_gene: str) -> dict:
    """Get conservation score and ortholog presence across model organisms."""
    pass
```

### Task 3: Cross-Species Targets Table

New database table:

```sql
CREATE TABLE cross_species_targets (
    id TEXT PRIMARY KEY,
    human_symbol TEXT NOT NULL,       -- e.g., SMN1
    human_target_id TEXT,             -- FK to targets.id
    species TEXT NOT NULL,            -- e.g., "axolotl"
    species_taxon_id TEXT,            -- NCBI taxonomy ID
    ortholog_symbol TEXT,             -- e.g., "smn1" in zebrafish
    ortholog_id TEXT,                 -- OrthoDB/NCBI ID
    conservation_score REAL,          -- 0-1 sequence identity
    functional_divergence TEXT,       -- JSON: what's different
    regeneration_relevant BOOLEAN,    -- is this gene involved in regeneration?
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

## Phase 2: Comparative Analysis

### Task 4: Regeneration Gene Set

Curate a set of genes known to be involved in neural regeneration:

| Gene | Species | Role |
|------|---------|------|
| Sox2 | Axolotl | Neural stem cell activation |
| Pax7 | Axolotl | Muscle/neural progenitor |
| Notch1 | Axolotl/Zebrafish | Neural regeneration signaling |
| Wnt3a | Zebrafish | Spinal cord patterning |
| CTNNB1 | Zebrafish | Wnt pathway, axon guidance |
| Ascl1a | Zebrafish | Motor neuron fate specification |
| Shh | Axolotl | Floor plate, motor neuron identity |
| FGF | Zebrafish | Glial bridge formation |

### Task 5: Divergence Analysis Engine

For each SMA target, analyze:
1. Is the ortholog present in regenerative species?
2. Is the ortholog expression pattern different?
3. Is the ortholog involved in regeneration pathways?
4. What are the key regulatory differences?

```python
# src/sma_platform/reasoning/comparative_analyzer.py

async def analyze_divergence(human_target_id: str) -> dict:
    """Compare a human SMA target across regenerative species.

    Returns:
    - ortholog_map: {species: {symbol, conservation, expression_diff}}
    - regeneration_pathways: which regeneration pathways the ortholog is in
    - divergence_hypothesis: AI-generated hypothesis about why the species differs
    """
    pass
```

### Task 6: Cross-Species Hypothesis Generation

New hypothesis type: `cross_species_insight`

```python
# Example hypothesis:
{
    "hypothesis_type": "cross_species_insight",
    "title": "Axolotl SMN ortholog maintains motor neurons via Sox2-mediated regeneration",
    "description": "In axolotl, the SMN ortholog is co-expressed with Sox2 in neural progenitors...",
    "species_source": "axolotl",
    "human_targets": ["SMN1", "SMN2"],
    "regeneration_genes": ["Sox2", "Notch1"],
    "therapeutic_angle": "Activating Sox2 in SMA motor neurons could promote neuroprotection",
}
```

---

## Phase 3: Frontend & API

### Task 7: API Endpoints

```
GET /api/v2/comparative/species          — List model organisms with target counts
GET /api/v2/comparative/orthologs/{symbol} — Orthologs for a target across species
GET /api/v2/comparative/divergence/{symbol} — Divergence analysis for a target
GET /api/v2/comparative/hypotheses       — Cross-species hypotheses
```

### Task 8: Frontend Tab

Add "Comparative" tab to index.html:
- Species overview cards (Axolotl, Zebrafish, Naked Mole Rat, C. elegans, Drosophila)
- Ortholog table per target
- Cross-species hypotheses section
- Visual: conservation heatmap (which targets are conserved in which species)

---

## Phase 4: Advanced Analysis

### Task 9: Pathway Comparison

For each SMA-disrupted pathway:
1. Map to KEGG pathway in regenerative species
2. Identify pathway components that are upregulated during regeneration
3. Cross-reference with existing SMA claims
4. Flag "pathway rescue" opportunities

### Task 10: Expression Atlas Integration

Pull expression data from Expression Atlas for model organisms:
- Baseline expression of SMA targets in different tissues
- Compare motor neuron expression across species
- Identify differentially expressed genes in regeneration contexts

---

## Data Sources Required

| Source | What | Status |
|--------|------|--------|
| PubMed | Cross-species motor neuron papers | NEW queries needed |
| OrthoDB | Ortholog mappings | NEW adapter |
| STRING-DB | Protein interactions per species | Existing (extend) |
| KEGG | Pathways per organism | NEW adapter (planned) |
| Expression Atlas | Cross-species expression | NEW adapter |
| NCBI Gene | Gene info per species | Existing (extend) |
| Ensembl | Genome annotations | Optional |

## Success Criteria

1. At least 100 cross-species papers ingested
2. Orthologs mapped for all 21 targets across 5+ species
3. At least 10 cross-species hypotheses generated
4. Divergence analysis available for top 10 SMA targets
5. Frontend tab with species overview and ortholog data

## Timeline Estimate

- Phase 1 (Ingestion): 1-2 days
- Phase 2 (Analysis): 2-3 days
- Phase 3 (Frontend/API): 1 day
- Phase 4 (Advanced): 3-5 days

## Unique Value Proposition

No other SMA platform performs systematic cross-species analysis. This module positions sma-research.info as the first platform to bridge regenerative biology with SMA drug discovery — a genuinely novel research direction.
