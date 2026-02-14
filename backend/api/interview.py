"""
Interview API routes — question generation and answer evaluation.
"""

import os
import tempfile
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, status

from backend.config import settings
from backend.models.schemas import (
    InterviewQuestionsResponse,
    InterviewAnswerRequest,
    AnswerEvaluationResponse,
    ErrorResponse,
)
from backend.services.resume_parser import parse_resume
from backend.services.question_generator import (
    generate_interview_questions,
    evaluate_interview_answer,
)

router = APIRouter(prefix="/api/interview", tags=["Interview"])


# ── helpers ─────────────────────────────────────────────────────

def _validate_file(file: UploadFile) -> None:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in settings.ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {settings.ALLOWED_FILE_EXTENSIONS}",
        )


async def _save_upload(file: UploadFile) -> str:
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
    "/questions",
    response_model=InterviewQuestionsResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Generate interview questions",
    description="Upload a resume and provide a job description. Returns tailored interview questions balanced across categories (technical, behavioral, situational, company-specific) and difficulty levels.",
)
async def generate_questions(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    company_name: str = Form(...),
    job_description: str = Form(...),
    num_questions: int = Form(default=10),
    industry: str = Form(default="technology"),
):
    _validate_file(file)
    file_path = await _save_upload(file)
    try:
        resume_data = await parse_resume(file_path)
        result = await generate_interview_questions(
            resume_data,
            job_title,
            company_name,
            job_description,
            num_questions,
            industry,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Question generation failed"),
            )

        return InterviewQuestionsResponse(
            success=True,
            questions=result.get("questions", []),
            metadata=result.get("metadata"),
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
    "/evaluate",
    response_model=AnswerEvaluationResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Evaluate an interview answer",
    description="Submit a question and the candidate's answer. Returns a score, strengths, areas for improvement, and a sample ideal answer.",
)
async def evaluate_answer(body: InterviewAnswerRequest):
    try:
        result = await evaluate_interview_answer(
            question=body.question,
            answer=body.answer,
            job_title=body.job_title,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Answer evaluation failed"),
            )

        return AnswerEvaluationResponse(
            success=True,
            score=result.get("score", 0),
            strengths=result.get("strengths", []),
            improvements=result.get("improvements", []),
            sample_answer=result.get("sample_answer"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
