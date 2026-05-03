"""
Research Analysis Layer

Detects:
1. Research Gaps: Under-explored areas based on low paper density
2. Trends: Growing, stable, or saturated topics based on publication years
3. Key Themes: Common concepts across top papers
4. Future Directions: Suggestions based on gaps + trends
"""

import re
from collections import Counter
from typing import List, Dict, Tuple
from models.schemas import Paper, ResearchGap, Trend, AnalysisResult


# ─────────────────────────────────────────────────
# COMMON ACADEMIC SUBTOPICS TO CHECK FOR PRESENCE
# ─────────────────────────────────────────────────
SUBTOPIC_PROBES = [
    ("efficiency", ["efficient", "lightweight", "fast", "scalable", "compressed"]),
    ("privacy", ["privacy", "differential privacy", "secure", "confidential"]),
    ("robustness", ["robust", "adversarial", "attack", "defense", "noise"]),
    ("explainability", ["explainable", "interpretable", "xai", "transparent"]),
    ("fairness", ["fair", "bias", "equity", "discrimination"]),
    ("real-world deployment", ["deploy", "production", "edge", "mobile", "iot"]),
    ("low-resource settings", ["low-resource", "few-shot", "zero-shot", "small data"]),
    ("cross-domain", ["transfer", "domain adaptation", "generalization"]),
    ("evaluation benchmarks", ["benchmark", "dataset", "evaluation", "metric"]),
    ("theoretical analysis", ["convergence", "bound", "proof", "theoretical"]),
]

STOP_WORDS = {
    "the", "a", "an", "and", "or", "in", "of", "to", "for", "is", "are",
    "with", "that", "this", "on", "at", "by", "as", "be", "was", "were",
    "it", "we", "our", "their", "from", "has", "have", "can", "which",
    "also", "using", "based", "proposed", "show", "paper", "method",
    "approach", "model", "result", "work", "study", "present", "use",
    "these", "those", "their", "between", "among", "within", "during",
    "through", "following", "related", "different", "various", "multiple"
}


def extract_keywords(papers: List[Paper], top_n: int = 15) -> List[str]:
    """Extract most frequent meaningful words and bigrams from abstracts."""
    word_freq: Counter = Counter()
    bigram_freq: Counter = Counter()

    for paper in papers:
        text = (paper.title + " " + paper.abstract).lower()
        words = re.findall(r'\b[a-z][a-z\-]{3,}\b', text)
        
        # Filtered words for bigrams
        filtered = [w for w in words if w not in STOP_WORDS]
        
        for w in filtered:
            word_freq[w] += 1
            
        # Extract bigrams
        for i in range(len(filtered) - 1):
            bigram = f"{filtered[i]} {filtered[i+1]}"
            bigram_freq[bigram] += 1

    # Combine and pick best
    best_bigrams = [b for b, count in bigram_freq.most_common(10) if count > 1]
    best_words = [w for w, count in word_freq.most_common(15)]
    
    # Prioritize bigrams if they are frequent
    combined = []
    seen = set()
    
    for b in best_bigrams:
        combined.append(b)
        for w in b.split():
            seen.add(w)
            
    for w in best_words:
        if w not in seen:
            combined.append(w)
            
    return combined[:top_n]


def detect_gaps(papers: List[Paper], query: str) -> List[ResearchGap]:
    """
    Detect under-explored research areas.
    Logic: Check which SUBTOPIC_PROBES are absent or rare in the papers.
    """
    gaps = []
    all_text = " ".join(
        (p.title + " " + p.abstract).lower()
        for p in papers
    )

    for subtopic, keywords in SUBTOPIC_PROBES:
        hits = sum(1 for kw in keywords if kw in all_text)
        if hits == 0:
            gaps.append(ResearchGap(
                area=subtopic,
                description=f"Research into {subtopic} appears nascent in this specific corpus, suggesting a potential gap for multi-faceted analysis.",
                confidence=0.9,
            ))
        elif hits == 1:
            gaps.append(ResearchGap(
                area=subtopic,
                description=f"Found isolated focus on {subtopic} — systemic analysis or integration remains a likely research opportunity.",
                confidence=0.6,
            ))

    # Limit to top 4 most confident gaps
    gaps.sort(key=lambda g: g.confidence, reverse=True)
    return gaps[:4]


