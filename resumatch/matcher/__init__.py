"""Matcher subpackage exposing retrieval, reranking, heuristics, and composite engines."""

from resumatch.matcher.retriever import SemanticRetriever
from resumatch.matcher.reranker import DeepReranker
from resumatch.matcher.heuristics import SkillOverlapHeuristics, SkillAnalysisResult
from resumatch.matcher.resume_matcher import CompositeMatcher, MatchResult

__all__ = [
    "SemanticRetriever",
    "DeepReranker",
    "SkillOverlapHeuristics",
    "SkillAnalysisResult",
    "CompositeMatcher",
    "MatchResult",
]
