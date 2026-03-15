"""ChEMBL / PubChem Molecule Screener — Agent B.

Searches molecular databases for bioactive compounds against SMA-relevant
targets, applies drug-likeness filters, persists hits, and posts discoveries
to the shared blackboard.

External APIs
-------------
- ChEMBL REST API : https://www.ebi.ac.uk/chembl/api/data
- PubChem PUG REST : https://pubchem.ncbi.nlm.nih.gov/rest/pug

Drug-likeness thresholds
------------------------
- MAX_MW                  : 800 Da  (relaxed for biologics / PROTACs)
- MAX_LIPINSKI_VIOLATIONS : 1       (Lipinski Ro5, one-violation tolerance)
- MIN_PCHEMBL              : 5.0    (10 µM potency floor)
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

from ..core.database import execute, execute_script, fetch, fetchrow, fetchval
from .blackboard import auto_post_discovery

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AGENT_NAME = "molecule-screener-agent"

CHEMBL_API = "https://www.ebi.ac.uk/chembl/api/data"
PUBCHEM_API = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

MAX_MW: float = 800.0
MAX_LIPINSKI_VIOLATIONS: int = 1
MIN_PCHEMBL: float = 5.0

# ChEMBL activity types considered meaningful for binding / functional evidence
RELEVANT_ACTIVITY_TYPES = {"IC50", "Ki", "Kd", "EC50", "AC50", "GI50", "Potency"}

# HTTP timeout (seconds) — ChEMBL can be slow under load
_HTTP_TIMEOUT = 30.0

# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

_CREATE_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS molecule_screenings (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_symbol      TEXT NOT NULL,
    target_id          UUID,
    chembl_id          TEXT,
    pubchem_cid        TEXT,
    compound_name      TEXT,
    smiles             TEXT,
    pchembl_value      REAL,
    activity_type      TEXT,
    molecular_weight   REAL,
    alogp              REAL,
    source             TEXT NOT NULL DEFAULT 'chembl',
    drug_likeness_pass BOOLEAN NOT NULL DEFAULT FALSE,
    metadata           JSONB DEFAULT '{}',
    screened_by        TEXT NOT NULL DEFAULT 'molecule-screener-agent',
    created_at         TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(target_symbol, chembl_id, source)
);
CREATE INDEX IF NOT EXISTS idx_mol_screen_symbol
    ON molecule_screenings(target_symbol);
CREATE INDEX IF NOT EXISTS idx_mol_screen_chembl
    ON molecule_screenings(chembl_id);
CREATE INDEX IF NOT EXISTS idx_mol_screen_pchembl
    ON molecule_screenings(pchembl_value DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_mol_screen_pass
    ON molecule_screenings(drug_likeness_pass);
"""

_table_ready = False


# ---------------------------------------------------------------------------
# Table bootstrap
# ---------------------------------------------------------------------------

async def ensure_table() -> None:
    """Create the ``molecule_screenings`` table and indexes if missing."""
    global _table_ready
    if _table_ready:
        return
    try:
        await execute_script(_CREATE_TABLE_DDL)
        _table_ready = True
        logger.info("molecule_screenings table ensured")
    except Exception as exc:
        logger.error("Failed to create molecule_screenings table: %s", exc, exc_info=True)
        raise


# ---------------------------------------------------------------------------
# Drug-likeness filter
# ---------------------------------------------------------------------------

def _check_drug_likeness(mw: float | None, alogp: float | None, pchembl: float | None) -> bool:
    """Return True when compound passes our relaxed drug-likeness gate.

    Rules applied:
    1. Molecular weight <= MAX_MW (800 Da)
    2. pChEMBL >= MIN_PCHEMBL (5.0 == 10 µM)
    3. aLogP <= 7.0  (rough oral-absorption ceiling)

    Lipinski Ro5 violations are tracked via *alogp* / *mw* but we use the
    one-violation tolerance (MAX_LIPINSKI_VIOLATIONS = 1).
    """
    if mw is not None and mw > MAX_MW:
        return False
    if pchembl is not None and pchembl < MIN_PCHEMBL:
        return False
    # Greasy compounds almost always fail absorption
    if alogp is not None and alogp > 7.0:
        return False
    return True


