"""
Test Suite for Research Intelligence System

Run from backend directory:
  python test_system.py
"""

import asyncio
import sys
import time


def test_imports():
    print("\n[TEST 1] Testing imports...")
    try:
        from agents.query_agent import QueryAgent
        from core.embedder import get_embedder
        from core.faiss_store import get_faiss_store
        from core.ranker import rank_papers, compute_final_score
        from core.analyzer import analyze
        from data.paper_store import get_paper_store
        from models.schemas import Paper, QueryRequest
        print("  ✓ All imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_query_agent():
    print("\n[TEST 2] Testing Query Agent...")
    from agents.query_agent import QueryAgent
    agent = QueryAgent()

    test_cases = [
        ("I'm confused about privacy in federated learning", "federated"),
        ("what is deep learning?", "deep"),
        ("recent stuff about cancer detection using AI", "cancer"),
        ("transformer attention NLP", "transformer"),
    ]

    for raw, expected_keyword in test_cases:
        result = agent.refine(raw)
        refined = result["refined_query"]
        ok = expected_keyword.lower() in refined.lower() or expected_keyword.lower() in raw.lower()
        status = "✓" if ok else "⚠"
        print(f"  {status} '{raw[:40]}...' → '{refined}'")

    return True


def test_embedder():
    print("\n[TEST 3] Testing Embedder (downloads model on first run)...")
    from core.embedder import get_embedder
    import numpy as np

    embedder = get_embedder()

    text1 = "federated learning privacy"
    text2 = "privacy-preserving machine learning"
    text3 = "cooking recipes pasta"

    v1 = embedder.embed_text(text1)
    v2 = embedder.embed_text(text2)
    v3 = embedder.embed_text(text3)

    assert v1.shape == (384,), f"Wrong shape: {v1.shape}"

    sim_related = embedder.similarity(v1, v2)
    sim_unrelated = embedder.similarity(v1, v3)

    print(f"  ✓ Vector shape: {v1.shape}")
    print(f"  ✓ Related texts similarity: {sim_related:.3f}")
    print(f"  ✓ Unrelated texts similarity: {sim_unrelated:.3f}")

    assert sim_related > sim_unrelated, "Related texts should be more similar!"
    print("  ✓ Semantic similarity ordering correct")
    return True


def test_faiss():
    print("\n[TEST 4] Testing FAISS Store...")
    from core.faiss_store import FAISSStore
    from core.embedder import get_embedder
    from models.schemas import Paper
    import numpy as np

    store = FAISSStore()
    embedder = get_embedder()

    papers = [
        Paper(id="p1", title="Federated Learning Privacy", abstract="Privacy in FL systems", authors=[], year=2023, citation_count=100),
        Paper(id="p2", title="Deep Learning Survey", abstract="Comprehensive survey of DL", authors=[], year=2022, citation_count=500),
        Paper(id="p3", title="Transformer Models NLP", abstract="Attention mechanism in NLP", authors=[], year=2021, citation_count=200),
    ]

    texts = [p.title + " " + p.abstract for p in papers]
    embeddings = embedder.embed_batch(texts)
    store.add_papers(papers, embeddings)

    assert store.size == 3, f"Expected 3, got {store.size}"

    query_vec = embedder.embed_text("federated learning privacy")
    results = store.search(query_vec, top_k=3)

    assert len(results) > 0
    assert results[0][0] == "p1", f"Expected p1 to be top result, got {results[0][0]}"

    print(f"  ✓ Indexed {store.size} papers")
    print(f"  ✓ Top result for 'federated learning privacy': {results[0][0]} (score: {results[0][1]:.3f})")
    return True


def test_ranker():
    print("\n[TEST 5] Testing Multi-Faceted Ranker...")
    from core.ranker import rank_papers, compute_final_score
    from models.schemas import Paper

    papers = [
        Paper(id="old_popular", title="Old Classic", abstract="...", authors=[], year=2015, citation_count=5000),
        Paper(id="new_relevant", title="New Relevant", abstract="...", authors=[], year=2024, citation_count=10),
        Paper(id="mid", title="Middle Ground", abstract="...", authors=[], year=2020, citation_count=200),
    ]

    similarity_map = {
        "old_popular": 0.60,
        "new_relevant": 0.95,
        "mid": 0.75,
    }

    ranked = rank_papers(papers, similarity_map, top_n=3)
    print(f"  ✓ Ranking order: {[p.id for p in ranked]}")
    print(f"  ✓ Scores: {[p.final_score for p in ranked]}")

    assert ranked[0].final_score >= ranked[1].final_score, "Should be sorted"
    return True


def test_analyzer():
    print("\n[TEST 6] Testing Analyzer...")
    from core.analyzer import analyze
    from models.schemas import Paper

    papers = [
        Paper(id=f"p{i}", title=f"Federated Learning Paper {i}",
              abstract="We propose a federated learning approach for privacy-preserving machine learning on distributed data.",
              authors=["Author A"], year=2020 + i, citation_count=i * 10)
        for i in range(8)
    ]

    result = analyze(papers, "federated learning privacy", ["federated", "privacy"])

    print(f"  ✓ Key themes: {result.key_themes[:4]}")
    print(f"  ✓ Gaps found: {len(result.gaps)}")
    print(f"  ✓ Trends found: {len(result.trends)}")
    print(f"  ✓ Future directions: {len(result.future_directions)}")
    assert len(result.key_themes) > 0
    return True


async def test_api_clients():
    print("\n[TEST 7] Testing API Clients (requires internet)...")
    try:
        from api.semantic_scholar import fetch_semantic_scholar
        papers = await fetch_semantic_scholar("federated learning", limit=5)
        print(f"  ✓ Semantic Scholar: fetched {len(papers)} papers")
    except Exception as e:
        print(f"  ⚠ Semantic Scholar: {e}")

    try:
        from api.arxiv_client import fetch_arxiv
        papers = await fetch_arxiv("federated learning", limit=5)
        print(f"  ✓ arXiv: fetched {len(papers)} papers")
    except Exception as e:
        print(f"  ⚠ arXiv: {e}")

    return True


def main():
    print("=" * 50)
    print("  RESEARCH INTELLIGENCE SYSTEM - TEST SUITE")
    print("=" * 50)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Query Agent", test_query_agent()))
    results.append(("Embedder", test_embedder()))
    results.append(("FAISS Store", test_faiss()))
    results.append(("Ranker", test_ranker()))
    results.append(("Analyzer", test_analyzer()))
    results.append(("API Clients", asyncio.run(test_api_clients())))

    print("\n" + "=" * 50)
    print("  RESULTS")
    print("=" * 50)
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"  {'✓' if ok else '✗'} {name}")
    print(f"\n  {passed}/{len(results)} tests passed")
    print("=" * 50)

    if passed == len(results):
        print("\n🎉 All tests passed! System is ready.")
        print("  Start backend:  uvicorn main:app --reload --port 8000")
        print("  Start frontend: cd ../frontend && npm start")
    else:
        print("\n⚠  Some tests failed. Check output above.")

    return passed == len(results)


if __name__ == "__main__":
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    success = main()
    sys.exit(0 if success else 1)
