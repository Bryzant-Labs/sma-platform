# NVIDIA NIMs as MCP Tools & Claude Code Skills — Integration Plan

**Date:** 2026-03-22
**Status:** PLAN (not yet implemented)
**Author:** Architecture session (Opus lead)

---

## Overview

The SMA Research Platform has 11 live NVIDIA NIM endpoints and an MCP server with 32 tools. This plan adds 8 new MCP tools wrapping NIM endpoints and 6 Claude Code skills combining MCP tools into research workflows.

### Current State

**MCP Server** (`mcp_server/server.py`, 1441 lines):
- 32 tools covering: targets, claims, hypotheses, sources, trials, drugs, evidence, discovery signals, splice prediction, screening, knowledge graph, patents, convergence scoring, cross-paper synthesis, PMID verification
- Already has 2 NIM-adjacent tools: `dock_compound_nim` (DiffDock via API) and `run_virtual_screening` (GenMol+RDKit+DiffDock pipeline)
- Also has: `check_nim_health`, `check_alphafold_complexes`, `list_binder_targets`
- Uses `httpx.AsyncClient` with FastMCP pattern, all data via REST API at `https://sma-research.info/api/v2/`

**NIM Adapter** (`src/sma_platform/ingestion/adapters/nvidia_nims.py`):
- `diffdock_dock`, `diffdock_dock_smiles`, `diffdock_batch_dock`
- `openfold3_predict`, `openfold3_protein_rna_complex`
- `genmol_generate`, `genmol_from_4ap`
- `predict_structure_af2`, `predict_structure_af2_multimer`
- `predict_structure_esmfold`
- `design_binder` (RFdiffusion)
- `design_sequence` (ProteinMPNN)
- `msa_search`
- `esm2_embed` (with retry logic for degraded endpoint)
- `rnapro_predict` (container-only, requires self-hosted URL)

**API Routes** (`src/sma_platform/api/routes/nvidia_nims.py`):
- All 11 NIMs exposed as REST endpoints under `/api/v2/nims/`
- All require `SMA_ADMIN_KEY` via `require_admin_key` dependency
- ROCK2 binder design pipeline already exists as end-to-end route

**Existing MCP Tools that overlap with proposed tools:**
- `dock_compound_nim` — already wraps DiffDock (but only accepts SMILES + PDB ID)
- `run_virtual_screening` — already wraps GenMol + DiffDock pipeline
- `check_nim_health` — already checks all NIM endpoints
- `check_alphafold_complexes` — checks AF DB for 8 SMA complexes
- `list_binder_targets` — lists 6 SMA targets ready for binder design

---

## Part 1: New MCP Tools for NIMs

### Design Principles

1. **Simple inputs** — accept protein names/symbols, not raw PDB content. The tool resolves structures internally via AlphaFold DB or the platform's target registry.
2. **Structured outputs** — return parsed results with confidence scores, not raw NIM JSON.
3. **SMA-aware** — default targets are SMA proteins. UniProt ID mapping is built in for all 12 SMA targets already in the NIM adapter.
4. **Error handling** — check NVIDIA_API_KEY, validate inputs, return descriptive error dicts (same pattern as existing `_get()` helper).
5. **Auth** — all NIM tools require `SMA_ADMIN_KEY` (POST requests to platform API).

### Tool 1: `predict_protein_structure`

**Priority:** HIGH

**Description:** Predict the 3D structure of a protein using AlphaFold2 or ESMfold. Accepts a protein name (resolved to sequence via UniProt) or a raw amino acid sequence. Returns PDB structure with confidence metrics.

**Input Schema:**
```python
async def predict_protein_structure(
    protein: str,          # Protein name/symbol (e.g., "NCALD", "PLS3") or amino acid sequence
    method: str = "auto",  # "alphafold2", "esmfold", or "auto" (ESMfold for <300 residues, AF2 otherwise)
) -> dict[str, Any]
```

**Output Schema:**
```json
{
  "protein": "NCALD",
  "sequence_length": 191,
  "method": "esmfold",
  "pdb_structure": "ATOM  1  N  MET A   1 ...",
  "plddt_mean": 87.3,
  "plddt_per_residue": [92.1, 88.4],
  "confidence_category": "high",
  "alphafold_db_available": true,
  "alphafold_db_url": "https://alphafold.ebi.ac.uk/entry/P61601",
  "runtime_seconds": 12.4
}
```

