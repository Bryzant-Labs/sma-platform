#!/bin/bash
set -euo pipefail

# Build context is gpu/ (parent dir) so COPY scripts/ works.
# Dockerfile lives in gpu/docker/.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GPU_DIR="$(dirname "$SCRIPT_DIR")"

echo "Building sma-gpu-toolkit..."
echo "  Context: ${GPU_DIR}"
echo "  Dockerfile: ${SCRIPT_DIR}/Dockerfile"

docker build \
  -t sma-gpu-toolkit:latest \
  -f "${SCRIPT_DIR}/Dockerfile" \
  "${GPU_DIR}"

docker tag sma-gpu-toolkit:latest csiicf/sma-gpu-toolkit:latest

echo ""
echo "Done. Image: sma-gpu-toolkit:latest"
echo "Push with: docker push csiicf/sma-gpu-toolkit:latest"
