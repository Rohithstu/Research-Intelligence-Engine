"""
AI Agent: Query Understanding & Refinement

ROLE: Extract academic intent from messy user queries
INTENT: Convert casual/unclear queries into precise academic search terms
CONTEXT: Users may be confused, use informal language, or be overly vague
ENFORCEMENT: Must always return a cleaned, academic-style query
"""

import re
from typing import Tuple, List


# ─────────────────────────────────────────────
# AGENT PROMPT (for use with LLM if API key set)
# ─────────────────────────────────────────────
AGENT_SYSTEM_PROMPT = """
You are an expert academic research query refiner.

ROLE: Convert messy, informal, or unclear user queries into precise academic search queries.

INTENT: Help users find the most relevant research papers by understanding their true intent.

CONTEXT: Users often write queries that are:
- Too vague ("tell me about AI")
- Too personal ("I'm confused about X")
- Too broad ("everything about deep learning")
- Contain noise words ("like", "kind of", "I think")

ENFORCEMENT RULES:
1. ALWAYS return a refined query in academic format
2. Extract the CORE TOPIC and KEY SUBTOPICS
3. Remove filler words and personal language
4. Use proper academic terminology
5. Keep it concise: 4-10 words ideal
6. Return ONLY the refined query, nothing else

EXAMPLES:
Input: "I'm confused about privacy in federated learning"
Output: "privacy-preserving federated learning techniques"

Input: "how does transformer work in NLP kind of?"
Output: "transformer architecture natural language processing attention mechanism"

Input: "recent stuff about cancer detection using AI"
Output: "deep learning cancer detection medical imaging"

Input: "tell me about climate change and ML"
Output: "machine learning climate change prediction modeling"
"""

AGENT_USER_PROMPT = """
Refine this research query into academic format:
"{query}"

Return ONLY the refined query.
"""


# ─────────────────────────────────────────────
# RULE-BASED REFINEMENT (no API key needed)
# ─────────────────────────────────────────────

# Noise words to remove
NOISE_PATTERNS = [
    r"\bi'?m\s+(confused|wondering|curious|interested|looking)\s+(about|into|for|at)\b",
    r"\bcan you (tell|show|explain|find)\s+(me\s+)?(about|regarding)?\b",
    r"\bi want to (know|learn|understand|find out) (about|regarding)?\b",
    r"\bwhat (is|are|about|regarding)\b",
    r"\brecent (stuff|things|papers|work|research) (on|about|regarding)?\b",
    r"\bkind of\b",
    r"\bsort of\b",
    r"\blike\b",
    r"\bmaybe\b",
    r"\bi think\b",
    r"\bplease\b",
    r"\bthanks?\b",
    r"\bhelp me\b",
    r"\bexplain\b",
    r"\btell me\b",
    r"\bshow me\b",
]

# Domain-specific keyword expansions
TOPIC_EXPANSIONS = {
    "federated learning": "federated learning privacy distributed",
    "transformer": "transformer architecture attention mechanism",
    "gpt": "large language model generative pre-training",
    "llm": "large language model neural network",
    "cancer": "cancer detection classification deep learning",
    "covid": "COVID-19 pandemic analysis machine learning",
    "climate": "climate change prediction machine learning",
    "nlp": "natural language processing text analysis",
    "cv": "computer vision image recognition",
    "rl": "reinforcement learning policy optimization",
    "gan": "generative adversarial network image synthesis",
}


def refine_query_rules(raw_query: str) -> Tuple[str, List[str]]:
    """
    Rule-based query refinement.
    Returns: (refined_query, extracted_topics)
    """
    query = raw_query.lower().strip()

    # Remove noise patterns
    for pattern in NOISE_PATTERNS:
        query = re.sub(pattern, " ", query, flags=re.IGNORECASE)

    # Clean whitespace
    query = re.sub(r"\s+", " ", query).strip()
    query = re.sub(r"[?!,;]+", "", query).strip()

    # Apply topic expansions for known abbreviations (without duplicates)
    original_words = set(query.split())
    for abbrev, expansion in TOPIC_EXPANSIONS.items():
        if abbrev in query:
            expansion_words = expansion.split()
            new_words = [w for w in expansion_words if w not in original_words]
            if new_words:
                query = query.replace(abbrev, f"{abbrev} {' '.join(new_words)}")

    # Final cleanup to ensure no duplicate words in the refined query
    seen = set()
    final_words = []
    for word in query.split():
        if word not in seen:
            final_words.append(word)
            seen.add(word)
    
    query = " ".join(final_words)

    # Extract key noun phrases
    topics = extract_topics(query)

    return query.strip(), topics


def extract_topics(text: str) -> List[str]:
    """Extract key topics from cleaned query."""
    # Remove common stop words
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at",
        "to", "for", "of", "with", "by", "from", "is", "are",
        "was", "were", "be", "been", "being", "have", "has",
        "do", "does", "did", "will", "would", "could", "should",
        "may", "might", "must", "can", "about", "using", "based"
    }
    words = text.lower().split()
    topics = [w for w in words if w not in stop_words and len(w) > 3]
    return list(dict.fromkeys(topics))[:5]  # deduplicate, keep order, max 5


class QueryAgent:
    """
    AI Query Refinement Agent

    Works in two modes:
    1. Rule-based (default, no API needed)
    2. LLM-powered (optional, set ANTHROPIC_API_KEY or OPENAI_API_KEY)
    """

    def __init__(self):
        self.mode = "rule-based"

    def refine(self, raw_query: str) -> dict:
        """
        Main entry point. Refines user query.

        Returns dict with:
          - refined_query: cleaned academic query
          - original_query: raw input
          - topics: extracted key topics
          - mode: which mode was used
        """
        if not raw_query or len(raw_query.strip()) < 3:
            return {
                "refined_query": raw_query,
                "original_query": raw_query,
                "topics": [],
                "mode": self.mode,
            }

        refined, topics = refine_query_rules(raw_query)

        return {
            "refined_query": refined,
            "original_query": raw_query,
            "topics": topics,
            "mode": self.mode,
        }
