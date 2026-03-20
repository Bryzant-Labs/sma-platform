"""DiffDock Self-Hosted Docking API Server.

Provides a REST API compatible with the SMA Research Platform's
virtual screening pipeline. Supports single and batch docking.

Endpoints:
  GET  /health              — Health check
  POST /dock                — Single ligand docking
  POST /dock/batch          — Batch docking (multiple ligands, one protein)
  POST /molecular-docking/diffdock/generate — NIM-compatible endpoint

Run: python3 server.py
"""

import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

DIFFDOCK_DIR = Path("/opt/DiffDock")
INFERENCE_SCRIPT = DIFFDOCK_DIR / "inference.py"


def run_diffdock(protein_pdb_path: str, ligand_path: str, out_dir: str,
                 num_poses: int = 10, steps: int = 18) -> dict:
    """Run DiffDock inference on a protein-ligand pair."""
    cmd = [
        sys.executable, str(INFERENCE_SCRIPT),
        "--protein_path", protein_pdb_path,
        "--ligand", ligand_path,
        "--out_dir", out_dir,
        "--inference_steps", str(steps),
        "--samples_per_complex", str(num_poses),
        "--batch_size", "10",
        "--no_final_step_noise",
    ]

    logger.info("Running DiffDock: %s", " ".join(cmd[-6:]))
    start = time.time()

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    duration = time.time() - start
    logger.info("DiffDock finished in %.1fs (exit=%d)", duration, result.returncode)

    if result.returncode != 0:
        logger.error("DiffDock stderr: %s", result.stderr[-500:])
        return {"error": result.stderr[-500:], "duration": duration}

    # Parse output poses
    poses = []
    out_path = Path(out_dir)
    for sdf_file in sorted(out_path.glob("rank*_confidence*.sdf")):
        name = sdf_file.stem
        # Extract confidence from filename: rank1_confidence-0.42.sdf
        conf = -999.0
        if "confidence" in name:
            try:
                conf = float(name.split("confidence")[1].replace(".sdf", ""))
            except (ValueError, IndexError):
                pass
        poses.append({
            "file": sdf_file.name,
            "confidence": conf,
            "sdf": sdf_file.read_text(),
        })

    return {
        "poses": poses,
        "num_poses": len(poses),
        "duration": duration,
        "position_confidence": [p["confidence"] for p in poses],
    }


@app.route("/health", methods=["GET"])
def health():
    """Health check."""
    import torch
    gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    return jsonify({
        "status": "healthy",
        "gpu": gpu,
        "diffdock_dir": str(DIFFDOCK_DIR),
        "inference_script": INFERENCE_SCRIPT.exists(),
    })


@app.route("/dock", methods=["POST"])
@app.route("/molecular-docking/diffdock/generate", methods=["POST"])
def dock():
    """Dock ligand(s) to protein. NIM-compatible endpoint.

    JSON body:
      protein: PDB content (string)
      ligand: SDF/SMILES content (string)
      ligand_file_type: "sdf", "smiles", or "txt" (multi-line SMILES)
      num_poses: int (default 10)
      steps: int (default 18)
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    protein_content = data.get("protein", "")
    ligand_content = data.get("ligand", "")
    ligand_type = data.get("ligand_file_type", "sdf")
    num_poses = data.get("num_poses", 10)
    steps = data.get("steps", 18)

    if not protein_content or not ligand_content:
        return jsonify({"error": "protein and ligand fields required"}), 400

    with tempfile.TemporaryDirectory(prefix="diffdock_") as tmpdir:
        # Write protein PDB
        pdb_path = os.path.join(tmpdir, "protein.pdb")
        with open(pdb_path, "w") as f:
            f.write(protein_content)

        # Handle different ligand formats
        if ligand_type == "txt":
            # Multi-line SMILES — batch mode
            smiles_list = [s.strip() for s in ligand_content.strip().split("\n") if s.strip()]
            all_confidences = []
            all_poses = []

            for i, smi in enumerate(smiles_list):
                lig_path = os.path.join(tmpdir, f"ligand_{i}.smi")
                with open(lig_path, "w") as f:
                    f.write(smi)
                out_dir = os.path.join(tmpdir, f"out_{i}")
                os.makedirs(out_dir, exist_ok=True)
                result = run_diffdock(pdb_path, lig_path, out_dir, num_poses, steps)

                confs = result.get("position_confidence", [-999.0])
                best_conf = max(confs) if confs else -999.0
                all_confidences.append(confs)
                all_poses.append(result.get("poses", []))

            return jsonify({
                "position_confidence": all_confidences,
                "num_ligands": len(smiles_list),
                "output": [
                    {"position_confidence": c, "poses": p}
                    for c, p in zip(all_confidences, all_poses)
                ],
            })
        else:
            # Single ligand
            ext = "sdf" if ligand_type == "sdf" else "smi"
            lig_path = os.path.join(tmpdir, f"ligand.{ext}")
            with open(lig_path, "w") as f:
                f.write(ligand_content)

            out_dir = os.path.join(tmpdir, "output")
            os.makedirs(out_dir, exist_ok=True)
            result = run_diffdock(pdb_path, lig_path, out_dir, num_poses, steps)
            return jsonify(result)


@app.route("/dock/batch", methods=["POST"])
def dock_batch():
    """Batch dock multiple SMILES against one protein.

    JSON body:
      protein: PDB content (string)
      smiles: list of SMILES strings
      num_poses: int (default 3)
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    # Redirect to main dock endpoint with txt format
    data["ligand"] = "\n".join(data.get("smiles", []))
    data["ligand_file_type"] = "txt"
    # Re-use the dock endpoint logic
    with app.test_request_context(json=data):
        return dock()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info("Starting DiffDock server on port %d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
