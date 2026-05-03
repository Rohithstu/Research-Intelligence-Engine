"""
Semantic Search Module

A pluggable semantic retrieval layer using Sentence-BERT + FAISS.
Acts as a clean wrapper around existing embedding + FAISS infrastructure.

Usage:
    results = semantic_search("deep learning transformers", papers, top_k=10)
"""

from typing import List, Dict, Any, Optional
import numpy as np

from models.schemas import Paper
from core.embedder import get_embedder, Embedder
from core.faiss_store import get_faiss_store, FAISSStore


# In-memory cache for paper embeddings to avoid re-embedding
# Key: paper.id, Value: np.ndarray (384,)
_embedding_cache: Dict[str, np.ndarray] = {}


def _combine_text(paper: Paper) -> str:
    """Combine title and abstract for embedding."""
    return f"Title: {paper.title}. Abstract: {paper.abstract}"


def _get_or_compute_embeddings(
    papers: List[Paper],
    embedder: Embedder,
    faiss_store: FAISSStore,
) -> np.ndarray:
    """
    Get or compute embeddings for papers.
    Uses cache to avoid re-embedding the same papers.
    """
    global _embedding_cache

    # Filter papers that need embedding
    papers_to_embed = []
    paper_indices = []

    for i, paper in enumerate(papers):
        if paper.id in _embedding_cache:
            continue  # Already cached
        papers_to_embed.append(paper)
        paper_indices.append(i)

    # Embed new papers if any
    if papers_to_embed:
        texts = [_combine_text(p) for p in papers_to_embed]
        new_embeddings = embedder.embed_batch(texts)

        # Cache the new embeddings
        for paper, emb in zip(papers_to_embed, new_embeddings):
            _embedding_cache[paper.id] = emb

    # Build the embeddings array in original order
    embeddings = np.zeros((len(papers), 384), dtype=np.float32)
    for i, paper in enumerate(papers):
        embeddings[i] = _embedding_cache[paper.id]

    return embeddings


def semantic_search(
    user_query: str,
    papers: List[Paper],
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    Perform semantic search on papers.

    Args:
        user_query: The search query string
        papers: List of Paper objects (with title + abstract)
        top_k: Number of top results to return (default: 10)

    Returns:
        List of dicts with "paper" and "score" keys, sorted by score descending.
        Example: [{"paper": <Paper>, "score": 0.95}, ...]
    """
    if not papers:
        return []

    if not user_query or not user_query.strip():
        return []

    # Get singleton instances
    embedder = get_embedder()
    faiss_store = get_faiss_store()

    # Convert query to embedding
    query_embedding = embedder.embed_text(user_query)

    # Get or compute paper embeddings
    paper_embeddings = _get_or_compute_embeddings(papers, embedder, faiss_store)

    # Add papers to FAISS store temporarily for search
    # Note: We use the FAISS store's search method which works on in-memory data
    # The add_papers method will deduplicate based on paper IDs
    faiss_store.add_papers(papers, paper_embeddings)

    # Perform similarity search
    results = faiss_store.search(query_embedding, top_k=top_k)

    # Build response with paper objects
    paper_map = {paper.id: paper for paper in papers}
    output = []

    for paper_id, score in results:
        if paper_id in paper_map:
            output.append({
                "paper": paper_map[paper_id],
                "score": score,
            })

    return output


def clear_embedding_cache():
    """Clear the embedding cache. Useful for testing or memory management."""
    global _embedding_cache
    _embedding_cache.clear()


def test_semantic_search():
    """
    Test function for semantic search.
    Runs search on dummy papers and prints top results.
    """
    # Create dummy papers
    dummy_papers = [
        Paper(
            id="paper_1",
            title="Deep Learning for Natural Language Processing",
            abstract="This paper presents a novel approach to using deep learning models for NLP tasks, achieving state-of-the-art results on benchmark datasets.",
            authors=["John Smith", "Jane Doe"],
            year=2023,
            citation_count=150,
        ),
        Paper(
            id="paper_2",
            title="Quantum Computing Algorithms",
            abstract="We introduce new quantum algorithms that can solve certain problems exponentially faster than classical computers.",
            authors=["Alice Johnson"],
            year=2022,
            citation_count=89,
        ),
        Paper(
            id="paper_3",
            title="Transformers in Computer Vision",
            abstract="This study explores the application of transformer architectures to image recognition tasks, showing promising results.",
            authors=["Bob Wilson", "Carol White"],
            year=2023,
            citation_count=67,
        ),
        Paper(
            id="paper_4",
            title="Climate Change Impact on Agriculture",
            abstract="We analyze the effects of climate change on crop yields and propose adaptation strategies for farmers.",
            authors=["David Brown"],
            year=2021,
            citation_count=45,
        ),
        Paper(
            id="paper_5",
            title="BERT and GPT Models for Text Generation",
            abstract="A comprehensive comparison of BERT and GPT models for various text generation tasks in natural language processing.",
            authors=["Emma Davis", "Frank Miller"],
            year=2023,
            citation_count=120,
        ),
    ]

    # Test query
    query = "transformer models for text and image understanding"

    print("=" * 60)
    print("SEMANTIC SEARCH TEST")
    print("=" * 60)
    print(f"\nQuery: {query}")
    print(f"Number of papers: {len(dummy_papers)}")
    print(f"Top K: 5")
    print("-" * 60)

    # Run semantic search
    results = semantic_search(query, dummy_papers, top_k=5)

    # Print results
    print(f"\nTop {len(results)} Results:")
    print("-" * 60)

    for i, result in enumerate(results, 1):
        paper = result["paper"]
        score = result["score"]
        print(f"\n#{i}: {paper.title}")
        print(f"    Score: {score:.4f}")
        print(f"    Authors: {', '.join(paper.authors)}")
        print(f"    Year: {paper.year}")
        print(f"    Abstract: {paper.abstract[:100]}...")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

    # Clean up cache after test
    clear_embedding_cache()


if __name__ == "__main__":
    test_semantic_search()