**NIMs called:** AlphaFold2 or ESMfold (based on `method` parameter)

**Platform APIs called:**
- `/api/v2/targets/symbol/{symbol}` — resolve protein name to identifiers
- AlphaFold DB API — check if pre-computed structure exists
- UniProt API — resolve symbol to sequence if not provided

**Error handling:**
- Unknown protein symbol: return list of available SMA targets
- NIM timeout (AF2 can take 10+ minutes): return timeout error with suggestion to use ESMfold
- NVIDIA_API_KEY not set: return setup instructions
- Sequence too long (>2000 residues): reject with explanation

**Example usage (in Claude Code):**
```
User: "Predict the structure of NCALD"
Claude: [calls predict_protein_structure(protein="NCALD")]
-> Returns ESMfold structure with pLDDT 87.3, links to AlphaFold DB entry
```

---

### Tool 2: `predict_protein_complex`

**Priority:** MEDIUM

**Description:** Predict the 3D structure of a protein-protein complex using AlphaFold2-Multimer. Accepts 2-6 protein names or sequences.

**Input Schema:**
```python
async def predict_protein_complex(
    proteins: list[str],           # 2-6 protein names/symbols or sequences
    relax_prediction: bool = True, # Apply Amber energy minimization
) -> dict[str, Any]
```

**Output Schema:**
```json
{
  "complex_name": "SMN-Gemin2",
  "chains": [
    {"protein": "SMN1", "sequence_length": 294},
    {"protein": "GEMIN2", "sequence_length": 280}
  ],
  "pdb_structure": "ATOM ...",
  "plddt_mean": 72.1,
  "ptm_score": 0.68,
  "iptm_score": 0.55,
  "interface_residues": ["A:45-52", "B:120-135"],
  "confidence_category": "medium",
  "runtime_seconds": 340.2
}
```

**NIMs called:** AlphaFold2-Multimer

**Error handling:**
- More than 6 chains: reject (AF2-Multimer limit)
- Unknown protein: resolve via UniProt or return error
- Very large complexes (>3000 total residues): warn about long runtime

**Example usage:**
```
User: "Predict the structure of the SMN-p53 complex"
Claude: [calls predict_protein_complex(proteins=["SMN1", "TP53"])]
-> Returns complex structure with interface analysis
```

---

### Tool 3: `design_protein_binder`

**Priority:** HIGH

**Description:** Design a novel protein that binds to a specified target using RFdiffusion (backbone design) + ProteinMPNN (sequence design). This is a 2-step pipeline.

**Input Schema:**
```python
async def design_protein_binder(
    target: str,                       # Target protein name/symbol (e.g., "ROCK2", "NCALD")
    hotspot_residues: list[str] = [],  # Optional: specific residues to target (e.g., ["A100", "A105"])
    binder_length: int = 100,          # Length of designed binder (50-200 residues)
    num_designs: int = 5,              # Number of designs (1-20)
) -> dict[str, Any]
```

**Output Schema:**
```json
{
  "target": "ROCK2",
  "target_uniprot": "O75116",
  "num_designs": 5,
  "designs": [
    {
      "design_id": "ROCK2-binder-001",
      "backbone_pdb": "ATOM ...",
      "sequence": "MKVILLDEFGH...",
      "mpnn_score": 0.82,
      "binder_length": 100,
      "hotspot_contacts": ["A100", "A105"]
    }
  ],
  "pipeline": ["RFdiffusion (backbone)", "ProteinMPNN (sequence)"],
  "runtime_seconds": 45.2
}
```

**NIMs called:**
1. RFdiffusion — generate binder backbones
2. ProteinMPNN — design sequences for each backbone

**Platform APIs called:**
- AlphaFold DB — download target structure (auto-resolved from target symbol)
- `/api/v2/targets/symbol/{symbol}` — resolve UniProt ID

**Error handling:**
- Target without AlphaFold structure: return error with suggestions
- RFdiffusion fails: return partial results (backbone only if MPNN fails)
- Empty hotspot_residues: use default interface residues from `SMA_BINDER_TARGETS` list

**Example usage:**
```
User: "Design a protein that blocks the ROCK2 kinase domain"
Claude: [calls design_protein_binder(target="ROCK2", hotspot_residues=["A160", "A165", "A230"])]
-> Returns 5 binder designs with sequences, ready for experimental validation
```

---

