from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Paper(BaseModel):
    id: str
    title: str
    abstract: str
    authors: List[str]
    year: Optional[int] = None
    citation_count: int = 0
    doi: Optional[str] = None
    url: Optional[str] = None
    source: str = "unknown"  # "semantic_scholar" | "arxiv" | "open_alex" | "crossref"
    access_type: str = "unknown"  # "open", "paid", "preprint"
    publisher: Optional[str] = None
    journal: Optional[str] = None
    is_restricted: bool = False
    external_links: List[Dict[str, str]] = []  # [{"type": "publisher", "url": "..."}, ...]
    relevance_score: float = 0.0
    final_score: float = 0.0


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    max_results: int = Field(default=12, ge=5, le=100)


class ResearchGap(BaseModel):
    area: str
    description: str
    confidence: float  # 0.0 to 1.0


class Trend(BaseModel):
    topic: str
    direction: str  # "growing" | "stable" | "saturated"
    evidence: str


class AnalysisResult(BaseModel):
    refined_query: str
    key_themes: List[str]
    gaps: List[ResearchGap]
    trends: List[Trend]
    summary: str
    future_directions: List[str]


class SearchResponse(BaseModel):
    query: str
    refined_query: str
    papers: List[Paper]
    analysis: AnalysisResult
    filters: Dict[str, List[Any]]  # Added for dynamic filtering
    total_fetched: int
    processing_time_ms: float
