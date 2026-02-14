import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class FeedbackGenerator:
    """Generates actionable resume improvement feedback using Gemini AI."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

        self.feedback_template = """
        You are an expert career coach and hiring manager with 15+ years of experience in technical recruiting.
        Analyze the following resume and provide specific, actionable feedback to improve it for the {job_title} role at {company_name}.
        
        Resume Summary:
        {resume_summary}
        
        Job Description:
        {job_description}
        
        Please provide feedback in the following format:
        
        1. **Strengths** (2-3 key strengths)
        2. **Areas for Improvement** (3-5 specific areas)
        3. **ATS Optimization** (how to improve for applicant tracking systems)
        4. **Skill Gap Analysis** (missing skills for this role)
        5. **Actionable Recommendations** (concrete steps to improve)
        """

    async def generate_feedback(
        self,
        resume_data: Dict[str, Any],
        job_title: str,
        company_name: str,
        job_description: str,
    ) -> Dict[str, Any]:
        """
        Generate feedback for a resume based on a specific job description.

        Args:
            resume_data: Parsed resume data from resume_parser.py
            job_title: The target job title
            company_name: The target company name
            job_description: The job description text

        Returns:
            Dictionary containing feedback sections
        """
        try:
            resume_summary = self._prepare_resume_summary(resume_data)

            prompt = self.feedback_template.format(
                job_title=job_title,
                company_name=company_name,
                resume_summary=resume_summary,
                job_description=job_description,
            )

            response = self.model.generate_content(prompt)
            feedback = self._parse_feedback_response(response.text)

            return {
                "success": True,
                "feedback": feedback,
                "raw_response": response.text,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _prepare_resume_summary(self, resume_data: Dict[str, Any]) -> str:
        """Convert parsed resume data into a structured text summary."""
        summary_parts = []

        if resume_data.get("name"):
            summary_parts.append(f"Name: {resume_data['name']}")
        if resume_data.get("email"):
            summary_parts.append(f"Contact: {resume_data['email']}")
        if resume_data.get("phone"):
            summary_parts.append(f"Phone: {resume_data['phone']}")

        summary_parts.append("\nProfessional Summary:")
        summary_parts.append(resume_data.get("summary", "Not provided"))

        if resume_data.get("skills"):
            summary_parts.append("\nKey Skills:")
            summary_parts.append(", ".join(resume_data["skills"]))

        if resume_data.get("experience"):
            summary_parts.append("\nWork Experience:")
            for exp in resume_data["experience"][:3]:
                exp_text = f"- {exp.get('title', '')} at {exp.get('company', '')}"
                if exp.get("duration"):
                    exp_text += f" ({exp.get('duration')})"
                summary_parts.append(exp_text)

        if resume_data.get("education"):
            summary_parts.append("\nEducation:")
            for edu in resume_data["education"]:
                edu_text = f"- {edu.get('degree', '')}"
                if edu.get("institution"):
                    edu_text += f" from {edu['institution']}"
                if edu.get("year"):
                    edu_text += f" ({edu['year']})"
                summary_parts.append(edu_text)

        return "\n".join(summary_parts)

    def _parse_feedback_response(self, response_text: str) -> Dict[str, List[str]]:
        """Parse the raw feedback text into structured sections."""
        sections = {
            "strengths": [],
            "areas_for_improvement": [],
            "ats_optimization": [],
            "skill_gap_analysis": [],
            "actionable_recommendations": [],
        }

        current_section = None
        section_map = {
            "strengths": "strengths",
            "areas for improvement": "areas_for_improvement",
            "ats optimization": "ats_optimization",
            "skill gap analysis": "skill_gap_analysis",
            "actionable recommendations": "actionable_recommendations",
        }

        for line in response_text.split("\n"):
            line = line.strip()

            # Check for section headers (flexible matching)
            line_lower = line.lower()
            for keyword, section_key in section_map.items():
                if keyword in line_lower and ("**" in line or "#" in line):
                    current_section = section_key
                    break

            # Add content to current section
            if current_section and line and not any(kw in line.lower() for kw in section_map):
                if line.startswith(("-", "•", "*", "–")) or (len(line) > 2 and line[0].isdigit() and line[1] in ".):"):
                    clean = line.lstrip("-•*–0123456789.). ").strip()
                    if clean:
                        sections[current_section].append(clean)
                elif line and not line.startswith(("#", "**")):
                    sections[current_section].append(line)

        return sections


# -------------------------------------------------------------------
# Lazy singleton
# -------------------------------------------------------------------
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
