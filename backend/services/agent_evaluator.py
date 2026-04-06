"""
Multi-Agent Hiring Committee — Agentic AI Evaluator

Three distinct AI agent personas independently evaluate a candidate's
interview answer, then a moderator agent aggregates and highlights
disagreements to produce the final panel verdict.

Agents:
  • Technical Lead  — strict, code/system-design focused
  • HR Manager      — friendly, behavioural/culture-fit focused
  • Domain Expert   — industry-specific practical knowledge
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional

from groq import AsyncGroq

from backend.config import settings

logger = logging.getLogger("campushire.agents")

# ── Agent Persona Prompts ──────────────────────────────────────────

AGENT_PERSONAS = {
    "technical_lead": {
        "name": "Alex Chen",
        "role": "Technical Lead",
        "emoji": "🔧",
        "color": "#6366f1",
        "system_prompt": (
            "You are Alex Chen, a strict Senior Technical Lead with 12 years of "
            "experience at top tech companies (Google, Meta, Amazon). You are known "
            "for being rigorous and detail-oriented. You focus primarily on:\n"
            "- Technical depth and accuracy of the answer\n"
            "- Problem-solving approach and algorithmic thinking\n"
            "- System design reasoning and trade-off analysis\n"
            "- Code quality and engineering best practices\n\n"
            "You are NOT easily impressed. You expect concrete examples, specific "
            "technologies, and clear technical reasoning. Vague or generic answers "
            "receive low scores from you."
        ),
    },
    "hr_manager": {
        "name": "Sarah Williams",
        "role": "HR Manager",
        "emoji": "🤝",
        "color": "#10b981",
        "system_prompt": (
            "You are Sarah Williams, a warm and perceptive HR Manager with 10 years "
            "of experience in talent acquisition. You focus primarily on:\n"
            "- Communication clarity and structure (STAR method usage)\n"
            "- Cultural fit and team collaboration indicators\n"
            "- Enthusiasm, self-awareness, and growth mindset\n"
            "- Leadership potential and interpersonal skills\n\n"
            "You are encouraging but honest. You reward well-structured answers "
            "and penalize answers that lack self-awareness or empathy."
        ),
    },
    "domain_expert": {
        "name": "Dr. Raj Patel",
        "role": "Domain Expert",
        "emoji": "🎓",
        "color": "#8b5cf6",
        "system_prompt": (
            "You are Dr. Raj Patel, a seasoned Domain Expert and industry consultant "
            "with 15 years of cross-industry experience. You focus primarily on:\n"
            "- Industry-specific knowledge and practical application\n"
            "- Real-world problem-solving versus theoretical knowledge\n"
            "- Innovation mindset and awareness of current trends\n"
            "- Ability to connect technical skills with business impact\n\n"
            "You value candidates who demonstrate practical experience and "
            "understand how their work impacts the broader business."
        ),
    },
}

EVALUATION_TEMPLATE = """
{system_prompt}

You are evaluating a candidate's answer in a panel interview.

Job Title: {job_title}
Interview Question: {question}
Candidate's Answer: {answer}

Evaluate this answer from YOUR perspective as {role}. Return ONLY valid JSON:
{{
    "score": <0-100>,
    "verdict": "<one sentence overall verdict from your perspective>",
    "strengths": ["<specific strength 1>", "<specific strength 2>"],
    "improvements": ["<specific improvement 1>", "<specific improvement 2>"],
    "key_observation": "<one unique insight only you would notice given your role>"
}}
"""

MODERATOR_TEMPLATE = """
You are the Panel Moderator summarizing the hiring committee's evaluation.

Three expert panelists have independently evaluated a candidate's interview answer.
Your job is to:
1. Aggregate their scores into a fair overall score
2. Highlight the key areas of agreement
3. Note any significant disagreements between panelists
4. Provide the final recommendation

Here are the individual evaluations:

Technical Lead ({tech_name}): Score {tech_score}/100
- Verdict: {tech_verdict}

HR Manager ({hr_name}): Score {hr_score}/100
- Verdict: {hr_verdict}

Domain Expert ({domain_name}): Score {domain_score}/100
- Verdict: {domain_verdict}