### Tool 4: `generate_molecules`

**Priority:** HIGH

**Description:** Generate novel drug-like molecules using GenMol. Accepts a scaffold SMILES or target name (uses known scaffolds for SMA targets).

**Input Schema:**
```python
async def generate_molecules(
    scaffold_smiles: str = "",    # Starting molecule (SMILES). If empty, uses target default.
    target: str = "SMN2",         # SMA target (used to select default scaffold if scaffold_smiles empty)
    num_molecules: int = 50,      # How many to generate (10-500)
    filter_druglike: bool = True, # Apply Lipinski + QED filter
) -> dict[str, Any]
```

**Output Schema:**
```json
{
  "scaffold": "Nc1ccncc1",
  "target": "SMN2",
  "num_generated": 50,
  "num_passed_filter": 32,
  "molecules": [
    {
      "smiles": "CC(=O)Nc1ccnc(NC(=O)c2ccccc2)c1",
      "qed": 0.78,
      "lipinski_pass": true,
      "molecular_weight": 255.3
    }
  ],
  "nim": "GenMol v1.0"
}
```

**NIMs called:** GenMol

**Platform APIs called:** None (standalone generation)

**Error handling:**
- Invalid SMILES: return parse error with common examples
- GenMol timeout: return partial results
- No molecules pass filter: lower filter threshold and retry, or return all unfiltered

**Default scaffolds by target:**

| Target | Default Scaffold | Rationale |
|--------|-----------------|-----------|
| SMN2 | `Nc1ccncc1` (4-AP) | Known hit from DiffDock screening |
| ROCK2 | `c1ccc2[nH]c(-c3ccncc3)nc2c1` (fasudil-like) | Validated ROCK inhibitor |
| CORO1C | (de novo) | No known small molecule binders |
| PLS3 | (de novo) | Protein-protein interface target |

---

### Tool 5: `optimize_molecule`

**Priority:** MEDIUM

**Description:** Optimize a molecule for improved properties using MolMIM. Takes an existing SMILES and generates optimized variants.

**Input Schema:**
```python
async def optimize_molecule(
    smiles: str,                        # Input molecule SMILES
    optimize_for: str = "drug_likeness", # "drug_likeness", "bbb_permeability", "potency"
    num_variants: int = 20,             # Number of optimized variants to generate
) -> dict[str, Any]
```

**Output Schema:**
```json
{
  "input_smiles": "Nc1ccncc1",
  "input_qed": 0.45,
  "optimization_target": "drug_likeness",
  "variants": [
    {
      "smiles": "CC(N)c1ccncc1O",
      "qed": 0.72,
      "tanimoto_similarity": 0.65,
      "improvement": "+0.27 QED"
    }
  ],
  "nim": "MolMIM"
}
```

**NIMs called:** MolMIM (molecule optimization)

**Error handling:**
- Invalid SMILES: return parse error
- MolMIM returns identical molecules: increase temperature, retry

---

### Tool 6: `search_sequence_alignment`

**Priority:** LOW

**Description:** Search for homologous protein sequences using MSA Search. Useful for finding evolutionary conservation of SMA targets across species.

**Input Schema:**
```python
async def search_sequence_alignment(
    protein: str,     # Protein name/symbol or amino acid sequence
    databases: list[str] = [],  # Databases to search (default: all available)
) -> dict[str, Any]
```

**Output Schema:**
```json
{
  "query_protein": "SMN1",
  "query_length": 294,
  "num_hits": 1250,
  "top_hits": [
    {
      "species": "Mus musculus",
      "identity_percent": 82.3,
      "alignment_length": 289,
      "accession": "Q9Z1X5"
    }
  ],
  "conservation_summary": "Highly conserved in vertebrates (>80% in mammals)",
  "databases_searched": ["uniref30", "pdb70", "colabfold_envdb"],
  "runtime_seconds": 25.1
}
```

**NIMs called:** MSA Search (ColabFold)

**Error handling:**
- Sequence too short (<20 residues): warn about low specificity
- No hits: return empty result with suggestion to lower e-value threshold

---

### Tool 7: `embed_protein`

**Priority:** LOW

**Description:** Get protein sequence embeddings using ESM-2 650M. Useful for similarity search and clustering of SMA targets.

**Input Schema:**
```python
async def embed_protein(
    proteins: list[str],  # 1-10 protein names/symbols or sequences
) -> dict[str, Any]
```

