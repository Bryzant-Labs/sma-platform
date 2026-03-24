"""Compute ADMET properties for all molecules in the molecule_screenings table.

Connects to the PostgreSQL database (moltbot or local), fetches all molecules
with SMILES, and calculates RDKit-based ADMET descriptors:
  - Lipinski: MW, LogP, HBD, HBA
  - TPSA (BBB indicator: < 90 = likely permeable)
  - QED (drug-likeness score)
  - Rotatable bonds, aromatic rings
  - BBB_permeable flag (TPSA < 90 AND MW < 450)

Usage:
    python scripts/compute_admet.py                       # default DB URL
    python scripts/compute_admet.py --db-url postgresql://sma:pass@host/db
    python scripts/compute_admet.py --update-db            # also write back to DB
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Default DB URL — moltbot via SSH tunnel (localhost:5432)
DEFAULT_DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://sma:sma-research-2026@localhost:5432/sma_platform",
)


def compute_admet_properties(smiles: str) -> dict | None:
    """Calculate ADMET properties from a SMILES string using RDKit."""
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors, QED, rdMolDescriptors
    except ImportError:
        logger.error("RDKit not installed. Install with: pip install rdkit-pypi")
        sys.exit(1)

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    hbd = rdMolDescriptors.CalcNumHBD(mol)
    hba = rdMolDescriptors.CalcNumHBA(mol)
    tpsa = Descriptors.TPSA(mol)
    qed_score = QED.qed(mol)
    rot_bonds = rdMolDescriptors.CalcNumRotatableBonds(mol)
    aromatic_rings = rdMolDescriptors.CalcNumAromaticRings(mol)
    num_rings = rdMolDescriptors.CalcNumRings(mol)
    heavy_atoms = mol.GetNumHeavyAtoms()

    # Lipinski Rule of Five
    lipinski_violations = sum([
        mw > 500,
        logp > 5,
        hbd > 5,
        hba > 10,
    ])
    lipinski_pass = lipinski_violations <= 1

    # BBB permeability heuristic
    bbb_permeable = tpsa < 90 and mw < 450

    # CNS MPO score (simplified)
    # Based on Wager et al. (2010) - CNS Multiparameter Optimization
    cns_mpo = 0.0
    # LogP component (optimal 1-3)
    if logp <= 3:
        cns_mpo += 1.0
    elif logp <= 5:
        cns_mpo += 1.0 - (logp - 3) / 2
    # TPSA component (optimal 40-90)
    if tpsa <= 90:
        cns_mpo += 1.0
    elif tpsa <= 120:
        cns_mpo += 1.0 - (tpsa - 90) / 30
    # MW component (optimal < 360)
    if mw <= 360:
        cns_mpo += 1.0
    elif mw <= 500:
        cns_mpo += 1.0 - (mw - 360) / 140
    # HBD component (optimal 0-1)
    if hbd <= 1:
        cns_mpo += 1.0
    elif hbd <= 3:
        cns_mpo += 1.0 - (hbd - 1) / 2
    # pKa approximation via HBA (rough proxy)
    if hba <= 5:
        cns_mpo += 1.0
    elif hba <= 8:
        cns_mpo += 1.0 - (hba - 5) / 3

    return {
        "mw": round(mw, 2),
        "logp": round(logp, 2),
        "hbd": hbd,
        "hba": hba,
        "tpsa": round(tpsa, 2),
        "qed": round(qed_score, 3),
        "rotatable_bonds": rot_bonds,
        "aromatic_rings": aromatic_rings,
        "num_rings": num_rings,
        "heavy_atoms": heavy_atoms,
        "lipinski_violations": lipinski_violations,
        "lipinski_pass": lipinski_pass,
        "bbb_permeable": bbb_permeable,
        "cns_mpo": round(cns_mpo, 2),
    }


async def fetch_molecules(db_url: str) -> list[dict]:
    """Fetch all molecules with SMILES from the database."""
    import asyncpg

    logger.info("Connecting to database...")
    pool = await asyncpg.create_pool(db_url, min_size=1, max_size=3)

    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT id, target_symbol, chembl_id, pubchem_cid,
                          compound_name, smiles, pchembl_value,
                          molecular_weight, alogp, drug_likeness_pass
                   FROM molecule_screenings
                   WHERE smiles IS NOT NULL AND smiles != ''
                   ORDER BY pchembl_value DESC NULLS LAST"""
            )
            logger.info("Fetched %d molecules with SMILES", len(rows))
            return [dict(r) for r in rows]
    finally:
        await pool.close()


async def update_db_metadata(db_url: str, updates: list[dict]):
    """Update molecule_screenings metadata with ADMET properties."""
    import asyncpg

    logger.info("Updating %d molecules in database...", len(updates))
    pool = await asyncpg.create_pool(db_url, min_size=1, max_size=3)

    try:
        async with pool.acquire() as conn:
            # Ensure metadata column supports JSONB merge
            for update in updates:
                mol_id = update["id"]
                admet_json = json.dumps(update["admet"])
                await conn.execute(
                    """UPDATE molecule_screenings
                       SET metadata = COALESCE(metadata, '{}'::jsonb) || $1::jsonb,
                           drug_likeness_pass = $2
                       WHERE id = $3""",
                    json.dumps({"admet": update["admet"]}),
                    update["admet"]["lipinski_pass"],
                    mol_id,
                )
            logger.info("Database updated successfully")
    finally:
        await pool.close()


