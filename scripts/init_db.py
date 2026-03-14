"""Initialize the database schema.

Auto-detects SQLite vs PostgreSQL from DATABASE_URL.
Run: python scripts/init_db.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sma_platform.core.config import settings
from sma_platform.core.database import close_pool, execute_script, init_pool


async def init():
    dsn = settings.database_url
    is_pg = dsn.startswith("postgresql://") or dsn.startswith("postgres://")

    if is_pg:
        print(f"Connecting to PostgreSQL: {dsn.split('@')[1] if '@' in dsn else '(local)'}")
        schema_path = Path(__file__).parent.parent / "db" / "schema.sql"
    else:
        db_path = dsn.replace("sqlite:///", "").replace("sqlite://", "")
        print(f"Using SQLite: {db_path}")
        schema_path = Path(__file__).parent.parent / "db" / "schema_sqlite.sql"

    await init_pool(dsn)

    schema_sql = schema_path.read_text(encoding="utf-8")
    print("Applying schema...")
    await execute_script(schema_sql)
    print("Schema applied successfully.")

    await close_pool()


if __name__ == "__main__":
    asyncio.run(init())
