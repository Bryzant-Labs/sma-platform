# NVIDIA GTC 2026 Integration — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate 7 new NVIDIA GTC 2026 announcements into the SMA Research Platform — from quick API calls (RNAPro) to full pipeline integration (Generative Virtual Screening Blueprint).

**Architecture:** Extend existing nvidia_nims.py adapter with new NIM endpoints, add new routes, integrate NVIDIA open-source repos for Proteina-Complexa and Virtual Screening Blueprint, update roadmap.

**Tech Stack:** FastAPI, httpx, NVIDIA NIM APIs, BioNeMo NIMs, Proteina-Complexa (PyTorch), GenMol, RNAPro, nvMolKit

**Project root:** `/mnt/c/Users/bryza/Dropbox/Christian fischer/SMA/sma-platform/`

**Important:** Do NOT use `isolation: "worktree"` — path spaces break worktrees.

---

## Task 1: RNAPro NIM — SMN2 pre-mRNA Structure Prediction (QUICKEST WIN)

**Goal:** Predict the 3D structure of SMN2 pre-mRNA around the ISS-N1 region using NVIDIA's RNAPro NIM. This is directly relevant for understanding why ASOs like nusinersen bind where they do.

**Files:**
- Modify: `src/sma_platform/ingestion/adapters/nvidia_nims.py` — add RNAPro API function
- Modify: `src/sma_platform/api/routes/nvidia_nims.py` — add RNAPro endpoint
- Frontend: add results to GPU Results section

**Step 1: Add RNAPro function to nvidia_nims.py adapter**

Add after existing GenMol section. RNAPro NIM endpoint for RNA 3D structure:

```python
# =============================================================================
# RNAPro — RNA 3D Structure Prediction
# =============================================================================

RNAPRO_URL = "https://health.api.nvidia.com/v1/biology/nvidia/rnapro"

async def rnapro_predict(
    rna_sequence: str,
    name: str = "SMN2_ISS_N1",
) -> dict:
    """Predict RNA 3D structure using NVIDIA RNAPro NIM."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            RNAPRO_URL,
            headers=_headers(),
            json={"sequence": rna_sequence, "name": name},
        )
        resp.raise_for_status()
        return resp.json()
```

**Step 2: Add route endpoint**

In nvidia_nims.py routes, add `POST /nims/rna-structure`:

```python
class RNAStructureRequest(BaseModel):
    rna_sequence: str
    name: str = "SMN2_ISS_N1"

@router.post("/rna-structure", dependencies=[Depends(require_admin_key)])
async def predict_rna_structure(req: RNAStructureRequest):
    """Predict RNA 3D structure using RNAPro NIM."""
    from ...ingestion.adapters.nvidia_nims import rnapro_predict
    result = await rnapro_predict(rna_sequence=req.rna_sequence, name=req.name)
    return {"status": "ok", "prediction": result, "model": "RNAPro"}
```

**Step 3: Run SMN2 ISS-N1 prediction on moltbot**

```bash
# SMN2 intron 7 ISS-N1 region (~50nt around the nusinersen binding site)
curl -X POST "http://localhost:8090/api/v2/nims/rna-structure" \
  -H "X-Admin-Key: sma-admin-2026" \
  -H "Content-Type: application/json" \
  -d '{"rna_sequence": "CCAGCAUUAUGAAAGUUGAAUUUUAAACUUUCCUUUAUUUUCCUUAAUUG", "name": "SMN2_intron7_ISS_N1"}'
```

**Step 4: Store result and add to GPU Results section**

**Step 5: Commit**

```
feat: add RNAPro NIM for SMN2 pre-mRNA 3D structure prediction
```

---

## Task 2: AlphaFold DB Complex Check

**Goal:** Check the expanded AlphaFold database (1.7M new complexes) for SMA-relevant protein complexes.

**Files:**
- Modify: `src/sma_platform/ingestion/adapters/alphafold.py` — add complex query function
- Modify: `src/sma_platform/api/routes/nvidia_nims.py` or create new route

**Step 1: Query AlphaFold DB for SMA protein complexes**

Check for predicted complexes involving:
- SMN + Gemin2/3/4/5
- SMN + p53
- SMN + UBA1
- PLS3 + actin
- NCALD + calcium channel

