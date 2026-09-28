import logging
import numpy as np
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

# contextual Cross-Encoder reranker for more precise scoring
class DeepReranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-base") -> None:
        logger.info(f"Loading Stage 2 Cross-Encoder model: {model_name}")
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, documents: list[str]) -> list[float]:
        if not documents:
            return []

        pairs = [[query, doc] for doc in documents]
        raw_logits = self.model.predict(pairs)

        if isinstance(raw_logits, (float, int, np.floating)):
            raw_logits = np.array([raw_logits])

        # use Sigmoid to make in range of 0.0 - 1.0 range
        scores = 1 / (1 + np.exp(-raw_logits))
        return [float(s) for s in scores]



if __name__ == "__main__":
    reranker = DeepReranker()

    job_text = "Seeking Python Engineer with experience in PyTorch and Machine Learning."
    candidate_texts = [
        "Data Scientist with 3 years building ML models using PyTorch and Python.",
        "Frontend React Developer specializing in CSS and HTML layout.",
    ]

    scores = reranker.rerank(job_text, candidate_texts)

    for i, score in enumerate(scores):
        print(f"Candidate {i+1} Rerank Score: {score * 100:.2f}%")