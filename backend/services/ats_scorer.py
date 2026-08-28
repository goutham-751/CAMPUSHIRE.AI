"""
Deterministic ATS scorer.

Computes criterion scores from resume evidence + JD requirements using fixed
weights. No LLM involvement in scoring. Same inputs → same outputs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.services.jd_extractor import (
    education_rank,
    extract_jd_requirements,
    infer_resume_education_level,
)
from backend.services.resume_extractors import count_quantified_bullets
from backend.services.semantic_matcher import compute_semantic_match
from backend.services.skill_lexicon import canonicalize_skills, extract_skills_from_text


class AtsScorer:
    """Scores a resume against a job description with a fixed weighted rubric."""

    criteria_weights = {
        "skills_match": 30,
        "experience_level": 25,
        "education": 15,
        "keyword_density": 15,
        "formatting": 10,
        "achievements": 5,
    }

    def score_resume(
        self,
        resume_data: Dict[str, Any],
        job_title: str,
        company_name: str,
        job_description: str,
    ) -> Dict[str, Any]:
        try:
            requirements = extract_jd_requirements(job_description, job_title)
            evidence = self._build_evidence(resume_data, requirements, job_description)

            scores = {
                "skills_match": self._score_skills(evidence),
                "experience_level": self._score_experience(evidence),
                "education": self._score_education(evidence),
                "keyword_density": self._score_keywords(resume_data, job_description, job_title),
                "formatting": self._score_formatting(evidence),
                "achievements": self._score_achievements(evidence),
            }
            # When JD has no lexicon skills, skills_match tracks TF-IDF keyword overlap instead of a flat constant
            if not evidence["required_skills"]:
                scores["skills_match"] = scores["keyword_density"]

            overall = self._calculate_weighted_score(scores)
            narrative = self._build_narrative(scores, evidence, job_title, company_name)

            result = {
                "scores": scores,
                "overall_score": overall,
                "strengths": narrative["strengths"],
                "weaknesses": narrative["weaknesses"],
                "suggestions": narrative["suggestions"],
                "missing_keywords": evidence["missing_skills"][:20],
                "ats_optimization_tips": narrative["ats_optimization_tips"],
                "evidence": {
                    "matched_skills": evidence["matched_skills"],
                    "missing_skills": evidence["missing_skills"],
                    "resume_years": evidence["resume_years"],
                    "required_years": evidence["required_years"],
                    "resume_education": evidence["resume_education"],
                    "required_education": evidence["required_education"],
                    "sections_present": evidence["sections_present"],
                    "quantified_bullets": evidence["quantified_bullets"],
                    "total_bullets": evidence["total_bullets"],
                    "scoring_engine": "deterministic_v1",
                },
            }
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _build_evidence(
        self,
        resume_data: Dict[str, Any],
        requirements: Dict[str, Any],
        job_description: str,
    ) -> Dict[str, Any]:
        resume_skills = canonicalize_skills(resume_data.get("skills") or [])
        # Also pick up skills buried in experience text
        exp_blob = " ".join(
            " ".join(exp.get("description") or [])
            + " "
            + str(exp.get("title") or "")
            for exp in (resume_data.get("experience") or [])
        )
        resume_skills = canonicalize_skills(
            resume_skills + extract_skills_from_text(exp_blob)
        )

        required = canonicalize_skills(requirements.get("required_skills") or [])
        if not required:
            # Fallback: scan JD anyway (already done in extractor) — keep empty
            required = extract_skills_from_text(job_description)

        resume_set = {s.lower(): s for s in resume_skills}
        matched = [resume_set[s.lower()] for s in required if s.lower() in resume_set]
        # Prefer canonical from required list for missing
        missing = [s for s in required if s.lower() not in resume_set]

        resume_years = float(resume_data.get("years_experience") or 0)
        if resume_years <= 0:
            resume_years = self._estimate_years(resume_data)

        quantified, total_bullets = count_quantified_bullets(resume_data)

        sections_present = {
            "skills": bool(resume_data.get("skills")),
            "experience": bool(resume_data.get("experience")),
            "education": bool(resume_data.get("education")),
            "summary": bool(resume_data.get("summary")),
            "projects": bool(resume_data.get("projects")),
            "contact": bool(resume_data.get("email") or resume_data.get("phone")),
        }

        return {
            "resume_skills": resume_skills,
            "required_skills": required,
            "matched_skills": matched,
            "missing_skills": missing,
            "resume_years": resume_years,
            "required_years": requirements.get("required_years"),
            "resume_education": infer_resume_education_level(resume_data.get("education") or []),
            "required_education": requirements.get("required_education"),
            "sections_present": sections_present,
            "quantified_bullets": quantified,
            "total_bullets": total_bullets,
            "name": resume_data.get("name") or "",
        }

    @staticmethod
    def _estimate_years(resume_data: Dict[str, Any]) -> float:
        jobs = resume_data.get("experience") or []
        if not jobs:
            return 0.0
        # Weak fallback: 1.5 years per role if dates were unparsable
        return round(len(jobs) * 1.5, 1)

    def _score_skills(self, evidence: Dict[str, Any]) -> float:
        required = evidence["required_skills"]
        matched = evidence["matched_skills"]
        if not required:
            # No lexicon skills in JD — fall back to TF-IDF keyword density already computed later.
            # Use a conservative placeholder only when we have neither required skills nor resume skills.
            if not evidence["resume_skills"]:
                return 25.0
            # Neutral-low: cannot claim a strong skills match without JD skill signals
            return 45.0
        ratio = len(matched) / len(required)
        return round(min(100.0, ratio * 100.0), 1)

    def _score_experience(self, evidence: Dict[str, Any]) -> float:
        required = evidence["required_years"]
        actual = evidence["resume_years"]
        if required is None:
            if actual <= 0:
                return 40.0
            if actual >= 5:
                return 90.0
            if actual >= 2:
                return 75.0
            return 55.0

        if actual <= 0:
            return 15.0
        if actual >= required:
            return 100.0
        return round(max(0.0, (actual / required) * 100.0), 1)

    def _score_education(self, evidence: Dict[str, Any]) -> float:
        required = evidence["required_education"]
        actual = evidence["resume_education"]
        if not required:
            return 80.0 if actual else 50.0
        req_rank = education_rank(required)
        act_rank = education_rank(actual)
        if act_rank <= 0:
            return 20.0
        if act_rank >= req_rank:
            return 100.0
        # One level below → 60, two → 35, etc.
        gap = req_rank - act_rank
        return round(max(0.0, 100.0 - gap * 40.0), 1)

    def _score_keywords(
        self,
        resume_data: Dict[str, Any],
        job_description: str,
        job_title: str,
    ) -> float:
        match = compute_semantic_match(resume_data, job_description, job_title)
        if not match.get("success"):
            return 0.0
        return float(match.get("overall_similarity") or 0.0)

    def _score_formatting(self, evidence: Dict[str, Any]) -> float:
        sections = evidence["sections_present"]
        checks = [
            sections.get("contact"),
            sections.get("skills"),
            sections.get("experience"),
            sections.get("education"),
            sections.get("summary") or sections.get("projects"),
            bool(evidence.get("name")),
        ]
        return round((sum(1 for c in checks if c) / len(checks)) * 100.0, 1)

    def _score_achievements(self, evidence: Dict[str, Any]) -> float:
        total = evidence["total_bullets"]
        quantified = evidence["quantified_bullets"]
        if total <= 0:
            return 20.0
        ratio = quantified / total
        # 40%+ quantified bullets → full marks
        return round(min(100.0, (ratio / 0.4) * 100.0), 1)

    def _calculate_weighted_score(self, scores: Dict[str, float]) -> float:
        if not scores:
            return 0.0
        total_weight = sum(self.criteria_weights.values())
        if total_weight == 0:
            return 0.0
        weighted_sum = 0.0
        for criterion, weight in self.criteria_weights.items():
            weighted_sum += float(scores.get(criterion, 0)) * weight
        return round(weighted_sum / total_weight, 1)

    def _build_narrative(
        self,
        scores: Dict[str, float],
        evidence: Dict[str, Any],
        job_title: str,
        company_name: str,
    ) -> Dict[str, List[str]]:
        strengths: List[str] = []
        weaknesses: List[str] = []
        suggestions: List[str] = []
        tips: List[str] = []

        role = job_title or "the target role"
        company = f" at {company_name}" if company_name else ""

        matched = evidence["matched_skills"]
        missing = evidence["missing_skills"]

        if scores["skills_match"] >= 70 and matched:
            strengths.append(
                f"Strong skills overlap for {role}{company}: {', '.join(matched[:6])}."
            )
        elif matched:
            strengths.append(f"Matched skills include: {', '.join(matched[:5])}.")

        if scores["experience_level"] >= 75:
            years = evidence["resume_years"]
            strengths.append(f"Experience level looks solid (~{years} years parsed from resume).")

        if scores["education"] >= 80 and evidence["resume_education"]:
            strengths.append(
                f"Education level ({evidence['resume_education'].replace('_', ' ')}) meets or exceeds the posting."
            )

        if scores["formatting"] >= 80:
            strengths.append("Resume structure includes the core ATS-friendly sections.")

        if scores["achievements"] >= 70:
            strengths.append(
                f"Quantified impact detected in {evidence['quantified_bullets']} bullet(s)."
            )

        if not strengths:
            strengths.append("Resume was parsed successfully; continue aligning content to the job description.")

        if missing:
            weaknesses.append(f"Missing keywords relative to the JD: {', '.join(missing[:8])}.")
            suggestions.append(f"Add or demonstrate these skills where truthful: {', '.join(missing[:6])}.")
            tips.append("Mirror exact JD skill phrasing in a dedicated Skills section.")

        if scores["skills_match"] < 50:
            weaknesses.append("Skills match is below 50% against extracted JD requirements.")

        req_years = evidence["required_years"]
        if req_years is not None and evidence["resume_years"] < req_years:
            weaknesses.append(
                f"Parsed experience (~{evidence['resume_years']} years) is below the JD ask ({req_years}+ years)."
            )
            suggestions.append(
                "Clarify tenure with explicit date ranges (e.g. Jan 2020 – Present) so years are measurable."
            )

        if scores["education"] < 50:
            weaknesses.append("Education level appears below what the job description requests.")
            suggestions.append("List degree, institution, and graduation year clearly under Education.")

        if scores["formatting"] < 70:
            missing_sections = [
                name for name, present in evidence["sections_present"].items() if not present
            ]
            if missing_sections:
                weaknesses.append(f"Weak ATS structure — missing: {', '.join(missing_sections)}.")
                tips.append("Use standard headings: Summary, Skills, Experience, Education.")

        if scores["achievements"] < 50:
            weaknesses.append("Few quantified achievements detected in bullets.")
            suggestions.append("Add metrics (%, $, user counts) to at least 40% of experience bullets.")
            tips.append("Replace vague verbs with measurable outcomes ATS scanners and humans both prefer.")

        if scores["keyword_density"] < 40:
            suggestions.append("Increase overlap with JD terminology in summary and experience bullets.")
            tips.append("Reuse high-signal nouns from the job description without keyword stuffing.")

        if not weaknesses:
            weaknesses.append("No major structural gaps detected against this JD.")
        if not suggestions:
            suggestions.append(f"Keep tailoring examples in Experience to {role}{company}.")
        if not tips:
            tips.append("Export to a text-based PDF/DOCX so ATS parsers can read all sections.")

        return {
            "strengths": strengths[:5],
            "weaknesses": weaknesses[:5],
            "suggestions": suggestions[:5],
            "ats_optimization_tips": tips[:5],
        }


_ats_scorer: Optional[AtsScorer] = None


def get_ats_scorer() -> AtsScorer:
    global _ats_scorer
    if _ats_scorer is None:
        _ats_scorer = AtsScorer()
    return _ats_scorer


async def score_resume_ats(
    resume_data: Dict[str, Any],
    job_title: str,
    company_name: str,
    job_description: str,
) -> Dict[str, Any]:
    """Score a resume against a job description using deterministic ATS criteria."""
    return get_ats_scorer().score_resume(
        resume_data, job_title, company_name, job_description
    )


def score_resume_ats_sync(
    resume_data: Dict[str, Any],
    job_title: str,
    company_name: str,
    job_description: str,
) -> Dict[str, Any]:
    """Synchronous deterministic scoring (tests / internal use)."""
    return get_ats_scorer().score_resume(
        resume_data, job_title, company_name, job_description
    )
