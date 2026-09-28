from dataclasses import dataclass, field
import numpy as np

from resumatch.models import MatchResult
from resumatch.matcher.retriever import SemanticRetriever
from resumatch.matcher.reranker import DeepReranker
from resumatch.matcher.heuristics import SkillOverlapHeuristics, SkillAnalysisResult


# combining neural retrieval + heuristic skill analysis
class CompositeMatcher:
    def __init__(
        self,
        semantic_weight: float = 0.7,
        skill_weight: float = 0.3,
        bi_encoder_model: str = "all-MiniLM-L6-v2",
        cross_encoder_model: str = "BAAI/bge-reranker-base",
    ) -> None:
        self.semantic_weight = semantic_weight
        self.skill_weight = skill_weight

        self.retriever = SemanticRetriever(model_name=bi_encoder_model)
        self.reranker = DeepReranker(model_name=cross_encoder_model)
        self.heuristics = SkillOverlapHeuristics()

    # for single cv
    def evaluate_single(
        self,
        cv_id: str,
        cv_text: str,
        cv_skills: set[str],
        job_id: str,
        job_text: str,
        job_skills: set[str],
    ) -> MatchResult:
       
        # direct rerank 
        rerank_score = self.reranker.rerank(job_text, [cv_text])[0]

        # heuristic Analysis
        skill_res: SkillAnalysisResult = self.heuristics.evaluate_skills(
            cv_skills, job_skills
        )

        # weighted composite calculation
        overall = (self.semantic_weight * rerank_score) + (
            self.skill_weight * skill_res.score
        )

        return MatchResult(
            cv_id=cv_id,
            job_id=job_id,
            overall_score=round(overall * 100, 2),
            semantic_score=round(rerank_score * 100, 2),
            skill_score=round(skill_res.score * 100, 2),
            matched_skills=skill_res.matched_skills,
            missing_skills=skill_res.missing_skills,
        )

    def evaluate_batch(
        self,
        candidates: list[dict],
        job: dict,
        top_k_retrieval: int = 50,
    ) -> list[MatchResult]:
        
        # Here, Two-step Retrieval and Reranking
        
        
        if not candidates:
            return []

        # First: Fast Retrieval
        cv_texts = [c["text"] for c in candidates]
        cv_embeddings = self.retriever.encode(cv_texts)
        job_embedding = self.retriever.encode([job["text"]])

        retrieved_items = self.retriever.search(
            job_embedding, cv_embeddings, top_k=top_k_retrieval
        )
        retrieved_indices = [idx for idx, _ in retrieved_items]
        selected_candidates = [candidates[i] for i in retrieved_indices]

        # Second: Deep Reranking on retrieved candidates
        selected_texts = [c["text"] for c in selected_candidates]
        semantic_scores = self.reranker.rerank(job["text"], selected_texts)

        results = []
        for cand, sem_score in zip(selected_candidates, semantic_scores):
            skill_res = self.heuristics.evaluate_skills(
                cand.get("skills", set()), job.get("skills", set())
            )

            overall = (self.semantic_weight * sem_score) + (
                self.skill_weight * skill_res.score
            )

            results.append(
                MatchResult(
                    cv_id=cand["id"],
                    job_id=job["id"],
                    overall_score=round(overall * 100, 2),
                    semantic_score=round(sem_score * 100, 2),
                    skill_score=round(skill_res.score * 100, 2),
                    matched_skills=skill_res.matched_skills,
                    missing_skills=skill_res.missing_skills,
                )
            )

        # sort results by overall score
        results.sort(key=lambda x: x.overall_score, reverse=True)
        return results


if __name__ == "__main__":
    matcher = CompositeMatcher()

    res = matcher.evaluate_single(
        cv_id="CV_001",
        cv_text="Data Scientist proficient in Python, SQL, and PyTorch.",
        cv_skills={"Python", "SQL", "PyTorch"},
        job_id="JOB_101",
        job_text="Looking for Data Scientist with Python, SQL, and AWS experience.",
        job_skills={"Python", "SQL", "AWS"},
    )

    print(f"CV: {res.cv_id} | Job: {res.job_id}")
    print(f"Overall Fit:    {res.overall_score}%")
    print(f"Semantic Match: {res.semantic_score}%")
    print(f"Skill Score:    {res.skill_score}%")
    print(f"Matched Skills: {res.matched_skills}")
    print(f"Missing Skills: {res.missing_skills}")