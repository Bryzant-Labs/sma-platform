"""Claim-Target NER Enrichment via Pattern Matching.

Scans unlinked claims (subject_id IS NULL) and finds target gene/protein/drug
mentions in predicate text using case-insensitive pattern matching with word
boundaries. No external NER model required.

Problem: Only ~7,400/25,000 claims have subject_id linked to a target.
Solution: Build alias dictionaries from targets + drugs tables and match
against predicate text to retroactively link claims.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

from ..core.database import execute, fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Static alias dictionaries
# Keys: canonical DB symbol or drug name
# Values: list of text patterns (matched case-insensitively)
# ---------------------------------------------------------------------------

GENE_ALIASES: dict[str, list[str]] = {
    "SMN1": ["SMN1", "survival motor neuron 1", "SMN gene", "5q13"],
    "SMN2": ["SMN2", "survival motor neuron 2", "SMN2 copy"],
    "PLS3": ["PLS3", "plastin 3", "plastin-3", "T-plastin"],
    "STMN2": ["STMN2", "stathmin-2", "stathmin 2", "SCG10"],
    "NCALD": ["NCALD", "neurocalcin delta", "neurocalcin-delta"],
    "UBA1": ["UBA1", "ubiquitin-activating enzyme", "UAE1"],
    "CORO1C": ["CORO1C", "coronin-1C", "coronin 1C"],
    "NAIP": ["NAIP", "neuronal apoptosis inhibitory"],
    "NEDD4L": ["NEDD4L", "NEDD4-like"],
    "SMN_PROTEIN": ["SMN protein", "SMN complex", "survival motor neuron protein"],
    # Discovery targets
    "CD44": ["CD44", "CD44 antigen"],
    "SULF1": ["SULF1", "sulfatase 1", "HSULF-1"],
    "DNMT3B": ["DNMT3B", "DNA methyltransferase 3B"],
    "ANK3": ["ANK3", "ankyrin-G", "ankyrin 3", "ankyrin-3"],
    "LY96": ["LY96", "MD-2", "MD2", "lymphocyte antigen 96"],
    "SPATA18": ["SPATA18", "MIEAP"],
    "LDHA": ["LDHA", "LDH-A", "lactate dehydrogenase A"],
    "CAST": ["CAST", "calpastatin"],
    "CTNNA1": ["CTNNA1", "alpha-catenin", "alpha catenin", "catenin alpha-1"],
    "MTOR_PATHWAY": ["mTOR pathway", "mammalian target of rapamycin", "mTOR signaling"],
    "NMJ_MATURATION": ["neuromuscular junction", "NMJ maturation"],
}

DRUG_ALIASES: dict[str, list[str]] = {
    "nusinersen": ["nusinersen", "spinraza", "IONIS-SMN", "IONIS-SMNRx"],
    "risdiplam": ["risdiplam", "evrysdi", "RG7916"],
    "onasemnogene": ["onasemnogene", "zolgensma", "AVXS-101", "onasemnogene abeparvovec"],
    "4-aminopyridine": ["4-aminopyridine", "4-AP", "dalfampridine", "fampridine", "fampyra"],
    "branaplam": ["branaplam", "LMI070"],
    "reldesemtiv": ["reldesemtiv", "CK-2127107"],
    "apitegromab": ["apitegromab", "SRK-015"],
    "valproic acid": ["valproic acid", "valproate", "VPA"],
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_pattern(alias: str) -> re.Pattern:
    """Build a word-boundary regex for a single alias string.

    Uses \\b word boundaries to avoid matching "SMN" inside "DISMANTLING".
    For aliases starting/ending with non-word chars (e.g. "4-AP"), we use
    lookaround assertions instead.
    """
    escaped = re.escape(alias)
    # If alias starts with a non-word char, use lookbehind for boundary
    prefix = r"(?<!\w)" if not alias[0].isalnum() else r"\b"
    # If alias ends with a non-word char, use lookahead for boundary
    suffix = r"(?!\w)" if not alias[-1].isalnum() else r"\b"
    return re.compile(prefix + escaped + suffix, re.IGNORECASE)


def _build_match_table(
    gene_aliases: dict[str, list[str]],
    drug_aliases: dict[str, list[str]],
    db_targets: list[dict],
    db_drugs: list[dict],
) -> list[tuple[re.Pattern, str, str, str]]:
    """Build a sorted list of (pattern, entity_type, entity_key, entity_id).

    Sorted by alias length descending so longer matches are tried first.
    This prevents "SMN" from matching before "SMN2" or "STMN2".

    Returns:
        List of (compiled_regex, "target"|"drug", symbol_or_name, db_id)
    """
    # Build lookup maps from DB rows
    target_by_symbol: dict[str, str] = {}  # symbol -> id
    for t in db_targets:
        target_by_symbol[t["symbol"].upper()] = str(t["id"])

    drug_by_name: dict[str, str] = {}  # lowercase name -> id
    for d in db_drugs:
        drug_by_name[d["name"].lower()] = str(d["id"])

    entries: list[tuple[str, re.Pattern, str, str, str]] = []
    # alias_text is kept for sorting by length

    # Gene/target aliases
    for symbol, aliases in gene_aliases.items():
        tid = target_by_symbol.get(symbol.upper())
        if not tid:
            continue  # symbol not in DB — skip
        for alias in aliases:
            pat = _build_pattern(alias)
            entries.append((alias, pat, "target", symbol, tid))

    # Also add every DB target symbol that isn't already in static aliases
    static_symbols = {s.upper() for s in gene_aliases}
    for t in db_targets:
        sym = t["symbol"].upper()
        if sym not in static_symbols:
            pat = _build_pattern(t["symbol"])
            entries.append((t["symbol"], pat, "target", t["symbol"], str(t["id"])))
            # Also add full name if available
            if t.get("name"):
                name_pat = _build_pattern(t["name"])
                entries.append((t["name"], name_pat, "target", t["symbol"], str(t["id"])))

    # Drug aliases
    for drug_name, aliases in drug_aliases.items():
        did = drug_by_name.get(drug_name.lower())
        if not did:
            continue  # drug not in DB — skip
        for alias in aliases:
            pat = _build_pattern(alias)
            entries.append((alias, pat, "drug", drug_name, did))

    # Also add every DB drug name/brand not already covered
    static_drug_names = {n.lower() for n in drug_aliases}
    for d in db_drugs:
        if d["name"].lower() not in static_drug_names:
            pat = _build_pattern(d["name"])
            entries.append((d["name"], pat, "drug", d["name"], str(d["id"])))
        # Add brand names too
        brands = d.get("brand_names") or []
        if isinstance(brands, str):
            try:
                brands = json.loads(brands)
            except (json.JSONDecodeError, TypeError):
                brands = []
        for brand in brands:
            if brand and brand.strip():
                pat = _build_pattern(brand.strip())
                entries.append((brand.strip(), pat, "drug", d["name"], str(d["id"])))

    # Sort by alias length descending — longer matches first
    entries.sort(key=lambda e: len(e[0]), reverse=True)

    return [(pat, etype, ekey, eid) for (_alias, pat, etype, ekey, eid) in entries]


def _find_first_match(
    text: str,
    match_table: list[tuple[re.Pattern, str, str, str]],
) -> tuple[str, str, str] | None:
    """Find the first (longest) matching entity in text.

    Returns (entity_type, entity_key, entity_id) or None.
    """
    for pattern, entity_type, entity_key, entity_id in match_table:
        if pattern.search(text):
            return entity_type, entity_key, entity_id
    return None


def _find_all_matches(
    text: str,
    match_table: list[tuple[re.Pattern, str, str, str]],
) -> list[tuple[str, str, str]]:
    """Find all distinct matching entities in text.

    Returns list of (entity_type, entity_key, entity_id).
    De-duplicates by entity_id.
    """
    seen_ids: set[str] = set()
    results: list[tuple[str, str, str]] = []
    for pattern, entity_type, entity_key, entity_id in match_table:
        if entity_id in seen_ids:
            continue
        if pattern.search(text):
            seen_ids.add(entity_id)
            results.append((entity_type, entity_key, entity_id))
    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def get_enrichment_stats() -> dict:
    """Get current claim linking status.

    Returns counts of linked vs unlinked claims, broken down by subject_type.
    """
    total = await fetchval("SELECT COUNT(*) FROM claims")
    linked = await fetchval("SELECT COUNT(*) FROM claims WHERE subject_id IS NOT NULL")
    unlinked = await fetchval("SELECT COUNT(*) FROM claims WHERE subject_id IS NULL")

    # Breakdown by subject_type for unlinked
    type_rows = await fetch(
        """SELECT COALESCE(subject_type, 'null') AS st, COUNT(*) AS cnt
           FROM claims WHERE subject_id IS NULL
           GROUP BY subject_type ORDER BY cnt DESC"""
    )
    unlinked_by_type = {r["st"]: r["cnt"] for r in type_rows}

    # Top linked targets
    top_targets = await fetch(
        """SELECT t.symbol, COUNT(c.id) AS cnt
           FROM claims c JOIN targets t ON c.subject_id = t.id
           GROUP BY t.symbol ORDER BY cnt DESC LIMIT 20"""
    )

    # Claims with object_id linked
    obj_linked = await fetchval("SELECT COUNT(*) FROM claims WHERE object_id IS NOT NULL")

    return {
        "total_claims": total or 0,
        "subject_linked": linked or 0,
        "subject_unlinked": unlinked or 0,
        "link_rate_pct": round((linked or 0) / max(total or 1, 1) * 100, 1),
        "object_linked": obj_linked or 0,
        "unlinked_by_subject_type": unlinked_by_type,
        "top_linked_targets": {r["symbol"]: r["cnt"] for r in top_targets},
    }


async def enrich_claims(
    batch_size: int = 1000,
    dry_run: bool = False,
) -> dict:
    """Scan unlinked claims and match target/drug aliases in predicate text.

    For each unlinked claim (subject_id IS NULL), scans the predicate text
    plus metadata (subject_label, object_label) for known gene/protein/drug
    mentions using case-insensitive word-boundary matching.

    Longer aliases are matched first to avoid partial matches (e.g. STMN2
    before SMN, "4-aminopyridine" before "4-AP").

    Args:
        batch_size: Number of unlinked claims to process per batch.
        dry_run: If True, compute matches but do not update the database.

    Returns:
        Dict with enrichment results including per-target counts.
    """
    start_time = datetime.now(timezone.utc)

    # Load targets and drugs from DB
    db_targets = [dict(r) for r in await fetch("SELECT id, symbol, name FROM targets")]
    db_drugs = [dict(r) for r in await fetch("SELECT id, name, brand_names FROM drugs")]

    # Build the match table (sorted by alias length, longest first)
    match_table = _build_match_table(GENE_ALIASES, DRUG_ALIASES, db_targets, db_drugs)
    logger.info("Built match table with %d patterns", len(match_table))

    # Fetch unlinked claims in batches
    total_checked = 0
    total_subject_linked = 0
    total_object_linked = 0
    targets_linked: dict[str, int] = {}
    sample_matches: list[dict] = []

    offset = 0
    while True:
        rows = await fetch(
            """SELECT id, predicate, metadata, subject_type, object_id
               FROM claims WHERE subject_id IS NULL
               ORDER BY created_at DESC
               LIMIT $1 OFFSET $2""",
            batch_size, offset,
        )
        if not rows:
            break

        for row in rows:
            row = dict(row)
            total_checked += 1

            predicate = row.get("predicate") or ""

            # Also check metadata labels
            try:
                meta = json.loads(row.get("metadata") or "{}")
            except (json.JSONDecodeError, TypeError):
                meta = {}

            subject_label = meta.get("subject_label", "")
            object_label = meta.get("object_label", "")

            # Combine searchable text
            search_text = f"{predicate} {subject_label} {object_label}"

            # Find matches
            matches = _find_all_matches(search_text, match_table)
            if not matches:
                continue

            # First match becomes subject_id (longest/best match)
            subject_match = matches[0]
            s_type, s_key, s_id = subject_match

            # If there's a second match and object_id is NULL, use it as object
            object_match = None
            if len(matches) > 1 and row.get("object_id") is None:
                object_match = matches[1]

            # Track stats
            total_subject_linked += 1
            targets_linked[s_key] = targets_linked.get(s_key, 0) + 1

            if object_match:
                total_object_linked += 1

            # Collect samples for dry-run preview
            if len(sample_matches) < 50:
                sample_matches.append({
                    "claim_id": str(row["id"]),
                    "predicate_preview": predicate[:120],
                    "subject_match": s_key,
                    "subject_type": s_type,
                    "object_match": object_match[1] if object_match else None,
                    "all_matches": [m[1] for m in matches],
                })

            # Update DB unless dry_run
            if not dry_run:
                # Determine the subject_type value for the DB
                db_subject_type = "target" if s_type == "target" else "drug"

                if object_match:
                    o_type, _o_key, o_id = object_match
                    db_object_type = "target" if o_type == "target" else "drug"
                    await execute(
                        """UPDATE claims
                           SET subject_id = $1, subject_type = $2,
                               object_id = $3, object_type = $4,
                               metadata = jsonb_set(
                                   COALESCE(metadata, '{}'),
                                   '{enrichment}',
                                   $5::jsonb
                               )
                           WHERE id = $6""",
                        s_id, db_subject_type,
                        o_id, db_object_type,
                        json.dumps({
                            "method": "claim_enricher_ner",
                            "matched_at": datetime.now(timezone.utc).isoformat(),
                            "subject_alias": s_key,
                            "object_alias": _o_key,
                        }),
                        row["id"],
                    )
                else:
                    await execute(
                        """UPDATE claims
                           SET subject_id = $1, subject_type = $2,
                               metadata = jsonb_set(
                                   COALESCE(metadata, '{}'),
                                   '{enrichment}',
                                   $3::jsonb
                               )
                           WHERE id = $4""",
                        s_id, db_subject_type,
                        json.dumps({
                            "method": "claim_enricher_ner",
                            "matched_at": datetime.now(timezone.utc).isoformat(),
                            "subject_alias": s_key,
                        }),
                        row["id"],
                    )

        offset += batch_size

        # Safety limit — process at most 100k claims per call
        if offset >= 100_000:
            logger.warning("Reached 100k claim limit, stopping enrichment batch")
            break

    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

    # Sort targets_linked by count descending
    targets_sorted = dict(sorted(targets_linked.items(), key=lambda x: x[1], reverse=True))

    result = {
        "dry_run": dry_run,
        "claims_checked": total_checked,
        "subject_linked": total_subject_linked,
        "object_linked": total_object_linked,
        "targets_linked": targets_sorted,
        "elapsed_seconds": round(elapsed, 2),
        "patterns_loaded": len(match_table),
    }

    if dry_run:
        result["sample_matches"] = sample_matches

    logger.info(
        "Enrichment %s: checked=%d, subject_linked=%d, object_linked=%d, elapsed=%.1fs",
        "DRY-RUN" if dry_run else "COMMITTED",
        total_checked, total_subject_linked, total_object_linked, elapsed,
    )

    return result
