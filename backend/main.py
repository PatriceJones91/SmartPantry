"""FastAPI entry point for Smart Pantry 2.0."""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request, Response

from config import build_health_payload, get_settings, origin_is_allowed
from routes import admin, auth, barcodes, pantry, profile, recommendations, surveys
from routes.barcodes import router as barcodes_router

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("smart_pantry.api")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend API for Smart Pantry 2.0 React, Supabase, and the versioned "
        "recommendation contract."
    ),
)



@app.middleware("http")
async def request_context_and_cors(request: Request, call_next):
    """Add request tracing, timing, and deploy-safe CORS headers."""

    started = time.perf_counter()
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    origin = request.headers.get("origin")

    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled request error request_id=%s method=%s path=%s",
                request_id,
                request.method,
                request.url.path,
            )
            raise

    elapsed_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"

    if origin_is_allowed(origin, settings):
        response.headers["Access-Control-Allow-Origin"] = origin.rstrip("/")
        response.headers["Vary"] = "Origin"

    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "86400"

    logger.info(
        "request_complete request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response

@app.get("/")
def root():
    return {
        "message": "Smart Pantry API is running",
        "health": "/api/health",
        "docs": "/docs",
    }

@app.get("/api/health")
def health_check():
    """Lightweight readiness endpoint that does not expose credentials."""

    return build_health_payload(settings)


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(pantry.router, prefix="/api/pantry", tags=["pantry"])
app.include_router(surveys.router, prefix="/api/surveys", tags=["surveys"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(barcodes.router, prefix="/api/barcodes", tags=["barcodes"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])

# Backward-compatible barcode routes used by earlier frontend builds.
app.include_router(barcodes_router, prefix="/api", tags=["barcodes"])
