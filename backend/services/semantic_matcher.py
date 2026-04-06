"""
Resume-to-Job Semantic Match Engine

Computes mathematical vector similarity between a resume and one or more
job descriptions using TF-IDF vectorization and cosine similarity.

Features:
  • Single match: resume vs. one JD → overall + section-level similarity
  • Batch match: resume vs. multiple JDs → ranked comparison
  • Section breakdown: Skills, Experience, Education scored independently
  • Keyword extraction: matched and missing keywords highlighted

Uses scikit-learn's TfidfVectorizer — lightweight, no external services.
"""

import logging
import re
from typing import Dict, List, Any, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("campushire.semantic")


class SemanticMatcher:
    """TF-IDF based semantic matching between resume and job descriptions."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 2),
            sublinear_tf=True,
        )

    def compute_match(
        self,
        resume_data: Dict[str, Any],
        job_description: str,
        job_title: str = "",
    ) -> Dict[str, Any]:
        """
        Compute semantic similarity between resume and a single job description.
        """
        try:
            resume_text = self._resume_to_text(resume_data)
            if not resume_text.strip() or not job_description.strip():
                return {"success": False, "error": "Empty resume or job description"}

            # Overall similarity
            overall_sim = self._compute_similarity(resume_text, job_description)

            # Section-level similarity
            section_scores = {}
            sections = {
                "skills": self._extract_skills_text(resume_data),
                "experience": self._extract_experience_text(resume_data),
                "education": self._extract_education_text(resume_data),
                "projects": self._extract_projects_text(resume_data),
            }

            for section_name, section_text in sections.items():
                if section_text.strip():
                    score = self._compute_similarity(section_text, job_description)
                    section_scores[section_name] = round(score, 1)
                else:
                    section_scores[section_name] = 0.0

            # Keyword analysis
            matched, missing = self._keyword_analysis(resume_text, job_description)

            # Recommendations
            recommendations = self._generate_recommendations(
                overall_sim, section_scores, missing
            )

            return {
                "success": True,
                "overall_similarity": round(overall_sim, 1),
                "section_scores": section_scores,
                "matched_keywords": matched[:15],
                "missing_keywords": missing[:15],
                "recommendations": recommendations,
                "job_title": job_title,
                "match_grade": self._grade(overall_sim),
            }

        except Exception as e:
            logger.exception("Semantic match failed")
            return {"success": False, "error": str(e)}

    def batch_match(
        self,
        resume_data: Dict[str, Any],
        job_entries: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Compare a resume against multiple job descriptions and rank them.

        Args:
            resume_data: Parsed resume data
            job_entries: List of {"title": "...", "description": "..."}

        Returns:
            Ranked list of match results
        """
        try:
            results = []
            for entry in job_entries[:10]:  # Cap at 10
                title = entry.get("title", "Untitled Job")
                desc = entry.get("description", "")
                if not desc.strip():
                    continue

                match_result = self.compute_match(resume_data, desc, title)
                if match_result.get("success"):
                    results.append(match_result)

            # Sort by similarity descending
            results.sort(key=lambda x: x.get("overall_similarity", 0), reverse=True)

            # Add rank
            for i, r in enumerate(results):
                r["rank"] = i + 1

            return {"success": True, "results": results, "total": len(results)}

        except Exception as e:
            logger.exception("Batch match failed")
            return {"success": False, "error": str(e)}

    def _compute_similarity(self, text_a: str, text_b: str) -> float:
        """Compute cosine similarity between two texts using TF-IDF."""
        try:
            vectorizer = TfidfVectorizer(
                stop_words="english",
                max_features=3000,
                ngram_range=(1, 2),
                sublinear_tf=True,
            )
            tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
            sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(sim * 100)  # Convert to percentage
        except Exception:
            return 0.0

    def _keyword_analysis(
        self, resume_text: str, job_description: str
    ) -> tuple:
        """Extract matched and missing keywords."""
        # Extract significant words from JD
        jd_words = set(self._extract_keywords(job_description))
        resume_words = set(self._extract_keywords(resume_text))

        matched = sorted(list(jd_words & resume_words))
        missing = sorted(list(jd_words - resume_words))

        return matched, missing

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text using TF-IDF weights."""
        try:
            vectorizer = TfidfVectorizer(
                stop_words="english",
                max_features=100,
                ngram_range=(1, 2),
                token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z+#.-]*[a-zA-Z+#]\b|\b[a-zA-Z]{2,}\b",
            )
            tfidf = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf.toarray()[0]

            # Get top keywords by TF-IDF score
            keyword_scores = list(zip(feature_names, scores))
            keyword_scores.sort(key=lambda x: x[1], reverse=True)

            # Filter out very short or generic terms
            keywords = [
                kw for kw, score in keyword_scores
                if score > 0.05 and len(kw) > 2
            ]
            return keywords[:50]
        except Exception:
            # Fallback: simple word extraction
            words = set(re.findall(r'\b[a-zA-Z]{3,}\b', text.lower()))
            stopwords = {
                "the", "and", "for", "with", "are", "will", "have", "has",
                "you", "your", "our", "this", "that", "from", "not", "but",
                "can", "all", "more", "also", "than", "been", "were", "was",
                "being", "able", "about", "their", "them", "they", "would",
                "should", "could", "into", "some", "other", "which", "when",
            }
            return list(words - stopwords)[:50]

    def _resume_to_text(self, resume_data: Dict[str, Any]) -> str:
        """Convert parsed resume data to flat text."""
        parts = []
        if resume_data.get("summary"):
            parts.append(resume_data["summary"])
        parts.append(self._extract_skills_text(resume_data))
        parts.append(self._extract_experience_text(resume_data))
        parts.append(self._extract_education_text(resume_data))
        parts.append(self._extract_projects_text(resume_data))

        if resume_data.get("certifications"):
            certs = resume_data["certifications"]
            if isinstance(certs, list):
                parts.append(" ".join(
                    c if isinstance(c, str) else c.get("name", "")
                    for c in certs
                ))

        return " ".join(p for p in parts if p)

    @staticmethod
    def _extract_skills_text(data: Dict) -> str:
        skills = data.get("skills", [])
        return " ".join(skills) if isinstance(skills, list) else str(skills)

    @staticmethod
    def _extract_experience_text(data: Dict) -> str:
        parts = []
        for exp in data.get("experience", []):
            parts.append(exp.get("title", ""))
            parts.append(exp.get("company", ""))
            desc = exp.get("description", [])
            if isinstance(desc, list):
                parts.extend(desc)
            else:
                parts.append(str(desc))
        return " ".join(parts)

    @staticmethod
    def _extract_education_text(data: Dict) -> str:
        parts = []
        for edu in data.get("education", []):
            parts.append(edu.get("degree", ""))
            parts.append(edu.get("institution", ""))
            parts.append(edu.get("field_of_study", ""))
        return " ".join(parts)

    @staticmethod
    def _extract_projects_text(data: Dict) -> str:
        parts = []
        for proj in data.get("projects", []):
            parts.append(proj.get("title", ""))
            desc = proj.get("description", [])
            if isinstance(desc, list):
                parts.extend(desc)
            else:
                parts.append(str(desc))
        return " ".join(parts)

    @staticmethod
    def _grade(similarity: float) -> str:
        if similarity >= 70:
            return "Excellent Match"
        elif similarity >= 50:
            return "Strong Match"
        elif similarity >= 35:
            return "Moderate Match"
        elif similarity >= 20:
            return "Weak Match"
        else:
            return "Poor Match"

    def _generate_recommendations(
        self,
        overall: float,
        sections: Dict[str, float],
        missing_keywords: List[str],
    ) -> List[str]:
        """Generate recommendations based on match analysis."""
        recs = []
        if overall < 30:
            recs.append(
                "Your resume has low alignment with this role. Consider tailoring "
                "your summary and skills section to mirror the job description."
            )
        elif overall < 50:
            recs.append(
                "Moderate alignment. Adding more relevant keywords from the job "
                "description could significantly improve your match."
            )

        weakest = min(sections, key=sections.get) if sections else None
        if weakest and sections.get(weakest, 100) < 20:
            label = weakest.replace("_", " ").title()
            recs.append(
                f"Your {label} section has the weakest match. "
                f"Strengthen it with relevant details from the job description."
            )

        if missing_keywords:
            top_missing = ", ".join(missing_keywords[:5])
            recs.append(f"Consider adding these keywords: {top_missing}")

        if not recs:
            recs.append("Great match! Your resume aligns well with this job description.")

        return recs


# ── Singleton ──────────────────────────────────────────────────────
_matcher: Optional[SemanticMatcher] = None


def get_semantic_matcher() -> SemanticMatcher:
    global _matcher
    if _matcher is None:
        _matcher = SemanticMatcher()
    return _matcher


def compute_semantic_match(
    resume_data: Dict[str, Any],
    job_description: str,
    job_title: str = "",
) -> Dict[str, Any]:
    """Compute semantic match between resume and JD."""
    return get_semantic_matcher().compute_match(resume_data, job_description, job_title)


def batch_semantic_match(
    resume_data: Dict[str, Any],
    job_entries: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Compare resume against multiple JDs."""
    return get_semantic_matcher().batch_match(resume_data, job_entries)
