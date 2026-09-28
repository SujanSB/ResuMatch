# semantic retriever: Fast Bi-Encoder Dense Retrieval Engine

import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# vector search retriever using sentence embeddings
class SemanticRetriever:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        logger.info(f"Loading Stage 1 Bi-Encoder model: {model_name}")
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        """Converts a list of raw text strings into a 2D numpy array of embeddings."""
        return self.model.encode(
            texts, convert_to_numpy=True, show_progress_bar=False
        )

    def search(
        self,
        query_embedding: np.ndarray,
        doc_embeddings: np.ndarray,
        top_k: int = 50,
    ) -> list[tuple[int, float]]:
        # calculate similarity between query and document
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
        top_indices = np.argsort(similarities)[::-1][:top_k]

        return [(int(idx), float(similarities[idx])) for idx in top_indices]



if __name__ == "__main__":

    retriever = SemanticRetriever()

    candidates = [
        "Senior Python Engineer with FastAPI and PostgreSQL expertise.",
        "Graphic Designer skilled in Photoshop, Figma, and UI/UX.",
        "Data Scientist working on PyTorch, Machine Learning, and NLP.",
    ]
    job_query = "Looking for a Python Backend Developer skilled in SQL databases."

    doc_embs = retriever.encode(candidates)
    query_emb = retriever.encode([job_query])

    top_matches = retriever.search(query_emb, doc_embs, top_k=2)

    for rank, (idx, score) in enumerate(top_matches, start=1):
        print(f"Rank {rank} (Score: {score:.4f}): {candidates[idx]}")