#!/bin/bash
# Build and push DiffDock self-hosted Docker image
# Usage: ./build.sh
set -e

IMAGE="csiicf/sma-diffdock:latest"

echo "=== Building DiffDock Docker Image ==="
echo "Image: $IMAGE"
echo ""

docker build -t "$IMAGE" .

echo ""
echo "=== Build complete ==="
echo "Test locally: docker run --gpus all -p 8000:8000 $IMAGE"
echo "Push: docker push $IMAGE"
echo ""

read -p "Push to Docker Hub? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker push "$IMAGE"
    echo "Pushed to Docker Hub: $IMAGE"
fi
