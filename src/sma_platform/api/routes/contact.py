"""Contact form endpoint with rate limiting, Slack notification, and admin access."""

from __future__ import annotations

import logging
import re
import time
from collections import defaultdict

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator

from ...core.config import settings
from ...core.database import execute, execute_script, fetch
from ..auth import require_admin_key

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory rate limiter: IP -> list of timestamps
_rate_store: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT = 3  # max submissions per window
_RATE_WINDOW = 3600  # 1 hour in seconds

# Table is created by db/schema.sql — these are SQLite fallbacks only
_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS contact_messages (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL,
    message     TEXT NOT NULL,
    ip_address  TEXT,
    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""

_MIGRATE_SQL = """
ALTER TABLE contact_messages ADD COLUMN ip_address TEXT;
"""


class ContactMessage(BaseModel):
    name: str
    email: str
    message: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 200:
            raise ValueError("Name is required (max 200 chars)")
        return v

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Invalid email address")
        if len(v) > 254:
            raise ValueError("Email too long")
        return v

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message is required")
        if len(v) > 5000:
            raise ValueError("Message too long (max 5000 chars)")
        return v


def _check_rate_limit(ip: str) -> bool:
    """Return True if request is allowed, False if rate limited."""
    now = time.time()
    _rate_store[ip] = [t for t in _rate_store[ip] if now - t < _RATE_WINDOW]
    if len(_rate_store[ip]) >= _RATE_LIMIT:
        return False
    _rate_store[ip].append(now)
    return True


async def _notify_slack(msg: ContactMessage, ip: str) -> None:
    """Send contact form notification to Slack #masterbots channel."""
    if not settings.slack_bot_token or not settings.slack_channel_id:
        logger.warning("Slack not configured — skipping notification")
        return

    text = (
        f"*New SMA Platform Contact Message*\n"
        f"*From:* {msg.name} ({msg.email})\n"
        f"*IP:* {ip}\n"
        f"---\n"
        f"{msg.message}"
    )

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {settings.slack_bot_token}"},
                json={"channel": settings.slack_channel_id, "text": text},
            )
            data = resp.json()
            if not data.get("ok"):
                logger.error("Slack API error: %s", data.get("error"))
    except Exception as e:
        logger.error("Failed to send Slack notification: %s", e)


@router.post("/contact")
async def submit_contact(msg: ContactMessage, request: Request):
    """Store a contact form submission and notify via Slack."""
    # Rate limit by IP
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Too many messages. Please try again later.")

    await execute_script(_TABLE_SQL)
    try:
        await execute_script(_MIGRATE_SQL)
    except Exception:
        pass  # Column already exists

    await execute(
        "INSERT INTO contact_messages (name, email, message, ip_address) VALUES ($1, $2, $3, $4)",
        msg.name,
        msg.email,
        msg.message,
        client_ip,
    )

    # Send Slack notification (fire-and-forget, don't block response)
    await _notify_slack(msg, client_ip)

    return {"status": "ok", "message": "Thank you for your message. We will get back to you."}


@router.get("/admin/messages", dependencies=[Depends(require_admin_key)])
async def list_messages():
    """List all contact form messages (admin only)."""

    await execute_script(_TABLE_SQL)
    try:
        await execute_script(_MIGRATE_SQL)
    except Exception:
        pass
    rows = await fetch(
        "SELECT id, name, email, message, ip_address, created_at FROM contact_messages ORDER BY created_at DESC"
    )
    return {"messages": rows, "total": len(rows)}
