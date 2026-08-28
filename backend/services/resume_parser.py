"""
Deterministic resume parser.

Extracts structured fields from PDF/DOCX/TXT using heuristics and a skill
lexicon — no LLM calls. Output shape matches the existing API contract.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from backend.services.resume_extractors import (
    extract_certifications,
    extract_contact,
    extract_education,
    extract_experience,
    extract_languages,
    extract_name,
    extract_projects,
    extract_skills_section,
    split_sections,
)

try:
    import docx
except ImportError:
    docx = None

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None


class ResumeParser:
    """Parses resume files into structured data without external AI."""

    async def parse_resume(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        ext = path.suffix.lower()
        if ext not in (".pdf", ".docx", ".txt"):
            raise ValueError(f"Unsupported format: {ext}. Use .pdf, .docx, or .txt")

        text = self._extract_text(path, ext)
        if not text.strip():
            raise ValueError("Document is empty or could not extract text")
        return self.parse_text(text)

    def parse_text(self, text: str) -> Dict[str, Any]:
        """Deterministic structured parse from raw resume text."""
        sections = split_sections(text)
        header = sections.get("header", text[:1500])
        contact = extract_contact(header + "\n" + text[:2000])

        experience, years_experience = extract_experience(sections.get("experience", ""))
        education = extract_education(sections.get("education", ""))
        skills = extract_skills_section(sections.get("skills", ""), text)
        projects = extract_projects(sections.get("projects", ""))
        certifications = extract_certifications(sections.get("certifications", ""))
        languages = extract_languages(sections.get("languages", ""))
        summary = sections.get("summary", "")
        if summary and len(summary) > 500:
            summary = summary[:500]

        name = extract_name(header, contact.get("email", ""))

        data: Dict[str, Any] = {
            "name": name,
            "email": contact.get("email", ""),
            "phone": contact.get("phone", ""),
            "linkedin": contact.get("linkedin", ""),
            "github": contact.get("github", ""),
            "summary": summary,
            "skills": skills,
            "experience": experience,
            "education": education,
            "projects": projects,
            "certifications": certifications,
            "languages": languages,
            "years_experience": years_experience,
            "sections_found": sorted(k for k in sections.keys() if k != "header"),
            "raw_text": text[:8000],
        }
        return data

    def _extract_text(self, path: Path, ext: str) -> str:
        if ext == ".pdf":
            return self._extract_pdf_text(path)
        if ext == ".docx":
            return self._extract_docx_text(path)
        return self._extract_txt_text(path)

    def _extract_pdf_text(self, path: Path) -> str:
        if PdfReader is None:
            raise ImportError("PyPDF2 is required for PDF files. pip install PyPDF2")
        reader = PdfReader(str(path))
        pages_text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                pages_text.append(page_text)
        return "\n".join(pages_text)

    def _extract_docx_text(self, path: Path) -> str:
        if docx is None:
            raise ImportError("python-docx is required for DOCX files. pip install python-docx")
        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs if p.text)

    @staticmethod
    def _extract_txt_text(path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="replace")


_resume_parser: Optional[ResumeParser] = None


def get_resume_parser() -> ResumeParser:
    global _resume_parser
    if _resume_parser is None:
        _resume_parser = ResumeParser()
    return _resume_parser


async def parse_resume(file_path: str) -> Dict[str, Any]:
    """Parse a resume file and return structured data."""
    return await get_resume_parser().parse_resume(file_path)


def parse_resume_text(text: str) -> Dict[str, Any]:
    """Parse resume text synchronously (for tests / scoring helpers)."""
    return get_resume_parser().parse_text(text)
