"""API key authentication for admin/write endpoints."""

from __future__ import annotations

import secrets

from fastapi import Header, HTTPException

from ..core.config import settings


async def require_admin_key(
    x_admin_key: str = Header(..., description="Admin API key for write operations"),
) -> str:
    """FastAPI dependency that enforces x-admin-key header on protected endpoints."""
    configured_key = settings.sma_admin_key
    if not configured_key:
        raise HTTPException(status_code=503, detail="Admin authentication not configured")
    if not secrets.compare_digest(x_admin_key, configured_key):
        raise HTTPException(status_code=403, detail="Invalid or missing admin key")
    return x_admin_key
