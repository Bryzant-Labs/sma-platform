"""Add claim_number SERIAL column to claims table and backfill existing rows."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sma_platform.core.config import settings
from sma_platform.core.database import close_pool, execute, fetch, init_pool


async def migrate():
    await init_pool(settings.database_url)

    print("Adding claim_number column...")
    await execute("""
        ALTER TABLE claims
        ADD COLUMN IF NOT EXISTS claim_number SERIAL
    """)

    print("Backfilling claim numbers ordered by created_at...")
    await execute("""
        WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at, id) AS rn
            FROM claims
        )
        UPDATE claims SET claim_number = numbered.rn
        FROM numbered WHERE claims.id = numbered.id
    """)

    print("Adding unique constraint...")
    try:
        await execute("""
            ALTER TABLE claims
            ADD CONSTRAINT claims_claim_number_unique UNIQUE (claim_number)
        """)
    except Exception as e:
        print(f"Constraint may already exist: {e}")

    row = await fetch("SELECT MAX(claim_number) AS max_num FROM claims")
    max_num = row[0]["max_num"] if row and row[0]["max_num"] else 0
    print(f"Max claim_number: {max_num}")
    await execute(f"SELECT setval(pg_get_serial_sequence('claims', 'claim_number'), {max_num})")

    print("Creating index...")
    await execute("CREATE INDEX IF NOT EXISTS idx_claims_number ON claims(claim_number)")

    print("Migration complete!")
    await close_pool()


if __name__ == "__main__":
    asyncio.run(migrate())
