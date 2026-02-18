import os
import json
from typing import Dict, List, Optional, Any
from groq import AsyncGroq
from dotenv import load_dotenv

from backend.config import settings

load_dotenv()


class AtsScorer:
    """Scores a resume against a job description using Groq AI and ATS criteria."""

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")

        self.client = AsyncGroq(api_key=self.api_key)
        self.model_name = settings.GROQ_MODEL

        self.criteria_weights = {
            "skills_match": 30,
            "experience_level": 25,
            "education": 15,
            "keyword_density": 15,
            "formatting": 10,
            "achievements": 5,
        }

        self.prompt_template = """
        You are an expert ATS (Applicant Tracking System) analyst with 10+ years of experience in resume evaluation.
        Analyze the following resume against the job description and provide a detailed scoring and feedback.
        
        JOB TITLE: {job_title}
        COMPANY: {company_name}
        
        JOB DESCRIPTION:
        {job_description}
        
        RESUME CONTENT:
        {resume_content}
        
        Please provide your analysis in the following JSON format (return ONLY the JSON, no markdown):
        {{
            "scores": {{
                "skills_match": 0-100,
                "experience_level": 0-100,
                "education": 0-100,
                "keyword_density": 0-100,
                "formatting": 0-100,
                "achievements": 0-100
            }},
            "overall_score": 0-100,
            "strengths": ["list", "of", "strengths"],
            "weaknesses": ["list", "of", "weaknesses"],
            "suggestions": ["list", "of", "suggestions"],
            "missing_keywords": ["list", "of", "missing", "keywords"],
            "ats_optimization_tips": ["list", "of", "tips"]
        }}
        """

    async def score_resume(
        self,
        resume_data: Dict[str, Any],
        job_title: str,
        company_name: str,
        job_description: str,
    ) -> Dict[str, Any]:
        """
        Score a resume against a job description using the Groq API.

        Args:
            resume_data: Parsed resume data from resume_parser.py
            job_title: The target job title
            company_name: The target company name
            job_description: The job description text

        Returns:
            Dictionary containing scoring results and feedback
        """
        try:
            resume_content = self._prepare_resume_content(resume_data)

            prompt = self.prompt_template.format(
                job_title=job_title,
                company_name=company_name,
                job_description=job_description,
                resume_content=resume_content,
            )

            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=4096,
            )

            response_text = response.choices[0].message.content
            if not response_text:
                raise ValueError("No text content in API response")

            result = self._parse_ats_response(response_text)

            if "scores" in result:
                result["overall_score"] = self._calculate_weighted_score(result["scores"])

            return {"success": True, "result": result}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _prepare_resume_content(self, resume_data: Dict[str, Any]) -> str:
        """Convert parsed resume data into a structured content summary."""
        sections = []

        if resume_data.get("name"):
            sections.append(f"Name: {resume_data['name']}")

        contact_info = []
        if resume_data.get("email"):
            contact_info.append(f"Email: {resume_data['email']}")
        if resume_data.get("phone"):
            contact_info.append(f"Phone: {resume_data['phone']}")
        if contact_info:
            sections.append("CONTACT: " + " | ".join(contact_info))

        if resume_data.get("summary"):
            sections.append(f"SUMMARY:\n{resume_data['summary']}")

        if resume_data.get("skills"):
            sections.append(f"SKILLS:\n{', '.join(resume_data['skills'])}")

        if resume_data.get("experience"):
            sections.append("EXPERIENCE:")
            for exp in resume_data["experience"]:
                exp_text = f"- {exp.get('title', '')}"
                if exp.get("company"):
                    exp_text += f" at {exp['company']}"
                if exp.get("duration"):
                    exp_text += f" ({exp['duration']})"
                sections.append(exp_text)
                if exp.get("description"):
                    if isinstance(exp["description"], list):
                        for desc in exp["description"]:
                            sections.append(f"  • {desc}")
                    else:
                        sections.append(f"  • {exp['description']}")

        if resume_data.get("education"):
            sections.append("EDUCATION:")
            for edu in resume_data["education"]:
                edu_text = f"- {edu.get('degree', '')}"
                if edu.get("institution"):
                    edu_text += f" from {edu['institution']}"
                if edu.get("year"):
                    edu_text += f" ({edu['year']})"
                sections.append(edu_text)

        if resume_data.get("projects"):
            sections.append("PROJECTS:")
            for proj in resume_data["projects"]:
                proj_text = f"- {proj.get('title', 'Untitled Project')}"
                if proj.get("description"):
                    if isinstance(proj["description"], list):
                        proj_text += ": " + "; ".join(proj["description"])
                    else:
                        proj_text += f": {proj['description']}"
                sections.append(proj_text)

        if resume_data.get("certifications"):
            sections.append("CERTIFICATIONS:")
            for cert in resume_data["certifications"]:
                if isinstance(cert, dict):
                    cert_text = f"- {cert.get('name', '')}"
                    if cert.get("issuer"):
                        cert_text += f" from {cert['issuer']}"
                    if cert.get("year"):
                        cert_text += f" ({cert['year']})"
                    sections.append(cert_text)
                else:
                    sections.append(f"- {cert}")

        return "\n\n".join(sections)

    def _parse_ats_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the ATS response into a structured dictionary."""
        try:
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()

            result = json.loads(json_str)

            required_fields = ["scores", "overall_score", "strengths", "weaknesses", "suggestions"]
            for field in required_fields:
                if field not in result:
                    if field == "scores":
                        result[field] = {k: 0 for k in self.criteria_weights}
                    elif field == "overall_score":
                        result[field] = 0
                    else:
                        result[field] = []

            return result

        except Exception as e:
            raise ValueError(f"Failed to parse ATS response: {str(e)}")

    def _calculate_weighted_score(self, scores: Dict[str, int]) -> float:
        """Calculate the weighted overall score based on criteria weights."""
        if not scores:
            return 0.0

        total_weight = sum(self.criteria_weights.values())
        if total_weight == 0:
            return 0.0

        weighted_sum = 0
        for criterion, weight in self.criteria_weights.items():
            score = scores.get(criterion, 0)
            weighted_sum += score * weight

        return round(weighted_sum / total_weight, 1)


# -------------------------------------------------------------------
# Lazy singleton to avoid crash on import when env var is missing
# -------------------------------------------------------------------
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
    """Score a resume against a job description using ATS criteria."""
    return await get_ats_scorer().score_resume(
        resume_data, job_title, company_name, job_description
    )