**Output Schema:**
```json
{
  "proteins": ["SMN1", "SMN2"],
  "embeddings": {
    "SMN1": [0.123, -0.456],
    "SMN2": [0.125, -0.452]
  },
  "similarity_matrix": {
    "SMN1-SMN2": 0.987
  },
  "embedding_dim": 1280,
  "nim": "ESM-2 650M",
  "status_note": "ESM-2 endpoint is intermittently degraded -- results may require retry"
}
```

**NIMs called:** ESM-2 650M (with retry logic)

**Error handling:**
- ESM-2 degraded (HTTP 500): retry 3x with exponential backoff (already implemented in adapter)
- More than 10 proteins: reject (rate limiting)
- Return partial results if some sequences fail

---

### Tool 8: `dock_compound` (enhanced version of existing `dock_compound_nim`)

**Priority:** HIGH

**Description:** Enhanced molecular docking tool that accepts protein names (not just PDB IDs), resolves structures automatically, and returns parsed results with comparison to existing screening hits.

**Input Schema:**
```python
async def dock_compound(
    compound: str,            # Drug name, SMILES, or compound identifier
    target: str = "SMN2",     # Target protein name/symbol
    num_poses: int = 10,      # Number of binding poses (1-20)
    compare_existing: bool = True,  # Compare with existing screening results
) -> dict[str, Any]
```

**Output Schema:**
```json
{
  "compound": "4-Aminopyridine",
  "smiles": "Nc1ccncc1",
  "target": "SMN2",
  "target_uniprot": "Q16637",
  "nim": "DiffDock v2.2",
  "poses": [
    {
      "pose_id": 1,
      "confidence": 0.342,
      "binding_site_residues": ["TYR130", "ASP134", "GLU137"],
      "sdf_content": "..."
    }
  ],
  "top_confidence": 0.342,
  "comparison": {
    "existing_hits_for_target": 12,
    "rank_among_existing": 3,
    "better_than_riluzole": true,
    "riluzole_confidence": 0.285
  },
  "runtime_seconds": 8.2
}
```

**NIMs called:** DiffDock v2.2

**Platform APIs called:**
- `/api/v2/targets/symbol/{symbol}` — resolve target
- `/api/v2/screen/compounds/results` — compare with existing hits
- `/api/v2/drugs` — resolve drug name to SMILES
- AlphaFold DB — download target structure

**Compound name resolution:**
The tool resolves common drug names to SMILES using the platform's drug registry. Supported name formats:
- SMILES string (detected by presence of special characters)
- Drug name from platform (e.g., "riluzole", "risdiplam", "4-AP")
- PubChem CID (e.g., "CID:5353940")

**Error handling:**
- Unknown compound: return error with suggestion to provide SMILES directly
- Unknown target: return list of available targets with UniProt IDs
- DiffDock timeout: return error with suggestion to reduce num_poses
- All poses have confidence < 0: warn that binding is unlikely

---

## Part 2: Claude Code Skills for Research Workflows

Skills are stored as markdown files in `.claude/skills/`. Each skill is a prompt template that Claude Code executes as a multi-step workflow, calling MCP tools and platform APIs.

### Skill File Location

Create skills at: `/mnt/c/Users/bryza/Dropbox/Christian fischer/SMA/sma-platform/.claude/skills/`

### Skill 1: `/sma-dock`

**Priority:** HIGH
**File:** `.claude/skills/sma-dock.md`

**Description:** Dock a compound against an SMA target. End-to-end from drug name to ranked binding poses with context.

**Input:** Drug name or SMILES + target name
**Example:** `/sma-dock riluzole against ROCK2`

**Workflow:**
```
1. Parse input -> extract compound identifier and target name
2. Call search_sma_drugs -> resolve drug name to SMILES
3. Call get_sma_target -> get target details and UniProt ID
4. Call dock_compound -> DiffDock v2.2 docking
5. Call get_screening_results -> compare with existing hits for this target
6. Call search_sma_claims -> find claims about this drug-target pair
7. Synthesize results:
   - Binding pose analysis (top confidence, binding site residues)
   - Comparison with existing screening hits (percentile rank)
   - Literature context (any prior evidence for this interaction?)
   - Actionable recommendation (worth pursuing? next steps?)
```

**MCP Tools Called:**

