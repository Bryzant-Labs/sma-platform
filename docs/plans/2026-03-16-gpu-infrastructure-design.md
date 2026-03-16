# GPU Compute Infrastructure — Design Document

**Date:** 2026-03-16
**Status:** Approved
**Goal:** Build a professional-grade GPU compute pipeline for AI-driven SMA drug discovery — the first of its kind.
**Toolchain Inventory:** See `docs/research/GPU_TOOLCHAIN_INVENTORY.md` for full tool catalog (40+ tools from GitHub/HuggingFace research).

---

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| GPU Router | **dstack** (7.5k★) | Built-in GPUhunt price scanner across 14+ providers. Lighter than SkyPilot. Auto-provisions cheapest GPU, runs job, terminates. |
| Primary GPU Provider | **Vast.ai** | Marketplace model = overcapacity pricing ($0.78-1.50/hr A100). Per-second billing. Perfect for burst jobs. |
| Backup Provider | **RunPod** | More reliable than Vast.ai ($1.19/hr A100). Fallback when marketplace availability is low. |
| Protein Structure | **Boltz-1/2** (MIT) | Open training code (can fine-tune on SMA). AF3-level accuracy. Boltz-2 predicts binding affinity jointly. 20 sec/structure on A100. |
| Pipeline Orchestrator | **Nextflow** (2.7k★) | Bioinformatics industry standard. 145+ nf-core pipelines. Checkpointing, retry, multi-executor support. |
| Container Strategy | **BioContainers** + custom | Pre-built Docker images for SpliceAI, ESM-2, DiffDock, OpenMM. Custom layer for SMA-specific config. |
| Molecular Docking | **DiffDock-L** | 100x faster than traditional docking. Diffusion-based. 38% top-1 success rate (RMSD<2Å). |
| CRISPR Off-Target | **Cas-OFFinder** (GPU) | OpenCL-based genome-wide scan. <1 min per guide on A100. Uses hg38.2bit (797 MB). |
| Protein Embeddings | **ESM-2 650M** | Meta's protein language model. 30-60 sec for 21 proteins. Enables mutation effect prediction. |
| Molecular Dynamics | **OpenMM 8.0** | CUDA-accelerated. 250 ns/day on A100. Industry standard for biomolecular simulation. |
| Splice Prediction | **SpliceAI** (Illumina) | Gold standard. GPU-accelerated. 762 SMN2 variants in ~3 minutes. |
| Billing Model | **On-demand burst** | Pay only for compute used. No monthly commitment. Scale up when validated. |

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│          SMA Research Platform (sma-research.info)    │
│          FastAPI + PostgreSQL + 174 endpoints         │
│                                                      │
│  Job Queue: POST /api/v2/gpu/submit                  │
│  Results:   POST /api/v2/gpu/results                 │
└────────────────────┬─────────────────────────────────┘
                     │ triggers via API
                     ▼
┌──────────────────────────────────────────────────────┐
│              dstack (GPU Router)                     │
│              + GPUhunt Price Scanner                 │
│                                                      │
│  Scans: Vast.ai, RunPod, Lambda, AWS, GCP, Azure,  │
│         CoreWeave, TensorDock, Vultr, FluidStack... │
│  Picks: cheapest available A100/H100                │
│  Manages: provision → run → terminate               │
└────────────────────┬─────────────────────────────────┘
                     │ provisions cheapest GPU
                     ▼
┌──────────────────────────────────────────────────────┐
│              Nextflow Pipeline                       │
│              (Bioinformatics Orchestrator)            │
│                                                      │
│  Checkpointing, retry, parallel execution           │
│  BioContainers for tool isolation                   │
└──┬──────┬──────┬──────┬──────┬──────┬───────────────┘
   │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼
┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐
│Splice││ESM-2 ││Cas-  ││Diff  ││Boltz ││Open  │
│AI    ││650M  ││OFF   ││Dock-L││1/2   ││MM    │
│      ││      ││finder││      ││      ││      │
│hg38  ││21    ││hg38  ││100+  ││21    ││6 sims│
│762   ││prots ││.2bit ││cpds  ││vars  ││100ns │
│vars  ││      ││      ││×7    ││      ││each  │
└──┬───┘└──┬───┘└──┬───┘└──┬───┘└──┬───┘└──┬───┘
   │       │       │       │       │       │
   └───────┴───────┴───────┴───────┴───────┘
                     │ results JSON
                     ▼
