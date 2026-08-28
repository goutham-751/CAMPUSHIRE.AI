"""
Curated skill lexicon with alias normalization for deterministic ATS matching.

Canonical names are the keys; aliases map to those keys. Matching is
case-insensitive and prefers longer aliases first to avoid partial collisions
(e.g. "C++" before "C", "Node.js" before "Node").
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Set, Tuple

# Canonical skill → aliases (lowercase). Canonical form is title-cased for display.
_SKILL_ALIASES: Dict[str, Tuple[str, ...]] = {
    "Python": ("python", "python3", "py"),
    "JavaScript": ("javascript", "js", "ecmascript"),
    "TypeScript": ("typescript", "ts"),
    "Java": ("java",),
    "C++": ("c++", "cpp", "c plus plus"),
    "C#": ("c#", "csharp", "c sharp"),
    "C": ("c language", "clang"),
    "Go": ("golang", "go lang"),
    "Rust": ("rust",),
    "Ruby": ("ruby", "rb"),
    "PHP": ("php",),
    "Swift": ("swift",),
    "Kotlin": ("kotlin",),
    "Scala": ("scala",),
    "R": ("r language", "rlang"),
    "SQL": ("sql", "t-sql", "pl/sql", "plsql"),
    "HTML": ("html", "html5"),
    "CSS": ("css", "css3"),
    "React": ("react", "react.js", "reactjs"),
    "Angular": ("angular", "angular.js", "angularjs"),
    "Vue": ("vue", "vue.js", "vuejs"),
    "Next.js": ("next.js", "nextjs", "next"),
    "Node.js": ("node.js", "nodejs", "node"),
    "Express": ("express", "express.js", "expressjs"),
    "Django": ("django",),
    "Flask": ("flask",),
    "FastAPI": ("fastapi", "fast api"),
    "Spring": ("spring", "spring boot", "springboot"),
    ".NET": (".net", "dotnet", "asp.net", "aspnet"),
    "GraphQL": ("graphql",),
    "REST": ("rest", "restful", "rest api", "restful api"),
    "Docker": ("docker",),
    "Kubernetes": ("kubernetes", "k8s"),
    "AWS": ("aws", "amazon web services"),
    "Azure": ("azure", "microsoft azure"),
    "GCP": ("gcp", "google cloud", "google cloud platform"),
    "Terraform": ("terraform",),
    "CI/CD": ("ci/cd", "cicd", "continuous integration", "continuous delivery"),
    "Git": ("git", "github", "gitlab", "bitbucket"),
    "Linux": ("linux", "unix"),
    "MongoDB": ("mongodb", "mongo"),
    "PostgreSQL": ("postgresql", "postgres", "psql"),
    "MySQL": ("mysql",),
    "Redis": ("redis",),
    "Elasticsearch": ("elasticsearch", "elastic search"),
    "Kafka": ("kafka", "apache kafka"),
    "Spark": ("spark", "apache spark", "pyspark"),
    "Hadoop": ("hadoop",),
    "Airflow": ("airflow", "apache airflow"),
    "Pandas": ("pandas",),
    "NumPy": ("numpy", "np"),
    "Scikit-learn": ("scikit-learn", "sklearn", "scikit learn"),
    "TensorFlow": ("tensorflow", "tf"),
    "PyTorch": ("pytorch", "torch"),
    "Machine Learning": ("machine learning", "ml"),
    "Deep Learning": ("deep learning", "dl"),
    "NLP": ("nlp", "natural language processing"),
    "Computer Vision": ("computer vision", "cv", "opencv"),
    "Data Analysis": ("data analysis", "data analytics"),
    "Data Science": ("data science",),
    "ETL": ("etl", "elt"),
    "Tableau": ("tableau",),
    "Power BI": ("power bi", "powerbi"),
    "Excel": ("excel", "microsoft excel"),
    "Agile": ("agile", "scrum", "kanban"),
    "Jira": ("jira",),
    "Figma": ("figma",),
    "UI/UX": ("ui/ux", "ui", "ux", "user experience", "user interface"),
    "Selenium": ("selenium",),
    "Jest": ("jest",),
    "Pytest": ("pytest", "py.test"),
    "Microservices": ("microservices", "micro services"),
    "System Design": ("system design", "distributed systems"),
    "API Design": ("api design", "api development"),
    "Communication": ("communication", "verbal communication"),
    "Leadership": ("leadership", "team leadership"),
    "Problem Solving": ("problem solving", "problem-solving"),
}

# Build flat alias → canonical map, longest aliases first for scanning
_ALIAS_TO_CANONICAL: Dict[str, str] = {}
for _canon, _aliases in _SKILL_ALIASES.items():
    _ALIAS_TO_CANONICAL[_canon.lower()] = _canon
    for _a in _aliases:
        _ALIAS_TO_CANONICAL[_a.lower()] = _canon

# Sorted by length descending so "machine learning" beats "ml" when scanning phrases
_SORTED_ALIASES: List[str] = sorted(_ALIAS_TO_CANONICAL.keys(), key=len, reverse=True)

# Precompiled word-boundary patterns for multi-word aliases
_ALIAS_PATTERNS: List[Tuple[re.Pattern, str]] = []
for _alias in _SORTED_ALIASES:
    # Escape and allow flexible separators for dots/slashes in skills
    escaped = re.escape(_alias)
    # Allow optional word boundaries; for short tokens like "c" / "r" / "go" be stricter
    if len(_alias) <= 2 and _alias.isalpha():
        pat = re.compile(rf"(?<![a-zA-Z0-9+#./]){escaped}(?![a-zA-Z0-9+#./])", re.IGNORECASE)
    else:
        pat = re.compile(rf"(?<![a-zA-Z0-9+#]){escaped}(?![a-zA-Z0-9+#])", re.IGNORECASE)
    _ALIAS_PATTERNS.append((pat, _ALIAS_TO_CANONICAL[_alias]))


def normalize_skill(token: str) -> str | None:
    """Return canonical skill name for a token, or None if unknown."""
    if not token:
        return None
    key = token.strip().lower()
    return _ALIAS_TO_CANONICAL.get(key)


def canonicalize_skills(skills: Iterable[str]) -> List[str]:
    """Deduplicate and canonicalize a list of skill strings."""
    seen: Set[str] = set()
    out: List[str] = []
    for s in skills:
        if not s or not isinstance(s, str):
            continue
        canon = normalize_skill(s) or s.strip()
        if not canon:
            continue
        low = canon.lower()
        if low not in seen:
            seen.add(low)
            out.append(canon if normalize_skill(s) else s.strip())
    return out


def extract_skills_from_text(text: str) -> List[str]:
    """
    Scan free text for known skills using longest-alias-first matching.
    Returns a deduplicated list of canonical skill names in discovery order.
    """
    if not text:
        return []

    found: List[str] = []
    seen: Set[str] = set()
    # Work on a mutable mask so overlapping aliases don't double-count
    masked = text

    for pattern, canonical in _ALIAS_PATTERNS:
        for match in pattern.finditer(masked):
            low = canonical.lower()
            if low not in seen:
                seen.add(low)
                found.append(canonical)
        # Blank out matches so shorter aliases inside longer ones are less noisy
        masked = pattern.sub(lambda m: " " * (m.end() - m.start()), masked)

    return found


def all_canonical_skills() -> List[str]:
    """Return all canonical skill names sorted alphabetically."""
    return sorted(_SKILL_ALIASES.keys())
