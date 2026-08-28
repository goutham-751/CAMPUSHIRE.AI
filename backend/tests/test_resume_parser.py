"""Unit tests for deterministic resume parser."""

from pathlib import Path

from backend.services.resume_parser import parse_resume_text

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_sample_resume_extracts_contact_and_skills():
    text = (FIXTURES / "sample_resume.txt").read_text(encoding="utf-8")
    data = parse_resume_text(text)

    assert data["name"] == "Jane Doe"
    assert data["email"] == "jane.doe@email.com"
    assert "555" in data["phone"]
    assert "linkedin.com/in/janedoe" in data["linkedin"].lower()
    assert "github.com/janedoe" in data["github"].lower()

    skills_lower = {s.lower() for s in data["skills"]}
    assert "python" in skills_lower
    assert "fastapi" in skills_lower
    assert "docker" in skills_lower
    assert "react" in skills_lower


def test_parse_sample_resume_experience_and_education():
    text = (FIXTURES / "sample_resume.txt").read_text(encoding="utf-8")
    data = parse_resume_text(text)

    assert len(data["experience"]) >= 1
    titles = " ".join(e.get("title", "") for e in data["experience"]).lower()
    assert "software engineer" in titles or "junior developer" in titles
    assert data["years_experience"] > 0

    assert len(data["education"]) >= 1
    degree_blob = " ".join(
        f"{e.get('degree', '')} {e.get('institution', '')}" for e in data["education"]
    ).lower()
    assert "bachelor" in degree_blob or "computer science" in degree_blob


def test_parse_is_deterministic():
    text = (FIXTURES / "sample_resume.txt").read_text(encoding="utf-8")
    a = parse_resume_text(text)
    b = parse_resume_text(text)
    assert a == b
