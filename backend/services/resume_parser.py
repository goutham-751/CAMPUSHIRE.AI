"""
Resume parser using Groq API for structured parsing.
Uses PyPDF2 for PDF text extraction, python-docx for DOCX.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from groq import AsyncGroq
from dotenv import load_dotenv

from backend.config import settings

load_dotenv()

try:
    import docx
except ImportError:
    docx = None

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None


RESUME_PARSE_PROMPT = """
You are an expert resume parser. Extract structured information from this resume document.

Return ONLY valid JSON (no markdown, no explanation) with this exact structure:
{
  "name": "Full name of the candidate",
  "email": "email address",
  "phone": "phone number",
  "linkedin": "LinkedIn URL if present",
  "github": "GitHub URL if present",
  "summary": "Professional summary or objective (first 500 chars)",
  "skills": ["skill1", "skill2", "skill3"],
  "experience": [
    {
      "company": "Company name",
      "title": "Job title",
      "duration": "e.g. Jan 2020 - Present",
      "description": ["bullet point 1", "bullet point 2"]
    }
  ],
  "education": [
    {
      "institution": "School/University name",
      "degree": "Degree type",
      "field_of_study": "Field if applicable",
      "year": "Graduation year"
    }
  ],
  "projects": [
    {
      "title": "Project name",
      "description": ["description or key points"]
    }
  ],
  "certifications": ["certification 1", "certification 2"],
  "languages": ["Language 1", "Language 2"]
}

Extract all available information. Use empty arrays [] or empty strings "" for missing fields.
"""


class ResumeParser:
    """Parses resume files using Groq API for structured output."""

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        self.client = AsyncGroq(api_key=self.api_key)
        self.model_name = settings.GROQ_MODEL

    async def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """Parse a resume file using Groq API and return structured data."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        ext = path.suffix.lower()
        if ext not in (".pdf", ".docx", ".txt"):
            raise ValueError(f"Unsupported format: {ext}. Use .pdf, .docx, or .txt")

        try:
            text = self._extract_text(path, ext)
            if not text.strip():
                raise ValueError("Document is empty or could not extract text")
            return await self._parse_text_with_groq(text)
        except Exception as e:
            raise Exception(f"Error parsing resume: {str(e)}")

    def _extract_text(self, path: Path, ext: str) -> str:
        """Extract raw text from a file based on its extension."""
        if ext == ".pdf":
            return self._extract_pdf_text(path)
        elif ext == ".docx":
            return self._extract_docx_text(path)
        else:
            return self._extract_txt_text(path)

    def _extract_pdf_text(self, path: Path) -> str:
        """Extract text from PDF using PyPDF2."""
        if PdfReader is None:
            raise ImportError("PyPDF2 is required for PDF files. pip install PyPDF2")
        reader = PdfReader(str(path))
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
        return "\n".join(pages_text)

    def _extract_docx_text(self, path: Path) -> str:
        """Extract raw text from DOCX."""
        if docx is None:
            raise ImportError("python-docx is required for DOCX files. pip install python-docx")
        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs if p.text)

    def _extract_txt_text(self, path: Path) -> str:
        """Extract raw text from TXT file."""
        return path.read_text(encoding="utf-8", errors="replace")

    async def _parse_text_with_groq(self, text: str) -> Dict[str, Any]:
        """Send resume text to Groq and get structured JSON."""
        prompt = f"""Resume content (raw text):
---
{text[:15000]}
---

{RESUME_PARSE_PROMPT}"""

        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=4096,
        )

        response_text = response.choices[0].message.content
        return self._parse_json_response(response_text)

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Extract and validate JSON from Groq response."""
        if not response_text or not response_text.strip():
            raise ValueError("No content in Groq response")

        # Parse JSON - handle markdown code blocks
        raw = response_text.strip()
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        data = json.loads(raw)

        # Ensure expected structure
        defaults = {
            "name": "",
            "email": "",
            "phone": "",
            "linkedin": "",
            "github": "",
            "summary": "",
            "skills": [],
            "experience": [],
            "education": [],
            "projects": [],
            "certifications": [],
            "languages": [],
        }
        for k, v in defaults.items():
            if k not in data:
                data[k] = v
            elif data[k] is None:
                data[k] = v

        data["raw_text"] = json.dumps(data)[:5000]  # fallback
        return data


_resume_parser: Optional[ResumeParser] = None


def get_resume_parser() -> ResumeParser:
    global _resume_parser
    if _resume_parser is None:
        _resume_parser = ResumeParser()
    return _resume_parser


async def parse_resume(file_path: str) -> Dict[str, Any]:
    """Parse a resume file and return structured data."""
    return await get_resume_parser().parse_resume(file_path)
