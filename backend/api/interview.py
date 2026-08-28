"""
Interview API routes — question generation, answer evaluation,
and multi-agent panel evaluation.
"""

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.auth import rate_limit
from backend.models.schemas import (
    InterviewQuestionsResponse,
    InterviewAnswerRequest,
    AnswerEvaluationResponse,
    PanelEvaluationRequest,
    PanelEvaluationResponse,
    ErrorResponse,
)
from backend.services.resume_parser import parse_resume
from backend.services.question_generator import (
    generate_interview_questions,
    evaluate_interview_answer,
)
from backend.services.agent_evaluator import panel_evaluate as run_panel_evaluate
from backend.utils.errors import client_error_detail
from backend.utils.uploads import save_upload, unlink_quiet

logger = logging.getLogger("campushire.interview")

router = APIRouter(prefix="/api/interview", tags=["Interview"])

_LLM_USER = rate_limit(20)
_MAX_JOB_DESCRIPTION = 20000


@router.post(
    "/questions",
    response_model=InterviewQuestionsResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Generate interview questions",
    description="Upload a resume and provide a job description. Returns tailored interview questions balanced across categories (technical, behavioral, situational, company-specific) and difficulty levels.",
)
async def generate_questions(
    file: UploadFile = File(...),
    job_title: str = Form(default="", max_length=200),
    company_name: str = Form(default="", max_length=200),
    job_description: str = Form(..., min_length=10, max_length=_MAX_JOB_DESCRIPTION),
    num_questions: int = Form(default=10, ge=1, le=15),
    industry: str = Form(default="technology", max_length=100),
    user=Depends(_LLM_USER),
):
    file_path = await save_upload(file)
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
                detail="Question generation failed",
            )

        return InterviewQuestionsResponse(
            success=True,
            questions=result.get("questions", []),
            metadata=result.get("metadata"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Question generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=client_error_detail(e, "Question generation failed."),
        )
    finally:
        unlink_quiet(file_path)


@router.post(
    "/evaluate",
    response_model=AnswerEvaluationResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Evaluate an interview answer",
    description="Submit a question and the candidate's answer. Returns a score, strengths, areas for improvement, and a sample ideal answer.",
)
async def evaluate_answer(
    body: InterviewAnswerRequest,
    user=Depends(_LLM_USER),
):
    try:
        result = await evaluate_interview_answer(
            question=body.question,
            answer=body.answer,
            job_title=body.job_title,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Answer evaluation failed",
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
        logger.exception("Answer evaluation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=client_error_detail(e, "Answer evaluation failed."),
        )


@router.post(
    "/panel-evaluate",
    response_model=PanelEvaluationResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Multi-Agent Panel Evaluation",
    description=(
        "Submit a question and the candidate's answer. Three AI agent personas "
        "(Technical Lead, HR Manager, Domain Expert) independently evaluate the "
        "answer, then a moderator aggregates results and highlights disagreements."
    ),
)
async def panel_evaluate_answer(
    body: PanelEvaluationRequest,
    user=Depends(_LLM_USER),
):
    try:
        result = await run_panel_evaluate(
            question=body.question,
            answer=body.answer,
            job_title=body.job_title,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Panel evaluation failed",
            )

        return PanelEvaluationResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Panel evaluation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=client_error_detail(e, "Panel evaluation failed."),
        )
