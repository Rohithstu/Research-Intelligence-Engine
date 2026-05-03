"""
Sentence-BERT Embedder
Model: all-MiniLM-L6-v2 (fast, good quality, 384-dim)

Vector Embedding = converting text into numerical vectors
so machines can understand MEANING, not just keywords.
"""

import numpy as np
from typing import List, Optional
from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


class Embedder:
    """
    Wraps Sentence-BERT for text → vector conversion.

    Why MiniLM-L6-v2?
    - Fast (only 6 layers)
    - Small (80MB)
    - Good semantic quality
    - 384-dimensional vectors
    """

    def __init__(self):
        print(f"[Embedder] Loading model: {MODEL_NAME}")
        self._model: Optional[SentenceTransformer] = None

    def _load(self):
        if self._model is None:
            self._model = SentenceTransformer(MODEL_NAME)
            print("[Embedder] Model loaded successfully")

    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single string → 1D numpy array (384,)"""
        self._load()
        vec = self._model.encode(text, normalize_embeddings=True)
        return vec.astype(np.float32)

    def embed_batch(self, texts: List[str], batch_size: int = 64) -> np.ndarray:
        """
        Embed a list of strings → 2D numpy array (N, 384)
        Uses batching for efficiency.
        """
        self._load()
        vecs = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 50,
        )
        return vecs.astype(np.float32)

    def similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """
        Cosine similarity between two normalized vectors.
        Since vectors are L2-normalized, dot product = cosine similarity.
        """
        return float(np.dot(vec_a, vec_b))


# Singleton instance
_embedder_instance: Optional[Embedder] = None


def get_embedder() -> Embedder:
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = Embedder()
    return _embedder_instance
