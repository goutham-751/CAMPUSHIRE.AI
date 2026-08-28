"""
Hybrid resume feedback generator.

Primary path is deterministic (built from ATS evidence). Optional Groq rewrite
polishes prose but cannot invent scores — facts are locked from the scorer.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from backend.config import settings
from backend.services.ats_scorer import score_resume_ats_sync

logger = logging.getLogger("campushire.feedback")


class FeedbackGenerator:
    """Builds actionable feedback from deterministic ATS facts."""

    async def generate_feedback(
        self,
        resume_data: Dict[str, Any],
        job_title: str,
        company_name: str,
        job_description: str,
    ) -> Dict[str, Any]:
        try:
            ats = score_resume_ats_sync(
                resume_data, job_title, company_name, job_description
            )
            if not ats.get("success"):
                return {"success": False, "error": ats.get("error", "ATS scoring failed")}

            result = ats["result"]
            feedback = self._from_ats_result(result, job_title, company_name)

            raw_response = None
            if settings.GROQ_API_KEY:
                polished, raw_response = await self._optional_llm_rewrite(
                    feedback, result, job_title, company_name
                )
                if polished:
                    feedback = polished

            return {
                "success": True,
                "feedback": feedback,
                "raw_response": raw_response,
                "ats_overall_score": result.get("overall_score"),
                "scoring_engine": "deterministic_v1",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _from_ats_result(
        self,
        result: Dict[str, Any],
        job_title: str,
        company_name: str,
    ) -> Dict[str, List[str]]:
        evidence = result.get("evidence") or {}
        scores = result.get("scores") or {}
        role = job_title or "the target role"
        company = f" at {company_name}" if company_name else ""

        strengths = list(result.get("strengths") or [])
        weaknesses = list(result.get("weaknesses") or [])
        suggestions = list(result.get("suggestions") or [])
        tips = list(result.get("ats_optimization_tips") or [])
        missing = list(result.get("missing_keywords") or evidence.get("missing_skills") or [])
        matched = list(evidence.get("matched_skills") or [])

        skill_gap: List[str] = []
        if missing:
            skill_gap.append(f"Skill gaps vs {role}{company}: {', '.join(missing[:10])}.")
        if matched:
            skill_gap.append(f"Already covered: {', '.join(matched[:8])}.")
        if scores.get("skills_match") is not None:
            skill_gap.append(f"Skills match score: {scores['skills_match']}/100 (deterministic).")

        if not skill_gap:
            skill_gap.append("No major skill gaps extracted from the job description lexicon.")

        recommendations = list(suggestions)
        if evidence.get("required_years") is not None:
            recommendations.append(
                f"JD asks for ~{evidence['required_years']}+ years; resume parsed ~{evidence.get('resume_years', 0)} years."
            )
        if (evidence.get("quantified_bullets") or 0) < 2:
            recommendations.append(
                "Add at least two bullets with measurable outcomes (%, $, scale)."
            )
        if not recommendations:
            recommendations.append(f"Continue aligning Experience bullets to {role}{company}.")

        return {
            "strengths": strengths[:6],
            "areas_for_improvement": weaknesses[:6],
            "ats_optimization": tips[:6],
            "skill_gap_analysis": skill_gap[:6],
            "actionable_recommendations": recommendations[:6],
        }

    async def _optional_llm_rewrite(
        self,
        feedback: Dict[str, List[str]],
        ats_result: Dict[str, Any],
        job_title: str,
        company_name: str,
    ) -> tuple[Optional[Dict[str, List[str]]], Optional[str]]:
        """
        Ask Groq to rephrase locked facts. On any failure, return (None, None)
        so the caller keeps deterministic feedback.
        """
        try:
            from groq import AsyncGroq

            client = AsyncGroq(api_key=settings.GROQ_API_KEY)
            facts = {
                "overall_score": ats_result.get("overall_score"),
                "scores": ats_result.get("scores"),
                "matched_skills": (ats_result.get("evidence") or {}).get("matched_skills"),
                "missing_skills": ats_result.get("missing_keywords"),
                "feedback_draft": feedback,
                "job_title": job_title,
                "company_name": company_name,
            }
            prompt = (
                "You are a career coach. Rewrite the feedback bullets to be clearer and more "
                "actionable. You MUST NOT invent new scores, skills, or metrics. Only rephrase "
                "using the provided facts. Return ONLY JSON with keys: strengths, "
                "areas_for_improvement, ats_optimization, skill_gap_analysis, "
                "actionable_recommendations — each a list of strings.\n\n"
                f"FACTS:\n{json.dumps(facts, indent=2)}"
            )

            response = await client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2048,
            )
            try:
                from backend.telemetry import record_llm_usage
                record_llm_usage(getattr(response, "usage", None))
            except Exception:
                pass
            raw = response.choices[0].message.content or ""
            polished = self._parse_json_feedback(raw)
            if not polished:
                return None, raw
            # Ensure all keys exist; fall back per-section
            merged = dict(feedback)
            for key in feedback.keys():
                vals = polished.get(key)
                if isinstance(vals, list) and vals:
                    merged[key] = [str(v) for v in vals][:8]
            return merged, raw
        except Exception as e:
            logger.warning("Optional feedback rewrite skipped: %s", e)
            return None, None

    @staticmethod
    def _parse_json_feedback(response_text: str) -> Optional[Dict[str, Any]]:
        raw = (response_text or "").strip()
        if not raw:
            return None
        if "```json" in raw:
            raw = raw.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in raw:
            raw = raw.split("```", 1)[1].split("```", 1)[0].strip()
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end == -1:
            return None
        try:
            data = json.loads(raw[start : end + 1])
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            return None


_feedback_generator: Optional[FeedbackGenerator] = None


def get_feedback_generator() -> FeedbackGenerator:
    global _feedback_generator
    if _feedback_generator is None:
        _feedback_generator = FeedbackGenerator()
    return _feedback_generator


async def generate_resume_feedback(
    resume_data: Dict[str, Any],
    job_title: str,
    company_name: str,
    job_description: str,
) -> Dict[str, Any]:
    """Generate feedback for a resume based on a specific job description."""
    return await get_feedback_generator().generate_feedback(
        resume_data, job_title, company_name, job_description
    )
