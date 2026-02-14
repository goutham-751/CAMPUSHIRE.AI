import os
import re
import json
from typing import Dict, List, Set, Optional, Any
from pathlib import Path
import spacy
from datetime import datetime

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import docx
except ImportError:
    docx = None

try:
    import datefinder
except ImportError:
    datefinder = None


class ResumeParser:
    """Parses resume files (PDF, DOCX, TXT) and extracts structured data using NLP."""

    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise RuntimeError(
                "English language model not found. "
                "Run 'python -m spacy download en_core_web_sm'"
            )

        self.skills = self._load_skills_list()

        self.phone_regex = re.compile(
            r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
        )
        self.email_regex = re.compile(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        )
        self.linkedin_regex = re.compile(
            r"(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+/?"
        )
        self.github_regex = re.compile(
            r"(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9-]+/?"
        )
        self.date_pattern = re.compile(
            r"((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})|"
            r"(\d{1,2}[/-]\d{4})|"
            r"((19|20)\d{2})"
        )

    async def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """Parse a resume file and return structured data."""
        try:
            text = self._extract_text(file_path)
            if not text:
                raise ValueError("Could not extract text from the file")

            doc = self.nlp(text)
            contact_info = self._extract_contact_info(text)
            name = self._extract_name(doc, contact_info.get("email", ""))

            return {
                "name": name,
                **contact_info,
                "skills": self._extract_skills(text),
                "experience": self._extract_experience(doc),
                "education": self._extract_education(doc),
                "projects": self._extract_projects(doc),
                "languages": self._extract_languages(text),
                "certifications": self._extract_certifications(doc),
                "summary": self._extract_summary(text),
                "raw_text": text[:5000],
            }

        except Exception as e:
            raise Exception(f"Error parsing resume: {str(e)}")

    # ── extraction helpers ──────────────────────────────────────

    def _extract_contact_info(self, text: str) -> Dict[str, str]:
        email_match = self.email_regex.search(text)
        phone_match = self.phone_regex.search(text)
        linkedin_match = self.linkedin_regex.search(text)
        github_match = self.github_regex.search(text)
        return {
            "email": email_match.group(0) if email_match else "",
            "phone": phone_match.group(0) if phone_match else "",
            "linkedin": linkedin_match.group(0) if linkedin_match else "",
            "github": github_match.group(0) if github_match else "",
        }

    def _extract_name(self, doc, email: str) -> str:
        if email:
            name_from_email = email.split("@")[0]
            name_parts = re.sub(r"[^a-zA-Z]", " ", name_from_email).split()
            if len(name_parts) >= 2:
                return " ".join(name_parts).title()
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text.strip()
        return ""

    def _extract_skills(self, text: str) -> List[str]:
        text_lower = text.lower()
        found_skills = set()
        for skill in self.skills:
            if skill.lower() in text_lower:
                found_skills.add(skill)
        return sorted(list(found_skills))

    def _extract_experience(self, doc) -> List[Dict[str, Any]]:
        experience = []
        current_exp: Dict[str, Any] = {}

        for sent in doc.sents:
            sent_text = sent.text.strip()
            for ent in sent.ents:
                if ent.label_ == "ORG" and len(ent.text) > 2:
                    if current_exp and "company" in current_exp:
                        experience.append(current_exp)
                        current_exp = {}
                    current_exp = {
                        "company": ent.text,
                        "title": "",
                        "duration": self._extract_duration(sent_text),
                        "description": [],
                    }
                    break

            if " - " in sent_text and not current_exp.get("title"):
                parts = sent_text.split(" - ", 1)
                if len(parts[0].split()) < 5:
                    current_exp["title"] = parts[0].strip()

            if sent_text.startswith(("•", "-", "•", "▪", "▸")):
                if current_exp:
                    current_exp.setdefault("description", []).append(
                        sent_text[1:].strip()
                    )

        if current_exp:
            experience.append(current_exp)
        return experience[:5]

    def _extract_education(self, doc) -> List[Dict[str, str]]:
        education = []
        current_edu: Dict[str, str] = {}
        edu_keywords = ["university", "college", "institute", "school"]

        for sent in doc.sents:
            sent_text = sent.text.strip()
            for ent in sent.ents:
                if ent.label_ == "ORG" and any(
                    kw in ent.text.lower() for kw in edu_keywords
                ):
                    if current_edu:
                        education.append(current_edu)
                    current_edu = {
                        "institution": ent.text,
                        "degree": "",
                        "field_of_study": "",
                        "year": self._extract_year(sent_text),
                    }
                    break

            if not current_edu.get("degree"):
                degree_indicators = [
                    "bachelor",
                    "master",
                    "phd",
                    "bsc",
                    "msc",
                    "b.tech",
                    "m.tech",
                ]
                if any(ind in sent_text.lower() for ind in degree_indicators):
                    current_edu["degree"] = sent_text

        if current_edu:
            education.append(current_edu)
        return education

    def _extract_projects(self, doc) -> List[Dict[str, Any]]:
        projects = []
        current_project: Dict[str, Any] = {}

        for sent in doc.sents:
            sent_text = sent.text.strip()
            if (
                sent_text.istitle()
                and 10 < len(sent_text) < 100
                and not any(
                    w in sent_text.lower() for w in ["experience", "education"]
                )
            ):
                if current_project:
                    projects.append(current_project)
                current_project = {"title": sent_text, "description": []}
            elif current_project:
                current_project["description"].append(sent_text)

        if current_project:
            projects.append(current_project)
        return projects[:10]

    def _extract_languages(self, text: str) -> List[str]:
        languages = set()
        common_languages = {
            "english", "spanish", "french", "german", "chinese",
            "japanese", "hindi", "arabic", "russian", "portuguese",
        }
        lang_pattern = (
            r"\b(" + "|".join(common_languages) + r")\s*:\s*"
            r"(fluent|native|proficient|intermediate|beginner)"
        )
        matches = re.findall(lang_pattern, text.lower())
        languages.update([m[0].capitalize() for m in matches])
        return sorted(list(languages))

    def _extract_certifications(self, doc) -> List[str]:
        certs = set()
        cert_keywords = ["certified", "certification", "license", "certificate"]
        for sent in doc.sents:
            sent_text = sent.text.strip()
            if any(kw in sent_text.lower() for kw in cert_keywords):
                cert = re.sub(r"[^\w\s-]", "", sent_text).strip()
                if len(cert.split()) < 10:
                    certs.add(cert)
        return sorted(list(certs))

    def _extract_summary(self, text: str) -> str:
        """Try to extract a professional summary section."""
        patterns = [
            r"(?i)(?:professional\s+)?summary\s*[:\n](.+?)(?:\n\n|\n[A-Z])",
            r"(?i)objective\s*[:\n](.+?)(?:\n\n|\n[A-Z])",
            r"(?i)about\s+me\s*[:\n](.+?)(?:\n\n|\n[A-Z])",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()[:500]
        return ""

    def _extract_duration(self, text: str) -> str:
        if datefinder:
            try:
                dates = list(datefinder.find_dates(text))
                if len(dates) >= 2:
                    return f"{dates[0].strftime('%b %Y')} - {dates[1].strftime('%b %Y')}"
                elif dates:
                    return f"{dates[0].strftime('%b %Y')} - Present"
            except Exception:
                pass

        matches = self.date_pattern.findall(text)
        if matches:
            return " - ".join(match[0] for match in matches[:2])
        return ""

    def _extract_year(self, text: str) -> str:
        matches = re.findall(r"(19|20)\d{2}", text)
        return matches[0] if matches else ""

    # ── file reading ────────────────────────────────────────────

    def _extract_text(self, file_path: str) -> str:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            ext = file_path.suffix.lower()
            if ext == ".pdf":
                return self._extract_text_from_pdf(file_path)
            elif ext == ".docx":
                return self._extract_text_from_docx(file_path)
            elif ext == ".txt":
                return file_path.read_text(encoding="utf-8")
            else:
                raise ValueError(f"Unsupported file format: {ext}")
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")

    def _extract_text_from_pdf(self, file_path: Path) -> str:
        if pdfplumber is None:
            raise ImportError("pdfplumber is required for PDF parsing. pip install pdfplumber")
        try:
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n".join(text_parts)
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")

    def _extract_text_from_docx(self, file_path: Path) -> str:
        if docx is None:
            raise ImportError("python-docx is required for DOCX parsing. pip install python-docx")
        try:
            document = docx.Document(file_path)
            return "\n".join(
                paragraph.text for paragraph in document.paragraphs if paragraph.text
            )
        except Exception as e:
            raise Exception(f"Error reading DOCX: {str(e)}")

    def _load_skills_list(self) -> Set[str]:
        skills_path = Path("data/skills.json")
        if skills_path.exists():
            try:
                with open(skills_path, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception:
                pass

        return {
            # Programming Languages
            "Python", "JavaScript", "Java", "C++", "C#", "Ruby", "PHP",
            "Swift", "Kotlin", "Go", "TypeScript", "Rust", "Scala", "Dart",
            "R", "MATLAB", "Perl", "Haskell", "Lua", "Julia",
            # Web Development
            "HTML", "CSS", "React", "Angular", "Vue.js", "Node.js",
            "Express.js", "Django", "Flask", "FastAPI", "Spring",
            "Ruby on Rails", "ASP.NET", "jQuery", "Bootstrap", "Tailwind CSS",
            # Mobile Development
            "React Native", "Flutter", "Android", "iOS", "SwiftUI",
            "Kotlin Multiplatform", "Xamarin",
            # Database
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite",
            "Oracle", "Microsoft SQL Server", "Cassandra", "Elasticsearch",
            "Firebase", "DynamoDB", "Neo4j",
            # DevOps & Cloud
            "Docker", "Kubernetes", "AWS", "Azure", "Google Cloud",
            "Terraform", "Ansible", "Jenkins", "GitHub Actions",
            "GitLab CI", "CircleCI", "Prometheus", "Grafana", "Nginx", "Apache",
            # Data Science & AI/ML
            "Pandas", "NumPy", "scikit-learn", "TensorFlow", "PyTorch",
            "Keras", "OpenCV", "NLTK", "spaCy", "Hugging Face", "MLflow",
            "PySpark", "Dask", "Jupyter",
            # Other Tools & Technologies
            "Git", "Linux", "Bash", "PowerShell", "REST API", "GraphQL",
            "gRPC", "WebSockets", "OAuth", "JWT",
        }


# -------------------------------------------------------------------
# Lazy singleton
# -------------------------------------------------------------------
_resume_parser: Optional[ResumeParser] = None


def get_resume_parser() -> ResumeParser:
    global _resume_parser
    if _resume_parser is None:
        _resume_parser = ResumeParser()
    return _resume_parser


async def parse_resume(file_path: str) -> Dict[str, Any]:
    """Parse a resume file and return structured data."""
    return await get_resume_parser().parse_resume(file_path)