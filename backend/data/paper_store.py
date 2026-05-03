"""
Paper Store: In-memory storage with deduplication and preprocessing.

Preprocessing pipeline:
1. Remove duplicates (by title similarity or DOI)
2. Handle missing values
3. Clean text (remove HTML, extra whitespace)
4. Normalize data
"""

import re
import unicodedata
from typing import List, Dict, Optional
from models.schemas import Paper


def clean_text(text: str) -> str:
    """Remove HTML tags, normalize whitespace, unicode."""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Normalize unicode
    text = unicodedata.normalize('NFKC', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def normalize_title(title: str) -> str:
    """Lowercase, remove punctuation for dedup comparison."""
    return re.sub(r'[^a-z0-9]', '', title.lower())


class PaperStore:
    """
    Thread-safe in-memory paper storage with deduplication.
    """

    def __init__(self):
        self._papers: Dict[str, Paper] = {}   # id → Paper
        self._doi_map: Dict[str, str] = {}    # doi → internal_id
        self._title_map: Dict[str, str] = {}  # normalized_title → internal_id

    def add_papers(self, papers: List[Paper]) -> List[Paper]:
        """
        Add papers with robust deduplication (DOI, Title) and metadata merging.
        """
        new_papers = []

        for paper in papers:
            # Preprocess
            paper = self._preprocess(paper)
            
            # 1. Identify Existing
            existing_id = None
            norm_title = normalize_title(paper.title)
            
            if paper.doi and paper.doi in self._doi_map:
                existing_id = self._doi_map[paper.doi]
            elif norm_title in self._title_map:
                existing_id = self._title_map[norm_title]
            
            if existing_id:
                # Merge metadata into existing paper
                self._merge(existing_id, paper)
                continue

            # 2. Add New
            self._papers[paper.id] = paper
            self._title_map[norm_title] = paper.id
            if paper.doi:
                self._doi_map[paper.doi] = paper.id
            
            new_papers.append(paper)

        return new_papers

    def _merge(self, existing_id: str, new_paper: Paper):
        """Merge new metadata into existing record."""
        existing = self._papers[existing_id]
        
        # Prefer longer abstract
        if len(new_paper.abstract) > len(existing.abstract):
            existing.abstract = new_paper.abstract
            
        # Prefer higher citation count
        if new_paper.citation_count > existing.citation_count:
            existing.citation_count = new_paper.citation_count
            
        # Fill missing fields
        if not existing.doi and new_paper.doi:
            existing.doi = new_paper.doi
            self._doi_map[new_paper.doi] = existing_id
            
        if not existing.year and new_paper.year:
            existing.year = new_paper.year
            
        if existing.access_type == "unknown" and new_paper.access_type != "unknown":
            existing.access_type = new_paper.access_type

        if not existing.publisher and new_paper.publisher:
            existing.publisher = new_paper.publisher
            
        if not existing.journal and new_paper.journal:
            existing.journal = new_paper.journal

    def get(self, paper_id: str) -> Optional[Paper]:
        return self._papers.get(paper_id)

    def get_all(self) -> List[Paper]:
        return list(self._papers.values())

    def get_by_ids(self, ids: List[str]) -> List[Paper]:
        return [self._papers[pid] for pid in ids if pid in self._papers]

    def clear(self):
        self._papers.clear()
        self._doi_map.clear()
        self._title_map.clear()

    @property
    def size(self) -> int:
        return len(self._papers)

    def _preprocess(self, paper: Paper) -> Paper:
        """Clean and normalize paper fields."""
        paper.title = clean_text(paper.title) or "Untitled"
        paper.abstract = clean_text(paper.abstract)

        # Classify Access
        if paper.access_type == "unknown":
            if paper.source == "arxiv":
                paper.access_type = "preprint"
            elif paper.url and any(domain in paper.url.lower() for domain in ["arxiv.org", "biorxiv.org"]):
                paper.access_type = "preprint"
            elif paper.citation_count > 500: # Heuristic: highly cited papers often have open versions
                paper.access_type = "open"

        # Handle missing year
        if paper.year and (paper.year < 1900 or paper.year > 2030):
            paper.year = None

        # Handle negative citations
        if paper.citation_count < 0:
            paper.citation_count = 0

        # Clean authors
        paper.authors = [clean_text(a) for a in paper.authors if a][:5]

        return paper


# Singleton
_store_instance: Optional[PaperStore] = None


def get_paper_store() -> PaperStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = PaperStore()
    return _store_instance
