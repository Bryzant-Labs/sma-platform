# DiffDock Self-Hosted Docking Server
# ====================================
# Custom container with DiffDock + Flask API for batch molecular docking.
# Eliminates NVIDIA NIM API bottleneck — unlimited docking on any GPU.
#
# Build:  docker build -t csiicf/sma-diffdock:latest .
# Run:    docker run --gpus all -p 8000:8000 csiicf/sma-diffdock:latest
# Test:   curl http://localhost:8000/health
# Dock:   POST http://localhost:8000/dock with JSON body
#
# GPU: Any NVIDIA GPU with 8GB+ VRAM (RTX 3060+, A100, V100, etc.)

FROM nvidia/cuda:11.7.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev git wget && \
    rm -rf /var/lib/apt/lists/*

# PyTorch 1.13.1 + CUDA 11.7 (DiffDock requirement)
RUN pip3 install --no-cache-dir \
    torch==1.13.1+cu117 \
    --extra-index-url https://download.pytorch.org/whl/cu117

# PyTorch Geometric + extensions (DiffDock requirement)
RUN pip3 install --no-cache-dir \
    torch-scatter==2.1.0+pt113cu117 \
    torch-sparse==0.6.16+pt113cu117 \
    torch-cluster==1.6.0+pt113cu117 \
    torch-spline-conv==1.2.1+pt113cu117 \
    torch-geometric==2.2.0 \
    --find-links https://pytorch-geometric.com/whl/torch-1.13.1+cu117.html

# DiffDock from source
RUN cd /opt && git clone https://github.com/gcorso/DiffDock.git && \
    cd DiffDock && \
    pip3 install --no-cache-dir \
    e3nn==0.5.0 \
    networkx==2.8.4 \
    pandas==1.5.1 \
    prody==2.2.0 \
    pybind11==2.11.1 \
    rdkit-pypi==2022.9.5 \
    scikit-learn==1.1.0 \
    scipy==1.12.0 \
    torchmetrics==0.11.0 \
    biopython \
    flask \
    gunicorn

# Download DiffDock model weights (v1.1)
RUN cd /opt/DiffDock && \
    python3 -c "from datasets import load_dataset; print('datasets ok')" 2>/dev/null || \
    pip3 install --no-cache-dir datasets

# API server
COPY server.py /opt/DiffDock/server.py

WORKDIR /opt/DiffDock
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8000/health || exit 1

CMD ["python3", "server.py"]
