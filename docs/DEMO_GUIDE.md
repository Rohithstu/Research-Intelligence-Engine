# 🎬 Demo Guide — Research Intelligence System

## BEFORE THE DEMO (5 min prep)

1. Start backend: `cd backend && uvicorn main:app --reload --port 8000`
2. Start frontend: `cd frontend && npm start`
3. Open http://localhost:3000 in Chrome
4. Pre-warm by running one search: `"federated learning privacy"`
   (This loads the ML model so live demo is fast)

---

## DEMO SCRIPT (10 minutes)

### Step 1: Show the Problem (1 min)
> "Traditional keyword search returns too many irrelevant papers.
>  This system understands what you MEAN, not just what you type."

### Step 2: Show Query Refinement (2 min)
Type: `"I'm really confused about privacy in federated learning"`
Point out the status bar: **Original query → Refined query**
> "The AI agent strips out noise and reformats it into academic language."

### Step 3: Show Results (3 min)
Point to the paper cards:
- **Score badges** (relevance + citations + recency combined)
- **Source badges** (arXiv vs Semantic Scholar)
- **Citation counts** (academic impact)
- **Year** (recency)
> "Papers ranked by a formula — not just keyword match."

### Step 4: Show Insights Panel (3 min)
- **Key Themes**: extracted automatically from 12 papers
- **Research Gaps**: areas with NO papers in the results
  > "The system found that 'explainability' is under-explored here."
- **Trends**: growing vs saturated fields
  > "Publication volume is growing — this is an active field."
- **Future Directions**: AI-generated suggestions

### Step 5: Try a Different Query (1 min)
Type: `"deep learning cancer detection"`
> "Same pipeline, completely different domain."

---

## TALKING POINTS

| Feature | What to Say |
|---------|------------|
| Semantic Search | "Finds papers about the concept, not just the keyword" |
| FAISS | "Facebook's battle-tested similarity search — handles millions of vectors" |
| MiniLM | "Small but powerful — same tech behind ChatGPT's search" |
| Multi-factor ranking | "Not just relevance — we balance impact AND recency" |
| Gap detection | "Identifies what's MISSING from the literature" |
| Legal compliance | "Only metadata, official APIs — no copyright issues" |

---

## LIKELY QUESTIONS & ANSWERS

**Q: How is this different from Google Scholar?**
A: Google Scholar is keyword-based. This uses semantic vectors — it understands that "privacy-preserving ML" and "confidential computing for AI" are the same topic.

**Q: Where does the data come from?**
A: Official APIs only — Semantic Scholar (200M+ papers) and arXiv (2M+ preprints). No scraping, fully legal.

**Q: What's the scoring formula?**
A: `Final = 0.55×relevance + 0.25×citations + 0.20×recency`. Weights are configurable in `ranker.py`.

**Q: Can it handle non-CS topics?**
A: Yes — both APIs cover medicine, biology, physics, economics. Try "CRISPR gene editing" or "climate change modeling".

**Q: How fast is it?**
A: First query ~3-5s (model loads, APIs respond). Subsequent queries ~1-2s (model cached, embeddings reused).

---

## IMPROVEMENTS TO MENTION

1. **LLM-powered agent**: Replace rule-based refinement with Claude API
2. **Persistent index**: Save FAISS to disk for instant cold starts
3. **CrossRef API**: Add DOI resolution and journal metadata
4. **Citation graph**: Visualize how papers cite each other
5. **User accounts**: Save search history and bookmarks
6. **PDF summarization**: Use Claude to summarize open-access papers