Use the AlphaFold REST API: `https://alphafold.ebi.ac.uk/api/complexes/{uniprot_id}`

**Step 2: Store new structural data in targets.metadata.alphafold_complexes**

**Step 3: Commit**

```
feat: check AlphaFold DB for SMA protein complexes (1.7M new structures)
```

---

## Task 3: Generative Virtual Screening Blueprint Integration

**Goal:** Replace our manual Trichter-Pipeline with NVIDIA's official open-source Blueprint for generative virtual screening.

**Files:**
- Create: `src/sma_platform/reasoning/virtual_screening.py` — orchestrator using NVIDIA Blueprint pattern
- Modify: `src/sma_platform/api/routes/funnel.py` or create new route
- Reference: `https://github.com/NVIDIA-BioNeMo-blueprints/generative-virtual-screening`

**Step 1: Study the Blueprint architecture**

Clone and analyze the NVIDIA blueprint:
```
git clone https://github.com/NVIDIA-BioNeMo-blueprints/generative-virtual-screening /tmp/nvidia-vs-blueprint
```

The blueprint uses: GenMol → MolMIM → DiffDock → ADMET filtering.

**Step 2: Create virtual_screening.py orchestrator**

Implement the pipeline using our existing NIM adapter:
1. **Generate**: GenMol generates candidate molecules from scaffold (4-AP, nusinersen backbone)
2. **Filter**: RDKit/nvMolKit Lipinski + BBB + PAINS filtering
3. **Dock**: DiffDock v2.2 docking against SMA targets
4. **Rank**: Score by docking confidence + drug-likeness + novelty
5. **Store**: Save results to screening_results table

**Step 3: Add API endpoint**

```python
@router.post("/screening/virtual", dependencies=[Depends(require_admin_key)])
async def run_virtual_screening(scaffold: str, targets: list[str], n_molecules: int = 100):
    """Run full generative virtual screening pipeline."""
```

**Step 4: Run first campaign** — 100 molecules from 4-AP scaffold against all 7 docked targets

**Step 5: Commit**

```
feat: generative virtual screening pipeline (NVIDIA Blueprint pattern)
```

---

## Task 4: Proteina-Complexa — Protein Binder Design for SMA Targets

**Goal:** Use NVIDIA's Proteina-Complexa model to design protein binders targeting SMN2 protein, SMN-p53 interface, or other SMA-relevant proteins. New therapeutic modality.

**Files:**
- Create: `src/sma_platform/reasoning/protein_binder_design.py`
- Create: `src/sma_platform/api/routes/binder_design.py`
- Modify: `src/sma_platform/api/app.py` — register new router

**Step 1: Research Proteina-Complexa API/usage**

Check if available as NIM or self-hosted only:
- GitHub: `https://github.com/NVIDIA-Digital-Bio/proteina-complexa`
- May require local GPU or Vast.ai instance

**Step 2: Create binder_design module**

If NIM available:
```python
async def design_binder(target_pdb: str, target_chain: str, n_designs: int = 10) -> list[dict]:
    """Design protein binders for a target using Proteina-Complexa."""
```

If self-hosted only: create Vast.ai launch script similar to existing GPU scripts.

**Step 3: Add API routes**

```python
@router.post("/binder/design", dependencies=[Depends(require_admin_key)])
async def design_protein_binder(target: str, n_designs: int = 10):
    """Design protein binders for an SMA target."""
```

**Step 4: Run first design** — binders for SMN2 protein (PDB or AlphaFold structure)

**Step 5: Add "Protein Binder Design" as new Research Direction** in the platform

**Step 6: Commit**

```
feat: Proteina-Complexa protein binder design for SMA targets
```

---

## Task 5: BioNeMo Recipes — ESM-2 Fine-Tuning Setup

**Goal:** Set up BioNeMo Recipes infrastructure for fine-tuning ESM-2 on SMA-specific protein sequences. Preparation for Phase G7.

**Files:**
- Create: `gpu/recipes/esm2_sma_finetune.yaml` — BioNeMo Recipe config
- Create: `gpu/scripts/prepare_sma_protein_data.py` — extract SMA protein sequences for training
- Create: `gpu/scripts/launch_finetune_vastai.sh` — Vast.ai launcher

