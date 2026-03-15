#!/usr/bin/env python3
"""Migrate SMA Platform from SQLite to PostgreSQL.

Steps:
1. Create PostgreSQL schema from db/schema.sql
2. Export all data from SQLite
3. Import into PostgreSQL with type conversions
4. Verify row counts match

Usage:
    python scripts/migrate_sqlite_to_pg.py

Requires:
    pip install asyncpg aiosqlite
"""

import asyncio
import json
import os
import re
import sqlite3
import sys
from datetime import date, datetime, timezone
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

SQLITE_PATH = os.environ.get("SQLITE_PATH", str(PROJECT_ROOT / "sma_platform.db"))
PG_DSN = os.environ.get("PG_DSN", "postgresql://sma:sma-research-2026@localhost:5432/sma_platform")
SCHEMA_PATH = PROJECT_ROOT / "db" / "schema.sql"

# Tables in dependency order (parents first)
TABLES = [
    "sources",
    "targets",
    "drugs",
    "trials",
    "datasets",
    "claims",
    "evidence",
    "graph_edges",
    "hypotheses",
    "ingestion_log",
    "contact_messages",
    "agent_runs",
    "cross_species_targets",
]

# Columns that are TEXT[] in PG but TEXT (JSON) in SQLite
ARRAY_COLUMNS = {
    "sources": {"authors"},
    "drugs": {"brand_names", "targets", "approved_for"},
    "trials": {"conditions"},
    "hypotheses": {"supporting_evidence", "contradicting_evidence"},
    "graph_edges": {"evidence_ids"},
    "ingestion_log": {"errors"},
}

# Columns that are JSONB in PG but TEXT in SQLite
JSONB_COLUMNS = {
    "sources": {"metadata"},
    "targets": {"identifiers", "metadata"},
    "drugs": {"metadata"},
    "trials": {"interventions", "locations", "metadata"},
    "datasets": {"metadata"},
    "claims": {"metadata"},
    "evidence": {"metadata"},
    "graph_edges": {"metadata"},
    "hypotheses": {"metadata"},
    "ingestion_log": {"metadata"},
    "agent_runs": {"input", "output"},
}


# Columns that are DATE in PG but TEXT in SQLite
DATE_COLUMNS = {
    "sources": {"pub_date"},
    "trials": {"start_date", "completion_date"},
}

# Columns that are TIMESTAMPTZ in PG but TEXT in SQLite
TIMESTAMP_COLUMNS = {
    "sources": {"created_at", "updated_at"},
    "targets": {"created_at", "updated_at"},
    "drugs": {"created_at", "updated_at"},
    "trials": {"created_at", "updated_at"},
    "datasets": {"created_at", "updated_at"},
    "claims": {"created_at"},
    "evidence": {"created_at"},
    "graph_edges": {"created_at"},
    "hypotheses": {"created_at", "updated_at"},
    "ingestion_log": {"run_at"},
    "contact_messages": {"created_at"},
    "agent_runs": {"started_at", "finished_at"},
    "cross_species_targets": {"created_at"},
}

# Month abbreviations for PubMed-style dates
MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


def parse_date(val):
    """Parse various date string formats to datetime.date."""
    if val is None or val == "":
        return None
    if isinstance(val, date):
        return val

    val = str(val).strip()

    # YYYY-Mon-DD (PubMed format: "2026-Mar-12")
    m = re.match(r"^(\d{4})-([A-Za-z]{3})-(\d{1,2})$", val)
    if m:
        year, mon, day = int(m.group(1)), MONTH_MAP.get(m.group(2), 1), int(m.group(3))
        return date(year, mon, day)

    # YYYY-MM-DD
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", val)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # YYYY-MM
    m = re.match(r"^(\d{4})-(\d{2})$", val)
    if m:
        return date(int(m.group(1)), int(m.group(2)), 1)

    # Mon YYYY (e.g., "Jan 2026")
    m = re.match(r"^([A-Za-z]{3})\s+(\d{4})$", val)
    if m:
        return date(int(m.group(2)), MONTH_MAP.get(m.group(1), 1), 1)

    return None


def parse_timestamp(val):
    """Parse timestamp string to datetime."""
    if val is None or val == "":
        return None
    if isinstance(val, datetime):
        return val

    val = str(val).strip()

    # YYYY-MM-DD HH:MM:SS
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})", val)
    if m:
        return datetime(
            int(m.group(1)), int(m.group(2)), int(m.group(3)),
            int(m.group(4)), int(m.group(5)), int(m.group(6)),
            tzinfo=timezone.utc,
        )

    # YYYY-MM-DDTHH:MM:SS
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})", val)
    if m:
        return datetime(
            int(m.group(1)), int(m.group(2)), int(m.group(3)),
            int(m.group(4)), int(m.group(5)), int(m.group(6)),
            tzinfo=timezone.utc,
        )

    # Fall back to date parsing + midnight
    d = parse_date(val)
    if d:
        return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)

    return None


