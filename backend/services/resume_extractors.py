"""
Deterministic resume text extractors — contact, sections, experience, education.

Used by resume_parser.py. No LLM calls.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from backend.services.skill_lexicon import extract_skills_from_text, canonicalize_skills

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)
LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-/%]+", re.I)
GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w\-]+", re.I)

MONTH = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
DATE_TOKEN = rf"(?:{MONTH}\s+\d{{4}}|\d{{4}}|\d{{1,2}}/\d{{4}})"
DATE_RANGE_RE = re.compile(
    rf"({DATE_TOKEN})\s*[-–—to]+\s*(Present|Current|Now|{DATE_TOKEN})",
    re.I,
)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
METRIC_RE = re.compile(
    r"(\d+\s*%|\$\s*\d[\d,.]*\s*[KkMmBb]?|\b\d{1,3}(?:,\d{3})+\b|\b\d+\+?\s*(?:users|customers|people|teams?|projects?|apps?)\b)",
    re.I,
)

SECTION_ALIASES: Dict[str, Tuple[str, ...]] = {
    "summary": (
        "summary", "professional summary", "profile", "objective",
        "about me", "about", "career objective",
    ),
    "skills": (
        "skills", "technical skills", "core skills", "key skills",
        "technologies", "tech stack", "competencies", "expertise",
    ),
    "experience": (
        "experience", "work experience", "professional experience",
        "employment", "employment history", "work history", "career history",
    ),
    "education": (
        "education", "academic background", "academics", "qualifications",
    ),
    "projects": (
        "projects", "personal projects", "academic projects", "key projects",
    ),
    "certifications": (
        "certifications", "certificates", "licenses", "licenses & certifications",
    ),
    "languages": (
        "languages", "language proficiency",
    ),
}

# Heading line: short, often ALL CAPS or Title Case, maybe trailing colon
_HEADING_LINE_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 &/+-]{1,40})\s*:?\s*$")


def _normalize_heading(raw: str) -> Optional[str]:
    key = re.sub(r"[^a-z0-9\s&/+-]", "", raw.lower()).strip()
    key = re.sub(r"\s+", " ", key)
    for section, aliases in SECTION_ALIASES.items():
        if key in aliases:
            return section
    return None


def split_sections(text: str) -> Dict[str, str]:
    """
    Split resume text into named sections by detecting heading lines.
    Content before the first heading goes under 'header'.
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    sections: Dict[str, List[str]] = {"header": []}
    current = "header"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            sections.setdefault(current, []).append("")
            continue

        heading_match = _HEADING_LINE_RE.match(stripped)
        if heading_match:
            section_key = _normalize_heading(heading_match.group(1))
            if section_key:
                current = section_key
                sections.setdefault(current, [])
                continue

        sections.setdefault(current, []).append(stripped)

    return {k: "\n".join(v).strip() for k, v in sections.items() if "".join(v).strip()}


def extract_contact(text: str) -> Dict[str, str]:
    """Extract email, phone, LinkedIn, GitHub from text (usually header)."""
    email = EMAIL_RE.search(text)
    phone = PHONE_RE.search(text)
    linkedin = LINKEDIN_RE.search(text)
    github = GITHUB_RE.search(text)

    return {
        "email": email.group(0) if email else "",
        "phone": phone.group(0) if phone else "",
        "linkedin": linkedin.group(0) if linkedin else "",
        "github": github.group(0) if github else "",
    }


def extract_name(header_text: str, email: str = "") -> str:
    """
    Heuristic: first non-empty line that is not contact info and looks like a name.
    """
    for line in header_text.split("\n"):
        line = line.strip()
        if not line or len(line) > 60:
            continue
        if EMAIL_RE.search(line) or PHONE_RE.search(line):
            continue
        if LINKEDIN_RE.search(line) or GITHUB_RE.search(line):
            continue
        if _normalize_heading(line):
            continue
        # Reject lines that are mostly punctuation/numbers
        letters = sum(c.isalpha() or c.isspace() for c in line)
        if letters < len(line) * 0.6:
            continue
        # Prefer 2–4 tokens
        tokens = line.split()
        if 1 <= len(tokens) <= 5:
            return line
    # Fallback: local-part of email
    if email and "@" in email:
        local = email.split("@")[0]
        return local.replace(".", " ").replace("_", " ").title()
    return ""


