# Data models for resume extraction details
# & matched evaluation results.
from dataclasses import dataclass, field
from typing import Any


@dataclass
# keep major things like: metadata, contact details, and skills extracted from the docs
class ExtractedProfile:
    raw_text: str = ""
    email: str | None = None
    phone: str | None = None
    github: str | None = None
    linkedin: str | None = None
    degrees: list[str] = field(default_factory=list)
    skills: set[str] = field(default_factory=set)
    taxonomy_skills: set[str] = field(default_factory=set)
    dynamic_skills: set[str] = field(default_factory=set)
    skills_with_sources: dict[str, str] = field(default_factory=dict)
    achievements: list[str] = field(default_factory=list)
    volunteering: list[str] = field(default_factory=list)
    section_texts: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "email": self.email,
            "phone": self.phone,
            "github": self.github,
            "linkedin": self.linkedin,
            "degrees": self.degrees,
            "skills": sorted(self.skills),
            "taxonomy_skills": sorted(self.taxonomy_skills),
            "dynamic_skills": sorted(self.dynamic_skills),
            "skills_with_sources": self.skills_with_sources,
            "achievements": self.achievements,
            "volunteering": self.volunteering,
            "section_texts": self.section_texts,
        }


@dataclass
# result of matching a cv details for a job description ( with scores and skills )
class MatchResult:
    cv_id: str
    job_id: str
    overall_score: float
    semantic_score: float
    skill_score: float
    matched_skills: set[str] = field(default_factory=set)
    missing_skills: set[str] = field(default_factory=set)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cv_id": self.cv_id,
            "job_id": self.job_id,
            "overall_score": self.overall_score,
            "semantic_score": self.semantic_score,
            "skill_score": self.skill_score,
            "matched_skills": sorted(self.matched_skills),
            "missing_skills": sorted(self.missing_skills),
        }
