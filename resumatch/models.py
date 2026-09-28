# Data models for resume extraction details
# & matched evaluation results.

from dataclasses import dataclass, field


@dataclass
# keep major things like: metadata, contact details, and skills extracted from the docs
class ExtractedProfile:
    raw_text: str
    email: str | None = None
    phone: str | None = None
    github: str | None = None
    linkedin: str | None = None
    degrees: list[str] = field(default_factory=list)
    skills: set[str] = field(default_factory=set)
    taxonomy_skills: set[str] = field(default_factory=set)
    dynamic_skills: set[str] = field(default_factory=set)
    skills_with_sources: dict[str, str] = field(default_factory=dict)

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
