"""
Resume API routes — upload, parse, ATS score, feedback, and semantic matching.
"""

import logging
import time
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.auth import get_current_user, rate_limit
from backend.config import settings
from backend.database import supabase
from backend.models.schemas import (
    ResumeParseResponse,
    ATSScoreResponse,
    FeedbackResponse,
    SemanticMatchResponse,
    SemanticMatchResult,
    BatchMatchResponse,
    ErrorResponse,
)
from backend.services.resume_parser import parse_resume
from backend.services.ats_scorer import score_resume_ats
from backend.services.feedback_generator import generate_resume_feedback
from backend.services.semantic_matcher import compute_semantic_match, batch_semantic_match
from backend.utils.errors import client_error_detail
from backend.utils.uploads import save_upload, safe_filename, unlink_quiet

logger = logging.getLogger("campushire.resume")

router = APIRouter(prefix="/api/resume", tags=["Resume"])

_LLM_USER = rate_limit(20)
_MAX_JOB_DESCRIPTION = 20000
_MAX_BATCH_JOBS = 8


def _persist_resume(
    user_id: str,
    filename: Optional[str],
    content_type: Optional[str],
    file_path: str,
    parsed_data: Any,
) -> None:
    """Best-effort store of the uploaded file + parsed JSON. Never raises."""
    if not supabase:
        return
    try:
        timestamp = int(time.time())
        storage_path = f"{user_id}/{timestamp}_{safe_filename(filename)}"
        with open(file_path, "rb") as f:
            supabase.storage.from_("resumes").upload(
                path=storage_path,
                file=f,
                file_options={"content-type": content_type or "application/octet-stream"},
            )
        supabase.table("resumes").insert({
            "user_id": user_id,
            "filename": safe_filename(filename),
            "file_path": storage_path,
            "parsed_data": parsed_data,
        }).execute()
    except Exception:
        logger.exception("Failed to persist resume for user %s", user_id)


# ── endpoints ───────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=ResumeParseResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Upload and parse a resume",
    description=(
        "Upload a PDF, DOCX, or TXT resume file. Deterministically extracts structured "
        "data: name, contact, skills, experience, education, projects, etc. (no LLM)."
    ),
)
async def upload_resume(
    file: UploadFile = File(...),
    user=Depends(_LLM_USER),
):
    file_path = await save_upload(file)
    try:
        data = await parse_resume(file_path)
        _persist_resume(user.id, file.filename, file.content_type, file_path, data)
        return ResumeParseResponse(success=True, data=data)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Resume upload failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=client_error_detail(e, "Failed to parse resume."),
        )
    finally:
        unlink_quiet(file_path)


