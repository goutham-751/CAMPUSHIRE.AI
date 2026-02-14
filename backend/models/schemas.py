"""
Pydantic request/response schemas for all CampusHire.AI API endpoints.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ──────────────────────────── Health ────────────────────────────


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = ""
    message: str = "CampusHire.AI backend is running"


# ──────────────────────────── Errors ────────────────────────────


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None


# ──────────────────────────── Resume ────────────────────────────


class ResumeParseResponse(BaseModel):
    """Response returned after parsing a resume file."""
    success: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)


class ResumeScoreRequest(BaseModel):
    """Extra fields sent alongside the uploaded resume for ATS scoring."""
    job_title: str = Field(..., min_length=1, max_length=200)
    company_name: str = Field(..., min_length=1, max_length=200)
    job_description: str = Field(..., min_length=10, max_length=10000)


class ScoreDetail(BaseModel):
    skills_match: float = 0 
    experience_level: float = 0
    education: float = 0
    keyword_density: float = 0
    formatting: float = 0
    achievements: float = 0


class ATSScoreResponse(BaseModel):
    success: bool = True
    overall_score: float = 0
    scores: Optional[ScoreDetail] = None
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    ats_optimization_tips: List[str] = Field(default_factory=list)


class FeedbackRequest(BaseModel):
    """Extra fields sent alongside the uploaded resume for feedback generation."""
    job_title: str = Field(..., min_length=1, max_length=200)
    company_name: str = Field(..., min_length=1, max_length=200)
    job_description: str = Field(..., min_length=10, max_length=10000)


class FeedbackSection(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    areas_for_improvement: List[str] = Field(default_factory=list)
    ats_optimization: List[str] = Field(default_factory=list)
    skill_gap_analysis: List[str] = Field(default_factory=list)
    actionable_recommendations: List[str] = Field(default_factory=list)


class FeedbackResponse(BaseModel):
    success: bool = True
    feedback: Optional[FeedbackSection] = None
    raw_response: Optional[str] = None


# ─────────────────────────── Interview ──────────────────────────


class InterviewQuestionsRequest(BaseModel):
    """Extra fields sent alongside the uploaded resume for question generation."""
    job_title: str = Field(..., min_length=1, max_length=200)
    company_name: str = Field(..., min_length=1, max_length=200)
    job_description: str = Field(..., min_length=10, max_length=10000)
    num_questions: int = Field(default=10, ge=1, le=30)
    industry: str = Field(default="technology", max_length=100)


class InterviewQuestion(BaseModel):
    question: str
    category: str
    difficulty: str
    suggested_answer: Optional[str] = None


class InterviewQuestionsResponse(BaseModel):
    success: bool = True
    questions: List[InterviewQuestion] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


class InterviewAnswerRequest(BaseModel):
    """Request body when evaluating a candidate's answer."""
    question: str = Field(..., min_length=1, max_length=2000)
    answer: str = Field(..., min_length=1, max_length=5000)
    job_title: str = Field(..., min_length=1, max_length=200)


class AnswerEvaluationResponse(BaseModel):
    success: bool = True
    score: float = 0
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    sample_answer: Optional[str] = None


# ──────────────────────────── Voice ─────────────────────────────


class TTSRequest(BaseModel):
    """Request body for text-to-speech."""
    text: str = Field(..., min_length=1, max_length=5000)
    language: str = Field(default="en", max_length=10)
    voice_id: Optional[str] = None
    output_format: str = Field(default="mp3", pattern=r"^(mp3|wav)$")


class STTResponse(BaseModel):
    success: bool = True
    text: Optional[str] = None
    language: str = "en-US"
    confidence: float = 0.0
    error: Optional[str] = None


class VoicesResponse(BaseModel):
    voices: Dict[str, List[str]] = Field(default_factory=dict)
