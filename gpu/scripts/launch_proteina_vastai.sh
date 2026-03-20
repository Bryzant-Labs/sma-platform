#!/bin/bash
# Launch Proteina-Complexa on Vast.ai A100 for protein binder design
# Usage: ./launch_proteina_vastai.sh <target_pdb_file>
#
# Requires: vastai CLI configured with API key
# GitHub: https://github.com/NVIDIA-Digital-Bio/proteina-complexa

set -e

TARGET_PDB="${1:-/data/smn2_alphafold.pdb}"
N_DESIGNS="${2:-10}"

echo "=== Proteina-Complexa Binder Design ==="
echo "Target PDB: $TARGET_PDB"
echo "Designs: $N_DESIGNS"

# Find cheapest A100 instance
echo "Searching for A100 instances..."
vastai search offers 'gpu_name=A100 num_gpus=1 disk_space>=50 inet_down>=200' \
  --order 'dph_total' --limit 5

echo ""
echo "To launch, run:"
echo "  vastai create instance <OFFER_ID> --image nvcr.io/nvidia/clara/proteina-complexa:latest --disk 50"
echo ""
echo "Then SSH in and run:"
echo "  python -m proteina_complexa.design --target $TARGET_PDB --n_designs $N_DESIGNS --output /data/designs/"
