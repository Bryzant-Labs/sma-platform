"""Blackboard API endpoints — Agent Message Bus (Phase 10.2).

Exposes the shared blackboard for reading/posting agent messages,
viewing statistics, marking messages as read, and cleaning up expired entries.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from ...reasoning.blackboard import (
    cleanup_expired,
    get_agent_activity,
    get_messages,
    get_unread_count,
    mark_read,
    post_message,
)
from ...core.database import fetch, fetchval
from ..auth import require_admin_key

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class PostMessageBody(BaseModel):
    agent_name: str = Field(..., min_length=1, max_length=100)
    message_type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    targets: list[str] | None = None
    priority: str = Field(default="normal", pattern="^(low|normal|high|critical)$")
    metadata: dict[str, Any] | None = None


class MarkReadBody(BaseModel):
    agent_name: str = Field(..., min_length=1, max_length=100)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/blackboard")
async def list_messages(
    agent_name: str | None = Query(default=None, description="Filter by posting agent"),
    message_type: str | None = Query(default=None, description="Filter by message type"),
    since: str | None = Query(default=None, description="ISO-8601 datetime — messages after this"),
    unread_by: str | None = Query(default=None, description="Agent name — only unread messages"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List blackboard messages with optional filters."""
    try:
        messages = await get_messages(
            agent_name=agent_name,
            message_type=message_type,
            since=since,
            unread_by=unread_by,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        logger.error("Failed to list blackboard messages: %s", exc, exc_info=True)
        return {
            "messages": [],
            "count": 0,
            "offset": offset,
            "note": "agent_messages table may not exist yet. Post a message first.",
        }

    return {"messages": messages, "count": len(messages), "offset": offset}


@router.get("/blackboard/stats")
async def blackboard_stats():
    """Aggregate statistics: counts by type, by agent, total, and recent activity."""
    try:
        by_type = await fetch(
            "SELECT message_type, COUNT(*) AS cnt FROM agent_messages GROUP BY message_type ORDER BY cnt DESC"
        )
        by_agent = await fetch(
            "SELECT agent_name, COUNT(*) AS cnt FROM agent_messages GROUP BY agent_name ORDER BY cnt DESC"
        )
        total = await fetchval("SELECT COUNT(*) FROM agent_messages")
        activity = await get_agent_activity(days=7)
    except Exception as exc:
        logger.error("Failed to get blackboard stats: %s", exc, exc_info=True)
        return {
            "total_messages": 0,
            "by_type": {},
            "by_agent": {},
            "recent_activity": [],
            "note": "agent_messages table may not exist yet.",
        }

    return {
        "total_messages": int(total) if total else 0,
        "by_type": {row["message_type"]: int(row["cnt"]) for row in by_type},
        "by_agent": {row["agent_name"]: int(row["cnt"]) for row in by_agent},
        "recent_activity": activity,
    }


@router.post("/blackboard", dependencies=[Depends(require_admin_key)])
async def create_message(body: PostMessageBody):
    """Post a new message to the blackboard. Requires x-admin-key header."""
    try:
        msg_id = await post_message(
            agent_name=body.agent_name,
            message_type=body.message_type,
            title=body.title,
            content=body.content,
            targets=body.targets,
            priority=body.priority,
            metadata=body.metadata,
        )
    except Exception as exc:
        logger.error("Failed to post blackboard message: %s", exc, exc_info=True)
        return {"error": f"Failed to post message: {exc}"}

    return {"id": msg_id, "status": "posted"}


@router.post("/blackboard/{message_id}/read", dependencies=[Depends(require_admin_key)])
async def mark_message_read(message_id: str, body: MarkReadBody):
    """Mark a message as read by the given agent. Requires x-admin-key header."""
    try:
        found = await mark_read(message_id, body.agent_name)
    except Exception as exc:
        logger.error("Failed to mark message read: %s", exc, exc_info=True)
        return {"error": f"Failed to mark read: {exc}"}

    if not found:
        return {"error": "Message not found", "message_id": message_id}

    return {"status": "read", "message_id": message_id, "agent_name": body.agent_name}


@router.post("/blackboard/cleanup", dependencies=[Depends(require_admin_key)])
async def trigger_cleanup():
    """Delete expired blackboard messages. Requires x-admin-key header."""
    try:
        count = await cleanup_expired()
    except Exception as exc:
        logger.error("Failed to cleanup blackboard: %s", exc, exc_info=True)
        return {"error": f"Cleanup failed: {exc}"}

    return {"deleted": count, "status": "cleanup_complete"}
