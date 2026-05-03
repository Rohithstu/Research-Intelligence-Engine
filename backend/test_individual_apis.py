import asyncio
from api.semantic_scholar import fetch_semantic_scholar
from api.arxiv_client import fetch_arxiv
from api.open_alex import fetch_open_alex
from api.crossref import fetch_crossref

async def test_apis():
    query = "deep learning"
    print("Testing Semantic Scholar...")
    s2 = await fetch_semantic_scholar(query, limit=5)
    print("S2 Found:", len(s2))

    print("\nTesting arXiv...")
    ar = await fetch_arxiv(query, limit=5)
    print("arXiv Found:", len(ar))

    print("\nTesting OpenAlex...")
    oa = await fetch_open_alex(query, limit=5)
    print("OpenAlex Found:", len(oa))

    print("\nTesting Crossref...")
    cr = await fetch_crossref(query, limit=5)
    print("Crossref Found:", len(cr))

if __name__ == "__main__":
    asyncio.run(test_apis())
