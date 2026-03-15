"""Data export endpoints — CSV/JSON download for researchers."""

from __future__ import annotations

import csv
import io
import json
import logging

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from ...core.database import fetch

logger = logging.getLogger(__name__)
router = APIRouter()

EXPORTABLE_TABLES = frozenset({
    "targets", "drugs", "trials", "claims", "hypotheses",
    "graph_edges", "drug_outcomes", "cross_species_targets", "target_scores",
    "molecule_screenings",
})


@router.get("/export/{table_name}")
async def export_table(
    table_name: str,
    fmt: str = Query(default="json", description="Format: json or csv"),
    limit: int = Query(default=1000, ge=1, le=50000),
):
    """Export a table as JSON or CSV for research use.

    Available tables: targets, drugs, trials, claims, hypotheses,
    graph_edges, drug_outcomes, cross_species_targets, target_scores.
    """
    if table_name not in EXPORTABLE_TABLES:
        return {"error": f"Table '{table_name}' is not exportable. Available: {sorted(EXPORTABLE_TABLES)}"}

    rows = await fetch(
        f"SELECT * FROM {table_name} ORDER BY id LIMIT $1",  # noqa: S608 — table from EXPORTABLE_TABLES
        limit,
    )

    if not rows:
        return {"data": [], "total": 0}

    data = []
    for row in rows:
        r = dict(row)
        # Convert UUIDs and datetimes to strings for serialization
        for k, v in r.items():
            if hasattr(v, "hex"):  # UUID
                r[k] = str(v)
            elif hasattr(v, "isoformat"):  # datetime
                r[k] = v.isoformat()
            elif isinstance(v, list):
                r[k] = [str(x) if hasattr(x, "hex") else x for x in v]
        data.append(r)

    if fmt == "csv":
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=sma_{table_name}.csv"},
        )

    return {"table": table_name, "total": len(data), "data": data}


@router.get("/export/target/{symbol}")
async def export_target_evidence(
    symbol: str,
    fmt: str = Query(default="json", description="Format: json, csv, or bibtex"),
    limit: int = Query(default=5000, ge=1, le=50000),
):
    """Export all evidence for a specific target: claims, sources, evidence links.

    Formats:
    - json: Full evidence package with claims, sources, and metadata
    - csv: Flat CSV with one row per claim+source pair
    - bibtex: BibTeX citations for all linked papers
    """
    symbol_upper = symbol.upper()

    # Get target info
    target = await fetch(
        "SELECT id, symbol, name, target_type, description FROM targets WHERE symbol = $1",
        symbol_upper,
    )
    if not target:
        return {"error": f"Target '{symbol}' not found"}
    target_info = dict(target[0])
    tid = str(target_info["id"])

    # Get all claims mentioning this target
    claims_rows = await fetch(
        """SELECT c.id, c.claim_type, c.predicate, c.confidence, c.value, c.metadata,
                  s.title AS source_title, s.external_id AS source_pmid,
                  s.journal, s.pub_date, s.doi, s.authors, s.url AS source_url,
                  e.excerpt, e.method
           FROM claims c
           LEFT JOIN evidence e ON e.claim_id = c.id
           LEFT JOIN sources s ON e.source_id = s.id
           WHERE CAST(c.metadata AS TEXT) LIKE $1
           ORDER BY c.confidence DESC
           LIMIT $2""",
        f'%"{symbol_upper}"%', limit,
    )

    data = []
    seen_pmids: set[str] = set()
    for row in claims_rows:
        r = dict(row)
        for k, v in r.items():
            if hasattr(v, "hex"):
                r[k] = str(v)
            elif hasattr(v, "isoformat"):
                r[k] = v.isoformat()
        data.append(r)
        if r.get("source_pmid"):
            seen_pmids.add(r["source_pmid"])

    if fmt == "bibtex":
        entries = []
        for pmid in sorted(seen_pmids):
            source_row = [d for d in data if d.get("source_pmid") == pmid]
            if not source_row:
                continue
            s = source_row[0]
            authors_raw = s.get("authors", "")
            if isinstance(authors_raw, str):
                try:
                    authors_list = json.loads(authors_raw)
                except (json.JSONDecodeError, TypeError):
                    authors_list = [authors_raw] if authors_raw else []
            else:
                authors_list = authors_raw or []
            authors_bib = " and ".join(authors_list[:5])
            year = str(s.get("pub_date", ""))[:4] or "n.d."
            title = s.get("source_title", "").replace("{", "\\{").replace("}", "\\}")
            journal = s.get("journal", "")
            doi = s.get("doi", "")
            entry = (
                f"@article{{pmid{pmid},\n"
                f"  author = {{{authors_bib}}},\n"
                f"  title = {{{{{title}}}}},\n"
                f"  journal = {{{journal}}},\n"
                f"  year = {{{year}}},\n"
            )
            if doi:
                entry += f"  doi = {{{doi}}},\n"
            entry += f"  note = {{PMID: {pmid}}},\n"
            entry += f"  url = {{https://pubmed.ncbi.nlm.nih.gov/{pmid}/}}\n}}\n"
            entries.append(entry)

        bibtex_str = "\n".join(entries)
        output = io.StringIO(bibtex_str)
        return StreamingResponse(
            output,
            media_type="application/x-bibtex",
            headers={"Content-Disposition": f"attachment; filename=sma_{symbol_upper}_evidence.bib"},
        )

    if fmt == "csv":
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=sma_{symbol_upper}_evidence.csv"},
        )

    return {
        "target": target_info,
        "total_claims": len(data),
        "unique_sources": len(seen_pmids),
        "claims": data,
    }


