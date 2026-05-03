"""
Multi-Faceted Paper Ranker

Combines multiple signals into a single score:
  Final Score = w1*relevance + w2*citation_impact + w3*recency

Why multi-factor?
- Relevance alone misses influential older papers
- Citations alone ignores new emerging work  
- Recency alone ignores seminal papers
"""

import math
from typing import List, Dict, Optional
from datetime import datetime
from models.schemas import Paper


# ─────────────────────────────────────────
# WEIGHTS (must sum to 1.0)
# ─────────────────────────────────────────
WEIGHT_RELEVANCE = 0.40    # Semantic similarity
WEIGHT_CITATION  = 0.20    # Impact / authority
WEIGHT_RECENCY   = 0.15    # How recent (newer = better)
WEIGHT_ACCESS    = 0.15    # Free content
WEIGHT_SOURCE    = 0.10    # Diversity of source

CURRENT_YEAR = datetime.now().year
MAX_AGE_YEARS = 10  # Papers older than this get min recency score


def normalize_citations(citation_count: int) -> float:
    """
    Log-normalize citation count to [0, 1].
    log(1001) ≈ 7, so 1000 citations → ~1.0
    Uses log to avoid huge papers dominating.
    """
    if citation_count <= 0:
        return 0.0
    return min(1.0, math.log1p(citation_count) / math.log1p(1000))


def normalize_access(access_type: str) -> float:
    """
    Score access type: Open/Preprint >> Paid.
    """
    mapping = {
        "open": 1.0,
        "preprint": 0.9,
        "paid": 0.2,
        "closed": 0.2,
    }
    return mapping.get(access_type.lower(), 0.1)


def normalize_recency(year: int) -> float:
    """
    Recency score: newer papers score higher.
    2024 → 1.0, 2014 → 0.0
    """
    if not year:
        return 0.3  # default for unknown year
    age = CURRENT_YEAR - year
    if age <= 0:
        return 1.0
    if age >= MAX_AGE_YEARS:
        return 0.0
    return 1.0 - (age / MAX_AGE_YEARS)


def compute_final_score(
    relevance: float,
    citation_count: int,
    year: int,
    access_type: str,
    source: str,
    publisher: Optional[str] = None,
) -> float:
    """
    Combine all factors into a single final score in [0, 1].
    """
    r = max(0.0, min(1.0, relevance))
    c = normalize_citations(citation_count)
    t = normalize_recency(year)
    a = normalize_access(access_type)
    s = 1.0 if source in ["arxiv", "open_alex"] else 0.8

    score = (
        WEIGHT_RELEVANCE * r +
        WEIGHT_CITATION  * c +
        WEIGHT_RECENCY   * t +
        WEIGHT_ACCESS    * a +
        WEIGHT_SOURCE    * s
    )
    
    # Publisher Boost (+0.1)
    if publisher:
        trusted = ["nature", "science", "ieee", "elsevier", "springer", "acm", "mit press"]
        if any(p in publisher.lower() for p in trusted):
            score += 0.1

    return round(score, 4)


def rank_papers(
    papers: List[Paper],
    similarity_map: Dict[str, float],
    top_n: int = 15,
) -> List[Paper]:
    """
    Rank papers using multi-faceted scoring.
    
    Args:
        papers: list of Paper objects
        similarity_map: {paper_id: cosine_similarity}
        top_n: number of top papers to return

    Returns sorted list of top N papers with scores attached.
    """
    scored = []
    for paper in papers:
        relevance = similarity_map.get(paper.id, 0.0)
        final = compute_final_score(
            relevance, 
            paper.citation_count, 
            paper.year or 2015,
            paper.access_type,
            paper.source,
            paper.publisher
        )

        paper.relevance_score = round(relevance, 4)
        paper.final_score = final
        scored.append(paper)

    # Sort by final score descending
    scored.sort(key=lambda p: p.final_score, reverse=True)

    # Diversity filter: avoid too many papers from same year cluster
    selected = _diversity_filter(scored, top_n)

    return selected


def _diversity_filter(papers: List[Paper], top_n: int) -> List[Paper]:
    """
    Simple diversity: limit papers per year cluster to avoid repetition.
    Max 3 papers from any single year.
    """
    year_counts: Dict[int, int] = {}
    result = []

    for paper in papers:
        yr = paper.year or 0
        count = year_counts.get(yr, 0)
        if count < 4:  # max 4 per year
            result.append(paper)
            year_counts[yr] = count + 1
        if len(result) >= top_n:
            break

    return result