| Step | Tool | Purpose |
|------|------|---------|
| 2 | `search_sma_drugs` | Resolve drug name to SMILES |
| 3 | `get_sma_target` | Get target UniProt ID |
| 4 | `dock_compound` (NEW) | DiffDock docking |
| 5 | `get_screening_results` | Compare with existing |
| 6 | `search_sma_claims` | Literature context |

**Output Format:**
```markdown
## Docking Result: {compound} vs {target}

**Top Binding Pose:** confidence {score} (rank #{n} of {total} screened compounds)
**Binding Site:** {residues}

### Comparison with Existing Hits
- Better than {n}% of previously screened compounds
- {comparison with riluzole/risdiplam benchmarks}

### Literature Context
- {n} existing claims about this drug-target pair
- {key findings from claims}

### Recommendation
{actionable next step}
```

**Error Handling:**
- Drug not found: ask user for SMILES directly
- Target not found: list available targets
- DiffDock fails: report error, suggest trying different target or checking NIM health

---

### Skill 2: `/sma-structure`

**Priority:** HIGH
**File:** `.claude/skills/sma-structure.md`

**Description:** Predict and analyze a protein structure with druggability assessment.

**Input:** Protein name or sequence
**Example:** `/sma-structure CORO1C`

**Workflow:**
```
1. Parse input -> identify protein name or raw sequence
2. Call get_sma_target -> get target details, known structures
3. Check AlphaFold DB -> is pre-computed structure available?
4. If no existing structure: call predict_protein_structure (NEW)
   - Use ESMfold for <300 residues, AlphaFold2 for longer
5. Call embed_protein (NEW) -> get ESM-2 embedding
6. Call get_knowledge_graph_neighbors -> find related proteins
7. Synthesize results:
   - Structure quality assessment (pLDDT analysis)
   - Druggability assessment (surface pockets, disorder regions)
   - Similarity to other SMA targets (embedding comparison)
   - Known binding partners and interfaces
```

**MCP Tools Called:**

| Step | Tool | Purpose |
|------|------|---------|
| 2 | `get_sma_target` | Target details |
| 3 | `check_alphafold_complexes` | Existing structures |
| 4 | `predict_protein_structure` (NEW) | De novo prediction |
| 5 | `embed_protein` (NEW) | Protein embeddings |
| 6 | `get_knowledge_graph_neighbors` | Biological context |

**Output Format:**
```markdown
## Structure Analysis: {protein}

**Method:** {ESMfold/AlphaFold2/AlphaFold DB}
**Confidence:** pLDDT {mean} ({category})
**Length:** {residues} residues

### Structure Quality
- High-confidence regions (pLDDT > 90): {residue ranges}
- Disordered regions (pLDDT < 50): {residue ranges}

### Druggability Assessment
- Surface pockets: {analysis}
- Known binding interfaces: {from knowledge graph}

### Similarity to Other SMA Targets
{embedding-based comparison table}

### Recommendations
{Is this target structurally tractable for drug design?}
```

---

### Skill 3: `/sma-design-drug`

**Priority:** HIGH
**File:** `.claude/skills/sma-design-drug.md`

**Description:** Design a new small molecule for an SMA target using the full generative virtual screening pipeline.

**Input:** Target name + optional scaffold
**Example:** `/sma-design-drug for ROCK2 starting from fasudil`

**Workflow:**
```
1. Parse input -> extract target name and optional scaffold
2. Call get_sma_target -> verify target, get UniProt ID
3. Call get_screening_results -> check what has already been screened
4. Call generate_molecules (NEW) -> GenMol de novo generation (50-100 molecules)
5. Filter by drug-likeness (Lipinski, QED > 0.5, BBB if needed)
6. Call dock_compound (NEW) -> DiffDock for top 10 filtered molecules
7. Call search_sma_claims -> find claims about this target's druggability
8. Rank and report:
   - Top 5 candidates with SMILES, QED, docking score
   - Comparison with known drugs for this target
   - ADMET prediction (basic: MW, LogP, HBD, HBA, TPSA)
   - Novelty assessment (Tanimoto similarity to known drugs)
```

**MCP Tools Called:**

| Step | Tool | Purpose |
|------|------|---------|
| 2 | `get_sma_target` | Target validation |
| 3 | `get_screening_results` | Existing screening data |
| 4 | `generate_molecules` (NEW) | GenMol generation |
| 6 | `dock_compound` (NEW) | DiffDock validation |
| 7 | `search_sma_claims` | Literature context |

