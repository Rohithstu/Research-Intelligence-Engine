"""
Crossref API Client
Official API: https://api.crossref.org/
Provides metadata for millions of academic works (DOIs).
"""

import httpx
from typing import List
from models.schemas import Paper

CROSSREF_URL = "https://api.crossref.org/works"

async def fetch_crossref(query: str, limit: int = 50) -> List[Paper]:
    """
    Fetch papers from Crossref API.
    """
    params = {
        "query": query,
        "rows": min(limit, 100),
    }

    headers = {
        "User-Agent": "ResearchIntelligenceSystem/1.0 (mailto:admin@example.com)"
    }

    papers: List[Paper] = []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(CROSSREF_URL, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        for item in data.get("message", {}).get("items", []):
            title = " ".join(item.get("title", ["Untitled"]))
            
            # Crossref doesn't provide abstracts in many cases, but we'll try
            abstract = item.get("abstract", "")
            
            authors = [
                f"{a.get('given', '')} {a.get('family', '')}".strip()
                for a in item.get("author", [])[:5]
            ]

            doi = item.get("DOI")
            
            # Publication Year
            created = item.get("created", {}).get("date-parts", [[None]])[0][0]
            year = int(created) if created else None
            
            # Publisher & Journal
            publisher = item.get("publisher")
            container_title = item.get("container-title", [None])[0]

            papers.append(Paper(
                id=f"cr_{doi.replace('/', '_')}" if doi else f"cr_{hash(title)}",
                title=title,
                abstract=abstract,
                authors=authors,
                year=year,
                citation_count=item.get("is-referenced-by-count", 0),
                doi=doi,
                url=f"https://doi.org/{doi}" if doi else None,
                source="crossref",
                access_type="paid",  # Default for Crossref, Unpaywall will enrich
                publisher=publisher,
                journal=container_title,
            ))

    except Exception as e:
        print(f"[Crossref] Error: {e}")

    return papers