@router.get("/evidence/gaps")
async def evidence_gaps(
    symbol: str | None = Query(default=None, description="Target symbol to analyze"),
):
    """Identify evidence gaps — where research is thin or missing for a target."""
    ALL_CLAIM_TYPES = [
        "gene_expression", "protein_interaction", "pathway_membership",
        "drug_target", "drug_efficacy", "biomarker", "splicing_event",
        "neuroprotection", "motor_function", "survival", "safety",
    ]

    targets = []
    if symbol:
        rows = await fetch(
            "SELECT id, symbol, name, target_type FROM targets WHERE symbol = $1", symbol.upper()
        )
    else:
        rows = await fetch("SELECT id, symbol, name, target_type FROM targets ORDER BY symbol")

    for t in rows:
        t = dict(t)
        tid = str(t["id"])
        sym = t["symbol"]

        # Count claims by type for this target
        type_counts = await fetch(
            """SELECT c.claim_type, count(*) AS cnt
               FROM claims c
               WHERE CAST(c.metadata AS TEXT) LIKE $1
               GROUP BY c.claim_type""",
            f'%"{sym}"%',
        )
        found_types = {r["claim_type"]: r["cnt"] for r in type_counts}
        total_claims = sum(found_types.values())

        # Count unique sources
        source_count = await fetch(
            """SELECT count(DISTINCT s.id) AS cnt
               FROM claims c
               LEFT JOIN evidence e ON e.claim_id = c.id
               LEFT JOIN sources s ON e.source_id = s.id
               WHERE CAST(c.metadata AS TEXT) LIKE $1 AND s.id IS NOT NULL""",
            f'%"{sym}"%',
        )
        n_sources = source_count[0]["cnt"] if source_count else 0

        # Identify gaps
        missing_types = [ct for ct in ALL_CLAIM_TYPES if ct not in found_types]
        weak_types = [ct for ct, n in found_types.items() if n <= 2]

        # Confidence distribution
        conf_rows = await fetch(
            """SELECT
                 count(*) FILTER (WHERE confidence >= 0.7) AS high,
                 count(*) FILTER (WHERE confidence >= 0.4 AND confidence < 0.7) AS medium,
                 count(*) FILTER (WHERE confidence < 0.4) AS low
               FROM claims WHERE CAST(metadata AS TEXT) LIKE $1""",
            f'%"{sym}"%',
        )
        conf = dict(conf_rows[0]) if conf_rows else {"high": 0, "medium": 0, "low": 0}

        targets.append({
            "symbol": sym,
            "name": t["name"],
            "total_claims": total_claims,
            "unique_sources": n_sources,
            "evidence_by_type": found_types,
            "missing_evidence_types": missing_types,
            "weak_evidence_types": weak_types,
            "confidence_distribution": conf,
            "gap_score": round(len(missing_types) / len(ALL_CLAIM_TYPES), 2),
            "suggestions": [
                f"Search PubMed for \"{sym}\" AND \"{ct.replace('_', ' ')}\" AND \"spinal muscular atrophy\""
                for ct in missing_types[:3]
            ],
        })

    targets.sort(key=lambda t: t["gap_score"], reverse=True)
    return {"targets": targets, "total": len(targets)}