def json_to_pg_array(val):
    """Convert JSON array string to PostgreSQL array."""
    if val is None:
        return None
    try:
        parsed = json.loads(val) if isinstance(val, str) else val
        if isinstance(parsed, list):
            return parsed
        return [str(parsed)]
    except (json.JSONDecodeError, TypeError):
        if isinstance(val, str) and val:
            return [val]
        return None


def json_to_jsonb(val):
    """Ensure value is valid JSON for JSONB column."""
    if val is None:
        return "{}"
    if isinstance(val, str):
        try:
            json.loads(val)
            return val
        except json.JSONDecodeError:
            return json.dumps(val)
    return json.dumps(val)


async def main():
    import asyncpg

    # 1. Check SQLite exists
    if not Path(SQLITE_PATH).exists():
        print(f"SQLite database not found: {SQLITE_PATH}")
        sys.exit(1)

    print(f"SQLite: {SQLITE_PATH}")
    print(f"PostgreSQL: {PG_DSN}")
    print()

    # 2. Connect to both databases
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    pg_conn = await asyncpg.connect(PG_DSN)

    # 3. Create PostgreSQL schema
    print("Creating PostgreSQL schema...")
    schema_sql = SCHEMA_PATH.read_text()
    try:
        await pg_conn.execute(schema_sql)
        print("  Schema created successfully")
    except Exception as e:
        if "already exists" in str(e):
            print(f"  Schema already exists (skipping): {e}")
        else:
            print(f"  Schema error: {e}")
            # Try statement by statement
            for stmt in schema_sql.split(";"):
                stmt = stmt.strip()
                if not stmt or stmt.startswith("--"):
                    continue
                try:
                    await pg_conn.execute(stmt + ";")
                except Exception as e2:
                    if "already exists" not in str(e2):
                        print(f"  Warning: {e2}")

    # 4. Migrate each table
    total_migrated = 0
    for table in TABLES:
        # Check if table exists in SQLite
        check = sqlite_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        if not check:
            print(f"\n{table}: not in SQLite, skipping")
            continue

        # Get SQLite rows
        rows = sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()
        if not rows:
            print(f"\n{table}: 0 rows (empty)")
            continue

        columns = rows[0].keys()
        array_cols = ARRAY_COLUMNS.get(table, set())
        jsonb_cols = JSONB_COLUMNS.get(table, set())

        # Filter columns that exist in both SQLite and PG
        # (SQLite may have extra columns like full_text that PG schema includes)
        pg_columns = set()
        try:
            col_info = await pg_conn.fetch(
                "SELECT column_name FROM information_schema.columns WHERE table_name = $1",
                table,
            )
            pg_columns = {r["column_name"] for r in col_info}
        except Exception:
            pg_columns = set(columns)

        valid_columns = [c for c in columns if c in pg_columns]

        print(f"\n{table}: {len(rows)} rows, {len(valid_columns)} columns")

        # Clear existing PG data for this table
        await pg_conn.execute(f"DELETE FROM {table}")

        # Build INSERT statement
        placeholders = ", ".join(f"${i+1}" for i in range(len(valid_columns)))
        col_list = ", ".join(valid_columns)
        insert_sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

        date_cols = DATE_COLUMNS.get(table, set())
        ts_cols = TIMESTAMP_COLUMNS.get(table, set())

        migrated = 0
        errors = 0
        for row in rows:
            values = []
            for col in valid_columns:
                val = row[col]
                if col in array_cols:
                    val = json_to_pg_array(val)
                elif col in jsonb_cols:
                    val = json_to_jsonb(val)
                elif col in date_cols:
                    val = parse_date(val)
                elif col in ts_cols:
                    val = parse_timestamp(val)
                values.append(val)

            try:
                await pg_conn.execute(insert_sql, *values)
                migrated += 1
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  Error row: {e}")
                    # Debug: show problematic values
                    for i, (c, v) in enumerate(zip(valid_columns, values)):
                        if c in array_cols or c in jsonb_cols:
                            print(f"    {c} ({type(v).__name__}): {str(v)[:100]}")

        total_migrated += migrated
        print(f"  Migrated: {migrated}, Errors: {errors}")

    # 5. Verify
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    for table in TABLES:
        check = sqlite_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        if not check:
            continue

        sqlite_count = sqlite_conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        try:
            pg_count = await pg_conn.fetchval(f"SELECT count(*) FROM {table}")
        except Exception:
            pg_count = "N/A"

        match = "OK" if sqlite_count == pg_count else "MISMATCH"
        print(f"  {table:25s}  SQLite: {sqlite_count:>6}  PG: {str(pg_count):>6}  {match}")

    print(f"\nTotal rows migrated: {total_migrated}")
    print("\nDone! Update .env to use PostgreSQL:")
    print(f"  DATABASE_URL={PG_DSN}")

    sqlite_conn.close()
    await pg_conn.close()


if __name__ == "__main__":
    asyncio.run(main())
