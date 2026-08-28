"""
CampusHire.AI — FastAPI Application Entry Point

Registers all API routers, configures CORS, and provides global error handling.
Start with:  uvicorn main:app --reload
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request, status
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
from backend.auth import get_current_user
from backend.telemetry import get_telemetry_data, record_api_call
import time

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
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# ── CORS ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# ── Telemetry Middleware ────────────────────────────────────────
@app.middleware("http")
async def telemetry_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000  # ms
    
    # Record latency for all routes; token usage is recorded only from real LLM responses
    if request.url.path != "/api/telemetry":
        record_api_call(process_time, is_llm=False)
        
    return response

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

@app.get("/api/telemetry", tags=["Health"])
async def telemetry_endpoint(_user=Depends(get_current_user)):
    return get_telemetry_data()


@app.get("/api/system/status", tags=["Health"])
async def system_status(_user=Depends(get_current_user)):
    """Live integration/config status for Settings — no hardcoded vendor claims."""
    from backend.database import supabase
    from backend.telemetry import get_telemetry_data

    groq_ok = bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY not in ("", "YOUR_GROQ_API_KEY", "your_groq_api_key_here"))
    supabase_ok = supabase is not None and bool(settings.SUPABASE_URL)
    tel = get_telemetry_data()
    payload = {
        "success": True,
        "integrations": [
            {
                "id": "groq",
                "name": "Groq Inference",
                "status": "connected" if groq_ok else "not_configured",
                "detail": settings.GROQ_MODEL if groq_ok else "Set GROQ_API_KEY",
            },
            {
                "id": "supabase",
                "name": "Supabase Auth & Storage",
                "status": "connected" if supabase_ok else "not_configured",
                "detail": "Auth + resume persistence" if supabase_ok else "Set SUPABASE_URL / SUPABASE_KEY",
            },
            {
                "id": "ats",
                "name": "Deterministic ATS",
                "status": "connected",
                "detail": "scoring_engine=deterministic_v1",
            },
            {
                "id": "voice",
                "name": "Voice (edge-tts / STT)",
                "status": "connected",
                "detail": "Browser MediaRecorder + tone metrics",
            },
        ],
        "telemetry": tel,
        "app_version": settings.APP_VERSION,
    }
    return payload
