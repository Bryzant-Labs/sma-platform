# Phase 12: NVIDIA GTC 2026 Integration — Complete Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete all remaining GTC 2026 NIM integrations — make every NVIDIA biology tool operational and producing results on the SMA platform.

**Architecture:** Each NIM tool gets: (1) adapter function in `nvidia_nims.py`, (2) API route in `nvidia_nims.py` routes, (3) frontend visualization. The Agentic Drug Discovery agent orchestrates all tools autonomously.

**Tech Stack:** FastAPI, httpx, NVIDIA NIM APIs (DiffDock v2.2, GenMol, OpenFold3, RNAPro), RDKit, ESM-2, asyncpg

**CRITICAL:** NVIDIA API key is NOT available via `source ~/.bashrc` in SSH. Always use: `export NVIDIA_API_KEY=$(grep NVIDIA_API_KEY /home/bryzant/sma-platform/.env | cut -d= -f2)`

---

## Status Assessment (2026-03-20)

| GTC Feature | Code Exists | Tested Live | Data Produced | Remaining |
|-------------|-------------|-------------|---------------|-----------|
| DiffDock v2.2 NIM | YES (adapter + routes) | YES (378+378 dockings running NOW) | YES | Expand to 630 compounds |
| GenMol molecule generation | YES (adapter + routes) | YES (1,051 molecules) | YES | SAFE format fix for larger scaffolds |
| AlphaFold DB complexes | YES (route) | YES (8/8 found) | YES | DONE |
| Virtual Screening Blueprint | YES (GenMol→RDKit→DiffDock) | YES | YES (56 hits) | DONE |
| RNAPro RNA structure | YES (adapter + route stub) | NO | NO | Test + run on SMN2 ISS-N1 |
| Proteina-Complexa binders | YES (binder_design module) | NO | NO | Test + run on 6 SMA targets |
| OpenFold3 structure | YES (adapter stub) | NO | NO | Test + run on SMN1/TP53/CORO1C |
| ESM-2 BioNeMo Recipes | YES (run locally) | YES (15 embeddings) | YES | Fine-tuning config |
| nvMolKit cheminformatics | NO | NO | NO | NVIDIA hasn't released SDK |
| Agentic Drug Discovery | YES (stub) | NO | NO | Wire up orchestration logic |

## Remaining Tasks (5 items)

---

### Task 1: RNAPro — SMN2 Pre-mRNA Structure Prediction

**Files:**
- Modify: `src/sma_platform/ingestion/adapters/nvidia_nims.py` — verify `predict_rna_structure()`
- Modify: `src/sma_platform/api/routes/nvidia_nims.py` — fix `/rna-structure` and `/smn2-rna-structure`
- Test on moltbot via API call

**Step 1: Check the existing RNAPro adapter function**
Read `nvidia_nims.py` adapter — find `predict_rna_structure` or `rnapro` function. Check URL, payload format, response parsing.

**Step 2: Test RNAPro NIM API directly**
```bash
ssh moltbot 'export NVIDIA_API_KEY=$(grep NVIDIA_API_KEY /home/bryzant/sma-platform/.env | cut -d= -f2) && cd /home/bryzant/sma-platform && source venv/bin/activate && python3 -c "
import httpx, os
key = os.environ[\"NVIDIA_API_KEY\"]
# SMN2 ISS-N1 region (intron 7, nusinersen binding site) — 50nt
rna_seq = \"CCAGCAUUAUGAAAGUUGAAUUUUAAUUUGGAUUUUACCAAACAAAUAUGU\"
r = httpx.post(\"https://health.api.nvidia.com/v1/biology/nvidia/rnapro\",
    json={\"sequence\": rna_seq},
    headers={\"Authorization\": \"Bearer \" + key},
    timeout=120)
print(f\"HTTP: {r.status_code}\")
print(r.text[:500])
"'
```

**Step 3: If RNAPro returns 200, run full SMN2 pre-mRNA structure prediction**
- ISS-N1 region (intron 7, pos +10 to +24): nusinersen binding site
- ISS-N2 region (intron 7, pos +100 to +136)
- ESE (exon 7 enhancer, pos 19-27): Tra2-beta binding
- Full exon 7 + flanking introns (~200nt)

**Step 4: Store results in platform + create news post**
POST to `/api/v2/news` with RNAPro results.

**Step 5: Commit**
```bash
git commit -m "feat: RNAPro SMN2 pre-mRNA structure prediction live"
```

---

### Task 2: OpenFold3 — Protein Structure Prediction

**Files:**
- Modify: `src/sma_platform/ingestion/adapters/nvidia_nims.py` — verify `predict_structure()` for OpenFold3
- Modify: `src/sma_platform/api/routes/nvidia_nims.py` — fix `/predict-structure` endpoint

**Step 1: Check existing OpenFold3 adapter**
Read the `predict_structure` function in nvidia_nims.py. Check URL format, payload (sequence vs PDB), response parsing.

**Step 2: Test OpenFold3 NIM API**
```bash
ssh moltbot 'export NVIDIA_API_KEY=$(grep NVIDIA_API_KEY /home/bryzant/sma-platform/.env | cut -d= -f2) && cd /home/bryzant/sma-platform && source venv/bin/activate && python3 -c "
import httpx, os
key = os.environ[\"NVIDIA_API_KEY\"]
# CORO1C WD repeat domain (short, 80 residues)
seq = \"MSFITDFSEDLTFEDIGIIAKDLAGTFHVNPETYLIADLKADPSYAKYRFTLVE\"
r = httpx.post(\"https://health.api.nvidia.com/v1/biology/openfold/openfold3\",
    json={\"sequence\": seq},
    headers={\"Authorization\": \"Bearer \" + key},
    timeout=120)
print(f\"HTTP: {r.status_code}\")
print(r.text[:500])
"'
```

