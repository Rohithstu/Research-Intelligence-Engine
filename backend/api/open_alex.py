"""
OpenAlex API Client
Official API: https://docs.openalex.org/
Free, open-source, no key required for basic use.
"""

import httpx
from typing import List
from models.schemas import Paper

OPEN_ALEX_URL = "https://api.openalex.org/works"

async def fetch_open_alex(query: str, limit: int = 50) -> List[Paper]:
    """
    Fetch papers from OpenAlex API.
    """
    params = {
        "search": query,
        "per_page": min(limit, 100),
        "sort": "relevance_score:desc",
    }

    headers = {
        "User-Agent": "ResearchIntelligenceSystem/1.0 (mailto:admin@example.com)"
    }

    papers: List[Paper] = []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(OPEN_ALEX_URL, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        for item in data.get("results", []):
            title = item.get("title") or "Untitled"
            # OpenAlex abstract is often in "abstract_inverted_index" format, 
            # but sometimes they provide plain text or we can skip if complex.
            # For now, we'll try to get what's available.
            abstract = ""
            if item.get("abstract_inverted_index"):
                # Simplistic reconstruction of inverted index
                try:
                    index = item["abstract_inverted_index"]
                    word_list = [None] * (max([max(pos) for pos in index.values()]) + 1)
                    for word, positions in index.items():
                        for pos in positions:
                            word_list[pos] = word
                    abstract = " ".join([w for w in word_list if w is not None])
                except:
                    abstract = ""

            if not abstract and not title:
                continue

            authors = [
                au.get("author", {}).get("display_name", "Unknown")
                for au in item.get("authorships", [])[:5]
            ]

            doi = item.get("doi")
            if doi and doi.startswith("https://doi.org/"):
                doi = doi.replace("https://doi.org/", "")

            # Determine Access Type
            oa_status = item.get("open_access", {}).get("oa_status", "closed")
            access_type = "open" if oa_status != "closed" else "paid"
            
            # Publisher & Journal
            host = item.get("primary_location", {}).get("source", {}) or {}
            publisher = host.get("host_organization_name")
            journal = host.get("display_name")

            papers.append(Paper(
                id=f"oa_{item.get('id', '').split('/')[-1]}",
                title=title,
                abstract=abstract,
                authors=authors,
                year=item.get("publication_year"),
                citation_count=item.get("cited_by_count", 0),
                doi=doi,
                url=item.get("doi") or item.get("ids", {}).get("mag"),
                source="open_alex",
                access_type=access_type,
                publisher=publisher,
                journal=journal,
            ))

    except Exception as e:
        print(f"[OpenAlex] Error: {e}")

    return papers
