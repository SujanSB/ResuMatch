import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from resumatch.matcher.resume_matcher import CompositeMatcher, MatchResult

logger = logging.getLogger(__name__)

# recommender 
class CandidateRecommender:
    def __init__(self, semantic_weight: float = 0.7, skill_weight: float = 0.3) -> None:
        self.matcher = CompositeMatcher(
            semantic_weight=semantic_weight,
            skill_weight=skill_weight,
        )

    def _determine_tier(self, overall_score: float) -> str:
        # heuristic recommendation benchmark
        if overall_score >= 75.0:
            return "Strongly Recommended"
        elif overall_score >= 50.0:
            return "Consider / Worth Interviewing"
        else:
            return "Not Recommended"

    def _build_candidate_json(
        self,
        candidate_input: Dict[str, Any],
        match: MatchResult,
        rank: Optional[int] = None,
    ) -> Dict[str, Any]:
        
        candidate_id = candidate_input.get("id", match.cv_id)
        
        # extract metadata from extractor
        profile_meta = candidate_input.get("metadata", {})
        extracted_skills = list(candidate_input.get("skills", set()))

        return {
            "rank": rank,
            "candidate_id": candidate_id,
            "candidate_details": {
                "name": candidate_input.get("name", profile_meta.get("name", candidate_id)),
                "email": candidate_input.get("email", profile_meta.get("email", "N/A")),
                "phone": candidate_input.get("phone", profile_meta.get("phone", "N/A")),
                "total_experience_years": candidate_input.get(
                    "experience_years", profile_meta.get("experience_years", "N/A")
                ),
                "extracted_skills_count": len(extracted_skills),
                "top_skills": sorted(extracted_skills)[:10],
            },
            "recommendation_tier": self._determine_tier(match.overall_score),
            "match_scores": {
                "overall_fit_percentage": match.overall_score,
                "semantic_context_score": match.semantic_score,
                "skill_coverage_score": match.skill_score,
            },
            "skills_analysis": {
                "matched_skills_count": len(match.matched_skills),
                "missing_skills_count": len(match.missing_skills),
                "matched_skills": sorted(list(match.matched_skills)),
                "missing_skills": sorted(list(match.missing_skills)),
            },
        }

    # evaluate and recommend single pair
    def recommend_single(
        self,
        candidate: Dict[str, Any],
        job: Dict[str, Any],
    ) -> str:
       
        match = self.matcher.evaluate_single(
            cv_id=candidate["id"],
            cv_text=candidate["text"],
            cv_skills=set(candidate.get("skills", set())),
            job_id=job["id"],
            job_text=job["text"],
            job_skills=set(job.get("skills", set())),
        )

        cand_json = self._build_candidate_json(candidate, match, rank=1)

        report = {
            "mode": "single_pair",
            "job_id": job["id"],
            "job_title": job.get("title", job["id"]),
            "candidate_recommendation": cand_json,
        }

        return json.dumps(report, indent=2)

    # evaluate and recommend multiple pair / batch
    def recommend_batch(
        self,
        candidates: List[Dict[str, Any]],
        jobs: Union[Dict[str, Any], List[Dict[str, Any]]],
        top_k: int = 10,
    ) -> str:
        # it takes candidates and jobs pair. 
        job_list = [jobs] if isinstance(jobs, dict) else jobs
        cand_map = {c["id"]: c for c in candidates}

        # resume_matcher in use
        match_results_map: Dict[str, List[MatchResult]] = self.matcher.evaluate_batch(
            candidates=candidates,
            jobs=job_list,
            top_k_retrieval=len(candidates),
        )

        job_reports = []
        for job in job_list:
            job_id = job["id"]
            job_matches = match_results_map.get(job_id, [])

            ranked_candidates = []
            for rank, m in enumerate(job_matches[:top_k], start=1):
                original_cand = cand_map.get(m.cv_id, {"id": m.cv_id, "skills": m.matched_skills})
                cand_json = self._build_candidate_json(original_cand, m, rank=rank)
                ranked_candidates.append(cand_json)

            job_reports.append({
                "job_id": job_id,
                "job_title": job.get("title", job_id),
                "total_candidates_evaluated": len(candidates),
                "recommended_candidates": ranked_candidates,
            })

        output = {
            "mode": "batch_ranking",
            "total_jobs_evaluated": len(job_list),
            "jobs": job_reports,
        }

        return json.dumps(output, indent=2)



if __name__ == "__main__":
    recommender = CandidateRecommender()

    sample_candidates = [
        {
            "id": "CV_002_Sujan_Sharma",
            "name": "Sujan Sharma",
            "email": "ersujansharma@gmail.com",
            "experience_years": 3.5,
            "text": "M.Sc. Data Science student skilled in Python, PyTorch, LangChain, RAG, Docker, AWS, SQL.",
            "skills": {"Python", "PyTorch", "LangChain", "RAG", "Docker", "AWS", "SQL", "FastAPI"},
        },
        {
            "id": "CV_003_Alice_Johnson",
            "name": "Alice Johnson",
            "email": "alice.johnson@example.com",
            "experience_years": 5,
            "text": "Experienced Data Scientist with expertise in Python, Machine Learning, and Deep Learning.",
            "skills": {"Python", "Machine Learning", "Deep Learning", "SQL"},
        }
    ]
    sample_jobs = [
        {
            "id": "JOB_101_AI_Engineer",
            "title": "Senior AI / ML Engineer",
            "text": "Looking for AI Engineer with Python, PyTorch, RAG, LangChain, Docker, and AWS.",
            "skills": {"Python", "PyTorch", "RAG", "LangChain", "Docker", "AWS", "Kubernetes"},
        },
        {
            "id": "JOB_102_Data_Scientist",
            "title": "Data Scientist",
            "text": "Seeking a Data Scientist with expertise in Python, Machine Learning, and Deep Learning.",
            "skills": {"Python", "Machine Learning", "Deep Learning", "SQL"},
        }
    ]
   

    # print("--- SINGLE PAIR RECOMMENDATION JSON ---")
    # json_single = recommender.recommend_single(sample_candidates[0], sample_jobs[0])
    # print(json_single)

    print("--- BATCH RECOMMENDATION JSON ---")
    top_k = 1 # lets look only 1
    batch_json = recommender.recommend_batch(sample_candidates, sample_jobs, top_k)
    print(batch_json)