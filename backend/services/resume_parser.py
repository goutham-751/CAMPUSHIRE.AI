"""
Resume parser using Gemini API for all text extraction and structured parsing.
No spacy/pdfplumber dependency - uses Gemini API exclusively for PDF; 
python-docx retained only for DOCX raw text (Gemini doesn't support DOCX natively).
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from google import genai
from dotenv import load_dotenv

from backend.config import settings

load_dotenv()

try:
    import docx
except ImportError:
    docx = None


GEMINI_RESUME_PARSE_PROMPT = """
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
    """Parses resume files using Gemini API for extraction and structured output."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = settings.GEMINI_MODEL

    async def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """Parse a resume file using Gemini API and return structured data."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        ext = path.suffix.lower()
        if ext not in (".pdf", ".docx", ".txt"):
            raise ValueError(f"Unsupported format: {ext}. Use .pdf, .docx, or .txt")

        try:
            if ext == ".pdf":
                return await self._parse_pdf_with_gemini(path)
            elif ext == ".docx":
                return await self._parse_docx_with_gemini(path)
            else:
                return await self._parse_txt_with_gemini(path)
        except Exception as e:
            raise Exception(f"Error parsing resume: {str(e)}")

    async def _parse_pdf_with_gemini(self, path: Path) -> Dict[str, Any]:
        """Send PDF to Gemini via Files API for extraction."""
        try:
            # Use Files API to upload PDF (Gemini native PDF support)
            uploaded = self.client.files.upload(file=str(path))
            contents = [uploaded, GEMINI_RESUME_PARSE_PROMPT]
        except Exception:
            # Fallback: read bytes and use inline data
            with open(path, "rb") as f:
                pdf_bytes = f.read()
            from google.genai import types
            contents = [
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                GEMINI_RESUME_PARSE_PROMPT,
            ]

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=contents,
        )

        return self._parse_gemini_json_response(response)

    def _extract_docx_text(self, path: Path) -> str:
        """Extract raw text from DOCX (Gemini does not support DOCX natively)."""
        if docx is None:
            raise ImportError("python-docx is required for DOCX files. pip install python-docx")
        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs if p.text)

    def _extract_txt_text(self, path: Path) -> str:
        """Extract raw text from TXT file."""
        return path.read_text(encoding="utf-8", errors="replace")

    async def _parse_docx_with_gemini(self, path: Path) -> Dict[str, Any]:
        """Extract text from DOCX, then send to Gemini for structured parsing."""
        text = self._extract_docx_text(path)
        if not text.strip():
            raise ValueError("Document is empty or could not extract text")
        return await self._parse_text_with_gemini(text)

    async def _parse_txt_with_gemini(self, path: Path) -> Dict[str, Any]:
        """Read TXT and send to Gemini for structured parsing."""
        text = self._extract_txt_text(path)
        if not text.strip():
            raise ValueError("Document is empty")
        return await self._parse_text_with_gemini(text)

    async def _parse_text_with_gemini(self, text: str) -> Dict[str, Any]:
        """Send resume text to Gemini and get structured JSON."""
        prompt = f"""Resume content (raw text):
---
{text[:15000]}
---

{GEMINI_RESUME_PARSE_PROMPT}"""

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        return self._parse_gemini_json_response(response)

    def _parse_gemini_json_response(self, response) -> Dict[str, Any]:
        """Extract and validate JSON from Gemini response."""
        response_text = ""
        if hasattr(response, "text") and response.text:
            response_text = response.text
        elif getattr(response, "candidates", None) and response.candidates:
            c0 = response.candidates[0]
            if getattr(c0, "content", None) and c0.content:
                parts = getattr(c0.content, "parts", None)
                if parts:
                    response_text = "".join(
                        getattr(p, "text", "") or "" for p in parts
                    )

        if not response_text.strip():
            raise ValueError("No content in Gemini response")

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