def extract_skills_section(skills_text: str, full_text: str) -> List[str]:
    """Prefer skills section; always augment with full-text lexicon scan."""
    from_section: List[str] = []
    if skills_text:
        # Split on commas, pipes, bullets, newlines
        parts = re.split(r"[,|•·/\n;]+", skills_text)
        from_section = [p.strip() for p in parts if p.strip() and len(p.strip()) < 40]
        # Also run lexicon on the section
        from_section.extend(extract_skills_from_text(skills_text))

    from_full = extract_skills_from_text(full_text)
    return canonicalize_skills(from_section + from_full)


def _parse_month_year(token: str) -> Optional[datetime]:
    token = token.strip()
    if re.match(r"(?i)present|current|now", token):
        return datetime.now()
    # Month Year
    m = re.match(rf"(?i)({MONTH})\s+(\d{{4}})", token)
    if m:
        month_str, year = m.group(1), int(m.group(2))
        month_map = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        }
        month = month_map[month_str[:3].lower()]
        return datetime(year, month, 1)
    # Year only
    m = re.match(r"(\d{4})", token)
    if m:
        return datetime(int(m.group(1)), 1, 1)
    # MM/YYYY
    m = re.match(r"(\d{1,2})/(\d{4})", token)
    if m:
        return datetime(int(m.group(2)), int(m.group(1)), 1)
    return None


def parse_date_range(text: str) -> Tuple[str, Optional[float]]:
    """
    Find a date range in text. Returns (duration_string, years_float).
    """
    m = DATE_RANGE_RE.search(text)
    if not m:
        years = YEAR_RE.findall(text)
        if years:
            # YEAR_RE captures groups oddly — use finditer
            ys = [int(x.group(0)) for x in re.finditer(r"\b(?:19|20)\d{2}\b", text)]
            if ys:
                return str(ys[0]), None
        return "", None

    start_s, end_s = m.group(1), m.group(2)
    duration = f"{start_s} - {end_s}"
    start = _parse_month_year(start_s)
    end = _parse_month_year(end_s)
    years = None
    if start and end and end >= start:
        years = max(0.0, (end - start).days / 365.25)
    return duration, years


def extract_experience(experience_text: str) -> Tuple[List[Dict[str, Any]], float]:
    """
    Parse experience section into list of jobs and total years (union of ranges, approx).
    """
    if not experience_text:
        return [], 0.0

    lines = [ln.strip() for ln in experience_text.split("\n") if ln.strip()]
    jobs: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    total_years = 0.0

    def flush():
        nonlocal current, total_years
        if current:
            jobs.append(current)
            # accumulate years from duration if we stored _years
            y = current.pop("_years", None)
            if y:
                total_years += y
            current = None

    for line in lines:
        duration, years = parse_date_range(line)
        is_bullet = bool(re.match(r"^[-•●▪▸*]\s+", line)) or line.startswith("·")
        clean_bullet = re.sub(r"^[-•●▪▸*·]\s+", "", line).strip()

        # New job header: has date range OR looks like "Title at Company" / "Title | Company"
        if duration and not is_bullet:
            flush()
            # Strip date part for title/company
            title_line = DATE_RANGE_RE.sub("", line).strip(" |-–,")
            title, company = _split_title_company(title_line)
            current = {
                "title": title,
                "company": company,
                "duration": duration,
                "description": [],
                "_years": years or 0.0,
            }
            continue

        if is_bullet and current is not None:
            current["description"].append(clean_bullet)
            continue

        # Title-like line without dates yet — start a job if previous flushed
        if current is None and not is_bullet and len(line) < 100:
            title, company = _split_title_company(line)
            current = {
                "title": title,
                "company": company,
                "duration": "",
                "description": [],
                "_years": 0.0,
            }
            continue

        if current is not None and not is_bullet:
            # Maybe company on next line
            if not current.get("company") and len(line) < 80:
                current["company"] = line
            else:
                current["description"].append(line)

    flush()

    # If total_years is 0 but we have jobs, estimate 1 year each as weak fallback
    if total_years == 0 and jobs:
        total_years = float(len(jobs))

    return jobs, round(total_years, 1)


