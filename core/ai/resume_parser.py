"""
PDF resume parsing service.

Uses PyMuPDF for text extraction and optional spaCy for NER enrichment.
Falls back to regex/keyword extraction when spaCy is unavailable.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Common technical & professional skills for keyword detection
SKILL_KEYWORDS = [
    "python", "django", "flask", "fastapi", "javascript", "typescript", "react",
    "vue", "angular", "node", "nodejs", "java", "spring", "kotlin", "swift",
    "go", "golang", "rust", "c++", "c#", ".net", "php", "laravel", "ruby",
    "rails", "sql", "postgresql", "mysql", "mongodb", "redis", "docker",
    "kubernetes", "aws", "azure", "gcp", "terraform", "ansible", "git",
    "linux", "html", "css", "tailwind", "bootstrap", "sass", "graphql",
    "rest", "api", "microservices", "machine learning", "deep learning",
    "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn", "nlp",
    "spacy", "opencv", "tableau", "power bi", "excel", "agile", "scrum",
    "communication", "leadership", "project management", "figma", "ui/ux",
    "devops", "ci/cd", "jenkins", "github actions", "selenium", "pytest",
    "junit", "next.js", "nextjs", "express", "nestjs", "prisma", "firebase",
]

EDUCATION_PATTERNS = [
    r"(?:b\.?\s*tech|bachelor|b\.?\s*sc|b\.?\s*e|m\.?\s*tech|master|m\.?\s*sc|mba|ph\.?d|doctorate)[^\n]{0,80}",
    r"(?:university|college|institute|school)[^\n]{0,100}",
]

EXPERIENCE_PATTERNS = [
    r"(?:\d+\+?\s*years?\s+(?:of\s+)?experience)",
    r"(?:experience|work history|employment)[:\s]*[^\n]{0,200}",
    r"(?:senior|junior|lead|intern|manager|developer|engineer|analyst)[^\n]{0,60}",
]

PROJECT_PATTERNS = [
    r"(?:projects?|portfolio)[:\s]*",
]

CERT_PATTERNS = [
    r"(?:certified|certification|certificate)[^\n]{0,100}",
    r"(?:aws certified|pmp|scrum master|google cloud|azure certified)",
]


class ResumeParserService:
    """Extract structured resume data from PDF uploads."""

    def __init__(self):
        self._nlp = None
        self._spacy_available = False
        self._load_spacy()

    def _load_spacy(self):
        try:
            import spacy

            self._nlp = spacy.load("en_core_web_sm")
            self._spacy_available = True
        except Exception as exc:
            logger.info("spaCy unavailable, using regex fallback: %s", exc)
            self._nlp = None
            self._spacy_available = False

    def parse_file(self, file_field) -> dict[str, Any]:
        """Parse an uploaded FileField (PDF preferred)."""
        empty = self._empty_result()
        if not file_field:
            return {**empty, "parse_status": "skipped", "error": "No file provided"}

        name = getattr(file_field, "name", "") or ""
        if not name.lower().endswith(".pdf"):
            return {
                **empty,
                "parse_status": "skipped",
                "error": "Only PDF parsing is supported; file preserved.",
                "source_file": name,
            }

        try:
            text = self._extract_pdf_text(file_field)
        except Exception as exc:
            logger.exception("PDF extraction failed")
            return {
                **empty,
                "parse_status": "failed",
                "error": str(exc),
                "source_file": name,
            }

        if not text.strip():
            return {
                **empty,
                "parse_status": "failed",
                "error": "Could not extract text from PDF (scanned image?)",
                "source_file": name,
            }

        parsed = self.parse_text(text)
        parsed["parse_status"] = "success"
        parsed["source_file"] = name
        parsed["raw_text"] = text[:50000]
        return parsed

    def parse_text(self, text: str) -> dict[str, Any]:
        """Parse plain resume text into structured fields."""
        text_lower = text.lower()
        result = self._empty_result()
        result["email"] = self._extract_email(text)
        result["phone"] = self._extract_phone(text)
        result["linkedin"] = self._extract_link(text, "linkedin.com")
        result["github"] = self._extract_link(text, "github.com")
        result["skills"] = self._extract_skills(text_lower)
        result["education"] = self._extract_by_patterns(text, EDUCATION_PATTERNS)
        result["experience"] = self._extract_by_patterns(text, EXPERIENCE_PATTERNS)
        result["projects"] = self._extract_section_lines(text, "project")
        result["certifications"] = self._extract_by_patterns(text, CERT_PATTERNS)

        if self._spacy_available and self._nlp:
            self._enrich_with_spacy(text, result)

        return result

    def _empty_result(self) -> dict[str, Any]:
        return {
            "skills": [],
            "education": [],
            "experience": [],
            "projects": [],
            "certifications": [],
            "email": "",
            "phone": "",
            "linkedin": "",
            "github": "",
            "raw_text": "",
            "source_file": "",
            "parse_status": "pending",
            "error": "",
        }

    def _extract_pdf_text(self, file_field) -> str:
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError(
                "PyMuPDF is required for PDF parsing. Install with: pip install PyMuPDF"
            ) from exc

        path = file_field.path if hasattr(file_field, "path") else None
        if path:
            doc = fitz.open(path)
        else:
            file_field.seek(0)
            doc = fitz.open(stream=file_field.read(), filetype="pdf")

        pages = []
        try:
            for page in doc:
                pages.append(page.get_text())
        finally:
            doc.close()
        return "\n".join(pages)

    def _extract_email(self, text: str) -> str:
        match = re.search(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text
        )
        return match.group(0) if match else ""

    def _extract_phone(self, text: str) -> str:
        patterns = [
            r"\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}",
            r"\b\d{10}\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0).strip()
        return ""

    def _extract_link(self, text: str, domain: str) -> str:
        match = re.search(
            rf"https?://(?:www\.)?{re.escape(domain)}[/\w\-\.?=&%#]*",
            text,
            re.IGNORECASE,
        )
        if match:
            return match.group(0)
        match = re.search(rf"{re.escape(domain)}[/\w\-\.?]+", text, re.IGNORECASE)
        return f"https://{match.group(0)}" if match else ""

    def _extract_skills(self, text_lower: str) -> list[str]:
        found = []
        for skill in SKILL_KEYWORDS:
            if skill in text_lower:
                display = skill.title() if len(skill) > 3 else skill.upper()
                if display not in found:
                    found.append(display)
        return sorted(found, key=str.lower)[:40]

    def _extract_by_patterns(self, text: str, patterns: list[str]) -> list[str]:
        results = []
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                snippet = match.group(0).strip()
                if snippet and snippet not in results:
                    results.append(snippet[:200])
        return results[:15]

    def _extract_section_lines(self, text: str, keyword: str) -> list[str]:
        lines = text.splitlines()
        in_section = False
        collected = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if keyword in stripped.lower() and len(stripped) < 40:
                in_section = True
                continue
            if in_section:
                if re.match(r"^[A-Z][A-Za-z\s]{2,30}:?\s*$", stripped) and len(collected) > 2:
                    break
                collected.append(stripped[:200])
                if len(collected) >= 10:
                    break
        return collected

    def _enrich_with_spacy(self, text: str, result: dict[str, Any]):
        doc = self._nlp(text[:100000])
        orgs = {ent.text for ent in doc.ents if ent.label_ in ("ORG", "GPE")}
        for org in list(orgs)[:5]:
            if org not in result["education"]:
                result["education"].append(org)
