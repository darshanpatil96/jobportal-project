"""
Candidate–job matching engine.

Combines keyword overlap, category weighting, and simple semantic similarity
(bag-of-words cosine) with an embedding-ready JSON snapshot for future ML.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from core.ai.resume_parser import SKILL_KEYWORDS


class MatchingEngineService:
    """Compute compatibility scores between parsed resumes and job postings."""

    SOFT_SKILL_KEYWORDS = [
        "communication", "leadership", "teamwork", "problem solving",
        "collaboration", "presentation", "management",
    ]

    def compute_match(
        self,
        job_description: str,
        job_category: str,
        parsed_resume: dict[str, Any],
        explicit_required_skills: list | None = None,
    ) -> dict[str, Any]:
        resume_skills = [s.lower() for s in parsed_resume.get("skills", [])]
        job_skills = self._extract_job_skills(
            job_description, job_category, explicit_required_skills or []
        )

        if not job_skills and resume_skills:
            job_skills = resume_skills[:10]

        skill_details = {}
        matched = []
        missing = []

        for skill in job_skills:
            score = self._skill_match_score(skill, resume_skills, job_description)
            skill_details[skill] = round(score, 1)
            if score >= 50:
                matched.append(skill)
            else:
                missing.append(skill)

        skills_overlap = self._average(skill_details.values()) if skill_details else 0
        education_score = self._education_relevance(
            parsed_resume.get("education", []), job_description, job_category
        )
        experience_score = self._experience_relevance(
            parsed_resume.get("experience", []),
            parsed_resume.get("raw_text", ""),
            job_description,
        )
        semantic_score = self._semantic_similarity(
            job_description,
            parsed_resume.get("raw_text", "")
            or " ".join(parsed_resume.get("experience", [])),
        )
        keyword_score = self._keyword_overlap(job_description, parsed_resume)

        category_scores = {
            "skills": round(skills_overlap, 1),
            "education": round(education_score, 1),
            "experience": round(experience_score, 1),
            "semantic": round(semantic_score, 1),
            "keywords": round(keyword_score, 1),
        }

        weights = {
            "skills": 0.40,
            "education": 0.15,
            "experience": 0.20,
            "semantic": 0.15,
            "keywords": 0.10,
        }
        overall = sum(
            category_scores[k] * weights[k] for k in weights
        )

        soft_scores = self._soft_skill_levels(parsed_resume, job_description)

        return {
            "overall_score": round(min(100, max(0, overall)), 1),
            "category_scores": category_scores,
            "skill_details": skill_details,
            "missing_skills": missing[:15],
            "matched_skills": matched[:15],
            "soft_skills": soft_scores,
            "embedding_snapshot": {
                "job_tokens": self._tokenize(job_description)[:200],
                "resume_tokens": self._tokenize(
                    parsed_resume.get("raw_text", "")
                )[:200],
                "version": 1,
            },
        }

    def _extract_job_skills(
        self, description: str, category: str, explicit: list
    ) -> list[str]:
        desc_lower = description.lower()
        found = [s for s in explicit if s]
        for skill in SKILL_KEYWORDS:
            if skill in desc_lower:
                label = skill.title() if len(skill) > 3 else skill.upper()
                if label not in found:
                    found.append(label)
        if category and category.lower() not in [f.lower() for f in found]:
            found.append(category)
        return found[:25]

    def _skill_match_score(
        self, job_skill: str, resume_skills: list[str], description: str
    ) -> float:
        js = job_skill.lower()
        if any(js in rs or rs in js for rs in resume_skills):
            return 92.0
        if js in description.lower():
            return 35.0
        return 15.0

    def _education_relevance(
        self, education: list, description: str, category: str
    ) -> float:
        if not education:
            return 40.0
        desc = description.lower()
        hits = sum(
            1 for edu in education if any(w in desc for w in edu.lower().split()[:3])
        )
        base = min(100, 50 + hits * 15)
        if category and any(category.lower() in e.lower() for e in education):
            base = min(100, base + 20)
        return float(base)

    def _experience_relevance(
        self, experience: list, raw_text: str, description: str
    ) -> float:
        blob = " ".join(experience + [raw_text[:3000]]).lower()
        desc = description.lower()
        if not blob.strip():
            return 35.0
        desc_words = set(self._tokenize(desc))
        exp_words = set(self._tokenize(blob))
        if not desc_words:
            return 50.0
        overlap = len(desc_words & exp_words) / len(desc_words)
        years = re.findall(r"(\d+)\+?\s*years?", blob)
        bonus = min(20, int(years[0])) if years else 0
        return min(100, 40 + overlap * 50 + bonus)

    def _semantic_similarity(self, job_text: str, resume_text: str) -> float:
        v1 = Counter(self._tokenize(job_text))
        v2 = Counter(self._tokenize(resume_text))
        if not v1 or not v2:
            return 30.0
        common = set(v1) & set(v2)
        dot = sum(v1[t] * v2[t] for t in common)
        mag1 = math.sqrt(sum(c * c for c in v1.values()))
        mag2 = math.sqrt(sum(c * c for c in v2.values()))
        if mag1 == 0 or mag2 == 0:
            return 30.0
        cosine = dot / (mag1 * mag2)
        return min(100, cosine * 100)

    def _keyword_overlap(self, description: str, parsed: dict) -> float:
        desc_tokens = set(self._tokenize(description))
        resume_tokens = set(
            self._tokenize(
                " ".join(
                    parsed.get("skills", [])
                    + parsed.get("experience", [])
                    + parsed.get("education", [])
                )
            )
        )
        if not desc_tokens:
            return 50.0
        overlap = len(desc_tokens & resume_tokens) / len(desc_tokens)
        return min(100, overlap * 100)

    def _soft_skill_levels(self, parsed: dict, description: str) -> dict[str, str]:
        text = (
            parsed.get("raw_text", "")
            + " "
            + " ".join(parsed.get("skills", []))
        ).lower()
        desc = description.lower()
        levels = {}
        for skill in self.SOFT_SKILL_KEYWORDS:
            in_resume = skill in text
            in_job = skill in desc
            if in_resume and in_job:
                levels[skill.title()] = "High"
            elif in_resume or in_job:
                levels[skill.title()] = "Medium"
            else:
                levels[skill.title()] = "Low"
        return levels

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[a-z0-9+#.]{2,}", text.lower())

    def _average(self, values) -> float:
        vals = list(values)
        return sum(vals) / len(vals) if vals else 0.0
