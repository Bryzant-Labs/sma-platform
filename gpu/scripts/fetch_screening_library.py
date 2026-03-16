"""Fetch a large compound library for scale DiffDock screening.

Sources:
1. Our platform's existing screened candidates (678 compounds)
2. ChEMBL compounds with SMA-related bioactivity
3. FDA-approved drugs for repurposing screen
"""
import argparse
import csv
import json
import logging
import time

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API = "https://sma-research.info/api/v2"


def fetch_platform_candidates(limit: int = 500) -> list[dict]:
    """Fetch compounds from our screening pipeline."""
    compounds = []
    r = httpx.get(f"{API}/screen/candidates?limit={limit}", timeout=30)
    for c in r.json().get("candidates", []):
        if c.get("smiles"):
            compounds.append({
                "name": c.get("chembl_id", f"compound_{len(compounds)}"),
                "smiles": c["smiles"],
                "source": "platform_screening",
            })
    logger.info("Platform: %d compounds with SMILES", len(compounds))
    return compounds


def fetch_chembl_sma_compounds(max_compounds: int = 2000) -> list[dict]:
    """Fetch SMA-related compounds from ChEMBL API."""
    compounds = []
    # ChEMBL targets related to SMA
    targets = {
        "CHEMBL2146302": "SMN1",  # Survival motor neuron protein 1
        "CHEMBL4523289": "SMN2",  # Survival motor neuron protein 2
    }

    for chembl_target, name in targets.items():
        try:
            url = (
                f"https://www.ebi.ac.uk/chembl/api/data/activity.json"
                f"?target_chembl_id={chembl_target}"
                f"&limit=500"
                f"&offset=0"
            )
            r = httpx.get(url, timeout=30)
            if r.status_code == 200:
                data = r.json()
                for act in data.get("activities", []):
                    smiles = act.get("canonical_smiles")
                    cid = act.get("molecule_chembl_id")
                    if smiles and cid:
                        compounds.append({
                            "name": cid,
                            "smiles": smiles,
                            "source": f"chembl_{name}",
                        })
            logger.info("ChEMBL %s (%s): %d activities", chembl_target, name, len(data.get("activities", [])))
            time.sleep(1)  # Rate limit
        except Exception as e:
            logger.error("ChEMBL fetch failed for %s: %s", chembl_target, e)

    # Also fetch motor neuron disease compounds
    try:
        url = (
            "https://www.ebi.ac.uk/chembl/api/data/activity.json"
            "?target_chembl_id=CHEMBL612545"  # Motor neuron related
            "&limit=500"
        )
        r = httpx.get(url, timeout=30)
        if r.status_code == 200:
            for act in r.json().get("activities", []):
                smiles = act.get("canonical_smiles")
                cid = act.get("molecule_chembl_id")
                if smiles and cid:
                    compounds.append({
                        "name": cid,
                        "smiles": smiles,
                        "source": "chembl_motor_neuron",
                    })
    except Exception as e:
        logger.error("ChEMBL motor neuron fetch failed: %s", e)

    logger.info("ChEMBL total: %d compounds", len(compounds))
    return compounds[:max_compounds]


def fetch_fda_approved(limit: int = 500) -> list[dict]:
    """Fetch FDA-approved drugs for repurposing screen."""
    compounds = []
    try:
        url = (
            "https://www.ebi.ac.uk/chembl/api/data/molecule.json"
            "?max_phase=4"  # Approved drugs
            "&molecule_type=Small%20molecule"
            "&limit=500"
        )
        r = httpx.get(url, timeout=30)
        if r.status_code == 200:
            for mol in r.json().get("molecules", []):
                structs = mol.get("molecule_structures") or {}
                smiles = structs.get("canonical_smiles")
                cid = mol.get("molecule_chembl_id")
                if smiles and cid and len(smiles) < 200:
                    compounds.append({
                        "name": cid,
                        "smiles": smiles,
                        "source": "fda_approved",
                    })
        logger.info("FDA approved: %d compounds", len(compounds))
    except Exception as e:
        logger.error("FDA fetch failed: %s", e)

    return compounds[:limit]


def main():
    parser = argparse.ArgumentParser(description="Fetch screening library for DiffDock")
    parser.add_argument("-o", "--output", default="gpu/data/screening_library.csv")
    parser.add_argument("--max", type=int, default=5000, help="Max total compounds")
    args = parser.parse_args()

    all_compounds = []
    seen_smiles = set()

    # 1. Platform candidates
    for c in fetch_platform_candidates():
        if c["smiles"] not in seen_smiles:
            seen_smiles.add(c["smiles"])
            all_compounds.append(c)

    # 2. ChEMBL SMA compounds
    for c in fetch_chembl_sma_compounds():
        if c["smiles"] not in seen_smiles:
            seen_smiles.add(c["smiles"])
            all_compounds.append(c)

    # 3. FDA approved drugs
    for c in fetch_fda_approved():
        if c["smiles"] not in seen_smiles:
            seen_smiles.add(c["smiles"])
            all_compounds.append(c)

    # Cap at max
    all_compounds = all_compounds[: args.max]

    # Write CSV
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "smiles", "source"])
        writer.writeheader()
        writer.writerows(all_compounds)

    logger.info("Total unique compounds: %d", len(all_compounds))
    logger.info("Written to: %s", args.output)

    # Source breakdown
    sources = {}
    for c in all_compounds:
        sources[c["source"]] = sources.get(c["source"], 0) + 1
    for src, count in sorted(sources.items()):
        logger.info("  %s: %d", src, count)


if __name__ == "__main__":
    main()
