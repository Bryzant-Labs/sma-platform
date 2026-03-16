"""Database abstraction layer.

Supports both PostgreSQL (asyncpg) and SQLite (aiosqlite).
Auto-detects from DATABASE_URL: postgresql:// → asyncpg, sqlite:// or file path → aiosqlite.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

# Global state
_db_type: str = "sqlite"  # "postgres" or "sqlite"
_pool: Any = None  # asyncpg.Pool or None
_sqlite_path: str = ""


class DictRow(dict):
    """Dict-like row that also supports attribute access (like asyncpg.Record)."""
    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)


def _pg_to_sqlite_query(query: str, args: tuple) -> tuple[str, tuple]:
    """Convert PostgreSQL $N params to SQLite ? params.

    Also strips PostgreSQL-specific casts like ::jsonb, ::int[], ::date, ::text.
    Handles reused $N references (e.g. WHERE col1 = $1 OR col2 = $1) by
    duplicating the corresponding argument for each occurrence.
    Translates NOW() to datetime('now') and ILIKE to LIKE.
    """
    # Remove PostgreSQL type casts
    query = re.sub(r'::\w+\[\]', '', query)
    query = re.sub(r'::\w+', '', query)

    # Translate PostgreSQL functions to SQLite equivalents
    query = re.sub(r'\bNOW\(\)', "datetime('now')", query, flags=re.IGNORECASE)
    query = re.sub(r'\bILIKE\b', 'LIKE', query, flags=re.IGNORECASE)

    # Replace $N with ? — handle reused params by duplicating args
    # Find all $N references in order of appearance
    param_refs = re.findall(r'\$(\d+)', query)
    if not param_refs:
        return query, args

    # Build new args tuple in order of appearance
    new_args = []
    for ref in param_refs:
        idx = int(ref) - 1  # $1 → index 0
        if idx < len(args):
            new_args.append(args[idx])

    # Replace all $N with ? (all occurrences)
    query = re.sub(r'\$\d+', '?', query)

    return query, tuple(new_args)


# ---------- Init / Close ----------

async def init_pool(dsn: str, **kwargs: Any) -> Any:
    """Initialize database connection. Auto-detects postgres vs sqlite from DSN."""
    global _db_type, _pool, _sqlite_path

    if dsn.startswith("postgresql://") or dsn.startswith("postgres://"):
        import asyncpg
        _db_type = "postgres"
        _pool = await asyncpg.create_pool(dsn, min_size=kwargs.get("min_size", 2), max_size=kwargs.get("max_size", 10))
        return _pool
    else:
        # SQLite path
        _db_type = "sqlite"
        path = dsn.replace("sqlite:///", "").replace("sqlite://", "")
        if not path or path == ":memory:":
            path = ":memory:"
        _sqlite_path = path

        # Ensure parent dir exists
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)

        # Create DB and enable WAL mode
        conn = sqlite3.connect(path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.close()
        return path


async def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _db_type == "postgres" and _pool:
        await _pool.close()
        _pool = None


def _get_sqlite_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_sqlite_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ---------- Query helpers ----------

async def fetch(query: str, *args: Any) -> list[DictRow]:
    if _db_type == "postgres" and _pool is None:
        raise RuntimeError("Database pool not initialized — call init_pool() first")
    if _db_type == "postgres":
        async with _pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [DictRow(r) for r in rows]
    else:
        q, a = _pg_to_sqlite_query(query, args)
        conn = _get_sqlite_conn()
        try:
            rows = conn.execute(q, a).fetchall()
            return [DictRow(zip(row.keys(), row)) for row in rows]
        finally:
            conn.close()


async def fetchrow(query: str, *args: Any) -> DictRow | None:
    if _db_type == "postgres" and _pool is None:
        raise RuntimeError("Database pool not initialized — call init_pool() first")
    if _db_type == "postgres":
        async with _pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return DictRow(row) if row else None
    else:
        q, a = _pg_to_sqlite_query(query, args)
        conn = _get_sqlite_conn()
        try:
            row = conn.execute(q, a).fetchone()
            return DictRow(zip(row.keys(), row)) if row else None
        finally:
            conn.close()


async def fetchval(query: str, *args: Any) -> Any:
    if _db_type == "postgres" and _pool is None:
        raise RuntimeError("Database pool not initialized — call init_pool() first")
    if _db_type == "postgres":
        async with _pool.acquire() as conn:
            return await conn.fetchval(query, *args)
    else:
        q, a = _pg_to_sqlite_query(query, args)
        conn = _get_sqlite_conn()
        try:
            row = conn.execute(q, a).fetchone()
            return row[0] if row else None
        finally:
            conn.close()


async def execute(query: str, *args: Any) -> str:
    if _db_type == "postgres" and _pool is None:
        raise RuntimeError("Database pool not initialized — call init_pool() first")
    if _db_type == "postgres":
        async with _pool.acquire() as conn:
            return await conn.execute(query, *args)
    else:
        q, a = _pg_to_sqlite_query(query, args)
        conn = _get_sqlite_conn()
        try:
            cursor = conn.execute(q, a)
            conn.commit()
            if cursor.lastrowid:
                return f"INSERT 0 {cursor.rowcount}"
            return f"UPDATE {cursor.rowcount}"
        finally:
            conn.close()


async def execute_script(sql: str) -> None:
    """Execute a multi-statement SQL script."""
    if _db_type == "postgres":
        async with _pool.acquire() as conn:
            await conn.execute(sql)
    else:
        conn = _get_sqlite_conn()
        try:
            conn.executescript(sql)
            conn.commit()
        finally:
            conn.close()
