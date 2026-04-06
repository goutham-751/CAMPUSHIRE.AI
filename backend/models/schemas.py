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
    confidence_metrics: Optional[Any] = None


class VoicesResponse(BaseModel):
    voices: Dict[str, List[str]] = Field(default_factory=dict)


# ──────────────────── Multi-Agent Panel ─────────────────────────


class AgentVerdict(BaseModel):
    """One agent's individual evaluation."""
    agent_id: str = ""
    agent_name: str = ""
    agent_role: str = ""
    agent_emoji: str = ""
    agent_color: str = ""
    score: float = 0
    verdict: str = ""
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    key_observation: str = ""


class PanelEvaluationRequest(BaseModel):
    """Request body for multi-agent panel evaluation."""
    question: str = Field(..., min_length=1, max_length=2000)
    answer: str = Field(..., min_length=1, max_length=5000)
    job_title: str = Field(..., min_length=1, max_length=200)


class PanelEvaluationResponse(BaseModel):
    """Response from the multi-agent hiring committee."""
    success: bool = True
    agents: List[AgentVerdict] = Field(default_factory=list)
    aggregated_score: float = 0
    consensus: str = ""
    disagreements: str = ""
    final_recommendation: str = ""
    overall_verdict: str = ""
    error: Optional[str] = None


# ──────────────────── Confidence Metrics ────────────────────────


class FillerWordDetail(BaseModel):
    word: str = ""
    count: int = 0


class ConfidenceMetrics(BaseModel):
    """Speech confidence analysis results."""
    success: bool = True
    confidence_score: float = 0
    duration_seconds: float = 0
    word_count: int = 0
    wpm: float = 0
    wpm_score: float = 0
    wpm_assessment: str = ""
    filler_count: int = 0
    filler_words: List[FillerWordDetail] = Field(default_factory=list)
    filler_score: float = 0
    pause_ratio: float = 0
    pause_score: float = 0
    tips: List[str] = Field(default_factory=list)
    error: Optional[str] = None


# ──────────────────── Semantic Matching ─────────────────────────


class SemanticMatchResult(BaseModel):
    """Result of a single resume-to-JD semantic match."""
    success: bool = True
    overall_similarity: float = 0
    section_scores: Dict[str, float] = Field(default_factory=dict)
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    job_title: str = ""
    match_grade: str = ""
    rank: Optional[int] = None


class SemanticMatchResponse(BaseModel):
    success: bool = True
    result: Optional[SemanticMatchResult] = None
    error: Optional[str] = None


class BatchMatchResponse(BaseModel):
    success: bool = True
    results: List[SemanticMatchResult] = Field(default_factory=list)
    total: int = 0
    error: Optional[str] = None