**Output Format:**
```markdown
## Drug Design Campaign: {target}

**Scaffold:** {SMILES or "de novo"}
**Generated:** {n} molecules | **Filtered:** {n} drug-like | **Docked:** {n}

### Top 5 Candidates

| Rank | SMILES | QED | Docking | MW | LogP |
|------|--------|-----|---------|-----|------|
| 1 | ... | 0.82 | 0.45 | 312 | 2.1 |

### Novelty Assessment
- Tanimoto similarity to closest known drug: {value}
- Novel scaffold: {yes/no}

### Recommendation
{Which candidates to prioritize for experimental validation}
```

---

### Skill 4: `/sma-binder`

**Priority:** MEDIUM
**File:** `.claude/skills/sma-binder.md`

**Description:** Design a therapeutic protein binder for an SMA target using the RFdiffusion + ProteinMPNN pipeline.

**Input:** Target name + optional hotspot residues
**Example:** `/sma-binder for ROCK2 kinase domain`

**Workflow:**
```
1. Parse input -> extract target and hotspot residues
2. Call get_sma_target -> verify target
3. Call list_binder_targets -> check if target is pre-configured
4. Call predict_protein_structure (NEW) -> get target structure if needed
5. Call design_protein_binder (NEW) -> RFdiffusion + ProteinMPNN pipeline
6. For top 3 designs: call predict_protein_structure (NEW) with ESMfold
   -> validate that designed sequences fold correctly
7. Synthesize:
   - Top 3-5 binder designs with sequences
   - Folding validation (pLDDT of designed proteins)
   - Interface analysis (contact residues)
   - Comparison with known binders/antibodies for this target
```

**MCP Tools Called:**

| Step | Tool | Purpose |
|------|------|---------|
| 2 | `get_sma_target` | Target details |
| 3 | `list_binder_targets` | Pre-configured targets |
| 4 | `predict_protein_structure` (NEW) | Target structure |
| 5 | `design_protein_binder` (NEW) | Binder design |
| 6 | `predict_protein_structure` (NEW) | Design validation |

**Output Format:**
```markdown
## Protein Binder Design: {target}

**Target:** {name} ({uniprot})
**Hotspot residues:** {list}
**Pipeline:** RFdiffusion -> ProteinMPNN -> ESMfold validation

### Top Designs

| # | Sequence (truncated) | Length | MPNN Score | ESMfold pLDDT |
|---|---------------------|--------|------------|---------------|
| 1 | MKVILLDEFGH... | 100 | 0.85 | 78.2 |

### Validation
- Design 1: pLDDT {value} -- {folds well / disordered / needs optimization}
- Predicted interface contacts: {residue list}

### Next Steps
{Recommendations for experimental testing}
```

---

### Skill 5: `/sma-hypothesis`

**Priority:** MEDIUM
**File:** `.claude/skills/sma-hypothesis.md`

**Description:** Generate, evaluate, and propose experiments for a research hypothesis. Combines evidence graph with computational validation.

**Input:** A research observation, question, or preliminary hypothesis
**Example:** `/sma-hypothesis "CORO1C knockdown rescues motor neuron defects"`

**Workflow:**
```
1. Parse input -> extract the core scientific claim
2. Call search_sma_claims -> find supporting and contradicting evidence
3. Call get_sma_hypotheses -> check if similar hypothesis already exists
4. Call get_shared_mechanisms -> find mechanistic context
5. Call get_knowledge_graph_neighbors -> explore connected targets
6. Call validate_sma_hypothesis -> run platform validation pipeline
7. Call get_convergence_score -> check evidence convergence for involved targets
8. Generate structured hypothesis:
   - Falsifiable prediction statement
   - Supporting evidence (with PMIDs)
   - Contradicting evidence
   - Evidence gaps
   - Proposed experiments (ranked by expected value)
   - Confidence assessment with calibration note
```

**MCP Tools Called:**

| Step | Tool | Purpose |
|------|------|---------|
| 2 | `search_sma_claims` | Evidence search |
| 3 | `get_sma_hypotheses` | Existing hypotheses |
| 4 | `get_shared_mechanisms` | Mechanistic context |
| 5 | `get_knowledge_graph_neighbors` | Network context |
| 6 | `validate_sma_hypothesis` | Platform validation |
| 7 | `get_convergence_score` | Evidence strength |