def _split_title_company(line: str) -> Tuple[str, str]:
    for sep in (" at ", " @ ", " | ", " – ", " — ", " - "):
        if sep in line:
            left, right = line.split(sep, 1)
            return left.strip(), right.strip()
    return line.strip(), ""


def extract_education(education_text: str) -> List[Dict[str, Any]]:
    if not education_text:
        return []

    lines = [ln.strip() for ln in education_text.split("\n") if ln.strip()]
    entries: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None

    def flush():
        nonlocal current
        if current:
            entries.append(current)
            current = None

    for line in lines:
        years = [m.group(0) for m in re.finditer(r"\b(?:19|20)\d{2}\b", line)]
        year = years[-1] if years else ""
        duration, _ = parse_date_range(line)

        looks_like_edu = bool(
            re.search(
                r"bachelor|master|ph\.?d|b\.?\s*s|m\.?\s*s|b\.?\s*tech|b\.?\s*e|mba|associate|diploma|university|college|institute|school",
                line,
                re.I,
            )
        )

        if looks_like_edu or duration:
            flush()
            degree = DATE_RANGE_RE.sub("", line).strip(" |-–,")
            # Try "Degree, Institution" or "Degree | Institution"
            institution = ""
            for sep in (",", " | ", " – ", " — ", " - ", " at "):
                if sep in degree:
                    left, right = degree.split(sep, 1)
                    # Prefer longer side as institution if it has University/College
                    if re.search(r"university|college|institute|school", right, re.I):
                        degree, institution = left.strip(), right.strip()
                    elif re.search(r"university|college|institute|school", left, re.I):
                        institution, degree = left.strip(), right.strip()
                    else:
                        degree, institution = left.strip(), right.strip()
                    break
            current = {
                "institution": institution,
                "degree": degree,
                "field_of_study": "",
                "year": year or (duration.split("-")[-1].strip() if duration else ""),
            }
        elif current is not None:
            if not current.get("institution") and len(line) < 100:
                current["institution"] = line
            elif not current.get("field_of_study"):
                current["field_of_study"] = line

    flush()
    return entries


def extract_projects(projects_text: str) -> List[Dict[str, Any]]:
    if not projects_text:
        return []

    lines = [ln.strip() for ln in projects_text.split("\n") if ln.strip()]
    projects: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None

    for line in lines:
        is_bullet = bool(re.match(r"^[-•●▪▸*·]\s+", line))
        clean = re.sub(r"^[-•●▪▸*·]\s+", "", line).strip()
        if not is_bullet and len(line) < 120:
            if current:
                projects.append(current)
            current = {"title": clean, "description": []}
        elif current is not None:
            current["description"].append(clean)

    if current:
        projects.append(current)
    return projects


def extract_certifications(cert_text: str) -> List[str]:
    if not cert_text:
        return []
    items = []
    for line in cert_text.split("\n"):
        line = re.sub(r"^[-•●▪▸*·]\s+", "", line.strip())
        if line:
            items.append(line)
    return items


def extract_languages(lang_text: str) -> List[str]:
    if not lang_text:
        return []
    parts = re.split(r"[,|•·/\n;]+", lang_text)
    return [p.strip() for p in parts if p.strip() and len(p.strip()) < 40]


def count_quantified_bullets(resume_data: Dict[str, Any]) -> Tuple[int, int]:
    """Return (quantified_count, total_bullets) across experience + projects."""
    total = 0
    quantified = 0
    for exp in resume_data.get("experience") or []:
        for desc in exp.get("description") or []:
            total += 1
            if METRIC_RE.search(str(desc)):
                quantified += 1
    for proj in resume_data.get("projects") or []:
        for desc in proj.get("description") or []:
            total += 1
            if METRIC_RE.search(str(desc)):
                quantified += 1
    return quantified, total


def has_core_sections(resume_data: Dict[str, Any], sections_present: Dict[str, bool]) -> Dict[str, bool]:
    return {
        "contact": bool(resume_data.get("email") or resume_data.get("phone")),
        "skills": bool(resume_data.get("skills")),
        "experience": bool(resume_data.get("experience")),
        "education": bool(resume_data.get("education")),
        "summary": bool(resume_data.get("summary")),
        **{f"section_{k}": v for k, v in sections_present.items()},
    }
