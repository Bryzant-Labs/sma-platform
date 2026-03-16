"""Master job runner for GPU Phase G1: Foundation.

Three stages:
  1. SpliceAI — score SMN2 exon 7 variants
  2. ESM-2 — compute protein embeddings for SMA targets
  3. Cas-OFFinder — genome-wide off-target scan for CRISPR guides

Each stage is independent — failures in one stage do not block others.
Results are POSTed back to the platform API at sma-research.info.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

try:
    import httpx
except ImportError:
    print("ERROR: httpx required. pip install httpx")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("g1-runner")

# Configuration from environment
SMA_API = os.environ.get("SMA_API", "https://sma-research.info/api/v2")
SMA_ADMIN_KEY = os.environ.get("SMA_ADMIN_KEY", "")
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
REFERENCE_GENOME = DATA_DIR / "GRCh38.fa"


def api_post(client: httpx.Client, path: str, payload: dict) -> dict | None:
    """POST results to the platform API with admin key."""
    url = f"{SMA_API}{path}"
    try:
        resp = client.post(
            url,
            json=payload,
            headers={"X-Admin-Key": SMA_ADMIN_KEY},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("API POST to %s failed: %s", url, e)
        return None


# ---------------------------------------------------------------------------
# Stage 1: SpliceAI
# ---------------------------------------------------------------------------

def run_spliceai(client: httpx.Client) -> dict:
    """Run SpliceAI on SMN2 variants and POST scores to platform."""
    logger.info("=== Stage 1: SpliceAI ===")
    start = time.time()

    vcf_input = DATA_DIR / "smn2_variants.vcf"
    vcf_output = DATA_DIR / "smn2_spliceai_scores.vcf"

    if not vcf_input.exists():
        return {"status": "error", "error": f"Input VCF not found: {vcf_input}"}

    # Run SpliceAI CLI
    ref_arg = str(REFERENCE_GENOME) if REFERENCE_GENOME.exists() else "grch38"
    cmd = [
        "spliceai",
        "-I", str(vcf_input),
        "-O", str(vcf_output),
        "-R", ref_arg,
        "-A", "grch38",
    ]
    logger.info("Running: %s", " ".join(cmd))

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            logger.error("SpliceAI stderr: %s", result.stderr)
            return {"status": "error", "error": f"SpliceAI exit code {result.returncode}: {result.stderr[:500]}"}
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "SpliceAI timed out after 600s"}
    except FileNotFoundError:
        return {"status": "error", "error": "spliceai binary not found — is it installed?"}

    # Parse output VCF
    scores = []
    if vcf_output.exists():
        with open(vcf_output) as f:
            for line in f:
                if line.startswith("#"):
                    continue
                fields = line.strip().split("\t")
                if len(fields) < 8:
                    continue
                chrom, pos, vid, ref, alt = fields[0], fields[1], fields[2], fields[3], fields[4]
                info = fields[7]

                # Parse SpliceAI INFO field: SpliceAI=ALLELE|SYMBOL|DS_AG|DS_AL|DS_DG|DS_DL|...
                ds_ag = ds_al = ds_dg = ds_dl = 0.0
                for part in info.split(";"):
                    if part.startswith("SpliceAI="):
                        vals = part.split("=")[1].split("|")
                        if len(vals) >= 5:
                            try:
                                ds_ag = float(vals[2])
                                ds_al = float(vals[3])
                                ds_dg = float(vals[4])
                                ds_dl = float(vals[5]) if len(vals) > 5 else 0.0
                            except (ValueError, IndexError):
                                pass

                max_delta = max(ds_ag, ds_al, ds_dg, ds_dl)
                scores.append({
                    "chrom": chrom,
                    "pos": int(pos),
                    "ref": ref,
                    "alt": alt,
                    "ds_ag": ds_ag,
                    "ds_al": ds_al,
                    "ds_dg": ds_dg,
                    "ds_dl": ds_dl,
                    "max_delta": max_delta,
                })

    duration = time.time() - start
    logger.info("SpliceAI scored %d variants in %.1fs", len(scores), duration)

    # POST results to platform in batches
    if scores:
        batch_size = 100
        for i in range(0, len(scores), batch_size):
            batch = scores[i : i + batch_size]
            resp = api_post(client, "/ingest/spliceai", {"scores": batch})
            if resp:
                logger.info("  Uploaded batch %d-%d", i, i + len(batch))
            else:
                logger.warning("  Failed to upload batch %d-%d", i, i + len(batch))

    return {
        "status": "ok",
        "variants_scored": len(scores),
        "high_impact": sum(1 for s in scores if s["max_delta"] >= 0.5),
        "duration_secs": round(duration, 1),
    }


# ---------------------------------------------------------------------------
# Stage 2: ESM-2
# ---------------------------------------------------------------------------

def run_esm2(client: httpx.Client) -> dict:
    """Run ESM-2 650M model on SMA target proteins and POST embeddings metadata."""
    logger.info("=== Stage 2: ESM-2 Embeddings ===")
    start = time.time()

    fasta_input = DATA_DIR / "sma_proteins.fasta"
    if not fasta_input.exists():
        return {"status": "error", "error": f"Input FASTA not found: {fasta_input}"}

    # Parse FASTA
    proteins: list[tuple[str, str, str]] = []  # (symbol, uniprot_id, sequence)
    current_header = ""
    current_seq: list[str] = []
    with open(fasta_input) as f:
        for line in f:
            line = line.strip()
            if line.startswith(">"):
                if current_header and current_seq:
                    parts = current_header.split("|")
                    symbol = parts[0]
                    uid = parts[1].split()[0] if len(parts) > 1 else ""
                    proteins.append((symbol, uid, "".join(current_seq)))
                current_header = line[1:]
                current_seq = []
            elif line:
                current_seq.append(line)
    if current_header and current_seq:
        parts = current_header.split("|")
        symbol = parts[0]
        uid = parts[1].split()[0] if len(parts) > 1 else ""
        proteins.append((symbol, uid, "".join(current_seq)))

    if not proteins:
        return {"status": "error", "error": "No proteins found in FASTA"}

    logger.info("Loaded %d proteins from FASTA", len(proteins))

    # Load ESM-2 model
    try:
        import torch
        import esm

        model, alphabet = esm.pretrained.esm2_t33_650M_UR50D()
        batch_converter = alphabet.get_batch_converter()
        model.train(False)

        # Move to GPU if available
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(device)
        logger.info("ESM-2 650M loaded on %s", device)
    except ImportError as e:
        return {"status": "error", "error": f"ESM-2 import failed: {e}"}
    except Exception as e:
        return {"status": "error", "error": f"ESM-2 model load failed: {e}"}

    # Process each protein
    results = []
    for symbol, uniprot_id, seq in proteins:
        try:
            # Truncate very long sequences (ESM-2 max ~1022 tokens)
            truncated = seq[:1022]

            data = [(symbol, truncated)]
            batch_labels, batch_strs, batch_tokens = batch_converter(data)
            batch_tokens = batch_tokens.to(device)

            with torch.no_grad():
                result = model(batch_tokens, repr_layers=[33], return_contacts=False)

            # Mean-pooled embedding from last layer (excluding BOS/EOS)
            token_reps = result["representations"][33]
            seq_len = len(truncated)
            embedding = token_reps[0, 1 : seq_len + 1].mean(0)

            embedding_list = embedding.cpu().numpy().tolist()
            embedding_dim = len(embedding_list)

            results.append({
                "symbol": symbol,
                "uniprot_id": uniprot_id,
                "sequence_length": len(seq),
                "embedding_dim": embedding_dim,
                "model": "esm2_t33_650M_UR50D",
            })

            # Save embedding to file for potential later use
            emb_path = DATA_DIR / f"embeddings_{symbol}_{uniprot_id}.json"
            with open(emb_path, "w") as ef:
                json.dump({
                    "symbol": symbol,
                    "uniprot_id": uniprot_id,
                    "model": "esm2_t33_650M_UR50D",
                    "embedding_dim": embedding_dim,
                    "embedding": embedding_list,
                }, ef)

            logger.info("  %s (%s): %d aa -> %d-dim embedding", symbol, uniprot_id, len(seq), embedding_dim)

        except Exception as e:
            logger.error("  ESM-2 failed for %s: %s", symbol, e)
            results.append({
                "symbol": symbol,
                "uniprot_id": uniprot_id,
                "error": str(e),
            })

    duration = time.time() - start
    logger.info("ESM-2 processed %d proteins in %.1fs", len(results), duration)

    # POST metadata to platform
    successful = [r for r in results if "error" not in r]
    if successful:
        resp = api_post(client, "/ingest/embeddings", {"embeddings": successful})
        if resp:
            logger.info("Uploaded %d embedding records to platform", len(successful))

    return {
        "status": "ok",
        "proteins_processed": len(results),
        "successful": len(successful),
        "failed": len(results) - len(successful),
        "duration_secs": round(duration, 1),
    }


# ---------------------------------------------------------------------------
# Stage 3: Cas-OFFinder
# ---------------------------------------------------------------------------

def run_casoffinder(client: httpx.Client) -> dict:
    """Run Cas-OFFinder off-target scan and POST results."""
    logger.info("=== Stage 3: Cas-OFFinder ===")
    start = time.time()

    guides_input = DATA_DIR / "crispr_guides.txt"
    output_file = DATA_DIR / "casoffinder_results.txt"

    if not guides_input.exists():
        return {"status": "error", "error": f"Guide file not found: {guides_input}"}

    # Run Cas-OFFinder (uses OpenCL for GPU acceleration)
    cmd = [
        "cas-offinder",
        str(guides_input),
        "G",  # Use GPU (OpenCL)
        str(output_file),
    ]
    logger.info("Running: %s", " ".join(cmd))

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        if result.returncode != 0:
            logger.error("Cas-OFFinder stderr: %s", result.stderr)
            return {"status": "error", "error": f"Cas-OFFinder exit code {result.returncode}: {result.stderr[:500]}"}
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Cas-OFFinder timed out after 1800s"}
    except FileNotFoundError:
        return {"status": "error", "error": "cas-offinder binary not found — is it installed?"}

    # Parse tab-delimited output:
    # pattern_seq  chrom  position  matched_seq  strand  mismatches
    offtargets = []
    if output_file.exists():
        with open(output_file) as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 6:
                    offtargets.append({
                        "guide_sequence": parts[0],
                        "chrom": parts[1],
                        "position": int(parts[2]),
                        "matched_sequence": parts[3],
                        "strand": parts[4],
                        "mismatches": int(parts[5]),
                    })

    duration = time.time() - start
    logger.info("Cas-OFFinder found %d off-target sites in %.1fs", len(offtargets), duration)

    # POST results to platform in batches
    if offtargets:
        batch_size = 200
        for i in range(0, len(offtargets), batch_size):
            batch = offtargets[i : i + batch_size]
            resp = api_post(client, "/ingest/offtargets", {"offtargets": batch})
            if resp:
                logger.info("  Uploaded batch %d-%d", i, i + len(batch))
            else:
                logger.warning("  Failed to upload batch %d-%d", i, i + len(batch))

    return {
        "status": "ok",
        "offtargets_found": len(offtargets),
        "unique_guides": len({ot["guide_sequence"] for ot in offtargets}),
        "duration_secs": round(duration, 1),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    logger.info("GPU Phase G1: Foundation — Starting")
    logger.info("API: %s", SMA_API)
    logger.info("Data dir: %s", DATA_DIR)
    logger.info("Admin key: %s", "configured" if SMA_ADMIN_KEY else "NOT SET")

    if not SMA_ADMIN_KEY:
        logger.warning("SMA_ADMIN_KEY not set — results will NOT be uploaded")

    results = {}

    with httpx.Client() as client:
        # Stage 1: SpliceAI
        try:
            results["spliceai"] = run_spliceai(client)
        except Exception as e:
            logger.error("SpliceAI stage crashed: %s", e, exc_info=True)
            results["spliceai"] = {"status": "error", "error": str(e)}

        # Stage 2: ESM-2
        try:
            results["esm2"] = run_esm2(client)
        except Exception as e:
            logger.error("ESM-2 stage crashed: %s", e, exc_info=True)
            results["esm2"] = {"status": "error", "error": str(e)}

        # Stage 3: Cas-OFFinder
        try:
            results["casoffinder"] = run_casoffinder(client)
        except Exception as e:
            logger.error("Cas-OFFinder stage crashed: %s", e, exc_info=True)
            results["casoffinder"] = {"status": "error", "error": str(e)}

        # Report job completion to platform
        api_post(client, "/gpu/jobs", {
            "job_type": "g1-foundation",
            "status": "completed",
            "results": results,
        })

    # Summary
    logger.info("=== G1 Results Summary ===")
    for stage, res in results.items():
        status = res.get("status", "unknown")
        logger.info("  %s: %s", stage, status)
        if status == "error":
            logger.info("    Error: %s", res.get("error", ""))

    all_ok = all(r.get("status") == "ok" for r in results.values())
    logger.info("Overall: %s", "SUCCESS" if all_ok else "PARTIAL (some stages failed)")

    # Write results to file
    results_path = DATA_DIR / "g1_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info("Results written to %s", results_path)

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
