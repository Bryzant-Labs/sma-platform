"""FastAPI application factory and lifespan management."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response as RawResponse

from ..core.config import settings
from ..core.database import close_pool, init_pool
from .routes import comparative, contact, datasets, drugs, evidence, export, ingestion, research, scoring, screening, stats, targets, trials


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage database pool lifecycle."""
    await init_pool(settings.database_url)
    yield
    await close_pool()


def create_app() -> FastAPI:
    # Conditional Swagger/ReDoc — disabled in production by default
    docs_url = "/api/v2/docs" if settings.enable_docs else None
    redoc_url = "/api/v2/redoc" if settings.enable_docs else None
    openapi_url = "/api/v2/openapi.json" if settings.enable_docs else None

    app = FastAPI(
        title="SMA Research Platform",
        description="Open-source biology-first target discovery for Spinal Muscular Atrophy",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )

    # CORS — restrict to own domain only
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://sma-research.info"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Admin-Key"],
    )

    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        # Swagger UI needs cdn.jsdelivr.net for JS/CSS
        path = request.url.path
        if path.startswith("/api/v2/docs") or path.startswith("/api/v2/redoc") or path.startswith("/api/v2/openapi"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "connect-src 'self'"
            )
        else:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data:; "
                "connect-src 'self'"
            )
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    # Register route modules
    app.include_router(stats.router, prefix="/api/v2", tags=["stats"])
    app.include_router(targets.router, prefix="/api/v2", tags=["targets"])
    app.include_router(trials.router, prefix="/api/v2", tags=["trials"])
    app.include_router(evidence.router, prefix="/api/v2", tags=["evidence"])
    app.include_router(drugs.router, prefix="/api/v2", tags=["drugs"])
    app.include_router(datasets.router, prefix="/api/v2", tags=["datasets"])
    app.include_router(ingestion.router, prefix="/api/v2", tags=["ingestion"])
    app.include_router(scoring.router, prefix="/api/v2", tags=["scoring"])
    app.include_router(contact.router, prefix="/api/v2", tags=["contact"])
    app.include_router(screening.router, prefix="/api/v2", tags=["screening"])
    app.include_router(research.router, prefix="/api/v2", tags=["research"])
    app.include_router(export.router, prefix="/api/v2", tags=["export"])
    app.include_router(comparative.router, prefix="/api/v2/comparative", tags=["comparative"])

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    # SEO/AEO static files — served via FastAPI since Nginx proxies everything
    _static_dir = Path("/var/www/sma-research.info")

    @app.get("/robots.txt", response_class=PlainTextResponse)
    async def robots_txt():
        f = _static_dir / "robots.txt"
        if f.exists():
            return PlainTextResponse(f.read_text())
        return PlainTextResponse("User-agent: *\nAllow: /\n")

    @app.get("/sitemap.xml")
    async def sitemap_xml():
        f = _static_dir / "sitemap.xml"
        if f.exists():
            return RawResponse(content=f.read_bytes(), media_type="application/xml")
        return PlainTextResponse("", status_code=404)

    @app.get("/links")
    async def links_page():
        f = _static_dir / "links.html"
        if f.exists():
            return RawResponse(content=f.read_bytes(), media_type="text/html")
        return PlainTextResponse("Not found", status_code=404)

    @app.get("/llms.txt", response_class=PlainTextResponse)
    async def llms_txt():
        f = _static_dir / "llms.txt"
        if f.exists():
            return PlainTextResponse(f.read_text())
        return PlainTextResponse("", status_code=404)

    return app
