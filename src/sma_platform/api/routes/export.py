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
