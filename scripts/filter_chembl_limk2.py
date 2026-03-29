#!/usr/bin/env python3
"""Filter ChEMBL compounds from molecule_screenings for LIMK2 docking candidates.

Queries the SMA platform PostgreSQL database for drug-like, BBB-favorable
compounds suitable for docking against LIMK2 (LIM Domain Kinase 2).

Selection criteria:
  - Lipinski/drug-likeness pass
  - MW 200-500 Da
  - LogP 1.0-4.0 (CNS/BBB-favorable range)
  - Valid SMILES present
  - Ranked by pChEMBL value (potency)

Usage:
    python scripts/filter_chembl_limk2.py [--top N] [--output PATH]

Environment:
    DATABASE_URL or individual PG vars (PGHOST, PGUSER, PGPASSWORD, PGDATABASE)
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

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "docking"

# Default DB connection (moltbot server)
DEFAULT_DSN = "postgresql://sma:sma-research-2026@localhost:5432/sma_platform"


def get_dsn() -> str:
    """Build database DSN from environment or defaults."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    host = os.environ.get("PGHOST", "localhost")
    port = os.environ.get("PGPORT", "5432")
    user = os.environ.get("PGUSER", "sma")
    password = os.environ.get("PGPASSWORD", "sma-research-2026")
    dbname = os.environ.get("PGDATABASE", "sma_platform")
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


# ── SQL Queries ──────────────────────────────────────────────────────────────

SQL_STATS = """
SELECT
    COUNT(*) AS total,
    COUNT(DISTINCT chembl_id) AS unique_compounds,
    COUNT(DISTINCT chembl_id) FILTER (WHERE drug_likeness_pass = true) AS lipinski_pass,
    COUNT(DISTINCT chembl_id) FILTER (
        WHERE drug_likeness_pass = true
        AND molecular_weight BETWEEN 200 AND 500
        AND alogp BETWEEN 1 AND 4
    ) AS bbb_sweet_spot
FROM molecule_screenings;
"""

SQL_LIMK_DIRECT = """
SELECT DISTINCT ON (chembl_id)
    chembl_id, compound_name, smiles, molecular_weight, alogp,
    pchembl_value, activity_type, target_symbol
FROM molecule_screenings
WHERE (target_symbol ILIKE '%LIMK%' OR target_symbol ILIKE '%LIM kinase%')
AND drug_likeness_pass = true
ORDER BY chembl_id, pchembl_value DESC NULLS LAST;
"""

SQL_KINASE_HITS = """
SELECT DISTINCT ON (chembl_id)
    chembl_id, compound_name, smiles, molecular_weight, alogp,
    pchembl_value, activity_type, target_symbol
FROM molecule_screenings
WHERE target_symbol ILIKE '%kinase%'
AND drug_likeness_pass = true
AND molecular_weight BETWEEN 200 AND 500
ORDER BY chembl_id, pchembl_value DESC NULLS LAST;
"""

SQL_TOP_CANDIDATES = """
SELECT DISTINCT ON (chembl_id)
    chembl_id, compound_name, smiles, molecular_weight, alogp,
    pchembl_value, activity_type
FROM molecule_screenings
WHERE drug_likeness_pass = true
AND molecular_weight BETWEEN $1 AND $2
AND alogp BETWEEN $3 AND $4
AND smiles IS NOT NULL
AND length(smiles) > 5
ORDER BY chembl_id, pchembl_value DESC NULLS LAST;
"""


