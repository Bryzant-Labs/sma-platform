#!/bin/bash
# Launch self-hosted DiffDock v2.2 NIM on Vast.ai
# =================================================
# Eliminates NIM API bottleneck — unlimited docking at ~$0.50/hr
# GPU: 1x A100 (16GB+ VRAM minimum)
# Docker: nvcr.io/nim/mit/diffdock:2.1.0
#
# Usage: ./launch_diffdock_vastai.sh
#
# After launch, update DIFFDOCK_URL in .env to point to the Vast.ai instance:
#   DIFFDOCK_URL=http://<vast_ip>:8000/molecular-docking/diffdock/generate

set -e

echo "=== Self-Hosted DiffDock v2.2 NIM ==="
echo "Searching for cheapest A100/L40S GPU..."

# Find cheapest instance with at least 16GB VRAM
vastai search offers 'gpu_ram>=16 num_gpus=1 disk_space>=30 inet_down>=200 reliability>0.95' \
  --order 'dph_total' --limit 5

echo ""
echo "To launch:"
echo "  1. Pick an offer ID from above"
echo "  2. Run: vastai create instance <OFFER_ID> \\"
echo "       --image nvcr.io/nim/mit/diffdock:2.1.0 \\"
echo "       --env '-e NGC_API_KEY=\$NGC_API_KEY -p 8000:8000' \\"
echo "       --disk 30"
echo ""
echo "  3. Wait ~2-3 min for container to start"
echo "  4. Get the instance IP: vastai show instances --raw | jq '.[0].public_ipaddr'"
echo "  5. Test: curl http://<IP>:8000/health"
echo "  6. Update platform: set DIFFDOCK_URL=http://<IP>:8000/molecular-docking/diffdock/generate"
echo ""
echo "Batch docking: Send multi-line SMILES text as ligand input"
echo "  One API call docks ALL molecules against the same receptor"
echo "  ~1000 molecules in ~5 minutes on A100 (vs ~60 min via NIM cloud)"
echo ""
echo "Cost: ~\$0.50-1.00/hr on A100. Destroy when done: vastai destroy instance <ID>"
