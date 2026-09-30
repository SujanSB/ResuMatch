from dataclasses import dataclass, field


@dataclass
class SkillAnalysisResult:
    score: float
    matched_skills: set[str] = field(default_factory=set)
    missing_skills: set[str] = field(default_factory=set)


# calculate ratio of matched skills to job requirements
class SkillOverlapHeuristics:
    @staticmethod
    def normalize_skill(skill: str) -> str:
        return skill.strip().lower()

    # with basic formula: coverage_ratio = len(matched_skills) / len(job_skills)
    def evaluate_skills(
        self, cv_skills: set[str], job_skills: set[str]
    ) -> SkillAnalysisResult:
        if not job_skills:
            return SkillAnalysisResult(score=1.0)

        normalized_cv = {self.normalize_skill(s) for s in cv_skills if s}
        normalized_job = {self.normalize_skill(s) for s in job_skills if s}

        matched = normalized_cv.intersection(normalized_job)
        missing = normalized_job - normalized_cv

        coverage_ratio = len(matched) / len(normalized_job) if normalized_job else 0.0

        return SkillAnalysisResult(
            score=float(coverage_ratio),
            matched_skills=matched,
            missing_skills=missing,
        )


if __name__ == "__main__":
    heuristics = SkillOverlapHeuristics()

    cv_skills = {"python", "SQL", "Docker", "Git"}
    job_skills = {"Python", "SQL", "Kubernetes", "AWS"}

    result = heuristics.evaluate_skills(cv_skills, job_skills)

    print(f"Skill Coverage Score: {result.score * 100:.2f}%")
    print(f"Matched Skills: {result.matched_skills}")
    print(f"Missing Skills: {result.missing_skills}")
