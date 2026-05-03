import json
import os
from typing import List
from models.schemas import Paper

DB_PATH = os.path.join(os.path.dirname(__file__), "saved_papers.json")

def load_library() -> List[Paper]:
    if not os.path.exists(DB_PATH):
        return []
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [Paper(**p) for p in data]
    except Exception as e:
        print(f"Error loading library: {e}")
        return []

def save_to_library(paper: Paper):
    library = load_library()
    # Check for duplicates
    if any(p.id == paper.id or (p.doi and p.doi == paper.doi) for p in library):
        return
    
    library.append(paper)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump([p.dict() for p in library], f, indent=2)

def remove_from_library(paper_id: str):
    library = load_library()
    library = [p for p in library if p.id != paper_id]
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump([p.dict() for p in library], f, indent=2)
