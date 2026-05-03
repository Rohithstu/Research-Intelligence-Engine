"""
FAISS Vector Store

FAISS = Facebook AI Similarity Search
Purpose: Store embeddings and do ultra-fast nearest-neighbor search.

Why FAISS?
- Handles millions of vectors
- Sub-millisecond search
- Battle-tested at Facebook/Meta scale
"""

import numpy as np
import faiss
from typing import List, Tuple, Optional, Dict
from models.schemas import Paper


EMBEDDING_DIM = 384


class FAISSStore:
    """
    In-memory FAISS index for paper embeddings.

    We use IndexFlatIP (Inner Product) because:
    - Our embeddings are L2-normalized
    - Inner product on normalized vectors = cosine similarity
    - Exact search (no approximation needed for <10k papers)
    """

    def __init__(self):
        # IndexFlatIP = exact search using inner product (cosine similarity)
        self.index = faiss.IndexFlatIP(EMBEDDING_DIM)
        self.paper_ids: List[str] = []   # maps FAISS index → paper ID
        self._id_to_pos: Dict[str, int] = {}  # paper ID → FAISS position

    @property
    def size(self) -> int:
        return self.index.ntotal

    def add_papers(self, papers: List[Paper], embeddings: np.ndarray):
        """
        Add papers and their embeddings to the index.

        Args:
            papers: list of Paper objects
            embeddings: 2D numpy array of shape (N, 384), float32, L2-normalized
        """
        if len(papers) == 0:
            return

        assert embeddings.shape == (len(papers), EMBEDDING_DIM), \
            f"Shape mismatch: {embeddings.shape} vs ({len(papers)}, {EMBEDDING_DIM})"
        assert embeddings.dtype == np.float32, "Embeddings must be float32"

        # Only add papers not already in index
        new_papers = []
        new_embeddings = []
        for paper, emb in zip(papers, embeddings):
            if paper.id not in self._id_to_pos:
                self._id_to_pos[paper.id] = len(self.paper_ids)
                self.paper_ids.append(paper.id)
                new_papers.append(paper)
                new_embeddings.append(emb)

        if new_embeddings:
            self.index.add(np.array(new_embeddings, dtype=np.float32))

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 100,
    ) -> List[Tuple[str, float]]:
        """
        Search for most similar papers.

        Returns list of (paper_id, similarity_score) sorted by score desc.
        """
        if self.size == 0:
            return []

        query = query_embedding.reshape(1, -1).astype(np.float32)
        k = min(top_k, self.size)

        scores, indices = self.index.search(query, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.paper_ids):
                results.append((self.paper_ids[idx], float(score)))

        return results

    def clear(self):
        self.index.reset()
        self.paper_ids.clear()
        self._id_to_pos.clear()


# Singleton
_store_instance: Optional[FAISSStore] = None


def get_faiss_store() -> FAISSStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = FAISSStore()
    return _store_instance
