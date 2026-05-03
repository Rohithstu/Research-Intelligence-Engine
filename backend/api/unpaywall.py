"""
Unpaywall API Client
Official API: https://unpaywall.org/products/api
Free for academic/personal use.
"""

import httpx

UNPAYWALL_URL = "https://api.unpaywall.org/v2"

async def check_unpaywall(doi: str) -> dict:
    """
    Check if a paper is open access via Unpaywall.
    """
    if not doi:
        return {"is_oa": False}
        
    params = {
        "email": "admin@example.com"
    }
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{UNPAYWALL_URL}/{doi}", params=params)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "is_oa": data.get("is_oa", False),
                    "pdf_url": data.get("best_oa_location", {}).get("url_for_pdf"),
                    "oa_status": data.get("oa_status"),
                }
    except:
        pass
        
    return {"is_oa": False}
