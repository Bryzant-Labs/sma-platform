"""API key authentication for admin/write endpoints."""

from __future__ import annotations

from fastapi import Header, HTTPException

from ..core.config import settings


async def require_admin_key(
    x_admin_key: str = Header(..., description="Admin API key for write operations"),
) -> str:
    """FastAPI dependency that enforces x-admin-key header on protected endpoints."""
    if x_admin_key != settings.sma_admin_key:
        raise HTTPException(status_code=403, detail="Invalid or missing admin key")
    return x_admin_key
