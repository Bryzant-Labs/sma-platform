#!/usr/bin/env python3
"""Batch dock Fasudil and ROCK/LIMK pathway compounds against SMA targets.

Run when NVIDIA NIM DiffDock v2.2 is back online:
    python scripts/batch_dock_fasudil.py

Uses the nvidia_nims adapter to dock each compound against each target.
Results are stored in molecule_screenings table with screened_by='diffdock_v2.2_nim'.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Compounds to dock — ROCK/LIMK pathway + controls
COMPOUNDS = [
    {
        "name": "Fasudil",
        "smiles": "O=C(c1ccncc1)N1CCCCCC1",
        "chembl_id": "CHEMBL279969",
        "mechanism": "ROCK inhibitor",
        "note": "Approved Japan/China, Phase 2 ALS, first-in-field for SMA",
    },
    {
        "name": "Y-27632",
        "smiles": "CC(N)C1CCC(C(=O)Nc2ccncc2)CC1",
        "chembl_id": "CHEMBL154236",
        "mechanism": "Selective ROCK inhibitor",
        "note": "Research tool, positive control",
    },
    {
        "name": "Ripasudil",
        "smiles": "O=S(=O)(NCC1CC1)c1ccc2[nH]c3c(c2c1)CNC3",
        "chembl_id": "CHEMBL2105735",
        "mechanism": "ROCK inhibitor",
        "note": "Approved for glaucoma, limited CNS penetration",
    },
    {
        "name": "Riluzole",
        "smiles": "Oc1nc2ccc(OC(F)(F)F)cc2s1",
        "chembl_id": "CHEMBL744",
        "mechanism": "Glutamate inhibitor",
        "note": "Only validated DiffDock hit from previous screening",
    },
    {
        "name": "Risdiplam",
        "smiles": "CC1=NN(C2CCC(OCC3(O)CC3)CC2)C(=O)C1NC1=NC2=CC(F)=C(F)C=C2C(=C1)N1CC(N)CC1",
        "chembl_id": "CHEMBL4297674",
        "mechanism": "SMN2 splicing modifier",
        "note": "Approved SMA therapy, control compound",
    },
]

# Targets to dock against — ROCK/actin pathway relevant
TARGETS = [
    {"symbol": "ROCK2", "uniprot": "O75116", "note": "Primary Fasudil target"},
    {"symbol": "PFN1", "uniprot": "P07737", "note": "SMN interaction partner"},
    {"symbol": "CFL2", "uniprot": "Q9Y281", "note": "Cofilin 2, actin depolymerization"},
    {"symbol": "SMN2", "uniprot": "Q16637", "note": "Primary SMA gene product"},
    {"symbol": "SMN1", "uniprot": "Q16637", "note": "Reference healthy protein"},
    {"symbol": "PLS3", "uniprot": "P13797", "note": "Known SMA modifier"},
    {"symbol": "UBA1", "uniprot": "P22314", "note": "Ubiquitin pathway"},
]


async def run_batch():
    """Run DiffDock v2.2 NIM batch docking."""
    from src.sma_platform.ingestion.adapters.nvidia_nims import (
        check_api_key,
        diffdock_dock_smiles,
    )

    if not check_api_key():
        logger.error("NVIDIA_API_KEY not set. Export it first.")
        return

    total = len(COMPOUNDS) * len(TARGETS)
    logger.info(f"Starting batch: {len(COMPOUNDS)} compounds x {len(TARGETS)} targets = {total} dockings")

    results = []
    for compound in COMPOUNDS:
        for target in TARGETS:
            logger.info(f"Docking {compound['name']} vs {target['symbol']}...")
            try:
                result = await diffdock_dock_smiles(
                    ligand_smiles=compound["smiles"],
                    target_uniprot=target["uniprot"],
                    num_poses=20,  # 20-pose for validation-grade results
                )
                confidence = result.get("top_confidence", result.get("confidence", None))
                results.append({
                    "compound": compound["name"],
                    "target": target["symbol"],
                    "confidence": confidence,
                    "poses": 20,
                    "smiles": compound["smiles"],
                    "chembl_id": compound["chembl_id"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                logger.info(f"  -> confidence: {confidence}")
            except Exception as e:
                logger.error(f"  -> FAILED: {e}")
                results.append({
                    "compound": compound["name"],
                    "target": target["symbol"],
                    "confidence": None,
                    "error": str(e),
                })

    # Save results
    outfile = f"data/fasudil_batch_dock_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(outfile, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {outfile}")

    # Summary
    successful = [r for r in results if r.get("confidence") is not None]
    positive = [r for r in successful if r["confidence"] > 0]
    logger.info(f"\nSummary: {len(successful)}/{total} successful, {len(positive)} positive confidence")
    for r in sorted(successful, key=lambda x: x["confidence"], reverse=True)[:5]:
        logger.info(f"  {r['compound']} -> {r['target']}: {r['confidence']:.3f}")


if __name__ == "__main__":
    asyncio.run(run_batch())
