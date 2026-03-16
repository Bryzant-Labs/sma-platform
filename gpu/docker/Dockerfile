# =============================================================================
# SMA GPU Toolkit — Production Dockerfile
# All deps baked in. No pip install on every GPU run.
# =============================================================================
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

LABEL maintainer="Bryzant Labs <info@bryzant.com>"
LABEL description="SMA Research Platform GPU toolkit — structure prediction, embeddings, splicing, docking"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ---------------------------------------------------------------------------
# 1. System packages + Python 3.10 (ships with Ubuntu 22.04 — no PPA needed)
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    wget \
    git \
    gcc \
    g++ \
    build-essential \
    ocl-icd-opencl-dev \
    opencl-headers \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel

# ---------------------------------------------------------------------------
# 2. Cas-OFFinder binary (OpenCL GPU-accelerated CRISPR off-target scanner)
# ---------------------------------------------------------------------------
RUN wget -q https://github.com/nickkoo/cas-offinder/releases/download/v2.4.1/cas-offinder-linux-x86_64 \
    -O /usr/local/bin/cas-offinder \
    && chmod +x /usr/local/bin/cas-offinder \
    || echo "WARN: Cas-OFFinder binary download failed"

# ---------------------------------------------------------------------------
# 3. Scientific stack first (numpy, scipy, pandas before everything else)
# ---------------------------------------------------------------------------
RUN pip install --no-cache-dir \
    "numpy<2" \
    "scipy>=1.11,<1.14" \
    "pandas>=2.0" \
    networkx

# ---------------------------------------------------------------------------
# 4. PyTorch with CUDA 12.4 support (match base image)
# ---------------------------------------------------------------------------
RUN pip install --no-cache-dir \
    "torch>=2.5" \
    --index-url https://download.pytorch.org/whl/cu124

# ---------------------------------------------------------------------------
# 5. Bioinformatics tools (order matters for dependency resolution)
# ---------------------------------------------------------------------------

# Protein language models
RUN pip install --no-cache-dir fair-esm

# Splicing analysis
RUN pip install --no-cache-dir spliceai

# Cheminformatics
RUN pip install --no-cache-dir \
    biopython \
    rdkit-pypi \
    prody

# Molecular dynamics (pdbfixer needs openmm)
RUN pip install --no-cache-dir mdtraj

# Structure prediction (boltz has complex deps — install last)
RUN pip install --no-cache-dir boltz \
    || echo "WARN: boltz install failed — structure prediction disabled"

# Molecular dynamics (OpenMM + PDBFixer via pip — no conda needed!)
RUN pip install --no-cache-dir openmm pdbfixer

# Communication & config
RUN pip install --no-cache-dir httpx pyyaml

# ---------------------------------------------------------------------------
# 8. Application code
# ---------------------------------------------------------------------------
WORKDIR /app
COPY scripts/ /app/scripts/

VOLUME /data

ENV SMA_API="https://sma-research.info/api/v2"
ENV SMA_ADMIN_KEY=""
ENV DATA_DIR="/data"

CMD ["python3", "/app/scripts/run_g1.py"]
