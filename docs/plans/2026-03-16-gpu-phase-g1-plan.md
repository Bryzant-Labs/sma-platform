# GPU Phase G1: Foundation — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Set up GPU infrastructure (dstack + Vast.ai), build Docker toolkit, run SpliceAI + ESM-2 + SpliceTransformer + Cas-OFFinder on SMN2 targets, ingest results into platform.

**Architecture:** dstack server runs locally on WSL, routes GPU jobs to cheapest A100 across Vast.ai (primary) + RunPod (backup). Jobs run in Docker containers, pull config from platform API, execute GPU computation, POST results back. New DB tables store GPU job state + results.

**Tech Stack:** dstack, Docker, Vast.ai API, SpliceAI (TensorFlow/GPU), ESM-2 (PyTorch), Cas-OFFinder (OpenCL), FastAPI endpoints, PostgreSQL.

**Prerequisites:**
- Vast.ai account with API key (user must create at https://cloud.vast.ai/)
- RunPod account with API key (backup, at https://runpod.io/)
- Docker installed locally (for building images)

---

## Task 1: Account Setup (Manual — User Action Required)

**Step 1:** Create Vast.ai account at https://cloud.vast.ai/ — add $25 credit, copy API key from Account page.

**Step 2:** Create RunPod account at https://runpod.io/ — add $10 credit, copy API key from Settings > API Keys.

**Step 3:** Store API keys:
```bash
echo 'export VASTAI_API_KEY="your_key"' >> ~/.bashrc
echo 'export RUNPOD_API_KEY="your_key"' >> ~/.bashrc
source ~/.bashrc
```

---

## Task 2: Install dstack + Configure Backends

**Step 1:** Install dstack
```bash
pip install dstack
```

**Step 2:** Create config at `~/.dstack/server/config.yml`:
```yaml
projects:
  - name: sma
    backends:
      - type: vastai
        creds:
          type: api_key
          api_key: ${VASTAI_API_KEY}
      - type: runpod
        creds:
          type: api_key
          api_key: ${RUNPOD_API_KEY}
        community_cloud: true
```

**Step 3:** Start server + verify:
```bash
dstack server &
dstack init
dstack offer --gpu A100
```

---

## Task 3: Download Reference Genomes

```bash
mkdir -p gpu/data
wget -O gpu/data/hg38.2bit https://hgdownload.cse.ucsc.edu/goldenpath/hg38/bigZips/hg38.2bit
wget -O gpu/data/GRCh38.fa.gz https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_44/GRCh38.primary_assembly.genome.fa.gz
gunzip gpu/data/GRCh38.fa.gz
```

---

## Task 4: Generate Input Files

**Files to create:** `gpu/scripts/generate_inputs.py`

Script generates:
- `gpu/data/smn2_variants.vcf` — All SNVs in SMN2 exon 7 region (254 bp, ~762 variants)
- `gpu/data/sma_proteins.fasta` — Protein sequences for 21 targets (fetched from UniProt)
- `gpu/data/crispr_guides.txt` — CRISPR guides from platform API (Cas-OFFinder format)

---

## Task 5: Build Docker Image

**Files:**
- `gpu/docker/Dockerfile` — CUDA 12.1 base + SpliceAI + ESM-2 + Cas-OFFinder
- `gpu/docker/requirements.txt` — Python deps
- `gpu/scripts/run_g1.py` — Master job runner (3 stages)

The runner:
1. Runs SpliceAI on SMN2 variants (~3 min)
2. Runs ESM-2 embeddings on 21 proteins (~1 min)
3. Runs Cas-OFFinder off-target scan (~5 min)
4. POSTs all results back to sma-research.info

---

## Task 6: Create Platform API Endpoints

**File:** `src/sma_platform/api/routes/gpu.py`

Endpoints:
- `POST /gpu/jobs` — Submit GPU job (admin)
- `GET /gpu/jobs` — List jobs
- `GET /gpu/jobs/{id}` — Job status
- `POST /ingest/spliceai` — Import SpliceAI scores (admin)
- `POST /ingest/embeddings` — Import ESM-2 data (admin)
- `POST /ingest/offtargets` — Import Cas-OFFinder results (admin)

---

## Task 7: Create Database Tables

**New tables:**
- `gpu_jobs` — Job tracking (type, status, provider, cost, timestamps)
- `splice_scores` — SpliceAI delta scores (chrom, pos, ref, alt, ds_ag/al/dg/dl, max_delta)
- `crispr_offtargets` — Off-target sites (guide, chrom, position, mismatches)

---

## Task 8: Deploy to Moltbot

1. Create tables on PostgreSQL
2. rsync gpu.py route + updated app.py
3. Restart PM2
4. Verify: `curl https://sma-research.info/api/v2/gpu/jobs`

---

## Task 9: Submit GPU Job via dstack

```bash
dstack apply -f gpu/jobs/g1-foundation.dstack.yml
dstack logs sma-g1-foundation --follow
```

---

## Task 10: Verify Results

- Check `splice_scores` table has 700+ scored variants
- Check target metadata has ESM-2 embeddings
- Check `crispr_offtargets` has off-target sites
- Total cost should be under $2

---

## Success Criteria

1. SpliceAI scores for 700+ SMN2 variants ingested
2. ESM-2 embeddings for 15+ proteins stored
3. Cas-OFFinder results for CRISPR guides ingested
4. Total GPU time < 30 minutes, cost < $2
5. All results accessible via API
