"""FastAPI application factory and lifespan management."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..core.config import settings
from ..core.database import close_pool, init_pool
from .routes import datasets, drugs, evidence, ingestion, stats, targets, trials


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage database pool lifecycle."""
    await init_pool(settings.database_url)
    yield
    await close_pool()


def create_app() -> FastAPI:
    app = FastAPI(
        title="SMA Research Platform",
        description="Open-source biology-first target discovery for Spinal Muscular Atrophy",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register route modules
    app.include_router(stats.router, prefix="/api/v2", tags=["stats"])
    app.include_router(targets.router, prefix="/api/v2", tags=["targets"])
    app.include_router(trials.router, prefix="/api/v2", tags=["trials"])
    app.include_router(evidence.router, prefix="/api/v2", tags=["evidence"])
    app.include_router(drugs.router, prefix="/api/v2", tags=["drugs"])
    app.include_router(datasets.router, prefix="/api/v2", tags=["datasets"])
    app.include_router(ingestion.router, prefix="/api/v2", tags=["ingestion"])

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    return app
