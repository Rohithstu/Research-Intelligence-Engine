"""
arXiv API Client
Official API: https://arxiv.org/help/api
Free, no key required.
"""

import httpx
import feedparser
from typing import List
from models.schemas import Paper


ARXIV_URL = "https://export.arxiv.org/api/query"


async def fetch_arxiv(query: str, limit: int = 30) -> List[Paper]:
    """
    Fetch papers from arXiv via official API (Atom feed).
    Returns list of Paper objects.
    """
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": min(limit, 50),
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    papers: List[Paper] = []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(ARXIV_URL, params=params)
            resp.raise_for_status()
            content = resp.text

        feed = feedparser.parse(content)

        for entry in feed.entries:
            abstract = entry.get("summary", "").replace("\n", " ").strip()
            if not abstract or len(abstract) < 30:
                continue

            # Extract year from published date
            published = entry.get("published", "")
            year = None
            if published and len(published) >= 4:
                try:
                    year = int(published[:4])
                except ValueError:
                    pass

            # Authors
            authors = [
                a.get("name", "Unknown")
                for a in entry.get("authors", [])[:5]
            ]

            # arXiv ID
            arxiv_id = entry.get("id", "").split("/abs/")[-1]
            url = f"https://arxiv.org/abs/{arxiv_id}"

            papers.append(Paper(
                id=f"arxiv_{arxiv_id.replace('/', '_')}",
                title=entry.get("title", "Untitled").replace("\n", " ").strip(),
                abstract=abstract,
                authors=authors,
                year=year,
                citation_count=0,  # arXiv doesn't provide citation counts
                doi=None,
                url=url,
                source="arxiv",
            ))

    except httpx.TimeoutException:
        print("[arXiv] Request timed out")
    except Exception as e:
        print(f"[arXiv] Error: {e}")

    return papers
