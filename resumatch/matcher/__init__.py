"""Matcher subpackage exposing retrieval, reranking, heuristics, and composite engines."""

from resumatch.matcher.heuristics import SkillAnalysisResult, SkillOverlapHeuristics
from resumatch.matcher.reranker import DeepReranker
from resumatch.matcher.resume_matcher import CompositeMatcher, MatchResult
from resumatch.matcher.retriever import SemanticRetriever

__all__ = [
    "CompositeMatcher",
    "DeepReranker",
    "MatchResult",
    "SemanticRetriever",
    "SkillAnalysisResult",
    "SkillOverlapHeuristics",
]