┌──────────────────────────────────────────────────────┐
│              Results Ingestion                        │
│                                                      │
│  • SpliceAI scores → splice_variants table           │
│  • ESM-2 embeddings → target metadata (JSONB)       │
│  • Off-targets → CRISPR safety annotations           │
│  • Docking poses → drug_candidates + scores          │
│  • Structures → AlphaFold metadata enrichment        │
│  • MD trajectories → binding mode analysis           │
│                                                      │
│  Auto-triggers: re-scoring, hypothesis regeneration  │
└──────────────────────────────────────────────────────┘
```

---

## Data Dependencies

| Data | Source | Size | Download Once |
|------|--------|------|---------------|
| hg38.2bit | UCSC Genome Browser | 797 MB | Yes (persistent volume) |
| GRCh38 FASTA | GENCODE/NCBI | ~3 GB | Yes |
| ColabFold DB | ColabFold server | 20-30 GB (or use API) | Optional |
| ESM-2 650M weights | HuggingFace/Meta | ~2.6 GB | Yes |
| SpliceAI model | Illumina GitHub | ~1 GB | Yes |
| DiffDock-L weights | GitHub/NVIDIA NIM | ~18 GB | Yes |
| Boltz-1/2 weights | MIT/GitHub | TBD | Yes |

**Strategy:** Store model weights + reference genomes on a persistent Vast.ai volume (~$0.10/GB/month). Avoids re-downloading on each job.

---

## Phase Plan

### Phase G1: Foundation (Day 1-2, ~$1)
- [ ] Set up dstack locally (pip install dstack)
- [ ] Configure Vast.ai + RunPod as backends
- [ ] Build base Docker image with SpliceAI + ESM-2 + Cas-OFFinder
- [ ] Download hg38.2bit + GRCh38 FASTA
- [ ] Run SpliceAI on 762 SMN2 variants (~3 min, ~$0.05)
- [ ] Run ESM-2 embeddings for 21 target proteins (~1 min, ~$0.02)
- [ ] Run Cas-OFFinder on all CRISPR guides (~5 min, ~$0.08)
- [ ] POST results back to sma-research.info
- [ ] Validate: scores visible in frontend

### Phase G2: Molecular Docking (Day 3-4, ~$10)
- [ ] Add DiffDock-L to Docker image
- [ ] Prepare PDB structures (7 AlphaFold + Boltz-1 variants)
- [ ] Prepare ligand library (top 100 drug candidates from screening)
- [ ] Batch dock: 100 compounds × 7 binding pockets = 700 docking jobs
- [ ] Parse poses, rank by confidence
- [ ] Ingest top binding poses into platform

### Phase G3: Protein Structures (Day 5, ~$6)
- [ ] Set up Boltz-1 (MIT, open weights)
- [ ] Predict structures for SMN protein variants (not just wild-type)
- [ ] Compare with AlphaFold DB structures (pLDDT validation)
- [ ] Generate mutant structures for key SMN2 splice variants
- [ ] Ingest structures + confidence scores into platform

### Phase G4: Molecular Dynamics (Week 2, ~$45)
- [ ] Set up OpenMM 8.0 with CUDA
- [ ] Run 6 priority MD simulations (from codebase md_generator.py):
  1. SMN protein stability
  2. Risdiplam binding to SMN2 pre-mRNA
  3. Nusinersen-ISS-N1 interaction
  4. PLS3 actin-binding dynamics
  5. NCALD calcium-binding conformational change
  6. UBA1 ubiquitin pathway dynamics
- [ ] Each: 100ns production run, ~9.6 GPU-hours
- [ ] Extract: binding free energy, RMSD, contact maps
- [ ] Ingest trajectory analysis into platform

### Phase G5: Scale Screening (Week 3-4, ~$100-500)
- [ ] Build Nextflow pipeline for automated screening
- [ ] Source compound libraries (ZINC20, ChEMBL, Enamine REAL)
- [ ] Screen 10K compounds against SMN2 splice site
- [ ] Scale to 100K if top hits look promising
- [ ] Rank by: docking score + drug-likeness + BBB permeability
- [ ] Generate novel SMA drug candidate shortlist

### Phase G6: Generative Drug Design (Month 2, ~$50)
- [ ] BoltzDesign1 — design protein binders for SMN targets
- [ ] ProteinMPNN — design peptides targeting NMJ
- [ ] Diffusion-based molecule generation (DiffGui/DrugDiff)
- [ ] Optimize for: SMN2 exon 7 inclusion + CNS penetration + drug-likeness

### Phase G7: Custom SMA Models (Month 2, ~$100)
- [ ] Fine-tune ESM-2 on SMA-specific protein sequences
- [ ] Train custom splice predictor (SpliceAI features + our 24k claims)
- [ ] Train drug-target interaction model on our screening data
- [ ] Publish models on HuggingFace (SMAResearch org)

---

## Cost Projections

| Scenario | Monthly Cost | What You Get |
|----------|-------------|-------------|
| Testing (G1-G2) | ~$15 | Validated pipeline, splice scores, docking results |
| Active Research (G3-G4) | ~$50-100 | Protein structures, MD simulations, binding analysis |
| Discovery Engine (G5-G7) | ~$200-500 | Large-scale screening, generative design, custom models |
| Scaled Discovery | ~$500-2,000 | 1M compounds/night, continuous model training |

---

## Docker Container Specification

```dockerfile
# sma-gpu-toolkit
FROM nvidia/cuda:12.1-devel-ubuntu22.04

