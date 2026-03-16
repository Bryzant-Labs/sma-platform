# GPU Batch Job: Validation + Discovery Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Run a combined validation (4-AP preprint data) + discovery (100 compounds x 7 targets) GPU workload, splitting free NIM API docking from paid Vast.ai compute.

**Architecture:** Two parallel tracks -- (A) NIM API docking/generation runs from moltbot at $0 cost, (B) Vast.ai A100 session runs OpenMM MD + Boltz-2 + ESM-2 for ~$12. Both upload results to the platform API. A single run_batch_gpu.py orchestrates the Vast.ai session. A separate run_nim_batch.py runs on moltbot.

**Tech Stack:** DiffDock v2.2 NIM, GenMol NIM, OpenMM, Boltz-2, ESM-2, Vast.ai CLI, httpx, RDKit

---

## Track A: NIM API Batch (moltbot, $0)

### Task 1: Create NIM batch docking script

**Files:**
- Create: `gpu/scripts/run_nim_batch.py`

Script does:
1. Load top 100 compounds (from screening_library.csv + platform API + reference compounds)
2. Download AlphaFold v6 structures for 7 targets (SMN2, SMN1, PLS3, STMN2, NCALD, UBA1, CORO1C)
3. Convert each compound SMILES to SDF via RDKit
4. Run DiffDock v2.2 NIM API: 100 compounds x 7 targets = 700 dockings
5. Run GenMol NIM API: generate 100 novel 4-AP analogs
6. Upload all results to platform API
7. Save results to gpu/results/nim_batch/

Rate limit: ~1 request per 2 seconds to avoid throttling.

**Deploy and start:**
```bash
rsync gpu/scripts/run_nim_batch.py moltbot:/home/bryzant/sma-platform/gpu/scripts/
ssh moltbot "screen -dmS nim-batch bash -c 'cd /home/bryzant/sma-platform && source venv/bin/activate && python3 gpu/scripts/run_nim_batch.py --compounds 100 2>&1 | tee /tmp/nim_batch.log'"
```

---

## Track B: Vast.ai GPU Session (~$12)

### Task 2: Create unified GPU batch script

**Files:**
- Create: `gpu/scripts/run_batch_gpu.py`

Script orchestrates 3 phases sequentially on A100:

**Phase 1: OpenMM MD (4-6 hours)**
- Download SMN2 AlphaFold v6 structure
- Fix with PDBFixer (missing residues, hydrogens)
- Solvate with Amber14 + TIP3P-FB, 0.15M NaCl
- Minimize (5000 steps)
- Equilibrate (1 ns NVT/NPT)
- Production run (100 ns, 2 fs timestep, CUDA platform)
- Analyze: RMSD, RMSF, Rg via MDTraj
- Upload results to platform API

**Phase 2: Boltz-2 structures (1 hour)**
- Predict structures for 5 targets: STMN2, NCALD, PLS3, UBA1, CORO1C
- Download FASTA from UniProt
- Run boltz predict for each
- Save CIF files with confidence scores

**Phase 3: ESM-2 embeddings (5 min)**
- Load ESM-2 t33 650M on CUDA
- Embed all 6 target proteins (1280-dim mean pooling)
- Save .npy files + metadata JSON

---

### Task 3: Launch both tracks in parallel

**Step 1: Deploy scripts**
```bash
rsync gpu/scripts/run_nim_batch.py moltbot:/home/bryzant/sma-platform/gpu/scripts/
rsync gpu/scripts/run_batch_gpu.py moltbot:/home/bryzant/sma-platform/gpu/scripts/
```

**Step 2: Copy batch script into Docker image's scripts dir**
The Docker image already COPYs gpu/scripts/ into /app/scripts/. Need to rebuild or mount.
Alternative: mount scripts via Vast.ai volume.

**Step 3: Start NIM batch on moltbot**
```bash
ssh moltbot "screen -dmS nim-batch bash -c '...'"
```

**Step 4: Launch Vast.ai GPU instance**
```bash
vastai search offers --type on-demand --gpu-name "A100" --disk 50 --ram 40 --order dph --limit 5
vastai create instance <OFFER_ID> \
  --image csiicf/sma-gpu-toolkit:latest \
  --env "SMA_ADMIN_KEY=sma-admin-2026" \
  --env "DATA_DIR=/data" \
  --disk 50 \
  --onstart-cmd "python3 /app/scripts/run_batch_gpu.py 2>&1 | tee /data/batch.log"
```

---

### Task 4: Monitor and collect results

**Monitor NIM batch:** `ssh moltbot "tail -20 /tmp/nim_batch.log"`
**Monitor GPU batch:** `vastai logs <INSTANCE_ID>`
**Check platform:** `curl -s https://sma-research.info/api/v2/stats`

**Collect when done:**
```bash
vastai copy <INSTANCE_ID>:/data/batch_results/ ./gpu/results/batch/
vastai destroy instance <INSTANCE_ID>
scp -r moltbot:/home/bryzant/sma-platform/gpu/results/nim_batch/ ./gpu/results/nim_batch/
```

---

## Expected Output

| Track | Output | Files |
|-------|--------|-------|
| NIM DiffDock | 700 docking scores (100 x 7) | diffdock_v2_batch_results.json |
| NIM GenMol | 100 novel 4-AP analogs | genmol_4ap_analogs.json |
| GPU OpenMM | 100ns trajectory + analysis | md_4ap_smn2/trajectory.dcd, md_results.json |
| GPU Boltz-2 | 5 protein structures | boltz2_complexes/*.cif |
| GPU ESM-2 | 6 protein embeddings | esm2/*_embedding.npy |

## Cost

| Resource | Time | Cost |
|----------|------|------|
| NVIDIA NIM API | ~6 hrs | $0 |
| Vast.ai A100 | ~6 hrs | ~$9-12 |
| **Total** | ~6 hrs parallel | **~$12** |