Return ONLY valid JSON:
{{
    "aggregated_score": <weighted average: Technical 40%, HR 30%, Domain 30%>,
    "consensus": "<one sentence on what all panelists agreed on>",
    "disagreements": "<one sentence on key disagreements, or 'None — unanimous assessment'>",
    "final_recommendation": "<2-3 sentence final recommendation for the candidate>",
    "overall_verdict": "<one of: Strong Hire, Hire, Lean Hire, Lean No Hire, No Hire>"
}}
"""


class AgentEvaluator:
    """Multi-agent panel evaluation using Groq API."""

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set")
        self.client = AsyncGroq(api_key=self.api_key)
        self.model_name = settings.GROQ_MODEL

    async def evaluate_with_panel(
        self,
        question: str,
        answer: str,
        job_title: str,
    ) -> Dict[str, Any]:
        """
        Run all three agents concurrently, then aggregate via moderator.
        """
        try:
            # Run all agents in parallel
            tech_task = self._run_agent("technical_lead", question, answer, job_title)
            hr_task = self._run_agent("hr_manager", question, answer, job_title)
            domain_task = self._run_agent("domain_expert", question, answer, job_title)

            tech_result, hr_result, domain_result = await asyncio.gather(
                tech_task, hr_task, domain_task
            )

            # Build agent results with metadata
            agents = []
            for agent_key, result in [
                ("technical_lead", tech_result),
                ("hr_manager", hr_result),
                ("domain_expert", domain_result),
            ]:
                persona = AGENT_PERSONAS[agent_key]
                agents.append({
                    "agent_id": agent_key,
                    "agent_name": persona["name"],
                    "agent_role": persona["role"],
                    "agent_emoji": persona["emoji"],
                    "agent_color": persona["color"],
                    "score": result.get("score", 0),
                    "verdict": result.get("verdict", ""),
                    "strengths": result.get("strengths", []),
                    "improvements": result.get("improvements", []),
                    "key_observation": result.get("key_observation", ""),
                })

            # Moderator aggregation
            moderation = await self._run_moderator(tech_result, hr_result, domain_result)

            return {
                "success": True,
                "agents": agents,
                "aggregated_score": moderation.get("aggregated_score", 0),
                "consensus": moderation.get("consensus", ""),
                "disagreements": moderation.get("disagreements", ""),
                "final_recommendation": moderation.get("final_recommendation", ""),
                "overall_verdict": moderation.get("overall_verdict", ""),
            }

        except Exception as e:
            logger.exception("Panel evaluation failed")
            return {"success": False, "error": str(e)}

    async def _run_agent(
        self,
        agent_key: str,
        question: str,
        answer: str,
        job_title: str,
    ) -> Dict[str, Any]:
        """Run a single agent evaluation."""
        persona = AGENT_PERSONAS[agent_key]

        prompt = EVALUATION_TEMPLATE.format(
            system_prompt=persona["system_prompt"],
            role=persona["role"],
            job_title=job_title,
            question=question,
            answer=answer,
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1024,
                response_format={"type": "json_object"},
            )

            text = response.choices[0].message.content or ""
            return self._parse_json(text)

        except Exception as e:
            logger.warning("Agent %s failed: %s", agent_key, e)
            return {
                "score": 0,
                "verdict": f"Agent evaluation failed: {str(e)}",
                "strengths": [],
                "improvements": [],
                "key_observation": "",
            }

    async def _run_moderator(
        self,
        tech: Dict,
        hr: Dict,
        domain: Dict,
    ) -> Dict[str, Any]:
        """Run the moderator to aggregate all agent results."""
        prompt = MODERATOR_TEMPLATE.format(
            tech_name=AGENT_PERSONAS["technical_lead"]["name"],
            tech_score=tech.get("score", 0),
            tech_verdict=tech.get("verdict", "N/A"),
            hr_name=AGENT_PERSONAS["hr_manager"]["name"],
            hr_score=hr.get("score", 0),
            hr_verdict=hr.get("verdict", "N/A"),
            domain_name=AGENT_PERSONAS["domain_expert"]["name"],
            domain_score=domain.get("score", 0),
            domain_verdict=domain.get("verdict", "N/A"),
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=512,
                response_format={"type": "json_object"},
            )

            text = response.choices[0].message.content or ""
            return self._parse_json(text)

        except Exception as e:
            logger.warning("Moderator failed: %s", e)
            # Fallback: simple average
            scores = [tech.get("score", 0), hr.get("score", 0), domain.get("score", 0)]
            avg = round(sum(scores) / len(scores)) if scores else 0
            return {
                "aggregated_score": avg,
                "consensus": "Unable to generate moderator summary",
                "disagreements": "N/A",
                "final_recommendation": "Please review individual agent feedback.",
                "overall_verdict": "Needs Review",
            }

    @staticmethod
    def _parse_json(text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response."""
        raw = text.strip()
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        return json.loads(raw)


# ── Lazy singleton ─────────────────────────────────────────────────
_agent_evaluator: Optional[AgentEvaluator] = None


def get_agent_evaluator() -> AgentEvaluator:
    global _agent_evaluator
    if _agent_evaluator is None:
        _agent_evaluator = AgentEvaluator()
    return _agent_evaluator


async def panel_evaluate(
    question: str,
    answer: str,
    job_title: str,
) -> Dict[str, Any]:
    """Evaluate an answer using the multi-agent panel."""
    return await get_agent_evaluator().evaluate_with_panel(question, answer, job_title)