@router.post(
    "/score",
    response_model=ATSScoreResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Score a resume against a job description",
    description=(
        "Upload a resume and provide a job description. Returns a deterministic ATS "
        "compatibility score (skills, experience, education, TF-IDF keywords, formatting, "
        "achievements) with evidence-driven feedback. Scoring does not call an LLM."
    ),
)
async def score_resume(
    file: UploadFile = File(...),
    job_title: str = Form(default="", max_length=200),
    company_name: str = Form(default="", max_length=200),
    job_description: str = Form(..., min_length=10, max_length=_MAX_JOB_DESCRIPTION),
    user=Depends(_LLM_USER),
):
    file_path = await save_upload(file)
    try:
        resume_data = await parse_resume(file_path)
        result = await score_resume_ats(
            resume_data, job_title, company_name, job_description
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ATS scoring failed",
            )

        _persist_resume(user.id, file.filename, file.content_type, file_path, resume_data)

        ats_result = result.get("result", {})
        evidence = ats_result.get("evidence") or {}
        return ATSScoreResponse(
            success=True,
            overall_score=ats_result.get("overall_score", 0),
            scores=ats_result.get("scores"),
            strengths=ats_result.get("strengths", []),
            weaknesses=ats_result.get("weaknesses", []),
            suggestions=ats_result.get("suggestions", []),
            missing_keywords=ats_result.get("missing_keywords", []),
            ats_optimization_tips=ats_result.get("ats_optimization_tips", []),
            scoring_engine=evidence.get("scoring_engine", "deterministic_v1"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("ATS scoring failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=client_error_detail(e, "ATS scoring failed."),
        )
    finally:
        unlink_quiet(file_path)


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get improvement feedback for a resume",
    description=(
        "Upload a resume and provide a target job description. Feedback is built from "
        "deterministic ATS evidence; an optional LLM rewrite may polish wording when Groq "
        "is configured, but scores and skill facts stay locked."
    ),
)
async def get_feedback(
    file: UploadFile = File(...),
    job_title: str = Form(default="", max_length=200),
    company_name: str = Form(default="", max_length=200),
    job_description: str = Form(..., min_length=10, max_length=_MAX_JOB_DESCRIPTION),
    user=Depends(_LLM_USER),
):
    file_path = await save_upload(file)
    try:
        resume_data = await parse_resume(file_path)
        result = await generate_resume_feedback(
            resume_data, job_title, company_name, job_description
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Feedback generation failed",
            )

        return FeedbackResponse(
            success=True,
            feedback=result.get("feedback"),
            raw_response=result.get("raw_response") if settings.DEBUG else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Feedback generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=client_error_detail(e, "Feedback generation failed."),
        )
    finally:
        unlink_quiet(file_path)


@router.post(
    "/semantic-match",
    response_model=SemanticMatchResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Semantic match resume vs job description",
    description=(
        "Upload a resume and provide a job description. Uses TF-IDF vectorization "
        "and cosine similarity to compute a mathematical semantic match score with "
        "section-level breakdowns and keyword analysis."
    ),
)
async def semantic_match(
    file: UploadFile = File(...),
    job_title: str = Form(default="", max_length=200),
    job_description: str = Form(..., min_length=10, max_length=_MAX_JOB_DESCRIPTION),
    user=Depends(_LLM_USER),
):
    file_path = await save_upload(file)
    try:
        resume_data = await parse_resume(file_path)
        result = compute_semantic_match(resume_data, job_description, job_title)

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Semantic matching failed",
            )

        return SemanticMatchResponse(
            success=True,
            result=SemanticMatchResult(**result),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Semantic matching failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=client_error_detail(e, "Semantic matching failed."),
        )
    finally:
        unlink_quiet(file_path)


@router.post(
    "/batch-match",
    response_model=BatchMatchResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Batch compare resume against multiple job descriptions",
    description=(
        "Upload a resume and provide multiple job descriptions. Returns a ranked "
        "list showing which jobs are the best semantic match for the candidate."
    ),
)
async def batch_match(
    file: UploadFile = File(...),
    job_entries: str = Form(..., max_length=80000),
    user=Depends(_LLM_USER),
):
    import json

    file_path = await save_upload(file)
    try:
        resume_data = await parse_resume(file_path)

        try:
            entries = json.loads(job_entries)
            if not isinstance(entries, list):
                raise ValueError("job_entries must be a JSON array")
            if len(entries) > _MAX_BATCH_JOBS:
                raise ValueError(f"A maximum of {_MAX_BATCH_JOBS} job descriptions is allowed")
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid job_entries format: {e}. Expected JSON array of objects with 'title' and 'description'.",
            )

        result = batch_semantic_match(resume_data, entries)

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Batch matching failed",
            )

        return BatchMatchResponse(
            success=True,
            results=[SemanticMatchResult(**r) for r in result.get("results", [])],
            total=result.get("total", 0),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Batch matching failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=client_error_detail(e, "Batch matching failed."),
        )
    finally:
        unlink_quiet(file_path)


@router.get(
    "/me",
    summary="Get all resumes for the signed-in user",
    description="Fetch stored resumes belonging to the authenticated candidate.",
)
async def get_my_resumes(user=Depends(get_current_user)):
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection not configured.",
        )

    try:
        response = (
            supabase.table("resumes")
            .select("id,filename,file_path,parsed_data,created_at")
            .eq("user_id", user.id)
            .order("created_at", desc=True)
            .execute()
        )
        return {"success": True, "data": response.data}
    except Exception as e:
        logger.exception("Failed to fetch resumes")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=client_error_detail(e, "Failed to load resumes."),
        )


@router.get(
    "/user/{user_id}",
    summary="Get all resumes for a user (self only)",
    description="Fetch stored resumes. The path user_id must match the authenticated user.",
)
async def get_user_resumes(user_id: str, user=Depends(get_current_user)):
    if user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access another user's resumes.",
        )
    return await get_my_resumes(user)