def analyze_trends(papers: List[Paper]) -> List[Trend]:
    """
    Detect publication growth trends by year.
    """
    if not papers:
        return []

    year_counts: Counter = Counter()
    for p in papers:
        if p.year and 2010 <= p.year <= 2025:
            year_counts[p.year] += 1

    if not year_counts:
        return []

    sorted_years = sorted(year_counts.keys())
    trends = []

    # Recent growth (last 3 years vs 3 years before)
    recent_years = [y for y in sorted_years if y >= 2021]
    older_years = [y for y in sorted_years if 2017 <= y <= 2020]

    recent_count = sum(year_counts[y] for y in recent_years)
    older_count = sum(year_counts[y] for y in older_years)

    if recent_count > older_count * 1.5:
        trends.append(Trend(
            topic="Publication Volume",
            direction="growing",
            evidence=f"{recent_count} papers from 2021-2025 vs {older_count} from 2017-2020 — strong growth.",
        ))
    elif recent_count < older_count * 0.6:
        trends.append(Trend(
            topic="Publication Volume",
            direction="saturated",
            evidence=f"Research appears to be declining — {recent_count} recent vs {older_count} older papers.",
        ))
    else:
        trends.append(Trend(
            topic="Publication Volume",
            direction="stable",
            evidence=f"Steady research activity: {recent_count} recent vs {older_count} older papers.",
        ))

    # Peak year
    if sorted_years:
        peak_year = max(year_counts, key=lambda y: year_counts[y])
        if peak_year < 2021:
            trends.append(Trend(
                topic="Research Peak",
                direction="saturated",
                evidence=f"Peak publication year was {peak_year}, suggesting the field may have matured.",
            ))
        else:
            trends.append(Trend(
                topic="Research Peak",
                direction="growing",
                evidence=f"Peak activity in {peak_year} — field is still active.",
            ))

    return trends


def generate_future_directions(
    gaps: List[ResearchGap],
    trends: List[Trend],
    keywords: List[str],
) -> List[str]:
    """Generate future research direction suggestions."""
    directions = []
    
    # Priority themes
    main_theme = keywords[0] if keywords else "this domain"

    for gap in gaps[:3]:
        directions.append(
            f"Synthesize {gap.area.lower()} with {main_theme} to address current structural limitations."
        )

    growing = [t for t in trends if t.direction == "growing"]
    if growing:
        directions.append(
            f"Capitalize on the upward trajectory of {growing[0].topic.lower()} by exploring hybrid methodologies."
        )

    saturated = [t for t in trends if t.direction == "saturated"]
    if saturated:
        directions.append(
            "Pivot towards cross-disciplinary applications to rejuvenate research in mature sub-sectors."
        )

    if not directions:
        directions = [
            "Explore cross-domain applications of existing methods.",
            "Conduct large-scale empirical comparisons of existing approaches.",
            "Investigate real-world deployment challenges.",
        ]

    return directions[:5]


def summarize_papers(papers: List[Paper], query: str) -> str:
    """Generate a short summary of what the papers cover."""
    if not papers:
        return "No papers found for this query."

    years = [p.year for p in papers if p.year]
    year_range = f"{min(years)}–{max(years)}" if years else "unknown years"
    total_citations = sum(p.citation_count for p in papers)
    top_title = papers[0].title if papers else ""

    return (
        f"Retrieved {len(papers)} papers spanning {year_range} "
        f"with a combined {total_citations:,} citations. "
        f"Top result: \"{top_title[:80]}{'...' if len(top_title) > 80 else ''}\"."
    )


def analyze(papers: List[Paper], query: str, topics: List[str]) -> AnalysisResult:
    """
    Full analysis pipeline.
    Returns AnalysisResult with themes, gaps, trends, directions.
    """
    keywords = extract_keywords(papers)
    gaps = detect_gaps(papers, query)
    trends = analyze_trends(papers)
    future_directions = generate_future_directions(gaps, trends, keywords)
    summary = summarize_papers(papers, query)

    return AnalysisResult(
        refined_query=query,
        key_themes=keywords[:8],
        gaps=gaps,
        trends=trends,
        summary=summary,
        future_directions=future_directions,
    )
