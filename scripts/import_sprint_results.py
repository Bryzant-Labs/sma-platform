#!/usr/bin/env python3
"""
Import 2026-03-24 sprint results into sma_platform DB.

Files:
  1. limk2_rock2_campaign_2026-03-24.json  -> diffdock_extended (14 dockings)
  2. chembl_limk2_screen_2026-03-24.json   -> diffdock_extended (20 dockings)
  3. genmol_limk2_2026-03-24.json          -> designed_molecules (136 molecules)
  4. genmol_rock2_2026-03-24.json          -> designed_molecules (107 molecules)
"""

import json
import os
import sys
import asyncio
import asyncpg

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "sma",
    "password": "sma-research-2026",
    "database": "sma_platform",
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "docking")


async def get_counts(pool):
    """Get current row counts."""
    async with pool.acquire() as conn:
        dd = await conn.fetchval("SELECT COUNT(*) FROM diffdock_extended")
        dm = await conn.fetchval("SELECT COUNT(*) FROM designed_molecules")
    return dd, dm


async def import_dockings(pool, filepath, campaign_name):
    """Import docking results into diffdock_extended."""
    with open(filepath) as f:
        data = json.load(f)

    results = data.get("results", [])
    inserted = 0

    async with pool.acquire() as conn:
        for r in results:
            drug_name = r.get("compound") or r.get("chembl_id", "Unknown")
            target = r.get("target", data.get("target", {}).get("symbol", ""))
            smiles = r.get("smiles", "")
            mw = r.get("mw")
            num_poses = r.get("num_poses")
            best_conf = r.get("top_confidence")
            avg_conf = r.get("mean_confidence")

            # Check for existing entry with same drug+target+campaign
            exists = await conn.fetchval(
                "SELECT 1 FROM diffdock_extended WHERE drug_name=$1 AND target_symbol=$2 AND campaign=$3",
                drug_name, target, campaign_name,
            )
            if exists:
                print(f"  SKIP (exists): {drug_name} vs {target}")
                continue

            await conn.execute(
                """INSERT INTO diffdock_extended
                   (drug_name, target_symbol, smiles, mw, num_poses, best_confidence, avg_confidence, campaign, status)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                drug_name, target, smiles, mw, num_poses, best_conf, avg_conf, campaign_name, "completed",
            )
            inserted += 1
            print(f"  INSERT: {drug_name} vs {target} (conf={best_conf:.3f})" if best_conf else f"  INSERT: {drug_name} vs {target}")

    return inserted, len(results)


async def import_molecules(pool, filepath, target_symbol, batch_name):
    """Import GenMol molecules into designed_molecules."""
    with open(filepath) as f:
        data = json.load(f)

    # Use all_drug_like (full set) if available, fall back to top_candidates
    molecules = data.get("all_drug_like", data.get("top_candidates", []))
    inserted = 0

    async with pool.acquire() as conn:
        for mol in molecules:
            smiles = mol.get("smiles", "")
            if not smiles:
                continue

            # Deduplicate by SMILES + target
            exists = await conn.fetchval(
                "SELECT 1 FROM designed_molecules WHERE smiles=$1 AND target_symbol=$2",
                smiles, target_symbol,
            )
            if exists:
                print(f"  SKIP (exists): {smiles[:40]}...")
                continue

            qed = mol.get("qed")
            mw = mol.get("mw")
            logp = mol.get("logp")
            hbd = mol.get("hbd")
            hba = mol.get("hba")
            tpsa = mol.get("tpsa")
            score = mol.get("api_score")
            seed = mol.get("seed", "")
            scaffold = mol.get("seed_smiles", "")

            # Lipinski check
            lipinski = True
            if mw and mw > 500:
                lipinski = False
            if logp and logp > 5:
                lipinski = False
            if hbd and hbd > 5:
                lipinski = False
            if hba and hba > 10:
                lipinski = False

            # BBB heuristic: MW<450, TPSA<90, logP 1-4
            bbb = bool(
                mw and mw < 450
                and tpsa and tpsa < 90
                and logp and 1.0 <= logp <= 4.0
            )

            await conn.execute(
                """INSERT INTO designed_molecules
                   (target_symbol, smiles, scaffold_smiles, score, qed, mw, logp, hbd, hba,
                    bbb_permeable, tpsa, lipinski_pass, method, generation_batch)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)""",
                target_symbol, smiles, scaffold, score, qed, mw, logp, hbd, hba,
                bbb, tpsa, lipinski, "GenMol", batch_name,
            )
            inserted += 1

    return inserted, len(molecules)


async def main():
    pool = await asyncpg.create_pool(**DB_CONFIG, min_size=1, max_size=3)

    dd_before, dm_before = await get_counts(pool)
    print(f"=== BEFORE: diffdock_extended={dd_before}, designed_molecules={dm_before} ===\n")

    # 1. LIMK2/ROCK2 campaign dockings
    f1 = os.path.join(DATA_DIR, "limk2_rock2_campaign_2026-03-24.json")
    print(f"[1] Importing LIMK2/ROCK2 campaign from {os.path.basename(f1)}")
    ins1, tot1 = await import_dockings(pool, f1, "limk2_rock2_campaign_2026-03-24")
    print(f"    -> {ins1}/{tot1} inserted\n")

    # 2. ChEMBL LIMK2 screen
    f2 = os.path.join(DATA_DIR, "chembl_limk2_screen_2026-03-24.json")
    print(f"[2] Importing ChEMBL LIMK2 screen from {os.path.basename(f2)}")
    ins2, tot2 = await import_dockings(pool, f2, "chembl_limk2_screen_2026-03-24")
    print(f"    -> {ins2}/{tot2} inserted\n")

    # 3. GenMol LIMK2 molecules
    f3 = os.path.join(DATA_DIR, "genmol_limk2_2026-03-24.json")
    print(f"[3] Importing GenMol LIMK2 molecules from {os.path.basename(f3)}")
    ins3, tot3 = await import_molecules(pool, f3, "LIMK2", "genmol_limk2_2026-03-24")
    print(f"    -> {ins3}/{tot3} inserted\n")

    # 4. GenMol ROCK2 molecules
    f4 = os.path.join(DATA_DIR, "genmol_rock2_2026-03-24.json")
    print(f"[4] Importing GenMol ROCK2 molecules from {os.path.basename(f4)}")
    ins4, tot4 = await import_molecules(pool, f4, "ROCK2", "genmol_rock2_2026-03-24")
    print(f"    -> {ins4}/{tot4} inserted\n")

    dd_after, dm_after = await get_counts(pool)
    print(f"=== AFTER: diffdock_extended={dd_after}, designed_molecules={dm_after} ===")
    print(f"=== DELTA: diffdock_extended +{dd_after - dd_before}, designed_molecules +{dm_after - dm_before} ===")

    await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
