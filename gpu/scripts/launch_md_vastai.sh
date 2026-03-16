#!/bin/bash
set -euo pipefail

# =============================================================================
# Launch OpenMM MD simulation on Vast.ai
# Requires: vastai CLI, Docker image pushed to Docker Hub
# =============================================================================

IMAGE="csiicf/sma-gpu-toolkit:latest"
DURATION_NS="${1:-100}"
SMA_ADMIN_KEY="${SMA_ADMIN_KEY:-sma-admin-2026}"

echo "=== OpenMM MD: 4-AP + SMN2 on Vast.ai ==="
echo "  Duration: ${DURATION_NS} ns"
echo "  Image: ${IMAGE}"
echo ""

# 1. Find cheapest A100 instance
echo "[1/4] Searching for GPU instances..."
OFFER=$(vastai search offers \
    --type on-demand \
    --gpu-name "A100" \
    --disk 50 \
    --ram 40 \
    --order dph \
    --limit 5 \
    --raw 2>/dev/null | head -1)

if [ -z "$OFFER" ]; then
    echo "  No A100 available. Trying A6000..."
    OFFER=$(vastai search offers \
        --type on-demand \
        --gpu-name "RTX A6000" \
        --disk 50 \
        --ram 40 \
        --order dph \
        --limit 5 \
        --raw 2>/dev/null | head -1)
fi

OFFER_ID=$(echo "$OFFER" | awk '{print $1}')
DPH=$(echo "$OFFER" | awk '{print $6}')
echo "  Best offer: ID=${OFFER_ID}, \$${DPH}/hr"

# 2. Create instance
echo ""
echo "[2/4] Creating instance..."
INSTANCE_ID=$(vastai create instance "$OFFER_ID" \
    --image "$IMAGE" \
    --env "SMA_ADMIN_KEY=${SMA_ADMIN_KEY}" \
    --env "DATA_DIR=/data" \
    --disk 50 \
    --onstart-cmd "python3 /app/scripts/run_md_4ap_smn2.py --duration_ns ${DURATION_NS} --output_dir /data/md_results 2>&1 | tee /data/md.log" \
    --raw 2>/dev/null | grep -o '[0-9]*')

echo "  Instance ID: ${INSTANCE_ID}"

# 3. Wait for instance to start
echo ""
echo "[3/4] Waiting for instance to start..."
for i in $(seq 1 30); do
    STATUS=$(vastai show instance "$INSTANCE_ID" --raw 2>/dev/null | awk '{print $3}' || echo "unknown")
    echo "  Status: ${STATUS} (attempt ${i}/30)"
    if [ "$STATUS" = "running" ]; then
        break
    fi
    sleep 10
done

# 4. Monitor
echo ""
echo "[4/4] Instance running. Monitor with:"
echo "  vastai show instance ${INSTANCE_ID}"
echo "  vastai logs ${INSTANCE_ID}"
echo "  vastai ssh-url ${INSTANCE_ID}"
echo ""
echo "Expected runtime: ~4-6 hours for ${DURATION_NS} ns on A100"
echo "Expected cost: ~\$5-8"
echo ""
echo "To download results when complete:"
echo "  vastai copy ${INSTANCE_ID}:/data/md_results/ ./gpu/results/md/"
echo ""
echo "To destroy instance after completion:"
echo "  vastai destroy instance ${INSTANCE_ID}"
