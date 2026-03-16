# SMA GPU Toolkit — Docker Image

Production-ready Docker image for the SMA Research Platform GPU pipeline. All dependencies are pre-installed — no `pip install` at runtime.

## What's Inside

| Category | Packages |
|---|---|
| **Structure Prediction** | Boltz, PDBFixer, MDTraj, OpenMM (conda) |
| **Protein Embeddings** | ESM-2 (fair-esm), E3nn |
| **Splicing Analysis** | SpliceAI |
| **Graph Neural Networks** | PyTorch Geometric + scatter/sparse/cluster/spline-conv |
| **Cheminformatics** | RDKit, BioPython, ProDy, sPyRMSD |
| **CRISPR Off-Target** | Cas-OFFinder (OpenCL binary) |
| **Scientific Computing** | NumPy, Pandas, SciPy, NetworkX |
| **Infrastructure** | httpx, PyYAML, CUDA 12.4 runtime |

Base image: `nvidia/cuda:12.4.1-devel-ubuntu22.04` with Python 3.11 and Miniconda.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SMA_API` | `https://sma-research.info/api/v2` | Platform API base URL |
| `SMA_ADMIN_KEY` | *(empty)* | Admin API key for uploading results |
| `DATA_DIR` | `/data` | Data directory inside container |

## Build

```bash
cd gpu/docker
chmod +x build.sh
./build.sh
```

This builds `sma-gpu-toolkit:latest` and tags it as `bryzantlabs/sma-gpu-toolkit:latest`.

Push to Docker Hub:

```bash
docker push bryzantlabs/sma-gpu-toolkit:latest
```

## Run Locally (Testing)

Run the default G1 pipeline with local data mounted:

```bash
docker run --gpus all \
  -e SMA_API=https://sma-research.info/api/v2 \
  -e SMA_ADMIN_KEY=your-key-here \
  -v $(pwd)/gpu/data:/data \
  sma-gpu-toolkit:latest
```

Run a specific script:

```bash
docker run --gpus all \
  -v $(pwd)/gpu/data:/data \
  sma-gpu-toolkit:latest \
  python3 /app/scripts/generate_smn2_variants.py -o /data/smn2_variants.vcf
```

Interactive shell for debugging:

```bash
docker run --gpus all -it \
  -v $(pwd)/gpu/data:/data \
  sma-gpu-toolkit:latest \
  /bin/bash
```

CPU-only mode (no `--gpus` flag — ESM-2 and SpliceAI will fall back to CPU):

```bash
docker run \
  -v $(pwd)/gpu/data:/data \
  sma-gpu-toolkit:latest
```

## Use with Vast.ai

1. Push the image to Docker Hub:
   ```bash
   docker push bryzantlabs/sma-gpu-toolkit:latest
   ```

2. On Vast.ai, create an instance with:
   - **Docker Image**: `bryzantlabs/sma-gpu-toolkit:latest`
   - **GPU**: A100 or similar (40GB+ VRAM recommended)
   - **Disk**: 50GB+

3. Set environment variables in the Vast.ai instance config:
   ```
   SMA_API=https://sma-research.info/api/v2
   SMA_ADMIN_KEY=your-admin-key
   ```

4. The container starts the G1 pipeline automatically. To run a different script, override the command in the Vast.ai launch config.

5. Mount `/data` as a persistent volume if you want results to survive container restarts.

## Use with dstack

See `gpu/jobs/g1-foundation.dstack.yml` for the job definition. Run with:

```bash
dstack run . -f gpu/jobs/g1-foundation.dstack.yml
```

## Pipeline Stages (G1)

The default `run_g1.py` runs three independent stages:

1. **SpliceAI** — Score all SMN2 exon 7 SNVs for splice impact
2. **ESM-2** — Compute protein embeddings for SMA targets (650M model)
3. **Cas-OFFinder** — Genome-wide CRISPR off-target scan (OpenCL GPU)

Results are POSTed to the platform API and saved to `/data/`.