**Output Format:**
```markdown
## Hypothesis: {title}

**Falsifiable Prediction:** {one sentence}
**Confidence:** {score} (calibrated)
**Status:** {novel / partially supported / well-supported / contradicted}

### Supporting Evidence ({n} claims)
1. {claim} -- {source} (PMID: {id})
...

### Contradicting Evidence ({n} claims)
1. {claim} -- {source}

### Evidence Gaps
- {what is missing to validate/refute}

### Proposed Experiments (ranked by Expected Value)
1. {experiment} -- Est. cost ${k}k, {weeks} weeks, P(success) = {p}
2. ...

### Mechanistic Context
{How this hypothesis connects to known SMA biology}
```

---

### Skill 6: `/sma-screen`

**Priority:** MEDIUM
**File:** `.claude/skills/sma-screen.md`

**Description:** Screen a compound library against an SMA target. Batch docking with filtering and ranking.

**Input:** Target + compound list (SMILES, drug names, or "top repurposing candidates")
**Example:** `/sma-screen ROCK2 against top 20 kinase inhibitors`

**Workflow:**
```
1. Parse input -> extract target and compound list
2. Call get_sma_target -> verify target
3. Resolve compounds:
   - If drug names: call search_sma_drugs for each -> SMILES
   - If "repurposing candidates": call get_repurposing_candidates -> SMILES
   - If SMILES list: use directly
4. Call dock_compound (NEW) -> batch DiffDock for all compounds
   (Use diffdock_batch_dock internally for efficiency -- single API call)
5. Filter results:
   - Lipinski rule of five
   - BBB permeability (if CNS target)
   - QED > 0.5
6. Rank by composite score (docking confidence * QED)
7. Call search_sma_claims -> find literature context for top hits
8. Generate screening report
```

**MCP Tools Called:**

| Step | Tool | Purpose |
|------|------|---------|
| 2 | `get_sma_target` | Target validation |
| 3 | `search_sma_drugs` / `get_repurposing_candidates` | Compound resolution |
| 4 | `dock_compound` (NEW, batch mode) | DiffDock docking |
| 7 | `search_sma_claims` | Literature context |

**Output Format:**
```markdown
## Screening Report: {n} compounds vs {target}

**Target:** {name} ({uniprot})
**Compounds screened:** {n} | **Passed filters:** {n}

### Ranked Hits

| Rank | Compound | SMILES | Dock Score | QED | Lipinski | BBB |
|------|----------|--------|------------|-----|----------|-----|
| 1 | ... | ... | 0.45 | 0.82 | Pass | Yes |

### Top Hit Analysis
- **{compound 1}:** {context from literature, mechanism of action}
- **{compound 2}:** ...

### Summary
- {n} compounds show confidence > 0.3 (actionable hits)
- Best hit: {name} (confidence {score}, {comparison to benchmark})
- Recommendation: {next steps}
```

---

## Part 3: Implementation Plan

### Phase 1: MCP Tools (Priority HIGH -- do first)

| # | Tool | Depends On | Est. Lines | Effort |
|---|------|-----------|------------|--------|
| 1 | `dock_compound` (enhanced) | Existing adapter | ~80 | 1h |
| 2 | `predict_protein_structure` | Existing adapter | ~70 | 1h |
| 3 | `generate_molecules` | Existing adapter | ~60 | 45m |
| 4 | `design_protein_binder` | Existing adapter | ~90 | 1.5h |

### Phase 2: MCP Tools (Priority MEDIUM/LOW)

| # | Tool | Depends On | Est. Lines | Effort |
|---|------|-----------|------------|--------|
| 5 | `predict_protein_complex` | Existing adapter | ~60 | 45m |
| 6 | `optimize_molecule` | Existing adapter | ~50 | 30m |
| 7 | `search_sequence_alignment` | Existing adapter | ~50 | 30m |
| 8 | `embed_protein` | Existing adapter | ~50 | 30m |

### Phase 3: Claude Code Skills

| # | Skill | Depends On | Est. Lines | Effort |
|---|-------|-----------|------------|--------|
| 1 | `/sma-dock` | `dock_compound` | ~100 (markdown) | 1h |
| 2 | `/sma-structure` | `predict_protein_structure`, `embed_protein` | ~100 | 1h |
| 3 | `/sma-design-drug` | `generate_molecules`, `dock_compound` | ~120 | 1.5h |
| 4 | `/sma-binder` | `design_protein_binder`, `predict_protein_structure` | ~120 | 1.5h |
| 5 | `/sma-hypothesis` | Existing MCP tools only | ~100 | 1h |
| 6 | `/sma-screen` | `dock_compound` (batch) | ~120 | 1.5h |