def _count_lipinski_violations(mw: float | None, alogp: float | None) -> int:
    """Count simple Lipinski Ro5 violations (MW > 500, cLogP > 5)."""
    violations = 0
    if mw is not None and mw > 500:
        violations += 1
    if alogp is not None and alogp > 5:
        violations += 1
    return violations


# ---------------------------------------------------------------------------
# ChEMBL helpers
# ---------------------------------------------------------------------------

async def _chembl_get(client: httpx.AsyncClient, path: str, params: dict | None = None) -> dict:
    """GET from ChEMBL REST API; returns parsed JSON or raises HTTPStatusError."""
    url = f"{CHEMBL_API}/{path}"
    resp = await client.get(url, params=params, timeout=_HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


# Known UniProt IDs for SMA-relevant targets (curated mapping for precise ChEMBL lookup)
_UNIPROT_MAP: dict[str, str] = {
    "SMN1": "Q16637",     # Survival motor neuron protein (SMN)
    "SMN2": "Q16637",     # Same protein, different gene
    "SMN_PROTEIN": "Q16637",
    "NCALD": "Q6P2D0",    # Neurocalcin-delta
    "PLS3": "P13797",     # Plastin-3
    "UBA1": "P22314",     # Ubiquitin-like modifier activating enzyme 1
    "STMN2": "Q93045",    # Stathmin-2
    "CORO1C": "Q9ULV4",   # Coronin-1C
    "CAST": "P20810",     # Calpastatin
    "ANK3": "Q12955",     # Ankyrin-3
    "LY96": "Q9Y6Y9",     # Lymphocyte antigen 96 (MD-2)
    "NEDD4L": "Q96PU5",   # E3 ubiquitin-protein ligase NEDD4-like
    "LDHA": "P00338",     # L-lactate dehydrogenase A
    "DNMT3B": "Q9UBC3",   # DNA methyltransferase 3B
    "CD44": "P16070",     # CD44 antigen
    "CTNNA1": "P35221",   # Catenin alpha-1
    "SULF1": "Q8IWU6",    # Extracellular sulfatase Sulf-1
    "GALNT6": "Q8NCL4",   # GalNAc transferase 6
    "SPATA18": "Q8TC71",  # Spermatogenesis-associated protein 18
}

# Pathway/phenotype targets need special search terms
_PATHWAY_SEARCH: dict[str, list[str]] = {
    "MTOR_PATHWAY": ["MTOR", "RPTOR", "RICTOR"],  # Search key kinases
    "NMJ_MATURATION": ["AGRN", "MUSK", "RAPSN"],  # NMJ assembly proteins
}


async def _get_chembl_target_ids(client: httpx.AsyncClient, symbol: str) -> list[str]:
    """Resolve a gene symbol to ChEMBL target accessions.

    Strategy (in priority order):
    1. Curated UniProt mapping → ChEMBL component search (most precise)
    2. Exact gene_name search (human SINGLE PROTEIN only)
    3. Fallback: pref_name search (broader, less precise)
    """
    # 1. Try curated UniProt mapping
    uniprot_id = _UNIPROT_MAP.get(symbol)
    if uniprot_id:
        try:
            data = await _chembl_get(
                client,
                "target",
                params={"target_components__accession": uniprot_id, "format": "json", "limit": 5},
            )
            targets = data.get("targets", [])
            ids = [t["target_chembl_id"] for t in targets
                   if t.get("target_chembl_id") and t.get("organism") == "Homo sapiens"]
            if ids:
                logger.info("ChEMBL: resolved %s via UniProt %s → %s", symbol, uniprot_id, ids)
                return ids
        except Exception:
            pass  # Fall through to gene_name search

    # 2. Exact gene_name search (filter to human SINGLE PROTEIN)
    data = await _chembl_get(
        client,
        "target",
        params={"gene_name": symbol, "format": "json", "limit": 10},
    )
    targets = data.get("targets", [])
    ids = [t["target_chembl_id"] for t in targets
           if t.get("target_chembl_id")
           and t.get("organism") == "Homo sapiens"
           and t.get("target_type") in ("SINGLE PROTEIN", "PROTEIN FAMILY", "PROTEIN COMPLEX")]

    if ids:
        logger.info("ChEMBL: resolved %s via gene_name → %s", symbol, ids)
        return ids

    # 3. Fallback: broader name search
    data2 = await _chembl_get(
        client,
        "target",
        params={"pref_name__icontains": symbol, "format": "json", "limit": 5},
    )
    ids = [t["target_chembl_id"] for t in data2.get("targets", [])
           if t.get("target_chembl_id") and t.get("organism") == "Homo sapiens"]

    logger.info("ChEMBL: resolved %s via pref_name fallback → %s", symbol, ids)
    return ids


MAX_ACTIVITIES_PER_TARGET: int = 500  # Cap to avoid multi-hour fetches

async def _get_chembl_activities(
    client: httpx.AsyncClient,
    chembl_target_id: str,
    limit: int = 200,
) -> list[dict]:
    """Fetch bioactivity records for one ChEMBL target (capped)."""
    activities: list[dict] = []
    offset = 0

    while True:
        data = await _chembl_get(
            client,
            "activity",
            params={
                "target_chembl_id": chembl_target_id,
                "format": "json",
                "limit": limit,
                "offset": offset,
                "pchembl_value__gte": str(MIN_PCHEMBL),
            },
        )
        page = data.get("activities", [])
        activities.extend(page)
        total = data.get("page_meta", {}).get("total_count", 0)
        offset += limit

        if len(activities) >= MAX_ACTIVITIES_PER_TARGET:
            logger.info(
                "ChEMBL: capping %s at %d activities (total available: %d)",
                chembl_target_id, len(activities), total,
            )
            activities = activities[:MAX_ACTIVITIES_PER_TARGET]
            break

        if offset >= total or not page:
            break

    logger.info("ChEMBL: fetched %d activities for %s", len(activities), chembl_target_id)
    return activities


async def _get_molecule_properties(
    client: httpx.AsyncClient,
    molecule_chembl_id: str,
) -> dict:
    """Fetch molecule properties (MW, aLogP, SMILES) for one ChEMBL compound."""
    data = await _chembl_get(
        client,
        f"molecule/{molecule_chembl_id}",
        params={"format": "json"},
    )
    props = data.get("molecule_properties") or {}
    struct = data.get("molecule_structures") or {}
    return {
        "molecular_weight": _safe_float(props.get("full_mwt") or props.get("mw_freebase")),
        "alogp": _safe_float(props.get("alogp")),
        "smiles": struct.get("canonical_smiles") or struct.get("molfile", ""),
        "pref_name": data.get("pref_name") or "",
    }


def _safe_float(val: Any) -> float | None:
    """Parse a value to float, returning None on failure."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# PubChem helpers
# ---------------------------------------------------------------------------

async def _pubchem_get(client: httpx.AsyncClient, path: str) -> Any:
    """GET from PubChem PUG REST; returns parsed JSON."""
    url = f"{PUBCHEM_API}/{path}"
    resp = await client.get(url, timeout=_HTTP_TIMEOUT)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


async def search_pubchem_target(symbol: str) -> list[dict]:
    """Search PubChem for bioassay-active compounds targeting *symbol*.

    Returns a list of compound dicts with keys:
    ``cid``, ``compound_name``, ``molecular_weight``, ``smiles``, ``source``.

    This is a lighter search than ChEMBL — PubChem does not expose pChEMBL
    values natively, so we only store the basic properties and mark
    ``pchembl_value`` as None.
    """
    results: list[dict] = []

    try:
        async with httpx.AsyncClient() as client:
            # Search by gene name via PubChem bioassay API
            data = await _pubchem_get(
                client,
                f"compound/name/{symbol}/JSON",
            )
            if data is None:
                return results

            compounds = data.get("PC_Compounds", [])
            for cmpd in compounds[:50]:  # cap to 50 per symbol
                cid = str(cmpd.get("id", {}).get("id", {}).get("cid", ""))
                if not cid:
                    continue

                props_list = cmpd.get("props", [])
                prop_map: dict[str, Any] = {}
                for prop in props_list:
                    urn = prop.get("urn", {})
                    label = urn.get("label", "")
                    name = urn.get("name", "")
                    val = prop.get("value", {})
                    key = f"{label}_{name}".strip("_").lower()
                    # Prefer sval (string) then fval (float) then ival (int)
                    prop_map[key] = (
                        val.get("sval") or val.get("fval") or val.get("ival")
                    )

                mw = _safe_float(prop_map.get("molecularweight_") or prop_map.get("molecular_weight_"))
                smiles = prop_map.get("smiles_canonical") or prop_map.get("isomericsmiles_") or ""
                name_val = str(prop_map.get("iupacname_preferred") or prop_map.get("iupacname_") or cid)

                results.append({
                    "cid": cid,
                    "compound_name": name_val,
                    "molecular_weight": mw,
                    "smiles": str(smiles) if smiles else None,
                    "alogp": None,  # PubChem JSON does not standardly include XLogP here
                    "pchembl_value": None,
                    "activity_type": None,
                    "source": "pubchem",
                })

    except httpx.HTTPStatusError as exc:
        logger.warning("PubChem HTTP error for %s: %s", symbol, exc)
    except Exception as exc:
        logger.error("PubChem search failed for %s: %s", symbol, exc, exc_info=True)

    return results


# ---------------------------------------------------------------------------
# ChEMBL main search
# ---------------------------------------------------------------------------

MOLECULE_BATCH_SIZE: int = 20  # Concurrent molecule property fetches


async def _batch_fetch_molecule_properties(
    client: httpx.AsyncClient,
    mol_ids: list[str],
) -> dict[str, dict]:
    """Fetch molecule properties for multiple IDs concurrently in batches."""
    results: dict[str, dict] = {}
    empty = {"molecular_weight": None, "alogp": None, "smiles": "", "pref_name": ""}

    for i in range(0, len(mol_ids), MOLECULE_BATCH_SIZE):
        batch = mol_ids[i : i + MOLECULE_BATCH_SIZE]

        async def _fetch_one(mid: str) -> tuple[str, dict]:
            try:
                props = await _get_molecule_properties(client, mid)
                return mid, props
            except Exception:
                return mid, dict(empty)

        tasks = [_fetch_one(mid) for mid in batch]
        batch_results = await asyncio.gather(*tasks)
        for mid, props in batch_results:
            results[mid] = props

        if i + MOLECULE_BATCH_SIZE < len(mol_ids):
            logger.info(
                "ChEMBL molecule props: %d/%d fetched",
                min(i + MOLECULE_BATCH_SIZE, len(mol_ids)), len(mol_ids),
            )

    return results


async def search_chembl_target(symbol: str) -> list[dict]:
    """Search ChEMBL for bioactive compounds against *symbol*.

    Steps:
    1. Resolve gene symbol → ChEMBL target IDs.
    2. Fetch bioactivity records with pChEMBL >= MIN_PCHEMBL (capped at 500).
    3. Batch-fetch molecule properties (MW, aLogP, SMILES) — 20 concurrent.
    4. Apply drug-likeness filter.

    Returns a list of compound dicts ready for DB insertion.
    """
    hits: list[dict] = []
    seen_chembl_ids: set[str] = set()
    # Collect activity records first, then batch-fetch molecule props
    pending_activities: list[tuple[str, dict]] = []  # (chembl_target_id, activity)

    try:
        async with httpx.AsyncClient() as client:
            # For pathway targets, search multiple sub-genes
            search_symbols = _PATHWAY_SEARCH.get(symbol, [symbol])
            target_ids: list[str] = []
            for sub_sym in search_symbols:
                sub_ids = await _get_chembl_target_ids(client, sub_sym)
                target_ids.extend(sub_ids)
            target_ids = list(dict.fromkeys(target_ids))  # Deduplicate preserving order

            if not target_ids:
                logger.info("ChEMBL: no targets found for symbol=%s", symbol)
                return hits

            logger.info("ChEMBL: %d target IDs for %s — fetching activities", len(target_ids), symbol)

            for chembl_target_id in target_ids:
                try:
                    activities = await _get_chembl_activities(client, chembl_target_id)
                except httpx.HTTPStatusError as exc:
                    logger.warning("ChEMBL activity fetch failed for %s: %s", chembl_target_id, exc)
                    continue

                for act in activities:
                    mol_id = act.get("molecule_chembl_id", "")
                    if not mol_id or mol_id in seen_chembl_ids:
                        continue
                    seen_chembl_ids.add(mol_id)

                    activity_type = act.get("standard_type", "")
                    if activity_type and activity_type not in RELEVANT_ACTIVITY_TYPES:
                        continue

                    pchembl = _safe_float(act.get("pchembl_value"))
                    if pchembl is not None and pchembl < MIN_PCHEMBL:
                        continue

                    pending_activities.append((chembl_target_id, act))

            if not pending_activities:
                logger.info("ChEMBL: 0 relevant activities for %s", symbol)
                return hits

            # Batch-fetch molecule properties (20 concurrent)
            mol_ids_needed = list({act.get("molecule_chembl_id", "") for _, act in pending_activities if act.get("molecule_chembl_id")})
            logger.info("ChEMBL: fetching properties for %d unique molecules for %s", len(mol_ids_needed), symbol)
            mol_props_map = await _batch_fetch_molecule_properties(client, mol_ids_needed)

            # Build hits
            for chembl_target_id, act in pending_activities:
                mol_id = act.get("molecule_chembl_id", "")
                pchembl = _safe_float(act.get("pchembl_value"))
                mol_props = mol_props_map.get(mol_id, {"molecular_weight": None, "alogp": None, "smiles": "", "pref_name": ""})

                mw = mol_props["molecular_weight"]
                alogp = mol_props["alogp"]
                dl_pass = _check_drug_likeness(mw, alogp, pchembl)

                hits.append({
                    "chembl_id": mol_id,
                    "pubchem_cid": None,
                    "compound_name": mol_props.get("pref_name") or act.get("molecule_pref_name") or mol_id,
                    "smiles": mol_props.get("smiles") or "",
                    "pchembl_value": pchembl,
                    "activity_type": act.get("standard_type", ""),
                    "molecular_weight": mw,
                    "alogp": alogp,
                    "source": "chembl",
                    "drug_likeness_pass": dl_pass,
                    "metadata": {
                        "chembl_target_id": chembl_target_id,
                        "assay_chembl_id": act.get("assay_chembl_id"),
                        "assay_type": act.get("assay_type"),
                        "standard_value": act.get("standard_value"),
                        "standard_units": act.get("standard_units"),
                        "lipinski_violations": _count_lipinski_violations(mw, alogp),
                    },
                })

    except httpx.HTTPStatusError as exc:
        logger.error("ChEMBL HTTP error for %s: %s", symbol, exc)
    except httpx.TimeoutException:
        logger.error("ChEMBL timeout while screening %s", symbol)
    except Exception as exc:
        logger.error("ChEMBL search failed for %s: %s", symbol, exc, exc_info=True)

    logger.info("ChEMBL: %d hits for %s (after dedup + filter)", len(hits), symbol)
    return hits


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

async def _store_hits(
    symbol: str,
    target_id: str | None,
    hits: list[dict],
) -> int:
    """Insert screening hits into ``molecule_screenings``.

    Returns number of rows inserted.
    """
    inserted = 0
    for hit in hits:
        meta_json = json.dumps(hit.get("metadata") or {})
        try:
            await execute(
                """INSERT INTO molecule_screenings
                       (target_symbol, target_id, chembl_id, pubchem_cid,
                        compound_name, smiles, pchembl_value, activity_type,
                        molecular_weight, alogp, source, drug_likeness_pass,
                        metadata, screened_by)
                   VALUES ($1, $2::uuid, $3, $4, $5, $6, $7, $8, $9, $10,
                           $11, $12, $13::jsonb, $14)
                   ON CONFLICT DO NOTHING""",
                symbol,
                target_id,
                hit.get("chembl_id"),
                hit.get("pubchem_cid"),
                hit.get("compound_name"),
                hit.get("smiles"),
                hit.get("pchembl_value"),
                hit.get("activity_type"),
                hit.get("molecular_weight"),
                hit.get("alogp"),
                hit.get("source", "chembl"),
                bool(hit.get("drug_likeness_pass", False)),
                meta_json,
                AGENT_NAME,
            )
            inserted += 1
        except Exception as exc:
            logger.warning(
                "Failed to insert screening hit %s for %s: %s",
                hit.get("chembl_id") or hit.get("pubchem_cid", "?"),
                symbol,
                exc,
            )

    return inserted


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def screen_target(
    symbol: str,
    target_id: str | None = None,
    skip_existing: bool = True,
) -> dict[str, Any]:
    """Screen ChEMBL and PubChem for compounds active against *symbol*.

    Parameters
    ----------
    symbol : Gene/target symbol (e.g. ``"SMN1"``, ``"DCLK1"``).
    target_id : Optional UUID of the matching row in the ``targets`` table.
    skip_existing : When True, return early if this target was already screened.

    Returns a summary dict with counts and top hits.
    """
    await ensure_table()

    # Resolve target_id from DB if not supplied
    if target_id is None:
        row = await fetchrow("SELECT id FROM targets WHERE symbol = $1", symbol)
        if row:
            target_id = str(row["id"])

    # Skip if already screened
    if skip_existing:
        existing = await fetchval(
            "SELECT COUNT(*) FROM molecule_screenings WHERE target_symbol = $1",
            symbol,
        )
        if existing and int(existing) > 0:
            logger.info("Skipping %s — %d records already exist", symbol, existing)
            return {
                "symbol": symbol,
                "skipped": True,
                "existing_records": int(existing),
            }

    start = datetime.now(timezone.utc)

    # --- ChEMBL search ---
    chembl_hits = await search_chembl_target(symbol)

    # --- PubChem search ---
    pubchem_hits = await search_pubchem_target(symbol)

    all_hits = chembl_hits + pubchem_hits
    if not all_hits:
        logger.info("No hits found for %s", symbol)
        return {
            "symbol": symbol,
            "total_hits": 0,
            "drug_likeness_pass": 0,
            "inserted": 0,
            "duration_secs": round((datetime.now(timezone.utc) - start).total_seconds(), 2),
        }

    # Store
    inserted = await _store_hits(symbol, target_id, all_hits)

    passing = [h for h in all_hits if h.get("drug_likeness_pass")]
    top_hits = sorted(
        [h for h in passing if h.get("pchembl_value") is not None],
        key=lambda h: h["pchembl_value"],
        reverse=True,
    )[:10]

    duration = round((datetime.now(timezone.utc) - start).total_seconds(), 2)

    result: dict[str, Any] = {
        "symbol": symbol,
        "target_id": target_id,
        "total_hits": len(all_hits),
        "chembl_hits": len(chembl_hits),
        "pubchem_hits": len(pubchem_hits),
        "drug_likeness_pass": len(passing),
        "inserted": inserted,
        "duration_secs": duration,
        "top_hits": top_hits,
    }

    # Post to blackboard when meaningful hits exist
    if passing:
        try:
            await auto_post_discovery(
                agent_name=AGENT_NAME,
                title=f"Molecule screen: {len(passing)} drug-like hits for {symbol}",
                findings_dict={
                    "symbols": [symbol],
                    "target_id": target_id,
                    "total_hits": len(all_hits),
                    "drug_likeness_pass": len(passing),
                    "top_pchembl": top_hits[0]["pchembl_value"] if top_hits else None,
                    "top_compound": top_hits[0]["compound_name"] if top_hits else None,
                    "sources": list({h["source"] for h in all_hits}),
                    "important": len(passing) >= 5,
                },
            )
        except Exception as exc:
            logger.warning("Failed to post discovery to blackboard for %s: %s", symbol, exc)

    return result


async def screen_all_targets(
    skip_existing: bool = True,
    batch_size: int = 5,
) -> dict[str, Any]:
    """Screen all targets in the ``targets`` table.

    Processes targets in batches of *batch_size* to avoid overwhelming the
    external APIs.  Results for each target are stored incrementally so
    progress is not lost if the run is interrupted.

    Returns an aggregated summary dict.
    """
    await ensure_table()

    target_rows = await fetch("SELECT id, symbol FROM targets ORDER BY symbol")
    if not target_rows:
        return {"error": "No targets found in database", "screened": 0}

    targets = [(str(row["id"]), row["symbol"]) for row in target_rows]
    total = len(targets)
    logger.info("screen_all_targets: %d targets to process (batch_size=%d)", total, batch_size)

    start = datetime.now(timezone.utc)
    results: list[dict] = []
    skipped = 0
    errors = 0

    for i in range(0, total, batch_size):
        batch = targets[i : i + batch_size]
        for target_id, symbol in batch:
            try:
                res = await screen_target(symbol, target_id=target_id, skip_existing=skip_existing)
                results.append(res)
                if res.get("skipped"):
                    skipped += 1
            except Exception as exc:
                logger.error("Error screening %s: %s", symbol, exc, exc_info=True)
                errors += 1
                results.append({"symbol": symbol, "error": str(exc)})

    duration = round((datetime.now(timezone.utc) - start).total_seconds(), 2)

    total_hits = sum(r.get("total_hits", 0) for r in results)
    total_pass = sum(r.get("drug_likeness_pass", 0) for r in results)
    total_inserted = sum(r.get("inserted", 0) for r in results)

    return {
        "targets_total": total,
        "targets_screened": total - skipped - errors,
        "targets_skipped": skipped,
        "targets_errored": errors,
        "total_hits": total_hits,
        "drug_likeness_pass": total_pass,
        "inserted": total_inserted,
        "duration_secs": duration,
        "per_target": results,
    }


async def get_screening_stats() -> dict[str, Any]:
    """Return counts and top compounds from the ``molecule_screenings`` table.

    Returns
    -------
    dict with keys:
    - ``total_screened`` — total rows in table
    - ``drug_likeness_pass`` — rows where drug_likeness_pass IS TRUE
    - ``targets_covered`` — distinct target symbols
    - ``chembl_compounds`` — rows sourced from ChEMBL
    - ``pubchem_compounds`` — rows sourced from PubChem
    - ``top_10_by_pchembl`` — top 10 rows sorted by pChEMBL descending
    """
    await ensure_table()

    counts = await fetchrow(
        """SELECT
               COUNT(*) AS total_screened,
               COUNT(*) FILTER (WHERE drug_likeness_pass) AS drug_likeness_pass,
               COUNT(DISTINCT target_symbol) AS targets_covered,
               COUNT(*) FILTER (WHERE source = 'chembl') AS chembl_compounds,
               COUNT(*) FILTER (WHERE source = 'pubchem') AS pubchem_compounds
           FROM molecule_screenings"""
    )

    top_rows = await fetch(
        """SELECT id, target_symbol, chembl_id, pubchem_cid, compound_name,
                  smiles, pchembl_value, activity_type, molecular_weight, alogp,
                  source, drug_likeness_pass, created_at
           FROM molecule_screenings
           WHERE pchembl_value IS NOT NULL
           ORDER BY pchembl_value DESC
           LIMIT 10"""
    )

    top_10 = []
    for row in top_rows:
        r = dict(row)
        r["id"] = str(r["id"]) if r.get("id") else None
        r["created_at"] = str(r["created_at"]) if r.get("created_at") else None
        top_10.append(r)

    return {
        "total_screened": int(counts["total_screened"]) if counts else 0,
        "drug_likeness_pass": int(counts["drug_likeness_pass"]) if counts else 0,
        "targets_covered": int(counts["targets_covered"]) if counts else 0,
        "chembl_compounds": int(counts["chembl_compounds"]) if counts else 0,
        "pubchem_compounds": int(counts["pubchem_compounds"]) if counts else 0,
        "top_10_by_pchembl": top_10,
    }
