"""FastAPI application factory and lifespan management."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, Response as RawResponse

from ..core.config import settings
from ..core.database import close_pool, init_pool
from .routes import aav, advanced_analytics, analytics, aso, assistant, bayesian, benchmark, binder_design, biomarker, blackboard, calibration, cascade, chat, comparative, contact, convergence, crispr, datasets, diffdock_local, digital_twin, discovery, docking, docking_proxy, drugs, dual_target, enrichment, evidence, evidence_writer, experiment_design, experiment_value, export, fair, federated, funnel, gene_versioning, gpu, graph, hit_validation, hypothesis_gen, ingestion, lab_os, literature_review, md_simulation, modifier, molecule_screen, news, nvidia_nims, omics, patent_landscape, personal_twin, predictions, preprints, prime_edit, prioritization, research, rna_binding, scoring, screening, search, source_quality, spatial_omics, splice, splice_predictor, splicing_map, stats, synergy, synthesis, target_report, targets, translation, trials, uncertainty, virtual_screening


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
        allow_methods=["GET", "POST", "PATCH", "PUT"],
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
    app.include_router(convergence.router, prefix="/api/v2", tags=["convergence"])
    app.include_router(screening.router, prefix="/api/v2", tags=["screening"])
    app.include_router(research.router, prefix="/api/v2", tags=["research"])
    app.include_router(export.router, prefix="/api/v2", tags=["export"])
    app.include_router(graph.router, prefix="/api/v2", tags=["graph"])
    app.include_router(hit_validation.router, prefix="/api/v2", tags=["hit-validation"])
    app.include_router(comparative.router, prefix="/api/v2/comparative", tags=["comparative"])
    app.include_router(preprints.router, prefix="/api/v2", tags=["preprints"])
    app.include_router(search.router, prefix="/api/v2", tags=["search"])
    app.include_router(blackboard.router, prefix="/api/v2", tags=["blackboard"])
    app.include_router(splice.router, prefix="/api/v2", tags=["splice"])
    app.include_router(splice_predictor.router, prefix="/api/v2", tags=["splice_predictor"])
    app.include_router(assistant.router, prefix="/api/v2", tags=["assistant"])
    app.include_router(chat.router, prefix="/api/v2", tags=["chat"])
    app.include_router(hypothesis_gen.router, prefix="/api/v2", tags=["hypothesis_gen"])
    app.include_router(evidence_writer.router, prefix="/api/v2", tags=["writing"])
    app.include_router(molecule_screen.router, prefix="/api/v2", tags=["screening"])
    app.include_router(crispr.router, prefix="/api/v2", tags=["crispr"])
    app.include_router(aav.router, prefix="/api/v2", tags=["aav"])
    app.include_router(gene_versioning.router, prefix="/api/v2", tags=["gene_versioning"])
    app.include_router(docking.router, prefix="/api/v2", tags=["docking"])
    app.include_router(diffdock_local.router, prefix="/api/v2", tags=["diffdock-local"])
    app.include_router(prime_edit.router, prefix="/api/v2", tags=["prime_editing"])
    app.include_router(md_simulation.router, prefix="/api/v2", tags=["md_simulation"])
    app.include_router(spatial_omics.router, prefix="/api/v2", tags=["spatial_omics"])
    app.include_router(advanced_analytics.router, prefix="/api/v2", tags=["advanced_analytics"])
    app.include_router(splicing_map.router, prefix="/api/v2", tags=["splicing_map"])
    app.include_router(rna_binding.router, prefix="/api/v2", tags=["rna_binding"])
    app.include_router(dual_target.router, prefix="/api/v2", tags=["dual_target"])
    app.include_router(digital_twin.router, prefix="/api/v2", tags=["digital_twin"])
    app.include_router(lab_os.router, prefix="/api/v2", tags=["lab_os"])
    app.include_router(federated.router, prefix="/api/v2", tags=["federated"])
    app.include_router(translation.router, prefix="/api/v2", tags=["translation"])
    app.include_router(discovery.router, prefix="/api/v2", tags=["discovery"])
    app.include_router(predictions.router, prefix="/api/v2", tags=["predictions"])
    app.include_router(gpu.router, prefix="/api/v2", tags=["gpu"])
    app.include_router(news.router, prefix="/api/v2", tags=["news"])
    app.include_router(nvidia_nims.router, prefix="/api/v2", tags=["nvidia-nims"])
    app.include_router(synergy.router, prefix="/api/v2", tags=["synergy"])
    app.include_router(synthesis.router, prefix="/api/v2", tags=["cross-paper-synthesis"])
    app.include_router(calibration.router, prefix="/api/v2", tags=["calibration"])
    app.include_router(enrichment.router, prefix="/api/v2", tags=["enrichment"])
    app.include_router(literature_review.router, prefix="/api/v2", tags=["literature-review"])
    app.include_router(source_quality.router, prefix="/api/v2", tags=["source-quality"])
    app.include_router(uncertainty.router, prefix="/api/v2", tags=["uncertainty"])
    app.include_router(benchmark.router, prefix="/api/v2", tags=["benchmark"])
    app.include_router(biomarker.router, prefix="/api/v2", tags=["biomarker"])
    app.include_router(bayesian.router, prefix="/api/v2", tags=["bayesian"])
    app.include_router(prioritization.router, prefix="/api/v2", tags=["prioritization"])
    app.include_router(experiment_value.router, prefix="/api/v2", tags=["experiment-value"])
    app.include_router(patent_landscape.router, prefix="/api/v2", tags=["patents"])
    app.include_router(modifier.router, prefix="/api/v2", tags=["modifier"])
    app.include_router(experiment_design.router, prefix="/api/v2", tags=["experiment-design"])
    app.include_router(omics.router, prefix="/api/v2", tags=["omics"])
    app.include_router(aso.router, prefix="/api/v2", tags=["aso"])
    app.include_router(personal_twin.router, prefix="/api/v2", tags=["personal-twin"])
    app.include_router(cascade.router, prefix="/api/v2", tags=["cascade"])
    app.include_router(funnel.router, prefix="/api/v2", tags=["funnel"])
    app.include_router(fair.router, prefix="/api/v2", tags=["fair"])
    app.include_router(docking_proxy.router, prefix="/api/v2", tags=["docking-proxy"])
    app.include_router(virtual_screening.router, prefix="/api/v2", tags=["virtual-screening"])
    app.include_router(binder_design.router, prefix="/api/v2", tags=["binder-design"])
    app.include_router(target_report.router, prefix="/api/v2", tags=["target-report"])
    app.include_router(analytics.router, prefix="/api/v2", tags=["analytics"])

    @app.get("/health")
    @app.get("/api/v2/health")
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
        """Serve index.html for /links — SPA handles the section routing."""
        f = _static_dir / "index.html"
        if f.exists():
            return FileResponse(str(f), media_type="text/html")
        return PlainTextResponse("Not found", status_code=404)

    @app.get("/llms.txt", response_class=PlainTextResponse)
    async def llms_txt():
        f = _static_dir / "llms.txt"
        if f.exists():
            return PlainTextResponse(f.read_text())
        return PlainTextResponse("", status_code=404)

    # --- Clean URL routing for SPA sections ---
    # Serves index.html for known section slugs so that URLs like
    # /gpu-results or /targets are shareable and SEO-friendly.
    # Registered AFTER all /api/v2 routes to avoid conflicts.
    SECTION_SLUGS = {
        "mission", "search", "ask", "chat",
        "targets", "trials", "drugs", "sources", "claims",
        "hypotheses", "predictions", "graph",
        "convergence",
        "scores", "outcomes", "screening", "candidates", "hits",
        "comparative", "directions",
        "spatial", "regen", "nmj", "multisystem", "bioelectric",
        "splicemap", "rnabind", "dualtarget", "twin",
        "molecules", "crispr", "aav", "aso", "docking", "prime", "mdsim",
        "labos", "federated", "translate", "gpu-results",
        "research", "write", "repurposing", "versions", "news",
        "analytics",
    }

    @app.get("/{section}")
    async def serve_section(section: str):
        if section in SECTION_SLUGS:
            index = _static_dir / "index.html"
            if index.exists():
                return FileResponse(str(index), media_type="text/html")
            raise HTTPException(status_code=500, detail="index.html not found")
        raise HTTPException(status_code=404, detail="Not found")

    return app