async def run_filter(
    top_n: int = 20,
    mw_min: float = 200.0,
    mw_max: float = 500.0,
    logp_min: float = 1.0,
    logp_max: float = 4.0,
) -> dict:
    """Query DB and return filtered candidates."""
    try:
        import asyncpg
    except ImportError:
        logger.error("asyncpg required: pip install asyncpg")
        sys.exit(1)

    dsn = get_dsn()
    logger.info("Connecting to database...")
    pool = await asyncpg.create_pool(dsn, min_size=1, max_size=3)

    async with pool.acquire() as conn:
        # 1. Get overall stats
        stats_row = await conn.fetchrow(SQL_STATS)
        stats = dict(stats_row)
        logger.info(
            "DB stats: %d total rows, %d unique compounds, %d Lipinski pass, %d in BBB sweet spot",
            stats["total"], stats["unique_compounds"],
            stats["lipinski_pass"], stats["bbb_sweet_spot"],
        )

        # 2. Check for direct LIMK hits
        limk_rows = await conn.fetch(SQL_LIMK_DIRECT)
        logger.info("Direct LIMK hits: %d", len(limk_rows))

        # 3. Check for kinase-annotated hits
        kinase_rows = await conn.fetch(SQL_KINASE_HITS)
        logger.info("Kinase-annotated hits: %d", len(kinase_rows))

        # 4. Get top candidates by potency in BBB-favorable range
        candidate_rows = await conn.fetch(
            SQL_TOP_CANDIDATES, mw_min, mw_max, logp_min, logp_max
        )
        logger.info("Candidates in filter range: %d", len(candidate_rows))

    await pool.close()

    # Sort by pchembl descending and take top N
    candidates = []
    for row in candidate_rows:
        candidates.append({
            "chembl_id": row["chembl_id"],
            "compound_name": row["compound_name"] or row["chembl_id"],
            "smiles": row["smiles"],
            "mw": float(row["molecular_weight"]) if row["molecular_weight"] else None,
            "logp": float(row["alogp"]) if row["alogp"] else None,
            "pchembl": float(row["pchembl_value"]) if row["pchembl_value"] else None,
            "activity_type": row["activity_type"],
        })

    # Sort by potency
    candidates.sort(key=lambda x: x.get("pchembl") or 0, reverse=True)
    top_candidates = candidates[:top_n]

    # Add rank
    for i, c in enumerate(top_candidates, 1):
        c["rank"] = i

    result = {
        "campaign": "ChEMBL LIMK2 candidate selection",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source_database": f"molecule_screenings ({stats['total']} rows, {stats['unique_compounds']} unique compounds)",
        "selection_criteria": {
            "drug_likeness_pass": True,
            "mw_range": f"{mw_min}-{mw_max} Da",
            "logp_range": f"{logp_min}-{logp_max} (BBB-favorable)",
            "smiles_required": True,
            "ranked_by": "pchembl_value DESC",
        },
        "pool_stats": {
            "total_screened": stats["total"],
            "unique_lipinski_pass": stats["lipinski_pass"],
            "unique_in_bbb_sweet_spot": stats["bbb_sweet_spot"],
            "limk_specific_hits": len(limk_rows),
            "kinase_specific_hits": len(kinase_rows),
        },
        "candidates": top_candidates,
        "total_candidates_in_range": len(candidates),
    }

    # Include LIMK-specific hits if any
    if limk_rows:
        result["limk_direct_hits"] = [
            {
                "chembl_id": r["chembl_id"],
                "compound_name": r["compound_name"],
                "smiles": r["smiles"],
                "mw": float(r["molecular_weight"]) if r["molecular_weight"] else None,
                "pchembl": float(r["pchembl_value"]) if r["pchembl_value"] else None,
                "target_symbol": r["target_symbol"],
            }
            for r in limk_rows
        ]

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Filter ChEMBL compounds for LIMK2 docking candidates"
    )
    parser.add_argument(
        "--top", type=int, default=20,
        help="Number of top candidates to select (default: 20)"
    )
    parser.add_argument(
        "--mw-min", type=float, default=200.0, help="Min molecular weight (default: 200)"
    )
    parser.add_argument(
        "--mw-max", type=float, default=500.0, help="Max molecular weight (default: 500)"
    )
    parser.add_argument(
        "--logp-min", type=float, default=1.0, help="Min LogP (default: 1.0)"
    )
    parser.add_argument(
        "--logp-max", type=float, default=4.0, help="Max LogP (default: 4.0)"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output JSON path (default: data/docking/limk2_candidates_topN.json)"
    )
    args = parser.parse_args()

    result = asyncio.run(run_filter(
        top_n=args.top,
        mw_min=args.mw_min,
        mw_max=args.mw_max,
        logp_min=args.logp_min,
        logp_max=args.logp_max,
    ))

    # Output path
    if args.output:
        out_path = Path(args.output)
    else:
        out_path = DATA_DIR / f"limk2_candidates_top{args.top}.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, default=str))
    logger.info("Saved %d candidates to %s", len(result["candidates"]), out_path)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"LIMK2 Docking Candidate Selection")
    print(f"{'=' * 60}")
    print(f"  Total screened:        {result['pool_stats']['total_screened']:,}")
    print(f"  Lipinski pass:         {result['pool_stats']['unique_lipinski_pass']:,}")
    print(f"  BBB sweet spot:        {result['pool_stats']['unique_in_bbb_sweet_spot']:,}")
    print(f"  LIMK-specific:         {result['pool_stats']['limk_specific_hits']}")
    print(f"  Kinase-specific:       {result['pool_stats']['kinase_specific_hits']}")
    print(f"  Selected (top {args.top}):    {len(result['candidates'])}")
    print(f"{'=' * 60}")
    print(f"\nTop 5 candidates:")
    for c in result["candidates"][:5]:
        name = c.get("compound_name", c["chembl_id"])
        pchembl = c.get("pchembl", "N/A")
        mw = c.get("mw", "?")
        print(f"  {c['rank']:2d}. {name:16s} pChEMBL={pchembl}  MW={mw}  LogP={c.get('logp', '?')}")
    print(f"\nOutput: {out_path}")


if __name__ == "__main__":
    main()
