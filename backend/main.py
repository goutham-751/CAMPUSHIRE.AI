"""
CampusHire.AI — FastAPI Application Entry Point

Registers all API routers, configures CORS, and provides global error handling.
Start with:  uvicorn main:app --reload
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure the project root is on sys.path so "backend.*" imports resolve
# when running with `uvicorn main:app` from the backend/ directory.
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.config import settings
from backend.models.schemas import HealthResponse, ErrorResponse
from backend.api.resume import router as resume_router
from backend.api.interview import router as interview_router
from backend.api.voice import router as voice_router

# ── Logging ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("campushire")


# ── Lifespan (startup / shutdown) ───────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀  CampusHire.AI backend starting up …")
    logger.info("   Upload dir : %s", settings.UPLOAD_DIR)
    logger.info("   CORS origins: %s", settings.CORS_ORIGINS)
    yield
    logger.info("🛑  CampusHire.AI backend shutting down …")


# ── Application ─────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ───────────────────────────────────────────
app.include_router(resume_router)
app.include_router(interview_router)
app.include_router(voice_router)


# ── Global Exception Handler ──────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else None,
        },
    )


# ── Health Check ───────────────────────────────────────────────
@app.get("/", response_model=HealthResponse, tags=["Health"])
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        message="CampusHire.AI backend is running",
    )
