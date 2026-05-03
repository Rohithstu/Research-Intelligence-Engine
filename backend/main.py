"""
Research Intelligence System — FastAPI Backend

ROLE: Orchestrate the full research intelligence pipeline
INTENT: Accept query → return analyzed papers, gaps, trends
CONTEXT: Called by React frontend on port 3000
"""

import asyncio
import time
print("--- RESEARCH INTELLIGENCE BACKEND STARTING ---")
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

from models.schemas import QueryRequest, SearchResponse, Paper
from agents.query_agent import QueryAgent
from api.semantic_scholar import fetch_semantic_scholar
from api.arxiv_client import fetch_arxiv
from api.open_alex import fetch_open_alex
from api.crossref import fetch_crossref
from core.discovery import find_free_version
from core.embedder import get_embedder
from core.faiss_store import get_faiss_store
from core.ranker import rank_papers
from core.analyzer import analyze
from core.semantic_search import semantic_search
from data.paper_store import get_paper_store
from data.library import load_library, save_to_library, remove_from_library
from core.progress import get_tracker, ProgressTracker
from fastapi import WebSocket, WebSocketDisconnect
import json


# ─────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────
app = FastAPI(
    title="Research Intelligence System",
    description="AI-powered research paper analysis and insight generation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singletons
agent = QueryAgent()


# ─────────────────────────────────────────
# WEBSOCKETS
# ─────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "ok", "message": "Research Intelligence System is running"}


@app.get("/health")
async def health():
    store = get_paper_store()
    faiss = get_faiss_store()
    return {
        "status": "healthy",
        "papers_in_store": store.size,
        "vectors_in_index": faiss.size,
    }


@app.post("/search", response_model=SearchResponse)
async def search(request: QueryRequest):
    """
    Main search endpoint.
    """
    start_time = time.time()
    tracker = get_tracker()
    tracker.on_update = manager.broadcast

    # Step 1: Query Refinement
    await tracker.update("refining", "AI Agent is refining your research query...")
    agent_result = agent.refine(request.query)
    refined_query = agent_result["refined_query"]
    topics = agent_result["topics"]

    # Step 2: Fetch Papers (with timeout)
    await tracker.update("fetching", f"Scanning global databases (S2, arXiv, OpenAlex, Crossref)...")
    try:
        results = await asyncio.wait_for(
            asyncio.gather(
                fetch_semantic_scholar(refined_query, limit=20),
                fetch_arxiv(refined_query, limit=20),
                fetch_open_alex(refined_query, limit=20),
                fetch_crossref(refined_query, limit=20),
                return_exceptions=True,
            ),
            timeout=15.0  # Max 15 seconds for API calls
        )
    except asyncio.TimeoutError:
        print("API Fetch Timed Out — continuing with what we have.")
        results = [[], [], [], []]

    ss_papers = results[0] if isinstance(results[0], list) else []
    arxiv_papers = results[1] if isinstance(results[1], list) else []
    oa_papers = results[2] if isinstance(results[2], list) else []
    cr_papers = results[3] if isinstance(results[3], list) else []
    print("Semantic Scholar:", len(ss_papers))
    print("arXiv:", len(arxiv_papers))
    print("OpenAlex:", len(oa_papers))
    print("Crossref:", len(cr_papers))

    all_fetched = ss_papers + arxiv_papers + oa_papers + cr_papers
    total_fetched = len(all_fetched)

    # FIXED INDENTATION ONLY
    if total_fetched == 0:
        all_fetched = [
            Paper(
                id="demo_1",
                title="Machine Learning Basics",
                abstract="This is a fallback demo paper for machine learning.",
                authors=["Demo Author"],
                year=2023,
                citation_count=100,
                source="demo",
                relevance_score=0.9,
                final_score=0.9,
            )
        ]
        total_fetched = 1

    # Step 3: Store
    await tracker.update("storing", "Syncing papers to local vector store...")
    paper_store = get_paper_store()
    faiss_store = get_faiss_store()
    embedder = get_embedder()

    new_papers = paper_store.add_papers(all_fetched)

    # Step 4: Embed
    if new_papers:
        await tracker.update("embedding", f"Generating S-BERT embeddings for {len(new_papers)} new papers...")
        texts = [p.title + ". " + p.abstract for p in new_papers]
        embeddings = embedder.embed_batch(texts)
        faiss_store.add_papers(new_papers, embeddings)

    # Step 5: Search
    await tracker.update("searching", "Performing semantic vector search...")
    query_vec = embedder.embed_text(refined_query)
    results = faiss_store.search(query_vec, top_k=min(100, faiss_store.size))

    result_ids = [r[0] for r in results]
    similarity_map = {r[0]: r[1] for r in results}

    candidate_papers = paper_store.get_by_ids(result_ids)

    # Step 6: Ranking
    await tracker.update("ranking", "Ranking papers by relevance, citations, and recency...")
    ranked_papers = rank_papers(
        candidate_papers,
        similarity_map,
        top_n=request.max_results,
    )

    # Step 6.5: Semantic Search for Analysis
    await tracker.update("analyzing", "AI is detecting research gaps and trends...")
    # Use semantic search to get top papers for analysis, but keep ranked_papers for response
    papers = all_fetched  # Keep original papers for fallback
    try:
        semantic_results = semantic_search(refined_query, papers, top_k=20)
        top_papers = [item["paper"] for item in semantic_results]
        print("Using semantic top papers:", len(top_papers))
    except Exception as e:
        # Fallback to original papers if semantic search fails
        print(f"Semantic search failed: {e}, using original papers for analysis")
        top_papers = papers[:20] if len(papers) >= 20 else papers

    # Step 7: Analysis - use semantic top papers
    analysis = analyze(top_papers, refined_query, topics)
    analysis.refined_query = refined_query

    # Step 8: Dynamic Filters for UI
    ui_filters = {
        "years": sorted(list(set(p.year for p in ranked_papers if p.year)), reverse=True),
        "sources": sorted(list(set(p.source for p in ranked_papers))),
        "access": sorted(list(set(p.access_type for p in ranked_papers))),
        "publishers": sorted(list(set(p.publisher for p in ranked_papers if p.publisher)))[:10],
    }

    elapsed_ms = (time.time() - start_time) * 1000

    await tracker.update("complete", "Research analysis complete!", {"time_ms": elapsed_ms})

    return SearchResponse(
        query=request.query,
        refined_query=refined_query,
        papers=ranked_papers,
        analysis=analysis,
        filters=ui_filters,
        total_fetched=total_fetched,
        processing_time_ms=round(elapsed_ms, 1),
    )


@app.delete("/cache")
async def clear_cache():
    get_paper_store().clear()
    get_faiss_store().clear()
    return {"status": "cleared"}


@app.post("/find-free")
async def find_free(request: dict):
    title = request.get("title")
    doi = request.get("doi")
    if not title:
        return {"error": "Title is required"}
    
    result = await find_free_version(title, doi)
    return result


@app.get("/library", response_model=List[Paper])
async def get_library():
    return load_library()

@app.post("/library")
async def add_to_library(paper: Paper):
    save_to_library(paper)
    return {"status": "success"}

@app.delete("/library/{paper_id}")
async def delete_from_library(paper_id: str):
    remove_from_library(paper_id)
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
