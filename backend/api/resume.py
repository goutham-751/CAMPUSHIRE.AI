"""
Resume API routes — upload, parse, ATS score, feedback, and semantic matching.
"""

import os
import json
import shutil
import tempfile
from typing import Optional, List
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, status

from backend.config import settings
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

router = APIRouter(prefix="/api/resume", tags=["Resume"])


# ── helpers ─────────────────────────────────────────────────────

def _validate_file(file: UploadFile) -> None:
    """Validate uploaded file type and size."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in settings.ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {settings.ALLOWED_FILE_EXTENSIONS}",
        )


async def _save_upload(file: UploadFile) -> str:
    """Save uploaded file to a temp location and return its path."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=ext, dir=settings.UPLOAD_DIR
    ) as tmp:
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
            )
        tmp.write(content)
        return tmp.name


# ── endpoints ───────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=ResumeParseResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Upload and parse a resume",
    description="Upload a PDF, DOCX, or TXT resume file. Returns structured data: name, contact, skills, experience, education, projects, etc.",
)
async def upload_resume(file: UploadFile = File(...)):
    _validate_file(file)
    file_path = await _save_upload(file)
    try:
        data = await parse_resume(file_path)
        return ResumeParseResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    finally:
        if os.path.exists(file_path):
            os.unlink(file_path)


@router.post(
    "/score",
    response_model=ATSScoreResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Score a resume against a job description",
    description="Upload a resume and provide a job description. Returns an ATS compatibility score with detailed breakdowns.",
)
async def score_resume(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    company_name: str = Form(...),
    job_description: str = Form(...),
):
    _validate_file(file)
    file_path = await _save_upload(file)
    try:
        resume_data = await parse_resume(file_path)
        result = await score_resume_ats(
            resume_data, job_title, company_name, job_description
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "ATS scoring failed"),
            )

        ats_result = result.get("result", {})
        return ATSScoreResponse(
            success=True,
            overall_score=ats_result.get("overall_score", 0),
            scores=ats_result.get("scores"),
            strengths=ats_result.get("strengths", []),
            weaknesses=ats_result.get("weaknesses", []),
            suggestions=ats_result.get("suggestions", []),
            missing_keywords=ats_result.get("missing_keywords", []),
            ats_optimization_tips=ats_result.get("ats_optimization_tips", []),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    finally:
        if os.path.exists(file_path):
            os.unlink(file_path)


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get improvement feedback for a resume",
    description="Upload a resume and provide a target job description. Returns actionable feedback grouped into strengths, areas for improvement, ATS tips, skill gaps, and recommendations.",
)
async def get_feedback(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    company_name: str = Form(...),
    job_description: str = Form(...),
):
    _validate_file(file)
    file_path = await _save_upload(file)
    try:
        resume_data = await parse_resume(file_path)
        result = await generate_resume_feedback(
            resume_data, job_title, company_name, job_description
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Feedback generation failed"),
            )

        return FeedbackResponse(
            success=True,
            feedback=result.get("feedback"),
            raw_response=result.get("raw_response"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    finally:
        if os.path.exists(file_path):
            os.unlink(file_path)


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
    job_title: str = Form(default=""),
    job_description: str = Form(...),
):
    _validate_file(file)
    file_path = await _save_upload(file)
    try:
        resume_data = await parse_resume(file_path)
        result = compute_semantic_match(resume_data, job_description, job_title)

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Semantic matching failed"),
            )

        return SemanticMatchResponse(
            success=True,
            result=SemanticMatchResult(**result),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    finally:
        if os.path.exists(file_path):
            os.unlink(file_path)


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
    job_entries: str = Form(...),
):
    _validate_file(file)
    file_path = await _save_upload(file)
    try:
        resume_data = await parse_resume(file_path)

        # Parse job entries JSON: [{"title": "...", "description": "..."}, ...]
        try:
            entries = json.loads(job_entries)
            if not isinstance(entries, list):
                raise ValueError("job_entries must be a JSON array")
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid job_entries format: {str(e)}. Expected JSON array of objects with 'title' and 'description'.",
            )

        result = batch_semantic_match(resume_data, entries)

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Batch matching failed"),
            )

        return BatchMatchResponse(
            success=True,
            results=[SemanticMatchResult(**r) for r in result.get("results", [])],
            total=result.get("total", 0),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    finally:
        if os.path.exists(file_path):
            os.unlink(file_path)


