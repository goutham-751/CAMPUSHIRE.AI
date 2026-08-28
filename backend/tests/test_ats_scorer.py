"""Unit tests for deterministic ATS scorer — no network / no Groq."""

from pathlib import Path

from backend.services.ats_scorer import score_resume_ats_sync
from backend.services.jd_extractor import extract_jd_requirements, extract_required_years
from backend.services.resume_parser import parse_resume_text
from backend.services.skill_lexicon import extract_skills_from_text, normalize_skill

FIXTURES = Path(__file__).parent / "fixtures"


def _sample_pair():
    resume = parse_resume_text((FIXTURES / "sample_resume.txt").read_text(encoding="utf-8"))
    jd = (FIXTURES / "sample_jd.txt").read_text(encoding="utf-8")
    return resume, jd


def test_skill_lexicon_aliases():
    assert normalize_skill("js") == "JavaScript"
    assert normalize_skill("k8s") == "Kubernetes"
    assert normalize_skill("react.js") == "React"
    found = extract_skills_from_text("Experience with Python, Docker, and k8s.")
    assert "Python" in found
    assert "Docker" in found
    assert "Kubernetes" in found


def test_jd_extractor_years_and_skills():
    jd = (FIXTURES / "sample_jd.txt").read_text(encoding="utf-8")
    assert extract_required_years(jd) == 3.0
    req = extract_jd_requirements(jd, "Software Engineer")
    skills = {s.lower() for s in req["required_skills"]}
    assert "python" in skills
    assert "docker" in skills
    assert req["required_education"] == "bachelor"


def test_ats_score_is_deterministic():
    resume, jd = _sample_pair()
    a = score_resume_ats_sync(resume, "Software Engineer", "Acme", jd)
    b = score_resume_ats_sync(resume, "Software Engineer", "Acme", jd)

    assert a["success"] and b["success"]
    assert a["result"]["overall_score"] == b["result"]["overall_score"]
    assert a["result"]["scores"] == b["result"]["scores"]
    assert a["result"]["missing_keywords"] == b["result"]["missing_keywords"]


def test_ats_score_has_expected_shape():
    resume, jd = _sample_pair()
    out = score_resume_ats_sync(resume, "Software Engineer", "Acme", jd)
    assert out["success"]
    result = out["result"]
    scores = result["scores"]
    for key in (
        "skills_match",
        "experience_level",
        "education",
        "keyword_density",
        "formatting",
        "achievements",
    ):
        assert key in scores
        assert 0 <= scores[key] <= 100

    assert 0 <= result["overall_score"] <= 100
    assert result["evidence"]["scoring_engine"] == "deterministic_v1"
    assert isinstance(result["missing_keywords"], list)
    assert isinstance(result["strengths"], list)


def test_missing_skill_lowers_skills_match():
    resume, jd = _sample_pair()
    baseline = score_resume_ats_sync(resume, "Software Engineer", "Acme", jd)
    # Strip Kubernetes-related skills from resume (JD requires k8s)
    resume2 = dict(resume)
    resume2["skills"] = [s for s in resume["skills"] if "kubernetes" not in s.lower()]
    # Ensure raw text also won't re-add k8s via experience scan — sample has no k8s
    scored = score_resume_ats_sync(resume2, "Software Engineer", "Acme", jd)

    assert "Kubernetes" in scored["result"]["missing_keywords"] or any(
        "kubernetes" in m.lower() for m in scored["result"]["missing_keywords"]
    )
    assert scored["result"]["scores"]["skills_match"] <= baseline["result"]["scores"]["skills_match"]


def test_works_without_groq(monkeypatch):
    """Scoring must not touch Groq."""
    import backend.services.ats_scorer as mod

    monkeypatch.setattr(mod, "AsyncGroq", None, raising=False)
    resume, jd = _sample_pair()
    out = score_resume_ats_sync(resume, "Software Engineer", "Acme", jd)
    assert out["success"]
    assert out["result"]["overall_score"] > 0