async def main():
    parser = argparse.ArgumentParser(description="Compute ADMET properties for SMA molecules")
    parser.add_argument(
        "--db-url",
        default=DEFAULT_DB_URL,
        help="PostgreSQL connection URL",
    )
    parser.add_argument(
        "--update-db",
        action="store_true",
        help="Write ADMET results back to the database",
    )
    args = parser.parse_args()

    # Verify RDKit is available
    try:
        from rdkit import Chem
        logger.info("RDKit version: %s", Chem.rdBase.rdkitVersion)
    except ImportError:
        logger.error("RDKit not installed. Install with: pip install rdkit-pypi")
        sys.exit(1)

    # Fetch molecules from DB
    try:
        molecules = await fetch_molecules(args.db_url)
    except Exception as e:
        logger.error("Failed to connect to database: %s", e)
        logger.info("Tip: Set up SSH tunnel first: ssh -L 5432:localhost:5432 moltbot")
        sys.exit(1)

    if not molecules:
        logger.warning("No molecules with SMILES found in database")
        sys.exit(0)

    # Compute ADMET for each molecule
    results = []
    failed = 0
    db_updates = []

    for mol in molecules:
        smiles = mol["smiles"]
        admet = compute_admet_properties(smiles)

        if admet is None:
            failed += 1
            logger.debug("Failed to parse SMILES: %s", smiles)
            continue

        result = {
            "id": str(mol["id"]),
            "target_symbol": mol["target_symbol"],
            "chembl_id": mol.get("chembl_id", ""),
            "compound_name": mol.get("compound_name", ""),
            "smiles": smiles,
            "pchembl_value": float(mol["pchembl_value"]) if mol.get("pchembl_value") else None,
            "admet": admet,
        }
        results.append(result)
        db_updates.append({"id": mol["id"], "admet": admet})

    # Summary statistics
    bbb_count = sum(1 for r in results if r["admet"]["bbb_permeable"])
    lipinski_count = sum(1 for r in results if r["admet"]["lipinski_pass"])
    high_qed = sum(1 for r in results if r["admet"]["qed"] >= 0.5)
    cns_ready = sum(1 for r in results if r["admet"]["cns_mpo"] >= 4.0)

    summary = {
        "total_molecules": len(molecules),
        "computed": len(results),
        "failed_parsing": failed,
        "bbb_permeable": bbb_count,
        "lipinski_pass": lipinski_count,
        "high_qed": high_qed,
        "cns_mpo_ready": cns_ready,
        "avg_qed": round(
            sum(r["admet"]["qed"] for r in results) / len(results), 3
        ) if results else 0,
        "avg_cns_mpo": round(
            sum(r["admet"]["cns_mpo"] for r in results) / len(results), 2
        ) if results else 0,
    }

    # Print report
    print("\n" + "=" * 60)
    print("ADMET Property Predictions")
    print("=" * 60)
    print(f"  Total molecules:    {summary['total_molecules']}")
    print(f"  Successfully parsed: {summary['computed']}")
    print(f"  Failed to parse:    {summary['failed_parsing']}")
    print(f"  BBB permeable:      {summary['bbb_permeable']} ({100*bbb_count/max(len(results),1):.1f}%)")
    print(f"  Lipinski pass:      {summary['lipinski_pass']} ({100*lipinski_count/max(len(results),1):.1f}%)")
    print(f"  High QED (>=0.5):   {summary['high_qed']} ({100*high_qed/max(len(results),1):.1f}%)")
    print(f"  CNS MPO ready (>=4): {summary['cns_mpo_ready']} ({100*cns_ready/max(len(results),1):.1f}%)")
    print(f"  Average QED:        {summary['avg_qed']}")
    print(f"  Average CNS MPO:    {summary['avg_cns_mpo']}")
    print("=" * 60)

    # Top BBB-permeable compounds by QED
    bbb_compounds = sorted(
        [r for r in results if r["admet"]["bbb_permeable"]],
        key=lambda x: x["admet"]["qed"],
        reverse=True,
    )
    if bbb_compounds:
        print("\nTop 10 BBB-Permeable Compounds by QED:")
        print(f"  {'Name':<30s} {'Target':<8s} {'QED':>5s} {'TPSA':>6s} {'MW':>7s} {'LogP':>5s} {'CNS':>4s}")
        for c in bbb_compounds[:10]:
            a = c["admet"]
            name = (c.get("compound_name") or c.get("chembl_id") or "?")[:30]
            print(
                f"  {name:<30s} {c['target_symbol']:<8s} "
                f"{a['qed']:>5.3f} {a['tpsa']:>6.1f} {a['mw']:>7.1f} "
                f"{a['logp']:>5.1f} {a['cns_mpo']:>4.1f}"
            )

    # Save results
    output = {
        "computation_date": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "molecules": results,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / "admet_predictions.json"
    out_path.write_text(json.dumps(output, indent=2, default=str))
    logger.info("Results saved to %s", out_path)

    # Optionally update DB
    if args.update_db and db_updates:
        await update_db_metadata(args.db_url, db_updates)


if __name__ == "__main__":
    asyncio.run(main())