### Implementation Order

```
Week 1:
  Day 1: dock_compound (enhanced), predict_protein_structure
  Day 2: generate_molecules, design_protein_binder
  Day 3: /sma-dock, /sma-structure skills
  Day 4: /sma-design-drug, /sma-binder skills

Week 2:
  Day 1: predict_protein_complex, optimize_molecule
  Day 2: search_sequence_alignment, embed_protein
  Day 3: /sma-hypothesis, /sma-screen skills
  Day 4: Integration testing, documentation
```

### Technical Notes

1. **All new MCP tools go in `mcp_server/server.py`** — single-file MCP server pattern (existing convention).
2. **Tools call the platform REST API** (`/api/v2/nims/*`), not the NIM adapter directly. This keeps auth and rate limiting centralized.
3. **Skills go in `.claude/skills/`** as markdown files — Claude Code reads these to understand available workflows.
4. **`SMA_ADMIN_KEY` is required** for all NIM-backed tools (same as existing `dock_compound_nim`).
5. **Compound name resolution** should use the platform's drug registry first, then fall back to PubChem CID lookup.
6. **Batch docking** (for `/sma-screen`) should use `diffdock_batch_dock` internally — single API call for up to ~50 compounds.
7. **Timeout handling**: AlphaFold2 can take 10+ minutes. Use `REQUEST_TIMEOUT = 600` for structure prediction tools (vs 30s for regular tools).

### Testing Strategy

For each new MCP tool:
1. Unit test with known SMA protein (SMN2, Q16637)
2. Error case: invalid input, NIM unavailable, API key missing
3. Integration test: call from Claude Code via MCP

For each skill:
1. End-to-end test with a simple case (e.g., `/sma-dock 4-AP against SMN2`)
2. Verify all MCP tool calls succeed
3. Verify output format matches specification

### Risk Factors

| Risk | Mitigation |
|------|-----------|
| ESM-2 endpoint degraded | Retry logic already in adapter; skip embedding step in skills if unavailable |
| AlphaFold2 timeout (>10min) | Default to ESMfold for screening; use AF2 only when user explicitly requests |
| NIM rate limiting (free tier) | Implement request queuing; warn user about delays |
| NVIDIA API key rotation | Store key in env var, not code; check at startup |
| Large batch docking (>50 compounds) | Chunk into batches of 20; report progress |
| Compound name resolution failures | Fall back to PubChem API; ask user for SMILES if all else fails |

---

## Appendix: Existing vs New Tool Mapping

| Existing MCP Tool | New MCP Tool | Relationship |
|-------------------|-------------|-------------|
| `dock_compound_nim` | `dock_compound` | **Replace** — enhanced version with name resolution and comparison |
| `run_virtual_screening` | `generate_molecules` + `dock_compound` | **Complement** — skills compose these; keep `run_virtual_screening` as single-call pipeline |
| `check_nim_health` | (keep as-is) | No change |
| `check_alphafold_complexes` | `predict_protein_complex` | **Complement** — complexes checks AF DB, new tool does de novo prediction |
| `list_binder_targets` | `design_protein_binder` | **Complement** — list shows what is available, new tool does the design |

| Existing MCP Tool | Used By Skills |
|-------------------|---------------|
| `search_sma_claims` | `/sma-dock`, `/sma-design-drug`, `/sma-hypothesis`, `/sma-screen` |
| `get_sma_target` | `/sma-dock`, `/sma-structure`, `/sma-design-drug`, `/sma-binder`, `/sma-screen` |
| `get_sma_hypotheses` | `/sma-hypothesis` |
| `validate_sma_hypothesis` | `/sma-hypothesis` |
| `get_convergence_score` | `/sma-hypothesis` |
| `get_knowledge_graph_neighbors` | `/sma-structure`, `/sma-hypothesis` |
| `get_screening_results` | `/sma-dock`, `/sma-design-drug` |
| `search_sma_drugs` | `/sma-dock`, `/sma-screen` |
| `get_repurposing_candidates` | `/sma-screen` |
| `get_shared_mechanisms` | `/sma-hypothesis` |
