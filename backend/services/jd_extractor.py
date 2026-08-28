"""
Deterministic job-description requirement extractor.

Pulls required skills (via skill lexicon), years of experience, and education
level cues from free-text JDs using regex and lexicon matching only.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from backend.services.skill_lexicon import extract_skills_from_text

# Degree ladder: higher index = higher level
DEGREE_LEVELS = {
    "high_school": 1,
    "associate": 2,
    "bachelor": 3,
    "master": 4,
    "phd": 5,
}

DEGREE_PATTERNS = [
    (re.compile(r"\bph\.?\s*d\b|\bdoctorate\b|\bdoctoral\b", re.I), "phd"),
    (re.compile(r"\bmasters?\b|\bm\.?\s*s\.?\b|\bm\.?\s*a\.?\b|\bmba\b|\bm\.?\s*eng\b", re.I), "master"),
    (re.compile(r"\bbachelors?\b|\bb\.?\s*s\.?\b|\bb\.?\s*a\.?\b|\bb\.?\s*tech\b|\bb\.?\s*e\.?\b|\bundergraduate\b", re.I), "bachelor"),
    (re.compile(r"\bassociates?\b|\ba\.?\s*s\.?\b", re.I), "associate"),
    (re.compile(r"\bhigh\s+school\b|\bg\.?\s*e\.?\s*d\.?\b", re.I), "high_school"),
]

YEARS_PATTERNS = [
    # "5+ years", "3-5 years", "at least 4 years", "minimum of 2 years"
    re.compile(
        r"(?:at\s+least|minimum\s+of|min(?:imum)?\.?\s*|over|more\s+than)?\s*"
        r"(\d+)\s*(?:\+|plus)?\s*(?:-|–|to)\s*(\d+)\s*\+?\s*years?",
        re.I,
    ),
    re.compile(
        r"(?:at\s+least|minimum\s+of|min(?:imum)?\.?\s*|over|more\s+than)\s*"
        r"(\d+)\s*\+?\s*years?",
        re.I,
    ),
    re.compile(r"(\d+)\s*\+\s*years?", re.I),
    re.compile(r"(\d+)\s*years?(?:\s+of)?\s+(?:experience|exp\.?)", re.I),
]


def extract_required_years(job_description: str) -> Optional[float]:
    """
    Extract minimum years of experience required from a JD.
    For ranges like 3-5, returns the lower bound (3).
    """
    if not job_description:
        return None

    text = job_description
    for pattern in YEARS_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        groups = [g for g in m.groups() if g is not None]
        if not groups:
            continue
        try:
            nums = [float(g) for g in groups]
            return min(nums)
        except ValueError:
            continue
    return None


def extract_required_education(job_description: str) -> Optional[str]:
    """Return the highest education level mentioned in the JD."""
    if not job_description:
        return None

    best: Optional[str] = None
    best_rank = 0
    for pattern, level in DEGREE_PATTERNS:
        if pattern.search(job_description):
            rank = DEGREE_LEVELS[level]
            if rank > best_rank:
                best_rank = rank
                best = level
    return best


def extract_jd_requirements(
    job_description: str,
    job_title: str = "",
) -> Dict[str, Any]:
    """
    Extract structured requirements from a job description.

    Returns:
        {
          "required_skills": [...],
          "required_years": float | None,
          "required_education": str | None,
          "title_skills": [...],  # skills inferred from job title
        }
    """
    combined = f"{job_title}\n{job_description}".strip()
    skills = extract_skills_from_text(combined)
    title_skills = extract_skills_from_text(job_title) if job_title else []

    return {
        "required_skills": skills,
        "required_years": extract_required_years(job_description),
        "required_education": extract_required_education(job_description),
        "title_skills": title_skills,
    }


def education_rank(level: Optional[str]) -> int:
    """Numeric rank for a degree level key, 0 if unknown."""
    if not level:
        return 0
    return DEGREE_LEVELS.get(level.lower(), 0)


def infer_resume_education_level(education_entries: List[Dict[str, Any]]) -> Optional[str]:
    """Infer highest education level from parsed resume education blocks."""
    best: Optional[str] = None
    best_rank = 0
    for edu in education_entries or []:
        blob = " ".join(
            str(edu.get(k, "") or "")
            for k in ("degree", "field_of_study", "institution")
        )
        for pattern, level in DEGREE_PATTERNS:
            if pattern.search(blob):
                rank = DEGREE_LEVELS[level]
                if rank > best_rank:
                    best_rank = rank
                    best = level
    return best
