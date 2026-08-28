"""
Feature smoke probe for deploy readiness.

Run from repo root:
  PYTHONPATH=. python backend/scripts/feature_smoke.py
"""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "backend" / "tests" / "fixtures"


def log(message: str, data: dict):
    print(message, json.dumps(data, default=str))


def main():
    from backend.config import settings
    from backend.telemetry import get_telemetry_data, record_api_call
    from backend.services.resume_parser import parse_resume_text
    from backend.services.ats_scorer import score_resume_ats_sync
    from backend.database import supabase

    log(
        "env_readiness",
        {
            "groq_configured": bool(
                settings.GROQ_API_KEY and settings.GROQ_API_KEY != "YOUR_GROQ_API_KEY"
            ),
            "supabase_client": supabase is not None,
            "supabase_url_set": bool(settings.SUPABASE_URL),
            "groq_model": settings.GROQ_MODEL,
            "debug": settings.DEBUG,
        },
    )

    t0 = get_telemetry_data()
    record_api_call(42.5)
    t1 = get_telemetry_data()
    log(
        "telemetry",
        {
            "tokens_start": t0.get("total_tokens"),
            "tokens_after_http": t1.get("total_tokens"),
            "request_count": t1.get("request_count"),
            "no_fake_seed": (t0.get("total_tokens") or 0) == 0,
        },
    )

    resume = parse_resume_text((FIX / "sample_resume.txt").read_text(encoding="utf-8"))
    jd_match = (FIX / "sample_jd.txt").read_text(encoding="utf-8")
    jd_mismatch = (
        "Hiring a Marketing Manager with 7+ years experience in brand strategy, "
        "SEO, Google Ads, HubSpot, and content marketing. MBA preferred."
    )
    a = score_resume_ats_sync(resume, "Software Engineer", "Acme", jd_match)
    b = score_resume_ats_sync(resume, "Marketing Manager", "BrandCo", jd_mismatch)
    log(
        "ats_cross_jd",
        {
            "software": a["result"]["overall_score"],
            "marketing": b["result"]["overall_score"],
            "differ": a["result"]["overall_score"] != b["result"]["overall_score"],
        },
    )

    async def _feedback():
        from backend.services.feedback_generator import generate_resume_feedback

        return await generate_resume_feedback(
            resume, "Software Engineer", "Acme", jd_match
        )

    fb = asyncio.run(_feedback())
    log(
        "feedback",
        {
            "success": fb.get("success"),
            "overall": fb.get("ats_overall_score"),
            "llm_rewrite": bool(fb.get("raw_response")),
        },
    )

    async def _questions():
        from backend.services.question_generator import generate_interview_questions

        return await generate_interview_questions(
            resume, "Software Engineer", "Acme", jd_match, num_questions=3
        )

    qs = asyncio.run(_questions())
    log(
        "questions",
        {
            "success": qs.get("success"),
            "count": len(qs.get("questions") or []),
            "sample": ((qs.get("questions") or [{}])[0].get("question") or "")[:100],
            "error": (qs.get("error") or "")[:160],
        },
    )

    settings_src = (
        ROOT / "frontend" / "src" / "pages" / "Settings" / "Settings.jsx"
    ).read_text(encoding="utf-8")
    log(
        "settings_ui",
        {
            "no_fake_openai": "Connected (GPT-4o)" not in settings_src,
            "uses_system_status": "getSystemStatus" in settings_src,
        },
    )


if __name__ == "__main__":
    started = time.time()
    main()
    print(f"done in {time.time() - started:.1f}s")
