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

# ---------------------------------------------------------------------------
# 6. Communication
# ---------------------------------------------------------------------------
RUN pip install --no-cache-dir httpx pyyaml

# ---------------------------------------------------------------------------
# 7. OpenMM via conda (installed AFTER pip packages to avoid PATH conflicts)
#    Conda python will be available as /opt/conda/bin/python3
#    System python (with all pip packages) stays as /usr/bin/python3
# ---------------------------------------------------------------------------
ENV CONDA_DIR=/opt/conda
RUN wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p ${CONDA_DIR} \
    && rm /tmp/miniconda.sh

# Install OpenMM in conda env but DON'T override system python
RUN ${CONDA_DIR}/bin/conda install -y -c conda-forge openmm pdbfixer \
    && ${CONDA_DIR}/bin/pip install --no-cache-dir numpy scipy pandas mdtraj httpx \
    && ${CONDA_DIR}/bin/conda clean -afy \
    || echo "WARN: OpenMM install failed — MD simulations disabled"

# Keep system Python 3.10 as default (conda PATH NOT prepended)
# OpenMM available via: /opt/conda/bin/python3 -c "import openmm"

# Symlink openmm + pdbfixer from conda into system Python so both pythons can import them
RUN ln -sf /opt/conda/lib/python3.*/site-packages/openmm* /usr/local/lib/python3.10/dist-packages/ || true
RUN ln -sf /opt/conda/lib/python3.*/site-packages/pdbfixer* /usr/local/lib/python3.10/dist-packages/ || true
RUN ln -sf /opt/conda/lib/python3.*/site-packages/OpenMM* /usr/local/lib/python3.10/dist-packages/ || true

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
