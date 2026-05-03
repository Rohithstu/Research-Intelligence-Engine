"""
Semantic Scholar API Client
Official API: https://api.semanticscholar.org/
Free, no key required for basic use.
"""

import httpx
import asyncio
from typing import List, Optional
from models.schemas import Paper


SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

FIELDS = [
    "paperId", "title", "abstract", "authors", "year",
    "citationCount", "externalIds", "url"
]


async def fetch_semantic_scholar(
    query: str,
    limit: int = 50,
    offset: int = 0,
) -> List[Paper]:
    """
    Fetch papers from Semantic Scholar API.
    Returns list of Paper objects (metadata only, no PDFs).
    """
    params = {
        "query": query,
        "limit": min(limit, 100),
        "offset": offset,
        "fields": ",".join(FIELDS),
    }

    papers: List[Paper] = []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(SEMANTIC_SCHOLAR_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        for item in data.get("data", []):
            abstract = item.get("abstract") or ""
            if not abstract or len(abstract) < 30:
                continue  # skip papers without useful abstracts

            authors = [
                a.get("name", "Unknown")
                for a in item.get("authors", [])[:5]
            ]

            ext_ids = item.get("externalIds") or {}
            doi = ext_ids.get("DOI")
            paper_id = item.get("paperId", "")

            papers.append(Paper(
                id=f"ss_{paper_id}",
                title=item.get("title", "Untitled"),
                abstract=abstract,
                authors=authors,
                year=item.get("year"),
                citation_count=item.get("citationCount", 0),
                doi=doi,
                url=item.get("url") or f"https://www.semanticscholar.org/paper/{paper_id}",
                source="semantic_scholar",
            ))

    except httpx.TimeoutException:
        print("[SemanticScholar] Request timed out")
    except Exception as e:
        print(f"[SemanticScholar] Error: {e}")

    return papers
