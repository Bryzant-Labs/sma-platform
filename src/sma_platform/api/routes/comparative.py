"""Cross-species comparative biology endpoints (Querdenker module).

Provides endpoints for cross-species ortholog data, model organism info,
and comparative analysis for SMA targets.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query

from ...core.database import execute, fetch, fetchrow
from ...ingestion.adapters.orthologs import batch_ortholog_search, get_ortholog_conservation
from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter()

SPECIES_INFO = [
    {"id": "10090", "name": "Mouse", "scientific": "Mus musculus",
     "key_trait": "Primary SMA disease model, 90% of preclinical research"},
    {"id": "10116", "name": "Rat", "scientific": "Rattus norvegicus",
     "key_trait": "Pharmacokinetic and toxicology studies"},
    {"id": "8296", "name": "Axolotl", "scientific": "Ambystoma mexicanum",
     "key_trait": "Full spinal cord regeneration"},
    {"id": "7955", "name": "Zebrafish", "scientific": "Danio rerio",
     "key_trait": "Motor neuron regeneration"},
    {"id": "10181", "name": "Naked Mole Rat", "scientific": "Heterocephalus glaber",
     "key_trait": "Neurodegeneration resistance"},
    {"id": "6239", "name": "C. elegans", "scientific": "Caenorhabditis elegans",
     "key_trait": "SMN ortholog studies"},
    {"id": "7227", "name": "Drosophila", "scientific": "Drosophila melanogaster",
     "key_trait": "SMN loss-of-function models"},
]


@router.get("/species")
async def list_species():
    """List model organisms with target mapping counts."""
    result = []
    for sp in SPECIES_INFO:
        row = await fetchrow(
            "SELECT COUNT(*) as cnt FROM cross_species_targets WHERE species_taxon_id = $1",
            sp["id"],
        )
        count = row["cnt"] if row else 0
        result.append({**sp, "mapped_targets": count})
    return {"species": result}


@router.get("/orthologs/{symbol}")
async def get_orthologs(symbol: str):
    """Get orthologs for a human gene symbol across model organisms.

    Checks the database first, falls back to live NCBI query.
    """
    # Check DB first
    rows = await fetch(
        "SELECT * FROM cross_species_targets WHERE human_symbol = $1",
        symbol.upper(),
    )
    if rows:
        return {
            "symbol": symbol.upper(),
            "source": "database",
            "orthologs": [dict(r) for r in rows],
        }

    # Live query from NCBI
    result = await get_ortholog_conservation(symbol.upper())
    return {
        "symbol": symbol.upper(),
        "source": "ncbi_live",
        **result,
    }


@router.get("/orthologs")
async def list_all_orthologs():
    """Get all ortholog mappings for the heatmap visualization."""
    rows = await fetch(
        "SELECT * FROM cross_species_targets ORDER BY human_symbol, species"
    )
    return [dict(r) for r in rows]


@router.get("/cross-species-targets")
async def list_cross_species_targets(
    species: Optional[str] = Query(default=None, description="Filter by species name"),
    human_symbol: Optional[str] = Query(default=None, description="Filter by human gene symbol"),
):
    """List all cross-species target mappings."""
    query = "SELECT * FROM cross_species_targets WHERE 1=1"
    params = []

    if species:
        query += f" AND species = ${len(params) + 1}"
        params.append(species)
    if human_symbol:
        query += f" AND human_symbol = ${len(params) + 1}"
        params.append(human_symbol.upper())

    query += " ORDER BY human_symbol, species"
    rows = await fetch(query, *params)

    return {
        "count": len(rows),
        "targets": [dict(r) for r in rows],
    }


@router.post("/ingest/orthologs", dependencies=[Depends(require_admin_key)])
async def trigger_ortholog_ingestion():
    """Map all human SMA targets to orthologs across model organisms.

    Queries NCBI for each target and stores results in cross_species_targets.
    """
    targets = await fetch("SELECT id, symbol FROM targets WHERE target_type = 'gene'")
    symbols = [t["symbol"] for t in targets]
    symbol_to_id = {t["symbol"]: str(t["id"]) for t in targets}

    results = await batch_ortholog_search(symbols)

    stored = 0
    for result in results:
        human_sym = result["gene_symbol"]
        human_id = symbol_to_id.get(human_sym)

        for orth in result.get("orthologs", []):
            orth_id = hashlib.sha256(
                f"{human_sym}:{orth['species_taxon_id']}:{orth['ortholog_symbol']}".encode()
            ).hexdigest()[:32]

            await execute(
                """INSERT INTO cross_species_targets
                   (id, human_symbol, human_target_id, species, species_taxon_id,
                    ortholog_symbol, ortholog_id, conservation_score)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                   ON CONFLICT(id) DO UPDATE SET
                    conservation_score = EXCLUDED.conservation_score,
                    ortholog_symbol = EXCLUDED.ortholog_symbol""",
                orth_id, human_sym, human_id,
                orth["species_name"], orth["species_taxon_id"],
                orth["ortholog_symbol"], orth["ortholog_gene_id"],
                result["conservation_breadth"],
            )
            stored += 1

    return {
        "targets_queried": len(symbols),
        "orthologs_stored": stored,
        "conservation_summary": [
            {"symbol": r["gene_symbol"], "breadth": r["conservation_breadth"],
             "species_count": r["total_species_with_ortholog"]}
            for r in results
        ],
    }
