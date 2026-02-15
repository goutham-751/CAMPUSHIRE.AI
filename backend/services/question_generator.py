import os
import json
import random
from typing import Dict, List, Optional, Any
from google import genai
from dotenv import load_dotenv

load_dotenv()


class QuestionGenerator:
    """Generates tailored interview questions using Gemini AI."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.0-flash"

        self.question_weights = {
            "technical": 40,
            "behavioral": 30,
            "situational": 20,
            "company_specific": 10,
        }

        self.prompt_template = """
        You are an experienced technical interviewer with expertise in {industry} roles.
        Generate {num_questions} interview questions for a {job_title} position at {company_name}.
        
        Candidate's background:
        {candidate_background}
        
        Job requirements:
        {job_description}
        
        Generate questions that:
        1. Assess technical skills relevant to the role
        2. Evaluate problem-solving abilities
        3. Gauge cultural fit
        4. Test domain-specific knowledge
        
        Return ONLY a JSON array (no markdown), each object with:
        - "question": The interview question
        - "category": One of [technical, behavioral, situational, company_specific]
        - "difficulty": One of [easy, medium, hard]
        - "suggested_answer": A brief suggestion of what a good answer might include
        """

        self.evaluation_prompt = """
        You are an expert interview evaluator. Evaluate the following candidate answer.

        Job Title: {job_title}
        Question: {question}
        Candidate Answer: {answer}

        Provide your evaluation as JSON (no markdown):
        {{
            "score": 0-100,
            "strengths": ["list of strengths in the answer"],
            "improvements": ["list of areas for improvement"],
            "sample_answer": "a brief example of an ideal answer"
        }}
        """

    async def generate_questions(
        self,
        resume_data: Dict[str, Any],
        job_title: str,
        company_name: str,
        job_description: str,
        num_questions: int = 10,
        industry: str = "technology",
    ) -> Dict[str, Any]:
        """Generate interview questions based on resume and job description."""
        try:
            candidate_background = self._prepare_candidate_background(resume_data)

            prompt = self.prompt_template.format(
                job_title=job_title,
                company_name=company_name,
                candidate_background=candidate_background,
                job_description=job_description,
                num_questions=num_questions,
                industry=industry,
            )

            response = await self.client.aio.models.generate_content(
                model=self.model_name, contents=prompt
            )
            questions = self._parse_questions_response(response.text)
            balanced_questions = self._balance_questions(questions, num_questions)

            # Build metadata
            cat_counts = {cat: 0 for cat in self.question_weights}
            diff_counts = {"easy": 0, "medium": 0, "hard": 0}
            for q in balanced_questions:
                cat_counts[q.get("category", "technical")] = (
                    cat_counts.get(q.get("category", "technical"), 0) + 1
                )
                diff_counts[q.get("difficulty", "medium")] = (
                    diff_counts.get(q.get("difficulty", "medium"), 0) + 1
                )

            return {
                "success": True,
                "questions": balanced_questions,
                "metadata": {
                    "total_questions": len(balanced_questions),
                    "categories": cat_counts,
                    "difficulty": diff_counts,
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def evaluate_answer(
        self,
        question: str,
        answer: str,
        job_title: str,
    ) -> Dict[str, Any]:
        """Evaluate a candidate's answer to an interview question."""
        try:
            prompt = self.evaluation_prompt.format(
                job_title=job_title,
                question=question,
                answer=answer,
            )
            response = await self.client.aio.models.generate_content(
                model=self.model_name, contents=prompt
            )
            result = self._parse_json_response(response.text)
            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── helpers ──────────────────────────────────────────────────

    def _prepare_candidate_background(self, resume_data: Dict[str, Any]) -> str:
        background_parts = []

        if resume_data.get("name"):
            background_parts.append(f"Name: {resume_data['name']}")

        if resume_data.get("skills"):
            background_parts.append("\nSkills:")
            background_parts.append(", ".join(resume_data["skills"]))

        if resume_data.get("experience"):
            background_parts.append("\nWork Experience:")
            for exp in resume_data["experience"][:3]:
                exp_text = f"- {exp.get('title', '')} at {exp.get('company', '')}"
                if exp.get("duration"):
                    exp_text += f" ({exp.get('duration')})"
                background_parts.append(exp_text)

        if resume_data.get("education"):
            background_parts.append("\nEducation:")
            for edu in resume_data["education"]:
                edu_text = f"- {edu.get('degree', '')}"
                if edu.get("institution"):
                    edu_text += f" from {edu['institution']}"
                if edu.get("year"):
                    edu_text += f" ({edu['year']})"
                background_parts.append(edu_text)

        if resume_data.get("projects"):
            background_parts.append("\nKey Projects:")
            for proj in resume_data["projects"][:3]:
                proj_text = f"- {proj.get('title', 'Untitled Project')}"
                if proj.get("description"):
                    proj_text += f": {proj['description']}"
                background_parts.append(proj_text)

        return "\n".join(background_parts)

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Extract and parse JSON from an AI response."""
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()
        return json.loads(json_str)

    def _parse_questions_response(self, response_text: str) -> List[Dict[str, str]]:
        questions = self._parse_json_response(response_text)
        valid_questions = []
        for q in questions:
            if (
                isinstance(q, dict)
                and "question" in q
                and "category" in q
                and "difficulty" in q
                and q["category"] in self.question_weights
                and q["difficulty"] in ["easy", "medium", "hard"]
            ):
                valid_questions.append(q)
        return valid_questions

    def _balance_questions(
        self, questions: List[Dict[str, str]], total_questions: int
    ) -> List[Dict[str, str]]:
        if not questions:
            return []

        categorized = {cat: [] for cat in self.question_weights}
        for q in questions:
            if q["category"] in categorized:
                categorized[q["category"]].append(q)

        total_weight = sum(self.question_weights.values())
        targets = {
            cat: max(1, int((weight / total_weight) * total_questions))
            for cat, weight in self.question_weights.items()
        }

        for cat in targets:
            targets[cat] = min(targets[cat], len(categorized[cat]) or 1)

        selected = []
        for cat, count in targets.items():
            if categorized[cat]:
                selected.extend(
                    random.sample(categorized[cat], min(count, len(categorized[cat])))
                )

        while len(selected) < total_questions and len(selected) < len(questions):
            remaining = [q for q in questions if q not in selected]
            if not remaining:
                break
            selected.append(random.choice(remaining))

        return selected[:total_questions]


# -------------------------------------------------------------------
# Lazy singleton
# -------------------------------------------------------------------
_question_generator: Optional[QuestionGenerator] = None


def get_question_generator() -> QuestionGenerator:
    global _question_generator
    if _question_generator is None:
        _question_generator = QuestionGenerator()
    return _question_generator


async def generate_interview_questions(
    resume_data: Dict[str, Any],
    job_title: str,
    company_name: str,
    job_description: str,
    num_questions: int = 10,
    industry: str = "technology",
) -> Dict[str, Any]:
    """Generate interview questions based on resume and job description."""
    return await get_question_generator().generate_questions(
        resume_data, job_title, company_name, job_description, num_questions, industry
    )


async def evaluate_interview_answer(
    question: str,
    answer: str,
    job_title: str,
) -> Dict[str, Any]:
    """Evaluate a candidate's answer to an interview question."""
    return await get_question_generator().evaluate_answer(question, answer, job_title)