# Core bioinformatics
RUN pip install spliceai tensorflow  # SpliceAI
RUN pip install fair-esm             # ESM-2
RUN pip install diffdock             # DiffDock-L
RUN pip install openmm               # Molecular dynamics
RUN pip install colabfold            # Protein folding

# Reference data (persistent volume mount)
# /data/hg38.2bit (797 MB)
# /data/GRCh38.fa (3 GB)
# /data/esm2_650M/ (2.6 GB)

# SMA job runner
COPY sma_gpu_runner/ /app/
# Pulls job config from platform API
# Runs computation
# POSTs results back to sma-research.info
```

---

## Integration with SMA Platform

### New API Endpoints Needed
```
POST /api/v2/gpu/submit          — Submit GPU job (admin)
GET  /api/v2/gpu/jobs             — List running/completed jobs
GET  /api/v2/gpu/jobs/{id}        — Job status + results
POST /api/v2/gpu/results          — Receive results from GPU worker

POST /api/v2/ingest/spliceai      — Import SpliceAI delta scores
POST /api/v2/ingest/embeddings    — Import ESM-2 protein embeddings
POST /api/v2/ingest/offtargets    — Import Cas-OFFinder results
POST /api/v2/ingest/docking       — Import DiffDock poses + scores
POST /api/v2/ingest/structures    — Import Boltz-1/2 structures
POST /api/v2/ingest/md-results    — Import MD trajectory analysis
```

### New Database Tables
```sql
-- GPU job tracking
CREATE TABLE gpu_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type TEXT NOT NULL,  -- spliceai, diffdock, boltz, openm, esm2, casoffinder
    status TEXT DEFAULT 'queued',
    config JSONB NOT NULL,
    results JSONB DEFAULT '{}',
    provider TEXT,           -- vast.ai, runpod, lambda, etc.
    gpu_type TEXT,           -- A100, H100
    cost_usd NUMERIC,
    gpu_hours NUMERIC,
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Docking results
CREATE TABLE docking_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    compound_name TEXT NOT NULL,
    target_symbol TEXT NOT NULL,
    pocket TEXT,
    confidence NUMERIC(4,3),
    binding_energy NUMERIC,
    rmsd NUMERIC,
    pose_data JSONB,         -- 3D coordinates
    method TEXT DEFAULT 'diffdock-l',
    gpu_job_id UUID REFERENCES gpu_jobs(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- MD simulation results
CREATE TABLE md_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    simulation_key TEXT NOT NULL,
    target_symbol TEXT NOT NULL,
    drug_name TEXT,
    duration_ns NUMERIC,
    avg_rmsd NUMERIC,
    binding_free_energy NUMERIC,
    contact_map JSONB,
    trajectory_summary JSONB,
    gpu_job_id UUID REFERENCES gpu_jobs(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Success Metrics

1. **Phase G1 validates in < 2 hours** — SpliceAI scores visible in frontend
2. **DiffDock identifies ≥5 compounds** with binding confidence >0.7 against SMN2
3. **Boltz-1 structures** match AlphaFold DB within 1Å RMSD (validation)
4. **MD simulations reveal** at least 1 binding mode not predicted by static docking
5. **Virtual screening** produces novel candidates not in existing drug databases
6. **Custom SMA models** outperform generic models on SMA-specific benchmarks

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Vast.ai GPU unavailable | dstack auto-falls back to RunPod/Lambda/AWS |
| Job interrupted (spot instance) | Nextflow checkpointing — resume from last stage |
| Model weights too large | Persistent volume on Vast.ai ($0.10/GB/mo) |
| Results don't integrate cleanly | Standard JSON schema for all GPU results |
| Costs spiral | dstack spending limits + per-job cost tracking |

---

## Reference: Tool Inventory

| Tool | Version | License | GPU Req | Docker Image |
|------|---------|---------|---------|-------------|
| SpliceAI | 1.3.1 | Apache 2.0 | Optional (faster) | cmgantwerpen/spliceai_v1.3 |
| ESM-2 | 650M | MIT | 2.6 GB VRAM | fair-esm (pip) |
| Cas-OFFinder | 2.4.1 | GPL-3.0 | OpenCL | Custom build |
| DiffDock-L | 2.1.0 | MIT | 16 GB VRAM | externelly/diffdock |
| Boltz-1 | 1.0 | MIT | 80 GB VRAM | genomenexus/boltz1 |
| OpenMM | 8.0 | MIT | CUDA 12.1+ | Conda |
| ColabFold | 1.5 | MIT | 16 GB VRAM | localcolabfold |
| ProteinMPNN | 1.0 | MIT | 8 GB VRAM | CyrusBiotechnology |
| dstack | 0.18+ | MPL-2.0 | N/A (orchestrator) | pip install |
| Nextflow | 24.x | Apache 2.0 | N/A (orchestrator) | Conda/Docker |

---

*This infrastructure makes the SMA Research Platform the first AI-driven virtual screening system specifically targeting SMA drug discovery. No published computational campaign of this scope exists for SMN2-targeting compounds.*