**Step 3: If OpenFold3 works, predict structures for key targets**
- TP53 (Simon's interest) — full 393 residues
- CORO1C (drug target) — 474 residues
- SMN1-p53 complex (if supported)

**Step 4: Compare with AlphaFold DB structures (8 complexes already found)**
Store pLDDT scores, compare confidence with AlphaFold v6.

**Step 5: Commit**

---

### Task 3: Proteina-Complexa — Designed Protein Binders

**Files:**
- Existing: `src/sma_platform/reasoning/protein_binder_design.py` — check what's built
- Existing: `src/sma_platform/api/routes/binder_design.py` — check endpoints
- Existing: `gpu/scripts/launch_binder_vastai.sh` — Vast.ai script

**Step 1: Read existing binder design module**
Check what functions exist, what the API endpoints do, what targets are configured.

**Step 2: Test binder design endpoints on live API**
```bash
curl -s http://localhost:8090/api/v2/binders/targets | python3 -m json.tool | head -30
curl -s http://localhost:8090/api/v2/binders/design/CORO1C -H "x-admin-key: sma-admin-2026" | python3 -m json.tool | head -30
```

**Step 3: If Proteina-Complexa NIM is available, test it**
Note: Proteina-Complexa may be self-hosted only (GTC announcement). If cloud API isn't available, document this and mark as BLOCKED.

**Step 4: Generate binder designs for top 3 targets using existing code**
- CORO1C (most druggable)
- UBA1 (ubiquitin pathway)
- PLS3 (actin modifier)

---

### Task 4: Agentic Drug Discovery — Wire Up Orchestration

**Files:**
- Modify: `src/sma_platform/agents/drug_discovery_agent.py` — complete the `run_discovery_campaign()` function
- Create: `src/sma_platform/api/routes/agent.py` — API endpoint to launch campaigns
- Add route to `app.py`

**Step 1: Read the existing agent stub**
Understand `DiscoveryCampaign`, `AgentAction`, `run_discovery_campaign()`. The stub has the structure but the orchestration logic is placeholder.

**Step 2: Implement `run_discovery_campaign()` to call real NIM APIs**
The function should:
1. Check existing data for the target (convergence score, existing dockings)
2. Call GenMol to generate N molecules (SAFE format)
3. Filter with RDKit (Lipinski, QED > 0.3, BBB)
4. Call DiffDock NIM for each passing compound
5. Rank by confidence score
6. Store results in `screening_results` table
7. If positive hit found → create news post via API
8. Return campaign summary with all AgentActions logged

**Step 3: Create API route**
```python
@router.post("/agent/discover/{target}", dependencies=[Depends(require_admin_key)])
async def launch_discovery(target: str, n_molecules: int = 100):
    campaign = await run_discovery_campaign(target, n_molecules)
    return campaign.to_dict()
```

**Step 4: Test end-to-end on CORO1C**
```bash
curl -X POST "http://localhost:8090/api/v2/agent/discover/CORO1C?n_molecules=20" \
  -H "x-admin-key: sma-admin-2026" | python3 -m json.tool
```

**Step 5: Add frontend section**
Add "Agent" section under Translate dropdown showing campaign history and results.

**Step 6: Commit**

---

### Task 5: Expand DiffDock Batch to Full 630 Compounds

**Files:**
- Modify: `gpu/scripts/run_nim_batch.py` — update `SCREENING_CSV` path and compound loading
- Modify: `gpu/data/screening_library.csv` — already has 630 compounds

**Step 1: Check current batch runner compound loading**
The runner at `gpu/scripts/run_nim_batch.py` line ~200-250 loads compounds. Check if it reads the full CSV or is limited.

**Step 2: Update to load all 630 compounds**
Change the CSV loading to use the full expanded library, not the original 54.

**Step 3: Launch expanded batch**
```bash
ssh moltbot 'export NVIDIA_API_KEY=$(grep NVIDIA_API_KEY /home/bryzant/sma-platform/.env | cut -d= -f2) && cd /home/bryzant/sma-platform && source venv/bin/activate && nohup python3 gpu/scripts/run_nim_batch.py --output-dir gpu/results/batch_630 > logs/nim_batch_630_full.log 2>&1 &'
```
This will run 630 × 7 = 4,410 dockings. At 13/min ≈ 5.5 hours. Cost: $0.

**Step 4: Monitor and ingest results**
After completion, POST results to platform API.

---

## Execution Order

1. **Task 1 (RNAPro)** — quick test, novel data (RNA structure)
2. **Task 2 (OpenFold3)** — quick test, structures for TP53/CORO1C
3. **Task 5 (Expand DiffDock)** — launch in background (5.5 hours)
4. **Task 3 (Proteina-Complexa)** — test existing code
5. **Task 4 (Agentic Agent)** — biggest build, depends on 1-3 working

## Definition of Done

- [ ] RNAPro produces SMN2 ISS-N1 3D structure
- [ ] OpenFold3 produces TP53 + CORO1C structures
- [ ] DiffDock batch covers 630 compounds (4,410 dockings)
- [ ] Protein binder designs exist for CORO1C, UBA1, PLS3
- [ ] Agentic agent runs end-to-end on at least 1 target
- [ ] All results visible on sma-research.info
- [ ] News posts for significant findings