**Step 1: Install BioNeMo Recipes locally for testing**

```bash
pip install bionemo-recipes
```

**Step 2: Create SMA protein dataset**

Extract all 21 SMA target protein sequences from UniProt, create FASTA file for fine-tuning.

**Step 3: Write BioNeMo Recipe config**

```yaml
model: esm2_650m
task: protein_property_prediction
dataset: /data/sma_proteins.fasta
training:
  epochs: 10
  batch_size: 4
  learning_rate: 1e-5
```

**Step 4: Commit**

```
feat: BioNeMo Recipes setup for ESM-2 fine-tuning on SMA proteins
```

---

## Task 6: nvMolKit — GPU-Accelerated Cheminformatics

**Goal:** Integrate nvMolKit as a faster alternative to RDKit for molecular filtering in the screening pipeline.

**Files:**
- Modify: `src/sma_platform/reasoning/screening_funnel.py` — add nvMolKit backend option
- Create: `gpu/scripts/install_nvmolkit.sh`

**Step 1: Research nvMolKit availability and API**

Check if available as pip package or only via BioNeMo containers.

**Step 2: Add nvMolKit as optional backend**

```python
def filter_molecules(molecules: list[str], backend: str = "rdkit") -> list[dict]:
    if backend == "nvmolkit":
        return _filter_nvmolkit(molecules)
    return _filter_rdkit(molecules)
```

**Step 3: Benchmark** — compare speed on 1000 molecules (RDKit vs nvMolKit)

**Step 4: Commit**

```
feat: add nvMolKit GPU cheminformatics as optional screening backend
```

---

## Task 7: Agentic Drug Discovery Architecture

**Goal:** Extend the Discovery Agent to autonomously orchestrate BioNeMo NIMs — generate molecules, dock them, filter, and rank without manual intervention.

**Files:**
- Modify: `src/sma_platform/agents/__init__.py` or create new agent module
- Create: `src/sma_platform/agents/drug_discovery_agent.py`

**Step 1: Design the agentic workflow**

```
Agent receives: target protein + desired properties
Agent autonomously:
  1. Checks existing docking results for baseline
  2. Generates 100 candidates via GenMol
  3. Filters via Lipinski/BBB
  4. Docks top 50 via DiffDock
  5. Predicts structures via OpenFold3/RNAPro where needed
  6. Ranks results
  7. Stores in DB + creates news post if significant finding
```

**Step 2: Implement DrugDiscoveryAgent class**

**Step 3: Add API endpoint to trigger agent run**

**Step 4: Commit**

```
feat: agentic drug discovery — autonomous BioNeMo NIM orchestration
```

---

## Task 8: Update Roadmap + Documentation

**Files:**
- Modify: `docs/MILESTONES_ROADMAP.md` — add GTC 2026 section + new deliverables
- Modify: `docs/ROADMAP.md` — if exists, update with new phases

**Step 1: Add "Phase 7: NVIDIA GTC 2026 Integration" section to MILESTONES_ROADMAP.md**

With all 7 items as deliverables, linked to the 4 strategic tracks.

**Step 2: Update Track 2 + Track 3 with new deliverables**

Track 2 gains: RNAPro SMN2 structure, Proteina-Complexa binders, BioNeMo Recipes
Track 3 gains: Virtual Screening Blueprint, nvMolKit, AlphaFold complexes

**Step 3: Commit**

```
docs: add NVIDIA GTC 2026 integration to roadmap — 7 new deliverables
```

---

## Implementation Order

| # | Task | Effort | Dependencies |
|---|------|--------|-------------|
| 8 | Update Roadmap | 15min | None |
| 1 | RNAPro NIM | 1h | NVIDIA_API_KEY on moltbot |
| 2 | AlphaFold DB Check | 1h | None |
| 3 | Virtual Screening Blueprint | 3h | Task 1 (GenMol/DiffDock) |
| 4 | Proteina-Complexa | 3h | GPU access (Vast.ai or NIM) |
| 5 | BioNeMo Recipes | 2h | None (config only) |
| 6 | nvMolKit | 2h | Availability check |
| 7 | Agentic Drug Discovery | 4h | Tasks 1-4 |

**Total estimated: ~16h across multiple sessions**
