"""Blackboard Architecture — shared knowledge space for research agents.

Agents post discoveries (new evidence, hypotheses, claims) and read each
other's findings via this module.  All messages are persisted in the
``agent_messages`` table and expire after 30 days by default.

Part of Phase 10.2 — Agent Message Bus.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from ..core.database import execute, execute_script, fetch, fetchrow, fetchval

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DDL — executed lazily via ensure_table()
# ---------------------------------------------------------------------------

_CREATE_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name TEXT NOT NULL,
    message_type TEXT NOT NULL,
    priority TEXT DEFAULT 'normal',
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    targets TEXT[],
    metadata JSONB DEFAULT '{}',
    read_by TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days')
);
CREATE INDEX IF NOT EXISTS idx_agent_messages_type ON agent_messages(message_type);
CREATE INDEX IF NOT EXISTS idx_agent_messages_agent ON agent_messages(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_messages_created ON agent_messages(created_at DESC);
"""

_table_ready = False


# ---------------------------------------------------------------------------
# Table bootstrap
# ---------------------------------------------------------------------------

async def ensure_table() -> None:
    """Create the ``agent_messages`` table and indexes if they do not exist."""
    global _table_ready
    if _table_ready:
        return
    try:
        await execute_script(_CREATE_TABLE_DDL)
        _table_ready = True
        logger.info("agent_messages table ensured")
    except Exception as exc:
        logger.error("Failed to create agent_messages table: %s", exc, exc_info=True)
        raise


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

async def post_message(
    agent_name: str,
    message_type: str,
    title: str,
    content: str,
    targets: list[str] | None = None,
    priority: str = "normal",
    metadata: dict[str, Any] | None = None,
) -> str:
    """Insert a message onto the blackboard and return its UUID as a string."""
    await ensure_table()

    meta_json = json.dumps(metadata) if metadata else "{}"
    row = await fetchrow(
        """INSERT INTO agent_messages
               (agent_name, message_type, title, content, targets, priority, metadata)
           VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
           RETURNING id""",
        agent_name,
        message_type,
        title,
        content,
        targets,
        priority,
        meta_json,
    )
    msg_id = str(row["id"])
    logger.info(
        "Blackboard message posted: id=%s agent=%s type=%s title=%s",
        msg_id, agent_name, message_type, title,
    )
    return msg_id


