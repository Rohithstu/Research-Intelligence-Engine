"""
Free Version Discovery Engine
Goal: Find free versions of closed/paid papers.
"""

from typing import Optional
from api.unpaywall import check_unpaywall
from api.arxiv_client import fetch_arxiv
from api.open_alex import fetch_open_alex

async def find_free_version(title: str, doi: Optional[str] = None) -> dict:
    """
    Search across multiple open sources to find a free PDF.
    """
    results = {
        "found": False,
        "source": None,
        "pdf_url": None,
        "type": None
    }
    
    # 1. Check Unpaywall if DOI exists
    if doi:
        upw = await check_unpaywall(doi)
        if upw["is_oa"] and upw["pdf_url"]:
            return {
                "found": True,
                "source": "Unpaywall",
                "pdf_url": upw["pdf_url"],
                "type": "OPEN"
            }
            
    # 2. Search arXiv by title
    arxiv_papers = await fetch_arxiv(title, limit=1)
    if arxiv_papers:
        # Check title similarity (simple)
        if title.lower()[:30] in arxiv_papers[0].title.lower():
            return {
                "found": True,
                "source": "arXiv",
                "pdf_url": arxiv_papers[0].url,
                "type": "PREPRINT"
            }
            
    # 3. Search OpenAlex
    oa_papers = await fetch_open_alex(title, limit=1)
    if oa_papers and oa_papers[0].access_type == "open":
        if title.lower()[:30] in oa_papers[0].title.lower():
            return {
                "found": True,
                "source": "OpenAlex",
                "pdf_url": oa_papers[0].url,
                "type": "OPEN"
            }
            
    return results