async def get_messages(
    agent_name: str | None = None,
    message_type: str | None = None,
    since: str | None = None,
    unread_by: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Read messages with optional filters.

    Parameters
    ----------
    agent_name : filter by posting agent
    message_type : filter by message type (e.g. ``discovery``, ``hypothesis``)
    since : ISO-8601 datetime string — only messages created after this
    unread_by : agent name — only messages this agent has *not* read yet
    limit : max rows (default 50)
    offset : pagination offset (default 0)
    """
    await ensure_table()

    conditions: list[str] = []
    params: list[Any] = []
    idx = 1

    if agent_name:
        conditions.append(f"agent_name = ${idx}")
        params.append(agent_name)
        idx += 1

    if message_type:
        conditions.append(f"message_type = ${idx}")
        params.append(message_type)
        idx += 1

    if since:
        conditions.append(f"created_at >= ${idx}::timestamptz")
        params.append(since)
        idx += 1

    if unread_by:
        conditions.append(f"NOT (${idx} = ANY(read_by))")
        params.append(unread_by)
        idx += 1

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    params.append(limit)
    limit_idx = idx
    idx += 1
    params.append(offset)
    offset_idx = idx

    query = f"""
        SELECT id, agent_name, message_type, priority, title, content,
               targets, metadata, read_by, created_at, expires_at
        FROM agent_messages
        {where}
        ORDER BY created_at DESC
        LIMIT ${limit_idx} OFFSET ${offset_idx}
    """

    rows = await fetch(query, *params)

    results: list[dict] = []
    for row in rows:
        r = dict(row)
        r["id"] = str(r["id"]) if r.get("id") else None
        r["created_at"] = str(r["created_at"]) if r.get("created_at") else None
        r["expires_at"] = str(r["expires_at"]) if r.get("expires_at") else None
        # Parse metadata from JSON string if needed
        if isinstance(r.get("metadata"), str):
            try:
                r["metadata"] = json.loads(r["metadata"])
            except (json.JSONDecodeError, TypeError):
                pass
        results.append(r)

    return results


async def mark_read(message_id: str, agent_name: str) -> bool:
    """Append *agent_name* to the ``read_by`` array of a message.

    Returns ``True`` if the message was found and updated, ``False`` otherwise.
    """
    await ensure_table()

    row = await fetchrow(
        "SELECT id FROM agent_messages WHERE id = $1::uuid",
        message_id,
    )
    if not row:
        return False

    await execute(
        """UPDATE agent_messages
           SET read_by = array_append(read_by, $1)
           WHERE id = $2::uuid
             AND NOT ($1 = ANY(read_by))""",
        agent_name,
        message_id,
    )
    logger.debug("Message %s marked read by %s", message_id, agent_name)
    return True


async def get_unread_count(agent_name: str) -> dict:
    """Count unread messages by type for *agent_name*.

    Returns a dict like ``{"discovery": 3, "hypothesis": 1, "total": 4}``.
    """
    await ensure_table()

    rows = await fetch(
        """SELECT message_type, COUNT(*) AS cnt
           FROM agent_messages
           WHERE NOT ($1 = ANY(read_by))
           GROUP BY message_type""",
        agent_name,
    )

    result: dict[str, int] = {}
    total = 0
    for row in rows:
        count = int(row["cnt"])
        result[row["message_type"]] = count
        total += count

    result["total"] = total
    return result


async def cleanup_expired() -> int:
    """Delete messages whose ``expires_at`` has passed. Returns deleted count."""
    await ensure_table()

    result = await execute(
        "DELETE FROM agent_messages WHERE expires_at < CURRENT_TIMESTAMP",
    )
    # asyncpg execute returns e.g. "DELETE 5"
    try:
        count = int(result.split()[-1])
    except (ValueError, IndexError):
        count = 0

    if count:
        logger.info("Cleaned up %d expired blackboard messages", count)
    return count


async def get_agent_activity(days: int = 7) -> list[dict]:
    """Messages posted per agent per day for the last *days* days.

    Returns a list of ``{agent_name, date, count}`` dicts ordered by date desc.
    """
    await ensure_table()

    rows = await fetch(
        """SELECT agent_name,
                  DATE(created_at) AS day,
                  COUNT(*) AS cnt
           FROM agent_messages
           WHERE created_at >= CURRENT_TIMESTAMP - ($1 || ' days')::interval
           GROUP BY agent_name, DATE(created_at)
           ORDER BY day DESC, agent_name""",
        str(days),
    )

    return [
        {
            "agent_name": row["agent_name"],
            "date": str(row["day"]),
            "count": int(row["cnt"]),
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Convenience helper
# ---------------------------------------------------------------------------

async def auto_post_discovery(
    agent_name: str,
    title: str,
    findings_dict: dict[str, Any],
) -> str:
    """Post a discovery message with auto-formatted content.

    - Serialises *findings_dict* as JSON content.
    - Extracts ``targets`` from the dict if present (gene symbols, drug names).
    - Sets priority to ``high`` when the findings include a confidence >=0.8
      or an ``important`` flag, otherwise ``normal``.
    """
    content = json.dumps(findings_dict, indent=2, default=str)

    # Extract target symbols if present
    targets: list[str] = []
    for key in ("targets", "genes", "symbols", "drugs"):
        val = findings_dict.get(key)
        if isinstance(val, list):
            targets.extend(str(v) for v in val)
        elif isinstance(val, str) and val:
            targets.append(val)

    # Determine priority
    priority = "normal"
    confidence = findings_dict.get("confidence", 0)
    if (isinstance(confidence, (int, float)) and confidence >= 0.8) or findings_dict.get("important"):
        priority = "high"

    metadata = {
        "auto_posted": True,
        "keys": list(findings_dict.keys()),
    }

    return await post_message(
        agent_name=agent_name,
        message_type="discovery",
        title=title,
        content=content,
        targets=targets or None,
        priority=priority,
        metadata=metadata,
    )
